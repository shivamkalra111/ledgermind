# Complete File Flow Guide

**Understanding what each file does and how they interact**

---

## 🎯 Overview - The Complete Flow

```
User Question
      ↓
   main.py (Entry Point)
      ↓
   rag/pipeline.py (Orchestrates everything)
      ↓
   ┌─────────────────────────────────────┐
   │  1. RETRIEVAL (Find relevant docs)  │
   │     rag/hybrid_search.py            │
   │     ↓                               │
   │     ChromaDB (chroma_db/)           │
   └─────────────────────────────────────┘
      ↓
   ┌─────────────────────────────────────┐
   │  2. GENERATION (Create answer)      │
   │     llm/assistant.py                │
   │     ↓                               │
   │     Ollama (qwen2.5:7b-instruct)    │
   └─────────────────────────────────────┘
      ↓
   ┌─────────────────────────────────────┐
   │  3. METRICS (Track performance)     │
   │     rag/metrics.py                  │
   │     ↓                               │
   │     rag_metrics.jsonl               │
   └─────────────────────────────────────┘
      ↓
   Answer with sources + metrics
```

---

## 📁 Core Files - Detailed Flow

### **1. `config.py` - Central Configuration**

**Purpose:** All settings in one place

**What's Inside:**
```python
# LLM Settings
LLM_MODEL_NAME = "qwen2.5:7b-instruct"
LLM_TEMPERATURE = 0.5    # Creativity (0=factual, 1=creative)
LLM_MAX_TOKENS = 256     # Response length

# Embedding Settings
EMBEDDING_MODEL = "BAAI/bge-large-en-v1.5"  # 1024 dimensions

# RAG Settings
RAG_NUM_RESULTS = 5          # How many chunks to retrieve
RAG_MIN_SIMILARITY = 0.30    # Minimum confidence threshold

# System Prompt
GST_SYSTEM_PROMPT = """You are a GST compliance assistant..."""
```

**Flow:**
- **Who uses it:** Every file imports from here
- **Why:** Change settings once, affects entire system
- **Key for:** Model switching, prompt tuning, retrieval tuning

---

### **2. `main.py` - Entry Point**

**Purpose:** User interaction layer

**Flow:**
```
User runs: python main.py "What is ITC?"
    ↓
main.py:
    1. Initialize RAGPipeline
    2. Pass question to pipeline.answer()
    3. Get result (answer + sources + metrics)
    4. Format and display nicely
    5. Save metrics to rag_metrics.jsonl
```

**What It Does:**
- Handles command-line arguments
- Provides interactive chat mode
- Formats output for readability
- Error handling for user

**Key Functions:**
```python
def main():
    pipeline = RAGPipeline()  # Initialize system
    
    if len(sys.argv) > 1:
        # Single question mode
        question = " ".join(sys.argv[1:])
        result = pipeline.answer(question)
        print_result(result)
    else:
        # Interactive chat mode
        pipeline.chat()
```

**Inputs:** User question (string)
**Outputs:** Formatted answer, sources, metrics
**Calls:** `rag/pipeline.py`

---

### **3. `rag/pipeline.py` - RAG Orchestrator**

**Purpose:** The brain of the system - coordinates retrieval + generation

**Complete Flow:**
```
Question: "What is Input Tax Credit?"
    ↓
[STEP 1: INITIALIZATION]
RAGPipeline.__init__():
    1. Load config settings
    2. Connect to ChromaDB (chroma_db/)
    3. Load embedding function (bge-large)
    4. Initialize HybridSearcher
    5. Initialize LLMAssistant
    6. Initialize RAGMetrics
    ↓
[STEP 2: RETRIEVAL]
answer() method:
    1. Start metrics tracking
    2. Call hybrid_search.hybrid_search()
       → Semantic search (ChromaDB)
       → Keyword search (BM25)
       → Combine scores
       → Boost exact term matches
    3. Get top 5 chunks
    4. Filter by min_similarity (0.30)
    5. Log retrieval metrics
    ↓
Retrieved chunks: [
    {text: "ITC means credit of input tax...", 
     source: "cgst-act.pdf", page: 42, similarity: 0.65},
    ...
]
    ↓
[STEP 3: GENERATION]
    1. Build prompt:
       - System prompt (from config)
       - Context (retrieved chunks)
       - User question
    2. Call llm_assistant.generate_with_context()
    3. Get LLM response
    4. Log generation metrics
    ↓
[STEP 4: METRICS]
    1. Calculate faithfulness (answer grounded in context?)
    2. Calculate relevance (answer addresses question?)
    3. Log final metrics
    4. Save to rag_metrics.jsonl
    ↓
Return: {
    question: "What is Input Tax Credit?",
    answer: "Input Tax Credit is...",
    sources: ["cgst-act.pdf, Page 42"],
    confidence: 0.65,
    faithfulness: 0.88,
    relevance: 0.92,
    time_taken: 2.3
}
```

