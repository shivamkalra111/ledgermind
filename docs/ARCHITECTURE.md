# LedgerMind - Technical Architecture

> Complete technical documentation for the Agentic AI CFO Platform

**Last Updated:** January 2026  
**Phase:** 1 (Foundation) ✅ Complete  
**Tests:** 121 Passing

---

## 1. System Overview

LedgerMind is an **autonomous financial intelligence platform** built on a multi-agent architecture. It transforms unstructured financial data (Excel/CSV) into actionable insights through specialized AI agents.

### Core Principles

1. **Agents over Chatbots** — Autonomous task execution, not just Q&A
2. **SQL over Embeddings for Data** — DuckDB for financial data, ChromaDB for rules only
3. **Local-First** — All processing on user's machine, $0 cloud cost
4. **Math Safety** — LLM reasons, Python/SQL calculates
5. **Proper Knowledge Routing** — Each knowledge layer serves its purpose
6. **Clean Separation** — Config for settings, reference_data for loading

---

## 2. Knowledge Architecture

### The Three Knowledge Layers

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     KNOWLEDGE ARCHITECTURE                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  LAYER 1: REFERENCE DATA (Facts that change with policy)               │
│  ─────────────────────────────────────────────────────                 │
│  Source: db/**/*.csv                                                    │
│  Purpose: Rate lookups, code validation, thresholds                    │
│  Examples: GST rates, MSME limits, state codes                         │
│                                                                         │
│  → Queried via: core/reference_data.py                                 │
│                                                                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  LAYER 2: LEGAL KNOWLEDGE (Rules, procedures, sections)                │
│  ───────────────────────────────────────────────────────               │
│  Source: ChromaDB (from PDFs in knowledge/)                            │
│  Purpose: RAG for specific legal questions                             │
│  Examples: CGST Act, Rules, Notifications                              │
│                                                                         │
│  → Queried via: core/knowledge.py                                      │
│                                                                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  LAYER 3: FOUNDATIONAL KNOWLEDGE (What the LLM already knows)          │
│  ────────────────────────────────────────────────────────              │
│  Source: LLM training data                                              │
│  Purpose: Definitions, concepts, explanations                          │
│  Examples: "What is CGST?", "How does ITC work?"                       │
│                                                                         │
│  → Queried via: LLM without context restriction                        │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Query Classification & Routing

