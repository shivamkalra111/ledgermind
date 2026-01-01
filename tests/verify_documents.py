#!/usr/bin/env python3
"""
Verify that test questions can be answered from available documents.

This script:
1. Analyzes your PDF documents
2. Checks which test questions can be answered from them
3. Identifies questions that may not have answers in your data
4. Suggests additional documents needed
"""

import sys
import json
import PyPDF2
from pathlib import Path
from typing import List, Dict, Set

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class DocumentVerifier:
    """Verify test questions against available documents."""
    
    def __init__(self, data_dir='data/gst', test_file='tests/test_questions.json'):
        self.data_dir = Path(data_dir)
        self.test_file = Path(test_file)
        self.documents_text = {}
        self.all_text = ""
    
    def load_pdfs(self):
        """Load and extract text from all PDFs."""
        print("="*70)
        print("LOADING PDF DOCUMENTS")
        print("="*70)
        
        pdf_files = list(self.data_dir.glob('*.pdf'))
        
        if not pdf_files:
            print(f"\n❌ No PDF files found in {self.data_dir}")
            return False
        
        print(f"\nFound {len(pdf_files)} PDF files:")
        
        for pdf_file in pdf_files:
            print(f"\n📄 Loading: {pdf_file.name}")
            try:
                with open(pdf_file, 'rb') as f:
                    reader = PyPDF2.PdfReader(f)
                    text = ""
                    
                    for page_num in range(len(reader.pages)):
                        page = reader.pages[page_num]
                        text += page.extract_text() + "\n"
                    
                    self.documents_text[pdf_file.name] = text
                    self.all_text += text + "\n"
                    
                    print(f"   ✅ Extracted {len(reader.pages)} pages, {len(text):,} characters")
            
            except Exception as e:
                print(f"   ❌ Error reading {pdf_file.name}: {e}")
                return False
        
        print(f"\n✅ Total content: {len(self.all_text):,} characters")
        return True
    
    def load_test_questions(self):
        """Load test questions."""
        with open(self.test_file) as f:
            return json.load(f)
    
    def check_keyword_coverage(self, keywords: List[str], text: str) -> tuple:
        """Check which keywords are present in text."""
        text_lower = text.lower()
        found = []
        missing = []
        
        for keyword in keywords:
            if keyword.lower() in text_lower:
                found.append(keyword)
            else:
                missing.append(keyword)
        
        return found, missing
    
    def verify_questions(self):
        """Verify each test question against documents."""
        tests = self.load_test_questions()
        
        print("\n" + "="*70)
        print(f"VERIFYING {len(tests)} TEST QUESTIONS")
        print("="*70)
        
        answerable = []
        questionable = []
        likely_unanswerable = []
        
        for i, test in enumerate(tests, 1):
            question = test['question']
            keywords = test['expected_answer_contains']
            
            # Check keyword coverage
            found, missing = self.check_keyword_coverage(keywords, self.all_text)
            coverage = len(found) / len(keywords) if keywords else 0
            
            # Categorize
            if coverage >= 0.7:  # 70%+ keywords present
                answerable.append((test, coverage, found, missing))
            elif coverage >= 0.3:  # 30-70% keywords present
                questionable.append((test, coverage, found, missing))
            else:  # <30% keywords present
                likely_unanswerable.append((test, coverage, found, missing))
        
        # Print results
        print(f"\n📊 VERIFICATION SUMMARY:")
        print(f"   ✅ Likely Answerable:     {len(answerable)}/{len(tests)} ({len(answerable)/len(tests):.0%})")
        print(f"   ⚠️  Questionable:          {len(questionable)}/{len(tests)} ({len(questionable)/len(tests):.0%})")
        print(f"   ❌ Likely Unanswerable:   {len(likely_unanswerable)}/{len(tests)} ({len(likely_unanswerable)/len(tests):.0%})")
        
        # Show details of questionable questions
        if questionable:
            print(f"\n⚠️  QUESTIONABLE QUESTIONS (may have partial answers):")
            print("="*70)
            for test, coverage, found, missing in questionable[:10]:  # Show first 10
                print(f"\nQ{test['id']}: {test['question']}")
                print(f"   Coverage: {coverage:.0%}")
                print(f"   Found: {', '.join(found[:3])}...")
                print(f"   Missing: {', '.join(missing)}")
        
        # Show details of likely unanswerable
        if likely_unanswerable:
            print(f"\n❌ LIKELY UNANSWERABLE QUESTIONS:")
            print("="*70)
            for test, coverage, found, missing in likely_unanswerable:
                print(f"\nQ{test['id']}: {test['question']}")
                print(f"   Coverage: {coverage:.0%}")
                if found:
                    print(f"   Found: {', '.join(found)}")
                print(f"   Missing: {', '.join(missing)}")
                print(f"   Category: {test.get('category', 'unknown')}")
                print(f"   Expected source: {test.get('expected_source', 'unknown')}")
        
        # Analyze by document
        self.analyze_by_document(tests)
        
        # Recommendations
        self.print_recommendations(answerable, questionable, likely_unanswerable)
        
        return answerable, questionable, likely_unanswerable
    
    def analyze_by_document(self, tests):
        """Analyze which document likely contains answers."""
        print(f"\n📚 COVERAGE BY DOCUMENT:")
        print("="*70)
        
        for doc_name, doc_text in self.documents_text.items():
            answerable_count = 0
            
            for test in tests:
                keywords = test['expected_answer_contains']
                found, _ = self.check_keyword_coverage(keywords, doc_text)
                coverage = len(found) / len(keywords) if keywords else 0
                
                if coverage >= 0.5:  # At least 50% keywords
                    answerable_count += 1
            
            print(f"\n{doc_name}:")
            print(f"   Can likely answer: {answerable_count}/{len(tests)} questions ({answerable_count/len(tests):.0%})")
    
    def print_recommendations(self, answerable, questionable, likely_unanswerable):
        """Print recommendations."""
        print(f"\n💡 RECOMMENDATIONS:")
        print("="*70)
        
        total = len(answerable) + len(questionable) + len(likely_unanswerable)
        coverage_rate = len(answerable) / total if total > 0 else 0
        
        if coverage_rate >= 0.8:
            print("\n✅ EXCELLENT: Your documents can answer 80%+ of test questions")
            print("   → Proceed with evaluation as-is")
            print("   → Minor adjustments may be needed for some questions")
        
        elif coverage_rate >= 0.6:
            print("\n⚠️  GOOD: Your documents can answer 60-80% of test questions")
            print("   → Most questions will work")
            print("   → Consider:")
            if likely_unanswerable:
                print(f"      • Remove {len(likely_unanswerable)} unanswerable questions from test set")
                print("      • Or add more comprehensive GST documents")
        
        elif coverage_rate >= 0.4:
            print("\n⚠️  MODERATE: Your documents can answer 40-60% of test questions")
            print("   → Evaluation results may be misleading")
            print("   → STRONGLY RECOMMEND:")
            print("      • Add more GST documents (CGST Act, IGST Act, etc.)")
            print("      • Or filter test questions to match your documents")
        
        else:
            print("\n❌ LOW: Your documents can answer <40% of test questions")
            print("   → Test suite is NOT suitable for your current documents")
            print("   → REQUIRED ACTIONS:")
            print("      • Add comprehensive GST documents:")
            print("         - CGST Act 2017 (full)")
            print("         - CGST Rules 2017 (full)")
            print("         - IGST Act 2017")
            print("         - UTGST Act 2017")
            print("      • Or create a custom test set for your specific documents")
        
        # Missing topics
        if likely_unanswerable:
            missing_topics = set()
            for test, _, _, _ in likely_unanswerable:
                missing_topics.add(test.get('category', 'unknown'))
            
            print(f"\n📋 Missing Topic Coverage:")
            for topic in missing_topics:
                count = sum(1 for t, _, _, _ in likely_unanswerable if t.get('category') == topic)
                print(f"   • {topic.title()}: {count} questions")
        
        print("="*70)


def main():
    print("\n🔍 DOCUMENT VERIFICATION TOOL")
    print("Checking if your documents can answer the test questions...\n")
    
    verifier = DocumentVerifier()
    
    # Load PDFs
    if not verifier.load_pdfs():
        print("\n❌ Failed to load PDFs. Exiting.")
        sys.exit(1)
    
    # Verify questions
    verifier.verify_questions()
    
    print("\n" + "="*70)
    print("✅ Verification complete!")
    print("="*70)
    print("\nNext steps:")
    print("  1. Review the unanswerable questions above")
    print("  2. Either:")
    print("     a) Remove those questions from tests/test_questions.json")
    print("     b) Add more comprehensive GST documents to data/gst/")
    print("  3. Re-run this verification")
    print("  4. Then run: python tests/evaluate_assistant.py")
    print("="*70 + "\n")


if __name__ == "__main__":
    try:
        main()
    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure you have:")
        print("  1. PDF files in data/gst/")
        print("  2. tests/test_questions.json")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Verification interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

