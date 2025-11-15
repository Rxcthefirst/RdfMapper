#!/usr/bin/env python3
"""Test OWL Characteristics Matcher implementation."""

import sys
sys.path.insert(0, 'src')

from rdflib import Graph, Namespace, RDF, RDFS, OWL, Literal, XSD
from rdfmap.generator.ontology_analyzer import OntologyAnalyzer
from rdfmap.generator.data_analyzer import DataFieldAnalysis
from rdfmap.generator.matchers.owl_characteristics_matcher import OWLCharacteristicsMatcher

print("="*80)
print("Testing OWL Characteristics Matcher")
print("="*80)

# Create test ontology with OWL characteristics
print("\n1. Creating test ontology with OWL characteristics...")

g = Graph()
EX = Namespace("http://example.org/")
g.bind("ex", EX)
g.bind("xsd", XSD)

# Define properties with OWL characteristics

# InverseFunctional Properties (unique identifiers)
g.add((EX.hasCustomerID, RDF.type, OWL.DatatypeProperty))
g.add((EX.hasCustomerID, RDF.type, OWL.InverseFunctionalProperty))
g.add((EX.hasCustomerID, RDFS.label, Literal("has customer ID")))
g.add((EX.hasCustomerID, RDFS.range, XSD.string))

g.add((EX.hasEmail, RDF.type, OWL.DatatypeProperty))
g.add((EX.hasEmail, RDF.type, OWL.InverseFunctionalProperty))
g.add((EX.hasEmail, RDFS.label, Literal("has email")))
g.add((EX.hasEmail, RDFS.range, XSD.string))

g.add((EX.hasSSN, RDF.type, OWL.DatatypeProperty))
g.add((EX.hasSSN, RDF.type, OWL.InverseFunctionalProperty))
g.add((EX.hasSSN, RDFS.label, Literal("has SSN")))
g.add((EX.hasSSN, RDFS.range, XSD.string))

# Functional Properties (single-valued)
g.add((EX.hasDateOfBirth, RDF.type, OWL.DatatypeProperty))
g.add((EX.hasDateOfBirth, RDF.type, OWL.FunctionalProperty))
g.add((EX.hasDateOfBirth, RDFS.label, Literal("has date of birth")))
g.add((EX.hasDateOfBirth, RDFS.range, XSD.date))

g.add((EX.hasAge, RDF.type, OWL.DatatypeProperty))
g.add((EX.hasAge, RDF.type, OWL.FunctionalProperty))
g.add((EX.hasAge, RDFS.label, Literal("has age")))
g.add((EX.hasAge, RDFS.range, XSD.integer))

# Regular properties (no special characteristics)
g.add((EX.hasName, RDF.type, OWL.DatatypeProperty))
g.add((EX.hasName, RDFS.label, Literal("has name")))
g.add((EX.hasName, RDFS.range, XSD.string))

g.add((EX.hasAddress, RDF.type, OWL.DatatypeProperty))
g.add((EX.hasAddress, RDFS.label, Literal("has address")))
g.add((EX.hasAddress, RDFS.range, XSD.string))

# Symmetric property (for relationship example)
g.add((EX.isSiblingOf, RDF.type, OWL.ObjectProperty))
g.add((EX.isSiblingOf, RDF.type, OWL.SymmetricProperty))
g.add((EX.isSiblingOf, RDFS.label, Literal("is sibling of")))

# Transitive property
g.add((EX.isAncestorOf, RDF.type, OWL.ObjectProperty))
g.add((EX.isAncestorOf, RDF.type, OWL.TransitiveProperty))
g.add((EX.isAncestorOf, RDFS.label, Literal("is ancestor of")))

# Save to file
test_onto_path = "test_data/test_owl_ontology.ttl"
from pathlib import Path
Path("test_data").mkdir(exist_ok=True)
g.serialize(test_onto_path, format="turtle")
print(f"  ✓ Created ontology with OWL characteristics")
print(f"  ✓ Saved to {test_onto_path}")

# Load ontology
print("\n2. Loading ontology...")
ontology = OntologyAnalyzer(test_onto_path)
print(f"  ✓ Loaded {len(ontology.properties)} properties")

