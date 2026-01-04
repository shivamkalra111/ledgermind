# LedgerMind: Agentic AI CFO for MSMEs

> An autonomous financial intelligence platform that transforms messy Excel/CSV data into actionable tax insights, compliance alerts, and strategic recommendations — all running locally with $0 software cost.

---

## 🎯 Vision: The "AI CFO"

**Problem:** MSMEs struggle with fragmented financial data across multiple Excel files, constantly changing GST regulations, and expensive CA consultations for routine compliance checks.

**Solution:** LedgerMind is an autonomous AI platform that:
- **Ingests** your messy Excel/CSV files (Sales, Purchases, Bank statements)
- **Maps** them to a standard data model using AI
- **Audits** for tax leakages, overpayments, and compliance issues
- **Advises** on vendor optimization and cash flow health
- **Answers** any accounting/GST question using up-to-date knowledge

All processing happens **locally on your machine** — your financial data never leaves your computer.

---

## 🏛️ 2026 Regulatory Engine (GST 2.0)

LedgerMind natively understands the **GST 2.0 Reforms** (Effective Sept 2025/Jan 2026):

### Simplified Tax Slabs

| Slab | Category | Key Items (2026) |
|------|----------|------------------|
| **0% (Exempt)** | Essentials | Health/Life Insurance, UHT Milk, Paneer, Diagnostic Kits, 33 life-saving drugs |
| **5% (Merit)** | High Volume | Soaps, Toothpaste, FMCG, Agri-machinery, Hotel Stay <₹7.5k, Gyms/Salons |
| **18% (Standard)** | Standard | Electronics, ACs, Small Cars, Motorcycles <350cc, Cement, most B2B Services |
| **40% (Sin/Luxury)** | Demerit | Tobacco, Luxury SUVs, High-end Bikes (>350cc), Yachts, Aerated Drinks |

### MSMED Act 2026 Compliance

- **Section 43B(h):** Mandatory payment to MSEs within **45 days**. Late payments are disallowed as tax deductions.
- **Classification:** Micro (<₹10Cr), Small (<₹100Cr), Medium (<₹500Cr)

---

## 🤖 Core Architecture: The Agentic Workflow

LedgerMind doesn't just "chat" — it performs tasks through an **autonomous Plan-Act-Verify loop**.

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER DROPS FOLDER                           │
│                    (Excel/CSV files + Questions)                    │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    AGENT 1: DISCOVERY (Mapper)                      │
│  • Scans Excel headers using LLM                                    │
│  • Identifies: Sales, Purchases, Bank, Tax Returns                  │
│  • Maps local headers → Standard Data Model                         │
│  • Loads into DuckDB as SQL tables                                  │
│  • Saves mapping in discovery_meta.json (remembers format)          │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    AGENT 2: COMPLIANCE (Auditor)                    │
│  • Cross-references data against GST PDFs (ChromaDB)                │
│  • ITC Check: Flag wrong tax rates (18% charged vs 5% allowed)      │
│  • Reconciliation: Sales in GSTR-1 vs Bank Credits                  │
│  • Section 17(5): Identify blocked credits (food, personal vehicle) │
│  • Section 43B(h): Flag overdue vendor payments (>45 days)          │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    AGENT 3: STRATEGIST (Optimizer)                  │
│  • Vendor Ranking: Reliability score (payment terms vs delivery)    │
│  • MSME Risk: Flag non-MSME vendors impacting 43B(h) deductions     │
│  • Profit Analysis: High-margin products after tax liability        │
│  • Cash Flow Forecast: Predict next month's tax + salary payouts    │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         ACTIONABLE INSIGHTS                         │
│  "You overpaid ₹12,400 on Soap purchases (18% vs 5%)"              │
│  "3 vendors are past 45-day payment — ₹2.1L at risk of disallowance"│
│  "Your top margin product is X after GST adjustment"                │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 💡 What Can LedgerMind Do?

