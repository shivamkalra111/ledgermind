"""
Knowledge Base - ChromaDB Integration
Stores GST rules and accounting standards for RAG lookups
"""

import chromadb
from chromadb.config import Settings
from pathlib import Path
from typing import List, Dict, Optional
import hashlib

from config import (
    CHROMA_DIR, 
    CHROMA_COLLECTION_NAME, 
    EMBEDDING_MODEL,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    GST_KNOWLEDGE_DIR,
    ACCOUNTING_KNOWLEDGE_DIR
)


class KnowledgeBase:
    """ChromaDB-based knowledge base for GST rules and accounting standards."""
    
    def __init__(self, persist_dir: Path = CHROMA_DIR):
        self.persist_dir = Path(persist_dir)
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize ChromaDB with persistence
        self.client = chromadb.PersistentClient(
            path=str(self.persist_dir),
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=CHROMA_COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"}
        )
        
        # Embedding function will be set when needed
        self._embedder = None
    
    @property
    def embedder(self):
        """Lazy load the embedding model."""
        if self._embedder is None:
            from sentence_transformers import SentenceTransformer
            self._embedder = SentenceTransformer(EMBEDDING_MODEL)
        return self._embedder
    
    def add_document(
        self,
        text: str,
        metadata: Dict,
        doc_id: Optional[str] = None
    ) -> str:
        """Add a document chunk to the knowledge base."""
        
        if doc_id is None:
            doc_id = hashlib.md5(text.encode()).hexdigest()
        
        # Generate embedding
        embedding = self.embedder.encode(text).tolist()
        
        self.collection.add(
            ids=[doc_id],
            embeddings=[embedding],
            documents=[text],
            metadatas=[metadata]
        )
        
        return doc_id
    
    def add_documents(
        self,
        texts: List[str],
        metadatas: List[Dict],
        ids: Optional[List[str]] = None
    ) -> List[str]:
        """Add multiple document chunks to the knowledge base."""
        
        if ids is None:
            ids = [hashlib.md5(t.encode()).hexdigest() for t in texts]
        
        # Generate embeddings
        embeddings = self.embedder.encode(texts).tolist()
        
        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas
        )
        
        return ids
    
    def search(
        self,
        query: str,
        n_results: int = 5,
        filter_metadata: Optional[Dict] = None
    ) -> List[Dict]:
        """Search the knowledge base for relevant documents."""
        
        # Generate query embedding
        query_embedding = self.embedder.encode(query).tolist()
        
        # Search
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=filter_metadata
        )
        
        # Format results
        formatted = []
        for i in range(len(results["ids"][0])):
            formatted.append({
                "id": results["ids"][0][i],
                "text": results["documents"][0][i],
                "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                "distance": results["distances"][0][i] if results["distances"] else None
            })
        
        return formatted
    
    def get_relevant_rules(self, query: str, n_results: int = 5) -> str:
        """Get relevant GST rules as formatted text for LLM context."""
        
        results = self.search(query, n_results)
        
        if not results:
            return "No relevant rules found."
        
        formatted_rules = []
        for i, result in enumerate(results, 1):
            source = result["metadata"].get("source", "Unknown")
            section = result["metadata"].get("section", "")
            text = result["text"]
            
            formatted_rules.append(f"[{i}] {source} {section}\n{text}")
        
        return "\n\n---\n\n".join(formatted_rules)
    
    def count(self) -> int:
        """Get the number of documents in the knowledge base."""
        return self.collection.count()
    
    def clear(self) -> None:
        """Clear all documents from the knowledge base."""
        # Delete and recreate collection
        self.client.delete_collection(CHROMA_COLLECTION_NAME)
        self.collection = self.client.create_collection(
            name=CHROMA_COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"}
        )
    
    def ingest_pdf(self, pdf_path: Path, source_name: Optional[str] = None) -> int:
        """Ingest a PDF file into the knowledge base."""
        
        from pypdf import PdfReader
        
        pdf_path = Path(pdf_path)
        if source_name is None:
            source_name = pdf_path.stem
        
        # Extract text from PDF
        reader = PdfReader(pdf_path)
        full_text = ""
        for page_num, page in enumerate(reader.pages):
            text = page.extract_text()
            if text:
                full_text += f"\n[Page {page_num + 1}]\n{text}"
        
        # Chunk the text
        chunks = self._chunk_text(full_text)
        
        # Add chunks to knowledge base
        texts = []
        metadatas = []
        
        for i, chunk in enumerate(chunks):
            texts.append(chunk)
            metadatas.append({
                "source": source_name,
                "chunk_index": i,
                "file_path": str(pdf_path)
            })
        
        self.add_documents(texts, metadatas)
        
        return len(chunks)
    
    def _chunk_text(self, text: str) -> List[str]:
        """Split text into overlapping chunks."""
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + CHUNK_SIZE
            
            # Try to break at sentence boundary
            if end < len(text):
                # Look for sentence ending
                for char in ['. ', '.\n', '\n\n']:
                    pos = text.rfind(char, start, end)
                    if pos > start:
                        end = pos + len(char)
                        break
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            start = end - CHUNK_OVERLAP
        
        return chunks


# Convenience function
def get_knowledge_base() -> KnowledgeBase:
    """Get the default knowledge base."""
    return KnowledgeBase()

