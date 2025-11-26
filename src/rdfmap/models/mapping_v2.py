"""New configuration models with improved structure.

This module contains the new, cleaner configuration structure with:
- Clear separation between pipeline config and mapping definition
- RML-aligned terminology
- Source-agnostic naming (sources instead of sheets)
- Better property names (predicate instead of as, entity instead of row_resource)

The old models in mapping.py are kept for backward compatibility.
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, field_validator, model_validator


# ═══════════════════════════════════════════════════════════════════════════
# Pipeline Configuration Models
# ═══════════════════════════════════════════════════════════════════════════

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
        True, description="Aggregate triples with duplicate IRIs"
    )
    output_format: Optional[str] = Field(
        None, description="Default output format (ttl, nt, xml, jsonld)"
    )

    class Config:
        use_enum_values = True


# ═══════════════════════════════════════════════════════════════════════════
# Mapping Definition Models (RML-aligned)
# ═══════════════════════════════════════════════════════════════════════════

class PropertyMapping(BaseModel):
    """Property (predicate-object) mapping.

    Maps a data field to an RDF predicate with optional datatype and transforms.
    """
    predicate: str = Field(..., description="RDF predicate (property) IRI or CURIE")
    datatype: Optional[str] = Field(
        None, description="XSD datatype (e.g., xsd:string, xsd:decimal)"
    )
    transform: Optional[Union[str, TransformType]] = Field(
        None, description="Transformation to apply before mapping"
    )
    default: Optional[Any] = Field(None, description="Default value if field is empty")
    required: bool = Field(False, description="Whether this field is required")
    language: Optional[str] = Field(None, description="Language tag for string literals")
    multi_valued: bool = Field(
        False, description="Whether field contains multiple values"
    )
    delimiter: Optional[str] = Field(None, description="Delimiter for multi-valued fields")


class EntityMapping(BaseModel):
    """Entity (subject) mapping.

    Defines how to create the main RDF resource (subject) from each data record.
    Corresponds to rr:SubjectMap in RML.
    """
    class_: str = Field(..., alias="class", description="RDF class for the entity")
    iri_template: str = Field(
        ..., description="IRI template using field placeholders (e.g., {base_iri}loan/{ID})"
    )

    class Config:
        populate_by_name = True


class RelationshipMapping(BaseModel):
    """Relationship (object property) mapping.

    Defines how to create linked RDF resources via object properties.
    Corresponds to rr:PredicateObjectMap with rr:parentTriplesMap in RML.
    """
    predicate: str = Field(..., description="Object property predicate")
    class_: str = Field(..., alias="class", description="RDF class for the linked resource")
    iri_template: str = Field(..., description="IRI template for the linked resource")
    properties: Dict[str, PropertyMapping] = Field(
        default_factory=dict, description="Properties of the linked resource"
    )

    class Config:
        populate_by_name = True


class SourceMapping(BaseModel):
    """Mapping for a single data source.

    Represents one logical source (rml:LogicalSource) with its subject and predicate-object maps.
    Works for CSV, JSON, XML, databases, APIs, etc.
    """
    name: str = Field(..., description="Logical name for this source")
    file: str = Field(..., description="Path to data file or connection string")
    format: str = Field(..., description="Data format: csv, json, xml, xlsx, etc.")

    # Optional source-specific settings
    iterator: Optional[str] = Field(
        None, description="Iterator expression (e.g., JSONPath for JSON)"
    )

    # Entity mapping (subject map)
    entity: EntityMapping = Field(..., description="How to create the main resource")

    # Property mappings (predicate-object maps)
    properties: Dict[str, PropertyMapping] = Field(
        default_factory=dict, description="Data field to RDF property mappings"
    )

    # Relationship mappings (object property maps with joins)
    relationships: Optional[List[RelationshipMapping]] = Field(
        None, description="Linked resource definitions"
    )

    # Filter condition
    filter_condition: Optional[str] = Field(
        None, description="Optional condition to filter records"
    )


class MappingDefinition(BaseModel):
    """RML-compatible mapping definition.

    Contains all RML concepts grouped together: namespaces, base IRI, and sources.
    Supports both inline mapping and external file reference.
    """

    # Option 1: Inline mapping
    namespaces: Optional[Dict[str, str]] = Field(
        None, description="Namespace prefix to IRI mappings (RML: prefixes)"
    )
    base_iri: Optional[str] = Field(
        None, description="Base IRI for resource generation (RML: base)"
    )
    sources: Optional[List[SourceMapping]] = Field(
        None, description="Data sources with their mappings (RML: sources + mappings)"
    )

    # Option 2: External reference
    file: Optional[str] = Field(
        None, description="Path to external RML or YARRRML file"
    )

    @model_validator(mode="after")
    def validate_inline_or_file(self) -> "MappingDefinition":
        """Ensure either inline mapping or file reference is provided, but not both."""
        has_inline = bool(self.sources)
        has_file = bool(self.file)

        if not has_inline and not has_file:
            raise ValueError(
                "mapping must have either 'sources' (inline) or 'file' (external reference)"
            )

        if has_inline and has_file:
            raise ValueError(
                "mapping cannot have both 'sources' and 'file'. Use one or the other."
            )

        # If inline, validate namespaces and base_iri are provided
        if has_inline:
            if not self.namespaces:
                raise ValueError("mapping.namespaces is required for inline mappings")
            if 'xsd' not in self.namespaces:
                raise ValueError("mapping.namespaces must include 'xsd' prefix")
            if not self.base_iri:
                raise ValueError("mapping.base_iri is required for inline mappings")

        return self


# ═══════════════════════════════════════════════════════════════════════════
# Root Configuration Model
# ═══════════════════════════════════════════════════════════════════════════

class MappingConfigV2(BaseModel):
    """Root configuration with clean two-section structure.

    Section 1: Pipeline Configuration (how to execute)
    - validation: SHACL validation settings
    - options: Processing options
    - imports: Ontology files to load

    Section 2: Mapping Definition (what to transform)
    - mapping: RML-compatible mapping structure

    This is the new, improved structure. The old structure in MappingConfig
    is maintained for backward compatibility.
    """

    # Pipeline Configuration (RDFMap-specific)
    validation: Optional[ValidationConfig] = Field(
        None, description="SHACL validation configuration"
    )
    options: ProcessingOptions = Field(
        default_factory=ProcessingOptions, description="Processing options"
    )
    imports: Optional[List[str]] = Field(
        None, description="Ontology files to import (for validation)"
    )

    # Mapping Definition (RML-compatible)
    mapping: MappingDefinition = Field(..., description="Mapping definition")

    class Config:
        use_enum_values = True

