# 📚 MCP Library Management Server

> A powerful Model Context Protocol (MCP) server for managing personal book libraries with advanced features like search, recommendations, and analytics.

[![MCP](https://img.shields.io/badge/MCP-Compatible-blue.svg)](https://modelcontextprotocol.io/)
[![Python](https://img.shields.io/badge/Python-3.8%2B-green.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 🌟 Features

### 📖 **Core Library Management**
- ✅ Add, update, and remove books with rich metadata
- 🔍 Advanced search by title, author, genre, or tags
- 📊 Comprehensive library analytics and statistics
- 🎯 AI-powered book recommendations
- 🏷️ Smart tagging and categorization system

### 🚀 **Capabilities** 
- 📈 **Analytics Dashboard**: Statistics by genre, author, rating, language
- 🔮 **Smart Recommendations**: Based on reading preferences and similarity
- 🔍 **Flexible Search**: Multi-criteria search with result limiting
- 📝 **Rich Metadata**: ISBN validation, ratings, descriptions, page counts
- 🌐 **Multiple Transports**: HTTP, STDIO, and SSE support
- 💾 **Data Safety**: Auto-backup and error recovery

### 🛠️ **Developer Features**
- 🧪 Interactive testing suite with demo mode
- 🔧 Comprehensive error handling and logging
- 📋 Full MCP protocol compliance
- 🔄 Backward compatibility with existing data
- 🌍 Unicode and multi-language support

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- pip or uv package manager

### Installation

```bash
# Clone the repository
git clone https://github.com/trngthnh369/library-mcp-server.git
cd library-mcp-server

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

### Running the Server

```bash
# HTTP Transport (Recommended)
python server.py --transport http --port 8000

# STDIO Transport
python server.py --transport stdio

# Custom configuration
python server.py --books-file my_library.json --log-level DEBUG
```

### Testing

```bash
# Run comprehensive tests
python client.py --transport http --port 8000

# Interactive demo mode
python client.py --transport http --test-only=false
```

## 📋 API Reference

### 🔧 Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `add_book` | Add a new book to library | title, author, isbn, tags, genre, rating, etc. |
| `update_book` | Update existing book info | isbn, fields to update |
| `remove_book` | Remove book by ISBN | isbn |
| `search_books` | Advanced book search | query, search_type, limit |
| `get_statistics` | Library analytics | group_by (genre/author/rating/language) |
| `get_recommendations` | Smart book suggestions | preferences, min_rating, based_on_isbn |
| `get_num_books` | Get total book count | none |

### 📚 Resources

| Resource | URI | Description |
|----------|-----|-------------|
| All Books | `books://all` | Complete library with metadata |
| Statistics | `books://stats` | Real-time library analytics |
| Book by ISBN | `books://isbn/{isbn}` | Individual book details |

### 💬 Prompts

| Prompt | Description | Arguments |
|--------|-------------|-----------|
| `suggest_random_book` | Random book suggestion | none |
| `suggest_book_title_by_abstract` | Title suggestion from abstract | abstract |
| `analyze_book` | Detailed book analysis | book, query |
| `library_recommendations` | Personalized recommendations | preferences |
| `library_analysis` | Complete library insights | none |

## 📖 Usage Examples

### Adding a Book

```python
# Full metadata example
book_data = {
    "title": "The Quantum Universe",
    "author": "Brian Cox",
    "isbn": "9780241952702",
    "tags": ["physics", "science", "quantum mechanics"],
    "genre": "Science",
    "year_published": 2011,
    "rating": 4.2,
    "description": "An exploration of quantum mechanics and reality",
    "pages": 352,
    "language": "English"
}

response = await session.call_tool("add_book", book_data)
print(response.content[0].text)
# Output: Book 'The Quantum Universe' by Brian Cox successfully added to the library.
```

### Advanced Search

```python
# Search by genre
search_response = await session.call_tool("search_books", {
    "query": "Science Fiction",
    "search_type": "genre",
    "limit": 5
})

# Universal search
search_response = await session.call_tool("search_books", {
    "query": "quantum physics",
    "search_type": "all",
    "limit": 10
})
```

### Getting Recommendations

```python
# Preference-based recommendations
rec_response = await session.call_tool("get_recommendations", {
    "preferred_genres": ["Science", "History"],
    "min_rating": 4.0
})

# Similar book recommendations  
rec_response = await session.call_tool("get_recommendations", {
    "based_on_isbn": "9780241952702"
})
```

### Library Analytics

```python
# Genre statistics
stats_response = await session.call_tool("get_statistics", {
    "group_by": "genre"
})

result = json.loads(stats_response.content[0].text)
print(f"Total books: {result['total_books']}")
print(f"Average rating: {result['summary']['average_rating']:.2f}")
```

## 🏗️ Architecture

```
library-mcp-server
├──server.py      # Main MCP server
├──client.py # Comprehensive test suiteutilities
├──requirements.txt # Dependencies
├──pyproject.toml 
├──README.md
└──uv.lock
```

## 🔧 Configuration

### Server Options

```bash
python server.py --help

Options:
  --log-level [DEBUG|INFO|WARNING|ERROR]  Set logging level (default: INFO)
  --transport [http|stdio|sse]            Transport type (default: http) 
  --port INTEGER                          HTTP server port (default: 8000)
  --books-file TEXT                       JSON data file (default: books.json)
```

### Environment Variables

```bash
# Optional environment configuration
export MCP_LOG_LEVEL=DEBUG
export MCP_TRANSPORT=http
export MCP_PORT=8000
export MCP_BOOKS_FILE=my_library.json
```

## 🧪 Testing & Development

### Running Tests

```bash
# Full test suite
python client.py --transport http

# Specific transport testing
python client.py --transport stdio
python client.py --transport http --port 8000

### Interactive Demo

The test client includes an interactive demo mode:

```bash
python client.py --test-only=false
```

Demo features:
- 🎮 Add random books
- 🔍 Interactive search
- 🎯 Get recommendations  
- 📊 View statistics
- 📚 Browse all books

### Sample Data

The test suite includes realistic sample books:
- "The Quantum Universe" by Brian Cox
- "Sapiens" by Yuval Noah Harari  
- "Dune" by Frank Herbert
- "The Art of War" by Sun Tzu

## 🛠️ Troubleshooting

### Common Issues

#### STDIO Transport Errors
```bash

# Alternative: Use HTTP transport
python server.py --transport http --port 8000
python client.py --transport http
```

#### Import Errors
```bash
# Check dependencies
pip install -r requirements.txt

# Verify MCP installation
python -c "import mcp; print('MCP OK')"
```

#### Data File Issues
```bash
# Reset library (backup created automatically)
rm books.json

# Restore from backup
cp books.backup.json books.json
```

### Debug Mode

Enable detailed logging:
```bash
python server.py --log-level DEBUG --transport http
```

### Performance Tips

- Use HTTP transport for better reliability
- Limit search results for large libraries
- Enable compression for large datasets
- Use SSD storage for better I/O performance

## 📊 Performance & Limits

| Metric | Recommended | Maximum |
|--------|------------|---------|
| Books in library | < 10,000 | ~50,000 |
| Search results | < 100 | 1,000 |
| Concurrent connections | < 50 | 100 |
| File size | < 50MB | 200MB |

## 🔒 Security Features

- ✅ Input validation and sanitization
- ✅ ISBN format validation
- ✅ Safe file operations
- ✅ Error message sanitization
- ✅ No sensitive data exposure

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Setup

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run linting
flake8 server.py client.py

# Run type checking
mypy server.py

# Format code
black server.py client.py
```

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Model Context Protocol](https://modelcontextprotocol.io/) team
- [Anthropic](https://anthropic.com/) for MCP development
- Python community for excellent libraries
- Contributors and testers

## 📞 Support

- Email: truongthinhnguyen30303@gmail.com
