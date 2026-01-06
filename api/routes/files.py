# File Management Routes
"""
Endpoints for managing user's uploaded files.

GET  /api/v1/files         - List all files
GET  /api/v1/files/{name}  - Get file info
DELETE /api/v1/files/{name} - Delete a file
"""

import os
from datetime import datetime
from pathlib import Path
from typing import List, Tuple, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from config import WORKSPACE_DIR
from api.auth import get_current_customer
from core.customer import CustomerManager
from core.data_engine import DataEngine


router = APIRouter(prefix="/files", tags=["files"])


ALLOWED_EXTENSIONS = {".xlsx", ".xls", ".csv"}


# =============================================================================
# Response Models
# =============================================================================

class FileInfo(BaseModel):
    name: str
    size_kb: float
    modified: str
    table_name: Optional[str] = None
    row_count: Optional[int] = None


class FilesListResponse(BaseModel):
    success: bool
    customer_id: str
    files: List[FileInfo]
    total_files: int
    tables_loaded: List[str]


class FileDeleteResponse(BaseModel):
    success: bool
    message: str
    file_deleted: str
    table_dropped: Optional[str] = None


# =============================================================================
# Endpoints
# =============================================================================

@router.get("", response_model=FilesListResponse)
async def list_files(
    customer: Tuple[str, dict] = Depends(get_current_customer)
):
    """
    List all uploaded files for the customer.
    
    Returns file info including size, modification date, and associated table.
    """
    customer_id, _ = customer
    
    data_path = WORKSPACE_DIR / customer_id / "data"
    
    if not data_path.exists():
        return FilesListResponse(
            success=True,
            customer_id=customer_id,
            files=[],
            total_files=0,
            tables_loaded=[]
        )
    
    # Get tables and their info
    tables_info = {}
    tables = []
    try:
        manager = CustomerManager()
        ctx = manager.get_customer(customer_id)
        
        engine = DataEngine(str(ctx.duckdb_path))
        tables = engine.list_tables()
        
        for table in tables:
            try:
                info = engine.get_table_info(table)
                tables_info[table] = info.get("row_count", 0)
            except:
                tables_info[table] = 0
        
        engine.close()
    except:
        pass
    
    # List files with their table associations
    files = []
    for f in data_path.iterdir():
        if f.suffix.lower() in ALLOWED_EXTENSIONS:
            # Guess table name from file name
            table_name = f.stem.lower().replace(" ", "_").replace("-", "_")
            
            files.append(FileInfo(
                name=f.name,
                size_kb=round(f.stat().st_size / 1024, 2),
                modified=datetime.fromtimestamp(f.stat().st_mtime).isoformat(),
                table_name=table_name if table_name in tables_info else None,
                row_count=tables_info.get(table_name)
            ))
    
    # Sort by name
    files.sort(key=lambda x: x.name)
    
    return FilesListResponse(
        success=True,
        customer_id=customer_id,
        files=files,
        total_files=len(files),
        tables_loaded=tables
    )


@router.get("/{filename}")
async def get_file_info(
    filename: str,
    customer: Tuple[str, dict] = Depends(get_current_customer)
):
    """Get detailed info about a specific file."""
    customer_id, _ = customer
    
    data_path = WORKSPACE_DIR / customer_id / "data"
    file_path = data_path / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"File not found: {filename}")
    
    # Get table info if exists
    table_name = file_path.stem.lower().replace(" ", "_").replace("-", "_")
    table_info = None
    
    try:
        manager = CustomerManager()
        ctx = manager.get_customer(customer_id)
        
        engine = DataEngine(str(ctx.duckdb_path))
        tables = engine.list_tables()
        
        if table_name in tables:
            table_info = engine.get_table_info(table_name)
        
        engine.close()
    except:
        pass
    
    return {
        "success": True,
        "file": {
            "name": filename,
            "path": str(file_path),
            "size_kb": round(file_path.stat().st_size / 1024, 2),
            "modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
        },
        "table": table_info
    }


@router.delete("/{filename}", response_model=FileDeleteResponse)
async def delete_file(
    filename: str,
    customer: Tuple[str, dict] = Depends(get_current_customer)
):
    """
    Delete a file and its associated table.
    
    This will:
    1. Delete the file from disk
    2. Drop the associated table from DuckDB
    """
    customer_id, _ = customer
    
    data_path = WORKSPACE_DIR / customer_id / "data"
    file_path = data_path / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"File not found: {filename}")
    
    # Get table name
    table_name = file_path.stem.lower().replace(" ", "_").replace("-", "_")
    table_dropped = None
    
    # Try to drop associated table
    try:
        manager = CustomerManager()
        ctx = manager.get_customer(customer_id)
        
        engine = DataEngine(str(ctx.duckdb_path))
        tables = engine.list_tables()
        
        if table_name in tables:
            engine.execute(f'DROP TABLE IF EXISTS "{table_name}"')
            table_dropped = table_name
        
        engine.close()
    except Exception as e:
        # Continue even if table drop fails
        pass
    
    # Delete the file
    try:
        file_path.unlink()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete file: {str(e)}")
    
    return FileDeleteResponse(
        success=True,
        message=f"File '{filename}' deleted successfully",
        file_deleted=filename,
        table_dropped=table_dropped
    )

