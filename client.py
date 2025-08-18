#!/usr/bin/env python3
"""
Library Management MCP Client
A client to test and interact with the Library MCP Server.
"""

import asyncio
import json
import random
from typing import Any, Dict, List

import click
from mcp import ClientSession
from mcp.client.stdio import stdio_client
# from mcp.client.streamablehttp import streamablehttp_client
from mcp_streamablehttp_client import streamablehttp_client



def display_tools(tools: List[Any]) -> None:
    """Display available tools."""
    print("\nAvailable Tools:")
    print("=" * 50)
    for tool in tools:
        print(f"• {tool.name}: {tool.description}")
    print()


def display_resources(resources: List[Any]) -> None:
    """Display available static resources."""
    print("\nAvailable Static Resources:")
    print("=" * 50)
    for resource in resources:
        print(f"• {resource.name} ({resource.uri}): {resource.description}")
    print()


def display_resource_templates(templates: List[Any]) -> None:
    """Display available resource templates."""
    print("\nAvailable Resource Templates:")
    print("=" * 50)
    for template in templates:
        print(f"• {template.name} ({template.uriTemplate}): {template.description}")
    print()


def display_prompts(prompts: List[Any]) -> None:
    """Display available prompts."""
    print("\nAvailable Prompts:")
    print("=" * 50)
    for prompt in prompts:
        args_str = ""
        if prompt.arguments:
            args = [f"{arg.name}{'*' if arg.required else ''}" for arg in prompt.arguments]
            args_str = f" ({', '.join(args)})"
        print(f"• {prompt.name}{args_str}: {prompt.description}")
    print()


def generate_random_book() -> Dict[str, Any]:
    """Generate random book data for testing."""
    titles = [
        "The Great Adventure", "Mystery of the Lost Key", "Digital Dreams",
        "The Last Library", "Coding Chronicles", "Data Science Secrets"
    ]
    authors = [
        "Alice Johnson", "Bob Smith", "Carol Williams", "David Brown",
        "Emma Davis", "Frank Wilson"
    ]
    tags_pool = [
        "fiction", "mystery", "technology", "adventure", "science",
        "programming", "data", "ai", "future", "classic"
    ]
    
    return {
        "title": random.choice(titles),
        "author": random.choice(authors),
        "isbn": f"978-{random.randint(1000000000, 9999999999)}",
        "tags": random.sample(tags_pool, k=random.randint(1, 3))
    }


