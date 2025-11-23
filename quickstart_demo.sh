#!/bin/bash

# Quick demonstration script for the Semantic Model Data Mapper
# This script runs a complete workflow using the mortgage example

set -e

echo "🏠 Semantic Model Data Mapper - Quickstart Demo"
echo "=============================================="
echo ""

# Check if package is installed
if ! command -v rdfmap &> /dev/null; then
    echo "❌ Error: rdfmap not found. Please install the package first:"
    echo "   pip install -e ."
    exit 1
fi

# Create output directory
OUTPUT_DIR="examples/mortgage/output"
mkdir -p "$OUTPUT_DIR"

echo "📋 Step 1: Display mapping configuration info"
echo "----------------------------------------------"
rdfmap info --mapping examples/mortgage/config/mortgage_mapping.yaml
echo ""

echo "🧪 Step 2: Dry run with first 2 rows"
echo "--------------------------------------"
rdfmap convert \
  --mapping examples/mortgage/config/mortgage_mapping.yaml \
  --limit 2 \
  --dry-run \
  --verbose
echo ""

echo "🔄 Step 3: Convert all data to Turtle format"
echo "--------------------------------------------"
rdfmap convert \
  --mapping examples/mortgage/config/mortgage_mapping.yaml \
  --format ttl \
  --output "$OUTPUT_DIR/mortgage.ttl" \
  --validate \
  --report "$OUTPUT_DIR/validation_report.json" \
  --verbose
echo ""

echo "📄 Step 4: Display generated Turtle (first 20 lines)"
echo "----------------------------------------------------"
head -20 "$OUTPUT_DIR/mortgage.ttl"
echo ""

echo "✅ Step 5: Display validation report"
echo "-----------------------------------"
if [ -f "$OUTPUT_DIR/validation_report.json" ]; then
    echo "Validation report contents:"
    jq -r '.summary' "$OUTPUT_DIR/validation_report.json" 2>/dev/null || cat "$OUTPUT_DIR/validation_report.json"
else
    echo "No validation report generated (likely passed validation)"
fi
echo ""

echo "🎯 Step 6: Generate mapping from ontology and data"
echo "-------------------------------------------------"
rdfmap generate \
  --ontology examples/mortgage/ontology/mortgage_ontology.ttl \
  --data examples/mortgage/data/loans.csv \
  --class "https://example.com/mortgage#MortgageLoan" \
  --output "$OUTPUT_DIR/generated_mapping.yaml" \
  --alignment-report \
  --verbose
echo ""

echo "📊 Step 7: Show alignment report summary"
echo "---------------------------------------"
ALIGNMENT_REPORT="$OUTPUT_DIR/generated_mapping_alignment_report.json"
if [ -f "$ALIGNMENT_REPORT" ]; then
    echo "Alignment summary:"
    jq -r '.statistics | "Mapped: \(.mapped_columns)/\(.total_columns) (\(.mapping_success_rate*100 | round)%), Confidence: \(.average_confidence | . * 100 | round)%"' "$ALIGNMENT_REPORT" 2>/dev/null || echo "Generated alignment report"
else
    echo "No alignment report found"
fi
echo ""

echo "🏁 Demo Complete!"
echo "================="
echo ""
echo "Generated files:"
echo "  📄 RDF Output: $OUTPUT_DIR/mortgage.ttl"
echo "  📋 Generated Mapping: $OUTPUT_DIR/generated_mapping.yaml"
echo "  📊 Alignment Report: $OUTPUT_DIR/generated_mapping_alignment_report.json"
echo "  ✅ Validation Report: $OUTPUT_DIR/validation_report.json"
echo ""
echo "Next steps:"
echo "  • Review the generated mapping configuration"
echo "  • Examine the alignment report for improvement suggestions"
echo "  • Try the full improvement cycle: examples/demo/run_demo.py"
echo "  • Read the complete guide: WORKFLOW_GUIDE.md"
echo ""
