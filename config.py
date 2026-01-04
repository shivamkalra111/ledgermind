"""
LedgerMind Configuration
Central configuration for all components
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

# Database subdirectories (CSVs, JSON)
GST_RATES_DIR = DB_DIR / "gst_rates"

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
# GST DATA FILES (Loaded from db/)
# =============================================================================

GST_DATA_FILE = DB_DIR / "gst_rates_2025.json"
GOODS_RATES_FILE = GST_RATES_DIR / "goods_rates_2025.csv"
SERVICES_RATES_FILE = GST_RATES_DIR / "services_rates_2025.csv"
BLOCKED_CREDITS_FILE = GST_RATES_DIR / "blocked_credits_17_5.csv"
MSME_FILE = DB_DIR / "msme_classification.csv"
STATE_CODES_FILE = DB_DIR / "state_codes.csv"


def load_gst_data():
    """Load GST rates and compliance rules from JSON file."""
    import json
    
    if GST_DATA_FILE.exists():
        with open(GST_DATA_FILE, "r") as f:
            return json.load(f)
    else:
        # Fallback minimal data if file not found
        return {
            "slabs": {
                "exempt": {"rate": 0, "items": []},
                "merit": {"rate": 5, "items": []},
                "standard": {"rate": 18, "items": []},
                "luxury": {"rate": 40, "items": []}
            },
            "msme_classification": {
                "categories": {
                    "micro": {"turnover_limit": 50000000},
                    "small": {"turnover_limit": 500000000},
                    "medium": {"turnover_limit": 2500000000}
                }
            },
            "compliance_rules": {}
        }


# Lazy-loaded GST data
_gst_data_cache = None


def get_gst_data():
    """Get GST data (cached)."""
    global _gst_data_cache
    if _gst_data_cache is None:
        _gst_data_cache = load_gst_data()
    return _gst_data_cache


# Convenience accessors
def get_gst_slabs():
    """Get GST rate slabs."""
    return get_gst_data().get("slabs", {})


def get_msme_classification():
    """Get MSME classification thresholds."""
    return get_gst_data().get("msme_classification", {}).get("categories", {})


def get_compliance_rules():
    """Get compliance rules (Section 43B(h), Section 17(5), etc.)."""
    return get_gst_data().get("compliance_rules", {})


def get_state_codes():
    """Get GST state codes."""
    return get_gst_data().get("state_codes", {})


# =============================================================================
# CSV DATA LOADERS
# =============================================================================

def load_goods_rates():
    """Load goods GST rates from CSV."""
    import csv
    
    rates = []
    if GOODS_RATES_FILE.exists():
        with open(GOODS_RATES_FILE, "r") as f:
            reader = csv.DictReader(f)
            rates = list(reader)
    return rates


def load_services_rates():
    """Load services GST rates from CSV."""
    import csv
    
    rates = []
    if SERVICES_RATES_FILE.exists():
        with open(SERVICES_RATES_FILE, "r") as f:
            reader = csv.DictReader(f)
            rates = list(reader)
    return rates


def load_blocked_credits():
    """Load Section 17(5) blocked credits from CSV."""
    import csv
    
    items = []
    if BLOCKED_CREDITS_FILE.exists():
        with open(BLOCKED_CREDITS_FILE, "r") as f:
            reader = csv.DictReader(f)
            items = list(reader)
    return items


def get_rate_for_hsn(hsn_code: str):
    """Get GST rate for a given HSN code."""
    rates = load_goods_rates()
    
    for rate in rates:
        if rate["hsn_code"] == hsn_code:
            return {
                "rate": int(rate["gst_rate"]),
                "cess": rate.get("cess_rate", "0"),
                "item": rate["item_name"],
                "category": rate["category"]
            }
        # Check for chapter/range matches
        if "-" in rate["hsn_code"]:
            start, end = rate["hsn_code"].split("-")
            if hsn_code.startswith(start[:2]):
                return {
                    "rate": int(rate["gst_rate"]),
                    "cess": rate.get("cess_rate", "0"),
                    "item": rate["item_name"],
                    "category": rate["category"]
                }
    
    return None


def get_rate_for_sac(sac_code: str):
    """Get GST rate for a given SAC code."""
    rates = load_services_rates()
    
    for rate in rates:
        if rate["sac_code"] == sac_code:
            return {
                "rate": int(rate["gst_rate"]),
                "service": rate["service_name"],
                "category": rate["category"],
                "condition": rate.get("condition", "")
            }
    
    return None

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

