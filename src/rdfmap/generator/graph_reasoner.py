"""Graph reasoning engine for deep ontology structure analysis.

This module provides sophisticated reasoning capabilities that leverage the full
semantic structure of the ontology, including class hierarchies, property chains,
domain/range relationships, and transitive reasoning.
"""

from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass
from rdflib import Graph, URIRef, RDFS, OWL, RDF
from collections import defaultdict, deque

from .ontology_analyzer import OntologyClass, OntologyProperty


@dataclass
class SemanticPath:
    """Represents a semantic path through the ontology graph."""
    start: URIRef
    end: URIRef
    hops: int
    path_type: str  # "subclass", "property_chain", "domain_range"
    intermediate_nodes: List[URIRef]
    confidence: float

    def __repr__(self):
        return f"SemanticPath({self.start} -> {self.end}, {self.hops} hops, {self.path_type})"


@dataclass
class PropertyContext:
    """Rich context about a property's position in the ontology."""
    property: OntologyProperty
    parent_properties: List[OntologyProperty]  # via rdfs:subPropertyOf
    sibling_properties: List[OntologyProperty]  # share same domain
    domain_ancestors: List[URIRef]  # ancestor classes of domain
    range_info: Optional[URIRef]  # validated range
    related_via_object_props: List[Tuple[OntologyProperty, URIRef]]  # (object_prop, target_class)


