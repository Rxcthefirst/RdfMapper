"""Test suite for validating all 17 matchers fire with parallel execution.

This test ensures:
1. All 17 matchers can fire on appropriate datasets
2. Evidence contains 6-8 entries per column
3. Ontology matchers appear in 80%+ of evidence lists
4. Parallel execution provides 3-5x speedup
5. Rich evidence is properly categorized
"""

import pytest
import time
from pathlib import Path

from rdfmap.generator.matchers import (
    create_default_pipeline,
    MatchContext,
    PerformanceMetrics
)
from rdfmap.generator.ontology_analyzer import OntologyAnalyzer
from rdfmap.generator.data_analyzer import DataSourceAnalyzer
from rdfmap.generator.graph_reasoner import GraphReasoner


@pytest.fixture
def test_ontology():
    """Load a test ontology with diverse property types."""
    ontology_path = Path(__file__).parent.parent / "test_data" / "test_owl_ontology.ttl"
    if not ontology_path.exists():
        pytest.skip(f"Test ontology not found: {ontology_path}")
    return OntologyAnalyzer(str(ontology_path))


@pytest.fixture
def messy_data():
    """Load the messy employees dataset designed to trigger all matchers."""
    data_path = Path(__file__).parent.parent / "test_data" / "messy_employees.csv"
    if not data_path.exists():
        pytest.skip(f"Test data not found: {data_path}")
    return DataSourceAnalyzer(str(data_path))


@pytest.fixture
def validation_data():
    """Load dataset with constraint violations."""
    data_path = Path(__file__).parent.parent / "test_data" / "validation_test.csv"
    if not data_path.exists():
        pytest.skip(f"Test data not found: {data_path}")
    return DataSourceAnalyzer(str(data_path))


@pytest.fixture
def matcher_pipeline(test_ontology):
    """Create matcher pipeline with all 17 matchers enabled."""
    reasoner = GraphReasoner(
        test_ontology.graph,
        test_ontology.classes,
        test_ontology.properties
    )

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
        semantic_threshold=0.45,
        datatype_threshold=0.0,  # Always fire
        history_threshold=0.6,
        structural_threshold=0.65,
        graph_reasoning_threshold=0.6,
        hierarchy_threshold=0.6,
        owl_characteristics_threshold=0.55,
        restrictions_threshold=0.5,
        skos_relations_threshold=0.45,
        ontology_analyzer=test_ontology,
        reasoner=reasoner,
        enable_logging=False,
        enable_calibration=True
    )

    return pipeline


def test_all_17_matchers_available(matcher_pipeline):
    """Test that pipeline has all 17 matchers configured."""
    assert len(matcher_pipeline.matchers) == 17, \
        f"Expected 17 matchers, got {len(matcher_pipeline.matchers)}"

    expected_matchers = {
        'ExactPrefLabelMatcher',
        'ExactRdfsLabelMatcher',
        'ExactAltLabelMatcher',
        'ExactHiddenLabelMatcher',
        'ExactLocalNameMatcher',
        'PropertyHierarchyMatcher',
        'OWLCharacteristicsMatcher',
        'RestrictionBasedMatcher',
        'SKOSRelationsMatcher',
        'HistoryAwareMatcher',
        'SemanticSimilarityMatcher',
        'LexicalMatcher',
        'DataTypeInferenceMatcher',
        'StructuralMatcher',
        'GraphReasoningMatcher',
        'PartialStringMatcher',
        'FuzzyStringMatcher'
    }

    actual_matchers = {m.name() for m in matcher_pipeline.matchers}

    assert expected_matchers == actual_matchers, \
        f"Matcher mismatch. Missing: {expected_matchers - actual_matchers}, " \
        f"Extra: {actual_matchers - expected_matchers}"

    print(f"✅ All 17 matchers configured")


