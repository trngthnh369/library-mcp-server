#!/usr/bin/env python3
"""
Library Management MCP Server
A Model Context Protocol server for managing a book library with tools, resources, and prompts.
"""

import asyncio
import contextlib
import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, AsyncIterator
from collections import Counter, defaultdict

import click
import uvicorn
from starlette.applications import Starlette
from starlette.routing import Mount
from starlette.types import Scope, Receive, Send

from mcp.server.lowlevel import Server
from mcp.server.stdio import stdio_server
from mcp.server.sse import SseServerTransport
from mcp.types import (
    EmbeddedResource,
    GetPromptResult,
    ImageContent,
    Prompt,
    PromptArgument,
    PromptMessage,
    Resource,
    ResourceTemplate,
    TextContent,
    Tool,
)
from pydantic.networks import AnyUrl

# Import local modules
from models import Book, BookISBNInput, AddBookInput, LibraryStats, SearchQuery, ErrorResponse
from config import get_config, ServerConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class LibraryCache:
    """Simple in-memory cache for library operations."""
    
    def __init__(self, ttl: int = 300):
        self.ttl = ttl
        self.cache: Dict[str, Dict[str, Any]] = {}
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if key in self.cache:
            entry = self.cache[key]
            if time.time() - entry["timestamp"] < self.ttl:
                return entry["value"]
            else:
                del self.cache[key]
        return None
    
    def set(self, key: str, value: Any) -> None:
        """Set value in cache."""
        self.cache[key] = {
            "value": value,
            "timestamp": time.time()
        }
    
    def invalidate(self, pattern: Optional[str] = None) -> None:
        """Invalidate cache entries."""
        if pattern is None:
            self.cache.clear()
        else:
            keys_to_remove = [k for k in self.cache.keys() if pattern in k]
            for key in keys_to_remove:
                del self.cache[key]