### 1. Autonomous Tasks (Agentic)
| Task | Agent | Example Output |
|------|-------|----------------|
| **Structure Discovery** | Discovery | "Found 3 sheets: Sales_Register, Purchase_Ledger, Bank_Statement" |
| **Tax Rate Verification** | Compliance | "Vendor charged 18% on Soaps. Current rate is 5%. Tax saving: ₹3,200" |
| **ITC Reconciliation** | Compliance | "₹45,000 ITC claimed but vendor GSTIN is cancelled" |
| **Section 43B(h) Alerts** | Compliance | "Payment to ABC Traders overdue by 12 days — disallowance risk" |
| **Blocked Credit Detection** | Compliance | "₹8,500 spent on staff meals — ITC blocked under Section 17(5)" |
| **Vendor Risk Analysis** | Strategist | "5 vendors are not MSME registered — affects ₹12L in deductions" |
| **Cash Flow Projection** | Strategist | "Estimated tax liability for Q4: ₹1.8L (due Jan 20)" |

### 2. Knowledge Queries (Rules from ChromaDB)
Questions about GST laws, accounting standards, compliance rules:
- "What is the time limit for claiming ITC?"
- "Can I claim ITC on hotel stays for business travel?"
- "What changed in GST for FMCG products in 2026?"
- "Explain Section 43B(h) compliance requirements"

### 3. Data Queries (User's Data from DuckDB)
Questions about the user's own financial data:
- "What's my total sales this quarter?"
- "Show me all purchases from Vendor X"
- "Which invoices are pending payment beyond 45 days?"
- "What's my GST liability for December?"

---

## 🛠️ Tech Stack ($0 Software Cost)

| Layer | Tool | Role |
|-------|------|------|
| **Core LLM** | `qwen2.5:7b-instruct` | Reasoning, SQL generation, tax interpretation |
| **Local Host** | Ollama | Runs LLM locally (privacy + $0 API cost) |
| **Data Engine** | DuckDB | Ultra-fast engine — Excel files as SQL tables |
| **Knowledge Base** | ChromaDB | Stores GST PDFs for RAG rule lookups |
| **Agent Framework** | LangGraph | Manages agent orchestration and hand-offs |
| **Embeddings** | `bge-large-en-v1.5` | Semantic search for rule retrieval |

---

## 🔒 Implementation Guardrails

### 1. Math Safety
> **LLM is FORBIDDEN from doing arithmetic.**

All calculations must go through Python functions or SQL queries. The LLM reasons about *what* to calculate, not *how* to calculate.

```python
# ✅ Correct: LLM generates SQL, DuckDB executes
SELECT SUM(tax_amount) FROM purchases WHERE vendor_gstin = 'ABC123'

# ❌ Wrong: LLM doing math
"The total is 18% of 50,000 which is 9,000..."  # BLOCKED
```

### 2. Data Locality
> **All processing happens on YOUR machine.**

No data is sent to external clouds. Ollama runs locally, DuckDB is file-based, ChromaDB persists locally.

### 3. Semantic Verification
> **Ask, don't guess.**

If the AI encounters an unknown ledger name (e.g., "Suspense_Account_New"), it stops and asks the user for clarification rather than making assumptions.

---

## 📂 Project Structure

```
ledgermind/
├── agents/
│   ├── __init__.py
│   ├── discovery.py          # Excel/CSV structure discovery + mapping
│   ├── compliance.py         # ITC checks, reconciliation, 43B(h)
│   └── strategist.py         # Vendor ranking, cash flow, optimization
│
├── core/
│   ├── __init__.py
│   ├── data_engine.py        # DuckDB integration (Excel → SQL)
│   ├── schema.py             # Standard Data Model definitions
│   ├── mapper.py             # Header mapping with LLM
│   └── knowledge.py          # ChromaDB for GST rule lookups
│
├── orchestration/
│   ├── __init__.py
│   ├── workflow.py           # LangGraph agent orchestration
│   └── router.py             # Intent classification (task vs question)
│
├── llm/
│   ├── __init__.py
│   └── client.py             # Ollama/Qwen integration
│
├── knowledge/                # Authoritative rules → ChromaDB (static)
│   ├── gst/                  # GST Act, CGST Rules, Notifications
│   └── accounting/           # Ind AS, Accounting Standards
│
├── workspace/                # User's company data → DuckDB (dynamic)
│   └── sample_company/       # Example data for testing
│
├── config.py                 # All configuration
├── main.py                   # Entry point
└── requirements.txt
```

### Data Separation Philosophy

