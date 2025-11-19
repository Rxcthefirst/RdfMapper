#!/usr/bin/env python3
"""Simple test to check if SKOS labels are loaded."""

from rdflib import Graph, Namespace
from rdfmap.generator.ontology_analyzer import OntologyAnalyzer

print("Testing OntologyAnalyzer with imports...")
print("="*80)

try:
    analyzer = OntologyAnalyzer(
        ontology_file='examples/comprehensive_test/hr_ontology.ttl',
        imports=['examples/comprehensive_test/hr_vocabulary.ttl']
    )

    print(f"✅ Loaded ontology successfully")
    print(f"   Total triples in graph: {len(analyzer.graph)}")
    print(f"   Total properties: {len(analyzer.properties)}")
    print()

    # Check if employeeID exists and has SKOS labels
    for prop_uri, prop in analyzer.properties.items():
        if 'employeeID' in str(prop_uri):
            print(f"Found property: {prop_uri}")
            print(f"  rdfs:label: '{prop.label}'")
            print(f"  skos:prefLabel: '{prop.pref_label}'")
            print(f"  skos:altLabel: {prop.alt_labels}")
            print(f"  skos:hiddenLabel: {prop.hidden_labels}")
            break
    else:
        print("❌ employeeID property not found!")

except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()

