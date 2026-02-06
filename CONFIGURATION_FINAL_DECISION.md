# Configuration Format Evolution - Final Decision

**Date**: December 9, 2025  
**Decision**: Define universal, intuitive configuration format for all data types

---

## Problem Statement

Current format uses `sheets` which implies spreadsheets only, but we need to support:
- CSV, TSV, Excel (tabular)
- JSON (nested structures)
- XML (hierarchical with attributes)
- SQL databases
- APIs
- Any RML-compatible source

**Question**: What terminology best represents universal data mapping?

---

## YARRRML Standard (Our Inspiration)

YARRRML is the YAML-based syntax for RML that we should align with:

```yaml
prefixes:
  ex: https://example.com/
  
base: http://example.org/

sources:
  persons:
    - data/persons.csv~csv
  companies:
    - data/companies.json~jsonpath
    - $.companies[*]

mappings:
  person:
    sources: persons
    s: http://example.org/person/$(ID)
    po:
      - [a, ex:Person]
      - [ex:name, $(name)]
      - [ex:age, $(age), xsd:integer]
```

**Key Terminology**:
- ✅ `sources` - universal term for data sources
- ✅ `mappings` - transformation rules
- ✅ Supports iterators for nested data (JSONPath, XPath)

---

## Proposed RDFMap Configuration Format (v3)

### Core Structure

```yaml
# Standard RML/YARRRML compatibility
namespaces: {...}
base_iri: http://example.org/

sources:
  <source_name>:
    - <path/connection>
    - <format>
    - <iterator>  # Optional: JSONPath, XPath, etc.

mappings:
  <mapping_name>:
    sources: <source_ref>
    subject:
      iri_template: "..."
      class: "..."
    properties: {...}
    relationships: {...}  # Nested entities

# RDFMap enhancements (optional)
validation: {...}
options: {...}
imports: [...]
```

### Key Design Decisions

#### 1. **`sources` NOT `sheets`**
**Rationale**: Universal term that works for all data types
- ✅ CSV file = source
- ✅ JSON API = source
- ✅ XML document = source
- ✅ Database table = source
- ✅ Excel sheet = source

#### 2. **`mappings` NOT `sheets[].mapping`**
**Rationale**: Follows RML/YARRRML standard, clearer separation
- Each mapping is independent
- One source can have multiple mappings
- Multiple sources can feed one mapping

#### 3. **`subject` instead of `row_resource`**
**Rationale**: RML terminology, more universal
- Row implies tabular data
- Subject works for any source type

#### 4. **`properties` for data properties (literals)**
**Rationale**: Clear distinction from relationships

#### 5. **`relationships` for object properties**
**Rationale**: More intuitive than `objects` which is ambiguous
- Clearly indicates connections between entities
- Contains nested entity definitions

---

## Format Comparison

### Old Format (v1 - DEPRECATED)
```yaml
sheets:  # ❌ Implies spreadsheets only
  - name: loans
    class: ex:Loan  # Direct
    columns: [...]  # ❌ List format
```

### Current Format (v2 - IN PROGRESS)
```yaml
sheets:  # ❌ Still implies spreadsheets
  - name: loans
    row_resource:  # ❌ Implies tabular rows
      class: ex:Loan
    properties: {...}  # ✅ Dict format
    objects: {...}  # ⚠️ Ambiguous term
```

### Proposed Format (v3 - RECOMMENDED)
```yaml
sources:  # ✅ Universal
  loans_data:
    - data.csv
    - csv

mappings:  # ✅ Clear purpose
  Loan:
    sources: loans_data
    subject:  # ✅ RML standard term
      iri_template: "..."
      class: ex:Loan
    properties: {...}  # ✅ Data properties
    relationships: {...}  # ✅ Clear meaning
```

---

## Examples: Universal Support

### CSV Example
```yaml
sources:
  employees:
    - employees.csv
    - csv

mappings:
  Employee:
    sources: employees
    subject:
      iri_template: "{base_iri}employee/{EmployeeID}"
      class: ex:Employee
    properties:
      Name:
        predicate: ex:name
        datatype: xsd:string
```

### JSON Example (Nested)
```yaml
sources:
  orders:
    - orders.json
    - json
    - $.orders[*]  # JSONPath iterator

mappings:
  Order:
    sources: orders
    subject:
      iri_template: "{base_iri}order/{id}"
      class: ex:Order
    properties:
      id:
        predicate: ex:orderNumber
      items.*.productName:  # Nested path
        predicate: ex:hasProduct
```

