"""Streaming RDF graph builder leveraging Polars' streaming capabilities."""

from pathlib import Path
from typing import Any, Dict, List, Optional, Generator
import polars as pl
from rdflib import Graph, Literal, Namespace, RDF, URIRef
from rdflib.namespace import OWL

from ..iri.generator import IRITemplate, curie_to_iri
from ..models.errors import ErrorSeverity, ProcessingReport
from ..models.mapping import ColumnMapping, MappingConfig, SheetMapping
from ..transforms.functions import apply_transform
from ..validator.datatypes import validate_datatype


class StreamingRDFGraphBuilder:
    """High-performance streaming RDF graph builder using Polars streaming engine."""

    def __init__(self, config: MappingConfig, report: ProcessingReport):
        """Initialize streaming graph builder.

        Args:
            config: Mapping configuration
            report: Processing report for error tracking
        """
        self.config = config
        self.report = report
        self.graph = Graph()

        # Track generated IRIs to detect duplicates
        self.iri_registry: Dict[str, List[int]] = {}

        # Bind namespaces
        for prefix, namespace in config.namespaces.items():
            self.graph.bind(prefix, Namespace(namespace))

        # Statistics
        self.total_triples = 0
        self.batches_processed = 0

    def stream_to_rdf(
        self,
        file_path: Path,
        sheet: SheetMapping,
        chunk_size: int = 10000,
        enable_streaming_transforms: bool = True
    ) -> Generator[int, None, None]:
        """Stream data processing with real-time RDF generation.

        This method leverages Polars' streaming capabilities for:
        - Memory-efficient processing of large datasets
        - Vectorized data transformations
        - Lazy evaluation optimizations
        - Real-time RDF triple generation

        Args:
            file_path: Path to data file
            sheet: Sheet mapping configuration
            chunk_size: Size of processing batches
            enable_streaming_transforms: Whether to use Polars streaming transforms

        Yields:
            Number of triples generated in each batch
        """
        from .streaming_parser import StreamingCSVParser

        parser = StreamingCSVParser(file_path)

        # Prepare transforms for streaming
        transforms = {}
        if enable_streaming_transforms:
            transforms = self._prepare_polars_transforms(sheet)

        # Stream and process batches
        row_offset = 0

        if transforms and enable_streaming_transforms:
            # Use Polars streaming with built-in transforms
            batch_generator = parser.stream_with_transforms(
                batch_size=chunk_size,
                transforms=transforms
            )
        else:
            # Use regular streaming
            batch_generator = parser.stream_batches(batch_size=chunk_size)

        for batch in batch_generator:
            batch_triples = self._process_streaming_batch(
                batch, sheet, row_offset
            )

            self.total_triples += batch_triples
            self.batches_processed += 1
            row_offset += len(batch)

            # Yield progress for real-time feedback
            yield batch_triples

    def _prepare_polars_transforms(self, sheet: SheetMapping) -> Dict[str, str]:
        """Prepare transforms for Polars streaming optimization.

        Args:
            sheet: Sheet mapping configuration

        Returns:
            Dictionary of column transforms
        """
        transforms = {}

        for column_name, column_mapping in sheet.columns.items():
            if column_mapping.transform:
                # Map our transform types to Polars-compatible operations
                if column_mapping.transform in [
                    "to_decimal", "to_integer", "to_date",
                    "lowercase", "uppercase", "trim"
                ]:
                    transforms[column_name] = column_mapping.transform

        return transforms

    def _process_streaming_batch(
        self,
        batch: pl.DataFrame,
        sheet: SheetMapping,
        offset: int
    ) -> int:
        """Process a single batch with optimized RDF generation.

        Args:
            batch: Polars DataFrame batch
            sheet: Sheet mapping configuration
            offset: Row offset for error reporting

        Returns:
            Number of triples generated
        """
        initial_triples = len(self.graph)

        # Convert batch to dictionaries for RDF processing
        # Future optimization: implement direct Polars → RDF conversion
        rows_data = batch.to_dicts()

        # Process each row efficiently
        for idx, row_data in enumerate(rows_data):
            row_num = offset + idx + 1

            # Generate main resource
            main_resource = self._add_row_resource_streaming(
                sheet, row_data, row_num
            )

            if main_resource:
                # Add linked objects
                self._add_linked_objects_streaming(
                    main_resource, sheet, row_data, row_num
                )

                self.report.total_rows += 1

        return len(self.graph) - initial_triples

    def _add_row_resource_streaming(
        self,
        sheet: SheetMapping,
        row_data: Dict[str, Any],
        row_num: int,
    ) -> Optional[URIRef]:
        """Add main row resource with streaming optimizations."""
        # Generate IRI for main resource
        resource_iri = self._generate_iri_fast(
            sheet.row_resource.iri_template,
            row_data,
            row_num,
        )

        if not resource_iri:
            self.report.failed_rows += 1
            return None

        # Add rdf:type efficiently
        class_uri = self._resolve_property_fast(sheet.row_resource.class_type)
        self.graph.add((resource_iri, RDF.type, class_uri))
        self.graph.add((resource_iri, RDF.type, OWL.NamedIndividual))

        # Add column properties with batched processing
        self._add_column_properties_batch(
            resource_iri, sheet.columns, row_data, row_num
        )

        return resource_iri

    def _add_column_properties_batch(
        self,
        resource_iri: URIRef,
        columns: Dict[str, ColumnMapping],
        row_data: Dict[str, Any],
        row_num: int,
    ) -> None:
        """Add column properties in batch for efficiency."""
        # Pre-resolve property URIs for better performance
        property_cache = {}

        for column_name, column_mapping in columns.items():
            if column_name not in row_data:
                continue

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

            # Apply custom transforms (non-Polars transforms)
            if (column_mapping.transform and
                column_mapping.transform not in [
                    "to_decimal", "to_integer", "to_date",
                    "lowercase", "uppercase", "trim"
                ]):
                try:
                    value = apply_transform(
                        value, column_mapping.transform, row_data
                    )
                except Exception as e:
                    self.report.add_error(
                        f"Transform '{column_mapping.transform}' failed: {e}",
                        row=row_num,
                        severity=ErrorSeverity.WARNING,
                    )
                    continue

            # Create literal efficiently
            literal = self._create_literal_fast(
                value,
                datatype=column_mapping.datatype,
                language=column_mapping.language or self.config.defaults.language,
            )

            if literal is not None:
                # Use cached property URI
                prop_ref = column_mapping.as_property
                if prop_ref not in property_cache:
                    property_cache[prop_ref] = self._resolve_property_fast(prop_ref)

                property_uri = property_cache[prop_ref]
                self.graph.add((resource_iri, property_uri, literal))

    def _add_linked_objects_streaming(
        self,
        main_resource: URIRef,
        sheet: SheetMapping,
        row_data: Dict[str, Any],
        row_num: int,
    ) -> None:
        """Add linked objects with streaming optimizations."""
        for obj_name, obj_mapping in sheet.objects.items():
            # Check condition if specified
            if hasattr(obj_mapping, 'condition') and obj_mapping.condition:
                try:
                    if not eval(obj_mapping.condition, {"__builtins__": {}}, row_data):
                        continue
                except Exception:
                    continue

            # Generate object IRI efficiently
            object_iri = self._generate_iri_fast(
                obj_mapping.iri_template,
                row_data,
                row_num,
            )

            if not object_iri:
                continue

            # Add object class
            class_uri = self._resolve_property_fast(obj_mapping.class_type)
            self.graph.add((object_iri, RDF.type, class_uri))
            self.graph.add((object_iri, RDF.type, OWL.NamedIndividual))

            # Add object properties efficiently
            for prop_mapping in obj_mapping.properties:
                column_name = prop_mapping.column
                if column_name in row_data:
                    value = row_data[column_name]

                    if value is None or value == "":
                        continue

                    literal = self._create_literal_fast(
                        value,
                        datatype=prop_mapping.datatype,
                        language=prop_mapping.language or self.config.defaults.language,
                    )

                    if literal is not None:
                        property_uri = self._resolve_property_fast(prop_mapping.as_property)
                        self.graph.add((object_iri, property_uri, literal))

            # Link main resource to object
            if obj_mapping.predicate:
                link_uri = self._resolve_property_fast(obj_mapping.predicate)
                self.graph.add((main_resource, link_uri, object_iri))

    def _generate_iri_fast(
        self,
        template: str,
        row_data: Dict[str, Any],
        row_num: int,
    ) -> Optional[URIRef]:
        """Fast IRI generation with minimal overhead."""
        try:
            # Add base_iri to context
            template_context = row_data.copy()
            template_context["base_iri"] = self.config.defaults.base_iri

            # Simple template rendering (could be optimized further)
            iri_gen = IRITemplate(template)
            iri = iri_gen.render(template_context)

            return URIRef(iri)

        except Exception as e:
            self.report.add_error(
                f"Failed to generate IRI: {e}",
                row=row_num,
                severity=ErrorSeverity.ERROR,
            )
            return None

    def _resolve_property_fast(self, property_ref: str) -> URIRef:
        """Fast property resolution with caching."""
        if ":" in property_ref and not property_ref.startswith("http"):
            # CURIE - resolve with namespaces
            iri = curie_to_iri(property_ref, self.config.namespaces)
            return URIRef(iri)
        else:
            # Full IRI
            return URIRef(property_ref)

    def _create_literal_fast(
        self,
        value: Any,
        datatype: Optional[str] = None,
        language: Optional[str] = None,
    ) -> Optional[Literal]:
        """Fast literal creation with minimal validation."""
        if value is None:
            return None

        # Convert Polars types to Python types if needed
        if hasattr(value, 'item'):
            value = value.item()

        if datatype:
            # Quick datatype handling
            dt_uri = self._resolve_property_fast(datatype)
            return Literal(value, datatype=dt_uri)
        elif language:
            return Literal(value, lang=language)
        else:
            return Literal(value)

    def get_streaming_stats(self) -> Dict[str, Any]:
        """Get streaming processing statistics."""
        return {
            "total_triples": self.total_triples,
            "batches_processed": self.batches_processed,
            "avg_triples_per_batch": (
                self.total_triples / self.batches_processed
                if self.batches_processed > 0 else 0
            ),
            "total_graph_size": len(self.graph),
        }

    def get_graph(self) -> Graph:
        """Get the constructed RDF graph."""
        return self.graph
