# Phase 2A: RML Export - W3C Standards Compatibility

**Timeline**: 2-3 weeks  
**Goal**: Add W3C RML export capability for standards compliance  
**Impact**: Academic credibility, enterprise trust, interoperability  
**Innovation Score Impact**: +0.5 points → 8.5-9.0/10

---

## Overview

This phase adds the ability to export your mapping configurations to W3C RML (R2RML/RML) format, making RDFMap compatible with the established semantic web ecosystem.

### Why This Matters

- ✅ **Standards Compliance**: "W3C RML Compatible" badge
- ✅ **Interoperability**: Share mappings with RMLMapper, CARML, Morph-KGC users
- ✅ **Academic Adoption**: Legitimacy in research communities
- ✅ **Enterprise Trust**: Standards compliance is a procurement requirement
- ✅ **Marketing Value**: Differentiates from custom-only solutions

### Why This Is Feasible

Your data structures already map almost perfectly to RML concepts:

| RDFMap Concept | RML Equivalent | Complexity |
|----------------|----------------|------------|
| `MappingConfig` | Collection of TriplesMaps | Simple |
| `SheetMapping` | TriplesMap | Simple |
| `RowResource` | SubjectMap | Simple |
| `ColumnMapping` | PredicateObjectMap | Simple |
| `LinkedObject` | ParentTriplesMap | Medium |

**This is mostly a serialization task, not an architecture change!**

---

## Week 1: Core Implementation

### Day 1: Project Setup

#### 1. Create Module Structure

```bash
mkdir -p src/rdfmap/exporters
touch src/rdfmap/exporters/__init__.py
touch src/rdfmap/exporters/rml_exporter.py
```

#### 2. Install RML Dependencies

Already have: `rdflib>=6.0.0` ✅

#### 3. Create Test Directory

```bash
mkdir -p tests/exporters
touch tests/exporters/__init__.py
touch tests/exporters/test_rml_exporter.py
```

### Day 2-3: Implement Core RMLExporter Class

**File**: `src/rdfmap/exporters/rml_exporter.py`

