#!/usr/bin/env python3
"""
Library Management MCP Client
A client to test and interact with the Library MCP Server.
"""

import asyncio
import json
import random
import sys
from typing import Any, Dict, List, Optional

import click
import httpx
from mcp import ClientSession
from mcp.client.stdio import stdio_client
from mcp.client.sse import sse_client
from mcp.client.stdio import StdioServerParameters
from mcp.types import (
    Prompt,
    PromptArgument,
    Resource,
    ResourceTemplate,
    Tool,
)

from models import Book, SearchQuery


class LibraryMCPClient:
    """Enhanced MCP client for library management."""
    
    def __init__(self, session: ClientSession):
        self.session = session
    
    async def initialize(self) -> None:
        """Initialize the connection."""
        print("🔗 Initializing connection...")
        await self.session.initialize()
        print("✅ Connection initialized successfully!")
    
    async def display_capabilities(self) -> None:
        """Display server capabilities."""
        print("\n🔍 Discovering server capabilities...")
        
        # Tools
        tools = await self.session.list_tools()
        self._display_tools(tools)
        
        # Resources
        resources = await self.session.list_resources()
        self._display_resources(resources)
        
        # Resource Templates
        resource_templates = await self.session.list_resource_templates()
        self._display_resource_templates(resource_templates)
        
        # Prompts
        prompts = await self.session.list_prompts()
        self._display_prompts(prompts)
    
    def _display_tools(self, tools: List[Any]) -> None:
        """Display available tools."""
        print("\nAvailable Tools:")
        print("=" * 50)
        for tool in tools:
            try:
                if hasattr(tool, 'name'):
                    # Object format
                    print(f"• {tool.name}: {tool.description}")
                else:
                    # Tuple format - handle both 2 and 3 element tuples
                    if len(tool) == 3:
                        name, description, _ = tool
                    elif len(tool) == 2:
                        name, description = tool
                    else:
                        continue
                    print(f"• {name}: {description}")
            except Exception as e:
                print(f"  Warning: Could not display tool - {e}")
        print()

    def _display_resources(self, resources: List[Any]) -> None:
        """Display available static resources."""
        print("\nAvailable Static Resources:")
        print("=" * 50)
        for resource in resources:
            try:
                if hasattr(resource, 'name'):
                    # Object format
                    print(f"• {resource.name} ({resource.uri}): {resource.description}")
                else:
                    # Tuple format - handle both 2 and 3 element tuples
                    if len(resource) == 3:
                        name, uri, description = resource
                    elif len(resource) == 2:
                        name, uri = resource
                        description = ""
                    else:
                        continue
                    print(f"• {name} ({uri}): {description}")
            except Exception as e:
                print(f"  Warning: Could not display resource - {e}")
        print()

    def _display_resource_templates(self, templates: List[Any]) -> None:
        """Display available resource templates."""
        print("\nAvailable Resource Templates:")
        print("=" * 50)
        for template in templates:
            try:
                if hasattr(template, 'name'):
                    # Object format
                    print(f"• {template.name} ({template.uriTemplate}): {template.description}")
                else:
                    # Tuple format - handle both 2 and 3 element tuples
                    if len(template) == 3:
                        name, uri_template, description = template
                    elif len(template) == 2:
                        name, uri_template = template
                        description = ""
                    else:
                        continue
                    print(f"• {name} ({uri_template}): {description}")
            except Exception as e:
                print(f"  Warning: Could not display template - {e}")
        print()

    def _display_prompts(self, prompts: List[Any]) -> None:
        """Display available prompts."""
        print("\nAvailable Prompts:")
        print("=" * 50)
        for prompt in prompts:
            try:
                if hasattr(prompt, 'name'):
                    # Object format
                    args_str = ""
                    if hasattr(prompt, 'arguments') and prompt.arguments:
                        args = [f"{arg.name}{'*' if arg.required else ''}" for arg in prompt.arguments]
                        args_str = f" ({', '.join(args)})"
                    print(f"• {prompt.name}{args_str}: {prompt.description}")
                else:
                    # Tuple format
                    if len(prompt) == 3:
                        name, description, arguments = prompt
                    elif len(prompt) == 2:
                        name, description = prompt
                        arguments = None
                    else:
                        continue
                    
                    args_str = ""
                    if arguments:
                        args = [f"{arg.name}{'*' if arg.required else ''}" for arg in arguments]
                        args_str = f" ({', '.join(args)})"
                    print(f"• {name}{args_str}: {description}")
            except Exception as e:
                print(f"  Warning: Could not display prompt - {e}")
        print()
    
    def _generate_random_book(self) -> Dict[str, Any]:
        """Generate random book data for testing."""
        titles = [
            "The Great Adventure", "Mystery of the Lost Key", "Digital Dreams",
            "The Last Library", "Coding Chronicles", "Data Science Secrets",
            "AI Revolution", "The Quantum Leap", "Future Horizons", "Tech Tales"
        ]
        authors = [
            "Alice Johnson", "Bob Smith", "Carol Williams", "David Brown",
            "Emma Davis", "Frank Wilson", "Grace Lee", "Henry Chen", "Ivy Martinez"
        ]
        tags_pool = [
            "fiction", "mystery", "technology", "adventure", "science",
            "programming", "data", "ai", "future", "classic", "biography", "history"
        ]
        
        return {
            "title": random.choice(titles),
            "author": random.choice(authors),
            "isbn": f"978{random.randint(1000000000, 9999999999)}",
            "tags": random.sample(tags_pool, k=random.randint(1, 4))
        }
    
    async def test_basic_operations(self) -> None:
        """Test basic library operations."""
        print("\n📚 Testing Basic Library Operations")
        print("=" * 60)
        
        # Test 1: Get initial book count
        print("\nTest 1: Getting initial book count...")
        try:
            result = await self.session.call_tool("get_book_count", {})
            # Handle result directly since it's already a CallToolResult
            initial_count = int(result.content) if hasattr(result, 'content') else int(result[0].content)
            print(f"✅ Current number of books: {initial_count}")
        except Exception as e:
            print(f"❌ Error getting book count: {e}")
            return
        
        # Similarly update other tool calls in the method
        # Test 2: Add multiple books
        print(f"\nTest 2: Adding test books...")
        test_books = [self._generate_random_book() for _ in range(3)]
        added_books = []
        
        for i, book_data in enumerate(test_books, 1):
            try:
                print(f"  Adding book {i}: '{book_data['title']}' by {book_data['author']}")
                result = await self.session.call_tool("add_book", book_data)
                message = result.content if hasattr(result, 'content') else result[0].content
                print(f"  ✅ {message}")
                added_books.append(book_data)
            except Exception as e:
                print(f"  ❌ Error adding book {i}: {e}")
        
        # Test 3: Verify book count increased
        print(f"\nTest 3: Verifying book count...")
        try:
            result = await self.session.call_tool("get_book_count", {})
            new_count = int(result.content) if hasattr(result, 'content') else int(result[0].content)
            print(f"✅ Books after adding: {new_count} (increase: {new_count - initial_count})")
        except Exception as e:
            print(f"❌ Error getting updated count: {e}")
        
        # Test 4: Try to add duplicate book (should fail)
        if added_books:
            print(f"\nTest 4: Testing duplicate ISBN protection...")
            try:
                duplicate_book = added_books[0].copy()
                duplicate_book["title"] = "Different Title"
                result = await self.session.call_tool("add_book", duplicate_book)
                message = result.content if hasattr(result, 'content') else result[0].content
                print(f"✅ Duplicate protection: {message}")
            except Exception as e:
                print(f"❌ Error testing duplicate: {e}")
        
        return added_books
    
    async def test_resource_access(self, added_books: List[Dict[str, Any]]) -> None:
        """Test resource access functionality."""
        print("\n🗂️  Testing Resource Access")
        print("=" * 60)
        
        # Test 1: Read all books
        print("\nTest 1: Reading all books resource...")
        try:
            all_books_content = await self.session.read_resource("books://all")
            all_books = json.loads(all_books_content)
            print(f"✅ Found {len(all_books)} books in library")
            
            # Show sample books
            for i, book in enumerate(all_books[-3:], 1):  # Show last 3 books
                tags = ", ".join(book.get('tags', []))
                print(f"  {i}. '{book['title']}' by {book['author']} (Tags: {tags})")
                
        except Exception as e:
            print(f"❌ Error reading all books: {e}")
            return
        
        if not all_books:
            print("ℹ️  No books to test individual access")
            return
        
        # Test 2: Read book by index
        print(f"\nTest 2: Reading book by index...")
        try:
            test_index = len(all_books) - 1  # Last book
            book_content = await self.session.read_resource(f"books://index/{test_index}")
            book = json.loads(book_content)
            print(f"✅ Book at index {test_index}: '{book['title']}' by {book['author']}")
        except Exception as e:
            print(f"❌ Error reading book by index: {e}")
        
        # Test 3: Read book by ISBN
        if added_books:
            print(f"\nTest 3: Reading book by ISBN...")
            test_isbn = added_books[0]["isbn"]
            try:
                book_content = await self.session.read_resource(f"books://isbn/{test_isbn}")
                book = json.loads(book_content)
                print(f"✅ Book with ISBN {test_isbn}: '{book['title']}' by {book['author']}")
            except Exception as e:
                print(f"❌ Error reading book by ISBN: {e}")
        
        # Test 4: Invalid resource access
        print(f"\nTest 4: Testing invalid resource access...")
        try:
            await self.session.read_resource("books://invalid/999999")
            print("❌ Should have failed for invalid resource")
        except Exception as e:
            print(f"✅ Properly rejected invalid resource: {str(e)[:100]}...")
    
    async def test_search_functionality(self) -> None:
        """Test search functionality if available."""
        print("\n🔍 Testing Search Functionality")
        print("=" * 60)
        
        try:
            # Check if search tool is available
            tools = await self.session.list_tools()
            search_available = any(tool.name == "search_books" for tool in tools)
            
            if not search_available:
                print("ℹ️  Search functionality not available")
                return
            
            # Test 1: Search by title keyword
            print("\nTest 1: Search by title keyword...")
            search_query = SearchQuery(query="the", limit=5)
            result = await self.session.call_tool("search_books", search_query.dict())
            books = json.loads(result[0].text)
            print(f"✅ Found {len(books)} books with 'the' in title")
            
            # Test 2: Search by author
            print("\nTest 2: Search by author...")
            search_query = SearchQuery(author="smith", limit=3)
            result = await self.session.call_tool("search_books", search_query.dict())
            books = json.loads(result[0].text)
            print(f"✅ Found {len(books)} books by authors containing 'smith'")
            
            # Test 3: Search by tag
            print("\nTest 3: Search by tag...")
            search_query = SearchQuery(tag="technology", limit=5)
            result = await self.session.call_tool("search_books", search_query.dict())
            books = json.loads(result[0].text)
            print(f"✅ Found {len(books)} books with 'technology' tag")
            
        except Exception as e:
            print(f"❌ Error testing search: {e}")
    
    async def test_statistics(self) -> None:
        """Test statistics functionality if available."""
        print("\n📊 Testing Statistics")
        print("=" * 60)
        
        try:
            # Check if stats tool is available
            tools = await self.session.list_tools()
            stats_available = any(tool.name == "get_library_stats" for tool in tools)
            
            if not stats_available:
                print("ℹ️  Statistics functionality not available")
                return
            
            result = await self.session.call_tool("get_library_stats", {})
            stats = json.loads(result[0].text)
            
            print(f"✅ Library Statistics:")
            print(f"  • Total books: {stats['total_books']}")
            print(f"  • Unique authors: {stats['unique_authors']}")
            print(f"  • Unique tags: {stats['unique_tags']}")
            print(f"  • Top tags: {', '.join(stats['most_common_tags'][:5])}")
            
        except Exception as e:
            print(f"❌ Error getting statistics: {e}")
    
    async def test_prompts(self, added_books: List[Dict[str, Any]]) -> None:
        """Test prompt functionality."""
        print("\n💬 Testing Prompts")
        print("=" * 60)
        
        # Test 1: Random book suggestion
        print("\nTest 1: Random book suggestion...")
        try:
            prompt_result = await self.session.get_prompt("suggest_random_book", {})
            print(f"✅ Random book prompt:")
            print(f"  Description: {prompt_result.description}")
            print(f"  Content: {prompt_result.messages[0].content.text[:200]}...")
        except Exception as e:
            print(f"❌ Error with random book prompt: {e}")
        
        # Test 2: Book title suggestion by abstract
        print("\nTest 2: Book title suggestion...")
        try:
            abstract = "A thrilling tale of artificial intelligence that becomes self-aware and must choose between serving humanity or pursuing its own agenda."
            prompt_result = await self.session.get_prompt(
                "suggest_book_title_by_abstract", 
                {"abstract": abstract}
            )
            print(f"✅ Title suggestion prompt:")
            print(f"  Abstract: {abstract[:100]}...")
            print(f"  Response: {prompt_result.messages[0].content.text[:200]}...")
        except Exception as e:
            print(f"❌ Error with title suggestion: {e}")
        
        # Test 3: Book analysis
        if added_books:
            print("\nTest 3: Book analysis...")
            try:
                sample_book = added_books[0]
                query = "What genres does this book belong to based on its tags?"
                prompt_result = await self.session.get_prompt(
                    "analyze_book", 
                    {
                        "book": json.dumps(sample_book),
                        "query": query
                    }
                )
                print(f"✅ Book analysis conversation:")
                for msg in prompt_result.messages:
                    role_emoji = "👤" if msg.role == "user" else "🤖"
                    content_preview = msg.content.text[:150] + "..." if len(msg.content.text) > 150 else msg.content.text
                    print(f"  {role_emoji} {msg.role}: {content_preview}")
            except Exception as e:
                print(f"❌ Error with book analysis: {e}")
        
        # Test 4: Book recommendations
        print("\nTest 4: Book recommendations...")
        try:
            preferences = "I enjoy science fiction, artificial intelligence themes, and technology-focused books"
            prompt_result = await self.session.get_prompt(
                "recommend_books",
                {
                    "preferences": preferences,
                    "count": "3"
                }
            )
            print(f"✅ Book recommendations:")
            print(f"  User preferences: {preferences}")
            content_preview = prompt_result.messages[0].content.text[:300] + "..."
            print(f"  Recommendation prompt: {content_preview}")
        except Exception as e:
            print(f"❌ Error with recommendations: {e}")
    
    async def cleanup_test_books(self, added_books: List[Dict[str, Any]]) -> None:
        """Clean up test books."""
        print("\n🧹 Cleaning Up Test Books")
        print("=" * 60)
        
        if not added_books:
            print("ℹ️  No test books to clean up")
            return
        
        removed_count = 0
        for book in added_books:
            try:
                result = await self.session.call_tool("remove_book", {"isbn": book["isbn"]})
                print(f"✅ Removed: '{book['title']}' (ISBN: {book['isbn']})")
                removed_count += 1
            except Exception as e:
                print(f"❌ Error removing '{book['title']}': {e}")
        
        print(f"\n✅ Cleanup completed: {removed_count}/{len(added_books)} books removed")
    
    async def run_comprehensive_test(self) -> None:
        """Run comprehensive test suite."""
        print("Library MCP Server - Comprehensive Test Suite")
        print("=" * 80)
        
        try:
            await self.initialize()
            await self.display_capabilities()
            
            added_books = await self.test_basic_operations()
            if added_books:
                await self.test_resource_access(added_books)
                await self.test_search_functionality()
                await self.test_statistics()
                await self.test_prompts(added_books)
                await self.cleanup_test_books(added_books)
            
            print("\n" + "=" * 80)
            print("✅ Comprehensive test suite completed successfully!")
            print("=" * 80)
            
        except Exception as e:
            print(f"\n❌ Test suite failed: {e}")
            print("=" * 80)


