"""
LedgerMind - GST Compliance Assistant
Main entry point for the application
"""

from rag.pipeline import RAGPipeline
import sys


def main():
    """Main application entry point."""
    print("="*70)
    print("🧾 LedgerMind - GST Compliance Assistant")
    print("="*70)
    print("\nInitializing system...\n")
    
    try:
        # Initialize RAG pipeline
        pipeline = RAGPipeline()
        
        # Check if question provided as command-line argument
        if len(sys.argv) > 1:
            # Single question mode
            question = " ".join(sys.argv[1:])
            print(f"\nProcessing question: {question}\n")
            
            result = pipeline.answer(question)
            
            # Display result
            print("\n" + "="*70)
            print(f"Question: {result['question']}")
            print("="*70)
            print(f"\n{result['answer']}\n")
            print("="*70)
            print("Sources:")
            for i, source in enumerate(result['sources'], 1):
                print(f"  {i}. {source}")
            print("="*70)
            print(f"\nConfidence: {result['confidence']:.0%}")
            print(f"Faithfulness: {result.get('faithfulness', 0):.0%}")
            print(f"Relevance: {result.get('relevance', 0):.0%}")
            print(f"Chunks used: {result['chunks_used']}")
            print(f"Time taken: {result['time_taken']:.2f}s")
            print("="*70)
        else:
            # Interactive chat mode
            pipeline.chat()
    
    except KeyboardInterrupt:
        print("\n\n👋 Interrupted by user. Goodbye!")
    except ConnectionError as e:
        print(f"\n❌ Connection Error: {e}")
        print("\nMake sure Ollama is running:")
        print("  1. Terminal 1: ollama serve")
        print("  2. Terminal 2: ollama pull qwen2.5:7b-instruct")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

