# Task Queue & Implementation Roadmap

**Date:** November 16, 2025  
**Status:** Post Stage 2 Matcher Refactor  
**Priority:** Based on FEATURE_IMPLEMENTATION_CHECKLIST.md and CYTOSCAPE_ONTOLOGY_VISUALIZATION.md

---

## ✅ COMPLETED TODAY - Stage 2 Matcher Refactor

### Backend (Complete)
- [x] Added `MatchType.DATA_TYPE_COMPATIBILITY`
- [x] Refactored DataTypeInferenceMatcher to be type-only
- [x] Implemented evidence aggregation with `pipeline.match_all()`
- [x] Added boosters (+0.05 datatype, +0.05 graph, +0.02 inherited, cap 0.15)
- [x] Added ambiguity penalty (−0.05 for 1 close, −0.10 for ≥2)
- [x] Formalized Pydantic models: `AdjustmentItem`, `EvidenceItem`, `AlternateCandidate`
- [x] Extended `MatchDetail` with evidence/boosters/penalties/ambiguity/alternates
- [x] Validation: All tests PASS (Min 0.693, Max 1.000, Mean 0.919, Std 0.086)

### Frontend (Started)
- [x] Created `EvidenceDrawer.tsx` component
  - Evidence stack table (matchers, types, scores, reasons)
  - Boosters/penalties display with icons
  - Ambiguity warnings
  - Alternates list (clickable)
  - Progressive disclosure (accordions)

### Documentation
- [x] `.github/prompts/` registry with YAML front matter
- [x] PERSONA.md workflow enforcement
- [x] LOG-001 progress tracking
- [x] Reviewed ANALYSIS_SUMMARY_NOV16.md, FEATURE_IMPLEMENTATION_CHECKLIST.md, CYTOSCAPE_ONTOLOGY_VISUALIZATION.md

---

## 🎯 IMMEDIATE NEXT (Week 1-2)

### 1. Wire Evidence Drawer into ProjectDetail ⭐ CURRENT
**Priority:** HIGH  
**Effort:** 2-4 hours  
**Status:** Component ready, needs integration

**Tasks:**
- [ ] Add "Evidence" button to match reasons table rows
- [ ] Add state management for drawer open/close
- [ ] Pass `match_details[columnName]` to drawer on button click
- [ ] Implement `onSwitchToAlternate` handler (future: API endpoint)
- [ ] Test with mortgage example to validate full flow

**Files to Edit:**
- `web-ui/src/pages/ProjectDetail.tsx`

**Acceptance Criteria:**
- Clicking [📊 Evidence] button opens drawer
- Drawer displays all evidence fields correctly
- Alternates are visible (switch action can be no-op for now)
- Drawer closes on X or outside click

---

### 2. Validation Dashboard Display
**Priority:** HIGH  
**Effort:** 4-6 hours  
**Status:** Backend validation exists, UI display missing

**Context:** Per FEATURE_IMPLEMENTATION_CHECKLIST.md:
- SHACL validation runs but results not shown in UI
- Constraint violations not displayed
- Validation error samples missing

**Tasks:**
- [ ] Create `ValidationDashboard.tsx` component
- [ ] Add to ProjectDetail after conversion step
- [ ] Display SHACL validation results (conforms: true/false)
- [ ] Show constraint violations table (property, constraint, count)
- [ ] Add ontology validation metrics (domain/range violations)
- [ ] Create validation report download (JSON/HTML)

**API Endpoints Needed:**
- GET `/api/projects/{id}/validation` (may need to create)
- Current validation logic in `src/rdfmap/polars_engine/validator.py`

**Acceptance Criteria:**
- Validation results visible post-conversion
- SHACL conforms status displayed
- Constraint violations listed with counts
- Downloadable validation report

---

## 🚀 HIGH PRIORITY (Week 3-4)

### 3. Manual Mapping Interface
**Priority:** HIGH  
**Effort:** 8-12 hours  
**Status:** Documented in CYTOSCAPE_ONTOLOGY_VISUALIZATION.md

**User Story:** When auto-mapping fails, user needs to manually map column to property.

