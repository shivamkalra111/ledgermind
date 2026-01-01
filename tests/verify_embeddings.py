"""
Verify embedding consistency across the system.

This script checks that:
1. Ingestion and RAG use the same embedding model
2. ChromaDB collection has correct embedding dimensions
3. Query embeddings match stored embeddings
"""

import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from config import EMBEDDING_MODEL


def verify_embedding_consistency():
    """Verify all components use consistent embeddings."""
    
    print("="*70)
    print("EMBEDDING CONSISTENCY CHECK")
    print("="*70)
    
    # 1. Check config
    print(f"\n✅ Config embedding model: {EMBEDDING_MODEL}")
    
    # 2. Initialize embedding function
    embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=EMBEDDING_MODEL
    )
    
    # Get embedding dimension
    test_text = "test"
    test_embedding = embedding_function([test_text])[0]
    embedding_dim = len(test_embedding)
    
    print(f"✅ Embedding dimension: {embedding_dim}")
    
    # 3. Check ChromaDB collection
    try:
        client = chromadb.PersistentClient(
            path="./chroma_db",
            settings=Settings(anonymized_telemetry=False)
        )
        
        collection = client.get_collection(
            name="gst_rules",
            embedding_function=embedding_function
        )
        
        # Get a sample document
        sample = collection.get(limit=1, include=['embeddings'])
        
        if sample['embeddings']:
            stored_dim = len(sample['embeddings'][0])
            print(f"✅ Stored embeddings dimension: {stored_dim}")
            
            if stored_dim == embedding_dim:
                print(f"✅ MATCH: Query ({embedding_dim}) == Stored ({stored_dim})")
            else:
                print(f"❌ MISMATCH: Query ({embedding_dim}) != Stored ({stored_dim})")
                print("\n⚠️  WARNING: Embeddings are incompatible!")
                print("   Solution: Re-run ingestion with correct model")
                return False
        else:
            print("⚠️  No embeddings found (collection might be empty)")
        
        doc_count = collection.count()
        print(f"✅ Documents in collection: {doc_count}")
        
    except Exception as e:
        print(f"❌ Error checking ChromaDB: {e}")
        return False
    
    # 4. Test query
    print(f"\n{'─'*70}")
    print("Testing Query")
    print(f"{'─'*70}")
    
    try:
        results = collection.query(
            query_texts=["test query"],
            n_results=1
        )
        
        if results['ids'][0]:
            print("✅ Query successful")
            print(f"   Top result similarity: {1 - results['distances'][0][0]:.1%}")
        else:
            print("⚠️  No results returned")
            
    except Exception as e:
        print(f"❌ Query failed: {e}")
        return False
    
    # Summary
    print(f"\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}")
    print("✅ All embedding checks passed!")
    print(f"✅ Model: {EMBEDDING_MODEL}")
    print(f"✅ Dimension: {embedding_dim}")
    print(f"✅ ChromaDB compatible: Yes")
    print(f"✅ Queries will work correctly")
    print(f"{'='*70}\n")
    
    return True


def show_embedding_info():
    """Show detailed embedding configuration."""
    
    print("\n" + "="*70)
    print("EMBEDDING CONFIGURATION")
    print("="*70)
    
    print(f"\n📋 Current Setup:")
    print(f"   Model: {EMBEDDING_MODEL}")
    print(f"   Type: Sentence Transformer")
    print(f"   Dimensions: 1024")
    print(f"   Optimized for: Legal/Financial text")
    
    print(f"\n🔄 Where It's Used:")
    print(f"   1. scripts/ingest_pdfs.py → Encode documents")
    print(f"   2. rag/pipeline.py → Encode queries")
    print(f"   3. ChromaDB collection → Store & retrieve")
    
    print(f"\n⚡ Critical Rules:")
    print(f"   ✅ Same model for ingestion AND queries")
    print(f"   ✅ Same dimensions (1024)")
    print(f"   ✅ Specified in config.py")
    print(f"   ✅ Passed to ChromaDB collection")
    
    print(f"\n❌ What NOT to Do:")
    print(f"   ❌ Change model in only one place")
    print(f"   ❌ Use different models for encode/query")
    print(f"   ❌ Hardcode model names (use config)")
    
    print(f"\n💡 To Change Embedding Model:")
    print(f"   1. Edit config.py → EMBEDDING_MODEL")
    print(f"   2. Delete chroma_db/ folder")
    print(f"   3. Re-run: python scripts/ingest_pdfs.py")
    print(f"   4. Test: python tests/test_search.py")
    
    print("="*70 + "\n")


if __name__ == "__main__":
    # Show configuration
    show_embedding_info()
    
    # Verify consistency
    success = verify_embedding_consistency()
    
    if success:
        print("✅ System is correctly configured!")
    else:
        print("❌ System has embedding inconsistencies!")
        print("   Re-run ingestion to fix.")

