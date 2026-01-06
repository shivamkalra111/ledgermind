"""
Tests for Smart Data State Management

Verifies:
1. File change detection (new, modified, deleted)
2. Hash-based change tracking
3. State persistence
4. Smart loading logic
"""

import pytest
import tempfile
import shutil
import time
from pathlib import Path

from core.data_state import (
    DataStateManager,
    DataState,
    FileState,
    FileChange,
    FileChangeType,
)
from core.customer import CustomerContext


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def temp_workspace():
    """Create a temporary workspace directory."""
    temp_dir = tempfile.mkdtemp(prefix="ledgermind_test_")
    yield Path(temp_dir)
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def customer(temp_workspace, monkeypatch):
    """Create a test customer with temp workspace."""
    import core.customer as customer_module
    monkeypatch.setattr(customer_module, "WORKSPACE_DIR", temp_workspace)
    
    ctx = CustomerContext("test_company")
    ctx.ensure_exists()
    return ctx


@pytest.fixture
def state_manager(customer):
    """Get data state manager for test customer."""
    return customer.get_data_state_manager()


def create_test_csv(path: Path, content: str = "col1,col2\n1,2\n3,4") -> Path:
    """Create a test CSV file."""
    path.write_text(content)
    return path


def create_test_xlsx(path: Path) -> Path:
    """Create a minimal test Excel file."""
    # Create a minimal Excel file using openpyxl
    try:
        from openpyxl import Workbook
        wb = Workbook()
        ws = wb.active
        ws.append(["col1", "col2"])
        ws.append([1, 2])
        wb.save(path)
    except ImportError:
        # Fallback: create empty file
        path.write_bytes(b"PK")  # Minimal zip header
    return path


# =============================================================================
# FILE STATE TESTS
# =============================================================================

class TestFileState:
    """Test FileState dataclass."""
    
    def test_create_file_state(self):
        """Test creating a file state."""
        state = FileState(
            filename="test.csv",
            file_path="/path/to/test.csv",
            file_hash="abc123",
            file_size=100,
            modified_time="2026-01-01T00:00:00",
            last_loaded="2026-01-01T00:00:00"
        )
        
        assert state.filename == "test.csv"
        assert state.file_hash == "abc123"
        assert state.table_name is None
    
    def test_to_dict(self):
        """Test serialization."""
        state = FileState(
            filename="test.csv",
            file_path="/path/to/test.csv",
            file_hash="abc123",
            file_size=100,
            modified_time="2026-01-01T00:00:00",
            last_loaded="2026-01-01T00:00:00",
            table_name="test_table"
        )
        
        data = state.to_dict()
        assert data["filename"] == "test.csv"
        assert data["table_name"] == "test_table"
    
    def test_from_dict(self):
        """Test deserialization."""
        data = {
            "filename": "test.csv",
            "file_path": "/path/to/test.csv",
            "file_hash": "abc123",
            "file_size": 100,
            "modified_time": "2026-01-01T00:00:00",
            "last_loaded": "2026-01-01T00:00:00",
            "table_name": "test_table",
            "sheet_type": "sales_register",
            "row_count": 50
        }
        
        state = FileState.from_dict(data)
        assert state.filename == "test.csv"
        assert state.sheet_type == "sales_register"
        assert state.row_count == 50


# =============================================================================
# DATA STATE TESTS
# =============================================================================

class TestDataState:
    """Test DataState dataclass."""
    
    def test_create_data_state(self):
        """Test creating a data state."""
        state = DataState(customer_id="test")
        assert state.customer_id == "test"
        assert state.files == {}
    
    def test_to_dict_and_back(self):
        """Test round-trip serialization."""
        state = DataState(customer_id="test")
        state.files["test.csv"] = FileState(
            filename="test.csv",
            file_path="/path/test.csv",
            file_hash="abc",
            file_size=100,
            modified_time="2026-01-01T00:00:00",
            last_loaded="2026-01-01T00:00:00"
        )
        
        data = state.to_dict()
        restored = DataState.from_dict(data)
        
        assert restored.customer_id == "test"
        assert "test.csv" in restored.files


