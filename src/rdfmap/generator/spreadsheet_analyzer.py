"""Spreadsheet analyzer for extracting column patterns and data types."""

from typing import Dict, List, Set, Optional, Tuple, Any
from pathlib import Path
import pandas as pd
from collections import Counter
import re


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
            sample_size: Number of rows to analyze (for performance)
        """
        self.file_path = Path(file_path)
        self.sample_size = sample_size
        self.df: Optional[pd.DataFrame] = None
        self.columns: Dict[str, ColumnAnalysis] = {}
        
        self._load_and_analyze()
    
    def _load_and_analyze(self):
        """Load the spreadsheet and perform analysis."""
        # Load data
        if self.file_path.suffix.lower() in [".xlsx", ".xls"]:
            self.df = pd.read_excel(self.file_path, nrows=self.sample_size)
        elif self.file_path.suffix.lower() == ".csv":
            self.df = pd.read_csv(self.file_path, nrows=self.sample_size)
        else:
            raise ValueError(f"Unsupported file format: {self.file_path.suffix}")
        
        # Analyze each column
        for col_name in self.df.columns:
            self.columns[col_name] = self._analyze_column(col_name)
    
    def _analyze_column(self, col_name: str) -> ColumnAnalysis:
        """Analyze a single column."""
        analysis = ColumnAnalysis(col_name)
        
        series = self.df[col_name]
        analysis.total_count = len(series)
        analysis.null_count = series.isna().sum()
        
        # Get non-null values
        non_null = series.dropna()
        if len(non_null) == 0:
            return analysis
        
        # Sample values (up to 5)
        analysis.sample_values = non_null.head(5).tolist()
        
        # Check uniqueness
        analysis.is_unique = len(non_null.unique()) == len(non_null)
        
        # Infer Python type
        analysis.inferred_type = self._infer_python_type(non_null)
        
        # Suggest XSD datatype
        analysis.suggested_datatype = self._suggest_xsd_datatype(non_null, col_name)
        
        # Check if this looks like an identifier
        analysis.is_identifier = self._is_identifier_column(col_name, non_null)
        
        # Extract pattern (for strings)
        if analysis.inferred_type == "string":
            analysis.pattern = self._extract_pattern(non_null)
        
        return analysis
    
    def _infer_python_type(self, series: pd.Series) -> str:
        """Infer the Python type of a series."""
        dtype = series.dtype
        
        if pd.api.types.is_integer_dtype(dtype):
            return "integer"
        elif pd.api.types.is_float_dtype(dtype):
            return "float"
        elif pd.api.types.is_bool_dtype(dtype):
            return "boolean"
        elif pd.api.types.is_datetime64_any_dtype(dtype):
            return "datetime"
        else:
            # Try to parse as date
            if self._looks_like_date(series):
                return "date"
            return "string"
    
    def _looks_like_date(self, series: pd.Series) -> bool:
        """Check if a string series looks like dates."""
        # Sample a few values
        sample = series.head(10)
        date_count = 0
        
        for val in sample:
            if pd.isna(val):
                continue
            try:
                pd.to_datetime(val)
                date_count += 1
            except (ValueError, TypeError):
                pass
        
        # If more than 80% parse as dates, it's probably a date column
        return date_count > len(sample) * 0.8
    
    def _suggest_xsd_datatype(self, series: pd.Series, col_name: str) -> str:
        """Suggest an XSD datatype based on column analysis."""
        inferred = self._infer_python_type(series)
        
        if inferred == "integer":
            return "xsd:integer"
        elif inferred == "float":
            # Check if it's a decimal (e.g., money, rates)
            if any(term in col_name.lower() for term in ["amount", "price", "rate", "balance", "principal"]):
                return "xsd:decimal"
            return "xsd:double"
        elif inferred == "boolean":
            return "xsd:boolean"
        elif inferred == "datetime":
            return "xsd:dateTime"
        elif inferred == "date":
            return "xsd:date"
        else:
            # String - check for URI patterns
            if self._looks_like_uri(series):
                return "xsd:anyURI"
            return "xsd:string"
    
    def _looks_like_uri(self, series: pd.Series) -> bool:
        """Check if values look like URIs."""
        sample = series.head(10)
        uri_pattern = re.compile(r'^https?://')
        
        uri_count = sum(1 for val in sample if pd.notna(val) and uri_pattern.match(str(val)))
        return uri_count > len(sample) * 0.8
    
    def _is_identifier_column(self, col_name: str, series: pd.Series) -> bool:
        """Determine if a column is likely an identifier."""
        name_lower = col_name.lower()
        
        # Check for ID-like names
        id_patterns = ["id", "code", "key", "number", "identifier"]
        has_id_name = any(pattern in name_lower for pattern in id_patterns)
        
        # Check uniqueness
        is_unique = len(series.unique()) == len(series)
        
        return has_id_name or is_unique
    
    def _extract_pattern(self, series: pd.Series) -> Optional[str]:
        """Extract common pattern from string values."""
        # Sample first few values
        sample = [str(val) for val in series.head(10) if pd.notna(val)]
        
        if not sample:
            return None
        
        # Look for common patterns
        if all(val.isdigit() for val in sample):
            return "numeric_string"
        
        if all(re.match(r'^[A-Z]+\d+$', val) for val in sample):
            return "alphanumeric_code"
        
        if all('@' in val for val in sample):
            return "email"
        
        return None
    
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
