"""Structural matcher for detecting relationships and foreign keys.

This matcher identifies structural patterns in data (like foreign keys)
and matches them to object properties in the ontology.
"""

import re
from typing import Optional, List, Set, Tuple
from collections import Counter

from .base import ColumnPropertyMatcher, MatchResult, MatchContext, MatchPriority
from ..ontology_analyzer import OntologyProperty
from ..data_analyzer import DataFieldAnalysis
from ...models.alignment import MatchType


class StructuralMatcher(ColumnPropertyMatcher):
    """Matches columns based on structural patterns (foreign keys, relationships).

    This matcher detects:
    - Foreign key columns (e.g., borrower_id, customer_ref)
    - Identifier patterns in values
    - Relationships between columns
    - Matches to object properties in ontology
    """

    # Foreign key patterns (regex)
    FK_PATTERNS = [
        r'(.+)_id$',          # customer_id, loan_id
        r'(.+)_ref$',         # property_ref, account_ref
        r'(.+)Id$',           # customerId, loanId (camelCase)
        r'(.+)Ref$',          # customerRef, loanRef
        r'(.+)_key$',         # customer_key
        r'(.+)Key$',          # customerKey
        r'fk_(.+)$',          # fk_customer
        r'(.+)_fk$',          # customer_fk
    ]

    # ID value patterns (for validation)
    ID_VALUE_PATTERNS = [
        r'^[A-Z0-9]{3,}-[A-Z0-9]+$',  # ABC-123, LOAN-001
        r'^[A-Z]+\d+$',                # CUST123, B456
        r'^\d{5,}$',                   # 12345, 67890 (5+ digits)
        r'^[a-f0-9\-]{36}$',          # UUIDs
    ]

    def __init__(self, enabled: bool = True, threshold: float = 0.7):
        """Initialize the structural matcher.

        Args:
            enabled: Whether this matcher is active
            threshold: Minimum confidence for matches (0-1)
        """
        super().__init__(enabled, threshold)

    def name(self) -> str:
        return "StructuralMatcher"

    def priority(self) -> MatchPriority:
        return MatchPriority.MEDIUM

    def match(
        self,
        column: DataFieldAnalysis,
        properties: List[OntologyProperty],
        context: Optional[MatchContext] = None
    ) -> Optional[MatchResult]:
        """Match based on structural patterns.

        Args:
            column: Column to match
            properties: Available properties
            context: Optional match context

        Returns:
            MatchResult if a structural match is found
        """
        # Check if this looks like a foreign key
        fk_info = self._detect_foreign_key(column)
        if not fk_info:
            return None

        base_name, pattern_type = fk_info

        # Find object properties that match the base name
        best_match = None
        best_confidence = 0.0

        for prop in properties:
            if not prop.is_object_property:
                continue  # Only match to object properties

            # Check if property name relates to the FK base name
            confidence = self._calculate_relationship_confidence(
                base_name, prop, pattern_type
            )

            if confidence > best_confidence and confidence >= self.threshold:
                best_confidence = confidence
                best_match = prop

        if best_match:
            return MatchResult(
                property=best_match,
                match_type=MatchType.SEMANTIC_SIMILARITY,  # Could add STRUCTURAL
                confidence=best_confidence,
                matched_via=f"structural: {pattern_type} pattern",
                matcher_name=self.name()
            )

        return None

    def _detect_foreign_key(
        self,
        column: DataFieldAnalysis
    ) -> Optional[Tuple[str, str]]:
        """Detect if a column is likely a foreign key.

        Args:
            column: Column to analyze

        Returns:
            Tuple of (base_name, pattern_type) if FK detected, None otherwise
        """
        col_name = column.name

        # Check name patterns
        for pattern in self.FK_PATTERNS:
            match = re.search(pattern, col_name, re.IGNORECASE)
            if match:
                base_name = match.group(1)
                pattern_type = pattern

                # Validate with value patterns if available
                if column.sample_values:
                    if self._values_look_like_ids(column.sample_values):
                        return (base_name, f"FK pattern: {pattern}")
                else:
                    # No sample values, trust the name pattern
                    return (base_name, f"FK pattern: {pattern}")

        # Check if values look like IDs even without name pattern
        if column.sample_values:
            if self._values_look_like_ids(column.sample_values):
                # Extract potential base name (remove common suffixes)
                base_name = self._extract_base_name(col_name)
                return (base_name, "ID value pattern")

        return None

    def _values_look_like_ids(self, values: List) -> bool:
        """Check if values look like identifiers.

        Args:
            values: Sample values to check

        Returns:
            True if values match ID patterns
        """
        if not values:
            return False

        # Check if values match ID patterns
        matching_values = 0
        total_values = 0

        for value in values:
            if value is None or value == '':
                continue

            total_values += 1
            value_str = str(value)

            for pattern in self.ID_VALUE_PATTERNS:
                if re.match(pattern, value_str):
                    matching_values += 1
                    break

        if total_values == 0:
            return False

        # If >60% of values match ID patterns, consider it an ID column
        return (matching_values / total_values) > 0.6

    def _extract_base_name(self, col_name: str) -> str:
        """Extract base name from a column name.

        Args:
            col_name: Column name

        Returns:
            Base name without common suffixes
        """
        # Remove common ID suffixes
        suffixes = ['_id', '_ref', '_key', '_fk', 'Id', 'Ref', 'Key']
        name = col_name

        for suffix in suffixes:
            if name.endswith(suffix):
                name = name[:-len(suffix)]
                break

        return name

    def _calculate_relationship_confidence(
        self,
        base_name: str,
        prop: OntologyProperty,
        pattern_type: str
    ) -> float:
        """Calculate confidence for a FK-to-object-property match.

        Args:
            base_name: Base name extracted from FK column
            prop: Object property to match against
            pattern_type: Type of pattern that was detected

        Returns:
            Confidence score (0-1)
        """
        base_clean = base_name.lower().replace('_', '').replace(' ', '')

        # Check property label
        if prop.label:
            prop_clean = prop.label.lower().replace('_', '').replace(' ', '')

            # Check for "has" prefix pattern: "hasBorrower" matches "borrower"
            if prop_clean.startswith('has') and base_clean in prop_clean:
                return 0.9

            # Check if base name is in property label
            if base_clean in prop_clean or prop_clean in base_clean:
                return 0.85

        # Check prefLabel
        if prop.pref_label:
            pref_clean = prop.pref_label.lower().replace('_', '').replace(' ', '')
            if prop_clean.startswith('has') and base_clean in pref_clean:
                return 0.88
            if base_clean in pref_clean or pref_clean in base_clean:
                return 0.83

        # Check altLabels
        for alt_label in prop.alt_labels:
            alt_clean = alt_label.lower().replace('_', '').replace(' ', '')
            if base_clean in alt_clean or alt_clean in base_clean:
                return 0.80

        # Check local name
        local_name = str(prop.uri).split('#')[-1].split('/')[-1]
        local_clean = local_name.lower().replace('_', '')

        if base_clean in local_clean or local_clean in base_clean:
            return 0.75

        return 0.0

    def suggest_linked_object_mapping(
        self,
        fk_column: str,
        matched_property: OntologyProperty,
        context: Optional[MatchContext] = None
    ) -> dict:
        """Suggest a linked object mapping configuration.

        This generates a suggestion for the YAML mapping config
        to create a linked object relationship.

        Args:
            fk_column: Foreign key column name
            matched_property: Object property it matched to
            context: Optional match context

        Returns:
            Dictionary with linked object mapping suggestion
        """
        # Extract base name for the linked object
        base_name = self._extract_base_name(fk_column)

        # Get range class from property if available
        range_class = None
        if matched_property.range_type:
            range_class = str(matched_property.range_type)

        suggestion = {
            'name': f'{base_name} reference',
            'predicate': str(matched_property.uri),
            'class': range_class or f'ex:{base_name.title()}',
            'iri_template': f'{base_name}:{{{fk_column}}}',
            'properties': [
                {
                    'column': fk_column,
                    'as': f'ex:{base_name}ID',
                    'datatype': 'xsd:string'
                }
            ],
            '_comment': f'Detected {fk_column} as foreign key to {base_name}'
        }

        return suggestion

