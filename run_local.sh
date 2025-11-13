#!/bin/bash
# Quick start script for local BISG label generator

echo "============================================================"
echo "🏷️  BISG Label Generator - Local Setup"
echo "============================================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    echo "❌ Error: Python is not installed"
    echo "   Please install Python 3.9 or higher"
    exit 1
fi

# Determine Python command
if command -v python3 &> /dev/null; then
    PYTHON_CMD=python3
else
    PYTHON_CMD=python
fi

echo "✅ Python found: $($PYTHON_CMD --version)"
echo ""

# Check if dependencies are installed
echo "📦 Checking dependencies..."
if ! $PYTHON_CMD -c "import flask" 2>/dev/null; then
    echo "⚠️  Dependencies not installed. Installing now..."
    $PYTHON_CMD -m pip install -r requirements_local.txt
    echo ""
else
    echo "✅ Dependencies already installed"
    echo ""
fi

# Run the application
echo "🚀 Starting local label generator..."
echo ""
$PYTHON_CMD local_app.py
