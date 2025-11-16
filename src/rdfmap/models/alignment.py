"""Data models for semantic alignment reporting.

This module provides models for tracking and reporting the quality of 
semantic alignment between spreadsheet data and ontologies, including
unmapped columns, weak matches, and suggestions for ontology enrichment.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class MatchType(str, Enum):
    """Type of match between column and property."""
    EXACT_PREF_LABEL = "exact_pref_label"  # Exact match with skos:prefLabel
    EXACT_LABEL = "exact_label"  # Exact match with rdfs:label
    EXACT_ALT_LABEL = "exact_alt_label"  # Exact match with skos:altLabel
    EXACT_HIDDEN_LABEL = "exact_hidden_label"  # Exact match with skos:hiddenLabel
    EXACT_LOCAL_NAME = "exact_local_name"  # Exact match with property local name
    SEMANTIC_SIMILARITY = "semantic_similarity"  # Semantic embedding similarity
    PARTIAL = "partial"  # Partial string match
    FUZZY = "fuzzy"  # Fuzzy/similarity match
    MANUAL = "manual"  # Manually specified in config
    GRAPH_REASONING = "graph_reasoning"  # Match using ontology graph structure
    INHERITED_PROPERTY = "inherited_property"  # Property inherited from parent class
    UNMAPPED = "unmapped"  # No match found


class ConfidenceLevel(str, Enum):
    """Confidence level for a match."""
    HIGH = "high"  # 0.8 - 1.0
    MEDIUM = "medium"  # 0.5 - 0.79
    LOW = "low"  # 0.3 - 0.49
    VERY_LOW = "very_low"  # 0.0 - 0.29



class PropertyContext(BaseModel):
    """Context information about an ontology property for human review."""
    uri: str = Field(description="Property URI")
    label: Optional[str] = Field(default=None, description="rdfs:label of the property")
    pref_label: Optional[str] = Field(default=None, description="skos:prefLabel")
    alt_labels: List[str] = Field(default_factory=list, description="skos:altLabel values")
    hidden_labels: List[str] = Field(default_factory=list, description="skos:hiddenLabel values")
    comment: Optional[str] = Field(default=None, description="rdfs:comment explaining the property")
    domain_class: Optional[str] = Field(default=None, description="Primary domain class")
    range_type: Optional[str] = Field(default=None, description="Range type (datatype or class)")
    local_name: str = Field(description="Local name part of the URI")


class ClassContext(BaseModel):
    """Context information about an ontology class for human review."""
    uri: str = Field(description="Class URI")
    label: Optional[str] = Field(default=None, description="rdfs:label of the class")
    comment: Optional[str] = Field(default=None, description="rdfs:comment explaining the class")
    local_name: str = Field(description="Local name part of the URI")
    properties: List[PropertyContext] = Field(default_factory=list, description="Properties available for this class")


class OntologyContext(BaseModel):
    """Comprehensive ontology context for human mapping decisions."""
    target_class: ClassContext = Field(description="The target class being mapped to")
    related_classes: List[ClassContext] = Field(default_factory=list, description="Related classes that might be relevant")
    all_properties: List[PropertyContext] = Field(default_factory=list, description="All available properties in ontology")
    object_properties: List[PropertyContext] = Field(default_factory=list, description="Object properties for relationships")


class UnmappedColumn(BaseModel):
    """Information about a column that couldn't be mapped."""
    column_name: str = Field(description="Name of the unmapped column")
    sample_values: List[Any] = Field(
        default_factory=list,
        description="Sample values from the column (up to 5)"
    )
    inferred_datatype: Optional[str] = Field(
        default=None,
        description="Inferred XSD datatype"
    )
    reason: str = Field(
        default="No matching property found in ontology",
        description="Reason why column couldn't be mapped"
    )
    ontology_context: Optional[OntologyContext] = Field(
        default=None,
        description="Ontology context to help with manual mapping decisions"
    )


class SKOSEnrichmentSuggestion(BaseModel):
    """Suggestion for enriching ontology with SKOS labels."""
    property_uri: str = Field(description="URI of the property to enrich")
    property_label: str = Field(description="Human-readable property label")
    suggested_label_type: str = Field(
        description="Type of SKOS label to add (altLabel, hiddenLabel)"
    )
    suggested_label_value: str = Field(
        description="The column name that should be added as a label"
    )
    turtle_snippet: str = Field(
        description="Ready-to-add Turtle syntax for the SKOS triple"
    )
    justification: str = Field(
        description="Why this suggestion is being made"
    )