class LibraryManagement:
    """Enhanced library management system with caching and improved error handling."""
    
    def __init__(self, config: ServerConfig):
        """Initialize library with configuration."""
        self.config = config
        self.books_path = config.books_file
        self.cache = LibraryCache(config.cache_ttl) if config.cache_enabled else None
        
        # Initialize books file if it doesn't exist
        if not self.books_path.exists():
            self.books_path.write_text("[]", encoding="utf-8")
        
        self._load_books()
        logger.info(f"Library initialized with {len(self.books)} books")
    
    def _load_books(self) -> None:
        """Load books from file with error handling."""
        try:
            content = self.books_path.read_text(encoding="utf-8")
            self.books = json.loads(content)
            if not isinstance(self.books, list):
                raise ValueError("Books file must contain a JSON array")
        except (json.JSONDecodeError, FileNotFoundError) as e:
            logger.error(f"Error loading books file: {e}")
            self.books = []
        except Exception as e:
            logger.error(f"Unexpected error loading books: {e}")
            self.books = []
    
    def _save_books(self) -> None:
        """Save books to file with error handling."""
        try:
            # Create backup
            backup_path = self.books_path.with_suffix('.json.backup')
            if self.books_path.exists():
                backup_path.write_text(
                    self.books_path.read_text(encoding="utf-8"),
                    encoding="utf-8"
                )
            
            # Write new data
            self.books_path.write_text(
                json.dumps(self.books, indent=2, ensure_ascii=False),
                encoding="utf-8"
            )
            
            # Invalidate cache
            if self.cache:
                self.cache.invalidate()
            
            logger.debug("Books saved successfully")
            
        except Exception as e:
            logger.error(f"Error saving books: {e}")
            raise RuntimeError(f"Failed to save books: {e}")
    
    def add_book(self, book: Book) -> str:
        """Add a book to the library with enhanced validation."""
        # Check library size limit
        if len(self.books) >= self.config.max_books:
            return f"Library is full (max {self.config.max_books} books)"
        
        # Check for duplicate ISBN
        isbn_exists = any(b["isbn"] == book.isbn for b in self.books)
        if isbn_exists:
            return f"Book with ISBN '{book.isbn}' already exists"
        
        # Add book
        book_dict = book.dict()
        self.books.append(book_dict)
        self._save_books()
        
        logger.info(f"Added book: '{book.title}' by {book.author}")
        return f"Book '{book.title}' by {book.author} added successfully"
    
    def remove_book(self, isbn: str) -> str:
        """Remove a book by ISBN."""
        original_count = len(self.books)
        self.books = [b for b in self.books if b["isbn"] != isbn]
        
        if len(self.books) == original_count:
            return f"No book found with ISBN '{isbn}'"
        
        self._save_books()
        logger.info(f"Removed book with ISBN: {isbn}")
        return f"Book with ISBN '{isbn}' removed successfully"
    
    def get_book_count(self) -> int:
        """Get total number of books."""
        return len(self.books)
    
    def get_all_books(self) -> List[Dict[str, Any]]:
        """Get all books with caching."""
        if self.cache:
            cached = self.cache.get("all_books")
            if cached is not None:
                return cached
        
        result = self.books.copy()
        
        if self.cache:
            self.cache.set("all_books", result)
        
        return result
    
    def get_book_by_index(self, index: int) -> Optional[Dict[str, Any]]:
        """Get book by index."""
        if 0 <= index < len(self.books):
            return self.books[index].copy()
        return None
    
    def get_book_by_isbn(self, isbn: str) -> Optional[Dict[str, Any]]:
        """Get book by ISBN with caching."""
        cache_key = f"book_isbn_{isbn}"
        
        if self.cache:
            cached = self.cache.get(cache_key)
            if cached is not None:
                return cached
        
        for book in self.books:
            if book["isbn"] == isbn:
                if self.cache:
                    self.cache.set(cache_key, book)
                return book.copy()
        
        return None
    
    def search_books(self, query: SearchQuery) -> List[Dict[str, Any]]:
        """Search books with various filters."""
        results = self.books.copy()
        
        # Filter by query text (title, author)
        if query.query:
            query_lower = query.query.lower()
            results = [
                book for book in results
                if (query_lower in book["title"].lower() or
                    query_lower in book["author"].lower())
            ]
        
        # Filter by author
        if query.author:
            author_lower = query.author.lower()
            results = [
                book for book in results
                if author_lower in book["author"].lower()
            ]
        
        # Filter by tag
        if query.tag:
            tag_lower = query.tag.lower()
            results = [
                book for book in results
                if any(tag_lower in tag.lower() for tag in book.get("tags", []))
            ]
        
        # Apply limit
        return results[:query.limit]
    
    def get_library_stats(self) -> LibraryStats:
        """Get library statistics with caching."""
        cache_key = "library_stats"
        
        if self.cache:
            cached = self.cache.get(cache_key)
            if cached is not None:
                return LibraryStats(**cached)
        
        # Calculate stats
        authors = set()
        all_tags = []
        
        for book in self.books:
            authors.add(book["author"])
            all_tags.extend(book.get("tags", []))
        
        tag_counts = Counter(all_tags)
        most_common_tags = [tag for tag, _ in tag_counts.most_common(10)]
        
        stats = LibraryStats(
            total_books=len(self.books),
            unique_authors=len(authors),
            unique_tags=len(set(all_tags)),
            most_common_tags=most_common_tags
        )
        
        if self.cache:
            self.cache.set(cache_key, stats.dict())
        
        return stats


