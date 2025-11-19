#!/usr/bin/env python3
"""Test exact matching with debug output."""

# Test exact matching logic
col_name = "Employee ID"
pref_label = "Employee ID"

col_clean = col_name.lower().replace("_", "").replace(" ", "")
label_clean = pref_label.lower().replace("_", "").replace(" ", "")

print(f"Column: '{col_name}'")
print(f"Cleaned column: '{col_clean}'")
print(f"prefLabel: '{pref_label}'")
print(f"Cleaned prefLabel: '{label_clean}'")
print(f"Match: {col_clean == label_clean}")
print()

# Now test with actual data
from rdfmap.generator.mapping_generator import MappingGenerator, GeneratorConfig

gen = MappingGenerator(
    ontology_file='examples/comprehensive_test/hr_ontology.ttl',
    data_file='examples/comprehensive_test/employees.csv',
    config=GeneratorConfig(
        base_iri='http://example.org/employees/',
        imports=['examples/comprehensive_test/hr_vocabulary.ttl']
    )
)

# Find employeeID property
employee_id_prop = None
for prop_uri, prop in gen.ontology.properties.items():
    if 'employeeID' in str(prop_uri):
        employee_id_prop = prop
        break

if employee_id_prop:
    print(f"Found property: {employee_id_prop.uri}")
    print(f"  skos:prefLabel: '{employee_id_prop.pref_label}'")
    print(f"  rdfs:label: '{employee_id_prop.label}'")

    # Test normalization
    if employee_id_prop.pref_label:
        col_clean = "Employee ID".lower().replace("_", "").replace(" ", "")
        label_clean = employee_id_prop.pref_label.lower().replace("_", "").replace(" ", "")
        print(f"\n  Column cleaned: '{col_clean}'")
        print(f"  Label cleaned: '{label_clean}'")
        print(f"  Should match: {col_clean == label_clean}")
else:
    print("Could not find employeeID property!")
    print("\nAll properties:")
    for prop_uri, prop in gen.ontology.properties.items():
        print(f"  {prop_uri}: pref_label='{prop.pref_label}'")

