"""
RAG Performance Metrics Module

Tracks and analyzes RAG system performance across multiple dimensions:
1. Retrieval Quality - How well we find relevant chunks
2. Generation Quality - How good the LLM answers are
3. System Performance - Speed, efficiency
4. User Satisfaction - Implicit and explicit feedback
"""

import time
from typing import List, Dict, Optional
from datetime import datetime
import json
from pathlib import Path


class RAGMetrics:
    """
    Comprehensive RAG metrics tracker.
    
    Tracks both quantitative metrics (speed, confidence) and 
    qualitative metrics (answer quality, relevance).
    """
    
    def __init__(self, log_file: str = "rag_metrics.jsonl"):
        self.log_file = Path(log_file)
        self.current_query_metrics = {}
        
    def start_query(self, question: str):
        """Start tracking a new query."""
        self.current_query_metrics = {
            'question': question,
            'timestamp': datetime.now().isoformat(),
            'start_time': time.time()
        }
    
    def log_retrieval(
        self, 
        chunks_retrieved: int,
        chunks_used: int,
        avg_similarity: float,
        top_similarity: float,
        retrieval_time: float
    ):
        """Log retrieval stage metrics."""
        self.current_query_metrics.update({
            'chunks_retrieved': chunks_retrieved,
            'chunks_used': chunks_used,
            'avg_similarity': avg_similarity,
            'top_similarity': top_similarity,
            'retrieval_time': retrieval_time,
            'retrieval_efficiency': chunks_used / chunks_retrieved if chunks_retrieved > 0 else 0
        })
    
    def log_generation(
        self,
        answer: str,
        generation_time: float,
        tokens_generated: Optional[int] = None
    ):
        """Log generation stage metrics."""
        self.current_query_metrics.update({
            'answer_length': len(answer),
            'answer_words': len(answer.split()),
            'generation_time': generation_time,
            'tokens_generated': tokens_generated
        })
    
    def log_sources(self, sources: List[str]):
        """Log source citations."""
        self.current_query_metrics.update({
            'num_sources_cited': len(sources),
            'sources': sources
        })
    
    def finalize_query(self, total_time: float, error: Optional[str] = None):
        """Finalize query metrics."""
        self.current_query_metrics.update({
            'total_time': total_time,
            'error': error,
            'success': error is None
        })
        
        # Calculate derived metrics
        self._calculate_derived_metrics()
        
        # Save to log
        self._save_to_log()
        
        return self.current_query_metrics.copy()
    
    def _calculate_derived_metrics(self):
        """Calculate additional derived metrics."""
        metrics = self.current_query_metrics
        
        # Confidence score (based on similarity)
        metrics['confidence_score'] = metrics.get('avg_similarity', 0)
        
        # Response quality indicators
        answer_length = metrics.get('answer_length', 0)
        
        # Too short = likely "I don't know"
        # Too long = might be verbose
        # Sweet spot: 200-800 characters
        if answer_length < 100:
            metrics['response_quality_flag'] = 'too_short'
        elif answer_length > 1000:
            metrics['response_quality_flag'] = 'verbose'
        else:
            metrics['response_quality_flag'] = 'good'
        
        # Efficiency score (speed vs quality tradeoff)
        # Fast + high confidence = efficient
        total_time = metrics.get('total_time', 0)
        confidence = metrics.get('confidence_score', 0)
        
        if total_time > 0:
            # Efficiency = confidence per second
            metrics['efficiency_score'] = confidence / total_time
        else:
            metrics['efficiency_score'] = 0
    
    def _save_to_log(self):
        """Save metrics to JSONL file."""
        with open(self.log_file, 'a') as f:
            f.write(json.dumps(self.current_query_metrics) + '\n')
    
    def get_summary_statistics(self, last_n: Optional[int] = None) -> Dict:
        """
        Get summary statistics from logged metrics.
        
        Args:
            last_n: Only analyze last N queries (None = all)
        
        Returns:
            Dictionary with summary statistics
        """
        if not self.log_file.exists():
            return {'error': 'No metrics logged yet'}
        
        # Load all metrics
        all_metrics = []
        with open(self.log_file, 'r') as f:
            for line in f:
                all_metrics.append(json.loads(line))
        
        if not all_metrics:
            return {'error': 'No metrics found'}
        
        # Filter to last N if specified
        if last_n:
            all_metrics = all_metrics[-last_n:]
        
        # Calculate statistics
        total_queries = len(all_metrics)
        successful_queries = sum(1 for m in all_metrics if m.get('success', False))
        
        # Average metrics
        avg_total_time = sum(m.get('total_time', 0) for m in all_metrics) / total_queries
        avg_retrieval_time = sum(m.get('retrieval_time', 0) for m in all_metrics) / total_queries
        avg_generation_time = sum(m.get('generation_time', 0) for m in all_metrics) / total_queries
        avg_confidence = sum(m.get('confidence_score', 0) for m in all_metrics) / total_queries
        avg_chunks_used = sum(m.get('chunks_used', 0) for m in all_metrics) / total_queries
        
        # Quality flags distribution
        quality_flags = {}
        for m in all_metrics:
            flag = m.get('response_quality_flag', 'unknown')
            quality_flags[flag] = quality_flags.get(flag, 0) + 1
        
        return {
            'total_queries': total_queries,
            'successful_queries': successful_queries,
            'success_rate': successful_queries / total_queries,
            'avg_total_time': round(avg_total_time, 2),
            'avg_retrieval_time': round(avg_retrieval_time, 2),
            'avg_generation_time': round(avg_generation_time, 2),
            'avg_confidence': round(avg_confidence, 2),
            'avg_chunks_used': round(avg_chunks_used, 1),
            'quality_distribution': quality_flags,
            'time_breakdown': {
                'retrieval_pct': round((avg_retrieval_time / avg_total_time * 100), 1) if avg_total_time > 0 else 0,
                'generation_pct': round((avg_generation_time / avg_total_time * 100), 1) if avg_total_time > 0 else 0
            }
        }
    
    def print_summary(self, last_n: Optional[int] = None):
        """Print formatted summary statistics."""
        stats = self.get_summary_statistics(last_n)
        
        if 'error' in stats:
            print(f"❌ {stats['error']}")
            return
        
        print("\n" + "="*70)
        print("RAG PERFORMANCE SUMMARY")
        if last_n:
            print(f"(Last {last_n} queries)")
        print("="*70)
        
        print(f"\n📊 Overall:")
        print(f"   Total Queries: {stats['total_queries']}")
        print(f"   Success Rate: {stats['success_rate']:.1%}")
        
        print(f"\n⏱️  Performance:")
        print(f"   Avg Total Time: {stats['avg_total_time']:.2f}s")
        print(f"   ├─ Retrieval: {stats['avg_retrieval_time']:.2f}s ({stats['time_breakdown']['retrieval_pct']}%)")
        print(f"   └─ Generation: {stats['avg_generation_time']:.2f}s ({stats['time_breakdown']['generation_pct']}%)")
        
        print(f"\n🎯 Quality:")
        print(f"   Avg Confidence: {stats['avg_confidence']:.1%}")
        print(f"   Avg Chunks Used: {stats['avg_chunks_used']:.1f}")
        
        print(f"\n📝 Response Quality:")
        for flag, count in stats['quality_distribution'].items():
            pct = (count / stats['total_queries']) * 100
            emoji = "✅" if flag == "good" else "⚠️"
            print(f"   {emoji} {flag}: {count} ({pct:.1f}%)")
        
        print("="*70 + "\n")


