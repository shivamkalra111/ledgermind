# LedgerMind: LLM-Powered Accounting & Compliance Assistant

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Status: MVP Development](https://img.shields.io/badge/status-MVP%20Development-orange.svg)]()

> An open-source AI assistant for accountants, SMEs, and finance teams that combines LLMs with accounting rules to provide intelligent, compliance-aware insights.

---

## 🎯 Vision

Build a **Tally-like accounting software** augmented with AI intelligence for natural language queries, real-time compliance checking, and intelligent financial insights — completely open-source and API-free.

## ✨ Key Features

- 🗣️ **Natural Language Understanding**: Ask questions in plain English like *"Why is my ITC lower this month?"*
- 🔍 **RAG-Powered Retrieval**: Only relevant rules and provisions are retrieved to ground AI responses
- ✅ **Rule-Grounded Reasoning**: AI outputs are validated against encoded compliance rules to prevent hallucinations
- 📊 **Structured JSON Output**: Responses include `finding`, `confidence`, `rules_used`, and `recommended_action`
- 🔄 **Extensible Knowledge Base**: Easily ingest new financial rules, legal updates, or company data

## 🏗️ Architecture

```
User Query (Natural Language)
         ↓
Intent Classification
         ↓
RAG: ChromaDB Retrieval
  • GST/TDS Rules
  • Accounting Heuristics
  • Company Summaries
         ↓
LLM: Qwen2.5-7B-Instruct
  • Context-aware Reasoning
  • Structured Output Generation
         ↓
Rule Validation Layer
  • Cross-check with Source Rules
  • Confidence Scoring
         ↓
JSON Response
```

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| **LLM** | Qwen2.5-7B-Instruct (4-bit quantized) |
| **Embeddings** | bge-large-en-v1.5 |
| **Vector DB** | ChromaDB |
| **Framework** | Python 3.9+ |
| **Future** | FastAPI + Streamlit/React |

**Why this stack?**
- ✅ 100% open-source (no API costs)
- ✅ Runs locally (data privacy)
- ✅ Production-ready and scalable

## 🚀 Quick Start

```bash
# Clone the repository
git clone https://github.com/yourusername/ledgermind.git
cd ledgermind

# Install dependencies
pip install -r requirements.txt

# Run the MVP (coming soon)
python main.py
```

## 💡 Usage Example

**Query:**
```
"Why is my ITC lower this month?"
```

**AI Response:**
```json
{
  "intent": "GST_ITC_DIAGNOSTIC",
  "finding": "ITC reduced because supplier has not filed GSTR-1",
  "confidence": 0.87,
  "rules_used": ["GST_ITC_17_5"],
  "recommended_action": "Follow up with supplier or defer ITC claim"
}
```

## 📊 Current Status

**Phase:** Phase 1 - MVP Development  
**Progress:** Data Collection & Setup (30%)

| Milestone | Status |
|-----------|--------|
| Project Setup | ✅ Complete |
| Data Collection (GST Rules) | 🔄 In Progress |
| ChromaDB Integration | ⏳ To-Do |
| LLM Integration | ⏳ To-Do |
| Rule Validation | ⏳ To-Do |
| MVP Testing | ⏳ To-Do |

See [DEVELOPMENT.md](DEVELOPMENT.md) for detailed roadmap and implementation tasks.

## 🎓 For Beginners

New to LLMs, RAG, or ChromaDB? Check out [GETTING_STARTED.md](GETTING_STARTED.md) for:
- Complete setup tutorials
- Concept explanations
- Step-by-step code examples
- Common troubleshooting

## 📂 Project Structure

```
ledgermind/
├── data/
│   ├── gst/              # GST rules and provisions
│   └── accounting/       # Accounting rules
├── rag/                  # RAG pipeline (embeddings, retrieval)
├── llm/                  # LLM inference and validation
├── main.py               # Entry point
└── requirements.txt      # Dependencies
```

## 🗺️ Roadmap

- **Phase 1 (Current):** Single GST query → RAG retrieval → LLM answer → Validation
- **Phase 2:** Scale to 50+ rules with confidence scoring and evaluation harness
- **Phase 3:** Full accounting features (ledgers, vouchers, reports) + Web UI
- **Phase 4:** Multi-language support, banking integration, cloud deployment

## 🤝 Contributing

Contributions are welcome! This project especially needs:

- 📜 GST/TDS rule collection and formatting
- 💼 Accounting domain expertise
- 🧪 Testing and evaluation
- 🎨 UI/UX design (Phase 3)

Please see [DEVELOPMENT.md](DEVELOPMENT.md) for contribution guidelines.

## 🎯 Why LedgerMind?

| Problem | LedgerMind Solution |
|---------|-------------------|
| ❌ Pure LLMs hallucinate on accounting rules | ✅ RAG grounds responses in actual regulations |
| ❌ Traditional software lacks natural language interface | ✅ Ask questions like talking to an accountant |
| ❌ Compliance is complex and error-prone | ✅ AI validates and explains rules automatically |
| ❌ Paid APIs are expensive for SMEs | ✅ 100% open-source, runs locally |

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 📧 Contact

For questions, suggestions, or collaboration:
- Open an issue on GitHub
- Email: [your-email@example.com]

---

**Built with ❤️ for accountants, by developers who understand compliance is hard.**

*Last Updated: December 30, 2025*
