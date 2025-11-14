"""N-Triples streaming writer for high-performance RDF output without aggregation."""

from pathlib import Path
from typing import Any, Dict, Optional, TextIO, Union
from rdflib import Graph, Literal, URIRef
from rdflib.namespace import RDF, OWL


class NTriplesStreamWriter:
    """High-performance N-Triples writer that streams triples directly to file without in-memory aggregation."""

    def __init__(self, output_path: Path, encoding: str = 'utf-8'):
        """Initialize the N-Triples stream writer.

        Args:
            output_path: Path to output NT file
            encoding: File encoding (default: utf-8)
        """
        self.output_path = output_path
        self.encoding = encoding
        self.file_handle: Optional[TextIO] = None
        self.triple_count = 0

    def __enter__(self):
        """Enter context manager."""
        self.file_handle = open(self.output_path, 'w', encoding=self.encoding, buffering=8192)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager."""
        if self.file_handle:
            self.file_handle.close()
            self.file_handle = None

    def write_triple(self, subject: URIRef, predicate: URIRef, obj: Union[URIRef, Literal]) -> None:
        """Write a single triple to the NT file.

        Args:
            subject: Subject URI
            predicate: Predicate URI
            obj: Object (URI or Literal)
        """
        if not self.file_handle:
            raise RuntimeError("Writer not opened (use context manager)")

        # Format N-Triples line
        if isinstance(obj, Literal):
            if obj.language:
                obj_str = f'"{self._escape_string(str(obj))}"@{obj.language}'
            elif obj.datatype:
                obj_str = f'"{self._escape_string(str(obj))}"^^<{obj.datatype}>'
            else:
                obj_str = f'"{self._escape_string(str(obj))}"'
        else:
            obj_str = f'<{obj}>'

        line = f'<{subject}> <{predicate}> {obj_str} .\n'
        self.file_handle.write(line)
        self.triple_count += 1

    def write_resource_triples(self, resource_iri: URIRef, triples: Dict[URIRef, Any]) -> None:
        """Write all triples for a resource.

        Args:
            resource_iri: Subject IRI
            triples: Dictionary of predicate -> object mappings
        """
        for predicate, obj in triples.items():
            if isinstance(obj, list):
                # Multi-valued property
                for value in obj:
                    self.write_triple(resource_iri, predicate, value)
            else:
                # Single value
                self.write_triple(resource_iri, predicate, obj)

    def _escape_string(self, value: str) -> str:
        """Escape string for N-Triples format.

        Args:
            value: String to escape

        Returns:
            Escaped string
        """
        # N-Triples string escaping
        value = value.replace('\\', '\\\\')  # Backslash
        value = value.replace('"', '\\"')    # Quote
        value = value.replace('\n', '\\n')   # Newline
        value = value.replace('\r', '\\r')   # Carriage return
        value = value.replace('\t', '\\t')   # Tab
        return value

    def get_triple_count(self) -> int:
        """Get number of triples written.

        Returns:
            Number of triples written
        """
        return self.triple_count


class StreamingRDFGraphBuilder:
    """RDF graph builder optimized for streaming N-Triples output without aggregation."""

    def __init__(self, config, report, enable_aggregation: bool = True):
        """Initialize streaming graph builder.

        Args:
            config: Mapping configuration
            report: Processing report
            enable_aggregation: Whether to aggregate duplicate IRIs (False for NT streaming)
        """
        self.config = config
        self.report = report
        self.enable_aggregation = enable_aggregation

        if enable_aggregation:
            # Use regular Graph for aggregation
            self.graph = Graph()
            self.nt_writer = None
        else:
            # Use streaming NT writer
            self.graph = None
            self.nt_writer = None

        # Bind namespaces for aggregated mode
        if self.graph:
            for prefix, namespace in config.namespaces.items():
                self.graph.bind(prefix, namespace)

    def set_nt_writer(self, nt_writer: NTriplesStreamWriter) -> None:
        """Set the NT writer for streaming mode.

        Args:
            nt_writer: NT writer instance
        """
        if not self.enable_aggregation:
            self.nt_writer = nt_writer

    def add_triple(self, subject: URIRef, predicate: URIRef, obj: Union[URIRef, Literal]) -> None:
        """Add a triple to the output.

        Args:
            subject: Subject URI
            predicate: Predicate URI
            obj: Object (URI or Literal)
        """
        if self.enable_aggregation and self.graph:
            # Add to in-memory graph (aggregates automatically)
            self.graph.add((subject, predicate, obj))
        elif not self.enable_aggregation and self.nt_writer:
            # Stream directly to NT file
            self.nt_writer.write_triple(subject, predicate, obj)
        else:
            raise RuntimeError("Builder not properly configured for streaming or aggregation")

    def add_resource_with_class(self, resource_iri: URIRef, class_uri: URIRef) -> None:
        """Add a resource with its RDF type.

        Args:
            resource_iri: Resource IRI
            class_uri: Class IRI
        """
        self.add_triple(resource_iri, RDF.type, class_uri)
        self.add_triple(resource_iri, RDF.type, OWL.NamedIndividual)

    def get_graph(self) -> Optional[Graph]:
        """Get the RDF graph (only for aggregated mode).

        Returns:
            RDF Graph or None if in streaming mode
        """
        return self.graph

    def get_triple_count(self) -> int:
        """Get the number of triples processed.

        Returns:
            Number of triples
        """
        if self.enable_aggregation and self.graph:
            return len(self.graph)
        elif not self.enable_aggregation and self.nt_writer:
            return self.nt_writer.get_triple_count()
        else:
            return 0


def create_streaming_builder(config, report, output_format: str, output_path: Optional[Path] = None):
    """Create appropriate builder based on output format and configuration.

    Args:
        config: Mapping configuration
        report: Processing report
        output_format: Output format (nt, ttl, xml, etc.)
        output_path: Output file path (required for NT streaming)

    Returns:
        Tuple of (builder, nt_writer_context_manager)
    """
    # Determine if we should use aggregation
    enable_aggregation = config.options.aggregate_duplicates

    # For NT format with aggregation disabled, use streaming
    if output_format.lower() in ['nt', 'ntriples'] and not enable_aggregation:
        if not output_path:
            raise ValueError("Output path required for NT streaming mode")

        # Import the regular graph builder for comparison
        from .graph_builder import RDFGraphBuilder

        # Create streaming builder
        builder = StreamingRDFGraphBuilder(config, report, enable_aggregation=False)
        nt_writer = NTriplesStreamWriter(output_path)

        return builder, nt_writer
    else:
        # Use regular aggregating builder
        from .graph_builder import RDFGraphBuilder
        builder = RDFGraphBuilder(config, report)
        return builder, None
