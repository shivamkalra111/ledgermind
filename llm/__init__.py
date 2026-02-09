"""
LedgerMind LLM Client
- client: Ollama/Qwen integration for local inference
- secure_prompts: Defensive prompt engineering for injection resistance
"""

from .client import LLMClient
from .secure_prompts import (
    SecurePromptBuilder,
    SecurePromptConfig,
    SecureResponseFormatter,
    SECURE_SYSTEM_PROMPT,
    SECURE_SQL_SYSTEM_PROMPT,
    SECURE_INTENT_PROMPT,
    get_prompt_builder,
    build_secure_prompt,
    build_secure_sql_prompt,
    get_secure_system_prompt,
    get_secure_sql_system_prompt,
)

__all__ = [
    "LLMClient",
    # Secure Prompts
    "SecurePromptBuilder",
    "SecurePromptConfig",
    "SecureResponseFormatter",
    "SECURE_SYSTEM_PROMPT",
    "SECURE_SQL_SYSTEM_PROMPT",
    "SECURE_INTENT_PROMPT",
    "get_prompt_builder",
    "build_secure_prompt",
    "build_secure_sql_prompt",
    "get_secure_system_prompt",
    "get_secure_sql_system_prompt",
]

