#!/usr/bin/env python3
"""
Setup script for Library MCP Server.
"""

from setuptools import setup, find_packages

# Read requirements
with open("requirements.txt", "r", encoding="utf-8") as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith("#")]

# Read README for long description
try:
    with open("README.md", "r", encoding="utf-8") as f:
        long_description = f.read()
except FileNotFoundError:
    long_description = "A Model Context Protocol server for managing a book library"

setup(
    name="library-mcp-server",
    version="0.1.0",
    description="A Model Context Protocol server for managing a book library with tools, resources, and prompts",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Library MCP Team",
    author_email="team@example.com",
    url="https://github.com/your-username/library-mcp-server",
    py_modules=["server", "client", "models", "config"],
    python_requires=">=3.11",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "library-mcp-server=server:main",
            "library-mcp-client=client:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Internet :: WWW/HTTP :: HTTP Servers",
    ],
    keywords="mcp library books server protocol",
    project_urls={
        "Documentation": "https://github.com/your-username/library-mcp-server#readme",
        "Source": "https://github.com/your-username/library-mcp-server",
        "Tracker": "https://github.com/your-username/library-mcp-server/issues",
    },
)