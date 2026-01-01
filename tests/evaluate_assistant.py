#!/usr/bin/env python3
"""
Automated evaluation of LLM assistant performance.
Runs test suite and generates performance report.

Usage:
    python tests/evaluate_assistant.py
    python tests/evaluate_assistant.py --limit 10  # Run only first 10 tests
"""

import json
import sys
import time
import argparse
from pathlib import Path
from typing import Dict, List

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from rag.pipeline import RAGPipeline


class AssistantEvaluator:
    """Evaluate assistant against ground truth test set."""
    
    def __init__(self, test_file='tests/test_questions.json'):
        self.test_file = Path(test_file)
        self.pipeline = None
        self.results = []
    
    def load_tests(self, limit=None):
        """Load test questions."""
        with open(self.test_file) as f:
            tests = json.load(f)
        
        if limit:
            tests = tests[:limit]
        
        return tests
    
    def evaluate_answer(self, result: Dict, expected: Dict) -> tuple:
        """
        Score an answer against expected criteria.
        
        Returns:
            (score_dict, passed_bool)
        """
        score = {
            'keyword_match': 0.0,
            'source_match': False,
            'confidence_ok': False,
            'faithfulness_ok': False,
            'relevance_ok': False
        }
        
        answer_lower = result['answer'].lower()
        
        # 1. Keyword matching (most important)
        keywords_found = sum(
            1 for kw in expected['expected_answer_contains']
            if kw.lower() in answer_lower
        )
        total_keywords = len(expected['expected_answer_contains'])
        score['keyword_match'] = keywords_found / total_keywords if total_keywords > 0 else 0
        
        # 2. Source matching
        expected_source = expected.get('expected_source', '').lower()
        if expected_source and result['sources']:
            score['source_match'] = any(
                expected_source in src.lower() 
                for src in result['sources']
            )
        else:
            score['source_match'] = True  # No source requirement
        
        # 3. Confidence threshold (retrieval quality)
        min_confidence = 0.25 if expected['difficulty'] == 'hard' else 0.30
        score['confidence_ok'] = result['confidence'] >= min_confidence
        
        # 4. Faithfulness threshold (grounding)
        score['faithfulness_ok'] = result.get('faithfulness', 0) >= 0.65
        
        # 5. Relevance threshold (answer quality)
        score['relevance_ok'] = result.get('relevance', 0) >= 0.70
        
        # Overall pass/fail logic
        # Must have at least 50% keywords AND good faithfulness
        passed = (
            score['keyword_match'] >= 0.5 and
            score['faithfulness_ok'] and
            score['confidence_ok']
        )
        
        return score, passed
    
    def run_evaluation(self, limit=None):
        """Run full evaluation suite."""
        print("="*70)
        print("🧪 EVALUATING LLM ASSISTANT")
        print("="*70)
        
        # Initialize pipeline
        print("\nInitializing RAG pipeline...")
        self.pipeline = RAGPipeline()
        
        # Load tests
        tests = self.load_tests(limit=limit)
        print(f"\n📋 Running {len(tests)} test questions...")
        print("="*70)
        
        total_passed = 0
        results_by_category = {}
        results_by_difficulty = {}
        
        for i, test in enumerate(tests, 1):
            question = test['question']
            print(f"\n[{i}/{len(tests)}] {question[:65]}...")
            
            # Get answer
            start = time.time()
            try:
                result = self.pipeline.answer(question)
                duration = time.time() - start
            except Exception as e:
                print(f"   ❌ ERROR: {e}")
                continue
            
            # Evaluate
            score, passed = self.evaluate_answer(result, test)
            
            # Record result
            test_result = {
                'test_id': test['id'],
                'question': test['question'],
                'category': test.get('category', 'unknown'),
                'difficulty': test.get('difficulty', 'unknown'),
                'answer': result['answer'],
                'confidence': result['confidence'],
                'faithfulness': result.get('faithfulness', 0),
                'relevance': result.get('relevance', 0),
                'duration': duration,
                'score': score,
                'passed': passed
            }
            
            self.results.append(test_result)
            
            # Track by category
            category = test.get('category', 'unknown')
            if category not in results_by_category:
                results_by_category[category] = {'passed': 0, 'total': 0}
            results_by_category[category]['total'] += 1
            if passed:
                results_by_category[category]['passed'] += 1
            
            # Track by difficulty
            difficulty = test.get('difficulty', 'unknown')
            if difficulty not in results_by_difficulty:
                results_by_difficulty[difficulty] = {'passed': 0, 'total': 0}
            results_by_difficulty[difficulty]['total'] += 1
            if passed:
                results_by_difficulty[difficulty]['passed'] += 1
                total_passed += 1
            
            # Show result
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"   {status} | Conf: {result['confidence']:.0%} | "
                  f"Faith: {result.get('faithfulness', 0):.0%} | "
                  f"Keywords: {score['keyword_match']:.0%} | "
                  f"Time: {duration:.1f}s")
            
            # Show why it failed
            if not passed:
                if score['keyword_match'] < 0.5:
                    print(f"      ⚠️  Missing keywords ({score['keyword_match']:.0%} coverage)")
                if not score['faithfulness_ok']:
                    print(f"      ⚠️  Low faithfulness ({result.get('faithfulness', 0):.0%})")
                if not score['confidence_ok']:
                    print(f"      ⚠️  Low confidence ({result['confidence']:.0%})")
        
        # Print summary
        self.print_summary(total_passed, len(tests), results_by_category, results_by_difficulty)
        
        return self.results
    
    def print_summary(self, passed, total, by_category, by_difficulty):
        """Print evaluation summary."""
        print("\n" + "="*70)
        print("📊 EVALUATION SUMMARY")
        print("="*70)
        
        # Overall
        pass_rate = passed / total if total > 0 else 0
        emoji = "✅" if pass_rate >= 0.7 else "⚠️" if pass_rate >= 0.5 else "❌"
        
        print(f"\n{emoji} Overall Performance:")
        print(f"   Passed: {passed}/{total} ({pass_rate:.0%})")
        print(f"   Failed: {total - passed}/{total}")
        
        # By category
        print(f"\n📋 By Category:")
        for category, stats in sorted(by_category.items()):
            cat_pass_rate = stats['passed'] / stats['total'] if stats['total'] > 0 else 0
            emoji = "✅" if cat_pass_rate >= 0.7 else "⚠️" if cat_pass_rate >= 0.5 else "❌"
            print(f"   {emoji} {category.title():15} {stats['passed']:2}/{stats['total']:2} ({cat_pass_rate:.0%})")
        
        # By difficulty
        print(f"\n📊 By Difficulty:")
        for difficulty in ['easy', 'medium', 'hard']:
            if difficulty in by_difficulty:
                stats = by_difficulty[difficulty]
                diff_pass_rate = stats['passed'] / stats['total'] if stats['total'] > 0 else 0
                emoji = "✅" if diff_pass_rate >= 0.7 else "⚠️" if diff_pass_rate >= 0.5 else "❌"
                print(f"   {emoji} {difficulty.title():15} {stats['passed']:2}/{stats['total']:2} ({diff_pass_rate:.0%})")
        
        # Performance metrics
        if self.results:
            print(f"\n⏱️  Performance Metrics:")
            avg_time = sum(r['duration'] for r in self.results) / len(self.results)
            avg_conf = sum(r['confidence'] for r in self.results) / len(self.results)
            avg_faith = sum(r['faithfulness'] for r in self.results) / len(self.results)
            avg_rel = sum(r['relevance'] for r in self.results) / len(self.results)
            
            print(f"   Avg Response Time: {avg_time:.2f}s")
            print(f"   Avg Confidence:    {avg_conf:.0%}")
            print(f"   Avg Faithfulness:  {avg_faith:.0%}")
            print(f"   Avg Relevance:     {avg_rel:.0%}")
        
        # Failure analysis
        failures = [r for r in self.results if not r['passed']]
        if failures:
            print(f"\n❌ Failure Analysis ({len(failures)} failures):")
            low_conf = sum(1 for f in failures if not f['score']['confidence_ok'])
            low_faith = sum(1 for f in failures if not f['score']['faithfulness_ok'])
            low_keywords = sum(1 for f in failures if f['score']['keyword_match'] < 0.5)
            
            if low_conf:
                print(f"   📉 Low confidence: {low_conf}/{len(failures)} ({low_conf/len(failures):.0%})")
            if low_faith:
                print(f"   📉 Low faithfulness: {low_faith}/{len(failures)} ({low_faith/len(failures):.0%})")
            if low_keywords:
                print(f"   📉 Missing keywords: {low_keywords}/{len(failures)} ({low_keywords/len(failures):.0%})")
        
        # Recommendations
        print(f"\n💡 Recommendations:")
        if pass_rate < 0.5:
            print("   ⚠️  CRITICAL: Pass rate is very low (<50%)")
            print("   → Check if ChromaDB has correct documents")
            print("   → Review system prompt in config.py")
            print("   → Consider lowering RAG_MIN_SIMILARITY")
        elif pass_rate < 0.7:
            print("   ⚠️  NEEDS IMPROVEMENT: Pass rate below 70%")
            if avg_conf < 0.35:
                print("   → Tune retrieval: increase RAG_NUM_RESULTS or lower RAG_MIN_SIMILARITY")
            if avg_faith < 0.7:
                print("   → Improve prompt: Add 'Answer ONLY from context' to system prompt")
            if sum(1 for r in self.results if r['score']['keyword_match'] < 0.5) > len(self.results) * 0.3:
                print("   → Improve answer quality: Add few-shot examples to system prompt")
        else:
            print("   ✅ Good performance! Consider:")
            print("   → Collect human feedback for validation")
            print("   → Test with real user questions")
            print("   → Monitor metrics over time")
        
        print("="*70)
    
    def save_results(self, output_file='evaluation_results.json'):
        """Save detailed results to file."""
        output_path = Path(output_file)
        with open(output_path, 'w') as f:
            json.dump({
                'timestamp': time.time(),
                'total_tests': len(self.results),
                'passed': sum(1 for r in self.results if r['passed']),
                'results': self.results
            }, f, indent=2)
        print(f"\n💾 Detailed results saved to: {output_path.absolute()}")


def main():
    parser = argparse.ArgumentParser(description='Evaluate LLM assistant performance')
    parser.add_argument(
        '--limit',
        type=int,
        default=None,
        help='Run only first N tests (for quick testing)'
    )
    parser.add_argument(
        '--save',
        type=str,
        default='evaluation_results.json',
        help='Output file for detailed results'
    )
    
    args = parser.parse_args()
    
    try:
        evaluator = AssistantEvaluator()
        results = evaluator.run_evaluation(limit=args.limit)
        evaluator.save_results(output_file=args.save)
        
        # Exit code based on pass rate
        passed = sum(1 for r in results if r['passed'])
        pass_rate = passed / len(results) if results else 0
        
        if pass_rate >= 0.7:
            sys.exit(0)  # Success
        else:
            sys.exit(1)  # Failure
            
    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure you have:")
        print("  1. Created tests/test_questions.json")
        print("  2. Ingested PDFs (python scripts/ingest_pdfs.py)")
        print("  3. Started Ollama (ollama serve)")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Evaluation interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

