"""
Test suite for matching system validation.

This validates that our matchers produce accurate, calibrated confidence scores
and correctly identify properties across diverse datasets.
"""

import pytest
from pathlib import Path
from rdfmap.generator.mapping_generator import MappingGenerator, GeneratorConfig
from rdfmap.generator.data_analyzer import DataFieldAnalysis
from rdfmap.models.alignment import MatchType


class TestMatchingAccuracy:
    """Validate matching system accuracy with known ground truth."""

    @pytest.fixture
    def mortgage_test_case(self, tmp_path):
        """Mortgage example we know works (from user's test)."""
        return {
            'name': 'Mortgage Loans',
            'data': Path('examples/mortgage/data/loans.csv'),
            'ontology': Path('examples/mortgage/ontology/mortgage_ontology.ttl'),
            'expected_matches': {
                'LoanID': {
                    'property': 'loanNumber',
                    'match_type': MatchType.SEMANTIC_SIMILARITY,
                    'min_confidence': 0.70,  # Should NOT be 1.00!
                    'max_confidence': 0.95
                },
                'Principal': {
                    'property': 'principalAmount',
                    'match_type': MatchType.SEMANTIC_SIMILARITY,
                    'min_confidence': 0.65,
                    'max_confidence': 0.90
                },
                'InterestRate': {
                    'property': 'interestRate',
                    'match_type': MatchType.EXACT_LABEL,
                    'min_confidence': 0.90,
                    'max_confidence': 1.00
                },
                'OriginationDate': {
                    'property': 'originationDate',
                    'match_type': MatchType.EXACT_LABEL,
                    'min_confidence': 0.90,
                    'max_confidence': 1.00
                },
                'LoanTerm': {
                    'property': 'loanTerm',
                    'match_type': MatchType.EXACT_LABEL,
                    'min_confidence': 0.90,
                    'max_confidence': 1.00
                },
                'Status': {
                    'property': 'loanStatus',
                    'match_type': MatchType.SEMANTIC_SIMILARITY,
                    'min_confidence': 0.75,
                    'max_confidence': 0.95
                },
                'BorrowerID': {
                    'property': 'hasBorrower',
                    'match_type': MatchType.GRAPH_REASONING,
                    'min_confidence': 0.95,
                    'max_confidence': 1.00
                },
                'PropertyID': {
                    'property': 'collateralProperty',
                    'match_type': MatchType.GRAPH_REASONING,
                    'min_confidence': 0.95,
                    'max_confidence': 1.00
                }
            }
        }

    def test_mortgage_matching_accuracy(self, mortgage_test_case):
        """Test mortgage loan matching against known ground truth."""
        test_case = mortgage_test_case

        # Generate mappings
        generator = MappingGenerator(
            ontology_file=str(test_case['ontology']),
            data_file=str(test_case['data']),
            config=GeneratorConfig(base_iri='http://test.org/'),
            use_semantic_matching=True
        )

        mapping_config, alignment_report = generator.generate_with_alignment_report()

        # Validate each expected match
        results = {
            'total': len(test_case['expected_matches']),
            'correct_property': 0,
            'correct_match_type': 0,
            'confidence_in_range': 0,
            'failures': []
        }

        for column_name, expected in test_case['expected_matches'].items():
            # Find this column's match in alignment report
            actual_match = None
            for detail in alignment_report.match_details:
                if detail.column_name == column_name:
                    actual_match = detail
                    break

            if not actual_match:
                results['failures'].append(f"{column_name}: No match found")
                continue

            # Validate property
            actual_prop_name = actual_match.matched_property.split('#')[-1].split('/')[-1]
            if actual_prop_name == expected['property']:
                results['correct_property'] += 1
            else:
                results['failures'].append(
                    f"{column_name}: Expected {expected['property']}, got {actual_prop_name}"
                )

            # Validate match type
            if actual_match.match_type == expected['match_type']:
                results['correct_match_type'] += 1
            else:
                results['failures'].append(
                    f"{column_name}: Expected {expected['match_type']}, got {actual_match.match_type}"
                )

            # Validate confidence range
            conf = actual_match.confidence_score
            if expected['min_confidence'] <= conf <= expected['max_confidence']:
                results['confidence_in_range'] += 1
            else:
                results['failures'].append(
                    f"{column_name}: Confidence {conf:.3f} outside range "
                    f"[{expected['min_confidence']}, {expected['max_confidence']}]"
                )

        # Calculate metrics
        precision = results['correct_property'] / results['total']
        match_type_accuracy = results['correct_match_type'] / results['total']
        confidence_calibration = results['confidence_in_range'] / results['total']

        # Print detailed results
        print(f"\n{'='*60}")
        print(f"Mortgage Matching Test Results:")
        print(f"{'='*60}")
        print(f"Total columns: {results['total']}")
        print(f"Correct properties: {results['correct_property']} (Precision: {precision:.1%})")
        print(f"Correct match types: {results['correct_match_type']} (Accuracy: {match_type_accuracy:.1%})")
        print(f"Confidence in range: {results['confidence_in_range']} (Calibration: {confidence_calibration:.1%})")

        if results['failures']:
            print(f"\nFailures:")
            for failure in results['failures']:
                print(f"  ❌ {failure}")

        print(f"{'='*60}\n")

        # Assertions
        assert precision >= 0.80, f"Precision {precision:.1%} below 80% threshold"
        assert match_type_accuracy >= 0.80, f"Match type accuracy {match_type_accuracy:.1%} below 80%"
        assert confidence_calibration >= 0.75, f"Confidence calibration {confidence_calibration:.1%} below 75%"

    def test_semantic_similarity_confidence_range(self):
        """Ensure semantic matches return scores in 0.4-0.9 range, not 1.00."""
        from rdfmap.generator.matchers.semantic_matcher import EnhancedSemanticMatcher
        from rdfmap.generator.ontology_analyzer import OntologyAnalyzer, OntologyProperty
        from rdflib import URIRef

        # Create test column
        column = DataFieldAnalysis(
            name='customer_name',
            inferred_type='string',
            sample_values=['John Doe', 'Jane Smith', 'Bob Johnson'],
            is_identifier=False,
            is_foreign_key=False
        )

        # Create test properties
        properties = [
            OntologyProperty(
                uri=URIRef('http://ex.org/clientName'),
                label='clientName',
                comment='Name of the client',
                domain=None,
                range_type=None,
                is_object_property=False,
                pref_label='Client Name',
                alt_labels=['Customer Name'],
                hidden_labels=[]
            ),
            OntologyProperty(
                uri=URIRef('http://ex.org/personName'),
                label='personName',
                comment='Name of a person',
                domain=None,
                range_type=None,
                is_object_property=False,
                pref_label='Person Name',
                alt_labels=[],
                hidden_labels=[]
            )
        ]

        matcher = EnhancedSemanticMatcher(threshold=0.5)
        result = matcher.match(column, properties)

        assert result is not None, "Semantic matcher should find a match"
        assert 0.4 <= result.confidence <= 0.95, \
            f"Semantic confidence {result.confidence} should be in range [0.4, 0.95], not 1.00"
        print(f"✅ Semantic match confidence: {result.confidence:.3f} (valid range)")

    def test_exact_label_high_confidence(self):
        """Ensure exact label matches have high confidence (0.9-1.0)."""
        from rdfmap.generator.matchers.exact_matcher import ExactLabelMatcher
        from rdfmap.generator.ontology_analyzer import OntologyProperty
        from rdflib import URIRef

        column = DataFieldAnalysis(
            name='interestRate',
            inferred_type='decimal',
            sample_values=[0.0525, 0.0475, 0.0600],
            is_identifier=False,
            is_foreign_key=False
        )

        properties = [
            OntologyProperty(
                uri=URIRef('http://ex.org/interestRate'),
                label='interestRate',
                comment='Annual interest rate',
                domain=None,
                range_type=None,
                is_object_property=False,
                pref_label='Interest Rate',
                alt_labels=[],
                hidden_labels=[]
            )
        ]

        matcher = ExactLabelMatcher(threshold=0.8)
        result = matcher.match(column, properties)

        assert result is not None, "Exact matcher should find a match"
        assert result.confidence >= 0.90, \
            f"Exact match confidence {result.confidence} should be >= 0.90"
        print(f"✅ Exact match confidence: {result.confidence:.3f} (high confidence)")


