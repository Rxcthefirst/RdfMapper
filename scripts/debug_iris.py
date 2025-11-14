#!/usr/bin/env python3
"""Debug to see what IRIs are being generated."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.rdfmap.parsers.data_source import create_parser

# Test with the 100k file
file_path = Path("test_data/benchmark_100000.csv")

parser = create_parser(file_path)
chunk_num = 0

for chunk in parser.parse(chunk_size=25000):
    chunk_num += 1

    # Show first 3 IDs from each chunk
    ids = chunk['ID'].head(3).to_list()
    print(f"Chunk {chunk_num}: First 3 IDs = {ids}")

    if chunk_num >= 4:
        break

print("\nThis shows that each chunk has DIFFERENT IDs (EMP000000, EMP000001...)")
print("So the issue must be elsewhere...")

