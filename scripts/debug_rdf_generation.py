#!/usr/bin/env python3
"""Debug why benchmark only processes one chunk."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.rdfmap.parsers.data_source import create_parser
from src.rdfmap.emitter.graph_builder import RDFGraphBuilder
from src.rdfmap.models.errors import ProcessingReport
from scripts.benchmark_scaling import create_test_mapping

# Test with the 100k file
file_path = Path("test_data/benchmark_100000.csv")
config = create_test_mapping(file_path)

print(f"Testing RDF generation with {file_path.name}")
print("=" * 50)

report = ProcessingReport()
builder = RDFGraphBuilder(config, report)

parser = create_parser(file_path)
chunk_num = 0
row_offset = 0
for chunk in parser.parse(chunk_size=25000):
    chunk_num += 1
    print(f"Processing chunk {chunk_num}: {len(chunk):,} rows (offset: {row_offset})")
    builder.add_dataframe(chunk, config.sheets[0], offset=row_offset)
    row_offset += len(chunk)

graph = builder.get_graph()
print(f"\nTotal chunks processed: {chunk_num}")
print(f"Total rows in report: {report.total_rows:,}")
print(f"Total triples generated: {len(graph):,}")
print(f"Expected triples: ~1,200,000 (12 per row)")

