"""OWL Characteristics Matcher using Functional, InverseFunctional, and other OWL property types.

This matcher leverages OWL property characteristics to:
1. Identify potential identifiers (InverseFunctional properties)
2. Validate data patterns against OWL definitions
3. Boost confidence when data patterns match OWL semantics
4. Suggest appropriate properties based on data characteristics
"""

from typing import Optional, List, Dict, Set
from rdflib import OWL, RDF
from .base import ColumnPropertyMatcher, MatchResult, MatchContext, MatchPriority
from ..ontology_analyzer import OntologyProperty, OntologyAnalyzer
from ..data_analyzer import DataFieldAnalysis
from ...models.alignment import MatchType


class OWLCharacteristicsMatcher(ColumnPropertyMatcher):
    """Matches columns using OWL property characteristics (Functional, InverseFunctional, etc.)."""

    def __init__(
        self,
        ontology_analyzer: OntologyAnalyzer,
        enabled: bool = True,
        threshold: float = 0.60,
        ifp_uniqueness_threshold: float = 0.90,  # % unique for IFP
        fp_uniqueness_threshold: float = 0.95   # % unique for FP
    ):
        """Initialize the OWL characteristics matcher.

        Args:
            ontology_analyzer: Analyzer with loaded ontology graph
            enabled: Whether this matcher is enabled
            threshold: Minimum confidence threshold
            ifp_uniqueness_threshold: Min uniqueness ratio to consider IFP match (0-1)
            fp_uniqueness_threshold: Min uniqueness ratio to consider FP match (0-1)
        """
        super().__init__(enabled, threshold)
        self.ontology = ontology_analyzer
        self.ifp_uniqueness_threshold = ifp_uniqueness_threshold
        self.fp_uniqueness_threshold = fp_uniqueness_threshold

        # Build OWL characteristics cache
        self._owl_cache: Dict[str, Dict[str, any]] = {}
        self._build_owl_cache()

    def name(self) -> str:
        return "OWLCharacteristicsMatcher"

    def priority(self) -> MatchPriority:
        return MatchPriority.HIGH  # High priority for ontology-based reasoning

    def _build_owl_cache(self):
        """Build cache of OWL property characteristics from ontology."""
        graph = self.ontology.graph

        for prop_uri in self.ontology.properties.keys():
            from rdflib import URIRef

            # Ensure URIRef
            if isinstance(prop_uri, str):
                prop_uri_ref = URIRef(prop_uri)
            else:
                prop_uri_ref = prop_uri

            owl_info = {
                'is_functional': False,
                'is_inverse_functional': False,
                'is_transitive': False,
                'is_symmetric': False,
                'is_asymmetric': False,
                'is_reflexive': False,
                'is_irreflexive': False,
                'equivalent_properties': set(),
                'inverse_of': set()
            }

            # Check for Functional Property
            if (prop_uri_ref, RDF.type, OWL.FunctionalProperty) in graph:
                owl_info['is_functional'] = True

            # Check for InverseFunctional Property
            if (prop_uri_ref, RDF.type, OWL.InverseFunctionalProperty) in graph:
                owl_info['is_inverse_functional'] = True

            # Check for Transitive Property
            if (prop_uri_ref, RDF.type, OWL.TransitiveProperty) in graph:
                owl_info['is_transitive'] = True

            # Check for Symmetric Property
            if (prop_uri_ref, RDF.type, OWL.SymmetricProperty) in graph:
                owl_info['is_symmetric'] = True

            # Check for Asymmetric Property
            if (prop_uri_ref, RDF.type, OWL.AsymmetricProperty) in graph:
                owl_info['is_asymmetric'] = True

            # Check for Reflexive Property
            if (prop_uri_ref, RDF.type, OWL.ReflexiveProperty) in graph:
                owl_info['is_reflexive'] = True

            # Check for Irreflexive Property
            if (prop_uri_ref, RDF.type, OWL.IrreflexiveProperty) in graph:
                owl_info['is_irreflexive'] = True

            # Get equivalent properties
            for equiv in graph.objects(prop_uri_ref, OWL.equivalentProperty):
                if equiv != prop_uri_ref:
                    owl_info['equivalent_properties'].add(str(equiv))

            # Get inverse properties
            for inverse in graph.objects(prop_uri_ref, OWL.inverseOf):
                if inverse != prop_uri_ref:
                    owl_info['inverse_of'].add(str(inverse))

            self._owl_cache[str(prop_uri)] = owl_info

    def _get_owl_info(self, prop: OntologyProperty) -> Dict:
        """Get OWL characteristics for a property."""
        return self._owl_cache.get(str(prop.uri), {
            'is_functional': False,
            'is_inverse_functional': False,
            'is_transitive': False,
            'is_symmetric': False,
            'is_asymmetric': False,
            'is_reflexive': False,
            'is_irreflexive': False,
            'equivalent_properties': set(),
            'inverse_of': set()
        })

    def _calculate_uniqueness_ratio(self, column: DataFieldAnalysis) -> float:
        """Calculate uniqueness ratio for column data.

        Returns:
            Ratio of unique values to total values (0.0 to 1.0)
        """
        if not column.sample_values or len(column.sample_values) == 0:
            return 0.0

        # Filter out None/null values
        non_null_values = [v for v in column.sample_values if v is not None and v != '']

        if len(non_null_values) == 0:
            return 0.0

        unique_count = len(set(non_null_values))
        return unique_count / len(non_null_values)

    def _has_id_pattern(self, column: DataFieldAnalysis) -> bool:
        """Check if column name or values suggest it's an identifier."""
        col_name_lower = column.name.lower()

        # Check name patterns
        id_indicators = ['id', '_id', 'key', 'code', 'number', 'ssn', 'email', 'username']
        has_id_name = any(indicator in col_name_lower for indicator in id_indicators)

        # Check value patterns (if available)
        has_id_pattern = False
        if column.sample_values and len(column.sample_values) > 0:
            sample = str(column.sample_values[0]) if column.sample_values[0] else ""

            # Common ID patterns
            import re
            id_patterns = [
                r'^[A-Z]{2,4}-?\d+$',  # CUST-001, ABC123
                r'^\d{5,}$',            # Long numbers
                r'^[0-9a-f]{8}-[0-9a-f]{4}',  # UUIDs
                r'^\w+@\w+\.\w+$'       # Emails
            ]

            has_id_pattern = any(re.match(pattern, sample) for pattern in id_patterns)

        return has_id_name or has_id_pattern

    def _matches_functional_property(self, column: DataFieldAnalysis, prop: OntologyProperty) -> bool:
        """Check if column data matches Functional Property semantics.

        Functional Property: Each subject can have at most one value.
        In data terms: If we have subject column, this property should have unique or mostly unique values.
        """
        owl_info = self._get_owl_info(prop)

        if not owl_info['is_functional']:
            return False

        # For functional properties, we expect relatively high uniqueness
        # (but not necessarily 100% as there could be repeated subjects)
        uniqueness = self._calculate_uniqueness_ratio(column)
        return uniqueness >= self.fp_uniqueness_threshold

    def _matches_inverse_functional_property(
        self,
        column: DataFieldAnalysis,
        prop: OntologyProperty
    ) -> bool:
        """Check if column data matches InverseFunctional Property semantics.

        InverseFunctional Property: Each value uniquely identifies a subject.
        In data terms: Values should be unique (like IDs, emails, SSNs).
        """
        owl_info = self._get_owl_info(prop)

        if not owl_info['is_inverse_functional']:
            return False

        # IFP requires very high uniqueness
        uniqueness = self._calculate_uniqueness_ratio(column)
        return uniqueness >= self.ifp_uniqueness_threshold

    def match(
        self,
        column: DataFieldAnalysis,
        properties: List[OntologyProperty],
        context: Optional[MatchContext] = None
    ) -> Optional[MatchResult]:
        """Match column to property using OWL characteristics.

        Matching strategies:
        1. Check if column is unique identifier → match to InverseFunctional properties
        2. Check if column values are mostly unique → match to Functional properties
        3. Validate data patterns against OWL semantics
        4. Boost confidence when characteristics align
        """
        if not properties:
            return None

        col_name_lower = column.name.lower()
        col_name_normalized = col_name_lower.replace('_', '').replace('-', '').replace(' ', '')

        # Calculate column characteristics
        uniqueness_ratio = self._calculate_uniqueness_ratio(column)
        has_id_pattern = self._has_id_pattern(column)

        best_match = None
        best_confidence = 0.0
        match_reasoning = []

        for prop in properties:
            owl_info = self._get_owl_info(prop)

            # Get all labels
            labels = prop.get_all_labels()
            if not labels:
                uri_str = str(prop.uri)
                local_name = uri_str.split('#')[-1].split('/')[-1]
                if local_name:
                    labels = [local_name]

            # Try label matching with OWL validation
            for label in labels:
                if not label:
                    continue

                label_lower = label.lower()
                label_no_has = label_lower[4:] if label_lower.startswith('has ') else label_lower
                label_no_has = label_no_has[3:] if label_no_has.startswith('has') else label_no_has
                label_normalized = label_no_has.replace('_', '').replace('-', '').replace(' ', '')

                # Check for label match
                is_match = (
                    col_name_lower == label_lower or
                    col_name_lower == label_no_has or
                    col_name_normalized == label_normalized or
                    col_name_lower.replace('_', '') == label_no_has.replace(' ', '') or
                    label_no_has in col_name_lower or
                    col_name_lower in label_no_has
                )

                if not is_match:
                    continue

                # We have a label match - now validate with OWL characteristics
                confidence = 0.70  # Base confidence for label match
                reasons = [f"label match: '{label}'"]

                # InverseFunctional Property validation
                if owl_info['is_inverse_functional']:
                    if uniqueness_ratio >= self.ifp_uniqueness_threshold:
                        # Data matches IFP semantics perfectly
                        confidence += 0.25
                        reasons.append(f"IFP validated: {uniqueness_ratio:.0%} unique")
                    elif uniqueness_ratio >= 0.70:
                        # Decent uniqueness, partial match
                        confidence += 0.10
                        reasons.append(f"IFP partial: {uniqueness_ratio:.0%} unique")
                    else:
                        # Data doesn't match IFP - reduce confidence
                        confidence -= 0.15
                        reasons.append(f"IFP violation: only {uniqueness_ratio:.0%} unique")

                    if has_id_pattern:
                        confidence += 0.05
                        reasons.append("ID pattern detected")

                # Functional Property validation
                elif owl_info['is_functional']:
                    if uniqueness_ratio >= self.fp_uniqueness_threshold:
                        confidence += 0.15
                        reasons.append(f"FP validated: {uniqueness_ratio:.0%} unique")
                    elif uniqueness_ratio >= 0.70:
                        confidence += 0.05
                        reasons.append(f"FP acceptable: {uniqueness_ratio:.0%} unique")

                # Symmetric property
                if owl_info['is_symmetric']:
                    reasons.append("symmetric property")
                    # Could check if data shows bidirectional relationships

                # Transitive property
                if owl_info['is_transitive']:
                    reasons.append("transitive property")
                    # Could check for relationship chains

                # Cap confidence at 1.0
                confidence = min(confidence, 1.0)

                # Update best match if this is better
                if confidence > best_confidence:
                    best_confidence = confidence
                    best_match = prop
                    match_reasoning = reasons

        # Special case: Column looks like unique identifier but no IFP found
        if not best_match and has_id_pattern and uniqueness_ratio >= self.ifp_uniqueness_threshold:
            # Look for any property with "id", "identifier", "key" in name
            for prop in properties:
                labels = prop.get_all_labels()
                for label in labels:
                    if not label:
                        continue

                    label_lower = label.lower()
                    if any(id_word in label_lower for id_word in ['id', 'identifier', 'key', 'code']):
                        # Found a property that looks like an ID
                        # Check if it should be IFP (suggest enrichment)
                        confidence = 0.75
                        reasons = [
                            f"label match: '{label}'",
                            f"high uniqueness: {uniqueness_ratio:.0%}",
                            "ID pattern detected",
                            "⚠ Consider marking as InverseFunctionalProperty"
                        ]

                        if confidence > best_confidence:
                            best_confidence = confidence
                            best_match = prop
                            match_reasoning = reasons
                        break

        # Return best match if above threshold
        if best_match and best_confidence >= self.threshold:
            matched_via = " + ".join(match_reasoning)

            return MatchResult(
                property=best_match,
                match_type=MatchType.GRAPH_REASONING,
                confidence=best_confidence,
                matched_via=f"OWL characteristics: {matched_via}",
                matcher_name=self.name()
            )

        return None

    def get_owl_characteristics(self, prop: OntologyProperty) -> Dict:
        """Get detailed OWL characteristics for a property.

        Useful for debugging and reporting.

        Returns:
            Dictionary with OWL characteristics
        """
        owl_info = self._get_owl_info(prop)

        characteristics = []
        if owl_info['is_functional']:
            characteristics.append('Functional')
        if owl_info['is_inverse_functional']:
            characteristics.append('InverseFunctional')
        if owl_info['is_transitive']:
            characteristics.append('Transitive')
        if owl_info['is_symmetric']:
            characteristics.append('Symmetric')
        if owl_info['is_asymmetric']:
            characteristics.append('Asymmetric')
        if owl_info['is_reflexive']:
            characteristics.append('Reflexive')
        if owl_info['is_irreflexive']:
            characteristics.append('Irreflexive')

        return {
            'property': prop,
            'characteristics': characteristics,
            'is_functional': owl_info['is_functional'],
            'is_inverse_functional': owl_info['is_inverse_functional'],
            'is_transitive': owl_info['is_transitive'],
            'is_symmetric': owl_info['is_symmetric'],
            'equivalent_properties': list(owl_info['equivalent_properties']),
            'inverse_of': list(owl_info['inverse_of']),
            'can_be_identifier': owl_info['is_inverse_functional'],
            'expects_single_value': owl_info['is_functional']
        }

