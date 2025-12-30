# LedgerMind: LLM-Powered Accounting & Compliance Assistant

## 🎯 Project Vision
Build a **Tally-like accounting software** augmented with LLM intelligence for natural language queries, compliance checking, and intelligent financial insights.

**Current Focus:** LLM + RAG Foundation (Phase 1)

---

## 📊 Project Status

| Component | Status | Progress |
|-----------|--------|----------|
| Project Setup | ✅ Complete | 100% |
| RAG Architecture Design | ✅ Complete | 100% |
| Data Collection (GST Rules) | 🔄 In Progress | 30% |
| ChromaDB Integration | ⏳ To-Do | 0% |
| LLM Integration (Qwen2.5) | ⏳ To-Do | 0% |
| Rule Validation Layer | ⏳ To-Do | 0% |
| MVP Testing | ⏳ To-Do | 0% |
| Accounting Software Features | 📅 Future | 0% |

**Legend:** ✅ Complete | 🔄 In Progress | ⏳ To-Do | 📅 Future Phase

---

## 1. Project Overview

LedgerMind is an open-source project designed to integrate Large Language Models (LLMs) with accounting and compliance data to provide intelligent, rule-aware insights. The system acts as an AI assistant for accountants, SMEs, and finance teams, helping them understand, validate, and interpret financial and tax-related queries.

Unlike traditional accounting software, LedgerMind does not simply store or report data. Instead, it uses RAG (Retrieval-Augmented Generation) and domain-specific rules to ensure that the AI's outputs are grounded, accurate, and actionable.

## 2. Motivation

Accounting and compliance tasks are often:

Complex and regulation-heavy (e.g., GST, TDS, ITC rules in India)

Error-prone when done manually

Time-consuming for SMEs and even experienced accountants

Problems we aim to solve:

Natural language queries over financial data

Instant explanations for compliance issues

Rule-grounded reasoning to reduce errors and hallucinations

Structured outputs ready for reporting, alerts, or automation

By combining LLMs, structured financial data, and domain rules, LedgerMind can assist users in making informed decisions quickly.

3. Key Features

Natural Language Understanding: Users can ask questions in plain English (or Hinglish) like “Why is my ITC lower this month?”

RAG-Powered Knowledge Retrieval: Only relevant rules, legal provisions, and financial summaries are retrieved to answer queries.

Rule-Grounded Reasoning: AI output is always constrained by encoded accounting and compliance rules.

Structured Output: Responses are returned in JSON with fields such as finding, confidence, rules_used, and recommended_action.

Extensible Knowledge Base: The system can ingest new financial rules, company summaries, or legal updates as they become available.

4. High-Level Architecture
+-----------------+
|   User Query    |
+-----------------+
          |
          v
+--------------------------+
|  Intent Classification   |
+--------------------------+
          |
          v
+--------------------------+
| RAG: ChromaDB Retrieval  |
| - GST rules              |
| - Accounting rules       |
| - Company summaries      |
+--------------------------+
          |
          v
+--------------------------+
|    Open-Source LLM       |
| - Qwen2.5-7B-Instruct    |
| - Context-aware reasoning|
+--------------------------+
          |
          v
+--------------------------+
|  Rule Validation Layer   |
+--------------------------+
          |
          v
+--------------------------+
|  Structured JSON Output  |
+--------------------------+


ChromaDB: Stores embeddings for GST laws, accounting rules, and company-specific summaries

Open-Source LLM: Performs reasoning over retrieved context

Validation Layer: Ensures output adheres to rules and avoids hallucinations

5. Open-Source Stack
Layer	Tool / Model
LLM	Qwen2.5-7B-Instruct (4-bit, CPU/GPU compatible)
Embeddings	bge-large-en-v1.5
Vector DB	ChromaDB
Orchestration	Python + LangChain / LlamaIndex optional
Rules	Python dictionaries / JSON
Evaluation	Custom scripts / test cases

This stack is chosen for cost-free development and scalable, production-ready architecture.

6. Data Requirements

The LLM works on three types of knowledge:

Legal & Tax Rules: Summaries of GST provisions, TDS, ITC, e-invoicing rules

Accounting Rules & Heuristics: Ledger validation rules, transaction classifications, alerts

