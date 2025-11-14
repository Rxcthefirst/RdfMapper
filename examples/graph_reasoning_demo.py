#!/usr/bin/env python3
"""
Graph Reasoning Demo

This script demonstrates the graph reasoning capabilities of the semantic mapper,
showing how the system understands and leverages ontology structure for intelligent
column-to-property matching.
"""

from rdflib import Graph, URIRef, Namespace, RDF, RDFS, OWL, Literal
from rdflib.namespace import XSD
import tempfile
import os

from rdfmap.generator.ontology_analyzer import OntologyAnalyzer
from rdfmap.generator.graph_reasoner import GraphReasoner
from rdfmap.generator.data_analyzer import DataFieldAnalysis
from rdfmap.generator.matchers.graph_matcher import (
    GraphReasoningMatcher,
    InheritanceAwareMatcher
)

# Define namespace
EX = Namespace("http://example.com/finance#")


def create_sample_ontology():
    """Create a sample financial ontology with class hierarchy."""
    g = Graph()
    g.bind("ex", EX)
    g.bind("xsd", XSD)

    print("Creating sample ontology...")

    # Class Hierarchy: FinancialInstrument > Loan > MortgageLoan
    g.add((EX.FinancialInstrument, RDF.type, OWL.Class))
    g.add((EX.FinancialInstrument, RDFS.label, Literal("Financial Instrument")))
    g.add((EX.FinancialInstrument, RDFS.comment,
           Literal("A tradeable asset or contract with monetary value")))

    g.add((EX.Loan, RDF.type, OWL.Class))
    g.add((EX.Loan, RDFS.label, Literal("Loan")))
    g.add((EX.Loan, RDFS.subClassOf, EX.FinancialInstrument))
    g.add((EX.Loan, RDFS.comment, Literal("Money lent to a borrower with expectation of repayment")))

    g.add((EX.MortgageLoan, RDF.type, OWL.Class))
    g.add((EX.MortgageLoan, RDFS.label, Literal("Mortgage Loan")))
    g.add((EX.MortgageLoan, RDFS.subClassOf, EX.Loan))
    g.add((EX.MortgageLoan, RDFS.comment, Literal("A loan secured by real estate property")))

    # Related entities
    g.add((EX.Borrower, RDF.type, OWL.Class))
    g.add((EX.Borrower, RDFS.label, Literal("Borrower")))

    g.add((EX.Property, RDF.type, OWL.Class))
    g.add((EX.Property, RDFS.label, Literal("Property")))

    # Properties on FinancialInstrument (inherited by all subclasses)
    g.add((EX.instrumentId, RDF.type, OWL.DatatypeProperty))
    g.add((EX.instrumentId, RDFS.label, Literal("instrument ID")))
    g.add((EX.instrumentId, RDFS.domain, EX.FinancialInstrument))
    g.add((EX.instrumentId, RDFS.range, XSD.string))

    g.add((EX.issueDate, RDF.type, OWL.DatatypeProperty))
    g.add((EX.issueDate, RDFS.label, Literal("issue date")))
    g.add((EX.issueDate, RDFS.domain, EX.FinancialInstrument))
    g.add((EX.issueDate, RDFS.range, XSD.date))

    # Properties on Loan (inherited by MortgageLoan)
    g.add((EX.principalAmount, RDF.type, OWL.DatatypeProperty))
    g.add((EX.principalAmount, RDFS.label, Literal("principal amount")))
    g.add((EX.principalAmount, RDFS.domain, EX.Loan))
    g.add((EX.principalAmount, RDFS.range, XSD.decimal))

    g.add((EX.interestRate, RDF.type, OWL.DatatypeProperty))
    g.add((EX.interestRate, RDFS.label, Literal("interest rate")))
    g.add((EX.interestRate, RDFS.domain, EX.Loan))
    g.add((EX.interestRate, RDFS.range, XSD.decimal))

    g.add((EX.loanStatus, RDF.type, OWL.DatatypeProperty))
    g.add((EX.loanStatus, RDFS.label, Literal("loan status")))
    g.add((EX.loanStatus, RDFS.domain, EX.Loan))
    g.add((EX.loanStatus, RDFS.range, XSD.string))

    # Properties specific to MortgageLoan
    g.add((EX.loanNumber, RDF.type, OWL.DatatypeProperty))
    g.add((EX.loanNumber, RDFS.label, Literal("loan number")))
    g.add((EX.loanNumber, RDFS.domain, EX.MortgageLoan))
    g.add((EX.loanNumber, RDFS.range, XSD.string))

    g.add((EX.loanTerm, RDF.type, OWL.DatatypeProperty))
    g.add((EX.loanTerm, RDFS.label, Literal("loan term")))
    g.add((EX.loanTerm, RDFS.comment, Literal("Term of the loan in months")))
    g.add((EX.loanTerm, RDFS.domain, EX.MortgageLoan))
    g.add((EX.loanTerm, RDFS.range, XSD.integer))

    # Object properties
    g.add((EX.hasBorrower, RDF.type, OWL.ObjectProperty))
    g.add((EX.hasBorrower, RDFS.label, Literal("has borrower")))
    g.add((EX.hasBorrower, RDFS.domain, EX.MortgageLoan))
    g.add((EX.hasBorrower, RDFS.range, EX.Borrower))

    g.add((EX.hasCollateral, RDF.type, OWL.ObjectProperty))
    g.add((EX.hasCollateral, RDFS.label, Literal("has collateral")))
    g.add((EX.hasCollateral, RDFS.domain, EX.MortgageLoan))
    g.add((EX.hasCollateral, RDFS.range, EX.Property))

    # Borrower properties
    g.add((EX.borrowerName, RDF.type, OWL.DatatypeProperty))
    g.add((EX.borrowerName, RDFS.label, Literal("borrower name")))
    g.add((EX.borrowerName, RDFS.domain, EX.Borrower))
    g.add((EX.borrowerName, RDFS.range, XSD.string))

    g.add((EX.creditScore, RDF.type, OWL.DatatypeProperty))
    g.add((EX.creditScore, RDFS.label, Literal("credit score")))
    g.add((EX.creditScore, RDFS.domain, EX.Borrower))
    g.add((EX.creditScore, RDFS.range, XSD.integer))

    return g


