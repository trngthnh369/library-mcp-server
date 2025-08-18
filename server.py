#!/usr/bin/env python3
"""
Library Management MCP Server
A Model Context Protocol server for managing a book library with tools, resources, and prompts.
"""

import asyncio
import contextlib
import json
import logging
from pathlib import Path
from typing import Dict, List, Sequence, AsyncIterator

import click
import uvicorn
from starlette.applications import Starlette
from starlette.routing import Mount
from starlette.types import Scope, Receive, Send

from mcp.server.lowlevel import Server
from mcp.server.stdio import stdio_server
# from mcp.server.streamablehttp import StreamableHTTPSessionManager
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
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
from pydantic import BaseModel, Field
from pydantic.networks import AnyUrl

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Book(BaseModel):
    """Book model with validation."""
    title: str = Field(..., description="The title of the book")
    author: str = Field(..., description="The author of the book")
    isbn: str = Field(..., description="The ISBN of the book")
    tags: List[str] = Field(default_factory=list, description="Tags associated with the book")


class BookISBNInput(BaseModel):
    """Input model for ISBN-based operations."""
    isbn: str = Field(..., description="The ISBN of the book to be removed or retrieved")


class AddBookInput(Book):
    """Input model for adding books."""
    pass


class LibraryManagement:
    """Library management system for handling book operations."""
    
    def __init__(self, books_path: Path):
        """Initialize library with books file path."""
        self.books_path = books_path
        if not books_path.exists():
            books_path.write_text("[]", encoding="utf-8")
        self.books = json.loads(books_path.read_text(encoding="utf-8"))
    
    def save_books(self):
        """Save books to file."""
        self.books_path.write_text(
            json.dumps(self.books, indent=4, ensure_ascii=False), 
            encoding="utf-8"
        )
    
    def add_book(self, book: Book) -> str:
        """Add a book to the library."""
        # Check for duplicate ISBN
        if any(b["isbn"] == book.isbn.strip() for b in self.books):
            return f"Book with ISBN '{book.isbn}' already exists."
        
        # Validate required fields
        if not all([book.title.strip(), book.author.strip(), book.isbn.strip()]):
            return "Title, author, and ISBN cannot be empty."
        
        # Clean tags
        clean_tags = [t.strip() for t in book.tags if isinstance(t, str) and t.strip()]
        
        # Add book
        self.books.append({
            "title": book.title.strip(),
            "author": book.author.strip(),
            "isbn": book.isbn.strip(),
            "tags": clean_tags,
        })
        self.save_books()
        return f"Book '{book.title}' by {book.author} added to the library."
    
    def remove_book(self, isbn: str) -> str:
        """Remove a book by ISBN."""
        updated = [b for b in self.books if b["isbn"] != isbn.strip()]
        if len(updated) == len(self.books):
            return f"No book found with ISBN '{isbn}'."
        self.books = updated
        self.save_books()
        return f"Book with ISBN '{isbn}' removed from the library."
    
    def get_num_books(self) -> int:
        """Get total number of books."""
        return len(self.books)
    
    def get_all_books(self) -> List[Dict]:
        """Get all books."""
        return self.books
    
    def get_book_by_index(self, index: int) -> Dict:
        """Get book by index."""
        if 0 <= index < len(self.books):
            return self.books[index]
        return {"error": "Book not found."}
    
    def get_book_by_isbn(self, isbn: str) -> Dict:
        """Get book by ISBN."""
        for book in self.books:
            if book["isbn"] == isbn.strip():
                return book
        return {"error": "Book not found."}
    
    def get_suggesting_random_book_prompt(self) -> str:
        """Get prompt for suggesting a random book."""
        return ("Suggest a random book from the library. The suggestion should include "
                "the title, author, and a brief description.")
    
    def get_suggesting_book_title_by_abstract_prompt(self, abstract: str) -> str:
        """Get prompt for suggesting book title by abstract."""
        return f"Suggest a memorable, descriptive title for a book based on the following abstract: {abstract}"
    
    def get_analyzing_book_messages(self, book: Dict, query: str) -> List[Dict[str, str]]:
        """Get messages for book analysis."""
        return [
            {
                "role": "user",
                "content": "This is the book I want to analyze: " + json.dumps(book, ensure_ascii=False),
            },
            {
                "role": "assistant",
                "content": "Sure! Let's analyze this book together. What would you like to know?",
            },
            {"role": "user", "content": query},
        ]


