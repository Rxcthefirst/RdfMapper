"""Test ontology imports functionality."""

import tempfile
from pathlib import Path
import pytest
import yaml
from rdfmap.generator.mapping_generator import MappingGenerator, GeneratorConfig
from rdfmap.generator.ontology_analyzer import OntologyAnalyzer


def test_ontology_imports_basic():
    """Test basic ontology import functionality."""
    # Create a base ontology
    base_ontology = """
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix skos: <http://www.w3.org/2004/02/skos/core#> .
@prefix base: <http://example.org/base#> .

base:Employee a owl:Class ;
    rdfs:label "Employee" ;
    skos:prefLabel "Employee" .

base:hasEmployeeID a owl:DatatypeProperty ;
    rdfs:domain base:Employee ;
    rdfs:range <http://www.w3.org/2001/XMLSchema#string> ;
    rdfs:label "has employee ID" ;
    skos:prefLabel "has employee ID" .
"""

    # Create an imported ontology with additional properties
    imported_ontology = """
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix skos: <http://www.w3.org/2004/02/skos/core#> .
@prefix imported: <http://example.org/imported#> .
@prefix base: <http://example.org/base#> .

imported:Department a owl:Class ;
    rdfs:label "Department" ;
    skos:prefLabel "Department" .

imported:hasDepartmentName a owl:DatatypeProperty ;
    rdfs:domain imported:Department ;
    rdfs:range <http://www.w3.org/2001/XMLSchema#string> ;
    rdfs:label "has department name" ;
    skos:prefLabel "has department name" ;
    skos:hiddenLabel "dept_name" .

imported:worksIn a owl:ObjectProperty ;
    rdfs:domain base:Employee ;
    rdfs:range imported:Department ;
    rdfs:label "works in" ;
    skos:prefLabel "works in" .
"""

    # Create test data CSV
    test_csv = """employee_id,dept_name,full_name
E001,Engineering,John Smith
E002,Marketing,Jane Doe
"""

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Write ontologies
        base_onto_path = temp_path / "base.ttl"
        base_onto_path.write_text(base_ontology)

        imported_onto_path = temp_path / "imported.ttl"
        imported_onto_path.write_text(imported_ontology)

        # Write test data
        csv_path = temp_path / "test_data.csv"
        csv_path.write_text(test_csv)

        # Test ontology analyzer with imports
        analyzer = OntologyAnalyzer(str(base_onto_path), imports=[str(imported_onto_path)])

        # Should find classes from both ontologies
        class_labels = [cls.label for cls in analyzer.classes.values()]
        assert "Employee" in class_labels
        assert "Department" in class_labels

        # Should find properties from both ontologies
        property_labels = [prop.label for prop in analyzer.properties.values()]
        assert "has employee ID" in property_labels
        assert "has department name" in property_labels
        assert "works in" in property_labels

        # Test mapping generation with imports
        config = GeneratorConfig(
            base_iri="http://example.org/data/",
            imports=[str(imported_onto_path)]
        )

        generator = MappingGenerator(
            str(base_onto_path),
            str(csv_path),
            config
        )

        mapping = generator.generate(target_class="Employee")

        # Should include imports in mapping
        assert "imports" in mapping
        assert str(imported_onto_path) in mapping["imports"]

        # Should be able to match dept_name using hiddenLabel from imported ontology
        columns = mapping["sheets"][0]["columns"]

        # Should have mapped employee_id to base ontology property
        assert "employee_id" in columns
        assert "hasEmployeeID" in columns["employee_id"]["as"]

        print("✓ Ontology imports test passed!")


def test_imports_in_yaml_config():
    """Test that imports work in YAML configuration files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create a dummy CSV file
        csv_path = temp_path / "test.csv"
        csv_path.write_text("employee_id,name\nE001,John")

        config_yaml = f"""
namespaces:
  base: http://example.org/base#
  imported: http://example.org/imported#
  xsd: http://www.w3.org/2001/XMLSchema#

imports:
  - /path/to/imported/ontology.ttl
  - http://example.org/remote/ontology.owl

defaults:
  base_iri: http://example.org/data/

sheets:
  - name: test_sheet
    source: {csv_path}
    row_resource:
      class: base:Employee
      iri_template: employee:{{employee_id}}
    columns:
      employee_id:
        as: base:hasEmployeeID
        datatype: xsd:string

options:
  on_error: report
"""

        config_path = temp_path / "config.yaml"
        config_path.write_text(config_yaml)

        # Should load successfully with imports field
        from rdfmap.config.loader import load_mapping_config
        config = load_mapping_config(config_path)

        # Should contain imports
        assert config.imports is not None
        assert len(config.imports) == 2
        assert "/path/to/imported/ontology.ttl" in config.imports
        assert "http://example.org/remote/ontology.owl" in config.imports

        print("✓ YAML imports configuration test passed!")


if __name__ == "__main__":
    test_ontology_imports_basic()
    test_imports_in_yaml_config()
    print("All imports tests passed!")
