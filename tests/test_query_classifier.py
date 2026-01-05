"""
Tests for core/query_classifier.py - Query routing logic
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.query_classifier import QueryClassifier, QueryType


class TestDefinitionQueries:
    """Test classification of definition/concept questions."""
    
    @pytest.fixture
    def classifier(self):
        return QueryClassifier()
    
    def test_what_is_cgst(self, classifier):
        """'What is CGST?' should be a definition query."""
        result = classifier.classify("What is CGST?")
        assert result.query_type == QueryType.DEFINITION
        assert result.suggested_source == "llm"
    
    def test_what_is_sgst(self, classifier):
        """'What is SGST?' should be a definition query."""
        result = classifier.classify("What is SGST?")
        assert result.query_type == QueryType.DEFINITION
    
    def test_define_igst(self, classifier):
        """'Define IGST' should be a definition query."""
        result = classifier.classify("Define IGST")
        assert result.query_type == QueryType.DEFINITION
    
    def test_explain_input_tax_credit(self, classifier):
        """'Explain input tax credit' should be a definition query."""
        result = classifier.classify("Explain input tax credit")
        assert result.query_type == QueryType.DEFINITION
    
    def test_meaning_of_gst(self, classifier):
        """'What is the meaning of GST?' should be a definition query."""
        result = classifier.classify("What is the meaning of GST?")
        assert result.query_type == QueryType.DEFINITION


class TestRateLookupQueries:
    """Test classification of GST rate lookup questions."""
    
    @pytest.fixture
    def classifier(self):
        return QueryClassifier()
    
    def test_gst_rate_on_milk(self, classifier):
        """GST rate lookup should route to CSV."""
        result = classifier.classify("What is the GST rate on milk?")
        assert result.query_type == QueryType.RATE_LOOKUP
        assert result.suggested_source == "csv"
    
    def test_gst_percentage_on_laptops(self, classifier):
        """GST percentage question should be rate lookup."""
        result = classifier.classify("GST rate for laptops HSN 8471")
        assert result.query_type == QueryType.RATE_LOOKUP
    
    def test_hsn_code_rate(self, classifier):
        """HSN code rate lookup."""
        result = classifier.classify("GST rate for HSN 8471")
        assert result.query_type == QueryType.RATE_LOOKUP
    
    def test_sac_code_rate(self, classifier):
        """SAC code rate lookup."""
        result = classifier.classify("GST rate for SAC 9954")
        assert result.query_type == QueryType.RATE_LOOKUP
    
    def test_tax_rate_query(self, classifier):
        """Tax rate query should be rate lookup."""
        result = classifier.classify("What is tax rate on mobile phones?")
        assert result.query_type == QueryType.RATE_LOOKUP


class TestLegalRuleQueries:
    """Test classification of legal/compliance questions."""
    
    @pytest.fixture
    def classifier(self):
        return QueryClassifier()
    
    def test_due_date_gstr3b(self, classifier):
        """Filing due date should be legal rule."""
        result = classifier.classify("What is the due date for filing GSTR-3B?")
        assert result.query_type == QueryType.LEGAL_RULE
        assert result.suggested_source == "chromadb"
    
    def test_when_to_file_gst(self, classifier):
        """Filing deadline question should be legal rule."""
        result = classifier.classify("What is the due date for filing GSTR-1?")
        assert result.query_type == QueryType.LEGAL_RULE
    
    def test_penalty_late_filing(self, classifier):
        """Penalty question should be legal rule."""
        result = classifier.classify("What is the penalty for late filing of GSTR-1?")
        assert result.query_type == QueryType.LEGAL_RULE
    
    def test_registration_requirement(self, classifier):
        """Registration requirement should be legal rule."""
        result = classifier.classify("What are the GST registration requirements under Section 22?")
        assert result.query_type == QueryType.LEGAL_RULE
    
    def test_section_43b_compliance(self, classifier):
        """Section 43B compliance should be legal rule."""
        result = classifier.classify("What is Section 43B(h)?")
        assert result.query_type == QueryType.LEGAL_RULE


class TestDataQueries:
    """Test classification of user data questions."""
    
    @pytest.fixture
    def classifier(self):
        return QueryClassifier()
    
    def test_my_sales(self, classifier):
        """'My sales' should be data query."""
        result = classifier.classify("What are my total sales this month?")
        assert result.query_type == QueryType.DATA_QUERY
        assert result.suggested_source == "duckdb"
    
    def test_how_much_tax_paid(self, classifier):
        """Tax paid question should be data query."""
        result = classifier.classify("How much GST have I paid this quarter?")
        assert result.query_type == QueryType.DATA_QUERY
    
    def test_invoices_this_month(self, classifier):
        """Invoice count should be data query."""
        result = classifier.classify("Show my invoices from sales data")
        assert result.query_type == QueryType.DATA_QUERY
    
    def test_vendor_payment(self, classifier):
        """Vendor payment should be data query."""
        result = classifier.classify("Show my pending vendor payments")
        assert result.query_type == QueryType.DATA_QUERY
    
    def test_itc_balance(self, classifier):
        """ITC balance from data should be data query."""
        result = classifier.classify("Show my ITC balance from invoices")
        assert result.query_type == QueryType.DATA_QUERY


class TestEdgeCases:
    """Test edge cases and ambiguous queries."""
    
    @pytest.fixture
    def classifier(self):
        return QueryClassifier()
    
    def test_empty_query(self, classifier):
        """Empty query should have default classification."""
        result = classifier.classify("")
        assert result is not None
        assert result.query_type in QueryType.__members__.values()
    
    def test_gibberish(self, classifier):
        """Gibberish should still return a classification."""
        result = classifier.classify("asdf qwer zxcv")
        assert result is not None
    
    def test_mixed_query_cgst_rate_on_my_product(self, classifier):
        """Mixed query - should prioritize appropriately."""
        result = classifier.classify("What is CGST rate on my products?")
        # Could be rate lookup or data query - either is acceptable
        assert result.query_type in [QueryType.RATE_LOOKUP, QueryType.DATA_QUERY]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