**Key Methods:**
1. `__init__()` - Setup everything
2. `answer(question)` - Main entry point
3. `_format_sources()` - Format citations
4. `chat()` - Interactive mode

**Inputs:** User question
**Outputs:** Complete result dict
**Calls:** 
- `rag/hybrid_search.py`
- `llm/assistant.py`
- `rag/metrics.py`

---

### **4. `rag/hybrid_search.py` - Smart Retrieval**

**Purpose:** Combines semantic + keyword search for better precision

**Flow:**
```
Query: "What is Section 16 about ITC?"
    ↓
hybrid_search():
    ↓
[STEP 1: SEMANTIC SEARCH]
    1. Convert query to embedding (bge-large)
    2. Search ChromaDB by similarity
    3. Get top 10 results
    → Results: [
        {text: "Section 16: Input Tax Credit...", similarity: 0.70},
        {text: "ITC can be claimed...", similarity: 0.60},
        ...
      ]
    ↓
[STEP 2: KEYWORD SEARCH (BM25)]
    1. Tokenize query: ["section", "16", "itc"]
    2. Run BM25 algorithm on all documents
    3. Get top 10 results
    → Results: [
        {text: "Section 16(2): Conditions...", score: 8.5},
        {text: "Section 16(1): Eligibility...", score: 7.2},
        ...
      ]
    ↓
[STEP 3: EXTRACT IMPORTANT TERMS]
    - Finds: "Section 16", "ITC"
    - These will get boosting
    ↓
[STEP 4: COMBINE & RANK]
    For each unique chunk:
        combined_score = (0.7 × semantic_score) + (0.3 × keyword_score)
        
        If chunk contains "Section 16": boost × 1.2
        If chunk contains "ITC": boost × 1.2
        
        final_score = combined_score × boost_factor
    ↓
    Sort by final_score
    ↓
Return top 5 chunks with highest final_score
```

**Why Hybrid?**
- **Semantic:** Understands "ITC" = "Input Tax Credit"
- **Keyword:** Finds exact "Section 16" references
- **Boost:** Prioritizes chunks with specific terms

**Key Components:**
1. `BM25Okapi` - Keyword search algorithm
2. `ChromaDB.query()` - Semantic search
3. `_extract_important_terms()` - Find section/rule numbers
4. `hybrid_search()` - Main orchestration

**Inputs:** Query string, n_results, semantic_weight
**Outputs:** List of chunks with similarity scores
**Used by:** `rag/pipeline.py`

---

### **5. `llm/assistant.py` - LLM Interface**

**Purpose:** Talk to local Ollama model

**Flow:**
```
LLMAssistant.generate_with_context(
    question="What is ITC?",
    context_chunks=[...],
    system_prompt="You are a GST assistant..."
)
    ↓
[STEP 1: BUILD PROMPT]
_build_prompt():
    Combines:
    ┌────────────────────────────────────┐
    │ System Prompt:                     │
    │ "You are a GST assistant..."       │
    ├────────────────────────────────────┤
    │ Context:                           │
    │ [Source 1: cgst-act.pdf, Page 42]  │
    │ Input Tax Credit means...          │
    │                                    │
    │ [Source 2: cgst-act.pdf, Page 43]  │
    │ Conditions for ITC...              │
    ├────────────────────────────────────┤
    │ User Question:                     │
    │ What is Input Tax Credit?          │
    ├────────────────────────────────────┤
    │ Answer:                            │
    └────────────────────────────────────┘
    ↓
[STEP 2: CALL OLLAMA API]
generate():
    1. POST to http://localhost:11434/api/generate
    2. Payload: {
         model: "qwen2.5:7b-instruct",
         prompt: [full_prompt],
         options: {
           temperature: 0.5,
           top_p: 0.9,
           num_predict: 256
         }
       }
    3. Wait for response (2-20 seconds)
    ↓
[STEP 3: RETURN ANSWER]
    "Input Tax Credit (ITC) is the tax paid on purchases 
     which can be set off against tax payable on sales. 
     To claim ITC, you must possess a valid invoice, 
     have received goods/services, and file returns 
     [Source: CGST Act, Section 16, Page 42]."
```

**Key Methods:**
1. `verify_setup()` - Check Ollama is running
2. `generate()` - Raw LLM call
3. `generate_with_context()` - RAG-specific generation
4. `_build_prompt()` - Construct full prompt

**Why Model-Agnostic?**
- Only need to change `LLM_MODEL_NAME` in `config.py`
- Works with any Ollama model
- No model-specific code

**Inputs:** Prompt (string)
**Outputs:** Generated text (string)
**Calls:** Ollama API (localhost:11434)

---

### **6. `rag/metrics.py` - Performance Tracking**

**Purpose:** Log every query for analysis

