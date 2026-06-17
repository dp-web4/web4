# Web4 Best Practices

**Strong recommendations for robust Web4 implementations — not part of the core standard.**

The Web4 core standard defines the *ontology and protocols* (LCTs, T3/V3·MRH, ATP/ADP,
witnessing, SAL, R6). It deliberately does **not** mandate how an implementation stores its
state, manages keys, or hardens its deployment — those are implementation concerns.

This directory collects **best-practice guidance**: patterns that production-grade Web4
implementations are strongly encouraged to follow. They are recommendations, not
conformance requirements — a system can be standard-conformant without them, but a
*trustworthy* deployment generally shouldn't be.

The distinction matters: trust infrastructure whose own state sits in plaintext, or whose
keys are recoverable from a stolen disk, undermines the very property the standard exists to
provide. Best practices are how an implementation earns the trust the standard lets it
*claim*.

## Documents

- [`storage-and-key-management.md`](storage-and-key-management.md) — **full enclosure**:
  encrypt all state at rest, memory-only unlock, fail-closed, and the complementary roles of
  application-level encryption and full-disk encryption.

*(More to come — agent identity hygiene, witnessing discipline, deployment hardening.)*

## How these relate to the core standard

- **Core standard** (`../specs/`, `../reference/`): the protocols and ontology. Normative.
- **Best practices** (here): how to implement them robustly. Recommended.
- Implementation-specific mechanisms (a given product's vault internals, hardware-binding
  specifics) live in that product's own repository, not here.
