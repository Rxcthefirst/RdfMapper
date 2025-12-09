#!/usr/bin/env python3
"""
Test script to verify RML support for multiple data source formats.

Tests:
- CSV (already working)
- XLSX (Excel)
- TSV (Tab-separated)
- JSON
- XML

Usage:
    python test_rml_formats.py
"""

import polars as pl
from pathlib import Path

def create_test_data():
    """Create test data in multiple formats."""

    # Sample loan data
    data = {
        'LoanID': ['L-001', 'L-002', 'L-003'],
        'BorrowerID': ['B-001', 'B-002', 'B-003'],
        'BorrowerName': ['Alice Johnson', 'Bob Smith', 'Carol Lee'],
        'PropertyID': ['P-001', 'P-002', 'P-003'],
        'PropertyAddress': ['123 Oak St', '456 Elm Ave', '789 Pine Rd'],
        'Principal': [250000, 350000, 180000],
        'InterestRate': [0.0425, 0.0525, 0.0375],
        'OriginationDate': ['2023-01-15', '2023-03-20', '2023-05-10'],
        'LoanTerm': [360, 240, 300],
        'Status': ['Active', 'Active', 'Paid Off']
    }

    df = pl.DataFrame(data)

    # Create test_formats directory
    test_dir = Path('../test_formats')
    test_dir.mkdir(exist_ok=True)

    print("Creating test data files...")

    # 1. CSV (baseline)
    csv_file = test_dir / 'loans.csv'
    df.write_csv(csv_file)
    print(f"✅ Created: {csv_file}")

    # 2. TSV (tab-separated)
    tsv_file = test_dir / 'loans.tsv'
    df.write_csv(tsv_file, separator='\t')
    print(f"✅ Created: {tsv_file}")

    # 3. XLSX (Excel) - requires xlsxwriter
    try:
        xlsx_file = test_dir / 'loans.xlsx'
        df.write_excel(xlsx_file)
        print(f"✅ Created: {xlsx_file}")
    except Exception as e:
        print(f"⚠️  XLSX creation skipped: {e}")
        print("   Install: pip install xlsxwriter")

    # 4. JSON (records format)
    json_file = test_dir / 'loans.json'
    try:
        # Try newer polars API
        df.write_json(json_file)
    except:
        # Fallback to manual JSON creation
        import json
        records = df.to_dicts()
        with open(json_file, 'w') as f:
            json.dump(records, f, indent=2)
    print(f"✅ Created: {json_file}")

    # 5. XML (manual creation - polars doesn't have direct XML write)
    xml_file = test_dir / 'loans.xml'
    create_xml_file(df, xml_file)
    print(f"✅ Created: {xml_file}")

    print(f"\n📁 All test files created in: {test_dir}")
    return test_dir

def create_xml_file(df, output_path):
    """Create XML file from dataframe."""
    xml_content = '<?xml version="1.0" encoding="UTF-8"?>\n<loans>\n'

    for row in df.iter_rows(named=True):
        xml_content += '  <loan>\n'
        for key, value in row.items():
            xml_content += f'    <{key}>{value}</{key}>\n'
        xml_content += '  </loan>\n'

    xml_content += '</loans>'

    with open(output_path, 'w') as f:
        f.write(xml_content)

