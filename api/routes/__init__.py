# API Routes Package
"""
API endpoints:
- upload: File uploads
- files: File management (list, delete)
- query: Everything else (LLM handles it)
"""

from .upload import router as upload_router
from .files import router as files_router
from .query import router as query_router

__all__ = ["upload_router", "files_router", "query_router"]
