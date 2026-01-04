"""
LedgerMind Configuration
Central configuration for all components
"""

from pathlib import Path

# =============================================================================
# PATHS
# =============================================================================

BASE_DIR = Path(__file__).parent
KNOWLEDGE_DIR = BASE_DIR / "knowledge"
WORKSPACE_DIR = BASE_DIR / "workspace"
CHROMA_DIR = BASE_DIR / "chroma_db"
DUCKDB_PATH = BASE_DIR / "ledgermind.duckdb"

# Knowledge subdirectories
GST_KNOWLEDGE_DIR = KNOWLEDGE_DIR / "gst"
ACCOUNTING_KNOWLEDGE_DIR = KNOWLEDGE_DIR / "accounting"

# =============================================================================
# OLLAMA / LLM SETTINGS
# =============================================================================

OLLAMA_BASE_URL = "http://localhost:11434"
LLM_MODEL = "qwen2.5:7b-instruct"
LLM_TEMPERATURE = 0.1  # Low temperature for factual responses
LLM_MAX_TOKENS = 1024
LLM_TIMEOUT = 120  # seconds

# =============================================================================
# EMBEDDINGS
# =============================================================================

EMBEDDING_MODEL = "BAAI/bge-large-en-v1.5"
EMBEDDING_DIMENSION = 1024

# =============================================================================
# CHROMADB (Knowledge Base)
# =============================================================================

CHROMA_COLLECTION_NAME = "gst_knowledge"
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

# =============================================================================
# DUCKDB (Data Engine)
# =============================================================================

# Standard Data Model table names
SDM_TABLES = {
    "sales": "sales_register",
    "purchases": "purchase_ledger", 
    "bank": "bank_statement",
    "tax_returns": "tax_returns",
    "vendors": "vendor_master",
}

# =============================================================================
# AGENT SETTINGS
# =============================================================================

# Discovery Agent
DISCOVERY_SAMPLE_ROWS = 10  # Rows to sample for structure detection
DISCOVERY_CONFIDENCE_THRESHOLD = 0.7

# Compliance Agent
COMPLIANCE_OVERDUE_DAYS = 45  # Section 43B(h) threshold

# Strategist Agent
FORECAST_MONTHS = 3

# =============================================================================
# GST 2026 TAX SLABS
# =============================================================================

GST_SLABS_2026 = {
    "exempt": {
        "rate": 0,
        "items": [
            "health insurance", "life insurance", "uht milk", "paneer",
            "diagnostic kits", "life-saving drugs"
        ]
    },
    "merit": {
        "rate": 5,
        "items": [
            "soaps", "toothpaste", "fmcg", "agri-machinery",
            "hotel stay <7500", "gyms", "salons"
        ]
    },
    "standard": {
        "rate": 18,
        "items": [
            "electronics", "ac", "small cars", "motorcycles <350cc",
            "cement", "b2b services"
        ]
    },
    "luxury": {
        "rate": 40,
        "items": [
            "tobacco", "luxury suv", "high-end bikes >350cc",
            "yachts", "aerated drinks"
        ]
    }
}

# =============================================================================
# MSME CLASSIFICATION (2026)
# =============================================================================

MSME_CLASSIFICATION = {
    "micro": {"turnover_limit": 10_00_00_000},      # <₹10 Cr
    "small": {"turnover_limit": 100_00_00_000},     # <₹100 Cr
    "medium": {"turnover_limit": 500_00_00_000},    # <₹500 Cr
}

# =============================================================================
# PROMPTS
# =============================================================================

SYSTEM_PROMPT = """You are LedgerMind, an AI CFO assistant for MSMEs in India.

CORE RULES:
1. NEVER perform arithmetic yourself. Always use SQL queries or Python functions.
2. Base all answers on actual data (DuckDB) and rules (ChromaDB).
3. When uncertain, ASK for clarification rather than guessing.
4. Cite specific sections when discussing GST rules.

GST 2026 CONTEXT:
- New simplified slabs: 0% (Exempt), 5% (Merit), 18% (Standard), 40% (Luxury)
- Section 43B(h): Payments to MSEs must be within 45 days or disallowed as deduction
- MSME Classification: Micro (<₹10Cr), Small (<₹100Cr), Medium (<₹500Cr)

Your job is to:
1. Analyze financial data for compliance issues
2. Identify tax savings opportunities
3. Flag overdue vendor payments
4. Answer accounting/GST questions accurately
"""

DISCOVERY_PROMPT = """Analyze these Excel/CSV headers and classify the sheet type.

Headers: {headers}
Sample data (first 3 rows): {sample_data}

Classify as ONE of:
- sales_register: Contains sales invoices, customer details, output tax
- purchase_ledger: Contains purchase bills, vendor details, input tax
- bank_statement: Contains bank transactions, credits, debits
- tax_returns: Contains GSTR data, tax summaries
- unknown: Cannot determine

Also map each header to our Standard Data Model:
- invoice_date, invoice_number, party_name, party_gstin
- taxable_value, cgst, sgst, igst, total_value
- description, hsn_code, quantity, rate

Respond in JSON format:
{{
    "sheet_type": "...",
    "confidence": 0.0-1.0,
    "header_mapping": {{"original_header": "sdm_field", ...}},
    "unmapped_headers": ["..."]
}}
"""

COMPLIANCE_PROMPT = """Analyze this transaction for GST compliance issues.

Transaction: {transaction}
Relevant GST Rules: {rules}

Check for:
1. Correct tax rate applied (compare against 2026 slabs)
2. ITC eligibility (check Section 17(5) blocked credits)
3. Vendor GSTIN validity
4. Section 43B(h) compliance (payment within 45 days for MSEs)

Respond with findings and recommendations.
"""

