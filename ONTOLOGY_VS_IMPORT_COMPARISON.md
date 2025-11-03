# `--ontology` vs `--import` Flag Comparison

## Key Differences

### `--ontology` Flag (Primary Ontology)
- **Purpose**: Specifies the **main domain ontology** that defines the target class and primary vocabulary
- **Role**: The **authoritative source** for the domain being mapped
- **Usage**: Required parameter - you must specify exactly one primary ontology
- **Mapping Target**: Contains the target class specified with `--class` parameter
- **Semantic Role**: Defines the **core domain model** and business logic

### `--import` Flag (Auxiliary Ontologies)  
- **Purpose**: Specifies **additional ontologies** to supplement the primary ontology
- **Role**: **Supporting vocabularies** that provide common properties and classes
- **Usage**: Optional parameter - you can specify zero or more imports
- **Mapping Source**: Provides additional properties that can be referenced in mappings
- **Semantic Role**: Provides **reusable, shared vocabularies** across domains

## Practical Example

```bash
# Primary ontology defines HR domain concepts
rdfmap generate \
  --ontology hr_domain.ttl \          # Main ontology: Employee, Department classes
  --import shared_person.ttl \        # Common person properties: firstName, lastName
  --import contact_info.ttl \         # Contact properties: email, phone
  --import dublin_core.ttl \          # Metadata properties: created, modified
  --data employees.csv \
  --class "Employee" \                # Target class from PRIMARY ontology
  --output mapping.yaml
```

## Architecture Comparison

### Without Imports (Single Ontology)
```
hr_domain.ttl (contains everything)
├── Employee class
├── Department class  
├── hasEmployeeID property
├── hasFirstName property
├── hasLastName property
├── hasEmail property
├── hasPhone property
└── hasSalary property
```

### With Imports (Modular Architecture)
```
hr_domain.ttl (primary - HR-specific)
├── Employee class
├── Department class
├── hasEmployeeID property
└── hasSalary property

shared_person.ttl (imported - reusable)
├── Person class
├── hasFirstName property
└── hasLastName property

contact_info.ttl (imported - reusable)
├── ContactInfo class
├── hasEmail property
└── hasPhone property
```

## Benefits of This Separation

### 1. **Domain Separation**
- **Primary ontology**: Domain-specific business concepts
- **Imported ontologies**: General-purpose, reusable concepts

### 2. **Reusability**
- Share common vocabularies across multiple projects
- Standard ontologies (FOAF, Dublin Core, Schema.org) can be imported

### 3. **Maintenance**
- Update shared vocabularies independently
- Domain ontologies stay focused on business logic

### 4. **Standards Compliance**
- Import industry-standard vocabularies
- Ensure interoperability with other systems

## Mapping Generation Behavior

### Properties Available for Mapping
The mapping generator considers properties from **ALL** ontologies:
- Primary ontology properties: `hr:hasEmployeeID`, `hr:hasSalary`
- Imported ontology properties: `shared:hasFirstName`, `contact:hasEmail`

### Namespace Resolution  
All imported ontologies contribute to namespace resolution:
```yaml
namespaces:
  hr: http://example.org/hr#           # From primary ontology
  shared: http://example.org/shared#   # From imported ontology
  contact: http://example.org/contact# # From imported ontology
  
imports:
  - shared_person.ttl
  - contact_info.ttl
```

## Real-World Use Cases

### 1. **Enterprise Vocabulary Management**
```bash
# Each department has domain ontology + shared enterprise vocabulary
rdfmap generate \
  --ontology finance_domain.ttl \
  --import enterprise_common.ttl \
  --import accounting_standards.ttl
```

### 2. **Standards Compliance**
```bash
# Import W3C/industry standard vocabularies
rdfmap generate \
  --ontology product_catalog.ttl \
  --import http://schema.org/ontology.ttl \
  --import http://purl.org/dc/terms/
```

### 3. **Incremental Development**
```bash
# Start with basic ontology, add capabilities through imports
rdfmap generate \
  --ontology basic_hr.ttl \
  --import advanced_reporting.ttl \
  --import compliance_framework.ttl
```

## Summary

| Aspect | `--ontology` | `--import` |
|--------|-------------|------------|
| **Quantity** | Exactly one | Zero or more |
| **Role** | Primary domain model | Supporting vocabularies |
| **Target Class** | Must contain target class | Provides additional properties |
| **Purpose** | Domain authority | Vocabulary extension |
| **Required** | Yes | No |
| **Namespace** | Primary namespace | Additional namespaces |

The `--ontology` flag establishes the **domain authority** while `--import` flags provide **vocabulary extensions** - they work together to create a comprehensive semantic mapping environment.
