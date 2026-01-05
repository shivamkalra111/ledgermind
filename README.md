# LedgerMind

**Your AI-Powered CFO for Small Businesses** — Making tax compliance simple and automatic.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Status: Phase 1](https://img.shields.io/badge/status-Phase%201-orange.svg)]()

---

## 🎯 The Problem We Solve

**Indian MSMEs face a nightmare:**
- Messy Excel files everywhere (sales, purchases, bank statements)
- Confusing GST rules that change every year
- Fear of tax penalties and compliance issues
- No idea if vendors are reliable or cash flow is healthy
- Can't afford a full-time CFO or CA

**LedgerMind is your AI assistant that:**
- Reads your Excel files and understands them automatically
- Knows all GST rules (updated for 2025-26)
- Finds tax savings you're missing
- Warns you before compliance deadlines
- Answers your finance questions in plain language

**100% Private** — Everything runs on your computer. Your data never goes to the cloud.

---

## 🧠 How It Works (Simple Explanation)

Think of LedgerMind as having **3 AI employees** working for you:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│   📂 YOUR EXCEL FILES                                                   │
│   (Sales, Purchases, Bank Statements)                                   │
│                         │                                               │
│                         ▼                                               │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │                    🤖 AI BRAIN (LedgerMind)                     │   │
│   │                                                                 │   │
│   │   ┌───────────┐   ┌───────────┐   ┌───────────┐               │   │
│   │   │ DISCOVERY │   │ AUDITOR   │   │ ADVISOR   │               │   │
│   │   │   Agent   │   │   Agent   │   │   Agent   │               │   │
│   │   │           │   │           │   │           │               │   │
│   │   │ "I read   │   │ "I check  │   │ "I find   │               │   │
│   │   │  your     │   │  for tax  │   │  savings  │               │   │
│   │   │  files"   │   │  mistakes"│   │  & risks" │               │   │
│   │   └───────────┘   └───────────┘   └───────────┘               │   │
│   │         │               │               │                       │   │
│   │         └───────────────┼───────────────┘                       │   │
│   │                         ▼                                       │   │
│   │              ┌─────────────────────┐                           │   │
│   │              │   📚 KNOWLEDGE      │                           │   │
│   │              │   GST Rules 2025    │                           │   │
│   │              │   Tax Rates         │                           │   │
│   │              │   Compliance Laws   │                           │   │
│   │              └─────────────────────┘                           │   │
│   └─────────────────────────────────────────────────────────────────┘   │
│                         │                                               │
│                         ▼                                               │
│   📊 INSIGHTS FOR YOU                                                   │
│   • "You overpaid ₹12,400 in GST last month"                           │
│   • "Warning: Payment to ABC Traders is overdue"                        │
│   • "Your best vendor is XYZ Supplies (98% reliable)"                  │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### The 3 AI Agents Explained

| Agent | What It Does | Real-World Analogy |
|-------|--------------|-------------------|
| 🔍 **Discovery Agent** | Reads your messy Excel files and organizes them | Like a junior accountant who sorts through your paperwork |
| ✅ **Compliance Agent** | Checks if you're following GST rules correctly | Like a tax auditor checking your books |
| 📈 **Strategist Agent** | Finds savings and warns about problems | Like a CFO giving you business advice |

---

## 💡 What Can You Ask LedgerMind?

### About Your Data
- *"What were my total sales last month?"*
- *"Show me all purchases above ₹50,000"*
- *"Which vendor do I owe the most?"*

### About GST Rules
- *"When should I file GSTR-3B?"*
- *"What is Section 43B(h)?"*
- *"Can I claim ITC on office furniture?"*

### Compliance Checks
- *"Run a compliance check"*
- *"Are there any tax issues?"*
- *"Check my vendor payments"*

---

## 🏗️ System Architecture (For the Curious)

```
┌──────────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE                               │
│                    (Command Line / Terminal)                         │
└──────────────────────────────────┬───────────────────────────────────┘
                                   │
                                   ▼
┌──────────────────────────────────────────────────────────────────────┐
│                      ORCHESTRATION LAYER                             │
│  ┌────────────────┐    ┌─────────────────────────────────────────┐  │
│  │ Intent Router  │───▶│ Workflow Engine                         │  │
│  │                │    │ (Coordinates which agent does what)     │  │
│  │ "What does the │    └─────────────────────────────────────────┘  │
│  │  user want?"   │                                                  │
│  └────────────────┘                                                  │
└──────────────────────────────────┬───────────────────────────────────┘
                                   │
            ┌──────────────────────┼──────────────────────┐
            ▼                      ▼                      ▼
┌───────────────────┐  ┌───────────────────┐  ┌───────────────────┐
│  DISCOVERY AGENT  │  │  COMPLIANCE AGENT │  │  STRATEGIST AGENT │
│                   │  │                   │  │                   │
│  • Read Excel/CSV │  │  • Tax rate check │  │  • Vendor ranking │
│  • Map headers    │  │  • ITC validation │  │  • Cash forecast  │
│  • Create tables  │  │  • 43B(h) alerts  │  │  • Profit analysis│
└─────────┬─────────┘  └─────────┬─────────┘  └─────────┬─────────┘
          │                      │                      │
          └──────────────────────┼──────────────────────┘
                                 │
┌────────────────────────────────┴─────────────────────────────────────┐
│                           CORE LAYER                                 │
│                                                                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │
│  │ Data Engine │  │ Knowledge   │  │ Guardrails  │  │   Metrics   │ │
│  │  (DuckDB)   │  │    Base     │  │  (Safety)   │  │  (Tracking) │ │
│  │             │  │ (ChromaDB)  │  │             │  │             │ │
│  │ Your Excel  │  │ GST PDFs &  │  │ Validates   │  │ Tracks      │ │
│  │ as Database │  │ Tax Rules   │  │ all inputs  │  │ performance │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘ │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌──────────────────────────────────────────────────────────────────────┐
│                         AI BRAIN (LOCAL)                             │
│                                                                      │
│         🧠 Qwen 2.5 (7B) running via Ollama on YOUR computer         │
│                     (No internet required)                           │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 📁 Project Structure (What's Inside)

```
ledgermind/
│
├── 🤖 agents/                     # The 3 AI workers
│   ├── discovery.py               # Reads and organizes your files
│   ├── compliance.py              # Checks tax rules
│   └── strategist.py              # Gives business advice
│
├── ⚙️ core/                       # The engine room
│   ├── data_engine.py             # Turns Excel into searchable database
│   ├── knowledge.py               # Stores GST rules for quick lookup
│   ├── guardrails.py              # Safety checks (validates GSTINs, etc.)
│   ├── metrics.py                 # Tracks system performance
│   ├── schema.py                  # Standard format for all data
│   └── mapper.py                  # Maps messy headers to standard names
│
├── 🎯 orchestration/              # The traffic controller
│   ├── router.py                  # Understands what you're asking
│   └── workflow.py                # Coordinates the agents
│
├── 🧠 llm/                        # AI brain connection
│   └── client.py                  # Talks to the Ollama AI model
│
├── 📊 db/                         # Reference data (pre-loaded)
│   ├── gst_rates/                 # Tax rates for 89 goods + 50 services
│   │   ├── goods_rates_2025.csv   # GST on products (HSN codes)
│   │   └── services_rates_2025.csv# GST on services (SAC codes)
│   ├── msme_classification.csv    # Micro/Small/Medium limits
│   └── state_codes.csv            # All Indian state GST codes
│
├── 📚 knowledge/                  # Legal documents (PDFs)
│   ├── gst/                       # CGST Act, Rules
│   └── accounting/                # Accounting standards
│
├── 📂 workspace/                  # YOUR company data goes here
│   └── sample_company/            # Example files to try
│
├── 📖 docs/                       # Detailed documentation
│   ├── ARCHITECTURE.md            # Technical deep-dive
│   └── ROADMAP.md                 # Future plans
│
├── 🔧 scripts/                    # Helper tools
│   ├── create_sample_data.py      # Generate test data
│   └── ingest_knowledge.py        # Load PDFs into knowledge base
│
├── main.py                        # 🚀 Start here!
├── config.py                      # Settings
└── requirements.txt               # Required packages
```

---

## 🛡️ Safety Features (Guardrails)

LedgerMind is designed to be **safe and reliable**:

| Feature | What It Does |
|---------|--------------|
| **GSTIN Validation** | Checks if tax IDs are real and correctly formatted |
| **Math Safety** | AI never does calculations — only the computer does (no mistakes!) |
| **Data Locality** | Your files never leave your computer |
| **Source Citations** | Always shows which rule or document an answer comes from |

---

## 📈 Current Status

### What's Working Now ✅

| Feature | Status | What You Can Do |
|---------|--------|-----------------|
| **Read Excel/CSV** | ✅ Ready | Drop your files, we understand them |
| **GST Q&A** | ✅ Ready | Ask any GST question |
| **Tax Rate Lookup** | ✅ Ready | 89 goods + 50 services |
| **Compliance Check** | ✅ Ready | Find tax issues |
| **GSTIN Validation** | ✅ Ready | Verify tax IDs |

### Coming Soon 🚧

| Feature | Phase | Description |
|---------|-------|-------------|
| **ITC Reconciliation** | Phase 2 | Match your purchases with GSTR-2B |
| **43B(h) Alerts** | Phase 2 | Warn before MSME payment deadlines |
| **Vendor Scoring** | Phase 3 | Rate vendors by reliability |
| **Cash Flow Forecast** | Phase 3 | Predict next 3 months |
| **Web Interface** | Phase 4 | Beautiful dashboard |
| **PDF Reports** | Phase 4 | Export audit reports |

---

## 🚀 Quick Start

### Step 1: Install (One Time)

```bash
cd ledgermind
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Step 2: Start AI Brain

```bash
# Install Ollama (if not installed)
curl -fsSL https://ollama.com/install.sh | sh

# Download the AI model (4GB, one time)
ollama pull qwen2.5:7b-instruct

# Start Ollama server
ollama serve
```

### Step 3: Run LedgerMind

```bash
python main.py
```

### Step 4: Try It!

```
You> analyze folder workspace/sample_company/
You> run compliance check
You> When should I file GSTR-3B?
You> What is the GST rate on laptops?
```

---

## 📅 Development Roadmap

```
        NOW                    NEXT                   FUTURE
         │                      │                       │
         ▼                      ▼                       ▼
┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐
│   PHASE 1       │   │   PHASE 2       │   │   PHASE 3 & 4   │
│   FOUNDATION    │   │   COMPLIANCE    │   │   INTELLIGENCE  │
│                 │   │                 │   │                 │
│ ✅ Read files   │   │ • ITC matching  │   │ • Vendor scores │
│ ✅ GST Q&A      │   │ • 43B(h) alerts │   │ • Cash forecast │
│ ✅ Tax rates    │   │ • HSN verify    │   │ • Web dashboard │
│ ✅ Compliance   │   │ • Audit reports │   │ • PDF exports   │
│    checks       │   │                 │   │                 │
│                 │   │                 │   │                 │
│   ~80% done     │   │   Coming next   │   │   Future        │
└─────────────────┘   └─────────────────┘   └─────────────────┘
```

---

## 📚 GST 2025-26 Knowledge

LedgerMind knows about:

| Category | Coverage |
|----------|----------|
| **GST Slabs** | 0%, 5%, 12%, 18%, 28% + Cess |
| **HSN Codes** | 89 common goods with rates |
| **SAC Codes** | 50 common services with rates |
| **Section 43B(h)** | MSME payment rules (45 days) |
| **Section 17(5)** | Blocked ITC items |
| **MSME Classification** | Micro/Small/Medium limits |

---

## ❓ FAQ

**Q: Is my data safe?**
> Yes! Everything runs on your computer. No data goes to any server.

**Q: Do I need internet?**
> Only to download the AI model once. After that, works offline.

**Q: How accurate is it?**
> Tax rules come from official CGST Act/Rules. AI provides explanations but always verify with your CA for critical decisions.

**Q: What Excel formats work?**
> .xlsx, .xls, and .csv files. Any format your accountant uses.

**Q: Can I use it for multiple companies?**
> Yes! Create separate folders in `workspace/` for each company.

---

## 🤝 Contributing

This project is under active development. Ideas and contributions welcome!

---

## 📄 License

MIT License — Free to use for personal and commercial purposes.

---

**Built with ❤️ for Indian MSMEs**

*Making tax compliance less painful, one Excel file at a time.*