Company-Specific Summaries: Aggregated ledger data, trial balance summaries, voucher statistics

All of these are pre-processed and embedded into ChromaDB for retrieval.

7. Implementation Roadmap

### 🔄 **Phase 1: LLM + RAG Foundation (CURRENT FOCUS - MVP)**

**Goal:** Prove that RAG + LLM can answer one GST query accurately

#### Tasks:

- [x] **Step 1.1:** Create project structure (`data/`, `rag/`, `llm/`)
- [x] **Step 1.2:** Write project README and architecture
- [ ] **Step 1.3:** Collect and format 5-10 GST rules as text documents
  - Status: 🔄 In Progress
  - Location: `data/gst/`
  - Format: Markdown or plain text with rule IDs
- [ ] **Step 1.4:** Set up ChromaDB locally
  - Install dependencies
  - Initialize vector store
  - Test basic insertion/retrieval
- [ ] **Step 1.5:** Implement embedding pipeline
  - Use `bge-large-en-v1.5`
  - Chunk GST documents (500-1000 tokens)
  - Store in ChromaDB with metadata
- [ ] **Step 1.6:** Download and quantize Qwen2.5-7B-Instruct
  - Test inference speed
  - Verify JSON output capability
- [ ] **Step 1.7:** Build RAG query pipeline
  - User query → Embed query → Retrieve top-k chunks → Pass to LLM
  - Implement prompt template for structured output
- [ ] **Step 1.8:** Implement rule validation layer
  - Define validation schema
  - Cross-check LLM output against retrieved rules
- [ ] **Step 1.9:** Test with sample queries
  - "Why is my ITC lower this month?"
  - "Can I claim ITC on office supplies?"
  - Measure: Accuracy, retrieval relevance, response time
- [ ] **Step 1.10:** Document results and learnings

**Success Criteria:**
- One GST query answered correctly with 80%+ confidence
- Response includes `rules_used` field with correct rule IDs
- No hallucinations (validated against source documents)

---

### ⏳ **Phase 2: Scale Knowledge Base**

**Goal:** Handle 50+ rules across GST, TDS, and accounting domains

#### Tasks:

- [ ] **Step 2.1:** Expand GST rule coverage (20-30 rules)
- [ ] **Step 2.2:** Add accounting rules (ledger validation, transaction classification)
- [ ] **Step 2.3:** Add company-specific summary templates
- [ ] **Step 2.4:** Implement multi-document retrieval with ranking
- [ ] **Step 2.5:** Add confidence calibration
- [ ] **Step 2.6:** Build evaluation harness (test cases + accuracy metrics)
- [ ] **Step 2.7:** Intent classification layer (rule-based or small classifier)
- [ ] **Step 2.8:** Fine-tune embeddings on accounting corpus (optional)

**Success Criteria:**
- 80%+ accuracy on 50 test queries
- Average response time < 3 seconds
- Confidence scores correlate with actual accuracy

---

### 📅 **Phase 3: Accounting Software Integration**

**Goal:** Build Tally-like features with LLM assistance

#### Tasks:

- [ ] **Step 3.1:** Design data models (Ledger, Voucher, Party, Transaction)
- [ ] **Step 3.2:** Build data ingestion pipeline (CSV, Excel, Tally XML)
- [ ] **Step 3.3:** Implement ledger summarization for RAG
- [ ] **Step 3.4:** Create voucher entry interface with AI suggestions
- [ ] **Step 3.5:** Build trial balance and reports
- [ ] **Step 3.6:** Real-time compliance alerts
- [ ] **Step 3.7:** Natural language report generation
- [ ] **Step 3.8:** Web interface (FastAPI + React/Streamlit)
- [ ] **Step 3.9:** Multi-user support and data isolation
- [ ] **Step 3.10:** Audit logs for all AI-generated insights

**Success Criteria:**
- Can process real company ledger data
- AI assists with 10+ common accounting tasks
- Production-ready deployment (Docker, API)

---

### 📅 **Phase 4: Production & Scale**

- [ ] Fine-tune Qwen on accounting-specific corpus
- [ ] Multi-language support (Hindi, Gujarati for Indian SMEs)
- [ ] Integration with banking APIs for auto-reconciliation
- [ ] Cloud deployment (AWS/GCP/Azure)
- [ ] Role-based access control
- [ ] SaaS features (multi-tenancy, billing)