async def test_book_library_management_mcp_server(session: ClientSession) -> None:
    """Test the book library management MCP server functionality."""
    print("\nStarting Library MCP Server Test")
    print("=" * 60)
    
    # Initialize the connection
    print("🔗 Initializing connection...")
    await session.initialize()
    print("✅ Connection initialized successfully!")
    
    # List and display server capabilities
    print("\n🔍 Discovering server capabilities...")
    
    tools = await session.list_tools()
    display_tools(tools)
    
    resources = await session.list_resources()
    display_resources(resources)
    
    resource_templates = await session.list_resource_templates()
    display_resource_templates(resource_templates)
    
    prompts = await session.list_prompts()
    display_prompts(prompts)
    
    # Test 1: Get initial book count
    print("\nTest 1: Getting initial book count...")
    result = await session.call_tool("get_num_books", {})
    initial_count = int(result[0].text)
    print(f"Current number of books: {initial_count}")
    
    # Test 2: Read all books resource
    print("\nTest 2: Reading all books resource...")
    try:
        all_books_content = await session.read_resource("books://all")
        all_books = json.loads(all_books_content)
        print(f"Found {len(all_books)} books in library:")
        for i, book in enumerate(all_books[:3]):  # Show first 3 books
            print(f"  {i+1}. '{book['title']}' by {book['author']} (ISBN: {book['isbn']})")
        if len(all_books) > 3:
            print(f"  ... and {len(all_books) - 3} more books")
    except Exception as e:
        print(f"No books in library yet: {e}")
        all_books = []
    
    # Test 3: Add a new book
    print("\nTest 3: Adding a new book...")
    test_book = generate_random_book()
    print(f"Adding book: '{test_book['title']}' by {test_book['author']}")
    result = await session.call_tool("add_book", test_book)
    print(f"{result[0].text}")
    
    # Test 4: Check book count after adding
    print("\nTest 4: Checking book count after adding...")
    result = await session.call_tool("get_num_books", {})
    new_count = int(result[0].text)
    print(f"Number of books after adding: {new_count}")
    print(f"Books added: {new_count - initial_count}")

    # Test 5: Read book by index
    if new_count > 0:
        print(f"\nTest 5: Reading book by index (index: {new_count - 1})...")
        try:
            book_content = await session.read_resource(f"books://index/{new_count - 1}")
            book = json.loads(book_content)
            print(f"Book found: '{book['title']}' by {book['author']}")
            print(f"Tags: {', '.join(book['tags']) if book['tags'] else 'None'}")
        except Exception as e:
            print(f"Error reading book by index: {e}")
    
    # Test 6: Read book by ISBN
    print(f"\nTest 6: Reading book by ISBN ({test_book['isbn']})...")
    try:
        book_content = await session.read_resource(f"books://isbn/{test_book['isbn']}")
        book = json.loads(book_content)
        print(f"Book found: '{book['title']}' by {book['author']}")
        print(f"ISBN: {book['isbn']}")
    except Exception as e:
        print(f"Error reading book by ISBN: {e}")
    
    # Test 7: Remove the book
    print(f"\nTest 7: Removing book with ISBN {test_book['isbn']}...")
    result = await session.call_tool("remove_book", {"isbn": test_book['isbn']})
    print(f"{result[0].text}")
    
    # Test 8: Check book count after removal
    print("\nTest 8: Checking book count after removal...")
    result = await session.call_tool("get_num_books", {})
    final_count = int(result[0].text)
    print(f"Final number of books: {final_count}")
    print(f"Books removed: {new_count - final_count}")
    
    # Test 9: Test static prompt
    print("\nTest 9: Testing static prompt (suggest_random_book)...")
    try:
        prompt_result = await session.get_prompt("suggest_random_book", {})
        print(f"Prompt description: {prompt_result.description}")
        print(f"Prompt content: {prompt_result.messages[0].content.text}")
    except Exception as e:
        print(f"Error getting static prompt: {e}")

    # Test 10: Test dynamic prompt with abstract
    print("\nTest 10: Testing dynamic prompt (suggest_book_title_by_abstract)...")
    try:
        abstract = "A thrilling story about artificial intelligence taking over the world and the humans who fight back."
        prompt_result = await session.get_prompt(
            "suggest_book_title_by_abstract", 
            {"abstract": abstract}
        )
        print(f"Abstract: {abstract}")
        print(f"Prompt content: {prompt_result.messages[0].content.text}")
    except Exception as e:
        print(f"Error getting dynamic prompt: {e}")

    # Test 11: Test book analysis prompt
    print("\nTest 11: Testing book analysis prompt...")
    try:
        sample_book = {
            "title": "The Art of Programming", 
            "author": "Jane Doe", 
            "isbn": "978-1234567890",
            "tags": ["programming", "computer science", "education"]
        }
        query = "What are the main themes of this book?"
        prompt_result = await session.get_prompt(
            "analyze_book", 
            {
                "book": json.dumps(sample_book),
                "query": query
            }
        )
        print(f"Book: {sample_book['title']} by {sample_book['author']}")
        print(f"Query: {query}")
        print(f"Analysis conversation:")
        for i, message in enumerate(prompt_result.messages):
            role_emoji = "👤" if message.role == "user" else "🤖"
            print(f"   {role_emoji} {message.role}: {message.content.text}")
    except Exception as e:
        print(f"Error getting analysis prompt: {e}")

    print("\nLibrary MCP Server test completed!")
    print("=" * 60)


async def test_mcp_server_with_stdio_transport():
    """Test MCP server using stdio transport."""
    print("Connecting to MCP server via stdio transport...")
    
    server_params = ["python", "server.py", "--transport", "stdio"]
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await test_book_library_management_mcp_server(session)


async def test_mcp_server_with_http_transport(server_url: str):
    """Test MCP server using HTTP transport."""
    print(f"Connecting to MCP server via HTTP transport at {server_url}...")
    
    try:
        async with streamablehttp_client(server_url) as (read, write, get_session_id_callback):
            async with ClientSession(read, write) as session:
                await test_book_library_management_mcp_server(session)
    except Exception as e:
        print(f"Failed to connect to HTTP server: {e}")
        print("Make sure the server is running with: python server.py --transport http --port 8000")


@click.command()
@click.option(
    "--transport",
    type=click.Choice(["stdio", "http", "sse"]),
    default="stdio",
    help="Transport mechanism to use",
)
@click.option(
    "--server-url",
    default="http://127.0.0.1:8000/mcp",
    help="Server URL for HTTP transport",
)
def main(transport: str, server_url: str):
    """Run the Library MCP Client."""
    print("Library MCP Client Starting...")
    print(f"Transport: {transport.upper()}")

    if transport == "stdio":
        asyncio.run(test_mcp_server_with_stdio_transport())
    else:
        asyncio.run(test_mcp_server_with_http_transport(server_url))


if __name__ == "__main__":
    main()