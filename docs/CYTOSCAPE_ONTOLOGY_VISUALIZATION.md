# Cytoscape Ontology Visualization Integration

**Date:** November 16, 2025  
**Purpose:** Interactive ontology graph visualization for mapping assistance and data exploration  
**Status:** Design & implementation plan  

---

## Executive Summary

**Goal:** Add interactive ontology visualization using Cytoscape.js to help users:
1. **Understand ontology structure** before mapping
2. **Find correct properties** when automatic matching fails
3. **Visualize data relationships** in mapped output
4. **Explore graph connections** for manual review

**Key Insight:** Graph visualization should be **contextual and lightweight**, not a separate overwhelming screen. Embed it strategically where it adds value without cluttering the workflow.

---

## Use Cases & User Stories

### Use Case 1: Class Selection During Manual Review

**Scenario:** User uploads employee data. System suggests mapping `dept_code` → `departmentCode` with 60% confidence. User is unsure if this is correct.

**With Cytoscape Visualization:**
1. User clicks **"Show in Ontology"** button next to the suggestion
2. A **slide-out panel** appears showing:
   - **Center node:** `Department` class (highlighted)
   - **Connected nodes:** All properties of Department class
   - **Target property:** `departmentCode` (pulsing/highlighted)
   - **Alternative properties:** `departmentName`, `departmentId` (visible)
3. User can **click alternative properties** to see examples
4. User can **drag column** to a different property to override

**Benefit:** User sees the FULL context of the Department class and can make an informed decision.

---

### Use Case 2: Understanding Object Relationships

**Scenario:** User uploads mortgage loan data with `BorrowerID` and `PropertyID` columns. System detected these are foreign keys but user doesn't understand the relationship structure.

**With Cytoscape Visualization:**
1. User clicks **"View Ontology Graph"** tab (next to "Match Reasons")
2. Graph shows:
   - **Main class:** `MortgageLoan` (center, larger node)
   - **Object properties:** `hasBorrower` → `Borrower` class
   - **Object properties:** `collateralProperty` → `Property` class
   - **Data properties:** `loanAmount`, `interestRate`, etc. (smaller nodes)
   - **Mapped columns:** Highlighted in green
   - **Unmapped properties:** Grayed out
3. User hovers over `hasBorrower` edge → tooltip shows: `"Maps BorrowerID → Borrower.identifier"`
4. User clicks `Borrower` node → expands to show `borrowerName`, `creditScore`, etc.

**Benefit:** User understands the graph structure and sees how their CSV columns map to the knowledge graph.

---

### Use Case 3: Finding Properties When Match Fails

**Scenario:** User has column `payment_method` but system couldn't find a match (no property named "paymentMethod" in ontology).

**With Cytoscape Visualization:**
1. User clicks **"Search Ontology"** for `payment_method`
2. Graph **filters to show only relevant classes:**
   - `Payment` class (if exists)
   - `Transaction` class (if has payment-related properties)
   - `Account` class (if has payment methods)
3. User sees available properties:
   - `paymentType`
   - `paymentInstrument`
   - `transactionMethod`
4. User clicks `paymentType` → **"Use this property"** → mapping created

**Benefit:** User can EXPLORE the ontology to find the right property even when AI fails.

---

### Use Case 4: Validating Data Model Coverage

**Scenario:** User wants to ensure they're using the full ontology and not missing important fields.

**With Cytoscape Visualization:**
1. User views **"Coverage Map"** (ontology graph colored by mapping status):
   - **Green nodes:** Mapped classes/properties
   - **Yellow nodes:** Partially mapped (some properties missing)
   - **Red nodes:** Unmapped classes
   - **Gray nodes:** Not applicable to this dataset
2. User clicks **yellow node** → sees which properties are missing
3. User can **add columns** to source data or **mark as N/A**

**Benefit:** User knows if they're fully utilizing the ontology or missing key fields.

---

## UI Integration Points

### 1. **Ontology Summary Panel** (Existing)

