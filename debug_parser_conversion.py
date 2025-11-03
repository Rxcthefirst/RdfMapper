#!/usr/bin/env python3

from pathlib import Path
from src.rdfmap.parsers.data_source import create_parser

# Debug what the parser returns during conversion
parser = create_parser(Path('examples/owl2_rdfxml_demo/data/students_nested.json'))

print("Debugging JSONParser during conversion...")
print("=" * 50)

for df in parser.parse():
    print(f"DataFrame shape: {df.shape}")
    print(f"Columns: {list(df.columns)}")
    print()

    # Check if we have the expected flattened fields
    expected_fields = ['courses.course_code', 'courses.course_title', 'courses.grade', 'courses.semester']

    print("Expected course fields check:")
    for field in expected_fields:
        exists = field in df.columns
        print(f"  {field}: {'✓' if exists else '❌'}")

    print()
    print("First few rows of data:")
    print(df[['student_id', 'courses.course_code', 'courses.course_title']].head() if 'courses.course_code' in df.columns else df[['student_id']].head())

    print()
    print("Raw 'courses' column (if exists):")
    if 'courses' in df.columns:
        print(f"Type: {type(df['courses'].iloc[0])}")
        print(f"Sample: {df['courses'].iloc[0]}")
    else:
        print("No 'courses' column found")
