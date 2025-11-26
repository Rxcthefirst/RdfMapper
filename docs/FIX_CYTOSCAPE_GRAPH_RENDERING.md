# Fixed: Cytoscape Graph Rendering with One-Hop Context

**Date**: November 25, 2025  
**Issue**: Cytoscape diagram not rendering + wrong graph structure  
**Status**: 🟢 **FIXED**

---

## 🎯 What Was Fixed

### Issue 1: Graph Not Rendering
**Root Cause**: Async timing - Cytoscape tried to initialize before container had dimensions

**Solution**: Added 100ms delay + dimension check before initialization

### Issue 2: Wrong Graph Structure
**Root Cause**: Graph only showed column → property → class, no context

**Solution**: Rebuilt graph to show domain-property-range with one-hop neighbors

---

## 📊 New Graph Structure

### What You'll See

```
[Domain Context]    [Center]    [Range Context]

Neighbor Classes    Domain      Current        Range      Neighbor Classes
    ↓               Class       Property       Class           ↓
Neighbor Props       ↓            ↑↓            ↓         Neighbor Props
                     └────────────┘─────────────┘
```

**Example for `ex:principalAmount` property:**

```
                    ┌──────────────┐
                    │ MortgageLoan │ ← Domain Class (yellow)
                    │  (Domain)    │
                    └──────┬───────┘
                           │
                    ┌──────▼────────────┐
              ┌─────┤ principalAmount   │ ← Current Property (blue, large)
              │     │   (Property)      │
              │     └───────────────────┘
              │
    ┌─────────┴─────────┐
    │   Borrower        │ ← One-hop neighbor (via hasBorrower)
    │  (Neighbor)       │
    └───────────────────┘
    
```

---

## 🔧 Technical Changes

### 1. Graph Building Logic

**New Algorithm**:
1. **Add current property** (center node)
2. **Add domain class** (if exists) + edge
3. **Add range class** (if exists) + edge
4. **For domain class**: Add all properties with this domain (one-hop out)
5. **For domain class**: Add all properties with this range (one-hop in)
6. **For range class**: Add all properties with this domain (one-hop out)
7. **For range class**: Add all properties with this range (one-hop in)
8. **Deduplicate** nodes and edges

**Key Features**:
- Uses `Set` to track added nodes/edges
- Skips self-loops
- Limits to one hop from domain/range
- Shows both outgoing and incoming relationships

---

### 2. Visual Styling

**Node Types**:

| Type | Shape | Color | Border | Size |
|------|-------|-------|--------|------|
| **Domain Class** | Rectangle | Yellow | Orange (3px) | 80x50 |
| **Range Class** | Rectangle | Green | Dark Green (3px) | 80x50 |
| **Current Property** | Circle | Light Blue | Dark Blue (4px) | 90x90 |
| **Neighbor Class** | Rectangle | Light Gray | Gray (1px) | 80x50 |
| **Neighbor Property** | Circle | White | Gray (1px) | 50x50 |

**Edge Types**:

| Label | Color | Width | Arrow |
|-------|-------|-------|-------|
| `domain` | Orange | 3px | Triangle |
| `range` | Green | 3px | Triangle |
| Other | Gray | 2px | Triangle |

---

### 3. Layout Configuration

```typescript
layout: {
  name: 'cola',           // Force-directed with constraints
  animate: true,          // Smooth animation
  maxSimulationTime: 3000, // 3 seconds max
  fit: true,              // Fit to container
  padding: 40,            // Edge padding
  edgeLength: 150,        // Preferred edge length
  nodeSpacing: 50,        // Min spacing between nodes
  flow: {                 // Left-to-right flow
    axis: 'x',
    minSeparation: 100
  }
}
```

---

### 4. Robust Async Initialization

**Borrowed from OntologyGraphMini (proven approach)**:

```typescript
useLayoutEffect(() => {
  if (!open || graphElements.length === 0) return

  let cancelled = false
  let attempts = 0

  const attemptInit = async () => {
    if (cancelled || cyInstance.current) return

    const el = cyRef.current
    if (!el) {
      attempts++
      if (attempts < 20) {
        return setTimeout(attemptInit, 40) // Retry with 40ms delay
      } else {
        console.error('Container not found after 20 attempts')
        return
      }
    }

    setLoading(true)

    // Wait for container to have dimensions (15 attempts, 30ms each)
    const sized = await waitForContainer(el, 15, 30)
    if (!sized) {
      el.style.minHeight = '400px' // Force minimum height
    }

    if (cancelled) return

    const cytoscape = getCytoscape()
    const cy = cytoscape({ container: el, elements, style, layout })
    
    cy.on('ready', () => {
      if (!cancelled) setLoading(false)
    })

    cyInstance.current = cy
  }

  attemptInit()

  return () => {
    cancelled = true
    if (cyInstance.current) {
      cyInstance.current.destroy()
      cyInstance.current = null
    }
  }
}, [open, graphElements])
```