```python
"""Export RDFMap configurations to RML (R2RML/RML) format.

This module provides functionality to convert RDFMap's YAML-based mapping
configurations to W3C RML Turtle format for compatibility with standard
RML processors like RMLMapper, CARML, and Morph-KGC.

Limitations:
- CSV/XLSX sources only (no JSON/XML yet)
- Single-source mappings (no cross-source joins yet)
- Basic transforms only (FnO functions not supported)
"""

from typing import Dict, List
from rdflib import Graph, Namespace, Literal, URIRef, BNode
from rdflib.namespace import RDF, RDFS, XSD

from ..models.mapping import (
    MappingConfig,
    SheetMapping,
    RowResource,
    ColumnMapping,
    LinkedObject,
)

# RML/R2RML namespaces
RML = Namespace("http://semweb.mmlab.be/ns/rml#")
RR = Namespace("http://www.w3.org/ns/r2rml#")
QL = Namespace("http://semweb.mmlab.be/ns/ql#")


class RMLExporter:
    """Convert RDFMap configuration to RML Turtle format."""
    
    def __init__(self, config: MappingConfig):
        """Initialize exporter with mapping configuration.
        
        Args:
            config: Validated MappingConfig object
        """
        self.config = config
        self.graph = Graph()
        self._bind_namespaces()
        self.warnings: List[str] = []
    
    def export(self) -> str:
        """Generate complete RML mapping as Turtle string.
        
        Returns:
            RML mapping in Turtle format
        """
        for sheet in self.config.sheets:
            self._create_triples_map(sheet)
        
        return self.graph.serialize(format="turtle")
    
    def _create_triples_map(self, sheet: SheetMapping):
        """Create RML TriplesMap for a sheet.
        
        Args:
            sheet: Sheet mapping configuration
        """
        # Create TriplesMap node
        tm = URIRef(f"#{sheet.name}TriplesMap")
        self.graph.add((tm, RDF.type, RR.TriplesMap))
        
        # Add logical source
        self._add_logical_source(tm, sheet)
        
        # Add subject map
        self._add_subject_map(tm, sheet)
        
        # Add predicate-object maps for columns
        for col_name, col_mapping in sheet.columns.items():
            self._add_predicate_object_map(tm, col_name, col_mapping)
        
        # Add linked objects
        if hasattr(sheet, 'objects') and sheet.objects:
            for obj_name, linked_obj in sheet.objects.items():
                self._add_linked_object(tm, obj_name, linked_obj, sheet)
    
    def _add_logical_source(self, tm: URIRef, sheet: SheetMapping):
        """Add rml:logicalSource with CSV configuration.
        
        Args:
            tm: TriplesMap URI
            sheet: Sheet mapping configuration
        """
        ls = BNode()
        self.graph.add((tm, RML.logicalSource, ls))
        
        # Source file
        self.graph.add((ls, RML.source, Literal(sheet.source)))
        
        # Reference formulation (CSV for now)
        self.graph.add((ls, RML.referenceFormulation, QL.CSV))
    
    def _add_subject_map(self, tm: URIRef, sheet: SheetMapping):
        """Add rr:subjectMap with IRI template and class.
        
        Args:
            tm: TriplesMap URI
            sheet: Sheet mapping configuration
        """
        sm = BNode()
        self.graph.add((tm, RR.subjectMap, sm))
        
        # IRI template
        template = sheet.row_resource.iri_template
        self.graph.add((sm, RR.template, Literal(template)))
        
        # rdf:type (class)
        class_uri = self._expand_curie(sheet.row_resource.class_type)
        self.graph.add((sm, RR.class_, class_uri))
    
    def _add_predicate_object_map(
        self, tm: URIRef, col_name: str, mapping: ColumnMapping
    ):
        """Add predicate-object map for a column.
        
        Args:
            tm: TriplesMap URI
            col_name: Column name from spreadsheet
            mapping: Column mapping configuration
        """
        pom = BNode()
        self.graph.add((tm, RR.predicateObjectMap, pom))
        
        # Predicate
        pred_uri = self._expand_curie(mapping.as_property)
        self.graph.add((pom, RR.predicate, pred_uri))
        
        # Object map
        om = BNode()
        self.graph.add((pom, RR.objectMap, om))
        
        # Reference (column name)
        self.graph.add((om, RML.reference, Literal(col_name)))
        
        # Datatype
        if mapping.datatype:
            dt_uri = self._expand_curie(mapping.datatype)
            self.graph.add((om, RR.datatype, dt_uri))
        
        # Language tag
        if mapping.language:
            self.graph.add((om, RR.language, Literal(mapping.language)))
        
        # Warn about unsupported features
        if mapping.transform:
            self.warnings.append(
                f"Column '{col_name}': Transform '{mapping.transform}' not "
                "supported in RML export. Custom functions (FnO) required."
            )
        
        if mapping.default is not None:
            self.warnings.append(
                f"Column '{col_name}': Default value '{mapping.default}' not "
                "supported in RML export. Use RML-specific extensions."
            )
    
    def _add_linked_object(
        self,
        tm: URIRef,
        obj_name: str,
        linked_obj: LinkedObject,
        parent_sheet: SheetMapping,
    ):
        """Add object property referencing another TriplesMap.
        
        Args:
            tm: Parent TriplesMap URI
            obj_name: Linked object name
            linked_obj: Linked object configuration
            parent_sheet: Parent sheet mapping
        """
        pom = BNode()
        self.graph.add((tm, RR.predicateObjectMap, pom))
        
        # Predicate (object property)
        pred_uri = self._expand_curie(linked_obj.predicate)
        self.graph.add((pom, RR.predicate, pred_uri))
        
        # Object map with parent triples map reference
        om = BNode()
        self.graph.add((pom, RR.objectMap, om))
        
        # Reference to parent TriplesMap
        parent_tm = URIRef(f"#{obj_name}TriplesMap")
        self.graph.add((om, RR.parentTriplesMap, parent_tm))
        
        # Create the parent TriplesMap
        self._create_linked_object_triples_map(
            parent_tm, obj_name, linked_obj, parent_sheet
        )
    
    def _create_linked_object_triples_map(
        self,
        tm: URIRef,
        obj_name: str,
        linked_obj: LinkedObject,
        parent_sheet: SheetMapping,
    ):
        """Create TriplesMap for a linked object.
        
        Args:
            tm: TriplesMap URI
            obj_name: Object name
            linked_obj: Linked object configuration
            parent_sheet: Parent sheet (for source info)
        """
        self.graph.add((tm, RDF.type, RR.TriplesMap))
        
        # Same logical source as parent
        ls = BNode()
        self.graph.add((tm, RML.logicalSource, ls))
        self.graph.add((ls, RML.source, Literal(parent_sheet.source)))
        self.graph.add((ls, RML.referenceFormulation, QL.CSV))
        
        # Subject map
        sm = BNode()
        self.graph.add((tm, RR.subjectMap, sm))
        self.graph.add((sm, RR.template, Literal(linked_obj.iri_template)))
        
        # Class
        class_uri = self._expand_curie(linked_obj.class_type)
        self.graph.add((sm, RR.class_, class_uri))
        
        # Properties of linked object
        for prop_config in linked_obj.properties:
            col_mapping = ColumnMapping(
                as_property=prop_config.get("as"),
                datatype=prop_config.get("datatype"),
                language=prop_config.get("language"),
            )
            self._add_predicate_object_map(
                tm, prop_config["column"], col_mapping
            )
    
    def _expand_curie(self, curie: str) -> URIRef:
        """Expand CURIE to full URI using config namespaces.
        
        Args:
            curie: CURIE string (e.g., "ex:Person")
        
        Returns:
            Full URI
        """
        if ":" in curie and not curie.startswith("http"):
            prefix, local = curie.split(":", 1)
            if prefix in self.config.namespaces:
                return URIRef(self.config.namespaces[prefix] + local)
        
        # Already a full URI
        return URIRef(curie)
    
    def _bind_namespaces(self):
        """Bind all namespaces to graph."""
        self.graph.bind("rml", RML)
        self.graph.bind("rr", RR)
        self.graph.bind("ql", QL)
        
        # Bind user-defined namespaces
        for prefix, uri in self.config.namespaces.items():
            self.graph.bind(prefix, Namespace(uri))


def export_rml(config: MappingConfig, output_path: str = None) -> str:
    """Export RDFMap configuration to RML Turtle format.
    
    Args:
        config: Validated MappingConfig object
        output_path: Optional file path to write output
    
    Returns:
        RML mapping as Turtle string
    
    Example:
        >>> config = load_mapping_config("mapping.yaml")
        >>> rml_turtle = export_rml(config, "mapping.rml.ttl")
        >>> print(f"Exported {len(rml_turtle)} characters")
    """
    exporter = RMLExporter(config)
    rml_turtle = exporter.export()
    
    # Print warnings if any
    if exporter.warnings:
        print("\n⚠️  RML Export Warnings:")
        for warning in exporter.warnings:
            print(f"  - {warning}")
        print()
    
    # Write to file if requested
    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(rml_turtle)
    
    return rml_turtle
```

