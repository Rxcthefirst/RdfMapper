#!/bin/bash

# Quick demo script for the mortgage example

set -e

echo "=========================================="
echo "Semantic Model Data Mapper - Quick Demo"
echo "=========================================="
echo ""

# Check if package is installed
if ! command -v rdfmap &> /dev/null; then
    echo "❌ Error: rdfmap not found. Please run ./install.sh first"
    exit 1
fi

# Create output directory
mkdir -p output

echo "Step 1: Display mapping configuration info"
echo "------------------------------------------"
rdfmap info --mapping examples/mortgage/config/mortgage_mapping.yaml
echo ""

echo "Step 2: Dry run with first 2 rows"
echo "------------------------------------------"
rdfmap convert \
  --mapping examples/mortgage/config/mortgage_mapping.yaml \
  --limit 2 \
  --dry-run \
  --verbose
echo ""

echo "Step 3: Convert all data to Turtle and JSON-LD"
echo "------------------------------------------"
rdfmap convert \
  --mapping examples/mortgage/config/mortgage_mapping.yaml \
  --out ttl output/mortgage.ttl \
  --out jsonld output/mortgage.jsonld \
  --validate \
  --report output/validation_report.json \
  --verbose
echo ""

echo "Step 4: Display generated Turtle (first 50 lines)"
echo "------------------------------------------"
head -50 output/mortgage.ttl
echo ""

echo "Step 5: Display validation report"
echo "------------------------------------------"
if [ -f output/validation_report.json ]; then
    cat output/validation_report.json | python -m json.tool
else
    echo "No validation report generated"
fi
echo ""

echo "=========================================="
echo "Demo Complete!"
echo "=========================================="
echo ""
echo "Generated files:"
echo "  - output/mortgage.ttl (Turtle format)"
echo "  - output/mortgage.jsonld (JSON-LD format)"
echo "  - output/validation_report.json (Validation report)"
echo ""
echo "Explore the examples/mortgage/ directory to see:"
echo "  - Input data (data/loans.csv)"
echo "  - Ontology (ontology/mortgage.ttl)"
echo "  - Mapping config (config/mortgage_mapping.yaml)"
echo "  - SHACL shapes (shapes/mortgage_shapes.ttl)"
echo ""