def create_rml_mappings(test_dir):
    """Create RML mappings for each format."""

    print("\nCreating RML mapping files...")

    # Common prefixes
    prefixes = """@prefix ex: <https://example.com/mortgage#> .
@prefix ql: <http://semweb.mmlab.be/ns/ql#> .
@prefix rml: <http://semweb.mmlab.be/ns/rml#> .
@prefix rr: <http://www.w3.org/ns/r2rml#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

"""

    # Common predicate-object maps
    po_maps = """    rr:predicateObjectMap [
        rr:predicate ex:loanNumber ;
        rr:objectMap [ rml:reference "LoanID" ; rr:datatype xsd:string ]
    ] ;
    rr:predicateObjectMap [
        rr:predicate ex:principalAmount ;
        rr:objectMap [ rml:reference "Principal" ; rr:datatype xsd:integer ]
    ] ;
    rr:predicateObjectMap [
        rr:predicate ex:interestRate ;
        rr:objectMap [ rml:reference "InterestRate" ; rr:datatype xsd:decimal ]
    ] ;
    rr:predicateObjectMap [
        rr:predicate ex:hasBorrower ;
        rr:objectMap [ rr:parentTriplesMap <http://example.org/borrowerMapping> ]
    ] ;
    rr:predicateObjectMap [
        rr:predicate ex:collateralProperty ;
        rr:objectMap [ rr:parentTriplesMap <http://example.org/propertyMapping> ]
    ] ."""

    borrower_map = """
<http://example.org/borrowerMapping> a rr:TriplesMap ;
    rml:logicalSource [ 
        rml:referenceFormulation {ref_formulation} ;
        rml:source "{source}"{iterator}
    ] ;
    rr:subjectMap [
        rr:class ex:Borrower ;
        rr:template "http://example.org/borrower/{{BorrowerID}}"
    ] ;
    rr:predicateObjectMap [
        rr:predicate ex:borrowerName ;
        rr:objectMap [ rml:reference "BorrowerName" ; rr:datatype xsd:string ]
    ] .

<http://example.org/propertyMapping> a rr:TriplesMap ;
    rml:logicalSource [ 
        rml:referenceFormulation {ref_formulation} ;
        rml:source "{source}"{iterator}
    ] ;
    rr:subjectMap [
        rr:class ex:Property ;
        rr:template "http://example.org/property/{{PropertyID}}"
    ] ;
    rr:predicateObjectMap [
        rr:predicate ex:propertyAddress ;
        rr:objectMap [ rml:reference "PropertyAddress" ; rr:datatype xsd:string ]
    ] .
"""

    # 1. CSV RML
    csv_rml = prefixes + f"""<http://example.org/loansMapping> a rr:TriplesMap ;
    rml:logicalSource [ 
        rml:referenceFormulation ql:CSV ;
        rml:source "loans.csv"
    ] ;
    rr:subjectMap [
        rr:class ex:MortgageLoan ;
        rr:template "http://example.org/loan/{{LoanID}}"
    ] ;
{po_maps}
""" + borrower_map.format(ref_formulation='ql:CSV', source='loans.csv', iterator='')

    (test_dir / 'mapping_csv.rml.ttl').write_text(csv_rml)
    print(f"✅ Created: {test_dir}/mapping_csv.rml.ttl")

    # 2. TSV RML (same as CSV but different source)
    tsv_rml = prefixes + f"""<http://example.org/loansMapping> a rr:TriplesMap ;
    rml:logicalSource [ 
        rml:referenceFormulation ql:CSV ;
        rml:source "loans.tsv"
    ] ;
    rr:subjectMap [
        rr:class ex:MortgageLoan ;
        rr:template "http://example.org/loan/{{LoanID}}"
    ] ;
{po_maps}
""" + borrower_map.format(ref_formulation='ql:CSV', source='loans.tsv', iterator='')

    (test_dir / 'mapping_tsv.rml.ttl').write_text(tsv_rml)
    print(f"✅ Created: {test_dir}/mapping_tsv.rml.ttl")

    # 3. JSON RML
    json_rml = prefixes + f"""<http://example.org/loansMapping> a rr:TriplesMap ;
    rml:logicalSource [ 
        rml:referenceFormulation ql:JSONPath ;
        rml:source "loans.json" ;
        rml:iterator "$[*]"
    ] ;
    rr:subjectMap [
        rr:class ex:MortgageLoan ;
        rr:template "http://example.org/loan/{{LoanID}}"
    ] ;
{po_maps}
""" + borrower_map.format(ref_formulation='ql:JSONPath', source='loans.json', iterator=' ;\n        rml:iterator "$[*]"')

    (test_dir / 'mapping_json.rml.ttl').write_text(json_rml)
    print(f"✅ Created: {test_dir}/mapping_json.rml.ttl")

    # 4. XML RML
    xml_rml = prefixes + f"""<http://example.org/loansMapping> a rr:TriplesMap ;
    rml:logicalSource [ 
        rml:referenceFormulation ql:XPath ;
        rml:source "loans.xml" ;
        rml:iterator "/loans/loan"
    ] ;
    rr:subjectMap [
        rr:class ex:MortgageLoan ;
        rr:template "http://example.org/loan/{{LoanID}}"
    ] ;
{po_maps}
""" + borrower_map.format(ref_formulation='ql:XPath', source='loans.xml', iterator=' ;\n        rml:iterator "/loans/loan"')

    (test_dir / 'mapping_xml.rml.ttl').write_text(xml_rml)
    print(f"✅ Created: {test_dir}/mapping_xml.rml.ttl")

