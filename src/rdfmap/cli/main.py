"""Main CLI application."""

from pathlib import Path
from typing import List, Optional

import typer
from rich.console import Console
from rich.table import Table

from ..config.loader import load_mapping_config
from ..emitter.graph_builder import RDFGraphBuilder, serialize_graph
from ..models.errors import ProcessingReport
from ..parsers.data_source import create_parser
from ..validator.shacl import validate_rdf, write_validation_report, validate_against_ontology
from ..validator.config import validate_namespace_prefixes, validate_required_fields
from ..generator.mapping_generator import MappingGenerator, GeneratorConfig
from ..generator.spreadsheet_analyzer import SpreadsheetAnalyzer
from ..generator.ontology_analyzer import OntologyAnalyzer

app = typer.Typer(
    name="rdfmap",
    help="Convert spreadsheet data to RDF triples aligned with ontologies",
    no_args_is_help=True,
)
console = Console()


@app.command()
def convert(
    mapping: Path = typer.Option(
        ...,
        "--mapping",
        "-m",
        help="Path to mapping configuration file (YAML/JSON)",
        exists=True,
        dir_okay=False,
    ),
    ontology: Optional[Path] = typer.Option(
        None,
        "--ontology",
        help="Path to ontology file (supports TTL, RDF/XML, JSON-LD, N-Triples, etc.)",
        exists=True,
        dir_okay=False,
    ),
    format: Optional[str] = typer.Option(
        None,
        "--format",
        "-f",
        help="Output format: ttl, xml, jsonld, nt (default: ttl)",
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output file path",
        dir_okay=False,
    ),
    validate_flag: bool = typer.Option(
        False,
        "--validate",
        help="Run SHACL validation after conversion",
    ),
    report: Optional[Path] = typer.Option(
        None,
        "--report",
        help="Path to write validation report (JSON)",
        dir_okay=False,
    ),
    limit: Optional[int] = typer.Option(
        None,
        "--limit",
        help="Process only first N rows (for testing)",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Parse and validate without writing output",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable detailed logging",
    ),
    log_file: Optional[Path] = typer.Option(
        None,
        "--log",
        help="Write log to file",
        dir_okay=False,
    ),
) -> None:
    """Convert spreadsheet data to RDF triples."""
    try:
        # Load mapping configuration
        console.print(f"[blue]Loading mapping configuration from {mapping}...[/blue]")
        config = load_mapping_config(mapping)
        
        # Validate configuration
        console.print("[blue]Validating configuration...[/blue]")
        
        # Check namespace prefixes
        prefix_errors = validate_namespace_prefixes(config)
        if prefix_errors:
            console.print("[red]✗ Configuration validation failed: undefined namespace prefixes[/red]")
            for context, prefix in prefix_errors:
                console.print(f"  • In {context}: prefix '{prefix}' is not declared in namespaces")
            raise typer.Exit(code=1)
        
        # Check required fields in IRI templates
        field_warnings = validate_required_fields(config)
        if field_warnings:
            console.print("[yellow]⚠ Configuration warnings:[/yellow]")
            for context, warning in field_warnings:
                console.print(f"  • In {context}: {warning}")
        
        if verbose:
            console.print(f"[green]Configuration loaded and validated successfully[/green]")
            console.print(f"  Sheets: {len(config.sheets)}")
            console.print(f"  Namespaces: {len(config.namespaces)}")
        
        # Initialize processing report
        processing_report = ProcessingReport()
        
        # Build RDF graph
        builder = RDFGraphBuilder(config, processing_report)
        
        # Process each sheet
        for sheet in config.sheets:
            console.print(f"[blue]Processing sheet: {sheet.name}[/blue]")
            
            # Create parser
            parser = create_parser(
                Path(sheet.source),
                delimiter=config.options.delimiter,
                has_header=config.options.header,
            )
            
            if verbose:
                columns = parser.get_column_names()
                console.print(f"  Columns: {', '.join(columns)}")
            
            # Process data in chunks
            row_offset = 0
            for chunk in parser.parse(chunk_size=config.options.chunk_size):
                # Apply limit if specified
                if limit and row_offset >= limit:
                    break
                
                if limit:
                    remaining = limit - row_offset
                    chunk = chunk.head(remaining)
                
                # Add to graph
                builder.add_dataframe(chunk, sheet, offset=row_offset)
                
                row_offset += len(chunk)
                
                if verbose:
                    console.print(f"  Processed {row_offset} rows...")
        
        # Finalize report
        processing_report.finalize()
        processing_report.successful_rows = (
            processing_report.total_rows - processing_report.failed_rows
        )
        
        # Display processing summary
        _display_processing_summary(processing_report, verbose)
        
        # Get graph
        graph = builder.get_graph()
        
        console.print(f"[green]Generated {len(graph)} RDF triples[/green]")
        
        # Validate if requested
        validation_report = None
        if validate_flag and config.validation and config.validation.shacl:
            console.print("[blue]Running SHACL validation...[/blue]")
            
            shapes_file = Path(config.validation.shacl.shapes_file)
            if not shapes_file.exists():
                console.print(f"[yellow]Warning: Shapes file not found: {shapes_file}[/yellow]")
            else:
                validation_report = validate_rdf(
                    graph,
                    shapes_file=shapes_file,
                    inference=config.validation.shacl.inference,
                )
                
                _display_validation_results(validation_report, verbose)
                
                # Write validation report if requested
                if report and validation_report:
                    write_validation_report(validation_report, report)
                    console.print(f"[green]Validation report written to {report}[/green]")
        
        # Validate against ontology if provided
        if ontology:
            console.print("[blue]Running ontology validation...[/blue]")
            
            ontology_report = validate_against_ontology(
                graph,
                ontology_file=ontology,
            )
            
            _display_validation_results(ontology_report, verbose)
            
            if not ontology_report.conforms:
                console.print("[red]✗ Ontology validation failed[/red]")
                if validate_flag:  # Only exit with error if --validate was used
                    raise typer.Exit(code=1)
            else:
                console.print("[green]✓ Ontology validation passed[/green]")
        
        # Display SHACL validation results if validation was performed
        if validate_flag and validation_report:
            _display_validation_results(validation_report, verbose)
            
            # Write validation report if requested
            if report:
                write_validation_report(validation_report, report)
                console.print(f"[green]Validation report written to {report}[/green]")
        
        # Write output
        if not dry_run and output:
            # Use provided format or default to ttl
            output_format = format or "ttl"
            
            console.print(f"[blue]Writing {output_format.upper()} to {output}...[/blue]")
            serialize_graph(graph, output_format, output)
            console.print(f"[green]Output written successfully[/green]")
        elif dry_run:
            console.print("[yellow]Dry run mode: no output written[/yellow]")
        elif not output:
            console.print("[yellow]No output file specified (use --output)[/yellow]")
        
        # Exit with error code if there were processing errors
        if processing_report.failed_rows > 0:
            if config.options.on_error == "fail-fast":
                raise typer.Exit(code=1)
            else:
                console.print(
                    f"[yellow]Warning: {processing_report.failed_rows} rows had errors[/yellow]"
                )
        
        # Exit with error code if SHACL validation failed
        if validate_flag and validation_report and not validation_report.conforms:
            console.print("[red]Validation failed[/red]")
            raise typer.Exit(code=1)
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        if verbose:
            import traceback
            console.print(traceback.format_exc())
        raise typer.Exit(code=1)