```
User Question
     │
     ▼
┌────────────────────────────────────────────────────────────┐
│              QUERY CLASSIFIER                              │
│              (core/query_classifier.py)                    │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  "What is CGST?"        → DEFINITION    → LLM (Layer 3)   │
│  "GST rate on milk?"    → RATE_LOOKUP   → CSV (Layer 1)   │
│  "Due date for GSTR-3B" → LEGAL_RULE    → ChromaDB (L2)   │
│  "My total sales?"      → DATA_QUERY    → DuckDB          │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

---

## 3. High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              USER INTERFACE                                  │
│                         (CLI / Future: Web UI)                              │
│                              main.py                                        │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           ORCHESTRATION LAYER                                │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐         │
│  │  Intent Router  │───▶│ Query Classifier│───▶│  Agent Workflow │         │
│  │   (router.py)   │    │  (classifier.py)│    │  (workflow.py)  │         │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘         │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                    ┌─────────────────┼─────────────────┐
                    ▼                 ▼                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              AGENT LAYER                                     │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐         │
│  │   DISCOVERY     │    │   COMPLIANCE    │    │   STRATEGIST    │         │
│  │   (discovery.py)│    │  (compliance.py)│    │  (strategist.py)│         │
│  │                 │    │                 │    │                 │         │
│  │ • File scanning │    │ • Tax rate      │    │ • Vendor        │         │
│  │ • Header map    │    │   verification  │    │   analysis      │         │
│  │ • Schema create │    │ • ITC checks    │    │ • Cash flow     │         │
│  │ • Type detect   │    │ • 43B(h) check  │    │ • Forecasting   │         │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘         │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                    ┌─────────────────┼─────────────────┐
                    ▼                 ▼                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CORE LAYER                                      │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐         │
│  │   DATA ENGINE   │    │  KNOWLEDGE BASE │    │   LLM CLIENT    │         │
│  │  (data_engine)  │    │  (knowledge.py) │    │   (client.py)   │         │
│  │                 │    │                 │    │                 │         │
│  │ • DuckDB        │    │ • ChromaDB      │    │ • Ollama        │         │
│  │ • Excel → SQL   │    │ • RAG retrieval │    │ • Qwen 7B       │         │
│  │ • Query engine  │    │ • PDF ingestion │    │ • JSON mode     │         │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘         │
│                                                                             │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐         │
│  │ REFERENCE DATA  │    │   GUARDRAILS    │    │    METRICS      │         │
│  │(reference_data) │    │ (guardrails.py) │    │  (metrics.py)   │         │
│  │                 │    │                 │    │                 │         │
│  │ • Load CSV      │    │ • GSTIN check   │    │ • Performance   │         │
│  │ • Rate lookup   │    │ • Tax math      │    │ • Compliance    │         │
│  │ • MSME limits   │    │ • LLM safety    │    │ • Tracking      │         │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘         │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                    ┌─────────────────┼─────────────────┐
                    ▼                 ▼                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              DATA LAYER                                      │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐         │
│  │    db/          │    │   knowledge/    │    │   workspace/    │         │
│  │ (Reference Data)│    │ (PDFs for RAG)  │    │ (User's Data)   │         │
│  │                 │    │                 │    │                 │         │
│  │ db/gst/         │    │ • CGST Act PDF  │    │ • Excel files   │         │
│  │ db/msme/        │    │ • CGST Rules    │    │ • CSV files     │         │
│  │ db/india/       │    │ • Accounting    │    │ • Discovery     │         │
│  │                 │    │   standards     │    │   metadata      │         │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘         │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Complete File Structure

```
ledgermind/
├── 🎯 main.py                      # Entry point - CLI interface
├── ⚙️  config.py                    # Configuration ONLY (paths, settings)
├── 📋 requirements.txt             # Python dependencies
│
├── 🤖 agents/                      # AI Agents (business logic)
│   ├── __init__.py
│   ├── discovery.py                # File discovery & schema mapping
│   ├── compliance.py               # Tax compliance checks
│   └── strategist.py               # Strategic analysis
│
├── ⚙️  core/                        # Core infrastructure
│   ├── __init__.py
│   ├── data_engine.py              # DuckDB integration
│   ├── knowledge.py                # ChromaDB RAG
│   ├── reference_data.py           # CSV data loading (Layer 1)
│   ├── query_classifier.py         # Query routing
│   ├── guardrails.py               # Safety validations
│   ├── metrics.py                  # Performance tracking
│   ├── schema.py                   # Data models (SDM)
│   └── mapper.py                   # Header mapping logic
│
├── 🔀 orchestration/               # Workflow control
│   ├── __init__.py
│   ├── router.py                   # Intent classification
│   └── workflow.py                 # Agent coordination
│
├── 🧠 llm/                         # LLM integration
│   ├── __init__.py
│   └── client.py                   # Ollama client
│
├── 📊 db/                          # Reference data (Layer 1) - CSVs ONLY
│   ├── README.md                   # Data documentation
│   ├── gst/                        # GST-related reference data
│   │   ├── slabs.csv               # Rate slabs (0%, 5%, 18%, 28%)
│   │   ├── goods_hsn.csv           # HSN → rate mapping (89 items)
│   │   ├── services_sac.csv        # SAC → rate mapping (50 services)
│   │   └── blocked_itc.csv         # Section 17(5) items (15)
│   ├── msme/                       # MSME classification
│   │   └── classification.csv      # Micro/Small/Medium thresholds
│   └── india/                      # India-specific data
│       └── state_codes.csv         # GST state codes (38)
│
├── 📚 knowledge/                   # PDFs for RAG (Layer 2)
│   ├── gst/
│   │   ├── a2017-12.pdf            # CGST Act 2017
│   │   └── 01062021-cgst-rules...  # CGST Rules
│   └── accounting/                 # Accounting standards
│
├── 📂 workspace/                   # User data
│   └── sample_company/             # Sample test data
│
├── 🧪 tests/                       # Test suite (121 tests)
│   ├── __init__.py
│   ├── conftest.py                 # Shared fixtures
│   ├── test_config.py              # Config path tests
│   ├── test_reference_data.py      # Data loading tests
│   ├── test_guardrails.py          # Validation tests
│   ├── test_query_classifier.py    # Query routing tests
│   ├── test_data_engine.py         # DuckDB tests
│   ├── test_knowledge.py           # ChromaDB tests
│   ├── test_agents.py              # Agent tests
│   ├── test_orchestration.py       # Workflow tests
│   └── test_integration.py         # End-to-end tests
│
├── 🔧 scripts/                     # Utility scripts
│   ├── create_sample_data.py       # Generate test data
│   ├── ingest_knowledge.py         # Populate ChromaDB
│   └── scrape_gst_rates.py         # Update GST rates
│
├── 📖 docs/                        # Documentation
│   ├── ARCHITECTURE.md             # This file
│   └── ROADMAP.md                  # Development plan
│
├── 🗄️  chroma_db/                   # ChromaDB storage
└── 🦆 ledgermind.duckdb            # DuckDB database
```

---

## 5. File Descriptions (What & Why)

### Entry Points

| File | Purpose | Why It Exists |
|------|---------|---------------|
| `main.py` | CLI entry point | User interacts with system here |
| `config.py` | Paths and settings ONLY | Single source for configuration |

### Core Infrastructure (`core/`)

| File | Purpose | Why It Exists |
|------|---------|---------------|
| `data_engine.py` | DuckDB wrapper - Excel as SQL | Fast analytics on user's financial data |
| `knowledge.py` | ChromaDB wrapper - RAG for rules | Legal questions need document search |
| `reference_data.py` | Load CSV data, rate lookups | **Clean separation from config** |
| `query_classifier.py` | Routes queries to correct source | Each knowledge layer serves its purpose |
| `guardrails.py` | Validation & safety checks | Prevent bad data, LLM hallucinations |
| `metrics.py` | Performance & compliance tracking | Monitor system health |
| `schema.py` | Standard Data Model definitions | Normalize different Excel formats |
| `mapper.py` | Header mapping logic | Map "Inv. No." → "invoice_number" |

### Agents (`agents/`)

| File | Purpose | Why It Exists |
|------|---------|---------------|
| `discovery.py` | Reads Excel/CSV, maps to standard schema | MSMEs have messy, inconsistent files |
| `compliance.py` | Checks tax compliance issues | Core value - find savings/risks |
| `strategist.py` | Vendor analysis, cash flow forecasting | Strategic business insights |

### Reference Data (`db/`)

| Path | Contents | Records |
|------|----------|---------|
| `db/gst/slabs.csv` | Rate slab definitions | 4 slabs |
| `db/gst/goods_hsn.csv` | HSN codes → rates | 89 items |
| `db/gst/services_sac.csv` | SAC codes → rates | 50 services |
| `db/gst/blocked_itc.csv` | Section 17(5) list | 15 items |
| `db/msme/classification.csv` | MSME thresholds | 3 categories |
| `db/india/state_codes.csv` | GST state codes | 38 codes |

### Tests (`tests/`)

| File | Tests | What It Covers |
|------|-------|----------------|
| `test_config.py` | 10 | Paths exist, settings valid |
| `test_reference_data.py` | 19 | CSV loading, rate lookups |
| `test_guardrails.py` | 17 | GSTIN, HSN, tax validation |
| `test_query_classifier.py` | 20 | Query routing accuracy |
| `test_data_engine.py` | 8 | DuckDB operations |
| `test_knowledge.py` | 7 | ChromaDB search |
| `test_agents.py` | 10 | Agent initialization |
| `test_orchestration.py` | 10 | Router, workflow |
| `test_integration.py` | 20 | End-to-end flows |
| **Total** | **121** | |

---

## 6. Guardrails System

### Current Guardrails (10 Methods)

| Guardrail | What It Does | When Used |
|-----------|--------------|-----------|
| `validate_gstin` | Check GSTIN format & checksum | All transactions |
| `validate_hsn_code` | Check HSN code format (4/6/8 digits) | Rate lookups |
| `validate_invoice_number` | Check invoice format | Data ingestion |
| `validate_date` | Check date validity | All date fields |
| `validate_amount` | Check amount is positive, reasonable | All amounts |
| `validate_tax_calculation` | Verify taxable + taxes = total | Tax fields |
| `validate_itc_time_limit` | Check ITC not expired | ITC claims |
| `validate_section_43b_h` | Check MSME payment deadline | Vendor payments |
| `validate_llm_response_no_math` | Ensure LLM doesn't do arithmetic | LLM outputs |
| `validate_llm_response_has_citation` | Check LLM cites sources | Legal answers |

---

## 7. Technology Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **LLM** | Qwen2.5-7B-Instruct | Reasoning, classification |
| **LLM Host** | Ollama | Local inference, no cloud |
| **Data Engine** | DuckDB | Excel/CSV as SQL, analytics |
| **Vector DB** | ChromaDB | RAG for legal documents |
| **Embeddings** | Default (ChromaDB) | Semantic search |
| **Framework** | Python 3.10+ | Core language |
| **CLI** | Rich | Beautiful terminal UI |
| **Testing** | Pytest | 121 tests |

---

## 8. Clean Code Principles

### Config vs Reference Data

**Before (Anti-pattern):**
```python
# config.py - BAD: Mixed concerns
GST_SLABS = {"exempt": 0, "merit": 5}  # Hardcoded data
def load_goods_rates(): ...            # Data loading logic
```

**After (Clean):**
```python
# config.py - GOOD: Only configuration
GST_SLABS_FILE = DB_DIR / "gst" / "slabs.csv"