**Flow:**
```
RAGMetrics lifecycle for one query:
    ↓
[START]
start_query("What is ITC?"):
    current_query_data = {
        question: "What is ITC?",
        timestamp: "2026-01-01T10:00:00",
        start_time: 1234567890.0,
        ...all fields initialized...
    }
    ↓
[RETRIEVAL]
log_retrieval(
    chunks_retrieved=10,
    chunks_used=5,
    avg_similarity=0.52,
    ...
):
    Update current_query_data:
        chunks_retrieved: 10
        chunks_used: 5
        avg_similarity: 0.52
        retrieval_efficiency: 5/10 = 0.5
    ↓
[GENERATION]
log_generation(
    answer="Input Tax Credit is...",
    generation_time=2.1,
    ...
):
    Update current_query_data:
        answer_length: 250
        answer_words: 45
        generation_time: 2.1
        response_quality_flag: "good"
    ↓
[FINALIZE]
finalize_query(
    total_time=3.5,
    faithfulness=0.88,
    relevance=0.92,
    ...
):
    Update current_query_data:
        total_time: 3.5
        faithfulness: 0.88
        relevance: 0.92
        success: True
        efficiency_score: 0.52 / 3.5 = 0.15
    
    Write to rag_metrics.jsonl:
        {full JSON of all metrics}
    
    Add to query_history (in-memory)
```

**What's Logged:**
```json
{
  "question": "What is Input Tax Credit?",
  "timestamp": "2026-01-01T10:00:00",
  "chunks_retrieved": 10,
  "chunks_used": 5,
  "avg_similarity": 0.52,
  "top_similarity": 0.65,
  "retrieval_time": 0.8,
  "retrieval_efficiency": 0.5,
  "answer_length": 250,
  "answer_words": 45,
  "generation_time": 2.1,
  "total_time": 3.5,
  "confidence_score": 0.52,
  "faithfulness": 0.88,
  "relevance": 0.92,
  "response_quality_flag": "good",
  "efficiency_score": 0.15,
  "success": true,
  "error": null
}
```

**Key Methods:**
1. `start_query()` - Begin tracking
2. `log_retrieval()` - Log retrieval phase
3. `log_generation()` - Log generation phase
4. `finalize_query()` - Write to file
5. `get_summary_statistics()` - Aggregate metrics
6. `calculate_faithfulness()` - Check if grounded in context
7. `calculate_relevance()` - Check if answers question

**Outputs:** `rag_metrics.jsonl` (one JSON per line)
**Used by:** `rag/pipeline.py`, `view_metrics.py`

---

### **7. `rag/enhanced_chunker.py` - Smart Document Splitting**

**Purpose:** Split documents while preserving meaning and adding context

**Flow:**
```
Input: PDF text (294 pages)
    ↓
EnhancedSemanticChunker.chunk(text, metadata):
    ↓
[STEP 1: EXTRACT DOCUMENT CONTEXT]
    - Document title: "CGST Act 2017"
    - Document type: "gst_legal"
    ↓
[STEP 2: FIND SEMANTIC BOUNDARIES]
    Patterns:
    - "Section 16:"  → boundary
    - "Rule 42:"     → boundary
    - "\n\n"         → boundary (paragraph)
    - "(a)"          → boundary (sub-point)
    
    Text split into segments at these points
    ↓
[STEP 3: SENTENCE-AWARE SPLITTING]
    For each segment:
        1. Use NLTK to detect sentence boundaries
        2. Get semantic embeddings for sentences
        3. Calculate similarity between consecutive sentences
        4. If similarity < threshold → new chunk boundary
        5. Merge similar sentences together
    
    Example:
        Original segment:
        "Section 16: Input Tax Credit. ITC means credit. 
         The person shall be entitled. Conditions apply."
        
        After sentence detection:
        ["Section 16: Input Tax Credit.",
         "ITC means credit.",
         "The person shall be entitled.",
         "Conditions apply."]
        
        After semantic merging (if similar):
        ["Section 16: Input Tax Credit. ITC means credit.",
         "The person shall be entitled. Conditions apply."]
    ↓
[STEP 4: SMART SIZING]
    For each potential chunk:
        - If < min_size (200) → merge with next
        - If > max_size (1200) → backtrack to last complete sentence
        - Never break mid-sentence!
    ↓
[STEP 5: CONTEXT ENRICHMENT]
    For each chunk:
        Prepend context:
        ┌─────────────────────────────────────┐
        │ Document: CGST Act 2017             │
        │ Section: Section 16                 │
        │ Type: GST Legal Document            │
        │ Page: 42                            │
        │                                     │
        │ [original chunk text]               │
        └─────────────────────────────────────┘
    
    This context gets embedded too!
    ↓
[STEP 6: METADATA ENRICHMENT]
    Add metadata:
        {
            source: "cgst-act.pdf",
            page: 42,
            document_title: "CGST Act 2017",
            section_id: "Section 16",
            section_title: "Input Tax Credit",
            document_type: "gst_legal",
            chunk_index: 0,
            char_start: 1200,
            char_end: 2350,
            chunk_size: 1150,
            chunking_strategy: "enhanced_semantic"
        }
    ↓
Output: List of enriched chunks
    [
        {
            text: "Document: CGST Act 2017\nSection: Section 16\n...",
            metadata: {...}
        },
        ...
    ]
```

