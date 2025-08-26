import asyncio
import json
import random
from datetime import datetime
from pathlib import Path

import click
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.streamable_http import streamablehttp_client
from mcp.shared.metadata_utils import get_display_name
from pydantic.networks import AnyUrl


async def display_tools(session: ClientSession):
    """Display available tools with descriptions"""
    print("=== AVAILABLE TOOLS ===")
    tools_response = await session.list_tools()
    
    for i, tool in enumerate(tools_response.tools, 1):
        display_name = get_display_name(tool)
        print(f"{i}. {display_name}")
        if tool.description:
            print(f"   📖 {tool.description}")
        print()


async def display_resources(session: ClientSession):
    """Display available resources"""
    print("=== AVAILABLE RESOURCES ===")
    resources_response = await session.list_resources()
    
    for resource in resources_response.resources:
        display_name = get_display_name(resource)
        print(f"📚 {display_name} ({resource.uri})")
        if resource.description:
            print(f"   {resource.description}")
        print()


async def comprehensive_library_test(session: ClientSession):
    """Comprehensive test of all library features"""
    
    print("🔧 TESTING MCP LIBRARY SERVER")
    print("=" * 60)
    
    try:
        # Display available tools and resources
        await display_tools(session)
        await display_resources(session)
        
        # 1. Check initial library state
        print("📊 INITIAL LIBRARY STATE")
        print("-" * 30)
        
        num_books_response = await session.call_tool("get_num_books", {})
        initial_count = int(num_books_response.content[0].text)
        print(f"📚 Total books in library: {initial_count}")
        
        # Get initial statistics - with error handling
        try:
            stats_response = await session.call_tool("get_statistics", {"group_by": "genre"})
            print(f"📈 Library statistics:\n{stats_response.content[0].text}")
        except Exception as e:
            print(f"⚠️ Statistics unavailable: {e}")
        print()
        
    except Exception as e:
        print(f"❌ Initial test setup failed: {e}")
        return False
    
    # 2. Add several books
    print("➕ ADDING BOOKS")
    print("-" * 30)
    
    sample_books = [
        {
            "title": "The Quantum Universe",
            "author": "Brian Cox",
            "isbn": "9780241952702",
            "tags": ["physics", "science", "quantum mechanics"],
            "genre": "Science",
            "year_published": 2011,
            "rating": 4.2,
            "description": "An exploration of quantum mechanics and its implications for our understanding of reality",
            "pages": 352,
            "language": "English"
        },
        {
            "title": "Sapiens: A Brief History of Humankind",
            "author": "Yuval Noah Harari", 
            "isbn": "9780062316097",
            "tags": ["history", "anthropology", "evolution"],
            "genre": "History",
            "year_published": 2014,
            "rating": 4.5,
            "description": "How Homo sapiens came to dominate the world",
            "pages": 443,
            "language": "English"
        },
        {
            "title": "Dune",
            "author": "Frank Herbert",
            "isbn": "9780441172719", 
            "tags": ["science fiction", "adventure", "politics"],
            "genre": "Science Fiction",
            "year_published": 1965,
            "rating": 4.8,
            "description": "Epic tale of politics, religion, and ecology on the desert planet Arrakis",
            "pages": 688,
            "language": "English"
        },
        {
            "title": "The Art of War",
            "author": "Sun Tzu",
            "isbn": "9781590302255",
            "tags": ["strategy", "philosophy", "military"],
            "genre": "Philosophy",
            "year_published": -500,  # Approximate BC date
            "rating": 4.0,
            "description": "Ancient Chinese military treatise on strategy and tactics",
            "pages": 273,
            "language": "English"
        }
    ]
    
    added_isbns = []
    for book in sample_books:
        try:
            add_response = await session.call_tool("add_book", book)
            print(f"✅ {add_response.content[0].text}")
            added_isbns.append(book["isbn"])
        except Exception as e:
            print(f"❌ Failed to add {book['title']}: {e}")
    
    print()
    
    # 3. Test search functionality
    print("🔍 TESTING SEARCH FUNCTIONALITY")
    print("-" * 30)
    
    search_tests = [
        {"query": "science", "search_type": "all"},
        {"query": "Harari", "search_type": "author"},
        {"query": "Science Fiction", "search_type": "genre"},
        {"query": "physics", "search_type": "tags"}
    ]
    
    for search_test in search_tests:
        try:
            search_response = await session.call_tool("search_books", search_test)
            results = json.loads(search_response.content[0].text)
            print(f"🔎 Search '{search_test['query']}' ({search_test['search_type']}): {len(results)} results")
            for result in results[:2]:  # Show first 2 results
                print(f"   📖 {result['title']} by {result['author']}")
        except Exception as e:
            print(f"❌ Search failed: {e}")
    
    print()
    
    # 4. Test book updates
    print("✏️ TESTING BOOK UPDATES")
    print("-" * 30)
    
    if added_isbns:
        isbn_to_update = added_isbns[0]
        update_data = {
            "isbn": isbn_to_update,
            "rating": 4.7,
            "description": "Updated description: An absolutely fascinating journey through quantum physics!"
        }
        
        try:
            update_response = await session.call_tool("update_book", update_data)
            print(f"✅ {update_response.content[0].text}")
        except Exception as e:
            print(f"❌ Update failed: {e}")
    
    print()
    
    # 5. Test recommendations
    print("🎯 TESTING RECOMMENDATION SYSTEM")
    print("-" * 30)
    
    recommendation_tests = [
        {"preferred_genres": ["Science", "History"], "min_rating": 4.0},
        {"based_on_isbn": added_isbns[0] if added_isbns else None},
    ]
    
    for i, rec_test in enumerate(recommendation_tests, 1):
        try:
            rec_response = await session.call_tool("get_recommendations", rec_test)
            recommendations = json.loads(rec_response.content[0].text)
            print(f"🎯 Recommendation Test {i}: {len(recommendations)} books recommended")
            for rec in recommendations[:3]:  # Show top 3
                rating_str = f" (⭐ {rec.get('rating', 'N/A')})" if rec.get('rating') else ""
                print(f"   📚 {rec['title']} by {rec['author']}{rating_str}")
        except Exception as e:
            print(f"❌ Recommendation test {i} failed: {e}")
    
    print()
    
    # 6. Test statistics
    print("📊 TESTING STATISTICS")
    print("-" * 30)
    
    stat_types = ["genre", "author", "language", "rating"]
    
    for stat_type in stat_types:
        try:
            stats_response = await session.call_tool("get_statistics", {"group_by": stat_type})
            stats = json.loads(stats_response.content[0].text)
            print(f"📈 Statistics by {stat_type}:")
            print(f"   Total books: {stats['total_books']}")
            if stats['breakdown']:
                top_items = list(stats['breakdown'].items())[:3]
                for item, count in top_items:
                    print(f"   - {item}: {count}")
            if stats['summary']:
                for key, value in stats['summary'].items():
                    if isinstance(value, float):
                        print(f"   {key}: {value:.2f}")
                    else:
                        print(f"   {key}: {value}")
            print()
        except Exception as e:
            print(f"❌ Statistics test for {stat_type} failed: {e}")
    
    # 7. Test resource access
    print("📖 TESTING RESOURCE ACCESS")
    print("-" * 30)
    
    try:
        # Test all books resource
        all_books_response = await session.read_resource(AnyUrl("books://all"))
        all_books = json.loads(all_books_response.contents[0].text)
        print(f"📚 All books resource: {len(all_books)} books retrieved")
        
        # Test stats resource
        stats_resource_response = await session.read_resource(AnyUrl("books://stats"))
        stats_data = json.loads(stats_resource_response.contents[0].text)
        print(f"📊 Statistics resource: {stats_data['total_books']} total books")
        
        # Test individual book by ISBN
        if added_isbns:
            isbn_resource = f"books://isbn/{added_isbns[0]}"
            book_response = await session.read_resource(AnyUrl(isbn_resource))
            book_data = json.loads(book_response.contents[0].text)
            print(f"📖 Individual book resource: '{book_data['title']}' retrieved")
            
    except Exception as e:
        print(f"❌ Resource access failed: {e}")
    
    print()
    
    # 8. Final library state
    print("📊 FINAL LIBRARY STATE")
    print("-" * 30)
    
    final_count_response = await session.call_tool("get_num_books", {})
    final_count = int(final_count_response.content[0].text)
    print(f"📚 Total books: {final_count} (added {final_count - initial_count} books)")
    
    # Show final comprehensive statistics
    try:
        final_stats_response = await session.call_tool("get_statistics", {"group_by": "genre"})
        final_stats = json.loads(final_stats_response.content[0].text)
        print("\n📈 Final Library Overview:")
        if final_stats['summary']:
            for key, value in final_stats['summary'].items():
                if isinstance(value, float):
                    print(f"   {key}: {value:.2f}")
                else:
                    print(f"   {key}: {value}")
        
        print("\n📚 Books by Genre:")
        for genre, count in final_stats['breakdown'].items():
            print(f"   {genre}: {count} books")
            
    except Exception as e:
        print(f"❌ Final stats failed: {e}")
    
    # 9. Cleanup (optional - remove test books)
    print("\n🧹 CLEANUP (removing test books)")
    print("-" * 30)
    
    removed_count = 0
    for isbn in added_isbns:
        try:
            remove_response = await session.call_tool("remove_book", {"isbn": isbn})
            print(f"🗑️ {remove_response.content[0].text}")
            removed_count += 1
        except Exception as e:
            print(f"❌ Failed to remove book {isbn}: {e}")
    
    print(f"\n✅ Test completed! Removed {removed_count} test books.")
    

