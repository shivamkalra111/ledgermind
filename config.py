"""
Configuration file for LLM and RAG system.

Easily change models and parameters here without modifying code.
"""

# ============================================================================
# LLM Configuration
# ============================================================================

# Model to use (any Ollama model)
# Examples:
#   - "qwen2.5:7b-instruct"  (Current choice - good for reasoning)
#   - "llama3:8b"             (Alternative - Meta's model)
#   - "mistral:7b"            (Alternative - Fast and efficient)
#   - "gemma:7b"              (Alternative - Google's model)
LLM_MODEL_NAME = "qwen2.5:7b-instruct"

# Ollama API endpoint
LLM_BASE_URL = "http://localhost:11434"

# Generation parameters
# Generation parameters
LLM_TEMPERATURE = 0.1  # Revert to 0.1 for maximum faithfulness
LLM_MAX_TOKENS = 300   # Keep this to limit verbosity
LLM_TOP_P = 0.9        # Nucleus sampling

# ============================================================================
# RAG Configuration
# ============================================================================

# Number of chunks to retrieve for context
# Reverted to 7 after testing showed 5 chunks caused low faithfulness
RAG_NUM_RESULTS = 7

# Minimum similarity threshold (0.0-1.0)
# Revert to 0.2 to fix Q8 (GSTR-3B) failure
RAG_MIN_SIMILARITY = 0.2

# ============================================================================
# ChromaDB Configuration
# ============================================================================

# Database path
CHROMA_DB_PATH = "./chroma_db"

# Collection name
CHROMA_COLLECTION_NAME = "gst_rules"

# Embedding model (for retrieval)
EMBEDDING_MODEL = "BAAI/bge-large-en-v1.5"

# ============================================================================
# Domain-Specific Configuration (GST)
# ============================================================================

# System prompt for GST domain
GST_SYSTEM_PROMPT = """You are a GST compliance assistant for India.

CRITICAL RULES:
1. Answer ONLY from the provided context
2. If information is not in context, say "I cannot find this in the provided documents"
3. Cite [Source: filename, Page X] for every claim
4. Keep answers CONCISE (max 3-4 sentences).

If the context is insufficient, respond:
"The provided documents don't contain sufficient information to answer this question."
"""

# ============================================================================
# Application Settings
# ============================================================================

# Display settings
SHOW_SOURCES = True
SHOW_CONFIDENCE = True
MAX_SOURCES_DISPLAY = 3

# Logging
VERBOSE = True

# ============================================================================
# Model Alternatives
# ============================================================================

# Uncomment to try different models:

# Fast and lightweight
# LLM_MODEL_NAME = "mistral:7b"

# Better reasoning (but slower)
# LLM_MODEL_NAME = "qwen2.5:14b-instruct"

# For coding tasks
# LLM_MODEL_NAME = "deepseek-coder:6.7b"

# For general knowledge
# LLM_MODEL_NAME = "llama3:8b"

