"""
Tests for orchestration/ - Router and Workflow
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestIntentRouter:
    """Test the intent router."""
    
    def test_import(self):
        """Router should import without errors."""
        from orchestration.router import IntentRouter
        assert IntentRouter is not None
    
    def test_initialization(self):
        """Router should initialize."""
        from orchestration.router import IntentRouter
        router = IntentRouter()
        assert router is not None
    
    def test_route_knowledge_query(self):
        """Should route knowledge queries correctly."""
        from orchestration.router import IntentRouter
        router = IntentRouter()
        
        result = router.route("What is GST?")
        assert result is not None
        assert hasattr(result, 'intent_type')  # ParsedIntent has intent_type
    
    def test_route_data_query(self):
        """Should route data queries correctly."""
        from orchestration.router import IntentRouter
        router = IntentRouter()
        
        result = router.route("Show my sales for October")
        assert result is not None


class TestAgentWorkflow:
    """Test the agent workflow orchestrator."""
    
    def test_import(self):
        """Workflow should import without errors."""
        from orchestration.workflow import AgentWorkflow
        assert AgentWorkflow is not None
    
    def test_initialization(self):
        """Workflow should initialize."""
        from orchestration.workflow import AgentWorkflow
        workflow = AgentWorkflow()
        assert workflow is not None
    
    def test_has_run_method(self):
        """Workflow should have a run method."""
        from orchestration.workflow import AgentWorkflow
        workflow = AgentWorkflow()
        assert hasattr(workflow, 'run')


class TestEndToEndFlow:
    """Test complete request flows."""
    
    @pytest.fixture
    def workflow(self):
        from orchestration.workflow import AgentWorkflow
        return AgentWorkflow()
    
    def test_definition_question(self, workflow):
        """Definition question should get an answer."""
        result = workflow.run("What is CGST?")
        assert result is not None
        assert 'response' in result or isinstance(result, str)
    
    def test_knowledge_question(self, workflow):
        """Knowledge question should get an answer."""
        result = workflow.run("When is GSTR-3B due?")
        assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

