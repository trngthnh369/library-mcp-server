# Library Management MCP Server

A comprehensive Model Context Protocol (MCP) server for managing a book library with tools, resources, and prompts.

## 🚀 Features

### Core Functionality
- **📚 Book Management**: Add, remove, and organize books with metadata
- **🔍 Advanced Search**: Search by title, author, tags with flexible filtering
- **📊 Statistics**: Library analytics and insights
- **💾 Persistent Storage**: JSON-based storage with backup functionality
- **🚀 Performance**: Built-in caching for improved response times

### MCP Capabilities
- **🛠️ Tools**: Interactive book operations
- **📋 Resources**: Static and dynamic resource access
- **💬 Prompts**: AI-ready prompts for book recommendations and analysis
- **🔗 Multiple Transports**: Support for stdio and Server-Sent Events (SSE)

## 📋 Requirements

- Python 3.11 or higher
- Dependencies listed in `pyproject.toml`

## 🛠️ Installation

1. **Clone the repository**:
```bash
git clone https://github.com/trngthnh369/library-mcp-server.git
cd library-mcp-server
```

2. **Create virtual environment**:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. **Install dependencies**:
```bash
pip install -e .
```

## 🚀 Quick Start

### Start the Server

#### Using stdio transport (default):
```bash
python server.py --transport stdio
```

#### Using SSE transport:
```bash
python server.py --transport sse --port 8000 --host 127.0.0.1
```

### Run the Client

#### Run comprehensive tests:
```bash
python client.py --transport stdio
```

#### Interactive mode:
```bash
python client.py --transport stdio --interactive
```

#### SSE transport:
```bash
python client.py --transport sse --server-url http://127.0.0.1:8000/messages --interactive
```

## 📖 Usage Examples

### Server Configuration

The server can be configured through environment variables:

```bash
export LIBRARY_BOOKS_FILE="my_books.json"
export LIBRARY_MAX_BOOKS="5000"
export LIBRARY_CACHE_ENABLED="true"
export LIBRARY_LOG_LEVEL="DEBUG"
```

### Available Tools

1. **add_book**: Add a new book to the library
2. **remove_book**: Remove a book by ISBN
3. **get_book_count**: Get total number of books
4. **search_books**: Search books with filters (if enabled)
5. **get_library_stats**: Get library statistics (if enabled)

### Book Data Structure

```json
{
  "title": "The Great Adventure",
  "author": "Alice Johnson",
  "isbn": "9781234567890",
  "tags": ["fiction", "adventure", "mystery"]
}
```

### Resource Access

- **All books**: `books://all`
- **Book by index**: `books://index/{index}`
- **Book by ISBN**: `books://isbn/{isbn}`
- **Search results**: `books://search?q={query}&author={author}&tag={tag}`
- **Statistics**: `books://stats`

### Available Prompts

1. **suggest_random_book**: Get a random book suggestion
2. **suggest_book_title_by_abstract**: Generate book titles from abstracts
3. **analyze_book**: Analyze a book with custom queries
4. **recommend_books**: Get personalized book recommendations

## 🔧 Configuration

### Server Configuration (config.py)

```python
from config import get_config, update_config

# Get current configuration
config = get_config()

# Update configuration
update_config(
    max_books=5000,
    cache_enabled=True,
    enable_search=True
)
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `LIBRARY_BOOKS_FILE` | `books.json` | Path to books storage file |
| `LIBRARY_HOST` | `127.0.0.1` | Server host |
| `LIBRARY_PORT` | `8000` | Server port |
| `LIBRARY_LOG_LEVEL` | `INFO` | Logging level |
| `LIBRARY_MAX_BOOKS` | `10000` | Maximum books limit |
| `LIBRARY_CACHE_ENABLED` | `true` | Enable caching |
| `LIBRARY_CACHE_TTL` | `300` | Cache TTL in seconds |

## 🏗️ Architecture

### Project Structure

```
library-mcp-server/
├── server.py          # Main MCP server
├── client.py          # Test client
├── models.py          # Data models and validation
├── config.py          # Configuration management
├── pyproject.toml     # Project configuration
├── .gitignore         # Git ignore rules
└── README.md          # Documentation
```

### Key Components

1. **LibraryManagement**: Core business logic
2. **LibraryCache**: In-memory caching system
3. **Book Models**: Pydantic models with validation
4. **ServerConfig**: Configuration management
5. **LibraryMCPClient**: Enhanced test client

## 📊 Performance Features

### Caching System
- In-memory caching with TTL support
- Automatic cache invalidation on data changes
- Configurable cache settings

### Error Handling
- Comprehensive error responses
- Structured error logging
- Graceful failure recovery

### Validation
- Strong input validation using Pydantic
- ISBN format validation
- Data sanitization and cleaning

## 🧪 Testing

### Automated Test Suite

```bash
# Run comprehensive tests
python client.py --test-only

# Test specific transport
python client.py --transport sse --server-url http://127.0.0.1:8000/messages --test-only
```

### Interactive Testing

```bash
# Start interactive mode
python client.py --interactive

# Available commands in interactive mode:
# - show: Display server capabilities
# - add: Add a new book
# - list: List all books
# - search: Search books
# - stats: Show statistics
# - random: Random book suggestion
# - count: Get book count
# - exit: Quit
```

### Manual Testing with curl (SSE)

```bash
# Start server
python server.py --transport sse --port 8000

# Test with curl
curl -X POST http://127.0.0.1:8000/messages \
  -H "Content-Type: application/json" \
  -d '{"method": "tools/list"}'
```

## 🔍 Troubleshooting

### Common Issues

1. **Import Errors**: Make sure all dependencies are installed
2. **File Permissions**: Ensure write permissions for books.json
3. **Port Conflicts**: Change port if 8000 is in use
4. **Python Version**: Requires Python 3.11+

### Debug Mode

```bash
python server.py --log-level DEBUG --transport stdio
```

### Logs Location
Logs are printed to stdout/stderr. For persistent logging, redirect output:

```bash
python server.py 2>&1 | tee library-server.log
```

## 📝 API Reference

### Tools

#### add_book
Adds a new book to the library.

**Parameters:**
- `title` (string, required): Book title
- `author` (string, required): Book author  
- `isbn` (string, required): Book ISBN
- `tags` (array, optional): Book tags

#### remove_book
Removes a book by ISBN.

**Parameters:**
- `isbn` (string, required): Book ISBN

#### search_books
Searches books with filters.

**Parameters:**
- `query` (string, optional): Search text
- `author` (string, optional): Author filter
- `tag` (string, optional): Tag filter
- `limit` (integer, optional): Result limit (default: 10)

### Resources

- `books://all` - All books
- `books://index/{index}` - Book by index
- `books://isbn/{isbn}` - Book by ISBN
- `books://stats` - Library statistics
- `books://search?...` - Search results

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Built with [Model Context Protocol (MCP)](https://github.com/modelcontextprotocol/python-sdk)
- Uses [Pydantic](https://pydantic-docs.helpmanual.io/) for data validation
- Powered by [FastAPI](https://fastapi.tiangolo.com/) ecosystem