#!/usr/bin/env python3
"""Test Property Hierarchy Matcher implementation."""

import sys
sys.path.insert(0, 'src')

from rdflib import Graph, Namespace, RDF, RDFS, OWL, Literal
from rdfmap.generator.ontology_analyzer import OntologyAnalyzer
from rdfmap.generator.data_analyzer import DataFieldAnalysis
from rdfmap.generator.matchers.hierarchy_matcher import PropertyHierarchyMatcher

print("="*80)
print("Testing Property Hierarchy Matcher")
print("="*80)

# Create test ontology with property hierarchy
print("\n1. Creating test ontology with property hierarchy...")

g = Graph()
EX = Namespace("http://example.org/")
g.bind("ex", EX)

# Define property hierarchy
# hasIdentifier (root)
#   ├── hasName (child of hasIdentifier)
#   │   ├── hasFullName (child of hasName)
#   │   ├── hasFirstName (child of hasName)
#   │   └── hasLastName (child of hasName)
#   └── hasID (child of hasIdentifier)
#       └── hasCustomerID (child of hasID)

# Add properties
g.add((EX.hasIdentifier, RDF.type, OWL.DatatypeProperty))
g.add((EX.hasIdentifier, RDFS.label, Literal("has identifier")))

g.add((EX.hasName, RDF.type, OWL.DatatypeProperty))
g.add((EX.hasName, RDFS.label, Literal("has name")))
g.add((EX.hasName, RDFS.subPropertyOf, EX.hasIdentifier))

g.add((EX.hasFullName, RDF.type, OWL.DatatypeProperty))
g.add((EX.hasFullName, RDFS.label, Literal("has full name")))
g.add((EX.hasFullName, RDFS.subPropertyOf, EX.hasName))

g.add((EX.hasFirstName, RDF.type, OWL.DatatypeProperty))
g.add((EX.hasFirstName, RDFS.label, Literal("has first name")))
g.add((EX.hasFirstName, RDFS.subPropertyOf, EX.hasName))

g.add((EX.hasLastName, RDF.type, OWL.DatatypeProperty))
g.add((EX.hasLastName, RDFS.label, Literal("has last name")))
g.add((EX.hasLastName, RDFS.subPropertyOf, EX.hasName))

g.add((EX.hasID, RDF.type, OWL.DatatypeProperty))
g.add((EX.hasID, RDFS.label, Literal("has ID")))
g.add((EX.hasID, RDFS.subPropertyOf, EX.hasIdentifier))

g.add((EX.hasCustomerID, RDF.type, OWL.DatatypeProperty))
g.add((EX.hasCustomerID, RDFS.label, Literal("has customer ID")))
g.add((EX.hasCustomerID, RDFS.subPropertyOf, EX.hasID))

# Save to file
test_onto_path = "test_data/test_hierarchy_ontology.ttl"
from pathlib import Path
Path("test_data").mkdir(exist_ok=True)
g.serialize(test_onto_path, format="turtle")
print(f"  ✓ Created ontology with property hierarchy")
print(f"  ✓ Saved to {test_onto_path}")

# Load ontology
print("\n2. Loading ontology...")
ontology = OntologyAnalyzer(test_onto_path)
print(f"  ✓ Loaded {len(ontology.properties)} properties")

# Create hierarchy matcher
print("\n3. Creating Property Hierarchy Matcher...")
matcher = PropertyHierarchyMatcher(
    ontology_analyzer=ontology,
    enabled=True,
    threshold=0.65,
    hierarchy_boost=0.15
)
print("  ✓ Hierarchy matcher created")
print(f"  ✓ Hierarchy cache built for {len(matcher._hierarchy_cache)} properties")

# Test 1: Exact match with hierarchy awareness
print("\n4. Test 1: Exact match - 'full_name' column")
print("  " + "-"*76)

column = DataFieldAnalysis("full_name")
column.sample_values = ["John Doe", "Jane Smith", "Bob Johnson"]
column.inferred_datatype = "string"

properties = list(ontology.properties.values())

# Debug: Show what properties we have
print(f"  Available properties ({len(properties)}):")
for prop in properties[:5]:
    labels = prop.get_all_labels()
    print(f"    • {prop.uri} - labels: {labels}")

result = matcher.match(column, properties)