def demo_class_hierarchy(reasoner):
    """Demonstrate class hierarchy reasoning."""
    print("\n" + "="*70)
    print("DEMO 1: Class Hierarchy Navigation")
    print("="*70)

    mortgage_loan = EX.MortgageLoan

    # Get ancestors
    ancestors = reasoner.get_all_ancestors(mortgage_loan)
    print(f"\n✓ Ancestors of MortgageLoan:")
    for ancestor in ancestors:
        print(f"  - {ancestor}")

    # Get inherited properties
    inherited = reasoner.get_inherited_properties(mortgage_loan)
    print(f"\n✓ All properties available to MortgageLoan (including inherited):")
    print(f"  Total: {len(inherited)} properties")

    direct_count = sum(1 for p in inherited if p.domain == mortgage_loan)
    inherited_count = len(inherited) - direct_count

    print(f"  - Direct: {direct_count}")
    print(f"  - Inherited: {inherited_count}")

    print("\n  Direct properties:")
    for prop in inherited:
        if prop.domain == mortgage_loan:
            print(f"    • {prop.label} ({prop.uri})")

    print("\n  Inherited properties:")
    for prop in inherited:
        if prop.domain != mortgage_loan:
            domain_class = reasoner.classes.get(prop.domain)
            domain_label = domain_class.label if domain_class else str(prop.domain)
            print(f"    • {prop.label} (from {domain_label})")


def demo_type_validation(reasoner, analyzer):
    """Demonstrate type validation."""
    print("\n" + "="*70)
    print("DEMO 2: Data Type Validation")
    print("="*70)

    # Get some properties
    interest_rate = analyzer.properties[EX.interestRate]
    loan_term = analyzer.properties[EX.loanTerm]

    print(f"\n✓ Testing type compatibility for '{interest_rate.label}' property:")
    print(f"  Expected range: {interest_rate.range_type}")

    test_types = [
        ("xsd:decimal", "Perfect match"),
        ("xsd:float", "Compatible numeric"),
        ("xsd:integer", "Compatible numeric"),
        ("xsd:string", "Incompatible"),
    ]

    for test_type, description in test_types:
        is_valid, confidence = reasoner.validate_property_for_data_type(
            interest_rate, test_type
        )
        status = "✓" if confidence > 0.5 else "✗"
        print(f"  {status} {test_type:15} ({description:20}) → confidence: {confidence:.2f}")

    print(f"\n✓ Testing type compatibility for '{loan_term.label}' property:")
    print(f"  Expected range: {loan_term.range_type}")

    test_types = [
        ("xsd:integer", "Perfect match"),
        ("xsd:decimal", "Compatible numeric"),
        ("xsd:string", "Incompatible"),
    ]

    for test_type, description in test_types:
        is_valid, confidence = reasoner.validate_property_for_data_type(
            loan_term, test_type
        )
        status = "✓" if confidence > 0.5 else "✗"
        print(f"  {status} {test_type:15} ({description:20}) → confidence: {confidence:.2f}")


