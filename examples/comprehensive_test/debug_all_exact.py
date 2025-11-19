#!/usr/bin/env python3
"""Debug script to see what all matchers return for specific columns."""

from rdfmap.generator.mapping_generator import MappingGenerator, GeneratorConfig
from rdfmap.generator.matchers import (
    ExactPrefLabelMatcher,
    ExactRdfsLabelMatcher,
    ExactAltLabelMatcher,
    ExactHiddenLabelMatcher,
    ExactLocalNameMatcher,
)

print("="*80)
print("DETAILED MATCHER DEBUG")
print("="*80)

gen = MappingGenerator(
    ontology_file='examples/comprehensive_test/hr_ontology.ttl',
    data_file='examples/comprehensive_test/employees.csv',
    config=GeneratorConfig(
        base_iri='http://example.org/employees/',
        imports=['examples/comprehensive_test/hr_vocabulary.ttl']
    )
)

# Test columns
test_columns = [
    "Employee ID",  # Should match via ExactPrefLabelMatcher
    "Full Name",    # Should match via ExactRdfsLabelMatcher
    "Birth Date",   # Should match via ExactAltLabelMatcher
    "emp_num",      # Should match via ExactHiddenLabelMatcher
]

# Get all properties for Employee class
employee_class = None
for cls_uri, cls in gen.ontology.classes.items():
    if 'Employee' in str(cls_uri):
        employee_class = cls
        break

properties = gen.ontology.get_datatype_properties(employee_class.uri)
print(f"\nTotal properties available for Employee: {len(properties)}")
print(f"Properties with SKOS labels:")
for prop in properties:
    if prop.pref_label or prop.alt_labels or prop.hidden_labels:
        print(f"  {str(prop.uri).split('#')[-1]}:")
        if prop.pref_label:
            print(f"    prefLabel: '{prop.pref_label}'")
        if prop.alt_labels:
            print(f"    altLabels: {prop.alt_labels}")
        if prop.hidden_labels:
            print(f"    hiddenLabels: {prop.hidden_labels}")
print()

matchers = [
    ("ExactPrefLabelMatcher", ExactPrefLabelMatcher()),
    ("ExactRdfsLabelMatcher", ExactRdfsLabelMatcher()),
    ("ExactAltLabelMatcher", ExactAltLabelMatcher()),
    ("ExactHiddenLabelMatcher", ExactHiddenLabelMatcher()),
    ("ExactLocalNameMatcher", ExactLocalNameMatcher()),
]

for col_name in test_columns:
    print("="*80)
    print(f"Column: '{col_name}'")
    print("="*80)

    col_analysis = gen.data_source.get_analysis(col_name)

    for matcher_name, matcher in matchers:
        result = matcher.match(col_analysis, properties, None)
        if result:
            print(f"✅ {matcher_name}:")
            print(f"   Property: {str(result.property.uri).split('#')[-1]}")
            print(f"   Confidence: {result.confidence}")
            print(f"   Matched via: {result.matched_via}")
        else:
            print(f"❌ {matcher_name}: No match")
    print()