def create_test_configs(test_dir):
    """Create config files for each format."""

    print("\nCreating test configuration files...")

    config_template = """options:
  on_error: report
  skip_empty_values: true
  chunk_size: 1000
  output_format: ttl

mapping:
  file: {mapping_file}
"""

    formats = ['csv', 'tsv', 'json', 'xml']

    for fmt in formats:
        config_file = test_dir / f'config_{fmt}.yaml'
        # Use just the filename since config is in same directory as mapping
        config_content = config_template.format(mapping_file=f'mapping_{fmt}.rml.ttl')
        config_file.write_text(config_content)
        print(f"✅ Created: {config_file}")

def run_conversion_tests():
    """Run conversion tests for all formats."""

    print("\n" + "="*60)
    print("RUNNING CONVERSION TESTS")
    print("="*60)

    test_dir = Path('../test_formats')
    formats = ['csv', 'tsv', 'json', 'xml']

    results = {}

    for fmt in formats:
        print(f"\n📝 Testing {fmt.upper()} format...")
        config_file = test_dir / f'config_{fmt}.yaml'
        output_file = test_dir / f'output_{fmt}.ttl'

        if not config_file.exists():
            print(f"   ⚠️  Config file not found: {config_file}")
            results[fmt] = "SKIP"
            continue

        # Run conversion
        import subprocess
        cmd = [
            'rdfmap', 'convert',
            '-m', str(config_file),
            '-o', str(output_file),
            '--limit', '3'
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode == 0 and output_file.exists():
                # Check output has content
                output_content = output_file.read_text()

                # Count entities
                loan_count = output_content.count('ex:MortgageLoan')
                borrower_count = output_content.count('ex:Borrower')
                property_count = output_content.count('ex:Property')

                if loan_count > 0 and borrower_count > 0 and property_count > 0:
                    results[fmt] = "✅ PASS"
                    print(f"   ✅ Success!")
                    print(f"      - {loan_count} Loans")
                    print(f"      - {borrower_count} Borrowers")
                    print(f"      - {property_count} Properties")
                else:
                    results[fmt] = "⚠️  INCOMPLETE"
                    print(f"   ⚠️  Missing entities")
                    print(f"      - {loan_count} Loans (expected 3)")
                    print(f"      - {borrower_count} Borrowers (expected 3)")
                    print(f"      - {property_count} Properties (expected 3)")
            else:
                results[fmt] = "❌ FAIL"
                print(f"   ❌ Failed")
                if result.stderr:
                    print(f"      Error: {result.stderr[:200]}")

        except subprocess.TimeoutExpired:
            results[fmt] = "⏱️  TIMEOUT"
            print(f"   ⏱️  Timeout (>30s)")
        except Exception as e:
            results[fmt] = f"❌ ERROR"
            print(f"   ❌ Error: {str(e)[:100]}")

    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    for fmt, result in results.items():
        print(f"{fmt.upper():10} {result}")

    # Overall status
    print("\n" + "="*60)
    passed = sum(1 for r in results.values() if r == "✅ PASS")
    total = len(results)

    if passed == total:
        print(f"✅ ALL TESTS PASSED ({passed}/{total})")
    elif passed > 0:
        print(f"⚠️  PARTIAL SUCCESS ({passed}/{total} passed)")
    else:
        print(f"❌ ALL TESTS FAILED (0/{total})")

    print("="*60)

if __name__ == "__main__":
    print("="*60)
    print("RML FORMAT COMPATIBILITY TEST SUITE")
    print("="*60)

    # Create test data
    test_dir = create_test_data()

    # Create RML mappings
    create_rml_mappings(test_dir)

    # Create config files
    create_test_configs(test_dir)

    # Run tests
    run_conversion_tests()

    print("\n✅ Test suite complete!")
    print(f"📁 Test files location: {test_dir.absolute()}")

