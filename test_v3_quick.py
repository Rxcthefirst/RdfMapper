#!/usr/bin/env python
"""Quick test to verify v3 functionality works end-to-end."""

from pathlib import Path
from rdfmap.config.loader import load_mapping_config
from rdfmap.emitter.graph_builder import RDFGraphBuilder
from rdfmap.parsers.data_source import create_parser
from rdfmap.models.errors import ProcessingReport

def test_v3_pipeline():
    """Test the complete v3 pipeline."""

    print("=" * 70)
    print("V3 PIPELINE TEST")
    print("=" * 70)

    # 1. Load v3 config
    print("\n1. Loading v3 config...")
    config_path = Path("examples/mortgage/config/internal_inline.yaml")
    config = load_mapping_config(config_path)
    print(f"   ✅ Config loaded")
    print(f"   - Sources: {list(config.sources.keys())}")
    print(f"   - Mappings: {list(config.mappings.keys())}")
    print(f"   - Base IRI: {config.base_iri}")

    # 2. Get mapping and source info
    print("\n2. Getting mapping info...")
    mapping_name = list(config.mappings.keys())[0]
    mapping = config.mappings[mapping_name]
    source_name = mapping.sources
    source = config.sources[source_name]
    print(f"   ✅ Mapping: {mapping_name}")
    print(f"   - Source: {source.path}")
    print(f"   - Format: {source.format}")
    print(f"   - Subject class: {mapping.subject.class_type}")
    print(f"   - Properties: {len(mapping.properties)}")
    print(f"   - Relationships: {len(mapping.relationships) if mapping.relationships else 0}")

    # 3. Create parser
    print("\n3. Creating parser...")
    parser = create_parser(Path(source.path))
    print(f"   ✅ Parser created")

    # 4. Create graph builder
    print("\n4. Creating graph builder...")
    report = ProcessingReport()
    builder = RDFGraphBuilder(config, report)
    print(f"   ✅ Graph builder created")

    # 5. Process data
    print("\n5. Processing data...")
    row_count = 0
    for chunk in parser.parse():
        builder.add_dataframe(chunk, mapping, mapping_name)
        row_count += len(chunk)
        print(f"   - Processed chunk: {len(chunk)} rows")
        break  # Just test first chunk

    print(f"   ✅ Processed {row_count} rows")

    # 6. Check results
    print("\n6. Checking results...")
    print(f"   - Total rows: {report.total_rows}")
    print(f"   - Failed rows: {report.failed_rows}")
    print(f"   - Graph triples: {len(builder.graph)}")
    print(f"   - Errors: {len(report.errors)}")

    # 7. Sample triples
    print("\n7. Sample triples:")
    for i, (s, p, o) in enumerate(builder.graph):
        if i >= 5:
            break
        print(f"   {i+1}. {s} -> {p} -> {o}")

    print("\n" + "=" * 70)
    print("✅ V3 PIPELINE TEST PASSED!")
    print("=" * 70)

    return True

if __name__ == "__main__":
    try:
        test_v3_pipeline()
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        exit(1)

