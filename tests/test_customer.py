"""
Tests for Customer Isolation Module

Verifies:
1. Customer creation and deletion
2. Customer workspace isolation
3. Profile management
4. Data engine scoping
"""

import pytest
import tempfile
import shutil
from pathlib import Path

from core.customer import (
    CustomerContext,
    CustomerManager,
    CustomerProfile,
    get_customer,
    get_customer_manager,
)


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def temp_workspace():
    """Create a temporary workspace directory."""
    temp_dir = tempfile.mkdtemp(prefix="ledgermind_test_")
    yield Path(temp_dir)
    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def manager(temp_workspace, monkeypatch):
    """Customer manager with temporary workspace."""
    # Patch WORKSPACE_DIR
    import core.customer as customer_module
    monkeypatch.setattr(customer_module, "WORKSPACE_DIR", temp_workspace)
    return CustomerManager(temp_workspace)


# =============================================================================
# CUSTOMER CONTEXT TESTS
# =============================================================================

class TestCustomerContext:
    """Test CustomerContext class."""
    
    def test_create_customer_context(self, temp_workspace, monkeypatch):
        """Test creating a customer context."""
        import core.customer as customer_module
        monkeypatch.setattr(customer_module, "WORKSPACE_DIR", temp_workspace)
        
        customer = CustomerContext("test_company")
        assert customer.customer_id == "test_company"
        assert customer.root_dir == temp_workspace / "test_company"
        assert customer.data_dir == temp_workspace / "test_company" / "data"
    
    def test_customer_id_normalization(self, temp_workspace, monkeypatch):
        """Test customer ID normalization."""
        import core.customer as customer_module
        monkeypatch.setattr(customer_module, "WORKSPACE_DIR", temp_workspace)
        
        # Spaces converted to underscores
        c1 = CustomerContext("Acme Corp")
        assert c1.customer_id == "acme_corp"
        
        # Dashes converted to underscores
        c2 = CustomerContext("test-company")
        assert c2.customer_id == "test_company"
        
        # Uppercase converted to lowercase
        c3 = CustomerContext("TestCOMPANY")
        assert c3.customer_id == "testcompany"
    
    def test_customer_id_validation(self, temp_workspace, monkeypatch):
        """Test customer ID validation."""
        import core.customer as customer_module
        monkeypatch.setattr(customer_module, "WORKSPACE_DIR", temp_workspace)
        
        # Empty ID
        with pytest.raises(ValueError, match="cannot be empty"):
            CustomerContext("")
        
        # Reserved ID
        with pytest.raises(ValueError, match="Reserved"):
            CustomerContext("admin")
        
        # Too long
        with pytest.raises(ValueError, match="too long"):
            CustomerContext("a" * 100)
    
    def test_ensure_exists(self, temp_workspace, monkeypatch):
        """Test workspace creation."""
        import core.customer as customer_module
        monkeypatch.setattr(customer_module, "WORKSPACE_DIR", temp_workspace)
        
        customer = CustomerContext("new_company")
        assert not customer.exists()
        
        customer.ensure_exists()
        
        assert customer.exists()
        assert customer.root_dir.exists()
        assert customer.data_dir.exists()
        assert customer.profile_path.exists()
    
    def test_profile_loading(self, temp_workspace, monkeypatch):
        """Test profile loading and saving."""
        import core.customer as customer_module
        monkeypatch.setattr(customer_module, "WORKSPACE_DIR", temp_workspace)
        
        customer = CustomerContext("profile_test")
        customer.ensure_exists()
        
        # Default profile
        profile = customer.profile
        assert profile.customer_id == "profile_test"
        assert profile.company_name == "Profile Test"
        
        # Update profile
        customer.update_profile(
            company_name="New Name",
            gstin="29AABCU9603R1ZM"
        )
        
        # Reload
        customer2 = CustomerContext("profile_test")
        assert customer2.profile.company_name == "New Name"
        assert customer2.profile.gstin == "29AABCU9603R1ZM"
    
    def test_context_manager(self, temp_workspace, monkeypatch):
        """Test context manager usage."""
        import core.customer as customer_module
        monkeypatch.setattr(customer_module, "WORKSPACE_DIR", temp_workspace)
        
        with CustomerContext("context_test") as customer:
            assert customer.exists()
            assert customer.data_dir.exists()
    
    def test_delete_customer(self, temp_workspace, monkeypatch):
        """Test customer deletion."""
        import core.customer as customer_module
        monkeypatch.setattr(customer_module, "WORKSPACE_DIR", temp_workspace)
        
        customer = CustomerContext("delete_test")
        customer.ensure_exists()
        assert customer.exists()
        
        customer.delete()
        assert not customer.exists()
        assert not customer.root_dir.exists()


# =============================================================================
# CUSTOMER MANAGER TESTS
# =============================================================================

