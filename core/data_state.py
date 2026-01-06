"""
Data State Manager

Tracks the state of customer's data files to enable smart auto-detection:
- Detects new files
- Detects modified files (by hash)
- Detects deleted files
- Only reloads what's necessary

This eliminates the need for customers to manually run "analyze data" every time.
"""

import json
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum


class FileChangeType(Enum):
    """Type of file change detected."""
    NEW = "new"
    MODIFIED = "modified"
    DELETED = "deleted"
    UNCHANGED = "unchanged"


@dataclass
class FileState:
    """State of a single data file."""
    filename: str
    file_path: str
    file_hash: str                      # MD5 hash of file contents
    file_size: int                      # Size in bytes
    modified_time: str                  # ISO timestamp
    last_loaded: str                    # When we last loaded this file
    table_name: Optional[str] = None    # DuckDB table name
    sheet_type: Optional[str] = None    # sales_register, purchase_ledger, etc.
    row_count: Optional[int] = None     # Number of rows loaded
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "FileState":
        return cls(**data)


@dataclass
class FileChange:
    """Represents a detected change in a file."""
    filename: str
    change_type: FileChangeType
    old_state: Optional[FileState] = None
    new_hash: Optional[str] = None
    reason: str = ""


@dataclass
class DataState:
    """
    Complete state of a customer's data files.
    Stored in workspace/{customer_id}/data_state.json
    """
    customer_id: str
    last_scan: str = field(default_factory=lambda: datetime.now().isoformat())
    files: Dict[str, FileState] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "customer_id": self.customer_id,
            "last_scan": self.last_scan,
            "files": {k: v.to_dict() for k, v in self.files.items()}
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "DataState":
        files = {k: FileState.from_dict(v) for k, v in data.get("files", {}).items()}
        return cls(
            customer_id=data["customer_id"],
            last_scan=data.get("last_scan", datetime.now().isoformat()),
            files=files
        )