@app.command()
def validate(
    rdf_file: Path = typer.Option(
        ...,
        "--rdf",
        help="Path to RDF file to validate",
        exists=True,
        dir_okay=False,
    ),
    shapes: Path = typer.Option(
        ...,
        "--shapes",
        help="Path to SHACL shapes file",
        exists=True,
        dir_okay=False,
    ),
    report: Optional[Path] = typer.Option(
        None,
        "--report",
        help="Path to write validation report (JSON)",
        dir_okay=False,
    ),
    inference: Optional[str] = typer.Option(
        None,
        "--inference",
        help="Inference mode (rdfs, owlrl, both)",
    ),
) -> None:
    """Validate RDF file against SHACL shapes."""
    try:
        console.print(f"[blue]Loading RDF from {rdf_file}...[/blue]")
        
        from rdflib import Graph
        
        data_graph = Graph()
        data_graph.parse(rdf_file)
        
        console.print(f"[green]Loaded {len(data_graph)} triples[/green]")
        
        console.print("[blue]Running SHACL validation...[/blue]")
        
        validation_report = validate_rdf(
            data_graph,
            shapes_file=shapes,
            inference=inference,
        )
        
        _display_validation_results(validation_report, verbose=True)
        
        if report:
            write_validation_report(validation_report, report)
            console.print(f"[green]Report written to {report}[/green]")
        
        if not validation_report.conforms:
            raise typer.Exit(code=1)
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(code=1)


