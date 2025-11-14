"""Graph-based ontology reasoning matcher.

This matcher leverages deep semantic structure of the ontology to make
intelligent matching decisions based on:
- Class hierarchies and inheritance
- Domain/Range validation
- Property relationships and paths
- Semantic distance and relevance
"""

from typing import List, Optional, Dict
from .base import (
    ColumnPropertyMatcher,
    MatchResult,
    MatchContext,
    MatchPriority
)
from ..ontology_analyzer import OntologyProperty
from ..data_analyzer import DataFieldAnalysis
from ..graph_reasoner import GraphReasoner
from ...models.alignment import MatchType


class GraphReasoningMatcher(ColumnPropertyMatcher):
    """Advanced matcher using ontology graph structure for reasoning.

    This matcher goes beyond simple label matching to understand the semantic
    context of properties within the ontology. It considers:

    1. Domain/Range compatibility with inferred data types
    2. Property inheritance from parent classes
    3. Semantic paths through the ontology
    4. Related properties that might be better matches
    5. Structural patterns in the data

    This matcher is particularly powerful when:
    - The ontology has rich hierarchical structure
    - Properties have well-defined domains and ranges
    - Data types can be reliably inferred
    - Context about related columns is available
    """

    def __init__(
        self,
        reasoner: GraphReasoner,
        enabled: bool = True,
        threshold: float = 0.6,
        validate_types: bool = True,
        use_inheritance: bool = True
    ):
        """Initialize graph reasoning matcher.

        Args:
            reasoner: GraphReasoner instance for ontology analysis
            enabled: Whether this matcher is active
            threshold: Minimum confidence for matches
            validate_types: Whether to validate data type compatibility
            use_inheritance: Whether to consider inherited properties
        """
        super().__init__(enabled, threshold)
        self.reasoner = reasoner
        self.validate_types = validate_types
        self.use_inheritance = use_inheritance

    def name(self) -> str:
        return "GraphReasoningMatcher"

    def priority(self) -> MatchPriority:
        return MatchPriority.MEDIUM

    def match(
        self,
        column: DataFieldAnalysis,
        properties: List[OntologyProperty],
        context: Optional[MatchContext] = None
    ) -> Optional[MatchResult]:
        """Match column using graph reasoning.

        Strategy:
        1. Score each property based on structural fit
        2. Validate domain/range compatibility
        3. Consider inherited properties
        4. Factor in semantic distance
        5. Return best match above threshold
        """
        if not self.enabled:
            return None

        best_match = None
        best_score = 0.0

        for prop in properties:
            score = self._score_property(column, prop, context)

            if score > best_score and score >= self.threshold:
                best_score = score
                best_match = prop

        if best_match:
            return MatchResult(
                property=best_match,
                match_type=MatchType.GRAPH_REASONING,
                confidence=best_score,
                matched_via=f"graph_reasoning(score={best_score:.3f})",
                matcher_name=self.name()
            )

        return None

    def _score_property(
        self,
        column: DataFieldAnalysis,
        prop: OntologyProperty,
        context: Optional[MatchContext]
    ) -> float:
        """Score a property based on graph reasoning.

        Returns:
            Score from 0.0 to 1.0
        """
        scores = []
        weights = []

        # 1. Data type compatibility (if validation enabled)
        if self.validate_types and column.inferred_type:
            is_valid, type_confidence = self.reasoner.validate_property_for_data_type(
                prop, column.inferred_type
            )
            if not is_valid:
                # Hard fail on type mismatch
                return 0.0
            scores.append(type_confidence)
            weights.append(0.3)

        # 2. Structural pattern matching
        if context and context.all_columns:
            structure_score = self._score_structural_fit(column, prop, context)
            if structure_score > 0:
                scores.append(structure_score)
                weights.append(0.25)

        # 3. Property context relevance
        context_score = self._score_property_context(column, prop)
        if context_score > 0:
            scores.append(context_score)
            weights.append(0.2)

        # 4. Semantic label similarity (as baseline)
        label_score = self._score_label_similarity(column, prop)
        scores.append(label_score)
        weights.append(0.25)

        # Calculate weighted average
        if not scores:
            return 0.0

        total_weight = sum(weights)
        weighted_score = sum(s * w for s, w in zip(scores, weights)) / total_weight

        return weighted_score

    def _score_structural_fit(
        self,
        column: DataFieldAnalysis,
        prop: OntologyProperty,
        context: MatchContext
    ) -> float:
        """Score based on structural patterns in the data.

        This looks for patterns like:
        - Foreign key relationships (if prop is ObjectProperty)
        - Related columns that map to sibling properties
        - Hierarchical data structures
        """
        score = 0.0

        # Check if this is an object property and column looks like FK
        if prop.is_object_property:
            # Look for FK patterns in column name
            fk_indicators = ['_id', 'id', 'ref', 'key', 'fk']
            col_name_lower = column.name.lower()

            if any(indicator in col_name_lower for indicator in fk_indicators):
                score += 0.4

            # Check if there's a unique constraint (typical for FKs)
            if column.is_unique:
                score += 0.2

        # Check if sibling properties are also matched by nearby columns
        if prop.domain:
            prop_context = self.reasoner.get_property_context(prop.uri)
            sibling_props = prop_context.sibling_properties

            if sibling_props and len(context.all_columns) > 1:
                # Check if other columns might match sibling properties
                matched_siblings = 0
                for sibling in sibling_props[:5]:  # Check up to 5 siblings
                    for other_col in context.all_columns:
                        if other_col.name != column.name:
                            if self._columns_match_roughly(other_col.name, sibling):
                                matched_siblings += 1
                                break

                if matched_siblings > 0:
                    # More matched siblings = stronger structural fit
                    sibling_score = min(matched_siblings / 3.0, 0.3)
                    score += sibling_score

        return min(score, 1.0)

    def _score_property_context(
        self,
        column: DataFieldAnalysis,
        prop: OntologyProperty
    ) -> float:
        """Score based on property's position in ontology.

        Properties that are:
        - Part of well-defined classes
        - Have clear domains and ranges
        - Are not too generic

        Score higher than orphaned or overly generic properties.
        """
        score = 0.0

        try:
            prop_context = self.reasoner.get_property_context(prop.uri)

            # Has well-defined domain
            if prop.domain:
                score += 0.3

            # Has well-defined range
            if prop.range_type:
                score += 0.2

            # Part of a larger class structure (has siblings)
            if prop_context.sibling_properties:
                num_siblings = len(prop_context.sibling_properties)
                # More siblings suggests it's part of a coherent model
                sibling_score = min(num_siblings / 10.0, 0.2)
                score += sibling_score

            # Has parent properties (specialized from more general property)
            if prop_context.parent_properties:
                score += 0.15

            # Domain has ancestors (part of class hierarchy)
            if prop_context.domain_ancestors:
                hierarchy_depth = len(prop_context.domain_ancestors)
                hierarchy_score = min(hierarchy_depth / 5.0, 0.15)
                score += hierarchy_score

        except Exception:
            # If we can't get context, neutral score
            score = 0.5

        return min(score, 1.0)

    def _score_label_similarity(
        self,
        column: DataFieldAnalysis,
        prop: OntologyProperty
    ) -> float:
        """Basic label-based similarity as fallback."""
        col_name_lower = column.name.lower().replace('_', ' ').replace('-', ' ')

        # Check all labels
        all_labels = prop.get_all_labels()

        max_similarity = 0.0
        for label in all_labels:
            label_lower = label.lower().replace('_', ' ').replace('-', ' ')

            # Exact match
            if col_name_lower == label_lower:
                max_similarity = max(max_similarity, 1.0)
                continue

            # Substring match
            if col_name_lower in label_lower or label_lower in col_name_lower:
                max_similarity = max(max_similarity, 0.7)
                continue

            # Word overlap
            col_words = set(col_name_lower.split())
            label_words = set(label_lower.split())

            if col_words and label_words:
                overlap = len(col_words & label_words)
                max_words = max(len(col_words), len(label_words))
                word_score = overlap / max_words
                max_similarity = max(max_similarity, word_score * 0.6)

        return max_similarity

    def _columns_match_roughly(self, column_name: str, prop: OntologyProperty) -> bool:
        """Quick check if column name roughly matches property."""
        col_lower = column_name.lower().replace('_', ' ')

        for label in prop.get_all_labels():
            label_lower = label.lower().replace('_', ' ')
            if col_lower in label_lower or label_lower in col_lower:
                return True

            # Check word overlap
            col_words = set(col_lower.split())
            label_words = set(label_lower.split())
            if len(col_words & label_words) >= min(len(col_words), len(label_words)) // 2:
                return True

        return False