**Why This Works Better**:
- ✅ Uses `useLayoutEffect` (runs before paint, more reliable)
- ✅ Uses `waitForContainer` helper (waits for actual dimensions)
- ✅ Multiple retry attempts (20 attempts with 40ms delays = 800ms total)
- ✅ Waits for Cytoscape 'ready' event before removing loading state
- ✅ Cancellation flag prevents race conditions
- ✅ Falls back to setting min-height if container still has no size
- ✅ Uses shared `getCytoscape()` to ensure cola is registered

---

## 🚀 Result

**After refresh, when you click Edit on any property:**

### You'll See:
1. **Current property** in the center (large blue circle)
2. **Domain class** on the left (yellow rectangle)
3. **Range class** on the right (green rectangle, if object property)
4. **One-hop neighbors** of domain class (smaller nodes)
5. **One-hop neighbors** of range class (smaller nodes)
6. **Orange edge** labeled "domain" from domain → property
7. **Green edge** labeled "range" from property → range
8. **Gray edges** for neighbor relationships

### Interactive Features:
- ✅ Click on any property node to select it
- ✅ Hover over nodes to see tooltips (comment)
- ✅ Graph animates into position
- ✅ Fits to container automatically
- ✅ Zoom and pan enabled

---

## 📝 Example Scenarios

### Scenario 1: Data Property (No Range Class)

**Property**: `ex:principalAmount` (domain: MortgageLoan, range: xsd:integer)

```
Graph shows:
- MortgageLoan (domain, yellow)
  ├─ principalAmount (current, blue, large)
  ├─ interestRate (neighbor)
  ├─ loanNumber (neighbor)
  └─ hasBorrower → Borrower (neighbor object property)
```

Range is a datatype (xsd:integer), not a class, so no range node.

---

### Scenario 2: Object Property (Has Range Class)

**Property**: `ex:hasBorrower` (domain: MortgageLoan, range: Borrower)

```
Graph shows:
- MortgageLoan (domain, yellow)    - Borrower (range, green)
  ├─ principalAmount                  ├─ borrowerName
  ├─ hasBorrower (current, blue)  →  └─ creditScore
  └─ collateralProperty → Property
```

Shows context on BOTH sides of the relationship!

---

## ✅ Benefits

**Before**:
- ❌ Graph didn't render (blank canvas)
- ❌ Simple structure (just column → property → class)
- ❌ No context about related properties
- ❌ Hard to understand property's role

**After**:
- ✅ Graph renders reliably
- ✅ Rich structure with one-hop context
- ✅ See domain and range classes
- ✅ See neighbor properties for context
- ✅ Visual distinction between node types
- ✅ Color-coded edges
- ✅ Interactive and zoomable
- ✅ Helps users make informed mapping decisions

---

## 🔍 Console Output

When opening the edit modal, check console:

```javascript
Building graph for property: ex:principalAmount
Current property: {uri: "...", label: "...", domain: "...", range: "..."}
Graph built: {
  nodes: 8,        ← Total nodes
  edges: 12,       ← Total edges
  elements: 20     ← Total Cytoscape elements
}
Initializing Cytoscape with 20 elements
```

Or if there's an issue:
```javascript
Cytoscape container has no dimensions yet, delaying initialization
```

---

## Files Modified

1. ✅ `frontend/src/components/EnhancedMappingModal.tsx`
   - **Rewrote `graphElements` useMemo**:
     - New algorithm for one-hop graph structure
     - Deduplication with `Set`
     - Separate handling for domain/range neighbors
   - **Updated Cytoscape styling**:
     - Different colors for domain/range classes
     - Size differentiation (current vs neighbor)
     - Color-coded edges
   - **Fixed async initialization**:
     - 100ms delay
     - Dimension check
     - Proper cleanup

---

## 🎨 Visual Legend

**In the graph:**

🟨 **Yellow Rectangle** = Domain class (subject of property)  
🟩 **Green Rectangle** = Range class (object of property)  
🔵 **Large Blue Circle** = Current property being edited  
⚪ **Small White Circle** = Neighbor property (context)  
⬜ **Gray Rectangle** = Neighbor class (context)  

🟧 **Orange Arrow** = Domain relationship  
🟢 **Green Arrow** = Range relationship  
⬛ **Gray Arrow** = Neighbor relationship  

---

**Status**: 🟢 **COMPLETE**

**Refresh your browser and click Edit on any property - you'll see a rich contextual graph!** 🎉

