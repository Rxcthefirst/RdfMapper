# Fix: YARRRML Column Names with Spaces

**Date:** November 18, 2025  
**Status:** ✅ FIXED AND TESTED  
**Issue:** Column names with spaces not parsed in YARRRML format

---

## Problem

YARRRML mappings with column names containing spaces were not working:

```yaml
mappings:
  person:
    po:
      - [ex:firstName, $(First Name), xsd:string]  # ❌ Not working
      - [ex:name, $(name), xsd:string]             # ✅ Working
```

**Symptom:** Only `ex:name` was mapped, `ex:firstName` was ignored.

---

## Root Cause

The YARRRML parser was using a regex pattern that only matched word characters:

```python
# OLD (BROKEN):
column_match = re.search(r'\$\((\w+)\)', str(object_value))
#                             ^^^^
#                         Only matches: a-z, A-Z, 0-9, _
#                         Does NOT match: spaces, hyphens, etc.
```

This pattern failed for column names like:
- `First Name` (space)
- `Birth-Date` (hyphen)
- `Email@Address` (special chars)

---

## Solution

Changed the regex pattern to match any characters except the closing parenthesis:

```python
# NEW (FIXED):
column_match = re.search(r'\$\(([^)]+)\)', str(object_value))
#                             ^^^^^^^
#                         Matches: any character except ')'
#                         Works with: spaces, hyphens, special chars
```

### Files Modified

**File:** `src/rdfmap/config/yarrrml_parser.py`

**Two regex patterns fixed:**

1. **Property mappings** (line ~165):
```python
# Extract column name from $(column) or $(Column Name)
# Match any characters except closing parenthesis to support spaces in column names
column_match = re.search(r'\$\(([^)]+)\)', str(object_value))
```

2. **IRI templates** (line ~134):
```python
# YARRRML uses $(column), we use {column}
# Support column names with spaces: $(First Name) -> {First Name}
iri_template = re.sub(r'\$\(([^)]+)\)', r'{\1}', subject_template)
```

---

## Test Results

### Before Fix
```
✅ Columns parsed: ['name', 'ContactEmail', 'Age', 'salary']
❌ Missing: 'First Name'
```

### After Fix
```
✅ Columns parsed: ['First Name', 'name', 'ContactEmail', 'Age', 'salary']
✅ All columns working!
```

### Generated RDF (After Fix)
```turtle
<https://data.example.com/person/1001> a ex:Person ;
    ex:age 39 ;
    ex:email "john.smith@company.com"^^xsd:string ;
    ex:firstName "John"^^xsd:string ;              # ✅ Now works!
    ex:name "John Smith"^^xsd:string ;
    ex:salary 95000.0 .
```

---

## Verification

**Test command:**
```bash
python3 -c "
from rdfmap.config.loader import load_mapping_config
config = load_mapping_config('test_yarrrml.yaml')
print('Columns:', list(config.sheets[0].columns.keys()))
"
```

**Output:**
```
Columns: ['First Name', 'name', 'ContactEmail', 'Age', 'salary']
```

**End-to-end test:**
```bash
python3 test_yarrrml_e2e.py
```

**Result:**
```
✅ PASS: Found 10 ex:Person instances
✅ PASS: Properties found:
   - ex:firstName: 10 values  # ✅ Working!
   - ex:name: 10 values
   - ex:email: 9 values
   - ex:age: 10 values
   - ex:salary: 10 values
✅ PASS: All expected properties present
```

---

## Supported Column Name Formats

After this fix, the YARRRML parser now supports:

✅ **Simple names:** `$(name)` → `{name}`  
✅ **Spaces:** `$(First Name)` → `{First Name}`  
✅ **Hyphens:** `$(Birth-Date)` → `{Birth-Date}`  
✅ **Underscores:** `$(employee_id)` → `{employee_id}`  
✅ **Mixed case:** `$(EmployeeID)` → `{EmployeeID}`  
✅ **Special chars:** `$(Email@Address)` → `{Email@Address}`  
✅ **Numbers:** `$(Column123)` → `{Column123}`  

The only limitation: Column names cannot contain `)` (closing parenthesis).

---

## Impact

### Standards Compliance ✅
- YARRRML spec doesn't restrict column name characters
- Fix ensures full compatibility with real-world CSV files
- Common in databases: "First Name", "Birth Date", "Email Address"

### Backward Compatibility ✅
- Simple column names still work exactly as before
- No breaking changes
- Existing mappings unaffected

### Real-World Usage ✅
- CSV files often have spaces in headers
- Excel exports commonly use spaces
- Legacy databases use various naming conventions

---

## Example Use Cases

### HR Data
```yaml
mappings:
  employee:
    po:
      - [ex:firstName, $(First Name), xsd:string]
      - [ex:lastName, $(Last Name), xsd:string]
      - [ex:birthDate, $(Birth Date), xsd:date]
      - [ex:hireDate, $(Hire Date), xsd:date]
```

### Customer Data
```yaml
mappings:
  customer:
    po:
      - [ex:email, $(Email Address), xsd:string]
      - [ex:phone, $(Phone Number), xsd:string]
      - [ex:address, $(Street Address), xsd:string]
```

### Financial Data
```yaml
mappings:
  transaction:
    po:
      - [ex:amount, $(Transaction Amount), xsd:decimal]
      - [ex:date, $(Transaction Date), xsd:date]
      - [ex:account, $(Account Number), xsd:string]
```

---

## Regex Pattern Explained

### New Pattern: `r'\$\(([^)]+)\)'`

**Breakdown:**
- `\$` - Literal dollar sign
- `\(` - Literal opening parenthesis
- `([^)]+)` - **Capture group:**
  - `[^)]` - Any character EXCEPT closing parenthesis
  - `+` - One or more times
- `\)` - Literal closing parenthesis

**Matches:**
- ✅ `$(name)` → captures `name`
- ✅ `$(First Name)` → captures `First Name`
- ✅ `$(email-address)` → captures `email-address`
- ✅ `$(col_123)` → captures `col_123`

**Does not match:**
- ❌ `$(name` - Missing closing parenthesis
- ❌ `$name)` - Missing opening parenthesis
- ❌ `$(name))` - Extra closing parenthesis (captures up to first `)`)

---

## Conclusion

**Status:** ✅ FIXED

The YARRRML parser now correctly handles column names with spaces and special characters, making it compatible with real-world CSV files and ensuring full YARRRML standards compliance.

**Files modified:** 1  
**Lines changed:** 2  
**Test coverage:** ✅ Passing  
**Impact:** High (enables real-world CSV usage)  
**Risk:** None (backward compatible)  

---

**Your YARRRML implementation is now production-ready for real-world data sources!** 🎉

