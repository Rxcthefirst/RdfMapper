"""Tests for mapping history and history-aware matcher."""

import pytest
import tempfile
import os
from datetime import datetime
from rdflib import URIRef

from src.rdfmap.generator.mapping_history import MappingHistory, MappingRecord
from src.rdfmap.generator.matchers.history_matcher import HistoryAwareMatcher
from src.rdfmap.generator.ontology_analyzer import OntologyProperty
from src.rdfmap.generator.data_analyzer import DataFieldAnalysis


def test_mapping_history_creation():
    """Test creating a mapping history database."""
    with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp:
        db_path = tmp.name

    try:
        history = MappingHistory(db_path)
        assert os.path.exists(db_path)
        assert history.get_total_mappings() == 0
        history.close()
        print("✅ Mapping history database created successfully")
    finally:
        os.unlink(db_path)


def test_record_and_retrieve_mapping():
    """Test recording and retrieving a mapping."""
    with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp:
        db_path = tmp.name

    try:
        history = MappingHistory(db_path)

        # Record a mapping
        record = MappingRecord(
            column_name="customer_id",
            property_uri="http://ex.org/clientIdentifier",
            property_label="Client Identifier",
            match_type="exact_pref_label",
            confidence=1.0,
            user_accepted=True,
            correction_to=None,
            ontology_file="test.ttl",
            data_file="test.csv",
            timestamp=datetime.now().isoformat(),
            matcher_name="ExactPrefLabelMatcher"
        )

        history.record_mapping(record)

        # Retrieve it
        total = history.get_total_mappings()
        assert total == 1

        # Find similar
        similar = history.find_similar_mappings("customer_id")
        assert len(similar) == 1
        assert similar[0]['property_uri'] == "http://ex.org/clientIdentifier"

        history.close()
        print("✅ Record and retrieve mapping works")
    finally:
        os.unlink(db_path)


def test_similar_mapping_fuzzy_match():
    """Test finding similar mappings with variations."""
    with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp:
        db_path = tmp.name

    try:
        history = MappingHistory(db_path)

        # Record mapping with underscores
        record = MappingRecord(
            column_name="customer_id",
            property_uri="http://ex.org/clientId",
            property_label="Client ID",
            match_type="semantic",
            confidence=0.85,
            user_accepted=True,
            correction_to=None,
            ontology_file="test.ttl",
            data_file="test.csv",
            timestamp=datetime.now().isoformat(),
            matcher_name="SemanticMatcher"
        )

        history.record_mapping(record)

        # Search with different formatting
        similar = history.find_similar_mappings("customerId")  # No underscore
        assert len(similar) == 1

        similar = history.find_similar_mappings("CUSTOMER_ID")  # Uppercase
        assert len(similar) == 1

        similar = history.find_similar_mappings("customer id")  # Space
        assert len(similar) == 1

        history.close()
        print("✅ Fuzzy matching for similar column names works")
    finally:
        os.unlink(db_path)


def test_property_success_rate():
    """Test calculating success rate for properties."""
    with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp:
        db_path = tmp.name

    try:
        history = MappingHistory(db_path)

        # Record several mappings for same property
        for i, accepted in enumerate([True, True, True, False, True]):
            record = MappingRecord(
                column_name=f"amount_{i}",
                property_uri="http://ex.org/amount",
                property_label="Amount",
                match_type="semantic",
                confidence=0.8,
                user_accepted=accepted,
                correction_to=None if accepted else "http://ex.org/other",
                ontology_file="test.ttl",
                data_file="test.csv",
                timestamp=datetime.now().isoformat(),
                matcher_name="SemanticMatcher"
            )
            history.record_mapping(record)

        # Check success rate: 4/5 = 0.8
        success_rate = history.get_property_success_rate("http://ex.org/amount")
        assert success_rate == 0.8

        history.close()
        print(f"✅ Success rate calculation works: {success_rate:.2f}")
    finally:
        os.unlink(db_path)


def test_matcher_performance_tracking():
    """Test tracking matcher performance statistics."""
    with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp:
        db_path = tmp.name

    try:
        history = MappingHistory(db_path)

        # Record mappings from different matchers
        matchers = [
            ("ExactMatcher", True, 1.0),
            ("ExactMatcher", True, 1.0),
            ("SemanticMatcher", True, 0.8),
            ("SemanticMatcher", False, 0.6),
            ("FuzzyMatcher", False, 0.4),
        ]

        for matcher_name, accepted, confidence in matchers:
            record = MappingRecord(
                column_name="test",
                property_uri="http://ex.org/test",
                property_label="Test",
                match_type="test",
                confidence=confidence,
                user_accepted=accepted,
                correction_to=None,
                ontology_file="test.ttl",
                data_file="test.csv",
                timestamp=datetime.now().isoformat(),
                matcher_name=matcher_name
            )
            history.record_mapping(record)

        # Get stats for ExactMatcher
        stats = history.get_matcher_performance("ExactMatcher")
        assert stats['total_matches'] == 2
        assert stats['accepted_matches'] == 2
        assert stats['success_rate'] == 1.0

        # Get stats for SemanticMatcher
        stats = history.get_matcher_performance("SemanticMatcher")
        assert stats['total_matches'] == 2
        assert stats['accepted_matches'] == 1
        assert stats['success_rate'] == 0.5

        history.close()
        print("✅ Matcher performance tracking works")
    finally:
        os.unlink(db_path)