async def create_server() -> Server:
    """Create and configure the MCP server."""
    config = get_config()
    library = LibraryManagement(config)
    
    server = Server("mcp-library")
    
    #### TOOLS ####
    @server.list_tools()
    async def list_tools() -> List[Tool]:
        """List all available tools for the library management system."""
        base_tools = [
            Tool(
                name="add_book",
                description="Add a book to the library",
                inputSchema=AddBookInput.schema(),
            ),
            Tool(
                name="remove_book",
                description="Remove a book by its ISBN",
                inputSchema=BookISBNInput.schema(),
            ),
            Tool(
                name="get_book_count",
                description="Get the total number of books in the library",
                inputSchema={"type": "object", "properties": {}},
            ),
        ]
        
        # Add optional tools based on configuration
        if config.enable_search:
            base_tools.append(Tool(
                name="search_books",
                description="Search books by title, author, or tags",
                inputSchema=SearchQuery.schema(),
            ))
        
        if config.enable_stats:
            base_tools.append(Tool(
                name="get_library_stats",
                description="Get library statistics",
                inputSchema={"type": "object", "properties": {}},
            ))
        
        return base_tools
    
    @server.call_tool()
    async def call_tool(
        name: str, arguments: Dict[str, Any]
    ) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
        """Call a specific tool by name with the provided arguments."""
        try:
            match name:
                case "add_book":
                    book = AddBookInput(**arguments)
                    result = library.add_book(book)
                    return [TextContent(type="text", text=result)]
                
                case "remove_book":
                    data = BookISBNInput(**arguments)
                    result = library.remove_book(data.isbn)
                    return [TextContent(type="text", text=result)]
                
                case "get_book_count":
                    result = library.get_book_count()
                    return [TextContent(type="text", text=str(result))]
                
                case "search_books":
                    if not config.enable_search:
                        raise ValueError("Search functionality is disabled")
                    query = SearchQuery(**arguments)
                    results = library.search_books(query)
                    return [TextContent(type="text", text=json.dumps(results, indent=2, ensure_ascii=False))]
                
                case "get_library_stats":
                    if not config.enable_stats:
                        raise ValueError("Statistics functionality is disabled")
                    stats = library.get_library_stats()
                    return [TextContent(type="text", text=json.dumps(stats.dict(), indent=2, ensure_ascii=False))]
                
                case _:
                    raise ValueError(f"Unknown tool: {name}")
        
        except Exception as e:
            logger.error(f"Tool '{name}' error: {str(e)}")
            error_response = ErrorResponse(
                error=str(e),
                error_code="TOOL_ERROR",
                details={"tool": name, "arguments": arguments}
            )
            return [TextContent(type="text", text=json.dumps(error_response.dict(), indent=2))]
    
    #### RESOURCES ####
    @server.list_resources()
    async def list_resources() -> List[Resource]:
        """List all available static resources."""
        resources = [
            Resource(
                name="all_books",
                title="All Books",
                uri=AnyUrl("books://all"),
                description="Get all books in the library",
            ),
        ]
        
        if config.enable_stats:
            resources.append(Resource(
                name="library_stats",
                title="Library Statistics",
                uri=AnyUrl("books://stats"),
                description="Get library statistics and metrics",
            ))
        
        return resources
    
    @server.list_resource_templates()
    async def list_resource_templates() -> List[ResourceTemplate]:
        """List all available dynamic resource templates."""
        templates = [
            ResourceTemplate(
                name="book_by_index",
                title="Book by Index",
                uriTemplate="books://index/{index}",
                description="Get a book by its index in the library",
            ),
            ResourceTemplate(
                name="book_by_isbn",
                title="Book by ISBN",
                uriTemplate="books://isbn/{isbn}",
                description="Get a book by its ISBN",
            ),
        ]
        
        if config.enable_search:
            templates.append(ResourceTemplate(
                name="search_books",
                title="Search Books",
                uriTemplate="books://search?q={query}&author={author}&tag={tag}&limit={limit}",
                description="Search books with optional filters",
            ))
        
        return templates
    
    @server.read_resource()
    async def read_resource(uri: AnyUrl) -> str:
        """Read a resource by its URI."""
        uri_str = str(uri)
        
        try:
            if uri_str == "books://all":
                books = library.get_all_books()
                return json.dumps(books, indent=2, ensure_ascii=False)
            
            elif uri_str == "books://stats" and config.enable_stats:
                stats = library.get_library_stats()
                return json.dumps(stats.dict(), indent=2, ensure_ascii=False)
            
            elif uri_str.startswith("books://index/"):
                index_str = uri_str.split("/")[-1]
                try:
                    index = int(index_str)
                    book = library.get_book_by_index(index)
                    if book is None:
                        raise ValueError(f"Book not found at index {index}")
                    return json.dumps(book, indent=2, ensure_ascii=False)
                except ValueError as e:
                    if "invalid literal" in str(e).lower():
                        raise ValueError(f"Invalid index: {index_str}")
                    raise
            
            elif uri_str.startswith("books://isbn/"):
                isbn = uri_str.split("/")[-1]
                book = library.get_book_by_isbn(isbn)
                if book is None:
                    raise ValueError(f"Book not found with ISBN: {isbn}")
                return json.dumps(book, indent=2, ensure_ascii=False)
            
            elif uri_str.startswith("books://search") and config.enable_search:
                # Parse query parameters
                from urllib.parse import urlparse, parse_qs
                parsed = urlparse(uri_str)
                params = parse_qs(parsed.query)
                
                search_args = {}
                if 'q' in params and params['q'][0]:
                    search_args['query'] = params['q'][0]
                if 'author' in params and params['author'][0]:
                    search_args['author'] = params['author'][0]
                if 'tag' in params and params['tag'][0]:
                    search_args['tag'] = params['tag'][0]
                if 'limit' in params and params['limit'][0]:
                    search_args['limit'] = int(params['limit'][0])
                
                query = SearchQuery(**search_args)
                results = library.search_books(query)
                return json.dumps(results, indent=2, ensure_ascii=False)
            
            else:
                raise ValueError(f"Resource not found: {uri}")
        
        except Exception as e:
            logger.error(f"Resource read error for {uri}: {str(e)}")
            error_response = ErrorResponse(
                error=str(e),
                error_code="RESOURCE_ERROR",
                details={"uri": uri_str}
            )
            return json.dumps(error_response.dict(), indent=2)
    
    #### PROMPTS ####
    @server.list_prompts()
    async def list_prompts() -> List[Prompt]:
        """List all available prompts."""
        return [
            Prompt(
                name="suggest_random_book",
                description="Suggest a random book from the library with title, author, and brief description.",
            ),
            Prompt(
                name="suggest_book_title_by_abstract",
                description="Suggest a memorable, descriptive title for a book based on an abstract.",
                arguments=[
                    PromptArgument(
                        name="abstract",
                        description="The abstract of the book",
                        required=True,
                    )
                ],
            ),
            Prompt(
                name="analyze_book",
                description="Analyze a book based on its content and user query.",
                arguments=[
                    PromptArgument(
                        name="book",
                        description="The book to analyze (JSON format)",
                        required=True
                    ),
                    PromptArgument(
                        name="query",
                        description="The analysis query",
                        required=True,
                    ),
                ],
            ),
            Prompt(
                name="recommend_books",
                description="Recommend books based on user preferences and library content.",
                arguments=[
                    PromptArgument(
                        name="preferences",
                        description="User preferences (genres, authors, themes)",
                        required=True,
                    ),
                    PromptArgument(
                        name="count",
                        description="Number of recommendations (default: 5)",
                        required=False,
                    ),
                ],
            ),
        ]
    
    @server.get_prompt()
    async def get_prompt(name: str, arguments: Dict[str, str] | None) -> GetPromptResult:
        """Get a specific prompt by name."""
        if arguments is None:
            arguments = {}
        
        try:
            match name:
                case "suggest_random_book":
                    books = library.get_all_books()
                    if not books:
                        prompt_text = "The library is empty. No books available to suggest."
                    else:
                        import random
                        book = random.choice(books)
                        prompt_text = (
                            f"Suggest this book from the library:\n\n"
                            f"Title: {book['title']}\n"
                            f"Author: {book['author']}\n"
                            f"ISBN: {book['isbn']}\n"
                            f"Tags: {', '.join(book.get('tags', []))}\n\n"
                            f"Please provide a brief, engaging description of why someone might enjoy this book."
                        )
                    
                    return GetPromptResult(
                        description="Suggest a random book from the library",
                        messages=[
                            PromptMessage(
                                role="user",
                                content=TextContent(type="text", text=prompt_text),
                            )
                        ],
                    )
                
                case "suggest_book_title_by_abstract":
                    if "abstract" not in arguments:
                        raise ValueError("Missing required argument: abstract")
                    
                    abstract = arguments["abstract"]
                    prompt_text = (
                        f"Based on the following abstract, suggest a memorable and descriptive book title:\n\n"
                        f"Abstract: {abstract}\n\n"
                        f"Please suggest 3-5 potential titles that would be engaging and accurately represent the content."
                    )
                    
                    return GetPromptResult(
                        description="Suggest book titles based on abstract",
                        messages=[
                            PromptMessage(
                                role="user",
                                content=TextContent(type="text", text=prompt_text),
                            )
                        ],
                    )
                
                case "analyze_book":
                    if "book" not in arguments or "query" not in arguments:
                        raise ValueError("Missing required arguments: book, query")
                    
                    try:
                        book = json.loads(arguments["book"])
                    except json.JSONDecodeError:
                        raise ValueError("Invalid book JSON format")
                    
                    query = arguments["query"]
                    
                    return GetPromptResult(
                        description="Analyze a book based on user query",
                        messages=[
                            PromptMessage(
                                role="user",
                                content=TextContent(
                                    type="text", 
                                    text=f"Here's the book I want to analyze: {json.dumps(book, ensure_ascii=False)}"
                                ),
                            ),
                            PromptMessage(
                                role="assistant",
                                content=TextContent(
                                    type="text",
                                    text="I'd be happy to analyze this book for you! What would you like to know about it?"
                                ),
                            ),
                            PromptMessage(
                                role="user",
                                content=TextContent(type="text", text=query),
                            ),
                        ],
                    )
                
                case "recommend_books":
                    preferences = arguments.get("preferences", "")
                    count = int(arguments.get("count", "5"))
                    
                    books = library.get_all_books()
                    books_summary = f"\n\nAvailable books in library ({len(books)} total):\n"
                    for i, book in enumerate(books[:20], 1):  # Show first 20 books
                        tags_str = ", ".join(book.get("tags", []))
                        books_summary += f"{i}. '{book['title']}' by {book['author']} [{tags_str}]\n"
                    
                    if len(books) > 20:
                        books_summary += f"... and {len(books) - 20} more books\n"
                    
                    prompt_text = (
                        f"Based on these user preferences: {preferences}\n\n"
                        f"Please recommend {count} books from the available library collection."
                        f"{books_summary}\n"
                        f"Provide recommendations with explanations of why each book matches the user's preferences."
                    )
                    
                    return GetPromptResult(
                        description="Recommend books based on user preferences",
                        messages=[
                            PromptMessage(
                                role="user",
                                content=TextContent(type="text", text=prompt_text),
                            )
                        ],
                    )
                
                case _:
                    raise ValueError(f"Unknown prompt: {name}")
        
        except Exception as e:
            logger.error(f"Prompt '{name}' error: {str(e)}")
            error_text = f"Error generating prompt '{name}': {str(e)}"
            return GetPromptResult(
                description=f"Error in prompt {name}",
                messages=[
                    PromptMessage(
                        role="user",
                        content=TextContent(type="text", text=error_text),
                    )
                ],
            )
    
    return server


