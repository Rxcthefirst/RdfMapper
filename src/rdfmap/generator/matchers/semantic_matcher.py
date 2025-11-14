"""Semantic similarity matcher using embeddings."""

from typing import Optional, List
from .base import ColumnPropertyMatcher, MatchResult, MatchContext, MatchPriority
from ..ontology_analyzer import OntologyProperty
from ..data_analyzer import DataFieldAnalysis
from ..semantic_matcher import SemanticMatcher as EmbeddingsMatcher
from ...models.alignment import MatchType


class SemanticSimilarityMatcher(ColumnPropertyMatcher):
    """Matches columns using semantic embeddings (BERT)."""

    def __init__(
        self,
        enabled: bool = True,
        threshold: float = 0.6,
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    ):
        super().__init__(enabled, threshold)
        self._embeddings_matcher = EmbeddingsMatcher(model_name) if enabled else None

    def name(self) -> str:
        return "SemanticSimilarityMatcher"

    def priority(self) -> MatchPriority:
        return MatchPriority.MEDIUM

    def match(
        self,
        column: DataFieldAnalysis,
        properties: List[OntologyProperty],
        context: Optional[MatchContext] = None
    ) -> Optional[MatchResult]:
        if not self._embeddings_matcher:
            return None

        result = self._embeddings_matcher.match(column, properties, self.threshold)

        if result:
            prop, similarity = result
            return MatchResult(
                property=prop,
                match_type=MatchType.SEMANTIC_SIMILARITY,
                confidence=similarity,
                matched_via=f"semantic similarity: {similarity:.3f}",
                matcher_name=self.name()
            )

        return None