**Why Enhanced?**
1. **Semantic Boundaries** - Respects document structure
2. **Sentence-Aware** - Never breaks mid-sentence
3. **Context-Enriched** - Adds document/section context
4. **Metadata-Rich** - Tracks everything

**Key Methods:**
1. `_get_document_title()` - Extract title from first lines
2. `_find_semantic_boundaries()` - Find section/rule/paragraph breaks
3. `_split_into_sentences_semantically()` - Sentence detection + merging
4. `_extract_section_info()` - Extract section ID and title
5. `chunk()` - Main orchestration

**Inputs:** Text + base metadata
**Outputs:** List of enriched chunks
**Used by:** `scripts/ingest_pdfs.py`

---

## 🔧 Script Files - One-Time Operations

### **8. `scripts/ingest_pdfs.py` - Data Pipeline**

**Purpose:** Convert PDFs → ChromaDB

**Complete Flow:**
```
Run: python scripts/ingest_pdfs.py
    ↓
[INITIALIZATION]
GSTProcessor.__init__():
    1. Load embedding model (bge-large, ~1.3GB download)
    2. Connect to ChromaDB (./chroma_db/)
    3. Get or create collection "gst_rules"
    4. Initialize EnhancedSemanticChunker
    ↓
[FIND PDFs]
process_all_pdfs():
    1. Scan data/gst/ folder
    2. Find all .pdf files
    3. List them: cgst-act.pdf (2.1 MB), cgst-rules.pdf (1.8 MB)
    ↓
[PROCESS EACH PDF]
For each PDF:
    ↓
    [STEP 1: EXTRACT]
    extract_text_from_pdf():
        1. Open PDF with pdfplumber
        2. Extract text page by page
        3. Filter empty pages
        → Result: [
            {page: 1, text: "CGST Act 2017..."},
            {page: 2, text: "Section 1..."},
            ...
          ]
    ↓
    [STEP 2: CHUNK]
    For each page:
        chunker.chunk(text, metadata):
            1. Find semantic boundaries
            2. Split sentences intelligently
            3. Size chunks appropriately
            4. Add context enrichment
            5. Attach metadata
    
    → Result: 855 chunks from 294 pages
    ↓
    [STEP 3: PREPARE]
    For each chunk:
        1. Generate unique ID: "cgst-act_0", "cgst-act_1", ...
        2. Extract text
        3. Clean metadata (remove None values)
    
    → Arrays:
        ids = ["cgst-act_0", "cgst-act_1", ...]
        documents = ["Document: CGST...", "Document: CGST...", ...]
        metadatas = [{source: ..., page: ...}, {...}, ...]
    ↓
    [STEP 4: EMBED & STORE]
    collection.add(ids, documents, metadatas):
        ChromaDB automatically:
        1. Creates embeddings using bge-large (1024-dim)
        2. Stores embeddings in ./chroma_db/
        3. Indexes for fast retrieval
        4. Persists to disk
    
    Progress: [████████████] 855/855 chunks
    ↓
[COMPLETION]
    Print statistics:
    ✅ 294 pages processed
    ✅ 855 chunks created
    ✅ Database: ./chroma_db/
    ✅ Ready for queries!
```

**When to Run:**
- First time setup
- After adding new PDFs
- After changing chunking strategy
- After corrupting database

**Inputs:** PDF files in `data/gst/`
**Outputs:** ChromaDB database in `chroma_db/`
**Time:** 2-5 minutes (first run with model download: 5-10 min)

---

### **9. `view_metrics.py` - Analytics**

**Purpose:** View performance summary

**Flow:**
```
Run: python view_metrics.py
    ↓
Load rag_metrics.jsonl:
    Read all lines
    Parse each JSON
    → query_history = [query1, query2, ...]
    ↓
Calculate statistics:
    total_queries = 50
    successful = 48
    success_rate = 48/50 = 96%
    
    avg_confidence = sum(confidence) / 50 = 0.36
    avg_faithfulness = sum(faithfulness) / 50 = 0.78
    avg_relevance = sum(relevance) / 50 = 0.82
    
    avg_retrieval_time = 0.8s
    avg_generation_time = 2.1s
    avg_total_time = 3.5s
    
    response_quality:
        good: 40
        too_short: 5
        verbose: 3
        unknown: 2
    ↓
Print formatted summary:
    ╔══════════════════════════════════════╗
    ║  RAG Performance Summary             ║
    ║  (Last 50 queries)                   ║
    ╠══════════════════════════════════════╣
    ║  Total Queries: 50                   ║
    ║  Success Rate: 96%                   ║
    ║  Avg Confidence: 36%                 ║
    ║  Avg Faithfulness: 78%               ║
    ║  Avg Relevance: 82%                  ║
    ║  ...                                 ║
    ╚══════════════════════════════════════╝
```