class RAGEvaluator:
    """
    Advanced RAG evaluation for testing specific aspects.
    
    Uses ground truth questions and expected answers to 
    calculate more sophisticated metrics.
    """
    
    def __init__(self):
        self.test_cases = []
    
    def add_test_case(
        self,
        question: str,
        expected_keywords: List[str],
        expected_sources: Optional[List[str]] = None,
        min_confidence: float = 0.3
    ):
        """Add a test case for evaluation."""
        self.test_cases.append({
            'question': question,
            'expected_keywords': expected_keywords,
            'expected_sources': expected_sources,
            'min_confidence': min_confidence
        })
    
    def evaluate(self, rag_pipeline) -> Dict:
        """
        Run evaluation on all test cases.
        
        Returns metrics like:
        - Answer accuracy (keyword coverage)
        - Source accuracy (correct citations)
        - Confidence calibration
        """
        results = []
        
        for test_case in self.test_cases:
            result = rag_pipeline.answer(test_case['question'])
            
            # Calculate keyword coverage
            answer_lower = result['answer'].lower()
            keywords_found = sum(
                1 for kw in test_case['expected_keywords'] 
                if kw.lower() in answer_lower
            )
            keyword_coverage = keywords_found / len(test_case['expected_keywords'])
            
            # Check confidence threshold
            meets_confidence = result['confidence'] >= test_case['min_confidence']
            
            # Check sources (if provided)
            source_accuracy = None
            if test_case['expected_sources']:
                sources_found = sum(
                    1 for exp_src in test_case['expected_sources']
                    if any(exp_src in src for src in result['sources'])
                )
                source_accuracy = sources_found / len(test_case['expected_sources'])
            
            results.append({
                'question': test_case['question'],
                'keyword_coverage': keyword_coverage,
                'meets_confidence': meets_confidence,
                'source_accuracy': source_accuracy,
                'actual_confidence': result['confidence'],
                'time_taken': result['time_taken']
            })
        
        # Calculate aggregate metrics
        avg_keyword_coverage = sum(r['keyword_coverage'] for r in results) / len(results)
        confidence_pass_rate = sum(1 for r in results if r['meets_confidence']) / len(results)
        
        return {
            'total_test_cases': len(results),
            'avg_keyword_coverage': round(avg_keyword_coverage, 2),
            'confidence_pass_rate': round(confidence_pass_rate, 2),
            'individual_results': results
        }
    
    def print_evaluation(self, rag_pipeline):
        """Run and print evaluation results."""
        eval_results = self.evaluate(rag_pipeline)
        
        print("\n" + "="*70)
        print("RAG EVALUATION RESULTS")
        print("="*70)
        
        print(f"\n📊 Overall:")
        print(f"   Test Cases: {eval_results['total_test_cases']}")
        print(f"   Avg Keyword Coverage: {eval_results['avg_keyword_coverage']:.1%}")
        print(f"   Confidence Pass Rate: {eval_results['confidence_pass_rate']:.1%}")
        
        print(f"\n📝 Individual Results:")
        for i, result in enumerate(eval_results['individual_results']):
            print(f"\n   [{i+1}] {result['question'][:50]}...")
            print(f"       Keyword Coverage: {result['keyword_coverage']:.1%}")
            print(f"       Confidence: {result['actual_confidence']:.1%} " + 
                  ("✅" if result['meets_confidence'] else "❌"))
            print(f"       Time: {result['time_taken']:.2f}s")
        
        print("="*70 + "\n")


