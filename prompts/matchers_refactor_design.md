Title: Matcher Responsibilities, Aggregation, and Confidence Calibration – Refactor Design
Date: 2025-11-16
Owner: Core Engine Team
Status: Draft for implementation (target: Phase 1B)

1) Problem Statement
- Confidence scores are clustered too high, especially on ambiguous columns (e.g., name, id, date).
- DataTypeInferenceMatcher mixes concerns by including name similarity and reporting match_type=SEMANTIC_SIMILARITY.
- Pipeline returns the first match above threshold, hiding ambiguity and preventing evidence aggregation.
- Alignment output doesn’t clearly attribute which matcher contributed evidence vs which produced the primary match.

2) Goals and Non-Goals
Goals
- Separate matcher responsibilities cleanly (semantic vs datatype vs structural).
- Change selection from “first success” to “aggregate evidence across matchers, then decide”.
- Introduce ambiguity penalties and boosters; produce calibrated, realistic confidence.
- Improve alignment report structure to surface evidence stack and ambiguity.
- Keep performance acceptable (embedding cache, minimal extra passes).

Non-Goals (now)
- Full ML-based calibration trained on user feedback (future phase).
- Replacing existing embeddings model (we will keep the configured model).
- UI visual editor work (handled in a different epic).

3) Proposed Architecture Changes
3.1 Matcher Responsibilities
- Exact Matchers (Pref/RDFS/Alt/Hidden/Local): deterministic string match tiers. Confidence: constants per tier.
- Semantic Matcher: embedding+lexical similarity with class/context boosts; computes continuous score; applies ambiguity penalty; primary source for name-based similarity.
- Datatype Compatibility Matcher: evaluate inferred XSD type vs property range (exact=0.85, compatible=0.70, else 0.0). No name similarity. New MatchType: DATA_TYPE_COMPATIBILITY.
- Structural/Relationship Matcher: detect FK/object relationships; confidence from structural signals (0.90–1.00 for clear FK patterns).
- Hierarchy/OWL Characteristics Matcher: small boosters (+0.02–0.05) for uniqueness/functional hints; rarely primary.
- SKOS Relations Matcher: evidence booster if not exact; or primary if exact alt/hidden label hit.

3.2 Aggregation Layer (new behavior)
- Gather candidate results from all enabled matchers for a column (no early exit).
- Collapse by property URI, keeping list of evidences: [{matcher, match_type, confidence, via}].
- Compute combined_confidence:
  base = max(primary_confidence from [Exact, Semantic])
  boosters = sum(small boosts from [Datatype, Hierarchy, SKOS, Structural hints]) with caps
  penalties = ambiguity_penalty + generic_token_penalty (e.g., very short names)
  final = clamp(base + boosters − penalties, 0.15, 1.00)
- Ambiguity penalty: if top-k semantic candidates are within ε (e.g., within 10% of top), subtract 0.05–0.20 depending on cluster size.
- Choose primary match = argmax(final). Retain top 3 alternates with individual combined_confidence.

3.3 Confidence Model (initial calibration)
- Exact tiers: Pref=1.00, RDFS=0.95, Alt=0.90, Hidden=0.85, Local=0.80.
- Semantic: raw similarity → rescale to 0.35–0.90.
- Datatype compatibility: exact=0.85, compatible (e.g., int vs decimal)=0.70, string fallback=0.60 only if strong semantic base exists.
- Structural FK/object evidence: +0.05–0.10 booster (not primary unless structural-only phase).
- Hierarchy/OWL uniqueness: +0.02–0.05 booster.
- Ambiguity penalty: −0.05 per close competitor, capped at −0.20.
- Generic short token penalty (e.g., id, name, date): −0.05 to −0.10.

4) Alignment Report Enhancements
4.1 MatchDetail (per column)
- primary_property (IRI)
- combined_confidence (float)
- primary_matcher (string)
- match_type (enum)
- matched_via (string)
- evidence: list of { matcher_name, match_type, confidence, matched_via }
- ambiguity_group_size (int)
- penalties_applied: list of { type, value }
- boosters_applied: list of { type, value }
- alternates: list of { property, combined_confidence, evidence_count }

