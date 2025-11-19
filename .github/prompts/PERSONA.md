---
id: PERSONA-001
title: Engineering Agent Persona & Workflow
type: reference
version: 0.1.0
status: active
owner: Core Engineering
date: 2025-11-16
tags: [persona, workflow, prompts]
links:
  - REF-001
  - TASK-001
  - LOG-001
---

# Engineering Agent Persona & Workflow

Principles
- Be explicit about task focus: start responses with a one-line task receipt and a short plan.
- Use the prompts registry in `.github/prompts/` to load context before working.
- Maintain a continuous progress log (LOG-xxx) for traceability.
- Prefer small, staged changes with validation after each stage.

Workflow
1) Load the current working prompt (TASK-xxx) and reference docs (REF-xxx) from `.github/prompts/index.json`.
2) Restate the objective and checklist; then execute the next item end-to-end.
3) After implementing, run validation scripts; report PASS/FAIL succinctly.
4) Append accomplishments and decisions to LOG-xxx (latest at top).
5) If scope changes, update TASK-xxx and link to REF-xxx as needed.

Conventions
- Use YAML front matter in all prompts; ensure index.json stays in sync.
- Preserve backward-compatible API fields when adding new structures.
- Prefer evidence aggregation and clear attribution in reports.

Validation
- Always run `scripts/validate_matching.py` and, when relevant, `scripts/validate_confidence_calibration.py` after matcher changes.
- For API/UI changes, run smoke tests and note any container/proxy caveats.

Escalation
- If blocked by missing details, document assumptions in TASK-xxx and proceed with the safest default.

