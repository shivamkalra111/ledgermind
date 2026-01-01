#!/usr/bin/env python3
"""
Quick script to view RAG performance metrics.

Usage:
  python view_metrics.py          # All metrics
  python view_metrics.py --last 10  # Last 10 queries
"""

import argparse
from pathlib import Path
from rag.metrics import RAGMetrics


def main():
    parser = argparse.ArgumentParser(description='View RAG performance metrics')
    parser.add_argument(
        '--last', 
        type=int, 
        default=None,
        help='Show only last N queries'
    )
    parser.add_argument(
        '--file',
        type=str,
        default='rag_metrics.jsonl',
        help='Path to metrics file'
    )
    
    args = parser.parse_args()
    
    # Check if file exists
    if not Path(args.file).exists():
        print(f"❌ Metrics file not found: {args.file}")
        print("\nNo metrics collected yet. Run some queries first:")
        print("  python main.py \"What is CGST?\"")
        return
    
    # Load and display metrics
    metrics = RAGMetrics(log_file=args.file)
    metrics.print_summary(last_n=args.last)
    
    # Show file location
    print(f"\n📁 Metrics saved to: {Path(args.file).absolute()}")
    print("   Each query is logged for performance tracking.\n")


if __name__ == "__main__":
    main()

