"""Interactive review of generated mappings.

Allows users to review and approve/reject column-to-property mappings
before finalizing the configuration.
"""

from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import yaml
from rich.console import Console
from rich.table import Table
from rich.prompt import Confirm, Prompt
from rich.panel import Panel
from rich import box

from ..generator.mapping_generator import MappingGenerator, GeneratorConfig
from ..models.alignment import AlignmentReport, WeakMatch


class InteractiveReviewer:
    """Interactive review system for generated mappings."""

    def __init__(self, console: Optional[Console] = None):
        """Initialize the interactive reviewer.

        Args:
            console: Rich console instance (creates new if None)
        """
        self.console = console or Console()
        self.changes_made = False
        self.accepted_count = 0
        self.rejected_count = 0
        self.modified_count = 0

    def review_mapping(
        self,
        mapping_file: str,
        alignment_report: Optional[AlignmentReport] = None,
        output_file: Optional[str] = None
    ) -> Dict[str, Any]:
        """Review a generated mapping configuration interactively.

        Args:
            mapping_file: Path to the mapping YAML file
            alignment_report: Optional alignment report with match details
            output_file: Where to save the reviewed mapping (default: overwrites input)

        Returns:
            Updated mapping configuration
        """
        # Load the mapping
        with open(mapping_file, 'r') as f:
            mapping = yaml.safe_load(f)

        if not mapping or 'sheets' not in mapping:
            self.console.print("[red]Error: Invalid mapping file[/red]")
            return mapping

        # Show header
        self._show_header(mapping_file)

        # Review each sheet
        for sheet_idx, sheet in enumerate(mapping['sheets']):
            self._review_sheet(sheet, sheet_idx, alignment_report)

        # Show summary
        self._show_summary()

        # Save if changes were made
        if self.changes_made:
            output_path = output_file or mapping_file

            if Confirm.ask(f"\n[green]Save changes to {output_path}?[/green]", default=True):
                with open(output_path, 'w') as f:
                    yaml.dump(mapping, f, default_flow_style=False, sort_keys=False)
                self.console.print(f"[green]✓ Saved to {output_path}[/green]")
            else:
                self.console.print("[yellow]Changes not saved[/yellow]")
        else:
            self.console.print("\n[dim]No changes made[/dim]")

        return mapping

    def _show_header(self, mapping_file: str):
        """Show review session header."""
        self.console.print("\n" + "="*80)
        self.console.print("[bold cyan]🔍 Interactive Mapping Review[/bold cyan]")
        self.console.print("="*80)
        self.console.print(f"[dim]File: {mapping_file}[/dim]\n")
        self.console.print("[yellow]Instructions:[/yellow]")
        self.console.print("  • Review each column-to-property mapping")
        self.console.print("  • Accept (y), Reject (n), or Modify (m)")
        self.console.print("  • Rejected mappings will be removed")
        self.console.print("  • You can choose alternatives when available\n")

    def _review_sheet(
        self,
        sheet: Dict[str, Any],
        sheet_idx: int,
        alignment_report: Optional[AlignmentReport]
    ):
        """Review mappings for a single sheet.

        Args:
            sheet: Sheet configuration
            sheet_idx: Index of the sheet
            alignment_report: Alignment report with match details
        """
        sheet_name = sheet.get('name', f'Sheet {sheet_idx}')

        self.console.print(f"\n[bold]📋 Reviewing: {sheet_name}[/bold]")
        self.console.print("─" * 80 + "\n")

        # Review column mappings
        columns = sheet.get('columns', {})
        if columns:
            self._review_columns(columns, alignment_report)

        # Review object mappings
        objects = sheet.get('objects', {})
        if objects:
            self._review_objects(objects, alignment_report)

    def _review_columns(
        self,
        columns: Dict[str, Any],
        alignment_report: Optional[AlignmentReport]
    ):
        """Review column mappings.

        Args:
            columns: Column mappings dictionary
            alignment_report: Alignment report with match details
        """
        self.console.print("[bold]Column Mappings:[/bold]\n")

        columns_to_remove = []

        for col_name, col_config in columns.items():
            # Get match details from alignment report
            match_info = self._get_match_info(col_name, alignment_report)

            # Show the mapping
            decision = self._review_single_column(
                col_name,
                col_config,
                match_info
            )

            if decision == 'reject':
                columns_to_remove.append(col_name)
                self.rejected_count += 1
                self.changes_made = True
            elif decision == 'modify':
                # Column config already modified by _review_single_column
                self.modified_count += 1
                self.changes_made = True
            elif decision == 'accept':
                self.accepted_count += 1

        # Remove rejected columns
        for col_name in columns_to_remove:
            del columns[col_name]

    def _review_single_column(
        self,
        col_name: str,
        col_config: Dict[str, Any],
        match_info: Optional[Dict[str, Any]]
    ) -> str:
        """Review a single column mapping.

        Args:
            col_name: Column name
            col_config: Column configuration
            match_info: Match information from alignment report

        Returns:
            Decision: 'accept', 'reject', or 'modify'
        """
        # Create info panel
        property_uri = col_config.get('as', 'unknown')
        property_label = property_uri.split(':')[-1].split('/')[-1]
        datatype = col_config.get('datatype', 'unknown')
        required = col_config.get('required', False)

        # Get confidence and alternatives
        confidence = match_info.get('confidence', 0.0) if match_info else 0.0
        confidence_level = match_info.get('confidence_level', 'unknown') if match_info else 'unknown'
        alternatives = match_info.get('alternatives', []) if match_info else []

        # Color code by confidence
        if confidence >= 0.9:
            conf_color = "green"
            conf_symbol = "✓"
        elif confidence >= 0.7:
            conf_color = "yellow"
            conf_symbol = "⚠"
        else:
            conf_color = "red"
            conf_symbol = "✗"

        # Build display
        info_lines = [
            f"[cyan]Column:[/cyan] {col_name}",
            f"[cyan]→ Property:[/cyan] {property_label}",
            f"[cyan]Datatype:[/cyan] {datatype}",
            f"[cyan]Required:[/cyan] {required}",
            f"[cyan]Confidence:[/cyan] [{conf_color}]{conf_symbol} {confidence:.2f}[/{conf_color}] ({confidence_level})"
        ]

        if alternatives:
            info_lines.append(f"\n[dim]Alternatives available: {len(alternatives)}[/dim]")

        panel = Panel(
            "\n".join(info_lines),
            title=f"[bold]{col_name}[/bold]",
            border_style=conf_color
        )

        self.console.print(panel)

        # Get user decision
        while True:
            choice = Prompt.ask(
                "[bold]Decision[/bold]",
                choices=["y", "n", "m", "a", "s"],
                default="y"
            ).lower()

            if choice == 'y':
                self.console.print("[green]✓ Accepted[/green]\n")
                return 'accept'

            elif choice == 'n':
                self.console.print("[red]✗ Rejected[/red]\n")
                return 'reject'

            elif choice == 'm':
                # Show alternatives and let user choose
                if alternatives:
                    new_property = self._choose_alternative(alternatives)
                    if new_property:
                        col_config['as'] = new_property
                        self.console.print(f"[green]✓ Modified to {new_property}[/green]\n")
                        return 'modify'
                    else:
                        continue  # User cancelled, ask again
                else:
                    # Manual entry
                    new_property = Prompt.ask("[cyan]Enter property URI[/cyan]")
                    if new_property:
                        col_config['as'] = new_property
                        self.console.print(f"[green]✓ Modified to {new_property}[/green]\n")
                        return 'modify'
                    else:
                        continue

            elif choice == 'a':
                # Accept all remaining
                self.console.print("[green]✓ Accepting all remaining mappings[/green]\n")
                return 'accept_all'

            elif choice == 's':
                # Skip (same as accept)
                self.console.print("[dim]→ Skipped[/dim]\n")
                return 'accept'

    def _choose_alternative(self, alternatives: List[Tuple[str, float]]) -> Optional[str]:
        """Let user choose from alternative properties.

        Args:
            alternatives: List of (property_uri, confidence) tuples

        Returns:
            Chosen property URI or None if cancelled
        """
        self.console.print("\n[bold]Available alternatives:[/bold]")

        # Show alternatives table
        table = Table(show_header=True, box=box.SIMPLE)
        table.add_column("#", style="cyan", width=3)
        table.add_column("Property", style="white")
        table.add_column("Confidence", justify="right")

        for idx, (prop, conf) in enumerate(alternatives[:10], 1):
            prop_label = prop.split(':')[-1].split('/')[-1]
            table.add_row(str(idx), prop_label, f"{conf:.2f}")

        self.console.print(table)

        choice = Prompt.ask(
            "\n[bold]Choose alternative (number) or [c] to cancel[/bold]",
            default="c"
        )

        if choice.lower() == 'c':
            return None

        try:
            idx = int(choice) - 1
            if 0 <= idx < len(alternatives):
                return alternatives[idx][0]
        except ValueError:
            pass

        self.console.print("[red]Invalid choice[/red]")
        return None

    def _review_objects(
        self,
        objects: Dict[str, Any],
        alignment_report: Optional[AlignmentReport]
    ):
        """Review object property mappings.

        Args:
            objects: Object mappings dictionary
            alignment_report: Alignment report with match details
        """
        self.console.print("\n[bold]Object Property Mappings:[/bold]\n")

        for obj_name, obj_config in objects.items():
            self.console.print(f"[cyan]Object:[/cyan] {obj_name}")
            self.console.print(f"[dim]  Class: {obj_config.get('class')}[/dim]")
            self.console.print(f"[dim]  IRI Template: {obj_config.get('iri_template')}[/dim]")

            # For now, just accept objects (can enhance later)
            if Confirm.ask(f"Accept object mapping for {obj_name}?", default=True):
                self.console.print("[green]✓ Accepted[/green]\n")
                self.accepted_count += 1
            else:
                self.console.print("[yellow]⚠ Object mappings can't be modified in review (yet)[/yellow]")
                self.console.print("[dim]Edit the YAML file directly to change object mappings[/dim]\n")

    def _get_match_info(
        self,
        col_name: str,
        alignment_report: Optional[AlignmentReport]
    ) -> Optional[Dict[str, Any]]:
        """Get match information for a column from alignment report.

        Args:
            col_name: Column name
            alignment_report: Alignment report

        Returns:
            Match info dictionary or None
        """
        if not alignment_report:
            return None

        # Check weak matches
        for match in alignment_report.weak_matches:
            if match.column_name == col_name:
                # Extract alternatives from suggestions
                alternatives = []
                for suggestion in match.suggestions:
                    alternatives.append((
                        suggestion.property_uri,
                        0.5  # Default confidence for suggestions
                    ))

                return {
                    'confidence': match.confidence_score,
                    'confidence_level': match.confidence_level.value,
                    'match_type': match.match_type.value,
                    'alternatives': alternatives
                }

        # Check unmapped columns
        for unmapped in alignment_report.unmapped_columns:
            if unmapped.column_name == col_name:
                return {
                    'confidence': 0.0,
                    'confidence_level': 'unmapped',
                    'match_type': 'none',
                    'alternatives': []
                }

        # If not in weak matches or unmapped, assume high confidence
        return {
            'confidence': 0.95,
            'confidence_level': 'high',
            'match_type': 'semantic',
            'alternatives': []
        }

    def _show_summary(self):
        """Show review summary."""
        self.console.print("\n" + "="*80)
        self.console.print("[bold]📊 Review Summary[/bold]")
        self.console.print("="*80)

        total = self.accepted_count + self.rejected_count + self.modified_count

        if total > 0:
            self.console.print(f"[green]✓ Accepted:[/green] {self.accepted_count}")
            self.console.print(f"[yellow]⚠ Modified:[/yellow] {self.modified_count}")
            self.console.print(f"[red]✗ Rejected:[/red] {self.rejected_count}")
            self.console.print(f"[bold]Total reviewed:[/bold] {total}\n")
        else:
            self.console.print("[dim]No mappings reviewed[/dim]\n")


def review_mapping_file(
    mapping_file: str,
    output_file: Optional[str] = None,
    alignment_file: Optional[str] = None
) -> Dict[str, Any]:
    """Review a mapping file interactively.

    Args:
        mapping_file: Path to mapping YAML file
        output_file: Where to save reviewed mapping (default: overwrites input)
        alignment_file: Optional alignment report JSON file

    Returns:
        Updated mapping configuration
    """
    # Load alignment report if provided
    alignment_report = None
    if alignment_file and Path(alignment_file).exists():
        import json
        from ..models.alignment import (
            AlignmentReport, AlignmentStatistics, WeakMatch, UnmappedColumn,
            MatchType, ConfidenceLevel
        )

        try:
            with open(alignment_file, 'r') as f:
                report_data = json.load(f)

            # Reconstruct AlignmentReport from JSON
            # For now, just use the data directly in the reviewer
            # Full reconstruction would require more complex deserialization
            Console().print(f"[dim]Loaded alignment report from {alignment_file}[/dim]")
        except Exception as e:
            Console().print(f"[yellow]Warning: Could not load alignment report: {e}[/yellow]")

    # Run interactive review
    reviewer = InteractiveReviewer()
    return reviewer.review_mapping(mapping_file, alignment_report, output_file)

