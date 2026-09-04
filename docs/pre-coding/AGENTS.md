# AGENTS.md — Coding Agent Contract

## Mission
Implement the IPO Listing-Gain Decision Engine from the approved docs. Do not invent already-decided product or strategy rules.

## Before coding
1. Read all `docs/pre-coding/*.md`.
2. Inspect the current repository and separate prototype code from intended architecture.
3. Run `/setup-matt-pocock-skills` if the repo is not configured.
4. Use the domain glossary.
5. Use `/grill-with-docs` or `/to-spec` when a genuine new ambiguity/feature arises.

## Engineering rules
- Preserve point-in-time semantics.
- Keep raw data separate from derived features.
- Isolate source adapters.
- Keep strategy out of UI.
- Add tests at the highest useful seam.
- Prefer small, reviewable changes.
- Do not add complex ML before baseline evidence exists.

## Research integrity
Never fabricate data, use look-ahead information, or present synthetic/in-sample performance as evidence of an edge.

## Versioning
Every prediction stores model, feature and strategy versions plus the decision timestamp.

## Recommended Matt Pocock workflow
Setup → domain/context → PRD/spec → TDD → implementation → code review → architecture review as needed.

## Success
Code, tests, data lineage, decisions and research results should all be reproducible and explicit.
