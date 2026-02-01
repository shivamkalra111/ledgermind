# Upload Route
"""
File upload endpoint for customers to upload their data.

POST /api/v1/upload
- Accepts multiple Excel/CSV files
- Auto-detects headers and creates DuckDB tables
- Uses smart loading (only processes new/changed files)

NOTE: This endpoint is DATA-AGNOSTIC - it does not assume specific data types.
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
    
    # Load data into DuckDB and populate table catalog
    tables_created = []
    try:
        # Get customer context and trigger data loading
        manager = CustomerManager()
        ctx = manager.get_customer(customer_id)
        ctx.ensure_exists()
        
        # Get data state manager for smart loading
        data_state_manager = DataStateManager(ctx)
        
        # Get files that need to be loaded
        from core.data_engine import DataEngine
        engine = DataEngine(str(ctx.duckdb_path))
        
        # Initialize table catalog for storing schema (IMPORTANT for efficient querying)
        from core.table_catalog import TableCatalog, create_table_metadata
        catalog = TableCatalog(ctx.root_dir)
        
        existing_tables = engine.list_tables()
        files_to_load = data_state_manager.get_files_to_load(existing_tables)
        
        if files_to_load:
            for filename, file_path, change_type in files_to_load:
                try:
                    table_name = engine.load_file(file_path)
                    
                    # Get row count for tracking
                    info = engine.get_table_info(table_name)
                    row_count = info.get("row_count", 0)
                    
                    # Mark file as loaded in data state
                    data_state_manager.mark_file_loaded(
                        filename=filename,
                        table_name=table_name,
                        row_count=row_count
                    )
                    
                    # IMPORTANT: Save schema to table catalog (so we don't query DuckDB every time)
                    try:
                        metadata = create_table_metadata(
                            table_name=table_name,
                            source_file=filename,
                            data_engine=engine,
                            llm_client=None,  # No LLM needed for basic metadata
                            extract_stats=True
                        )
                        catalog.register_table(metadata)
                    except Exception as catalog_err:
                        # Log but don't fail upload if catalog fails
                        print(f"Warning: Could not add {table_name} to catalog: {catalog_err}")
                    
                    tables_created.append(table_name)
                    
                except Exception as e:
                    errors.append(f"Failed to load {filename}: {str(e)}")
            
            # Save data state
            data_state_manager.save()
            
            # Save table catalog (schema persisted for efficient queries)
            catalog.save()
        
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

