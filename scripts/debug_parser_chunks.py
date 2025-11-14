#!/usr/bin/env python3
"""Quick test to verify CSV parser is reading all chunks."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.rdfmap.parsers.data_source import create_parser

# Test with the 100k file
file_path = Path("test_data/benchmark_100000.csv")

if not file_path.exists():
    print(f"File not found: {file_path}")
    sys.exit(1)

print(f"Testing parser with {file_path.name}")
print("=" * 50)

parser = create_parser(file_path)
total_rows = 0
chunk_num = 0

for chunk in parser.parse(chunk_size=25000):
    chunk_num += 1
    rows_in_chunk = len(chunk)
    total_rows += rows_in_chunk
    print(f"Chunk {chunk_num}: {rows_in_chunk:,} rows (total: {total_rows:,})")

print(f"\nTotal rows parsed: {total_rows:,}")
print(f"Expected: 100,000")
print(f"Match: {'✓' if total_rows == 100000 else '✗'}")

