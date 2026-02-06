"""
RDFMap Configuration Models - v3 (Universal Format)

Aligned with RML/YARRRML standards while adding RDFMap enhancements.
Supports: CSV, JSON, XML, SQL databases, APIs, and any RML-compatible source.
"""

from typing import Dict, List, Optional, Union, Any
from pydantic import BaseModel, Field, field_validator
from enum import Enum


class TransformType(str, Enum):
    """Data transformation functions."""
    TO_INTEGER = "to_integer"
    TO_DECIMAL = "to_decimal"
    TO_FLOAT = "to_float"
    TO_DATE = "to_date"
    TO_DATETIME = "to_datetime"
    TO_BOOLEAN = "to_boolean"
    TO_UPPER = "to_upper"
    TO_LOWER = "to_lower"
    STRIP = "strip"


class DataSource(BaseModel):
    """Universal data source definition.

    Supports:
    - Files: CSV, TSV, JSON, XML, Excel
    - Databases: SQL queries
    - APIs: HTTP endpoints
    """

    path: str = Field(..., description="File path, connection string, or URL")
    format: str = Field(..., description="Data format: csv, json, xml, xlsx, sql, etc.")
    iterator: Optional[str] = Field(
        None,
        description="Data selector: JSONPath ($.path), XPath (//element), or SQL query"
    )

    class Config:
        populate_by_name = True


class SubjectDefinition(BaseModel):
    """RDF subject configuration (RML standard)."""

    iri_template: str = Field(..., description="IRI template with {column} placeholders")
    class_type: Union[str, List[str]] = Field(
        ...,
        alias="class",
        description="RDF class(es). Can be single or list (e.g., [ex:Person, owl:NamedIndividual])"
    )

    class Config:
        populate_by_name = True


class PropertyMapping(BaseModel):
    """Data property (literal) mapping."""

    predicate: str = Field(..., description="RDF predicate (property)")
    datatype: Optional[str] = Field(None, description="XSD datatype (e.g., xsd:string, xsd:integer)")
    language: Optional[str] = Field(None, description="Language tag for string literals (e.g., 'en', 'fr')")
    transform: Optional[Union[str, TransformType]] = Field(
        None,
        description="Data transformation function"
    )
    default: Optional[Any] = Field(None, description="Default value if column is empty")
    required: bool = Field(False, description="Whether this property is required")

    class Config:
        populate_by_name = True


class NestedEntityDefinition(BaseModel):
    """Definition for a nested/linked entity."""

    iri_template: str = Field(..., description="IRI template for the nested entity")
    class_type: Union[str, List[str]] = Field(
        ...,
        alias="class",
        description="RDF class(es) for the nested entity"
    )
    properties: Dict[str, PropertyMapping] = Field(
        default_factory=dict,
        description="Properties of the nested entity"
    )

    class Config:
        populate_by_name = True


class RelationshipMapping(BaseModel):
    """Object property (relationship) mapping."""

    predicate: str = Field(..., description="Object property predicate")
    object: NestedEntityDefinition = Field(..., description="Definition of the linked entity")

    class Config:
        populate_by_name = True


class EntityMapping(BaseModel):
    """Mapping definition for one entity type."""

    sources: Union[str, List[str]] = Field(
        ...,
        description="Reference to data source(s) defined in 'sources' section"
    )
    subject: SubjectDefinition = Field(..., description="Subject (main resource) configuration")
    properties: Dict[str, PropertyMapping] = Field(
        default_factory=dict,
        description="Data properties (literals) keyed by source column/field name"
    )
    relationships: Optional[Dict[str, RelationshipMapping]] = Field(
        default_factory=dict,
        description="Object properties (relationships to other entities)"
    )
    condition: Optional[str] = Field(
        None,
        description="Optional filter condition (not implemented yet)"
    )

    class Config:
        populate_by_name = True


class SHACLValidationConfig(BaseModel):
    """SHACL validation configuration."""

    enabled: bool = Field(True, description="Enable SHACL validation")
    shapes_file: Optional[str] = Field(None, description="Path to SHACL shapes file")
    inference: str = Field("none", description="Inference mode: none, rdfs, owl")

    class Config:
        populate_by_name = True


class ValidationConfig(BaseModel):
    """Validation configuration."""

    shacl: Optional[SHACLValidationConfig] = None

    class Config:
        populate_by_name = True


class ProcessingOptions(BaseModel):
    """Data processing options."""

    on_error: str = Field("report", description="Error handling: report, skip, fail")
    skip_empty_values: bool = Field(True, description="Skip properties with empty values")
    chunk_size: int = Field(1000, description="Chunk size for processing large datasets")
    aggregate_duplicates: bool = Field(True, description="Aggregate duplicate resources")
    output_format: str = Field("ttl", description="Output format: ttl, nt, xml, jsonld")
    delimiter: Optional[str] = Field(None, description="CSV delimiter (auto-detected if not specified)")
    header: bool = Field(True, description="Whether data has header row")

    class Config:
        populate_by_name = True


class Defaults(BaseModel):
    """Default values."""

    base_iri: str = Field(..., description="Base IRI for generated resources")

    class Config:
        populate_by_name = True


class MappingConfig(BaseModel):
    """Root RDFMap configuration - v3 Universal Format.

    Aligned with RML/YARRRML standards with RDFMap enhancements.
    """

    # Core RML/YARRRML structure
    namespaces: Dict[str, str] = Field(
        default_factory=dict,
        description="Namespace prefix mappings"
    )
    base_iri: str = Field(..., description="Base IRI for generated resources")
    sources: Dict[str, DataSource] = Field(
        ...,
        description="Data source definitions (files, databases, APIs)"
    )
    mappings: Dict[str, EntityMapping] = Field(
        ...,
        description="Entity mapping definitions"
    )

    # RDFMap enhancements (optional)
    validation: Optional[ValidationConfig] = Field(
        None,
        description="Validation configuration"
    )
    options: Optional[ProcessingOptions] = Field(
        default_factory=ProcessingOptions,
        description="Processing options"
    )
    imports: Optional[List[str]] = Field(
        default_factory=list,
        description="Ontology files to import"
    )

    # Backward compatibility (deprecated)
    defaults: Optional[Defaults] = Field(
        None,
        description="DEPRECATED: Use base_iri at root level instead"
    )

    @field_validator("namespaces")
    @classmethod
    def validate_namespaces(cls, v):
        """Ensure standard namespaces are present."""
        defaults = {
            'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
            'rdfs': 'http://www.w3.org/2000/01/rdf-schema#',
            'xsd': 'http://www.w3.org/2001/XMLSchema#',
        }
        for prefix, uri in defaults.items():
            if prefix not in v:
                v[prefix] = uri
        return v

    def model_post_init(self, __context):
        """Post-initialization processing."""
        # Handle deprecated 'defaults' field
        if self.defaults and not hasattr(self, '_base_iri_set'):
            if not self.base_iri or self.base_iri == "http://example.org/":
                self.base_iri = self.defaults.base_iri

    class Config:
        populate_by_name = True
        extra = "forbid"  # Strict mode - no extra fields allowed