async def interactive_demo(session: ClientSession):
    """Interactive demonstration of library features"""
    print("\n🎮 INTERACTIVE DEMO MODE")
    print("=" * 40)
    
    while True:
        print("\nAvailable actions:")
        print("1. Add a random book")
        print("2. Search books")  
        print("3. Get recommendations")
        print("4. View statistics")
        print("5. List all books")
        print("6. Exit demo")
        
        try:
            choice = input("\nEnter your choice (1-6): ").strip()
            
            if choice == "1":
                # Add random book
                random_book = {
                    "title": f"Random Book {random.randint(1000, 9999)}",
                    "author": f"Author {random.randint(100, 999)}",
                    "isbn": f"978{random.randint(1000000000, 9999999999)}",
                    "tags": random.choices(["fiction", "science", "history", "fantasy"], k=2),
                    "genre": random.choice(["Fiction", "Science", "History", "Fantasy"]),
                    "rating": round(random.uniform(3.0, 5.0), 1),
                    "pages": random.randint(200, 800)
                }
                
                response = await session.call_tool("add_book", random_book)
                print(f"✅ {response.content[0].text}")
                
            elif choice == "2":
                # Search books
                query = input("Enter search query: ").strip()
                search_type = input("Search type (all/title/author/genre/tags) [all]: ").strip() or "all"
                
                response = await session.call_tool("search_books", {
                    "query": query,
                    "search_type": search_type,
                    "limit": 10
                })
                
                results = json.loads(response.content[0].text)
                print(f"\n🔍 Found {len(results)} results:")
                for i, book in enumerate(results, 1):
                    rating_str = f" (⭐ {book.get('rating', 'N/A')})" if book.get('rating') else ""
                    print(f"{i}. {book['title']} by {book['author']}{rating_str}")
                
            elif choice == "3":
                # Get recommendations
                min_rating = input("Minimum rating (1-5) [optional]: ").strip()
                genres = input("Preferred genres (comma-separated) [optional]: ").strip()
                
                rec_params = {}
                if min_rating:
                    rec_params["min_rating"] = float(min_rating)
                if genres:
                    rec_params["preferred_genres"] = [g.strip() for g in genres.split(",")]
                
                response = await session.call_tool("get_recommendations", rec_params)
                recommendations = json.loads(response.content[0].text)
                
                print(f"\n🎯 Found {len(recommendations)} recommendations:")
                for i, book in enumerate(recommendations, 1):
                    rating_str = f" (⭐ {book.get('rating', 'N/A')})" if book.get('rating') else ""
                    print(f"{i}. {book['title']} by {book['author']}{rating_str}")
                
            elif choice == "4":
                # View statistics
                group_by = input("Group by (genre/author/language/rating) [genre]: ").strip() or "genre"
                
                response = await session.call_tool("get_statistics", {"group_by": group_by})
                stats = json.loads(response.content[0].text)
                
                print(f"\n📊 Library Statistics (by {group_by}):")
                print(f"Total books: {stats['total_books']}")
                
                if stats['breakdown']:
                    print(f"\nBreakdown:")
                    for item, count in sorted(stats['breakdown'].items()):
                        print(f"  {item}: {count}")
                
                if stats['summary']:
                    print(f"\nSummary:")
                    for key, value in stats['summary'].items():
                        if isinstance(value, float):
                            print(f"  {key}: {value:.2f}")
                        else:
                            print(f"  {key}: {value}")
                
            elif choice == "5":
                # List all books
                count_response = await session.call_tool("get_num_books", {})
                count = int(count_response.content[0].text)
                
                if count > 0:
                    all_books_response = await session.read_resource(AnyUrl("books://all"))
                    all_books = json.loads(all_books_response.contents[0].text)
                    
                    print(f"\n📚 All {count} books in library:")
                    for i, book in enumerate(all_books, 1):
                        rating_str = f" (⭐ {book.get('rating', 'N/A')})" if book.get('rating') else ""
                        genre_str = f" [{book.get('genre', 'Unknown')}]" if book.get('genre') else ""
                        print(f"{i}. {book['title']} by {book['author']}{genre_str}{rating_str}")
                else:
                    print("\n📚 No books in library yet.")
                
            elif choice == "6":
                print("👋 Exiting demo mode...")
                break
                
            else:
                print("❌ Invalid choice. Please enter 1-6.")
                
        except KeyboardInterrupt:
            print("\n👋 Exiting demo...")
            break
        except Exception as e:
            print(f"❌ Error: {e}")


