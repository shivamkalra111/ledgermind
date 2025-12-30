# LedgerMind Development Guide

This document is your **tactical implementation guide**. It contains detailed tasks, technical decisions, and week-by-week progress tracking.

If you're new to LLMs/RAG/ChromaDB, start with [GETTING_STARTED.md](GETTING_STARTED.md) first.

---

## 📊 Current Status

**Phase:** Phase 1 - MVP Development  
**Current Step:** 1.3 - Data Collection  
**Last Updated:** December 30, 2025

### Progress Dashboard

| Component | Status | Progress | Notes |
|-----------|--------|----------|-------|
| Project Setup | ✅ Complete | 100% | Folders, README created |
| RAG Architecture Design | ✅ Complete | 100% | Documented in README |
| Data Collection (GST Rules) | 🔄 In Progress | 30% | Need 5-10 rules in `data/gst/` |
| ChromaDB Integration | ⏳ To-Do | 0% | See Step 1.4 below |
| LLM Integration (Qwen2.5) | ⏳ To-Do | 0% | See Step 1.6 below |
| Embedding Pipeline | ⏳ To-Do | 0% | See Step 1.5 below |
| Rule Validation Layer | ⏳ To-Do | 0% | See Step 1.8 below |
| MVP Testing | ⏳ To-Do | 0% | See Step 1.9 below |

---

## 🗓️ Phase 1: LLM + RAG Foundation (MVP)

**Goal:** Prove that RAG + LLM can answer ONE GST query accurately with rule grounding.

### Success Criteria
- [ ] One GST query answered correctly with 80%+ confidence
- [ ] Response includes `rules_used` field with correct rule IDs
- [ ] No hallucinations (validated against source documents)
- [ ] Complete code pipeline from query → retrieval → LLM → validation

---

## ✅ Step-by-Step Implementation Tasks

### ✅ Step 1.1: Create Project Structure
**Status:** Complete ✅

```
ledgermind/
├── data/
│   ├── gst/
│   └── accounting/
├── rag/
├── llm/
├── main.py
├── requirements.txt
└── README.md
```

---

### ✅ Step 1.2: Write Project Documentation
**Status:** Complete ✅

- [x] README.md created with architecture
- [x] DEVELOPMENT.md created (this file)
- [x] GETTING_STARTED.md for beginners

---

### 🔄 Step 1.3: Collect and Format GST Rules
**Status:** In Progress 🔄 (30%)  
**Priority:** HIGH  
**Estimated Time:** 2-3 days

#### What You Need:
Collect **5-10 GST rules** relevant to common queries like ITC claims, GST rates, reverse charge mechanism, etc.

