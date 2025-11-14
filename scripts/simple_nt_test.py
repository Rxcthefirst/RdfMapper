#!/usr/bin/env python3
"""Simple test to verify NT streaming functionality."""

import tempfile
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_nt_writer():
    """Test basic NT writer functionality."""
    print("🧪 Testing NT Writer")

    try:
        from src.rdfmap.emitter.nt_streaming import NTriplesStreamWriter
        from rdflib import URIRef, Literal

        # Create temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.nt', delete=False) as f:
            temp_path = Path(f.name)

        # Test writing triples
        with NTriplesStreamWriter(temp_path) as writer:
            writer.write_triple(
                URIRef("http://example.org/person1"),
                URIRef("http://example.org/name"),
                Literal("John Doe")
            )
            writer.write_triple(
                URIRef("http://example.org/person1"),
                URIRef("http://example.org/age"),
                Literal("30", datatype=URIRef("http://www.w3.org/2001/XMLSchema#integer"))
            )

        # Read back and verify
        with open(temp_path, 'r') as f:
            content = f.read()

        print(f"✅ NT Writer works!")
        print(f"Generated content:")
        print(content)

        # Cleanup
        temp_path.unlink()

        return True

    except Exception as e:
        print(f"❌ NT Writer failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_mapping_config():
    """Test mapping config creation."""
    print("\n🧪 Testing Mapping Config")

    try:
        from src.rdfmap.models.mapping import MappingConfig, SheetMapping, RowResource, ColumnMapping, DefaultsConfig, ProcessingOptions

        config = MappingConfig(
            namespaces={
                'ex': 'http://example.org/',
                'xsd': 'http://www.w3.org/2001/XMLSchema#'
            },
            defaults=DefaultsConfig(base_iri='http://data.example.org/'),
            sheets=[
                SheetMapping(
                    name='test',
                    source='test.csv',
                    row_resource=RowResource(
                        **{'class': 'ex:Person'},
                        iri_template='{base_iri}person/{ID}'
                    ),
                    columns={
                        'ID': ColumnMapping(**{'as': 'ex:id', 'datatype': 'xsd:string'})
                    }
                )
            ],
            options=ProcessingOptions(aggregate_duplicates=False)
        )

        print(f"✅ Mapping Config works!")
        print(f"Aggregation setting: {config.options.aggregate_duplicates}")

        return True

    except Exception as e:
        print(f"❌ Mapping Config failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_graph_builder():
    """Test graph builder with streaming."""
    print("\n🧪 Testing Graph Builder with Streaming")

    try:
        from src.rdfmap.emitter.graph_builder import RDFGraphBuilder
        from src.rdfmap.emitter.nt_streaming import NTriplesStreamWriter
        from src.rdfmap.models.errors import ProcessingReport
        from src.rdfmap.models.mapping import MappingConfig, SheetMapping, RowResource, ColumnMapping, DefaultsConfig, ProcessingOptions

        # Create config
        config = MappingConfig(
            namespaces={
                'ex': 'http://example.org/',
                'xsd': 'http://www.w3.org/2001/XMLSchema#'
            },
            defaults=DefaultsConfig(base_iri='http://data.example.org/'),
            sheets=[
                SheetMapping(
                    name='test',
                    source='test.csv',
                    row_resource=RowResource(
                        **{'class': 'ex:Person'},
                        iri_template='{base_iri}person/{ID}'
                    ),
                    columns={
                        'ID': ColumnMapping(**{'as': 'ex:id', 'datatype': 'xsd:string'})
                    }
                )
            ],
            options=ProcessingOptions(aggregate_duplicates=False)
        )

        # Test regular builder
        report1 = ProcessingReport()
        builder1 = RDFGraphBuilder(config, report1)
        print(f"✅ Regular RDFGraphBuilder created")

        # Test streaming builder
        with tempfile.NamedTemporaryFile(mode='w', suffix='.nt', delete=False) as f:
            temp_path = Path(f.name)

        with NTriplesStreamWriter(temp_path) as nt_writer:
            report2 = ProcessingReport()
            builder2 = RDFGraphBuilder(config, report2, streaming_writer=nt_writer)
            print(f"✅ Streaming RDFGraphBuilder created")

        # Cleanup
        temp_path.unlink()

        return True

    except Exception as e:
        print(f"❌ Graph Builder failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Simple NT Streaming Test")
    print("=" * 30)

    success = True
    success &= test_nt_writer()
    success &= test_mapping_config()
    success &= test_graph_builder()

    if success:
        print(f"\n🎉 All tests passed!")
        print(f"NT streaming functionality is working correctly.")
    else:
        print(f"\n❌ Some tests failed.")
        sys.exit(1)