**Options:**
```bash
python view_metrics.py          # All queries
python view_metrics.py --last 10  # Last 10 only
```

**Inputs:** `rag_metrics.jsonl`
**Outputs:** Console summary

---

## 🧪 Test Files

### **10. `tests/test_questions.json` - Ground Truth**

**Purpose:** 50 test questions with expected answers

**Structure:**
```json
[
  {
    "id": 1,
    "category": "factual",
    "difficulty": "easy",
    "question": "What is Input Tax Credit?",
    "expected_keywords": ["credit", "input tax", "set off"],
    "expected_source": "cgst-act.pdf",
    "min_confidence": 0.4
  },
  {
    "id": 2,
    "category": "procedural",
    "difficulty": "medium",
    "question": "How to claim ITC under Section 16?",
    "expected_keywords": ["invoice", "received", "returns", "filed"],
    "expected_source": "cgst-act.pdf",
    "min_confidence": 0.35
  },
  ...
]
```

**Categories:**
- `factual` - "What is X?"
- `procedural` - "How to do X?"
- `analytical` - "Why/How many?"
- `reference` - "Section X says?"

**Used by:** `tests/evaluate_assistant.py`

---

### **11. `tests/evaluate_assistant.py` - Automated Testing**

**Purpose:** Test assistant against ground truth

**Flow:**
```
Run: python tests/evaluate_assistant.py
    ↓
Load test_questions.json:
    50 questions
    ↓
For each question:
    ↓
    [ASK ASSISTANT]
    result = pipeline.answer(question)
    
    [EVALUATE]
    1. Keyword Match:
       expected = ["credit", "input tax"]
       answer_text = result['answer'].lower()
       
       matches = [kw for kw in expected if kw in answer_text]
       keyword_score = len(matches) / len(expected)
    
    2. Source Match:
       expected_source = "cgst-act.pdf"
       actual_sources = result['sources']
       
       source_match = expected_source in str(actual_sources)
    
    3. Confidence Check:
       min_confidence = 0.4
       actual_confidence = result['confidence']
       
       confidence_ok = actual_confidence >= min_confidence
    
    4. Faithfulness/Relevance:
       faithfulness = result['faithfulness']
       relevance = result['relevance']
    
    [DETERMINE PASS/FAIL]
    If (keyword_score >= 0.5 AND 
        source_match AND 
        confidence_ok):
        ✅ PASS
    else:
        ❌ FAIL
    ↓
[AGGREGATE RESULTS]
    Overall:
        Pass Rate: 32/50 = 64%
    
    By Category:
        Factual: 18/20 = 90%
        Procedural: 10/15 = 67%
        Analytical: 4/15 = 27%
    
    By Difficulty:
        Easy: 15/15 = 100%
        Medium: 12/20 = 60%
        Hard: 5/15 = 33%
    
    Avg Metrics:
        Confidence: 36%
        Faithfulness: 78%
        Relevance: 82%
        Response Time: 3.5s
    ↓
[GENERATE REPORT]
    Save to: evaluation_report_TIMESTAMP.json
    Print summary to console
    Identify weakest categories
    Suggest improvements
```

**Options:**
```bash
python tests/evaluate_assistant.py              # All 50 questions
python tests/evaluate_assistant.py --limit 10   # First 10 only
```

**Inputs:** `tests/test_questions.json`
**Outputs:** 
- Console report
- `evaluation_report_YYYYMMDD_HHMMSS.json`

---

### **12. `tests/verify_documents.py` - Coverage Check**

**Purpose:** Can documents answer test questions?

**Flow:**
```
Run: python tests/verify_documents.py
    ↓
Load test_questions.json
    ↓
For each question:
    ↓
    Extract expected keywords
    Extract expected source
    ↓
    Search ChromaDB directly:
        results = collection.query(
            query_texts=[question],
            n_results=5
        )
    ↓
    Check if keywords appear in results:
        If 80% of keywords found:
            ✅ ANSWERABLE
        else:
            ❌ MISSING DATA
    ↓
Aggregate:
    Answerable: 44/50 = 88%
    Missing: 6/50 = 12%
    
    Missing categories:
    - Analytical questions (need calculation)
    - Recent GST updates (not in documents)
    - State-specific rules (only have CGST)
```

**Purpose:** Validate that your documents CAN answer the questions (before blaming RAG/LLM)

**Inputs:** `tests/test_questions.json`, ChromaDB
**Outputs:** Coverage report

---

### **13. `tests/test_search.py` - Retrieval Tests**

**Purpose:** Test ChromaDB retrieval quality

