"""
Tests for core/data_engine.py - DuckDB operations
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestDataEngineConnection:
    """Test DuckDB connection and initialization."""
    
    def test_engine_initialization(self):
        """Data engine should initialize without errors."""
        from core.data_engine import DataEngine
        
        engine = DataEngine()
        assert engine is not None
    
    def test_connection_is_valid(self):
        """Connection should be valid."""
        from core.data_engine import DataEngine
        
        engine = DataEngine()
        # Run a simple query to verify connection
        result = engine.query("SELECT 1 as test")
        assert result is not None
    
    def test_list_tables(self):
        """Should be able to list tables."""
        from core.data_engine import DataEngine
        
        engine = DataEngine()
        tables = engine.list_tables()
        assert isinstance(tables, list)


class TestDataEngineQueries:
    """Test SQL query execution."""
    
    @pytest.fixture
    def engine(self):
        from core.data_engine import DataEngine
        return DataEngine()
    
    def test_simple_select(self, engine):
        """Simple SELECT should work."""
        result = engine.query("SELECT 42 as answer")
        assert result is not None
    
    def test_arithmetic_query(self, engine):
        """Arithmetic in SQL should work."""
        result = engine.query("SELECT 10000 * 0.18 as gst")
        assert result is not None
    
    def test_date_functions(self, engine):
        """Date functions should work."""
        result = engine.query("SELECT CURRENT_DATE as today")
        assert result is not None
    
    def test_invalid_query_handling(self, engine):
        """Invalid SQL should be handled gracefully."""
        try:
            result = engine.query("SELECT * FROM nonexistent_table_xyz")
        except Exception:
            pass  # Expected - invalid table


class TestSampleDataLoading:
    """Test loading sample company data."""
    
    @pytest.fixture
    def engine(self):
        from core.data_engine import DataEngine
        return DataEngine()
    
    def test_load_sample_sales(self, engine):
        """Should be able to query sample sales data if loaded."""
        sample_dir = Path(__file__).parent.parent / "workspace" / "sample_company"
        sales_file = sample_dir / "sales_register_2025.xlsx"
        
        if not sales_file.exists():
            pytest.skip("Sample data not generated yet")
        
        # Try to load the Excel file - sheet_name defaults to first sheet
        table_name = engine.load_excel(sales_file)
        assert table_name is not None
        
        # Query the loaded data
        count = engine.query(f"SELECT COUNT(*) as cnt FROM {table_name}")
        assert count is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

