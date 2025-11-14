"""History-aware matcher that learns from past mapping decisions."""

from typing import Optional, List, Dict
from .base import ColumnPropertyMatcher, MatchResult, MatchContext, MatchPriority
from ..ontology_analyzer import OntologyProperty
from ..data_analyzer import DataFieldAnalysis
from ..mapping_history import MappingHistory
from ...models.alignment import MatchType


class HistoryAwareMatcher(ColumnPropertyMatcher):
    """Matches columns based on historical mapping decisions.

    This matcher learns from past mappings to improve future suggestions.
    It boosts confidence for properties that were successfully used before
    with similar column names.
    """

    def __init__(
        self,
        enabled: bool = True,
        threshold: float = 0.6,
        history_db: Optional[MappingHistory] = None
    ):
        """Initialize the history-aware matcher.

        Args:
            enabled: Whether this matcher is active
            threshold: Minimum confidence for matches (0-1)
            history_db: MappingHistory instance (creates default if None)
        """
        super().__init__(enabled, threshold)
        self.history = history_db or MappingHistory()

    def name(self) -> str:
        return "HistoryAwareMatcher"

    def priority(self) -> MatchPriority:
        return MatchPriority.MEDIUM

    def match(
        self,
        column: DataFieldAnalysis,
        properties: List[OntologyProperty],
        context: Optional[MatchContext] = None
    ) -> Optional[MatchResult]:
        """Match based on historical mapping decisions.

        Args:
            column: Column to match
            properties: Available properties
            context: Optional match context

        Returns:
            MatchResult if a historically successful match is found
        """
        # Find similar mappings from history
        similar_mappings = self.history.find_similar_mappings(
            column.name,
            limit=5,
            accepted_only=True
        )

        if not similar_mappings:
            return None

        # Look for matching properties in current options
        for historical in similar_mappings:
            for prop in properties:
                if str(prop.uri) == historical['property_uri']:
                    # Found a historical match!

                    # Get success rate for this property
                    success_rate = self.history.get_property_success_rate(
                        historical['property_uri']
                    )

                    # Calculate confidence based on:
                    # - Historical confidence (50%)
                    # - Success rate (30%)
                    # - Recency bonus (20%)
                    base_confidence = historical['confidence']
                    confidence = (
                        base_confidence * 0.5 +
                        success_rate * 0.3 +
                        0.2  # Recency bonus for exact match
                    )

                    # Cap at 0.95 (never claim perfect certainty from history alone)
                    confidence = min(confidence, 0.95)

                    if confidence >= self.threshold:
                        return MatchResult(
                            property=prop,
                            match_type=MatchType.SEMANTIC_SIMILARITY,  # Could add HISTORICAL
                            confidence=confidence,
                            matched_via=f"historical match (success rate: {success_rate:.2f})",
                            matcher_name=self.name()
                        )

        return None

    def boost_confidence(
        self,
        result: MatchResult,
        column_name: str
    ) -> MatchResult:
        """Boost confidence of a match based on historical success.

        This can be called by other matchers to enhance their results.

        Args:
            result: Existing match result
            column_name: Name of the column being matched

        Returns:
            Enhanced MatchResult with boosted confidence
        """
        # Check if this property was successful historically
        success_rate = self.history.get_property_success_rate(
            str(result.property.uri)
        )

        if success_rate > 0.7:  # High historical success
            # Boost confidence by up to 10%
            boost = (success_rate - 0.7) * 0.33  # Max 0.1 boost
            new_confidence = min(result.confidence + boost, 1.0)

            return MatchResult(
                property=result.property,
                match_type=result.match_type,
                confidence=new_confidence,
                matched_via=f"{result.matched_via} + history boost",
                matcher_name=result.matcher_name
            )

        return result

    def get_recommendations(
        self,
        column_name: str,
        top_k: int = 3
    ) -> List[Dict]:
        """Get property recommendations based on history.

        Args:
            column_name: Name of the column
            top_k: Number of recommendations to return

        Returns:
            List of recommendation dictionaries
        """
        similar = self.history.find_similar_mappings(
            column_name,
            limit=top_k,
            accepted_only=True
        )

        recommendations = []
        for mapping in similar:
            success_rate = self.history.get_property_success_rate(
                mapping['property_uri']
            )

            recommendations.append({
                'property_uri': mapping['property_uri'],
                'property_label': mapping['property_label'],
                'confidence': mapping['confidence'],
                'success_rate': success_rate,
                'times_used': 1,  # Could track this separately
                'last_used': mapping['timestamp']
            })

        return recommendations

    def close(self):
        """Close the history database connection."""
        if self.history:
            self.history.close()