def test_history_aware_matcher():
    """Test the history-aware matcher."""
    with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp:
        db_path = tmp.name

    try:
        history = MappingHistory(db_path)

        # Record a successful historical mapping
        record = MappingRecord(
            column_name="loan_amount",
            property_uri="http://ex.org/loanAmount",
            property_label="Loan Amount",
            match_type="semantic",
            confidence=0.85,
            user_accepted=True,
            correction_to=None,
            ontology_file="mortgage_ontology.ttl",
            data_file="loans.csv",
            timestamp=datetime.now().isoformat(),
            matcher_name="SemanticMatcher"
        )
        history.record_mapping(record)

        # Now try to match similar column with history-aware matcher
        matcher = HistoryAwareMatcher(history_db=history)

        column = DataFieldAnalysis("loan_amount", "loan_amount")
        props = [
            OntologyProperty(
                URIRef("http://ex.org/loanAmount"),
                label="Loan Amount"
            ),
            OntologyProperty(
                URIRef("http://ex.org/loanDescription"),
                label="Loan Description"
            )
        ]

        result = matcher.match(column, props)

        assert result is not None
        assert result.property.uri == URIRef("http://ex.org/loanAmount")
        assert result.confidence > 0.6
        print(f"✅ History-aware matching works (confidence: {result.confidence:.2f})")

        history.close()
    finally:
        os.unlink(db_path)


def test_confidence_boosting():
    """Test confidence boosting based on history."""
    with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp:
        db_path = tmp.name

    try:
        history = MappingHistory(db_path)

        # Record multiple successful uses of a property
        for i in range(10):
            record = MappingRecord(
                column_name=f"amount_{i}",
                property_uri="http://ex.org/amount",
                property_label="Amount",
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

        # Create a match result
        from src.rdfmap.generator.matchers.base import MatchResult
        from src.rdfmap.models.alignment import MatchType

        original_result = MatchResult(
            property=OntologyProperty(URIRef("http://ex.org/amount"), label="Amount"),
            match_type=MatchType.SEMANTIC_SIMILARITY,
            confidence=0.7,
            matched_via="semantic",
            matcher_name="SemanticMatcher"
        )

        # Boost it
        matcher = HistoryAwareMatcher(history_db=history)
        boosted = matcher.boost_confidence(original_result, "amount_new")

        # Should be boosted
        assert boosted.confidence > original_result.confidence
        print(f"✅ Confidence boosting works: {original_result.confidence:.2f} → {boosted.confidence:.2f}")

        history.close()
    finally:
        os.unlink(db_path)


def test_export_import():
    """Test exporting and importing history."""
    with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp:
        db_path = tmp.name

    with tempfile.NamedTemporaryFile(delete=False, suffix='.json', mode='w') as json_file:
        json_path = json_file.name

    try:
        history = MappingHistory(db_path)

        # Record some mappings
        for i in range(3):
            record = MappingRecord(
                column_name=f"col_{i}",
                property_uri=f"http://ex.org/prop_{i}",
                property_label=f"Property {i}",
                match_type="exact",
                confidence=1.0,
                user_accepted=True,
                correction_to=None,
                ontology_file="test.ttl",
                data_file="test.csv",
                timestamp=datetime.now().isoformat(),
                matcher_name="ExactMatcher"
            )
            history.record_mapping(record)

        # Export
        history.export_to_json(json_path)
        assert os.path.exists(json_path)

        # Check file has content
        with open(json_path) as f:
            import json
            data = json.load(f)
            assert len(data['mappings']) == 3

        history.close()
        print("✅ Export/import works")
    finally:
        os.unlink(db_path)
        os.unlink(json_path)


if __name__ == "__main__":
    print("Running mapping history tests...\n")
    test_mapping_history_creation()
    test_record_and_retrieve_mapping()
    test_similar_mapping_fuzzy_match()
    test_property_success_rate()
    test_matcher_performance_tracking()
    test_history_aware_matcher()
    test_confidence_boosting()
    test_export_import()
    print("\n✅ All mapping history tests passed!")