async def test_mcp_server_stdio(port: int = 8000):
    """Test the MCP server using stdio transport"""
    try:
        # First check if server file exists
        server_files = ["server.py"]
        server_file = None
        
        for file in server_files:
            if Path(file).exists():
                server_file = file
                break
        
        if not server_file:
            print("❌ Server file not found. Please ensure 'server.py' exists.")
            return
        
        print(f"📂 Using server file: {server_file}")
        
        stdio_server_params = StdioServerParameters(
            command="python",
            args=[
                server_file,
                "--transport", "stdio",
                "--port", str(port), 
                "--log-level", "ERROR"
            ],
        )

        print(f"🔌 Starting server with command: python {' '.join(stdio_server_params.args)}")
        
        async with stdio_client(stdio_server_params) as (read, write):
            print("📡 Server process started, creating session...")
            
            async with ClientSession(read, write) as session:
                print("🤝 Initializing session...")
                
                # Add timeout for initialization
                try:
                    await asyncio.wait_for(session.initialize(), timeout=10.0)
                    print("✅ Session initialized successfully!")
                except asyncio.TimeoutError:
                    print("❌ Session initialization timed out")
                    return
                except Exception as e:
                    print(f"❌ Session initialization failed: {e}")
                    return
                
                print("🚀 MCP Library Server Connected!")
                print("=" * 50)
                
                try:
                    # Run comprehensive test
                    await comprehensive_library_test(session)
                    
                    # Optional: Run interactive demo
                    demo_choice = input("\nRun interactive demo? (y/n): ").strip().lower()
                    if demo_choice == 'y':
                        await interactive_demo(session)
                        
                except Exception as e:
                    print(f"❌ Test execution failed: {e}")
                    import traceback
                    traceback.print_exc()
                    
    except KeyboardInterrupt:
        print("\n👋 Test interrupted by user")
    except Exception as e:
        print(f"❌ STDIO test setup failed: {e}")
        import traceback
        traceback.print_exc()


