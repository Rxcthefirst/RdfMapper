"""Matcher module for column-property matching strategies."""

from .base import (
    ColumnPropertyMatcher,
    MatcherPipeline,
    MatchResult,
    MatchContext,
    MatchPriority
)
from .exact_matchers import (
    ExactPrefLabelMatcher,
    ExactRdfsLabelMatcher,
    ExactAltLabelMatcher,
    ExactHiddenLabelMatcher,
    ExactLocalNameMatcher
)
from .semantic_matcher import SemanticSimilarityMatcher
from .datatype_matcher import DataTypeInferenceMatcher
from .history_matcher import HistoryAwareMatcher
from .structural_matcher import StructuralMatcher
from .fuzzy_matchers import PartialStringMatcher, FuzzyStringMatcher
from .hierarchy_matcher import PropertyHierarchyMatcher
from .owl_characteristics_matcher import OWLCharacteristicsMatcher
from .factory import (
    create_default_pipeline,
    create_exact_only_pipeline,
    create_fast_pipeline,
    create_semantic_only_pipeline,
    create_custom_pipeline
)

__all__ = [
    # Base classes
    'ColumnPropertyMatcher',
    'MatcherPipeline',
    'MatchResult',
    'MatchContext',
    'MatchPriority',

    # Exact matchers
    'ExactPrefLabelMatcher',
    'ExactRdfsLabelMatcher',
    'ExactAltLabelMatcher',
    'ExactHiddenLabelMatcher',
    'ExactLocalNameMatcher',

    # Advanced matchers
    'SemanticSimilarityMatcher',
    'HistoryAwareMatcher',
    'StructuralMatcher',
    'HistoryAwareMatcher',
    'DataTypeInferenceMatcher',
    'PartialStringMatcher',
    'FuzzyStringMatcher',
    'PropertyHierarchyMatcher',
    'OWLCharacteristicsMatcher',

    # Factory functions
    'create_default_pipeline',
    'create_exact_only_pipeline',
    'create_fast_pipeline',
    'create_semantic_only_pipeline',
    'create_custom_pipeline',
]


