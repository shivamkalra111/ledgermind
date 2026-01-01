"""
Comprehensive RAG System Tests with Metrics

This test suite verifies:
1. Prompt construction (system + user + context)
2. RAG pipeline flow
3. Answer quality metrics
4. Performance benchmarks
"""

import time
import json
from typing import Dict, List
from rag.pipeline import RAGPipeline
from llm.assistant import LLMAssistant


class RAGMetrics:
    """Track and display RAG system metrics."""
    
    def __init__(self):
        self.results = []
    
    def add_result(self, result: Dict):
        """Add a test result."""
        self.results.append(result)
    
    def calculate_metrics(self) -> Dict:
        """Calculate aggregate metrics."""
        if not self.results:
            return {}
        
        return {
            'total_queries': len(self.results),
            'avg_confidence': sum(r.get('confidence', 0) for r in self.results) / len(self.results),
            'avg_chunks_used': sum(r.get('chunks_used', 0) for r in self.results) / len(self.results),
            'avg_response_time': sum(r.get('time_taken', 0) for r in self.results) / len(self.results),
            'successful': sum(1 for r in self.results if not r.get('error')),
            'failed': sum(1 for r in self.results if r.get('error')),
            'avg_answer_length': sum(len(r.get('answer', '')) for r in self.results) / len(self.results)
        }
    
    def print_report(self):
        """Print detailed metrics report."""
        metrics = self.calculate_metrics()
        
        print("\n" + "="*70)
        print("RAG SYSTEM METRICS REPORT")
        print("="*70)
        
        print(f"\n📊 Overall Statistics:")
        print(f"  Total queries: {metrics['total_queries']}")
        print(f"  Successful: {metrics['successful']}")
        print(f"  Failed: {metrics['failed']}")
        
        print(f"\n⏱️  Performance:")
        print(f"  Avg response time: {metrics['avg_response_time']:.2f}s")
        print(f"  Avg chunks used: {metrics['avg_chunks_used']:.1f}")
        
        print(f"\n📈 Quality Metrics:")
        print(f"  Avg confidence: {metrics['avg_confidence']:.1%}")
        print(f"  Avg answer length: {metrics['avg_answer_length']:.0f} chars")
        
        print("\n" + "="*70)
        
        return metrics


def test_prompt_construction():
    """
    Test 1: Understand how prompts are built
    
    Shows how system prompt, user question, and context are combined
    into the final prompt sent to the LLM.
    """
    print("\n" + "="*70)
    print("TEST 1: PROMPT CONSTRUCTION")
    print("="*70)
    
    print("\n📝 How prompts work in our RAG system:\n")
    
    # Initialize LLM
    llm = LLMAssistant()
    
    # Example context chunks
    context_chunks = [
        {
            'text': 'Input Tax Credit (ITC) is available to registered persons...',
            'source': 'a2017-12.pdf',
            'page': 29
        },
        {
            'text': 'To claim ITC, you must have a valid tax invoice...',
            'source': 'cgst-rules.pdf',
            'page': 38
        }
    ]
    
    question = "How to claim Input Tax Credit?"
    
    system_prompt = """You are a GST compliance assistant.
Provide accurate answers based on the given context."""
    
    # Build the prompt (same way the system does it)
    prompt = llm._build_prompt(question, context_chunks, system_prompt)
    
    print("FINAL PROMPT STRUCTURE:")
    print("-"*70)
    print(prompt)
    print("-"*70)
    
    print("\n✅ Key Points:")
    print("  1. System prompt defines LLM behavior")
    print("  2. Context chunks provide knowledge (from ChromaDB)")
    print("  3. User question is at the end")
    print("  4. Sources are cited for each chunk")
    print()
    
    return True


