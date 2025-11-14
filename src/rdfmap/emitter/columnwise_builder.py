"""Enhanced RDF graph builder that supports true column-wise streaming processing."""

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


class ColumnWiseRDFBuilder:
    """RDF graph builder that processes data column-wise for true streaming performance."""

    def __init__(self, config: MappingConfig, report: ProcessingReport, streaming_writer=None):
        """Initialize column-wise graph builder.

        Args:
            config: Mapping configuration
            report: Processing report
            streaming_writer: Optional NT streaming writer
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

    def _add_triple(self, subject: URIRef, predicate: URIRef, obj) -> None:
        """Add a triple to the output (streaming or aggregated)."""
        if self.streaming_writer:
            # Stream directly to NT file
            self.streaming_writer.write_triple(subject, predicate, obj)
        elif self.graph is not None:
            # Add to in-memory graph
            self.graph.add((subject, predicate, obj))
        else:
            raise RuntimeError("Builder not properly configured")

    def _resolve_property(self, property_ref: str) -> URIRef:
        """Resolve property reference (CURIE or IRI) to URIRef."""
        if ":" in property_ref and not property_ref.startswith("http"):
            # Looks like a CURIE
            iri = curie_to_iri(property_ref, self.config.namespaces)
            return URIRef(iri)
        else:
            # Full IRI
            return URIRef(property_ref)

    def _resolve_class(self, class_ref: str) -> URIRef:
        """Resolve class reference (CURIE or IRI) to URIRef."""
        return self._resolve_property(class_ref)  # Same logic

    def add_dataframe_columnwise(self, df: pl.DataFrame, sheet: SheetMapping, offset: int = 0) -> None:
        """Add DataFrame using column-wise processing for streaming mode."""
        if len(df) == 0:
            return

        print(f"🌊 Column-wise processing: {len(df)} rows")

        # Step 1: Generate all subject IRIs first (this is one column operation)
        print("  📍 Step 1: Generating subject IRIs...")
        subject_iris = self._generate_subject_iris_vectorized(df, sheet, offset)

        # Step 2: Add rdf:type triples for all subjects (column-wise)
        print("  🏷️  Step 2: Adding type triples...")
        self._add_type_triples_vectorized(subject_iris, sheet)

        # Step 3: Process each property column independently
        print("  📊 Step 3: Processing property columns...")
        for column_name, column_mapping in sheet.columns.items():
            if column_name in df.columns:
                print(f"    Processing column: {column_name}")
                self._add_property_column_vectorized(
                    df, subject_iris, column_name, column_mapping, offset
                )

        self.report.total_rows += len(df)

    def _generate_subject_iris_vectorized(self, df: pl.DataFrame, sheet: SheetMapping, offset: int) -> List[URIRef]:
        """Generate all subject IRIs using vectorized operations."""
        # Convert IRI template to work with Polars
        template = sheet.row_resource.iri_template
        base_iri = self.config.defaults.base_iri

        # Simple template substitution (could be enhanced)
        if '{base_iri}' in template and '{EmployeeID}' in template:
            # Example: {base_iri}employee/{EmployeeID}
            template_without_base = template.replace('{base_iri}', base_iri)

            if 'EmployeeID' in df.columns:
                # Use Polars string operations for vectorized IRI generation
                iri_series = df.select(
                    pl.lit(template_without_base.replace('{EmployeeID}', '')) +
                    pl.col('EmployeeID').cast(pl.Utf8)
                ).to_series()

                return [URIRef(iri) for iri in iri_series.to_list()]

        # Fallback to row-wise processing for complex templates
        subject_iris = []
        for idx, row in enumerate(df.to_dicts()):
            iri_template = IRITemplate(template)
            try:
                context = {**row, 'base_iri': base_iri}
                iri_str = iri_template.render(context)
                subject_iris.append(URIRef(iri_str))
            except Exception as e:
                self.report.add_error(f"IRI generation failed: {e}", row=offset + idx + 1)
                subject_iris.append(None)

        return [iri for iri in subject_iris if iri is not None]

    def _add_type_triples_vectorized(self, subject_iris: List[URIRef], sheet: SheetMapping) -> None:
        """Add rdf:type triples for all subjects at once."""
        class_uri = self._resolve_class(sheet.row_resource.class_type)

        for subject_iri in subject_iris:
            self._add_triple(subject_iri, RDF.type, class_uri)
            self._add_triple(subject_iri, RDF.type, OWL.NamedIndividual)

    def _add_property_column_vectorized(
        self,
        df: pl.DataFrame,
        subject_iris: List[URIRef],
        column_name: str,
        column_mapping,
        offset: int
    ) -> None:
        """Process an entire property column at once."""
        property_uri = self._resolve_property(column_mapping.as_property)

        # Get the column values
        column_values = df[column_name].to_list()

        # Process all values in this column
        for idx, (subject_iri, value) in enumerate(zip(subject_iris, column_values)):
            if subject_iri is None or value is None:
                continue

            # Apply transforms if specified
            if hasattr(column_mapping, 'transform') and column_mapping.transform:
                try:
                    # For column-wise processing, we'd ideally use Polars expressions
                    # For now, apply transform row-wise
                    row_data = df.row(idx, named=True)
                    value = apply_transform(value, column_mapping.transform, row_data)
                except Exception as e:
                    self.report.add_error(
                        f"Transform failed for {column_name}: {e}",
                        row=offset + idx + 1,
                        severity=ErrorSeverity.WARNING
                    )
                    continue

            # Create literal
            literal = self._create_literal(
                value,
                datatype=getattr(column_mapping, 'datatype', None),
                language=getattr(column_mapping, 'language', None) or self.config.defaults.language,
                row_num=offset + idx + 1,
                column_name=column_name
            )

            if literal is not None:
                self._add_triple(subject_iri, property_uri, literal)

    def _create_literal(
        self,
        value: Any,
        datatype: Optional[str] = None,
        language: Optional[str] = None,
        row_num: Optional[int] = None,
        column_name: Optional[str] = None,
    ) -> Optional[Literal]:
        """Create RDF literal with appropriate datatype or language tag."""
        # Handle Polars null values and regular Python values
        if value is None:
            return None

        # Convert Polars types to Python types
        if hasattr(value, 'item'):
            value = value.item()

        # Validate datatype before creating literal
        if datatype:
            is_valid, error_msg = validate_datatype(value, datatype)
            if not is_valid:
                self.report.add_error(
                    f"Invalid datatype for column '{column_name}': {error_msg}",
                    row=row_num,
                    severity=ErrorSeverity.WARNING,
                )
                return None

            # Convert value to appropriate Python type for RDF
            if datatype == "xsd:integer":
                try:
                    value = int(float(str(value)))  # Handle string numbers
                except (ValueError, TypeError):
                    return None
            elif datatype == "xsd:decimal" or datatype == "xsd:double":
                try:
                    value = float(str(value))
                except (ValueError, TypeError):
                    return None
            elif datatype == "xsd:boolean":
                if isinstance(value, bool):
                    value = value
                elif str(value).lower() in ('true', '1', 'yes', 'on'):
                    value = True
                elif str(value).lower() in ('false', '0', 'no', 'off'):
                    value = False
                else:
                    return None

        # Create the literal
        try:
            if language:
                return Literal(value, lang=language)
            elif datatype:
                dt_uri = self._resolve_property(datatype)
                return Literal(value, datatype=dt_uri)
            else:
                return Literal(value)
        except Exception as e:
            self.report.add_error(
                f"Literal creation failed for column '{column_name}': {e}",
                row=row_num,
                severity=ErrorSeverity.WARNING,
            )
            return None

    def get_graph(self) -> Optional[Graph]:
        """Get the RDF graph (only for aggregated mode)."""
        return self.graph

    def get_triple_count(self) -> int:
        """Get the number of triples processed."""
        if self.streaming_writer:
            return self.streaming_writer.get_triple_count()
        elif self.graph:
            return len(self.graph)
        else:
            return 0
