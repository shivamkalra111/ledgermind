"""
Process GST PDFs and Load into ChromaDB

Optimized for legal/financial documents:
- Uses bge-large-en-v1.5 embeddings (better for formal text)
- Semantic chunking (preserves sections and concepts)
- Complete metadata tracking
"""

import pdfplumber
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import os
from pathlib import Path
import re

class SemanticChunker:
    """
    Semantic chunking for legal/financial documents.
    Splits by sections, rules, and logical units.
    """
    
    def __init__(self, max_chunk_size=1200, min_chunk_size=200):
        self.max_chunk_size = max_chunk_size
        self.min_chunk_size = min_chunk_size
        
        # Patterns for GST document structure
        self.section_patterns = [
            r'Section \d+[\.:)]',     # Section 16: or Section 16.
            r'Rule \d+[\.:)]',        # Rule 42: or Rule 42.
            r'Chapter [IVX]+',        # Chapter IV
            r'\n\d+\.',               # Numbered points: 1. 2. 3.
            r'\([a-z]\)',             # Sub-points: (a) (b) (c)
            r'\n\n+'                  # Paragraph breaks
        ]
    
    def find_semantic_boundaries(self, text):
        """Find positions where semantic units begin."""
        boundaries = {0}  # Start of text
        
        for pattern in self.section_patterns:
            for match in re.finditer(pattern, text):
                pos = match.start()
                if pos > 0:
                    boundaries.add(pos)
        
        boundaries = sorted(boundaries)
        boundaries.append(len(text))  # End of text
        return boundaries
    
    def extract_section_id(self, text):
        """Try to extract section/rule identifier from text."""
        # Look in first 300 characters
        section_match = re.search(
            r'(Section|Rule|Chapter)\s+([IVX\d]+(?:\(\d+\))?(?:\([a-z]\))?)',
            text[:300]
        )
        if section_match:
            return section_match.group(0)
        return None
    
    def chunk(self, text, base_metadata):
        """Create chunks at semantic boundaries."""
        boundaries = self.find_semantic_boundaries(text)
        chunks = []
        chunk_index = 0
        
        i = 0
        while i < len(boundaries) - 1:
            start = boundaries[i]
            
            # Accumulate text until max_chunk_size
            end = boundaries[i + 1]
            j = i + 1
            
            while j < len(boundaries) - 1:
                next_end = boundaries[j + 1]
                if (next_end - start) > self.max_chunk_size:
                    break
                end = next_end
                j += 1
            
            chunk_text = text[start:end].strip()
            
            # Only keep substantial chunks
            if len(chunk_text) >= self.min_chunk_size:
                section_id = self.extract_section_id(chunk_text)
                
                metadata = {
                    **base_metadata,
                    'chunk_index': chunk_index,
                    'char_start': start,
                    'char_end': end,
                    'section_id': section_id,
                    'chunking_strategy': 'semantic',
                    'chunk_size': len(chunk_text)
                }
                
                chunks.append({
                    'text': chunk_text,
                    'metadata': metadata
                })
                chunk_index += 1
            
            i = j
        
        return chunks

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
            max_chunk_size=1200,   # Larger for complete concepts
            min_chunk_size=200     # Minimum meaningful size
        )
        
        print("   ✅ Ready to process PDFs!")
        print(f"   Chunking: Semantic (preserves sections/rules)")
        print(f"   Max chunk size: 1200 chars")
    
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
        
        # Step 2: Semantic chunking
        print(f"\n  [Step 2/4] Semantic chunking (preserves sections)...")
        all_chunks = []
        
        for page_data in text_pages:
            page_num = page_data['page']
            text = page_data['text']
            
            # Create semantic chunks
            chunks = self.chunker.chunk(
                text,
                base_metadata={
                    'source': pdf_name,
                    'page': page_num,
                    'document_type': 'gst_legal'
                }
            )
            all_chunks.extend(chunks)
        
        print(f"  ✅ Created {len(all_chunks)} semantic chunks")
        
        # Show sample chunk
        if all_chunks:
            sample = all_chunks[0]
            print(f"\n  📄 Sample chunk:")
            print(f"     Section: {sample['metadata'].get('section_id', 'N/A')}")
            print(f"     Size: {len(sample['text'])} chars")
            print(f"     Preview: {sample['text'][:150]}...")
        
        # Step 3: Prepare data for ChromaDB
        print(f"\n  [Step 3/4] Preparing data for ChromaDB...")
        
        # Prepare data (ChromaDB will handle embeddings automatically)
        ids = []
        documents = []
        metadatas = []
        
        for i, chunk in enumerate(all_chunks):
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
        
        # Step 4: Store in ChromaDB (embeddings created automatically)
        print(f"\n  [Step 4/4] Storing in ChromaDB...")
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
