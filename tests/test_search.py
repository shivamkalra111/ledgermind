"""
Test suite for GST semantic search functionality.

Run this after ingesting PDFs to verify the system works correctly.
"""

import chromadb
from chromadb.config import Settings
import sys

def test_collection_exists():
    """Test that ChromaDB collection exists."""
    print("\n[TEST 1] Checking ChromaDB collection...")
    
    try:
        client = chromadb.Client(Settings(anonymized_telemetry=False))
        collection = client.get_collection("gst_rules")
        count = collection.count()
        
        assert count > 0, f"Collection is empty! Expected documents, got {count}"
        print(f"   ✅ PASS: Collection exists with {count} documents")
        return True
    except Exception as e:
        print(f"   ❌ FAIL: {e}")
        return False

def test_metadata_completeness():
    """Test that chunks have required metadata."""
    print("\n[TEST 2] Checking metadata completeness...")
    
    try:
        client = chromadb.Client(Settings(anonymized_telemetry=False))
        collection = client.get_collection("gst_rules")
        
        # Get a sample document
        results = collection.get(limit=1, include=['metadatas'])
        
        if not results['metadatas']:
            print("   ❌ FAIL: No metadata found")
            return False
        
        metadata = results['metadatas'][0]
        required_fields = ['source', 'page', 'chunk_index', 'section_id', 'chunking_strategy']
        
        missing = [field for field in required_fields if field not in metadata]
        
        if missing:
            print(f"   ❌ FAIL: Missing fields: {missing}")
            return False
        
        print(f"   ✅ PASS: All required metadata fields present")
        print(f"      Sample: {metadata}")
        return True
    except Exception as e:
        print(f"   ❌ FAIL: {e}")
        return False

def test_semantic_search():
    """Test semantic search with known queries."""
    print("\n[TEST 3] Testing semantic search...")
    
    test_queries = [
        {
            'query': 'How to claim Input Tax Credit?',
            'expected_terms': ['input', 'tax', 'credit', 'ITC'],
            'min_similarity': 0.6
        },
        {
            'query': 'What is reverse charge mechanism?',
            'expected_terms': ['reverse', 'charge'],
            'min_similarity': 0.6
        }
    ]
    
    try:
        client = chromadb.Client(Settings(anonymized_telemetry=False))
        collection = client.get_collection("gst_rules")
        
        passed = 0
        for test in test_queries:
            query = test['query']
            
            results = collection.query(
                query_texts=[query],
                n_results=3
            )
            
            if not results['ids'][0]:
                print(f"   ❌ FAIL: No results for '{query}'")
                continue
            
            # Check similarity score
            distance = results['distances'][0][0]
            similarity = 1 - distance
            
            if similarity < test['min_similarity']:
                print(f"   ⚠️  WARN: Low similarity for '{query}': {similarity:.3f}")
                continue
            
            # Check if results contain expected terms
            top_result = results['documents'][0][0].lower()
            has_terms = any(term in top_result for term in test['expected_terms'])
            
            if has_terms and similarity >= test['min_similarity']:
                print(f"   ✅ PASS: '{query}' (similarity: {similarity:.3f})")
                passed += 1
            else:
                print(f"   ❌ FAIL: '{query}' - results not relevant")
        
        return passed == len(test_queries)
        
    except Exception as e:
        print(f"   ❌ FAIL: {e}")
        return False