| Folder | Contains | Engine | Role |
|--------|----------|--------|------|
| `knowledge/` | PDFs (GST Acts, Accounting Standards) | ChromaDB | **Rules** — What the AI knows |
| `workspace/` | Excel/CSV (user's financial data) | DuckDB | **Facts** — What to analyze |

---

## 🚀 Quick Start

### Prerequisites

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull the model
ollama pull qwen2.5:7b-instruct

# Start Ollama server (keep running)
ollama serve
```

### Installation

```bash
# Clone and setup
git clone <repo-url>
cd ledgermind

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Usage

```bash
# Analyze a folder of Excel files
python main.py /path/to/company/excels/

# Ask a question
python main.py "What is the ITC eligibility for hotel stays?"

# Interactive mode
python main.py
```

---

## 📋 Workflow Examples

### Workflow A: "Messy Excel" Ingestion

```
1. User drops folder with: Sales_2025.xlsx, Purchases.xlsx, HDFC_Statement.csv

2. Discovery Agent scans headers:
   - Sales_2025.xlsx → "InvoiceDate", "CustomerGSTIN", "TotalAmt" → Sales_Register
   - Purchases.xlsx → "VendorName", "BillNo", "TaxableValue" → Purchase_Ledger  
   - HDFC_Statement.csv → "Date", "Description", "Credit", "Debit" → Bank_Statement

3. Mapper creates Standard Data Model:
   - "TotalAmt" → gross_value
   - "TaxableValue" → taxable_value
   - Saves mapping to discovery_meta.json

4. Data loaded into DuckDB as queryable SQL tables
```

### Workflow B: Real-Time Tax Planning

```
User: "What is my tax liability for this quarter?"

1. Compliance Agent queries DuckDB:
   - SELECT SUM(output_tax) FROM sales WHERE quarter = 'Q4-2025'
   - SELECT SUM(input_tax) FROM purchases WHERE itc_eligible = true

2. Cross-checks with ChromaDB:
   - Verifies tax rates against 2026 GST slabs
   - Checks Section 43B(h) for overdue vendor payments

3. Returns:
   "Q4 Tax Liability: ₹1,84,500
    - Output Tax: ₹3,20,000
    - Eligible ITC: ₹1,35,500
    ⚠️ Warning: ₹45,000 ITC at risk due to 2 vendors past 45-day payment"
```

---

## 🗺️ Roadmap

### Phase 1: Foundation (Current)
- [ ] DuckDB integration (Excel → SQL)
- [ ] Discovery Agent (header mapping)
- [ ] ChromaDB with GST 2026 rules
- [ ] Basic LLM integration

### Phase 2: Compliance Engine
- [ ] Compliance Agent (ITC verification)
- [ ] Section 43B(h) monitoring
- [ ] Section 17(5) blocked credit detection
- [ ] GSTR reconciliation

### Phase 3: Strategic Intelligence
- [ ] Strategist Agent
- [ ] Vendor ranking system
- [ ] Cash flow forecasting
- [ ] Profit optimization

### Phase 4: Production
- [ ] Web UI
- [ ] Multi-company support
- [ ] Report generation (GSTR-1, GSTR-3B)
- [ ] Audit trail

---

## 🎯 Design Principles

1. **Agents over Chatbots** — Autonomous task execution, not just Q&A
2. **SQL over Embeddings for Data** — DuckDB for financial data, ChromaDB for rules only
3. **Local over Cloud** — Privacy-first, $0 cost
4. **Python Calculates, LLM Reasons** — Never let LLM do arithmetic
5. **Ask, Don't Guess** — Clarify unknown data rather than hallucinate

---

## 📚 Knowledge Sources

| Source | Purpose | Storage |
|--------|---------|---------|
| GST Act 2017 | Tax rules, sections, definitions | ChromaDB |
| CGST Rules 2017 | Procedural requirements | ChromaDB |
| GST 2026 Notifications | Rate changes, exemptions | ChromaDB |
| User Excel/CSV | Actual financial data | DuckDB |

---

## 🤝 Contributing

This is an active development project. Core philosophy:
- Keep it simple
- Local-first, privacy-first
- Agents that actually work, not demos

---

**Status:** 🚧 Rebuilding with Agentic Architecture  
**Philosophy:** Autonomous AI CFO > Chatbot  
**Stack:** Ollama + DuckDB + ChromaDB + LangGraph

*Last Updated: January 5, 2026*