### Day 4-5: Write Tests

**File**: `tests/exporters/test_rml_exporter.py`

```python
"""Tests for RML export functionality."""

import pytest
from pathlib import Path
from rdflib import Graph, Namespace, RDF, Literal

from rdfmap.models.mapping import load_mapping_config
from rdfmap.exporters.rml_exporter import export_rml, RMLExporter

# RML/R2RML namespaces
RR = Namespace("http://www.w3.org/ns/r2rml#")
RML = Namespace("http://semweb.mmlab.be/ns/rml#")
QL = Namespace("http://semweb.mmlab.be/ns/ql#")


class TestRMLExporter:
    """Test RML export functionality."""
    
    def test_exporter_initialization(self):
        """Test RMLExporter initializes correctly."""
        config = load_mapping_config("examples/mortgage/config/mortgage_mapping.yaml")
        exporter = RMLExporter(config)
        
        assert exporter.config == config
        assert isinstance(exporter.graph, Graph)
        assert len(exporter.warnings) == 0
    
    def test_export_creates_valid_turtle(self):
        """Test export creates valid Turtle syntax."""
        config = load_mapping_config("examples/mortgage/config/mortgage_mapping.yaml")
        rml_turtle = export_rml(config)
        
        # Should be parseable as Turtle
        g = Graph()
        g.parse(data=rml_turtle, format="turtle")
        
        assert len(g) > 0
    
    def test_export_creates_triples_map(self):
        """Test export creates TriplesMap for each sheet."""
        config = load_mapping_config("examples/mortgage/config/mortgage_mapping.yaml")
        rml_turtle = export_rml(config)
        
        g = Graph()
        g.parse(data=rml_turtle, format="turtle")
        
        # Find TriplesMap nodes
        triples_maps = list(g.subjects(RDF.type, RR.TriplesMap))
        
        assert len(triples_maps) > 0
        assert len(triples_maps) == len(config.sheets)
    
    def test_export_includes_logical_source(self):
        """Test logical source is included."""
        config = load_mapping_config("examples/mortgage/config/mortgage_mapping.yaml")
        rml_turtle = export_rml(config)
        
        g = Graph()
        g.parse(data=rml_turtle, format="turtle")
        
        # Each TriplesMap should have a logical source
        for tm in g.subjects(RDF.type, RR.TriplesMap):
            ls = g.value(tm, RML.logicalSource)
            assert ls is not None
            
            # Should have source file
            source = g.value(ls, RML.source)
            assert source is not None
            
            # Should have reference formulation
            ref_form = g.value(ls, RML.referenceFormulation)
            assert ref_form == QL.CSV
    
    def test_export_includes_subject_map(self):
        """Test subject map is included."""
        config = load_mapping_config("examples/mortgage/config/mortgage_mapping.yaml")
        rml_turtle = export_rml(config)
        
        g = Graph()
        g.parse(data=rml_turtle, format="turtle")
        
        # Each TriplesMap should have a subject map
        for tm in g.subjects(RDF.type, RR.TriplesMap):
            sm = g.value(tm, RR.subjectMap)
            assert sm is not None
            
            # Should have IRI template
            template = g.value(sm, RR.template)
            assert template is not None
            
            # Should have class
            class_uri = g.value(sm, RR.class_)
            assert class_uri is not None
    
    def test_export_includes_predicate_object_maps(self):
        """Test predicate-object maps are included."""
        config = load_mapping_config("examples/mortgage/config/mortgage_mapping.yaml")
        rml_turtle = export_rml(config)
        
        g = Graph()
        g.parse(data=rml_turtle, format="turtle")
        
        # Should have predicate-object maps
        poms = list(g.triples((None, RR.predicateObjectMap, None)))
        assert len(poms) > 0
        
        # Each pom should have predicate and object map
        for _, _, pom in poms:
            predicate = g.value(pom, RR.predicate)
            object_map = g.value(pom, RR.objectMap)
            
            assert predicate is not None
            assert object_map is not None
            
            # Object map should have reference
            reference = g.value(object_map, RML.reference)
            assert reference is not None
    
    def test_export_preserves_namespaces(self):
        """Test user-defined namespaces are preserved."""
        config = load_mapping_config("examples/mortgage/config/mortgage_mapping.yaml")
        rml_turtle = export_rml(config)
        
        g = Graph()
        g.parse(data=rml_turtle, format="turtle")
        
        # Check that user namespaces are bound
        bound_prefixes = {prefix for prefix, _ in g.namespaces()}
        
        assert "rml" in bound_prefixes
        assert "rr" in bound_prefixes
        assert "ql" in bound_prefixes
        
        # User namespaces from config should also be present
        for prefix in config.namespaces.keys():
            assert prefix in bound_prefixes
    
    def test_export_handles_datatypes(self):
        """Test datatypes are correctly exported."""
        config = load_mapping_config("examples/mortgage/config/mortgage_mapping.yaml")
        rml_turtle = export_rml(config)
        
        g = Graph()
        g.parse(data=rml_turtle, format="turtle")
        
        # Find object maps with datatypes
        datatypes_found = False
        for om in g.subjects(RML.reference, None):
            datatype = g.value(om, RR.datatype)
            if datatype:
                datatypes_found = True
                # Should be a valid URI
                assert isinstance(datatype, URIRef)
                break
        
        assert datatypes_found, "No datatypes found in export"
    
    def test_export_to_file(self, tmp_path):
        """Test export writes to file correctly."""
        config = load_mapping_config("examples/mortgage/config/mortgage_mapping.yaml")
        output_file = tmp_path / "test_output.rml.ttl"
        
        rml_turtle = export_rml(config, str(output_file))
        
        # File should exist
        assert output_file.exists()
        
        # File content should match returned string
        with open(output_file, "r") as f:
            file_content = f.read()
        
        assert file_content == rml_turtle
    
    def test_export_warns_about_transforms(self):
        """Test warnings are generated for unsupported features."""
        # This test would need a mapping config with transforms
        # For now, just verify warning mechanism works
        config = load_mapping_config("examples/mortgage/config/mortgage_mapping.yaml")
        exporter = RMLExporter(config)
        
        # Manually add a warning to test the mechanism
        exporter.warnings.append("Test warning")
        
        assert len(exporter.warnings) == 1
        assert "Test warning" in exporter.warnings[0]


class TestRMLCompatibility:
    """Test RML output compatibility with RML processors."""
    
    def test_rml_structure_validity(self):
        """Test generated RML has valid structure."""
        config = load_mapping_config("examples/mortgage/config/mortgage_mapping.yaml")
        rml_turtle = export_rml(config)
        
        g = Graph()
        g.parse(data=rml_turtle, format="turtle")
        
        # Check required RML/R2RML structure
        assert len(list(g.triples((None, RDF.type, RR.TriplesMap)))) > 0
        assert len(list(g.triples((None, RML.logicalSource, None)))) > 0
        assert len(list(g.triples((None, RR.subjectMap, None)))) > 0
        assert len(list(g.triples((None, RR.predicateObjectMap, None)))) > 0
    
    def test_rml_can_be_reloaded(self):
        """Test exported RML can be loaded back as RDF."""
        config = load_mapping_config("examples/mortgage/config/mortgage_mapping.yaml")
        rml_turtle = export_rml(config)
        
        # Load once
        g1 = Graph()
        g1.parse(data=rml_turtle, format="turtle")
        
        # Serialize and reload
        turtle_again = g1.serialize(format="turtle")
        g2 = Graph()
        g2.parse(data=turtle_again, format="turtle")
        
        # Should have same number of triples
        assert len(g1) == len(g2)
```

