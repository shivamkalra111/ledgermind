# LedgerMind API Application
"""
FastAPI application - the customer-facing product.

Run with:
    uvicorn api.app:app --reload --port 8000

API Documentation:
    http://localhost:8000/docs (Swagger UI)
    http://localhost:8000/redoc (ReDoc)
"""

from datetime import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.models import HealthResponse
from api.routes import upload_router, query_router
from llm.client import LLMClient
from core.knowledge import KnowledgeBase


# =============================================================================
# Lifespan Events
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    # Startup
    print("\n🚀 LedgerMind API Starting...")
    
    # Check LLM availability
    llm = LLMClient()
    if llm.is_available():
        print("✅ Ollama LLM available")
    else:
        print("⚠️ Ollama LLM not available - queries will fail")
    
    # Check ChromaDB
    try:
        kb = KnowledgeBase()
        print("✅ ChromaDB ready")
    except Exception as e:
        print(f"⚠️ ChromaDB not ready: {e}")
    
    print("✅ API ready at http://localhost:8000")
    print("📚 Docs at http://localhost:8000/docs\n")
    
    yield
    
    # Shutdown
    print("\n👋 LedgerMind API shutting down...")


# =============================================================================
# FastAPI Application
# =============================================================================

app = FastAPI(
    title="LedgerMind API",
    description="""
# LedgerMind - AI CFO for MSMEs

Transform your messy Excel/CSV data into actionable financial intelligence.

## Two Endpoints. That's it.

| Endpoint | What it does |
|----------|--------------|
| `POST /api/v1/upload` | Upload your Excel/CSV files |
| `POST /api/v1/query` | Ask anything - AI handles it |

## Authentication

All endpoints require an API key in the `X-API-Key` header:

```
X-API-Key: lm_live_xxxxxxxxxxxxx
```

## Examples

**Upload files:**
```bash
curl -X POST -H "X-API-Key: YOUR_KEY" \\
  -F "files=@sales.xlsx" \\
  http://localhost:8000/api/v1/upload
```

**Ask anything:**
```bash
curl -X POST -H "X-API-Key: YOUR_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{"query": "What is my total sales?"}' \\
  http://localhost:8000/api/v1/query
```

The AI figures out if you're asking about:
- Your data ("Show me November sales")
- GST rules ("What is CGST?")
- Compliance ("Check my invoices")
- Anything else

## Support

Contact: support@ledgermind.ai
    """,
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)


# =============================================================================
# CORS Middleware
# =============================================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# Exception Handlers
# =============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.detail,
            "error_code": f"HTTP_{exc.status_code}"
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "error_code": "INTERNAL_ERROR",
            "detail": str(exc) if app.debug else None
        }
    )


# =============================================================================
# Routes
# =============================================================================

# Health check (no auth required)
@app.get("/health", response_model=HealthResponse, tags=["health"])
async def health_check():
    """Check API health and service status."""
    llm = LLMClient()
    
    chromadb_ready = False
    try:
        kb = KnowledgeBase()
        chromadb_ready = True
    except:
        pass
    
    return HealthResponse(
        status="healthy",
        version="0.1.0",
        llm_available=llm.is_available(),
        chromadb_ready=chromadb_ready,
        timestamp=datetime.now()
    )


# Root endpoint
@app.get("/", tags=["health"])
async def root():
    """API information."""
    return {
        "name": "LedgerMind API",
        "version": "0.1.0",
        "description": "AI CFO for MSMEs - Ask anything",
        "endpoints": {
            "upload": "POST /api/v1/upload",
            "query": "POST /api/v1/query"
        },
        "docs": "/docs",
        "health": "/health"
    }


# Include routers - just 2!
app.include_router(upload_router, prefix="/api/v1")
app.include_router(query_router, prefix="/api/v1")


# =============================================================================
# Entry Point
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
