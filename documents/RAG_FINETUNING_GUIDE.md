# RAG Fine-Tuning Guide: Complete Overview

## Overview

This guide explains all the methods to improve RAG performance, from simple to advanced, with specific recommendations for your GST compliance system.

---

## 🎯 RAG Fine-Tuning Methods (Ordered by Complexity)

### **Level 1: Prompt Engineering** (Easiest, No Training Required)
### **Level 2: Retrieval Optimization** (Medium, Configuration Only)
### **Level 3: Chunking & Embedding** (Medium, Data Processing)
### **Level 4: Model Fine-Tuning** (Hard, Requires Training Data)
### **Level 5: Advanced Architectures** (Expert, Research-Level)

---

## Level 1: Prompt Engineering (⭐ START HERE)

**What:** Modify how you ask the LLM questions and provide context.
**Effort:** Low (minutes to hours)
**Cost:** Free
**Impact:** High (20-50% improvement possible)

### Methods:

#### 1.1 System Prompt Tuning
**Current (config.py):**
```python
GST_SYSTEM_PROMPT = """You are a GST compliance assistant.
Provide accurate answers based on official GST rules..."""
```

**Improvements:**
```python
# A. Add specific behaviors
GST_SYSTEM_PROMPT = """You are a GST compliance assistant for India.

RESPONSE RULES:
1. Answer ONLY from the provided context
2. If unsure, say "The provided documents don't clearly state..."
3. For numerical questions (dates, amounts), cite exact text
4. For procedural questions, provide step-by-step answers
5. Always cite source document and page number

RESPONSE FORMAT:
- Direct answer first
- Supporting details second
- Source citations last

TONE: Professional, precise, factual
"""

# B. Add few-shot examples (show the LLM how to answer)
GST_SYSTEM_PROMPT = """You are a GST compliance assistant.

EXAMPLE 1:
Question: What is the due date for GSTR-1?
Answer: GSTR-1 must be filed by the 11th of the month following the tax period [Source: CGST Rules 2017, Rule 59, Page 42].

EXAMPLE 2:
Question: How many types of GST are there?
Answer: There are four types of GST in India: CGST, SGST, IGST, and UTGST [Source: GST Act 2017, Section 2, Page 5].

Now answer user questions in this format.
"""
```

**How to Test:**
```python
from config import GST_SYSTEM_PROMPT

# Edit config.py, then:
from rag.pipeline import RAGPipeline
pipeline = RAGPipeline()
result = pipeline.answer("Your question")
```

---

#### 1.2 Context Formatting
**Current (llm/assistant.py - line 138):**
```python
context_str = "\n\n".join([
    f"[Source {i+1}: {chunk.get('source', 'Unknown')}, Page {chunk.get('page', 'N/A')}]\n{chunk['text']}"
    for i, chunk in enumerate(context_chunks)
])
```

**Improvements:**
```python
# A. Add relevance scores
context_str = "\n\n".join([
    f"[Source {i+1}: {chunk.get('source')}, Page {chunk.get('page')}, Relevance: {chunk.get('similarity', 0):.0%}]\n{chunk['text']}"
    for i, chunk in enumerate(context_chunks)
])

# B. Hierarchical context (most relevant first)
sorted_chunks = sorted(context_chunks, key=lambda x: x['similarity'], reverse=True)
context_str = "MOST RELEVANT:\n" + sorted_chunks[0]['text']
context_str += "\n\nSUPPORTING INFORMATION:\n"
context_str += "\n".join([c['text'] for c in sorted_chunks[1:]])

# C. Add metadata hints
context_str = f"Found {len(context_chunks)} relevant sections:\n\n"
for i, chunk in enumerate(context_chunks):
    section_type = chunk['metadata'].get('document_type', 'Unknown')
    context_str += f"[{section_type}] {chunk['text']}\n\n"
```

---

#### 1.3 Query Reformulation
**Problem:** User asks "ITC eligibility?" but documents say "Input Tax Credit conditions"