8. Why This is Important

Demonstrates LLM orchestration for structured reasoning

Bridges AI reasoning + real-world accounting domain

Safe for open-source, low-cost development

Extensible for future SaaS or enterprise integration

9. Usage Example (Phase 1)

Query: “Why is my ITC lower this month?”

RAG retrieves: “ITC cannot be claimed if the supplier has not filed GSTR-1 (Rule GST_ITC_17_5).”

LLM Response (JSON):

{
  "intent": "GST_ITC_DIAGNOSTIC",
  "finding": "ITC reduced because supplier has not filed GSTR-1",
  "confidence": 0.87,
  "rules_used": ["GST_ITC_17_5"],
  "recommended_action": "Follow up with supplier or defer ITC claim"
}

10. Why LLM + RAG is Essential

Pure LLM hallucination is dangerous in accounting

Pure rules are rigid and do not handle natural language queries

Combining RAG + LLM + validation layer gives:

Flexibility

Accuracy

Explainability

11. Current Working Directory Structure

```
ledgermind/
├── data/
│   ├── accounting/          # Accounting rules and heuristics
│   │   └── (to be populated)
│   └── gst/                 # GST rules and provisions
│       └── (🔄 collecting rules)
├── rag/
│   ├── __init__.py         # (⏳ to be created)
│   ├── vector_store.py     # ChromaDB setup
│   ├── embeddings.py       # bge-large embedding wrapper
│   └── retriever.py        # Query → Retrieve logic
├── llm/
│   ├── __init__.py         # (⏳ to be created)
│   ├── model.py            # Qwen2.5 loading and inference
│   ├── prompts.py          # Prompt templates
│   └── validator.py        # Rule validation layer
├── main.py                 # (⏳ entry point for MVP)
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

---

## 12. Next Immediate Steps (This Week)

**Priority tasks to start:**

1. **Populate `data/gst/`** with 5-10 GST rules
   - Format: One rule per file or structured JSON
   - Include: Rule ID, description, conditions, examples
   
2. **Set up development environment:**
   ```bash
   pip install -r requirements.txt
   # Add: chromadb, sentence-transformers, transformers, torch
   ```

3. **Create `rag/vector_store.py`:**
   - Initialize ChromaDB
   - Test document insertion
   
4. **Download and test Qwen2.5-7B-Instruct:**
   - Verify inference works
   - Test JSON output formatting

---

## 13. Git & Reproducibility Plan

Each milestone will be committed to Git:

- ✅ Initial folder structure
- 🔄 GST data collection
- ⏳ RAG ingestion pipeline
- ⏳ LLM integration
- ⏳ Evaluation scripts
- ⏳ MVP demo

Ensures traceability, rollback, and collaboration.

---

## 14. Conclusion

LedgerMind is a first-of-its-kind open-source AI system that augments accounting and compliance workflows with reasoning intelligence.
It is designed to be safe, extensible, and production-ready while being completely implementable without paid APIs.

**Current Status:** Building Phase 1 MVP - LLM + RAG foundation for GST query answering.

**Long-term Goal:** Full-featured Tally-like accounting software with AI-powered insights, compliance checking, and natural language interface.

---

## 15. Contributing & Contact

This is an evolving project. Contributions, suggestions, and feedback are welcome!

**Focus areas for contributors:**
- GST/TDS rule collection and formatting
- Accounting domain knowledge
- LLM prompt engineering
- Testing and evaluation

---

## 16. Tech Stack Summary

| Layer | Technology | Status |
|-------|-----------|--------|
| **LLM** | Qwen2.5-7B-Instruct (4-bit) | ⏳ To integrate |
| **Embeddings** | bge-large-en-v1.5 | ⏳ To integrate |
| **Vector DB** | ChromaDB | ⏳ To set up |
| **Framework** | Python 3.9+ | ✅ Ready |
| **Orchestration** | Custom (LangChain optional) | 🔄 Building |
| **Frontend** | Streamlit/FastAPI (Phase 3) | 📅 Future |
| **Deployment** | Docker (Phase 4) | 📅 Future |

---

**Last Updated:** December 30, 2025  
**Current Phase:** Phase 1 - Step 1.3 (Data Collection)