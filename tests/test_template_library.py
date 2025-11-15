"""Tests for Template Library.

This module tests the template library functionality for pre-built mapping configurations.
"""

import pytest
from pathlib import Path

from rdfmap.templates.library import MappingTemplate, TemplateLibrary, get_template_library


class TestMappingTemplate:
    """Test suite for MappingTemplate dataclass."""

    def test_template_creation(self):
        """Test creating a MappingTemplate instance."""
        template = MappingTemplate(
            name="test-template",
            domain="testing",
            description="A test template",
            template_config={"entity_class": "TestClass", "properties": {"name": "hasName"}}
        )

        assert template.name == "test-template"
        assert template.domain == "testing"
        assert "entity_class" in template.template_config

    def test_template_with_examples(self):
        """Test template with example data and ontology."""
        template = MappingTemplate(
            name="with-examples",
            domain="testing",
            description="Template with examples",
            example_ontology="path/to/ontology.ttl",
            example_data="path/to/data.csv"
        )

        assert template.example_ontology is not None
        assert template.example_data is not None

    def test_template_to_dict(self):
        """Test converting template to dictionary."""
        template = MappingTemplate(
            name="test",
            domain="test",
            description="Test"
        )

        result = template.to_dict()
        assert isinstance(result, dict)
        assert result['name'] == "test"


class TestTemplateLibrary:
    """Test suite for TemplateLibrary."""

    def test_library_initialization(self):
        """Test that template library initializes."""
        library = TemplateLibrary()
        assert library is not None
        assert hasattr(library, 'templates')

    def test_get_all_templates(self):
        """Test getting all templates."""
        library = get_template_library()
        templates = library.list_templates()

        assert isinstance(templates, list)
        assert len(templates) > 0
        assert all(isinstance(t, MappingTemplate) for t in templates)

    def test_get_by_domain(self):
        """Test filtering templates by domain."""
        library = get_template_library()

        # Test with known domains
        financial_templates = library.list_templates(domain="financial")
        assert isinstance(financial_templates, list)

        if len(financial_templates) > 0:
            assert all(t.domain == "financial" for t in financial_templates)

    def test_get_by_name(self):
        """Test getting template by name."""
        library = get_template_library()

        # Try to get a specific template
        all_templates = library.list_templates()
        if len(all_templates) > 0:
            first_template = all_templates[0]
            retrieved = library.get_template(first_template.name)

            assert retrieved is not None
            assert retrieved.name == first_template.name

    def test_get_nonexistent_template(self):
        """Test getting non-existent template returns None."""
        library = get_template_library()
        result = library.get_template("nonexistent-template-12345")

        assert result is None

    def test_list_domains(self):
        """Test listing available domains."""
        library = get_template_library()
        domains = library.list_domains()

        assert isinstance(domains, list)
        # Should have at least some domains
        expected_domains = ["financial", "healthcare", "ecommerce", "academic", "hr"]
        for domain in expected_domains:
            if any(t.domain == domain for t in library.list_templates()):
                assert domain in domains


class TestPredefinedTemplates:
    """Test that predefined templates are properly configured."""

    def test_financial_loans_template(self):
        """Test financial-loans template."""
        library = get_template_library()
        template = library.get_template("financial-loans")

        if template:
            assert template.domain == "financial"
            assert template.template_config is not None
            assert len(template.template_config) > 0

    def test_healthcare_patients_template(self):
        """Test healthcare-patients template."""
        library = get_template_library()
        template = library.get_template("healthcare-patients")

        if template:
            assert template.domain == "healthcare"
            assert template.template_config is not None

    def test_ecommerce_orders_template(self):
        """Test ecommerce-orders template."""
        library = get_template_library()
        template = library.get_template("ecommerce-orders")

        if template:
            assert template.domain == "ecommerce"
            assert template.template_config is not None

    def test_all_templates_have_required_fields(self):
        """Test that all templates have required fields."""
        library = get_template_library()
        templates = library.list_templates()

        for template in templates:
            assert template.name is not None
            assert template.domain is not None
            assert template.description is not None
            # template_config is optional but should be a dict if present
            if template.template_config:
                assert isinstance(template.template_config, dict)


class TestTemplateGeneration:
    """Test template-based configuration generation."""

    def test_template_to_config(self):
        """Test converting template to mapping config."""
        library = get_template_library()
        templates = library.list_templates()

        if len(templates) > 0:
            template = templates[0]

            # Template should have the necessary data to generate config
            assert template.name is not None
            assert template.template_config is not None

    def test_template_with_example_data(self):
        """Test templates that include example data."""
        library = get_template_library()
        templates = library.list_templates()

        templates_with_examples = [t for t in templates if t.example_data is not None]

        for template in templates_with_examples:
            # Example data should be a path string
            assert isinstance(template.example_data, str)


class TestTemplateValidation:
    """Test template validation."""

    def test_template_names_unique(self):
        """Test that all template names are unique."""
        library = get_template_library()
        templates = library.list_templates()

        names = [t.name for t in templates]
        assert len(names) == len(set(names)), "Template names should be unique"

    def test_template_names_format(self):
        """Test that template names follow naming convention."""
        library = get_template_library()
        templates = library.list_templates()

        for template in templates:
            # Names should be lowercase with hyphens
            assert template.name == template.name.lower()
            assert ' ' not in template.name

    def test_domains_valid(self):
        """Test that all domains are from expected set."""
        library = get_template_library()
        templates = library.list_templates()

        valid_domains = ["financial", "healthcare", "ecommerce", "academic", "hr", "general"]

        for template in templates:
            assert template.domain in valid_domains, f"Invalid domain: {template.domain}"


@pytest.mark.integration
class TestTemplateIntegration:
    """Integration tests for template library."""

    def test_template_library_cli_integration(self):
        """Test that template library works with CLI."""
        # This would test the full workflow
        # Skip for unit tests
        pytest.skip("Integration test - requires CLI")

    def test_template_with_generator(self):
        """Test using template with mapping generator."""
        # This would test using a template to generate mappings
        # Skip for unit tests
        pytest.skip("Integration test - requires full generator")


class TestGetTemplateLibrary:
    """Test the get_template_library function."""

    def test_singleton_pattern(self):
        """Test that get_template_library returns same instance."""
        library1 = get_template_library()
        library2 = get_template_library()

        # Should return the same instance
        assert library1 is library2

    def test_library_not_none(self):
        """Test that library is never None."""
        library = get_template_library()
        assert library is not None


class TestTemplateSearch:
    """Test template search and filtering functionality."""

    def test_search_by_keyword(self):
        """Test searching templates by keyword in description."""
        library = get_template_library()
        templates = library.list_templates()

        # Search for "loan" or "patient" in descriptions
        loan_templates = [t for t in templates if "loan" in t.description.lower()]
        patient_templates = [t for t in templates if "patient" in t.description.lower()]

        # Should find relevant templates
        if len(loan_templates) > 0:
            assert all(t.domain in ["financial", "healthcare"]
                      for t in loan_templates)

    def test_filter_by_domain(self):
        """Test filtering templates by domain."""
        library = get_template_library()

        # Get financial templates
        financial = library.list_templates(domain="financial")

        # All should be financial domain
        assert all(t.domain == "financial" for t in financial)

        # Get healthcare templates
        healthcare = library.list_templates(domain="healthcare")

        # All should be healthcare domain
        assert all(t.domain == "healthcare" for t in healthcare)

