# 📚 Library MCP Server

A modern, extensible **Model Context Protocol (MCP) server** for managing a digital book library. This project provides a robust agentic API for book management, resource access, and prompt-based workflows, built with Python 3.11+, MCP, Starlette, Uvicorn, and Pydantic.

---

## 🚀 Technologies Used

- **Python 3.11+**
- **MCP** (`mcp`, `mcp-streamablehttp-client`) — agentic protocol for tools, resources, and prompts
- **Starlette** — ASGI web framework
- **Uvicorn** — lightning-fast ASGI server
- **Pydantic** — data validation and serialization
- **Click** — elegant CLI interface

---

## 📁 Project Structure

```
library-mcp-server/
├── books.json                # Persistent storage for library books
├── server.py                 # MCP server exposing tools, resources, prompts
├── client.py                 # Example MCP client for testing and interaction
├── pyproject.toml            # Project metadata and dependencies
├── uv.lock                   # Locked dependency versions (for uv/pip)
├── README.md                 # Project documentation (this file)
```

---

## ⚡ Quick Start

### 1. Clone the Repository

```sh
git clone https://github.com/yourusername/library-mcp-server.git
cd library-mcp-server
```

### 2. Create & Activate Python Environment

```sh
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate
```

### 3. Install Dependencies

```sh
pip install -r requirements.txt
# Or, if using uv:
uv pip install -r requirements.txt
```

### 4. Run the MCP Server

#### Standard IO Transport (for agentic integration):

```sh
python server.py --transport stdio
```

#### HTTP Transport (for web/REST/SSE):

```sh
python server.py --transport http --port 8000
```

#### SSE Transport (for streaming):

```sh
python server.py --transport sse --port 8000
```

### 5. Interact with the Server

#### Using the Example Client

```sh
python client.py --transport stdio
# Or for HTTP:
python client.py --transport http --server-url http://127.0.0.1:8000/mcp
```

---

## 🛠️ Features

- **Book Management Tools**: Add, remove, and query books via agentic tools.
- **Resource API**: Access all books, or query by index/ISBN using resource URIs.
- **Prompt API**: Generate suggestions, analyze books, and create agentic conversations.
- **Extensible**: Easily add new tools, resources, and prompts for custom workflows.
- **Transport Flexibility**: Supports stdio, HTTP, and SSE for integration with agents, web apps, or streaming clients.

---

## 📚 Example Usage

- **Add a Book**: Use the `add_book` tool with title, author, ISBN, and tags.
- **Remove a Book**: Use the `remove_book` tool with ISBN.
- **List All Books**: Read the `books://all` resource.
- **Get Book by Index/ISBN**: Read `books://index/{n}` or `books://isbn/{isbn}`.
- **Prompt Suggestions**: Use prompts like `suggest_random_book` or `suggest_book_title_by_abstract`.

---

## 📝 License

MIT License

---

## 💡 References

- [Model Context Protocol (MCP)](https://modelcontextprotocol.io/)
- [Starlette Documentation](https://www.starlette.io/)
- [Uvicorn Documentation](https://www.uvicorn.org/)
- [Pydantic Documentation](https://docs.pydantic.dev/)