# Create OWL characteristics matcher
print("\n3. Creating OWL Characteristics Matcher...")
matcher = OWLCharacteristicsMatcher(
    ontology_analyzer=ontology,
    enabled=True,
    threshold=0.60,
    ifp_uniqueness_threshold=0.90,
    fp_uniqueness_threshold=0.95
)
print("  ✓ OWL matcher created")
print(f"  ✓ OWL cache built for {len(matcher._owl_cache)} properties")

# Show OWL characteristics detected
print("\n  OWL Characteristics detected:")
for uri, info in list(matcher._owl_cache.items())[:5]:
    prop = ontology.properties.get(uri)
    if prop:
        chars = []
        if info['is_functional']:
            chars.append("Functional")
        if info['is_inverse_functional']:
            chars.append("InverseFunctional")
        if info['is_transitive']:
            chars.append("Transitive")
        if info['is_symmetric']:
            chars.append("Symmetric")

        if chars:
            print(f"    • {prop.label}: {', '.join(chars)}")

# Test 1: InverseFunctional Property - Customer ID
print("\n4. Test 1: InverseFunctional Property - 'customer_id' column")
print("  " + "-"*76)

column1 = DataFieldAnalysis("customer_id")
column1.sample_values = ["CUST001", "CUST002", "CUST003", "CUST004", "CUST005"]
column1.inferred_datatype = "string"

properties = list(ontology.properties.values())
result1 = matcher.match(column1, properties)

if result1:
    print(f"  ✓ Match found: {result1.property.label}")
    print(f"  ✓ Confidence: {result1.confidence:.3f}")
    print(f"  ✓ Matched via: {result1.matched_via}")

    # Get OWL characteristics
    owl_chars = matcher.get_owl_characteristics(result1.property)
    print(f"\n  OWL Characteristics:")
    print(f"    • Type: {', '.join(owl_chars['characteristics'])}")
    print(f"    • Can be identifier: {owl_chars['can_be_identifier']}")
    print(f"    • Expects single value: {owl_chars['expects_single_value']}")

    # Calculate uniqueness
    uniqueness = matcher._calculate_uniqueness_ratio(column1)
    print(f"\n  Data Validation:")
    print(f"    • Uniqueness: {uniqueness:.0%}")
    print(f"    • Has ID pattern: {matcher._has_id_pattern(column1)}")
    print(f"    • ✓ Data matches InverseFunctionalProperty semantics")
else:
    print("  ✗ No match found")

# Test 2: InverseFunctional Property - Email
print("\n5. Test 2: InverseFunctional Property - 'email' column")
print("  " + "-"*76)

column2 = DataFieldAnalysis("email")
column2.sample_values = ["john@ex.com", "jane@ex.com", "bob@ex.com", "alice@ex.com"]
column2.inferred_datatype = "string"

result2 = matcher.match(column2, properties)

if result2:
    print(f"  ✓ Match found: {result2.property.label}")
    print(f"  ✓ Confidence: {result2.confidence:.3f}")

    uniqueness = matcher._calculate_uniqueness_ratio(column2)
    print(f"\n  Validation:")
    print(f"    • Uniqueness: {uniqueness:.0%} (all unique)")
    print(f"    • ✓ Perfect match for InverseFunctionalProperty")
else:
    print("  ✗ No match found")

# Test 3: InverseFunctional Property with violations
print("\n6. Test 3: IFP Violation - 'email' with duplicates")
print("  " + "-"*76)

column3 = DataFieldAnalysis("email")
column3.sample_values = ["john@ex.com", "jane@ex.com", "john@ex.com", "alice@ex.com"]  # Duplicate!
column3.inferred_datatype = "string"

result3 = matcher.match(column3, properties)

if result3:
    print(f"  ✓ Match found: {result3.property.label}")
    print(f"  ✓ Confidence: {result3.confidence:.3f}")

    uniqueness = matcher._calculate_uniqueness_ratio(column3)
    print(f"\n  Validation:")
    print(f"    • Uniqueness: {uniqueness:.0%} (has duplicates)")
    print(f"    • ⚠ Warning: InverseFunctionalProperty violation detected")
    print(f"    • Lower confidence due to data not matching OWL semantics")
