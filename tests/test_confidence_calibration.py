"""Tests for confidence calibration."""

import pytest
import tempfile
import os
import sys
from datetime import datetime
from rdflib import URIRef

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from rdfmap.generator.confidence_calibrator import ConfidenceCalibrator, CalibrationStats
from rdfmap.generator.mapping_history import MappingHistory, MappingRecord
from rdfmap.generator.matchers.base import MatchResult
from rdfmap.generator.ontology_analyzer import OntologyProperty
from rdfmap.models.alignment import MatchType


def test_calibration_with_insufficient_data():
    """Test that calibration doesn't adjust with insufficient history."""
    with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp:
        db_path = tmp.name

    try:
        history = MappingHistory(db_path)
        calibrator = ConfidenceCalibrator(history, min_samples=10)

        # Only 5 samples (below min_samples)
        for i in range(5):
            record = MappingRecord(
                column_name=f"col_{i}",
                property_uri="http://ex.org/prop",
                property_label="Property",
                match_type="semantic",
                confidence=0.8,
                user_accepted=True,
                correction_to=None,
                ontology_file="test.ttl",
                data_file="test.csv",
                timestamp=datetime.now().isoformat(),
                matcher_name="SemanticMatcher"
            )
            history.record_mapping(record)

        # Should return original confidence
        calibrated = calibrator.calibrate_score(0.75, "SemanticMatcher", MatchType.SEMANTIC_SIMILARITY)
        assert calibrated == 0.75  # No change

        print("✅ Calibration correctly skipped with insufficient data")
        history.close()
    finally:
        os.unlink(db_path)


def test_calibration_boosts_conservative_matcher():
    """Test that over-conservative matcher gets boosted."""
    with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp:
        db_path = tmp.name

    try:
        history = MappingHistory(db_path)
        calibrator = ConfidenceCalibrator(history, min_samples=10)

        # Record 15 matches: high success rate (90%) but reported low confidence (0.7)
        for i in range(15):
            record = MappingRecord(
                column_name=f"col_{i}",
                property_uri="http://ex.org/prop",
                property_label="Property",
                match_type="semantic",
                confidence=0.7,  # Reported confidence
                user_accepted=(i < 13),  # 13/15 = 87% success (but reported 70%)
                correction_to=None if (i < 13) else "http://ex.org/other",
                ontology_file="test.ttl",
                data_file="test.csv",
                timestamp=datetime.now().isoformat(),
                matcher_name="ConservativeMatcher"
            )
            history.record_mapping(record)

        # Should boost confidence
        original = 0.7
        calibrated = calibrator.calibrate_score(original, "ConservativeMatcher", MatchType.SEMANTIC_SIMILARITY)

        assert calibrated > original, f"Expected boost but got {calibrated} (original: {original})"
        print(f"✅ Conservative matcher boosted: {original:.3f} → {calibrated:.3f}")

        history.close()
    finally:
        os.unlink(db_path)


def test_calibration_reduces_overconfident_matcher():
    """Test that over-confident matcher gets reduced."""
    with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp:
        db_path = tmp.name

    try:
        history = MappingHistory(db_path)
        calibrator = ConfidenceCalibrator(history, min_samples=10)

        # Record 15 matches: low success rate (60%) but reported high confidence (0.9)
        for i in range(15):
            record = MappingRecord(
                column_name=f"col_{i}",
                property_uri="http://ex.org/prop",
                property_label="Property",
                match_type="fuzzy",
                confidence=0.9,  # Reported confidence
                user_accepted=(i < 9),  # 9/15 = 60% success (but reported 90%)
                correction_to=None if (i < 9) else "http://ex.org/other",
                ontology_file="test.ttl",
                data_file="test.csv",
                timestamp=datetime.now().isoformat(),
                matcher_name="OverconfidentMatcher"
            )
            history.record_mapping(record)

        # Should reduce confidence
        original = 0.9
        calibrated = calibrator.calibrate_score(original, "OverconfidentMatcher", MatchType.FUZZY)

        assert calibrated < original, f"Expected reduction but got {calibrated} (original: {original})"
        print(f"✅ Overconfident matcher reduced: {original:.3f} → {calibrated:.3f}")

        history.close()
    finally:
        os.unlink(db_path)


