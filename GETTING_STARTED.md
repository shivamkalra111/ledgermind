# Getting Started with LedgerMind: A Complete Beginner's Guide

**Welcome!** This guide is for you if you've never worked with LLMs, RAG, or ChromaDB before. Don't worry — we'll explain everything step-by-step.

---

## 🎓 What You'll Learn

By the end of this guide, you'll understand:
1. What LLMs, RAG, and embeddings are
2. How ChromaDB stores and retrieves information
3. How to build your first RAG-powered application
4. How all these pieces work together in LedgerMind

---

## 📚 Core Concepts Explained

### 1. What is an LLM (Large Language Model)?

**Simple Explanation:**  
An LLM is like a very smart autocomplete. You give it a prompt, and it generates text that makes sense based on patterns it learned from millions of documents.

**Examples of LLMs:**
- ChatGPT (GPT-4)
- Qwen (what we're using)
- Llama
- Mistral

**Why We Use It:**  
To answer user questions in natural language, like "Why is my ITC lower this month?"

**Key Point:**  
LLMs can "hallucinate" — they might make up facts that sound correct but aren't true. This is why we need RAG.

---

### 2. What is RAG (Retrieval-Augmented Generation)?

**Simple Explanation:**  
RAG is a technique where we:
1. **Retrieve** relevant documents from a database
2. **Feed** those documents to the LLM as context
3. **Generate** an answer based ONLY on those documents

**Why It's Important:**  
- Reduces hallucinations
- Grounds answers in your actual data
- Makes AI responses auditable (you can see which rules were used)

**Analogy:**  
Think of it like an open-book exam vs. a closed-book exam:
- **Without RAG:** LLM tries to answer from memory (often wrong)
- **With RAG:** LLM gets to look up the answer in your rulebook (much more reliable)

---

### 3. What are Embeddings?

**Simple Explanation:**  
Embeddings convert text into numbers (vectors) that represent the *meaning* of the text.

**Example:**
```
Text: "ITC can be claimed on input services"
Embedding: [0.234, -0.567, 0.891, ..., 0.123]  (a list of 1024 numbers)
```

**Why We Need Them:**  
So we can find documents that are *semantically similar* to a user's query.

**Example:**
```
Query: "Why is my input tax credit low?"
Similar documents found:
  ✅ "ITC eligibility requirements"  (high similarity)
  ✅ "Supplier compliance for ITC"   (high similarity)
  ❌ "GST registration process"      (low similarity)
```

**Model We Use:**  
`bge-large-en-v1.5` — a model specifically trained to create good embeddings for retrieval.

---

### 4. What is ChromaDB?

**Simple Explanation:**  
ChromaDB is a database that stores embeddings and lets you search by similarity instead of exact matches.

**Traditional Database (SQL):**
```sql
SELECT * FROM rules WHERE rule_id = 'GST_ITC_17_5'
```
You get exact match or nothing.

**Vector Database (ChromaDB):**
```python
db.query("Why is my ITC lower?")
```
You get the 3 most relevant documents, even if they don't contain those exact words.

**Why We Use It:**  
To store all our GST rules and quickly find the most relevant ones for any user query.

---

## 🏗️ How LedgerMind Works: The Full Pipeline

Here's what happens when a user asks: *"Why is my ITC lower this month?"*

```
Step 1: User Query
  Input: "Why is my ITC lower this month?"

Step 2: Query Embedding
  Convert query to vector: [0.12, -0.45, 0.78, ...]

Step 3: Similarity Search in ChromaDB
  Find top 3 most similar rule documents:
    1. "ITC eligibility - supplier must file GSTR-1" (distance: 0.23)
    2. "Time limit for ITC claims" (distance: 0.45)
    3. "ITC reversal conditions" (distance: 0.52)

Step 4: Build Prompt for LLM
  Prompt = """
  You are a GST expert. Answer based on these rules:
  
  [Rule 1] ITC can be claimed only if supplier filed GSTR-1...
  [Rule 2] Time limit for ITC claim is...
  [Rule 3] ITC must be reversed if...
  
  User Query: Why is my ITC lower this month?
  
  Provide response in JSON format.
  """

Step 5: LLM Generates Response
  {
    "finding": "ITC may be lower because supplier has not filed GSTR-1...",
    "confidence": 0.87,
    "rules_used": ["GST_ITC_17_5"],
    "recommended_action": "Follow up with supplier"
  }

Step 6: Validation
  Check: Are cited rules actually in retrieved documents? ✅
  Check: Is finding grounded in context? ✅
  Adjust confidence if needed

Step 7: Return to User
  Display JSON response with explainability
```

---

## 🛠️ Installation Guide

### Prerequisites

**Hardware:**
- Minimum: 8GB RAM, any CPU
- Recommended: 16GB RAM + GPU with 6GB VRAM
- Optimal: 32GB RAM + GPU with 8GB+ VRAM

**Software:**
- Python 3.9 or higher
- pip (Python package manager)
- Git

### Step 1: Clone Repository

```bash
git clone https://github.com/yourusername/ledgermind.git
cd ledgermind
```

### Step 2: Create Virtual Environment (Recommended)

**Why?** Keeps dependencies isolated from your system Python.

```bash
# Create virtual environment
python -m venv venv

# Activate it
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate
```

You'll see `(venv)` in your terminal prompt.

### Step 3: Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**What's being installed?**
- `chromadb` — Vector database
- `sentence-transformers` — Embedding models
- `transformers` — LLM loading and inference
- `torch` — PyTorch (ML framework)
- `bitsandbytes` — For 4-bit quantization
- `accelerate` — For faster model loading

**This will take 5-10 minutes** depending on your internet speed.

### Step 4: Verify Installation

```bash
python -c "import chromadb; import transformers; import sentence_transformers; print('✅ All packages installed!')"
```

If you see `✅ All packages installed!`, you're ready!

---

## 📖 Tutorial: Your First RAG Application

Let's build a minimal RAG system step-by-step to understand the concepts.

### Tutorial 1: Understanding Embeddings

Create `learn_embeddings.py`:

```python
from sentence_transformers import SentenceTransformer

# Load embedding model
print("Loading embedding model...")
model = SentenceTransformer('BAAI/bge-small-en-v1.5')  # Smaller model for tutorial
print("Model loaded!")

# Create embeddings
sentences = [
    "ITC can be claimed on input services",
    "Supplier must file GSTR-1 for ITC",
    "The weather is nice today"
]

print("\nCreating embeddings...")
embeddings = model.encode(sentences)

print(f"\nEmbedding shape: {embeddings.shape}")
print(f"Each sentence becomes a vector of {embeddings.shape[1]} numbers")

# Calculate similarity
from numpy import dot
from numpy.linalg import norm

def cosine_similarity(a, b):
    return dot(a, b) / (norm(a) * norm(b))

print("\nSimilarity scores:")
print(f"Sentence 1 vs 2: {cosine_similarity(embeddings[0], embeddings[1]):.3f}")
print(f"Sentence 1 vs 3: {cosine_similarity(embeddings[0], embeddings[2]):.3f}")
print(f"Sentence 2 vs 3: {cosine_similarity(embeddings[1], embeddings[2]):.3f}")

print("\n👉 Notice: ITC-related sentences are more similar to each other!")
```

Run it:
```bash
python learn_embeddings.py
```

**Expected Output:**
```
Similarity scores:
Sentence 1 vs 2: 0.782  ← High similarity (both about ITC)
Sentence 1 vs 3: 0.234  ← Low similarity (different topics)
Sentence 2 vs 3: 0.198  ← Low similarity (different topics)
```

---

### Tutorial 2: Using ChromaDB

Create `learn_chromadb.py`:

```python
import chromadb

# Initialize ChromaDB
print("Initializing ChromaDB...")
client = chromadb.Client()
collection = client.create_collection("tutorial")
print("Collection created!")

# Add documents
documents = [
    "ITC can be claimed only if supplier filed GSTR-1",
    "GST rate on office supplies is 18%",
    "Reverse charge applies to services from unregistered vendors",
    "Export of services is zero-rated under GST"
]

ids = ["rule_1", "rule_2", "rule_3", "rule_4"]

metadatas = [
    {"category": "ITC", "importance": "high"},
    {"category": "RATES", "importance": "medium"},
    {"category": "RCM", "importance": "high"},
    {"category": "EXPORT", "importance": "medium"}
]

print(f"\nAdding {len(documents)} documents...")
collection.add(
    documents=documents,
    ids=ids,
    metadatas=metadatas
)
print("Documents added!")

# Query
queries = [
    "Why can't I claim input tax credit?",
    "What is the tax rate for stationery?",
    "How does GST work for exports?"
]

print("\n" + "="*60)
print("QUERY RESULTS")
print("="*60)

for query in queries:
    print(f"\nQuery: {query}")
    results = collection.query(
        query_texts=[query],
        n_results=2  # Get top 2 results
    )
    
    print("Top matches:")
    for i, (doc, metadata, distance) in enumerate(zip(
        results['documents'][0],
        results['metadatas'][0],
        results['distances'][0]
    )):
        print(f"  {i+1}. {doc}")
        print(f"     Category: {metadata['category']}, Distance: {distance:.3f}")
```

Run it:
```bash
python learn_chromadb.py
```

**Expected Output:**
```
Query: Why can't I claim input tax credit?
Top matches:
  1. ITC can be claimed only if supplier filed GSTR-1
     Category: ITC, Distance: 0.234
  2. Reverse charge applies to services from unregistered vendors
     Category: RCM, Distance: 0.567
```

**Key Insight:** ChromaDB automatically found the ITC rule even though our query didn't use the exact words!

---

### Tutorial 3: Simple RAG Without LLM

Let's build a simple RAG retrieval system (we'll add the LLM next).