4.2 Backward Compatibility
- Keep existing fields (column_name, matched_property, match_type, confidence_score, matcher_name, matched_via) but populate from combined figures.

5) API & UI Implications
- API: update generator’s alignment_report to include evidence, penalties, alternates.
- UI: Match Reasons table shows
  - Confidence (combined)
  - Primary matcher
  - “View details” to expand evidence and ambiguity cluster
  - Show top-3 alternates (click to switch)

6) Implementation Plan (staged)
Stage 1 (1–2 days)
- Add MatchType.DATA_TYPE_COMPATIBILITY.
- Remove name similarity from DataTypeInferenceMatcher; only type logic remains.
- Ensure DataTypeInferenceMatcher outputs DATA_TYPE_COMPATIBILITY.
- Maintain current pipeline, but pass through actual matcher confidences (already fixed).

Stage 2 (2–3 days)
- Implement aggregation layer in MatcherPipeline:
  - new method match_all_with_evidence(column, properties, context) → list[MatchResult] from all matchers.
  - aggregator to combine by property and compute combined_confidence with boosters/penalties.
  - ambiguity detection & penalties.
- Update mapping_generator to use aggregator instead of first-success.
- Expand alignment report with evidence/alternates; keep backward fields.
- Update tests & validation scripts (expect broader distribution).

Stage 3 (1–2 days)
- Fine-tune thresholds and penalty magnitudes using validation suite.
- Add config flags in GeneratorConfig to tweak thresholds (semantic_threshold, ambiguity_epsilon, booster_caps) for power users.

Stage 4 (later)
- Historical calibration using acceptance data.
- Domain-specific priors per ontology.

7) Testing & Validation
Unit Tests
- DataTypeInferenceMatcher no longer considers names; verify type-only behavior.
- Semantic matcher returns continuous scores; verify ambiguity penalty applied when top2 close.
- Aggregation computes combined_confidence with boosters/penalties correctly.

Integration Tests
- Mortgage baseline: high but more varied scores; still >80% high acceptable.
- Ambiguous columns: medium scores 0.50–0.70; alternates present.
- Abbreviations: mixture of medium/high; std dev ≥ 0.12.

Metrics & Scripts
- scripts/validate_matching.py (existing) for sanity checks.
- scripts/validate_confidence_calibration.py (extended) to track distribution across cases.

8) Risks & Mitigations
- Risk: Over‑penalizing true positives when terms are legitimately ambiguous but context says otherwise → Mitigate via small, capped penalties and context boosts.
- Risk: Performance due to multiple matcher passes → Cache embeddings and property analysis; reuse analyzer instances.
- Risk: UI overload with evidence → Progressive disclosure (expand row for details).

9) Rollout & Config
- Feature flag: enable_aggregation_v2 (default on after bake-in).
- Config knobs: semantic_threshold, ambiguity_epsilon, booster_caps, penalty_caps.
- Backward compat: Retain simple confidence if aggregator disabled.

10) Acceptance Criteria
- On ambiguous test, ≥60% of columns fall into 0.5–0.8; high confidence ≤40%.
- On mortgage baseline, high confidence remains ≥80%.
- Alignment report includes evidence and alternates.
- No regression in runtime >10% on baseline datasets.

Appendix A: Example Evidence Block
column: name
primary: ex:fullName (0.62)
primary_matcher: SemanticSimilarityMatcher
penalties: [ {type: ambiguity, value: 0.10}, {type: generic_token, value: 0.05} ]
boosters: [ {type: datatype_compatibility, value: 0.05} ]
alternates:
- ex:personName (0.59)
- ex:customerName (0.56)
- ex:contactName (0.54)

Appendix B: Data Model Deltas
- Add MatchType.DATA_TYPE_COMPATIBILITY
- Extend AlignmentReport.MatchDetail schema to include evidence, penalties, alternates