**Location:** Project Detail page, after uploading ontology

**Current State:**
```
Ontology Summary
  Classes: 3
  Properties: 14
  Sample Classes: MortgageLoan, Borrower, Property
  Sample Properties: loanNumber, principalAmount, ...
```

**Enhanced with Cytoscape:**
```
Ontology Summary
  Classes: 3  Properties: 14  [View Graph]  <-- NEW BUTTON

  [Mini Graph Preview]  <-- NEW: Small embedded graph (300x200px)
    - Shows class hierarchy
    - Clickable to expand full screen
```

**Interaction:**
- Click **[View Graph]** → Opens full-screen modal with interactive graph
- Click **mini preview** → Same as above
- Hover over mini preview → Tooltip: "Click to explore ontology structure"

---

### 2. **Mapping Review Table** (Existing)

**Location:** After "Generate Mappings", showing match reasons

**Current State:**
```
Match Reasons Table:
  Column | Property | Match Type | Matcher | Confidence
  ----------------------------------------------------------------
  LoanID | loanNumber | Semantic | ... | 1.00  [✓][✗][Edit]
```

**Enhanced with Cytoscape:**
```
Match Reasons Table:
  Column | Property | Match Type | Confidence | Actions
  ----------------------------------------------------------------
  LoanID | loanNumber | Semantic | 1.00  [✓][✗][📊 Graph]  <-- NEW
                                         ↑
                                         Opens slide-out panel with:
                                         - Property in context
                                         - Alternative properties
                                         - Related classes
```

**Interaction:**
- Click **[📊 Graph]** → Slide-out panel (400px wide, right side)
- Panel shows:
  - **Target property** (center, highlighted)
  - **Parent class** (above)
  - **Sibling properties** (around it)
  - **Domain/Range classes** (if object property)
- User can **drag column** to different property in graph
- User can **click alternative** property → "Use this instead?"

---

### 3. **Manual Mapping Mode** (New Feature)

**Location:** When user clicks **"Map Manually"** for unmapped column

**Current Flow:**
1. User clicks **"Map Manually"** next to `payment_method`
2. Dropdown appears with all properties (alphabetical list)
3. User scrolls through 100+ properties to find the right one

**Enhanced with Cytoscape:**
```
Manual Mapping Modal:
  ┌─────────────────────────────────────────────────────────┐
  │ Map Column: payment_method                              │
  ├─────────────────────────────────────────────────────────┤
  │ [Search box]                                            │
  │                                                         │
  │ ┌───────────────┐  ┌───────────────────────────────┐   │
  │ │ Property List │  │   Ontology Graph View         │   │
  │ │ (filtered)    │  │                               │   │
  │ │               │  │   [Interactive Cytoscape]     │   │
  │ │ ☐ paymentType │  │                               │   │
  │ │ ☐ paymentInst │  │   - Click property to select  │   │
  │ │ ☐ transaction │  │   - Hover for details         │   │
  │ └───────────────┘  │   - Zoom/pan to explore       │   │
  │                    └───────────────────────────────┘   │
  │                                                         │
  │ [Cancel]  [Create Mapping]                             │
  └─────────────────────────────────────────────────────────┘
```

**Interaction:**
- **Search box** filters both list AND graph
- Clicking property in **list** → highlights in **graph**
- Clicking property in **graph** → selects for mapping
- Graph shows **context** (parent class, sibling properties)

---

### 4. **Data Lineage View** (Future Enhancement)

**Location:** After conversion, viewing RDF output

**Purpose:** Show how source CSV columns flowed through to RDF triples

**Cytoscape Visualization:**
```
Data Lineage Graph:
  Source Columns (left) → Properties (middle) → RDF Triples (right)
  
  [LoanID] ──────▶ [ex:loanNumber] ──────▶ [Triple 1]
                                           [Triple 2]
                                           ...
  
  [BorrowerID] ──▶ [ex:hasBorrower] ──────▶ [Triple 10]
                                           [Triple 11]
                                           ...
  
  Interactive:
  - Click column → highlight all triples it generated
  - Click triple → trace back to source column
  - Color-code by match confidence
```

