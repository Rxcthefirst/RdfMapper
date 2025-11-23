# Mortgage Example

This example demonstrates how to convert mortgage loan data from a CSV spreadsheet into RDF triples aligned with a custom mortgage ontology.

## Overview

The example includes:

- **Ontology** (`ontology/mortgage.ttl`): Defines classes and properties for mortgage loans, borrowers, and properties
- **Data** (`data/loans.csv`): Sample mortgage loan records
- **Mapping** (`config/mortgage_mapping.yaml`): Configuration for converting CSV to RDF
- **Shapes** (`shapes/mortgage_shapes.ttl`): SHACL validation rules

## Data Model

### Classes

- `ex:MortgageLoan` - A mortgage loan
- `ex:Borrower` - The person borrowing money
- `ex:Property` - The property used as collateral

### Key Properties

**MortgageLoan properties:**
- `ex:loanNumber` (xsd:string) - Unique loan identifier
- `ex:principalAmount` (xsd:decimal) - Original loan amount
- `ex:interestRate` (xsd:decimal) - Annual interest rate
- `ex:originationDate` (xsd:date) - Date loan was originated
- `ex:hasBorrower` (ObjectProperty) - Links to Borrower
- `ex:collateralProperty` (ObjectProperty) - Links to Property

**Borrower properties:**
- `ex:borrowerName` (xsd:string) - Full name

**Property properties:**
- `ex:propertyAddress` (xsd:string) - Street address

## Running the Example

### Basic Conversion

```bash
cd /path/to/SemanticModelDataMapper

rdfmap convert \
  --mapping examples/mortgage/config/mortgage_mapping.yaml \
  --format ttl \
  --output output/mortgage_ontology.ttl
```

### With Validation

```bash
rdfmap convert \
  --mapping examples/mortgage/config/mortgage_mapping.yaml \
  --ontology examples/mortgage/ontology/mortgage_ontology.ttl \
  --format ttl \
  --output output/mortgage_ontology.ttl \
  --validate \
  --report output/validation_report.json \
  --verbose
```

### Test Configuration

```bash
rdfmap convert \
  --mapping examples/mortgage/config/mortgage_mapping.yaml \
  --limit 2 \
  --dry-run \
  --verbose
```

## Expected Output

### Turtle Format

```turtle
@prefix ex: <https://example.com/mortgage#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

<https://data.example.com/loan/L-1001> a ex:MortgageLoan ;
    ex:loanNumber "L-1001"^^xsd:string ;
    ex:principalAmount "250000"^^xsd:decimal ;
    ex:interestRate "0.0525"^^xsd:decimal ;
    ex:originationDate "2023-06-15"^^xsd:date ;
    ex:loanTerm "360"^^xsd:integer ;
    ex:loanStatus "Active" ;
    ex:hasBorrower <https://data.example.com/borrower/B-9001> ;
    ex:collateralProperty <https://data.example.com/property/P-7001> .

<https://data.example.com/borrower/B-9001> a ex:Borrower ;
    ex:borrowerName "Alex Morgan" .

<https://data.example.com/property/P-7001> a ex:Property ;
    ex:propertyAddress "12 Oak St" .
```

## Mapping Configuration Explained

### IRI Templates

```yaml
row_resource:
  class: ex:MortgageLoan
  iri_template: "{base_iri}loan/{LoanID}"
```

This creates IRIs like `https://data.example.com/loan/L-1001` using the `base_iri` default and the `LoanID` column value.

### Data Transformations

```yaml
columns:
  Principal:
    as: ex:principalAmount
    datatype: xsd:decimal
    transform: to_decimal
```

The `to_decimal` transform:
- Removes currency symbols and commas
- Converts to proper decimal representation
- Ensures correct XSD datatype

### Linked Objects

```yaml
objects:
  borrower:
    predicate: ex:hasBorrower
    class: ex:Borrower
    iri_template: "{base_iri}borrower/{BorrowerID}"
    properties:
      - column: BorrowerName
        as: ex:borrowerName
        datatype: xsd:string
```

This creates a separate `Borrower` resource and links it to the loan via the `ex:hasBorrower` property.

## Validation Rules

The SHACL shapes enforce:

1. **Required Properties**: Each loan must have a loan number, principal, interest rate, and origination date
2. **Cardinality**: Exactly one principal amount, one origination date
3. **Data Types**: Correct XSD datatypes for all properties
4. **Value Ranges**: Interest rate between 0 and 1, principal > 0
5. **Links**: Each loan must have at least one borrower and exactly one property

## Extending the Example

### Add More Data

Edit `data/loans.csv` to add more loan records:

```csv
L-1006,B-9006,New Borrower,P-7006,123 New St,400000,0.0450,2023-12-01,360,Active
```

### Add New Properties

1. **Update the Ontology** (`ontology/mortgage.ttl`):

```turtle
ex:loanOfficer a owl:DatatypeProperty ;
    rdfs:label "loan officer"@en ;
    rdfs:domain ex:MortgageLoan ;
    rdfs:range xsd:string .
```

2. **Add Column to CSV**:

```csv
LoanID,BorrowerID,BorrowerName,...,LoanOfficer
L-1001,B-9001,Alex Morgan,...,Jane Smith
```

3. **Update Mapping** (`config/mortgage_mapping.yaml`):

```yaml
columns:
  LoanOfficer:
    as: ex:loanOfficer
    datatype: xsd:string
```

### Add Validation Rules

Edit `shapes/mortgage_shapes.ttl`:

```turtle
ex:MortgageLoanShape
    sh:property [
        sh:path ex:loanOfficer ;
        sh:datatype xsd:string ;
        sh:minCount 1 ;
        sh:message "Loan officer is required" ;
    ] .
```

## Troubleshooting

### Common Issues

1. **File Paths**: Ensure paths in mapping config are relative to the config file location
2. **Column Names**: CSV column names are case-sensitive and must match exactly
3. **Data Types**: Use appropriate transforms (to_decimal, to_date) for non-string data
4. **Validation Failures**: Check validation report for specific issues

### Validation Report Example

If validation fails, you'll see:

```json
{
  "conforms": false,
  "results": [
    {
      "focus_node": "https://data.example.com/loan/L-1001",
      "result_path": "ex:principalAmount",
      "result_message": "Value must be greater than 0",
      "severity": "Violation"
    }
  ]
}
```

## Next Steps

Use this example as a template for your own data:

1. Create your ontology in Turtle format
2. Prepare your data in CSV/XLSX
3. Write a mapping configuration following this example
4. Define SHACL shapes for validation
5. Run the converter and iterate

For more details, see the main README and QUICKSTART guide.
