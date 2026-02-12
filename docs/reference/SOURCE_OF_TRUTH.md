# Web4 Source of Truth

**Last Updated**: February 12, 2026

This document defines the **authority hierarchy** for Web4 documentation. When conflicts arise between documents, use this hierarchy to determine which governs.

---

## Authority Hierarchy

### Tier 1: Normative Specifications (Highest Authority)

These documents define the canonical behavior and are the final word on "what something is."

| Document | Governs |
|----------|---------|
| `docs/reference/CANONICAL_TERMS_v1.md` | Term definitions, acronym expansions |
| `web4-standard/core-spec/*.md` | Protocol specifications (LCT, T3, V3, ATP, etc.) |
| `web4-standard/README.md` | Standard versioning and compatibility |

### Tier 2: Implementation Status

These documents describe the current state of implementation.

| Document | Governs |
|----------|---------|
| `STATUS.md` | What is built vs. planned |
| `SECURITY.md` | Security scope and contact |
| `CHANGELOG.md` | Version history |

### Tier 3: Reference and Guidance

These documents help users understand and use the system.

| Document | Governs |
|----------|---------|
| `docs/reference/GLOSSARY.md` | Quick-reference definitions (defer to Tier 1 on conflicts) |
| `docs/how/*.md` | Integration guides |
| `docs/architecture/*.md` | Design rationale |

### Tier 4: Overview (Lowest Authority)

High-level entry points that may simplify or summarize.

| Document | Governs |
|----------|---------|
| `README.md` | Project overview, getting started |
| Repository index files | Discovery and navigation |

---

## Conflict Resolution

When documents conflict:

1. **Higher tier wins.** A core-spec document overrides the glossary.
2. **Within same tier, more specific wins.** `LCT-linked-context-token.md` overrides `web4-standard/README.md` for LCT details.
3. **When unclear, file an issue.** Tag it `documentation` and `conflict`.

---

## Common Conflicts and Resolutions

| Conflict | Resolution |
|----------|------------|
| README.md says T3 is 6-dimensional | CANONICAL_TERMS says 3D. **3D is correct.** T3+V3 together form 6D space. |
| GLOSSARY.md uses different T3 components | CANONICAL_TERMS governs. **Talent/Training/Temperament** is canonical. |
| Old docs reference `/game/` directory | `/game/` moved to standalone 4-life repo. Update links to external repo or `archive/game-prototype/`. |
| STATUS.md and README.md disagree on completion | STATUS.md governs implementation state. |

---

## Updating This Document

When adding new authoritative documents:

1. Determine appropriate tier
2. Add to table with scope description
3. Update CANONICAL_TERMS if new terminology introduced
4. Commit with reference to this file

---

## Related Documents

- [CANONICAL_TERMS_v1.md](./CANONICAL_TERMS_v1.md) - Authoritative terminology
- [GLOSSARY.md](./GLOSSARY.md) - Quick reference (Tier 3)
- [web4-standard/README.md](../../web4-standard/README.md) - Standard overview
