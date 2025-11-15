#!/usr/bin/env python3
"""Test the interactive review feature."""

import sys
import subprocess
from pathlib import Path

sys.path.insert(0, 'src')

print("="*80)
print("Testing Interactive Review Feature")
print("="*80)

# First, generate a mapping with alignment report
print("\n1. Generating mapping with alignment report...")
result = subprocess.run([
    sys.executable, '-m', 'rdfmap', 'generate',
    '--ontology', 'examples/mortgage/ontology/mortgage.ttl',
    '--data', 'examples/mortgage/data/loans.csv',
    '--output', 'test_review_mapping.yaml',
    '--report'
], capture_output=True, text=True)

if result.returncode != 0:
    print(f"Error generating mapping: {result.stderr}")
    sys.exit(1)

print("✓ Mapping generated")
print("✓ Files created:")
print("  - test_review_mapping.yaml")
print("  - test_review_mapping_alignment.json")
print("  - test_review_mapping_alignment.html")

# Now show how to run the review command
print("\n2. To review the mapping interactively, run:")
print("   python -m rdfmap review --mapping test_review_mapping.yaml")
print("\n   Or with alignment report:")
print("   python -m rdfmap review \\")
print("     --mapping test_review_mapping.yaml \\")
print("     --alignment test_review_mapping_alignment.json")

print("\n3. The review interface will guide you through:")
print("   • Viewing each column mapping with confidence scores")
print("   • Accepting (y), rejecting (n), or modifying (m) each mapping")
print("   • Choosing from alternatives when available")
print("   • Saving the reviewed configuration")

print("\n✓ Test setup complete!")
print("\nReady to test interactively? Run the command above.")