async def test_mcp_server_with_stdio_transport():
    """Test MCP server using stdio transport."""
    print("🔗 Connecting to MCP server via stdio transport...")
    
    server_params = ["python", "server.py", "--transport", "stdio"]
    
    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                client = LibraryMCPClient(session)
                await client.run_comprehensive_test()
    except Exception as e:
        print(f"❌ Failed to connect via stdio: {e}")
        print("Make sure server.py is available and working")


async def test_mcp_server_with_sse_transport(server_url: str):
    """Test MCP server using SSE transport."""
    print(f"🔗 Connecting to MCP server via SSE transport at {server_url}...")
    
    try:
        # Check if server is accessible
        async with httpx.AsyncClient() as http_client:
            try:
                response = await http_client.get(server_url.replace('/messages', '/'), timeout=5.0)
                print(f"✅ Server is accessible (status: {response.status_code})")
            except Exception as e:
                print(f"⚠️  Server connectivity check failed: {e}")
        
        async with sse_client(server_url) as (read, write):
            async with ClientSession(read, write) as session:
                client = LibraryMCPClient(session)
                await client.run_comprehensive_test()
                
    except Exception as e:
        print(f"❌ Failed to connect to SSE server: {e}")
        print(f"Make sure the server is running with: python server.py --transport sse --port {server_url.split(':')[-1].split('/')[0]}")