def test_rag_flow():
    """
    Test 2: Understand RAG pipeline flow
    
    Step-by-step breakdown of what happens when you ask a question.
    """
    print("\n" + "="*70)
    print("TEST 2: RAG PIPELINE FLOW")
    print("="*70)
    
    print("\n🔄 Step-by-step breakdown:\n")
    
    pipeline = RAGPipeline()
    
    question = "What is Input Tax Credit?"
    
    print(f"Step 1: User asks question")
    print(f"  → \"{question}\"")
    
    print(f"\nStep 2: Question is embedded (1024-dim vector)")
    print(f"  → Uses bge-large-en-v1.5 model")
    
    print(f"\nStep 3: Vector search in ChromaDB")
    print(f"  → Finds top 5 most similar chunks")
    print(f"  → Calculates similarity scores")
    
    print(f"\nStep 4: Build prompt")
    print(f"  → System prompt (from config.py)")
    print(f"  → Retrieved chunks (context)")
    print(f"  → User question")
    
    print(f"\nStep 5: LLM generates answer")
    print(f"  → Sends prompt to Ollama")
    print(f"  → Model: qwen2.5:7b-instruct")
    print(f"  → Temperature: 0.3 (focused)")
    
    print(f"\nStep 6: Post-process response")
    print(f"  → Add source citations")
    print(f"  → Calculate confidence")
    print(f"  → Format output")
    
    # Actually run it
    print(f"\n{'─'*70}")
    print("ACTUAL EXECUTION:")
    print(f"{'─'*70}\n")
    
    result = pipeline.answer(question)
    
    print(f"\n✅ Result:")
    print(f"  Answer: {result['answer'][:100]}...")
    print(f"  Confidence: {result['confidence']:.1%}")
    print(f"  Chunks used: {result['chunks_used']}")
    print(f"  Time taken: {result['time_taken']:.2f}s")
    print(f"  Sources: {len(result['sources'])}")
    print()
    
    return result


def test_question_types():
    """
    Test 3: Test different question types
    
    Evaluates how the system handles:
    - Factual questions
    - Analytical questions
    - Comparison questions
    """
    print("\n" + "="*70)
    print("TEST 3: DIFFERENT QUESTION TYPES")
    print("="*70)
    
    pipeline = RAGPipeline()
    metrics = RAGMetrics()
    
    test_cases = [
        {
            'type': 'Factual',
            'question': 'What is Input Tax Credit?',
            'expected': 'Should define ITC and explain concept'
        },
        {
            'type': 'Procedural',
            'question': 'How to claim Input Tax Credit?',
            'expected': 'Should provide step-by-step process'
        },
        {
            'type': 'Analytical',
            'question': 'How many tax rules are indexed?',
            'expected': 'Should count and provide number'
        },
        {
            'type': 'Comparison',
            'question': 'What is the difference between ITC and reverse charge?',
            'expected': 'Should compare and contrast both concepts'
        }
    ]
    
    print("\nRunning test cases...\n")
    
    for i, test in enumerate(test_cases, 1):
        print(f"{'─'*70}")
        print(f"Test Case {i}: {test['type']}")
        print(f"{'─'*70}")
        print(f"Question: {test['question']}")
        print(f"Expected: {test['expected']}")
        print()
        
        result = pipeline.answer(test['question'])
        metrics.add_result(result)
        
        print(f"Answer preview: {result['answer'][:150]}...")
        print(f"Confidence: {result['confidence']:.1%}")
        print(f"Time: {result['time_taken']:.2f}s")
        print()
    
    # Print metrics
    metrics.print_report()
    
    return metrics


def test_performance_benchmarks():
    """
    Test 4: Performance benchmarks
    
    Measures:
    - Response time
    - Retrieval speed
    - LLM generation speed
    """
    print("\n" + "="*70)
    print("TEST 4: PERFORMANCE BENCHMARKS")
    print("="*70)
    
    pipeline = RAGPipeline()
    
    questions = [
        "What is CGST?",
        "How to file GST returns?",
        "What are GST rates?",
        "Who is eligible for ITC?",
        "What is reverse charge mechanism?"
    ]
    
    print(f"\nBenchmarking {len(questions)} queries...\n")
    
    times = {
        'total': [],
        'retrieval': [],
        'generation': []
    }
    
    for i, question in enumerate(questions, 1):
        print(f"Query {i}/{len(questions)}: {question}")
        
        start = time.time()
        result = pipeline.answer(question)
        total_time = time.time() - start
        
        times['total'].append(total_time)
        
        print(f"  → Time: {total_time:.2f}s")
        print(f"  → Confidence: {result['confidence']:.0%}")
        print()
    
    # Calculate statistics
    print("="*70)
    print("PERFORMANCE SUMMARY")
    print("="*70)
    print(f"\nResponse Times:")
    print(f"  Min: {min(times['total']):.2f}s")
    print(f"  Max: {max(times['total']):.2f}s")
    print(f"  Avg: {sum(times['total'])/len(times['total']):.2f}s")
    print(f"  Total: {sum(times['total']):.2f}s")
    
    print(f"\nThroughput:")
    print(f"  {len(questions)/sum(times['total']):.2f} queries/second")
    
    print()
    
    return times