---

## Cytoscape.js Implementation Details

### Graph Rendering Configuration

```typescript
// frontend/src/components/ontology/OntologyGraph.tsx

import cytoscape from 'cytoscape';
import { useEffect, useRef } from 'react';

interface OntologyGraphProps {
  ontology: OntologyData;
  highlightedNodes?: string[];
  onNodeClick?: (nodeId: string) => void;
  mode?: 'full' | 'mini' | 'context';
}

export default function OntologyGraph({ 
  ontology, 
  highlightedNodes, 
  onNodeClick,
  mode = 'full' 
}: OntologyGraphProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  
  useEffect(() => {
    if (!containerRef.current) return;
    
    const cy = cytoscape({
      container: containerRef.current,
      
      elements: {
        nodes: [
          // Classes as large circular nodes
          ...ontology.classes.map(cls => ({
            data: { 
              id: cls.uri, 
              label: cls.label,
              type: 'class',
              properties: cls.properties.length
            }
          })),
          
          // Properties as smaller rectangular nodes
          ...ontology.properties.map(prop => ({
            data: { 
              id: prop.uri, 
              label: prop.label,
              type: 'property',
              domain: prop.domain,
              range: prop.range,
              is_mapped: prop.is_mapped  // Highlight if mapped
            }
          }))
        ],
        
        edges: [
          // Connect properties to their domain class
          ...ontology.properties.map(prop => ({
            data: {
              source: prop.domain,
              target: prop.uri,
              label: 'has property'
            }
          })),
          
          // Connect object properties to range class
          ...ontology.properties
            .filter(prop => prop.is_object_property)
            .map(prop => ({
              data: {
                source: prop.uri,
                target: prop.range,
                label: 'points to'
              }
            }))
        ]
      },
      
      style: [
        // Class nodes: Large circles
        {
          selector: 'node[type="class"]',
          style: {
            'background-color': '#3498db',
            'label': 'data(label)',
            'width': 60,
            'height': 60,
            'font-size': 14,
            'text-valign': 'center',
            'text-halign': 'center',
            'color': '#fff',
            'text-outline-width': 2,
            'text-outline-color': '#3498db'
          }
        },
        
        // Property nodes: Small rectangles
        {
          selector: 'node[type="property"]',
          style: {
            'background-color': '#95a5a6',
            'shape': 'round-rectangle',
            'label': 'data(label)',
            'width': 'label',
            'height': 30,
            'padding': 10,
            'font-size': 11,
            'text-valign': 'center',
            'text-halign': 'center'
          }
        },
        
        // Mapped properties: Green
        {
          selector: 'node[type="property"][is_mapped="true"]',
          style: {
            'background-color': '#27ae60',
            'border-width': 3,
            'border-color': '#229954'
          }
        },
        
        // Highlighted nodes: Pulsing animation
        {
          selector: '.highlighted',
          style: {
            'background-color': '#e74c3c',
            'border-width': 4,
            'border-color': '#c0392b',
            'transition-property': 'background-color, border-color',
            'transition-duration': '0.5s'
          }
        },
        
        // Edges
        {
          selector: 'edge',
          style: {
            'width': 2,
            'line-color': '#bdc3c7',
            'target-arrow-color': '#bdc3c7',
            'target-arrow-shape': 'triangle',
            'curve-style': 'bezier',
            'label': 'data(label)',
            'font-size': 10,
            'text-rotation': 'autorotate'
          }
        }
      ],
      
      layout: {
        name: mode === 'mini' ? 'circle' : 'cose',  // Force-directed layout
        animate: true,
        animationDuration: 500,
        fit: true,
        padding: 30
      }
    });
    
    // Highlight specified nodes
    if (highlightedNodes) {
      highlightedNodes.forEach(nodeId => {
        cy.$(`#${nodeId}`).addClass('highlighted');
      });
    }
    
    // Handle node clicks
    cy.on('tap', 'node', (evt) => {
      const node = evt.target;
      if (onNodeClick) {
        onNodeClick(node.id());
      }
    });
    
    // Tooltip on hover
    cy.on('mouseover', 'node', (evt) => {
      const node = evt.target;
      const data = node.data();
      
      // Show tooltip with node details
      const tooltip = document.getElementById('cytoscape-tooltip');
      if (tooltip) {
        tooltip.innerHTML = `
          <strong>${data.label}</strong><br>
          Type: ${data.type}<br>
          ${data.properties ? `Properties: ${data.properties}` : ''}
        `;
        tooltip.style.display = 'block';
      }
    });
    
    cy.on('mouseout', 'node', () => {
      const tooltip = document.getElementById('cytoscape-tooltip');
      if (tooltip) {
        tooltip.style.display = 'none';
      }
    });
    
    return () => cy.destroy();
  }, [ontology, highlightedNodes, onNodeClick, mode]);
  
  return (
    <div style={{ position: 'relative', width: '100%', height: '100%' }}>
      <div ref={containerRef} style={{ width: '100%', height: '100%' }} />
      <div 
        id="cytoscape-tooltip" 
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          background: 'rgba(0,0,0,0.8)',
          color: 'white',
          padding: '8px 12px',
          borderRadius: '4px',
          display: 'none',
          pointerEvents: 'none',
          zIndex: 1000
        }}
      />
    </div>
  );
}
```

---

### Backend API Endpoints

Add new endpoint to return ontology as graph structure:

```python
# backend/app/routers/ontology.py

