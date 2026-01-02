"""
Scalable PDF Ingestion System

This script can handle:
1. Single PDF files
2. Entire folders of PDFs
3. Batch processing with progress tracking
4. Automatic detection and handling of different document types
5. Resume capability (skip already processed files)
6. Error handling and logging

Usage:
    # Process all PDFs in data/gst/
    python scripts/ingest_documents.py
    
    # Process specific folder
    python scripts/ingest_documents.py --folder data/my_docs
    
    # Process single file
    python scripts/ingest_documents.py --file data/my_docs/file.pdf
    
    # Force reprocess (clear existing chunks)
    python scripts/ingest_documents.py --clear
    
    # Dry run (show what would be processed)
    python scripts/ingest_documents.py --dry-run
"""

import os
import sys
from pathlib import Path
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
import pdfplumber
import argparse
from typing import List, Dict, Optional
import json
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from rag.enhanced_chunker import EnhancedSemanticChunker as SemanticChunker
from config import (
    CHROMA_DB_PATH,
    CHROMA_COLLECTION_NAME,
    EMBEDDING_MODEL
)


class DocumentIngestionPipeline:
    """
    Scalable document ingestion pipeline.
    
    Features:
    - Multi-format support (PDF primarily, extensible to others)
    - Batch processing with progress tracking
    - Resume capability (skip already processed)
    - Error handling and logging
    - Configurable chunking strategies
    """
    
    def __init__(
        self,
        db_path: str = CHROMA_DB_PATH,
        collection_name: str = CHROMA_COLLECTION_NAME,
        embedding_model: str = EMBEDDING_MODEL,
        clear_existing: bool = False
    ):
        """
        Initialize ingestion pipeline.
        
        Args:
            db_path: Path to ChromaDB
            collection_name: Name of collection
            embedding_model: Embedding model to use
            clear_existing: Whether to clear existing collection
        """
        print("="*70)
        print("📚 Document Ingestion Pipeline")
        print("="*70)
        
        # Initialize embedding function
        print(f"\n[1/3] Loading embedding model...")
        print(f"   Model: {embedding_model}")
        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=embedding_model
        )
        print(f"   ✅ Embedding model loaded (1024 dimensions)")
        
        # Initialize ChromaDB
        print(f"\n[2/3] Initializing ChromaDB...")
        self.client = chromadb.PersistentClient(
            path=db_path,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Create or get collection
        try:
            self.collection = self.client.get_collection(
                name=collection_name,
                embedding_function=self.embedding_function
            )
            count = self.collection.count()
            print(f"   ✅ Existing collection loaded ({count} documents)")
            
            if clear_existing:
                print(f"   ⚠️  Clearing existing collection...")
                self.client.delete_collection(collection_name)
                self.collection = self.client.create_collection(
                    name=collection_name,
                    embedding_function=self.embedding_function,
                    metadata={"description": "Document knowledge base"}
                )
                print("   ✅ Collection cleared and recreated")
        except:
            self.collection = self.client.create_collection(
                name=collection_name,
                embedding_function=self.embedding_function,
                metadata={"description": "Document knowledge base"}
            )
            print("   ✅ New collection created")
        
        # Initialize chunker
        print(f"\n[3/3] Initializing semantic chunker...")
        self.chunker = SemanticChunker(
            max_chunk_size=2000,
            min_chunk_size=300
        )
        print("   ✅ Ready to process documents!")
        
        # Track processed files (for resume capability)
        self.processed_log_file = Path(db_path) / "ingestion_log.json"
        self.processed_files = self._load_processed_log()
    
    def _load_processed_log(self) -> Dict:
        """Load log of previously processed files."""
        if self.processed_log_file.exists():
            with open(self.processed_log_file, 'r') as f:
                return json.load(f)
        return {}
    
    def _save_processed_log(self):
        """Save log of processed files."""
        self.processed_log_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.processed_log_file, 'w') as f:
            json.dump(self.processed_files, f, indent=2)
    
    def _is_already_processed(self, file_path: Path) -> bool:
        """Check if file was already processed."""
        file_key = str(file_path.absolute())
        if file_key not in self.processed_files:
            return False
        
        # Check if file was modified since last processing
        last_modified = file_path.stat().st_mtime
        last_processed = self.processed_files[file_key].get('timestamp', 0)
        
        return last_modified <= last_processed
    
    def _mark_as_processed(self, file_path: Path, chunks_created: int):
        """Mark file as processed."""
        file_key = str(file_path.absolute())
        self.processed_files[file_key] = {
            'timestamp': datetime.now().timestamp(),
            'chunks': chunks_created,
            'size_mb': file_path.stat().st_size / (1024 * 1024)
        }
        self._save_processed_log()
    
    def extract_text_from_pdf(self, pdf_path: Path) -> List[Dict]:
        """
        Extract text from PDF file.
        
        Returns:
            List of dicts with 'page' and 'text' keys
        """
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
    
    def process_pdf(
        self,
        pdf_path: Path,
        document_type: str = 'general',
        skip_if_processed: bool = True
    ) -> int:
        """
        Process a single PDF file.
        
        Args:
            pdf_path: Path to PDF file
            document_type: Type of document (for metadata)
            skip_if_processed: Skip if already processed
        
        Returns:
            Number of chunks created
        """
        pdf_name = pdf_path.name
        
        # Check if already processed
        if skip_if_processed and self._is_already_processed(pdf_path):
            print(f"   ⏭️  Skipping {pdf_name} (already processed)")
            return 0
        
        print(f"\n{'='*70}")
        print(f"Processing: {pdf_name}")
        print('='*70)
        
        try:
            # Step 1: Extract text
            print(f"\n  [Step 1/4] Extracting text from PDF...")
            text_pages = self.extract_text_from_pdf(pdf_path)
            print(f"  ✅ Extracted {len(text_pages)} pages")
            
            # Step 2: Combine pages
            print(f"\n  [Step 2/4] Combining pages...")
            full_text = ""
            page_boundaries = []
            
            for page_data in text_pages:
                page_num = page_data['page']
                text = page_data['text']
                
                page_boundaries.append({
                    'page': page_num,
                    'start_char': len(full_text)
                })
                
                full_text += f"\n[PAGE {page_num}]\n{text}\n"
            
            print(f"  ✅ Combined {len(text_pages)} pages ({len(full_text)} chars)")
            
            # Step 3: Semantic chunking
            print(f"\n  [Step 3/4] Semantic chunking...")
            chunks = self.chunker.chunk(
                full_text,
                base_metadata={
                    'source': pdf_name,
                    'document_type': document_type
                }
            )
            
            # Assign page numbers
            for chunk in chunks:
                chunk_start = chunk['metadata'].get('char_start', 0)
                chunk_page = 1
                for boundary in reversed(page_boundaries):
                    if chunk_start >= boundary['start_char']:
                        chunk_page = boundary['page']
                        break
                chunk['metadata']['page'] = chunk_page
            
            print(f"  ✅ Created {len(chunks)} semantic chunks")
            
            # Step 4: Store in ChromaDB
            print(f"\n  [Step 4/4] Storing in ChromaDB...")
            
            ids = []
            documents = []
            metadatas = []
            
            for i, chunk in enumerate(chunks):
                chunk_id = f"{pdf_path.stem}_{i}_{int(datetime.now().timestamp())}"
                ids.append(chunk_id)
                documents.append(chunk['text'])
                
                # Clean metadata
                clean_metadata = {}
                for key, value in chunk['metadata'].items():
                    if value is not None:
                        clean_metadata[key] = value
                    else:
                        clean_metadata[key] = "" if key == 'section_id' else 0
                
                metadatas.append(clean_metadata)
            
            # Add to ChromaDB
            self.collection.add(
                ids=ids,
                documents=documents,
                metadatas=metadatas
            )
            
            print(f"  ✅ Stored {len(ids)} chunks")
            print(f"  📊 Total in database: {self.collection.count()}")
            
            # Mark as processed
            self._mark_as_processed(pdf_path, len(chunks))
            
            return len(chunks)
            
        except Exception as e:
            print(f"  ❌ Error processing {pdf_name}: {e}")
            import traceback
            traceback.print_exc()
            return 0
    
    def process_folder(
        self,
        folder_path: Path,
        document_type: str = 'general',
        recursive: bool = True,
        skip_if_processed: bool = True
    ) -> Dict[str, int]:
        """
        Process all PDFs in a folder.
        
        Args:
            folder_path: Path to folder
            document_type: Type of documents
            recursive: Search subfolders
            skip_if_processed: Skip already processed files
        
        Returns:
            Dict with statistics
        """
        print(f"\n{'='*70}")
        print(f"📁 Scanning folder: {folder_path}")
        print('='*70)
        
        # Find all PDFs
        if recursive:
            pdf_files = sorted(folder_path.rglob("*.pdf"))
        else:
            pdf_files = sorted(folder_path.glob("*.pdf"))
        
        if not pdf_files:
            print("\n⚠️  No PDF files found!")
            return {'total_files': 0, 'total_chunks': 0}
        
        print(f"\nFound {len(pdf_files)} PDF file(s):")
        for pdf in pdf_files:
            size_mb = pdf.stat().st_size / (1024 * 1024)
            status = " (processed)" if self._is_already_processed(pdf) and skip_if_processed else ""
            print(f"  - {pdf.name} ({size_mb:.1f} MB){status}")
        
        # Process each PDF
        total_chunks = 0
        processed_count = 0
        
        for pdf_path in pdf_files:
            chunks = self.process_pdf(
                pdf_path,
                document_type=document_type,
                skip_if_processed=skip_if_processed
            )
            if chunks > 0:
                total_chunks += chunks
                processed_count += 1
        
        # Final summary
        print(f"\n{'='*70}")
        print("✅ PROCESSING COMPLETE!")
        print('='*70)
        print(f"\n📊 Statistics:")
        print(f"   Files found: {len(pdf_files)}")
        print(f"   Files processed: {processed_count}")
        print(f"   Files skipped: {len(pdf_files) - processed_count}")
        print(f"   Total chunks: {self.collection.count()}")
        print(f"   New chunks: {total_chunks}")
        
        print(f"\n💾 Database:")
        print(f"   Location: {CHROMA_DB_PATH}")
        print(f"   Collection: {CHROMA_COLLECTION_NAME}")
        print(f"   Embedding model: {EMBEDDING_MODEL}")
        
        return {
            'total_files': len(pdf_files),
            'processed_files': processed_count,
            'total_chunks': total_chunks
        }


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Scalable PDF Ingestion System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument(
        '--folder',
        type=str,
        default='data/gst',
        help='Folder containing PDFs (default: data/gst)'
    )
    
    parser.add_argument(
        '--file',
        type=str,
        help='Process single PDF file'
    )
    
    parser.add_argument(
        '--type',
        type=str,
        default='gst_legal',
        help='Document type (for metadata)'
    )
    
    parser.add_argument(
        '--clear',
        action='store_true',
        help='Clear existing collection before processing'
    )
    
    parser.add_argument(
        '--force',
        action='store_true',
        help='Force reprocess (ignore processed log)'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be processed without actually processing'
    )
    
    args = parser.parse_args()
    
    # Initialize pipeline
    pipeline = DocumentIngestionPipeline(clear_existing=args.clear)
    
    if args.dry_run:
        print("\n🔍 DRY RUN MODE - No processing will occur")
        print("="*70)
    
    # Process single file or folder
    if args.file:
        file_path = Path(args.file)
        if not file_path.exists():
            print(f"❌ File not found: {file_path}")
            return
        
        if not args.dry_run:
            pipeline.process_pdf(
                file_path,
                document_type=args.type,
                skip_if_processed=not args.force
            )
        else:
            print(f"Would process: {file_path.name}")
    else:
        folder_path = Path(args.folder)
        if not folder_path.exists():
            print(f"❌ Folder not found: {folder_path}")
            return
        
        if not args.dry_run:
            pipeline.process_folder(
                folder_path,
                document_type=args.type,
                skip_if_processed=not args.force
            )
        else:
            pdfs = list(folder_path.rglob("*.pdf"))
            print(f"Would process {len(pdfs)} PDF files from {folder_path}")
            for pdf in pdfs:
                print(f"  - {pdf.name}")


if __name__ == "__main__":
    main()