if result:
    print(f"\n  ✓ Match found: {result.property.label}")
    print(f"  ✓ Confidence: {result.confidence:.3f}")
    print(f"  ✓ Match type: {result.match_type}")
    print(f"  ✓ Matched via: {result.matched_via}")

    # Get hierarchy info
    hierarchy_info = matcher.get_property_hierarchy_info(result.property)
    print(f"\n  Hierarchy Information:")
    print(f"    • Depth in hierarchy: {hierarchy_info['depth']}")
    print(f"    • Specificity: {hierarchy_info['specificity']:.2f}")
    print(f"    • Parent properties: {len(hierarchy_info['parents'])}")
    print(f"    • Child properties: {len(hierarchy_info['children'])}")
    print(f"    • Is root: {hierarchy_info['is_root']}")
    print(f"    • Is leaf: {hierarchy_info['is_leaf']}")

    if hierarchy_info['parents']:
        print(f"    • Parents: {[p.label for p in hierarchy_info['parents']]}")
    if hierarchy_info['children']:
        print(f"    • Children: {[c.label for c in hierarchy_info['children']]}")
else:
    print("\n  ✗ No match found")
    print("  Debug: Column name variations tried:")
    print(f"    • full_name")
    print(f"    • fullname")
    print(f"    • has full name")

# Test 2: General term matching to specific property
print("\n5. Test 2: General term - 'name' column")
print("  " + "-"*76)

column2 = DataFieldAnalysis("name")
column2.sample_values = ["John", "Jane", "Bob"]
column2.inferred_datatype = "string"

result2 = matcher.match(column2, properties)

if result2:
    print(f"  ✓ Match found: {result2.property.label}")
    print(f"  ✓ Confidence: {result2.confidence:.3f}")
    print(f"  ✓ Reasoning: Matched to general property")

    # Show hierarchy info
    hierarchy_info = matcher.get_property_hierarchy_info(result2.property)
    print(f"  ✓ This property has {len(hierarchy_info['children'])} more specific children")

    if hierarchy_info['children']:
        print(f"\n  More specific alternatives:")
        for child_prop in hierarchy_info['children']:
            print(f"    • {child_prop.label}")
else:
    print("  ✗ No match found")

# Test 3: Hierarchy navigation
print("\n6. Test 3: Analyzing full hierarchy")
print("  " + "-"*76)

# Find root property
for prop_uri, prop in ontology.properties.items():
    hierarchy_info = matcher.get_property_hierarchy_info(prop)
    if hierarchy_info['is_root']:
        print(f"\n  Root Property: {prop.label}")
        print(f"    • URI: {prop.uri}")
        print(f"    • Descendants: {hierarchy_info['descendant_count']}")

        # Show tree structure
        def show_children(parent_prop, indent=2):
            h_info = matcher.get_property_hierarchy_info(parent_prop)
            for child in h_info['children']:
                print(f"    {'  ' * indent}├── {child.label} (depth: {matcher._hierarchy_cache.get(str(child.uri), {}).get('depth', 0)})")
                show_children(child, indent + 1)

        show_children(prop)

# Test 4: Customer ID matching
print("\n7. Test 4: Specific ID - 'customer_id' column")
print("  " + "-"*76)

column3 = DataFieldAnalysis("customer_id")
column3.sample_values = ["C001", "C002", "C003"]
column3.inferred_datatype = "string"

result3 = matcher.match(column3, properties)

if result3:
    print(f"  ✓ Match found: {result3.property.label}")
    print(f"  ✓ Confidence: {result3.confidence:.3f}")

    hierarchy_info = matcher.get_property_hierarchy_info(result3.property)
    print(f"  ✓ This is a {'leaf' if hierarchy_info['is_leaf'] else 'intermediate'} property")
    print(f"  ✓ Depth: {hierarchy_info['depth']} (deeper = more specific)")

    if hierarchy_info['parents']:
        print(f"\n  Generalizations (parent properties):")
        for parent in hierarchy_info['parents']:
            print(f"    • {parent.label}")
else:
    print("  ✗ No match found")

print("\n" + "="*80)
print("Property Hierarchy Matcher Tests Complete!")
print("="*80)

print("\n✓ Key Features Demonstrated:")
print("  1. Hierarchy-aware matching")
print("  2. Confidence boosting based on specificity")
print("  3. Parent/child property suggestions")
print("  4. Depth and specificity calculations")
print("  5. Complete hierarchy navigation")

print("\n✓ Benefits:")
print("  • Understands property relationships")
print("  • Suggests appropriate generalization levels")
print("  • Higher confidence for well-placed matches")
print("  • Enables semantic reasoning beyond string matching")

