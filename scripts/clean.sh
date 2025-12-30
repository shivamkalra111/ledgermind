#!/bin/bash
# Clean up script - removes existing ChromaDB data

echo "Cleaning up existing ChromaDB data..."

if [ -d "chroma_db" ]; then
    echo "Found chroma_db directory"
    rm -rf chroma_db
    echo "✅ Removed chroma_db/"
else
    echo "No chroma_db directory found"
fi

echo ""
echo "Clean! You can now run:"
echo "  python scripts/ingest_pdfs.py"