def test_chunk_quality():
    """Test that chunks are well-formed."""
    print("\n[TEST 4] Checking chunk quality...")
    
    try:
        client = chromadb.Client(Settings(anonymized_telemetry=False))
        collection = client.get_collection("gst_rules")
        
        # Sample 10 random documents
        results = collection.get(limit=10, include=['documents', 'metadatas'])
        
        issues = []
        
        for i, (doc, meta) in enumerate(zip(results['documents'], results['metadatas'])):
            # Check chunk size
            if len(doc) < 100:
                issues.append(f"Chunk {i}: Too small ({len(doc)} chars)")
            
            # Check if chunk ends mid-sentence
            if doc and doc[-1] not in '.!?"\')\n':
                issues.append(f"Chunk {i}: Broken sentence")
            
            # Check chunk size matches metadata
            if 'chunk_size' in meta and abs(len(doc) - meta['chunk_size']) > 10:
                issues.append(f"Chunk {i}: Size mismatch")
        
        if issues:
            print(f"   ⚠️  WARN: Found {len(issues)} issues:")
            for issue in issues[:3]:  # Show first 3
                print(f"      - {issue}")
            return False
        else:
            print(f"   ✅ PASS: Chunks are well-formed")
            return True
            
    except Exception as e:
        print(f"   ❌ FAIL: {e}")
        return False

def interactive_search():
    """Interactive search mode for manual testing."""
    print("\n" + "="*70)
    print("Interactive Search Mode")
    print("="*70)
    print("Type your questions (or 'quit' to exit)\n")
    
    try:
        client = chromadb.Client(Settings(anonymized_telemetry=False))
        collection = client.get_collection("gst_rules")
        
        while True:
            query = input("🔍 Question: ").strip()
            
            if query.lower() in ['quit', 'exit', 'q']:
                break
            
            if not query:
                continue
            
            results = collection.query(query_texts=[query], n_results=2)
            
            if results['ids'][0]:
                print(f"\n{'─'*70}")
                for i in range(min(2, len(results['ids'][0]))):
                    doc = results['documents'][0][i]
                    meta = results['metadatas'][0][i]
                    similarity = 1 - results['distances'][0][i]
                    
                    print(f"Result {i+1} (similarity: {similarity:.3f})")
                    print(f"Source: {meta.get('source', 'N/A')} | Page: {meta.get('page', 'N/A')}")
                    print(f"Section: {meta.get('section_id', 'N/A')}")
                    print(f"\n{doc[:300]}...\n")
                print('─'*70 + '\n')
            else:
                print("❌ No results found\n")
                
    except KeyboardInterrupt:
        print("\n")
    except Exception as e:
        print(f"\n❌ Error: {e}\n")

def run_all_tests():
    """Run all tests and report results."""
    print("="*70)
    print("GST Search System - Test Suite")
    print("="*70)
    
    tests = [
        test_collection_exists,
        test_metadata_completeness,
        test_semantic_search,
        test_chunk_quality
    ]
    
    results = []
    for test_func in tests:
        try:
            result = test_func()
            results.append(result)
        except Exception as e:
            print(f"\n   ❌ ERROR: {e}")
            results.append(False)
    
    # Summary
    passed = sum(results)
    total = len(results)
    
    print("\n" + "="*70)
    print("Test Summary")
    print("="*70)
    print(f"Passed: {passed}/{total}")
    print(f"Failed: {total - passed}/{total}")
    
    if passed == total:
        print("\n✅ All tests passed! System is working correctly.")
        return True
    else:
        print("\n⚠️  Some tests failed. Check the output above.")
        return False

def main():
    """Main entry point."""
    import sys
    
    # Check if collection exists
    try:
        client = chromadb.Client(Settings(anonymized_telemetry=False))
        collection = client.get_collection("gst_rules")
        count = collection.count()
        
        if count == 0:
            print("❌ No documents in collection!")
            print("\nRun the ingestion script first:")
            print("  python scripts/ingest_pdfs.py")
            sys.exit(1)
            
    except Exception as e:
        print("❌ ChromaDB collection not found!")
        print("\nRun the ingestion script first:")
        print("  python scripts/ingest_pdfs.py")
        sys.exit(1)
    
    # Run tests
    all_passed = run_all_tests()
    
    # Offer interactive mode
    if all_passed:
        print("\n" + "="*70)
        response = input("Try interactive search? (y/n): ").strip().lower()
        if response in ['y', 'yes']:
            interactive_search()
    
    sys.exit(0 if all_passed else 1)

if __name__ == "__main__":
    main()