**Solution: Expand queries before retrieval**
```python
# Add to rag/pipeline.py

def _expand_query(self, question: str) -> List[str]:
    """Generate multiple query variations for better retrieval."""
    
    # Common GST abbreviations
    abbreviations = {
        'ITC': 'Input Tax Credit',
        'GSTR': 'GST Return',
        'GST': 'Goods and Services Tax',
        'CGST': 'Central Goods and Services Tax',
        'SGST': 'State Goods and Services Tax',
        'IGST': 'Integrated Goods and Services Tax'
    }
    
    queries = [question]  # Original
    
    # Expand abbreviations
    expanded = question
    for abbr, full in abbreviations.items():
        if abbr in question:
            expanded = expanded.replace(abbr, full)
            queries.append(expanded)
    
    # Add question type variations
    if question.startswith("What is"):
        queries.append(question.replace("What is", "Define"))
    elif question.startswith("How to"):
        queries.append(question.replace("How to", "Process for"))
    
    return queries

# Then in answer():
def answer(self, question, ...):
    queries = self._expand_query(question)
    
    # Retrieve for each query, deduplicate results
    all_results = []
    for query in queries:
        results = self.collection.query(query_texts=[query], n_results=3)
        all_results.extend(results['documents'][0])
    
    # Deduplicate and rank
    unique_docs = list(set(all_results))
    # ... continue with ranking
```

**Impact:** 15-30% better retrieval recall

---

## Level 2: Retrieval Optimization (⭐ RECOMMENDED)

**What:** Improve how you find relevant chunks
**Effort:** Medium (hours to days)
**Cost:** Free
**Impact:** High (30-60% improvement)

### Methods:

#### 2.1 Tuning Retrieval Parameters

**Current (config.py):**
```python
RAG_NUM_RESULTS = 5
RAG_MIN_SIMILARITY = 0.25
```

**Optimization Process:**
```python
# Test different combinations
test_configs = [
    {'n_results': 3, 'min_similarity': 0.3},
    {'n_results': 5, 'min_similarity': 0.25},
    {'n_results': 7, 'min_similarity': 0.2},
    {'n_results': 10, 'min_similarity': 0.15}
]

from rag.metrics import RAGEvaluator
evaluator = RAGEvaluator()

# Add test questions
evaluator.add_test_case(
    question="How to claim ITC?",
    expected_keywords=["invoice", "goods", "services"],
    min_confidence=0.4
)

# Test each config
for config in test_configs:
    pipeline = RAGPipeline()
    result = evaluator.evaluate(pipeline)
    print(f"Config {config}: Accuracy = {result['avg_keyword_coverage']}")
```

**Guidelines:**
- **More results** = More context but slower
- **Lower threshold** = More recall but lower precision
- **For factual Q&A:** Higher threshold (0.3-0.4)
- **For exploratory:** Lower threshold (0.15-0.25)

---

#### 2.2 Hybrid Search (Semantic + Keyword)

**Problem:** Semantic search misses exact matches like "Section 17(5)"

**Solution: Combine semantic and keyword search**
```python
def hybrid_search(self, question, n_results=5):
    """Combine semantic and keyword-based retrieval."""
    
    # 1. Semantic search (ChromaDB)
    semantic_results = self.collection.query(
        query_texts=[question],
        n_results=n_results
    )
    
    # 2. Keyword search (BM25 or simple matching)
    # Extract important keywords from question
    keywords = self._extract_keywords(question)
    
    # Search for exact matches in metadata
    keyword_results = self.collection.get(
        where={
            "$or": [
                {"text": {"$contains": kw}} for kw in keywords
            ]
        },
        limit=n_results
    )
    
    # 3. Merge and rerank
    # Semantic results get weight 0.7, keyword results 0.3
    combined_chunks = self._merge_and_rerank(
        semantic_results, 
        keyword_results,
        weights=[0.7, 0.3]
    )
    
    return combined_chunks

def _extract_keywords(self, question):
    """Extract important keywords (sections, numbers, etc.)."""
    import re
    
    # Find section references
    sections = re.findall(r'Section \d+\(\d+\)', question)
    
    # Find numbers
    numbers = re.findall(r'\d+', question)
    
    # Important legal terms
    legal_terms = ['shall', 'must', 'required', 'eligible', 'taxable']
    terms = [w for w in question.split() if w.lower() in legal_terms]
    
    return sections + terms
```

**Impact:** 25-40% improvement for specific queries (sections, dates, amounts)

---

#### 2.3 Re-ranking Retrieved Chunks

**Problem:** Top retrieved chunks may not be the best for LLM generation

