#!/usr/bin/env python3

from src.rdfmap.generator.data_analyzer import DataSourceAnalyzer

# Test the enhanced array handling
print("Testing Enhanced Nested JSON Processing with Arrays...")
print("=" * 60)

analyzer = DataSourceAnalyzer('examples/owl2_rdfxml_demo/data/students_nested.json')

print(f'Data format: {analyzer.data_format}')
print(f'Total rows (after expansion): {analyzer.total_rows}')
print(f'Fields detected: {len(analyzer.field_analyses)}')
print()

print('Detected fields:')
for field_name in sorted(analyzer.get_column_names())[:10]:  # Show first 10
    analysis = analyzer.get_analysis(field_name)
    print(f'  {field_name}: {analysis.inferred_type}')

print()
print('Course-related fields now available:')
course_fields = [f for f in analyzer.get_column_names() if 'course' in f.lower()]
for field in course_fields:
    print(f'  ✓ {field}')

print()
print('Personal info fields:')
personal_fields = [f for f in analyzer.get_column_names() if 'personal_info' in f]
for field in personal_fields:
    print(f'  ✓ {field}')
