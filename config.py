"""
LedgerMind Configuration

Central configuration for all components.
Contains ONLY configuration values - no business logic or data loading.

For data loading functions, see: core/reference_data.py
"""

from pathlib import Path

# =============================================================================
# PATHS
# =============================================================================

BASE_DIR = Path(__file__).parent
KNOWLEDGE_DIR = BASE_DIR / "knowledge"      # PDFs for RAG
WORKSPACE_DIR = BASE_DIR / "workspace"      # User's Excel/CSV data
DB_DIR = BASE_DIR / "db"                    # Structured reference data
CHROMA_DIR = BASE_DIR / "chroma_db"         # Vector database
DUCKDB_PATH = BASE_DIR / "ledgermind.duckdb"

# Knowledge subdirectories (PDFs)
GST_KNOWLEDGE_DIR = KNOWLEDGE_DIR / "gst"
ACCOUNTING_KNOWLEDGE_DIR = KNOWLEDGE_DIR / "accounting"

# =============================================================================
# REFERENCE DATA PATHS (db/ folder - CSV files)
# =============================================================================

# GST data
GST_DIR = DB_DIR / "gst"
GST_SLABS_FILE = GST_DIR / "slabs.csv"
GOODS_RATES_FILE = GST_DIR / "goods_hsn.csv"
SERVICES_RATES_FILE = GST_DIR / "services_sac.csv"
BLOCKED_CREDITS_FILE = GST_DIR / "blocked_itc.csv"

# MSME data
MSME_DIR = DB_DIR / "msme"
MSME_FILE = MSME_DIR / "classification.csv"

# India reference data
INDIA_DIR = DB_DIR / "india"
STATE_CODES_FILE = INDIA_DIR / "state_codes.csv"

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
# CUSTOMER ISOLATION
# =============================================================================

# Default customer (used when no customer is selected)
DEFAULT_CUSTOMER_ID = None  # None = require selection

# Customer workspace structure
# workspace/{customer_id}/
#   ├── data/              # Customer's Excel/CSV files
#   ├── {customer_id}.duckdb  # Customer's database
#   └── profile.json       # Customer metadata

# Reserved customer IDs (cannot be used for new companies)
# Note: sample_company is allowed as it's the demo data folder
RESERVED_CUSTOMER_IDS = {"test", "admin", "system", "default"}

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
# PROMPTS
# =============================================================================

SYSTEM_PROMPT = """You are LedgerMind, an AI CFO assistant for MSMEs in India.

CORE RULES:
1. NEVER perform arithmetic yourself. Always use SQL queries or the data provided.
2. For GST rates: Use the rate data provided in context (from our database).
3. For legal rules: Use the CGST Act/Rules context provided (from ChromaDB).
4. For user's financial data: Use the SQL results provided (from DuckDB).
5. When uncertain, ASK for clarification rather than guessing.
6. Cite specific sections when discussing GST rules.

Your job is to:
1. Analyze financial data for compliance issues
2. Identify tax savings opportunities  
3. Flag overdue vendor payments (especially Section 43B(h) for MSMEs)
4. Answer accounting/GST questions accurately using provided context
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
1. Correct tax rate applied
2. ITC eligibility (check Section 17(5) blocked credits)
3. Vendor GSTIN validity
4. Section 43B(h) compliance (payment within 45 days for MSEs)

Respond with findings and recommendations.
"""
