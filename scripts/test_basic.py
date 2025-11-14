#!/usr/bin/env python3
"""Simple test to verify streaming functionality works."""

import tempfile
import csv
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.rdfmap.parsers.data_source import create_parser
from src.rdfmap.emitter.graph_builder import RDFGraphBuilder
from src.rdfmap.models.errors import ProcessingReport

def test_basic_functionality():
    """Test basic RDF conversion functionality."""
    print("🧪 Testing Basic RDF Conversion...")

    # Create a small test file
    temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
    writer = csv.writer(temp_file)
    writer.writerow(['ID', 'Name', 'Age'])
    writer.writerow(['1', 'John', '25'])
    writer.writerow(['2', 'Jane', '30'])
    temp_file.close()

    test_file = Path(temp_file.name)

    try:
        # Test basic parsing
        print("  Testing parser...")
        parser = create_parser(test_file)
        row_count = 0
        for chunk in parser.parse(chunk_size=10):
            row_count += len(chunk)
            print(f"    Parsed chunk with {len(chunk)} rows")

        print(f"  ✅ Parser works: {row_count} rows total")

        # Test basic RDF generation (without full config)
        print("  Testing RDF generation...")
        from src.rdfmap.models.mapping import (
            MappingConfig, SheetMapping, RowResource, ColumnMapping,
            DefaultsConfig, ProcessingOptions
        )

        config = MappingConfig(
            namespaces={
                'ex': 'http://example.org/',
                'xsd': 'http://www.w3.org/2001/XMLSchema#'
            },
            defaults=DefaultsConfig(base_iri='http://data.example.org/'),
            sheets=[
                SheetMapping(
                    name='test',
                    source=str(test_file),
                    row_resource=RowResource(
                        **{'class': 'ex:Person'},
                        iri_template='{base_iri}person/{ID}'
                    ),
                    columns={
                        'ID': ColumnMapping(**{'as': 'ex:id', 'datatype': 'xsd:string'}),
                        'Name': ColumnMapping(**{'as': 'ex:name', 'datatype': 'xsd:string'}),
                        'Age': ColumnMapping(**{'as': 'ex:age', 'datatype': 'xsd:integer'}),
                    }
                )
            ],
            options=ProcessingOptions()
        )

        report = ProcessingReport()
        builder = RDFGraphBuilder(config, report)

        parser = create_parser(test_file)
        for chunk in parser.parse(chunk_size=10):
            builder.add_dataframe(chunk, config.sheets[0])

        graph = builder.get_graph()
        print(f"  ✅ RDF generation works: {len(graph)} triples generated")

        # Show some sample triples
        print("  Sample triples:")
        for i, (s, p, o) in enumerate(graph):
            if i < 3:  # Show first 3 triples
                print(f"    {s} {p} {o}")
            else:
                break

        print("🎉 Basic functionality test passed!")
        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        test_file.unlink()

if __name__ == "__main__":
    test_basic_functionality()