async def test_mcp_server_http(server_url: str = "http://localhost:8000/mcp"):
    """Test the MCP server using HTTP transport"""
    async with streamablehttp_client(server_url) as (read, write, get_session_id):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            print("🚀 MCP Library Server Connected via HTTP!")
            print("=" * 50)
            
            # Run comprehensive test
            await comprehensive_library_test(session)
            
            # Optional: Run interactive demo  
            demo_choice = input("\nRun interactive demo? (y/n): ").strip().lower()
            if demo_choice == 'y':
                await interactive_demo(session)


@click.command()
@click.option("--transport", type=click.Choice(["stdio", "http", "sse"]), default="http")
@click.option("--server-url", default="http://localhost", help="Server URL for HTTP transport")
@click.option("--port", default=8000, type=int, help="Server port")
@click.option("--endpoint", default="/mcp", help="MCP endpoint path")
@click.option("--test-only", is_flag=True, help="Run tests only, skip interactive demo")
def test_library(transport, server_url, port, endpoint, test_only):
    """Test the MCP Library Server"""
    
    print("🎯 MCP Library Server Test Suite")
    print("=" * 50)
    print(f"Transport: {transport}")
    print(f"Server: {server_url}:{port}{endpoint if transport != 'stdio' else ''}")
    print()
    
    try:
        if transport == "stdio":
            asyncio.run(test_mcp_server_stdio(port))
        elif transport in ["http", "sse"]:
            full_url = f"{server_url}:{port}{endpoint}"
            asyncio.run(test_mcp_server_http(full_url))
        
        print("\n✅ All tests completed successfully!")
        
    except KeyboardInterrupt:
        print("\n👋 Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")


if __name__ == "__main__":
    test_library()