class InheritanceAwareMatcher(ColumnPropertyMatcher):
    """Matcher that considers inherited properties from parent classes.

    When matching columns to a specific class, this matcher also considers
    properties inherited from parent classes in the ontology hierarchy.

    Example: If matching to a "MortgageLoan" class, also consider properties
    from parent "Loan" or "FinancialInstrument" classes.
    """

    def __init__(
        self,
        reasoner: GraphReasoner,
        target_class: Optional[str] = None,
        enabled: bool = True,
        threshold: float = 0.7
    ):
        """Initialize inheritance-aware matcher.

        Args:
            reasoner: GraphReasoner instance
            target_class: URI of target class to match to (optional)
            enabled: Whether this matcher is active
            threshold: Minimum confidence for matches
        """
        super().__init__(enabled, threshold)
        self.reasoner = reasoner
        self.target_class = target_class

    def name(self) -> str:
        return "InheritanceAwareMatcher"

    def priority(self) -> MatchPriority:
        return MatchPriority.MEDIUM

    def match(
        self,
        column: DataFieldAnalysis,
        properties: List[OntologyProperty],
        context: Optional[MatchContext] = None
    ) -> Optional[MatchResult]:
        """Match considering inherited properties."""
        if not self.enabled or not self.target_class:
            return None

        # Get inherited properties
        from rdflib import URIRef
        class_uri = URIRef(self.target_class)
        inherited_props = self.reasoner.get_inherited_properties(class_uri)

        # Expand property list with inherited ones
        all_props_map = {p.uri: p for p in properties}
        for inherited_prop in inherited_props:
            if inherited_prop.uri not in all_props_map:
                all_props_map[inherited_prop.uri] = inherited_prop

        expanded_properties = list(all_props_map.values())

        # Try to match with expanded list
        best_match = None
        best_score = 0.0

        for prop in expanded_properties:
            score = self._score_property(column, prop)

            if score > best_score and score >= self.threshold:
                best_score = score
                best_match = prop

        if best_match:
            # Check if this was an inherited property
            is_inherited = best_match.uri not in [p.uri for p in properties]

            match_type = (
                MatchType.INHERITED_PROPERTY
                if is_inherited
                else MatchType.GRAPH_REASONING
            )

            matched_via = (
                f"inherited_from_parent(score={best_score:.3f})"
                if is_inherited
                else f"direct_property(score={best_score:.3f})"
            )

            return MatchResult(
                property=best_match,
                match_type=match_type,
                confidence=best_score,
                matched_via=matched_via,
                matcher_name=self.name()
            )

        return None

    def _score_property(self, column: DataFieldAnalysis, prop: OntologyProperty) -> float:
        """Score property match."""
        col_name_lower = column.name.lower().replace('_', ' ')

        for label in prop.get_all_labels():
            label_lower = label.lower().replace('_', ' ')

            # Exact match
            if col_name_lower == label_lower:
                return 1.0

            # High similarity
            if col_name_lower in label_lower or label_lower in col_name_lower:
                return 0.8

        return 0.0

