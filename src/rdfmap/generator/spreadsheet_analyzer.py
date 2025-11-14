"""Spreadsheet analyzer for extracting column patterns and data types."""

from typing import Dict, List, Optional, Any
from pathlib import Path
import polars as pl
import re

# Import Polars helper functions
from .polars_helpers import (_infer_polars_type, _suggest_xsd_datatype_polars,
                           _is_likely_identifier_polars, _detect_pattern_polars)


class ColumnAnalysis:
    """Analysis results for a single column."""
    
    def __init__(self, name: str):
        self.name = name
        self.sample_values: List[Any] = []
        self.null_count: int = 0
        self.total_count: int = 0
        self.inferred_type: Optional[str] = None
        self.is_identifier: bool = False
        self.is_unique: bool = False
        self.suggested_datatype: Optional[str] = None
        self.pattern: Optional[str] = None
    
    @property
    def null_percentage(self) -> float:
        """Calculate percentage of null values."""
        if self.total_count == 0:
            return 0.0
        return (self.null_count / self.total_count) * 100
    
    @property
    def is_required(self) -> bool:
        """Suggest if this field should be required (< 10% null)."""
        return self.null_percentage < 10
    
    def __repr__(self):
        return (
            f"ColumnAnalysis({self.name}, type={self.inferred_type}, "
            f"null_pct={self.null_percentage:.1f}%, unique={self.is_unique})"
        )


class SpreadsheetAnalyzer:
    """Analyzes a spreadsheet to extract patterns for mapping generation."""
    
    def __init__(self, file_path: str, sample_size: int = 100):
        """
        Initialize the analyzer with a spreadsheet file.
        
        Args:
            file_path: Path to CSV or Excel file
            sample_size: Number of rows to analyze
        """
        self.file_path = Path(file_path)
        self.sample_size = sample_size
        self.df: Optional[pl.DataFrame] = None
        self.columns: Dict[str, ColumnAnalysis] = {}
        
        self._load_and_analyze()
    
    def _load_and_analyze(self):
        """Load the spreadsheet and perform analysis."""
        # Load data using Polars
        if self.file_path.suffix.lower() in [".xlsx", ".xls"]:
            self.df = pl.read_excel(self.file_path).head(self.sample_size)
        elif self.file_path.suffix.lower() == ".csv":
            self.df = pl.read_csv(self.file_path, n_rows=self.sample_size)
        else:
            raise ValueError(f"Unsupported file format: {self.file_path.suffix}")
        
        # Analyze each column
        for col_name in self.df.columns:
            self.columns[col_name] = self._analyze_column(col_name)
    
    def _analyze_column(self, col_name: str) -> ColumnAnalysis:
        """Analyze a single column."""
        analysis = ColumnAnalysis(col_name)

        column = self.df[col_name]
        analysis.total_count = len(self.df)
        analysis.null_count = column.null_count()

        # Get non-null values
        non_null = column.drop_nulls()
        if len(non_null) == 0:
            return analysis
        
        # Sample values (up to 5)
        analysis.sample_values = non_null.head(5).to_list()

        # Check uniqueness
        analysis.is_unique = non_null.n_unique() == len(non_null)

        # Use imported Polars helper functions
        analysis.inferred_type = _infer_polars_type(column)
        analysis.suggested_datatype = _suggest_xsd_datatype_polars(column)
        analysis.is_identifier = _is_likely_identifier_polars(col_name, column)

        # Extract pattern for strings
        if analysis.inferred_type == "string":
            analysis.pattern = _detect_pattern_polars(column)

        return analysis
    

    def get_identifier_columns(self) -> List[ColumnAnalysis]:
        """Get columns that look like identifiers."""
        return [col for col in self.columns.values() if col.is_identifier]
    
    def get_required_columns(self) -> List[ColumnAnalysis]:
        """Get columns that should probably be required."""
        return [col for col in self.columns.values() if col.is_required]
    
    def suggest_iri_template_columns(self) -> List[str]:
        """Suggest columns to use in IRI template."""
        # Prefer unique identifier columns
        id_cols = self.get_identifier_columns()
        if id_cols:
            return [col.name for col in id_cols]
        
        # Fall back to first column
        if self.columns:
            return [next(iter(self.columns.keys()))]
        
        return []
    
    def get_column_names(self) -> List[str]:
        """Get list of all column names."""
        return list(self.columns.keys())
    
    def get_analysis(self, col_name: str) -> Optional[ColumnAnalysis]:
        """Get analysis for a specific column."""
        return self.columns.get(col_name)
    
    def summary(self) -> str:
        """Generate a summary report."""
        lines = [
            f"Spreadsheet Analysis: {self.file_path.name}",
            f"Rows analyzed: {len(self.df)}",
            f"Columns: {len(self.columns)}",
            "",
            "Column Details:",
        ]
        
        for col in self.columns.values():
            lines.append(
                f"  - {col.name}: {col.inferred_type}, "
                f"null={col.null_percentage:.1f}%, "
                f"unique={col.is_unique}, "
                f"suggested_type={col.suggested_datatype}"
            )
        
        id_cols = self.get_identifier_columns()
        if id_cols:
            lines.append("")
            lines.append("Suggested Identifier Columns:")
            for col in id_cols:
                lines.append(f"  - {col.name}")
        
        return "\n".join(lines)
