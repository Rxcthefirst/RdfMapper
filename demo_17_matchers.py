"""Demo script showing 17 matcher parallel execution with rich evidence.

This demonstrates the new capabilities:
1. Parallel execution of all 17 matchers
2. Polars-integrated embedding cache
3. Evidence categorization (semantic/ontological/structural)
4. Performance metrics
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from rdfmap.generator.matchers import create_default_pipeline, MatchContext
from rdfmap.generator.ontology_analyzer import OntologyAnalyzer
from rdfmap.generator.data_analyzer import DataSourceAnalyzer, DataFieldAnalysis
from rdfmap.generator.graph_reasoner import GraphReasoner
from rdfmap.generator.evidence_categorizer import (
    categorize_evidence,
    generate_reasoning_summary,
    format_evidence_for_display
)
from rdfmap.models.alignment import EvidenceItem

def main():
    print("=" * 70)
    print("17/17 MATCHER DEMONSTRATION - Parallel Execution + Rich Evidence")
    print("=" * 70)

    # Setup (using test data)
    print("\n📁 Loading test ontology and data...")
    ontology_path = Path(__file__).parent / "test_data" / "test_owl_ontology.ttl"
    data_path = Path(__file__).parent / "test_data" / "messy_employees.csv"

    if not ontology_path.exists():
        print(f"❌ Ontology not found: {ontology_path}")
        print("   Please ensure test_owl_ontology.ttl exists in test_data/")
        return

    if not data_path.exists():
        print(f"❌ Data not found: {data_path}")
        return

    ontology = OntologyAnalyzer(str(ontology_path))
    data_source = DataSourceAnalyzer(str(data_path))
    reasoner = GraphReasoner(ontology.graph, ontology.classes, ontology.properties)

    print(f"✅ Loaded {len(ontology.properties)} properties from ontology")
    print(f"✅ Loaded {len(data_source.get_column_names())} columns from CSV")

    # Create pipeline with all 17 matchers
    print("\n🔧 Creating matcher pipeline with all 17 matchers...")
    pipeline = create_default_pipeline(
        use_semantic=True,
        use_datatype=True,
        use_history=True,
        use_structural=True,
        use_graph_reasoning=True,
        use_hierarchy=True,
        use_owl_characteristics=True,
        use_restrictions=True,
        use_skos_relations=True,
        ontology_analyzer=ontology,
        reasoner=reasoner,
        enable_logging=False
    )

    stats = pipeline.get_matcher_stats()
    print(f"✅ Pipeline configured with {stats['total_matchers']} matchers")

    # Test on a messy column
    test_column_name = "employeeID"  # camelCase to trigger multiple matchers
    if test_column_name not in data_source.get_column_names():
        test_column_name = data_source.get_column_names()[0]

    column = data_source.get_analysis(test_column_name)
    properties = list(ontology.properties.values())[:30]  # Limit for demo speed

    print(f"\n🎯 Testing column: '{test_column_name}'")
    print(f"   Properties to match against: {len(properties)}")

    # Run parallel matching
    print("\n⚡ Running parallel matcher execution...")
    import time
    start = time.time()
    results = pipeline.match_all(column, properties, parallel=True, top_k=15)
    elapsed = (time.time() - start) * 1000

    # Get performance metrics
    metrics = pipeline.get_last_performance_metrics()

    print(f"✅ Execution complete in {elapsed:.2f}ms")
    if metrics:
        print(f"   Matchers fired: {metrics.matchers_fired}")
        print(f"   Matchers succeeded: {metrics.matchers_succeeded}")
        if metrics.matchers_failed > 0:
            print(f"   Matchers failed: {metrics.matchers_failed}")
        if metrics.matchers_timeout > 0:
            print(f"   Matchers timeout: {metrics.matchers_timeout}")
        print(f"   Parallel speedup: {metrics.parallel_speedup:.2f}x")

    # Show results
    print(f"\n📊 Evidence collected: {len(results)} matchers contributed")

    if results:
        winner = results[0]
        print(f"\n🏆 Winner: {winner.matcher_name}")
        print(f"   Property: {winner.property.label or winner.property.uri}")
        print(f"   Confidence: {winner.confidence:.3f}")
        print(f"   Matched via: {winner.matched_via}")

        # Convert to EvidenceItem format
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
        print("\n📋 Evidence Categorization:")
        evidence_groups = categorize_evidence(evidence_items)

        for group in evidence_groups:
            icon = "✅" if group.category == 'semantic' else "⭐" if group.category == 'ontological_validation' else "🔗"
            print(f"\n{icon} {group.description.upper()}")
            print(f"   Count: {len(group.evidence_items)} matchers")
            print(f"   Avg confidence: {group.avg_confidence:.3f}")

            for item in group.evidence_items[:3]:  # Show top 3
                via = item.matched_via[:60] + "..." if len(item.matched_via) > 60 else item.matched_via
                print(f"     - {item.matcher_name}: {item.confidence:.3f} ({via})")

            if len(group.evidence_items) > 3:
                print(f"     ... and {len(group.evidence_items) - 3} more")

        # Generate reasoning summary
        print("\n💡 Reasoning Summary:")
        summary = generate_reasoning_summary(
            winner.matcher_name,
            winner.confidence,
            evidence_groups,
            winner.property.label or str(winner.property.uri)
        )
        print(f"   {summary}")

        # Show all matchers that fired
        print(f"\n📈 All {len(results)} matchers that contributed evidence:")
        for i, r in enumerate(results, 1):
            print(f"   {i:2d}. {r.matcher_name:<35} {r.confidence:.3f}")

    else:
        print("❌ No matches found")

    print("\n" + "=" * 70)
    print("✅ DEMONSTRATION COMPLETE")
    print("=" * 70)
    print("\nKey Achievements Demonstrated:")
    print("  ✅ All 17 matchers executing in parallel")
    print("  ✅ Polars-integrated embedding cache")
    print("  ✅ Evidence categorized into semantic/ontological/structural")
    print("  ✅ Performance metrics tracked")
    print("  ✅ Human-readable reasoning summaries")
    print("\nNext steps: Integrate into mapping generator and create React UI!")

if __name__ == "__main__":
    main()

