# Enhanced YAML Output - With Template Sections

## What Was Added

The YAML formatter now includes **commented template sections** for all available features, making the configuration file self-documenting.

---

## Complete Output Structure

```yaml
# ════════════════════════════════════════════════════════════════════════════════
# RDFMap Mapping Configuration
# ════════════════════════════════════════════════════════════════════════════════
# [Header with helpful information]

namespaces:
  ex: https://example.com/mortgage#
  xsd: http://www.w3.org/2001/XMLSchema#
  rdfs: http://www.w3.org/2000/01/rdf-schema#

defaults:
  base_iri: http://example.org/

sheets:
  - name: loans
    source: examples/mortgage/data/loans.csv
    
    # Main resource configuration
    row_resource:
      class: ex:MortgageLoan
      iri_template: "{base_iri}mortgage_loan/{LoanID}"
    
    # Column mappings (data properties)
    columns:
      LoanID:
        as: ex:loanNumber
        datatype: xsd:string
        required: true
      # ... more columns ...

    # Linked objects (object properties)
    objects:
      has borrower:
        predicate: ex:hasBorrower
        class: ex:Borrower
        iri_template: "{base_iri}borrower/{BorrowerID}"
        properties:
          - column: BorrowerName
            as: ex:borrowerName
            datatype: xsd:string
            required: true

# Processing options
options:
  on_error: "report"
  skip_empty_values: true

# ────────────────────────────────────────────────────────────────────────────────
# Validation Configuration (Optional)
# ────────────────────────────────────────────────────────────────────────────────
# Uncomment to enable SHACL validation during conversion:
#
# validation:
#   shacl:
#     enabled: true
#     shapes_file: path/to/shapes.ttl
#     inference: none  # Options: none, rdfs, owlrl
#
# This validates generated RDF against SHACL shapes to catch:
#   - Missing required properties
#   - Invalid data types
#   - Cardinality violations
#   - Domain/range mismatches
#

# ────────────────────────────────────────────────────────────────────────────────
# Ontology Imports (Optional)
# ────────────────────────────────────────────────────────────────────────────────
# Uncomment to import additional ontologies:
#
# imports:
#   - path/to/external_ontology.ttl
#   - path/to/another_ontology.owl
#
# Use this when your ontology references external vocabularies like:
#   - FOAF (Friend of a Friend)
#   - Dublin Core
#   - Schema.org
#   - Domain-specific ontologies
#

# ────────────────────────────────────────────────────────────────────────────────
# Advanced Features (Optional)
# ────────────────────────────────────────────────────────────────────────────────
#
# Multi-valued Cells:
#   columns:
#     Tags:
#       as: ex:hasTag
#       multi_valued: true
#       separator: ","  # Split "tag1,tag2,tag3" into multiple values
#
# Conditional Mapping:
#   columns:
#     Status:
#       as: ex:status
#       condition:
#         when: "value == 'Active'"
#         then: "ex:ActiveStatus"
#
# Custom Transforms:
#   columns:
#     Amount:
#       as: ex:amount
#       transform: "lambda x: float(x.replace('$', '').replace(',', ''))"
#
# Composite Keys:
#   row_resource:
#     class: ex:Transaction
#     iri_template: "{base_iri}transaction/{Date}/{AccountID}/{TransactionID}"
#
# Language Tags:
#   columns:
#     Name:
#       as: ex:name
#       language: "en"  # Add @en language tag
#
# Null Handling:
#   columns:
#     OptionalField:
#       as: ex:optional
#       skip_if_empty: true  # Don't create triple if value is null/empty
#

# ────────────────────────────────────────────────────────────────────────────────
# Additional Processing Options
# ────────────────────────────────────────────────────────────────────────────────
#
# options:
#   # CSV/TSV specific:
#   delimiter: ","           # Field separator (default: ',')
#   quote_char: '"'          # Quote character (default: '"')
#   header: true            # First row contains headers (default: true)
#   encoding: "utf-8"        # File encoding (default: 'utf-8')
#
#   # Memory management:
#   chunk_size: 1000        # Process data in chunks (for large files)
#   streaming: false        # Enable streaming mode (constant memory)
#
#   # Error handling:
#   on_error: "report"       # Options: report, skip, stop
#   skip_empty_values: true # Don't create triples for empty/null values
#   strict_mode: false      # Fail on any validation error
#
#   # Performance:
#   parallel: false         # Enable parallel processing
#   workers: 4              # Number of worker threads
#   batch_size: 10000       # RDF write batch size
#
#   # Output:
#   pretty_print: true      # Format output for readability
#   compression: "gzip"      # Compress output (gzip, bz2, xz)
#

# ════════════════════════════════════════════════════════════════════════════════
# Usage Examples
# ════════════════════════════════════════════════════════════════════════════════
#
# Test with sample data (dry run):
#   rdfmap convert --mapping <this-file> --limit 10 --dry-run
#
# Convert with validation:
#   rdfmap convert --mapping <this-file> --validate
#
# Convert to specific format:
#   rdfmap convert --mapping <this-file> --format nt --output output.nt
#
# Process large file with streaming:
#   rdfmap convert --mapping <this-file> --streaming --chunk-size 50000
#
# Generate validation report:
#   rdfmap convert --mapping <this-file> --validate --report validation.json
#
# For more information:
#   rdfmap convert --help
#   https://github.com/YourOrg/RDFMap/docs
#
# ════════════════════════════════════════════════════════════════════════════════
```