class GraphReasoner:
    """Deep ontology reasoning engine.

    This reasoner goes beyond simple label matching to understand the semantic
    structure of the ontology. It can:
    - Navigate class hierarchies (rdfs:subClassOf)
    - Follow property chains (domain -> range relationships)
    - Discover inherited properties from parent classes
    - Validate type compatibility through domain/range
    - Find semantic shortcuts and alternative paths
    """

    def __init__(
        self,
        graph: Graph,
        classes: Dict[URIRef, OntologyClass],
        properties: Dict[URIRef, OntologyProperty]
    ):
        """Initialize the reasoner.

        Args:
            graph: RDFLib graph of the ontology
            classes: Dictionary of ontology classes
            properties: Dictionary of ontology properties
        """
        self.graph = graph
        self.classes = classes
        self.properties = properties

        # Build indexes for efficient reasoning
        self._subclass_index: Dict[URIRef, Set[URIRef]] = defaultdict(set)
        self._superclass_index: Dict[URIRef, Set[URIRef]] = defaultdict(set)
        self._subproperty_index: Dict[URIRef, Set[URIRef]] = defaultdict(set)
        self._superproperty_index: Dict[URIRef, Set[URIRef]] = defaultdict(set)
        self._domain_index: Dict[URIRef, List[URIRef]] = defaultdict(list)
        self._range_index: Dict[URIRef, List[URIRef]] = defaultdict(list)

        self._build_indexes()

    def _build_indexes(self):
        """Build reasoning indexes from the ontology graph."""
        # Index subClassOf relationships
        for subclass, _, superclass in self.graph.triples((None, RDFS.subClassOf, None)):
            if isinstance(subclass, URIRef) and isinstance(superclass, URIRef):
                self._subclass_index[superclass].add(subclass)
                self._superclass_index[subclass].add(superclass)

        # Index subPropertyOf relationships
        for subprop, _, superprop in self.graph.triples((None, RDFS.subPropertyOf, None)):
            if isinstance(subprop, URIRef) and isinstance(superprop, URIRef):
                self._subproperty_index[superprop].add(subprop)
                self._superproperty_index[subprop].add(superprop)

        # Index domain and range
        for prop_uri, prop in self.properties.items():
            if prop.domain:
                self._domain_index[prop.domain].append(prop_uri)
            if prop.range_type:
                self._range_index[prop.range_type].append(prop_uri)

    def get_all_ancestors(self, class_uri: URIRef, max_depth: int = 10) -> List[URIRef]:
        """Get all ancestor classes (transitive superclasses).

        Args:
            class_uri: The class to find ancestors for
            max_depth: Maximum depth to traverse (prevent infinite loops)

        Returns:
            List of ancestor class URIs, ordered by distance (nearest first)
        """
        ancestors = []
        visited = set()
        queue = deque([(class_uri, 0)])

        while queue:
            current, depth = queue.popleft()

            if depth >= max_depth or current in visited:
                continue

            visited.add(current)

            # Get direct superclasses
            for superclass in self._superclass_index.get(current, set()):
                if superclass not in visited:
                    ancestors.append(superclass)
                    queue.append((superclass, depth + 1))

        return ancestors

    def get_all_descendants(self, class_uri: URIRef, max_depth: int = 10) -> List[URIRef]:
        """Get all descendant classes (transitive subclasses).

        Args:
            class_uri: The class to find descendants for
            max_depth: Maximum depth to traverse

        Returns:
            List of descendant class URIs
        """
        descendants = []
        visited = set()
        queue = deque([(class_uri, 0)])

        while queue:
            current, depth = queue.popleft()

            if depth >= max_depth or current in visited:
                continue

            visited.add(current)

            # Get direct subclasses
            for subclass in self._subclass_index.get(current, set()):
                if subclass not in visited:
                    descendants.append(subclass)
                    queue.append((subclass, depth + 1))

        return descendants

    def get_inherited_properties(self, class_uri: URIRef) -> List[OntologyProperty]:
        """Get all properties available to a class, including inherited ones.

        This includes:
        - Properties with this class as domain
        - Properties inherited from ancestor classes

        Args:
            class_uri: The class to get properties for

        Returns:
            List of available properties
        """
        properties = []
        seen_uris = set()

        # Get properties for this class
        for prop_uri in self._domain_index.get(class_uri, []):
            if prop_uri not in seen_uris:
                properties.append(self.properties[prop_uri])
                seen_uris.add(prop_uri)

        # Get properties from ancestor classes
        for ancestor in self.get_all_ancestors(class_uri):
            for prop_uri in self._domain_index.get(ancestor, []):
                if prop_uri not in seen_uris:
                    properties.append(self.properties[prop_uri])
                    seen_uris.add(prop_uri)

        return properties

    def find_property_by_domain_and_range(
        self,
        domain: URIRef,
        range_type: URIRef,
        allow_subclasses: bool = True
    ) -> List[OntologyProperty]:
        """Find properties connecting a domain to a range.

        Args:
            domain: Domain class URI
            range_type: Range class/type URI
            allow_subclasses: If True, also consider subclasses of domain/range

        Returns:
            List of matching properties
        """
        matches = []

        # Collect candidate domains
        candidate_domains = {domain}
        if allow_subclasses:
            candidate_domains.update(self.get_all_ancestors(domain))
            candidate_domains.update(self.get_all_descendants(domain))

        # Collect candidate ranges
        candidate_ranges = {range_type}
        if allow_subclasses:
            candidate_ranges.update(self.get_all_ancestors(range_type))
            candidate_ranges.update(self.get_all_descendants(range_type))

        # Find matching properties
        for prop in self.properties.values():
            if prop.domain in candidate_domains and prop.range_type in candidate_ranges:
                matches.append(prop)

        return matches

    def get_property_context(self, prop_uri: URIRef) -> PropertyContext:
        """Get rich contextual information about a property.

        Args:
            prop_uri: Property URI

        Returns:
            PropertyContext with detailed information
        """
        prop = self.properties.get(prop_uri)
        if not prop:
            raise ValueError(f"Property not found: {prop_uri}")

        # Find parent properties (via subPropertyOf)
        parent_properties = []
        for parent_uri in self._superproperty_index.get(prop_uri, set()):
            if parent_uri in self.properties:
                parent_properties.append(self.properties[parent_uri])

        # Find sibling properties (share same domain)
        sibling_properties = []
        if prop.domain:
            for sibling_uri in self._domain_index.get(prop.domain, []):
                if sibling_uri != prop_uri and sibling_uri in self.properties:
                    sibling_properties.append(self.properties[sibling_uri])

        # Find domain ancestors
        domain_ancestors = []
        if prop.domain:
            domain_ancestors = self.get_all_ancestors(prop.domain)

        # Find related properties through object properties
        related_via_object_props = []
        if prop.domain:
            for obj_prop in self.properties.values():
                if obj_prop.is_object_property and obj_prop.domain == prop.domain:
                    if obj_prop.range_type:
                        related_via_object_props.append((obj_prop, obj_prop.range_type))

        return PropertyContext(
            property=prop,
            parent_properties=parent_properties,
            sibling_properties=sibling_properties,
            domain_ancestors=domain_ancestors,
            range_info=prop.range_type,
            related_via_object_props=related_via_object_props
        )

    def find_semantic_path(
        self,
        start_class: URIRef,
        target_property: URIRef,
        max_hops: int = 3
    ) -> Optional[SemanticPath]:
        """Find a semantic path from a class to a property.

        This can help discover indirect relationships, like finding that a
        "Loan" can access "borrower name" through "Loan -> Borrower -> name".

        Args:
            start_class: Starting class URI
            target_property: Target property URI
            max_hops: Maximum number of hops to explore

        Returns:
            SemanticPath if found, None otherwise
        """
        target_prop = self.properties.get(target_property)
        if not target_prop or not target_prop.domain:
            return None

        target_domain = target_prop.domain

        # BFS to find shortest path
        queue = deque([(start_class, [], 0)])
        visited = set()

        while queue:
            current_class, path, hops = queue.popleft()

            if hops > max_hops or current_class in visited:
                continue

            visited.add(current_class)

            # Check if we've reached the target
            if current_class == target_domain:
                confidence = 1.0 / (hops + 1)  # Shorter paths = higher confidence
                return SemanticPath(
                    start=start_class,
                    end=target_domain,
                    hops=hops,
                    path_type="class_navigation",
                    intermediate_nodes=path,
                    confidence=confidence
                )

            # Explore superclasses
            for superclass in self._superclass_index.get(current_class, set()):
                if superclass not in visited:
                    queue.append((superclass, path + [current_class], hops + 1))

            # Explore via object properties
            for obj_prop in self.properties.values():
                if obj_prop.is_object_property and obj_prop.domain == current_class:
                    if obj_prop.range_type and obj_prop.range_type not in visited:
                        queue.append((obj_prop.range_type, path + [current_class], hops + 1))

        return None

    def get_related_properties(
        self,
        prop_uri: URIRef,
        relationship_types: Optional[List[str]] = None
    ) -> Dict[str, List[OntologyProperty]]:
        """Get properties related to the given property.

        Args:
            prop_uri: Property to find relations for
            relationship_types: Types of relationships to consider
                               (default: ["sibling", "parent", "child", "range_related"])

        Returns:
            Dictionary mapping relationship type to list of properties
        """
        if relationship_types is None:
            relationship_types = ["sibling", "parent", "child", "range_related"]

        prop = self.properties.get(prop_uri)
        if not prop:
            return {}

        related = defaultdict(list)

        # Sibling properties (same domain)
        if "sibling" in relationship_types and prop.domain:
            for sibling_uri in self._domain_index.get(prop.domain, []):
                if sibling_uri != prop_uri and sibling_uri in self.properties:
                    related["sibling"].append(self.properties[sibling_uri])

        # Parent properties (via subPropertyOf)
        if "parent" in relationship_types:
            for parent_uri in self._superproperty_index.get(prop_uri, set()):
                if parent_uri in self.properties:
                    related["parent"].append(self.properties[parent_uri])

        # Child properties (inverse of subPropertyOf)
        if "child" in relationship_types:
            for child_uri in self._subproperty_index.get(prop_uri, set()):
                if child_uri in self.properties:
                    related["child"].append(self.properties[child_uri])

        # Range-related (properties with same range)
        if "range_related" in relationship_types and prop.range_type:
            for range_prop_uri in self._range_index.get(prop.range_type, []):
                if range_prop_uri != prop_uri and range_prop_uri in self.properties:
                    related["range_related"].append(self.properties[range_prop_uri])

        return dict(related)

    def validate_property_for_data_type(
        self,
        prop: OntologyProperty,
        inferred_data_type: str
    ) -> Tuple[bool, float]:
        """Validate if a property's range is compatible with inferred data type.

        Args:
            prop: The property to validate
            inferred_data_type: Inferred type like "xsd:integer", "xsd:string", etc.

        Returns:
            Tuple of (is_valid, confidence)
        """
        if not prop.range_type:
            # No range specified - moderately confident it could work
            return (True, 0.5)

        range_str = str(prop.range_type).lower()
        data_type_lower = inferred_data_type.lower()

        # Direct match
        if data_type_lower in range_str:
            return (True, 1.0)

        # Compatible types
        compatible_types = {
            "integer": ["int", "long", "short", "byte", "decimal", "number"],
            "decimal": ["float", "double", "number"],
            "string": ["string", "literal", "text"],
            "date": ["date", "datetime", "timestamp"],
            "boolean": ["bool", "boolean"]
        }

        for base_type, compatible in compatible_types.items():
            if base_type in data_type_lower:
                if any(compat in range_str for compat in compatible):
                    return (True, 0.8)

        # If range is a class (object property), it's not compatible with datatype
        if prop.range_type in self.classes:
            return (False, 0.0)

        # Unknown compatibility - low confidence
        return (True, 0.3)

    def explain_property_choice(
        self,
        prop: OntologyProperty,
        context_class: Optional[URIRef] = None
    ) -> str:
        """Generate human-readable explanation for why a property is relevant.

        Args:
            prop: Property to explain
            context_class: Optional context class for relation explanation

        Returns:
            Explanation string
        """
        parts = []

        # Basic info
        parts.append(f"Property: {prop.label or prop.uri}")

        # Domain info
        if prop.domain:
            domain_class = self.classes.get(prop.domain)
            domain_label = domain_class.label if domain_class else str(prop.domain)
            parts.append(f"Domain: {domain_label}")

            # Check if context class is related
            if context_class and context_class != prop.domain:
                if context_class in self.get_all_ancestors(prop.domain):
                    parts.append("(inherited from parent class)")
                elif context_class in self.get_all_descendants(prop.domain):
                    parts.append("(available to child class)")

        # Range info
        if prop.range_type:
            range_class = self.classes.get(prop.range_type)
            if range_class:
                parts.append(f"Range: {range_class.label} (object property)")
            else:
                parts.append(f"Range: {prop.range_type} (datatype)")

        # Property type
        if prop.is_object_property:
            parts.append("Type: ObjectProperty (relates to other entities)")
        else:
            parts.append("Type: DatatypeProperty (has literal values)")

        return " | ".join(parts)