def calculate_faithfulness(answer: str, context_chunks: List[str]) -> float:
    """
    Calculate faithfulness score using NLI (Natural Language Inference).
    
    Uses a DeBERTa-based NLI model to check if each sentence in the answer
    is entailed by the context chunks.
    
    Returns:
        float: Faithfulness score between 0.0 and 1.0
    """
    import re
    
    # Lazy import to avoid loading model unless needed
    try:
        from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
    except ImportError:
        print("⚠️  Warning: transformers not installed. Falling back to basic faithfulness.")
        return _calculate_faithfulness_fallback(answer, context_chunks)
    
    # Initialize NLI model (cached after first call)
    global _nli_model
    if '_nli_model' not in globals():
        try:
            print("   📦 Loading NLI model (cross-encoder/nli-deberta-v3-base)...")
            print("   ⏳ First run: Downloading ~760MB model (takes 2-4 minutes)")
            
            # Load model and tokenizer explicitly
            model_name = "cross-encoder/nli-deberta-v3-base"
            tokenizer = AutoTokenizer.from_pretrained(model_name)
            model = AutoModelForSequenceClassification.from_pretrained(model_name)
            
            _nli_model = pipeline(
                "text-classification",
                model=model,
                tokenizer=tokenizer,
                device=-1  # CPU
            )
            print("   ✅ NLI model loaded successfully")
        except Exception as e:
            print(f"   ❌ Failed to load NLI model: {e}")
            print("   ⚠️  Falling back to basic faithfulness calculation")
            return _calculate_faithfulness_fallback(answer, context_chunks)
    
    # Split answer into sentences
    sentences = re.split(r'[.!?]+', answer)
    
    # Remove citations and filter short sentences
    citation_pattern = r'\[source:.*?\]'
    sentences = [
        re.sub(citation_pattern, '', s, flags=re.IGNORECASE).strip() 
        for s in sentences 
        if len(s.strip()) > 10
    ]
    
    if not sentences:
        return 0.0
    
    # Combine context chunks
    context_text = ' '.join(context_chunks)
    
    # Truncate context if too long (NLI models have token limits)
    # DeBERTa can handle ~512 tokens, leave room for answer sentence
    if len(context_text) > 2000:  # ~400 tokens
        context_text = context_text[:2000] + "..."
    
    supported_count = 0
    
    # Check each sentence against context
    for sentence in sentences:
        try:
            # NLI format: {text: context, text_pair: sentence}
            result = _nli_model({"text": context_text, "text_pair": sentence})
            
            # Extract label and confidence (result is a dict, not a list!)
            label = result['label'].lower()
            score = result['score']
            
            # Consider sentence supported if:
            # - Label is 'entailment' with confidence > 50%
            # - Label is 'neutral' with very high confidence > 90% (strong inference)
            # - Label is 'contradiction' is definitely NOT supported
            if (label == 'entailment' and score > 0.5) or \
               (label == 'neutral' and score > 0.90):
                supported_count += 1
                
        except Exception as e:
            # If NLI fails for this sentence, use fallback for this one
            sentence_lower = sentence.lower()
            words = [w for w in sentence_lower.split() if len(w) > 3]
            if words:
                context_lower = context_text.lower()
                words_found = sum(1 for w in words if w in context_lower)
                if words_found / len(words) >= 0.5:
                    supported_count += 1
    
    return supported_count / len(sentences) if sentences else 0.0


