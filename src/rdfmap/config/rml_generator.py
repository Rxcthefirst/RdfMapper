"""RML Generator - Converts internal format to RML/R2RML standard."""

from pathlib import Path
from typing import Dict, Any, Optional
from rdflib import Graph, Namespace, RDF, RDFS, Literal, URIRef, BNode
import re

# R2RML namespace
RR = Namespace("http://www.w3.org/ns/r2rml#")
# RML namespaces
RML = Namespace("http://semweb.mmlab.be/ns/rml#")
QL = Namespace("http://semweb.mmlab.be/ns/ql#")


class RMLGenerator:
    """Generate RML/R2RML mappings from internal format."""

    def __init__(self):
        self.graph = Graph()
        self.base_uri = "http://example.org/mapping#"
        self._bind_namespaces()

    def _bind_namespaces(self):
        """Bind standard namespaces to graph."""
        self.graph.bind('rr', RR)
        self.graph.bind('rml', RML)
        self.graph.bind('ql', QL)
        self.graph.bind('rdf', RDF)
        self.graph.bind('rdfs', RDFS)

    def generate(self, internal_config: Dict[str, Any]) -> str:
        """
        Generate RML from internal mapping configuration.

        Args:
            internal_config: Internal mapping configuration dict

        Returns:
            RML as Turtle string
        """
        # Bind namespaces from config
        if 'namespaces' in internal_config:
            for prefix, uri in internal_config['namespaces'].items():
                if prefix not in ['rr', 'rml', 'ql', 'rdf', 'rdfs']:
                    self.graph.bind(prefix, Namespace(uri))

        # Get base IRI
        if 'defaults' in internal_config and 'base_iri' in internal_config['defaults']:
            self.base_uri = internal_config['defaults']['base_iri']
            # Don't add # if it already ends with / (which is typical for base IRIs)
            if not self.base_uri.endswith('#') and not self.base_uri.endswith('/'):
                self.base_uri += '/'  # Changed from '#' to '/'

        # Convert each sheet to a TriplesMap
        for sheet in internal_config.get('sheets', []):
            self._generate_triples_map(sheet)

        # Serialize to Turtle
        return self.graph.serialize(format='turtle')

    def _generate_triples_map(self, sheet: Dict[str, Any]):
        """Generate a TriplesMap from a sheet."""
        sheet_name = sheet.get('name', 'data')
        tm_uri = URIRef(f"{self.base_uri}{sheet_name}Mapping")

        # TriplesMap declaration
        self.graph.add((tm_uri, RDF.type, RR.TriplesMap))

        # Logical Source
        self._add_logical_source(tm_uri, sheet)

        # Subject Map
        self._add_subject_map(tm_uri, sheet)

        # Predicate-Object Maps
        self._add_predicate_object_maps(tm_uri, sheet)

    def _add_logical_source(self, tm_uri: URIRef, sheet: Dict[str, Any]):
        """Add logical source to TriplesMap."""
        ls_node = BNode()
        self.graph.add((tm_uri, RML.logicalSource, ls_node))

        # Source file
        source = sheet.get('source', 'data.csv')
        self.graph.add((ls_node, RML.source, Literal(source)))

        # Reference formulation (format)
        format_type = sheet.get('format', 'csv').lower()
        ref_formulation = {
            'csv': QL.CSV,
            'json': QL.JSONPath,
            'xml': QL.XPath,
        }.get(format_type, QL.CSV)

        self.graph.add((ls_node, RML.referenceFormulation, ref_formulation))

        # Iterator (for JSON/XML)
        if 'iterator' in sheet:
            self.graph.add((ls_node, RML.iterator, Literal(sheet['iterator'])))

    def _add_subject_map(self, tm_uri: URIRef, sheet: Dict[str, Any]):
        """Add subject map to TriplesMap."""
        sm_node = BNode()
        self.graph.add((tm_uri, RR.subjectMap, sm_node))

        # Template
        template = sheet.get('subject_template', sheet.get('row_resource', {}).get('iri_template', ''))
        if template:
            # IMPORTANT: Substitute base_iri FIRST, before any bracket conversion
            # Template might have $(base_iri) OR {base_iri} depending on source
            template = template.replace('$(base_iri)', self.base_uri)
            template = template.replace('{base_iri}', self.base_uri)

            # NOW convert remaining $(column) to {column} for RML
            template = re.sub(r'\$\((\w+)\)', r'{\1}', template)

            self.graph.add((sm_node, RR.template, Literal(template)))

        # Class
        rdf_class = sheet.get('class', sheet.get('row_resource', {}).get('class', ''))
        if rdf_class:
            class_uri = self._expand_uri(rdf_class, sheet)
            self.graph.add((sm_node, RR['class'], class_uri))

    def _add_predicate_object_maps(self, tm_uri: URIRef, sheet: Dict[str, Any]):
        """Add predicate-object maps to TriplesMap."""
        # Handle columns from different formats
        columns = sheet.get('columns', [])

        # If columns is a dict (old format), convert to list
        if isinstance(columns, dict):
            columns = [
                {'column': col_name, **col_config}
                for col_name, col_config in columns.items()
            ]

        for column in columns:
            self._add_predicate_object_map(tm_uri, column, sheet)

        # Handle linked objects (object properties)
        objects = sheet.get('objects', {})
        for obj_name, obj_config in objects.items():
            self._add_object_property_map(tm_uri, obj_config, sheet)

    def _add_predicate_object_map(self, tm_uri: URIRef, column: Dict[str, Any], sheet: Dict[str, Any]):
        """Add a single predicate-object map."""
        pom_node = BNode()
        self.graph.add((tm_uri, RR.predicateObjectMap, pom_node))

        # Predicate
        predicate = column.get('property', column.get('as', ''))
        if predicate:
            predicate_uri = self._expand_uri(predicate, sheet)
            self.graph.add((pom_node, RR.predicate, predicate_uri))

        # Object Map
        om_node = BNode()
        self.graph.add((pom_node, RR.objectMap, om_node))

        # Determine object type
        if 'constant' in column:
            # Constant value
            self.graph.add((om_node, RR.constant, Literal(column['constant'])))
        elif 'template' in column:
            # Template
            template = column['template']
            template = re.sub(r'\$\((\w+)\)', r'{\1}', template)
            self.graph.add((om_node, RR.template, Literal(template)))
        else:
            # Column reference
            col_name = column.get('column', column.get('name', ''))
            if col_name:
                self.graph.add((om_node, RML.reference, Literal(col_name)))

        # Datatype
        if 'datatype' in column:
            datatype_uri = self._expand_uri(column['datatype'], sheet)
            self.graph.add((om_node, RR.datatype, datatype_uri))

        # Language
        if 'language' in column:
            self.graph.add((om_node, RR.language, Literal(column['language'])))

        # Object property (IRI)
        if column.get('object_property', False):
            self.graph.add((om_node, RR.termType, RR.IRI))

    def _add_object_property_map(self, tm_uri: URIRef, obj_config: Dict[str, Any], sheet: Dict[str, Any]):
        """Add predicate-object map for a linked object (object property).

        Creates a parent triples map for the linked object with its own
        subject and properties.
        """
        pom_node = BNode()
        self.graph.add((tm_uri, RR.predicateObjectMap, pom_node))

        # Predicate (the object property linking to the related resource)
        predicate = obj_config.get('predicate', '')
        if predicate:
            predicate_uri = self._expand_uri(predicate, sheet)
            self.graph.add((pom_node, RR.predicate, predicate_uri))

        # Create UNIQUE parent triples map for THIS linked object
        obj_name = obj_config.get('name')

        # If no name, derive from class
        if not obj_name or obj_name == 'object':
            obj_class = obj_config.get('class', obj_config.get('class_type', ''))
            if ':' in obj_class:
                # Extract local name from prefixed class (e.g., "ex:Borrower" → "borrower")
                obj_name = obj_class.split(':')[1].lower()
            else:
                obj_name = 'object'

        parent_tm_uri = URIRef(f"{self.base_uri}{obj_name}Mapping")

        # Object Map with parentTriplesMap reference
        om_node = BNode()
        self.graph.add((pom_node, RR.objectMap, om_node))
        self.graph.add((om_node, RR.parentTriplesMap, parent_tm_uri))

        # Only create the parent TriplesMap if it doesn't exist yet
        if (parent_tm_uri, RDF.type, RR.TriplesMap) not in self.graph:
            # Define the parent triples map
            self.graph.add((parent_tm_uri, RDF.type, RR.TriplesMap))

            # Use same logical source as parent (only ONE)
            ls_node = BNode()
            self.graph.add((parent_tm_uri, RML.logicalSource, ls_node))

            source = sheet.get('source', 'data.csv')
            self.graph.add((ls_node, RML.source, Literal(source)))

            format_type = sheet.get('format', 'csv').lower()
            ref_formulation = {
                'csv': QL.CSV,
                'json': QL.JSONPath,
                'xml': QL.XPath,
            }.get(format_type, QL.CSV)
            self.graph.add((ls_node, RML.referenceFormulation, ref_formulation))

            # Subject map for the linked object (only ONE)
            parent_sm_node = BNode()
            self.graph.add((parent_tm_uri, RR.subjectMap, parent_sm_node))

            # IRI template for linked object
            iri_template = obj_config.get('iri_template', '')
            if iri_template:
                # Substitute base_iri with actual value (handle both formats)
                iri_template = iri_template.replace('$(base_iri)', self.base_uri)
                iri_template = iri_template.replace('{base_iri}', self.base_uri)
                # Convert $(column) to {column}
                iri_template = re.sub(r'\$\((\w+)\)', r'{\1}', iri_template)
                self.graph.add((parent_sm_node, RR.template, Literal(iri_template)))

            # Class for linked object
            obj_class = obj_config.get('class', obj_config.get('class_type', ''))
            if obj_class:
                class_uri = self._expand_uri(obj_class, sheet)
                self.graph.add((parent_sm_node, RR['class'], class_uri))

            # Properties of the linked object
            properties = obj_config.get('properties', [])
            for prop in properties:
                self._add_linked_object_property(parent_tm_uri, prop, sheet)

    def _add_linked_object_property(self, parent_tm_uri: URIRef, prop: Dict[str, Any], sheet: Dict[str, Any]):
        """Add a property to a linked object's parent triples map."""
        pom_node = BNode()
        self.graph.add((parent_tm_uri, RR.predicateObjectMap, pom_node))

        # Predicate
        predicate = prop.get('as', prop.get('as_property', ''))
        if predicate:
            predicate_uri = self._expand_uri(predicate, sheet)
            self.graph.add((pom_node, RR.predicate, predicate_uri))

        # Object Map
        om_node = BNode()
        self.graph.add((pom_node, RR.objectMap, om_node))

        # Column reference
        col_name = prop.get('column', '')
        if col_name:
            self.graph.add((om_node, RML.reference, Literal(col_name)))

        # Datatype
        if 'datatype' in prop:
            datatype_uri = self._expand_uri(prop['datatype'], sheet)
            self.graph.add((om_node, RR.datatype, datatype_uri))

    def _expand_uri(self, compact_uri: str, sheet: Dict[str, Any]) -> URIRef:
        """Expand compact URI (prefix:localName) to full URI."""
        if ':' in compact_uri and not compact_uri.startswith('http'):
            # It's a prefixed URI
            prefix, local_name = compact_uri.split(':', 1)

            # Try to find namespace in graph
            for ns_prefix, ns_uri in self.graph.namespaces():
                if str(ns_prefix) == prefix:
                    return URIRef(str(ns_uri) + local_name)

        # If it's already a full URI or can't be expanded, return as-is
        return URIRef(compact_uri)


def generate_rml(internal_config: Dict[str, Any]) -> str:
    """
    Convenience function to generate RML from internal config.

    Args:
        internal_config: Internal mapping configuration dict

    Returns:
        RML as Turtle string
    """
    generator = RMLGenerator()
    return generator.generate(internal_config)


def internal_to_rml(internal_config: Dict[str, Any],
                   alignment_report: Optional[Dict] = None) -> tuple[str, Optional[str]]:
    """
    Convert internal mapping format to RML and separate alignment report.

    This mirrors the YARRRML generator pattern but keeps x-alignment separate.

    Args:
        internal_config: Internal mapping configuration dict
        alignment_report: Optional alignment report with AI metadata

    Returns:
        Tuple of (RML string, alignment_report_json_string or None)
    """
    # Generate clean RML (no x-alignment embedded)
    rml_content = generate_rml(internal_config)

    # Generate separate alignment report if provided
    alignment_json = None
    if alignment_report:
        import json
        # Keep alignment report as separate JSON
        alignment_json = json.dumps(alignment_report, indent=2)

    return rml_content, alignment_json

