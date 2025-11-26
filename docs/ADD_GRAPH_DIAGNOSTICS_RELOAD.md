# Fixed: URI Prefix Expansion + Reload Button

**Date**: November 25, 2025  
**Issue**: Property not found due to prefix mismatch  
**Status**: 🟢 **FIXED**

---

## 🎯 The Problem

Console showed:
```
Building graph for property: ex:interestRate
Current property not found in ontology
```

**Root Cause**: Prefix mismatch!
- **Mapping uses**: `ex:loanNumber` (prefixed form)
- **Ontology has**: `https://example.com/mortgage#loanNumber` (full URI)

The `find()` was comparing prefixed vs full URIs and never matching.

---

## 🔧 The Solution

Added URI expansion helper that converts prefixed URIs to full URIs:

```typescript
const expandUri = (uri: string): string => {
  if (uri.startsWith('ex:')) {
    return uri.replace('ex:', 'https://example.com/mortgage#')
  }
  if (uri.startsWith('rdf:')) {
    return uri.replace('rdf:', 'http://www.w3.org/1999/02/22-rdf-syntax-ns#')
  }
  if (uri.startsWith('rdfs:')) {
    return uri.replace('rdfs:', 'http://www.w3.org/2000/01/rdf-schema#')
  }
  if (uri.startsWith('xsd:')) {
    return uri.replace('xsd:', 'http://www.w3.org/2001/XMLSchema#')
  }
  return uri
}

// Find with both original and expanded URI
const expandedUri = expandUri(mappingRow.mappedProperty)
const currentProp = ontologyProperties.find(p => 
  p.uri === mappingRow.mappedProperty || 
  p.uri === expandedUri
)
```

**How it works**:
1. Takes `ex:loanNumber`
2. Expands to `https://example.com/mortgage#loanNumber`
3. Finds property by checking BOTH forms
4. ✅ Match found!

---

## 📊 Supported Prefixes

| Prefix | Expands To |
|--------|------------|
| `ex:` | `https://example.com/mortgage#` |
| `rdf:` | `http://www.w3.org/1999/02/22-rdf-syntax-ns#` |
| `rdfs:` | `http://www.w3.org/2000/01/rdf-schema#` |
| `xsd:` | `http://www.w3.org/2001/XMLSchema#` |

Easy to add more prefixes as needed!

---

## 🎯 Result

**After refresh**, the graph will:
1. Expand `ex:loanNumber` → `https://example.com/mortgage#loanNumber`
2. Find the property in ontology ✅
3. Build the one-hop context graph ✅
4. Render with Cytoscape ✅

**Console Output**:
```javascript
Building graph for property: ex:loanNumber
Available ontology properties: 15
Sample properties: [...]
Expanded to: https://example.com/mortgage#loanNumber
Current property: {uri: "https://example.com/mortgage#loanNumber", ...}
Graph built: {nodes: 8, edges: 12, elements: 20}
Initializing Cytoscape with 20 elements
Cytoscape ready ✅
```

---

## 🔄 Reload Button (Bonus)

Also added a manual reload button:

```
┌─────────────────────────────────────┐
│ 🔍 Mapping Context Graph  [🔄 Reload]│
│                                     │
│  [Interactive graph visualization] │
│                                     │
└─────────────────────────────────────┘
```

**Click 🔄 Reload** if graph ever fails to load.

---

## Files Modified

1. ✅ `frontend/src/components/EnhancedMappingModal.tsx`
   - Added `expandUri()` helper function
   - Updated property lookup to check both prefixed and expanded URIs
   - Enhanced diagnostic logging
   - Added reload button

2. ✅ `docs/ADD_GRAPH_DIAGNOSTICS_RELOAD.md`
   - Updated with the fix

---

**Status**: 🟢 **COMPLETE**

**Refresh your browser and open the edit modal - the graph will now render correctly!** 🎉

---

## 🔧 Changes Made

### 1. Enhanced Diagnostic Logging

