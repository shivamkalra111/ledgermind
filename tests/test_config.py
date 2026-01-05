"""
Tests for config.py - Configuration and data loading
"""

import pytest
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestConfigPaths:
    """Test that all configured paths exist."""
    
    def test_base_dir_exists(self):
        from config import BASE_DIR
        assert BASE_DIR.exists(), f"BASE_DIR not found: {BASE_DIR}"
    
    def test_db_dir_exists(self):
        from config import DB_DIR
        assert DB_DIR.exists(), f"DB_DIR not found: {DB_DIR}"
    
    def test_knowledge_dir_exists(self):
        from config import KNOWLEDGE_DIR
        assert KNOWLEDGE_DIR.exists(), f"KNOWLEDGE_DIR not found: {KNOWLEDGE_DIR}"
    
    def test_workspace_dir_exists(self):
        from config import WORKSPACE_DIR
        assert WORKSPACE_DIR.exists(), f"WORKSPACE_DIR not found: {WORKSPACE_DIR}"


class TestGSTDataLoading:
    """Test GST reference data loading."""
    
    def test_load_goods_rates(self):
        from config import load_goods_rates
        
        goods = load_goods_rates()
        assert len(goods) > 0, "No goods rates loaded"
        assert len(goods) >= 80, f"Expected 80+ goods, got {len(goods)}"
        
        # Check structure
        first = goods[0]
        assert 'hsn_code' in first
        assert 'gst_rate' in first
        assert 'item_name' in first
    
    def test_load_services_rates(self):
        from config import load_services_rates
        
        services = load_services_rates()
        assert len(services) > 0, "No services rates loaded"
        assert len(services) >= 40, f"Expected 40+ services, got {len(services)}"
        
        # Check structure
        first = services[0]
        assert 'sac_code' in first
        assert 'gst_rate' in first
        assert 'service_name' in first
    
    def test_load_blocked_credits(self):
        from config import load_blocked_credits
        
        blocked = load_blocked_credits()
        assert len(blocked) > 0, "No blocked credits loaded"
        assert len(blocked) >= 10, f"Expected 10+ blocked items, got {len(blocked)}"
    
    def test_get_rate_for_hsn(self):
        from config import get_rate_for_hsn
        
        # Fresh milk - should be 0%
        milk = get_rate_for_hsn('0401')
        assert milk is not None, "HSN 0401 (milk) not found"
        assert int(milk['rate']) == 0, f"Milk should be 0%, got {milk['rate']}%"
    
    def test_get_rate_for_sac(self):
        from config import get_rate_for_sac
        
        # Education - should be 0%
        education = get_rate_for_sac('9992')
        assert education is not None, "SAC 9992 (education) not found"
        assert int(education['rate']) == 0, f"Education should be 0%, got {education['rate']}%"


class TestGSTDataFile:
    """Test master GST data JSON file."""
    
    def test_gst_data_file_exists(self):
        from config import GST_DATA_FILE
        assert GST_DATA_FILE.exists(), f"GST data file not found: {GST_DATA_FILE}"
    
    def test_get_gst_data(self):
        from config import get_gst_data
        
        data = get_gst_data()
        assert data is not None
        assert 'slabs' in data or len(data) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