@app.command()
def info(
    mapping: Path = typer.Option(
        ...,
        "--mapping",
        "-m",
        help="Path to mapping configuration file",
        exists=True,
        dir_okay=False,
    ),
) -> None:
    """Display information about mapping configuration."""
    try:
        config = load_mapping_config(mapping)
        
        console.print(f"\n[bold]Mapping Configuration: {mapping}[/bold]\n")
        
        # Namespaces
        console.print("[bold cyan]Namespaces:[/bold cyan]")
        for prefix, uri in config.namespaces.items():
            console.print(f"  {prefix}: {uri}")
        
        # Defaults
        console.print(f"\n[bold cyan]Base IRI:[/bold cyan] {config.defaults.base_iri}")
        if config.defaults.language:
            console.print(f"[bold cyan]Default Language:[/bold cyan] {config.defaults.language}")
        
        # Sheets
        console.print(f"\n[bold cyan]Sheets ({len(config.sheets)}):[/bold cyan]")
        for sheet in config.sheets:
            console.print(f"\n  [bold]{sheet.name}[/bold]")
            console.print(f"    Source: {sheet.source}")
            console.print(f"    Class: {sheet.row_resource.class_type}")
            console.print(f"    IRI Template: {sheet.row_resource.iri_template}")
            console.print(f"    Columns: {len(sheet.columns)}")
            console.print(f"    Linked Objects: {len(sheet.objects)}")
        
        # Validation
        if config.validation and config.validation.shacl:
            console.print(f"\n[bold cyan]Validation:[/bold cyan]")
            console.print(f"  SHACL Enabled: {config.validation.shacl.enabled}")
            console.print(f"  Shapes File: {config.validation.shacl.shapes_file}")
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(code=1)


def _display_processing_summary(report: ProcessingReport, verbose: bool) -> None:
    """Display processing summary table."""
    table = Table(title="Processing Summary")
    
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Total Rows", str(report.total_rows))
    table.add_row("Successful", str(report.successful_rows))
    table.add_row("Failed", str(report.failed_rows))
    table.add_row("Warnings", str(report.warnings))
    
    console.print(table)
    
    # Show error samples
    if report.errors and verbose:
        console.print("\n[bold]Errors (sample):[/bold]")
        for error in report.errors[:10]:  # Show first 10
            console.print(f"  Row {error.row}: {error.error}")
        
        if len(report.errors) > 10:
            console.print(f"  ... and {len(report.errors) - 10} more errors")


def _display_validation_results(report, verbose: bool) -> None:
    """Display validation results."""
    if report.conforms:
        console.print("[bold green]✓ Validation passed[/bold green]")
    else:
        console.print("[bold red]✗ Validation failed[/bold red]")
        console.print(f"\n[bold]Violations ({len(report.results)}):[/bold]")
        
        for result in report.results[:20]:  # Show first 20
            console.print(f"\n  [red]●[/red] {result.focus_node}")
            if result.result_path:
                console.print(f"    Path: {result.result_path}")
            console.print(f"    {result.result_message}")
            console.print(f"    Severity: {result.severity}")
        
        if len(report.results) > 20:
            console.print(f"\n  ... and {len(report.results) - 20} more violations")


