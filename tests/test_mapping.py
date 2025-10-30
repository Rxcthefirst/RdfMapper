"""Tests for mapping configuration parsing."""

import pytest
from pathlib import Path

from rdfmap.models.mapping import (
    MappingConfig,
    ColumnMapping,
    LinkedObject,
    RowResource,
    SheetMapping,
    DefaultsConfig,
    ProcessingOptions,
    ErrorHandling,
)


class TestColumnMapping:
    """Tests for ColumnMapping model."""
    
    def test_basic_column_mapping(self):
        mapping = ColumnMapping(
            **{"as": "ex:loanNumber", "datatype": "xsd:string"}
        )
        assert mapping.as_property == "ex:loanNumber"
        assert mapping.datatype == "xsd:string"
    
    def test_column_mapping_with_transform(self):
        mapping = ColumnMapping(
            **{"as": "ex:amount", "datatype": "xsd:decimal", "transform": "to_decimal"}
        )
        assert mapping.transform == "to_decimal"
    
    def test_column_mapping_with_default(self):
        mapping = ColumnMapping(
            **{"as": "ex:status", "datatype": "xsd:string", "default": "Active"}
        )
        assert mapping.default == "Active"
    
    def test_multi_valued_column(self):
        mapping = ColumnMapping(
            **{
                "as": "ex:tags",
                "datatype": "xsd:string",
                "multi_valued": True,
                "delimiter": ";"
            }
        )
        assert mapping.multi_valued is True
        assert mapping.delimiter == ";"


class TestLinkedObject:
    """Tests for LinkedObject model."""
    
    def test_linked_object(self):
        obj = LinkedObject(
            predicate="ex:hasBorrower",
            **{
                "class": "ex:Borrower",
                "iri_template": "{base_iri}borrower/{BorrowerID}",
                "properties": [
                    {
                        "column": "BorrowerName",
                        "as": "ex:borrowerName",
                        "datatype": "xsd:string"
                    }
                ]
            }
        )
        assert obj.predicate == "ex:hasBorrower"
        assert obj.class_type == "ex:Borrower"
        assert len(obj.properties) == 1


class TestSheetMapping:
    """Tests for SheetMapping model."""
    
    def test_complete_sheet_mapping(self):
        sheet = SheetMapping(
            name="loans",
            source="data/loans.csv",
            row_resource=RowResource(
                **{"class": "ex:MortgageLoan", "iri_template": "{base_iri}loan/{LoanID}"}
            ),
            columns={
                "LoanID": ColumnMapping(**{"as": "ex:loanNumber", "datatype": "xsd:string"})
            },
            objects={
                "borrower": LinkedObject(
                    predicate="ex:hasBorrower",
                    **{
                        "class": "ex:Borrower",
                        "iri_template": "{base_iri}borrower/{BorrowerID}",
                        "properties": []
                    }
                )
            }
        )
        assert sheet.name == "loans"
        assert sheet.source == "data/loans.csv"
        assert "LoanID" in sheet.columns
        assert "borrower" in sheet.objects


class TestMappingConfig:
    """Tests for complete MappingConfig."""
    
    def test_valid_mapping_config(self):
        config = MappingConfig(
            namespaces={
                "ex": "https://example.com/mortgage#",
                "xsd": "http://www.w3.org/2001/XMLSchema#"
            },
            defaults=DefaultsConfig(base_iri="https://data.example.com/"),
            sheets=[
                SheetMapping(
                    name="loans",
                    source="data/loans.csv",
                    row_resource=RowResource(
                        **{"class": "ex:MortgageLoan", "iri_template": "{base_iri}loan/{LoanID}"}
                    ),
                    columns={},
                    objects={}
                )
            ]
        )
        assert "ex" in config.namespaces
        assert "xsd" in config.namespaces
        assert config.defaults.base_iri == "https://data.example.com/"
        assert len(config.sheets) == 1
    
    def test_missing_required_namespace(self):
        with pytest.raises(ValueError, match="Missing required namespaces"):
            MappingConfig(
                namespaces={"ex": "https://example.com/mortgage#"},  # Missing 'xsd'
                defaults=DefaultsConfig(base_iri="https://data.example.com/"),
                sheets=[]
            )
    
    def test_error_handling_enum(self):
        config = MappingConfig(
            namespaces={
                "ex": "https://example.com/mortgage#",
                "xsd": "http://www.w3.org/2001/XMLSchema#"
            },
            defaults=DefaultsConfig(base_iri="https://data.example.com/"),
            sheets=[],
            options=ProcessingOptions(on_error="fail-fast")
        )
        assert config.options.on_error == "fail-fast"