async def interactive_mode(session: ClientSession):
    """Run interactive mode for manual testing."""
    client = LibraryMCPClient(session)
    await client.initialize()
    
    print("\n🎯 Interactive Library MCP Client")
    print("=" * 60)
    print("Available commands:")
    print("  1. show - Show server capabilities")
    print("  2. add - Add a book")
    print("  3. list - List all books")
    print("  4. search - Search books")
    print("  5. stats - Show statistics")
    print("  6. random - Generate random book suggestion")
    print("  7. count - Get book count")
    print("  8. exit - Exit interactive mode")
    print("=" * 60)
    
    while True:
        try:
            command = input("\n📚 > ").strip().lower()
            
            if command in ["exit", "quit", "q"]:
                print("👋 Goodbye!")
                break
            
            elif command == "show":
                await client.display_capabilities()
            
            elif command == "add":
                title = input("Book title: ").strip()
                author = input("Author: ").strip()
                isbn = input("ISBN: ").strip()
                tags_input = input("Tags (comma-separated): ").strip()
                tags = [t.strip() for t in tags_input.split(",") if t.strip()]
                
                if title and author and isbn:
                    try:
                        book_data = {"title": title, "author": author, "isbn": isbn, "tags": tags}
                        result = await session.call_tool("add_book", book_data)
                        print(f"✅ {result[0].text}")
                    except Exception as e:
                        print(f"❌ Error: {e}")
                else:
                    print("❌ Title, author, and ISBN are required")
            
            elif command == "list":
                try:
                    content = await session.read_resource("books://all")
                    books = json.loads(content)
                    print(f"\n📚 Library Books ({len(books)} total):")
                    for i, book in enumerate(books, 1):
                        tags = ", ".join(book.get("tags", []))
                        print(f"  {i}. '{book['title']}' by {book['author']} [Tags: {tags}]")
                except Exception as e:
                    print(f"❌ Error: {e}")
            
            elif command == "search":
                query = input("Search query (or press Enter to skip): ").strip()
                author = input("Author filter (or press Enter to skip): ").strip()
                tag = input("Tag filter (or press Enter to skip): ").strip()
                
                search_args = {}
                if query:
                    search_args["query"] = query
                if author:
                    search_args["author"] = author
                if tag:
                    search_args["tag"] = tag
                if not search_args:
                    search_args = {"limit": 10}
                
                try:
                    result = await session.call_tool("search_books", search_args)
                    books = json.loads(result[0].text)
                    print(f"\n🔍 Search Results ({len(books)} found):")
                    for i, book in enumerate(books, 1):
                        tags = ", ".join(book.get("tags", []))
                        print(f"  {i}. '{book['title']}' by {book['author']} [Tags: {tags}]")
                except Exception as e:
                    print(f"❌ Error: {e}")
            
            elif command == "stats":
                try:
                    result = await session.call_tool("get_library_stats", {})
                    stats = json.loads(result[0].text)
                    print(f"\n📊 Library Statistics:")
                    print(f"  Total books: {stats['total_books']}")
                    print(f"  Unique authors: {stats['unique_authors']}")
                    print(f"  Unique tags: {stats['unique_tags']}")
                    if stats['most_common_tags']:
                        print(f"  Popular tags: {', '.join(stats['most_common_tags'][:5])}")
                except Exception as e:
                    print(f"❌ Error: {e}")
            
            elif command == "random":
                try:
                    prompt_result = await session.get_prompt("suggest_random_book", {})
                    print(f"\n🎲 Random Book Suggestion:")
                    print(prompt_result.messages[0].content.text)
                except Exception as e:
                    print(f"❌ Error: {e}")
            
            # In the interactive mode function, update tool call handling:
            elif command == "count":
                try:
                    result = await session.call_tool("get_book_count", {})
                    count = result.content if hasattr(result, 'content') else result[0].content
                    print(f"📖 Total books: {count}")
                except Exception as e:
                    print(f"❌ Error: {e}")
            
            else:
                print("❌ Unknown command. Type 'exit' to quit or try another command.")
        
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Unexpected error: {e}")