**Tasks:**
- [ ] Create `ManualMappingModal.tsx` component
- [ ] Property search with autocomplete
- [ ] Display unmapped columns list
- [ ] Alternative property suggestions from API
- [ ] "Switch to alternate" from Match Reasons table
- [ ] API endpoint: POST `/api/projects/{id}/mappings/manual`

**Acceptance Criteria:**
- Modal opens for unmapped columns
- Search filters property list
- Selecting property creates mapping
- Match reasons table reflects manual mappings

---

### 4. Matcher Attribution Clarity Fix
**Priority:** HIGH  
**Effort:** 2-3 hours  
**Status:** Backend captures evidence, UI needs display format

**Issue:** DataTypeInferenceMatcher appearing as primary everywhere.

**Solution:** Display format: `Primary: SemanticMatcher (0.78) | Context: DataType (string)`

**Tasks:**
- [ ] Update Match Reasons table "Matcher" column format
- [ ] Extract primary matcher from evidence stack (first/highest)
- [ ] Show context matchers as chip tags below primary
- [ ] Update Evidence Drawer to highlight primary vs context

**Files to Edit:**
- `web-ui/src/pages/ProjectDetail.tsx` (match reasons table)
- `web-ui/src/components/EvidenceDrawer.tsx` (add primary highlight)

---

## 🎨 NEXT PHASE (Week 5-8)

### 5. Cytoscape.js Integration - Contextual Views
**Priority:** MEDIUM-HIGH  
**Effort:** 16-24 hours  
**Status:** Detailed plan in CYTOSCAPE_ONTOLOGY_VISUALIZATION.md

**Philosophy:** Graph viz should be **contextual and lightweight**, not a separate overwhelming screen.

#### 5a. Mini Graph Preview in Ontology Summary
**Effort:** 4-6 hours

- [ ] Install `cytoscape` and `cytoscape-cola` npm packages
- [ ] Create `OntologyGraphMini.tsx` (300x200px embedded preview)
- [ ] Show class hierarchy with 3 levels
- [ ] Click to expand full-screen modal
- [ ] Add to ontology summary section

#### 5b. Slide-Out Panel from Match Reasons [📊 Graph]
**Effort:** 6-8 hours

- [ ] Create `PropertyContextPanel.tsx`
- [ ] Add [📊 Graph] button to match reasons table
- [ ] Panel shows property in context (parent class, siblings)
- [ ] Highlight target property (pulsing)
- [ ] Show alternative properties
- [ ] Allow drag column to different property

#### 5c. Manual Mapping Modal - Graph View
**Effort:** 6-8 hours

- [ ] Add graph view tab to `ManualMappingModal.tsx`
- [ ] Split view: Property list (left) | Graph (right)
- [ ] Search filters both list and graph
- [ ] Click property in graph to select
- [ ] Highlight selected property

#### 5d. Coverage Map Post-Conversion
**Effort:** 4-6 hours

- [ ] Create `CoverageMapView.tsx`
- [ ] Color nodes by mapping status (green/yellow/red)
- [ ] Green: Mapped, Yellow: Partially mapped, Red: Unmapped
- [ ] Click node to see missing properties
- [ ] Add to post-conversion analysis section

---

### 6. Visual Mapping Editor (React Flow)
**Priority:** MEDIUM  
**Effort:** 20-30 hours  
**Status:** Documented in WEB_UI_ARCHITECTURE.md Phase 2

**Vision:** Drag-and-drop visual editor for creating/editing mappings.

**Tasks:**
- [ ] Install `reactflow` npm package
- [ ] Create `VisualMappingEditor.tsx`
- [ ] Left panel: CSV columns (draggable nodes)
- [ ] Right panel: Ontology properties (drop targets)
- [ ] Middle canvas: Visual connections with confidence overlays
- [ ] Edit/delete connections
- [ ] Alternative suggestions on connection click
- [ ] Export/import visual layouts

**Deferred to:** Week 9-12 (after core UX is solid)

---

## 📊 LOWER PRIORITY (Week 9-12)

