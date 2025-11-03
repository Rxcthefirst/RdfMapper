# Ontology Imports Example

This directory demonstrates the ontology imports feature, which allows you to reference classes and properties from multiple ontology files in your mapping configurations.

## Files

- `core_ontology.ttl` - Main domain ontology (HR concepts)
- `shared_ontology.ttl` - Shared/imported ontology (common concepts)
- `employees_with_imports.csv` - Sample employee data
- `mapping_with_imports.yaml` - Mapping configuration using imports
- `README.md` - This file

## Usage

1. Generate mapping with imports:
```bash
rdfmap generate \
  --ontology core_ontology.ttl \
  --import shared_ontology.ttl \
  --data employees_with_imports.csv \
  --class "Employee" \
  --output mapping_with_imports.yaml
```

2. Convert data to RDF:
```bash
rdfmap convert \
  --mapping mapping_with_imports.yaml \
  --format ttl \
  --output employees_output.ttl
```

## Benefits of Imports

- **Reusability**: Share common ontologies across projects
- **Modularity**: Separate domain-specific and general concepts  
- **Namespace Management**: Proper namespace resolution across ontologies
- **Semantic Alignment**: Access to properties from multiple sources for better matching