**Flow:**
```
Run: python tests/test_search.py
    ↓
[TEST 1: Collection Exists]
    Connect to ChromaDB
    Check collection "gst_rules"
    Count documents
    → Expected: >0
    ↓
[TEST 2: Metadata Completeness]
    Sample 10 random documents
    Check each has:
        - source
        - page
        - document_type
        - chunk_index
    → Expected: 100% complete
    ↓
[TEST 3: Semantic Search]
    Test queries:
        - "How to claim Input Tax Credit?"
        - "What is reverse charge mechanism?"
        - "Time limit for filing GSTR-1"
    
    For each:
        results = collection.query(query, n_results=5)
        
        Check:
        1. Got 5 results
        2. Similarity > 0.3
        3. Relevant keywords in results
        4. Sources cited
    → Expected: 80% pass
    ↓
[TEST 4: Chunk Quality]
    Sample 20 chunks
    For each:
        1. Length in range (200-1500 chars)
        2. Ends with complete sentence
        3. Has section_id (if applicable)
        4. Text is readable
    → Expected: 90% pass
    ↓
[TEST 5: Interactive Search]
    Prompt user for custom queries
    Show top results
    Display metadata
```

**When to Run:**
- After ingestion
- After changing chunking
- When debugging retrieval issues

**Inputs:** ChromaDB
**Outputs:** Test results + interactive search

---

## 🔄 Complete Query Flow - Step by Step

Let's trace a complete query: **"What is Input Tax Credit?"**

