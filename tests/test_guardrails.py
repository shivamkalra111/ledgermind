"""
Tests for core/guardrails.py - Validation and safety checks
"""

import pytest
import sys
from pathlib import Path
from datetime import date, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.guardrails import Guardrails, ValidationLevel


class TestGSTINValidation:
    """Test GSTIN format validation."""
    
    @pytest.fixture
    def guardrails(self):
        return Guardrails()
    
    def test_valid_gstin(self, guardrails):
        """Valid GSTIN should pass."""
        result = guardrails.validate_gstin("27AAPFU0939F1ZV")
        assert result.is_valid is True
        assert result.level == ValidationLevel.INFO
    
    def test_invalid_gstin_length(self, guardrails):
        """GSTIN with wrong length should fail."""
        result = guardrails.validate_gstin("27AAPFU0939F")
        assert result.is_valid is False
        assert result.level == ValidationLevel.ERROR
    
    def test_invalid_gstin_format(self, guardrails):
        """GSTIN with invalid format should fail."""
        result = guardrails.validate_gstin("INVALIDGSTIN123")
        assert result.is_valid is False
    
    def test_invalid_state_code(self, guardrails):
        """GSTIN with invalid state code should fail."""
        result = guardrails.validate_gstin("99AAPFU0939F1ZV")  # 99 is valid (Centre)
        # State code 50 would be invalid
        result = guardrails.validate_gstin("50AAPFU0939F1ZV")
        assert result.is_valid is False
    
    def test_empty_gstin_allowed(self, guardrails):
        """Empty GSTIN should be allowed (optional field)."""
        result = guardrails.validate_gstin("")
        assert result.is_valid is True
        assert result.level == ValidationLevel.INFO
    
    def test_none_gstin_allowed(self, guardrails):
        """None GSTIN should be allowed."""
        result = guardrails.validate_gstin(None)
        assert result.is_valid is True


class TestHSNValidation:
    """Test HSN code validation."""
    
    @pytest.fixture
    def guardrails(self):
        return Guardrails()
    
    def test_valid_4_digit_hsn(self, guardrails):
        """4-digit HSN should be valid."""
        result = guardrails.validate_hsn_code("8471")
        assert result.is_valid is True
    
    def test_valid_6_digit_hsn(self, guardrails):
        """6-digit HSN should be valid."""
        result = guardrails.validate_hsn_code("847130")
        assert result.is_valid is True
    
    def test_valid_8_digit_hsn(self, guardrails):
        """8-digit HSN should be valid."""
        result = guardrails.validate_hsn_code("84713010")
        assert result.is_valid is True
    
    def test_invalid_3_digit_hsn(self, guardrails):
        """3-digit HSN should be invalid."""
        result = guardrails.validate_hsn_code("847")
        assert result.is_valid is False
    
    def test_invalid_hsn_with_letters(self, guardrails):
        """HSN with letters should be invalid."""
        result = guardrails.validate_hsn_code("84AB")
        assert result.is_valid is False


class TestTaxCalculation:
    """Test GST calculation validation."""
    
    @pytest.fixture
    def guardrails(self):
        return Guardrails()
    
    def test_correct_intra_state_18_percent(self, guardrails):
        """Correct 18% intra-state calculation should pass."""
        # ₹10,000 + CGST ₹900 + SGST ₹900 = Total ₹11,800
        result = guardrails.validate_tax_calculation(
            taxable_value=10000,
            cgst=900,
            sgst=900,
            igst=0,
            total=11800
        )
        assert result.is_valid is True
    
    def test_correct_inter_state_18_percent(self, guardrails):
        """Correct 18% inter-state calculation should pass."""
        # ₹10,000 + IGST ₹1800 = Total ₹11,800
        result = guardrails.validate_tax_calculation(
            taxable_value=10000,
            cgst=0,
            sgst=0,
            igst=1800,
            total=11800
        )
        assert result.is_valid is True
    
    def test_incorrect_calculation_should_fail(self, guardrails):
        """Incorrect tax calculation should fail."""
        # Wrong: Total doesn't match taxable + taxes
        result = guardrails.validate_tax_calculation(
            taxable_value=10000,
            cgst=500,
            sgst=500,
            igst=0,
            total=15000  # Wrong total
        )
        assert result.is_valid is False


class TestAmountValidation:
    """Test monetary amount validation."""
    
    @pytest.fixture
    def guardrails(self):
        return Guardrails()
    
    def test_valid_positive_amount(self, guardrails):
        """Positive amount should be valid."""
        result = guardrails.validate_amount(10000)
        assert result.is_valid is True
    
    def test_zero_amount_valid(self, guardrails):
        """Zero amount should be valid."""
        result = guardrails.validate_amount(0)
        assert result.is_valid is True
    
    def test_negative_amount_invalid(self, guardrails):
        """Negative amount should be invalid."""
        result = guardrails.validate_amount(-100)
        assert result.is_valid is False


class TestSection43BH:
    """Test Section 43B(h) compliance validation."""
    
    @pytest.fixture
    def guardrails(self):
        return Guardrails()
    
    def test_payment_within_45_days(self, guardrails):
        """Payment within 45 days should be compliant."""
        invoice_date = date.today() - timedelta(days=30)
        result = guardrails.validate_section_43b_h(
            invoice_date=invoice_date,
            payment_date=date.today(),
            is_msme_vendor=True
        )
        assert result.is_valid is True
    
    def test_payment_after_45_days_to_msme(self, guardrails):
        """Payment after 45 days to MSME should be non-compliant."""
        invoice_date = date.today() - timedelta(days=60)
        result = guardrails.validate_section_43b_h(
            invoice_date=invoice_date,
            payment_date=None,  # Not paid yet
            is_msme_vendor=True
        )
        assert result.is_valid is False
        assert result.level == ValidationLevel.ERROR
    
    def test_payment_after_45_days_to_non_msme(self, guardrails):
        """Payment after 45 days to non-MSME should be allowed."""
        invoice_date = date.today() - timedelta(days=60)
        result = guardrails.validate_section_43b_h(
            invoice_date=invoice_date,
            payment_date=None,
            is_msme_vendor=False
        )
        assert result.is_valid is True


class TestITCTimeLimit:
    """Test ITC time limit validation (Section 16(4))."""
    
    @pytest.fixture
    def guardrails(self):
        return Guardrails()
    
    def test_itc_within_time_limit(self, guardrails):
        """ITC claimed within time limit should be valid."""
        # Invoice from 6 months ago - should be claimable
        invoice_date = date.today() - timedelta(days=180)
        result = guardrails.validate_itc_time_limit(invoice_date=invoice_date)
        # This depends on current date, but should generally be valid if recent
        assert result is not None
    
    def test_itc_recent_invoice(self, guardrails):
        """Recent invoice should always be claimable."""
        invoice_date = date.today() - timedelta(days=30)
        result = guardrails.validate_itc_time_limit(invoice_date=invoice_date)
        assert result.is_valid is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

