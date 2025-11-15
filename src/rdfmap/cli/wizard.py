"""Interactive configuration wizard for RDFMap.

This module provides a user-friendly CLI wizard that guides users through
creating a mapping configuration with smart defaults and validation.
"""

from pathlib import Path
from typing import Optional, Dict, Any, List
import polars as pl
from rich.console import Console
from rich.prompt import Prompt, Confirm, IntPrompt
from rich.panel import Panel
from rich.table import Table
from rich import box
import yaml

console = Console()


class ConfigurationWizard:
    """Interactive wizard for creating RDFMap configurations."""

    def __init__(self):
        self.config: Dict[str, Any] = {}
        self.data_preview: Optional[pl.DataFrame] = None

    def run(self, output_path: Optional[str] = None) -> Dict[str, Any]:
        """Run the interactive configuration wizard.

        Args:
            output_path: Optional path to save the configuration file

        Returns:
            Generated configuration dictionary
        """
        console.print(Panel.fit(
            "[bold cyan]🎯 RDFMap Configuration Wizard[/bold cyan]\n"
            "Let me help you set up your semantic mapping configuration!",
            border_style="cyan"
        ))
        console.print()

        # Step 1: Data source
        self._configure_data_source()

        # Step 2: Ontology
        self._configure_ontology()

        # Step 3: Target class
        self._configure_target_class()

        # Step 4: Processing options
        self._configure_processing()

        # Step 5: Output format
        self._configure_output()

        # Step 6: Advanced options
        if Confirm.ask("\n[yellow]⚙️  Configure advanced options?[/yellow]", default=False):
            self._configure_advanced()

        # Step 7: Summary and save
        self._show_summary()

        if output_path or Confirm.ask("\n[green]💾 Save configuration?[/green]", default=True):
            save_path = output_path or Prompt.ask(
                "Configuration file path",
                default="mapping_config.yaml"
            )

            # Generate complete mapping automatically
            console.print("\n[yellow]🔄 Generating complete mapping...[/yellow]")
            complete_config = self._generate_complete_mapping(save_path)

            # Save the complete configuration
            self._save_complete_config(complete_config, save_path)
            console.print(f"[green]✓[/green] Complete configuration saved to [cyan]{save_path}[/cyan]")

            return complete_config

        # If not saved, build and return the mapping config
        return self._build_mapping_config()

    def _configure_data_source(self):
        """Configure data source settings."""
        console.print("[bold blue]📁 Step 1: Data Source[/bold blue]")
        console.print()

        # File path
        while True:
            file_path = Prompt.ask("Data file path")
            path = Path(file_path)

            if path.exists():
                self.config['data_source'] = str(path)
                break
            else:
                console.print(f"[red]✗[/red] File not found: {file_path}")
                if not Confirm.ask("Try again?", default=True):
                    raise ValueError("No valid data source provided")

        # Detect format
        suffix = path.suffix.lower()
        format_map = {
            '.csv': 'csv',
            '.tsv': 'tsv',
            '.xlsx': 'excel',
            '.json': 'json',
            '.xml': 'xml'
        }

        detected_format = format_map.get(suffix)
        if detected_format:
            console.print(f"[green]✓[/green] Detected format: [cyan]{detected_format}[/cyan]")
            self.config['format'] = detected_format
        else:
            self.config['format'] = Prompt.ask(
                "File format",
                choices=['csv', 'tsv', 'excel', 'json', 'xml']
            )

        # Analyze data
        self._analyze_data_source(path)

    def _analyze_data_source(self, path: Path):
        """Analyze the data source and show preview."""
        console.print("\n[yellow]🔍 Analyzing data...[/yellow]")

        try:
            # Try to load data with Polars
            if self.config['format'] == 'csv':
                self.data_preview = pl.read_csv(path, n_rows=100)
            elif self.config['format'] == 'excel':
                self.data_preview = pl.read_excel(path, sheet_id=0)
            elif self.config['format'] == 'json':
                self.data_preview = pl.read_json(path)

            if self.data_preview is not None:
                n_rows = len(self.data_preview)
                n_cols = len(self.data_preview.columns)

                console.print(f"[green]✓[/green] Found [cyan]{n_cols}[/cyan] columns, "
                             f"[cyan]{n_rows}[/cyan] rows (preview)")

                # Show column preview
                if Confirm.ask("\n[yellow]📊 Show column preview?[/yellow]", default=True):
                    self._show_column_preview()

        except Exception as e:
            console.print(f"[yellow]⚠[/yellow] Could not analyze data: {e}")

    def _show_column_preview(self):
        """Display a preview of columns and their data."""
        if self.data_preview is None:
            return

        table = Table(title="Column Preview", box=box.ROUNDED)
        table.add_column("Column", style="cyan")
        table.add_column("Type", style="yellow")
        table.add_column("Sample Value", style="white")
        table.add_column("Nulls", style="red")

        for col in self.data_preview.columns[:10]:  # Show first 10 columns
            dtype = str(self.data_preview[col].dtype)
            sample = str(self.data_preview[col][0]) if len(self.data_preview) > 0 else "N/A"
            null_count = self.data_preview[col].null_count()

            # Truncate long samples
            if len(sample) > 30:
                sample = sample[:27] + "..."

            table.add_row(col, dtype, sample, str(null_count))

        if len(self.data_preview.columns) > 10:
            table.add_row("...", "...", "...", "...")

        console.print(table)

    def _configure_ontology(self):
        """Configure ontology settings."""
        console.print("\n[bold blue]🧠 Step 2: Ontology[/bold blue]")
        console.print()

        has_ontology = Confirm.ask("Do you have an ontology file?", default=True)

        if has_ontology:
            while True:
                ontology_path = Prompt.ask("Ontology file path")
                path = Path(ontology_path)

                if path.exists():
                    self.config['ontology'] = str(path)
                    console.print(f"[green]✓[/green] Ontology: [cyan]{path.name}[/cyan]")
                    break
                else:
                    console.print(f"[red]✗[/red] File not found: {ontology_path}")
                    if not Confirm.ask("Try again?", default=True):
                        break

            # Check for imports
            if Confirm.ask("\n[yellow]📚 Does your ontology import other ontologies?[/yellow]",
                          default=False):
                imports = []
                while True:
                    import_path = Prompt.ask("Import file path (or press Enter to finish)",
                                            default="")
                    if not import_path:
                        break
                    if Path(import_path).exists():
                        imports.append(import_path)
                        console.print(f"[green]✓[/green] Added import")
                    else:
                        console.print(f"[red]✗[/red] File not found")

                if imports:
                    self.config['imports'] = imports
        else:
            console.print("[yellow]ℹ[/yellow] You can create a simple ontology or use a template")
            # TODO: Add ontology template generator

    def _configure_target_class(self):
        """Configure target class for mapping."""
        console.print("\n[bold blue]🎯 Step 3: Target Class[/bold blue]")
        console.print()

        target_class = Prompt.ask(
            "Target class URI (the main entity in your data)",
            default="http://example.com/MyClass"
        )
        self.config['target_class'] = target_class

        # IRI template
        console.print("\n[yellow]🔗 IRI Template[/yellow]")
        console.print("Template for generating unique identifiers")

        if self.data_preview is not None and len(self.data_preview.columns) > 0:
            # Suggest ID columns
            id_candidates = [col for col in self.data_preview.columns
                           if 'id' in col.lower() or col.lower().endswith('_id')]

            if id_candidates:
                console.print(f"[cyan]💡 Suggested ID columns:[/cyan] {', '.join(id_candidates[:3])}")

        iri_template = Prompt.ask(
            "IRI template",
            default=f"{target_class}/{{id}}"
        )
        self.config['iri_template'] = iri_template

    def _configure_processing(self):
        """Configure processing options."""
        console.print("\n[bold blue]⚙️  Step 4: Processing Options[/bold blue]")
        console.print()

        # Processing mode
        console.print("[cyan]Processing priority:[/cyan]")
        console.print("  1. Speed - Fast processing")
        console.print("  2. Memory - Handle large files efficiently")
        console.print("  3. Quality - Best matching quality")
        console.print("  4. Balanced - Good balance (recommended)")

        priority = Prompt.ask(
            "Choose priority",
            choices=['1', '2', '3', '4'],
            default='4'
        )

        priority_map = {
            '1': 'speed',
            '2': 'memory',
            '3': 'quality',
            '4': 'balanced'
        }

        mode = priority_map[priority]
        self.config['priority'] = mode

        # Configure based on priority
        if mode == 'speed':
            self.config['use_semantic'] = False
            self.config['streaming'] = False
        elif mode == 'memory':
            self.config['streaming'] = True
            self.config['chunk_size'] = 10000
        elif mode == 'quality':
            self.config['use_semantic'] = True
            self.config['use_graph_reasoning'] = True
            self.config['use_history'] = True
        else:  # balanced
            self.config['use_semantic'] = True
            self.config['streaming'] = False

        console.print(f"[green]✓[/green] Configured for [cyan]{mode}[/cyan] priority")

    def _configure_output(self):
        """Configure output options."""
        console.print("\n[bold blue]📤 Step 5: Output Format[/bold blue]")
        console.print()

        output_format = Prompt.ask(
            "Output RDF format",
            choices=['turtle', 'nt', 'jsonld', 'rdfxml'],
            default='turtle'
        )
        self.config['output_format'] = output_format

        output_file = Prompt.ask(
            "Output file path",
            default=f"output.{output_format}"
        )
        self.config['output'] = output_file

        # Validation
        if Confirm.ask("\n[yellow]✓ Enable SHACL validation?[/yellow]", default=False):
            shapes_file = Prompt.ask("SHACL shapes file path")
            if Path(shapes_file).exists():
                self.config['validate'] = True
                self.config['shapes'] = shapes_file

    def _configure_advanced(self):
        """Configure advanced options."""
        console.print("\n[bold blue]🔧 Advanced Options[/bold blue]")
        console.print()

        # Matching thresholds
        if Confirm.ask("Customize matching thresholds?", default=False):
            self.config['thresholds'] = {}

            console.print("\n[cyan]Matching confidence thresholds (0.0-1.0):[/cyan]")
            self.config['thresholds']['semantic'] = float(Prompt.ask(
                "Semantic matching threshold", default="0.6"
            ))
            self.config['thresholds']['fuzzy'] = float(Prompt.ask(
                "Fuzzy matching threshold", default="0.4"
            ))

        # Enable specific features
        console.print("\n[cyan]Feature toggles:[/cyan]")

        if 'use_semantic' not in self.config:
            self.config['use_semantic'] = Confirm.ask(
                "Enable semantic matching (AI-powered)?", default=True
            )

        if 'use_graph_reasoning' not in self.config:
            self.config['use_graph_reasoning'] = Confirm.ask(
                "Enable graph reasoning (ontology structure)?", default=True
            )

        if 'use_history' not in self.config:
            self.config['use_history'] = Confirm.ask(
                "Enable mapping history (continuous learning)?", default=True
            )

        # Logging
        if Confirm.ask("\nEnable detailed logging?", default=True):
            self.config['enable_logging'] = True
            log_file = Prompt.ask("Log file path", default="rdfmap.log")
            self.config['log_file'] = log_file

    def _show_summary(self):
        """Show configuration summary."""
        console.print("\n" + "="*60)
        console.print("[bold green]📋 Configuration Summary[/bold green]")
        console.print("="*60)

        summary_table = Table(show_header=False, box=box.SIMPLE)
        summary_table.add_column("Setting", style="cyan")
        summary_table.add_column("Value", style="white")

        # Key settings
        summary_table.add_row("Data Source", self.config.get('data_source', 'N/A'))
        summary_table.add_row("Format", self.config.get('format', 'N/A'))
        summary_table.add_row("Ontology", self.config.get('ontology', 'N/A'))
        summary_table.add_row("Target Class", self.config.get('target_class', 'N/A'))
        summary_table.add_row("Output", self.config.get('output', 'N/A'))
        summary_table.add_row("Priority", self.config.get('priority', 'balanced'))

        console.print(summary_table)

        console.print("\n[bold yellow]ℹ️  Configuration Ready[/bold yellow]")
        console.print("The wizard will automatically generate a complete mapping configuration.")
        console.print("This includes:\n")
        console.print("  ✓ [cyan]Intelligent column-to-property matching[/cyan]")
        console.print("  ✓ [cyan]Foreign key relationship detection[/cyan]")
        console.print("  ✓ [cyan]Data type inference and validation[/cyan]")
        console.print("  ✓ [cyan]Helpful comments for review[/cyan]\n")
        console.print("After generation, you can:")
        console.print("  1. Review and adjust the mappings as needed")
        console.print("  2. Test with: [white]rdfmap convert --mapping <path> --limit 10[/white]")
        console.print("  3. Process full dataset once verified\n")

        # Estimate processing
        self._show_estimate()

    def _show_estimate(self):
        """Show processing time and quality estimates."""
        console.print("\n[bold yellow]📊 Estimates[/bold yellow]")

        if self.data_preview is not None:
            n_cols = len(self.data_preview.columns)

            # Estimate match rate based on configuration
            base_rate = 0.70
            if self.config.get('use_semantic'):
                base_rate += 0.15
            if self.config.get('use_graph_reasoning'):
                base_rate += 0.05
            if self.config.get('use_history'):
                base_rate += 0.05

            match_rate = min(base_rate, 0.95)

            console.print(f"[cyan]Expected match rate:[/cyan] {match_rate*100:.0f}%")
            console.print(f"[cyan]Columns likely mapped:[/cyan] {int(n_cols * match_rate)}/{n_cols}")
            console.print(f"[cyan]Manual review needed:[/cyan] ~{int(n_cols * (1-match_rate))} columns")

            # Time estimate (very rough)
            time_seconds = n_cols * 2  # ~2 seconds per column
            if self.config.get('use_semantic'):
                time_seconds += n_cols * 1

            if time_seconds < 60:
                time_str = f"{time_seconds:.0f} seconds"
            else:
                time_str = f"{time_seconds/60:.1f} minutes"

            console.print(f"[cyan]Estimated processing time:[/cyan] {time_str}")

    def _build_mapping_config(self) -> Dict[str, Any]:
        """Build proper mapping configuration structure from wizard config.

        Returns:
            Mapping configuration dictionary
        """
        from pathlib import Path

        # Build proper mapping configuration structure
        mapping_config = {
            'namespaces': {
                'xsd': 'http://www.w3.org/2001/XMLSchema#',
                'rdfs': 'http://www.w3.org/2000/01/rdf-schema#',
                'owl': 'http://www.w3.org/2002/07/owl#',
            },
            'defaults': {
                'base_iri': self._extract_base_iri(),
            },
            'sheets': [{
                'name': Path(self.config.get('data_source', 'data')).stem,
                'source': self.config.get('data_source'),
                'row_resource': {
                    'class': self.config.get('target_class', 'http://example.com/Thing'),
                    'iri_template': self.config.get('iri_template', '{base_iri}resource/{id}'),
                },
                'columns': {},
                'objects': {}
            }],
            'options': {
                'on_error': 'report',
                'skip_empty_values': True,
            }
        }

        # Add ontology if specified
        if 'ontology' in self.config:
            mapping_config['ontology'] = self.config['ontology']

        # Add imports if specified
        if 'imports' in self.config:
            mapping_config['imports'] = self.config['imports']

        # Add format-specific options
        if self.config.get('format') == 'csv':
            mapping_config['options']['delimiter'] = ','
            mapping_config['options']['header'] = True

        # Add validation if enabled
        if self.config.get('validate'):
            mapping_config['validation'] = {
                'shacl': {
                    'enabled': True,
                    'shapes_file': self.config.get('shapes', ''),
                    'inference': 'none'
                }
            }

        # Add processing hints as comments
        if self.config.get('chunk_size'):
            mapping_config['options']['chunk_size'] = self.config['chunk_size']

        # Store wizard metadata separately for reference
        mapping_config['_wizard_config'] = {
            'priority': self.config.get('priority', 'balanced'),
            'use_semantic': self.config.get('use_semantic', True),
            'use_graph_reasoning': self.config.get('use_graph_reasoning', True),
            'use_history': self.config.get('use_history', True),
            'streaming': self.config.get('streaming', False),
            'output_format': self.config.get('output_format', 'turtle'),
            'output': self.config.get('output', 'output.ttl'),
            'enable_logging': self.config.get('enable_logging', False),
            'log_file': self.config.get('log_file', ''),
        }

        return mapping_config

    def _generate_complete_mapping(self, output_path: str) -> Dict[str, Any]:
        """Generate complete mapping by running the generator and merging wizard settings.

        Args:
            output_path: Path where config will be saved

        Returns:
            Complete mapping configuration with wizard settings merged
        """
        from ..generator.mapping_generator import MappingGenerator, GeneratorConfig
        from rich.console import Console

        console = Console()

        # Create generator config from wizard settings
        gen_config = GeneratorConfig(
            base_iri=self._extract_base_iri(),
            include_comments=True,
            auto_detect_relationships=True,
            min_confidence=0.5
        )

        # Create generator
        generator = MappingGenerator(
            ontology_file=self.config.get('ontology'),
            data_file=self.config.get('data_source'),
            config=gen_config
        )

        # Generate mapping
        target_class = self.config.get('target_class')
        mapping = generator.generate(target_class=target_class, output_path=output_path)

        # Display alignment report if available
        if hasattr(generator, 'alignment_report') and generator.alignment_report:
            console.print()
            generator.print_alignment_summary(show_details=True)

            # Save alignment reports
            try:
                from pathlib import Path
                output_dir = Path(output_path).parent
                json_report, html_report = generator.save_alignment_report(str(output_dir))
                console.print(f"\n[dim]Alignment reports saved to:[/dim]")
                console.print(f"[dim]  • {json_report}[/dim]")
                console.print(f"[dim]  • {html_report}[/dim]\n")
            except Exception:
                pass

        # Merge wizard-specific settings
        mapping = self._merge_wizard_settings(mapping)

        return mapping

    def _merge_wizard_settings(self, mapping: Dict[str, Any]) -> Dict[str, Any]:
        """Merge wizard-specific settings into generated mapping.

        Args:
            mapping: Generated mapping configuration

        Returns:
            Mapping with wizard settings merged
        """
        # Update namespaces - keep only essential ones plus ontology namespace
        essential_ns = {'xsd', 'rdfs', 'owl', 'rdf'}
        ontology_ns = {k: v for k, v in mapping.get('namespaces', {}).items()
                      if k in essential_ns or 'example.com' in v or 'mortgage' in v}
        mapping['namespaces'] = ontology_ns

        # Ensure sheet source uses full path from wizard config
        if mapping.get('sheets') and self.config.get('data_source'):
            for sheet in mapping['sheets']:
                # Override with full path from wizard
                sheet['source'] = self.config['data_source']

        # Add validation if configured
        if self.config.get('validate'):
            mapping['validation'] = {
                'shacl': {
                    'enabled': True,
                    'shapes_file': self.config.get('shapes', ''),
                    'inference': 'none'
                }
            }

        # Enhance options with wizard settings
        options = mapping.get('options', {})

        # Add format-specific options
        if self.config.get('format') == 'csv':
            options['delimiter'] = ','
            options['header'] = True

        # Add processing options based on priority
        priority = self.config.get('priority', 'balanced')
        if priority == 'memory' and self.config.get('streaming'):
            options['chunk_size'] = self.config.get('chunk_size', 10000)
        elif priority == 'balanced':
            options['chunk_size'] = 1000

        mapping['options'] = options

        # Store wizard metadata for reference
        mapping['_wizard_metadata'] = {
            'generated_by': 'RDFMap Configuration Wizard',
            'priority': priority,
            'use_semantic_matching': self.config.get('use_semantic', True),
            'use_graph_reasoning': self.config.get('use_graph_reasoning', True),
            'use_history': self.config.get('use_history', True),
            'output_format': self.config.get('output_format', 'turtle'),
            'output_file': self.config.get('output', 'output.ttl'),
        }

        if self.config.get('enable_logging'):
            mapping['_wizard_metadata']['log_file'] = self.config.get('log_file', 'rdfmap.log')

        return mapping

    def _save_complete_config(self, mapping: Dict[str, Any], path: str):
        """Save complete configuration with helpful comments and formatting.

        Args:
            mapping: Complete mapping configuration
            path: Path to save the file
        """
        try:
            from ..generator.yaml_formatter import save_formatted_mapping

            # Prepare wizard config for header
            wizard_config = {
                'data_source': self.config.get('data_source'),
                'ontology': self.config.get('ontology'),
                'target_class': self.config.get('target_class'),
            }

            # Use custom formatter
            save_formatted_mapping(mapping, path, wizard_config)
        except ImportError:
            # Fallback to simple YAML dump if formatter not available
            with open(path, 'w') as f:
                yaml.dump(mapping, f, default_flow_style=False, sort_keys=False)

    def _save_config(self, path: str):
        """Save configuration to YAML file.

        Args:
            path: Path to save the configuration file
        """
        # Build proper mapping config structure
        mapping_config = self._build_mapping_config()

        # Save as YAML
        with open(path, 'w') as f:
            yaml.dump(mapping_config, f, default_flow_style=False, sort_keys=False)

    def _extract_base_iri(self) -> str:
        """Extract base IRI from target class or use default.

        Returns:
            Base IRI string
        """
        target_class = self.config.get('target_class', '')

        if target_class:
            # Extract base IRI from target class URI
            # e.g., "http://example.com/ontology#Person" -> "http://example.com/ontology#"
            if '#' in target_class:
                return target_class.rsplit('#', 1)[0] + '#'
            elif '/' in target_class:
                return target_class.rsplit('/', 1)[0] + '/'

        # Use default
        return 'http://example.org/data/'


def run_wizard(output_path: Optional[str] = None, template_name: Optional[str] = None) -> Dict[str, Any]:
    """Run the configuration wizard.

    Args:
        output_path: Optional path to save configuration
        template_name: Optional template name to use as starting point

    Returns:
        Generated configuration dictionary
    """
    wizard = ConfigurationWizard()

    # If template is specified, show template info
    if template_name:
        from ..templates import get_template_library

        library = get_template_library()
        template = library.get_template(template_name)

        if template:
            console.print(Panel.fit(
                f"[bold cyan]Using Template: {template.name}[/bold cyan]\n"
                f"[dim]{template.description}[/dim]\n\n"
                f"Domain: {template.domain}",
                border_style="cyan"
            ))
            console.print()

            # Set template context in wizard
            wizard.config['_template_hint'] = {
                'name': template.name,
                'domain': template.domain,
                'expected_columns': template.template_config.get('expected_columns', []),
                'target_classes': template.template_config.get('target_classes', [])
            }

    return wizard.run(output_path)


if __name__ == "__main__":
    # Test the wizard
    config = run_wizard()
    print("\nGenerated configuration:")
    print(yaml.dump(config, default_flow_style=False))

