# API Routes Package
"""
Two endpoints only:
- upload: File uploads
- query: Everything else (LLM handles it)
"""

from .upload import router as upload_router
from .query import router as query_router

__all__ = ["upload_router", "query_router"]
