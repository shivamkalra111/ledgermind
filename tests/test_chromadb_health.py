#!/usr/bin/env python3
"""
ChromaDB Health Check Script

Tests if your ChromaDB database is healthy and properly configured.
Run this after ingestion to verify everything is working.
"""

import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import EMBEDDING_MODEL, CHROMA_DB_PATH, CHROMA_COLLECTION_NAME


def test_1_connection():
    """Test 1: Can we connect to ChromaDB?"""
    print("\n" + "="*70)
    print("TEST 1: ChromaDB Connection")
    print("="*70)
    
    try:
        client = chromadb.PersistentClient(
            path=CHROMA_DB_PATH,
            settings=Settings(anonymized_telemetry=False, allow_reset=True)
        )
        print("✅ PASS: Successfully connected to ChromaDB")
        return client
    except Exception as e:
        print(f"❌ FAIL: Cannot connect to ChromaDB")
        print(f"   Error: {e}")
        return None


def test_2_collection_exists(client):
    """Test 2: Does the collection exist?"""
    print("\n" + "="*70)
    print("TEST 2: Collection Exists")
    print("="*70)
    
    try:
        embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=EMBEDDING_MODEL
        )
        
        collection = client.get_collection(
            name=CHROMA_COLLECTION_NAME,
            embedding_function=embedding_function
        )
        
        count = collection.count()
        print(f"✅ PASS: Collection '{CHROMA_COLLECTION_NAME}' exists")
        print(f"   Documents: {count}")
        
        if count == 0:
            print("⚠️  WARNING: Collection is empty!")
            return None
        
        return collection
    except Exception as e:
        print(f"❌ FAIL: Collection does not exist or cannot be loaded")
        print(f"   Error: {e}")
        return None


def test_3_basic_query(collection):
    """Test 3: Can we perform a basic query without errors?"""
    print("\n" + "="*70)
    print("TEST 3: Basic Query")
    print("="*70)
    
    try:
        # Try a simple query
        results = collection.query(
            query_texts=["GST tax rules"],
            n_results=5
        )
        
        print("✅ PASS: Query executed successfully")
        print(f"   Results returned: {len(results['documents'][0])}")
        
        # Check if we got valid results
        if len(results['documents'][0]) == 0:
            print("⚠️  WARNING: Query returned no results")
            return False
        
        return results
    except Exception as e:
        print(f"❌ FAIL: Query failed")
        print(f"   Error: {e}")
        
        # Check if it's the corruption error
        if "range start index" in str(e) or "PanicException" in str(e):
            print("\n🚨 CRITICAL: This is a DATABASE CORRUPTION error!")
            print("   You need to re-ingest the database.")
        
        return None


def test_4_metadata_integrity(collection):
    """Test 4: Do documents have proper metadata?"""
    print("\n" + "="*70)
    print("TEST 4: Metadata Integrity")
    print("="*70)
    
    try:
        # Get a sample of documents
        sample = collection.get(limit=10, include=['metadatas'])
        
        if not sample['metadatas']:
            print("❌ FAIL: No metadata found")
            return False
        
        # Check required fields
        required_fields = ['source', 'page', 'document_type', 'chunk_index']
        optional_fields = ['section_id', 'document_title', 'section_title']
        
        missing_fields = set()
        samples_checked = min(10, len(sample['metadatas']))
        
        for meta in sample['metadatas'][:samples_checked]:
            for field in required_fields:
                if field not in meta:
                    missing_fields.add(field)
        
        if missing_fields:
            print(f"⚠️  WARNING: Missing required fields: {missing_fields}")
        else:
            print(f"✅ PASS: All required metadata fields present")
            print(f"   Checked {samples_checked} documents")
        
        # Show sample metadata
        print("\n   Sample metadata:")
        first_meta = sample['metadatas'][0]
        for key, value in list(first_meta.items())[:8]:
            print(f"     {key}: {value}")
        
        return True
        
    except Exception as e:
        print(f"❌ FAIL: Cannot check metadata")
        print(f"   Error: {e}")
        return False


def test_5_embedding_dimensions(collection):
    """Test 5: Are embeddings the correct dimension?"""
    print("\n" + "="*70)
    print("TEST 5: Embedding Dimensions")
    print("="*70)
    
    try:
        # Get one document with embeddings
        result = collection.get(limit=1, include=['embeddings'])
        
        if not result['embeddings'] or len(result['embeddings']) == 0:
            print("⚠️  WARNING: Cannot retrieve embeddings")
            return False
        
        embedding = result['embeddings'][0]
        dimension = len(embedding)
        
        expected_dim = 1024  # bge-large-en-v1.5
        
        if dimension == expected_dim:
            print(f"✅ PASS: Embeddings are correct dimension")
            print(f"   Dimension: {dimension} (bge-large-en-v1.5)")
        else:
            print(f"❌ FAIL: Wrong embedding dimension")
            print(f"   Expected: {expected_dim}")
            print(f"   Got: {dimension}")
            if dimension == 384:
                print("   ⚠️  You're using bge-small (384) instead of bge-large (1024)")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ FAIL: Cannot check embeddings")
        print(f"   Error: {e}")
        return False