#### Where to Find Rules:
1. [CBIC GST Portal](https://www.cbic.gov.in/)
2. [GST Council Notifications](https://gstcouncil.gov.in/)
3. CGST Act, 2017 - Sections on ITC (Chapter V)
4. GST Rates Schedules

#### Format for Each Rule:
Create files in `data/gst/` like `GST_ITC_17_5.md`:

```markdown
# Rule ID: GST_ITC_17_5
## Title: Input Tax Credit - Supplier Compliance Requirement
## Source: CGST Act 2017, Section 16(2)(c)

### Rule Description:
Input Tax Credit (ITC) can be claimed only if the supplier has filed their GSTR-1 return and the tax has been paid to the government.

### Conditions:
1. Supplier must file GSTR-1 declaring the invoice
2. Tax must be deposited to government account
3. Invoice details must appear in recipient's GSTR-2B

### When This Rule Applies:
- Monthly ITC reconciliation
- GSTR-3B filing
- Annual return filing

### Example Scenario:
**Case:** Business received invoice for ₹1,00,000 + ₹18,000 GST from supplier.
**Problem:** ITC of ₹18,000 not appearing in GSTR-2B.
**Reason:** Supplier has not filed GSTR-1 yet.
**Action:** Follow up with supplier or defer ITC claim to next month.

### Related Rules:
- GST_ITC_16_2: Time limit for claiming ITC
- GST_ITC_42: Matching and reversal of ITC
```

#### Task Checklist:
- [ ] Research and identify 10 common GST scenarios
- [ ] Create 5-10 rule documents in `data/gst/`
- [ ] Verify each rule against official CGST Act
- [ ] Include real-world examples in each rule
- [ ] Add metadata (rule_id, category, keywords)

#### Suggested First 5 Rules:
1. `GST_ITC_17_5.md` - ITC supplier filing requirement
2. `GST_RATE_12.md` - 12% GST rate applicability
3. `GST_RCM_9_3.md` - Reverse Charge Mechanism
4. `GST_ITC_TIME_LIMIT.md` - Time limit for ITC claim
5. `GST_EXEMPTION.md` - Exempt supplies

---

### ⏳ Step 1.4: Set Up ChromaDB Locally
**Status:** To-Do ⏳  
**Priority:** HIGH  
**Estimated Time:** 1 day  
**Prerequisites:** Step 1.3 complete

#### What You'll Learn:
- How ChromaDB stores document embeddings
- How to insert and retrieve documents
- How vector similarity search works

#### Tasks:

**A. Install Dependencies**
```bash
pip install chromadb sentence-transformers
```

**B. Create `rag/vector_store.py`**

```python
import chromadb
from chromadb.config import Settings

class VectorStore:
    def __init__(self, persist_directory="./chroma_db"):
        """Initialize ChromaDB client."""
        self.client = chromadb.Client(Settings(
            persist_directory=persist_directory,
            anonymized_telemetry=False
        ))
        self.collection = self.client.get_or_create_collection(
            name="gst_rules",
            metadata={"description": "GST and accounting rules"}
        )
    
    def add_documents(self, documents, metadatas, ids):
        """Add documents to vector store."""
        self.collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        print(f"Added {len(documents)} documents to vector store.")
    
    def query(self, query_text, n_results=3):
        """Query vector store for similar documents."""
        results = self.collection.query(
            query_texts=[query_text],
            n_results=n_results
        )
        return results
    
    def count(self):
        """Return number of documents in collection."""
        return self.collection.count()
```

**C. Test Basic Insertion/Retrieval**

Create `test_chromadb.py`:
```python
from rag.vector_store import VectorStore

# Initialize
vs = VectorStore()

# Test documents
docs = [
    "ITC can be claimed only if supplier filed GSTR-1",
    "GST rate on office supplies is 18%",
    "Reverse charge applies to services from unregistered vendors"
]
metadatas = [
    {"rule_id": "GST_ITC_17_5", "category": "ITC"},
    {"rule_id": "GST_RATE_18", "category": "RATES"},
    {"rule_id": "GST_RCM_9_3", "category": "RCM"}
]
ids = ["rule_1", "rule_2", "rule_3"]

# Add documents
vs.add_documents(docs, metadatas, ids)

# Test query
results = vs.query("Why is my ITC not available?", n_results=2)
print("Query Results:", results)

# Check count
print(f"Total documents: {vs.count()}")
```

Run:
```bash
python test_chromadb.py
```

**Expected Output:**
```
Added 3 documents to vector store.
Query Results: {'ids': [['rule_1', 'rule_2']], 'distances': [[0.234, 0.567]], ...}
Total documents: 3
```

#### Task Checklist:
- [ ] Install ChromaDB and dependencies
- [ ] Create `rag/vector_store.py`
- [ ] Create `rag/__init__.py` (can be empty)
- [ ] Test insertion with sample documents
- [ ] Test retrieval with sample query
- [ ] Verify persistence (close and reopen to check data persists)

**Debugging Tips:**
- If ChromaDB gives errors, try: `pip install chromadb --upgrade`
- Check `chroma_db/` folder is created after first run
- Use `client.reset()` to clear database if needed

---

### ⏳ Step 1.5: Implement Embedding Pipeline
**Status:** To-Do ⏳  
**Priority:** HIGH  
**Estimated Time:** 1-2 days  
**Prerequisites:** Steps 1.3 and 1.4 complete

#### What You'll Learn:
- How text embeddings work (convert text → vectors)
- How to chunk long documents
- How to process and ingest your GST rules

#### Tasks:

**A. Install Embedding Model**
```bash
pip install sentence-transformers
```

**B. Create `rag/embeddings.py`**

```python
from sentence_transformers import SentenceTransformer

class EmbeddingModel:
    def __init__(self, model_name="BAAI/bge-large-en-v1.5"):
        """Initialize embedding model."""
        print(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)
        print("Embedding model loaded!")
    
    def embed_text(self, text):
        """Embed a single text."""
        return self.model.encode(text, convert_to_tensor=False)
    
    def embed_batch(self, texts):
        """Embed multiple texts."""
        return self.model.encode(texts, convert_to_tensor=False, show_progress_bar=True)
```

**C. Create Document Chunker: `rag/chunker.py`**

```python
def chunk_document(text, chunk_size=500, overlap=50):
    """
    Split document into overlapping chunks.
    
    Args:
        text: Full document text
        chunk_size: Target chunk size in characters
        overlap: Overlap between chunks
    
    Returns:
        List of text chunks
    """
    chunks = []
    start = 0
    text_length = len(text)
    
    while start < text_length:
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk.strip())
        start += (chunk_size - overlap)
    
    return chunks

def load_markdown_file(filepath):
    """Load and parse markdown file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    return content
```

**D. Create Ingestion Script: `scripts/ingest_gst_rules.py`**

```python
import os
import glob
from rag.vector_store import VectorStore
from rag.embeddings import EmbeddingModel
from rag.chunker import chunk_document, load_markdown_file

def ingest_gst_rules():
    """Ingest all GST rules from data/gst/ into ChromaDB."""
    
    # Initialize
    vs = VectorStore()
    embedder = EmbeddingModel()
    
    # Find all rule files
    rule_files = glob.glob("data/gst/*.md")
    print(f"Found {len(rule_files)} rule files")
    
    all_chunks = []
    all_metadatas = []
    all_ids = []
    
    # Process each file
    for idx, filepath in enumerate(rule_files):
        print(f"\nProcessing: {filepath}")
        
        # Load content
        content = load_markdown_file(filepath)
        
        # Extract rule_id from filename
        filename = os.path.basename(filepath)
        rule_id = filename.replace('.md', '')
        
        # Chunk document
        chunks = chunk_document(content, chunk_size=500, overlap=50)
        print(f"  Created {len(chunks)} chunks")
        
        # Create metadata for each chunk
        for chunk_idx, chunk in enumerate(chunks):
            all_chunks.append(chunk)
            all_metadatas.append({
                "rule_id": rule_id,
                "source_file": filepath,
                "chunk_index": chunk_idx
            })
            all_ids.append(f"{rule_id}_chunk_{chunk_idx}")
    
    # Embed all chunks (batched for efficiency)
    print(f"\n\nEmbedding {len(all_chunks)} total chunks...")
    embeddings = embedder.embed_batch(all_chunks)
    
    # Add to vector store
    print("Adding to ChromaDB...")
    vs.add_documents(
        documents=all_chunks,
        metadatas=all_metadatas,
        ids=all_ids
    )
    
    print(f"\n✅ Ingestion complete! Total documents in DB: {vs.count()}")

if __name__ == "__main__":
    ingest_gst_rules()
```

**E. Run Ingestion**
```bash
mkdir -p scripts
python scripts/ingest_gst_rules.py
```

#### Task Checklist:
- [ ] Install sentence-transformers
- [ ] Create `rag/embeddings.py`
- [ ] Create `rag/chunker.py`
- [ ] Create `scripts/ingest_gst_rules.py`
- [ ] Run ingestion on your GST rule files
- [ ] Verify all documents are in ChromaDB (check count)
- [ ] Test retrieval with a sample query

**Expected Output:**
```
Found 5 rule files
Processing: data/gst/GST_ITC_17_5.md
  Created 3 chunks
...
Embedding 15 total chunks...
Adding to ChromaDB...
✅ Ingestion complete! Total documents in DB: 15
```

---

### ⏳ Step 1.6: Download and Quantize Qwen2.5-7B-Instruct
**Status:** To-Do ⏳  
**Priority:** HIGH  
**Estimated Time:** 2-3 days (includes download time)  
**Prerequisites:** GPU recommended but CPU works

#### What You'll Learn:
- How to load large language models locally
- What quantization is (4-bit = smaller model size, faster inference)
- How to format prompts for instruction models

#### Tasks:

**A. Install Dependencies**
```bash
pip install transformers torch accelerate bitsandbytes
```

**B. Create `llm/model.py`**

```python
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
import json

class LLMInference:
    def __init__(self, model_name="Qwen/Qwen2.5-7B-Instruct"):
        """Initialize LLM with 4-bit quantization."""
        print(f"Loading model: {model_name}")
        print("This may take 5-10 minutes on first run...")
        
        # 4-bit quantization config
        quantization_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_use_double_quant=True
        )
        
        # Load model
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            quantization_config=quantization_config,
            device_map="auto",
            trust_remote_code=True
        )
        
        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(
            model_name,
            trust_remote_code=True
        )
        
        print("✅ Model loaded successfully!")
    
    def generate(self, prompt, max_new_tokens=512, temperature=0.3):
        """Generate text from prompt."""
        
        # Tokenize
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
        
        # Generate
        outputs = self.model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            do_sample=True,
            top_p=0.9
        )
        
        # Decode
        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Remove prompt from response
        response = response[len(prompt):].strip()
        
        return response
    
    def generate_json(self, prompt, max_new_tokens=512):
        """Generate JSON response."""
        response = self.generate(prompt, max_new_tokens)
        
        # Try to extract JSON
        try:
            # Find JSON in response
            start = response.find('{')
            end = response.rfind('}') + 1
            json_str = response[start:end]
            return json.loads(json_str)
        except:
            return {"error": "Failed to parse JSON", "raw_response": response}
```

**C. Test Model: Create `test_llm.py`**

```python
from llm.model import LLMInference

# Initialize (this will download model on first run)
llm = LLMInference()

# Test basic generation
prompt = """You are a helpful assistant. Answer concisely.

Question: What is GST?
Answer:"""

response = llm.generate(prompt, max_new_tokens=100)
print("Response:", response)

# Test JSON generation
json_prompt = """Given the following information, provide a structured response in JSON format.

Question: Why is my ITC lower this month?
Context: ITC can be claimed only if supplier filed GSTR-1

Provide response in this JSON format:
{
  "finding": "brief explanation",
  "confidence": 0.0-1.0,
  "rules_used": ["rule_id"]
}

Response:"""

json_response = llm.generate_json(json_prompt)
print("\nJSON Response:", json_response)
```

**D. Run Test**
```bash
python test_llm.py
```

**First run:** Will download ~4GB model (takes 10-30 min depending on internet)  
**Subsequent runs:** Loads from cache (~2-3 min)

#### Task Checklist:
- [ ] Install transformers, torch, bitsandbytes
- [ ] Create `llm/__init__.py` (empty file)
- [ ] Create `llm/model.py`
- [ ] Create `test_llm.py`
- [ ] Run test and verify model loads
- [ ] Test basic text generation
- [ ] Test JSON output generation
- [ ] Measure inference speed (should be 1-3 sec per response)

**Hardware Requirements:**
- **Minimum:** 8GB RAM, CPU only (slow but works)
- **Recommended:** 16GB RAM + GPU with 6GB+ VRAM
- **Optimal:** 32GB RAM + GPU with 8GB+ VRAM

**Troubleshooting:**
- Out of memory? Use CPU: Set `device_map="cpu"` in model loading
- Slow generation? Lower `max_new_tokens` to 256
- Model not found? Check internet connection for download

---

### ⏳ Step 1.7: Build RAG Query Pipeline
**Status:** To-Do ⏳  
**Priority:** HIGH  
**Estimated Time:** 1-2 days  
**Prerequisites:** Steps 1.5 and 1.6 complete

#### What You'll Learn:
- How RAG connects retrieval + LLM
- How to format prompts with retrieved context
- How to structure JSON outputs

#### Tasks:

**A. Create Prompt Templates: `llm/prompts.py`**

```python
def build_rag_prompt(user_query, retrieved_chunks, top_k=3):
    """
    Build prompt with user query and retrieved context.
    
    Args:
        user_query: User's question
        retrieved_chunks: List of retrieved document chunks
        top_k: Number of chunks to include
    
    Returns:
        Formatted prompt string
    """
    
    # Format retrieved context
    context = ""
    for i, chunk in enumerate(retrieved_chunks[:top_k]):
        context += f"\n[Rule {i+1}]\n{chunk['text']}\n"
    
    # Build prompt
    prompt = f"""You are an expert Indian GST and accounting assistant. Answer user queries based ONLY on the provided rules. Do not hallucinate or make up information.

Retrieved Rules:{context}

User Query: {user_query}

Provide your response in the following JSON format:
{{
  "intent": "category of the query (e.g., GST_ITC_DIAGNOSTIC)",
  "finding": "clear explanation based on the retrieved rules",
  "confidence": 0.0 to 1.0 (how confident you are based on the rules),
  "rules_used": ["list", "of", "rule_ids"],
  "recommended_action": "actionable next steps for the user"
}}

Response (JSON only):"""
    
    return prompt
```

**B. Create RAG Pipeline: `rag/retriever.py`**

```python
from rag.vector_store import VectorStore
from rag.embeddings import EmbeddingModel
from llm.model import LLMInference
from llm.prompts import build_rag_prompt

class RAGPipeline:
    def __init__(self):
        """Initialize RAG pipeline."""
        print("Initializing RAG Pipeline...")
        self.vector_store = VectorStore()
        self.embedder = EmbeddingModel()
        self.llm = LLMInference()
        print("✅ RAG Pipeline ready!")
    
    def query(self, user_query, top_k=3):
        """
        Process user query through RAG pipeline.
        
        Args:
            user_query: User's natural language question
            top_k: Number of chunks to retrieve
        
        Returns:
            dict: Structured JSON response from LLM
        """
        
        print(f"\n🔍 Query: {user_query}")
        
        # Step 1: Retrieve relevant chunks
        print("  Retrieving relevant rules...")
        results = self.vector_store.query(user_query, n_results=top_k)
        
        # Format retrieved chunks
        retrieved_chunks = []
        for i in range(len(results['ids'][0])):
            retrieved_chunks.append({
                'text': results['documents'][0][i],
                'metadata': results['metadatas'][0][i],
                'distance': results['distances'][0][i]
            })
        
        print(f"  Retrieved {len(retrieved_chunks)} chunks")
        
        # Step 2: Build prompt
        print("  Building prompt...")
        prompt = build_rag_prompt(user_query, retrieved_chunks, top_k)
        
        # Step 3: Generate LLM response
        print("  Generating LLM response...")
        response = self.llm.generate_json(prompt, max_new_tokens=512)
        
        # Step 4: Add retrieval metadata
        response['retrieval_metadata'] = {
            'chunks_retrieved': len(retrieved_chunks),
            'rule_ids': [chunk['metadata'].get('rule_id') for chunk in retrieved_chunks]
        }
        
        print("✅ Response generated!")
        return response
```

**C. Create Main Entry Point: Update `main.py`**

```python
from rag.retriever import RAGPipeline
import json

def main():
    """LedgerMind MVP - Phase 1"""
    print("=" * 60)
    print("LedgerMind MVP - LLM-Powered Accounting Assistant")
    print("=" * 60)
    
    # Initialize pipeline
    pipeline = RAGPipeline()
    
    # Test queries
    test_queries = [
        "Why is my ITC lower this month?",
        "Can I claim ITC on office supplies?",
        "What is the GST rate for restaurant services?"
    ]
    
    for query in test_queries:
        response = pipeline.query(query, top_k=3)
        
        print("\n" + "=" * 60)
        print(f"Query: {query}")
        print("=" * 60)
        print(json.dumps(response, indent=2))
        print()

if __name__ == "__main__":
    main()
```

**D. Run Complete Pipeline**
```bash
python main.py
```

#### Task Checklist:
- [ ] Create `llm/prompts.py`
- [ ] Create `rag/retriever.py`
- [ ] Update `main.py`
- [ ] Test with sample queries
- [ ] Verify retrieved chunks are relevant
- [ ] Verify LLM output is in correct JSON format
- [ ] Measure end-to-end latency

**Expected Output:**
```
==========================================================
Query: Why is my ITC lower this month?
==========================================================
{
  "intent": "GST_ITC_DIAGNOSTIC",
  "finding": "ITC may be lower because supplier has not filed GSTR-1...",
  "confidence": 0.85,
  "rules_used": ["GST_ITC_17_5"],
  "recommended_action": "Follow up with supplier...",
  "retrieval_metadata": {
    "chunks_retrieved": 3,
    "rule_ids": ["GST_ITC_17_5", "GST_ITC_16_2"]
  }
}
```

---

### ⏳ Step 1.8: Implement Rule Validation Layer
**Status:** To-Do ⏳  
**Priority:** MEDIUM  
**Estimated Time:** 1 day  
**Prerequisites:** Step 1.7 complete

#### What You'll Learn:
- How to prevent hallucinations
- How to validate LLM outputs against source documents

#### Tasks:

**A. Create `llm/validator.py`**

```python
import re

class RuleValidator:
    """Validate LLM outputs against retrieved rules."""
    
    def validate_response(self, llm_response, retrieved_chunks):
        """
        Validate LLM response against retrieved context.
        
        Returns:
            dict: Validation results with flags and confidence adjustments
        """
        validation = {
            "is_valid": True,
            "warnings": [],
            "adjusted_confidence": llm_response.get("confidence", 0.0)
        }
        
        # Check 1: Are cited rules actually in retrieved chunks?
        cited_rules = llm_response.get("rules_used", [])
        retrieved_rule_ids = [chunk['metadata'].get('rule_id') for chunk in retrieved_chunks]
        
        for rule in cited_rules:
            if rule not in retrieved_rule_ids:
                validation["warnings"].append(f"Cited rule {rule} not in retrieved context")
                validation["adjusted_confidence"] *= 0.8  # Penalize confidence
        
        # Check 2: Is finding grounded in retrieved text?
        finding = llm_response.get("finding", "").lower()
        retrieved_text = " ".join([chunk['text'].lower() for chunk in retrieved_chunks])
        
        # Simple keyword overlap check
        finding_keywords = set(re.findall(r'\w+', finding))
        context_keywords = set(re.findall(r'\w+', retrieved_text))
        overlap = len(finding_keywords & context_keywords) / max(len(finding_keywords), 1)
        
        if overlap < 0.3:  # Less than 30% overlap
            validation["warnings"].append("Finding may not be well-grounded in context")
            validation["adjusted_confidence"] *= 0.9
        
        # Check 3: Required fields present?
        required_fields = ["intent", "finding", "confidence", "rules_used", "recommended_action"]
        for field in required_fields:
            if field not in llm_response:
                validation["warnings"].append(f"Missing required field: {field}")
                validation["is_valid"] = False
        
        return validation

def validate_and_adjust(llm_response, retrieved_chunks):
    """
    Convenience function to validate and adjust LLM response.
    
    Returns:
        dict: LLM response with validation metadata
    """
    validator = RuleValidator()
    validation = validator.validate_response(llm_response, retrieved_chunks)
    
    # Add validation to response
    llm_response["validation"] = validation
    llm_response["confidence"] = validation["adjusted_confidence"]
    
    return llm_response
```

**B. Update `rag/retriever.py` to Use Validation**

Add this to the `query` method in `RAGPipeline` class:

```python
# After Step 3 (Generate LLM response), add:

# Step 4: Validate response
from llm.validator import validate_and_adjust
response = validate_and_adjust(response, retrieved_chunks)
```

**C. Test Validation**

Run `python main.py` and check for `validation` field in output.

#### Task Checklist:
- [ ] Create `llm/validator.py`
- [ ] Update `rag/retriever.py` to use validation
- [ ] Test with queries to see validation warnings
- [ ] Verify confidence adjustments work
- [ ] Test with intentionally bad queries

---

### ⏳ Step 1.9: Test with Sample Queries
**Status:** To-Do ⏳  
**Priority:** HIGH  
**Estimated Time:** 1-2 days  
**Prerequisites:** Steps 1.1-1.8 complete

#### What You'll Learn:
- How to evaluate LLM accuracy
- How to measure system performance

#### Tasks:

**A. Create Test Suite: `tests/test_queries.py`**

```python
test_cases = [
    {
        "query": "Why is my ITC lower this month?",
        "expected_intent": "GST_ITC_DIAGNOSTIC",
        "expected_rules": ["GST_ITC_17_5"],
        "expected_keywords": ["supplier", "GSTR-1", "filed"]
    },
    {
        "query": "Can I claim ITC on office supplies?",
        "expected_intent": "GST_ITC_ELIGIBILITY",
        "expected_rules": ["GST_ITC_*"],
        "expected_keywords": ["claim", "ITC", "eligible"]
    },
    # Add more test cases
]
```

**B. Create Evaluation Script: `scripts/evaluate_mvp.py`**

```python
import json
import time
from rag.retriever import RAGPipeline
from tests.test_queries import test_cases

def evaluate():
    """Evaluate MVP performance."""
    pipeline = RAGPipeline()
    
    results = []
    total_time = 0
    
    for i, test in enumerate(test_cases):
        print(f"\n{'='*60}")
        print(f"Test {i+1}/{len(test_cases)}: {test['query']}")
        print('='*60)
        
        start = time.time()
        response = pipeline.query(test['query'])
        elapsed = time.time() - start
        total_time += elapsed
        
        # Evaluate
        eval_result = {
            "query": test['query'],
            "response": response,
            "elapsed_time": elapsed,
            "intent_match": response.get("intent") == test.get("expected_intent"),
            "confidence": response.get("confidence", 0.0),
            "validation_passed": response.get("validation", {}).get("is_valid", False)
        }
        
        results.append(eval_result)
        
        print(f"Response: {json.dumps(response, indent=2)}")
        print(f"Time: {elapsed:.2f}s")
        print(f"Confidence: {response.get('confidence', 0):.2f}")
    
    # Summary
    print(f"\n{'='*60}")
    print("EVALUATION SUMMARY")
    print('='*60)
    print(f"Total tests: {len(test_cases)}")
    print(f"Average confidence: {sum(r['confidence'] for r in results) / len(results):.2f}")
    print(f"Average time: {total_time / len(test_cases):.2f}s")
    print(f"Validation passed: {sum(r['validation_passed'] for r in results)}/{len(results)}")
    
    # Save results
    with open("evaluation_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print("\n✅ Results saved to evaluation_results.json")

if __name__ == "__main__":
    evaluate()
```

**C. Run Evaluation**
```bash
python scripts/evaluate_mvp.py
```

#### Task Checklist:
- [ ] Create `tests/` folder
- [ ] Create `tests/test_queries.py` with 5-10 test cases
- [ ] Create `scripts/evaluate_mvp.py`
- [ ] Run evaluation
- [ ] Analyze results (accuracy, latency, confidence)
- [ ] Document learnings

**Success Criteria Check:**
- [ ] At least 80% of queries answered correctly
- [ ] Average confidence > 0.75
- [ ] No hallucinations (rules_used match retrieved context)
- [ ] Response time < 5 seconds per query

---

### ⏳ Step 1.10: Document Results and Learnings
**Status:** To-Do ⏳  
**Priority:** MEDIUM  
**Estimated Time:** Half day

#### Tasks:
- [ ] Create `RESULTS.md` documenting MVP performance
- [ ] Screenshot/save sample outputs
- [ ] Document any issues faced and solutions
- [ ] Create demo video (optional)
- [ ] Update README with MVP status
- [ ] Commit all code to Git

---

## 🗓️ Phase 2: Scale Knowledge Base

**Status:** Future Phase  
**Start Date:** TBD (after Phase 1 complete)

### Goals:
- Expand to 50+ rules (GST, TDS, accounting)
- Add company-specific summary templates
- Implement confidence calibration
- Build comprehensive evaluation harness

### Key Tasks:
- [ ] Expand rule coverage to 50+ documents
- [ ] Add accounting rules (ledger validation, transaction classification)
- [ ] Implement multi-document retrieval with re-ranking
- [ ] Fine-tune confidence scoring
- [ ] Create test dataset with 100+ queries
- [ ] Achieve 85%+ accuracy on test set

---

## 🗓️ Phase 3: Accounting Software Integration

**Status:** Future Phase  
**Start Date:** TBD

### Goals:
- Build Tally-like accounting features
- Web interface (FastAPI + React/Streamlit)
- Real-time compliance alerts
- Natural language report generation

### Key Tasks:
- [ ] Design data models (Ledger, Voucher, Transaction, Party)
- [ ] Build data ingestion (CSV, Excel, Tally XML)
- [ ] Create voucher entry interface
- [ ] Build trial balance and financial reports
- [ ] Web UI with authentication
- [ ] Audit logs for all AI insights

---

## 🗓️ Phase 4: Production & Scale

**Status:** Future Phase

### Goals:
- Production deployment
- Multi-language support
- Banking integration
- SaaS features

---

## 📝 Development Notes

### Current Blockers:
- None

### Decisions Made:
1. **Qwen2.5-7B** chosen over Llama/Mistral for instruction-following quality
2. **ChromaDB** over Pinecone/Weaviate for local-first, cost-free approach
3. **4-bit quantization** to enable CPU inference
4. **Markdown format** for rules (human-readable, easy to version control)

### Future Considerations:
- Fine-tuning Qwen on GST corpus (Phase 2)
- Adding Hindi/Gujarati support for Indian SMEs (Phase 4)
- Switching to pgvector if scale requires Postgres (Phase 4)

---

## 🔗 Useful Resources

### ChromaDB:
- [Official Docs](https://docs.trychroma.com/)
- [Getting Started Tutorial](https://docs.trychroma.com/getting-started)

### Qwen:
- [Model Card](https://huggingface.co/Qwen/Qwen2.5-7B-Instruct)
- [Documentation](https://qwen.readthedocs.io/)

### RAG:
- [LangChain RAG Guide](https://python.langchain.com/docs/use_cases/question_answering/)
- [RAG Best Practices](https://www.pinecone.io/learn/retrieval-augmented-generation/)

### GST Resources:
- [CBIC GST Portal](https://www.cbic.gov.in/)
- [GST Council](https://gstcouncil.gov.in/)
- [CGST Act 2017 PDF](https://www.cbic.gov.in/resources//htdocs-cbec/gst/cgst-act.pdf)

---

**Last Updated:** December 30, 2025  
**Maintainer:** Shivam

