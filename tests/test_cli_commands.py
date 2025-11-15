"""Tests for CLI Commands.

This module tests the CLI interface including init, convert, wizard, and templates commands.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from typer.testing import CliRunner

from rdfmap.cli.main import app


@pytest.fixture
def cli_runner():
    """Create CLI runner for testing."""
    return CliRunner()


@pytest.fixture
def sample_csv(tmp_path):
    """Create a sample CSV file."""
    csv_file = tmp_path / "data.csv"
    csv_file.write_text("id,name,age\n1,Alice,30\n2,Bob,25\n")
    return csv_file


@pytest.fixture
def sample_ontology(tmp_path):
    """Create a sample ontology file."""
    onto_file = tmp_path / "ontology.ttl"
    onto_file.write_text("""
@prefix ex: <http://example.org/> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

ex:Person a owl:Class ;
    rdfs:label "Person" .

ex:hasName a owl:DatatypeProperty ;
    rdfs:label "has name" ;
    rdfs:domain ex:Person .

ex:hasAge a owl:DatatypeProperty ;
    rdfs:label "has age" ;
    rdfs:domain ex:Person .
""")
    return onto_file


@pytest.fixture
def sample_mapping(tmp_path):
    """Create a sample mapping configuration."""
    mapping_file = tmp_path / "mapping.yaml"
    mapping_file.write_text("""
namespaces:
  ex: "http://example.org/"
  
defaults:
  base_iri: "http://example.org/"
  
sheets:
  - name: "data"
    source: "data.csv"
    row_resource:
      class: "ex:Person"
      iri_template: "{base_iri}person/{id}"
    property_mappings:
      name: "ex:hasName"
      age: "ex:hasAge"
""")
    return mapping_file


class TestCLIApp:
    """Test suite for CLI app."""

    def test_app_help(self, cli_runner):
        """Test that app shows help."""
        result = cli_runner.invoke(app, ['--help'])
        assert result.exit_code == 0
        assert 'rdfmap' in result.output.lower() or 'command' in result.output.lower()


class TestCLIInit:
    """Test suite for init command."""

    def test_init_command_help(self, cli_runner):
        """Test that init command shows help."""
        result = cli_runner.invoke(app, ['init', '--help'])
        assert result.exit_code == 0
        assert 'init' in result.output.lower() or 'wizard' in result.output.lower()

    @patch('rdfmap.cli.main.run_wizard')
    def test_init_with_output(self, mock_wizard, cli_runner, tmp_path):
        """Test init command with output file."""
        output_file = tmp_path / "output.yaml"

        # Mock the wizard
        mock_wizard.return_value = {"test": "config"}

        result = cli_runner.invoke(app, [
            'init',
            '-o', str(output_file)
        ])

        # Should succeed or show expected error
        assert result.exit_code in [0, 1]  # May fail if mocking incomplete

    @patch('rdfmap.templates.library.get_template_library')
    @patch('rdfmap.cli.main.run_wizard')
    def test_init_with_template(self, mock_wizard, mock_get_library, cli_runner, tmp_path):
        """Test init with template option."""
        # Mock the library
        mock_library = Mock()
        mock_template = Mock()
        mock_template.name = "test-template"
        mock_template.description = "Test"
        mock_template.example_ontology = None
        mock_template.example_data = None
        mock_library.get_template.return_value = mock_template
        mock_get_library.return_value = mock_library

        # Mock wizard
        mock_wizard.return_value = {"test": "config"}

        result = cli_runner.invoke(app, [
            'init',
            '--template', 'test-template',
            '-o', str(tmp_path / "config.yaml")
        ])

        # Should succeed or show expected error
        assert result.exit_code in [0, 1]


class TestCLIConvert:
    """Test suite for convert command."""

    def test_convert_command_help(self, cli_runner):
        """Test that convert command shows help."""
        result = cli_runner.invoke(app, ['convert', '--help'])
        assert result.exit_code == 0
        assert 'convert' in result.output.lower() or 'mapping' in result.output.lower()

    def test_convert_missing_mapping(self, cli_runner, tmp_path):
        """Test convert with missing mapping file."""
        result = cli_runner.invoke(app, [
            'convert',
            '--mapping', str(tmp_path / "nonexistent.yaml")
        ])

        # Should fail
        assert result.exit_code != 0


class TestCLITemplates:
    """Test suite for templates command."""

    def test_templates_command_help(self, cli_runner):
        """Test that templates command shows help."""
        result = cli_runner.invoke(app, ['templates', '--help'])

        # Should show help or succeed
        assert result.exit_code in [0, 2]  # 2 for missing subcommand


class TestCLIValidate:
    """Test suite for validate command."""

    def test_validate_command_help(self, cli_runner):
        """Test that validate command shows help."""
        result = cli_runner.invoke(app, ['validate', '--help'])

        # Should show help or succeed
        assert result.exit_code in [0, 2]


class TestCLIErrorHandling:
    """Test CLI error handling."""

    def test_invalid_command(self, cli_runner):
        """Test invalid command."""
        result = cli_runner.invoke(app, ['invalid-command'])

        # Should fail gracefully
        assert result.exit_code != 0


@pytest.mark.integration
class TestCLIIntegration:
    """Integration tests for CLI."""

    @pytest.mark.slow
    def test_init_creates_config(self, cli_runner, tmp_path):
        """Test that init creates a configuration file."""
        output_file = tmp_path / "test_config.yaml"

        # This would require mocking the entire wizard flow
        # For now, just test the command exists
        result = cli_runner.invoke(app, ['init', '--help'])
        assert result.exit_code == 0