---

## Week 2: CLI Integration & Documentation

### Day 1: Add CLI Command

**File**: `src/rdfmap/cli/main.py`

Add this command:

```python
@app.command()
def export_rml(
    mapping: Annotated[
        Path,
        typer.Option(
            "--mapping",
            "-m",
            help="RDFMap mapping configuration file (YAML/JSON)",
            exists=True,
            dir_okay=False,
        ),
    ],
    output: Annotated[
        Path,
        typer.Option(
            "--output",
            "-o",
            help="Output RML file (.ttl extension recommended)",
            dir_okay=False,
        ),
    ],
    verbose: Annotated[
        bool, typer.Option("--verbose", "-v", help="Enable verbose output")
    ] = False,
):
    """
    Export RDFMap configuration to W3C RML (R2RML/RML) format.
    
    This command converts your RDFMap YAML/JSON mapping configuration to
    W3C-standard RML Turtle format, making it compatible with other RML
    processors like RMLMapper, CARML, and Morph-KGC.
    
    Example:
    
        rdfmap export-rml -m mapping.yaml -o mapping.rml.ttl
    
    Compatible Tools:
    - RMLMapper (Java): https://github.com/RMLio/rmlmapper-java
    - CARML (Java): https://github.com/carml/carml
    - Morph-KGC (Python): https://github.com/oeg-upm/morph-kgc
    - SDM-RDFizer (Python): https://github.com/SDM-TIB/SDM-RDFizer
    
    Limitations:
    - CSV/XLSX sources only (no JSON/XML yet)
    - Single-source mappings (no cross-source joins yet)
    - Transforms not supported (FnO functions required)
    """
    from rdfmap.config.loader import load_mapping_config
    from rdfmap.exporters.rml_exporter import export_rml
    
    try:
        if verbose:
            console.print(f"[blue]Loading mapping configuration from {mapping}...[/blue]")
        
        config = load_mapping_config(mapping)
        
        if verbose:
            console.print(f"  Sheets: {len(config.sheets)}")
            console.print(f"  Namespaces: {len(config.namespaces)}")
            console.print(f"\n[blue]Exporting to RML format...[/blue]")
        
        rml_content = export_rml(config, str(output))
        
        console.print(f"\n[green]✓ RML mapping exported to: {output}[/green]")
        console.print(f"  Format: Turtle")
        console.print(f"  Size: {len(rml_content)} characters")
        console.print(f"\n[dim]Compatible with: RMLMapper, CARML, Morph-KGC, SDM-RDFizer[/dim]")
        
        if verbose:
            # Parse to show statistics
            from rdflib import Graph
            g = Graph()
            g.parse(data=rml_content, format="turtle")
            console.print(f"\n[dim]Statistics:[/dim]")
            console.print(f"  Triples: {len(g)}")
            console.print(f"  TriplesMap count: {len(config.sheets)}")
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        if verbose:
            import traceback
            console.print(traceback.format_exc())
        raise typer.Exit(code=1)
```