class DataStateManager:
    """
    Manages data file state for smart auto-detection.
    
    Usage:
        manager = DataStateManager(customer_context)
        
        # Detect what changed
        changes = manager.detect_changes()
        
        # After loading, update state
        manager.mark_file_loaded("sales.xlsx", table_name="sales_register_2025")
        manager.save()
    """
    
    SUPPORTED_EXTENSIONS = {".xlsx", ".xls", ".csv"}
    
    def __init__(self, customer_context):
        """
        Initialize with customer context.
        
        Args:
            customer_context: CustomerContext instance
        """
        self.customer = customer_context
        self.data_dir = customer_context.data_dir
        self.state_file = customer_context.root_dir / "data_state.json"
        self._state: Optional[DataState] = None
    
    @property
    def state(self) -> DataState:
        """Get current state (lazy loaded)."""
        if self._state is None:
            self._load_state()
        return self._state
    
    def _load_state(self) -> None:
        """Load state from disk."""
        if self.state_file.exists():
            try:
                with open(self.state_file, "r") as f:
                    data = json.load(f)
                self._state = DataState.from_dict(data)
            except (json.JSONDecodeError, KeyError):
                # Corrupted state file - start fresh
                self._state = DataState(customer_id=self.customer.customer_id)
        else:
            self._state = DataState(customer_id=self.customer.customer_id)
    
    def save(self) -> None:
        """Save state to disk."""
        self.state.last_scan = datetime.now().isoformat()
        with open(self.state_file, "w") as f:
            json.dump(self.state.to_dict(), f, indent=2)
    
    @staticmethod
    def _compute_file_hash(file_path: Path) -> str:
        """Compute MD5 hash of file contents."""
        hasher = hashlib.md5()
        with open(file_path, "rb") as f:
            # Read in chunks for large files
            for chunk in iter(lambda: f.read(8192), b""):
                hasher.update(chunk)
        return hasher.hexdigest()
    
    def _get_current_files(self) -> Dict[str, Path]:
        """Get all supported data files in data directory."""
        files = {}
        if self.data_dir.exists():
            for ext in self.SUPPORTED_EXTENSIONS:
                for file_path in self.data_dir.glob(f"*{ext}"):
                    if file_path.is_file():
                        files[file_path.name] = file_path
        return files
    
    def detect_changes(self) -> List[FileChange]:
        """
        Detect changes between current files and saved state.
        
        Returns:
            List of FileChange objects describing what changed
        """
        changes = []
        current_files = self._get_current_files()
        known_files = set(self.state.files.keys())
        current_filenames = set(current_files.keys())
        
        # Check for new files
        new_files = current_filenames - known_files
        for filename in new_files:
            changes.append(FileChange(
                filename=filename,
                change_type=FileChangeType.NEW,
                reason="New file detected"
            ))
        
        # Check for deleted files
        deleted_files = known_files - current_filenames
        for filename in deleted_files:
            changes.append(FileChange(
                filename=filename,
                change_type=FileChangeType.DELETED,
                old_state=self.state.files.get(filename),
                reason="File no longer exists"
            ))
        
        # Check for modified files
        common_files = known_files & current_filenames
        for filename in common_files:
            file_path = current_files[filename]
            current_hash = self._compute_file_hash(file_path)
            old_state = self.state.files[filename]
            
            if current_hash != old_state.file_hash:
                changes.append(FileChange(
                    filename=filename,
                    change_type=FileChangeType.MODIFIED,
                    old_state=old_state,
                    new_hash=current_hash,
                    reason="File contents changed"
                ))
            else:
                changes.append(FileChange(
                    filename=filename,
                    change_type=FileChangeType.UNCHANGED,
                    old_state=old_state,
                    reason="No changes"
                ))
        
        return changes
    
    def get_files_to_load(self, existing_tables: Optional[List[str]] = None) -> List[Tuple[str, Path, FileChangeType]]:
        """
        Get list of files that need to be loaded.
        
        Args:
            existing_tables: Optional list of tables in DuckDB for verification.
        
        Returns:
            List of (filename, path, change_type) for files needing load
        """
        changes = self.detect_changes()
        current_files = self._get_current_files()
        
        to_load = []
        for change in changes:
            if change.change_type in [FileChangeType.NEW, FileChangeType.MODIFIED]:
                if change.filename in current_files:
                    to_load.append((
                        change.filename,
                        current_files[change.filename],
                        change.change_type
                    ))
        
        # Also check for state-out-of-sync: files marked loaded but tables don't exist
        if existing_tables is not None:
            for filename, state in self.state.files.items():
                if state.table_name and state.table_name not in existing_tables:
                    # State says loaded but table doesn't exist - need to reload
                    if filename in current_files and filename not in [f[0] for f in to_load]:
                        to_load.append((
                            filename,
                            current_files[filename],
                            FileChangeType.NEW  # Treat as new since table is missing
                        ))
        
        return to_load
    
    def get_tables_to_delete(self) -> List[str]:
        """
        Get list of DuckDB tables that should be deleted (files removed).
        
        Returns:
            List of table names to delete
        """
        changes = self.detect_changes()
        tables = []
        
        for change in changes:
            if change.change_type == FileChangeType.DELETED:
                if change.old_state and change.old_state.table_name:
                    tables.append(change.old_state.table_name)
        
        return tables
    
    def mark_file_loaded(
        self,
        filename: str,
        table_name: str,
        sheet_type: Optional[str] = None,
        row_count: Optional[int] = None
    ) -> None:
        """
        Mark a file as successfully loaded.
        
        Args:
            filename: Name of the file
            table_name: DuckDB table name created
            sheet_type: Detected sheet type
            row_count: Number of rows loaded
        """
        file_path = self.data_dir / filename
        if not file_path.exists():
            return
        
        stat = file_path.stat()
        
        self.state.files[filename] = FileState(
            filename=filename,
            file_path=str(file_path),
            file_hash=self._compute_file_hash(file_path),
            file_size=stat.st_size,
            modified_time=datetime.fromtimestamp(stat.st_mtime).isoformat(),
            last_loaded=datetime.now().isoformat(),
            table_name=table_name,
            sheet_type=sheet_type,
            row_count=row_count
        )
    
    def mark_file_deleted(self, filename: str) -> None:
        """Remove a file from state."""
        if filename in self.state.files:
            del self.state.files[filename]
    
    def get_loaded_tables(self) -> Dict[str, str]:
        """
        Get mapping of filenames to table names.
        
        Returns:
            Dict of {filename: table_name}
        """
        return {
            filename: state.table_name
            for filename, state in self.state.files.items()
            if state.table_name
        }
    
    def needs_reload(self, existing_tables: Optional[List[str]] = None) -> bool:
        """
        Check if any files need to be reloaded.
        
        Args:
            existing_tables: Optional list of tables that actually exist in DuckDB.
                           If provided, also verifies state matches reality.
        """
        changes = self.detect_changes()
        
        # Check for file changes
        has_changes = any(
            c.change_type in [FileChangeType.NEW, FileChangeType.MODIFIED, FileChangeType.DELETED]
            for c in changes
        )
        
        if has_changes:
            return True
        
        # Also check if state says files are loaded but tables don't exist
        if existing_tables is not None:
            for filename, state in self.state.files.items():
                if state.table_name and state.table_name not in existing_tables:
                    return True  # State out of sync with reality
        
        return False
    
    def get_summary(self, existing_tables: Optional[List[str]] = None) -> Dict:
        """
        Get summary of current data state.
        
        Args:
            existing_tables: Optional list of tables in DuckDB for verification.
        """
        changes = self.detect_changes()
        
        return {
            "customer_id": self.customer.customer_id,
            "last_scan": self.state.last_scan,
            "total_files": len(self._get_current_files()),
            "loaded_files": len(self.state.files),
            "new_files": sum(1 for c in changes if c.change_type == FileChangeType.NEW),
            "modified_files": sum(1 for c in changes if c.change_type == FileChangeType.MODIFIED),
            "deleted_files": sum(1 for c in changes if c.change_type == FileChangeType.DELETED),
            "needs_reload": self.needs_reload(existing_tables)
        }


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def get_data_state_manager(customer_context) -> DataStateManager:
    """Get a DataStateManager for a customer."""
    return DataStateManager(customer_context)

