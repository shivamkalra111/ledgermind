# LedgerMind

**AI CFO for Small Businesses** — Ask anything about your finances.

---

## 🎯 What Is This?

Small businesses have messy Excel files and confusing tax rules.  
**LedgerMind** is an AI that reads your files, knows GST rules, and answers questions.

---

## 🏗️ Complete Architecture

### The Big Picture

```
┌──────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                      │
│                              LEDGERMIND SYSTEM                                       │
│                                                                                      │
│  ┌────────────────────────────────────────────────────────────────────────────────┐  │
│  │                                                                                │  │
│  │                         📚 PRE-LOADED KNOWLEDGE                                │  │
│  │                         (We provide this - same for all users)                 │  │
│  │                                                                                │  │
│  │   ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐            │  │
│  │   │  GST Rules      │   │  Tax Rates      │   │  Accounting     │            │  │
│  │   │  (PDFs)         │   │  (CSVs)         │   │  Standards      │            │  │
│  │   │                 │   │                 │   │  (PDFs)         │            │  │
│  │   │  • CGST Act     │   │  • 89 goods     │   │                 │            │  │
│  │   │  • GST Rules    │   │  • 50 services  │   │  • AS, Ind AS   │            │  │
│  │   │  • Notifications│   │  • State codes  │   │  • Standards    │            │  │
│  │   │                 │   │  • MSME limits  │   │                 │            │  │
│  │   └────────┬────────┘   └────────┬────────┘   └────────┬────────┘            │  │
│  │            │                     │                     │                      │  │
│  │            └─────────────────────┼─────────────────────┘                      │  │
│  │                                  │                                            │  │
│  │                                  ▼                                            │  │
│  │                    ┌─────────────────────────┐                                │  │
│  │                    │     ChromaDB            │                                │  │
│  │                    │  (Vector Database)      │                                │  │
│  │                    │                         │                                │  │
│  │                    │  1,276 searchable       │                                │  │
│  │                    │  knowledge chunks       │                                │  │
│  │                    └─────────────────────────┘                                │  │
│  │                                                                                │  │
│  └────────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                      │
│  ┌────────────────────────────────────────────────────────────────────────────────┐  │
│  │                                                                                │  │
│  │                         👥 USER DATA                                           │  │
│  │                         (Each user uploads their own - completely separate)    │  │
│  │                                                                                │  │
│  │   User A                      User B                      User C              │  │
│  │   ┌──────────────────┐       ┌──────────────────┐       ┌──────────────────┐  │  │
│  │   │ 📁 Excel Files   │       │ 📁 Excel Files   │       │ 📁 Excel Files   │  │  │
│  │   │ • sales.xlsx     │       │ • invoices.xlsx  │       │ • ledger.xlsx    │  │  │
│  │   │ • purchases.xlsx │       │ • expenses.csv   │       │ • bank.csv       │  │  │
│  │   │                  │       │                  │       │                  │  │  │
│  │   │       ▼          │       │       ▼          │       │       ▼          │  │  │
│  │   │                  │       │                  │       │                  │  │  │
│  │   │ 🗄️ DuckDB        │       │ 🗄️ DuckDB        │       │ 🗄️ DuckDB        │  │  │
│  │   │ (User A's DB)    │       │ (User B's DB)    │       │ (User C's DB)    │  │  │
│  │   │                  │       │                  │       │                  │  │  │
│  │   │ SQL-queryable    │       │ SQL-queryable    │       │ SQL-queryable    │  │  │
│  │   │ tables from      │       │ tables from      │       │ tables from      │  │  │
│  │   │ their files      │       │ their files      │       │ their files      │  │  │
│  │   └──────────────────┘       └──────────────────┘       └──────────────────┘  │  │
│  │                                                                                │  │
│  │   🔒 ISOLATION: User A cannot see User B's data. Each has own database.       │  │
│  │                                                                                │  │
│  └────────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                      │
│  ┌────────────────────────────────────────────────────────────────────────────────┐  │
│  │                                                                                │  │
│  │                         🧠 AI BRAIN (LLM + Agents)                             │  │
│  │                                                                                │  │
│  │   ┌────────────────────────────────────────────────────────────────────────┐  │  │
│  │   │                                                                        │  │  │
│  │   │                    LLM: Query Router (Qwen 2.5)                        │  │  │
│  │   │                                                                        │  │  │
│  │   │   User question comes in ───▶ LLM classifies and routes               │  │  │
│  │   │                                                                        │  │  │
│  │   │   "What are my sales?"  ───▶  DATA_QUERY                              │  │  │
│  │   │   "What is CGST?"       ───▶  KNOWLEDGE_QUERY                         │  │  │
│  │   │   "Check compliance"    ───▶  COMPLIANCE_CHECK                        │  │  │
│  │   │   "Analyze my data"     ───▶  FOLDER_ANALYSIS                         │  │  │
│  │   │                                                                        │  │  │
│  │   └────────────────────────────────────────────────────────────────────────┘  │  │
│  │                                        │                                       │  │
│  │                                        ▼                                       │  │
│  │   ┌────────────────────────────────────────────────────────────────────────┐  │  │
│  │   │                                                                        │  │  │
│  │   │                         🤖 AI AGENTS                                   │  │  │
│  │   │                         (Specialized workers)                          │  │  │
│  │   │                                                                        │  │  │
│  │   │   ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐    │  │  │
│  │   │   │  🔍 DISCOVERY    │  │  ✅ COMPLIANCE   │  │  📈 STRATEGIST   │    │  │  │
│  │   │   │     AGENT        │  │     AGENT        │  │     AGENT        │    │  │  │
│  │   │   │                  │  │                  │  │                  │    │  │  │
│  │   │   │  Reads Excel     │  │  Checks GST      │  │  Gives business  │    │  │  │
│  │   │   │  files, maps     │  │  rules, finds    │  │  advice, finds   │    │  │  │
│  │   │   │  columns, loads  │  │  tax mistakes,   │  │  savings, warns  │    │  │  │
│  │   │   │  into DuckDB     │  │  validates       │  │  about risks     │    │  │  │
│  │   │   │                  │  │  GSTINs          │  │                  │    │  │  │
│  │   │   └──────────────────┘  └──────────────────┘  └──────────────────┘    │  │  │
│  │   │                                                                        │  │  │
│  │   │   Each agent uses LLM + domain knowledge to complete its task         │  │  │
│  │   │                                                                        │  │  │
│  │   └────────────────────────────────────────────────────────────────────────┘  │  │
│  │                                        │                                       │  │
│  │                                        ▼                                       │  │
│  │   ┌────────────────────────────────────────────────────────────────────────┐  │  │
│  │   │                                                                        │  │  │
│  │   │                    LLM: SQL Generator (For data queries)               │  │  │
│  │   │                                                                        │  │  │
│  │   │   "Show November sales"                                               │  │  │
│  │   │         │                                                              │  │  │
│  │   │         ▼                                                              │  │  │
│  │   │   LLM generates SQL: SELECT * FROM sales WHERE month = 'November'     │  │  │
│  │   │         │                                                              │  │  │
│  │   │         ▼                                                              │  │  │
│  │   │   Execute on user's DuckDB ───▶ Format response                       │  │  │
│  │   │                                                                        │  │  │
│  │   └────────────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                                │  │
│  └────────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                      │
│  ┌────────────────────────────────────────────────────────────────────────────────┐  │
│  │                                                                                │  │
│  │                         🌐 ACCESS LAYER                                        │  │
│  │                                                                                │  │
│  │   FOR CUSTOMERS                              FOR US (Internal)                │  │
│  │   ─────────────                              ──────────────────                │  │
│  │                                                                                │  │
│  │   ┌─────────────────────────┐              ┌─────────────────────────┐        │  │
│  │   │      FastAPI            │              │      Streamlit          │        │  │
│  │   │      (REST API)         │              │      (Testing UI)       │        │  │
│  │   │                         │              │                         │        │  │
│  │   │  POST /upload           │              │  • Select customer      │        │  │
│  │   │  POST /query            │              │  • Upload files         │        │  │
│  │   │                         │              │  • Chat with AI         │        │  │
│  │   │  + API Key Auth         │              │  • Debug issues         │        │  │
│  │   │                         │              │                         │        │  │
│  │   └─────────────────────────┘              └─────────────────────────┘        │  │
│  │                                                                                │  │
│  │   Customers call our API                   We use Streamlit to test           │  │
│  │   from their own apps                      (NOT given to customers)           │  │
│  │                                                                                │  │
│  └────────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                      │
└──────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 📊 Component Breakdown

### What We Provide (Pre-loaded)

| Component | Type | Contents | Purpose |
|-----------|------|----------|---------|
| **GST Rules** | PDFs → ChromaDB | CGST Act, Rules, Notifications | Answer legal questions |
| **Tax Rates** | CSV files | 89 goods (HSN), 50 services (SAC) | Rate lookups |
| **State Codes** | CSV file | All 38 GST state codes | GSTIN validation |
| **MSME Limits** | CSV file | Micro/Small/Medium thresholds | Classification |
| **Blocked ITC** | CSV file | Section 17(5) items | ITC eligibility |

### What Users Provide

| What | Formats | Example |
|------|---------|---------|
| **Excel/CSV Files** | .xlsx, .xls, .csv | sales.xlsx, purchases.xlsx, bank_statement.csv |

**That's it.** Users just upload their files. Our system does the rest.

### What Our System Creates (Using LLM)

| Component | Created By | Purpose | Storage |
|-----------|------------|---------|---------|
| **DuckDB Database** | Discovery Agent | SQL-queryable tables from user's files | `workspace/{user}/{user}.duckdb` |
| **Profile** | System | Company info, settings | `workspace/{user}/profile.json` |
| **Data State** | System | Tracks file changes for auto-reload | `workspace/{user}/data_state.json` |

### AI Agents

| Agent | Purpose | When Used | What It Does |
|-------|---------|-----------|--------------|
| **🔍 Discovery Agent** | Understand data | User uploads files | Reads Excel, maps columns to standard names, loads into DuckDB |
| **✅ Compliance Agent** | Check tax rules | "Check compliance" | Validates GSTINs, checks tax calculations, finds mistakes |
| **📈 Strategist Agent** | Business advice | "Analyze my business" | Finds tax savings, warns about risks, vendor analysis |

### LLM Responsibilities

| LLM Role | What It Does | Input | Output |
|----------|--------------|-------|--------|
| **Query Router** | Classifies user question | "What is CGST?" | Route to: Knowledge |
| **Agent Coordinator** | Triggers right agent | "Check compliance" | Run: Compliance Agent |
| **SQL Generator** | Converts question to SQL | "Show sales" | `SELECT * FROM sales` |
| **Response Formatter** | Makes results readable | Raw data | "Your sales: ₹5L" |

### Access Methods

| Method | Who Uses It | Purpose | Authentication |
|--------|-------------|---------|----------------|
| **FastAPI** | Customers | Production use | API Key required |
| **Streamlit** | Us only | Testing & debugging | Internal only |

---

## 🔄 Data Flow Example

### User Asks: "What were my November sales?"

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                                                                 │
│  Step 1: User sends question via API                                           │
│  ───────────────────────────────────                                           │
│                                                                                 │
│  POST /api/v1/query                                                            │
│  { "query": "What were my November sales?" }                                   │
│  Header: X-API-Key: lm_live_xxxxx                                              │
│                                                                                 │
│         │                                                                       │
│         ▼                                                                       │
│                                                                                 │
│  Step 2: API validates key, identifies user                                    │
│  ──────────────────────────────────────────                                    │
│                                                                                 │
│  API Key → User: "acme_corp" → Load acme_corp's DuckDB                        │
│                                                                                 │
│         │                                                                       │
│         ▼                                                                       │
│                                                                                 │
│  Step 3: LLM Router classifies question                                        │
│  ──────────────────────────────────────                                        │
│                                                                                 │
│  "November sales" → DATA_QUERY (needs user's database)                         │
│                                                                                 │
│         │                                                                       │
│         ▼                                                                       │
│                                                                                 │
│  Step 4: LLM generates SQL                                                     │
│  ─────────────────────────                                                     │
│                                                                                 │
│  LLM sees: Table "sales" with columns [date, amount, customer, invoice_no]     │
│  LLM generates: SELECT SUM(amount) FROM sales WHERE date LIKE '%-11-%'         │
│                                                                                 │
│         │                                                                       │
│         ▼                                                                       │
│                                                                                 │
│  Step 5: Execute SQL on user's DuckDB                                          │
│  ────────────────────────────────────                                          │
│                                                                                 │
│  Result: 250000                                                                 │
│                                                                                 │
│         │                                                                       │
│         ▼                                                                       │
│                                                                                 │
│  Step 6: LLM formats response                                                  │
│  ────────────────────────────                                                  │
│                                                                                 │
│  { "answer": "Your November sales were ₹2,50,000" }                           │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 📁 Folder Structure

```
ledgermind/
│
├── 📚 db/                    # Pre-loaded knowledge (CSVs)
├── 📚 knowledge/             # Pre-loaded knowledge (PDFs)
│
├── 🤖 agents/                # AI Agents (Discovery, Compliance, Strategist)
├── 🧠 llm/                   # LLM connection (Ollama)
├── 🎯 orchestration/         # Query routing & workflow
├── ⚙️ core/                   # Data engine, knowledge base, utilities
│
├── 🌐 api/                   # FastAPI (for customers)
├── 🔧 streamlit/             # Streamlit UI (internal testing)
│
├── 👥 workspace/             # User data (per-user, isolated)
│
├── main.py                   # CLI entry point
├── config.py                 # Configuration
└── requirements.txt          # Dependencies
```

---

## 🚀 Quick Start

```bash
# 1. Install
pip install -r requirements.txt