**Solution: Add a second-stage ranker**
```python
def rerank_chunks(self, question, chunks):
    """Re-rank chunks based on additional criteria."""
    
    for chunk in chunks:
        score = 0.0
        
        # 1. Original similarity (60% weight)
        score += chunk['similarity'] * 0.6
        
        # 2. Question word overlap (20% weight)
        q_words = set(question.lower().split())
        c_words = set(chunk['text'].lower().split())
        overlap = len(q_words & c_words) / len(q_words)
        score += overlap * 0.2
        
        # 3. Document type relevance (10% weight)
        # Prefer certain document types
        doc_type = chunk['metadata'].get('document_type', '')
        if 'rules' in doc_type.lower():
            score += 0.1
        
        # 4. Chunk position (10% weight)
        # Sections often appear early
        chunk_index = chunk['metadata'].get('chunk_index', 999)
        if chunk_index < 10:
            score += 0.1
        
        chunk['rerank_score'] = score
    
    # Sort by new score
    return sorted(chunks, key=lambda x: x['rerank_score'], reverse=True)
```

---

## Level 3: Chunking & Embedding Optimization

**What:** Improve how documents are split and embedded
**Effort:** Medium-High (days)
**Cost:** Free to low
**Impact:** Medium-High (20-40%)

### Methods:

#### 3.1 Advanced Chunking Strategies

**Current:** Semantic chunking by document structure

**Improvements:**

**A. Sliding Window with Overlap**
```python
def chunk_with_overlap(text, chunk_size=512, overlap=128):
    """
    Create overlapping chunks to preserve context at boundaries.
    
    Example:
    Chunk 1: [0:512]
    Chunk 2: [384:896]  (overlaps 128 tokens with chunk 1)
    Chunk 3: [768:1280]
    """
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        
        # Add metadata about overlap
        chunks.append({
            'text': chunk,
            'char_start': start,
            'char_end': end,
            'overlaps_previous': start > 0
        })
        
        start += (chunk_size - overlap)
    
    return chunks
```

**B. Sentence-Aware Chunking**
```python
def sentence_aware_chunking(text, target_size=512):
    """Don't break sentences mid-way."""
    import nltk
    nltk.download('punkt', quiet=True)
    
    sentences = nltk.sent_tokenize(text)
    chunks = []
    current_chunk = []
    current_size = 0
    
    for sentence in sentences:
        sent_len = len(sentence)
        
        if current_size + sent_len > target_size and current_chunk:
            # Save current chunk
            chunks.append(' '.join(current_chunk))
            current_chunk = [sentence]
            current_size = sent_len
        else:
            current_chunk.append(sentence)
            current_size += sent_len
    
    if current_chunk:
        chunks.append(' '.join(current_chunk))
    
    return chunks
```

**C. Context-Enriched Chunking**
```python
def context_enriched_chunking(text, section_title, document_name):
    """Prepend context to each chunk."""
    base_chunks = semantic_chunking(text)
    
    enriched_chunks = []
    for chunk in base_chunks:
        # Add document context
        enriched_text = f"Document: {document_name}\n"
        enriched_text += f"Section: {section_title}\n\n"
        enriched_text += chunk['text']
        
        enriched_chunks.append({
            'text': enriched_text,
            'original_text': chunk['text'],  # Keep for display
            'metadata': chunk['metadata']
        })
    
    return enriched_chunks
```

---

#### 3.2 Embedding Model Selection

**Current:** `bge-large-en-v1.5` (1024-dim)

**When to Change:**

| Use Case | Recommended Model | Dimensions | Notes |
|----------|-------------------|------------|-------|
| **Legal/Financial (Your case)** | `bge-large-en-v1.5` | 1024 | ✅ Current choice is optimal |
| **Multilingual GST** | `paraphrase-multilingual-mpnet-base-v2` | 768 | For Hindi/Tamil/etc. |
| **Very large corpus (>1M docs)** | `bge-small-en-v1.5` | 384 | Faster, less accurate |
| **Maximum accuracy** | `instructor-xl` | 768 | Can customize instructions |

**Specialized Embedding (Advanced):**
```python
# Domain-specific instructions for instructor models
from InstructorEmbedding import INSTRUCTOR

model = INSTRUCTOR('hkunlp/instructor-xl')

# Customize embedding for legal text
instruction = "Represent the legal document for retrieval:"
embeddings = model.encode([[instruction, doc_text]])
```

---

