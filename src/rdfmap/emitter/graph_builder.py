"""High-performance RDF graph construction using Polars DataFrames."""

from pathlib import Path
from typing import Any, Dict, List, Optional

import polars as pl
from rdflib import Graph, Literal, Namespace, RDF, URIRef
from rdflib.namespace import OWL

from ..iri.generator import IRITemplate, curie_to_iri
from ..models.errors import ErrorSeverity, ProcessingReport
from ..models.mapping import MappingConfig, SheetMapping
from ..transforms.functions import apply_transform
from ..validator.datatypes import validate_datatype


class RDFGraphBuilder:
    """Build RDF graphs from Polars DataFrames with high performance."""

    def __init__(self, config: MappingConfig, report: ProcessingReport, streaming_writer=None):
        """Initialize graph builder.

        Args:
            config: Mapping configuration
            report: Processing report for error tracking
            streaming_writer: Optional NT streaming writer for non-aggregated output
        """
        self.config = config
        self.report = report
        self.streaming_writer = streaming_writer

        # Only create in-memory graph if not streaming
        if streaming_writer is None:
            self.graph = Graph()
            # Bind namespaces
            for prefix, namespace in config.namespaces.items():
                self.graph.bind(prefix, Namespace(namespace))
        else:
            self.graph = None

        # Track generated IRIs to detect duplicates (only when aggregating)
        self.iri_registry: Dict[str, List[int]] = {}  # iri -> [row_numbers]

    def _add_triple(self, subject: URIRef, predicate: URIRef, obj) -> None:
        """Add a triple to the output (streaming or aggregated).

        Args:
            subject: Subject URI
            predicate: Predicate URI
            obj: Object (URI or Literal)
        """
        if self.streaming_writer:
            # Stream directly to NT file
            self.streaming_writer.write_triple(subject, predicate, obj)
        elif self.graph is not None:
            # Add to in-memory graph
            self.graph.add((subject, predicate, obj))
        else:
            raise RuntimeError("Builder not properly configured")

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
        # Handle Polars null values and regular Python values
        if value is None:
            # Handle empty values
            if datatype:
                # Return typed empty literal
                dt_uri = self._resolve_property(datatype)
                return Literal("", datatype=dt_uri)
            return Literal("")

        # Convert Polars types to Python types
        if hasattr(value, 'item'):
            value = value.item()

        # Validate datatype before creating literal
        if datatype:
            is_valid, error_msg = validate_datatype(value, datatype)
            if not is_valid:
                context = f" in column '{column_name}'" if column_name else ""
                self.report.add_error(
                    f"Datatype validation failed{context}: {error_msg}",
                    row=row_num,
                    severity=ErrorSeverity.WARNING,
                )
                # Return string literal as fallback
                return Literal(str(value))

            # Create typed literal
            dt_uri = self._resolve_property(datatype)
            return Literal(value, datatype=dt_uri)
        elif language:
            # Create language-tagged literal
            return Literal(value, lang=language)
        else:
            # Create untyped literal
            return Literal(value)

    def _generate_iri(
        self,
        template: str,
        row_data: Dict[str, Any],
        row_num: int,
        context: str = "resource",
    ) -> Optional[URIRef]:
        """Generate IRI from template and row data.

        Args:
            template: IRI template string
            row_data: Row data dictionary
            row_num: Row number for error reporting
            context: Context for error reporting

        Returns:
            Generated URIRef or None if generation fails
        """
        try:
            # Add base_iri to context for template rendering
            template_context = row_data.copy()
            template_context["base_iri"] = self.config.defaults.base_iri

            # Render template
            iri_gen = IRITemplate(template)
            iri = iri_gen.render(template_context)

            # Track for duplicate detection
            if iri in self.iri_registry:
                self.iri_registry[iri].append(row_num)
            else:
                self.iri_registry[iri] = [row_num]

            return URIRef(iri)

        except Exception as e:
            self.report.add_error(
                f"Failed to generate IRI for {context}: {e}",
                row=row_num,
                severity=ErrorSeverity.ERROR,
            )
            return None

    def _apply_column_transforms(
        self, df: pl.DataFrame, sheet: SheetMapping
    ) -> pl.DataFrame:
        """Apply transforms to DataFrame columns using Polars expressions.

        Args:
            df: Input DataFrame
            sheet: Sheet mapping configuration

        Returns:
            DataFrame with transforms applied
        """
        # Build list of Polars expressions for transforms
        exprs = []

        for column_name in df.columns:
            if column_name in sheet.columns:
                column_mapping = sheet.columns[column_name]
                if column_mapping.transform:
                    # Apply transform using Polars expression
                    try:
                        if column_mapping.transform == "to_decimal":
                            expr = pl.col(column_name).cast(pl.Float64)
                        elif column_mapping.transform == "to_integer":
                            expr = pl.col(column_name).cast(pl.Int64)
                        elif column_mapping.transform == "to_date":
                            expr = pl.col(column_name).str.strptime(pl.Date, "%Y-%m-%d", strict=False)
                        elif column_mapping.transform == "to_datetime":
                            expr = pl.col(column_name).str.strptime(pl.Datetime, "%Y-%m-%d %H:%M:%S", strict=False)
                        elif column_mapping.transform == "lowercase":
                            expr = pl.col(column_name).str.to_lowercase()
                        elif column_mapping.transform == "uppercase":
                            expr = pl.col(column_name).str.to_uppercase()
                        elif column_mapping.transform == "trim":
                            expr = pl.col(column_name).str.strip_chars()
                        else:
                            # Keep original column for custom transforms
                            expr = pl.col(column_name)

                        exprs.append(expr.alias(column_name))
                    except Exception as e:
                        # Keep original column on transform error
                        exprs.append(pl.col(column_name))
                        self.report.add_error(
                            f"Transform '{column_mapping.transform}' failed for column '{column_name}': {e}",
                            severity=ErrorSeverity.WARNING,
                        )
                else:
                    exprs.append(pl.col(column_name))
            else:
                exprs.append(pl.col(column_name))

        return df.select(exprs)

    def add_dataframe(
        self,
        df: pl.DataFrame,
        sheet: SheetMapping,
        offset: int = 0,
    ) -> None:
        """Add Polars DataFrame to RDF graph with vectorized processing.

        Args:
            df: Polars DataFrame to process
            sheet: Sheet mapping configuration
            offset: Row offset for error reporting
        """
        if len(df) == 0:
            return

        # Apply transforms using Polars expressions
        df = self._apply_column_transforms(df, sheet)

        # Convert to Python dictionaries for RDF processing
        # This is currently necessary for IRI template rendering
        # Future optimization: implement template rendering directly in Polars
        rows_data = df.to_dicts()

        # Process each row (vectorized processing opportunities exist here)
        for idx, row_data in enumerate(rows_data):
            row_num = offset + idx + 1  # 1-indexed for users

            # Add main resource
            main_resource = self._add_row_resource(sheet, row_data, row_num)

            if main_resource:
                # Add linked objects
                self._add_linked_objects(main_resource, sheet, row_data, row_num)

                self.report.total_rows += 1

    def _add_row_resource(
        self,
        sheet: SheetMapping,
        row_data: Dict[str, Any],
        row_num: int,
    ) -> Optional[URIRef]:
        """Add main row resource to graph.

        Args:
            sheet: Sheet mapping configuration
            row_data: Row data dictionary
            row_num: Row number for error reporting

        Returns:
            URIRef of created resource or None if creation failed
        """
        # Generate IRI for main resource
        resource_iri = self._generate_iri(
            sheet.row_resource.iri_template,
            row_data,
            row_num,
            f"row resource (sheet: {sheet.name})",
        )

        if not resource_iri:
            self.report.failed_rows += 1
            return None

        # Add rdf:type
        class_uri = self._resolve_class(sheet.row_resource.class_type)
        self._add_triple(resource_iri, RDF.type, class_uri)

        # Add owl:NamedIndividual declaration for OWL2 compliance
        self._add_triple(resource_iri, RDF.type, OWL.NamedIndividual)

        # Add column properties
        for column_name, column_mapping in sheet.columns.items():
            if column_name in row_data:
                value = row_data[column_name]

                # Skip empty required values
                if column_mapping.required and (value is None or value == ""):
                    self.report.add_error(
                        f"Required column '{column_name}' is empty",
                        row=row_num,
                        severity=ErrorSeverity.ERROR,
                    )
                    continue

                # Skip non-required empty values
                if value is None or value == "":
                    continue

                # Apply custom transform if needed (fallback for complex transforms)
                if column_mapping.transform and column_mapping.transform not in [
                    "to_decimal", "to_integer", "to_date", "to_datetime",
                    "lowercase", "uppercase", "trim"
                ]:
                    try:
                        value = apply_transform(value, column_mapping.transform, row_data)
                    except Exception as e:
                        self.report.add_error(
                            f"Transform '{column_mapping.transform}' failed for column '{column_name}': {e}",
                            row=row_num,
                            severity=ErrorSeverity.WARNING,
                        )
                        continue

                # Create literal
                literal = self._create_literal(
                    value,
                    datatype=column_mapping.datatype,
                    language=column_mapping.language or self.config.defaults.language,
                    row_num=row_num,
                    column_name=column_name,
                )

                if literal is not None:
                    property_uri = self._resolve_property(column_mapping.as_property)
                    self._add_triple(resource_iri, property_uri, literal)

        return resource_iri

    def _add_linked_objects(
        self,
        main_resource: URIRef,
        sheet: SheetMapping,
        row_data: Dict[str, Any],
        row_num: int,
    ) -> None:
        """Add linked objects to graph.

        Args:
            main_resource: Main resource URI
            sheet: Sheet mapping configuration
            row_data: Row data dictionary
            row_num: Row number for error reporting
        """
        for obj_name, obj_mapping in sheet.objects.items():
            # Check condition if specified
            if hasattr(obj_mapping, 'condition') and obj_mapping.condition:
                try:
                    # Simple condition evaluation (could be enhanced)
                    if not eval(obj_mapping.condition, {"__builtins__": {}}, row_data):
                        continue
                except Exception:
                    # Skip on condition evaluation error
                    continue

            # Generate object IRI
            object_iri = self._generate_iri(
                obj_mapping.iri_template,
                row_data,
                row_num,
                f"linked object (class: {obj_mapping.class_type})",
            )

            if not object_iri:
                continue

            # Add object class
            class_uri = self._resolve_class(obj_mapping.class_type)
            self._add_triple(object_iri, RDF.type, class_uri)
            self._add_triple(object_iri, RDF.type, OWL.NamedIndividual)

            # Add object properties
            for prop_mapping in obj_mapping.properties:
                column_name = prop_mapping.column
                if column_name in row_data:
                    value = row_data[column_name]

                    if value is None or value == "":
                        continue

                    # Apply transform if needed
                    if prop_mapping.transform:
                        try:
                            value = apply_transform(value, prop_mapping.transform, row_data)
                        except Exception as e:
                            self.report.add_error(
                                f"Transform '{prop_mapping.transform}' failed for linked object column '{column_name}': {e}",
                                row=row_num,
                                severity=ErrorSeverity.WARNING,
                            )
                            continue

                    # Create literal
                    literal = self._create_literal(
                        value,
                        datatype=prop_mapping.datatype,
                        language=prop_mapping.language or self.config.defaults.language,
                        row_num=row_num,
                        column_name=column_name,
                    )

                    if literal is not None:
                        property_uri = self._resolve_property(prop_mapping.as_property)
                        self._add_triple(object_iri, property_uri, literal)

            # Link main resource to object
            if obj_mapping.predicate:
                link_uri = self._resolve_property(obj_mapping.predicate)
                self._add_triple(main_resource, link_uri, object_iri)

    def get_graph(self) -> Optional[Graph]:
        """Get the RDF graph.

        Returns:
            RDF Graph or None if in streaming mode
        """
        return self.graph

    def get_triple_count(self) -> int:
        """Get the number of triples processed.

        Returns:
            Number of triples
        """
        if self.streaming_writer:
            return self.streaming_writer.get_triple_count()
        elif self.graph:
            return len(self.graph)
        else:
            return 0

    def get_duplicate_iris(self) -> Dict[str, List[int]]:
        """Get IRIs that were generated for multiple rows.

        Returns:
            Dictionary mapping duplicate IRIs to row numbers
        """
        return {iri: rows for iri, rows in self.iri_registry.items() if len(rows) > 1}


def serialize_graph(graph: Graph, format: str, output_path: Path) -> None:
    """Serialize RDF graph to file.

    Args:
        graph: RDF graph to serialize
        format: Output format (ttl, xml, jsonld, nt)
        output_path: Output file path
    """
    format_map = {
        "ttl": "turtle",
        "turtle": "turtle",
        "xml": "xml",
        "rdf": "xml",
        "rdfxml": "xml",
        "jsonld": "json-ld",
        "json-ld": "json-ld",
        "nt": "nt",
        "ntriples": "nt",
    }

    rdf_format = format_map.get(format.lower(), "turtle")
    graph.serialize(destination=str(output_path), format=rdf_format)

