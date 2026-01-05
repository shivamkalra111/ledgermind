"""
Tests for config.py - Configuration paths and settings
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


class TestConfigFiles:
    """Test that reference data files exist."""
    
    def test_goods_rates_file_exists(self):
        from config import GOODS_RATES_FILE
        assert GOODS_RATES_FILE.exists(), f"Goods rates file not found: {GOODS_RATES_FILE}"
    
    def test_services_rates_file_exists(self):
        from config import SERVICES_RATES_FILE
        assert SERVICES_RATES_FILE.exists(), f"Services rates file not found: {SERVICES_RATES_FILE}"
    
    def test_msme_file_exists(self):
        from config import MSME_FILE
        assert MSME_FILE.exists(), f"MSME file not found: {MSME_FILE}"
    
    def test_state_codes_file_exists(self):
        from config import STATE_CODES_FILE
        assert STATE_CODES_FILE.exists(), f"State codes file not found: {STATE_CODES_FILE}"


class TestConfigSettings:
    """Test configuration settings have valid values."""
    
    def test_llm_model_set(self):
        from config import LLM_MODEL
        assert LLM_MODEL is not None
        assert len(LLM_MODEL) > 0
    
    def test_chunk_size_valid(self):
        from config import CHUNK_SIZE, CHUNK_OVERLAP
        assert CHUNK_SIZE > 0
        assert CHUNK_OVERLAP > 0
        assert CHUNK_OVERLAP < CHUNK_SIZE


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
