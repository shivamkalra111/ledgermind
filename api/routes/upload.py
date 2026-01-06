# Upload Route
"""
File upload endpoint for customers to upload their financial data.

POST /api/v1/upload
- Accepts multiple Excel/CSV files
- Auto-detects file types and creates DuckDB tables
- Uses smart loading (only processes new/changed files)
"""

import os
import time
import shutil
import aiofiles
from pathlib import Path
from typing import List, Tuple
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException

from config import WORKSPACE_DIR
from api.auth import get_current_customer
from api.models import UploadResponse
from core.customer import CustomerManager
from core.data_state import DataStateManager


router = APIRouter(prefix="/upload", tags=["upload"])


ALLOWED_EXTENSIONS = {".xlsx", ".xls", ".csv"}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB per file


def validate_file(filename: str, size: int) -> Tuple[bool, str]:
    """Validate uploaded file."""
    ext = Path(filename).suffix.lower()
    
    if ext not in ALLOWED_EXTENSIONS:
        return False, f"Invalid file type: {ext}. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
    
    if size > MAX_FILE_SIZE:
        return False, f"File too large: {size / 1024 / 1024:.1f}MB. Max: 50MB"
    
    return True, ""


@router.post("", response_model=UploadResponse)
async def upload_files(
    files: List[UploadFile] = File(..., description="Excel or CSV files to upload"),
    customer: Tuple[str, dict] = Depends(get_current_customer)
):
    """
    Upload Excel/CSV files for analysis.
    
    Files are saved to customer's data folder and automatically 
    processed into queryable tables.
    """
    customer_id, _ = customer
    
    # Get customer data path
    data_path = WORKSPACE_DIR / customer_id / "data"
    data_path.mkdir(parents=True, exist_ok=True)
    
    files_uploaded = 0
    errors = []
    saved_files = []
    
    for upload_file in files:
        # Get file size
        content = await upload_file.read()
        file_size = len(content)
        await upload_file.seek(0)  # Reset for saving
        
        # Validate
        is_valid, error = validate_file(upload_file.filename, file_size)
        if not is_valid:
            errors.append(f"{upload_file.filename}: {error}")
            continue
        
        # Save file
        file_path = data_path / upload_file.filename
        
        try:
            async with aiofiles.open(file_path, "wb") as f:
                await f.write(content)
            
            files_uploaded += 1
            saved_files.append(upload_file.filename)
            
        except Exception as e:
            errors.append(f"{upload_file.filename}: Failed to save - {str(e)}")
    
    if files_uploaded == 0:
        return UploadResponse(
            success=False,
            message="No files were uploaded",
            files_uploaded=0,
            errors=errors
        )
    
    # Load data into DuckDB
    tables_created = []
    try:
        # Get customer context and trigger data loading
        manager = CustomerManager()
        ctx = manager.get_customer(customer_id)
        ctx.ensure_exists()
        
        # Get data state manager for smart loading
        data_state_manager = DataStateManager(ctx.root_dir)
        data_state = data_state_manager.get_current_state()
        
        # Check what changed
        changes = data_state_manager.get_changes()
        
        if changes["new"] or changes["modified"]:
            # Load new/changed files
            from core.data_engine import DataEngine
            engine = DataEngine(str(ctx.duckdb_path))
            
            for file_path in changes["new"] + changes["modified"]:
                try:
                    engine.load_file(file_path)
                except Exception as e:
                    errors.append(f"Failed to load {Path(file_path).name}: {str(e)}")
            
            # Get tables
            tables_created = engine.list_tables()
            
            # Save data state
            data_state_manager.save_state()
            
            engine.close()
    
    except Exception as e:
        errors.append(f"Data processing error: {str(e)}")
    
    return UploadResponse(
        success=True,
        message=f"Successfully uploaded {files_uploaded} file(s)",
        files_uploaded=files_uploaded,
        tables_created=tables_created,
        errors=errors if errors else []
    )


@router.get("/status")
async def upload_status(
    customer: Tuple[str, dict] = Depends(get_current_customer)
):
    """Get current data status for the customer."""
    customer_id, _ = customer
    
    data_path = WORKSPACE_DIR / customer_id / "data"
    
    if not data_path.exists():
        return {
            "customer_id": customer_id,
            "files": [],
            "total_files": 0,
            "tables_loaded": []
        }
    
    # List files
    files = []
    for f in data_path.iterdir():
        if f.suffix.lower() in ALLOWED_EXTENSIONS:
            files.append({
                "name": f.name,
                "size_kb": f.stat().st_size / 1024,
                "modified": f.stat().st_mtime
            })
    
    # Get loaded tables
    tables = []
    try:
        manager = CustomerManager()
        ctx = manager.get_customer(customer_id)
        
        from core.data_engine import DataEngine
        engine = DataEngine(str(ctx.duckdb_path))
        tables = engine.list_tables()
        engine.close()
    except Exception:
        pass
    
    return {
        "customer_id": customer_id,
        "files": files,
        "total_files": len(files),
        "tables_loaded": tables
    }

