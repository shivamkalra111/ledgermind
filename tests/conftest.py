"""
Pytest configuration and shared fixtures.

This file is automatically loaded by pytest for all tests.
"""

import pytest
import sys
from pathlib import Path

# Add project root to path for all tests
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


# ═══════════════════════════════════════════════════════════════════════════════
# SHARED FIXTURES
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.fixture(scope="session")
def project_root():
    """Return project root directory."""
    return PROJECT_ROOT


@pytest.fixture(scope="session")
def db_dir(project_root):
    """Return database directory."""
    return project_root / "db"


@pytest.fixture(scope="session")
def knowledge_dir(project_root):
    """Return knowledge directory."""
    return project_root / "knowledge"


@pytest.fixture(scope="session")
def workspace_dir(project_root):
    """Return workspace directory."""
    return project_root / "workspace"


# ═══════════════════════════════════════════════════════════════════════════════
# COMPONENT FIXTURES (Module scope for performance)
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.fixture(scope="module")
def guardrails():
    """Return Guardrails instance."""
    from core.guardrails import Guardrails
    return Guardrails()


@pytest.fixture(scope="module")
def query_classifier():
    """Return QueryClassifier instance."""
    from core.query_classifier import QueryClassifier
    return QueryClassifier()


@pytest.fixture(scope="module")
def data_engine():
    """Return DataEngine instance."""
    from core.data_engine import DataEngine
    return DataEngine()


@pytest.fixture(scope="module")
def knowledge_base():
    """Return KnowledgeBase instance."""
    from core.knowledge import KnowledgeBase
    return KnowledgeBase()


@pytest.fixture(scope="module")
def workflow():
    """Return AgentWorkflow instance (no customer - legacy mode)."""
    from orchestration.workflow import AgentWorkflow
    # auto_load=False because we're in legacy mode without customer
    return AgentWorkflow(customer=None, auto_load=False)


# ═══════════════════════════════════════════════════════════════════════════════
# SAMPLE DATA FIXTURES
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.fixture(scope="session")
def sample_gstin():
    """Return a valid sample GSTIN."""
    return "27AAPFU0939F1ZV"


@pytest.fixture(scope="session")
def sample_hsn():
    """Return a valid sample HSN code."""
    return "8471"


@pytest.fixture(scope="session")
def sample_sac():
    """Return a valid sample SAC code."""
    return "9954"


@pytest.fixture(scope="session")
def sample_invoice():
    """Return sample invoice data."""
    return {
        "invoice_number": "INV-2025-001",
        "invoice_date": "2025-10-15",
        "customer_gstin": "27AAPFU0939F1ZV",
        "taxable_value": 10000,
        "gst_rate": 18,
        "cgst": 900,
        "sgst": 900,
        "igst": 0,
        "total": 11800
    }


# ═══════════════════════════════════════════════════════════════════════════════
# MARKS FOR CONDITIONAL TESTS
# ═══════════════════════════════════════════════════════════════════════════════

def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "slow: mark test as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "llm: mark test as requiring LLM (Ollama)"
    )


# ═══════════════════════════════════════════════════════════════════════════════
# SKIP CONDITIONS
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.fixture(scope="session")
def llm_available():
    """Check if LLM is available."""
    try:
        from llm.client import LLMClient
        client = LLMClient()
        return client.is_available()
    except Exception:
        return False


@pytest.fixture
def skip_without_llm(llm_available):
    """Skip test if LLM is not available."""
    if not llm_available:
        pytest.skip("LLM (Ollama) not available")

