import asyncio
import contextlib
import json
import logging
from collections.abc import AsyncIterator
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Sequence
from dataclasses import dataclass, asdict
import hashlib
import re

import click
import uvicorn
from mcp.server.lowlevel import Server
from mcp.server.stdio import stdio_server
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
from pydantic import BaseModel, Field, validator
from pydantic.networks import AnyUrl
from starlette.applications import Starlette
from starlette.routing import Mount
from starlette.types import Receive, Scope, Send


# Models with validation
class Book(BaseModel):
    title: str = Field(..., description="The title of the book", min_length=1)
    author: str = Field(..., description="The author of the book", min_length=1)
    isbn: str = Field(..., description="The ISBN of the book (10 or 13 digits)")
    tags: list[str] = Field(default_factory=list, description="Tags associated with the book")
    genre: Optional[str] = Field(None, description="Primary genre of the book")
    year_published: Optional[int] = Field(None, description="Year the book was published")
    rating: Optional[float] = Field(None, description="Book rating (1-5 stars)", ge=1, le=5)
    description: Optional[str] = Field(None, description="Book description/summary")
    pages: Optional[int] = Field(None, description="Number of pages", gt=0)
    language: str = Field(default="English", description="Book language")
    added_date: str = Field(default_factory=lambda: datetime.now().isoformat(), description="Date added to library")
    
    @validator('isbn')
    def validate_isbn(cls, v):
        # Remove hyphens and spaces
        isbn_clean = re.sub(r'[-\s]', '', v)
        if not re.match(r'^\d{10}(\d{3})?$', isbn_clean):
            raise ValueError('ISBN must be 10 or 13 digits')
        return isbn_clean
    
    @validator('tags')
    def validate_tags(cls, v):
        return [tag.strip().lower() for tag in v if tag.strip()]


class BookSearchInput(BaseModel):
    query: str = Field(..., description="Search query for books")
    search_type: str = Field(default="all", description="Search type: title, author, genre, tags, or all")
    limit: Optional[int] = Field(10, description="Maximum number of results", gt=0, le=100)


class BookUpdateInput(BaseModel):
    isbn: str = Field(..., description="The ISBN of the book to update")
    title: Optional[str] = None
    author: Optional[str] = None
    tags: Optional[list[str]] = None
    genre: Optional[str] = None
    year_published: Optional[int] = None
    rating: Optional[float] = Field(None, ge=1, le=5)
    description: Optional[str] = None
    pages: Optional[int] = Field(None, gt=0)
    language: Optional[str] = None


class LibraryStatsInput(BaseModel):
    group_by: str = Field(default="genre", description="Group statistics by: genre, author, year, language, or rating")


class BookRecommendationInput(BaseModel):
    based_on_isbn: Optional[str] = Field(None, description="ISBN of book to base recommendations on")
    preferred_genres: Optional[list[str]] = Field(None, description="Preferred genres")
    min_rating: Optional[float] = Field(None, description="Minimum rating", ge=1, le=5)
    exclude_read: bool = Field(False, description="Exclude books marked as read")


