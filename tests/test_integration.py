"""
Integration tests - End-to-end scenarios

These tests verify that all components work together correctly.
Run with: pytest tests/test_integration.py -v
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.mark.integration
class TestDefinitionWorkflow:
    """Test complete definition question workflow."""
    
    def test_cgst_definition_flow(self, workflow, skip_without_llm):
        """Test 'What is CGST?' complete flow."""
        result = workflow.run("What is CGST?")
        
        assert result is not None
        response = result.get('response', '') if isinstance(result, dict) else str(result)
        
        # Should contain relevant terms
        response_lower = response.lower()
        assert any(term in response_lower for term in ['cgst', 'central', 'tax', 'gst'])
    
    def test_gst_components_explanation(self, workflow, skip_without_llm):
        """Test explanation of GST components."""
        result = workflow.run("Explain the components of GST")
        
        assert result is not None
        response = result.get('response', '') if isinstance(result, dict) else str(result)
        
        # Should mention at least some GST components
        response_lower = response.lower()
        assert any(term in response_lower for term in ['cgst', 'sgst', 'igst', 'tax'])


@pytest.mark.integration
class TestRateLookupWorkflow:
    """Test complete rate lookup workflow."""
    
    def test_milk_rate_lookup(self, workflow):
        """Test GST rate lookup for milk (0%)."""
        result = workflow.run("What is the GST rate on milk?")
        
        assert result is not None
        response = result.get('response', '') if isinstance(result, dict) else str(result)
        
        # Should mention 0% or exempt
        response_lower = response.lower()
        assert any(term in response_lower for term in ['0%', 'exempt', 'nil', 'zero'])
    
    def test_laptop_rate_lookup(self, workflow):
        """Test GST rate lookup for laptops (18%)."""
        result = workflow.run("GST rate on laptops")
        
        assert result is not None


@pytest.mark.integration
class TestKnowledgeWorkflow:
    """Test knowledge-based question workflow."""
    
    def test_filing_deadline_question(self, workflow):
        """Test GSTR-3B filing deadline question."""
        result = workflow.run("What is the due date for GSTR-3B?")
        
        assert result is not None
        response = result.get('response', '') if isinstance(result, dict) else str(result)
        
        # Should mention some date-related info
        assert len(response) > 20  # Should have substantial answer


@pytest.mark.integration
class TestGuardrailsIntegration:
    """Test guardrails integration."""
    
    def test_gstin_validation_in_context(self, guardrails):
        """Test GSTIN validation works in context."""
        # Valid GSTIN
        valid = guardrails.validate_gstin("27AAPFU0939F1ZV")
        assert valid.is_valid is True
        
        # Invalid GSTIN
        invalid = guardrails.validate_gstin("INVALID123")
        assert invalid.is_valid is False
    
    def test_tax_calculation_validation(self, guardrails):
        """Test tax calculation validation."""
        # Correct calculation
        correct = guardrails.validate_tax_calculation(
            taxable_value=10000,
            cgst=900,
            sgst=900,
            igst=0,
            total=11800
        )
        assert correct.is_valid is True
        
        # Wrong calculation
        wrong = guardrails.validate_tax_calculation(
            taxable_value=10000,
            cgst=100,
            sgst=100,
            igst=0,
            total=15000  # Wrong total
        )
        assert wrong.is_valid is False


@pytest.mark.integration
class TestQueryClassifierIntegration:
    """Test query classifier integration."""
    
    def test_classifier_routes_correctly(self, query_classifier):
        """Test that classifier routes queries to correct sources."""
        from core.query_classifier import QueryType
        
        # Definition → LLM
        definition = query_classifier.classify("What is CGST?")
        assert definition.query_type == QueryType.DEFINITION
        assert definition.suggested_source == "llm"
        
        # Rate → CSV
        rate = query_classifier.classify("GST rate on milk")
        assert rate.query_type == QueryType.RATE_LOOKUP
        assert rate.suggested_source == "csv"
        
        # Legal → ChromaDB (use explicit due date query)
        legal = query_classifier.classify("What is the due date for GSTR-3B?")
        assert legal.query_type == QueryType.LEGAL_RULE
        assert legal.suggested_source == "chromadb"
        
        # Data → DuckDB
        data = query_classifier.classify("What are my total sales?")
        assert data.query_type == QueryType.DATA_QUERY
        assert data.suggested_source == "duckdb"


@pytest.mark.integration
class TestDataPipeline:
    """Test data loading and processing pipeline."""
    
    def test_reference_data_loads(self):
        """Test that reference data loads correctly."""
        from config import load_goods_rates, load_services_rates
        
        goods = load_goods_rates()
        services = load_services_rates()
        
        assert len(goods) > 0
        assert len(services) > 0
    
    def test_duckdb_connection(self, data_engine):
        """Test DuckDB is accessible."""
        result = data_engine.query("SELECT 1 as test")
        assert result is not None
    
    def test_chromadb_searchable(self, knowledge_base):
        """Test ChromaDB is searchable."""
        results = knowledge_base.search("GST return")
        assert results is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "integration"])