```
┌─────────────────────────────────────────────────────────────┐
│ USER                                                         │
│ $ python main.py "What is Input Tax Credit?"               │
└──────────────────────┬──────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│ main.py                                                      │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ 1. Parse arguments                                       │ │
│ │    question = "What is Input Tax Credit?"               │ │
│ │                                                          │ │
│ │ 2. Initialize RAGPipeline                               │ │
│ │    pipeline = RAGPipeline()                             │ │
│ └─────────────────────────────────────────────────────────┘ │
└──────────────────────┬──────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│ rag/pipeline.py - RAGPipeline.__init__()                    │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ 1. Load config from config.py                           │ │
│ │    LLM_MODEL_NAME = "qwen2.5:7b-instruct"              │ │
│ │    EMBEDDING_MODEL = "bge-large-en-v1.5"               │ │
│ │                                                          │ │
│ │ 2. Connect to ChromaDB                                  │ │
│ │    client = chromadb.PersistentClient("./chroma_db")   │ │
│ │    collection = client.get_collection("gst_rules")     │ │
│ │    → 855 documents loaded                               │ │
│ │                                                          │ │
│ │ 3. Initialize HybridSearcher                            │ │
│ │    hybrid_searcher = HybridSearcher(collection)        │ │
│ │    → BM25 index built                                   │ │
│ │                                                          │ │
│ │ 4. Initialize LLMAssistant                              │ │
│ │    llm_assistant = LLMAssistant("qwen2.5:7b")          │ │
│ │    → Verify Ollama running ✓                            │ │
│ │                                                          │ │
│ │ 5. Initialize RAGMetrics                                │ │
│ │    metrics = RAGMetrics()                               │ │
│ └─────────────────────────────────────────────────────────┘ │
└──────────────────────┬──────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│ rag/pipeline.py - answer()                                   │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ metrics.start_query("What is Input Tax Credit?")       │ │
│ └─────────────────────────────────────────────────────────┘ │
└──────────────────────┬──────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│ rag/hybrid_search.py - hybrid_search()                       │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ [SEMANTIC SEARCH]                                        │ │
│ │ 1. Embed query using bge-large                          │ │
│ │    query_embedding = [0.23, -0.45, 0.67, ...]          │ │
│ │                                                          │ │
│ │ 2. Search ChromaDB                                      │ │
│ │    results = collection.query(embedding, n=10)         │ │
│ │    → Top results:                                        │ │
│ │       [0.70] "Section 16: Input Tax Credit means..."   │ │
│ │       [0.65] "ITC is credit of input tax paid..."      │ │
│ │       [0.58] "Conditions for claiming ITC..."          │ │
│ │       ...                                               │ │
│ │                                                          │ │
│ │ [KEYWORD SEARCH]                                        │ │
│ │ 3. Tokenize query                                       │ │
│ │    tokens = ["input", "tax", "credit"]                 │ │
│ │                                                          │ │
│ │ 4. Run BM25                                             │ │
│ │    bm25_scores = [8.5, 7.2, 6.8, ...]                  │ │
│ │    → Top results:                                        │ │
│ │       [8.5] "Input Tax Credit shall be..."             │ │
│ │       [7.2] "Section 16(2): Conditions for ITC"        │ │
│ │       ...                                               │ │
│ │                                                          │ │
│ │ [COMBINE]                                               │ │
│ │ 5. For each unique chunk:                               │ │
│ │    score = (0.7 × semantic) + (0.3 × bm25)            │ │
│ │    if contains "ITC": score × 1.2                      │ │
│ │                                                          │ │
│ │ 6. Sort and return top 5                                │ │
│ │    → Chunks: [                                          │ │
│ │        {text: "Section 16...", similarity: 0.72},      │ │
│ │        {text: "ITC means...", similarity: 0.68},       │ │
│ │        {text: "Conditions...", similarity: 0.61},      │ │
│ │        {text: "Time limit...", similarity: 0.55},      │ │
│ │        {text: "Documentation...", similarity: 0.48}    │ │
│ │      ]                                                  │ │
│ └─────────────────────────────────────────────────────────┘ │
└──────────────────────┬──────────────────────────────────────┘
                       ↓ (returns chunks)
┌─────────────────────────────────────────────────────────────┐
│ rag/pipeline.py - answer() [continued]                       │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ 7. Filter by min_similarity (0.30)                      │ │
│ │    → All 5 chunks pass                                  │ │
│ │                                                          │ │
│ │ 8. Log retrieval metrics                                │ │
│ │    metrics.log_retrieval(                               │ │
│ │      chunks_retrieved=5,                                │ │
│ │      avg_similarity=0.61,                               │ │
│ │      retrieval_time=0.8s                                │ │
│ │    )                                                     │ │
│ └─────────────────────────────────────────────────────────┘ │
└──────────────────────┬──────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│ llm/assistant.py - generate_with_context()                   │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ 9. Build prompt                                          │ │
│ │    full_prompt = """                                    │ │
│ │    You are a GST compliance assistant.                  │ │
│ │    Answer ONLY from context. Be CONCISE.               │ │
│ │                                                          │ │
│ │    Context:                                             │ │
│ │    [Source 1: cgst-act.pdf, Page 42]                   │ │
│ │    Section 16: Input Tax Credit                        │ │
│ │    ITC means the credit of input tax paid on           │ │
│ │    purchases which can be set off against output       │ │
│ │    tax liability.                                       │ │
│ │                                                          │ │
│ │    [Source 2: cgst-act.pdf, Page 43]                   │ │
│ │    Conditions for claiming ITC under Section 16(2):    │ │
│ │    1. Valid tax invoice                                 │ │
│ │    2. Goods/services received                          │ │
│ │    3. Tax paid to government                           │ │
│ │    4. Returns filed                                     │ │
│ │                                                          │ │
│ │    ...3 more sources...                                 │ │
│ │                                                          │ │
│ │    User Question: What is Input Tax Credit?            │ │
│ │                                                          │ │
│ │    Answer:                                              │ │
│ │    """                                                  │ │
│ └─────────────────────────────────────────────────────────┘ │
└──────────────────────┬──────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│ llm/assistant.py - generate()                                │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ 10. Call Ollama API                                      │ │
│ │     POST http://localhost:11434/api/generate            │ │
│ │     {                                                    │ │
│ │       model: "qwen2.5:7b-instruct",                     │ │
│ │       prompt: [full_prompt],                            │ │
│ │       options: {temperature: 0.5, max_tokens: 256}     │ │
│ │     }                                                    │ │
│ │                                                          │ │
│ │ 11. Wait for LLM response (2-20 seconds)                │ │
│ │     ⏳ Generating...                                     │ │
│ └─────────────────────────────────────────────────────────┘ │
└──────────────────────┬──────────────────────────────────────┘
                       ↓ (2.1 seconds later)
┌─────────────────────────────────────────────────────────────┐
│ Ollama (qwen2.5:7b-instruct)                                 │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ [LLM GENERATES]                                          │ │
│ │                                                          │ │
│ │ "Input Tax Credit (ITC) is the credit of input tax     │ │
│ │  paid on purchases of goods and services, which can    │ │
│ │  be set off against the output tax liability on        │ │
│ │  sales. To claim ITC under Section 16, you must:       │ │
│ │  1. Possess a valid tax invoice                         │ │
│ │  2. Have received the goods or services                 │ │
│ │  3. Ensure tax has been paid to the government         │ │
│ │  4. File your returns on time                          │ │
│ │  [Source: CGST Act, Section 16, Page 42-43]"           │ │
│ └─────────────────────────────────────────────────────────┘ │
└──────────────────────┬──────────────────────────────────────┘
                       ↓ (returns answer)
┌─────────────────────────────────────────────────────────────┐
│ rag/pipeline.py - answer() [continued]                       │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ 12. Log generation metrics                               │ │
│ │     metrics.log_generation(                              │ │
│ │       answer=llm_answer,                                 │ │
│ │       generation_time=2.1s                               │ │
│ │     )                                                     │ │
│ │                                                           │ │
│ │ 13. Calculate faithfulness & relevance                   │ │
│ │     faithfulness = 0.88  (88% grounded in context)      │ │
│ │     relevance = 0.92     (92% addresses question)       │ │
│ │                                                           │ │
│ │ 14. Finalize metrics                                     │ │
│ │     metrics.finalize_query(                              │ │
│ │       total_time=3.5s,                                   │ │
│ │       faithfulness=0.88,                                 │ │
│ │       relevance=0.92                                     │ │
│ │     )                                                     │ │
│ │     → Saved to rag_metrics.jsonl                         │ │
│ │                                                           │ │
│ │ 15. Return result                                        │ │
│ │     return {                                             │ │
│ │       question: "What is Input Tax Credit?",            │ │
│ │       answer: "Input Tax Credit (ITC) is...",           │ │
│ │       sources: ["cgst-act.pdf, Page 42", ...],          │ │
│ │       confidence: 0.61,                                  │ │
│ │       faithfulness: 0.88,                                │ │
│ │       relevance: 0.92,                                   │ │
│ │       chunks_used: 5,                                    │ │
│ │       time_taken: 3.5                                    │ │
│ │     }                                                     │ │
│ └─────────────────────────────────────────────────────────┘ │
└──────────────────────┬──────────────────────────────────────┘
                       ↓ (returns to main.py)
┌─────────────────────────────────────────────────────────────┐
│ main.py - print_result()                                     │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ 16. Format output                                        │ │
│ │     ════════════════════════════════════════════        │ │
│ │     Question: What is Input Tax Credit?                 │ │
│ │     ════════════════════════════════════════════        │ │
│ │                                                          │ │
│ │     Input Tax Credit (ITC) is the credit of input      │ │
│ │     tax paid on purchases of goods and services,       │ │
│ │     which can be set off against the output tax        │ │
│ │     liability on sales. To claim ITC under             │ │
│ │     Section 16, you must:                              │ │
│ │     1. Possess a valid tax invoice                      │ │
│ │     2. Have received the goods or services             │ │
│ │     3. Ensure tax has been paid to the government      │ │
│ │     4. File your returns on time                       │ │
│ │     [Source: CGST Act, Section 16, Page 42-43]         │ │
│ │                                                          │ │
│ │     ════════════════════════════════════════════        │ │
│ │     Sources:                                            │ │
│ │       1. cgst-act.pdf, Page 42 (72% similarity)        │ │
│ │       2. cgst-act.pdf, Page 43 (68% similarity)        │ │
│ │       3. cgst-act.pdf, Page 44 (61% similarity)        │ │
│ │     ════════════════════════════════════════════        │ │
│ │     Confidence: 61%                                     │ │
│ │     Faithfulness: 88%                                   │ │
│ │     Relevance: 92%                                      │ │
│ │     Chunks used: 5                                      │ │
│ │     Time taken: 3.5s                                    │ │
│ │     ════════════════════════════════════════════        │ │
│ └─────────────────────────────────────────────────────────┘ │
└──────────────────────┬──────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│ USER sees answer ✅                                          │
└─────────────────────────────────────────────────────────────┘
```