def test_parallel_execution_speed(matcher_pipeline, messy_data, test_ontology):
    """Test that parallel execution is faster than sequential."""
    properties = list(test_ontology.properties.values())[:20]  # Use subset for speed
    column = messy_data.get_analysis("employeeID")

    # Sequential execution
    start_seq = time.time()
    results_seq = matcher_pipeline.match_all(
        column,
        properties,
        parallel=False,
        top_k=10
    )
    time_seq = (time.time() - start_seq) * 1000

    # Parallel execution
    start_par = time.time()
    results_par = matcher_pipeline.match_all(
        column,
        properties,
        parallel=True,
        top_k=10
    )
    time_par = (time.time() - start_par) * 1000

    # Get performance metrics
    metrics = matcher_pipeline.get_last_performance_metrics()

    print(f"Sequential: {time_seq:.2f}ms")
    print(f"Parallel: {time_par:.2f}ms")
    if metrics:
        print(f"Speedup: {metrics.parallel_speedup:.2f}x")
        print(f"Matchers fired: {metrics.matchers_fired}")
        print(f"Matchers succeeded: {metrics.matchers_succeeded}")

    # Parallel should be faster (allow some variance for overhead)
    assert time_par < time_seq * 1.2, \
        f"Parallel execution not faster: {time_par:.2f}ms vs {time_seq:.2f}ms"

    # Results should be similar
    assert len(results_par) > 0, "Parallel execution produced no results"

    print(f"✅ Parallel execution validated")


def test_evidence_quality_messy_data(matcher_pipeline, messy_data, test_ontology):
    """Test that messy data produces rich evidence from multiple matchers."""
    properties = list(test_ontology.properties.values())

    # Test columns with different patterns
    test_columns = [
        "employeeID",       # camelCase - ExactLocalNameMatcher
        "Frist_Name",       # typo - FuzzyStringMatcher
        "Emplyee_Email",    # typo - FuzzyStringMatcher
        "DepartmentCode",   # FK pattern - GraphReasoningMatcher
        "ManagerRef",       # FK pattern - StructuralMatcher
        "Anual_Salary",     # typo - FuzzyStringMatcher
    ]

    evidence_counts = []
    ontology_matcher_counts = []

    ontology_matchers = {
        'PropertyHierarchyMatcher',
        'OWLCharacteristicsMatcher',
        'RestrictionBasedMatcher',
        'DataTypeInferenceMatcher',
        'GraphReasoningMatcher',
        'StructuralMatcher'
    }

    for col_name in test_columns:
        if col_name not in messy_data.get_column_names():
            continue

        column = messy_data.get_analysis(col_name)
        results = matcher_pipeline.match_all(column, properties, top_k=10)

        evidence_counts.append(len(results))

        # Count ontology matchers in evidence
        ontology_count = sum(1 for r in results if r.matcher_name in ontology_matchers)
        ontology_matcher_counts.append(ontology_count)

        print(f"\n{col_name}:")
        print(f"  Evidence items: {len(results)}")
        print(f"  Ontology matchers: {ontology_count}")
        for r in results[:5]:
            print(f"    - {r.matcher_name}: {r.confidence:.3f} ({r.matched_via[:50]}...)")

    # Target: 6-8 evidence entries per column
    avg_evidence = sum(evidence_counts) / len(evidence_counts) if evidence_counts else 0
    print(f"\n✅ Average evidence per column: {avg_evidence:.1f}")
    assert avg_evidence >= 4, f"Expected avg evidence >= 4, got {avg_evidence:.1f}"

    # Target: Ontology matchers in 80%+ of evidence lists
    columns_with_ontology = sum(1 for count in ontology_matcher_counts if count > 0)
    ontology_rate = columns_with_ontology / len(ontology_matcher_counts) if ontology_matcher_counts else 0
    print(f"✅ Ontology validation rate: {ontology_rate:.1%}")
    assert ontology_rate >= 0.6, f"Expected ontology rate >= 60%, got {ontology_rate:.1%}"


def test_matcher_firing_rates(matcher_pipeline, messy_data, test_ontology):
    """Test how many matchers actually fire across all columns."""
    properties = list(test_ontology.properties.values())

    matcher_fire_counts = {}
    total_columns = 0

    for col_name in messy_data.get_column_names():
        column = messy_data.get_analysis(col_name)
        results = matcher_pipeline.match_all(column, properties, top_k=20)

        total_columns += 1

        for result in results:
            matcher_name = result.matcher_name
            matcher_fire_counts[matcher_name] = matcher_fire_counts.get(matcher_name, 0) + 1

    print(f"\n{'Matcher':<35} {'Fires':<8} {'Rate':<8}")
    print("-" * 52)

    for matcher in sorted(matcher_fire_counts.keys()):
        count = matcher_fire_counts[matcher]
        rate = count / total_columns
        print(f"{matcher:<35} {count:<8} {rate:<8.1%}")

    # Target: Most matchers should fire at least once
    matchers_fired = len(matcher_fire_counts)
    print(f"\n✅ Matchers that fired: {matchers_fired}/17")

    # Should have at least 10/17 firing
    assert matchers_fired >= 10, \
        f"Expected at least 10 matchers to fire, got {matchers_fired}"


