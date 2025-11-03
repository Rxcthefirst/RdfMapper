# Understanding `--ontology` vs `--import` in Semantic Model Data Mapper

## The Key Difference

The distinction between `--ontology` and `--import` is **fundamental to the architecture** of semantic mapping:

### `--ontology` (Primary Domain Ontology)
- **Role**: The **authoritative domain model** 
- **Contains**: The target class you're mapping to (specified with `--class`)
- **Purpose**: Defines the **core business concepts** specific to your domain
- **Requirement**: **Exactly one** must be specified
- **Example**: `hr_domain.ttl` containing Employee, Department, Position classes

### `--import` (Supporting Vocabularies)  
- **Role**: **Supplementary vocabularies** that extend the primary ontology
- **Contains**: Reusable properties and classes from other domains
- **Purpose**: Provides **common, shared concepts** across multiple domains
- **Requirement**: **Zero or more** can be specified
- **Examples**: `shared_person.ttl`, `contact_info.ttl`, FOAF, Dublin Core, Schema.org

## Practical Demonstration

Our demonstration showed:

```
PRIMARY ONTOLOGY (--ontology):
  ✓ 1 class (Employee - the target class)
  ✓ 2 properties (hasEmployeeID, hasSalary - domain-specific)

IMPORTED ONTOLOGY (--import):
  ✓ 1 class (Person - reusable concept)  
  ✓ 2 properties (hasFirstName, hasLastName - common properties)

COMBINED RESULT:
  ✓ 2 classes total
  ✓ 4 properties total
  ✓ Richer vocabulary for better semantic mapping
```

## Why This Separation Matters

### 1. **Domain Authority**
- The `--ontology` establishes **what domain you're working in**
- The target class **must come from the primary ontology**
- This ensures semantic consistency and domain ownership

### 2. **Vocabulary Reuse**
- `--import` allows you to **leverage existing vocabularies**
- No need to reinvent common concepts like "firstName" or "email"
- Promotes **interoperability** with other systems

### 3. **Modular Architecture**
- Keep domain-specific concepts in the primary ontology
- Share common concepts through imports
- **Easier maintenance** and **better organization**

## CLI Usage Examples

### Basic Usage (Primary Ontology Only)
```bash
rdfmap generate \
  --ontology hr_domain.ttl \     # Contains Employee class and HR properties
  --data employees.csv \
  --class "Employee"
```

### Enhanced Usage (With Imports)
```bash  
rdfmap generate \
  --ontology hr_domain.ttl \          # Primary: Employee, Department classes
  --import shared_person.ttl \        # Common person properties
  --import contact_info.ttl \         # Contact information properties  
  --import http://xmlns.com/foaf/0.1/ # FOAF vocabulary
  --data employees.csv \
  --class "Employee"                  # Target class from PRIMARY ontology
```

### Enterprise Usage (Multiple Standards)
```bash
rdfmap generate \
  --ontology product_catalog.ttl \
  --import http://schema.org/ontology.ttl \
  --import http://purl.org/dc/terms/ \
  --import http://xmlns.com/foaf/0.1/ \
  --data products.csv \
  --class "Product"
```

## Mapping Generation Impact

When generating mappings, the system considers **ALL properties** from primary + imported ontologies:

```yaml
# Generated mapping uses properties from both sources
columns:
  employee_id:
    as: hr:hasEmployeeID        # From PRIMARY ontology
  first_name:
    as: shared:hasFirstName     # From IMPORTED ontology
  salary:
    as: hr:hasSalary           # From PRIMARY ontology
  email:
    as: foaf:mbox              # From IMPORTED FOAF ontology
```

## Best Practices

### ✅ **Do**
- Use `--ontology` for your domain-specific business model
- Use `--import` for common, reusable vocabularies
- Import standard vocabularies (FOAF, Dublin Core, Schema.org)
- Keep primary ontologies focused on domain concepts

### ❌ **Don't**  
- Mix domain concepts in imported ontologies
- Duplicate common properties in primary ontologies
- Use imports as primary ontologies
- Forget to specify the target class in the primary ontology

## Summary

| Aspect | `--ontology` | `--import` |
|--------|-------------|------------|
| **Quantity** | Exactly one | Zero or more |
| **Role** | Domain authority | Vocabulary extension |
| **Target Class** | Must contain it | Provides additional properties |
| **Scope** | Domain-specific | Cross-domain reusable |
| **Purpose** | Business model | Common concepts |

**The `--ontology` flag establishes your domain authority, while `--import` flags provide vocabulary extensions to create comprehensive semantic mappings.**
