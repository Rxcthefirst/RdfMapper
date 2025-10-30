#!/bin/bash

# Installation script for Semantic Model Data Mapper

set -e  # Exit on error

echo "=========================================="
echo "Semantic Model Data Mapper - Installation"
echo "=========================================="
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
required_version="3.11"

if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 11) else 1)"; then
    echo "❌ Error: Python 3.11+ is required. Found: $python_version"
    exit 1
fi

echo "✓ Python version: $python_version"
echo ""

# Create virtual environment
echo "Creating virtual environment..."
if [ -d "venv" ]; then
    echo "Virtual environment already exists. Skipping creation."
else
    python3 -m venv venv
    echo "✓ Virtual environment created"
fi
echo ""

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate
echo "✓ Virtual environment activated"
echo ""

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip > /dev/null 2>&1
echo "✓ pip upgraded"
echo ""

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt
echo "✓ Dependencies installed"
echo ""

# Install package in development mode
echo "Installing rdfmap package..."
pip install -e .
echo "✓ Package installed"
echo ""

# Verify installation
echo "Verifying installation..."
if command -v rdfmap &> /dev/null; then
    echo "✓ rdfmap CLI is available"
    echo ""
    echo "=========================================="
    echo "Installation Complete!"
    echo "=========================================="
    echo ""
    echo "Quick Start:"
    echo ""
    echo "1. Run the mortgage example:"
    echo "   rdfmap convert \\"
    echo "     --mapping examples/mortgage/config/mortgage_mapping.yaml \\"
    echo "     --out ttl output/mortgage.ttl \\"
    echo "     --validate"
    echo ""
    echo "2. Run tests:"
    echo "   pytest"
    echo ""
    echo "3. View help:"
    echo "   rdfmap --help"
    echo ""
    echo "For more information, see README.md and QUICKSTART.md"
    echo ""
else
    echo "❌ Error: rdfmap command not found. Installation may have failed."
    exit 1
fi