# core/reference_data.py - GOOD: Data loading
def load_gst_slabs() -> List[Dict]:
    return _load_csv(GST_SLABS_FILE)
```

### System Prompt

**Before (Anti-pattern):**
```python
SYSTEM_PROMPT = """...
GST 2026 CONTEXT:
- Slabs: 0%, 5%, 18%, 40%  # Hardcoded rates!
"""
```

**After (Clean):**
```python
SYSTEM_PROMPT = """...
For GST rates: Use the rate data provided in context (from our database).
"""
```

---

## 9. Test Commands

```bash
# Run all tests
pytest tests/ -v

# Run specific module
pytest tests/test_guardrails.py -v

# Run with coverage
pytest tests/ --cov=core --cov=agents

# Quick smoke test
python -c "
from core.query_classifier import QueryClassifier
c = QueryClassifier()
print(c.classify('What is CGST?'))  # → definition, llm
print(c.classify('GST rate on milk?'))  # → rate_lookup, csv
"
```

---

## 10. Current Status

### Phase 1 Complete ✅

| Component | Status | Details |
|-----------|--------|---------|
| DuckDB Data Engine | ✅ | Connected |
| ChromaDB Knowledge | ✅ | 1,276 chunks |
| Query Classifier | ✅ | 4 types |
| Guardrails | ✅ | 10 methods |
| 3 Agents | ✅ | All working |
| LLM Client | ✅ | Ollama connected |
| Reference Data | ✅ | 6 CSV files |
| Tests | ✅ | 121 passing |

---

*Last Updated: January 2026*
