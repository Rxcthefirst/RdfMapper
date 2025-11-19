"""
Extended validation with diverse test cases to check confidence calibration.

Tests matching system on:
1. Clean data (mortgage) - baseline
2. Ambiguous columns (generic names)
3. Abbreviations and acronyms
4. Domain-specific terminology
5. Synonym variations
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from rdfmap.generator.mapping_generator import MappingGenerator, GeneratorConfig
from rdfmap.generator.data_analyzer import DataFieldAnalysis
from rdfmap.generator.ontology_analyzer import OntologyProperty
from rdflib import URIRef, Graph, Namespace
import tempfile
import csv


def create_ambiguous_test_case():
    """Create test case with deliberately ambiguous column names."""

    # Create ontology with multiple properties that could match
    ontology = """
    @prefix ex: <http://example.org/> .
    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
    @prefix owl: <http://www.w3.org/2002/07/owl#> .
    @prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
    
    ex:Person a owl:Class ;
        rdfs:label "Person" .
    
    ex:personName a owl:DatatypeProperty ;
        rdfs:label "personName" ;
        rdfs:domain ex:Person ;
        rdfs:range xsd:string .
    
    ex:fullName a owl:DatatypeProperty ;
        rdfs:label "fullName" ;
        rdfs:domain ex:Person ;
        rdfs:range xsd:string .
    
    ex:customerName a owl:DatatypeProperty ;
        rdfs:label "customerName" ;
        rdfs:domain ex:Person ;
        rdfs:range xsd:string .
    
    ex:contactName a owl:DatatypeProperty ;
        rdfs:label "contactName" ;
        rdfs:domain ex:Person ;
        rdfs:range xsd:string .
    
    ex:accountNumber a owl:DatatypeProperty ;
        rdfs:label "accountNumber" ;
        rdfs:domain ex:Person ;
        rdfs:range xsd:string .
    
    ex:identifier a owl:DatatypeProperty ;
        rdfs:label "identifier" ;
        rdfs:domain ex:Person ;
        rdfs:range xsd:string .
    
    ex:customerId a owl:DatatypeProperty ;
        rdfs:label "customerId" ;
        rdfs:domain ex:Person ;
        rdfs:range xsd:string .
    
    ex:createdDate a owl:DatatypeProperty ;
        rdfs:label "createdDate" ;
        rdfs:domain ex:Person ;
        rdfs:range xsd:date .
    
    ex:registrationDate a owl:DatatypeProperty ;
        rdfs:label "registrationDate" ;
        rdfs:domain ex:Person ;
        rdfs:range xsd:date .
    
    ex:signupDate a owl:DatatypeProperty ;
        rdfs:label "signupDate" ;
        rdfs:domain ex:Person ;
        rdfs:range xsd:date .
    """

    # Create data with ambiguous column names
    data = [
        {"name": "John Doe", "id": "C001", "date": "2023-01-15"},
        {"name": "Jane Smith", "id": "C002", "date": "2023-02-20"},
        {"name": "Bob Johnson", "id": "C003", "date": "2023-03-10"},
    ]

    return ontology, data


def create_abbreviation_test_case():
    """Create test case with abbreviations and acronyms."""

    ontology = """
    @prefix ex: <http://example.org/> .
    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
    @prefix owl: <http://www.w3.org/2002/07/owl#> .
    @prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
    
    ex:Employee a owl:Class ;
        rdfs:label "Employee" .
    
    ex:socialSecurityNumber a owl:DatatypeProperty ;
        rdfs:label "socialSecurityNumber" ;
        rdfs:domain ex:Employee ;
        rdfs:range xsd:string .
    
    ex:employeeIdentifier a owl:DatatypeProperty ;
        rdfs:label "employeeIdentifier" ;
        rdfs:domain ex:Employee ;
        rdfs:range xsd:string .
    
    ex:dateOfBirth a owl:DatatypeProperty ;
        rdfs:label "dateOfBirth" ;
        rdfs:domain ex:Employee ;
        rdfs:range xsd:date .
    
    ex:residentialAddress a owl:DatatypeProperty ;
        rdfs:label "residentialAddress" ;
        rdfs:domain ex:Employee ;
        rdfs:range xsd:string .
    
    ex:phoneNumber a owl:DatatypeProperty ;
        rdfs:label "phoneNumber" ;
        rdfs:domain ex:Employee ;
        rdfs:range xsd:string .
    """

    data = [
        {"ssn": "123-45-6789", "emp_id": "E001", "dob": "1980-05-15", "addr": "123 Main St", "ph": "555-1234"},
        {"ssn": "987-65-4321", "emp_id": "E002", "dob": "1975-08-22", "addr": "456 Oak Ave", "ph": "555-5678"},
    ]

    return ontology, data


def run_test_case(name, ontology_ttl, data_rows):
    """Run a test case and analyze confidence distribution."""

    print(f"\n{'='*70}")
    print(f"Test Case: {name}")
    print(f"{'='*70}")

    # Create temp files
    with tempfile.NamedTemporaryFile(mode='w', suffix='.ttl', delete=False) as ont_file:
        ont_file.write(ontology_ttl)
        ont_path = ont_file.name

    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='') as data_file:
        if data_rows:
            writer = csv.DictWriter(data_file, fieldnames=data_rows[0].keys())
            writer.writeheader()
            writer.writerows(data_rows)
        data_path = data_file.name

    try:
        # Generate mappings
        generator = MappingGenerator(
            ontology_file=ont_path,
            data_file=data_path,
            config=GeneratorConfig(base_iri='http://test.org/'),
            use_semantic_matching=True
        )

        mapping_config, alignment_report = generator.generate_with_alignment_report()

        # Analyze confidence distribution
        confidences = [d.confidence_score for d in alignment_report.match_details]

        if confidences:
            import statistics

            print(f"\nColumns: {len(confidences)}")
            print(f"Min confidence: {min(confidences):.3f}")
            print(f"Max confidence: {max(confidences):.3f}")
            print(f"Mean confidence: {statistics.mean(confidences):.3f}")
            print(f"Median confidence: {statistics.median(confidences):.3f}")
            print(f"Std dev: {statistics.stdev(confidences) if len(confidences) > 1 else 0:.3f}")

            # Categorize
            high = sum(1 for c in confidences if c >= 0.8)
            medium = sum(1 for c in confidences if 0.5 <= c < 0.8)
            low = sum(1 for c in confidences if c < 0.5)

            print(f"\nDistribution:")
            print(f"  High (≥0.8):   {high:2d} ({high/len(confidences)*100:.1f}%)")
            print(f"  Medium (0.5-0.8): {medium:2d} ({medium/len(confidences)*100:.1f}%)")
            print(f"  Low (<0.5):    {low:2d} ({low/len(confidences)*100:.1f}%)")

            # Print individual matches
            print(f"\nIndividual Matches:")
            for detail in alignment_report.match_details:
                prop_name = detail.matched_property.split('#')[-1].split('/')[-1]
                print(f"  {detail.column_name:15} → {prop_name:25} {detail.confidence_score:.3f}  {detail.matcher_name}")

            # Assessment
            variance_ratio = statistics.stdev(confidences) / statistics.mean(confidences) if len(confidences) > 1 else 0

            print(f"\n{'='*70}")
            if variance_ratio > 0.15:
                print("✅ GOOD variance - scores are well distributed")
            elif variance_ratio > 0.08:
                print("⚠️  MODERATE variance - some distribution but could be better")
            else:
                print("❌ LOW variance - scores are too clustered")

            if high / len(confidences) > 0.7:
                print("⚠️  Most matches are high confidence - may indicate:")
                print("    1. Clean, well-designed test data (good!)")
                print("    2. OR matchers still boosting too much (investigate)")

            return {
                'name': name,
                'count': len(confidences),
                'min': min(confidences),
                'max': max(confidences),
                'mean': statistics.mean(confidences),
                'std': statistics.stdev(confidences) if len(confidences) > 1 else 0,
                'high_pct': high / len(confidences),
                'medium_pct': medium / len(confidences),
                'low_pct': low / len(confidences)
            }

    finally:
        import os
        os.unlink(ont_path)
        os.unlink(data_path)

    return None


def main():
    print("="*70)
    print("EXTENDED CONFIDENCE CALIBRATION VALIDATION")
    print("="*70)

    results = []

    # Test 1: Mortgage (baseline - should be mostly high confidence)
    print("\n📊 Running baseline test (Mortgage)...")
    if Path('examples/mortgage/ontology/mortgage.ttl').exists():
        from rdfmap.generator.mapping_generator import MappingGenerator, GeneratorConfig
        generator = MappingGenerator(
            ontology_file='examples/mortgage/ontology/mortgage.ttl',
            data_file='examples/mortgage/data/loans.csv',
            config=GeneratorConfig(base_iri='http://test.org/'),
            use_semantic_matching=True
        )
        _, report = generator.generate_with_alignment_report()
        confidences = [d.confidence_score for d in report.match_details]
        import statistics
        results.append({
            'name': 'Mortgage (Baseline)',
            'count': len(confidences),
            'min': min(confidences),
            'max': max(confidences),
            'mean': statistics.mean(confidences),
            'std': statistics.stdev(confidences),
            'high_pct': sum(1 for c in confidences if c >= 0.8) / len(confidences),
            'medium_pct': sum(1 for c in confidences if 0.5 <= c < 0.8) / len(confidences),
            'low_pct': sum(1 for c in confidences if c < 0.5) / len(confidences)
        })

    # Test 2: Ambiguous columns
    print("\n📊 Running ambiguous columns test...")
    ont, data = create_ambiguous_test_case()
    result = run_test_case("Ambiguous Columns", ont, data)
    if result:
        results.append(result)

    # Test 3: Abbreviations
    print("\n📊 Running abbreviations test...")
    ont, data = create_abbreviation_test_case()
    result = run_test_case("Abbreviations", ont, data)
    if result:
        results.append(result)

    # Summary
    print("\n\n" + "="*70)
    print("SUMMARY ACROSS ALL TEST CASES")
    print("="*70)

    print(f"\n{'Test Case':<25} {'Count':>6} {'Mean':>6} {'Std':>6} {'High%':>7} {'Med%':>7} {'Low%':>7}")
    print("-"*70)
    for r in results:
        print(f"{r['name']:<25} {r['count']:>6} {r['mean']:>6.3f} {r['std']:>6.3f} {r['high_pct']*100:>6.1f}% {r['medium_pct']*100:>6.1f}% {r['low_pct']*100:>6.1f}%")

    print("\n" + "="*70)
    print("INTERPRETATION")
    print("="*70)

    # Calculate average high% across all tests
    avg_high_pct = sum(r['high_pct'] for r in results) / len(results) if results else 0
    avg_std = sum(r['std'] for r in results) / len(results) if results else 0

    print(f"\nAverage high confidence matches: {avg_high_pct*100:.1f}%")
    print(f"Average std deviation: {avg_std:.3f}")

    if avg_high_pct > 0.75:
        print("\n⚠️  CONCERN: >75% high confidence across diverse tests")
        print("   This suggests matchers may still be boosting too aggressively.")
        print("   Expected: ~50-60% high confidence for diverse, realistic data")
    elif avg_high_pct > 0.60:
        print("\n✅ ACCEPTABLE: 60-75% high confidence")
        print("   Reasonable distribution for well-structured test data")
    else:
        print("\n✅ GOOD: <60% high confidence")
        print("   Realistic distribution showing matcher discrimination")

    if avg_std < 0.10:
        print("\n⚠️  LOW variance: Std < 0.10")
        print("   Scores are too tightly clustered")
        print("   Recommendation: Review matcher thresholds and confidence calculations")
    else:
        print("\n✅ GOOD variance: Std ≥ 0.10")
        print("   Scores are well distributed")


if __name__ == '__main__':
    main()

