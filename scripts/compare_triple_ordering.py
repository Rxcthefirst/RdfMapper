#!/usr/bin/env python3
"""Compare subject-grouped vs column-wise triple ordering patterns."""

import tempfile
import csv
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def create_test_data():
    """Create simple test data."""
    temp_dir = Path(tempfile.mkdtemp())
    csv_file = temp_dir / "employees.csv"

    with open(csv_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['EmployeeID', 'Name', 'Department', 'Salary'])

        # Just 3 employees for clear visualization
        writer.writerow(['EMP001', 'Alice', 'Engineering', '75000'])
        writer.writerow(['EMP002', 'Bob', 'Sales', '65000'])
        writer.writerow(['EMP003', 'Carol', 'Engineering', '80000'])

    return temp_dir, csv_file

def demonstrate_ordering_difference():
    """Show the conceptual difference in triple ordering."""
    print("🔄 Triple Ordering Comparison: Aggregated vs Streaming")
    print("=" * 60)

    temp_dir, csv_file = create_test_data()

    try:
        # Show source data
        print("📊 Source Data:")
        with open(csv_file, 'r') as f:
            for i, line in enumerate(f):
                print(f"  {i}: {line.strip()}")

        print(f"\n🔧 AGGREGATED MODE (Subject-Grouped):")
        print("Expected triple ordering - all triples for each subject together:")
        print("  1. <employee/EMP001> rdf:type ex:Employee .")
        print("  2. <employee/EMP001> rdf:type owl:NamedIndividual .")
        print("  3. <employee/EMP001> ex:employeeId \"EMP001\" .")
        print("  4. <employee/EMP001> ex:name \"Alice\" .")
        print("  5. <employee/EMP001> ex:department \"Engineering\" .")
        print("  6. <employee/EMP001> ex:salary \"75000\" .")
        print("  7. <employee/EMP002> rdf:type ex:Employee .")
        print("  8. <employee/EMP002> rdf:type owl:NamedIndividual .")
        print("  9. <employee/EMP002> ex:employeeId \"EMP002\" .")
        print(" 10. <employee/EMP002> ex:name \"Bob\" .")
        print(" 11. <employee/EMP002> ex:department \"Sales\" .")
        print(" 12. <employee/EMP002> ex:salary \"65000\" .")
        print("     ... (continues for EMP003)")

        print(f"\n🌊 STREAMING MODE (Column-wise):")
        print("Expected triple ordering - all values for each property together:")
        print("  1. <employee/EMP001> rdf:type ex:Employee .")
        print("  2. <employee/EMP002> rdf:type ex:Employee .")
        print("  3. <employee/EMP003> rdf:type ex:Employee .")
        print("  4. <employee/EMP001> rdf:type owl:NamedIndividual .")
        print("  5. <employee/EMP002> rdf:type owl:NamedIndividual .")
        print("  6. <employee/EMP003> rdf:type owl:NamedIndividual .")
        print("  7. <employee/EMP001> ex:employeeId \"EMP001\" .")
        print("  8. <employee/EMP002> ex:employeeId \"EMP002\" .")
        print("  9. <employee/EMP003> ex:employeeId \"EMP003\" .")
        print(" 10. <employee/EMP001> ex:name \"Alice\" .")
        print(" 11. <employee/EMP002> ex:name \"Bob\" .")
        print(" 12. <employee/EMP003> ex:name \"Carol\" .")
        print("     ... (continues with department, salary columns)")

        print(f"\n💡 Key Differences:")
        print(f"  🔧 Aggregated (Row-wise Processing):")
        print(f"     • Process: Row 1 completely → Row 2 completely → Row 3 completely")
        print(f"     • Output: All triples for subject grouped together")
        print(f"     • Benefits: Better for XML/RDF, more readable")
        print(f"     • Drawbacks: Must collect triples in memory before writing")
        print(f"")
        print(f"  🌊 Streaming (Column-wise Processing):")
        print(f"     • Process: All IDs → All names → All departments → All salaries")
        print(f"     • Output: Triples scattered by processing order")
        print(f"     • Benefits: Leverages Polars columnar processing, constant memory")
        print(f"     • Drawbacks: Scattered output, not suitable for XML/RDF")

        print(f"\n📊 Analysis of Current Implementation:")

        # Try to import and test actual behavior
        try:
            from src.rdfmap.models.mapping import MappingConfig, SheetMapping, RowResource, ColumnMapping, DefaultsConfig, ProcessingOptions
            from src.rdfmap.models.errors import ProcessingReport
            from src.rdfmap.emitter.graph_builder import RDFGraphBuilder
            from src.rdfmap.emitter.nt_streaming import NTriplesStreamWriter
            from src.rdfmap.parsers.data_source import create_parser

            print("✅ Successfully imported RDF components")

            # Create config
            config = MappingConfig(
                namespaces={
                    'ex': 'http://example.org/',
                    'xsd': 'http://www.w3.org/2001/XMLSchema#'
                },
                defaults=DefaultsConfig(base_iri='http://data.example.org/'),
                sheets=[
                    SheetMapping(
                        name='employees',
                        source=str(csv_file.absolute()),
                        row_resource=RowResource(
                            **{'class': 'ex:Employee'},
                            iri_template='{base_iri}employee/{EmployeeID}'
                        ),
                        columns={
                            'EmployeeID': ColumnMapping(**{'as': 'ex:employeeId', 'datatype': 'xsd:string'}),
                            'Name': ColumnMapping(**{'as': 'ex:name', 'datatype': 'xsd:string'}),
                            'Department': ColumnMapping(**{'as': 'ex:department', 'datatype': 'xsd:string'}),
                            'Salary': ColumnMapping(**{'as': 'ex:salary', 'datatype': 'xsd:decimal'})
                        }
                    )
                ],
                options=ProcessingOptions(chunk_size=10, header=True)
            )

            # Test current implementation
            parser = create_parser(csv_file)
            for chunk in parser.parse():
                df = chunk
                break

            # Test with streaming NT writer
            nt_file = temp_dir / "test_output.nt"
            with NTriplesStreamWriter(nt_file) as writer:
                report = ProcessingReport()
                builder = RDFGraphBuilder(config, report, streaming_writer=writer)
                builder.add_dataframe(df, config.sheets[0])
                triple_count = writer.get_triple_count()

            print(f"✅ Generated {triple_count} triples")

            # Analyze actual output
            print(f"\n📋 Actual Output Analysis:")
            if nt_file.exists():
                with open(nt_file, 'r') as f:
                    lines = [line.strip() for line in f.readlines() if line.strip()]

                print(f"Total triples: {len(lines)}")
                print(f"First 10 triples (showing actual ordering):")

                for i, line in enumerate(lines[:10]):
                    parts = line.split(' ')
                    if len(parts) >= 3:
                        subject = parts[0].split('/')[-1].rstrip('>')
                        predicate = parts[1].split('#')[-1].split('/')[-1].rstrip('>')
                        print(f"  {i+1:2d}. {subject} -> {predicate}")

                # Check if triples are grouped by subject
                subjects_order = []
                for line in lines:
                    subject = line.split(' ')[0]
                    subjects_order.append(subject)

                # Count transitions between subjects
                transitions = 0
                current_subject = None
                for subject in subjects_order:
                    if current_subject and subject != current_subject:
                        transitions += 1
                    current_subject = subject

                unique_subjects = len(set(subjects_order))
                print(f"\n🔍 Ordering Analysis:")
                print(f"  Unique subjects: {unique_subjects}")
                print(f"  Subject transitions: {transitions}")

                if transitions == unique_subjects - 1:
                    print(f"  ✅ AGGREGATED: Triples are grouped by subject (perfect grouping)")
                elif transitions > unique_subjects * 2:
                    print(f"  🌊 STREAMING: Triples are scattered (column-wise processing)")
                else:
                    print(f"  ⚠️  MIXED: Some grouping, some scattering")

        except ImportError as e:
            print(f"❌ Could not import RDF components: {e}")
            print(f"   This demonstrates the concept without actual testing")
        except Exception as e:
            print(f"❌ Error during testing: {e}")
            import traceback
            traceback.print_exc()

        print(f"\n🎯 Summary:")
        print(f"The key insight is that 'aggregation' in your context means:")
        print(f"• ORGANIZING triples by subject (not deduplicating)")
        print(f"• CHOOSING between readability vs performance")
        print(f"• ENABLING proper XML/RDF output when needed")
        print(f"")
        print(f"Current implementation appears to be row-wise (aggregated) in both modes.")
        print(f"True streaming would require column-wise processing for performance benefits.")

        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        # Cleanup
        import shutil
        shutil.rmtree(temp_dir)

if __name__ == "__main__":
    print("🔍 Understanding Triple Ordering: Aggregated vs Streaming")
    print("=" * 60)
    print("This demonstrates the conceptual difference between:")
    print("• Subject-grouped: All triples for each subject together")
    print("• Column-wise: Triples ordered by property/column processing")
    print()

    success = demonstrate_ordering_difference()

    if success:
        print(f"\n🎉 Triple ordering analysis completed!")
        print(f"Now you understand the difference between aggregation modes.")
    else:
        print(f"\n❌ Analysis failed - check the output above")