# 2. Start AI model
ollama pull qwen2.5:7b-instruct
ollama serve

# 3. Start API
uvicorn api.app:app --port 8000

# 4. Create API key
python -m streamlit.api_keys create company_name
```

---

## 📈 Current Status

| Layer | Component | Status | Notes |
|-------|-----------|--------|-------|
| **Knowledge** | ChromaDB | ✅ Ready | 1,276 chunks loaded |
| **Knowledge** | Tax CSVs | ✅ Ready | 89 goods, 50 services |
| **User Data** | DuckDB | ✅ Ready | Per-user databases |
| **User Data** | File Detection | ✅ Ready | Auto-reload on change |
| **Agents** | Discovery | ✅ Ready | Reads & maps Excel files |
| **Agents** | Compliance | ✅ Ready | Tax rule checking |
| **Agents** | Strategist | ✅ Ready | Business advice |
| **LLM** | Query Router | ✅ Ready | Classifies all queries |
| **LLM** | SQL Generator | ⚠️ Basic | ~70% accuracy |
| **Access** | FastAPI | ✅ Ready | 2 endpoints |
| **Access** | Streamlit | ✅ Ready | Internal testing |
| **Security** | API Keys | ✅ Ready | Per-user auth |
| **Security** | Data Isolation | ✅ Ready | Users can't see each other |

---

## 🗺️ Roadmap

| Phase | Focus | Status | Key Features |
|-------|-------|--------|--------------|
| **Phase 1** | Core LLM + Agents | ✅ Done | DuckDB, ChromaDB, 3 Agents |
| **Phase 1B** | API Layer | ✅ Done | FastAPI, Auth, Streamlit |
| **Phase 2** | Better SQL | 🔜 Next | Specialized SQL model, 90%+ accuracy |
| **Phase 3** | Advanced | 📅 Planned | Alerts, Reports, Google Sheets |

---

## ❓ FAQ

**Q: Is user data safe?**  
> Yes. Each user has their own DuckDB database. User A cannot access User B's data. Everything runs locally.

**Q: What knowledge does the AI have?**  
> Pre-loaded: GST rules (CGST Act, notifications), tax rates (89 goods, 50 services), MSME limits, state codes. This is same for all users.

**Q: What are the AI Agents?**  
> Three specialized workers: Discovery (reads your files), Compliance (checks tax rules), Strategist (gives business advice). Each uses LLM + domain knowledge.

**Q: What data do users provide?**  
> Users upload their own Excel/CSV files (sales, purchases, bank statements). This becomes their private, queryable database.

**Q: How does the AI know where to look?**  
> LLM Router classifies every question and routes it to the right place: user's DuckDB, ChromaDB knowledge, CSV rates, or an Agent.

**Q: Why no web dashboard for customers?**  
> We're API-only (like OpenAI, Stripe). Customers integrate our API into their own apps. Streamlit is only for our internal testing.

**Q: Can this work offline?**  
> Yes, after initial setup. Ollama runs locally, all data is local.

---

**Built for Indian MSMEs 🇮🇳**
