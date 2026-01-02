"""
Process GST PDFs and Load into ChromaDB

Enhanced with:
- Context-enriched chunking (adds document/section context)
- Sentence-aware splitting (never breaks mid-sentence)
- Semantic boundaries (preserves sections and concepts)
"""

import pdfplumber
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import os
from pathlib import Path
import re
import sys

# Import enhanced chunker
sys.path.insert(0, str(Path(__file__).parent.parent))
from rag.enhanced_chunker import EnhancedSemanticChunker as SemanticChunker


class GSTProcessor:
    """Process GST PDFs with optimized settings for legal text."""
    
    def __init__(self):
        print("="*70)
        print("GST PDF Processor - Optimized for Legal/Financial Documents")
        print("="*70)
        
        # Initialize embedding function FIRST (needed for collection)
        print("\n[1/3] Loading embedding model...")
        
        # Import from config to ensure consistency
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from config import EMBEDDING_MODEL
        
        print(f"   Model: {EMBEDDING_MODEL} (optimized for formal text)")
        print("   First run: Downloads ~1.3 GB (takes 3-5 minutes)")
        
        from chromadb.utils import embedding_functions
        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=EMBEDDING_MODEL
        )
        print(f"   ✅ Embedding model loaded (1024 dimensions)")
        
        # Initialize ChromaDB
        print("\n[2/3] Initializing ChromaDB...")
        self.client = chromadb.PersistentClient(
            path="./chroma_db",
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Create or get collection
        try:
            self.collection = self.client.get_collection(
                name="gst_rules",
                embedding_function=self.embedding_function  # MUST specify for queries!
            )
            count = self.collection.count()
            print(f"   ✅ Existing collection loaded ({count} documents)")
            
            # Ask if user wants to clear existing data
            if count > 0:
                print(f"\n   ⚠️  Collection already has {count} documents!")
                print("   Do you want to:")
                print("   1. Add to existing (append)")
                print("   2. Clear and reprocess")
                choice = input("   Enter choice (1 or 2): ").strip()
                
                if choice == '2':
                    self.client.delete_collection("gst_rules")
                    self.collection = self.client.create_collection(
                        name="gst_rules",
                        embedding_function=self.embedding_function,  # Specify embedding function!
                        metadata={"description": "GST rules from official PDFs"}
                    )
                    print("   ✅ Collection cleared and recreated")
        except:
            self.collection = self.client.create_collection(
                name="gst_rules",
                embedding_function=self.embedding_function,  # Specify embedding function!
                metadata={"description": "GST rules from official PDFs"}
            )
            print("   ✅ New collection created")
        
        # Initialize semantic chunker
        print("\n[3/3] Initializing semantic chunker...")
        self.chunker = SemanticChunker(
            max_chunk_size=2000,   # Larger to keep full legal sections together
            min_chunk_size=300     # Higher minimum for better context
        )
        
        print("   ✅ Ready to process PDFs!")
        print(f"   Chunking: Semantic (preserves sections/rules, no sub-clause splits)")
        print(f"   Max chunk size: 2000 chars")
    
    def extract_text_from_pdf(self, pdf_path):
        """Extract text from PDF file."""
        text_pages = []
        
        with pdfplumber.open(pdf_path) as pdf:
            for i, page in enumerate(pdf.pages):
                text = page.extract_text()
                if text and len(text.strip()) > 50:
                    text_pages.append({
                        'page': i + 1,
                        'text': text
                    })
        
        return text_pages
    
    def process_pdf(self, pdf_path):
        """Process a single PDF: extract, chunk, embed, store."""
        
        pdf_name = os.path.basename(pdf_path)
        print(f"\n{'='*70}")
        print(f"Processing: {pdf_name}")
        print('='*70)
        
        # Step 1: Extract text from PDF
        print(f"\n  [Step 1/4] Extracting text from PDF...")
        text_pages = self.extract_text_from_pdf(pdf_path)
        print(f"  ✅ Extracted {len(text_pages)} pages")
        
        # Step 2: Combine all pages into one document with page markers
        print(f"\n  [Step 2/4] Combining pages (preserves cross-page sections)...")
        full_text = ""
        page_boundaries = []  # Track where each page starts in the full text
        
        for page_data in text_pages:
            page_num = page_data['page']
            text = page_data['text']
            
            # Record where this page starts
            page_boundaries.append({
                'page': page_num,
                'start_char': len(full_text)
            })
            
            # Add page text with marker
            full_text += f"\n[PAGE {page_num}]\n{text}\n"
        
        print(f"  ✅ Combined {len(text_pages)} pages into single document ({len(full_text)} chars)")
        
        # Step 3: Semantic chunking on the FULL document
        print(f"\n  [Step 3/4] Semantic chunking (preserves cross-page sections)...")
        
        # Create semantic chunks from full document
        chunks = self.chunker.chunk(
            full_text,
            base_metadata={
                'source': pdf_name,
                'document_type': 'gst_legal'
            }
        )
        
        # Now assign page numbers to each chunk based on where it appears
        for chunk in chunks:
            # Find which page this chunk is primarily on
            chunk_start = chunk['metadata'].get('char_start', 0)
            
            # Find the page this chunk starts in
            chunk_page = 1
            for boundary in reversed(page_boundaries):
                if chunk_start >= boundary['start_char']:
                    chunk_page = boundary['page']
                    break
            
            chunk['metadata']['page'] = chunk_page
        
        print(f"  ✅ Created {len(chunks)} semantic chunks")
        
        # Show sample chunk
        if chunks:
            sample = chunks[0]
            print(f"\n  📄 Sample chunk:")
            print(f"     Page: {sample['metadata'].get('page', 'N/A')}")
            print(f"     Section: {sample['metadata'].get('section_id', 'N/A')}")
            print(f"     Size: {len(sample['text'])} chars")
            print(f"     Preview: {sample['text'][:150]}...")
        
        # Step 4: Prepare data for ChromaDB
        print(f"\n  [Step 4/4] Preparing data for ChromaDB...")
        
        # Prepare data (ChromaDB will handle embeddings automatically)
        ids = []
        documents = []
        metadatas = []
        
        for i, chunk in enumerate(chunks):
            chunk_id = f"{pdf_name.replace('.pdf', '')}_{i}"
            ids.append(chunk_id)
            documents.append(chunk['text'])
            
            # Clean metadata: ChromaDB doesn't accept None values
            clean_metadata = {}
            for key, value in chunk['metadata'].items():
                if value is not None:
                    clean_metadata[key] = value
                else:
                    # Convert None to empty string for section_id
                    clean_metadata[key] = "" if key == 'section_id' else 0
            
            metadatas.append(clean_metadata)
        
        print(f"  ✅ Prepared {len(ids)} chunks for embedding")
        
        # Step 5: Store in ChromaDB (embeddings created automatically)
        print(f"\n  [Step 5/5] Storing in ChromaDB...")
        print(f"  (ChromaDB will create {len(documents)} embeddings with bge-large)")
        
        # Add to ChromaDB - it will use the embedding_function we specified
        self.collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas
            # Note: No embeddings parameter! ChromaDB handles this automatically
        )
        
        print(f"  ✅ Stored {len(ids)} chunks")
        print(f"  📊 Total in database: {self.collection.count()}")
    
    def process_all_pdfs(self):
        """Process all PDFs in data/gst/ folder."""
        
        # Find all PDFs
        gst_folder = Path("data/gst")
        pdf_files = sorted(gst_folder.glob("*.pdf"))
        
        if not pdf_files:
            print("\n⚠️  No PDF files found in data/gst/")
            return
        
        print(f"\nFound {len(pdf_files)} PDF file(s):")
        for pdf in pdf_files:
            size_mb = pdf.stat().st_size / (1024 * 1024)
            print(f"  - {pdf.name} ({size_mb:.1f} MB)")
        
        # Process each PDF
        for pdf_path in pdf_files:
            self.process_pdf(str(pdf_path))
        
        # Final summary
        print("\n" + "="*70)
        print("✅ PROCESSING COMPLETE!")
        print("="*70)
        
        total = self.collection.count()
        print(f"\n📊 Statistics:")
        print(f"   Total chunks: {total}")
        print(f"   PDFs processed: {len(pdf_files)}")
        print(f"   Avg chunks per PDF: {total // len(pdf_files)}")
        
        print(f"\n💾 Database:")
        print(f"   Location: ./chroma_db/")
        print(f"   Collection: gst_rules")
        print(f"   Embedding model: bge-large-en-v1.5 (1024 dims)")
        print(f"   Chunking: Semantic (section-aware)")
        
        print(f"\n🎯 Next Steps:")
        print(f"   1. Test search: python scripts/3_test_gst_search.py")
        print(f"   2. Try queries like:")
        print(f"      - 'How to claim Input Tax Credit?'")
        print(f"      - 'What is reverse charge mechanism?'")
        print(f"      - 'Time limit for ITC claim'")

def main():
    """Main entry point."""
    processor = GSTProcessor()
    processor.process_all_pdfs()

if __name__ == "__main__":
    main()