class WeakMatch(BaseModel):
    """Information about a low-confidence match that needs review."""
    column_name: str = Field(description="Name of the column")
    matched_property: str = Field(description="URI of the matched property")
    match_type: MatchType = Field(description="Type of match that was made")
    confidence_score: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence score between 0 and 1"
    )
    confidence_level: ConfidenceLevel = Field(
        description="Categorical confidence level"
    )
    matched_via: str = Field(
        description="What label/name was used for the match"
    )
    sample_values: List[Any] = Field(
        default_factory=list,
        description="Sample values from the column"
    )
    suggestions: List[SKOSEnrichmentSuggestion] = Field(
        default_factory=list,
        description="Suggestions to improve this match"
    )


class MatchDetail(BaseModel):
    """Full details for a mapped column (reason/explanation)."""
    column_name: str = Field(description="Name of the column")
    matched_property: str = Field(description="URI of the matched property")
    match_type: MatchType = Field(description="How the match was made")
    confidence_score: float = Field(ge=0.0, le=1.0)
    matcher_name: str = Field(description="Matcher that produced the result")
    matched_via: str = Field(description="The label/text or signal that led to this match")


class AlignmentStatistics(BaseModel):
    """Summary statistics for the alignment."""
    total_columns: int = Field(description="Total number of columns in spreadsheet")
    mapped_columns: int = Field(description="Number of successfully mapped columns")
    unmapped_columns: int = Field(description="Number of unmapped columns")
    high_confidence_matches: int = Field(description="Matches with confidence >= 0.8")
    medium_confidence_matches: int = Field(description="Matches with confidence 0.5-0.79")
    low_confidence_matches: int = Field(description="Matches with confidence 0.3-0.49")
    very_low_confidence_matches: int = Field(description="Matches with confidence < 0.3")
    mapping_success_rate: float = Field(
        ge=0.0,
        le=1.0,
        description="Percentage of columns successfully mapped (0-1)"
    )
    average_confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Average confidence score across all matches"
    )