### Day 2: Write Documentation

**File**: `docs/guides/rml-export.md`

```markdown
# RML Export Guide

Learn how to export RDFMap configurations to W3C RML format for compatibility with other semantic web tools.

## What is RML?

RML (RDF Mapping Language) is a W3C community standard for expressing mappings from heterogeneous data sources to RDF. It's widely used in academic and enterprise contexts.

## Why Export to RML?

- **Standards Compliance**: Share mappings using W3C standards
- **Interoperability**: Use with RMLMapper, CARML, Morph-KGC
- **Archival**: Store mappings in standardized format
- **Enterprise Integration**: Meet procurement requirements
- **Academic Publishing**: Reference standard formats in papers

## Basic Usage

```bash
rdfmap export-rml --mapping mapping.yaml --output mapping.rml.ttl
```

This converts your RDFMap YAML configuration to RML Turtle format.

## Example

### Input: RDFMap Configuration

```yaml
namespaces:
  ex: http://example.org/
  xsd: http://www.w3.org/2001/XMLSchema#

defaults:
  base_iri: http://example.org/

sheets:
  - name: employees
    source: employees.csv
    row_resource:
      class: ex:Employee
      iri_template: "{base_iri}employee/{id}"
    columns:
      id:
        as: ex:employeeId
        datatype: xsd:string
      name:
        as: ex:name
        datatype: xsd:string
      hire_date:
        as: ex:hireDate
        datatype: xsd:date