class TestCustomerManager:
    """Test CustomerManager class."""
    
    def test_list_empty(self, manager):
        """Test listing with no customers."""
        customers = manager.list_customers()
        assert customers == []
    
    def test_create_customer(self, manager):
        """Test creating a customer."""
        customer = manager.create_customer(
            "acme_corp",
            company_name="Acme Corporation",
            gstin="29AABCU9603R1ZM",
            business_type="trading",
            turnover_category="small"
        )
        
        assert customer.customer_id == "acme_corp"
        assert customer.profile.company_name == "Acme Corporation"
        assert customer.profile.gstin == "29AABCU9603R1ZM"
        assert customer.profile.business_type == "trading"
        assert customer.profile.turnover_category == "small"
    
    def test_list_customers(self, manager):
        """Test listing customers."""
        manager.create_customer("company_a", company_name="Company A")
        manager.create_customer("company_b", company_name="Company B")
        
        customers = manager.list_customers()
        assert len(customers) == 2
        
        names = [c["company_name"] for c in customers]
        assert "Company A" in names
        assert "Company B" in names
    
    def test_duplicate_customer(self, manager):
        """Test creating duplicate customer."""
        manager.create_customer("unique_company")
        
        with pytest.raises(ValueError, match="already exists"):
            manager.create_customer("unique_company")
    
    def test_get_customer(self, manager):
        """Test getting a customer."""
        manager.create_customer("get_test", company_name="Get Test Corp")
        
        customer = manager.get_customer("get_test")
        assert customer.customer_id == "get_test"
    
    def test_delete_customer(self, manager):
        """Test deleting a customer."""
        manager.create_customer("to_delete")
        assert manager.customer_exists("to_delete")
        
        # Without confirmation
        with pytest.raises(ValueError, match="confirm"):
            manager.delete_customer("to_delete")
        
        # With confirmation
        result = manager.delete_customer("to_delete", confirm=True)
        assert result is True
        assert not manager.customer_exists("to_delete")
    
    def test_customer_exists(self, manager):
        """Test customer existence check."""
        assert not manager.customer_exists("nonexistent")
        
        manager.create_customer("exists_test")
        assert manager.customer_exists("exists_test")


# =============================================================================
# DATA ISOLATION TESTS
# =============================================================================

class TestDataIsolation:
    """Test data isolation between customers."""
    
    def test_separate_duckdb_files(self, manager):
        """Test that each customer has separate DuckDB file."""
        c1 = manager.create_customer("company_1")
        c2 = manager.create_customer("company_2")
        
        assert c1.duckdb_path != c2.duckdb_path
        assert "company_1" in str(c1.duckdb_path)
        assert "company_2" in str(c2.duckdb_path)
    
    def test_separate_data_directories(self, manager):
        """Test that each customer has separate data directory."""
        c1 = manager.create_customer("data_1")
        c2 = manager.create_customer("data_2")
        
        assert c1.data_dir != c2.data_dir
        assert c1.data_dir.parent != c2.data_dir.parent
    
    def test_data_engine_isolation(self, manager):
        """Test that data engines are isolated."""
        c1 = manager.create_customer("engine_1")
        c2 = manager.create_customer("engine_2")
        
        engine1 = c1.get_data_engine()
        engine2 = c2.get_data_engine()
        
        # Create table in engine1
        engine1.execute("CREATE TABLE test_table (id INTEGER)")
        engine1.execute("INSERT INTO test_table VALUES (1)")
        
        # Verify table exists in engine1
        tables1 = engine1.list_tables()
        assert "test_table" in tables1
        
        # Verify table does NOT exist in engine2
        tables2 = engine2.list_tables()
        assert "test_table" not in tables2
        
        # Cleanup
        c1.close()
        c2.close()


# =============================================================================
# PROFILE TESTS
# =============================================================================

class TestCustomerProfile:
    """Test CustomerProfile dataclass."""
    
    def test_profile_defaults(self):
        """Test profile default values."""
        profile = CustomerProfile(
            customer_id="test",
            company_name="Test Company"
        )
        
        assert profile.business_type == "trading"
        assert profile.turnover_category == "micro"
        assert profile.state_code == "27"
        assert profile.gstin is None
    
    def test_profile_to_dict(self):
        """Test profile serialization."""
        profile = CustomerProfile(
            customer_id="test",
            company_name="Test Company",
            gstin="29AABCU9603R1ZM"
        )
        
        data = profile.to_dict()
        assert data["customer_id"] == "test"
        assert data["company_name"] == "Test Company"
        assert data["gstin"] == "29AABCU9603R1ZM"
    
    def test_profile_from_dict(self):
        """Test profile deserialization."""
        data = {
            "customer_id": "test",
            "company_name": "Test Company",
            "gstin": "29AABCU9603R1ZM",
            "business_type": "services",
            "turnover_category": "small",
            "state_code": "27",
            "created_at": "2026-01-01T00:00:00",
            "last_accessed": "2026-01-01T00:00:00"
        }
        
        profile = CustomerProfile.from_dict(data)
        assert profile.customer_id == "test"
        assert profile.business_type == "services"
        assert profile.turnover_category == "small"


# =============================================================================
# FILE LISTING TESTS
# =============================================================================

class TestFileOperations:
    """Test file operations within customer workspace."""
    
    def test_list_data_files_empty(self, manager):
        """Test listing files when empty."""
        customer = manager.create_customer("empty_files")
        files = customer.list_data_files()
        assert files == []
    
    def test_list_data_files(self, manager):
        """Test listing data files."""
        customer = manager.create_customer("with_files")
        
        # Create test files
        (customer.data_dir / "sales.xlsx").touch()
        (customer.data_dir / "purchases.csv").touch()
        (customer.data_dir / "notes.txt").touch()  # Should be ignored
        
        files = customer.list_data_files()
        
        # Only Excel/CSV files
        assert len(files) == 2
        names = [f["name"] for f in files]
        assert "sales.xlsx" in names
        assert "purchases.csv" in names
        assert "notes.txt" not in names
    
    def test_get_data_file_path(self, manager):
        """Test getting file path."""
        customer = manager.create_customer("path_test")
        
        path = customer.get_data_file_path("sales.xlsx")
        assert path == customer.data_dir / "sales.xlsx"