def test_6_semantic_search_quality(collection):
    """Test 6: Does semantic search return relevant results?"""
    print("\n" + "="*70)
    print("TEST 6: Semantic Search Quality")
    print("="*70)
    
    test_queries = [
        {
            'query': "What is Input Tax Credit?",
            'expected_keywords': ["input", "tax", "credit", "itc"],
            'min_similarity': 0.30
        },
        {
            'query': "Section 16 conditions",
            'expected_keywords': ["section", "16"],
            'min_similarity': 0.25
        }
    ]
    
    passed = 0
    
    for i, test in enumerate(test_queries, 1):
        print(f"\n   Query {i}: '{test['query']}'")
        
        try:
            results = collection.query(
                query_texts=[test['query']],
                n_results=3
            )
            
            if not results['documents'][0]:
                print(f"   ❌ No results returned")
                continue
            
            # Calculate similarity (1 - distance)
            top_similarity = 1 - results['distances'][0][0]
            
            # Check keywords
            top_doc = results['documents'][0][0].lower()
            keywords_found = sum(1 for kw in test['expected_keywords'] if kw in top_doc)
            
            print(f"   Top similarity: {top_similarity:.2%}")
            print(f"   Keywords found: {keywords_found}/{len(test['expected_keywords'])}")
            
            if top_similarity >= test['min_similarity'] and keywords_found >= 2:
                print(f"   ✅ PASS")
                passed += 1
            else:
                print(f"   ⚠️  Low quality (similarity < {test['min_similarity']:.0%} or few keywords)")
        
        except Exception as e:
            print(f"   ❌ FAIL: {e}")
    
    print(f"\n{'✅' if passed == len(test_queries) else '⚠️ '} Overall: {passed}/{len(test_queries)} queries passed")
    return passed == len(test_queries)


def test_7_chunk_quality(collection):
    """Test 7: Are chunks well-formed (complete sentences, proper size)?"""
    print("\n" + "="*70)
    print("TEST 7: Chunk Quality")
    print("="*70)
    
    try:
        # Get sample documents
        sample = collection.get(limit=20, include=['documents', 'metadatas'])
        
        issues = {
            'too_short': 0,
            'too_long': 0,
            'no_content': 0,
            'broken_sentence': 0
        }
        
        for i, doc in enumerate(sample['documents']):
            length = len(doc)
            
            # Check length (considering context enrichment adds ~150 chars)
            if length < 150:
                issues['too_short'] += 1
            elif length > 1500:
                issues['too_long'] += 1
            
            # Check if empty or just whitespace
            if not doc.strip():
                issues['no_content'] += 1
            
            # Check if ends with proper punctuation (allowing for legal text endings)
            # Legal text can end with: . , ; : ) numbers, etc.
            if doc.strip() and not doc.strip()[-1] in '.,:;)0123456789]"\'':
                issues['broken_sentence'] += 1
        
        total_issues = sum(issues.values())
        
        if total_issues == 0:
            print(f"✅ PASS: All {len(sample['documents'])} chunks are well-formed")
        else:
            print(f"⚠️  Issues found in {total_issues}/{len(sample['documents'])} chunks:")
            for issue_type, count in issues.items():
                if count > 0:
                    print(f"   - {issue_type}: {count}")
        
        # Show sample chunk
        print("\n   Sample chunk:")
        sample_chunk = sample['documents'][0]
        print(f"   Length: {len(sample_chunk)} chars")
        print(f"   Preview: {sample_chunk[:200]}...")
        
        return total_issues < len(sample['documents']) * 0.1  # Allow up to 10% issues
        
    except Exception as e:
        print(f"❌ FAIL: Cannot check chunk quality")
        print(f"   Error: {e}")
        return False