### 7. Bulk Actions on Mappings
- [ ] "Accept all high confidence (>0.8)" button
- [ ] "Reject all low confidence (<0.5)" button
- [ ] "Review all semantic matches" filter
- [ ] Export/import mapping overrides

### 8. Real-Time Progress Updates (WebSockets)
- [ ] During mapping generation (show matcher progress)
- [ ] During RDF conversion (show row count)
- [ ] Live alignment report updates
- [ ] WebSocket endpoint: `/ws/projects/{id}`

### 9. Template Gallery
- [ ] Browse pre-built templates (Financial, Healthcare, E-commerce)
- [ ] Use template for new project
- [ ] Fork/customize templates
- [ ] Template management API

### 10. RDF Preview Panel
- [ ] Live preview of generated RDF (split view)
- [ ] Syntax highlighting (Turtle/JSON-LD/RDF-XML)
- [ ] Search in RDF
- [ ] Monaco Editor integration

---

## 🧪 VALIDATION & TESTING

### Matcher Validation Suite
**Status:** Documented in MATCHING_VALIDATION_ANALYSIS.md

**Needed:**
- [ ] Create `tests/validation/contrived_cases.py`
  - Abbreviations (emp_num → employeeNumber)
  - Synonyms (cost_center → costCentre)
  - Ambiguous cases (payment_method → ?)
- [ ] Create `tests/validation/real_world_examples/`
  - Healthcare (FHIR)
  - E-commerce (schema.org)
  - Financial (FIBO)
- [ ] Automated testing: precision, recall, confidence calibration
- [ ] Ground truth datasets with expected matches
- [ ] Regression tests for each matcher type

---

## 📈 SUCCESS METRICS

### Stage 2 Matcher Refactor (✅ COMPLETE)
- ✅ Confidence scores realistic (0.4-1.0 range, not all 1.00)
- ✅ Matcher attribution captured in evidence
- ✅ Ambiguity detected and penalized
- ✅ Alternates available for user review
- ✅ Validation tests pass

### UI Evidence Transparency (🚧 IN PROGRESS)
- ⏳ Evidence Drawer component created
- ⏳ Integration with ProjectDetail (NEXT)
- ⏳ All evidence fields displayed correctly
- ⏳ User can switch to alternates

### Validation Display (📋 QUEUED)
- ⏳ SHACL results visible in UI
- ⏳ Constraint violations listed
- ⏳ Downloadable validation reports

### Manual Mapping (📋 QUEUED)
- ⏳ Modal for unmapped columns
- ⏳ Property search works
- ⏳ Manual mappings persist

### Graph Visualization (📋 QUEUED)
- ⏳ Mini preview in ontology summary
- ⏳ Slide-out panel from match reasons
- ⏳ Graph view in manual mapping
- ⏳ Coverage map post-conversion

---

## 🔄 CONTINUOUS IMPROVEMENTS

### Documentation
- [ ] Update FEATURE_IMPLEMENTATION_CHECKLIST.md as features complete
- [ ] Keep LOG-001 updated with daily progress
- [ ] Add UI screenshots to docs/
- [ ] Create video walkthrough for new features

### Code Quality
- [ ] Add TypeScript types for all API responses
- [ ] Write unit tests for new UI components
- [ ] Integration tests for evidence drawer workflow
- [ ] E2E tests for full mapping workflow

### Performance
- [ ] Monitor API response times
- [ ] Optimize evidence aggregation for large datasets
- [ ] Cache ontology graph layouts
- [ ] Lazy-load Cytoscape only when needed

---

## 📝 NOTES

### Design Principles (from Cytoscape doc)
1. **Progressive Disclosure:** Start simple, reveal complexity only when needed
2. **Contextual:** Show graph when it helps decision-making
3. **Non-Blocking:** Doesn't interrupt main workflow
4. **Avoid Overwhelming:** Don't dump 1000-node graph on users

### Key Insights
- Semantic confidence bug already fixed via Stage 1/2 ✅
- Backend has all data needed for transparency ✅
- Focus on UX polish and contextual help
- Graph viz should enhance, not replace, existing workflow

---

**Next Action:** Wire EvidenceDrawer into ProjectDetail match reasons table.

