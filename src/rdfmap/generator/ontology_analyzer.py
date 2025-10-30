"""Ontology analyzer for extracting classes and properties."""

from typing import Dict, List, Set, Tuple, Optional
from rdflib import Graph, Namespace, RDF, RDFS, OWL
from rdflib.term import URIRef


class OntologyClass:
    """Represents a class from the ontology."""
    
    def __init__(self, uri: URIRef, label: Optional[str] = None, comment: Optional[str] = None):
        self.uri = uri
        self.label = label
        self.comment = comment
        self.properties: List['OntologyProperty'] = []
    
    def __repr__(self):
        return f"OntologyClass({self.uri}, label={self.label})"


class OntologyProperty:
    """Represents a property from the ontology."""
    
    def __init__(
        self,
        uri: URIRef,
        label: Optional[str] = None,
        comment: Optional[str] = None,
        domain: Optional[URIRef] = None,
        range_type: Optional[URIRef] = None,
        is_object_property: bool = False,
    ):
        self.uri = uri
        self.label = label
        self.comment = comment
        self.domain = domain
        self.range_type = range_type
        self.is_object_property = is_object_property
    
    def __repr__(self):
        return f"OntologyProperty({self.uri}, domain={self.domain}, range={self.range_type})"


class OntologyAnalyzer:
    """Analyzes an ontology to extract classes and properties for mapping generation."""
    
    def __init__(self, ontology_file: str):
        """
        Initialize the analyzer with an ontology file.
        
        Args:
            ontology_file: Path to ontology file (any RDFLib-supported format)
        """
        self.graph = Graph()
        self.graph.parse(ontology_file)
        
        self.classes: Dict[URIRef, OntologyClass] = {}
        self.properties: Dict[URIRef, OntologyProperty] = {}
        
        self._analyze()
    
    def _analyze(self):
        """Analyze the ontology to extract classes and properties."""
        self._extract_classes()
        self._extract_properties()
        self._link_properties_to_classes()
    
    def _extract_classes(self):
        """Extract all OWL/RDFS classes from the ontology."""
        for cls_uri in self.graph.subjects(RDF.type, OWL.Class):
            label = self._get_label(cls_uri)
            comment = self._get_comment(cls_uri)
            self.classes[cls_uri] = OntologyClass(cls_uri, label, comment)
        
        # Also check for RDFS classes
        for cls_uri in self.graph.subjects(RDF.type, RDFS.Class):
            if cls_uri not in self.classes:
                label = self._get_label(cls_uri)
                comment = self._get_comment(cls_uri)
                self.classes[cls_uri] = OntologyClass(cls_uri, label, comment)
    
    def _extract_properties(self):
        """Extract all properties (data and object) from the ontology."""
        # Object properties
        for prop_uri in self.graph.subjects(RDF.type, OWL.ObjectProperty):
            self._extract_property(prop_uri, is_object_property=True)
        
        # Data properties
        for prop_uri in self.graph.subjects(RDF.type, OWL.DatatypeProperty):
            self._extract_property(prop_uri, is_object_property=False)
        
        # RDF properties
        for prop_uri in self.graph.subjects(RDF.type, RDF.Property):
            if prop_uri not in self.properties:
                self._extract_property(prop_uri, is_object_property=False)
    
    def _extract_property(self, prop_uri: URIRef, is_object_property: bool):
        """Extract property details."""
        label = self._get_label(prop_uri)
        comment = self._get_comment(prop_uri)
        
        # Get domain
        domain = None
        for d in self.graph.objects(prop_uri, RDFS.domain):
            domain = d
            break  # Take first domain
        
        # Get range
        range_type = None
        for r in self.graph.objects(prop_uri, RDFS.range):
            range_type = r
            break  # Take first range
        
        self.properties[prop_uri] = OntologyProperty(
            prop_uri,
            label,
            comment,
            domain,
            range_type,
            is_object_property,
        )
    
    def _link_properties_to_classes(self):
        """Link properties to their domain classes."""
        for prop in self.properties.values():
            if prop.domain and prop.domain in self.classes:
                self.classes[prop.domain].properties.append(prop)
    
    def _get_label(self, uri: URIRef) -> Optional[str]:
        """Get rdfs:label for a URI."""
        for label in self.graph.objects(uri, RDFS.label):
            return str(label)
        return None
    
    def _get_comment(self, uri: URIRef) -> Optional[str]:
        """Get rdfs:comment for a URI."""
        for comment in self.graph.objects(uri, RDFS.comment):
            return str(comment)
        return None
    
    def get_class_by_uri(self, uri: URIRef) -> Optional[OntologyClass]:
        """Get a class by its URI."""
        return self.classes.get(uri)
    
    def get_class_by_label(self, label: str) -> Optional[OntologyClass]:
        """Get a class by its label (case-insensitive)."""
        label_lower = label.lower()
        for cls in self.classes.values():
            if cls.label and cls.label.lower() == label_lower:
                return cls
        return None
    
    def get_properties_for_class(self, class_uri: URIRef) -> List[OntologyProperty]:
        """Get all properties with the given class as domain."""
        cls = self.classes.get(class_uri)
        return cls.properties if cls else []
    
    def get_datatype_properties(self, class_uri: Optional[URIRef] = None) -> List[OntologyProperty]:
        """Get all datatype properties, optionally filtered by class domain."""
        props = [p for p in self.properties.values() if not p.is_object_property]
        if class_uri:
            props = [p for p in props if p.domain == class_uri]
        return props
    
    def get_object_properties(self, class_uri: Optional[URIRef] = None) -> List[OntologyProperty]:
        """Get all object properties, optionally filtered by class domain."""
        props = [p for p in self.properties.values() if p.is_object_property]
        if class_uri:
            props = [p for p in props if p.domain == class_uri]
        return props
    
    def suggest_class_for_name(self, name: str) -> List[OntologyClass]:
        """
        Suggest classes based on a name (e.g., from a sheet name or column pattern).
        
        Returns classes whose labels or URIs contain the given name (case-insensitive).
        """
        name_lower = name.lower()
        suggestions = []
        
        for cls in self.classes.values():
            # Check label
            if cls.label and name_lower in cls.label.lower():
                suggestions.append(cls)
                continue
            
            # Check URI local name
            local_name = str(cls.uri).split("#")[-1].split("/")[-1]
            if name_lower in local_name.lower():
                suggestions.append(cls)
        
        return suggestions
    
    def get_namespaces(self) -> Dict[str, str]:
        """Extract namespace prefixes and URIs from the ontology."""
        namespaces = {}
        for prefix, namespace in self.graph.namespaces():
            if prefix:  # Skip default namespace
                namespaces[prefix] = str(namespace)
        return namespaces
