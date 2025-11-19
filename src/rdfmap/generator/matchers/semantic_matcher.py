"""Pure semantic similarity matcher using embeddings only."""

from typing import Optional, List, Dict
import logging
from .base import ColumnPropertyMatcher, MatchResult, MatchContext, MatchPriority
from ..ontology_analyzer import OntologyProperty
from ..data_analyzer import DataFieldAnalysis
from ..semantic_matcher import SemanticMatcher as EmbeddingsMatcher
from ...models.alignment import MatchType

logger = logging.getLogger(__name__)


class SemanticSimilarityMatcher(ColumnPropertyMatcher):
    """Pure embedding-based semantic matcher.

    Uses sentence transformers to compute semantic similarity between
    column names and property labels. Includes:
    - Phrase-level embeddings
    - Token-level embeddings
    - Identifier pattern boost
    - No lexical fallback (use LexicalMatcher separately)
    """

    def __init__(
        self,
        enabled: bool = True,
        threshold: float = 0.45,
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        reasoner=None,
        domain_boost: float = 0.1,
        cooccurrence_boost: float = 0.05
    ):
        super().__init__(enabled, threshold)
        self.reasoner = reasoner
        self.domain_boost = domain_boost
        self.cooccurrence_boost = cooccurrence_boost

        # Initialize embeddings
        self._embeddings_matcher = None
        if enabled:
            try:
                self._embeddings_matcher = EmbeddingsMatcher(model_name)
            except Exception as e:
                logger.warning(f"Failed to load embeddings model: {e}. SemanticSimilarityMatcher will be disabled.")
                self.enabled = False

        # Build property domain cache for context awareness
        self._prop_domain: Dict[str, Optional[str]] = {}
        if reasoner:
            self._prop_domain = {
                str(uri): (str(prop.domain) if prop.domain else None)
                for uri, prop in reasoner.properties.items()
            }

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
        """Match using embeddings only.

        Returns:
            Match result if embeddings available and score above threshold, else None
        """
        if not self.enabled or not properties or not self._embeddings_matcher:
            return None

        # Use enhanced scoring (phrase + token + id_boost)
        enriched = self._embeddings_matcher.enhanced_score_all(column, properties)
        if not enriched:
            return None

        # Pick best combined score above threshold
        best = enriched[0]
        if best['combined'] >= self.threshold:
            matched_prop = best['property']

            # Format evidence with embedding breakdown
            evidence_parts = [
                f"phrase={best['phrase_cosine']:.3f}",
                f"token={best['token_cosine']:.3f}"
            ]
            if best['id_boost'] > 0:
                evidence_parts.append(f"id_boost={best['id_boost']:.3f}")

            return MatchResult(
                property=matched_prop,
                match_type=MatchType.SEMANTIC_SIMILARITY,
                confidence=best['combined'],
                matched_via=f"embedding ({'; '.join(evidence_parts)})",
                matcher_name=self.name()
            )

        return None