class AlignmentReport(BaseModel):
    """Complete alignment report for a mapping generation session."""
    
    # Metadata
    generated_at: datetime = Field(
        default_factory=datetime.now,
        description="Timestamp when report was generated"
    )
    ontology_file: str = Field(description="Path to the ontology file")
    spreadsheet_file: str = Field(description="Path to the spreadsheet file")
    target_class: str = Field(description="Target ontology class for mapping")
    
    # Statistics
    statistics: AlignmentStatistics = Field(
        description="Summary statistics for the alignment"
    )
    
    # Details
    unmapped_columns: List[UnmappedColumn] = Field(
        default_factory=list,
        description="Columns that couldn't be mapped"
    )
    weak_matches: List[WeakMatch] = Field(
        default_factory=list,
        description="Low-confidence matches requiring review"
    )
    skos_enrichment_suggestions: List[SKOSEnrichmentSuggestion] = Field(
        default_factory=list,
        description="Suggestions for enriching the ontology with SKOS labels"
    )
    ontology_context: Optional[OntologyContext] = Field(
        default=None,
        description="Comprehensive ontology context for informed mapping decisions"
    )
    match_details: List[MatchDetail] = Field(default_factory=list, description="Detailed reasons for all mapped columns")

    # Configuration
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with proper JSON encoding."""
        return self.model_dump(mode='json')
    
    def summary_message(self) -> str:
        """Generate a human-readable summary message."""
        stats = self.statistics
        lines = [
            "Semantic Alignment Report",
            "=" * 50,
            f"Generated: {self.generated_at.strftime('%Y-%m-%d %H:%M:%S')}",
            f"Ontology: {self.ontology_file}",
            f"Spreadsheet: {self.spreadsheet_file}",
            f"Target Class: {self.target_class}",
            "",
            "Statistics:",
            f"  Total Columns: {stats.total_columns}",
            f"  Mapped: {stats.mapped_columns} ({stats.mapping_success_rate:.1%})",
            f"  Unmapped: {stats.unmapped_columns}",
            "",
            "Confidence Distribution:",
            f"  High (≥0.8):     {stats.high_confidence_matches}",
            f"  Medium (0.5-0.8): {stats.medium_confidence_matches}",
            f"  Low (0.3-0.5):    {stats.low_confidence_matches}",
            f"  Very Low (<0.3):  {stats.very_low_confidence_matches}",
            f"  Average: {stats.average_confidence:.2f}",
        ]

        if self.unmapped_columns:
            lines.extend([
                "",
                f"Unmapped Columns ({len(self.unmapped_columns)}):",
            ])
            for col in self.unmapped_columns[:5]:
                lines.append(f"  - {col.column_name}")
            if len(self.unmapped_columns) > 5:
                lines.append(f"  ... and {len(self.unmapped_columns) - 5} more")

        if self.weak_matches:
            lines.extend([
                "",
                f"Weak Matches Requiring Review ({len(self.weak_matches)}):",
            ])
            for match in self.weak_matches[:5]:
                lines.append(f"  - {match.column_name} → {match.matched_property} "
                           f"(confidence: {match.confidence_score:.2f})")
            if len(self.weak_matches) > 5:
                lines.append(f"  ... and {len(self.weak_matches) - 5} more")

        return "\n".join(lines)

    def print_rich_terminal(self, show_details: bool = True) -> None:
        """Print alignment report to terminal with Rich formatting.

        Args:
            show_details: Whether to show detailed match tables
        """
        try:
            from rich.console import Console
            from rich.table import Table
            from rich import box
            from pathlib import Path

            console = Console()
            stats = self.statistics

            # Header
            console.print("\n" + "="*80)
            console.print("[bold cyan]📊 Semantic Alignment Report[/bold cyan]")
            console.print("="*80 + "\n")

            # Metadata
            console.print(f"[dim]Generated: {self.generated_at.strftime('%Y-%m-%d %H:%M:%S')}[/dim]")
            console.print(f"[dim]Data: {Path(self.spreadsheet_file).name}[/dim]")
            console.print(f"[dim]Ontology: {Path(self.ontology_file).name}[/dim]\n")

            # Summary statistics
            console.print("[bold]Overall Quality:[/bold]")
            success_color = "green" if stats.mapping_success_rate >= 0.9 else "yellow" if stats.mapping_success_rate >= 0.7 else "red"
            console.print(f"  • Mapping Success Rate: [{success_color}]{stats.mapping_success_rate:.1%}[/{success_color}] "
                         f"({stats.mapped_columns}/{stats.total_columns} columns)")

            conf_color = "green" if stats.average_confidence >= 0.8 else "yellow" if stats.average_confidence >= 0.6 else "red"
            console.print(f"  • Average Confidence: [{conf_color}]{stats.average_confidence:.2f}[/{conf_color}]\n")

            # Confidence breakdown
            console.print("[bold]Confidence Distribution:[/bold]")
            console.print(f"  • [green]High (≥0.8):[/green] {stats.high_confidence_matches} columns")
            console.print(f"  • [yellow]Medium (0.5-0.79):[/yellow] {stats.medium_confidence_matches} columns")
            console.print(f"  • [red]Low (<0.5):[/red] {stats.low_confidence_matches + stats.very_low_confidence_matches} columns")
            if stats.unmapped_columns > 0:
                console.print(f"  • [red]Unmapped:[/red] {stats.unmapped_columns} columns\n")
            else:
                console.print()

            if show_details:
                # Weak matches needing review
                if self.weak_matches:
                    console.print("[bold yellow]⚠ Matches Requiring Review[/bold yellow]")
                    table = Table(show_header=True, box=box.SIMPLE)
                    table.add_column("Column", style="cyan")
                    table.add_column("Property", style="yellow")
                    table.add_column("Confidence", justify="right")
                    table.add_column("Match Type")

                    for match in self.weak_matches[:10]:
                        table.add_row(
                            match.column_name,
                            match.matched_property.split('#')[-1].split('/')[-1],
                            f"{match.confidence_score:.2f}",
                            match.match_type.value
                        )

                    console.print(table)
                    if len(self.weak_matches) > 10:
                        console.print(f"  [dim]... and {len(self.weak_matches) - 10} more[/dim]\n")
                    else:
                        console.print()

                # Unmapped columns
                if self.unmapped_columns:
                    console.print("[bold red]✗ Unmapped Columns[/bold red]")
                    table = Table(show_header=True, box=box.SIMPLE)
                    table.add_column("Column", style="cyan")
                    table.add_column("Type", style="dim")
                    table.add_column("Sample", style="dim")
                    table.add_column("Reason")

                    for col in self.unmapped_columns[:10]:
                        sample = str(col.sample_values[0]) if col.sample_values else ""
                        if len(sample) > 30:
                            sample = sample[:27] + "..."

                        table.add_row(
                            col.column_name,
                            col.inferred_datatype or "unknown",
                            sample,
                            col.reason
                        )

                    console.print(table)
                    if len(self.unmapped_columns) > 10:
                        console.print(f"  [dim]... and {len(self.unmapped_columns) - 10} more[/dim]\n")
                    else:
                        console.print()

            console.print("="*80 + "\n")

        except ImportError:
            # Fallback to simple print if Rich is not available
            print(self.summary_message())

    def export_html(self, output_path: str) -> None:
        """Export alignment report as HTML file.

        Args:
            output_path: Path to save HTML file
        """
        from pathlib import Path

        stats = self.statistics
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Alignment Report - {Path(self.spreadsheet_file).name}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            max-width: 1200px;
            margin: 40px auto;
            padding: 0 20px;
            background: #f5f5f5;
            color: #333;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
        }}
        .header h1 {{
            margin: 0 0 10px 0;
            font-size: 28px;
        }}
        .header .meta {{
            opacity: 0.9;
            font-size: 14px;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .stat-card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .stat-card .label {{
            color: #666;
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 5px;
        }}
        .stat-card .value {{
            font-size: 32px;
            font-weight: bold;
            color: #667eea;
        }}
        .stat-card .sub {{
            color: #999;
            font-size: 14px;
            margin-top: 5px;
        }}
        .section {{
            background: white;
            padding: 25px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .section h2 {{
            margin-top: 0;
            color: #667eea;
            font-size: 20px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }}
        th {{
            background: #f8f9fa;
            padding: 12px;
            text-align: left;
            font-weight: 600;
            color: #666;
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        td {{
            padding: 12px;
            border-bottom: 1px solid #f0f0f0;
        }}
        .badge {{
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
        }}
        .badge-high {{ background: #d4edda; color: #155724; }}
        .badge-medium {{ background: #fff3cd; color: #856404; }}
        .badge-low {{ background: #f8d7da; color: #721c24; }}
        .confidence {{ font-weight: 600; }}
        .confidence-high {{ color: #28a745; }}
        .confidence-medium {{ color: #ffc107; }}
        .confidence-low {{ color: #dc3545; }}
        .footer {{
            text-align: center;
            color: #999;
            font-size: 12px;
            margin-top: 40px;
            padding: 20px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📊 Semantic Alignment Report</h1>
        <div class="meta">
            <div>Data: {Path(self.spreadsheet_file).name}</div>
            <div>Ontology: {Path(self.ontology_file).name}</div>
            <div>Generated: {self.generated_at.strftime('%Y-%m-%d %H:%M:%S')}</div>
        </div>
    </div>
    
    <div class="stats-grid">
        <div class="stat-card">
            <div class="label">Success Rate</div>
            <div class="value">{stats.mapping_success_rate:.0%}</div>
            <div class="sub">{stats.mapped_columns}/{stats.total_columns} columns</div>
        </div>
        <div class="stat-card">
            <div class="label">Avg Confidence</div>
            <div class="value">{stats.average_confidence:.2f}</div>
            <div class="sub">across all mappings</div>
        </div>
        <div class="stat-card">
            <div class="label">High Confidence</div>
            <div class="value">{stats.high_confidence_matches}</div>
            <div class="sub">≥ 0.8 threshold</div>
        </div>
        <div class="stat-card">
            <div class="label">Needs Review</div>
            <div class="value">{stats.medium_confidence_matches + stats.low_confidence_matches}</div>
            <div class="sub">< 0.8 confidence</div>
        </div>
    </div>
"""

        # Weak matches section
        if self.weak_matches:
            html += """
    <div class="section">
        <h2>⚠ Matches Requiring Review</h2>
        <p style="color: #856404; font-size: 14px; margin-bottom: 15px;">
            These mappings have moderate to low confidence. Please review and validate.
        </p>
        <table>
            <thead>
                <tr>
                    <th>Column</th>
                    <th>Property</th>
                    <th>Confidence</th>
                    <th>Match Type</th>
                </tr>
            </thead>
            <tbody>
"""
            for match in self.weak_matches:
                conf_class = "high" if match.confidence_score >= 0.8 else "medium" if match.confidence_score >= 0.5 else "low"
                property_short = match.matched_property.split('#')[-1].split('/')[-1]
                html += f"""
                <tr>
                    <td><strong>{match.column_name}</strong></td>
                    <td>{property_short}</td>
                    <td><span class="confidence confidence-{conf_class}">{match.confidence_score:.2f}</span></td>
                    <td><span class="badge badge-{conf_class}">{match.match_type.value}</span></td>
                </tr>
"""
            html += """
            </tbody>
        </table>
    </div>
"""

        # Match Details section (all mapped columns with reasons)
        if self.match_details:
            html += """
    <div class="section">
        <h2>✓ Match Details</h2>
        <p style="color: #155724; font-size: 14px; margin-bottom: 15px;">
            Detailed reasons for all mapped columns showing matcher type and confidence.
        </p>
        <table>
            <thead>
                <tr>
                    <th>Column</th>
                    <th>Property</th>
                    <th>Match Type</th>
                    <th>Matcher</th>
                    <th>Matched Via</th>
                    <th>Confidence</th>
                </tr>
            </thead>
            <tbody>
"""
            for detail in self.match_details:
                conf_class = "high" if detail.confidence_score >= 0.8 else "medium" if detail.confidence_score >= 0.5 else "low"
                property_short = detail.matched_property.split('#')[-1].split('/')[-1]
                html += f"""
                <tr>
                    <td><strong>{detail.column_name}</strong></td>
                    <td>{property_short}</td>
                    <td><span class="badge badge-{conf_class}">{detail.match_type.value.replace('_', ' ').title()}</span></td>
                    <td>{detail.matcher_name}</td>
                    <td><em>{detail.matched_via}</em></td>
                    <td><span class="confidence confidence-{conf_class}">{detail.confidence_score:.2f}</span></td>
                </tr>
"""
            html += """
            </tbody>
        </table>
    </div>
"""

        # Unmapped columns section
        if self.unmapped_columns:
            html += """
    <div class="section">
        <h2>✗ Unmapped Columns</h2>
        <p style="color: #721c24; font-size: 14px; margin-bottom: 15px;">
            These columns could not be automatically mapped. Manual review required.
        </p>
        <table>
            <thead>
                <tr>
                    <th>Column</th>
                    <th>Data Type</th>
                    <th>Sample Value</th>
                    <th>Reason</th>
                </tr>
            </thead>
            <tbody>
"""
            for col in self.unmapped_columns:
                sample = str(col.sample_values[0]) if col.sample_values else ""
                if len(sample) > 50:
                    sample = sample[:47] + "..."

                html += f"""
                <tr>
                    <td><strong>{col.column_name}</strong></td>
                    <td>{col.inferred_datatype or 'unknown'}</td>
                    <td><code>{sample}</code></td>
                    <td>{col.reason}</td>
                </tr>
"""
            html += """
            </tbody>
        </table>
    </div>
"""

        html += """
    <div class="footer">
        <p>Generated by RDFMap Semantic Alignment System</p>
    </div>
</body>
</html>
"""

        with open(output_path, 'w') as f:
            f.write(html)


