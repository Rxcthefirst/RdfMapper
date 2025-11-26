#!/bin/bash
#
# Quick data generator wrapper script
# Usage: ./generate_test_data.sh [size] [output]
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/generate_large_dataset.py"

# Default values
SIZE=${1:-500000}
OUTPUT=${2:-"examples/mortgage/data/loans_${SIZE}.csv"}

echo "============================================"
echo "  Large Dataset Generator"
echo "============================================"
echo ""
echo "Generating: $SIZE rows"
echo "Output:     $OUTPUT"
echo ""

# Check if polars is installed
if ! python3 -c "import polars" 2>/dev/null; then
    echo "⚠️  Polars not found. Installing..."
    pip install polars numpy
    echo ""
fi

# Run the generator
python3 "$PYTHON_SCRIPT" \
    --rows "$SIZE" \
    --output "$OUTPUT" \
    --sample 5

echo ""
echo "✅ Done! Generated $OUTPUT"
echo ""
echo "Next steps:"
echo "  1. Test mapping generation:"
echo "     rdfmap generate --ontology examples/mortgage/ontology/mortgage_ontology.ttl --data $OUTPUT"
echo ""
echo "  2. Test conversion:"
echo "     rdfmap convert --mapping mapping_config.yaml --limit $SIZE"
echo ""