@app.command()
def generate(
    ontology: Path = typer.Option(
        ...,
        "--ontology",
        "-ont",
        help="Path to ontology file (TTL, RDF/XML, etc.)",
        exists=True,
        dir_okay=False,
    ),
    spreadsheet: Path = typer.Option(
        ...,
        "--spreadsheet",
        "-s",
        help="Path to spreadsheet file (CSV or XLSX)",
        exists=True,
        dir_okay=False,
    ),
    output: Path = typer.Option(
        ...,
        "--output",
        "-o",
        help="Path to write generated mapping configuration",
        dir_okay=False,
    ),
    base_iri: str = typer.Option(
        "http://example.org/",
        "--base-iri",
        "-b",
        help="Base IRI for generated resources",
    ),
    target_class: Optional[str] = typer.Option(
        None,
        "--class",
        "-c",
        help="Target ontology class (URI or label). If omitted, will auto-detect.",
    ),
    format: str = typer.Option(
        "yaml",
        "--format",
        "-f",
        help="Output format: yaml or json",
    ),
    analyze_only: bool = typer.Option(
        False,
        "--analyze-only",
        help="Only analyze and show suggestions, don't generate mapping",
    ),
    export_schema: bool = typer.Option(
        False,
        "--export-schema",
        help="Export JSON Schema for mapping validation",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable detailed logging",
    ),
):
    """
    Generate a mapping configuration from an ontology and spreadsheet.
    
    This command analyzes your ontology and spreadsheet to automatically
    generate a mapping configuration file. It will:
    
    - Extract classes and properties from the ontology
    - Analyze column types and patterns in the spreadsheet
    - Match columns to ontology properties
    - Suggest IRI templates based on identifier columns
    - Detect potential linked objects
    
    The generated configuration can then be refined manually if needed.
    """
    try:
        console.print("[blue]Analyzing ontology...[/blue]")
        onto_analyzer = OntologyAnalyzer(str(ontology))
        console.print(f"  Found {len(onto_analyzer.classes)} classes")
        console.print(f"  Found {len(onto_analyzer.properties)} properties")
        
        console.print("\n[blue]Analyzing spreadsheet...[/blue]")
        sheet_analyzer = SpreadsheetAnalyzer(str(spreadsheet))
        console.print(f"  Columns: {len(sheet_analyzer.columns)}")
        console.print(f"  Identifier columns: {[c.name for c in sheet_analyzer.get_identifier_columns()]}")
        
        if analyze_only:
            console.print("\n[bold]Spreadsheet Analysis:[/bold]")
            console.print(sheet_analyzer.summary())
            
            if target_class:
                # Show properties for target class
                cls = None
                for c in onto_analyzer.classes.values():
                    if c.label == target_class or str(c.uri).endswith(target_class):
                        cls = c
                        break
                
                if cls:
                    console.print(f"\n[bold]Properties for class {cls.label}:[/bold]")
                    props = onto_analyzer.get_properties_for_class(cls.uri)
                    for prop in props:
                        console.print(f"  - {prop.label or prop.uri} (range: {prop.range_type})")
            
            return
        
        console.print("\n[blue]Generating mapping configuration...[/blue]")
        
        config = GeneratorConfig(
            base_iri=base_iri,
            include_comments=True,
            auto_detect_relationships=True,
        )
        
        generator = MappingGenerator(
            str(ontology),
            str(spreadsheet),
            config,
        )
        
        mapping = generator.generate(target_class=target_class, output_path=str(output))
        
        if verbose:
            console.print("\n[bold]Generated Mapping:[/bold]")
            import json
            console.print(json.dumps(mapping, indent=2))
        
        # Save to file
        if format.lower() == "json":
            generator.save_json(str(output))
        else:
            generator.save_yaml(str(output))
        
        console.print(f"\n[green]✓ Mapping configuration written to {output}[/green]")
        
        # Export JSON Schema if requested
        if export_schema:
            schema_file = output.parent / f"{output.stem}_schema.json"
            schema = generator.get_json_schema()
            
            import json
            with open(schema_file, 'w') as f:
                json.dump(schema, f, indent=2)
            
            console.print(f"[green]✓ JSON Schema exported to {schema_file}[/green]")
            console.print("\n[yellow]You can use this schema to validate your mapping configurations.[/yellow]")
        
        # Show next steps
        console.print("\n[bold]Next Steps:[/bold]")
        console.print(f"1. Review the generated mapping: {output}")
        console.print(f"2. Refine column-to-property mappings if needed")
        console.print(f"3. Run conversion:")
        console.print(f"   [cyan]rdfmap convert --mapping {output} --format ttl --output output.ttl[/cyan]")
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        if verbose:
            import traceback
            console.print(traceback.format_exc())
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
