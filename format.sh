#!/bin/bash

# Simple script to run pre-commit checks manually
# This runs exactly what the pre-commit hooks run

echo "🎨 Running pre-commit checks..."
echo "================================"

# Run pre-commit on all files
pre-commit run --all-files

echo ""
echo "✅ Done! Pre-commit checks completed."
