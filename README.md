# LedgerMind

**AI CFO for Small Businesses** — Ask anything about your finances.

---

## 🎯 What Is This?

Small businesses have messy Excel files and confusing tax rules.  
**LedgerMind** is an AI that reads your files and answers questions.

---

## 🧠 How It Works (For Non-Tech People)

### The Simple Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│  STEP 1: Upload                 STEP 2: Ask                        │
│  ─────────────                  ─────────                          │
│                                                                     │
│  📁 Your Excel files    ───▶    💬 "What are my total sales?"      │
│     (sales, purchases)                                              │
│                                          │                          │
│                                          ▼                          │
│                                                                     │
│                              ┌─────────────────┐                   │
│                              │    🧠 AI Brain  │                   │
│                              │                 │                   │
│                              │  Reads files    │                   │
│                              │  Knows GST rules│                   │
│                              │  Finds answer   │                   │
│                              └────────┬────────┘                   │
│                                       │                             │
│                                       ▼                             │
│                                                                     │
│                              📊 "Your total sales: ₹5,00,000"      │
│                                                                     │
│  STEP 3: Get Answer                                                │
│  ──────────────────                                                 │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### What You Can Ask

| Question Type | Example | Where AI Looks |
|---------------|---------|----------------|
| **Your Data** | "Show my November sales" | Your Excel files |
| **Tax Rules** | "What is CGST?" | GST knowledge base |
| **Tax Rates** | "GST on laptops?" | Rate database |
| **Compliance** | "Any tax issues?" | Checks your data |

**One input box. AI figures out the rest.**

---

## 🔌 How Customers Use It

We provide an **API** (like OpenAI). Customers call it from their code.

| What | How |
|------|-----|
| **Upload files** | `POST /api/v1/upload` + your Excel files |
| **Ask anything** | `POST /api/v1/query` + your question |

```bash
# Example: Ask a question
curl -X POST http://localhost:8000/api/v1/query \
  -H "X-API-Key: YOUR_KEY" \
  -d '{"query": "What is my total sales?"}'

# Response
{"answer": "Your total sales: ₹5,00,000"}
```

**No UI from us.** Customers build their own or use the API directly.

---

## 📁 Project Structure (Simplified)

```
ledgermind/
│
├── 🧠 LLM Brain
│   ├── llm/                  # Talks to AI model
│   └── orchestration/        # Routes questions to right place
│
├── 📊 Data Sources  
│   ├── core/data_engine.py   # Reads customer Excel files
│   ├── core/knowledge.py     # GST rules database
│   └── db/                   # Tax rates (CSV files)
│
├── 🌐 API (for customers)
│   └── api/                  # FastAPI endpoints
│
├── 🔧 Internal Tools
│   └── streamlit/            # Our testing UI (not for customers)
│
└── 📂 Customer Data
    └── workspace/            # Each customer's files stored here
```

---

## 🚀 Quick Start

```bash
# 1. Setup
pip install -r requirements.txt

# 2. Start AI
ollama pull qwen2.5:7b-instruct
ollama serve

# 3. Start API
uvicorn api.app:app --port 8000

# 4. Create API key for a customer
python -m streamlit.api_keys create company_name
```

**API ready at:** http://localhost:8000/docs

---

## 📈 Current Status

| What | Status |
|------|--------|
| AI Brain | ✅ Working |
| Read Excel/CSV | ✅ Working |
| GST Knowledge | ✅ 1,276 rules loaded |
| API | ✅ 2 endpoints |
| Customer Isolation | ✅ Each customer separate |

### Known Limitations

- SQL accuracy ~70% (improving in Phase 2)
- Needs Ollama running locally

---

## 🗺️ Roadmap

```
DONE ✅              NEXT                    FUTURE
   │                  │                        │
   ▼                  ▼                        ▼
┌────────┐      ┌────────┐      ┌────────┐      ┌────────┐
│ Phase 1│      │Phase 1B│      │ Phase 2│      │ Phase 3│
│        │      │        │      │        │      │        │
│ AI Core│─────▶│  API   │─────▶│ Better │─────▶│Advanced│
│        │      │        │      │  SQL   │      │Features│
│  DONE  │      │  DONE  │      │        │      │        │
└────────┘      └────────┘      └────────┘      └────────┘
```

---

## ❓ FAQ

**Q: Is my data safe?**  
> Yes. Everything runs on your computer. Nothing goes to cloud.

**Q: Why no web dashboard?**  
> We're API-only. Like OpenAI — you call our API, build your own UI.

**Q: What if AI gives wrong answer?**  
> Rephrase your question. Phase 2 will have better accuracy.

---

**Built for Indian MSMEs 🇮🇳**