def test_answer_quality():
    """
    Test 5: Answer quality metrics
    
    Evaluates:
    - Relevance (confidence score)
    - Completeness (answer length)
    - Source quality (similarity scores)
    """
    print("\n" + "="*70)
    print("TEST 5: ANSWER QUALITY METRICS")
    print("="*70)
    
    pipeline = RAGPipeline()
    
    test_questions = [
        "What is Input Tax Credit?",
        "How to claim ITC?",
        "What is reverse charge?"
    ]
    
    print("\nEvaluating answer quality...\n")
    
    quality_scores = []
    
    for question in test_questions:
        print(f"Question: {question}")
        result = pipeline.answer(question)
        
        # Calculate quality score
        quality = {
            'question': question,
            'confidence': result['confidence'],
            'answer_length': len(result['answer']),
            'chunks_used': result['chunks_used'],
            'has_sources': len(result['sources']) > 0,
            'complete': len(result['answer']) > 100,  # Basic check
        }
        
        quality_scores.append(quality)
        
        print(f"  Confidence: {quality['confidence']:.1%}")
        print(f"  Answer length: {quality['answer_length']} chars")
        print(f"  Sources: {len(result['sources'])}")
        print(f"  Quality: {'✅ Good' if quality['confidence'] > 0.5 else '⚠️ Low'}")
        print()
    
    # Summary
    avg_confidence = sum(q['confidence'] for q in quality_scores) / len(quality_scores)
    avg_length = sum(q['answer_length'] for q in quality_scores) / len(quality_scores)
    
    print("="*70)
    print(f"Overall Quality:")
    print(f"  Avg Confidence: {avg_confidence:.1%}")
    print(f"  Avg Answer Length: {avg_length:.0f} chars")
    print(f"  All have sources: {all(q['has_sources'] for q in quality_scores)}")
    print()
    
    return quality_scores


def run_all_tests():
    """Run all tests and generate comprehensive report."""
    print("="*70)
    print("🧪 RAG SYSTEM COMPREHENSIVE TEST SUITE")
    print("="*70)
    
    results = {}
    
    try:
        # Test 1: Prompt construction
        results['prompt'] = test_prompt_construction()
        
        # Test 2: RAG flow
        results['flow'] = test_rag_flow()
        
        # Test 3: Question types
        results['questions'] = test_question_types()
        
        # Test 4: Performance
        results['performance'] = test_performance_benchmarks()
        
        # Test 5: Quality
        results['quality'] = test_answer_quality()
        
        # Final summary
        print("\n" + "="*70)
        print("✅ ALL TESTS COMPLETED")
        print("="*70)
        print("\nYou now understand:")
        print("  1. How prompts are constructed (system + context + question)")
        print("  2. How RAG pipeline flows (retrieve → generate)")
        print("  3. How different question types are handled")
        print("  4. System performance characteristics")
        print("  5. Answer quality metrics")
        print()
        
        return results
        
    except ConnectionError as e:
        print(f"\n❌ Connection Error: {e}")
        print("\nMake sure:")
        print("  1. Ollama is running: ollama serve")
        print("  2. Model is downloaded: ollama pull qwen2.5:7b-instruct")
        return None
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    # Run all tests
    results = run_all_tests()
    
    # Save results
    if results:
        with open('test_results.json', 'w') as f:
            # Convert non-serializable objects
            serializable = {
                'timestamp': time.time(),
                'tests_run': list(results.keys()),
                'success': True
            }
            json.dump(serializable, f, indent=2)
        print("\n📊 Results saved to: test_results.json")

