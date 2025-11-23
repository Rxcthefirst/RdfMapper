# 🐛 RML Generation Issues - Need to Fix

**Date**: November 22, 2025  
**Status**: 🔴 Issues Identified

---

## Issues Found

### 1. ❌ `{base_iri}` Not Being Replaced
**Problem**: Template shows `{base_iri}mortgage_loan/{LoanID}` instead of `http://example.org/mortgage_loan/{LoanID}`

**Location**: Line 32 in generated RML
```turtle
rr:template "{base_iri}mortgage_loan/{LoanID}"
```

**Should be**:
```turtle
rr:template "http://example.org/mortgage_loan/{LoanID}"
```

**Root Cause**: The `replace('$(base_iri)', self.base_uri)` is not working. Need to debug why.

---

### 2. ❌ Object Properties Creating Single TriplesMap
**Problem**: Both Borrower and Property objects are being merged into one `objectMapping` TriplesMap

**Current (Wrong)**:
```turtle
<http://example.org/objectMapping> a rr:TriplesMap ;
    rml:logicalSource [ ... ] ;
    rml:logicalSource [ ... ] ;  ← TWO logical sources! Invalid!
    rr:predicateObjectMap [ ... BorrowerName ... ] ;
    rr:predicateObjectMap [ ... PropertyAddress ... ] ;
    rr:subjectMap [ rr:class ex:Borrower ; ... ] ;
    rr:subjectMap [ rr:class ex:Property ; ... ] .  ← TWO subject maps! Invalid!
```

**Should be**:
```turtle
<http://example.org/borrowerMapping> a rr:TriplesMap ;
    rml:logicalSource [ ... ] ;
    rr:predicateObjectMap [ ... BorrowerName ... ] ;
    rr:subjectMap [ rr:class ex:Borrower ; 
            rr:template "http://example.org/borrower/{BorrowerID}" ] .

<http://example.org/propertyMapping> a rr:TriplesMap ;
    rml:logicalSource [ ... ] ;
    rr:predicateObjectMap [ ... PropertyAddress ... ] ;
    rr:subjectMap [ rr:class ex:Property ; 
            rr:template "http://example.org/property/{PropertyID}" ] .
```

**Root Cause**: The check `if (parent_tm_uri, RDF.type, RR.TriplesMap) not in self.graph` is not working properly. The same parent_tm_uri is being reused.

---

### 3. ❌ Missing Property Object
**Problem**: Only seeing Borrower object, missing Property object

**Expected**:
- `ex:hasBorrower` → Borrower object
- `ex:collateralProperty` → Property object

---

## Root Causes

### Issue 1: base_iri Replacement
The template replacement code:
```python
iri_template = iri_template.replace('$(base_iri)', self.base_uri)
```

**Possible causes**:
1. `self.base_uri` is not set correctly
2. The template doesn't contain `$(base_iri)` (maybe already converted?)
3. The replacement happens but then gets overwritten

**Debug needed**: Print `iri_template` before and after replacement

---

### Issue 2: Parent TriplesMap URI Collision
The code creates parent TriplesMap URI like:
```python
obj_name = obj_config.get('name', 'object')
parent_tm_uri = URIRef(f"{self.base_uri}{obj_name}Mapping")
```

**Problem**: If `obj_config['name']` is missing or same for both objects, they collide!

**Fix**: Ensure each object has a unique name OR use object class + counter

---

## Required Fixes

### Fix 1: Ensure base_iri Substitution Works
```python
def _add_subject_map(self, tm_uri: URIRef, sheet: Dict[str, Any]):
    # ...
    template = sheet.get('subject_template', ...)
    
    # DEBUG: Print before
    print(f"Template before: {template}")
    print(f"base_uri: {self.base_uri}")
    
    # Substitute
    template = template.replace('$(base_iri)', self.base_uri)
    
    # DEBUG: Print after
    print(f"Template after: {template}")
    
    # Convert $(column) to {column}
    template = re.sub(r'\$\((\w+)\)', r'{\1}', template)
    
    # DEBUG: Print final
    print(f"Template final: {template}")
```