## Level 4: Model Fine-Tuning (⚠️ ADVANCED)

**What:** Train the LLM or embedding model on your specific data
**Effort:** High (weeks)
**Cost:** Medium to High ($50-$500+)
**Impact:** High (40-70%) but risky

### Methods:

#### 4.1 LLM Fine-Tuning (Generation)

**When to do this:**
- LLM consistently gives wrong answer format
- Need specific legal language style
- Have 500+ question-answer pairs

**How:**
```python
# 1. Collect training data
training_data = [
    {
        "context": "Input Tax Credit means...",
        "question": "What is ITC?",
        "answer": "Input Tax Credit (ITC) is..."
    },
    # ... 500+ examples
]

# 2. Format for fine-tuning
from datasets import Dataset

dataset = Dataset.from_list([
    {
        "prompt": f"Context: {ex['context']}\nQuestion: {ex['question']}\n\nAnswer:",
        "completion": ex['answer']
    }
    for ex in training_data
])

# 3. Fine-tune (using Hugging Face)
from transformers import AutoModelForCausalLM, TrainingArguments, Trainer

model = AutoModelForCausalLM.from_pretrained("Qwen/Qwen2.5-7B-Instruct")

training_args = TrainingArguments(
    output_dir="./gst-qwen-finetuned",
    num_train_epochs=3,
    per_device_train_batch_size=2,
    learning_rate=2e-5,
    # ... more args
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=dataset
)

trainer.train()
model.save_pretrained("./gst-qwen-finetuned")
```

**Pros:**
- Learns GST-specific language
- Consistent answer format
- Can learn implicit patterns

**Cons:**
- Needs 500+ high-quality examples
- Expensive (GPU hours)
- Risk of overfitting
- Maintenance burden (retrain for updates)

**Verdict for your case:** ❌ **NOT RECOMMENDED YET**
- Your prompt engineering can achieve 80% of this benefit
- Legal rules change frequently (GST amendments)
- Hard to maintain fine-tuned model

---

#### 4.2 Embedding Model Fine-Tuning (Retrieval)

**When to do this:**
- Retrieval consistently misses relevant docs
- Domain-specific terminology (GST jargon)
- Have 1000+ query-document pairs

**How:**
```python
# 1. Create contrastive pairs
training_pairs = [
    {
        "query": "How to claim ITC?",
        "positive": "Section 16(1) states that ITC can be claimed...",
        "negative": "Export procedures under GST..."
    },
    # ... 1000+ examples
]

# 2. Fine-tune with sentence-transformers
from sentence_transformers import SentenceTransformer, InputExample, losses
from torch.utils.data import DataLoader

model = SentenceTransformer('BAAI/bge-large-en-v1.5')

train_examples = [
    InputExample(
        texts=[pair['query'], pair['positive']],
        label=1.0
    )
    for pair in training_pairs
]

train_dataloader = DataLoader(train_examples, shuffle=True, batch_size=16)

train_loss = losses.MultipleNegativesRankingLoss(model)

model.fit(
    train_objectives=[(train_dataloader, train_loss)],
    epochs=3,
    warmup_steps=100
)

model.save('gst-bge-finetuned')
```

**Pros:**
- Better at GST-specific queries
- Understands domain abbreviations
- Persistent improvement

**Cons:**
- Needs quality training pairs
- GPU required
- Need to rebuild ChromaDB with new embeddings

**Verdict for your case:** 🤔 **MAYBE LATER**
- Wait until you collect 6+ months of real user queries
- Use metrics to identify retrieval failures
- Then consider if benefit > cost

---

## Level 5: Advanced Architectures (🔬 RESEARCH)

**What:** Fundamental changes to RAG pipeline
**Effort:** Very High (months)
**Cost:** High
**Impact:** Varies (high if successful)

### Methods:

#### 5.1 Multi-Hop Reasoning
For questions requiring multiple documents:
```
Q: "Compare ITC rules under old vs new GST amendment"
→ Retrieve old GST doc
→ Generate sub-question: "What changed in amendment?"
→ Retrieve amendment doc
→ Synthesize comparison
```

#### 5.2 Retrieval with Feedback
LLM requests more context if unsure:
```
Q: "ITC time limit"
→ Retrieve chunks
→ LLM: "Context unclear, need Section 16 specifically"
→ Retrieve again with refined query
→ Generate answer
```

