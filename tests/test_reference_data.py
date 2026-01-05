"""
Tests for core/reference_data.py - Reference data loading and lookup
"""

import pytest
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestGoodsRatesLoading:
    """Test loading goods GST rates from CSV."""
    
    def test_load_goods_rates(self):
        from core.reference_data import load_goods_rates
        
        goods = load_goods_rates()
        assert len(goods) > 0, "No goods rates loaded"
        assert len(goods) >= 80, f"Expected 80+ goods, got {len(goods)}"
        
        # Check structure
        first = goods[0]
        assert 'hsn_code' in first
        assert 'gst_rate' in first
        assert 'item_name' in first
    
    def test_goods_rates_have_valid_rates(self):
        from core.reference_data import load_goods_rates, is_valid_gst_rate
        
        goods = load_goods_rates()
        for item in goods[:20]:  # Check first 20
            rate = int(item['gst_rate'])
            assert is_valid_gst_rate(rate), f"Invalid rate {rate} for {item['item_name']}"


class TestServicesRatesLoading:
    """Test loading services GST rates from CSV."""
    
    def test_load_services_rates(self):
        from core.reference_data import load_services_rates
        
        services = load_services_rates()
        assert len(services) > 0, "No services rates loaded"
        assert len(services) >= 40, f"Expected 40+ services, got {len(services)}"
        
        # Check structure
        first = services[0]
        assert 'sac_code' in first
        assert 'gst_rate' in first
        assert 'service_name' in first


class TestBlockedCreditsLoading:
    """Test loading Section 17(5) blocked credits."""
    
    def test_load_blocked_credits(self):
        from core.reference_data import load_blocked_credits
        
        blocked = load_blocked_credits()
        assert len(blocked) > 0, "No blocked credits loaded"
        assert len(blocked) >= 10, f"Expected 10+ blocked items, got {len(blocked)}"


class TestHSNLookup:
    """Test HSN code rate lookup."""
    
    def test_get_rate_for_hsn_milk(self):
        from core.reference_data import get_rate_for_hsn
        
        # Fresh milk - should be 0%
        milk = get_rate_for_hsn('0401')
        assert milk is not None, "HSN 0401 (milk) not found"
        assert int(milk['rate']) == 0, f"Milk should be 0%, got {milk['rate']}%"
    
    def test_get_rate_for_hsn_laptop(self):
        from core.reference_data import get_rate_for_hsn
        
        # Laptops/computers (HSN 8471) - rate as per our data
        laptop = get_rate_for_hsn('8471')
        assert laptop is not None, "HSN 8471 (laptops) not found"
        # Rate can vary - just check it's a valid slab
        assert int(laptop['rate']) in [0, 5, 12, 18, 28], f"Invalid rate: {laptop['rate']}%"
    
    def test_get_rate_for_hsn_not_found(self):
        from core.reference_data import get_rate_for_hsn
        
        # Invalid HSN
        result = get_rate_for_hsn('9999999')
        assert result is None


class TestSACLookup:
    """Test SAC code rate lookup."""
    
    def test_get_rate_for_sac_education(self):
        from core.reference_data import get_rate_for_sac
        
        # Education - should be 0%
        education = get_rate_for_sac('9992')
        assert education is not None, "SAC 9992 (education) not found"
        assert int(education['rate']) == 0, f"Education should be 0%, got {education['rate']}%"
    
    def test_get_rate_for_sac_not_found(self):
        from core.reference_data import get_rate_for_sac
        
        result = get_rate_for_sac('0000')
        assert result is None


class TestNameSearch:
    """Test searching rates by item name."""
    
    def test_search_by_name_milk(self):
        from core.reference_data import search_rate_by_name
        
        result = search_rate_by_name('milk')
        assert result is not None
        assert result['rate'] == 0
    
    def test_search_by_name_software(self):
        from core.reference_data import search_rate_by_name
        
        result = search_rate_by_name('software')
        # May be goods or services
        assert result is not None


class TestGSTSlabs:
    """Test GST slab loading from CSV."""
    
    def test_load_gst_slabs(self):
        from core.reference_data import load_gst_slabs
        
        slabs = load_gst_slabs()
        assert len(slabs) >= 4, "Should have at least 4 slabs (0%, 5%, 18%, 28%)"
    
    def test_get_gst_slabs(self):
        from core.reference_data import get_gst_slabs
        
        slabs = get_gst_slabs()
        assert "exempt" in slabs
        assert slabs["exempt"]["rate"] == 0
        assert "standard" in slabs
        assert slabs["standard"]["rate"] == 18
    
    def test_get_msme_classification(self):
        from core.reference_data import get_msme_classification
        
        msme = get_msme_classification()
        assert msme is not None
        assert "micro" in msme
        assert "small" in msme
        assert "medium" in msme


class TestStateCodes:
    """Test state codes loading."""
    
    def test_load_state_codes(self):
        from core.reference_data import load_state_codes
        
        states = load_state_codes()
        assert len(states) >= 30, "Should have 30+ states/UTs"
    
    def test_get_state_codes(self):
        from core.reference_data import get_state_codes
        
        states = get_state_codes()
        assert "27" in states  # Maharashtra
        assert states["27"] == "Maharashtra"
    
    def test_get_state_name(self):
        from core.reference_data import get_state_name
        
        assert get_state_name("27") == "Maharashtra"
        assert get_state_name("29") == "Karnataka"


class TestValidationHelpers:
    """Test validation helper functions."""
    
    def test_is_valid_gst_rate(self):
        from core.reference_data import is_valid_gst_rate
        
        assert is_valid_gst_rate(0) is True
        assert is_valid_gst_rate(5) is True
        assert is_valid_gst_rate(12) is True
        assert is_valid_gst_rate(18) is True
        assert is_valid_gst_rate(28) is True
        assert is_valid_gst_rate(15) is False
        assert is_valid_gst_rate(100) is False
    
    def test_get_msme_category(self):
        from core.reference_data import get_msme_category
        
        assert get_msme_category(10000000) == 'micro'  # ₹1 Cr
        assert get_msme_category(100000000) == 'small'  # ₹10 Cr
        assert get_msme_category(1000000000) == 'medium'  # ₹100 Cr
        assert get_msme_category(5000000000) == 'large'  # ₹500 Cr


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

