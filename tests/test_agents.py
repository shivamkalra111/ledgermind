"""
Tests for agents/ - Discovery, Compliance, and Strategist agents
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestDiscoveryAgent:
    """Test the Discovery & Mapping Agent."""
    
    def test_import(self):
        """Discovery agent should import without errors."""
        from agents.discovery import DiscoveryAgent
        assert DiscoveryAgent is not None
    
    def test_initialization(self):
        """Discovery agent should initialize."""
        from agents.discovery import DiscoveryAgent
        agent = DiscoveryAgent()
        assert agent is not None
    
    def test_has_discover_method(self):
        """Discovery agent should have discover method."""
        from agents.discovery import DiscoveryAgent
        agent = DiscoveryAgent()
        assert hasattr(agent, 'discover')


class TestComplianceAgent:
    """Test the Compliance/Auditor Agent."""
    
    def test_import(self):
        """Compliance agent should import without errors."""
        from agents.compliance import ComplianceAgent
        assert ComplianceAgent is not None
    
    def test_initialization(self):
        """Compliance agent should initialize."""
        from agents.compliance import ComplianceAgent
        agent = ComplianceAgent()
        assert agent is not None
    
    def test_has_audit_method(self):
        """Compliance agent should have audit method."""
        from agents.compliance import ComplianceAgent
        agent = ComplianceAgent()
        assert hasattr(agent, 'run_full_audit') or hasattr(agent, 'check_tax_rates')


class TestStrategistAgent:
    """Test the Strategist/Advisor Agent."""
    
    def test_import(self):
        """Strategist agent should import without errors."""
        from agents.strategist import StrategistAgent
        assert StrategistAgent is not None
    
    def test_initialization(self):
        """Strategist agent should initialize."""
        from agents.strategist import StrategistAgent
        agent = StrategistAgent()
        assert agent is not None
    
    def test_has_analysis_method(self):
        """Strategist agent should have analysis methods."""
        from agents.strategist import StrategistAgent
        agent = StrategistAgent()
        assert hasattr(agent, 'run_full_analysis') or hasattr(agent, 'analyze_vendors')


class TestAgentCoordination:
    """Test that agents can work together."""
    
    def test_all_agents_import(self):
        """All three agents should import together."""
        from agents.discovery import DiscoveryAgent
        from agents.compliance import ComplianceAgent
        from agents.strategist import StrategistAgent
        
        discovery = DiscoveryAgent()
        compliance = ComplianceAgent()
        strategist = StrategistAgent()
        
        assert all([discovery, compliance, strategist])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

