# Project Prompts Registry

This folder centralizes prompts and reference docs used to guide development and reviews.

Conventions
- Location: `.github/prompts/`
- File types:
  - `REF-xxx-<slug>.md` → Reference/design docs (stable context)
  - `TASK-xxx-<slug>.md` → Working task prompts (current iteration focus)
  - `LOG-xxx-<slug>.md` → Append-only progress logs (history & decisions)
  - `index.json` → Machine-readable catalog for tools
- Front matter (YAML) at top of each file:
  ```yaml
  ---
  id: REF-001            # unique id
  title: Matcher Responsibilities, Aggregation, and Confidence Calibration – Refactor Design
  type: reference        # reference | task | log
  version: 0.1.0
  status: draft          # draft | active | done
  owner: Core Engine Team
  date: 2025-11-16
  tags: [matchers, confidence, aggregation]
  links:
    - LOG-001
    - TASK-001
  ---
  ```

How to use
- Reference docs (REF-xxx) provide background and design constraints to include in system/developer prompts.
- Task prompts (TASK-xxx) describe today’s objectives, guardrails, checklists, and DoD.
- Log files (LOG-xxx) are append-only; add latest entries to the top.
- Tools can discover files via `index.json`.

Updating
- When you start a new iteration, duplicate the latest `TASK-xxx` and bump the id.
- Add a new entry in `index.json` (or let automation update it).
- Append a summary of outcomes to the `LOG-xxx` file when the iteration ends.

