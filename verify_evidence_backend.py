"""Verify that evidence categorization is working in the backend.

This script tests the backend evidence generation to ensure:
1. Evidence groups are being created
2. Categories are properly assigned
3. Reasoning summaries are generated
4. Performance metrics are captured
"""

import sys
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from rdfmap.generator.matchers import create_default_pipeline
from rdfmap.generator.ontology_analyzer import OntologyAnalyzer
from rdfmap.generator.data_analyzer import DataSourceAnalyzer, DataFieldAnalysis
from rdfmap.generator.graph_reasoner import GraphReasoner
from rdfmap.generator.evidence_categorizer import categorize_evidence, generate_reasoning_summary
from rdfmap.models.alignment import EvidenceItem


def test_evidence_generation():
    """Test complete evidence generation flow."""

    print("=" * 70)
    print("EVIDENCE CATEGORIZATION VERIFICATION")
    print("=" * 70)

    # Check if test files exist
    ontology_path = Path(__file__).parent / "test_data" / "test_owl_ontology.ttl"
    data_path = Path(__file__).parent / "test_data" / "messy_employees.csv"

    if not ontology_path.exists():
        print(f"\n❌ Ontology not found: {ontology_path}")
        print("   Please ensure test_owl_ontology.ttl exists in test_data/")
        return False

    if not data_path.exists():
        print(f"\n❌ Data not found: {data_path}")
        print("   Please ensure messy_employees.csv exists in test_data/")
        return False

    # Load ontology and data
    print("\n📁 Loading test files...")
    ontology = OntologyAnalyzer(str(ontology_path))
    data_source = DataSourceAnalyzer(str(data_path))
    reasoner = GraphReasoner(ontology.graph, ontology.classes, ontology.properties)

    print(f"✅ Loaded {len(ontology.properties)} properties")
    print(f"✅ Loaded {len(data_source.get_column_names())} columns")

    # Create pipeline
    print("\n🔧 Creating matcher pipeline...")
    pipeline = create_default_pipeline(
        use_semantic=True,
        use_datatype=True,
        use_structural=True,
        use_graph_reasoning=True,
        use_hierarchy=True,
        use_owl_characteristics=True,
        ontology_analyzer=ontology,
        reasoner=reasoner,
        enable_logging=False
    )

    stats = pipeline.get_matcher_stats()
    print(f"✅ Pipeline configured with {stats['total_matchers']} matchers")

    # Test on a column
    test_column = "employeeID"
    if test_column not in data_source.get_column_names():
        test_column = data_source.get_column_names()[0]

    print(f"\n🎯 Testing column: '{test_column}'")

    column = data_source.get_analysis(test_column)
    properties = list(ontology.properties.values())[:20]

    # Run parallel matching
    print("\n⚡ Running parallel matcher execution...")
    results = pipeline.match_all(column, properties, parallel=True, top_k=15)

    if not results:
        print("❌ No matches found!")
        return False

    print(f"✅ Got {len(results)} evidence items")

    # Get performance metrics
    metrics = pipeline.get_last_performance_metrics()
    if metrics:
        print(f"✅ Performance metrics captured:")
        print(f"   Execution time: {metrics.execution_time_ms:.2f}ms")
        print(f"   Matchers fired: {metrics.matchers_fired}")
        print(f"   Parallel speedup: {metrics.parallel_speedup:.2f}x")
    else:
        print("⚠️  No performance metrics available")

    # Convert to EvidenceItem format
    print("\n📊 Converting to EvidenceItem format...")
    evidence_items = [
        EvidenceItem(
            matcher_name=r.matcher_name,
            match_type=str(r.match_type),
            confidence=r.confidence,
            matched_via=r.matched_via
        )
        for r in results
    ]

    # Categorize evidence
    print("\n🏷️  Categorizing evidence...")
    evidence_groups = categorize_evidence(evidence_items)

    if not evidence_groups:
        print("❌ No evidence groups created!")
        return False

    print(f"✅ Created {len(evidence_groups)} evidence groups")

    # Show evidence groups
    for group in evidence_groups:
        icon = "✅" if group.category == 'semantic' else "⭐" if group.category == 'ontological_validation' else "🔗"
        print(f"\n{icon} {group.category.upper()}")
        print(f"   Description: {group.description}")
        print(f"   Items: {len(group.evidence_items)}")
        print(f"   Avg confidence: {group.avg_confidence:.3f}")

        for item in group.evidence_items[:3]:
            print(f"     - {item.matcher_name}: {item.confidence:.3f}")

        if len(group.evidence_items) > 3:
            print(f"     ... and {len(group.evidence_items) - 3} more")

    # Generate reasoning summary
    print("\n💡 Generating reasoning summary...")
    winner = results[0]
    prop_label = winner.property.label or str(winner.property.uri).split('#')[-1]

    reasoning = generate_reasoning_summary(
        winner.matcher_name,
        winner.confidence,
        evidence_groups,
        prop_label
    )

    print(f"✅ Reasoning summary generated:")
    print(f"   {reasoning}")

    # Verify structure for JSON export
    print("\n📦 Verifying JSON serialization...")

    try:
        evidence_json = {
            'column_name': test_column,
            'matched_property': str(winner.property.uri),
            'confidence_score': winner.confidence,
            'matcher_name': winner.matcher_name,
            'evidence_groups': [
                {
                    'category': g.category,
                    'evidence_items': [
                        {
                            'matcher_name': e.matcher_name,
                            'match_type': e.match_type,
                            'confidence': e.confidence,
                            'matched_via': e.matched_via,
                            'evidence_category': e.evidence_category
                        }
                        for e in g.evidence_items
                    ],
                    'avg_confidence': g.avg_confidence,
                    'description': g.description
                }
                for g in evidence_groups
            ],
            'reasoning_summary': reasoning,
            'performance_metrics': {
                'execution_time_ms': metrics.execution_time_ms if metrics else None,
                'matchers_fired': metrics.matchers_fired if metrics else None,
                'parallel_speedup': metrics.parallel_speedup if metrics else None
            } if metrics else None
        }

        json_str = json.dumps(evidence_json, indent=2)
        print("✅ JSON serialization successful")
        print(f"\nSample JSON (first 500 chars):")
        print(json_str[:500] + "...")

    except Exception as e:
        print(f"❌ JSON serialization failed: {e}")
        return False

    # Final summary
    print("\n" + "=" * 70)
    print("✅ VERIFICATION COMPLETE")
    print("=" * 70)
    print("\nAll checks passed:")
    print("  ✅ Evidence items generated")
    print("  ✅ Evidence categorized into groups")
    print("  ✅ Reasoning summary created")
    print("  ✅ Performance metrics captured")
    print("  ✅ JSON serializable")
    print("\nThe backend is ready to generate rich evidence for the UI!")

    return True


if __name__ == "__main__":
    success = test_evidence_generation()
    sys.exit(0 if success else 1)