# Library Management with advanced features
class EnhancedLibraryManagement:
    def __init__(self, books_path: Path, backup_path: Optional[Path] = None):
        self.books_path = books_path
        self.backup_path = backup_path or books_path.with_suffix('.backup.json')
        
        if not books_path.exists():
            books_path.write_text("[]", encoding="utf-8")
        
        self.books = self._load_books()
        self.logger = logging.getLogger(__name__)
        
    def _load_books(self) -> list:
        """Load books with error handling and validation"""
        try:
            raw_data = json.loads(self.books_path.read_text(encoding="utf-8"))
            # Validate and migrate old format books
            validated_books = []
            for book_data in raw_data:
                try:
                    # Add default fields for backward compatibility
                    book_data.setdefault('genre', None)
                    book_data.setdefault('year_published', None)
                    book_data.setdefault('rating', None)
                    book_data.setdefault('description', None)
                    book_data.setdefault('pages', None)
                    book_data.setdefault('language', 'English')
                    book_data.setdefault('added_date', datetime.now().isoformat())
                    
                    validated_book = Book(**book_data)
                    validated_books.append(validated_book.dict())
                except Exception as e:
                    self.logger.warning(f"Skipping invalid book data: {e}")
            
            return validated_books
        except Exception as e:
            self.logger.error(f"Error loading books: {e}")
            return []

    def _backup_books(self):
        """Create backup before modifications"""
        try:
            if self.books_path.exists():
                self.backup_path.write_text(
                    self.books_path.read_text(encoding="utf-8"), 
                    encoding="utf-8"
                )
        except Exception as e:
            self.logger.warning(f"Backup failed: {e}")

    def save_books(self):
        """Save books with backup"""
        self._backup_books()
        try:
            self.books_path.write_text(
                json.dumps(self.books, indent=2, ensure_ascii=False), 
                encoding="utf-8"
            )
        except Exception as e:
            self.logger.error(f"Failed to save books: {e}")
            raise

    def add_book(self, book: Book) -> str:
        """Add book with validation"""
        if any(b["isbn"] == book.isbn for b in self.books):
            return f"Book with ISBN '{book.isbn}' already exists."

        book_dict = book.dict()
        self.books.append(book_dict)
        self.save_books()
        
        self.logger.info(f"Added book: {book.title} by {book.author}")
        return f"Book '{book.title}' by {book.author} successfully added to the library."

    def update_book(self, isbn: str, updates: BookUpdateInput) -> str:
        """Update book information"""
        book_index = None
        for i, book in enumerate(self.books):
            if book["isbn"] == isbn:
                book_index = i
                break
        
        if book_index is None:
            return f"No book found with ISBN '{isbn}'."
        
        # Apply updates
        update_dict = updates.dict(exclude_unset=True, exclude={'isbn'})
        for field, value in update_dict.items():
            if value is not None:
                self.books[book_index][field] = value
        
        self.save_books()
        return f"Book with ISBN '{isbn}' updated successfully."

    def search_books(self, query: str, search_type: str = "all", limit: int = 10) -> list:
        """Advanced search functionality"""
        query_lower = query.lower()
        results = []
        
        for book in self.books:
            match = False
            
            if search_type == "all":
                searchable_text = f"{book.get('title', '')} {book.get('author', '')} {book.get('genre', '')} {' '.join(book.get('tags', []))}"
                match = query_lower in searchable_text.lower()
            elif search_type == "title":
                match = query_lower in book.get('title', '').lower()
            elif search_type == "author":
                match = query_lower in book.get('author', '').lower()
            elif search_type == "genre":
                match = query_lower in book.get('genre', '').lower()
            elif search_type == "tags":
                match = any(query_lower in tag.lower() for tag in book.get('tags', []))
            
            if match:
                results.append(book)
                if len(results) >= limit:
                    break
        
        return results

    def get_library_statistics(self, group_by: str = "genre") -> dict:
        """Generate library statistics"""
        stats = {
            "total_books": len(self.books),
            "breakdown": {},
            "summary": {}
        }
        
        if not self.books:
            return stats
        
        # Group by specified field
        for book in self.books:
            key = book.get(group_by, "Unknown")
            if isinstance(key, list):  # For tags
                for item in key:
                    stats["breakdown"][item] = stats["breakdown"].get(item, 0) + 1
            else:
                stats["breakdown"][key] = stats["breakdown"].get(key, 0) + 1
        
        # Additional summary statistics
        ratings = [book.get('rating') for book in self.books if book.get('rating')]
        if ratings:
            stats["summary"]["average_rating"] = sum(ratings) / len(ratings)
            stats["summary"]["total_rated_books"] = len(ratings)
        
        pages = [book.get('pages') for book in self.books if book.get('pages')]
        if pages:
            stats["summary"]["total_pages"] = sum(pages)
            stats["summary"]["average_pages"] = sum(pages) / len(pages)
        
        return stats

    def get_recommendations(self, based_on_isbn: Optional[str] = None, 
                          preferred_genres: Optional[list[str]] = None,
                          min_rating: Optional[float] = None,
                          limit: int = 5) -> list:
        """Get book recommendations based on preferences"""
        candidates = []
        
        # If based on a specific book, find similar books
        if based_on_isbn:
            base_book = next((b for b in self.books if b["isbn"] == based_on_isbn), None)
            if base_book:
                base_tags = set(base_book.get('tags', []))
                base_genre = base_book.get('genre')
                
                for book in self.books:
                    if book["isbn"] == based_on_isbn:
                        continue
                    
                    similarity_score = 0
                    book_tags = set(book.get('tags', []))
                    
                    # Tag similarity
                    if base_tags and book_tags:
                        similarity_score += len(base_tags.intersection(book_tags)) / len(base_tags.union(book_tags))
                    
                    # Genre match
                    if base_genre and book.get('genre') == base_genre:
                        similarity_score += 0.5
                    
                    if similarity_score > 0:
                        candidates.append((book, similarity_score))
        else:
            # General recommendations based on preferences
            for book in self.books:
                score = 0
                
                if preferred_genres and book.get('genre') in preferred_genres:
                    score += 1
                
                if min_rating and book.get('rating') and book.get('rating') >= min_rating:
                    score += 0.5
                
                if score > 0:
                    candidates.append((book, score))
        
        # Sort by score and return top recommendations
        candidates.sort(key=lambda x: x[1], reverse=True)
        return [book for book, _ in candidates[:limit]]

    # Existing methods with improvements
    def remove_book(self, isbn: str) -> str:
        initial_count = len(self.books)
        self.books = [b for b in self.books if b["isbn"] != isbn.strip()]
        
        if len(self.books) == initial_count:
            return f"No book found with ISBN '{isbn}'."
        
        self.save_books()
        self.logger.info(f"Removed book with ISBN: {isbn}")
        return f"Book with ISBN '{isbn}' removed from the library."

    def get_num_books(self) -> int:
        return len(self.books)

    def get_all_books(self) -> list:
        return self.books

    def get_book_by_index(self, index: int) -> dict:
        if 0 <= index < len(self.books):
            return self.books[index]
        return {"error": "Book not found."}

    def get_book_by_isbn(self, isbn: str) -> dict:
        for book in self.books:
            if book["isbn"] == isbn.strip():
                return book
        return {"error": "Book not found."}

    # prompt methods
    def get_recommendation_prompt(self, preferences: dict) -> str:
        return f"""Based on the following library and preferences, recommend the best books:
        
Library Overview:
- Total books: {len(self.books)}
- Available genres: {list(set(book.get('genre') for book in self.books if book.get('genre')))}

User Preferences: {json.dumps(preferences, indent=2)}

Please provide personalized book recommendations with explanations."""

    def get_library_analysis_prompt(self) -> str:
        stats = self.get_library_statistics()
        return f"""Analyze this personal library and provide insights:

{json.dumps(stats, indent=2)}

Please provide:
1. Collection strengths and gaps
2. Reading pattern analysis  
3. Suggestions for diversifying the collection
4. Quality assessment based on ratings"""


