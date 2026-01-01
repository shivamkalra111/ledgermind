"""
Enhanced Semantic Chunker with:
1. Context Enrichment - Adds document/section context to each chunk
2. Sentence Awareness - Never breaks mid-sentence
3. Semantic Boundaries - Respects document structure
"""

import re
import nltk
from typing import List, Dict
from pathlib import Path

# Download sentence tokenizer (one-time)
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    print("Downloading sentence tokenizer...")
    nltk.download('punkt', quiet=True)


class EnhancedSemanticChunker:
    """
    Advanced chunker for legal/financial documents.
    
    Features:
    - Semantic boundaries (sections, rules, paragraphs)
    - Sentence-aware (never breaks mid-sentence)
    - Context-enriched (adds document/section context to each chunk)
    - Smart sizing (respects min/max while preserving meaning)
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
    
    def find_semantic_boundaries(self, text: str) -> List[int]:
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
    
    def extract_section_id(self, text: str) -> str:
        """Try to extract section/rule identifier from text."""
        # Look in first 300 characters
        section_match = re.search(
            r'(Section|Rule|Chapter)\s+([IVX\d]+(?:\(\d+\))?(?:\([a-z]\))?)',
            text[:300]
        )
        if section_match:
            return section_match.group(0)
        return None
    
    def extract_document_context(self, text: str, metadata: Dict) -> str:
        """
        Extract document-level context from text.
        
        Returns a brief context string to prepend to chunks.
        """
        context_parts = []
        
        # Document name
        doc_name = metadata.get('source', 'Unknown')
        if doc_name:
            # Clean up filename
            clean_name = doc_name.replace('.pdf', '').replace('_', ' ').title()
            context_parts.append(f"Document: {clean_name}")
        
        # Section/Rule identification
        section_id = self.extract_section_id(text[:500])
        if section_id:
            context_parts.append(f"Section: {section_id}")
        
        # Document type
        doc_type = metadata.get('document_type', '')
        if doc_type == 'gst_legal':
            context_parts.append("Type: GST Legal Document")
        
        # Page number
        page = metadata.get('page')
        if page:
            context_parts.append(f"Page: {page}")
        
        if context_parts:
            return "\n".join(context_parts) + "\n\n"
        return ""
    
    def split_into_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences using NLTK.
        Handles legal text better than simple split.
        """
        try:
            sentences = nltk.sent_tokenize(text)
            return sentences
        except Exception as e:
            # Fallback to simple split if NLTK fails
            return text.split('. ')
    
    def create_sentence_aware_chunk(
        self, 
        text: str, 
        start_pos: int, 
        end_pos: int
    ) -> str:
        """
        Create chunk that doesn't break mid-sentence.
        
        If chunk would exceed max_size, backtrack to last complete sentence.
        """
        candidate_text = text[start_pos:end_pos]
        
        # If within size limits, return as-is
        if len(candidate_text) <= self.max_chunk_size:
            return candidate_text
        
        # Too large - need to split at sentence boundaries
        sentences = self.split_into_sentences(candidate_text)
        
        chunk_text = ""
        for sentence in sentences:
            # Check if adding this sentence would exceed limit
            if len(chunk_text) + len(sentence) + 2 <= self.max_chunk_size:
                chunk_text += sentence + ". " if not sentence.endswith('.') else sentence + " "
            else:
                # Stop here - don't break mid-sentence
                break
        
        # Ensure we have at least min_chunk_size
        if len(chunk_text.strip()) < self.min_chunk_size and sentences:
            # Add at least one full sentence even if it exceeds max slightly
            chunk_text = sentences[0]
        
        return chunk_text.strip()
    
    def enrich_with_context(
        self, 
        chunk_text: str, 
        document_context: str,
        section_id: str = None
    ) -> str:
        """
        Add context to chunk for better embedding and retrieval.
        
        Format:
        [Document Context]
        [Section Context if available]
        
        [Chunk Text]
        """
        enriched = ""
        
        # Add document context (once per chunk)
        if document_context:
            enriched += document_context
        
        # Add section-specific context if different from document context
        if section_id and section_id not in document_context:
            enriched += f"Section: {section_id}\n\n"
        
        # Add the actual chunk text
        enriched += chunk_text
        
        return enriched
    
    def chunk(
        self, 
        text: str, 
        base_metadata: Dict,
        enable_context_enrichment: bool = True
    ) -> List[Dict]:
        """
        Create context-enriched, sentence-aware semantic chunks.
        
        Args:
            text: Full text to chunk
            base_metadata: Metadata to attach to all chunks
            enable_context_enrichment: Whether to add context to chunks
        
        Returns:
            List of dicts with 'text', 'metadata', 'original_text'
        """
        # Extract document-level context once
        document_context = self.extract_document_context(text, base_metadata)
        
        # Find semantic boundaries
        boundaries = self.find_semantic_boundaries(text)
        
        chunks = []
        chunk_index = 0
        
        for i in range(len(boundaries) - 1):
            start = boundaries[i]
            end = boundaries[i + 1]
            
            # Create sentence-aware chunk
            original_chunk_text = self.create_sentence_aware_chunk(text, start, end)
            
            # Skip tiny chunks
            if len(original_chunk_text.strip()) < self.min_chunk_size:
                continue
            
            # Extract section ID for this chunk
            section_id = self.extract_section_id(original_chunk_text)
            
            # Enrich with context if enabled
            if enable_context_enrichment:
                enriched_text = self.enrich_with_context(
                    original_chunk_text,
                    document_context,
                    section_id
                )
            else:
                enriched_text = original_chunk_text
            
            # Prepare metadata
            chunk_metadata = base_metadata.copy()
            chunk_metadata.update({
                'chunk_index': chunk_index,
                'section_id': section_id or '',
                'char_start': start,
                'char_end': end,
                'original_length': len(original_chunk_text),
                'enriched_length': len(enriched_text),
                'has_context': enable_context_enrichment
            })
            
            chunks.append({
                'text': enriched_text,  # This is what gets embedded
                'original_text': original_chunk_text,  # For reference
                'metadata': chunk_metadata
            })
            
            chunk_index += 1
        
        return chunks


# Backward compatibility - keep old name as alias
SemanticChunker = EnhancedSemanticChunker