def test_8_context_enrichment(collection):
    """Test 8: Do chunks have context enrichment?"""
    print("\n" + "="*70)
    print("TEST 8: Context Enrichment (Enhanced Chunking)")
    print("="*70)
    
    try:
        # Get sample documents
        sample = collection.get(limit=5, include=['documents', 'metadatas'])
        
        enriched_count = 0
        
        for doc, meta in zip(sample['documents'], sample['metadatas']):
            # Check if chunk has context enrichment indicators
            has_document_title = 'document_title' in meta and meta['document_title']
            has_section_info = 'section_id' in meta or 'section_title' in meta
            
            # Check if document text starts with context (optional since context may be in metadata only)
            # has_text_context = doc.startswith('Document:') or 'Document:' in doc[:200]
            
            if has_document_title or has_section_info:
                enriched_count += 1
        
        percentage = (enriched_count / len(sample['documents'])) * 100
        
        if percentage >= 80:
            print(f"✅ PASS: {enriched_count}/{len(sample['documents'])} chunks have context enrichment ({percentage:.0f}%)")
            print(f"   ✅ Enhanced chunking is working!")
        elif percentage >= 50:
            print(f"⚠️  PARTIAL: {enriched_count}/{len(sample['documents'])} chunks enriched ({percentage:.0f}%)")
            print(f"   Some chunks may be from old ingestion")
        else:
            print(f"❌ FAIL: Only {enriched_count}/{len(sample['documents'])} chunks enriched ({percentage:.0f}%)")
            print(f"   ❌ Enhanced chunking may not be working properly")
            return False
        
        # Show example
        print("\n   Sample enriched metadata:")
        first_meta = sample['metadatas'][0]
        for key in ['document_title', 'section_id', 'section_title', 'source', 'page']:
            if key in first_meta:
                value = first_meta[key]
                print(f"     {key}: {value}")
        
        return percentage >= 80
        
    except Exception as e:
        print(f"❌ FAIL: Cannot check context enrichment")
        print(f"   Error: {e}")
        return False


def run_all_tests():
    """Run all health checks."""
    print("="*70)
    print("🔍 CHROMADB HEALTH CHECK")
    print("="*70)
    print(f"Database: {CHROMA_DB_PATH}")
    print(f"Collection: {CHROMA_COLLECTION_NAME}")
    print(f"Embedding Model: {EMBEDDING_MODEL}")
    
    results = {}
    
    # Test 1: Connection
    client = test_1_connection()
    results['connection'] = client is not None
    if not client:
        print("\n🚨 CRITICAL: Cannot proceed without database connection")
        return results
    
    # Test 2: Collection exists
    collection = test_2_collection_exists(client)
    results['collection'] = collection is not None
    if not collection:
        print("\n🚨 CRITICAL: Cannot proceed without collection")
        return results
    
    # Test 3: Basic query (CORRUPTION CHECK)
    query_result = test_3_basic_query(collection)
    results['query'] = query_result is not None
    if query_result is None:
        print("\n🚨 CRITICAL: Database is CORRUPTED! Re-ingest required.")
        return results
    
    # Test 4-8: Quality checks
    results['metadata'] = test_4_metadata_integrity(collection)
    results['embeddings'] = test_5_embedding_dimensions(collection)
    results['search_quality'] = test_6_semantic_search_quality(collection)
    results['chunk_quality'] = test_7_chunk_quality(collection)
    results['context_enrichment'] = test_8_context_enrichment(collection)
    
    # Final summary
    print("\n" + "="*70)
    print("📊 FINAL SUMMARY")
    print("="*70)
    
    passed = sum(results.values())
    total = len(results)
    
    print(f"\nTests Passed: {passed}/{total}\n")
    
    for test_name, passed_test in results.items():
        status = "✅" if passed_test else "❌"
        print(f"  {status} {test_name.replace('_', ' ').title()}")
    
    print("\n" + "="*70)
    
    if passed == total:
        print("✅ ALL TESTS PASSED! Your ChromaDB is healthy!")
        print("\n🎯 Ready to run:")
        print("   python tests/evaluate_assistant.py --limit 10")
    elif passed >= total - 2:
        print("⚠️  MOSTLY GOOD with minor issues")
        print("\n💡 Consider re-ingesting if search quality is poor")
    else:
        print("❌ CRITICAL ISSUES FOUND")
        
        if not results.get('query'):
            print("\n🚨 DATABASE IS CORRUPTED!")
            print("\n🔧 Fix:")
            print("   rm -rf chroma_db/")
            print("   python scripts/ingest_pdfs.py")
        elif not results.get('context_enrichment'):
            print("\n⚠️  Enhanced chunking not detected")
            print("\n🔧 Fix:")
            print("   Make sure you ran: pip install nltk")
            print("   Then re-ingest: python scripts/ingest_pdfs.py")
        else:
            print("\n🔧 Recommended:")
            print("   rm -rf chroma_db/")
            print("   python scripts/ingest_pdfs.py")
    
    print("="*70)
    
    return results


if __name__ == "__main__":
    results = run_all_tests()
    
    # Exit code: 0 if all pass, 1 otherwise
    sys.exit(0 if all(results.values()) else 1)