@click.command()
@click.option("--log-level", default="INFO", help="Set the logging level")
@click.option("--transport", default="http", type=click.Choice(["http", "stdio", "sse"]))
@click.option("--port", default=8000, type=int, help="Port to run the HTTP server on")
@click.option("--books-file", default="books.json", help="Path to books JSON file")
def serve(log_level: str, transport: str, port: int, books_file: str) -> None:
    """Start the MCP Library Management Server"""
    
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    logger = logging.getLogger(__name__)

    books_path = Path(books_file)
    library = EnhancedLibraryManagement(books_path)

    server = Server("enhanced-mcp-library")

    #### TOOLS ####
    @server.list_tools()
    async def list_tools() -> list[Tool]:
        """List all available tools for the library management system."""
        return [
            Tool(
                name="add_book",
                description="Add a book to the library with full metadata",
                inputSchema=Book.schema(),
            ),
            Tool(
                name="update_book", 
                description="Update book information by ISBN",
                inputSchema=BookUpdateInput.schema(),
            ),
            Tool(
                name="remove_book",
                description="Remove a book by its ISBN",
                inputSchema={"type": "object", "properties": {"isbn": {"type": "string"}}, "required": ["isbn"]},
            ),
            Tool(
                name="search_books",
                description="Search books by title, author, genre, or tags",
                inputSchema=BookSearchInput.schema(),
            ),
            Tool(
                name="get_statistics",
                description="Get library statistics grouped by various fields",
                inputSchema=LibraryStatsInput.schema(),
            ),
            Tool(
                name="get_recommendations",
                description="Get personalized book recommendations",
                inputSchema=BookRecommendationInput.schema(),
            ),
            Tool(
                name="get_num_books",
                description="Get the total number of books",
                inputSchema={"type": "object", "properties": {}},
            ),
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
        """tool calling with better error handling"""
        try:
            match name:
                case "add_book":
                    book = Book(**arguments)
                    result = library.add_book(book)
                    return [TextContent(type="text", text=result)]

                case "update_book":
                    updates = BookUpdateInput(**arguments)
                    result = library.update_book(updates.isbn, updates)
                    return [TextContent(type="text", text=result)]

                case "remove_book":
                    result = library.remove_book(arguments["isbn"])
                    return [TextContent(type="text", text=result)]

                case "search_books":
                    search_input = BookSearchInput(**arguments)
                    results = library.search_books(
                        search_input.query, 
                        search_input.search_type, 
                        search_input.limit
                    )
                    return [TextContent(type="text", text=json.dumps(results, indent=2, ensure_ascii=False))]

                case "get_statistics":
                    stats_input = LibraryStatsInput(**arguments)
                    stats = library.get_library_statistics(stats_input.group_by)
                    return [TextContent(type="text", text=json.dumps(stats, indent=2, ensure_ascii=False))]

                case "get_recommendations":
                    rec_input = BookRecommendationInput(**arguments)
                    recommendations = library.get_recommendations(
                        rec_input.based_on_isbn,
                        rec_input.preferred_genres,
                        rec_input.min_rating
                    )
                    return [TextContent(type="text", text=json.dumps(recommendations, indent=2, ensure_ascii=False))]

                case "get_num_books":
                    result = library.get_num_books()
                    return [TextContent(type="text", text=str(result))]

                case _:
                    raise ValueError(f"Unknown tool: {name}")

        except Exception as e:
            logger.error(f"Tool execution error: {str(e)}")
            return [TextContent(type="text", text=f"Error: {str(e)}")]

    # resources and prompts remain similar but with new functionality
    @server.list_resources()
    async def list_resources() -> list[Resource]:
        return [
            Resource(
                name="all_books",
                title="All Books", 
                uri=AnyUrl("books://all"),
                description="Get all books in the library with full metadata"
            ),
            Resource(
                name="library_stats",
                title="Library Statistics",
                uri=AnyUrl("books://stats"),
                description="Get comprehensive library statistics"
            ),
        ]

    @server.read_resource()
    async def read_resource(uri: AnyUrl) -> str:
        uri_str = str(uri)
        if uri_str == "books://all":
            books = library.get_all_books()
            return json.dumps(books, indent=2, ensure_ascii=False)
        elif uri_str == "books://stats":
            stats = library.get_library_statistics()
            return json.dumps(stats, indent=2, ensure_ascii=False)
        elif uri_str.startswith("books://isbn/"):
            isbn = uri_str.split("/")[-1]
            book = library.get_book_by_isbn(isbn)
            if "error" in book:
                raise ValueError(book["error"])
            return json.dumps(book, indent=2, ensure_ascii=False)
        else:
            raise ValueError(f"Resource '{uri}' not found.")

    #### Start server ####
    logger.info("🚀 Launching MCP Library Server...")

    if transport == "stdio":
        async def arun_stdio_server():
            logger.info("Starting MCP server with stdio transport...")
            options = server.create_initialization_options()
            async with stdio_server() as (read_stream, write_stream):
                await server.run(read_stream, write_stream, options)

        asyncio.run(arun_stdio_server())

    elif transport in ["http", "sse"]:
        session_manager = StreamableHTTPSessionManager(
            app=server,
            event_store=None,
            json_response=(transport == "http"),
            stateless=True,
        )

        async def handle_streamable_http(scope: Scope, receive: Receive, send: Send) -> None:
            await session_manager.handle_request(scope, receive, send)

        @contextlib.asynccontextmanager
        async def lifespan(app: Starlette) -> AsyncIterator[None]:
            async with session_manager.run():
                logger.info("MCP Library Server started!")
                try:
                    yield
                finally:
                    logger.info("Server shutting down...")

        starlette_app = Starlette(
            routes=[Mount("/mcp", app=handle_streamable_http)],
            lifespan=lifespan,
        )

        uvicorn.run(starlette_app, host="127.0.0.1", port=port, log_level=log_level.lower())

    else:
        raise ValueError(f"Unsupported transport type: {transport}")


if __name__ == "__main__":
    serve()