#### 5.3 Graph RAG
Model relationships between rules:
```
GST Act → references → CGST Rules → implements → Section 16
                                                      ↓
                                                   Time limits
```

**Verdict:** ❌ **NOT NEEDED for your use case**

---

## 🎯 RECOMMENDATIONS FOR YOUR GST SYSTEM

### Phase 1: Start Here (This Week)

**Priority 1: Prompt Engineering**
1. ✅ **Improve system prompt** (1 hour)
   - Add response format rules
   - Add citation requirements
   - Add few-shot examples

2. ✅ **Add query expansion** (2 hours)
   - GST abbreviation expansion
   - Synonym handling
   
3. ✅ **Tune context formatting** (1 hour)
   - Sort by relevance
   - Add metadata hints

**Expected improvement:** 30-40%
**Cost:** Free
**Time:** 4-6 hours

---

### Phase 2: Optimize Retrieval (Next Week)

**Priority 2: Retrieval Tuning**
1. ✅ **Test different retrieval parameters** (3 hours)
   - Run evaluation suite
   - Find optimal `n_results` and `min_similarity`

2. ✅ **Implement hybrid search** (4 hours)
   - Add keyword matching for sections
   - Combine with semantic search

3. ✅ **Add reranking** (2 hours)
   - Score based on document type
   - Prefer rule-heavy sections

**Expected improvement:** Additional 20-30%
**Cost:** Free
**Time:** 1 week

---

### Phase 3: Advanced (Month 2-3)

**Priority 3: Chunking Improvements**
1. ✅ **Sliding window overlap** (1 day)
2. ✅ **Context-enriched chunks** (1 day)

**Expected improvement:** Additional 10-15%
**Cost:** Free
**Time:** 1 week

---

### What NOT to Do (Yet)

❌ **Don't fine-tune models** until:
- You have 6+ months of real usage data
- Metrics show clear failure patterns
- Prompt engineering is maxed out

❌ **Don't change embedding model** because:
- `bge-large-en-v1.5` is already optimal for legal text
- Switching requires re-ingesting all data
- Marginal benefit

❌ **Don't implement multi-hop reasoning** because:
- Most GST queries are single-doc
- Adds complexity and latency
- Diminishing returns

---

## 📊 How to Measure Improvements

**Use the metrics system:**
```python
from rag.pipeline import RAGPipeline

# Before changes
pipeline_old = RAGPipeline()
result_old = pipeline_old.answer("Your test question")

# After changes (e.g., new prompt)
# Edit config.py
pipeline_new = RAGPipeline()
result_new = pipeline_new.answer("Your test question")

# Compare
print(f"Confidence: {result_old['confidence']:.1%} → {result_new['confidence']:.1%}")
print(f"Faithfulness: {result_old['faithfulness']:.1%} → {result_new['faithfulness']:.1%}")
print(f"Time: {result_old['time_taken']:.2f}s → {result_new['time_taken']:.2f}s")
```

**Track over time:**
```bash
python main.py "Test question 1"
python main.py "Test question 2"
# ... more queries

# View aggregate metrics
python -c "from rag.metrics import RAGMetrics; m = RAGMetrics(); m.print_summary()"
```

---

## Summary Table

| Method | Effort | Cost | Impact | For You |
|--------|--------|------|--------|---------|
| **Prompt Engineering** | Low | Free | High (30-50%) | ✅ START HERE |
| **Retrieval Tuning** | Medium | Free | High (20-40%) | ✅ NEXT PRIORITY |
| **Hybrid Search** | Medium | Free | Medium (15-30%) | ✅ RECOMMENDED |
| **Chunking Optimization** | Medium | Free | Medium (10-20%) | 🤔 OPTIONAL |
| **Embedding Change** | Low | Free | Low (5-10%) | ❌ NOT NEEDED |
| **LLM Fine-tuning** | Very High | High | High (40-70%) | ❌ WAIT 6+ MONTHS |
| **Embedding Fine-tuning** | High | Medium | Medium (20-30%) | ❌ WAIT 6+ MONTHS |
| **Advanced Architectures** | Very High | High | Varies | ❌ OVERKILL |

---

**Next Steps:**
1. Read this guide
2. Implement Phase 1 (prompt engineering)
3. Measure improvement with metrics
4. If needed, proceed to Phase 2

Let me know when you're ready to start implementing!