def calculate_confidence_score(match_type: MatchType, similarity: float = 1.0) -> float:
    """Calculate confidence score based on match type and similarity.
    
    Args:
        match_type: Type of match that was made
        similarity: Similarity score for fuzzy/semantic matches (0-1)

    Returns:
        Confidence score between 0 and 1
    """
    base_scores = {
        MatchType.EXACT_PREF_LABEL: 1.0,
        MatchType.EXACT_LABEL: 0.95,
        MatchType.EXACT_ALT_LABEL: 0.90,
        MatchType.EXACT_HIDDEN_LABEL: 0.85,
        MatchType.EXACT_LOCAL_NAME: 0.80,
        MatchType.SEMANTIC_SIMILARITY: similarity,  # Use actual embedding similarity
        MatchType.PARTIAL: 0.60,
        MatchType.FUZZY: 0.40,
        MatchType.MANUAL: 1.0,
        MatchType.UNMAPPED: 0.0,
    }
    
    base_score = base_scores.get(match_type, 0.5)
    
    # For fuzzy matches, scale by similarity
    if match_type == MatchType.FUZZY:
        return base_score * similarity
    
    return base_score


def get_confidence_level(score: float) -> ConfidenceLevel:
    """Get categorical confidence level from numeric score.
    
    Args:
        score: Confidence score between 0 and 1
        
    Returns:
        Categorical confidence level
    """
    if score >= 0.8:
        return ConfidenceLevel.HIGH
    elif score >= 0.5:
        return ConfidenceLevel.MEDIUM
    elif score >= 0.3:
        return ConfidenceLevel.LOW
    else:
        return ConfidenceLevel.VERY_LOW