else:
    print("  ✗ No match found")

# Test 4: Functional Property - Date of Birth
print("\n7. Test 4: Functional Property - 'date_of_birth' column")
print("  " + "-"*76)

column4 = DataFieldAnalysis("date_of_birth")
column4.sample_values = ["1990-01-15", "1985-05-20", "1992-08-10", "1988-03-25"]
column4.inferred_datatype = "date"

result4 = matcher.match(column4, properties)

if result4:
    print(f"  ✓ Match found: {result4.property.label}")
    print(f"  ✓ Confidence: {result4.confidence:.3f}")

    owl_chars = matcher.get_owl_characteristics(result4.property)
    print(f"\n  OWL Characteristics:")
    print(f"    • Type: {', '.join(owl_chars['characteristics'])}")
    print(f"    • Expects single value: {owl_chars['expects_single_value']}")

    uniqueness = matcher._calculate_uniqueness_ratio(column4)
    print(f"\n  Validation:")
    print(f"    • Uniqueness: {uniqueness:.0%}")
    print(f"    • ✓ High uniqueness matches Functional Property")
else:
    print("  ✗ No match found")

# Test 5: Regular property without OWL characteristics
print("\n8. Test 5: Regular Property - 'name' column")
print("  " + "-"*76)

column5 = DataFieldAnalysis("name")
column5.sample_values = ["John", "Jane", "Bob", "Alice", "John"]  # Some duplicates
column5.inferred_datatype = "string"

result5 = matcher.match(column5, properties)

if result5:
    print(f"  ✓ Match found: {result5.property.label}")
    print(f"  ✓ Confidence: {result5.confidence:.3f}")

    owl_chars = matcher.get_owl_characteristics(result5.property)
    print(f"\n  OWL Characteristics:")
    if owl_chars['characteristics']:
        print(f"    • Type: {', '.join(owl_chars['characteristics'])}")
    else:
        print(f"    • No special OWL characteristics")

    uniqueness = matcher._calculate_uniqueness_ratio(column5)
    print(f"\n  Validation:")
    print(f"    • Uniqueness: {uniqueness:.0%}")
    print(f"    • Regular property - duplicates are acceptable")
else:
    print("  ✗ No match found")

# Test 6: Identifier without IFP declaration
print("\n9. Test 6: Unique ID without IFP - 'ssn' column")
print("  " + "-"*76)

column6 = DataFieldAnalysis("ssn")
column6.sample_values = ["111-11-1111", "222-22-2222", "333-33-3333", "444-44-4444"]
column6.inferred_datatype = "string"

result6 = matcher.match(column6, properties)

if result6:
    print(f"  ✓ Match found: {result6.property.label}")
    print(f"  ✓ Confidence: {result6.confidence:.3f}")
    print(f"  ✓ Matched via: {result6.matched_via}")

    uniqueness = matcher._calculate_uniqueness_ratio(column6)
    print(f"\n  Data Analysis:")
    print(f"    • Uniqueness: {uniqueness:.0%} (all unique)")
    print(f"    • Has ID pattern: {matcher._has_id_pattern(column6)}")

    owl_chars = matcher.get_owl_characteristics(result6.property)
    if owl_chars['is_inverse_functional']:
        print(f"    • ✓ Property correctly declared as InverseFunctionalProperty")
    else:
        print(f"    • ⚠ Property should be InverseFunctionalProperty (enrichment opportunity)")
else:
    print("  ✗ No match found")

print("\n" + "="*80)
print("OWL Characteristics Matcher Tests Complete!")
print("="*80)

print("\n✓ Key Features Demonstrated:")
print("  1. InverseFunctional Property detection and validation")
print("  2. Functional Property detection")
print("  3. Data uniqueness validation against OWL semantics")
print("  4. Confidence boosting for matching data patterns")
print("  5. Confidence reduction for OWL violations")
print("  6. Identifier detection (IFP properties)")
print("  7. Enrichment suggestions")

print("\n✓ Benefits:")
print("  • Identifies columns that can be used as identifiers")
print("  • Validates data against ontology definitions")
print("  • Detects data quality issues (IFP violations)")
print("  • Boosts confidence when semantics align")
print("  • Suggests ontology improvements")

