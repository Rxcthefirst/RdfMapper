"""Data models for processing errors and validation reports."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ErrorSeverity(str, Enum):
    """Error severity levels."""

    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ProcessingError(BaseModel):
    """Error that occurred during data processing."""

    row: Optional[int] = Field(None, description="Row number where error occurred")
    column: Optional[str] = Field(None, description="Column name")
    error: str = Field(..., description="Error message")
    severity: ErrorSeverity = Field(ErrorSeverity.ERROR, description="Error severity")
    value: Optional[Any] = Field(None, description="The problematic value")
    timestamp: datetime = Field(default_factory=datetime.now, description="When error occurred")


class ProcessingReport(BaseModel):
    """Report of processing execution."""

    total_rows: int = Field(0, description="Total number of rows processed")
    successful_rows: int = Field(0, description="Successfully processed rows")
    failed_rows: int = Field(0, description="Failed rows")
    warnings: int = Field(0, description="Number of warnings")
    errors: List[ProcessingError] = Field(default_factory=list, description="All errors")
    start_time: datetime = Field(default_factory=datetime.now, description="Processing start time")
    end_time: Optional[datetime] = Field(None, description="Processing end time")
    
    def add_error(
        self,
        error: str,
        row: Optional[int] = None,
        column: Optional[str] = None,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        value: Optional[Any] = None,
    ) -> None:
        """Add an error to the report."""
        self.errors.append(
            ProcessingError(
                row=row,
                column=column,
                error=error,
                severity=severity,
                value=value,
            )
        )
        if severity == ErrorSeverity.WARNING:
            self.warnings += 1
        else:
            self.failed_rows += 1
    
    def finalize(self) -> None:
        """Finalize the report."""
        self.end_time = datetime.now()
        self.successful_rows = self.total_rows - self.failed_rows


class ValidationResult(BaseModel):
    """SHACL validation result."""

    focus_node: str = Field(..., description="The node being validated")
    result_path: Optional[str] = Field(None, description="The property path")
    result_message: str = Field(..., description="Validation message")
    severity: str = Field(..., description="Violation, Warning, or Info")
    source_constraint: Optional[str] = Field(None, description="The constraint that was violated")


class ValidationReport(BaseModel):
    """SHACL validation report."""

    conforms: bool = Field(..., description="Whether the data conforms to shapes")
    results: List[ValidationResult] = Field(
        default_factory=list, description="Validation results"
    )
    results_graph: Optional[str] = Field(
        None, description="Full validation graph in Turtle format"
    )
