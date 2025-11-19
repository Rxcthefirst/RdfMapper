"""Data type inference matcher using sample data and OWL restrictions.

This matcher analyzes the actual data types in columns and compares them
against OWL datatype restrictions in the ontology to find compatible matches.
"""

from typing import Optional, List, Set
from rdflib import RDF, RDFS, OWL, XSD, Namespace
from .base import ColumnPropertyMatcher, MatchResult, MatchContext, MatchPriority
from ..ontology_analyzer import OntologyProperty
from ..data_analyzer import DataFieldAnalysis
from ...models.alignment import MatchType


class DataTypeInferenceMatcher(ColumnPropertyMatcher):
    """Matches columns based on data type compatibility.

    This matcher:
    1. Infers the actual data type from sample values
    2. Gets the expected data type from OWL restrictions
    3. Matches only if types are compatible
    4. Provides confidence based solely on type compatibility (no name similarity)
    """

    # XSD type hierarchy for compatibility checking
    XSD_NUMERIC_TYPES = {
        XSD.integer, XSD.int, XSD.long, XSD.short, XSD.byte,
        XSD.decimal, XSD.float, XSD.double,
        XSD.positiveInteger, XSD.negativeInteger,
        XSD.nonNegativeInteger, XSD.nonPositiveInteger
    }

    XSD_STRING_TYPES = {
        XSD.string, XSD.normalizedString, XSD.token,
        XSD.language, XSD.Name, XSD.NCName, XSD.NMTOKEN
    }

    XSD_DATE_TYPES = {
        XSD.date, XSD.dateTime, XSD.time, XSD.gYear, XSD.gYearMonth
    }

    XSD_BOOLEAN_TYPES = {
        XSD.boolean
    }

    def __init__(self, enabled: bool = True, threshold: float = 0.0):
        """Initialize the data type matcher.

        Args:
            enabled: Whether this matcher is active
            threshold: Minimum confidence for matches (0-1)
                      Default 0.0 - always fire to provide type validation evidence
                      Confidence kept moderate so it never wins alone, only validates other matches
        """
        super().__init__(enabled, threshold)

    def name(self) -> str:
        return "DataTypeInferenceMatcher"

    def priority(self) -> MatchPriority:
        return MatchPriority.MEDIUM

    def match(
        self,
        column: DataFieldAnalysis,
        properties: List[OntologyProperty],
        context: Optional[MatchContext] = None
    ) -> Optional[MatchResult]:
        """Match based on data type compatibility.

        Args:
            column: Column to match
            properties: Available properties
            context: Optional match context

        Returns:
            MatchResult if a type-compatible match is found
        """
        # Infer the column's data type from sample values
        inferred_type = self._infer_column_type(column)
        if not inferred_type:
            return None

        # Find properties with compatible data types
        best_match = None
        best_confidence = 0.0

        for prop in properties:
            # Get expected type from ontology
            expected_types = self._get_property_datatype(prop)
            if not expected_types:
                continue

            # Check compatibility (always return result for evidence, even partial compatibility)
            compatibility = self._check_type_compatibility(inferred_type, expected_types)
            if compatibility > 0:
                # Datatype matcher provides ontological validation evidence
                # Confidence is moderate - validates other matches but doesn't win alone
                # This shows that the ontology's type system aligns with the data
                if compatibility >= 1.0:
                    confidence = 0.68  # Perfect type match - strong validation
                elif compatibility >= 0.9:
                    confidence = 0.65  # Very compatible (e.g., int → decimal)
                elif compatibility >= 0.7:
                    confidence = 0.62  # Compatible with conversion
                elif compatibility >= 0.5:
                    confidence = 0.60  # Moderate compatibility
                else:
                    confidence = 0.58  # Minimal compatibility (still evidence)

                if confidence > best_confidence:
                    best_confidence = confidence
                    best_match = prop
            elif compatibility > 0.3:
                # Even weak compatibility provides evidence
                confidence = 0.55
                if confidence > best_confidence:
                    best_confidence = confidence
                    best_match = prop

        if best_match:
            # Build detailed type compatibility message
            expected_types_str = ', '.join(sorted(self._get_property_datatype(best_match)))
            compatibility_pct = int(self._check_type_compatibility(inferred_type, self._get_property_datatype(best_match)) * 100)

            return MatchResult(
                property=best_match,
                match_type=MatchType.DATA_TYPE_COMPATIBILITY,
                confidence=best_confidence,
                matched_via=f"Type validation: {inferred_type} → {expected_types_str} ({compatibility_pct}% compatible)",
                matcher_name=self.name()
            )

        return None

    def _infer_column_type(self, column: DataFieldAnalysis) -> Optional[str]:
        """Infer data type from column analysis.

        Args:
            column: Column to analyze

        Returns:
            Inferred XSD type (e.g., "integer", "string", "date")
        """
        # Use the data analyzer's inferred type if available
        if column.inferred_type:
            type_map = {
                'integer': 'integer',
                'int': 'integer',
                'float': 'decimal',
                'decimal': 'decimal',
                'double': 'double',
                'string': 'string',
                'str': 'string',
                'date': 'date',
                'datetime': 'dateTime',
                'boolean': 'boolean',
                'bool': 'boolean'
            }
            return type_map.get(column.inferred_type.lower())

        # Fallback: analyze sample values
        if not column.sample_values:
            return None

        # Check if all non-null values are numeric
        numeric_count = 0
        integer_count = 0
        float_count = 0

        for value in column.sample_values:
            if value is None or value == '':
                continue

            try:
                float_val = float(str(value))
                numeric_count += 1

                if float_val.is_integer():
                    integer_count += 1
                else:
                    float_count += 1
            except (ValueError, TypeError):
                pass

        total_values = len([v for v in column.sample_values if v is not None and v != ''])

        if numeric_count == total_values and total_values > 0:
            if integer_count == total_values:
                return 'integer'
            else:
                return 'decimal'

        # Check for dates (basic pattern matching)
        date_patterns = ['-', '/', ':']
        date_count = sum(1 for v in column.sample_values
                        if v and any(p in str(v) for p in date_patterns))

        if date_count > total_values * 0.8:
            return 'date'

        # Default to string
        return 'string'

    def _get_property_datatype(self, prop: OntologyProperty) -> Set[str]:
        """Get expected datatype(s) from property.

        Args:
            prop: Property to check

        Returns:
            Set of expected XSD type names
        """
        expected_types = set()

        # Check the range_type from ontology analyzer
        if prop.range_type:
            range_str = str(prop.range_type)

            # Extract XSD type name
            if 'XMLSchema#' in range_str:
                xsd_type = range_str.split('#')[-1]
                expected_types.add(xsd_type.lower())
            elif range_str.startswith('xsd:'):
                xsd_type = range_str.split(':')[-1]
                expected_types.add(xsd_type.lower())

        # If no explicit range, try to infer from property name
        if not expected_types:
            prop_name = str(prop.label or prop.uri).lower()

            # Remove heuristic type inference from property names - this is too dangerous
            # It causes wrong matches like "loanNumber" being inferred as integer just because "number" is in the name
            # Datatype matcher should ONLY match on explicit range definitions in the ontology
            pass

        return expected_types

    def _check_type_compatibility(
        self,
        inferred: str,
        expected: Set[str]
    ) -> float:
        """Check if inferred type is compatible with expected types.

        Args:
            inferred: Inferred type from data
            expected: Set of expected types from ontology

        Returns:
            Compatibility score (0-1)
        """
        # Exact match
        if inferred in expected:
            return 1.0

        # Check type family compatibility
        inferred_lower = inferred.lower()
        expected_lower = {t.lower() for t in expected}

        # Numeric compatibility
        if inferred_lower in ['integer', 'int', 'long']:
            if any(t in ['integer', 'int', 'long', 'decimal', 'double', 'float']
                   for t in expected_lower):
                return 0.9

        if inferred_lower in ['decimal', 'float', 'double']:
            if any(t in ['decimal', 'double', 'float'] for t in expected_lower):
                return 1.0
            if any(t in ['integer', 'int'] for t in expected_lower):
                return 0.7  # Can convert but may lose precision

        # Date compatibility
        if inferred_lower in ['date', 'datetime']:
            if any(t in ['date', 'datetime', 'time'] for t in expected_lower):
                return 0.9

        # String is compatible with anything (as fallback)
        if inferred_lower == 'string':
            return 0.5

        # If expected includes string, moderate compatibility
        if 'string' in expected_lower:
            return 0.6

        return 0.0

    def _calculate_name_similarity(
        self,
        column_name: str,
        prop: OntologyProperty
    ) -> float:
        """Deprecated: Name similarity removed from datatype matcher (kept for backward compat, returns 0)."""
        return 0.0
