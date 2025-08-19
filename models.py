"""
Models and validation schemas for the Library MCP Server.
"""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field, validator
import re


class Book(BaseModel):
    """Book model with comprehensive validation."""
    
    title: str = Field(..., description="The title of the book", min_length=1, max_length=500)
    author: str = Field(..., description="The author of the book", min_length=1, max_length=200)
    isbn: str = Field(..., description="The ISBN of the book", min_length=10, max_length=17)
    tags: List[str] = Field(
        default_factory=list, 
        description="Tags associated with the book",
        max_items=20
    )
    
    @validator('title', 'author')
    def validate_text_fields(cls, v: str) -> str:
        """Validate and clean text fields."""
        if not v or not v.strip():
            raise ValueError("Field cannot be empty or only whitespace")
        return v.strip()
    
    @validator('isbn')
    def validate_isbn(cls, v: str) -> str:
        """Validate ISBN format."""
        if not v or not v.strip():
            raise ValueError("ISBN cannot be empty")
        
        # Remove any spaces, hyphens, or other non-digit characters except 'X'
        clean_isbn = re.sub(r'[^0-9X]', '', v.upper())
        
        # Check length
        if len(clean_isbn) not in [10, 13]:
            raise ValueError("ISBN must be 10 or 13 digits")
        
        # Basic format validation for ISBN-10 and ISBN-13
        if len(clean_isbn) == 10:
            if not re.match(r'^\d{9}[\dX]$', clean_isbn):
                raise ValueError("Invalid ISBN-10 format")
        else:  # ISBN-13
            if not re.match(r'^\d{13}$', clean_isbn):
                raise ValueError("Invalid ISBN-13 format")
        
        return clean_isbn
    
    @validator('tags')
    def validate_tags(cls, v: List[str]) -> List[str]:
        """Validate and clean tags."""
        if not v:
            return []
        
        clean_tags = []
        for tag in v:
            if isinstance(tag, str) and tag.strip():
                clean_tag = tag.strip().lower()
                if len(clean_tag) <= 50 and clean_tag not in clean_tags:
                    clean_tags.append(clean_tag)
        
        return clean_tags[:20]  # Limit to 20 tags
    
    class Config:
        """Pydantic configuration."""
        str_strip_whitespace = True
        validate_assignment = True
        extra = "forbid"


class BookISBNInput(BaseModel):
    """Input model for ISBN-based operations."""
    
    isbn: str = Field(..., description="The ISBN of the book", min_length=10, max_length=17)
    
    @validator('isbn')
    def validate_isbn(cls, v: str) -> str:
        """Validate ISBN format."""
        return Book.validate_isbn(v)
    
    class Config:
        """Pydantic configuration."""
        str_strip_whitespace = True
        extra = "forbid"


class AddBookInput(Book):
    """Input model for adding books."""
    pass


class LibraryStats(BaseModel):
    """Model for library statistics."""
    
    total_books: int = Field(..., description="Total number of books")
    unique_authors: int = Field(..., description="Number of unique authors")
    unique_tags: int = Field(..., description="Number of unique tags")
    most_common_tags: List[str] = Field(default_factory=list, description="Most common tags")
    
    class Config:
        """Pydantic configuration."""
        extra = "forbid"


class SearchQuery(BaseModel):
    """Model for book search queries."""
    
    query: Optional[str] = Field(None, description="Search query text", max_length=200)
    author: Optional[str] = Field(None, description="Filter by author", max_length=200)
    tag: Optional[str] = Field(None, description="Filter by tag", max_length=50)
    limit: int = Field(10, description="Maximum number of results", ge=1, le=100)
    
    @validator('query', 'author', 'tag')
    def validate_search_fields(cls, v: Optional[str]) -> Optional[str]:
        """Validate search fields."""
        if v is not None:
            v = v.strip()
            return v if v else None
        return v
    
    class Config:
        """Pydantic configuration."""
        str_strip_whitespace = True
        extra = "forbid"


class ErrorResponse(BaseModel):
    """Standard error response model."""
    
    error: str = Field(..., description="Error message")
    error_code: str = Field(..., description="Error code")
    details: Optional[Dict] = Field(None, description="Additional error details")
    
    class Config:
        """Pydantic configuration."""
        extra = "forbid"