#!/usr/bin/env python3

"""
Demonstration of --ontology vs --import distinction
"""

import tempfile
from pathlib import Path

# Create example ontologies to show the difference

# PRIMARY ONTOLOGY (--ontology): Contains target class and domain-specific concepts
primary_ontology = """
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix hr: <http://example.org/hr#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

# PRIMARY DOMAIN CONCEPTS - HR specific
hr:Employee a owl:Class ;
    rdfs:label "Employee" ;
    rdfs:comment "A person employed by the organization" .

hr:hasEmployeeID a owl:DatatypeProperty ;
    rdfs:domain hr:Employee ;
    rdfs:range xsd:string ;
    rdfs:label "has employee ID" .

hr:hasSalary a owl:DatatypeProperty ;
    rdfs:domain hr:Employee ;
    rdfs:range xsd:decimal ;
    rdfs:label "has salary" .
"""

# IMPORTED ONTOLOGY (--import): Reusable common concepts
imported_ontology = """
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix shared: <http://example.org/shared#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

# SHARED CONCEPTS - Reusable across domains
shared:Person a owl:Class ;
    rdfs:label "Person" ;
    rdfs:comment "A human being" .

shared:hasFirstName a owl:DatatypeProperty ;
    rdfs:domain shared:Person ;
    rdfs:range xsd:string ;
    rdfs:label "has first name" .

shared:hasLastName a owl:DatatypeProperty ;
    rdfs:domain shared:Person ;
    rdfs:range xsd:string ;
    rdfs:label "has last name" .
"""

# Sample data
sample_data = """employee_id,first_name,last_name,salary
E001,John,Smith,75000
E002,Jane,Doe,68000
"""

def demonstrate_ontology_vs_import():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Write files
        primary_file = temp_path / "hr_domain.ttl"
        primary_file.write_text(primary_ontology)

        imported_file = temp_path / "shared_common.ttl"
        imported_file.write_text(imported_ontology)

        data_file = temp_path / "employees.csv"
        data_file.write_text(sample_data)

        print("=== ONTOLOGY vs IMPORT DEMONSTRATION ===")
        print()
        print("PRIMARY ONTOLOGY (--ontology hr_domain.ttl):")
        print("  ✓ Contains Employee class (target class)")
        print("  ✓ Contains hr:hasEmployeeID (domain-specific)")
        print("  ✓ Contains hr:hasSalary (domain-specific)")
        print()
        print("IMPORTED ONTOLOGY (--import shared_common.ttl):")
        print("  ✓ Contains shared:hasFirstName (reusable)")
        print("  ✓ Contains shared:hasLastName (reusable)")
        print("  ✓ Provides common person concepts")
        print()

        # Test with ontology analyzer
        from src.rdfmap.generator.ontology_analyzer import OntologyAnalyzer

        print("ANALYSIS RESULTS:")
        print()

        # Primary ontology only
        analyzer_primary = OntologyAnalyzer(str(primary_file))
        print(f"Primary ontology only: {len(analyzer_primary.classes)} classes, {len(analyzer_primary.properties)} properties")

        # With imports
        analyzer_combined = OntologyAnalyzer(str(primary_file), imports=[str(imported_file)])
        print(f"With imports:          {len(analyzer_combined.classes)} classes, {len(analyzer_combined.properties)} properties")
        print()

        print("KEY INSIGHT:")
        print("• --ontology provides the TARGET CLASS and domain authority")
        print("• --import provides ADDITIONAL PROPERTIES for richer mappings")
        print("• Both are combined for comprehensive semantic coverage")
        print()

        # Show properties available from each
        print("PROPERTIES FROM PRIMARY ONTOLOGY:")
        for uri, prop in analyzer_primary.properties.items():
            print(f"  • {prop.label} ({uri})")

        print()
        print("ADDITIONAL PROPERTIES FROM IMPORTS:")
        combined_props = set(analyzer_combined.properties.keys())
        primary_props = set(analyzer_primary.properties.keys())
        import_props = combined_props - primary_props

        for prop_uri in import_props:
            prop = analyzer_combined.properties[prop_uri]
            print(f"  • {prop.label} ({prop_uri})")

if __name__ == "__main__":
    demonstrate_ontology_vs_import()
