"""Exact label matching strategies (SKOS and rdfs:label)."""

from typing import Optional, List
from .base import ColumnPropertyMatcher, MatchResult, MatchContext, MatchPriority
from ..ontology_analyzer import OntologyProperty
from ..data_analyzer import DataFieldAnalysis
from ...models.alignment import MatchType


class ExactPrefLabelMatcher(ColumnPropertyMatcher):
    """Matches columns to SKOS prefLabel exactly."""

    def name(self) -> str:
        return "ExactPrefLabelMatcher"

    def priority(self) -> MatchPriority:
        return MatchPriority.CRITICAL

    def match(
        self,
        column: DataFieldAnalysis,
        properties: List[OntologyProperty],
        context: Optional[MatchContext] = None
    ) -> Optional[MatchResult]:
        col_clean = column.name.lower().replace("_", "").replace(" ", "")

        for prop in properties:
            if prop.pref_label:
                label_clean = prop.pref_label.lower().replace("_", "").replace(" ", "")
                if col_clean == label_clean:
                    return MatchResult(
                        property=prop,
                        match_type=MatchType.EXACT_PREF_LABEL,
                        confidence=0.98,
                        matched_via=prop.pref_label,
                        matcher_name=self.name()
                    )

        return None


class ExactRdfsLabelMatcher(ColumnPropertyMatcher):
    """Matches columns to rdfs:label exactly."""

    def name(self) -> str:
        return "ExactRdfsLabelMatcher"

    def priority(self) -> MatchPriority:
        return MatchPriority.HIGH

    def match(
        self,
        column: DataFieldAnalysis,
        properties: List[OntologyProperty],
        context: Optional[MatchContext] = None
    ) -> Optional[MatchResult]:
        col_clean = column.name.lower().replace("_", "").replace(" ", "")

        for prop in properties:
            if prop.label:
                label_clean = prop.label.lower().replace("_", "").replace(" ", "")
                if col_clean == label_clean:
                    return MatchResult(
                        property=prop,
                        match_type=MatchType.EXACT_LABEL,
                        confidence=0.95,
                        matched_via=prop.label,
                        matcher_name=self.name()
                    )

        return None


class ExactAltLabelMatcher(ColumnPropertyMatcher):
    """Matches columns to SKOS altLabel exactly."""

    def name(self) -> str:
        return "ExactAltLabelMatcher"

    def priority(self) -> MatchPriority:
        return MatchPriority.HIGH

    def match(
        self,
        column: DataFieldAnalysis,
        properties: List[OntologyProperty],
        context: Optional[MatchContext] = None
    ) -> Optional[MatchResult]:
        col_clean = column.name.lower().replace("_", "").replace(" ", "")

        for prop in properties:
            for alt_label in prop.alt_labels:
                label_clean = alt_label.lower().replace("_", "").replace(" ", "")
                if col_clean == label_clean:
                    return MatchResult(
                        property=prop,
                        match_type=MatchType.EXACT_ALT_LABEL,
                        confidence=0.90,
                        matched_via=alt_label,
                        matcher_name=self.name()
                    )

        return None


class ExactHiddenLabelMatcher(ColumnPropertyMatcher):
    """Matches columns to SKOS hiddenLabel exactly."""

    def name(self) -> str:
        return "ExactHiddenLabelMatcher"

    def priority(self) -> MatchPriority:
        return MatchPriority.HIGH

    def match(
        self,
        column: DataFieldAnalysis,
        properties: List[OntologyProperty],
        context: Optional[MatchContext] = None
    ) -> Optional[MatchResult]:
        col_clean = column.name.lower().replace("_", "").replace(" ", "")

        for prop in properties:
            for hidden_label in prop.hidden_labels:
                label_clean = hidden_label.lower().replace("_", "").replace(" ", "")
                if col_clean == label_clean:
                    return MatchResult(
                        property=prop,
                        match_type=MatchType.EXACT_HIDDEN_LABEL,
                        confidence=0.85,
                        matched_via=hidden_label,
                        matcher_name=self.name()
                    )

        return None


class ExactLocalNameMatcher(ColumnPropertyMatcher):
    """Matches columns to property local name exactly."""

    def name(self) -> str:
        return "ExactLocalNameMatcher"

    def priority(self) -> MatchPriority:
        return MatchPriority.HIGH

    def match(
        self,
        column: DataFieldAnalysis,
        properties: List[OntologyProperty],
        context: Optional[MatchContext] = None
    ) -> Optional[MatchResult]:
        col_clean = column.name.lower().replace("_", "")

        for prop in properties:
            local_name = str(prop.uri).split("#")[-1].split("/")[-1]
            local_clean = local_name.lower().replace("_", "")
            if col_clean == local_clean:
                return MatchResult(
                    property=prop,
                    match_type=MatchType.EXACT_LOCAL_NAME,
                    confidence=0.80,
                    matched_via=local_name,
                    matcher_name=self.name()
                )

        return None