async def serve_stdio():
    """Serve using standard input/output transport."""
    server = await create_server()
    options = server.create_initialization_options()
    
    async with stdio_server() as (read_stream, write_stream):
        logger.info("MCP Library Server running with stdio transport")
        await server.run(read_stream, write_stream, options)


async def serve_http(port: int, host: str, log_level: str):
    """Serve using SSE HTTP transport."""
    server = await create_server()
    
    transport = SseServerTransport("/messages")
    
    async def handle_sse_request(scope: Scope, receive: Receive, send: Send) -> None:
        """Handle SSE requests."""
        await transport.handle_request(scope, receive, send, server)
    
    @contextlib.asynccontextmanager
    async def lifespan(app: Starlette) -> AsyncIterator[None]:
        """Manage application lifecycle."""
        logger.info(f"MCP Library Server started with SSE transport on {host}:{port}")
        try:
            yield
        finally:
            logger.info("MCP Library Server shutting down...")
    
    # Create ASGI application
    starlette_app = Starlette(
        debug=True,
        routes=[
            Mount("/messages", app=handle_sse_request),
        ],
        lifespan=lifespan,
    )
    
    # Run the server
    config = uvicorn.Config(
        starlette_app,
        host=host,
        port=port,
        log_level=log_level.lower()
    )
    uvicorn_server = uvicorn.Server(config)
    await uvicorn_server.serve()


@click.command()
@click.option(
    "--log-level",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]),
    default="INFO",
    help="Set the logging level",
)
@click.option(
    "--transport",
    type=click.Choice(["stdio", "sse"]),
    default="stdio",
    help="Transport mechanism to use",
)
@click.option(
    "--port",
    type=int,
    default=8000,
    help="Port for SSE transport (ignored for stdio)",
)
@click.option(
    "--host",
    type=str,
    default="127.0.0.1",
    help="Host for SSE transport (ignored for stdio)",
)
def main(log_level: str, transport: str, port: int, host: str):
    """Run the Library MCP Server."""
    # Configure logging
    logging.getLogger().setLevel(getattr(logging, log_level))
    
    # Update configuration
    from config import update_config
    update_config(
        host=host,
        port=port,
        log_level=log_level
    )
    
    if transport == "stdio":
        asyncio.run(serve_stdio())
    else:
        asyncio.run(serve_http(port, host, log_level))


if __name__ == "__main__":
    main()