---

## Benefits

### 1. **Self-Documenting**
Users don't need to look up documentation - everything is explained right in the file.

### 2. **Feature Discovery**
Users learn about advanced features they might not know about:
- Multi-valued cells
- Conditional mapping
- Custom transforms
- Language tags
- Streaming mode
- Validation

### 3. **Copy-Paste Ready**
All templates are ready to uncomment and customize:
```yaml
# Just uncomment and modify:
# validation:
#   shacl:
#     enabled: true
#     shapes_file: my_shapes.ttl
```

### 4. **Consistent Across Generation Methods**
Whether generated via:
- `rdfmap init` (wizard)
- `rdfmap generate` (direct command)
- Manual creation

All methods produce the same comprehensive, self-documenting format.

---

## Template Sections Added

### 1. **Validation Configuration**
Shows how to enable SHACL validation with shapes files.

### 2. **Ontology Imports**
Explains how to import external ontologies (FOAF, Dublin Core, etc.)

### 3. **Advanced Features**
Comprehensive examples of:
- Multi-valued cells (splitting comma-separated values)
- Conditional mapping (if-then logic)
- Custom transforms (lambda functions)
- Composite keys (multi-column IRIs)
- Language tags (@en, @fr, etc.)
- Null handling (skip empty values)

### 4. **Processing Options Reference**
Complete list of all available options with defaults:
- CSV/TSV settings
- Memory management
- Error handling
- Performance tuning
- Output formatting

### 5. **Usage Examples**
Common commands for:
- Testing with sample data
- Validation
- Format conversion
- Large file processing
- Report generation

---

## Implementation

**File Modified:** `src/rdfmap/generator/yaml_formatter.py`

**Method Added:** `_write_template_sections()`

**Logic:**
1. Check what's already configured (validation, imports)
2. Add commented templates for unconfigured features
3. Always add advanced features reference
4. Always add processing options reference
5. Always add usage examples

**Smart Behavior:**
- If validation is already configured → Skip validation template
- If imports are already configured → Skip imports template
- Always include advanced features and usage examples

---

## User Experience

### Before
```yaml
# Basic config with no guidance
namespaces:
  ex: https://example.com/mortgage#
  
columns:
  LoanID:
    as: ex:loanNumber

options:
  on_error: report
```

Users had to:
- Read documentation separately
- Search for feature examples
- Remember all available options

### After
```yaml
# Basic config PLUS comprehensive templates
namespaces:
  ex: https://example.com/mortgage#
  
columns:
  LoanID:
    as: ex:loanNumber

options:
  on_error: report

# ────────────────────────────────────────────────────────────────────────────────
# Validation Configuration (Optional)
# ────────────────────────────────────────────────────────────────────────────────
# [Full template with explanations]

# ────────────────────────────────────────────────────────────────────────────────
# Advanced Features (Optional)
# ────────────────────────────────────────────────────────────────────────────────
# [All features with examples]
```

Users can:
- Learn by reading the file
- Discover features inline
- Copy-paste templates
- Understand options immediately

---

## Impact

✅ **Better User Experience** - Self-documenting configurations  
✅ **Faster Learning** - Examples right in the file  
✅ **Feature Discovery** - Users learn what's possible  
✅ **Reduced Support** - Less "how do I..." questions  
✅ **Professional Quality** - Comprehensive, polished output  
✅ **Consistency** - Same format everywhere  

---

## Next Steps

The enhancement is complete and will be applied to:
- ✅ `rdfmap init` (wizard-generated configs)
- ✅ `rdfmap generate` (direct generation)
- ✅ All YAML output from the formatter

**The generated configurations are now self-documenting and comprehensive!** 🎉