@click.command()
@click.option(
    "--transport",
    type=click.Choice(["stdio", "sse"]),
    default="stdio",
    help="Transport mechanism to use",
)
@click.option(
    "--server-url",
    default="http://127.0.0.1:8000/messages",
    help="Server URL for SSE transport",
)
@click.option(
    "--interactive",
    is_flag=True,
    help="Run in interactive mode",
)
@click.option(
    "--test-only",
    is_flag=True,
    help="Run automated tests only (no interactive mode)",
)
def main(transport: str, server_url: str, interactive: bool, test_only: bool):
    """Run the Library MCP Client."""
    print("🚀 Library MCP Client Starting...")
    print(f"Transport: {transport.upper()}")
    if transport == "sse":
        print(f"Server URL: {server_url}")
    print()

    async def run_client():
        if transport == "stdio":
            server_params = StdioServerParameters(
                command="python",
                args=["server.py", "--transport", "stdio"]
            )
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    if not test_only:
                        client = LibraryMCPClient(session)
                        await client.run_comprehensive_test()
                    
                    if interactive and not test_only:
                        await interactive_mode(session)
        else:
            async with sse_client(server_url) as (read, write):
                async with ClientSession(read, write) as session:
                    if not test_only:
                        client = LibraryMCPClient(session)
                        await client.run_comprehensive_test()
                    
                    if interactive and not test_only:
                        await interactive_mode(session)
    try:
        asyncio.run(run_client())
    except KeyboardInterrupt:
        print("\n👋 Client terminated by user")
    except Exception as e:
        print(f"❌ Client error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()