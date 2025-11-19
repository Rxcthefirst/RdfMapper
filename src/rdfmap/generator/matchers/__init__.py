"""Matcher module for column-property matching strategies."""

from .base import (
    ColumnPropertyMatcher,
    MatcherPipeline,
    MatchResult,
    MatchContext,
    MatchPriority,
    PerformanceMetrics
)
from .exact_matchers import (
    ExactPrefLabelMatcher,
    ExactRdfsLabelMatcher,
    ExactAltLabelMatcher,
    ExactHiddenLabelMatcher,
    ExactLocalNameMatcher
)
from .semantic_matcher import SemanticSimilarityMatcher
from .lexical_matcher import LexicalMatcher
from .datatype_matcher import DataTypeInferenceMatcher
from .history_matcher import HistoryAwareMatcher
from .structural_matcher import StructuralMatcher
from .fuzzy_matchers import PartialStringMatcher, FuzzyStringMatcher
from .hierarchy_matcher import PropertyHierarchyMatcher
from .owl_characteristics_matcher import OWLCharacteristicsMatcher
from .graph_matcher import GraphReasoningMatcher, InheritanceAwareMatcher, GraphContextMatcher
from .factory import (
    create_default_pipeline,
    create_simplified_pipeline,  # NEW: Simplified high-performance pipeline
    create_exact_only_pipeline,
    create_fast_pipeline,
    create_semantic_only_pipeline,
    create_custom_pipeline
)
from .restriction_matcher import RestrictionBasedMatcher
from .skos_relations_matcher import SKOSRelationsMatcher

__all__ = [
    # Base classes
    'ColumnPropertyMatcher',
    'MatcherPipeline',
    'MatchResult',
    'MatchContext',
    'MatchPriority',
    'PerformanceMetrics',

    # Exact matchers
    'ExactPrefLabelMatcher',
    'ExactRdfsLabelMatcher',
    'ExactAltLabelMatcher',
    'ExactHiddenLabelMatcher',
    'ExactLocalNameMatcher',

    # Advanced matchers
    'SemanticSimilarityMatcher',
    'LexicalMatcher',
    'DataTypeInferenceMatcher',
    'HistoryAwareMatcher',
    'StructuralMatcher',
    'DataTypeInferenceMatcher',
    'PartialStringMatcher',
    'FuzzyStringMatcher',
    'PropertyHierarchyMatcher',
    'OWLCharacteristicsMatcher',
    'GraphReasoningMatcher',
    'InheritanceAwareMatcher',
    'GraphContextMatcher',
    'RestrictionBasedMatcher',
    'SKOSRelationsMatcher',

    # Factory functions
    'create_default_pipeline',
    'create_exact_only_pipeline',
    'create_fast_pipeline',
    'create_semantic_only_pipeline',
    'create_custom_pipeline',
]


