---
id: TASK-001
title: Working Prompt – Matcher Refactor & Confidence Calibration (Phase 1B)
type: task
version: 0.1.0
status: active
owner: Core Engine Team
date: 2025-11-16
tags: [matchers, aggregation, confidence]
links:
  - REF-001
  - LOG-001
---

# Working Prompt: Matcher Refactor and Confidence Calibration (Phase 1B)

Objective
- Implement matcher separation, evidence aggregation, and confidence calibration to reduce over‑confidence on ambiguous columns and improve transparency.

Scope (this iteration)
- Stage 1: Create DATA_TYPE_COMPATIBILITY match type; enforce type-only behavior in DataTypeInferenceMatcher.
- Stage 2: Add aggregation path to gather evidence, apply boosters/penalties with ambiguity detection.
- Update alignment report with evidence and alternates.

Guardrails
- Preserve backward fields; fallback gracefully if UI doesn’t consume new fields yet.
- Configurable thresholds via GeneratorConfig.
- Keep runtime impact under 10% on mortgage baseline.

Definition of Done
- Mortgage: ≥80% high confidence, visible variance.
- Ambiguous test: 40–60% medium confidence, alternates present.
- Extended validation scripts pass with improved variance.

Checklist
- [ ] Add MatchType.DATA_TYPE_COMPATIBILITY
- [ ] Remove name similarity from DataTypeInferenceMatcher (type-only)
- [ ] Emit DATA_TYPE_COMPATIBILITY evidence
- [ ] Implement pipeline match_all_with_evidence
- [ ] Aggregation: combine, boost, penalize, detect ambiguity
- [ ] Update alignment report schema & population
- [ ] Update tests and validation scripts

Next Up
- Evidence drawer in UI with alternatives
- User feedback capture for future calibration

