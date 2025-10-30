"""Tests for IRI generation and templating."""

import pytest

from rdfmap.iri.generator import (
    IRITemplate,
    validate_iri,
    curie_to_iri,
    iri_to_curie,
)


class TestIRITemplate:
    """Tests for IRITemplate class."""
    
    def test_simple_template(self):
        template = IRITemplate(
            "https://example.com/resource/{id}",
            base_iri="https://example.com/"
        )
        result = template.render({"id": "123"})
        assert result == "https://example.com/resource/123"
    
    def test_multiple_variables(self):
        template = IRITemplate(
            "{base_iri}{type}/{id}",
            base_iri="https://example.com/"
        )
        result = template.render({"type": "loan", "id": "L-1001"})
        assert result == "https://example.com/loan/L-1001"
    
    def test_base_iri_substitution(self):
        template = IRITemplate(
            "{base_iri}resource/{id}",
            base_iri="https://data.example.com/"
        )
        result = template.render({"id": "456"})
        assert result == "https://data.example.com/resource/456"
    
    def test_extract_variables(self):
        template = IRITemplate(
            "{base_iri}loan/{LoanID}/borrower/{BorrowerID}",
            base_iri="https://example.com/"
        )
        variables = template.variables
        assert "LoanID" in variables
        assert "BorrowerID" in variables
        assert "base_iri" in variables
    
    def test_missing_variable(self):
        template = IRITemplate(
            "https://example.com/{type}/{id}",
            base_iri="https://example.com/"
        )
        with pytest.raises(ValueError, match="Missing required variables"):
            template.render({"type": "loan"})  # Missing 'id'
    
    def test_url_encoding(self):
        template = IRITemplate(
            "https://example.com/resource/{name}",
            base_iri="https://example.com/"
        )
        result = template.render({"name": "hello world"})
        assert "hello%20world" in result


class TestValidateIRI:
    """Tests for validate_iri function."""
    
    def test_valid_http_iri(self):
        assert validate_iri("https://example.com/resource/123") is True
    
    def test_valid_custom_scheme(self):
        assert validate_iri("urn:isbn:0-486-27557-4") is True
    
    def test_invalid_iri_no_scheme(self):
        assert validate_iri("example.com/resource") is False
    
    def test_invalid_iri_empty(self):
        assert validate_iri("") is False


class TestCurieConversion:
    """Tests for CURIE to IRI conversion."""
    
    def test_curie_to_iri(self):
        namespaces = {
            "ex": "https://example.com/mortgage#",
            "xsd": "http://www.w3.org/2001/XMLSchema#"
        }
        
        result = curie_to_iri("ex:MortgageLoan", namespaces)
        assert result == "https://example.com/mortgage#MortgageLoan"
    
    def test_curie_to_iri_unknown_prefix(self):
        namespaces = {"ex": "https://example.com/mortgage#"}
        
        with pytest.raises(ValueError, match="Unknown namespace prefix"):
            curie_to_iri("unknown:Class", namespaces)
    
    def test_curie_to_iri_invalid_format(self):
        namespaces = {"ex": "https://example.com/mortgage#"}
        
        with pytest.raises(ValueError, match="Invalid CURIE format"):
            curie_to_iri("nocolon", namespaces)
    
    def test_iri_to_curie(self):
        namespaces = {
            "ex": "https://example.com/mortgage#",
            "xsd": "http://www.w3.org/2001/XMLSchema#"
        }
        
        result = iri_to_curie("https://example.com/mortgage#MortgageLoan", namespaces)
        assert result == "ex:MortgageLoan"
    
    def test_iri_to_curie_no_match(self):
        namespaces = {"ex": "https://example.com/mortgage#"}
        
        iri = "https://other.com/Class"
        result = iri_to_curie(iri, namespaces)
        assert result == iri  # Returns original if no match
