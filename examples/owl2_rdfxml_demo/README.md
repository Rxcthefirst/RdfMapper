# OWL2 RDF/XML Demonstration

This demonstration shows how to use the Semantic Model Data Mapper with proper OWL2 ontologies and RDF/XML serialization formats.

## Overview

This demo illustrates:
1. **OWL2 Ontology Consumption**: Loading a proper OWL2 ontology with rich semantics
2. **Semantic Data Mapping**: Mapping CSV data to OWL2 classes and properties
3. **RDF/XML Output**: Generating semantic data in RDF/XML format
4. **OWL2 Standards Compliance**: Using proper OWL2 constructs and annotations

## Demo Components

### 1. OWL2 Ontology (`ontology/university_owl2.rdf`)
A comprehensive university domain ontology featuring:
- **OWL2 Classes**: Person, Student, Professor, Course, Department
- **OWL2 Properties**: Object and datatype properties with domains/ranges
- **OWL2 Annotations**: Proper RDFS/OWL annotations and SKOS labels
- **OWL2 Restrictions**: Property restrictions and cardinality constraints
- **OWL2 Axioms**: Class hierarchies and property hierarchies

### 2. Sample Data (`data/students.csv`)
University student data with:
- Student IDs, names, and contact information
- Course enrollments and grades
- Department affiliations
- Academic status information

### 3. Generated Outputs
- **Mapping Configuration**: YAML mapping from CSV to OWL2 classes
- **RDF/XML Data**: Semantic data instances in RDF/XML format
- **Alignment Report**: Analysis of mapping quality with ontology context

## Usage

### Basic Workflow

```bash
# 1. Generate mapping configuration
rdfmap generate \
  --ontology ontology/university_owl2.rdf \
  --spreadsheet data/students.csv \
  --class http://example.org/university#Student \
  --output mapping.yaml \
  --alignment-report

# 2. Convert data to RDF/XML
rdfmap convert \
  --mapping mapping.yaml \
  --format rdfxml \
  --output students_data.rdf

# 3. Validate generated RDF/XML
rdfmap validate \
  --data students_data.rdf \
  --ontology ontology/university_owl2.rdf
```

### Advanced Features

```bash
# Generate with comprehensive alignment analysis
rdfmap generate \
  --ontology ontology/university_owl2.rdf \
  --spreadsheet data/students.csv \
  --class http://example.org/university#Student \
  --output mapping.yaml \
  --alignment-report \
  --include-comments \
  --auto-detect-relationships

# Convert with validation and pretty formatting
rdfmap convert \
  --mapping mapping.yaml \
  --format rdfxml \
  --output students_data.rdf \
  --validate \
  --pretty-print

# Analyze ontology coverage
rdfmap validate-ontology \
  --ontology ontology/university_owl2.rdf \
  --min-coverage 0.8 \
  --output coverage_report.json \
  --verbose
```

## Expected Outputs

### 1. Mapping Configuration (mapping.yaml)
```yaml
namespaces:
  owl: http://www.w3.org/2002/07/owl#
  rdf: http://www.w3.org/1999/02/22-rdf-syntax-ns#
  rdfs: http://www.w3.org/2000/01/rdf-schema#
  uni: http://example.org/university#
  
defaults:
  base_iri: http://example.org/data/

sheets:
- name: students
  source: data/students.csv
  row_resource:
    class: uni:Student
    iri_template: student:{student_id}
  columns:
    student_id:
      as: uni:hasStudentID
      datatype: xsd:string
    first_name:
      as: uni:hasFirstName
      datatype: xsd:string
    # ... more mappings
```

### 2. RDF/XML Output (students_data.rdf)
```xml
<?xml version="1.0" encoding="UTF-8"?>
<rdf:RDF
    xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
    xmlns:owl="http://www.w3.org/2002/07/owl#"
    xmlns:rdfs="http://www.w3.org/2000/01/rdf-schema#"
    xmlns:uni="http://example.org/university#">
    
  <uni:Student rdf:about="http://example.org/data/student/S001">
    <uni:hasStudentID>S001</uni:hasStudentID>
    <uni:hasFirstName>Alice</uni:hasFirstName>
    <uni:hasLastName>Johnson</uni:hasLastName>
    <uni:hasEmail>alice.johnson@university.edu</uni:hasEmail>
    <uni:enrolledIn rdf:resource="http://example.org/data/course/CS101"/>
    <uni:memberOf rdf:resource="http://example.org/data/department/ComputerScience"/>
  </uni:Student>
  
  <!-- More instances... -->
</rdf:RDF>
```

### 3. Alignment Report
Comprehensive analysis including:
- Mapping success rates and confidence scores
- Unmapped columns with ontology context
- SKOS enrichment suggestions
- OWL2 property and class information
- Related classes and object properties

## OWL2 Standards Compliance

This demonstration ensures:
- **Proper OWL2 Namespaces**: Uses standard OWL2, RDFS, and SKOS namespaces
- **Valid OWL2 Constructs**: Classes, properties, restrictions, and annotations
- **RDF/XML Serialization**: Compliant with W3C RDF/XML specification
- **Semantic Correctness**: Proper use of domains, ranges, and cardinalities
- **Annotation Properties**: Rich metadata using standard annotation properties

## Files Generated

- `mapping.yaml` - Mapping configuration
- `students_data.rdf` - RDF/XML semantic data
- `alignment_report.json` - Mapping analysis
- `coverage_report.json` - Ontology coverage analysis
- `validation_report.json` - RDF validation results

## Integration with Ontology Tools

The generated RDF/XML can be used with:
- **Protégé**: Load and visualize the semantic data
- **Apache Jena**: Process with SPARQL queries
- **OWL API**: Programmatic access and reasoning
- **Semantic Web frameworks**: Integration with linked data platforms

## Performance Metrics

Expected performance for the demo:
- **Mapping Success Rate**: 85-95% with proper OWL2 ontology
- **RDF/XML Generation**: Fast serialization with validation
- **Ontology Coverage**: High coverage with rich SKOS labels
- **Standards Compliance**: Full OWL2 and RDF/XML compliance
