"""Factory for creating default matcher pipelines."""

from typing import List, Optional
from .base import MatcherPipeline, ColumnPropertyMatcher
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
from .graph_matcher import GraphReasoningMatcher, InheritanceAwareMatcher
from .hierarchy_matcher import PropertyHierarchyMatcher
from .owl_characteristics_matcher import OWLCharacteristicsMatcher
from .restriction_matcher import RestrictionBasedMatcher
from .skos_relations_matcher import SKOSRelationsMatcher


def create_simplified_pipeline(
    use_semantic: bool = True,
    semantic_threshold: float = 0.5,
    semantic_model: str = "sentence-transformers/all-MiniLM-L6-v2",
    enable_logging: bool = False,
) -> MatcherPipeline:
    """Create a simplified, high-performance matcher pipeline.

    This pipeline focuses on what works:
    - Exact label matching (no false positives)
    - Semantic embeddings (handles synonyms, abbreviations, context)
    - Datatype validation (used for boosting, not primary matching)

    Benefits:
    - Better results (semantic embeddings can shine)
    - Faster (5 matchers instead of 17)
    - More reliable (no conflicting signals)
    - Easier to maintain and debug

    Args:
        use_semantic: Enable semantic similarity matching (recommended: True)
        semantic_threshold: Threshold for semantic matches (0-1, recommended: 0.5)
        semantic_model: Sentence transformer model name
        enable_logging: Enable detailed matching logger

    Returns:
        Simplified MatcherPipeline focused on accuracy
    """
    matchers: List[ColumnPropertyMatcher] = [
        # Exact matchers (highest confidence, no false positives)
        ExactPrefLabelMatcher(threshold=0.98),
        ExactRdfsLabelMatcher(threshold=0.95),
        ExactAltLabelMatcher(threshold=0.90),

        # Semantic matcher (the real workhorse - handles 90% of matches)
        SemanticSimilarityMatcher(
            enabled=use_semantic,
            threshold=semantic_threshold,
            model_name=semantic_model
        ),

        # Datatype matcher (used for validation/boosting, not primary matching)
        DataTypeInferenceMatcher(
            enabled=True,
            threshold=0.0  # Always emit evidence, used for validation only
        ),
    ]

    logger = None
    if enable_logging:
        from ..matching_logger import MatchingLogger
        logger = MatchingLogger()

    return MatcherPipeline(matchers, logger=logger, calibrator=None)