### Fix 2: Use Unique Names for Parent TriplesMap
```python
def _add_object_property_map(self, tm_uri: URIRef, obj_config: Dict[str, Any], sheet: Dict[str, Any]):
    # Get object name from config
    obj_name = obj_config.get('name')
    
    if not obj_name:
        # Fallback: use class name
        obj_class = obj_config.get('class', obj_config.get('class_type', ''))
        if ':' in obj_class:
            obj_name = obj_class.split(':')[1].lower()
        else:
            obj_name = 'object'
    
    # Create UNIQUE URI
    parent_tm_uri = URIRef(f"{self.base_uri}{obj_name}Mapping")
    
    # DEBUG
    print(f"Creating parent TriplesMap: {parent_tm_uri}")
    print(f"  Object config: {obj_config}")
```

### Fix 3: Verify Objects Config
Check if internal mapping actually has TWO objects:
```python
# In generate command
print("Sheet objects:")
for obj_name, obj_config in sheet.get('objects', {}).items():
    print(f"  {obj_name}: {obj_config.get('class')}")
```

---

## Testing Plan

1. **Test base_iri substitution**:
   ```bash
   python3 test_base_iri_substitution.py
   ```

2. **Test object separation**:
   ```bash
   python3 test_object_separation.py
   ```

3. **Regenerate and validate**:
   ```bash
   rdfmap generate ... -f rml -o test.rml.ttl
   # Check output has:
   # - http://example.org/ not {base_iri}
   # - Two separate TriplesMap for borrower and property
   ```

---

## Expected Output

```turtle
@prefix ex: <https://example.com/mortgage#> .
@prefix rml: <http://semweb.mmlab.be/ns/rml#> .
@prefix rr: <http://www.w3.org/ns/r2rml#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

<http://example.org/loansMapping> a rr:TriplesMap ;
    rml:logicalSource [ 
        rml:source "examples/mortgage/data/loans.csv" ;
        rml:referenceFormulation ql:CSV 
    ] ;
    rr:subjectMap [ 
        rr:class ex:MortgageLoan ;
        rr:template "http://example.org/mortgage_loan/{LoanID}"  ← FIXED!
    ] ;
    rr:predicateObjectMap [
        rr:predicate ex:loanNumber ;
        rr:objectMap [ rml:reference "LoanID" ]
    ] ;
    rr:predicateObjectMap [
        rr:predicate ex:hasBorrower ;
        rr:objectMap [ rr:parentTriplesMap <http://example.org/borrowerMapping> ]
    ] ;
    rr:predicateObjectMap [
        rr:predicate ex:collateralProperty ;
        rr:objectMap [ rr:parentTriplesMap <http://example.org/propertyMapping> ]
    ] .

<http://example.org/borrowerMapping> a rr:TriplesMap ;  ← SEPARATE!
    rml:logicalSource [ 
        rml:source "examples/mortgage/data/loans.csv" ;
        rml:referenceFormulation ql:CSV 
    ] ;
    rr:subjectMap [ 
        rr:class ex:Borrower ;
        rr:template "http://example.org/borrower/{BorrowerID}"  ← FIXED!
    ] ;
    rr:predicateObjectMap [
        rr:predicate ex:borrowerName ;
        rr:objectMap [ rml:reference "BorrowerName" ]
    ] .

<http://example.org/propertyMapping> a rr:TriplesMap ;  ← SEPARATE!
    rml:logicalSource [ 
        rml:source "examples/mortgage/data/loans.csv" ;
        rml:referenceFormulation ql:CSV 
    ] ;
    rr:subjectMap [ 
        rr:class ex:Property ;
        rr:template "http://example.org/property/{PropertyID}"  ← FIXED!
    ] ;
    rr:predicateObjectMap [
        rr:predicate ex:propertyAddress ;
        rr:objectMap [ rml:reference "PropertyAddress" ]
    ] .
```

---

## Next Steps

1. Add debug logging to identify root causes
2. Fix base_iri substitution
3. Fix object TriplesMap separation
4. Test with mortgage example
5. Verify RDF output creates 5 separate loan instances

---

**Status**: Issues identified, fixes needed before v0.4.0 release

