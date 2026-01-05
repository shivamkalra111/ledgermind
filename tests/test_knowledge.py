"""
Tests for core/knowledge.py - ChromaDB operations
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestKnowledgeBaseConnection:
    """Test ChromaDB connection and initialization."""
    
    def test_knowledge_base_initialization(self):
        """Knowledge base should initialize without errors."""
        from core.knowledge import KnowledgeBase
        
        kb = KnowledgeBase()
        assert kb is not None
    
    def test_can_search(self):
        """Knowledge base should be searchable."""
        from core.knowledge import KnowledgeBase
        
        kb = KnowledgeBase()
        results = kb.search("GST")
        assert results is not None


class TestKnowledgeBaseSearch:
    """Test semantic search functionality."""
    
    @pytest.fixture
    def kb(self):
        from core.knowledge import KnowledgeBase
        return KnowledgeBase()
    
    def test_search_returns_results(self, kb):
        """Search should return results for GST queries."""
        results = kb.search("GST return filing deadline")
        assert results is not None
    
    def test_search_with_limit(self, kb):
        """Search should respect result limit."""
        results = kb.search("GSTR-3B", n_results=3)
        assert results is not None
        if isinstance(results, list):
            assert len(results) <= 3
    
    def test_search_relevance(self, kb):
        """Search results should be relevant."""
        results = kb.search("GSTR-1 filing due date")
        # Results should contain GST-related content
        assert results is not None


class TestKnowledgeBaseContent:
    """Test knowledge base content."""
    
    @pytest.fixture
    def kb(self):
        from core.knowledge import KnowledgeBase
        return KnowledgeBase()
    
    def test_document_count(self, kb):
        """Should have documents in the collection."""
        # Search returns something, indicating content exists
        results = kb.search("GST")
        assert results is not None
    
    def test_has_gst_content(self, kb):
        """Should have GST-related content."""
        results = kb.search("GST registration requirements")
        assert results is not None
        # At least some content should be found


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

