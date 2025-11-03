# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-11-02

### 🎉 Initial Release

This is the first public release of RDFMap - Semantic Model Data Mapper.

### ✨ Features

#### **Multi-Format Data Sources**
- **CSV/TSV Support**: Standard delimited files with configurable separators
- **Excel (XLSX) Support**: Multi-sheet workbooks with automatic type detection  
- **JSON Support**: Complex nested structures with automatic array expansion
- **XML Support**: Structured document parsing with namespace awareness

#### **Intelligent Semantic Mapping**
- **SKOS-Based Column Matching**: Automatic alignment using SKOS preferred, alternative, and hidden labels
- **Ontology Import System**: Modular architecture with `--import` flag for reusable vocabularies
- **Semantic Alignment Reports**: Confidence scoring and mapping quality metrics
- **OWL2 Best Practices**: NamedIndividual declarations and W3C standards compliance

#### **Advanced Data Processing**
- **IRI Templating**: Deterministic, idempotent IRI construction with Python-style formatting
- **Data Transformations**: Built-in transforms (to_decimal, to_date, to_boolean, etc.)
- **Complex JSON Arrays**: Automatic expansion of nested array structures
- **Cross-Sheet Linking**: Object property mappings with multi-valued support

#### **Enterprise Features**
- **Multiple RDF Formats**: Turtle, RDF/XML, JSON-LD, N-Triples output
- **SHACL Validation**: Comprehensive RDF validation against ontology shapes
- **Batch Processing**: Efficient handling of 100k+ row datasets
- **Error Reporting**: Detailed validation and processing reports

#### **CLI Commands**
- **`rdfmap convert`**: Convert data files to RDF using mapping configurations
- **`rdfmap generate`**: Auto-generate mapping configurations from ontologies and data
- **`rdfmap validate`**: Validate RDF files against SHACL shapes
- **`rdfmap info`**: Display mapping configuration information

### 🔧 Technical Implementation

#### **Architecture**
- **Configuration-Driven**: Declarative YAML/JSON mapping specifications
- **Modular Design**: Clear separation of parsing, transformation, and RDF emission
- **Pydantic Models**: Type-safe configuration validation
- **RDFLib Integration**: Robust RDF graph construction and serialization

#### **Dependencies**
- Python 3.11+ (tested with Python 3.13)
- rdflib >= 7.0.0 (RDF processing)
- pandas >= 2.1.0 (data manipulation)
- pydantic >= 2.5.0 (data validation)
- pyshacl >= 0.25.0 (SHACL validation)
- typer >= 0.9.0 (CLI framework)

### 📊 **Test Coverage**
- **144 test cases** covering all major functionality
- **58% code coverage** with focus on core business logic
- **Integration tests** for real-world examples (mortgage, HR data)
- **End-to-end workflow testing** from data input to RDF output

### 📚 **Documentation**
- Comprehensive README with quickstart guide
- Detailed CLI reference and examples
- Configuration schema documentation
- Architecture overview and extension guide

### 🌟 **Key Benefits**
- **Standards Compliant**: Full OWL2 and W3C RDF support
- **Enterprise Ready**: Scalable processing with robust error handling
- **Developer Friendly**: Rich CLI, comprehensive docs, extensible architecture
- **Semantic Intelligence**: SKOS-based automatic mapping reduces manual configuration

### 🎯 **Use Cases**
- **Data Integration**: Convert legacy data to semantic web formats
- **Knowledge Graph Construction**: Build RDF knowledge bases from tabular data  
- **Ontology Population**: Populate ontologies with instance data
- **Data Migration**: Migrate between different data representation formats
- **Semantic Data Publishing**: Create Linked Data from existing datasets

---

**Full Documentation**: https://rdfmap.readthedocs.io/  
**Repository**: https://github.com/rdfmap/rdfmap  
**PyPI Package**: https://pypi.org/project/rdfmap/