# =============================================================================
# DATA STATE MANAGER TESTS
# =============================================================================

class TestDataStateManager:
    """Test DataStateManager class."""
    
    def test_init(self, state_manager, customer):
        """Test manager initialization."""
        assert state_manager.customer == customer
        assert state_manager.data_dir == customer.data_dir
    
    def test_empty_state(self, state_manager):
        """Test with no files."""
        changes = state_manager.detect_changes()
        assert changes == []
        assert not state_manager.needs_reload()
    
    def test_detect_new_file(self, state_manager, customer):
        """Test detecting a new file."""
        # Create a new file
        create_test_csv(customer.data_dir / "sales.csv")
        
        changes = state_manager.detect_changes()
        assert len(changes) == 1
        assert changes[0].change_type == FileChangeType.NEW
        assert changes[0].filename == "sales.csv"
        assert state_manager.needs_reload()
    
    def test_detect_modified_file(self, state_manager, customer):
        """Test detecting a modified file."""
        # Create and mark as loaded
        csv_path = create_test_csv(customer.data_dir / "sales.csv")
        state_manager.mark_file_loaded("sales.csv", "sales_table")
        state_manager.save()
        
        # Reload manager to simulate restart
        state_manager._state = None
        
        # Modify the file
        time.sleep(0.1)  # Ensure different timestamp
        csv_path.write_text("col1,col2\n5,6\n7,8")
        
        changes = state_manager.detect_changes()
        modified = [c for c in changes if c.change_type == FileChangeType.MODIFIED]
        assert len(modified) == 1
        assert modified[0].filename == "sales.csv"
    
    def test_detect_deleted_file(self, state_manager, customer):
        """Test detecting a deleted file."""
        # Create and mark as loaded
        csv_path = create_test_csv(customer.data_dir / "sales.csv")
        state_manager.mark_file_loaded("sales.csv", "sales_table")
        state_manager.save()
        
        # Delete the file
        csv_path.unlink()
        
        # Reload manager
        state_manager._state = None
        
        changes = state_manager.detect_changes()
        deleted = [c for c in changes if c.change_type == FileChangeType.DELETED]
        assert len(deleted) == 1
        assert deleted[0].filename == "sales.csv"
        assert deleted[0].old_state.table_name == "sales_table"
    
    def test_detect_unchanged_file(self, state_manager, customer):
        """Test detecting unchanged file."""
        # Create and mark as loaded
        create_test_csv(customer.data_dir / "sales.csv")
        state_manager.mark_file_loaded("sales.csv", "sales_table")
        state_manager.save()
        
        # Reload manager
        state_manager._state = None
        
        changes = state_manager.detect_changes()
        unchanged = [c for c in changes if c.change_type == FileChangeType.UNCHANGED]
        assert len(unchanged) == 1
    
    def test_mark_file_loaded(self, state_manager, customer):
        """Test marking a file as loaded."""
        create_test_csv(customer.data_dir / "sales.csv")
        
        state_manager.mark_file_loaded(
            filename="sales.csv",
            table_name="sales_table",
            sheet_type="sales_register",
            row_count=100
        )
        
        assert "sales.csv" in state_manager.state.files
        file_state = state_manager.state.files["sales.csv"]
        assert file_state.table_name == "sales_table"
        assert file_state.sheet_type == "sales_register"
        assert file_state.row_count == 100
    
    def test_save_and_load(self, state_manager, customer):
        """Test state persistence."""
        create_test_csv(customer.data_dir / "sales.csv")
        state_manager.mark_file_loaded("sales.csv", "sales_table")
        state_manager.save()
        
        # Create new manager
        new_manager = DataStateManager(customer)
        assert "sales.csv" in new_manager.state.files
        assert new_manager.state.files["sales.csv"].table_name == "sales_table"
    
    def test_get_files_to_load(self, state_manager, customer):
        """Test getting list of files to load."""
        # Create files
        create_test_csv(customer.data_dir / "new.csv")
        create_test_csv(customer.data_dir / "old.csv")
        
        # Mark old as loaded
        state_manager.mark_file_loaded("old.csv", "old_table")
        state_manager.save()
        
        # Reload
        state_manager._state = None
        
        to_load = state_manager.get_files_to_load()
        filenames = [f[0] for f in to_load]
        
        assert "new.csv" in filenames
        assert "old.csv" not in filenames
    
    def test_get_tables_to_delete(self, state_manager, customer):
        """Test getting tables to delete for removed files."""
        # Create and load
        csv_path = create_test_csv(customer.data_dir / "removed.csv")
        state_manager.mark_file_loaded("removed.csv", "removed_table")
        state_manager.save()
        
        # Delete file
        csv_path.unlink()
        
        # Reload
        state_manager._state = None
        
        tables = state_manager.get_tables_to_delete()
        assert "removed_table" in tables
    
    def test_get_loaded_tables(self, state_manager, customer):
        """Test getting loaded tables mapping."""
        create_test_csv(customer.data_dir / "a.csv")
        create_test_csv(customer.data_dir / "b.csv")
        
        state_manager.mark_file_loaded("a.csv", "table_a")
        state_manager.mark_file_loaded("b.csv", "table_b")
        
        tables = state_manager.get_loaded_tables()
        assert tables == {"a.csv": "table_a", "b.csv": "table_b"}
    
    def test_get_summary(self, state_manager, customer):
        """Test getting state summary."""
        create_test_csv(customer.data_dir / "new.csv")
        create_test_csv(customer.data_dir / "loaded.csv")
        state_manager.mark_file_loaded("loaded.csv", "loaded_table")
        
        summary = state_manager.get_summary()
        assert summary["total_files"] == 2
        assert summary["loaded_files"] == 1
        assert summary["new_files"] == 1
        assert summary["needs_reload"] is True


