#!/usr/bin/env python3
"""Debug object detection logic."""

import sys
sys.path.insert(0, 'src')

from rdfmap.generator.ontology_analyzer import OntologyAnalyzer
from rdfmap.generator.data_analyzer import DataSourceAnalyzer

# Load
ontology = OntologyAnalyzer('examples/mortgage/ontology/mortgage.ttl')
data = DataSourceAnalyzer('examples/mortgage/data/loans.csv')

# Get Borrower class
borrower_class = None
for cls in ontology.classes.values():
    if 'Borrower' in str(cls.label):
        borrower_class = cls
        break

print(f"Borrower class: {borrower_class.label}")
print(f"Borrower URI: {borrower_class.uri}")

# Get properties
props = ontology.get_datatype_properties(borrower_class.uri)
print(f"\nBorrower properties ({len(props)}):")
for prop in props:
    print(f"  - {prop.label}: {prop.uri}")

# Test each column
print("\n" + "="*80)
print("Testing columns against Borrower class:")
print("="*80)

class_name = borrower_class.label.lower()
print(f"Class name (lowercase): '{class_name}'")

for col_name in data.get_column_names():
    col_lower = col_name.lower()

    # Check if column contains class name
    contains_class = class_name in col_lower

    # Check if any property contains class name
    prop_match = any(class_name in prop.label.lower() if prop.label else False for prop in props)

    print(f"\n{col_name}:")
    print(f"  - Contains '{class_name}'? {contains_class}")
    print(f"  - Matches property with '{class_name}'? {prop_match}")
    print(f"  - Would be assigned to Borrower? {contains_class or prop_match}")