@router.get("/{project_id}/ontology-graph")
async def get_ontology_graph(project_id: str, db: Session = Depends(get_db)):
    """Get ontology structure formatted for Cytoscape.js visualization."""
    project = _get_project(db, project_id)
    
    if not project.ontology_file:
        raise HTTPException(status_code=400, detail="No ontology uploaded")
    
    analyzer = OntologyAnalyzer(project.ontology_file)
    
    # Build nodes
    nodes = []
    
    # Add class nodes
    for cls_uri, cls in analyzer.classes.items():
        nodes.append({
            'data': {
                'id': str(cls_uri),
                'label': cls.label or cls_uri.split('#')[-1],
                'type': 'class',
                'uri': str(cls_uri),
                'comment': cls.comment,
                'properties': len(cls.properties)
            }
        })
    
    # Add property nodes
    for prop_uri, prop in analyzer.properties.items():
        nodes.append({
            'data': {
                'id': str(prop_uri),
                'label': prop.label or prop_uri.split('#')[-1],
                'type': 'property',
                'uri': str(prop_uri),
                'comment': prop.comment,
                'domain': str(prop.domain) if prop.domain else None,
                'range': str(prop.range_type) if prop.range_type else None,
                'is_object_property': prop.is_object_property,
                'is_mapped': False  # Will be set by frontend based on mapping
            }
        })
    
    # Build edges
    edges = []
    
    # Connect properties to domain class
    for prop_uri, prop in analyzer.properties.items():
        if prop.domain:
            edges.append({
                'data': {
                    'source': str(prop.domain),
                    'target': str(prop_uri),
                    'label': 'has property',
                    'type': 'domain'
                }
            })
    
    # Connect object properties to range class
    for prop_uri, prop in analyzer.properties.items():
        if prop.is_object_property and prop.range_type:
            edges.append({
                'data': {
                    'source': str(prop_uri),
                    'target': str(prop.range_type),
                    'label': 'points to',
                    'type': 'range'
                }
            })
    
    # Connect subclass relationships
    for cls_uri in analyzer.classes.keys():
        for super_cls in analyzer.get_superclasses(cls_uri):
            edges.append({
                'data': {
                    'source': str(cls_uri),
                    'target': str(super_cls),
                    'label': 'subclass of',
                    'type': 'subclass'
                }
            })
    
    return {
        'elements': {
            'nodes': nodes,
            'edges': edges
        },
        'statistics': {
            'total_classes': len(analyzer.classes),
            'total_properties': len(analyzer.properties),
            'object_properties': len([p for p in analyzer.properties.values() if p.is_object_property]),
            'data_properties': len([p for p in analyzer.properties.values() if not p.is_object_property])
        }
    }