# =============================================================================
# MULTIPLE FILE TYPES TESTS
# =============================================================================

class TestMultipleFileTypes:
    """Test handling multiple file types."""
    
    def test_csv_and_xlsx(self, state_manager, customer):
        """Test detecting both CSV and XLSX files."""
        create_test_csv(customer.data_dir / "data.csv")
        create_test_xlsx(customer.data_dir / "report.xlsx")
        
        changes = state_manager.detect_changes()
        filenames = [c.filename for c in changes]
        
        assert "data.csv" in filenames
        assert "report.xlsx" in filenames
    
    def test_ignores_other_extensions(self, state_manager, customer):
        """Test that non-data files are ignored."""
        create_test_csv(customer.data_dir / "data.csv")
        (customer.data_dir / "notes.txt").write_text("notes")
        (customer.data_dir / "image.png").write_bytes(b"PNG")
        
        changes = state_manager.detect_changes()
        filenames = [c.filename for c in changes]
        
        assert "data.csv" in filenames
        assert "notes.txt" not in filenames
        assert "image.png" not in filenames


# =============================================================================
# EDGE CASES
# =============================================================================

class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_empty_data_dir(self, state_manager):
        """Test with empty data directory."""
        assert state_manager.get_files_to_load() == []
        assert not state_manager.needs_reload()
    
    def test_corrupted_state_file(self, customer):
        """Test recovery from corrupted state file."""
        # Write invalid JSON
        state_file = customer.root_dir / "data_state.json"
        state_file.write_text("{invalid json")
        
        # Should recover gracefully
        manager = DataStateManager(customer)
        assert manager.state.customer_id == customer.customer_id
        assert manager.state.files == {}
    
    def test_mark_nonexistent_file(self, state_manager, customer):
        """Test marking a file that doesn't exist."""
        # Should not raise, just do nothing
        state_manager.mark_file_loaded("nonexistent.csv", "table")
        assert "nonexistent.csv" not in state_manager.state.files

