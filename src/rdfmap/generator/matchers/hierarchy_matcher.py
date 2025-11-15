"""Property Hierarchy Matcher using rdfs:subPropertyOf reasoning.

This matcher leverages property hierarchies defined in ontologies to:
1. Match columns to properties with inheritance awareness
2. Understand property specificity levels
3. Boost confidence based on hierarchy position
4. Suggest parent/child properties as alternatives
"""

from typing import Optional, List, Dict, Set
from rdflib import RDF, RDFS, Namespace
from .base import ColumnPropertyMatcher, MatchResult, MatchContext, MatchPriority
from ..ontology_analyzer import OntologyProperty, OntologyAnalyzer
from ..data_analyzer import DataFieldAnalysis
from ...models.alignment import MatchType


class PropertyHierarchyMatcher(ColumnPropertyMatcher):
    """Matches columns using property hierarchy reasoning (rdfs:subPropertyOf)."""

    def __init__(
        self,
        ontology_analyzer: OntologyAnalyzer,
        enabled: bool = True,
        threshold: float = 0.65,
        hierarchy_boost: float = 0.15
    ):
        """Initialize the property hierarchy matcher.

        Args:
            ontology_analyzer: Analyzer with loaded ontology graph
            enabled: Whether this matcher is enabled
            threshold: Minimum confidence threshold
            hierarchy_boost: Confidence boost for hierarchy matches (0.0-0.3)
        """
        super().__init__(enabled, threshold)
        self.ontology = ontology_analyzer
        self.hierarchy_boost = min(hierarchy_boost, 0.3)  # Cap at 0.3

        # Build property hierarchy cache
        self._hierarchy_cache: Dict[str, Dict[str, any]] = {}
        self._build_hierarchy_cache()

    def name(self) -> str:
        return "PropertyHierarchyMatcher"

    def priority(self) -> MatchPriority:
        return MatchPriority.HIGH  # High priority for ontology-based reasoning

    def _build_hierarchy_cache(self):
        """Build cache of property hierarchies from ontology."""
        from rdflib import URIRef

        graph = self.ontology.graph

        for prop_uri in self.ontology.properties.keys():
            hierarchy_info = {
                'parents': set(),
                'children': set(),
                'ancestors': set(),  # All parents recursively
                'descendants': set(),  # All children recursively
                'depth': 0,  # Distance from root
                'specificity': 0.0  # How specific this property is (0=general, 1=specific)
            }

            # Ensure we're working with URIRef
            if isinstance(prop_uri, str):
                prop_uri_ref = URIRef(prop_uri)
            else:
                prop_uri_ref = prop_uri

            # Get direct parents (subPropertyOf)
            for parent in graph.objects(prop_uri_ref, RDFS.subPropertyOf):
                if parent != prop_uri_ref:  # Avoid self-reference
                    hierarchy_info['parents'].add(str(parent))

            # Get direct children (inverse of subPropertyOf)
            for child in graph.subjects(RDFS.subPropertyOf, prop_uri_ref):
                if child != prop_uri_ref:
                    hierarchy_info['children'].add(str(child))

            # Calculate ancestors (recursive parents)
            hierarchy_info['ancestors'] = self._get_ancestors(prop_uri_ref, graph)

            # Calculate descendants (recursive children)
            hierarchy_info['descendants'] = self._get_descendants(prop_uri_ref, graph)

            # Calculate depth (distance from root)
            hierarchy_info['depth'] = len(hierarchy_info['ancestors'])

            # Calculate specificity (0=root, 1=leaf)
            # More specific = deeper in hierarchy + fewer children
            max_depth = 10  # Reasonable maximum depth
            depth_score = min(hierarchy_info['depth'] / max_depth, 1.0)
            child_penalty = len(hierarchy_info['children']) * 0.1
            hierarchy_info['specificity'] = max(0.0, depth_score - child_penalty)

            self._hierarchy_cache[str(prop_uri)] = hierarchy_info

    def _get_ancestors(self, prop_uri, graph) -> Set[str]:
        """Get all ancestors (recursive parents) of a property.

        Args:
            prop_uri: URIRef of the property
            graph: RDFLib graph

        Returns:
            Set of ancestor URI strings
        """
        from rdflib import URIRef

        ancestors = set()
        to_process = {prop_uri}
        processed = set()

        while to_process:
            current = to_process.pop()
            if current in processed:
                continue
            processed.add(current)

            for parent in graph.objects(current, RDFS.subPropertyOf):
                parent_str = str(parent)
                if parent != current and parent_str not in ancestors:
                    ancestors.add(parent_str)
                    to_process.add(parent)

        return ancestors

    def _get_descendants(self, prop_uri, graph) -> Set[str]:
        """Get all descendants (recursive children) of a property.

        Args:
            prop_uri: URIRef of the property
            graph: RDFLib graph

        Returns:
            Set of descendant URI strings
        """
        from rdflib import URIRef

        descendants = set()
        to_process = {prop_uri}
        processed = set()

        while to_process:
            current = to_process.pop()
            if current in processed:
                continue
            processed.add(current)

            for child in graph.subjects(RDFS.subPropertyOf, current):
                child_str = str(child)
                if child != current and child_str not in descendants:
                    descendants.add(child_str)
                    to_process.add(child)

        return descendants

    def _get_hierarchy_info(self, prop: OntologyProperty) -> Dict:
        """Get hierarchy information for a property."""
        return self._hierarchy_cache.get(str(prop.uri), {
            'parents': set(),
            'children': set(),
            'ancestors': set(),
            'descendants': set(),
            'depth': 0,
            'specificity': 0.0
        })

    def _calculate_hierarchy_confidence(
        self,
        prop: OntologyProperty,
        base_confidence: float,
        match_type: str
    ) -> float:
        """Calculate confidence boost based on hierarchy position.

        Args:
            prop: The matched property
            base_confidence: Base confidence from label matching
            match_type: Type of match (exact, fuzzy, parent, child)

        Returns:
            Adjusted confidence score
        """
        hierarchy_info = self._get_hierarchy_info(prop)

        if match_type == "exact":
            # Exact matches get full hierarchy boost
            # More specific properties get higher boost
            specificity_boost = hierarchy_info['specificity'] * self.hierarchy_boost
            return min(base_confidence + specificity_boost, 1.0)

        elif match_type == "parent":
            # Matched to parent property (more general)
            # Lower confidence than exact, but valid
            # Deeper parents (more general) get lower confidence
            depth = hierarchy_info['depth']
            parent_penalty = min(depth * 0.05, 0.2)  # Max 0.2 penalty
            return base_confidence - parent_penalty

        elif match_type == "child":
            # Matched to child property (more specific)
            # Higher confidence than parent
            # But not as high as exact
            specificity_boost = hierarchy_info['specificity'] * (self.hierarchy_boost * 0.5)
            return min(base_confidence + specificity_boost - 0.05, 0.95)

        return base_confidence

    def match(
        self,
        column: DataFieldAnalysis,
        properties: List[OntologyProperty],
        context: Optional[MatchContext] = None
    ) -> Optional[MatchResult]:
        """Match column to property using hierarchy reasoning.

        Matching logic:
        1. Check for exact label matches
        2. Check parent properties (generalization)
        3. Check child properties (specialization)
        4. Boost confidence based on hierarchy position
        5. Provide alternatives from hierarchy
        """
        if not properties:
            return None

        col_name_lower = column.name.lower()
        col_name_normalized = col_name_lower.replace('_', '').replace('-', '').replace(' ', '')
        best_match = None
        best_confidence = 0.0
        alternatives = []
        match_type_used = "none"

        for prop in properties:
            # Get all labels for this property
            labels = prop.get_all_labels()
            if not labels:
                # If no labels, try to extract from URI
                uri_str = str(prop.uri)
                local_name = uri_str.split('#')[-1].split('/')[-1]
                if local_name:
                    labels = [local_name]

            hierarchy_info = self._get_hierarchy_info(prop)

            # Check for exact match on any label
            for label in labels:
                if not label:
                    continue

                label_lower = label.lower()
                label_normalized = label_lower.replace('_', '').replace('-', '').replace(' ', '')

                # Also create version without common prefixes
                label_no_has = label_lower
                if label_lower.startswith('has '):
                    label_no_has = label_lower[4:]  # Remove "has "
                elif label_lower.startswith('has'):
                    label_no_has = label_lower[3:]  # Remove "has"

                label_no_has_normalized = label_no_has.replace('_', '').replace('-', '').replace(' ', '')

                # Try multiple matching strategies
                is_exact = (
                    # Direct matches
                    col_name_lower == label_lower or
                    col_name_lower == label_no_has or
                    # With space-to-underscore
                    col_name_lower == label_lower.replace(' ', '_') or
                    col_name_lower == label_no_has.replace(' ', '_') or
                    # Fully normalized
                    col_name_normalized == label_normalized or
                    col_name_normalized == label_no_has_normalized or
                    # Column with underscores matches label without spaces
                    col_name_lower.replace('_', '') == label_lower.replace(' ', '') or
                    col_name_lower.replace('_', '') == label_no_has.replace(' ', '')
                )

                if is_exact:
                    confidence = self._calculate_hierarchy_confidence(
                        prop, 0.95, "exact"
                    )

                    if confidence > best_confidence:
                        best_confidence = confidence
                        best_match = prop
                        match_type_used = "exact"

                        # Add parent properties as alternatives (more general)
                        for parent_uri in hierarchy_info['parents']:
                            if parent_uri in self.ontology.properties:
                                parent_prop = self.ontology.properties[parent_uri]
                                parent_conf = self._calculate_hierarchy_confidence(
                                    parent_prop, 0.85, "parent"
                                )
                                alternatives.append((parent_prop, parent_conf))

                        # Add child properties as alternatives (more specific)
                        for child_uri in hierarchy_info['children']:
                            if child_uri in self.ontology.properties:
                                child_prop = self.ontology.properties[child_uri]
                                child_conf = self._calculate_hierarchy_confidence(
                                    child_prop, 0.80, "child"
                                )
                                alternatives.append((child_prop, child_conf))

                # Fuzzy match on property name
                elif label_lower in col_name_lower or col_name_lower in label_lower:
                    confidence = self._calculate_hierarchy_confidence(
                        prop, 0.75, "exact"
                    )

                    if confidence > best_confidence:
                        best_confidence = confidence
                        best_match = prop
                        match_type_used = "fuzzy"

            # Check if column matches parent property label
            # (Column might be specific, property is general)
            for parent_uri in hierarchy_info['parents']:
                if parent_uri not in self.ontology.properties:
                    continue

                parent_prop = self.ontology.properties[parent_uri]
                parent_labels = parent_prop.get_all_labels()

                for parent_label in parent_labels:
                    if not parent_label:
                        continue

                    parent_label_lower = parent_label.lower()
                    if col_name_lower == parent_label_lower or \
                       col_name_lower in parent_label_lower:
                        # Column matches parent - suggest the child (more specific)
                        confidence = self._calculate_hierarchy_confidence(
                            prop, 0.80, "child"
                        )

                        if confidence > best_confidence:
                            best_confidence = confidence
                            best_match = prop
                            match_type_used = "parent_match"

            # Check if column matches child property label
            # (Column might be general, property is specific)
            for child_uri in hierarchy_info['children']:
                if child_uri not in self.ontology.properties:
                    continue

                child_prop = self.ontology.properties[child_uri]
                child_labels = child_prop.get_all_labels()

                for child_label in child_labels:
                    if not child_label:
                        continue

                    child_label_lower = child_label.lower()
                    if col_name_lower == child_label_lower or \
                       child_label_lower in col_name_lower:
                        # Column matches child - consider the parent (more general)
                        confidence = self._calculate_hierarchy_confidence(
                            child_prop, 0.85, "exact"
                        )

                        if confidence > best_confidence:
                            best_confidence = confidence
                            best_match = child_prop
                            match_type_used = "child_match"

        # Return best match if above threshold
        if best_match and best_confidence >= self.threshold:
            hierarchy_info = self._get_hierarchy_info(best_match)

            # Build matched_via string with hierarchy context
            matched_via = f"hierarchy-aware {match_type_used}"
            if hierarchy_info['depth'] > 0:
                matched_via += f" (depth: {hierarchy_info['depth']}, specificity: {hierarchy_info['specificity']:.2f})"

            # Store alternatives in context for later use if needed
            result = MatchResult(
                property=best_match,
                match_type=MatchType.GRAPH_REASONING,
                confidence=best_confidence,
                matched_via=matched_via,
                matcher_name=self.name()
            )

            # Alternatives can be accessed separately via get_alternatives method
            return result

        return None

    def get_property_hierarchy_info(self, prop: OntologyProperty) -> Dict:
        """Get detailed hierarchy information for a property.

        Useful for debugging and visualization.

        Returns:
            Dictionary with hierarchy information
        """
        hierarchy_info = self._get_hierarchy_info(prop)

        # Get property objects for URIs
        parents = [self.ontology.properties.get(uri) for uri in hierarchy_info['parents']]
        children = [self.ontology.properties.get(uri) for uri in hierarchy_info['children']]

        return {
            'property': prop,
            'parents': [p for p in parents if p],
            'children': [c for c in children if c],
            'depth': hierarchy_info['depth'],
            'specificity': hierarchy_info['specificity'],
            'ancestor_count': len(hierarchy_info['ancestors']),
            'descendant_count': len(hierarchy_info['descendants']),
            'is_root': len(hierarchy_info['parents']) == 0,
            'is_leaf': len(hierarchy_info['children']) == 0
        }

