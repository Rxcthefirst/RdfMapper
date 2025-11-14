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
from .datatype_matcher import DataTypeInferenceMatcher
from .history_matcher import HistoryAwareMatcher
from .structural_matcher import StructuralMatcher
from .fuzzy_matchers import PartialStringMatcher, FuzzyStringMatcher
from .graph_matcher import GraphReasoningMatcher, InheritanceAwareMatcher


def create_default_pipeline(
    use_semantic: bool = True,
    use_datatype: bool = True,
    use_history: bool = True,
    use_structural: bool = True,
    use_graph_reasoning: bool = True,
    semantic_threshold: float = 0.6,
    datatype_threshold: float = 0.7,
    history_threshold: float = 0.6,
    structural_threshold: float = 0.7,
    graph_reasoning_threshold: float = 0.6,
    semantic_model: str = "sentence-transformers/all-MiniLM-L6-v2",
    enable_logging: bool = False,
    enable_calibration: bool = True,
    reasoner: Optional[any] = None  # GraphReasoner instance
) -> MatcherPipeline:
    """Create the default matcher pipeline.

    Args:
        use_semantic: Enable semantic similarity matching
        use_datatype: Enable data type inference matching
        use_history: Enable history-aware matching
        use_structural: Enable structural/relationship matching
        use_graph_reasoning: Enable ontology graph reasoning
        semantic_threshold: Threshold for semantic matches (0-1)
        datatype_threshold: Threshold for datatype matches (0-1)
        history_threshold: Threshold for history matches (0-1)
        structural_threshold: Threshold for structural matches (0-1)
        graph_reasoning_threshold: Threshold for graph reasoning matches (0-1)
        semantic_model: Sentence transformer model name
        enable_logging: Enable detailed matching logger
        enable_calibration: Enable confidence calibration
        reasoner: GraphReasoner instance (required for graph reasoning)

    Returns:
        Configured MatcherPipeline
    """
    matchers: List[ColumnPropertyMatcher] = [
        ExactPrefLabelMatcher(threshold=1.0),
        ExactRdfsLabelMatcher(threshold=0.95),
        ExactAltLabelMatcher(threshold=0.90),
        ExactHiddenLabelMatcher(threshold=0.85),
        ExactLocalNameMatcher(threshold=0.80),
        HistoryAwareMatcher(enabled=use_history, threshold=history_threshold),
        SemanticSimilarityMatcher(enabled=use_semantic, threshold=semantic_threshold, model_name=semantic_model),
        DataTypeInferenceMatcher(enabled=use_datatype, threshold=datatype_threshold),
        StructuralMatcher(enabled=use_structural, threshold=structural_threshold),
    ]

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

