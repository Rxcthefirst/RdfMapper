#!/usr/bin/env python3

from pathlib import Path
from src.rdfmap.parsers.data_source import create_parser

# Debug what get_column_names returns vs what parse returns
parser = create_parser(Path('../examples/owl2_rdfxml_demo/data/students_nested.json'))

print("Debugging get_column_names vs parse methods...")
print("=" * 50)

print("get_column_names() returns:")
column_names = parser.get_column_names()
print(column_names)
print(f"Count: {len(column_names)}")

print("\nparse() DataFrame columns:")
for df in parser.parse():
    parse_columns = list(df.columns)
    print(parse_columns)
    print(f"Count: {len(parse_columns)}")
    break

print("\nComparison:")
print("Fields in get_column_names but NOT in parse:")
for col in column_names:
    if col not in parse_columns:
        print(f"  - {col}")

print("\nFields in parse but NOT in get_column_names:")
for col in parse_columns:
    if col not in column_names:
        print(f"  + {col}")