async def create_server() -> Server:
    """Create and configure the MCP server."""
    books_path = Path("books.json")
    library = LibraryManagement(books_path)
    
    server = Server("mcp-library")
    
    #### TOOLS ####
    @server.list_tools()
    async def list_tools() -> List[Tool]:
        """List all available tools for the library management system."""
        return [
            Tool(
                name="add_book",
                description="Add a book to the library",
                inputSchema={
                    "type": "object",
                    "required": ["title", "author", "isbn"],
                    "properties": {
                        "title": {
                            "description": "The title of the book",
                            "type": "string",
                        },
                        "author": {
                            "description": "The author of the book",
                            "type": "string",
                        },
                        "isbn": {
                            "description": "The ISBN of the book",
                            "type": "string",
                        },
                        "tags": {
                            "description": "Tags associated with the book",
                            "items": {"type": "string"},
                            "type": "array",
                        },
                    },
                },
            ),
            Tool(
                name="remove_book",
                description="Remove a book by its ISBN",
                inputSchema=BookISBNInput.model_json_schema(),
            ),
            Tool(
                name="get_num_books",
                description="Get the total number of books in the library",
                inputSchema={"type": "object", "properties": {}},
            ),
        ]
    
    @server.call_tool()
    async def call_tool(
        name: str, arguments: Dict
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
                
                case "get_num_books":
                    result = library.get_num_books()
                    return [TextContent(type="text", text=str(result))]
                
                case _:
                    raise ValueError(f"Unknown tool: {name}")
        
        except Exception as e:
            raise ValueError(f"LibraryServer Error: {str(e)}")
    
    #### RESOURCES ####
    @server.list_resources()
    async def list_resources() -> List[Resource]:
        """List all available static resources."""
        return [
            Resource(
                name="all_books",
                title="All Books",
                uri=AnyUrl("books://all"),
                description="Get all books in the library",
            ),
        ]
    
    @server.list_resource_templates()
    async def list_resource_templates() -> List[ResourceTemplate]:
        """List all available dynamic resource templates."""
        return [
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
    
    @server.read_resource()
    async def read_resource(uri: AnyUrl) -> str:
        """Read a resource by its URI."""
        uri_str = str(uri)
        
        if uri_str == "books://all":
            books = library.get_all_books()
            return json.dumps(books, indent=4, ensure_ascii=False)
        
        elif uri_str.startswith("books://index/"):
            index_str = uri_str.split("/")[-1]
            try:
                index = int(index_str)
                book = library.get_book_by_index(index)
                if "error" in book:
                    raise ValueError(book["error"])
                return json.dumps(book, indent=4, ensure_ascii=False)
            except ValueError as e:
                if "error" not in str(e):
                    raise ValueError(f"Invalid index: {index_str}")
                raise e
        
        elif uri_str.startswith("books://isbn/"):
            isbn = uri_str.split("/")[-1]
            book = library.get_book_by_isbn(isbn)
            if "error" in book:
                raise ValueError(book["error"])
            return json.dumps(book, indent=4, ensure_ascii=False)
        
        else:
            raise ValueError(f"Resource '{uri}' not found.")
    
    #### PROMPTS ####
    @server.list_prompts()
    async def list_prompts() -> List[Prompt]:
        """List all available prompts."""
        return [
            Prompt(
                name="suggest_random_book",
                description="Suggest a random book from the library. The suggestion should include the title, author, and a brief description.",
            ),
            Prompt(
                name="suggest_book_title_by_abstract",
                description="Suggest a memorable, descriptive title for a book based on the following abstract.",
                arguments=[
                    PromptArgument(
                        name="abstract",
                        description="The abstract of the book.",
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
                        description="The book to analyze.", 
                        required=True
                    ),
                    PromptArgument(
                        name="query",
                        description="The query for analysis.",
                        required=True,
                    ),
                ],
            ),
        ]
    
    @server.get_prompt()
    async def get_prompt(name: str, arguments: Dict[str, str] | None) -> GetPromptResult:
        """Get a specific prompt by name."""
        prompts = await list_prompts()
        
        # Find the prompt
        prompt = None
        for p in prompts:
            if p.name == name:
                prompt = p
                break
        
        if not prompt:
            raise ValueError(f"Prompt '{name}' not found.")
        
        # Validate arguments
        if arguments is None:
            arguments = {}
        
        if prompt.arguments:
            for arg in prompt.arguments:
                if arg.name not in arguments and arg.required:
                    raise ValueError(f"Missing required argument: {arg.name}")
        
        # Generate prompt content
        if name == "suggest_random_book":
            prompt_result = library.get_suggesting_random_book_prompt()
            return GetPromptResult(
                description=prompt.description,
                messages=[
                    PromptMessage(
                        role="user",
                        content=TextContent(type="text", text=prompt_result),
                    )
                ],
            )
        
        elif name == "suggest_book_title_by_abstract":
            prompt_result = library.get_suggesting_book_title_by_abstract_prompt(**arguments)
            return GetPromptResult(
                description=prompt.description,
                messages=[
                    PromptMessage(
                        role="user",
                        content=TextContent(type="text", text=prompt_result),
                    )
                ],
            )
        
        elif name == "analyze_book":
            book_str = arguments["book"]
            query = arguments["query"]
            try:
                book = json.loads(book_str)
            except json.JSONDecodeError:
                raise ValueError("Invalid book JSON format")
            
            messages = library.get_analyzing_book_messages(book, query)
            return GetPromptResult(
                description=prompt.description,
                messages=[
                    PromptMessage(
                        role=m["role"],
                        content=TextContent(type="text", text=m["content"]),
                    )
                    for m in messages
                ],
            )
        
        else:
            raise ValueError(f"Prompt '{name}' is not implemented.")
    
    return server


async def serve_stdio():
    """Serve using standard input/output transport."""
    server = await create_server()
    options = server.create_initialization_options()
    
    async with stdio_server() as (read_stream, write_stream):
        logger.info("MCP Library Server running with stdio transport")
        await server.run(read_stream, write_stream, options)


async def serve_http(port: int, transport: str, log_level: str):
    """Serve using streamable HTTP transport."""
    server = await create_server()
    
    session_manager = StreamableHTTPSessionManager(
        app=server,
        event_store=None,
        json_response=True if transport == "sse" else False,
        stateless=True,
    )
    
    async def handle_streamable_http(scope: Scope, receive: Receive, send: Send) -> None:
        """Handle HTTP requests with the session manager."""
        await session_manager.handle_request(scope, receive, send)
    
    @contextlib.asynccontextmanager
    async def lifespan(app: Starlette) -> AsyncIterator[None]:
        """Manage application lifecycle."""
        async with session_manager.run():
            logger.info(f"MCP Library Server started with {transport.upper()} transport on port {port}")
            try:
                yield
            finally:
                logger.info("MCP Library Server shutting down...")
    
    # Create ASGI application
    starlette_app = Starlette(
        debug=True,
        routes=[
            Mount("/mcp", app=handle_streamable_http),
        ],
        lifespan=lifespan,
    )
    
    # Run the server
    config = uvicorn.Config(
        starlette_app, 
        host="127.0.0.1", 
        port=port, 
        log_level=log_level.lower()
    )
    server = uvicorn.Server(config)
    await server.serve()


@click.command()
@click.option(
    "--log-level",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]),
    default="INFO",
    help="Set the logging level",
)
@click.option(
    "--transport",
    type=click.Choice(["stdio", "http", "sse"]),
    default="stdio",
    help="Transport mechanism to use",
)
@click.option(
    "--port",
    type=int,
    default=8000,
    help="Port for HTTP transport (ignored for stdio)",
)
def main(log_level: str, transport: str, port: int):
    """Run the Library MCP Server."""
    # Configure logging
    logging.getLogger().setLevel(getattr(logging, log_level))
    
    if transport == "stdio":
        asyncio.run(serve_stdio())
    else:
        asyncio.run(serve_http(port, transport, log_level))


if __name__ == "__main__":
    main()