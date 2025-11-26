"""RML Parser - Converts RML/R2RML format to internal MappingConfig model.

RML (RDF Mapping Language) is a W3C standard for mapping non-RDF data to RDF.
Specification: https://rml.io/specs/rml/

This parser converts RML (Turtle/RDF format) to our internal Pydantic models
so the existing conversion engine can process it without modification.
"""

from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from rdflib import Graph, Namespace, RDF, RDFS, Literal, URIRef, BNode

# R2RML namespace
RR = Namespace("http://www.w3.org/ns/r2rml#")

# RML namespaces
RML = Namespace("http://semweb.mmlab.be/ns/rml#")
QL = Namespace("http://semweb.mmlab.be/ns/ql#")

# Custom alignment namespace for AI metadata
XALIGN = Namespace("http://rdfmap.io/ns/alignment#")


class RMLParser:
    """Parse RML/R2RML mappings to internal format."""

    def __init__(self):
        self.graph = None
        self.config_dir = None

    def parse(self, rml_path: Path) -> Dict[str, Any]:
        """
        Parse RML file and convert to internal mapping config format.

        Args:
            rml_path: Path to RML file (Turtle, N-Triples, or RDF/XML)

        Returns:
            Dictionary in internal mapping format (compatible with MappingConfig)
        """
        rml_path = Path(rml_path)
        self.config_dir = rml_path.parent

        # Load RML file into graph
        self.graph = Graph()
        try:
            # Try to detect format from extension
            format_map = {
                '.ttl': 'turtle',
                '.n3': 'n3',
                '.nt': 'nt',
                '.rdf': 'xml',
                '.xml': 'xml',
            }
            rml_format = format_map.get(rml_path.suffix.lower(), 'turtle')
            self.graph.parse(str(rml_path), format=rml_format)
        except Exception as e:
            raise ValueError(f"Failed to parse RML file: {e}")

        return self._convert_to_internal()

    def _convert_to_internal(self) -> Dict[str, Any]:
        """Convert RML graph to internal mapping format."""
        internal = {}

        # Extract namespaces
        internal['namespaces'] = self._extract_namespaces()

        # Extract base IRI
        internal['defaults'] = {
            'base_iri': self._extract_base_iri()
        }

        # Extract triples maps and convert to sheets
        triples_maps = list(self.graph.subjects(RDF.type, RR.TriplesMap))
        sheets = []

        for tm in triples_maps:
            sheet = self._convert_triples_map(tm)
            if sheet:
                sheets.append(sheet)

        internal['sheets'] = sheets

        # Extract x-alignment metadata if present
        alignment_data = self._extract_alignment_metadata()
        if alignment_data:
            internal['_x_alignment'] = alignment_data

        return internal

    def _extract_namespaces(self) -> Dict[str, str]:
        """Extract namespace prefixes from RML graph."""
        namespaces = {}

        for prefix, namespace in self.graph.namespaces():
            if prefix:  # Skip empty prefix
                namespaces[str(prefix)] = str(namespace)

        # Ensure standard namespaces are present
        defaults = {
            'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
            'rdfs': 'http://www.w3.org/2000/01/rdf-schema#',
            'xsd': 'http://www.w3.org/2001/XMLSchema#',
        }

        for prefix, uri in defaults.items():
            if prefix not in namespaces:
                namespaces[prefix] = uri

        return namespaces

    def _extract_base_iri(self) -> str:
        """Extract base IRI from RML graph or use default."""
        # Try to find base IRI in graph
        # RML doesn't have a standard way to specify base, so we look for common patterns

        # Look for most common namespace used in subject templates
        base_iris = set()
        for tm in self.graph.subjects(RDF.type, RR.TriplesMap):
            subject_map = self.graph.value(tm, RR.subjectMap)
            if subject_map:
                template = self.graph.value(subject_map, RR.template)
                if template:
                    template_str = str(template)
                    # Extract base from template like "http://example.org/person_{id}"
                    if 'http://' in template_str or 'https://' in template_str:
                        parts = template_str.split('/')
                        if len(parts) >= 3:
                            base = '/'.join(parts[:3]) + '/'
                            base_iris.add(base)

        # Return most common base or default
        if base_iris:
            return sorted(base_iris)[0]  # Use first alphabetically for consistency

        return 'http://example.org/'

    def _convert_triples_map(self, triples_map: URIRef) -> Optional[Dict[str, Any]]:
        """Convert a single RML TriplesMap to internal sheet format."""

        # Extract logical source
        logical_source = self.graph.value(triples_map, RML.logicalSource)
        if not logical_source:
            # Try R2RML logicalTable for R2RML mappings
            logical_source = self.graph.value(triples_map, RR.logicalTable)

        if not logical_source:
            return None

        # Get source file/table
        source_info = self._extract_source_info(logical_source)
        if not source_info:
            return None

        # Extract subject map
        subject_map = self.graph.value(triples_map, RR.subjectMap)
        if not subject_map:
            return None

        subject_info = self._extract_subject_map(subject_map)

        # Extract predicate-object maps
        po_maps = list(self.graph.objects(triples_map, RR.predicateObjectMap))
        extraction_result = self._extract_predicate_object_maps_with_separation(po_maps, source_info['columns'])
        columns_dict = extraction_result['data_properties']
        objects_dict = extraction_result['object_properties']

        # Build sheet configuration in internal format
        sheet = {
            'name': source_info['name'],
            'source': source_info['source'],
            'row_resource': {
                'class': subject_info['class'],
                'iri_template': subject_info['template']
            },
            'columns': columns_dict  # Dict format, not list!
        }

        # Add objects if any were found
        if objects_dict:
            sheet['objects'] = objects_dict

        # Add optional fields
        if 'format' in source_info:
            sheet['format'] = source_info['format']

        if 'iterator' in source_info:
            sheet['iterator'] = source_info['iterator']

        return sheet

    def _extract_source_info(self, logical_source: URIRef) -> Optional[Dict[str, Any]]:
        """Extract source file and format information."""
        info = {}

        # Get source file/table
        source = self.graph.value(logical_source, RML.source)
        if not source:
            # Try R2RML tableName
            source = self.graph.value(logical_source, RR.tableName)

        if not source:
            return None

        source_str = str(source)


        info['source'] = source_str

        # Extract name from source (filename without extension)
        if '/' in source_str or '\\' in source_str:
            source_str = Path(source_str).name

        name = Path(source_str).stem
        info['name'] = name

        # Get reference formulation (format)
        ref_formulation = self.graph.value(logical_source, RML.referenceFormulation)
        if ref_formulation:
            # Map QL formats to our internal formats
            format_map = {
                str(QL.CSV): 'csv',
                str(QL.JSONPath): 'json',
                str(QL.XPath): 'xml',
            }
            info['format'] = format_map.get(str(ref_formulation), 'csv')
        else:
            # Detect from extension
            ext = Path(source_str).suffix.lower()
            format_map = {
                '.csv': 'csv',
                '.json': 'json',
                '.xml': 'xml',
                '.xlsx': 'excel',
            }
            info['format'] = format_map.get(ext, 'csv')

        # Get iterator (for JSON/XML)
        iterator = self.graph.value(logical_source, RML.iterator)
        if iterator:
            info['iterator'] = str(iterator)

        # For now, set empty columns list (will be populated from predicate-object maps)
        info['columns'] = []

        return info

    def _extract_subject_map(self, subject_map: URIRef) -> Dict[str, Any]:
        """Extract subject template and class information."""
        info = {}

        # Get template
        template = self.graph.value(subject_map, RR.template)
        if template:
            template_str = str(template)
            # KEEP {column} format - it's used by Python string formatting in graph_builder
            # Do NOT convert to $(column) - that's only for YARRRML export
            info['template'] = template_str
        else:
            # Try constant
            constant = self.graph.value(subject_map, RR.constant)
            if constant:
                info['template'] = str(constant)
            else:
                info['template'] = 'http://example.org/resource/{id}'

        # Get class
        rdf_class = self.graph.value(subject_map, RR['class'])
        if rdf_class:
            info['class'] = self._compact_uri(str(rdf_class))
        else:
            info['class'] = 'owl:Thing'

        return info

    def _extract_predicate_object_maps(
        self,
        po_maps: List[URIRef],
        columns: List[str]
    ) -> List[Dict[str, Any]]:
        """Extract column mappings from predicate-object maps (returns list for backwards compatibility)."""
        result = []

        for po_map in po_maps:
            # Get predicate
            predicate = self.graph.value(po_map, RR.predicate)
            if not predicate:
                continue

            predicate_uri = self._compact_uri(str(predicate))

            # Get object map
            object_map = self.graph.value(po_map, RR.objectMap)
            if not object_map:
                # Try shortcut predicate-object
                obj = self.graph.value(po_map, RR.object)
                if obj:
                    # Constant value
                    column_mapping = {
                        'property': predicate_uri,
                        'datatype': self._infer_datatype(obj),
                        'constant': str(obj),
                    }
                    result.append(column_mapping)
                continue

            # Extract from object map
            column_mapping = self._extract_object_map(object_map, predicate_uri)
            if column_mapping:
                result.append(column_mapping)

        return result

    def _extract_predicate_object_maps_with_separation(
        self,
        po_maps: List[URIRef],
        columns: List[str]
    ) -> Dict[str, Any]:
        """
        Extract column mappings from predicate-object maps, separating data properties and object properties.

        Returns:
            Dict with 'data_properties' and 'object_properties' keys
        """
        data_properties = {}
        object_properties = {}

        for po_map in po_maps:
            # Get predicate
            predicate = self.graph.value(po_map, RR.predicate)
            if not predicate:
                continue

            predicate_uri = self._compact_uri(str(predicate))

            # Get object map
            object_map = self.graph.value(po_map, RR.objectMap)
            if not object_map:
                # Try shortcut predicate-object
                obj = self.graph.value(po_map, RR.object)
                if obj:
                    # Constant value - use property name as key
                    column_name = f"constant_{len(data_properties)}"
                    data_properties[column_name] = {
                        'as': predicate_uri,
                        'datatype': self._infer_datatype(obj),
                        'default': str(obj),
                    }
                continue

            # Check if this is a parent triples map (object property / relationship)
            parent_triples_map = self.graph.value(object_map, RR.parentTriplesMap)
            if parent_triples_map:
                # This is an object property linking to another entity
                # Extract the target entity's information
                target_subject_map = self.graph.value(parent_triples_map, RR.subjectMap)
                if target_subject_map:
                    target_class = self.graph.value(target_subject_map, RR['class'])
                    target_template = self.graph.value(target_subject_map, RR.template)

                    if target_class and target_template:
                        # Create object property in format expected by the LinkedObject model
                        # Use predicate name as key
                        obj_key = predicate_uri.split(':')[-1] if ':' in predicate_uri else predicate_uri

                        # Get properties of the linked object from the parent triples map
                        target_po_maps = list(self.graph.objects(parent_triples_map, RR.predicateObjectMap))
                        target_properties = []
                        for target_po in target_po_maps:
                            target_pred = self.graph.value(target_po, RR.predicate)
                            target_obj_map = self.graph.value(target_po, RR.objectMap)
                            if target_pred and target_obj_map:
                                target_ref = self.graph.value(target_obj_map, RML.reference)
                                if not target_ref:
                                    target_ref = self.graph.value(target_obj_map, RR.column)
                                if target_ref:
                                    target_datatype = self.graph.value(target_obj_map, RR.datatype)
                                    prop_mapping = {
                                        'as': self._compact_uri(str(target_pred)),  # Changed from 'property' to 'as'
                                        'column': str(target_ref)
                                    }
                                    if target_datatype:
                                        prop_mapping['datatype'] = self._compact_uri(str(target_datatype))
                                    target_properties.append(prop_mapping)

                        object_properties[obj_key] = {
                            'predicate': predicate_uri,
                            'class': self._compact_uri(str(target_class)),
                            'iri_template': str(target_template),
                            'properties': target_properties
                        }
                continue

            # Extract from object map (data property)
            column_mapping = self._extract_object_map_for_dict(object_map, predicate_uri)
            if column_mapping:
                column_name = column_mapping.pop('_column_name')
                data_properties[column_name] = column_mapping

        return {
            'data_properties': data_properties,
            'object_properties': object_properties
        }

    def _extract_predicate_object_maps_as_dict(
        self,
        po_maps: List[URIRef],
        columns: List[str]
    ) -> Dict[str, Dict[str, Any]]:
        """Extract column mappings from predicate-object maps as dict (column_name -> mapping).
        DEPRECATED: Use _extract_predicate_object_maps_with_separation instead."""
        result = self._extract_predicate_object_maps_with_separation(po_maps, columns)
        # Merge both for backwards compatibility
        merged = result['data_properties'].copy()
        # Add object properties with special prefix
        for key, value in result['object_properties'].items():
            merged[f'_obj_{key}'] = value
        return merged

    def _extract_object_map(self, object_map: URIRef, predicate_uri: str) -> Optional[Dict[str, Any]]:
        """Extract column mapping from object map (returns list format for backwards compatibility)."""
        mapping = {'property': predicate_uri}

        # Get reference (column name)
        reference = self.graph.value(object_map, RML.reference)
        if not reference:
            # Try R2RML column
            reference = self.graph.value(object_map, RR.column)

        if reference:
            column_name = str(reference)
            # Handle column names with spaces (YARRRML compatibility)
            mapping['column'] = column_name
        else:
            # Try constant
            constant = self.graph.value(object_map, RR.constant)
            if constant:
                mapping['constant'] = str(constant)
            else:
                # Try template
                template = self.graph.value(object_map, RR.template)
                if template:
                    # Keep {column} format for Python string formatting
                    mapping['template'] = str(template)
                else:
                    return None

        # Get datatype
        datatype = self.graph.value(object_map, RR.datatype)
        if datatype:
            mapping['datatype'] = self._compact_uri(str(datatype))

        # Get language
        language = self.graph.value(object_map, RR.language)
        if language:
            mapping['language'] = str(language)

        # Check if it's an object property (reference to another resource)
        term_type = self.graph.value(object_map, RR.termType)
        if term_type and str(term_type) == str(RR.IRI):
            mapping['object_property'] = True

        # Extract x-alignment metadata if present
        confidence = self.graph.value(object_map, XALIGN.confidence)
        if confidence:
            mapping['_confidence'] = float(confidence)

        matcher = self.graph.value(object_map, XALIGN.matcher)
        if matcher:
            mapping['_matcher'] = str(matcher)

        return mapping

    def _extract_object_map_for_dict(self, object_map: URIRef, predicate_uri: str) -> Optional[Dict[str, Any]]:
        """Extract column mapping from object map for dict format (uses 'as' property)."""
        mapping = {'as': predicate_uri}

        # Get reference (column name)
        reference = self.graph.value(object_map, RML.reference)
        if not reference:
            # Try R2RML column
            reference = self.graph.value(object_map, RR.column)

        if reference:
            column_name = str(reference)
            # Store column name to use as dict key
            mapping['_column_name'] = column_name
        else:
            # Try constant
            constant = self.graph.value(object_map, RR.constant)
            if constant:
                # For constants, use a generated name
                mapping['_column_name'] = f"constant_{predicate_uri.split(':')[-1]}"
                mapping['default'] = str(constant)
            else:
                # Try template
                template = self.graph.value(object_map, RR.template)
                if template:
                    # Keep {column} format for Python string formatting
                    mapping['_column_name'] = f"template_{predicate_uri.split(':')[-1]}"
                    mapping['template'] = str(template)
                else:
                    return None

        # Get datatype
        datatype = self.graph.value(object_map, RR.datatype)
        if datatype:
            mapping['datatype'] = self._compact_uri(str(datatype))

        # Get language
        language = self.graph.value(object_map, RR.language)
        if language:
            mapping['language'] = str(language)

        # Check if it's an object property (reference to another resource)
        term_type = self.graph.value(object_map, RR.termType)
        if term_type and str(term_type) == str(RR.IRI):
            mapping['object_property'] = True

        # Extract x-alignment metadata if present
        confidence = self.graph.value(object_map, XALIGN.confidence)
        if confidence:
            mapping['_confidence'] = float(confidence)

        matcher = self.graph.value(object_map, XALIGN.matcher)
        if matcher:
            mapping['_matcher'] = str(matcher)

        return mapping

    def _compact_uri(self, uri: str) -> str:
        """Convert full URI to compact form using namespaces."""
        for prefix, namespace in self.graph.namespaces():
            if uri.startswith(str(namespace)):
                local_name = uri[len(str(namespace)):]
                return f"{prefix}:{local_name}"
        return uri

    def _infer_datatype(self, value) -> str:
        """Infer datatype from RDF literal."""
        if isinstance(value, Literal):
            if value.datatype:
                return self._compact_uri(str(value.datatype))
            return 'xsd:string'
        return 'xsd:string'

    def _extract_alignment_metadata(self) -> Optional[Dict[str, Any]]:
        """Extract x-alignment metadata if present in RML."""
        # Look for custom alignment annotations
        alignment = {}

        # This would be stored as RDF comments or custom properties
        # For now, return None - will be populated when we add RML export

        return None if not alignment else alignment


def parse_rml(rml_path: Path) -> Dict[str, Any]:
    """
    Convenience function to parse RML file.

    Args:
        rml_path: Path to RML file

    Returns:
        Dictionary in internal mapping format
    """
    parser = RMLParser()
    return parser.parse(rml_path)