Create `learn_rag.py`:

```python
import chromadb
from sentence_transformers import SentenceTransformer

class SimpleRAG:
    def __init__(self):
        # Initialize components
        self.client = chromadb.Client()
        self.collection = self.client.create_collection("simple_rag")
        self.embedder = SentenceTransformer('BAAI/bge-small-en-v1.5')
        
        # Sample knowledge base
        self.add_knowledge_base()
    
    def add_knowledge_base(self):
        """Add GST rules to vector store."""
        rules = [
            {
                "id": "GST_ITC_17_5",
                "text": "Input Tax Credit can be claimed only if the supplier has filed GSTR-1 and the tax has been paid to the government.",
                "category": "ITC"
            },
            {
                "id": "GST_RATE_18",
                "text": "Office supplies like stationery, pens, and paper are taxed at 18% GST rate.",
                "category": "RATES"
            },
            {
                "id": "GST_RCM",
                "text": "Reverse Charge Mechanism applies when services are received from unregistered vendors. The recipient must pay GST.",
                "category": "RCM"
            }
        ]
        
        self.collection.add(
            documents=[rule['text'] for rule in rules],
            ids=[rule['id'] for rule in rules],
            metadatas=[{"category": rule['category']} for rule in rules]
        )
        print(f"✅ Added {len(rules)} rules to knowledge base")
    
    def retrieve(self, query, top_k=2):
        """Retrieve relevant documents."""
        results = self.collection.query(
            query_texts=[query],
            n_results=top_k
        )
        
        retrieved = []
        for i in range(len(results['ids'][0])):
            retrieved.append({
                'rule_id': results['ids'][0][i],
                'text': results['documents'][0][i],
                'category': results['metadatas'][0][i]['category'],
                'distance': results['distances'][0][i]
            })
        
        return retrieved
    
    def answer(self, query):
        """Retrieve and format answer (without LLM for now)."""
        print(f"\n{'='*60}")
        print(f"Query: {query}")
        print('='*60)
        
        # Retrieve
        retrieved = self.retrieve(query, top_k=2)
        
        # Format simple answer
        print("\nRetrieved Rules:")
        for i, doc in enumerate(retrieved):
            print(f"\n{i+1}. [{doc['rule_id']}] (distance: {doc['distance']:.3f})")
            print(f"   {doc['text']}")
        
        # Simple answer (rule-based, no LLM)
        print("\nSimple Answer:")
        print(f"Based on rule {retrieved[0]['rule_id']}: {retrieved[0]['text'][:100]}...")
        
        return retrieved

# Test it
rag = SimpleRAG()

test_queries = [
    "Why is my ITC not available?",
    "What is the GST rate for pens and paper?",
    "Do I need to pay GST for freelancer services?"
]

for query in test_queries:
    rag.answer(query)
    input("\nPress Enter for next query...")
```