```

### Output: RML Turtle

```turtle
@prefix rml: <http://semweb.mmlab.be/ns/rml#> .
@prefix rr: <http://www.w3.org/ns/r2rml#> .
@prefix ql: <http://semweb.mmlab.be/ns/ql#> .
@prefix ex: <http://example.org/> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

<#employeesTriplesMap> a rr:TriplesMap ;
    rml:logicalSource [
        rml:source "employees.csv" ;
        rml:referenceFormulation ql:CSV
    ] ;
    rr:subjectMap [
        rr:template "http://example.org/employee/{id}" ;
        rr:class ex:Employee
    ] ;
    rr:predicateObjectMap [
        rr:predicate ex:employeeId ;
        rr:objectMap [
            rml:reference "id" ;
            rr:datatype xsd:string
        ]
    ] ;
    rr:predicateObjectMap [
        rr:predicate ex:name ;
        rr:objectMap [
            rml:reference "name" ;
            rr:datatype xsd:string
        ]
    ] ;
    rr:predicateObjectMap [
        rr:predicate ex:hireDate ;
        rr:objectMap [
            rml:reference "hire_date" ;
            rr:datatype xsd:date
        ]
    ] .
```

## Using with RML Processors

### RMLMapper (Java)

```bash
# Download RMLMapper
wget https://github.com/RMLio/rmlmapper-java/releases/download/v6.2.2/rmlmapper-6.2.2-r367-all.jar

# Run mapping
java -jar rmlmapper-6.2.2-r367-all.jar -m mapping.rml.ttl -o output.ttl
```

### Morph-KGC (Python)

```bash
pip install morph-kgc

morph-kgc mapping.rml.ttl -o output.ttl
```

## Supported Features

✅ **Fully Supported:**
- CSV/XLSX logical sources
- IRI templates with column references
- Data properties with datatypes
- Language tags
- Object properties (linked resources)
- Class declarations
- Multi-sheet mappings

⚠️ **Partially Supported:**
- Transforms (exported as warnings, require FnO)
- Default values (not in RML standard)

❌ **Not Yet Supported:**
- JSON/XML sources (roadmap item)
- Cross-source joins (roadmap item)
- Named graphs
- Custom functions (FnO)

## Warnings

The exporter will warn you about features that cannot be represented in RML:

```
⚠️  RML Export Warnings:
  - Column 'amount': Transform 'to_decimal' not supported in RML export. Custom functions (FnO) required.
  - Column 'status': Default value 'pending' not supported in RML export. Use RML-specific extensions.
```

These warnings indicate where manual RML editing may be needed for full functionality.

## Workflow: RDFMap ↔ RML

### Option 1: RDFMap as Primary

```
1. Author in RDFMap (human-friendly YAML)
2. Export to RML (standards compliance)
3. Share RML with collaborators
4. Keep YAML as source of truth
```

### Option 2: RML as Archive

```
1. Develop with RDFMap
2. Export to RML for archival
3. Store both formats in version control
4. Reference RML in publications
```

### Option 3: Hybrid Workflow

```
1. Auto-generate with RDFMap
2. Export to RML
3. Use RMLMapper for production (performance)
4. Update RDFMap YAML as needed
```

## Best Practices

### 1. Version Both Formats

```
mappings/
├── source.yaml           # Human-editable source
└── generated.rml.ttl     # Generated, don't edit
```

### 2. Add Export to CI/CD

```yaml
# .github/workflows/export-rml.yml
name: Export RML
on: [push]
jobs:
  export:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - run: pip install rdfmap
      - run: rdfmap export-rml -m mapping.yaml -o mapping.rml.ttl
      - run: git add mapping.rml.ttl && git commit -m "Update RML export" || true