def demo_graph_matching(graph_matcher, analyzer):
    """Demonstrate graph-based matching."""
    print("\n" + "="*70)
    print("DEMO 3: Graph-Based Column Matching")
    print("="*70)

    # Simulate columns from a spreadsheet
    test_columns = [
        ("loan_number", ["LN-12345", "LN-23456"], "xsd:string", True),
        ("interest_rate", [0.0525, 0.0450, 0.0375], "xsd:decimal", False),
        ("loan_term_months", [360, 240, 180], "xsd:integer", False),
        ("borrower_id", ["B001", "B002", "B003"], "xsd:string", True),
    ]

    properties = list(analyzer.properties.values())

    print("\n✓ Matching columns using graph reasoning:")

    for col_name, sample_vals, data_type, is_unique in test_columns:
        # Create column analysis
        column = DataFieldAnalysis(name=col_name)
        column.sample_values = sample_vals
        column.inferred_type = data_type
        column.is_unique = is_unique
        column.total_count = len(sample_vals)

        # Match
        result = graph_matcher.match(column, properties)

        if result:
            print(f"\n  Column: '{col_name}'")
            print(f"    → Matched to: {result.property.label}")
            print(f"    → Confidence: {result.confidence:.2f}")
            print(f"    → Match type: {result.match_type}")
            print(f"    → Explanation: {result.matched_via}")
        else:
            print(f"\n  Column: '{col_name}'")
            print(f"    → No match found")


def demo_inheritance_matching(reasoner, analyzer):
    """Demonstrate inheritance-aware matching."""
    print("\n" + "="*70)
    print("DEMO 4: Inheritance-Aware Matching")
    print("="*70)

    # Create inheritance-aware matcher for MortgageLoan
    matcher = InheritanceAwareMatcher(
        reasoner=reasoner,
        target_class=str(EX.MortgageLoan),
        enabled=True,
        threshold=0.7
    )

    # Only get direct MortgageLoan properties
    direct_properties = [
        p for p in analyzer.properties.values()
        if p.domain == EX.MortgageLoan
    ]

    print(f"\n✓ Direct MortgageLoan properties: {len(direct_properties)}")
    for p in direct_properties:
        print(f"  - {p.label}")

    # Try to match columns to inherited properties
    test_columns = [
        ("principal_amount", [500000.0, 750000.0], "xsd:decimal", "Loan"),
        ("instrument_id", ["INS-001", "INS-002"], "xsd:string", "FinancialInstrument"),
        ("loan_number", ["LN-001", "LN-002"], "xsd:string", "MortgageLoan (direct)"),
    ]

    print(f"\n✓ Matching columns (including inherited properties):")

    for col_name, sample_vals, data_type, expected_from in test_columns:
        column = DataFieldAnalysis(name=col_name)
        column.sample_values = sample_vals
        column.inferred_type = data_type
        column.total_count = len(sample_vals)

        result = matcher.match(column, direct_properties)

        if result:
            print(f"\n  Column: '{col_name}'")
            print(f"    → Matched to: {result.property.label}")
            print(f"    → Expected from: {expected_from}")
            print(f"    → Match type: {result.match_type}")
            print(f"    → Confidence: {result.confidence:.2f}")

            # Verify it's inherited
            if result.property.domain != EX.MortgageLoan:
                domain_class = reasoner.classes.get(result.property.domain)
                domain_label = domain_class.label if domain_class else "Unknown"
                print(f"    → Inherited from: {domain_label}")


def main():
    """Run all demos."""
    print("\n" + "="*70)
    print("GRAPH REASONING DEMONSTRATION")
    print("="*70)
    print("\nThis demo shows how the semantic mapper uses ontology structure")
    print("for intelligent column-to-property matching.")

    # Create sample ontology
    graph = create_sample_ontology()

    # Save to temp file and load with analyzer
    with tempfile.NamedTemporaryFile(mode='wb', suffix='.ttl', delete=False) as f:
        graph.serialize(f, format='turtle')
        temp_path = f.name

    try:
        # Load ontology
        analyzer = OntologyAnalyzer(temp_path)

        # Create reasoner
        reasoner = GraphReasoner(
            graph,
            analyzer.classes,
            analyzer.properties
        )

        # Create graph matcher
        graph_matcher = GraphReasoningMatcher(
            reasoner=reasoner,
            enabled=True,
            threshold=0.6
        )

        # Run demos
        demo_class_hierarchy(reasoner)
        demo_type_validation(reasoner, analyzer)
        demo_graph_matching(graph_matcher, analyzer)
        demo_inheritance_matching(reasoner, analyzer)

        print("\n" + "="*70)
        print("DEMO COMPLETE")
        print("="*70)
        print("\nKey Takeaways:")
        print("  1. The reasoner understands class hierarchies and inheritance")
        print("  2. Type validation ensures data compatibility")
        print("  3. Graph matching leverages ontology structure")
        print("  4. Inherited properties are automatically discovered")
        print("\nFor more information, see docs/GRAPH_REASONING.md")

    finally:
        # Cleanup
        os.unlink(temp_path)


if __name__ == "__main__":
    main()