Run it:
```bash
python learn_rag.py
```

**What You'll See:**  
The system retrieves the most relevant rules for each query WITHOUT using an LLM!

---

### Tutorial 4: Adding the LLM

Now let's add Qwen to generate natural language answers.

Create `learn_rag_with_llm.py`:

```python
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

# Note: This will download the model (4-5GB) on first run
print("Loading LLM (this takes a few minutes first time)...")

model_name = "Qwen/Qwen2.5-7B-Instruct"
tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    torch_dtype=torch.float16,  # Use float16 for faster inference
    device_map="auto",
    trust_remote_code=True
)

print("✅ Model loaded!")

def generate_answer(query, retrieved_rules):
    """Generate answer using LLM with retrieved context."""
    
    # Build prompt
    context = "\n\n".join([
        f"[Rule {i+1}: {rule['rule_id']}]\n{rule['text']}"
        for i, rule in enumerate(retrieved_rules)
    ])
    
    prompt = f"""You are a GST expert. Answer the user's question based ONLY on the provided rules.

Retrieved Rules:
{context}

User Question: {query}

Provide a clear, concise answer based on the rules above:"""
    
    # Generate
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    outputs = model.generate(**inputs, max_new_tokens=150, temperature=0.3)
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    
    # Extract answer (remove prompt)
    answer = response[len(prompt):].strip()
    
    return answer

# Test with retrieved rules from previous tutorial
query = "Why is my ITC not available?"
retrieved_rules = [
    {
        'rule_id': 'GST_ITC_17_5',
        'text': 'Input Tax Credit can be claimed only if the supplier has filed GSTR-1 and the tax has been paid to the government.',
        'distance': 0.234
    }
]

print(f"\nQuery: {query}")
print("\nRetrieved Rules:")
for rule in retrieved_rules:
    print(f"  - {rule['rule_id']}: {rule['text']}")

print("\nGenerating LLM answer...")
answer = generate_answer(query, retrieved_rules)

print(f"\nLLM Answer:\n{answer}")
```

