"""
Hybrid Search: Combines semantic (vector) and keyword (BM25) search.

For GST queries, this is especially useful for:
- Exact section references: "Section 16(5)"
- Specific numbers: "6 months", "20 lakh"
- Abbreviations: "GSTR-1", "ITC"
- Dates and amounts
"""

import re
from typing import List, Dict, Set
from rank_bm25 import BM25Okapi


class HybridSearcher:
    """
    Hybrid search combining semantic similarity and keyword matching.
    
    Semantic: Good for understanding meaning/context
    Keyword: Good for exact matches (sections, numbers, terms)
    """
    
    def __init__(self, collection):
        """
        Initialize hybrid searcher.
        
        Args:
            collection: ChromaDB collection
        """
        self.collection = collection
        self.bm25_index = None
        self.all_documents = []
        self.doc_ids = []
        
        # Build BM25 index
        self._build_bm25_index()
    
    def _build_bm25_index(self):
        """Build BM25 keyword index from all documents."""
        # Get all documents from ChromaDB
        all_data = self.collection.get(
            include=['documents', 'metadatas']
        )
        
        self.all_documents = all_data['documents']
        self.doc_ids = all_data['ids']
        
        # Tokenize documents for BM25
        tokenized_docs = [doc.lower().split() for doc in self.all_documents]
        self.bm25_index = BM25Okapi(tokenized_docs)
        
        print(f"   ✅ BM25 index built with {len(self.all_documents)} documents")
    
    def _extract_important_terms(self, question: str) -> List[str]:
        """
        Extract important terms from question for keyword search.
        
        Focus on:
        - Section references: "Section 16", "Rule 42"
        - Numbers: "6 months", "20 lakh"
        - Abbreviations: "ITC", "GSTR-1"
        - Dates: "31st March"
        """
        important_terms = []
        
        # 1. Section/Rule references
        sections = re.findall(r'Section\s+\d+(?:\(\d+\))?', question, re.IGNORECASE)
        rules = re.findall(r'Rule\s+\d+(?:\(\d+\))?', question, re.IGNORECASE)
        important_terms.extend(sections + rules)
        
        # 2. Numbers with context
        numbers = re.findall(r'\d+\s*(?:lakh|crore|months?|days?|years?|percent|%)', question, re.IGNORECASE)
        important_terms.extend(numbers)
        
        # 3. Specific GST terms
        gst_terms = [
            'GSTR-1', 'GSTR-3B', 'GSTR-9', 'ITC', 'CGST', 'SGST', 'IGST', 'UTGST',
            'Input Tax Credit', 'reverse charge', 'composition scheme', 'e-way bill',
            'place of supply', 'time of supply', 'taxable supply', 'exempt supply'
        ]
        for term in gst_terms:
            if term.lower() in question.lower():
                important_terms.append(term)
        
        # 4. Dates
        dates = re.findall(r'\d+(?:st|nd|rd|th)?\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)', question, re.IGNORECASE)
        important_terms.extend(dates)
        
        return important_terms
    
    def hybrid_search(
        self, 
        question: str, 
        n_results: int = 7,
        semantic_weight: float = 0.7,
        keyword_weight: float = 0.3
    ) -> List[Dict]:
        """
        Perform hybrid search combining semantic and keyword results.
        
        Args:
            question: User's question
            n_results: Total number of results to return
            semantic_weight: Weight for semantic search (0-1)
            keyword_weight: Weight for keyword search (0-1)
        
        Returns:
            List of dicts with 'text', 'metadata', 'score', 'search_type'
        """
        # 1. Semantic search via ChromaDB
        semantic_results = self.collection.query(
            query_texts=[question],
            n_results=n_results,
            include=['documents', 'metadatas', 'distances']
        )
        
        # 2. Keyword search via BM25
        tokenized_query = question.lower().split()
        bm25_scores = self.bm25_index.get_scores(tokenized_query)
        
        # Get top N from BM25
        top_bm25_indices = sorted(
            range(len(bm25_scores)), 
            key=lambda i: bm25_scores[i], 
            reverse=True
        )[:n_results]
        
        # 3. Boost for important terms (section numbers, dates, etc.)
        important_terms = self._extract_important_terms(question)
        
        # 4. Combine and score
        combined_scores = {}
        
        # Add semantic results
        for i, (doc, meta, dist) in enumerate(zip(
            semantic_results['documents'][0],
            semantic_results['metadatas'][0],
            semantic_results['distances'][0]
        )):
            doc_id = semantic_results['ids'][0][i]
            semantic_score = 1 - dist  # Convert distance to similarity
            
            # Boost if contains important terms
            boost = 1.0
            doc_lower = doc.lower()
            for term in important_terms:
                if term.lower() in doc_lower:
                    boost += 0.2  # 20% boost per important term
            
            combined_scores[doc_id] = {
                'text': doc,
                'metadata': meta,
                'semantic_score': semantic_score,
                'keyword_score': 0,
                'boost': boost,
                'final_score': semantic_score * semantic_weight * boost,
                'search_type': 'semantic'
            }
        
        # Add keyword results
        for idx in top_bm25_indices:
            doc_id = self.doc_ids[idx]
            doc_text = self.all_documents[idx]
            bm25_score = bm25_scores[idx]
            
            # Normalize BM25 score (0-1 range)
            max_bm25 = max(bm25_scores) if max(bm25_scores) > 0 else 1
            normalized_bm25 = bm25_score / max_bm25
            
            # Boost for important terms
            boost = 1.0
            doc_lower = doc_text.lower()
            for term in important_terms:
                if term.lower() in doc_lower:
                    boost += 0.2
            
            if doc_id in combined_scores:
                # Already in semantic results, add keyword score
                combined_scores[doc_id]['keyword_score'] = normalized_bm25
                combined_scores[doc_id]['final_score'] += normalized_bm25 * keyword_weight * boost
                combined_scores[doc_id]['search_type'] = 'both'
            else:
                # Only in keyword results
                # Get metadata from collection
                doc_data = self.collection.get(
                    ids=[doc_id],
                    include=['metadatas']
                )
                
                combined_scores[doc_id] = {
                    'text': doc_text,
                    'metadata': doc_data['metadatas'][0] if doc_data['metadatas'] else {},
                    'semantic_score': 0,
                    'keyword_score': normalized_bm25,
                    'boost': boost,
                    'final_score': normalized_bm25 * keyword_weight * boost,
                    'search_type': 'keyword'
                }
        
        # 5. Sort by final score and return top N
        sorted_results = sorted(
            combined_scores.items(),
            key=lambda x: x[1]['final_score'],
            reverse=True
        )[:n_results]
        
        # 6. Format results
        results = []
        for doc_id, scores in sorted_results:
            results.append({
                'text': scores['text'],
                'metadata': scores['metadata'],
                'similarity': scores['final_score'],  # For compatibility
                'semantic_score': scores['semantic_score'],
                'keyword_score': scores['keyword_score'],
                'boost': scores['boost'],
                'search_type': scores['search_type'],
                'source': scores['metadata'].get('source', 'Unknown'),
                'page': scores['metadata'].get('page', 'N/A')
            })
        
        return results
    
    def explain_search(self, question: str, results: List[Dict]):
        """Print explanation of hybrid search results."""
        important_terms = self._extract_important_terms(question)
        
        print(f"\n🔍 Hybrid Search Explanation:")
        print(f"   Question: {question}")
        if important_terms:
            print(f"   Important terms detected: {', '.join(important_terms)}")
        print(f"   Results: {len(results)} documents")
        print()
        
        for i, result in enumerate(results[:3], 1):
            print(f"   [{i}] {result['source']} (Page {result['page']})")
            print(f"       Semantic: {result['semantic_score']:.2%} | "
                  f"Keyword: {result['keyword_score']:.2%} | "
                  f"Boost: {result['boost']:.1f}x | "
                  f"Type: {result['search_type']}")
            print(f"       Final Score: {result['similarity']:.2%}")
            print()