def create_default_pipeline(
    use_semantic: bool = True,
    use_datatype: bool = True,
    use_history: bool = True,
    use_structural: bool = True,
    use_graph_reasoning: bool = True,
    use_hierarchy: bool = True,
    use_owl_characteristics: bool = True,
    use_restrictions: bool = True,
    use_skos_relations: bool = True,
    semantic_threshold: float = 0.5,
    datatype_threshold: float = 0.0,  # Emit dtype evidence always; aggregation caps and acceptance floor guard
    history_threshold: float = 0.6,
    structural_threshold: float = 0.7,
    graph_reasoning_threshold: float = 0.6,
    hierarchy_threshold: float = 0.65,
    owl_characteristics_threshold: float = 0.60,
    restrictions_threshold: float = 0.55,
    skos_relations_threshold: float = 0.50,
    semantic_model: str = "sentence-transformers/all-MiniLM-L6-v2",
    enable_logging: bool = False,
    enable_calibration: bool = True,
    reasoner: Optional[any] = None,  # GraphReasoner instance
    ontology_analyzer: Optional[any] = None,  # OntologyAnalyzer instance
    # Advanced experimental flags (temporarily disabled until implemented)
    use_probabilistic_reasoning: bool = False,
    probabilistic_threshold: float = 0.6,
    use_ontology_validation: bool = False,
    validation_threshold: float = 0.6,
    # NEW: Simplified mode (recommended)
    use_simplified: bool = True,
) -> MatcherPipeline:
    """Create the default matcher pipeline.

    NEW in v0.2.1: Defaults to simplified pipeline for better results.
    Set use_simplified=False to use the legacy complex pipeline.

    Args:
        use_simplified: Use simplified pipeline (recommended: True)
        use_semantic: Enable semantic similarity matching
        semantic_threshold: Threshold for semantic matches (0-1)
        semantic_model: Sentence transformer model name
        enable_logging: Enable detailed matching logger
        ... (other args for legacy mode)

    Returns:
        Configured MatcherPipeline
    """
    # NEW DEFAULT: Use simplified pipeline
    if use_simplified:
        return create_simplified_pipeline(
            use_semantic=use_semantic,
            semantic_threshold=semantic_threshold,
            semantic_model=semantic_model,
            enable_logging=enable_logging
        )

    # LEGACY MODE: Complex pipeline with all matchers
    matchers: List[ColumnPropertyMatcher] = [
        # Exact matchers first (highest confidence)
        ExactPrefLabelMatcher(threshold=0.98),
        ExactRdfsLabelMatcher(threshold=0.95),
        ExactAltLabelMatcher(threshold=0.90),
        ExactHiddenLabelMatcher(threshold=0.85),
        ExactLocalNameMatcher(threshold=0.80),
    ]

    # Add ontology-based matchers (HIGH priority)
    # These come after exact matchers but before fuzzy/semantic
    # because they use ontology structure which is more reliable

    if use_hierarchy and ontology_analyzer is not None:
        matchers.append(
            PropertyHierarchyMatcher(
                ontology_analyzer=ontology_analyzer,
                enabled=True,
                threshold=hierarchy_threshold,
                hierarchy_boost=0.15
            )
        )

    if use_owl_characteristics and ontology_analyzer is not None:
        matchers.append(
            OWLCharacteristicsMatcher(
                ontology_analyzer=ontology_analyzer,
                enabled=True,
                threshold=owl_characteristics_threshold,
                ifp_uniqueness_threshold=0.90,
                fp_uniqueness_threshold=0.95
            )
        )

    # Phase 2 matchers: Restriction-based and SKOS relations
    if use_restrictions and ontology_analyzer is not None:
        matchers.append(
            RestrictionBasedMatcher(
                ontology_analyzer=ontology_analyzer,
                enabled=True,
                threshold=restrictions_threshold
            )
        )

    if use_skos_relations:
        matchers.append(
            SKOSRelationsMatcher(
                enabled=True,
                threshold=skos_relations_threshold
            )
        )

    # Phase 3 matchers: Probabilistic reasoning and validation (currently disabled unless flags set)
    if use_probabilistic_reasoning and ontology_analyzer is not None and reasoner is not None:
        try:
            from .probabilistic_matcher import ProbabilisticGraphMatcher  # optional module
            matchers.append(
                ProbabilisticGraphMatcher(
                    ontology_analyzer=ontology_analyzer,
                    graph_reasoner=reasoner,
                    enabled=True,
                    threshold=probabilistic_threshold
                )
            )
        except ImportError:
            pass  # Silently skip if module not available

    if use_ontology_validation and ontology_analyzer is not None:
        try:
            from .validation_matcher import OntologyValidationMatcher  # optional module
            matchers.append(
                OntologyValidationMatcher(
                    ontology_analyzer=ontology_analyzer,
                    enabled=True,
                    threshold=validation_threshold
                )
            )
        except ImportError:
            pass

    # Continue with other matchers
    matchers.extend([
        HistoryAwareMatcher(enabled=use_history, threshold=history_threshold),
        SemanticSimilarityMatcher(enabled=use_semantic, threshold=semantic_threshold, model_name=semantic_model),
        LexicalMatcher(enabled=True, threshold=0.60),  # Pure lexical string matching
        DataTypeInferenceMatcher(enabled=use_datatype, threshold=datatype_threshold),
        StructuralMatcher(enabled=use_structural, threshold=structural_threshold),
    ])

    # Add graph reasoning matcher if reasoner provided
    if use_graph_reasoning and reasoner is not None:
        matchers.append(
            GraphReasoningMatcher(
                reasoner=reasoner,
                enabled=True,
                threshold=graph_reasoning_threshold
            )
        )

    # Add fallback matchers
    matchers.extend([
        PartialStringMatcher(threshold=0.60),
        FuzzyStringMatcher(threshold=0.40),
    ])

    logger = None
    if enable_logging:
        from ..matching_logger import MatchingLogger
        logger = MatchingLogger()

    calibrator = None
    if enable_calibration:
        from ..confidence_calibrator import ConfidenceCalibrator
        calibrator = ConfidenceCalibrator()

    return MatcherPipeline(matchers, logger=logger, calibrator=calibrator)


def create_exact_only_pipeline() -> MatcherPipeline:
    """Create a pipeline with only exact matchers (no fuzzy/semantic).

    Useful for strict matching requirements.
    """
    matchers = [
        ExactPrefLabelMatcher(),
        ExactRdfsLabelMatcher(),
        ExactAltLabelMatcher(),
        ExactHiddenLabelMatcher(),
        ExactLocalNameMatcher(),
    ]
    return MatcherPipeline(matchers)


def create_fast_pipeline() -> MatcherPipeline:
    """Create a fast pipeline without semantic matching.

    Useful when speed is critical and semantic model isn't needed.
    """
    matchers = [
        ExactPrefLabelMatcher(),
        ExactRdfsLabelMatcher(),
        ExactAltLabelMatcher(),
        ExactHiddenLabelMatcher(),
        ExactLocalNameMatcher(),
        PartialStringMatcher(),
        FuzzyStringMatcher(),
    ]
    return MatcherPipeline(matchers)


def create_semantic_only_pipeline(
    threshold: float = 0.6,
    model: str = "sentence-transformers/all-MiniLM-L6-v2"
) -> MatcherPipeline:
    """Create a pipeline with only semantic matching.

    Useful for testing semantic matching in isolation.
    """
    matchers = [
        SemanticSimilarityMatcher(
            enabled=True,
            threshold=threshold,
            model_name=model
        )
    ]
    return MatcherPipeline(matchers)


def create_custom_pipeline(
    matchers: List[ColumnPropertyMatcher],
    enable_logging: bool = False,
    enable_calibration: bool = False
) -> MatcherPipeline:
    """Create a custom pipeline with specified matchers.

    Args:
        matchers: List of matcher instances
        enable_logging: Enable detailed matching logger
        enable_calibration: Enable confidence calibration

    Returns:
        MatcherPipeline with custom matchers
    """
    logger = None
    if enable_logging:
        from ..matching_logger import MatchingLogger
        logger = MatchingLogger()

    calibrator = None
    if enable_calibration:
        from ..confidence_calibrator import ConfidenceCalibrator
        calibrator = ConfidenceCalibrator()

    return MatcherPipeline(matchers, logger=logger, calibrator=calibrator)
