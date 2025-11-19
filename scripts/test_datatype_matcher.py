#!/usr/bin/env python3
"""Direct test of DataTypeMatcher to verify confidence cap."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from rdfmap.generator.matchers.datatype_matcher import DataTypeInferenceMatcher
from rdfmap.generator.data_analyzer import DataFieldAnalysis
from rdfmap.generator.ontology_analyzer import OntologyProperty
from rdflib import URIRef

# Create test column
column = DataFieldAnalysis(name='LoanID')
column.inferred_type = 'string'
column.sample_values = ['L-1001', 'L-1002', 'L-1003']
column.is_identifier = True
column.is_foreign_key = False

# Create test property
prop = OntologyProperty(
    uri=URIRef('http://example.org/loanNumber'),
    label='loanNumber',
    comment='Unique loan identifier',
    domain=None,
    range_type=URIRef('http://www.w3.org/2001/XMLSchema#string'),
    is_object_property=False,
    pref_label='Loan Number',
    alt_labels=[],
    hidden_labels=[]
)

# Test matcher
matcher = DataTypeInferenceMatcher(threshold=0.75)
result = matcher.match(column, [prop])

print("="*70)
print("DataTypeMatcher Direct Test")
print("="*70)
print(f"Column: {column.name}")
print(f"Property: {prop.label}")
print(f"Result: {result}")
if result:
    print(f"Confidence: {result.confidence:.3f}")
    print(f"Expected: ≤ 0.95 (should be capped)")
    if result.confidence > 0.95:
        print("❌ FAIL: Confidence exceeds 0.95 cap!")
        sys.exit(1)
    else:
        print("✅ PASS: Confidence properly capped")
        sys.exit(0)
else:
    print("❌ FAIL: No match found")
    sys.exit(1)