def _calculate_faithfulness_fallback(answer: str, context_chunks: List[str]) -> float:
    """
    Fallback faithfulness calculation using word-level matching.
    Used when NLI model is unavailable.
    """
    import re
    
    # Split sentences
    sentences = re.split(r'[.!?]+', answer)
    
    # Remove citations
    citation_pattern = r'\[source:.*?\]'
    sentences = [re.sub(citation_pattern, '', s, flags=re.IGNORECASE).strip() 
                 for s in sentences if len(s.strip()) > 10]
    
    if not sentences:
        return 0.0
    
    # Combine context
    context_text = ' '.join(context_chunks).lower()
    
    supported_count = 0
    
    for sentence in sentences:
        sentence_lower = sentence.lower()
        
        # Extract meaningful words
        words = [w for w in sentence_lower.split() if len(w) > 3]
        
        if not words:
            continue
        
        # Check word presence (relaxed threshold: 50%)
        words_found = sum(1 for w in words if w in context_text)
        
        if words_found / len(words) >= 0.5:
            supported_count += 1
    
    return supported_count / len(sentences) if sentences else 0.0


def calculate_relevance(question: str, answer: str) -> float:
    """
    Calculate relevance score - how well the answer addresses the question.
    
    Simple heuristic: Check keyword overlap and answer type matching.
    """
    question_lower = question.lower()
    answer_lower = answer.lower()
    
    # Extract question keywords (exclude common words)
    stop_words = {'what', 'is', 'are', 'the', 'a', 'an', 'how', 'when', 'where', 'why', 'who'}
    question_keywords = [
        w for w in question_lower.split() 
        if len(w) > 3 and w not in stop_words
    ]
    
    if not question_keywords:
        return 0.5  # Neutral if can't extract keywords
    
    # Check keyword presence in answer
    keywords_in_answer = sum(1 for kw in question_keywords if kw in answer_lower)
    keyword_score = keywords_in_answer / len(question_keywords)
    
    # Check if answer type matches question type
    type_score = 0.0
    if question_lower.startswith('what is') or question_lower.startswith('define'):
        # Definition questions should have defining phrases
        if any(phrase in answer_lower for phrase in ['is a', 'refers to', 'means', 'defined as']):
            type_score = 1.0
    elif question_lower.startswith('how'):
        # How-to questions should have procedural language
        if any(phrase in answer_lower for phrase in ['must', 'should', 'need to', 'required', 'steps']):
            type_score = 1.0
    else:
        type_score = 0.5  # Neutral for other types
    
    # Weighted combination
    return (keyword_score * 0.7) + (type_score * 0.3)