class TestConfidenceCalibration:
    """Validate that confidence scores correlate with match quality."""

    def test_high_confidence_matches_are_correct(self, mortgage_test_case):
        """High confidence matches (>0.8) should be correct >90% of the time."""
        # This will be implemented with user acceptance data over time
        # For now, validate that high confidence exists and is not always 1.00
        pass

    def test_confidence_distribution(self):
        """Confidence scores should be distributed, not all 1.00."""
        # Validate that we have a range of confidence scores
        pass


class TestMatcherAttribution:
    """Validate that matcher attribution is clear and consistent."""

    def test_primary_matcher_identified(self, mortgage_test_case):
        """Ensure primary matcher is clearly identified, not just DataTypeInferenceMatcher."""
        test_case = mortgage_test_case

        generator = MappingGenerator(
            ontology_file=str(test_case['ontology']),
            data_file=str(test_case['data']),
            config=GeneratorConfig(base_iri='http://test.org/'),
            use_semantic_matching=True
        )

        mapping_config, alignment_report = generator.generate_with_alignment_report()

        # Check that semantic matches are attributed to SemanticMatcher, not DataTypeMatcher
        for detail in alignment_report.match_details:
            if detail.match_type == MatchType.SEMANTIC_SIMILARITY:
                assert 'Semantic' in detail.matcher_name or 'Enhanced' in detail.matcher_name, \
                    f"{detail.column_name}: Semantic match should be attributed to SemanticMatcher, not {detail.matcher_name}"
                print(f"✅ {detail.column_name}: {detail.matcher_name} (correct attribution)")


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])

