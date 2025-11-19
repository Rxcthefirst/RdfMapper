#!/usr/bin/env python3
"""Test if partial/fuzzy matchers are working for specific columns."""

from rdfmap.generator.mapping_generator import MappingGenerator, GeneratorConfig
from rdfmap.generator.matchers import PartialStringMatcher, FuzzyStringMatcher, LexicalMatcher

gen = MappingGenerator(
    ontology_file='examples/comprehensive_test/hr_ontology.ttl',
    data_file='examples/comprehensive_test/employees.csv',
    config=GeneratorConfig(
        base_iri='http://example.org/employees/',
        min_confidence=0.30,  # Lower threshold
        imports=['examples/comprehensive_test/hr_vocabulary.ttl']
    )
)

employee_class = None
for cls_uri, cls in gen.ontology.classes.items():
    if 'Employee' in str(cls_uri):
        employee_class = cls
        break

properties = gen.ontology.get_datatype_properties(employee_class.uri)

test_cols = ["ph", "wrk_loc", "emp_nm", "pos_ttl", "dept_nm"]

matchers = [
    ("PartialStringMatcher", PartialStringMatcher(threshold=0.30)),
    ("FuzzyStringMatcher", FuzzyStringMatcher(threshold=0.30)),
    ("LexicalMatcher", LexicalMatcher(threshold=0.30)),
]

for col_name in test_cols:
    print(f"\n{'='*80}")
    print(f"Column: '{col_name}'")
    print(f"{'='*80}")

    col_analysis = gen.data_source.get_analysis(col_name)

    for matcher_name, matcher in matchers:
        result = matcher.match(col_analysis, properties, None)
        if result:
            prop_name = str(result.property.uri).split('#')[-1]
            print(f"✅ {matcher_name}: {prop_name} (confidence={result.confidence:.3f}, via='{result.matched_via}')")
        else:
            print(f"❌ {matcher_name}: No match")