### XML Example (Hierarchical)
```yaml
sources:
  products:
    - products.xml
    - xml
    - //product  # XPath iterator

mappings:
  Product:
    sources: products
    subject:
      iri_template: "{base_iri}product/{@id}"  # Attribute reference
      class: ex:Product
    properties:
      name:
        predicate: ex:productName
      category/@type:  # XML attribute
        predicate: ex:categoryType
```

### Database Example
```yaml
sources:
  customers:
    - postgresql://user:pass@localhost/db
    - sql
    - SELECT * FROM customers

mappings:
  Customer:
    sources: customers
    subject:
      iri_template: "{base_iri}customer/{customer_id}"
      class: ex:Customer
    properties:
      email:
        predicate: ex:email
```

---

## Pydantic Model Changes Required

### Current Models
```python
class SheetMapping(BaseModel):  # ❌ "Sheet" is wrong term
    name: str
    source: str
    row_resource: RowResource  # ❌ "Row" implies tabular
    properties: Dict[str, ColumnMapping]  # ⚠️ "Column" implies tabular
    objects: Dict[str, LinkedObject]  # ⚠️ Ambiguous
```

### Proposed Models (v3)
```python
class DataSource(BaseModel):
    """Universal data source definition."""
    path: str  # File path, connection string, URL
    format: str  # csv, json, xml, xlsx, sql, etc.
    iterator: Optional[str] = None  # JSONPath, XPath, SQL query

class SubjectDefinition(BaseModel):
    """RDF subject configuration."""
    iri_template: str
    class_type: Union[str, List[str]] = Field(alias="class")

class PropertyMapping(BaseModel):
    """Data property (literal) mapping."""
    predicate: str
    datatype: Optional[str] = None
    transform: Optional[str] = None
    required: bool = False

class RelationshipMapping(BaseModel):
    """Object property (relationship) mapping."""
    predicate: str
    object: ObjectDefinition  # Nested entity

class EntityMapping(BaseModel):
    """Mapping definition for one entity type."""
    sources: Union[str, List[str]]  # Source reference(s)
    subject: SubjectDefinition
    properties: Dict[str, PropertyMapping]
    relationships: Optional[Dict[str, RelationshipMapping]] = {}

class MappingConfig(BaseModel):
    """Root configuration."""
    namespaces: Dict[str, str]
    base_iri: str
    sources: Dict[str, DataSource]
    mappings: Dict[str, EntityMapping]
    # Optional RDFMap enhancements
    validation: Optional[ValidationConfig] = None
    options: Optional[ProcessingOptions] = None
    imports: Optional[List[str]] = None
```

---

## Migration Path

### Phase 1: Model Updates
1. Rename `SheetMapping` → `EntityMapping`
2. Rename `row_resource` → `subject`
3. Rename `objects` → `relationships`
4. Add `DataSource` model
5. Update `MappingConfig` root structure

### Phase 2: Parser Updates
1. Update YARRRML parser to use new structure
2. Update RML parser to output new structure
3. Update config loader

### Phase 3: Engine Updates
1. Update graph builder to use new terminology
2. Update emitters
3. Update CLI

### Phase 4: Test & Doc Updates
1. Update all tests
2. Update examples
3. Update documentation

---

## Recommendation

**Adopt v3 format immediately** because:

1. ✅ **No users yet** - Can make breaking changes
2. ✅ **RML/YARRRML alignment** - Better interoperability
3. ✅ **Universal terminology** - Works for all data types
4. ✅ **Clearer semantics** - Less ambiguity
5. ✅ **Future-proof** - Ready for databases, APIs, etc.

**Timeline**: 2-3 days to implement fully

**Breaking changes**: Yes, but acceptable since no production users

---

## Next Steps

1. ✅ Create v3 example config (done)
2. Update Pydantic models
3. Update parsers (RML, YARRRML)
4. Update engine (graph builder, emitters)
5. Update all tests
6. Update documentation

---

## Conclusion

**Decision**: Adopt `sources` + `mappings` structure (v3)

This aligns with RML/YARRRML standards while providing intuitive configuration for:
- CSV/TSV/Excel (tabular data)
- JSON (nested objects)
- XML (hierarchical with attributes)
- SQL databases
- Any future data source types

The terminology is **universal, intuitive, and standards-compliant**.

