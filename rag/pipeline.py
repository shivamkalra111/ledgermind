"""
RAG Pipeline: Combines Retrieval (ChromaDB) with Generation (LLM)

This is the core of your intelligent assistant.
"""

import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from typing import Dict, List, Optional
import time
import asyncio

from llm.assistant import LLMAssistant
from rag.metrics import RAGMetrics, calculate_faithfulness, calculate_relevance
from rag.hybrid_search import HybridSearcher
from config import (
    LLM_MODEL_NAME,
    LLM_BASE_URL,
    LLM_TEMPERATURE,
    LLM_MAX_TOKENS,
    RAG_NUM_RESULTS,
    RAG_MIN_SIMILARITY,
    CHROMA_DB_PATH,
    CHROMA_COLLECTION_NAME,
    EMBEDDING_MODEL,
    GST_SYSTEM_PROMPT,
    VERBOSE
)


class RAGPipeline:
    """
    Complete RAG (Retrieval-Augmented Generation) pipeline.
    
    Combines:
    - Retrieval: Find relevant documents from ChromaDB
    - Generation: Use LLM to generate natural language answers
    """
    
    def __init__(
        self,
        db_path: str = CHROMA_DB_PATH,
        collection_name: str = CHROMA_COLLECTION_NAME,
        model_name: str = LLM_MODEL_NAME,
        system_prompt: str = GST_SYSTEM_PROMPT,
        enable_metrics: bool = True
    ):
        """
        Initialize RAG pipeline.
        
        Args:
            db_path: Path to ChromaDB
            collection_name: Name of the collection
            model_name: LLM model to use
            system_prompt: System instruction for the LLM
            enable_metrics: Whether to track performance metrics
        """
        print("="*70)
        print("Initializing RAG Pipeline")
        print("="*70)
        
        self.system_prompt = system_prompt
        self.enable_metrics = enable_metrics
        
        # Initialize metrics tracker
        if self.enable_metrics:
            self.metrics = RAGMetrics()
            if VERBOSE:
                print("\n[Metrics] Enabled - logging to rag_metrics.jsonl")
        
        # 1. Setup retriever (ChromaDB)
        if VERBOSE:
            print("\n[1/2] Connecting to vector database...")
        
        # Suppress telemetry warning
        import warnings
        warnings.filterwarnings("ignore", message=".*telemetry.*")
        
        self.client = chromadb.PersistentClient(
            path=db_path,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=EMBEDDING_MODEL
        )
        
        self.collection = self.client.get_collection(
            name=collection_name,
            embedding_function=self.embedding_function
        )
        
        doc_count = self.collection.count()
        if VERBOSE:
            print(f"   ✅ Connected to '{collection_name}'")
            print(f"   📊 {doc_count} documents indexed")
        
        # Initialize hybrid searcher
        if VERBOSE:
            print("\n   → Building hybrid search index (semantic + keyword)...")
        
        self.hybrid_searcher = HybridSearcher(self.collection)
        
        if VERBOSE:
            print("   ✅ Hybrid search enabled")
        
        # 2. Setup LLM
        if VERBOSE:
            print(f"\n[2/2] Loading LLM ({model_name})...")
        
        self.llm = LLMAssistant(model_name=model_name, base_url=LLM_BASE_URL)
        
        print("\n" + "="*70)
        print("✅ RAG Pipeline Ready!")
        print("="*70)
        print()
    
    def answer(
        self,
        question: str,
        n_results: int = RAG_NUM_RESULTS,
        min_similarity: float = RAG_MIN_SIMILARITY,
        temperature: float = LLM_TEMPERATURE,
        max_tokens: int = LLM_MAX_TOKENS
    ) -> Dict:
        """
        Answer a question using RAG.
        
        Args:
            question: User's question
            n_results: Number of chunks to retrieve
            min_similarity: Minimum similarity threshold
            temperature: LLM temperature
            max_tokens: Maximum response length
        
        Returns:
            Dict with:
            - question: Original question
            - answer: Generated answer
            - sources: List of source documents
            - confidence: Average similarity score
            - chunks_used: Number of chunks provided to LLM
            - time_taken: Total processing time
            - faithfulness: How grounded the answer is in context
            - relevance: How well the answer addresses the question
        """
        start_time = time.time()
        
        # Start metrics tracking
        if self.enable_metrics:
            self.metrics.start_query(question)
        
        if VERBOSE:
            print(f"🔍 Question: {question}")
        
        # Step 1: Retrieve relevant chunks using HYBRID SEARCH
        retrieval_start = time.time()
        
        if VERBOSE:
            print(f"   → Searching knowledge base (hybrid: semantic + keyword)...")
        
        try:
            # Use hybrid search instead of pure semantic
            hybrid_results = self.hybrid_searcher.hybrid_search(
                question=question,
                n_results=n_results,
                semantic_weight=0.7,  # 70% semantic
                keyword_weight=0.3    # 30% keyword
            )
            
            # Show explanation if verbose
            if VERBOSE:
                self.hybrid_searcher.explain_search(question, hybrid_results)
            
        except Exception as e:
            error_result = {
                'question': question,
                'answer': f"Error retrieving documents: {e}",
                'sources': [],
                'confidence': 0.0,
                'chunks_used': 0,
                'time_taken': time.time() - start_time,
                'error': str(e)
            }
            if self.enable_metrics:
                self.metrics.finalize_query(
                    total_time=error_result['time_taken'],
                    error=str(e)
                )
            return error_result
        
        # Format chunks from hybrid results
        context_chunks = []
        all_similarities = []
        
        for result in hybrid_results:
            similarity = result['similarity']
            all_similarities.append(similarity)
            
            # Filter by minimum similarity
            if similarity >= min_similarity:
                context_chunks.append({
                    'text': result['text'],
                    'source': result['source'],
                    'page': result['page'],
                    'similarity': similarity,
                    'metadata': result['metadata'],
                    'search_type': result['search_type'],  # semantic/keyword/both
                    'semantic_score': result['semantic_score'],
                    'keyword_score': result['keyword_score']
                })
        
        retrieval_time = time.time() - retrieval_start
        
        # Log retrieval metrics
        if self.enable_metrics:
            self.metrics.log_retrieval(
                chunks_retrieved=len(all_similarities),
                chunks_used=len(context_chunks),
                avg_similarity=sum(all_similarities) / len(all_similarities) if all_similarities else 0,
                top_similarity=max(all_similarities) if all_similarities else 0,
                retrieval_time=retrieval_time
            )
        
        if not context_chunks:
            no_result = {
                'question': question,
                'answer': "I couldn't find relevant information to answer this question. The knowledge base may not contain this information.",
                'sources': [],
                'confidence': 0.0,
                'chunks_used': 0,
                'time_taken': time.time() - start_time,
                'faithfulness': 0.0,
                'relevance': 0.0
            }
            if self.enable_metrics:
                self.metrics.finalize_query(
                    total_time=no_result['time_taken'],
                    error=None
                )
            return no_result
        
        avg_similarity = sum(c['similarity'] for c in context_chunks) / len(context_chunks)
        
        if VERBOSE:
            print(f"   ✅ Found {len(context_chunks)} relevant chunks")
            print(f"   📊 Average similarity: {avg_similarity:.1%}")
        
        # Step 2: Generate answer with LLM
        generation_start = time.time()
        
        if VERBOSE:
            print(f"   → Generating answer with LLM...")
        
        try:
            answer = self.llm.generate_with_context(
                question=question,
                context_chunks=context_chunks,
                system_prompt=self.system_prompt,
                temperature=temperature,
                max_tokens=max_tokens
            )
        except Exception as e:
            error_result = {
                'question': question,
                'answer': f"Error generating answer: {e}",
                'sources': self._format_sources(context_chunks),
                'confidence': avg_similarity,
                'chunks_used': len(context_chunks),
                'time_taken': time.time() - start_time,
                'error': str(e)
            }
            if self.enable_metrics:
                self.metrics.finalize_query(
                    total_time=error_result['time_taken'],
                    error=str(e)
                )
            return error_result
        
        generation_time = time.time() - generation_start
        
        # Log generation metrics
        if self.enable_metrics:
            self.metrics.log_generation(
                answer=answer,
                generation_time=generation_time
            )
        
        if VERBOSE:
            print(f"   ✅ Answer generated ({len(answer)} chars)")
        
        time_taken = time.time() - start_time
        
        # Calculate advanced metrics
        context_texts = [c['text'] for c in context_chunks]
        faithfulness_score = calculate_faithfulness(answer, context_texts)
        relevance_score = calculate_relevance(question, answer)
        
        sources = self._format_sources(context_chunks)
        
        # Log sources
        if self.enable_metrics:
            self.metrics.log_sources(sources)
        
        if VERBOSE:
            print(f"   ⏱️  Total time: {time_taken:.2f}s")
            print(f"   📊 Faithfulness: {faithfulness_score:.1%}")
            print(f"   📊 Relevance: {relevance_score:.1%}")
        
        # Build result
        result = {
            'question': question,
            'answer': answer,
            'sources': sources,
            'confidence': avg_similarity,
            'chunks_used': len(context_chunks),
            'time_taken': time_taken,
            'faithfulness': faithfulness_score,
            'relevance': relevance_score
        }
        
        # Finalize metrics
        if self.enable_metrics:
            self.metrics.finalize_query(
                total_time=time_taken,
                error=None
            )
        
        # Return complete result
        return result
    
    async def answer_async(
        self,
        question: str,
        n_results: int = RAG_NUM_RESULTS,
        min_similarity: float = RAG_MIN_SIMILARITY,
        temperature: float = LLM_TEMPERATURE,
        max_tokens: int = LLM_MAX_TOKENS
    ) -> Dict:
        """
        Async version of answer() for parallel processing.
        
        Metrics calculation is done in background to not block the response.
        
        Args:
            question: User's question
            n_results: Number of chunks to retrieve
            min_similarity: Minimum similarity threshold
            temperature: LLM temperature
            max_tokens: Maximum response length
        
        Returns:
            Dict with answer, sources, confidence, etc.
        """
        start_time = time.time()
        
        # Start metrics tracking
        if self.enable_metrics:
            self.metrics.start_query(question)
        
        if VERBOSE:
            print(f"🔍 Question: {question}")
        
        # Step 1: Retrieve relevant chunks (synchronous - ChromaDB doesn't support async yet)
        retrieval_start = time.time()
        
        if VERBOSE:
            print(f"   → Searching knowledge base (hybrid: semantic + keyword)...")
        
        try:
            hybrid_results = self.hybrid_searcher.hybrid_search(
                question=question,
                n_results=n_results,
                semantic_weight=0.7,
                keyword_weight=0.3
            )
            
            if VERBOSE:
                self.hybrid_searcher.explain_search(question, hybrid_results)
            
        except Exception as e:
            error_result = {
                'question': question,
                'answer': f"Error retrieving documents: {e}",
                'sources': [],
                'confidence': 0.0,
                'chunks_used': 0,
                'time_taken': time.time() - start_time,
                'error': str(e)
            }
            if self.enable_metrics:
                self.metrics.finalize_query(
                    total_time=error_result['time_taken'],
                    error=str(e)
                )
            return error_result
        
        # Format chunks
        context_chunks = []
        all_similarities = []
        
        for result in hybrid_results:
            similarity = result['similarity']
            all_similarities.append(similarity)
            
            if similarity >= min_similarity:
                context_chunks.append({
                    'text': result['text'],
                    'source': result['source'],
                    'page': result['page'],
                    'similarity': similarity,
                    'metadata': result['metadata'],
                    'search_type': result['search_type'],
                    'semantic_score': result['semantic_score'],
                    'keyword_score': result['keyword_score']
                })
        
        retrieval_time = time.time() - retrieval_start
        
        # Log retrieval metrics
        if self.enable_metrics:
            self.metrics.log_retrieval(
                chunks_retrieved=len(all_similarities),
                chunks_used=len(context_chunks),
                avg_similarity=sum(all_similarities) / len(all_similarities) if all_similarities else 0,
                top_similarity=max(all_similarities) if all_similarities else 0,
                retrieval_time=retrieval_time
            )
        
        if not context_chunks:
            no_result = {
                'question': question,
                'answer': "I couldn't find relevant information to answer this question.",
                'sources': [],
                'confidence': 0.0,
                'chunks_used': 0,
                'time_taken': time.time() - start_time,
                'faithfulness': 0.0,
                'relevance': 0.0
            }
            if self.enable_metrics:
                self.metrics.finalize_query(
                    total_time=no_result['time_taken'],
                    error=None
                )
            return no_result
        
        avg_similarity = sum(c['similarity'] for c in context_chunks) / len(context_chunks)
        
        if VERBOSE:
            print(f"   ✅ Found {len(context_chunks)} relevant chunks")
            print(f"   📊 Average similarity: {avg_similarity:.1%}")
        
        # Step 2: Generate answer with LLM (ASYNC)
        generation_start = time.time()
        
        if VERBOSE:
            print(f"   → Generating answer with LLM...")
        
        try:
            answer = await self.llm.generate_with_context_async(
                question=question,
                context_chunks=context_chunks,
                system_prompt=self.system_prompt,
                temperature=temperature,
                max_tokens=max_tokens
            )
        except Exception as e:
            error_result = {
                'question': question,
                'answer': f"Error generating answer: {e}",
                'sources': self._format_sources(context_chunks),
                'confidence': avg_similarity,
                'chunks_used': len(context_chunks),
                'time_taken': time.time() - start_time,
                'error': str(e)
            }
            if self.enable_metrics:
                self.metrics.finalize_query(
                    total_time=error_result['time_taken'],
                    error=str(e)
                )
            return error_result
        
        generation_time = time.time() - generation_start
        
        # Log generation metrics
        if self.enable_metrics:
            self.metrics.log_generation(
                answer=answer,
                generation_time=generation_time
            )
        
        if VERBOSE:
            print(f"   ✅ Answer generated ({len(answer)} chars)")
        
        time_taken = time.time() - start_time
        sources = self._format_sources(context_chunks)
        
        # Build result (without metrics - they'll be calculated in background)
        result = {
            'question': question,
            'answer': answer,
            'sources': sources,
            'confidence': avg_similarity,
            'chunks_used': len(context_chunks),
            'time_taken': time_taken,
            'faithfulness': None,  # Will be calculated in background
            'relevance': None      # Will be calculated in background
        }
        
        # Calculate metrics in background (don't block response)
        if self.enable_metrics:
            context_texts = [c['text'] for c in context_chunks]
            asyncio.create_task(self._calculate_metrics_background(
                question, answer, context_texts, sources, time_taken
            ))
        
        if VERBOSE:
            print(f"   ⏱️  Total time: {time_taken:.2f}s")
            print(f"   📊 Metrics calculating in background...")
        
        # Return result immediately (metrics calculated async)
        return result
    
    async def _calculate_metrics_background(
        self,
        question: str,
        answer: str,
        context_texts: List[str],
        sources: List[str],
        time_taken: float
    ):
        """
        Calculate faithfulness and relevance in background.
        Doesn't block the main response.
        """
        try:
            # Run in thread pool since these functions are synchronous
            loop = asyncio.get_event_loop()
            
            faithfulness_score = await loop.run_in_executor(
                None, calculate_faithfulness, answer, context_texts
            )
            relevance_score = await loop.run_in_executor(
                None, calculate_relevance, question, answer
            )
            
            # Log sources
            if self.enable_metrics:
                self.metrics.log_sources(sources)
            
            # Finalize metrics
            if self.enable_metrics:
                self.metrics.finalize_query(
                    total_time=time_taken,
                    error=None
                )
            
            if VERBOSE:
                print(f"   📊 Faithfulness: {faithfulness_score:.1%}")
                print(f"   📊 Relevance: {relevance_score:.1%}")
                
        except Exception as e:
            if VERBOSE:
                print(f"   ⚠️  Background metrics calculation failed: {e}")
    
    def _format_sources(self, chunks: List[Dict]) -> List[str]:
        """Format source citations."""
        sources = []
        for chunk in chunks:
            source = chunk['source']
            page = chunk['page']
            similarity = chunk['similarity']
            sources.append(
                f"{source} (Page {page}, {similarity:.0%} match)"
            )
        return sources
    
    def show_metrics_summary(self, last_n: Optional[int] = None):
        """
        Display metrics summary.
        
        Args:
            last_n: Show stats for last N queries (None = all)
        """
        if not self.enable_metrics:
            print("⚠️  Metrics are disabled. Initialize with enable_metrics=True")
            return
        
        self.metrics.print_summary(last_n=last_n)
    
    def chat(self):
        """Interactive chat mode."""
        print("\n" + "="*70)
        print("💬 Interactive Chat Mode")
        print("="*70)
        print("Ask questions about GST rules. Type 'quit' to exit.")
        print("Commands: 'quit', 'help', 'stats', 'metrics'")
        print("="*70)
        print()
        
        while True:
            try:
                question = input("You: ").strip()
                
                if not question:
                    continue
                
                if question.lower() in ['quit', 'exit', 'q']:
                    print("\n👋 Goodbye!")
                    break
                
                if question.lower() == 'help':
                    self._show_help()
                    continue
                
                if question.lower() == 'stats':
                    self._show_stats()
                    continue
                
                if question.lower() in ['metrics', 'performance']:
                    if self.enable_metrics:
                        self.show_metrics_summary()
                    else:
                        print("\n⚠️  Metrics tracking is disabled.\n")
                    continue
                
                # Get answer
                print()
                result = self.answer(question)
                
                # Display answer
                print(f"\n{'='*70}")
                print(f"Assistant: {result['answer']}")
                print(f"{'='*70}")
                
                # Display sources
                if result['sources']:
                    print(f"\n📚 Sources:")
                    for i, source in enumerate(result['sources'][:3], 1):
                        print(f"   {i}. {source}")
                
                # Display confidence
                if result['confidence']:
                    print(f"\n💡 Confidence: {result['confidence']:.0%}")
                    print(f"⏱️  Response time: {result['time_taken']:.2f}s")
                
                print()
                
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")
                print()
    
    def _show_help(self):
        """Show help information."""
        print("\n" + "="*70)
        print("📖 Help")
        print("="*70)
        print("Commands:")
        print("  quit/exit/q - Exit chat mode")
        print("  help        - Show this help")
        print("  stats       - Show system statistics")
        print("  metrics     - Show performance metrics")
        print("\nExample questions:")
        print("  • How to claim Input Tax Credit?")
        print("  • What is reverse charge mechanism?")
        print("  • Time limit for filing GST returns")
        print("="*70)
        print()
    
    def _show_stats(self):
        """Show system statistics."""
        doc_count = self.collection.count()
        available_models = self.llm.list_available_models()
        
        print("\n" + "="*70)
        print("📊 System Statistics")
        print("="*70)
        print(f"Database: {CHROMA_DB_PATH}")
        print(f"Collection: {CHROMA_COLLECTION_NAME}")
        print(f"Documents indexed: {doc_count}")
        print(f"Current LLM: {self.llm.model_name}")
        print(f"Available models: {', '.join(available_models)}")
        print(f"Embedding model: {EMBEDDING_MODEL}")
        print("="*70)
        print()


# Example usage
if __name__ == "__main__":
    pipeline = RAGPipeline()
    
    # Single question
    result = pipeline.answer("How to claim Input Tax Credit?")
    print(result['answer'])
    
    # Interactive mode
    # pipeline.chat()