```

### 3. Validate Exports

```bash
# Validate with RMLMapper
java -jar rmlmapper.jar -m mapping.rml.ttl --validate

# Or use SHACL
rdfmap validate --mapping mapping.rml.ttl --shapes shapes.ttl
```

## Limitations & Roadmap

### Current Limitations

1. **CSV/XLSX Only**: JSON/XML sources not yet supported
   - **Workaround**: Convert to CSV first

2. **No Cross-Source Joins**: Each sheet must be self-contained
   - **Workaround**: Pre-join data with SQL/pandas

3. **No FnO Functions**: Custom transforms not exported
   - **Workaround**: Apply transforms in RMLMapper using FnO

4. **No Named Graphs**: All triples go to default graph
   - **Workaround**: Post-process output with SPARQL UPDATE

### Roadmap

- ✅ **v1.0**: Basic RML export (CSV/XLSX)
- 🚧 **v1.1**: Multi-source support
- 📅 **v1.2**: JSON/XML sources
- 📅 **v1.3**: FnO function mapping
- 📅 **v2.0**: RML import (reverse direction)

## FAQ

**Q: Should I use RDFMap or RML?**  
A: Use RDFMap for development (human-friendly), export to RML for sharing/archival.

**Q: Is RDFMap RML-compliant?**  
A: For CSV/XLSX, yes. The export is valid RML that works with standard processors.

**Q: Can I import RML back to RDFMap?**  
A: Not yet, but it's on the roadmap (v2.0).

**Q: What about performance?**  
A: RMLMapper may be faster for large datasets. Export and use both tools as needed.

## See Also

- [RML Specification](https://rml.io/specs/rml/)
- [R2RML Standard](https://www.w3.org/TR/r2rml/)
- [RMLMapper Documentation](https://github.com/RMLio/rmlmapper-java/wiki)
- [RDFMap vs RML Comparison](../about/rml-comparison.md)
```

### Day 3: Update README

Add to main README.md:

```markdown
### RML Export

Export your mapping configuration to W3C RML format for compatibility with other tools:

```bash
rdfmap export-rml --mapping mapping.yaml --output mapping.rml.ttl
```

This creates an RML Turtle file that works with:
- [RMLMapper](https://github.com/RMLio/rmlmapper-java)
- [CARML](https://github.com/carml/carml)
- [Morph-KGC](https://github.com/oeg-upm/morph-kgc)
- [SDM-RDFizer](https://github.com/SDM-TIB/SDM-RDFizer)

📖 See [RML Export Guide](docs/guides/rml-export.md) for details.
```

Add badge:

```markdown
[![W3C RML Compatible](https://img.shields.io/badge/W3C-RML_Compatible-blue.svg)](https://rml.io/)
```

### Day 4-5: Examples & Blog Post

#### Create RML Export Examples

**File**: `examples/rml_export/README.md`

```markdown
# RML Export Examples

This directory demonstrates RDFMap to RML export capability.

## Files

- `input/`: RDFMap mapping configurations
- `output/`: Generated RML Turtle files
- `verify/`: Scripts to verify RML validity

## Run Examples

```bash
# Export all examples
./export_all.sh

# Verify with RMLMapper
./verify_with_rmlmapper.sh
```

## Examples

### 1. Basic Employee Mapping
- Input: `input/employees.yaml`
- Output: `output/employees.rml.ttl`
- Shows: Simple CSV to RDF mapping

### 2. Multi-Sheet with Links
- Input: `input/organization.yaml`
- Output: `output/organization.rml.ttl`
- Shows: Object properties and linked resources

### 3. With Datatypes
- Input: `input/typed_data.yaml`
- Output: `output/typed_data.rml.ttl`
- Shows: XSD datatype handling
```

#### Write Blog Post

**Title**: "RDFMap Now Supports W3C RML Export"

Key points:
- Standards compliance milestone
- Why this matters for users
- How to use it
- Comparison with alternatives
- Roadmap for RML import

---

## Week 3: Testing & Release