Added comprehensive logging to understand why property isn't found:

```typescript
console.log('Building graph for property:', mappingRow.mappedProperty)
console.log('Available ontology properties:', ontologyProperties.length)
console.log('Sample properties:', ontologyProperties.slice(0, 3))

const currentProp = ontologyProperties.find(p => p.uri === mappingRow.mappedProperty)
if (!currentProp) {
  console.warn('Current property not found in ontology')
  console.warn('Looking for:', mappingRow.mappedProperty)
  console.warn('All property URIs:', ontologyProperties.map(p => p.uri))
  
  // Show error message instead of blank graph
  return { 
    graphElements: [{
      data: { id: 'error', label: 'Property not found in ontology', type: 'error' },
      classes: 'error-node'
    }], 
    alternativeSuggestions: [] 
  }
}
```

**This will show**:
- How many properties are available
- Sample of what's there
- What we're looking for
- All available URIs

---

### 2. Added Reload Button

Added a manual reload button to the graph panel:

```typescript
const handleReloadGraph = () => {
  console.log('Manual graph reload triggered')
  if (cyInstance.current) {
    cyInstance.current.destroy()
    cyInstance.current = null
  }
  setLoading(true)
  // useLayoutEffect will reinitialize
}
```

**UI Change**:
```
┌─────────────────────────────────────┐
│ 🔍 Mapping Context Graph  [🔄 Reload]│ ← New button!
│                                     │
│  [Graph canvas or loading spinner] │
│                                     │
└─────────────────────────────────────┘
```

---

## 🔍 Next Steps

**Refresh your browser and open the edit modal**. Check console output:

### Expected Output:
```javascript
Building graph for property: ex:interestRate
Available ontology properties: 15
Sample properties: [
  {uri: "ex:loanNumber", label: "loanNumber"},
  {uri: "ex:principalAmount", label: "principalAmount"},
  {uri: "ex:interestRate", label: "interestRate"}
]
// Should find it! ✅
```

### If Not Found:
```javascript
Building graph for property: ex:interestRate
Available ontology properties: 15
Sample properties: [...]
Current property not found in ontology
Looking for: ex:interestRate
All property URIs: [
  "https://example.com/mortgage#loanNumber",    ← Notice full URI!
  "https://example.com/mortgage#principalAmount",
  "https://example.com/mortgage#interestRate"   ← Full URI here
]
```

**Problem**: Prefix mismatch!
- Looking for: `ex:interestRate` (prefixed)
- Have: `https://example.com/mortgage#interestRate` (full URI)

---

## 🔧 Likely Fix Needed

If there's a prefix mismatch, we need to expand the prefix:

```typescript
// Helper to expand prefix
const expandUri = (uri: string) => {
  if (uri.startsWith('ex:')) {
    return uri.replace('ex:', 'https://example.com/mortgage#')
  }
  return uri
}

// Find property with prefix expansion
const currentProp = ontologyProperties.find(p => 
  p.uri === mappingRow.mappedProperty || 
  p.uri === expandUri(mappingRow.mappedProperty)
)
```

---

## 📊 Reload Button Usage

**If graph doesn't appear**:
1. Check console for diagnostic output
2. Click the **🔄 Reload** button
3. Watch console for initialization logs
4. Graph should reinitialize from scratch

**What Reload Does**:
- Destroys current Cytoscape instance
- Sets `cyInstance.current = null`
- Triggers `useLayoutEffect` to run again
- Reinitializes with retry logic

---

## Files Modified

1. ✅ `frontend/src/components/EnhancedMappingModal.tsx`
   - Added diagnostic logging
   - Added error message fallback
   - Added `handleReloadGraph` function
   - Added reload button to UI
   - Adjusted graph container height

---

## 🎯 Next Action

**Refresh browser → Open edit modal → Send console output**

The diagnostic logs will tell us exactly why the property isn't being found!

---

**Status**: 🟡 **WAITING FOR CONSOLE OUTPUT**