def test_calibrate_result():
    """Test calibrating a full MatchResult."""
    with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp:
        db_path = tmp.name

    try:
        history = MappingHistory(db_path)
        calibrator = ConfidenceCalibrator(history, min_samples=5)

        # Record some history
        for i in range(10):
            record = MappingRecord(
                column_name=f"col_{i}",
                property_uri="http://ex.org/prop",
                property_label="Property",
                match_type="semantic",
                confidence=0.75,
                user_accepted=(i < 9),  # 90% success
                correction_to=None,
                ontology_file="test.ttl",
                data_file="test.csv",
                timestamp=datetime.now().isoformat(),
                matcher_name="TestMatcher"
            )
            history.record_mapping(record)

        # Create a result
        original_result = MatchResult(
            property=OntologyProperty(URIRef("http://ex.org/prop"), label="Property"),
            match_type=MatchType.SEMANTIC_SIMILARITY,
            confidence=0.75,
            matched_via="semantic",
            matcher_name="TestMatcher"
        )

        # Calibrate it
        calibrated_result = calibrator.calibrate_result(original_result)

        assert calibrated_result.confidence >= original_result.confidence  # Should boost (90% > 75%)
        assert calibrated_result.property == original_result.property
        assert calibrated_result.match_type == original_result.match_type

        print(f"✅ Result calibrated: {original_result.confidence:.3f} → {calibrated_result.confidence:.3f}")

        history.close()
    finally:
        os.unlink(db_path)


def test_get_matcher_reliability():
    """Test getting reliability scores for matchers."""
    with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp:
        db_path = tmp.name

    try:
        history = MappingHistory(db_path)
        calibrator = ConfidenceCalibrator(history, min_samples=5)

        # Record different matchers with different success rates
        matchers_data = [
            ("ExactMatcher", 10, 10),      # 100% success
            ("SemanticMatcher", 10, 8),    # 80% success
            ("FuzzyMatcher", 10, 6),       # 60% success
        ]

        for matcher_name, total, accepted in matchers_data:
            for i in range(total):
                record = MappingRecord(
                    column_name=f"col_{i}",
                    property_uri="http://ex.org/prop",
                    property_label="Property",
                    match_type="test",
                    confidence=0.8,
                    user_accepted=(i < accepted),
                    correction_to=None,
                    ontology_file="test.ttl",
                    data_file="test.csv",
                    timestamp=datetime.now().isoformat(),
                    matcher_name=matcher_name
                )
                history.record_mapping(record)

        # Get reliability scores
        exact_rel = calibrator.get_matcher_reliability("ExactMatcher")
        semantic_rel = calibrator.get_matcher_reliability("SemanticMatcher")
        fuzzy_rel = calibrator.get_matcher_reliability("FuzzyMatcher")

        assert exact_rel == 1.0
        assert semantic_rel == 0.8
        assert fuzzy_rel == 0.6

        print(f"✅ Reliability scores: Exact={exact_rel:.1%}, Semantic={semantic_rel:.1%}, Fuzzy={fuzzy_rel:.1%}")

        history.close()
    finally:
        os.unlink(db_path)


def test_calibration_report():
    """Test generating calibration report."""
    with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp:
        db_path = tmp.name

    try:
        history = MappingHistory(db_path)
        calibrator = ConfidenceCalibrator(history, min_samples=5)

        # Record some history
        for i in range(10):
            record = MappingRecord(
                column_name=f"col_{i}",
                property_uri="http://ex.org/prop",
                property_label="Property",
                match_type="semantic",
                confidence=0.75,
                user_accepted=(i < 9),
                correction_to=None,
                ontology_file="test.ttl",
                data_file="test.csv",
                timestamp=datetime.now().isoformat(),
                matcher_name="TestMatcher"
            )
            history.record_mapping(record)

        # Generate report
        report = calibrator.generate_calibration_report()

        assert "Calibration Report" in report
        assert "TestMatcher" in report
        assert "Success Rate" in report

        print("✅ Calibration report generated:")
        print(report)

        history.close()
    finally:
        os.unlink(db_path)


def test_calibration_bounds():
    """Test that calibration respects bounds (0-1)."""
    with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp:
        db_path = tmp.name

    try:
        history = MappingHistory(db_path)
        calibrator = ConfidenceCalibrator(history, min_samples=5)

        # Record extreme case
        for i in range(10):
            record = MappingRecord(
                column_name=f"col_{i}",
                property_uri="http://ex.org/prop",
                property_label="Property",
                match_type="semantic",
                confidence=0.95,
                user_accepted=True,  # 100% success
                correction_to=None,
                ontology_file="test.ttl",
                data_file="test.csv",
                timestamp=datetime.now().isoformat(),
                matcher_name="PerfectMatcher"
            )
            history.record_mapping(record)

        # Even with perfect history, shouldn't exceed 1.0
        calibrated = calibrator.calibrate_score(0.95, "PerfectMatcher", MatchType.SEMANTIC_SIMILARITY)

        assert 0.0 <= calibrated <= 1.0
        print(f"✅ Calibration respects bounds: {calibrated:.3f} (within 0-1)")

        history.close()
    finally:
        os.unlink(db_path)


if __name__ == "__main__":
    print("Running confidence calibration tests...\n")
    test_calibration_with_insufficient_data()
    test_calibration_boosts_conservative_matcher()
    test_calibration_reduces_overconfident_matcher()
    test_calibrate_result()
    test_get_matcher_reliability()
    test_calibration_report()
    test_calibration_bounds()
    print("\n✅ All confidence calibration tests passed!")