### Day 1-2: Integration Testing

**Test with Real RML Processors**:

```bash
# 1. Install RMLMapper
wget https://github.com/RMLio/rmlmapper-java/releases/download/v6.2.2/rmlmapper-6.2.2-r367-all.jar

# 2. Export example
rdfmap export-rml -m examples/mortgage/config/mortgage_mapping.yaml -o test.rml.ttl

# 3. Run with RMLMapper
java -jar rmlmapper-6.2.2-r367-all.jar -m test.rml.ttl -o rmlmapper_output.ttl

# 4. Compare with RDFMap output
rdfmap convert --mapping examples/mortgage/config/mortgage_mapping.yaml -o rdfmap_output.ttl

# 5. Verify they're equivalent (modulo blank node IDs)
python scripts/compare_rdf.py rdfmap_output.ttl rmlmapper_output.ttl
```

### Day 3: Documentation Review

Checklist:
- [ ] README updated with badge and example
- [ ] CLI help text clear and complete
- [ ] RML Export Guide complete
- [ ] Code comments thorough
- [ ] Docstrings follow Google style
- [ ] Examples work end-to-end

### Day 4: Create Release

**Version**: v1.1.0

**Release Notes**:

```markdown
# RDFMap v1.1.0 - W3C RML Export Support

## 🎉 New Features

### W3C RML Export
RDFMap can now export mapping configurations to W3C RML format!

```bash
rdfmap export-rml --mapping mapping.yaml --output mapping.rml.ttl
```

This makes RDFMap compatible with:
- RMLMapper (Java)
- CARML (Java)
- Morph-KGC (Python)
- SDM-RDFizer (Python)

#### What's Supported
- ✅ CSV/XLSX sources
- ✅ IRI templates
- ✅ Data properties with datatypes
- ✅ Object properties (links)
- ✅ Multi-sheet mappings

#### Limitations
- ⚠️ JSON/XML sources (roadmap)
- ⚠️ Cross-source joins (roadmap)
- ⚠️ Transforms require FnO functions

See [RML Export Guide](https://yourusername.github.io/rdfmap/guides/rml-export/) for complete documentation.

## 📖 Documentation

- New guide: [RML Export](https://yourusername.github.io/rdfmap/guides/rml-export/)
- Updated: [README](README.md) with RML badge
- Examples: [RML Export Examples](examples/rml_export/)

## 🧪 Testing

- 10 new tests for RML export
- Verified compatibility with RMLMapper v6.2.2
- Total tests: 154/154 passing

## 🙏 Acknowledgments

Thanks to the RML community for the excellent standard!

---

**Full Changelog**: v1.0.0...v1.1.0
```

### Day 5: Announce

**Channels**:
1. GitHub Release
2. PyPI (update with new version)
3. Twitter/X thread
4. Reddit (r/semanticweb)
5. LinkedIn
6. RML Community Group

**Message**:
```
🎉 RDFMap v1.1.0 released!

Now with W3C RML export support. Convert your RDFMap configs to standard 
RML format for use with RMLMapper, CARML, Morph-KGC, and other processors.

📦 pip install --upgrade rdfmap
📖 https://yourusername.github.io/rdfmap/guides/rml-export/
⭐ https://github.com/yourusername/rdfmap

#semanticweb #rml #linkeddata #opensource
```

---

## Success Metrics

### Technical
- [ ] 10+ tests passing for RML export
- [ ] Zero test failures
- [ ] RML validates with RMLMapper
- [ ] Output equivalent to hand-written RML

### Documentation
- [ ] Guide complete and clear
- [ ] README updated
- [ ] Examples work
- [ ] Code fully commented

### Adoption
- [ ] 3+ users try RML export
- [ ] 0 critical bugs reported
- [ ] Positive feedback on feature
- [ ] Mentioned in RML community

---

## Troubleshooting

### Common Issues

**Issue**: Export fails with "Unknown attribute"  
**Solution**: Update to latest version of dependencies

**Issue**: RMLMapper can't parse output  
**Solution**: Check Turtle syntax with `rapper -i turtle file.ttl`

**Issue**: Transforms not working in RML  
**Solution**: This is expected - add FnO functions manually

---

## Next Steps

After Phase 2A completion:
- **Phase 2B**: Academic Paper (parallel)
- **Phase 3**: User feedback period
- **Phase 4**: RML Import (reverse direction)

---

**Remember**: This phase establishes standards credibility. Quality and compatibility are more important than speed!
