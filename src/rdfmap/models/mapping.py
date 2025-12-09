"""Pydantic models for mapping configuration schema."""

from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, field_validator, model_validator


class ErrorHandling(str, Enum):
    """Error handling strategies."""

    REPORT = "report"
    FAIL_FAST = "fail-fast"


class TransformType(str, Enum):
    """Built-in transformation types."""

    TO_DECIMAL = "to_decimal"
    TO_INTEGER = "to_integer"
    TO_DATE = "to_date"
    TO_DATETIME = "to_datetime"
    TO_BOOLEAN = "to_boolean"
    UPPERCASE = "uppercase"
    LOWERCASE = "lowercase"
    STRIP = "strip"


class ColumnMapping(BaseModel):
    """Mapping for a single column to an ontology property."""

    as_property: str = Field(..., alias="as", description="Target ontology property IRI or CURIE")
    datatype: Optional[str] = Field(
        None, description="XSD datatype for the value (e.g., xsd:string, xsd:decimal)"
    )
    transform: Optional[Union[str, TransformType]] = Field(
        None, description="Transformation to apply before mapping"
    )
    default: Optional[Any] = Field(None, description="Default value if column is empty")
    required: bool = Field(False, description="Whether this column is required")
    language: Optional[str] = Field(None, description="Language tag for string literals")
    multi_valued: bool = Field(
        False, description="Whether column contains multiple values (comma-separated)"
    )
    delimiter: Optional[str] = Field(None, description="Delimiter for multi-valued columns")

    class Config:
        populate_by_name = True


class ObjectPropertyMapping(BaseModel):
    """Mapping for a linked object (object property)."""

    column: str = Field(..., description="Source column name")
    as_property: str = Field(..., alias="as", description="Target ontology property")
    datatype: Optional[str] = None
    transform: Optional[Union[str, TransformType]] = None
    default: Optional[Any] = None
    required: bool = False
    language: Optional[str] = None

    class Config:
        populate_by_name = True


class LinkedObject(BaseModel):
    """Configuration for creating linked object resources."""

    predicate: str = Field(..., description="Object property linking main resource to this object")
    class_type: Union[str, List[str]] = Field(
        ...,
        alias="class",
        description="RDF class(es) for the linked object. Can be single class or list of classes"
    )
    iri_template: str = Field(..., description="IRI template for generating object IRIs")
    properties: List[ObjectPropertyMapping] = Field(
        default_factory=list, description="Properties of the linked object"
    )

    class Config:
        populate_by_name = True


class RowResource(BaseModel):
    """Configuration for the main resource created from each row."""

    class_type: Union[str, List[str]] = Field(
        ...,
        alias="class",
        description="RDF class(es) for the resource. Can be single class or list of classes (e.g., for owl:NamedIndividual)"
    )
    iri_template: str = Field(..., description="IRI template using column placeholders")

    class Config:
        populate_by_name = True


class SheetMapping(BaseModel):
    """Mapping configuration for a single sheet/file."""

    name: str = Field(..., description="Logical name for this sheet")
    source: str = Field(..., description="Path to CSV/XLSX file (relative or absolute)")
    row_resource: RowResource = Field(..., description="Configuration for main row resource")
    columns: Dict[str, ColumnMapping] = Field(
        default_factory=dict, description="Column to property mappings"
    )
    objects: Dict[str, LinkedObject] = Field(
        default_factory=dict, description="Linked object configurations"
    )
    iterator: Optional[str] = Field(
        None, description="XPath/JSONPath iterator for XML/JSON data sources"
    )
    format: Optional[str] = Field(
        None, description="Data format (csv, json, xml) - auto-detected if not specified"
    )
    filter_condition: Optional[str] = Field(
        None, description="Optional condition to filter rows (not implemented in v1)"
    )


class SHACLValidationConfig(BaseModel):
    """SHACL validation configuration."""

    enabled: bool = Field(True, description="Whether to run SHACL validation")
    shapes_file: str = Field(..., description="Path to SHACL shapes file")
    inference: Optional[str] = Field(None, description="Inference mode (rdfs, owlrl, both)")


class ValidationConfig(BaseModel):
    """Validation configuration."""

    shacl: Optional[SHACLValidationConfig] = None


class ProcessingOptions(BaseModel):
    """Processing options."""

    delimiter: str = Field(",", description="CSV delimiter")
    header: bool = Field(True, description="Whether CSV has header row")
    on_error: ErrorHandling = Field(
        ErrorHandling.REPORT, description="Error handling strategy"
    )
    skip_empty_values: bool = Field(True, description="Skip columns with empty values")
    chunk_size: int = Field(1000, description="Number of rows to process at a time")
    aggregate_duplicates: bool = Field(
        True, description="Aggregate triples with duplicate IRIs (improves readability but has performance cost)"
    )
    output_format: Optional[str] = Field(
        None, description="Default output format (ttl, nt, xml, jsonld)"
    )


class DefaultsConfig(BaseModel):
    """Default configuration values."""

    base_iri: str = Field(..., description="Base IRI for resource generation")
    language: Optional[str] = Field(None, description="Default language tag")


class MappingConfig(BaseModel):
    """Root mapping configuration schema.

    Supports two modes:
    1. Inline mapping: Full configuration with sheets defined inline
    2. External mapping: Reference to external RML/YARRRML file with config options

    When using external mapping file, the 'sheets' field is populated from the referenced file.
    """

    namespaces: Dict[str, str] = Field(
        ..., description="Namespace prefix to IRI mappings"
    )
    imports: Optional[List[str]] = Field(
        None, description="List of ontology files to import (file paths or URIs)"
    )
    defaults: DefaultsConfig = Field(..., description="Default configuration values")

    # Either sheets OR mapping_file must be provided
    sheets: Optional[List[SheetMapping]] = Field(
        None, description="Sheet/file mappings (inline mode)"
    )
    mapping_file: Optional[str] = Field(
        None,
        description="Path to external RML or YARRRML mapping file (external mode)"
    )

    validation: Optional[ValidationConfig] = Field(None, description="Validation configuration")
    options: ProcessingOptions = Field(
        default_factory=ProcessingOptions, description="Processing options"
    )

    @field_validator("namespaces")
    @classmethod
    def validate_namespaces(cls, v: Dict[str, str]) -> Dict[str, str]:
        """Ensure required namespaces are present."""
        required = {"xsd"}
        missing = required - set(v.keys())
        if missing:
            raise ValueError(f"Missing required namespaces: {missing}")
        return v

    @model_validator(mode="after")
    def validate_sheets_or_mapping_file(self) -> "MappingConfig":
        """Ensure either sheets or mapping_file is provided, but not both."""
        has_sheets = self.sheets is not None and len(self.sheets) > 0
        has_mapping_file = self.mapping_file is not None

        if not has_sheets and not has_mapping_file:
            raise ValueError("Either 'sheets' (inline mapping) or 'mapping_file' (external mapping) must be provided")

        if has_sheets and has_mapping_file:
            raise ValueError("Cannot specify both 'sheets' and 'mapping_file'. Use one or the other.")

        return self

    @model_validator(mode="after")
    def validate_iri_templates(self) -> "MappingConfig":
        """Validate that IRI templates reference valid columns."""
        if self.sheets:
            for sheet in self.sheets:
                # Collect all available column names
                available_cols = set(sheet.columns.keys())

                # Add columns referenced in objects
                for obj in sheet.objects.values():
                    for prop in obj.properties:
                        available_cols.add(prop.column)

                # Note: Full validation of template variables would require parsing
                # the actual data, so we do basic checks here
        return self

    class Config:
        use_enum_values = True