**Total Flow:**
1. User → `main.py` (parse)
2. `main.py` → `rag/pipeline.py` (initialize)
3. `rag/pipeline.py` → `rag/hybrid_search.py` (retrieve)
4. `rag/hybrid_search.py` → ChromaDB (semantic search)
5. `rag/hybrid_search.py` → BM25 (keyword search)
6. `rag/hybrid_search.py` → `rag/pipeline.py` (return chunks)
7. `rag/pipeline.py` → `llm/assistant.py` (generate)
8. `llm/assistant.py` → Ollama API (LLM call)
9. Ollama → `llm/assistant.py` (answer)
10. `llm/assistant.py` → `rag/pipeline.py` (return)
11. `rag/pipeline.py` → `rag/metrics.py` (log)
12. `rag/pipeline.py` → `main.py` (return result)
13. `main.py` → User (display)

**Time Breakdown:**
- Retrieval: 0.8s (semantic + keyword search)
- Generation: 2.1s (LLM thinking)
- Metrics: 0.1s (logging)
- Formatting: 0.5s (display)
- **Total: 3.5s**

---

## 📝 Key Takeaways

### **File Responsibilities:**

| File | Role | When It Runs |
|------|------|-------------|
| `config.py` | Settings storage | Imported by all |
| `main.py` | User interface | Every query |
| `rag/pipeline.py` | Orchestrator | Every query |
| `rag/hybrid_search.py` | Retrieval | Every query |
| `rag/enhanced_chunker.py` | Document splitting | During ingestion |
| `llm/assistant.py` | LLM interface | Every query |
| `rag/metrics.py` | Performance tracking | Every query |
| `scripts/ingest_pdfs.py` | Data pipeline | One-time / updates |
| `tests/evaluate_assistant.py` | Testing | When validating |
| `view_metrics.py` | Analytics | When analyzing |

### **Data Flow:**
```
PDFs → ingest_pdfs.py → ChromaDB
                            ↓
User Query → pipeline.py → hybrid_search.py → ChromaDB
                            ↓                     ↓
                         chunks             embeddings
                            ↓
                      llm/assistant.py → Ollama
                            ↓
                         answer
                            ↓
                      metrics.py → rag_metrics.jsonl
                            ↓
                          User
```

### **Configuration Flow:**
```
config.py
   ↓
   ├─→ main.py (gets all settings)
   ├─→ rag/pipeline.py (RAG settings)
   ├─→ llm/assistant.py (LLM settings)
   ├─→ rag/hybrid_search.py (retrieval settings)
   └─→ scripts/ingest_pdfs.py (embedding settings)
```

---

**Now you understand every file and how they work together!** 🎯

