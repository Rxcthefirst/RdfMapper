"""Tests for the configuration wizard."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import polars as pl

from rdfmap.cli.wizard import ConfigurationWizard, run_wizard


@pytest.fixture
def sample_csv(tmp_path):
    """Create a sample CSV file for testing."""
    csv_path = tmp_path / "sample.csv"
    csv_content = """id,name,age,email
1,Alice,30,alice@example.com
2,Bob,25,bob@example.com
3,Charlie,35,charlie@example.com
"""
    csv_path.write_text(csv_content)
    return csv_path


@pytest.fixture
def sample_ontology(tmp_path):
    """Create a sample ontology file."""
    onto_path = tmp_path / "ontology.ttl"
    onto_content = """@prefix ex: <http://example.com/> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

ex:Person a owl:Class ;
    rdfs:label "Person" .

ex:name a owl:DatatypeProperty ;
    rdfs:label "name" ;
    rdfs:domain ex:Person .

ex:age a owl:DatatypeProperty ;
    rdfs:label "age" ;
    rdfs:domain ex:Person .
"""
    onto_path.write_text(onto_content)
    return onto_path


class TestConfigurationWizard:
    """Tests for ConfigurationWizard class."""

    def test_init(self):
        """Test wizard initialization."""
        wizard = ConfigurationWizard()
        assert wizard.config == {}
        assert wizard.data_preview is None

    def test_analyze_csv_data(self, sample_csv):
        """Test CSV data analysis."""
        wizard = ConfigurationWizard()
        wizard.config['format'] = 'csv'

        wizard._analyze_data_source(sample_csv)

        assert wizard.data_preview is not None
        assert len(wizard.data_preview.columns) == 4
        assert 'id' in wizard.data_preview.columns
        assert 'name' in wizard.data_preview.columns

    @patch('rdfmap.cli.wizard.Prompt.ask')
    @patch('rdfmap.cli.wizard.Confirm.ask')
    def test_configure_data_source(self, mock_confirm, mock_prompt, sample_csv):
        """Test data source configuration."""
        wizard = ConfigurationWizard()

        # Mock user inputs
        mock_prompt.return_value = str(sample_csv)
        mock_confirm.return_value = False  # Don't show preview

        wizard._configure_data_source()

        assert wizard.config['data_source'] == str(sample_csv)
        assert wizard.config['format'] == 'csv'
        assert wizard.data_preview is not None

    @patch('rdfmap.cli.wizard.Prompt.ask')
    @patch('rdfmap.cli.wizard.Confirm.ask')
    def test_configure_ontology(self, mock_confirm, mock_prompt, sample_ontology):
        """Test ontology configuration."""
        wizard = ConfigurationWizard()

        # Mock user inputs
        mock_confirm.side_effect = [True, False]  # Has ontology, no imports
        mock_prompt.return_value = str(sample_ontology)

        wizard._configure_ontology()

        assert wizard.config['ontology'] == str(sample_ontology)

    @patch('rdfmap.cli.wizard.Prompt.ask')
    def test_configure_target_class(self, mock_prompt):
        """Test target class configuration."""
        wizard = ConfigurationWizard()

        # Mock user inputs
        mock_prompt.side_effect = [
            "http://example.com/Person",
            "http://example.com/Person/{id}"
        ]

        wizard._configure_target_class()

        assert wizard.config['target_class'] == "http://example.com/Person"
        assert wizard.config['iri_template'] == "http://example.com/Person/{id}"

    @patch('rdfmap.cli.wizard.Prompt.ask')
    def test_configure_processing_speed(self, mock_prompt):
        """Test processing configuration with speed priority."""
        wizard = ConfigurationWizard()

        mock_prompt.return_value = '1'  # Speed priority

        wizard._configure_processing()

        assert wizard.config['priority'] == 'speed'
        assert wizard.config.get('use_semantic') == False
        assert wizard.config.get('streaming') == False

    @patch('rdfmap.cli.wizard.Prompt.ask')
    def test_configure_processing_memory(self, mock_prompt):
        """Test processing configuration with memory priority."""
        wizard = ConfigurationWizard()

        mock_prompt.return_value = '2'  # Memory priority

        wizard._configure_processing()

        assert wizard.config['priority'] == 'memory'
        assert wizard.config.get('streaming') == True
        assert wizard.config.get('chunk_size') == 10000

    @patch('rdfmap.cli.wizard.Prompt.ask')
    def test_configure_processing_quality(self, mock_prompt):
        """Test processing configuration with quality priority."""
        wizard = ConfigurationWizard()

        mock_prompt.return_value = '3'  # Quality priority

        wizard._configure_processing()

        assert wizard.config['priority'] == 'quality'
        assert wizard.config.get('use_semantic') == True
        assert wizard.config.get('use_graph_reasoning') == True
        assert wizard.config.get('use_history') == True

    @patch('rdfmap.cli.wizard.Prompt.ask')
    @patch('rdfmap.cli.wizard.Confirm.ask')
    def test_configure_output(self, mock_confirm, mock_prompt):
        """Test output configuration."""
        wizard = ConfigurationWizard()

        # Mock user inputs
        mock_prompt.side_effect = ['turtle', 'output.ttl']
        mock_confirm.return_value = False  # No validation

        wizard._configure_output()

        assert wizard.config['output_format'] == 'turtle'
        assert wizard.config['output'] == 'output.ttl'

    @patch('rdfmap.cli.wizard.Prompt.ask')
    @patch('rdfmap.cli.wizard.Confirm.ask')
    def test_configure_advanced(self, mock_confirm, mock_prompt):
        """Test advanced configuration."""
        wizard = ConfigurationWizard()

        # Mock user inputs
        mock_confirm.side_effect = [
            True,  # Customize thresholds
            True,  # Use semantic
            True,  # Use graph reasoning
            True,  # Use history
            True,  # Enable logging
        ]
        mock_prompt.side_effect = [
            '0.7',  # Semantic threshold
            '0.5',  # Fuzzy threshold
            'rdfmap.log',  # Log file
        ]

        wizard._configure_advanced()

        assert wizard.config['thresholds']['semantic'] == 0.7
        assert wizard.config['thresholds']['fuzzy'] == 0.5
        assert wizard.config['use_semantic'] == True
        assert wizard.config['use_graph_reasoning'] == True
        assert wizard.config['use_history'] == True
        assert wizard.config['enable_logging'] == True
        assert wizard.config['log_file'] == 'rdfmap.log'

    def test_save_config(self, tmp_path):
        """Test configuration saving."""
        wizard = ConfigurationWizard()
        wizard.config = {
            'data_source': 'test.csv',
            'format': 'csv',
            'ontology': 'onto.ttl',
            'target_class': 'http://example.com/Test',
            'iri_template': '{base_iri}test/{id}',
            'output': 'output.ttl',
            'priority': 'balanced',
        }

        config_path = tmp_path / "config.yaml"
        wizard._save_config(str(config_path))

        assert config_path.exists()

        # Verify content has proper mapping structure
        import yaml
        with open(config_path) as f:
            loaded_config = yaml.safe_load(f)

        # Check for required mapping structure
        assert 'namespaces' in loaded_config
        assert 'defaults' in loaded_config
        assert 'sheets' in loaded_config
        assert 'options' in loaded_config

        # Check sheet structure
        assert len(loaded_config['sheets']) == 1
        sheet = loaded_config['sheets'][0]
        assert sheet['source'] == 'test.csv'
        assert sheet['row_resource']['class'] == 'http://example.com/Test'
        assert 'columns' in sheet
        assert 'objects' in sheet

        # Check wizard metadata is preserved
        assert '_wizard_config' in loaded_config
        assert loaded_config['_wizard_config']['priority'] == 'balanced'

    def test_show_column_preview(self, sample_csv):
        """Test column preview display."""
        wizard = ConfigurationWizard()
        wizard.config['format'] = 'csv'
        wizard._analyze_data_source(sample_csv)

        # Should not raise any errors
        wizard._show_column_preview()

    def test_estimate_with_data(self, sample_csv):
        """Test processing estimates with data."""
        wizard = ConfigurationWizard()
        wizard.config['format'] = 'csv'
        wizard.config['use_semantic'] = True
        wizard.config['use_graph_reasoning'] = True
        wizard.config['use_history'] = True
        wizard._analyze_data_source(sample_csv)

        # Should not raise any errors
        wizard._show_estimate()

    def test_estimate_without_data(self):
        """Test processing estimates without data."""
        wizard = ConfigurationWizard()
        wizard.config['use_semantic'] = True

        # Should not raise any errors (gracefully handles no data)
        wizard._show_estimate()


@pytest.mark.integration
class TestWizardIntegration:
    """Integration tests for the full wizard flow."""

    @patch('rdfmap.cli.wizard.Prompt.ask')
    @patch('rdfmap.cli.wizard.Confirm.ask')
    @patch('rdfmap.cli.wizard.console')
    def test_full_wizard_flow(
        self, mock_console, mock_confirm, mock_prompt,
        sample_csv, sample_ontology, tmp_path
    ):
        """Test complete wizard flow."""
        output_path = tmp_path / "generated_config.yaml"

        # Mock all user inputs in order
        mock_prompt.side_effect = [
            str(sample_csv),  # Data file path
            str(sample_ontology),  # Ontology path
            "http://example.com/Person",  # Target class
            "http://example.com/Person/{id}",  # IRI template
            '4',  # Balanced priority
            'turtle',  # Output format
            'output.ttl',  # Output file
            str(output_path),  # Config save path
        ]

        mock_confirm.side_effect = [
            True,  # Show column preview
            True,  # Has ontology
            False,  # No imports
            False,  # No validation
            False,  # No advanced options
            True,  # Save configuration
        ]

        config = run_wizard(str(output_path))

        # Verify config has proper mapping structure
        assert 'namespaces' in config
        assert 'defaults' in config
        assert 'sheets' in config
        assert 'options' in config

        # Verify sheet configuration
        assert len(config['sheets']) == 1
        sheet = config['sheets'][0]
        assert sheet['source'] == str(sample_csv)
        assert sheet['row_resource']['class'] == "http://example.com/Person"

        # Verify wizard metadata
        assert '_wizard_config' in config
        assert config['_wizard_config']['priority'] == 'balanced'
        assert config['_wizard_config']['output_format'] == 'turtle'

        # Verify file was saved
        assert output_path.exists()

    @patch('rdfmap.cli.wizard.Prompt.ask')
    @patch('rdfmap.cli.wizard.Confirm.ask')
    def test_wizard_with_invalid_file(self, mock_confirm, mock_prompt):
        """Test wizard handles invalid file paths."""
        wizard = ConfigurationWizard()

        # First try invalid, then cancel
        mock_prompt.side_effect = [
            "/nonexistent/file.csv",
        ]
        mock_confirm.return_value = False  # Don't try again

        with pytest.raises(ValueError, match="No valid data source"):
            wizard._configure_data_source()

    def test_wizard_detects_excel_format(self, tmp_path):
        """Test wizard detects Excel format."""
        excel_path = tmp_path / "test.xlsx"
        excel_path.touch()

        wizard = ConfigurationWizard()

        with patch('rdfmap.cli.wizard.Prompt.ask', return_value=str(excel_path)):
            with patch('rdfmap.cli.wizard.Confirm.ask', return_value=False):
                wizard._configure_data_source()

        assert wizard.config['format'] == 'excel'

    def test_wizard_detects_json_format(self, tmp_path):
        """Test wizard detects JSON format."""
        json_path = tmp_path / "test.json"
        json_path.write_text('{"key": "value"}')

        wizard = ConfigurationWizard()

        with patch('rdfmap.cli.wizard.Prompt.ask', return_value=str(json_path)):
            with patch('rdfmap.cli.wizard.Confirm.ask', return_value=False):
                wizard._configure_data_source()

        assert wizard.config['format'] == 'json'


@pytest.mark.parametrize("priority,expected_config", [
    ('1', {'priority': 'speed', 'use_semantic': False, 'streaming': False}),
    ('2', {'priority': 'memory', 'streaming': True, 'chunk_size': 10000}),
    ('3', {'priority': 'quality', 'use_semantic': True, 'use_graph_reasoning': True}),
    ('4', {'priority': 'balanced', 'use_semantic': True, 'streaming': False}),
])
def test_processing_priorities(priority, expected_config):
    """Test different processing priority configurations."""
    wizard = ConfigurationWizard()

    with patch('rdfmap.cli.wizard.Prompt.ask', return_value=priority):
        wizard._configure_processing()

    for key, value in expected_config.items():
        assert wizard.config.get(key) == value

