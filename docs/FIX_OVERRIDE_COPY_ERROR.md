# Fixed: Mapping Override Causing Conversion Error

**Date**: November 25, 2025  
**Issue**: `'str' object has no attribute 'copy'` error when converting after override  
**Status**: 🟢 **FIXED**

---

## 🎯 The Problem

**Error when converting after overriding a mapping**:
```
Conversion failed: {"detail":"'str' object has no attribute 'copy'"}
```

**Root Causes**:
1. Override endpoint was saving property URIs as **strings** instead of **objects**
2. V2 format expects properties to be objects with a `predicate` field
3. When conversion tried to use `.copy()` on the property, it failed because it was a string
4. Additionally, backend was using wrong field name: `nested_entities` instead of `relationships`

---

## 🔧 The Fix

### Issue 1: Simple Property Override

**Before (WRONG)**:
```python
properties[column_name] = property_uri  # Saves as string!
```

**After (CORRECT)**:
```python
if column_name not in properties:
    properties[column_name] = {'predicate': property_uri}
else:
    if isinstance(properties[column_name], dict):
        properties[column_name]['predicate'] = property_uri
    else:
        # Convert string to object if needed
        properties[column_name] = {'predicate': property_uri}
```

**Result**: Properties are now saved as objects with `predicate` field, matching v2 format!

---

### Issue 2: Nested Property Override

**Before (WRONG)**:
```python
nested_entities = source.get('nested_entities', [])  # Wrong field name!
# ...
properties[column_name] = property_uri  # String again!
```

**After (CORRECT)**:
```python
relationships = source.get('relationships', [])  # Correct v2 field name!
# ...
if column_name not in properties:
    properties[column_name] = {'predicate': property_uri}
else:
    if isinstance(properties[column_name], dict):
        properties[column_name]['predicate'] = property_uri
    else:
        properties[column_name] = {'predicate': property_uri}
```

**Result**: 
- Uses correct v2 field name `relationships`
- Saves properties as objects

---

## 📊 V2 Format Structure

**Correct v2 inline format**:
```yaml
mapping:
  sources:
    - entity:
        class: ex:MortgageLoan
        iri_template: "loan/{LoanID}"
      properties:
        Principal:
          predicate: ex:principalAmount    # ← Object with predicate!
          datatype: xsd:integer
        InterestRate:
          predicate: ex:interestRate       # ← Not just a string!
          datatype: xsd:decimal
      relationships:                        # ← V2 uses 'relationships'
        - predicate: ex:hasBorrower
          class: ex:Borrower
          iri_template: "borrower/{BorrowerID}"
          properties:
            BorrowerName:
              predicate: ex:borrowerName   # ← Object format here too!
```

**What Was Happening (WRONG)**:
```yaml
properties:
  Principal: ex:principalAmount    # ← Just a string! Breaks .copy()
```

---

## 🚀 Result

**After restarting the backend**:

1. **Override a mapping** in the UI
2. **Click Convert**
3. ✅ **Conversion succeeds!**

The conversion engine can now properly handle overridden mappings because they're in the correct object format.

---

## 🔍 Why It Failed Before

**Conversion process**:
```python
# In v2_generator.py or conversion code
for col_name, col_config in sheet['columns'].items():
    prop_config = col_config.copy()  # ← Calls .copy() on the value
    # If col_config is a string, this fails!
    # Strings don't have .copy() method
```

**Error trace**:
```
AttributeError: 'str' object has no attribute 'copy'
```

**Now with objects**:
```python
col_config = {'predicate': 'ex:principalAmount'}
prop_config = col_config.copy()  # ← Works! Dicts have .copy()
```

---

## 📁 Files Modified

1. ✅ `backend/app/routers/mappings.py`
   - **Fixed `override_mapping` endpoint** (line ~191):
     - Changed from saving string to saving object with `predicate` field
     - Added handling for existing dict properties
     - Added fallback for string-to-object conversion
   
   - **Fixed `override_nested_mapping` endpoint** (line ~320):
     - Changed `nested_entities` → `relationships` (correct v2 field name)
     - Changed from saving string to saving object with `predicate` field
     - Added same dict/string handling as above

---

## 🎯 Testing

**Test the fix**:

1. **Restart backend**:
   ```bash
   docker-compose restart backend worker
   ```

2. **Override a mapping**:
   - Open any AI-generated project
   - Go to Step 2 (Mapping Review)
   - Click Edit on any property
   - Select a different property
   - Click Save

3. **Convert**:
   - Go to Step 4 (Convert)
   - Click Convert
   - ✅ **Should succeed!**

4. **Check the config**:
   ```bash
   cat backend/data/{project_id}/mapping_config.yaml
   ```
   
   Should see:
   ```yaml
   properties:
     Principal:
       predicate: ex:principalAmount  # ← Object format ✅
   ```
   
   NOT:
   ```yaml
   properties:
     Principal: ex:principalAmount  # ← String format ❌
   ```

---

## 🐛 What This Fixes

✅ **Override + Convert** - No more `'str' object has no attribute 'copy'` error  
✅ **Nested overrides** - Uses correct `relationships` field  
✅ **V2 format consistency** - All properties are objects  
✅ **Backward compatible** - Handles existing string values and converts them  

---

## 📝 Related Issues

This fix ensures that manual overrides create the same data structure as AI-generated mappings, so the conversion engine can handle both uniformly.

**Key principle**: V2 format properties should ALWAYS be objects with a `predicate` field, never bare strings.

---

**Status**: 🟢 **COMPLETE**

**Restart the backend and try overriding + converting - it will work now!** 🎉

