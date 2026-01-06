# LedgerMind API Models
"""
Pydantic models for API request/response validation.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


# =============================================================================
# Authentication Models
# =============================================================================

class APIKeyInfo(BaseModel):
    """Information about an API key."""
    key_id: str = Field(..., description="Unique key identifier (lm_...)")
    customer_id: str = Field(..., description="Associated customer ID")
    name: str = Field(..., description="Human-readable key name")
    created_at: datetime
    last_used: Optional[datetime] = None
    is_active: bool = True


# =============================================================================
# Request Models
# =============================================================================

class QueryRequest(BaseModel):
    """
    Single request model for ALL queries.
    
    Ask anything - the LLM figures out what to do.
    """
    query: str = Field(
        ..., 
        min_length=3, 
        max_length=2000,
        description="Ask anything in natural language",
        examples=[
            "What is my total sales in November?",
            "What is CGST?",
            "Show me my tables",
            "Check my compliance",
            "What is the GST rate for laptops?",
            "When should I file GSTR-3B?"
        ]
    )


# =============================================================================
# Response Models
# =============================================================================

class UploadResponse(BaseModel):
    """Response after file upload."""
    success: bool
    message: str
    files_uploaded: int
    tables_created: List[str] = []
    errors: List[str] = []


class QueryResponse(BaseModel):
    """
    Single response model for ALL queries.
    
    The LLM processed your query and here's the answer.
    """
    success: bool
    query: str = Field(..., description="Your original query")
    answer: str = Field(..., description="The AI's response")
    processing_time_ms: int = Field(..., description="Time taken to process (ms)")


class HealthResponse(BaseModel):
    """API health check response."""
    status: str = "healthy"
    version: str
    llm_available: bool
    chromadb_ready: bool
    timestamp: datetime


class ErrorResponse(BaseModel):
    """Standard error response."""
    success: bool = False
    error: str
    error_code: str
    detail: Optional[str] = None


# =============================================================================
# Customer Info Models
# =============================================================================

class CustomerInfo(BaseModel):
    """Information about the authenticated customer."""
    customer_id: str
    name: str
    created_at: datetime
    tables_loaded: List[str] = []
    total_files: int = 0
    last_data_update: Optional[datetime] = None
