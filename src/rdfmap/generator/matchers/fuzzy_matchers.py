"""Partial and fuzzy matching strategies."""

from typing import Optional, List
from .base import ColumnPropertyMatcher, MatchResult, MatchContext, MatchPriority
from ..ontology_analyzer import OntologyProperty
from ..data_analyzer import DataFieldAnalysis
from ...models.alignment import MatchType


class PartialStringMatcher(ColumnPropertyMatcher):
    """Matches columns using partial string matching."""

    def name(self) -> str:
        return "PartialStringMatcher"

    def priority(self) -> MatchPriority:
        return MatchPriority.MEDIUM

    def match(
        self,
        column: DataFieldAnalysis,
        properties: List[OntologyProperty],
        context: Optional[MatchContext] = None
    ) -> Optional[MatchResult]:
        col_clean = column.name.lower().replace("_", "").replace(" ", "")

        for prop in properties:
            all_labels = []
            if prop.pref_label:
                all_labels.append(prop.pref_label)
            if prop.label:
                all_labels.append(prop.label)
            all_labels.extend(prop.alt_labels)

            for label in all_labels:
                label_clean = label.lower().replace("_", "").replace(" ", "")
                if col_clean in label_clean or label_clean in col_clean:
                    return MatchResult(
                        property=prop,
                        match_type=MatchType.PARTIAL,
                        confidence=0.60,
                        matched_via=label,
                        matcher_name=self.name()
                    )

        return None


class FuzzyStringMatcher(ColumnPropertyMatcher):
    """Matches columns using fuzzy string matching on local names."""

    def name(self) -> str:
        return "FuzzyStringMatcher"

    def priority(self) -> MatchPriority:
        return MatchPriority.LOW

    def match(
        self,
        column: DataFieldAnalysis,
        properties: List[OntologyProperty],
        context: Optional[MatchContext] = None
    ) -> Optional[MatchResult]:
        col_clean = column.name.lower().replace("_", "").replace(" ", "")

        for prop in properties:
            local_name = str(prop.uri).split("#")[-1].split("/")[-1]
            local_clean = local_name.lower().replace("_", "")

            # Simple fuzzy: check if one contains the other
            if col_clean in local_clean or local_clean in col_clean:
                return MatchResult(
                    property=prop,
                    match_type=MatchType.FUZZY,
                    confidence=0.40,
                    matched_via=local_name,
                    matcher_name=self.name()
                )

        return None

