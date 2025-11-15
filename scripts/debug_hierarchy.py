#!/usr/bin/env python3
"""Debug the hierarchy matcher to see what's going wrong."""

import sys
sys.path.insert(0, 'src')

from rdflib import Graph, Namespace, RDF, RDFS, OWL, Literal
from rdfmap.generator.ontology_analyzer import OntologyAnalyzer

print("="*80)
print("Debugging Hierarchy Matcher")
print("="*80)

# Load the test ontology
test_onto_path = "test_data/test_hierarchy_ontology.ttl"
print(f"\n1. Loading ontology from {test_onto_path}...")

ontology = OntologyAnalyzer(test_onto_path)
print(f"  ✓ Loaded {len(ontology.properties)} properties")

# Check what properties we have
print("\n2. Properties in ontology:")
for uri, prop in list(ontology.properties.items())[:10]:
    print(f"  • URI: {uri}")
    print(f"    Type: {type(uri)}")
    print(f"    Label: {prop.label}")
    print(f"    Pref Label: {prop.pref_label}")
    print(f"    Alt Labels: {prop.alt_labels}")
    print(f"    All Labels: {prop.get_all_labels()}")
    print()

# Check the graph directly
print("\n3. Checking graph for subPropertyOf relationships:")
from rdflib import URIRef
EX = Namespace("http://example.org/")

for s, p, o in ontology.graph.triples((None, RDFS.subPropertyOf, None)):
    print(f"  {s} --subPropertyOf--> {o}")

print("\n4. Checking for property type declarations:")
for s, p, o in ontology.graph.triples((None, RDF.type, OWL.DatatypeProperty)):
    print(f"  {s} is a DatatypeProperty")
    # Get its label
    for label_triple in ontology.graph.triples((s, RDFS.label, None)):
        print(f"    Label: {label_triple[2]}")

print("\n5. Testing label matching manually:")
test_labels = ["full_name", "fullname", "full name", "has full name", "hasfullname"]
for label in test_labels:
    print(f"\n  Testing: '{label}'")
    for uri, prop in ontology.properties.items():
        all_labels = prop.get_all_labels()
        for prop_label in all_labels:
            if prop_label:
                prop_label_lower = prop_label.lower()
                label_lower = label.lower()

                if (label_lower == prop_label_lower or
                    label_lower == prop_label_lower.replace(' ', '_') or
                    label_lower == prop_label_lower.replace(' ', '')):
                    print(f"    ✓ MATCH: {prop_label} ({uri})")

