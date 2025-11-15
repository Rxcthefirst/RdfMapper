#!/usr/bin/env python3

import json
from src.rdfmap.parsers.data_source import JSONParser
from pathlib import Path

# Test the JSONParser directly
parser = JSONParser(Path('examples/owl2_rdfxml_demo/data/students_nested.json'))

print("Testing JSONParser with array expansion...")
print("=" * 50)

# Get the parsed DataFrame
for df in parser.parse():
    print(f"DataFrame shape: {df.shape}")
    print(f"Columns: {df.columns.tolist()}")
    print()
    print("First few rows:")
    print(df[['student_id', 'courses.course_code', 'courses.course_title']].head())
    print()

    # Check for duplicated student IDs (indicating expansion worked)
    student_counts = df['student_id'].value_counts()
    print("Student ID counts (should show expansion):")
    print(student_counts)
    print()

    # Show sample course data
    print("Sample course data:")
    for idx, row in df.iterrows():
        print(f"Student {row['student_id']}: {row['courses.course_code']} - {row['courses.course_title']}")
        if idx >= 5:  # Show first 6 records
            break
