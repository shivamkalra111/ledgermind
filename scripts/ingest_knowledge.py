"""
Ingest GST and Accounting PDFs into ChromaDB Knowledge Base
"""

from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.knowledge import KnowledgeBase
from config import GST_KNOWLEDGE_DIR, ACCOUNTING_KNOWLEDGE_DIR


def ingest_gst_pdfs():
    """Ingest GST PDFs into knowledge base."""
    print("=" * 60)
    print("📚 Ingesting GST Knowledge Base")
    print("=" * 60)
    
    kb = KnowledgeBase()
    total_chunks = 0
    
    if not GST_KNOWLEDGE_DIR.exists():
        print(f"❌ GST directory not found: {GST_KNOWLEDGE_DIR}")
        return 0
    
    pdf_files = list(GST_KNOWLEDGE_DIR.glob("*.pdf"))
    print(f"\nFound {len(pdf_files)} PDF files in {GST_KNOWLEDGE_DIR}\n")
    
    for pdf_path in pdf_files:
        print(f"Processing: {pdf_path.name}")
        try:
            chunks = kb.ingest_pdf(pdf_path, source_name=pdf_path.stem)
            print(f"  ✅ Added {chunks} chunks")
            total_chunks += chunks
        except Exception as e:
            print(f"  ❌ Error: {e}")
    
    return total_chunks


def ingest_accounting_pdfs(limit: int = 3):
    """Ingest Accounting PDFs into knowledge base (limited for performance)."""
    print("\n" + "=" * 60)
    print("📚 Ingesting Accounting Knowledge Base")
    print("=" * 60)
    
    kb = KnowledgeBase()
    total_chunks = 0
    
    if not ACCOUNTING_KNOWLEDGE_DIR.exists():
        print(f"❌ Accounting directory not found: {ACCOUNTING_KNOWLEDGE_DIR}")
        return 0
    
    pdf_files = list(ACCOUNTING_KNOWLEDGE_DIR.glob("*.pdf"))[:limit]
    print(f"\nProcessing {len(pdf_files)} of {len(list(ACCOUNTING_KNOWLEDGE_DIR.glob('*.pdf')))} PDF files\n")
    
    for pdf_path in pdf_files:
        print(f"Processing: {pdf_path.name}")
        try:
            chunks = kb.ingest_pdf(pdf_path, source_name=pdf_path.stem)
            print(f"  ✅ Added {chunks} chunks")
            total_chunks += chunks
        except Exception as e:
            print(f"  ❌ Error: {e}")
    
    return total_chunks


def main():
    print("\n🚀 LedgerMind Knowledge Base Ingestion\n")
    
    gst_chunks = ingest_gst_pdfs()
    accounting_chunks = ingest_accounting_pdfs(limit=2)  # Limit to 2 for speed
    
    print("\n" + "=" * 60)
    print("📊 Summary")
    print("=" * 60)
    print(f"GST Knowledge: {gst_chunks} chunks")
    print(f"Accounting Knowledge: {accounting_chunks} chunks")
    print(f"Total: {gst_chunks + accounting_chunks} chunks")
    
    # Verify
    kb = KnowledgeBase()
    print(f"\nKnowledge Base Total: {kb.count()} documents")
    
    # Test search
    print("\n🔍 Testing search...")
    results = kb.search("What is Input Tax Credit?", n_results=2)
    if results:
        print(f"  Found {len(results)} results for 'Input Tax Credit'")
        print(f"  Top result from: {results[0]['metadata'].get('source', 'Unknown')}")
    else:
        print("  No results found")
    
    print("\n✅ Ingestion complete!")


if __name__ == "__main__":
    main()

