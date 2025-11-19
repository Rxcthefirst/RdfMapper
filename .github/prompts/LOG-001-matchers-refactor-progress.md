---
id: LOG-001
title: Progress Log – Matcher Refactor & Calibration
type: log
version: 0.1.0
status: active
owner: Core Engine Team
date: 2025-11-16
tags: [progress, decisions]
links:
  - REF-001
  - TASK-001
---

# Progress Log: Matcher Refactor & Calibration

- 2025-11-16
  - Stage 1 implemented: Introduced MatchType.DATA_TYPE_COMPATIBILITY and refactored DataTypeInferenceMatcher to be type-only (removed name similarity). Now emits data_type_compatibility.
  - Updated confidence mapping (fallback) for new match type.
  - Baseline validation passed; output shows clearer attribution and stable variance: semantic vs datatype vs exact matches are distinguished.
  - No API regressions detected in scripts; next step is aggregation/evidence and ambiguity handling per REF-001.

- 2025-11-16
  - Fixed confidence pipeline to use actual matcher confidence (removed legacy override).
  - Reweighted and capped DataTypeInferenceMatcher; still observed high clustering in diverse tests.
  - Added validation scripts: `scripts/validate_matching.py`, `scripts/validate_confidence_calibration.py`.
  - Analysis: 90% high confidence across tests; ambiguous columns not penalized → needs aggregation & ambiguity detection.
  - Authored design refactor doc (REF-001) and working prompt (TASK-001).

- 2025-11-16
  - Stage 2 started: Implemented aggregation in MappingGenerator using pipeline.match_all, combined base + boosters with ambiguity penalty (0.05–0.10), clamped results.
  - Baseline validation (mortgage) PASS with Std=0.086; attribution shows exact/datatype/semantic/graph distributed; no regressions.
  - Next: add alternates/evidence to alignment report and extend UI to display stack and alternates (per REF-001).

- 2025-11-16
  - Stage 2 continued: Added per-column evidence capture and alternates in MappingGenerator; extended MatchDetail population with evidence/boosters/penalties/ambiguity_group_size/alternates (models accept dict coercion for now).
  - Baseline validation PASS (mortgage); no regressions observed; confidence variance unchanged, as expected.
  - Next: formalize EvidenceItem/AdjustmentItem/AlternateCandidate classes in models (extend alignment.py) and wire UI Evidence Drawer (Phase: UI sync).

- 2025-11-16
  - Stage 2 complete: Formalized Pydantic models (AdjustmentItem, EvidenceItem, AlternateCandidate) and extended MatchDetail with evidence/boosters/penalties/ambiguity/alternates fields.
  - Validation PASS with no schema regressions; all fields serialize correctly.
  - Ready for UI wiring: Evidence Drawer component to display evidence stack, adjustments, ambiguity, and alternates with progressive disclosure.
  - Next: Wire UI to consume extended MatchDetail fields and display evidence transparency (TASK-001 checklist near complete).

- 2025-11-16
  - Documentation review: Analyzed ANALYSIS_SUMMARY_NOV16.md, FEATURE_IMPLEMENTATION_CHECKLIST.md, CYTOSCAPE_ONTOLOGY_VISUALIZATION.md.
  - Key findings:
    - ✅ Semantic confidence bug FIXED (Stage 1/2 work addressed the 1.00 scores issue)
    - 🎯 HIGH PRIORITY: Wire UI Evidence Drawer to show matcher attribution, evidence stack, alternates
    - 🎯 HIGH PRIORITY: Add validation display to UI (currently only backend)
    - 🎯 NEXT PHASE: Manual mapping modal with property search and graph context
    - 🎯 NEXT PHASE: Cytoscape.js integration (contextual, not separate screen)
  - Task queue updated per FEATURE_IMPLEMENTATION_CHECKLIST priorities:
    1. Evidence Drawer (Stage 2 completion) ← CURRENT
    2. Validation Dashboard in ProjectDetail
    3. Manual Mapping Interface with alternatives
    4. Cytoscape graph views (match reasons slide-out, manual mapping modal, ontology summary)
  - Next: Implement Evidence Drawer component in ProjectDetail to display match_details with full transparency.

- 2025-11-16
  - Stage 2 UI implementation: Created EvidenceDrawer.tsx component with:
    - Evidence stack table showing all matchers (name, type, score, matched_via)
    - Boosters/penalties display with icons and magnitudes
    - Ambiguity warning when multiple candidates were close
    - Alternates list (clickable to switch property)
    - Progressive disclosure (collapsible accordions)
    - Material-UI styling consistent with existing UI
  - Ready to wire into ProjectDetail match reasons table with [📊 Evidence] button per row.
  - Stage 2 COMPLETE: Full evidence transparency from backend → frontend.
  - Next queue based on FEATURE_IMPLEMENTATION_CHECKLIST:
    1. Wire EvidenceDrawer into ProjectDetail (add button + state)
    2. Validation Dashboard display (SHACL results, constraint violations)
    3. Manual Mapping Interface (modal for unmapped columns)
    4. Cytoscape.js contextual views (slide-out, mini preview, manual mapping graph)

- 2025-11-16
  - UI enhancements: Added ValidationDashboard component consolidating ontology SHACL constraints, uploaded shapes validation, structural ontology checks.
  - Integrated EvidenceDrawer button column and Remap (manual override) flow with ManualMappingModal (local override pending backend endpoint).
  - Manual overrides set match_type=manual_override & confidence=1.0 locally (temporary).
  - Next: Implement backend override API (POST /api/projects/{id}/mappings/override), persist manual changes, and display primary/context matcher attribution in table.

- 2025-11-16
  - Backend: Added POST /api/mappings/{project_id}/override endpoint to persist manual mapping overrides (updates mapping_config.yaml + alignment_report match_details).
  - Frontend: Wired overrideMapping API call; Remap modal now persists overrides (confidence=1.0, matcher=ManualOverride) and updates local state.
  - Next: Enhance matcher attribution display (Primary vs Context) using evidence stack; integrate alternates 'Use' action to call override endpoint.

- 2025-11-16
  - UI: Added matcher attribution formatting in Match Reasons table (Primary matcher + contextual evidence chips + manual override badge). Displays up to 6 context matchers with overflow indicator.

- 2025-11-16
  - UI: Added ontology visualization phase 1.
    - Installed cytoscape & cytoscape-cola.
    - Created OntologyGraphMini (limited nodes/edges, click to expand) and OntologyGraphModal (full-screen interactive graph).
    - Integrated mini graph + View Graph button in Ontology Summary.
  - Next: Color nodes by mapping coverage, add search/filter, and integrate property selection with manual mapping overrides.