```

---

## UX Principles

### 1. **Progressive Disclosure**
Don't show the full ontology graph immediately. Start with:
- **Step 1:** Summary stats (3 classes, 14 properties)
- **Step 2:** Mini preview (if user clicks "View")
- **Step 3:** Full interactive graph (if user clicks mini preview or "Explore")

### 2. **Context-Sensitive**
Show graph **only when it helps**:
- ✅ Show when user clicks "Find alternatives"
- ✅ Show when user is manually mapping
- ✅ Show when reviewing object relationships
- ❌ Don't show by default on every page

### 3. **Non-Blocking**
Graph should be:
- **Slide-out panel** (doesn't cover main workflow)
- **Modal overlay** (can be dismissed easily)
- **Collapsible section** (can be hidden if not needed)

### 4. **Performance**
- **Lazy load** Cytoscape.js (only when graph is opened)
- **Limit nodes** to 200 max (offer filtering if larger)
- **Cache graph data** (don't regenerate on every view)

### 5. **Mobile-Friendly**
- Graph should work on tablets (touch zoom/pan)
- On mobile, offer **text list view** as alternative

---

## Implementation Phases

### Phase 1: Basic Graph Visualization (1 week)
- [ ] Install Cytoscape.js (`npm install cytoscape`)
- [ ] Create `OntologyGraph.tsx` component
- [ ] Add backend endpoint `/api/ontology-graph`
- [ ] Render basic class/property graph
- [ ] Add zoom, pan, search controls

### Phase 2: Mapping Integration (1 week)
- [ ] Highlight mapped properties in graph (green)
- [ ] Add "Show in Graph" button to match reasons table
- [ ] Implement slide-out panel with context view
- [ ] Allow clicking properties in graph to create mappings

### Phase 3: Manual Mapping Mode (1 week)
- [ ] Add "Map Manually" modal with graph view
- [ ] Implement search/filter in graph
- [ ] Allow dragging columns to properties in graph
- [ ] Show alternative suggestions in graph

### Phase 4: Polish & Advanced Features (1 week)
- [ ] Add coverage map (color by mapping status)
- [ ] Implement data lineage view
- [ ] Add animations (pulsing highlights, smooth transitions)
- [ ] Performance optimization (virtualization for large graphs)

---

## Success Metrics

1. **User Engagement:**
   - % of users who open graph view: Target > 60%
   - Time spent in graph view: Target 30-90 seconds (not too short, not too long)

2. **Mapping Accuracy:**
   - % of manual mappings created via graph: Target > 40%
   - % of incorrect auto-mappings fixed via graph: Target > 30%

3. **User Feedback:**
   - "Graph helped me understand ontology": Target > 80% agree
   - "Graph was easy to use": Target > 75% agree

---

## Conclusion

Cytoscape ontology visualization should be:
- ✅ **Contextual:** Shown when needed, not always
- ✅ **Lightweight:** Slide-out panels, not full-screen takeovers
- ✅ **Interactive:** Click to select, drag to map, search to filter
- ✅ **Helpful:** Aids understanding and decision-making
- ❌ **Not overwhelming:** Don't dump full 1000-node graph on user

**Recommended Starting Point:** Add graph view to Match Reasons table as **"📊 Show Context"** button that opens slide-out panel with target property highlighted and alternatives visible.

**Expected Impact:** 
- 15-20% reduction in manual mapping time
- 10-15% improvement in mapping accuracy
- Significant improvement in user confidence

---

**Next Steps:**
1. Review this design with team
2. Create wireframes for slide-out panel
3. Implement Phase 1 (basic graph)
4. Test with 5 users, gather feedback
5. Iterate and add Phase 2 features

**Status:** Ready for implementation ✅