**Expected Output:**
```
Query: Why is my ITC not available?

Retrieved Rules:
  - GST_ITC_17_5: Input Tax Credit can be claimed only if...

LLM Answer:
Based on Rule GST_ITC_17_5, your ITC (Input Tax Credit) may not be 
available because your supplier has not filed their GSTR-1 return or 
has not paid the GST to the government. You can claim ITC only after 
your supplier completes these requirements.
```

---

## 🎯 Now Build LedgerMind!

You now understand:
- ✅ What embeddings are and how they work
- ✅ How ChromaDB stores and retrieves documents
- ✅ How RAG combines retrieval + LLM
- ✅ How to build a complete RAG pipeline

**Next Steps:**
1. Go to [DEVELOPMENT.md](DEVELOPMENT.md)
2. Start with **Step 1.3** (Collect GST rules)
3. Follow the step-by-step tasks
4. Build your MVP!

---

## 🐛 Common Issues & Troubleshooting

### Issue 1: "Out of memory" when loading LLM

**Solution:**
- Use 4-bit quantization (see `llm/model.py` in DEVELOPMENT.md)
- Or use CPU-only mode: `device_map="cpu"`
- Or use a smaller model: `Qwen/Qwen2.5-3B-Instruct`

### Issue 2: ChromaDB gives "ImportError"

**Solution:**
```bash
pip uninstall chromadb
pip install chromadb --upgrade
```

### Issue 3: Model download is very slow

**Solution:**
- Use HuggingFace mirror in your country
- Or download manually and load from local path

### Issue 4: "CUDA out of memory" on GPU

**Solution:**
```python
# In your model loading code, add:
torch.cuda.empty_cache()
```

---

## 📚 Further Learning

### Recommended Reading:
- [Attention Is All You Need](https://arxiv.org/abs/1706.03762) - The Transformer paper
- [RAG Paper](https://arxiv.org/abs/2005.11401) - Original RAG research
- [Sentence-BERT](https://arxiv.org/abs/1908.10084) - Embeddings for retrieval

### Tutorials:
- [HuggingFace Transformers Course](https://huggingface.co/learn/nlp-course)
- [LangChain RAG Tutorial](https://python.langchain.com/docs/use_cases/question_answering/)
- [ChromaDB Documentation](https://docs.trychroma.com/)

### Videos:
- [What are Vector Embeddings](https://www.youtube.com/watch?v=5MaWmXwxFNQ)
- [RAG Explained](https://www.youtube.com/watch?v=T-D1OfcDW1M)

---

## 💬 Get Help

If you're stuck:
1. Check [DEVELOPMENT.md](DEVELOPMENT.md) for detailed code
2. Search existing GitHub issues
3. Open a new issue with:
   - What you tried
   - Error message
   - Your system info (OS, Python version, GPU/CPU)

---

**Good luck building LedgerMind! 🚀**

*Remember: Everyone starts as a beginner. Take it one step at a time, and you'll get there!*

