"""RDF graph construction and emission."""

from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
from rdflib import Graph, Literal, Namespace, RDF, URIRef
from rdflib.namespace import XSD

from ..iri.generator import IRITemplate, curie_to_iri
from ..models.errors import ErrorSeverity, ProcessingReport
from ..models.mapping import ColumnMapping, LinkedObject, MappingConfig, SheetMapping
from ..transforms.functions import apply_transform
from ..validator.datatypes import validate_datatype


class RDFGraphBuilder:
    """Build RDF graphs from tabular data using mapping configuration."""

    def __init__(self, config: MappingConfig, report: ProcessingReport):
        """Initialize graph builder.
        
        Args:
            config: Mapping configuration
            report: Processing report for error tracking
        """
        self.config = config
        self.report = report
        self.graph = Graph()
        
        # Track generated IRIs to detect duplicates
        self.iri_registry: Dict[str, List[int]] = {}  # iri -> [row_numbers]
        
        # Bind namespaces
        for prefix, namespace in config.namespaces.items():
            self.graph.bind(prefix, Namespace(namespace))

    def _resolve_property(self, property_ref: str) -> URIRef:
        """Resolve property reference (CURIE or IRI) to URIRef.
        
        Args:
            property_ref: Property as CURIE or full IRI
            
        Returns:
            URIRef for the property
        """
        if ":" in property_ref and not property_ref.startswith("http"):
            # Looks like a CURIE
            iri = curie_to_iri(property_ref, self.config.namespaces)
            return URIRef(iri)
        else:
            # Full IRI
            return URIRef(property_ref)

    def _resolve_class(self, class_ref: str) -> URIRef:
        """Resolve class reference (CURIE or IRI) to URIRef.
        
        Args:
            class_ref: Class as CURIE or full IRI
            
        Returns:
            URIRef for the class
        """
        return self._resolve_property(class_ref)  # Same logic

    def _create_literal(
        self,
        value: Any,
        datatype: Optional[str] = None,
        language: Optional[str] = None,
        row_num: Optional[int] = None,
        column_name: Optional[str] = None,
    ) -> Optional[Literal]:
        """Create RDF literal with appropriate datatype or language tag.
        
        Args:
            value: Literal value
            datatype: XSD datatype (as CURIE or IRI)
            language: Language tag
            row_num: Row number for error reporting
            column_name: Column name for error reporting
            
        Returns:
            RDF Literal or None if validation fails
        """
        if pd.isna(value) or value == "":
            # Handle empty values
            if datatype:
                # Return typed empty literal
                dt_uri = self._resolve_property(datatype)
                return Literal("", datatype=dt_uri)
            return Literal("")
        
        # Validate datatype before creating literal
        if datatype:
            is_valid, error_msg = validate_datatype(value, datatype)
            if not is_valid:
                context = f" in column '{column_name}'" if column_name else ""
                self.report.add_error(
                    f"Datatype validation failed{context}: {error_msg}",
                    row=row_num,
                    severity=ErrorSeverity.ERROR,
                )
                return None
        
        # Convert value to string
        str_value = str(value)
        
        if language:
            # Language-tagged literal (no datatype)
            return Literal(str_value, lang=language)
        elif datatype:
            # Typed literal
            dt_uri = self._resolve_property(datatype)
            return Literal(str_value, datatype=dt_uri)
        else:
            # Plain literal
            return Literal(str_value)

    def _apply_column_transform(
        self,
        value: Any,
        column_name: str,
        column_mapping: ColumnMapping,
        row_num: int,
    ) -> Optional[Any]:
        """Apply transformation to column value.
        
        Args:
            value: Raw value
            column_name: Column name
            column_mapping: Column mapping configuration
            row_num: Row number for error reporting
            
        Returns:
            Transformed value or None if transformation failed
        """
        # Handle empty values
        if pd.isna(value) or value == "":
            if column_mapping.default is not None:
                return column_mapping.default
            elif column_mapping.required:
                self.report.add_error(
                    f"Required column '{column_name}' is empty",
                    row=row_num,
                    column=column_name,
                    severity=ErrorSeverity.ERROR,
                )
                return None
            elif self.config.options.skip_empty_values:
                return None
            else:
                return value
        
        # Apply transform if specified
        if column_mapping.transform:
            try:
                value = apply_transform(value, column_mapping.transform)
            except ValueError as e:
                self.report.add_error(
                    f"Transform '{column_mapping.transform}' failed: {e}",
                    row=row_num,
                    column=column_name,
                    severity=ErrorSeverity.ERROR,
                    value=value,
                )
                return None
        
        return value

    def _build_resource_iri(
        self, template: IRITemplate, row: pd.Series, row_num: int
    ) -> Optional[URIRef]:
        """Build resource IRI from template and row data.
        
        Args:
            template: IRI template
            row: Data row
            row_num: Row number for error reporting
            
        Returns:
            URIRef or None if IRI construction failed
        """
        try:
            # Build context from row data
            context = row.to_dict()
            iri_str = template.render(context)
            iri_ref = URIRef(iri_str)
            
            # Track IRI for duplicate detection
            if iri_str in self.iri_registry:
                self.iri_registry[iri_str].append(row_num)
                # Warn about duplicate
                self.report.add_error(
                    f"Duplicate IRI detected: {iri_str} (also used in row(s) {self.iri_registry[iri_str][:-1]})",
                    row=row_num,
                    severity=ErrorSeverity.WARNING,
                )
            else:
                self.iri_registry[iri_str] = [row_num]
            
            return iri_ref
        except (ValueError, KeyError) as e:
            self.report.add_error(
                f"Failed to construct IRI: {e}",
                row=row_num,
                severity=ErrorSeverity.ERROR,
            )
            return None

    def _add_row_resource(
        self,
        sheet: SheetMapping,
        row: pd.Series,
        row_num: int,
    ) -> Optional[URIRef]:
        """Add main resource for a row.
        
        Args:
            sheet: Sheet mapping configuration
            row: Data row
            row_num: Row number for error reporting
            
        Returns:
            Resource URIRef or None if creation failed
        """
        # Build resource IRI
        iri_template = IRITemplate(
            sheet.row_resource.iri_template,
            self.config.defaults.base_iri,
        )
        resource = self._build_resource_iri(iri_template, row, row_num)
        
        if not resource:
            return None
        
        # Add rdf:type
        class_uri = self._resolve_class(sheet.row_resource.class_type)
        self.graph.add((resource, RDF.type, class_uri))
        
        # Add column properties
        for column_name, column_mapping in sheet.columns.items():
            if column_name not in row.index:
                if column_mapping.required:
                    self.report.add_error(
                        f"Required column '{column_name}' not found in data",
                        row=row_num,
                        column=column_name,
                        severity=ErrorSeverity.ERROR,
                    )
                continue
            
            value = row[column_name]
            
            # Apply transformations
            transformed_value = self._apply_column_transform(
                value, column_name, column_mapping, row_num
            )
            
            if transformed_value is None:
                continue
            
            # Create property and literal
            prop = self._resolve_property(column_mapping.as_property)
            
            # Determine language tag
            language = column_mapping.language or self.config.defaults.language
            
            # Handle multi-valued columns
            if column_mapping.multi_valued:
                delimiter = column_mapping.delimiter or ","
                values = str(transformed_value).split(delimiter)
                
                for val in values:
                    val = val.strip()
                    if val:
                        literal = self._create_literal(
                            val,
                            datatype=column_mapping.datatype,
                            language=language,
                            row_num=row_num,
                            column_name=column_name,
                        )
                        if literal is not None:
                            self.graph.add((resource, prop, literal))
            else:
                literal = self._create_literal(
                    transformed_value,
                    datatype=column_mapping.datatype,
                    language=language,
                    row_num=row_num,
                    column_name=column_name,
                )
                if literal is not None:
                    self.graph.add((resource, prop, literal))
        
        return resource

    def _add_linked_objects(
        self,
        main_resource: URIRef,
        sheet: SheetMapping,
        row: pd.Series,
        row_num: int,
    ) -> None:
        """Add linked object resources.
        
        Args:
            main_resource: Main resource URI
            sheet: Sheet mapping configuration
            row: Data row
            row_num: Row number for error reporting
        """
        for obj_name, obj_config in sheet.objects.items():
            # Build linked object IRI
            iri_template = IRITemplate(
                obj_config.iri_template,
                self.config.defaults.base_iri,
            )
            obj_resource = self._build_resource_iri(iri_template, row, row_num)
            
            if not obj_resource:
                continue
            
            # Link main resource to object
            predicate = self._resolve_property(obj_config.predicate)
            self.graph.add((main_resource, predicate, obj_resource))
            
            # Add object type
            obj_class = self._resolve_class(obj_config.class_type)
            self.graph.add((obj_resource, RDF.type, obj_class))
            
            # Add object properties
            for prop_mapping in obj_config.properties:
                if prop_mapping.column not in row.index:
                    if prop_mapping.required:
                        self.report.add_error(
                            f"Required column '{prop_mapping.column}' not found for linked object '{obj_name}'",
                            row=row_num,
                            column=prop_mapping.column,
                            severity=ErrorSeverity.ERROR,
                        )
                    continue
                
                value = row[prop_mapping.column]
                
                # Apply transformations (reuse ColumnMapping logic)
                col_mapping = ColumnMapping(
                    **{"as": prop_mapping.as_property, **prop_mapping.model_dump(exclude={"as_property"})}
                )
                transformed_value = self._apply_column_transform(
                    value, prop_mapping.column, col_mapping, row_num
                )
                
                if transformed_value is None:
                    continue
                
                # Create property and literal
                prop = self._resolve_property(prop_mapping.as_property)
                language = prop_mapping.language or self.config.defaults.language
                
                literal = self._create_literal(
                    transformed_value,
                    datatype=prop_mapping.datatype,
                    language=language,
                    row_num=row_num,
                    column_name=prop_mapping.column,
                )
                if literal is not None:
                    self.graph.add((obj_resource, prop, literal))

    def add_dataframe(
        self,
        df: pd.DataFrame,
        sheet: SheetMapping,
        offset: int = 0,
    ) -> None:
        """Add DataFrame to RDF graph.
        
        Args:
            df: DataFrame to process
            sheet: Sheet mapping configuration
            offset: Row offset for error reporting
        """
        for idx, row in df.iterrows():
            row_num = offset + idx + 1  # 1-indexed for users
            
            # Add main resource
            main_resource = self._add_row_resource(sheet, row, row_num)
            
            if main_resource:
                # Add linked objects
                self._add_linked_objects(main_resource, sheet, row, row_num)
                
                self.report.total_rows += 1

    def get_graph(self) -> Graph:
        """Get the constructed RDF graph.
        
        Returns:
            RDF Graph
        """
        return self.graph


def serialize_graph(graph: Graph, format: str, output_path: Optional[Path] = None) -> str:
    """Serialize RDF graph to string or file.
    
    Args:
        graph: RDF graph to serialize
        format: Output format (turtle, json-ld, nt)
        output_path: Optional path to write output
        
    Returns:
        Serialized graph as string
        
    Raises:
        ValueError: If format is not supported
    """
    format_map = {
        "turtle": "turtle",
        "ttl": "turtle",
        "jsonld": "json-ld",
        "json-ld": "json-ld",
        "nt": "nt",
        "ntriples": "nt",
        "xml": "xml",
        "rdf": "xml",
        "rdfxml": "xml",
        "rdf-xml": "xml",
    }
    
    rdf_format = format_map.get(format.lower())
    if not rdf_format:
        raise ValueError(f"Unsupported format: {format}")
    
    # Serialize
    serialized = graph.serialize(format=rdf_format)
    
    # Write to file if path provided
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(serialized, encoding="utf-8")
    
    return serialized