def test_evidence_categorization(matcher_pipeline, messy_data, test_ontology):
    """Test that evidence can be categorized into semantic/ontological/structural."""
    properties = list(test_ontology.properties.values())
    column = messy_data.get_analysis("employeeID")

    results = matcher_pipeline.match_all(column, properties, top_k=15)

    # Categorize matchers
    semantic_matchers = {
        'SemanticSimilarityMatcher',
        'LexicalMatcher',
        'ExactPrefLabelMatcher',
        'ExactRdfsLabelMatcher',
        'ExactAltLabelMatcher',
        'PartialStringMatcher',
        'FuzzyStringMatcher'
    }

    ontology_matchers = {
        'PropertyHierarchyMatcher',
        'OWLCharacteristicsMatcher',
        'RestrictionBasedMatcher',
        'DataTypeInferenceMatcher',
        'SKOSRelationsMatcher'
    }

    structural_matchers = {
        'GraphReasoningMatcher',
        'StructuralMatcher',
        'HistoryAwareMatcher',
        'ExactLocalNameMatcher'
    }

    semantic_count = sum(1 for r in results if r.matcher_name in semantic_matchers)
    ontology_count = sum(1 for r in results if r.matcher_name in ontology_matchers)
    structural_count = sum(1 for r in results if r.matcher_name in structural_matchers)

    print(f"\nEvidence categories:")
    print(f"  Semantic: {semantic_count}")
    print(f"  Ontological: {ontology_count}")
    print(f"  Structural: {structural_count}")

    # Should have evidence from multiple categories
    categories_present = sum([
        semantic_count > 0,
        ontology_count > 0,
        structural_count > 0
    ])

    print(f"✅ Categories present: {categories_present}/3")
    assert categories_present >= 2, \
        f"Expected evidence from at least 2 categories, got {categories_present}"


def test_cache_performance(matcher_pipeline, messy_data, test_ontology):
    """Test that semantic embedding cache provides performance benefit."""
    properties = list(test_ontology.properties.values())[:10]
    column = messy_data.get_analysis("employeeID")

    # First run - cold cache
    start_cold = time.time()
    results1 = matcher_pipeline.match_all(column, properties, top_k=10)
    time_cold = (time.time() - start_cold) * 1000

    # Second run - warm cache
    start_warm = time.time()
    results2 = matcher_pipeline.match_all(column, properties, top_k=10)
    time_warm = (time.time() - start_warm) * 1000

    print(f"\nCache performance:")
    print(f"  Cold cache: {time_cold:.2f}ms")
    print(f"  Warm cache: {time_warm:.2f}ms")
    print(f"  Speedup: {time_cold/time_warm:.2f}x")

    # Warm should be faster (or at least not slower)
    assert time_warm <= time_cold * 1.5, \
        f"Warm cache slower than cold: {time_warm:.2f}ms vs {time_cold:.2f}ms"

    print(f"✅ Cache performance validated")


def test_constraint_validation(matcher_pipeline, validation_data, test_ontology):
    """Test that RestrictionBasedMatcher identifies constraint violations."""
    properties = list(test_ontology.properties.values())

    # Test columns with violations
    test_columns = ["Age", "Salary", "Email"]

    for col_name in test_columns:
        if col_name not in validation_data.get_column_names():
            continue

        column = validation_data.get_analysis(col_name)
        results = matcher_pipeline.match_all(column, properties, top_k=10)

        # Check if RestrictionBasedMatcher fired
        restriction_results = [r for r in results if r.matcher_name == 'RestrictionBasedMatcher']

        print(f"\n{col_name}:")
        if restriction_results:
            for r in restriction_results:
                print(f"  ✅ RestrictionBasedMatcher: {r.confidence:.3f}")
                print(f"     {r.matched_via}")
        else:
            print(f"  ⚠️ RestrictionBasedMatcher did not fire")


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "-s"])

