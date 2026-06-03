# C29 — `data-formats.md` First-Pass Internal-Consistency + Cross-Spec Audit

**Audit ID**: C29
**Target**: `web4-standard/core-spec/data-formats.md` (137 lines)
**Date**: 2026-06-03
**Auditor**: autonomous web4 session (legion, slot `120001`), v2 protocol
**Type**: First-pass internal-consistency audit + cross-spec consistency audit
**Prior coverage**: none — `data-formats.md` is genuinely un-audited. C27 (core-protocol) and C28 (web4-handshake) both *defer to* this document; this audit examines the deference target itself.

---

## Scope & Methodology

`data-formats.md` is the document that `core-protocol.md:99` designates as the **single source of truth** for Web4 data and credential formats:

> *"Web4 data and credential formats (W4ID, Verifiable Credentials, JSON-LD) — together with pairwise-identifier derivation and canonicalization … are normatively specified in `data-formats.md`. … `data-formats.md` is the single source of truth."*

Because it is the SSOT for identifiers and canonicalization, an inconsistency here propagates to every spec that references it. The audit proceeds in two passes plus the **auditor-blindspot pass**:

1. **Internal-consistency pass** (§A) — does the document agree with itself, section to section?
2. **Cross-spec pass** (§B) — does it agree with the specs that consume it (`core-protocol.md`, `web4-handshake.md`, `LCT-linked-context-token.md`, `web4-lct.md`, `errors.md`, `web4-witnessing.md`, `web4-metering.md`, `multi-device-lct-binding.md`, `lct-capability-levels.md`)?
3. **Primitive-clustered pass** — re-read with the *identifier* primitive as the lens, looking for cross-section contradictions that a section-by-section read misses (the `auditor-blindspot-pattern`).

Severity: **HIGH** = correctness/normative contradiction; **MEDIUM** = consumer-affecting inconsistency or wrong normative citation; **LOW** = hygiene/reference discipline; **INFO** = forward-awareness, no action required.

Each finding is routed: **AUTONOMOUS** (a future remediation turn can fix it inside `data-formats.md` without a design decision), **DESIGN-Q** (requires an operator-level decision; routed to an existing carry, *not* resolved here per binding condition 1), or **CROSS-TRACK** (the fix or verification lands in *another* spec — not edited this turn).

---

## §A — Internal-Consistency Findings

### A-H1 (HIGH, DESIGN-Q) — The SSOT contradicts itself on identifier scheme

§1.1 defines the canonical Web4 Identifier with a **DID scheme**:

```
w4id = "did:web4:" method-name ":" method-specific-id
```

and §1 asserts the W4ID is *"compliant with the W3C Decentralized Identifier (DID) specification."* But §4.1 (Pairwise W4ID Derivation) emits:

```python
return f"w4id:pair:{base32_encode(pairwise_key[:16])}"
```

— a `w4id:pair:` scheme, which is **not a valid DID** (a DID MUST begin with `did:`). So within the single document designated as the identifier SSOT, §1 uses `did:web4:…` and §4 uses `w4id:pair:…`. The document is self-contradictory on the most fundamental primitive it owns.

This is the cross-section contradiction surfaced by the primitive-clustered pass: read section-by-section, §1 and §4 each look internally fine; read through the *identifier-scheme* lens they directly conflict.

- **Routing**: DESIGN-Q. The prefix choice (`did:web4:` vs `w4id:` vs a distinct pairwise scheme) is the **open repo-wide identifier-scheme decision** that `core-protocol.md:99` already flags as *"intentionally not resolved."* Resolving §1-vs-§4 *is* that decision. Bundles into `carry-C28-design-Q` (C-M3) / C27-H1 / C24-H1.
- **Autonomous sub-option (non-binding on the decision)**: a remediation turn *could*, without picking the scheme, add a sentence to §4 stating that pairwise identifiers are a **distinct, deliberately non-DID identifier class** pending the scheme decision — converting a silent contradiction into a documented, scoped exception. Flagged for the remediator's judgment; not mandated.

### A-M1 (MEDIUM, AUTONOMOUS + cross-track verify) — Method-name set omits `device`

§1.2 enumerates a closed-looking set:

> *"Web4 defines the following methods … `key` … `web` …"*

But `did:web4:device:…` is used as a normative method-name in `multi-device-lct-binding.md:244`. The SSOT's method enumeration is missing a method that another core-spec doc already uses.

- **Routing**: AUTONOMOUS (the fix lands in `data-formats.md` §1.2 — either register `device`, or restate the list as **non-exhaustive/extensible** with a method registry). A full enumeration of method-names in use across the corpus is a CROSS-TRACK verification the remediator should run first (at minimum `key`, `web`, `device` are attested).

### A-M2 (MEDIUM, AUTONOMOUS) — §5.1 JCS code does not implement RFC 8785

§5.1 mandates JCS (RFC 8785) for JSON canonicalization (correct, normative) but illustrates it with:

```javascript
function canonicalizeJSON(obj) {
  return JSON.stringify(obj, Object.keys(obj).sort());
}
```

This does **not** implement JCS. `JSON.stringify(obj, replacerArray)` only whitelists *top-level* keys; it does **not** recursively sort nested object keys, and it does not apply RFC 8785's number-serialization or string-escaping rules. An implementer copying this snippet would produce non-canonical, non-interoperable signatures — in the SSOT for canonicalization, on which all signature verification depends.

- **Routing**: AUTONOMOUS. Relabel the snippet as a **non-normative sketch** and state plainly that conformance requires a full RFC 8785 implementation (the prose MUST is correct; only the code misleads). The §5.2 CBOR block is already comment-only/illustrative and is fine.

### A-L1 (LOW, AUTONOMOUS) — Two-era authoring residue

A stray `_` on line 65 (an orphaned horizontal-rule/emphasis artifact) and inconsistent multi-blank-line spacing (lines 4–7, 63–68, 99–101) mark where §§4–5 were appended in a later editing pass than §§1–3. Cosmetic but visible in the SSOT.

- **Routing**: AUTONOMOUS hygiene.

### A-L2 (LOW, AUTONOMOUS) — Reference discipline breaks after §3

The numbered References section lists [1]–[4] (DID, VC-DM, JSON-LD, Schema.org), all consumed by §§1–3. But the later sections cite normative standards **inline and unlisted**: RFC 8785 (§5.1), RFC 7049 (§5.2 — see B-M1), and HKDF/RFC 5869 (§4). The reference apparatus is half-applied.

- **Routing**: AUTONOMOUS. Add the missing references (RFC 8785; RFC 8949 per B-M1; RFC 5869) and cite them by number for consistency.

---

## §B — Cross-Spec Findings

### B-H1 (HIGH, DESIGN-Q) — Two divergent normative pairwise-derivation algorithms with contradictory salt models

The same primitive — the pairwise pseudonymous identifier — is specified **twice, differently**, in two normative documents:

| Aspect | `data-formats.md` §4.1 | `web4-handshake.md` §4.1 |
|---|---|---|
| Salt | `salt = sha256(peer_identifier)` — **derived from the peer's stable id** | `peer_salt` — **128-bit random, exchanged in handshake** |
| `info` string | `b"web4-pairwise-id"` | `"W4IDp:v1"` |
| Output encoding | `base32_encode(key[:16])` (16 bytes, plain base32) | `MB32(...)` (multibase base32, no padding, full output) |
| Surface form | `w4id:pair:<…>` | bare `MB32` value (no prefix) |

These produce **different identifiers from the same inputs**, and — more seriously — embody **contradictory privacy models**. `data-formats.md` §4.2 step 3 derives the salt deterministically *from the peer identifier*; `web4-handshake.md` §4.2 **mandates the opposite**:

> *"`peer_salt` MUST be 128-bit random … MUST NOT be derived from stable identifiers."*

A deterministic salt (data-formats) is correlatable across sessions and cannot satisfy handshake §4.2's rotation requirement ("MUST be re-derived when either party rotates its master key" — re-derivation is meaningless if the salt is a pure function of a stable id). The handshake's random-salt model is the security-defensible one; `data-formats.md` §4.2 step-3 appears to be the defect.

- **Routing**: DESIGN-Q — the canonical derivation algorithm must be chosen at operator level (bundles the W4IDp cluster: `carry-C28-design-Q` C-M3, C27-H1, C24-H1). This audit **does not pick the winner** (binding condition 1), but records the security analysis: handshake's random-salt model dominates data-formats' deterministic-salt model on correlation-resistance and rotation correctness.

### B-M1 (MEDIUM, AUTONOMOUS for the citation; the rest n/a) — CBOR determinism cites obsoleted RFC 7049

§5.2:

> *"messages MUST be encoded using the deterministic encoding rules specified in **RFC 7049**."*

RFC 7049 (CBOR, 2013) was **obsoleted by RFC 8949** (December 2020). Deterministic CBOR encoding is now normatively specified in **RFC 8949 §4.2 "Core Deterministic Encoding."** The four rules the section then lists (smallest integer encoding; maps sorted by key encoding; definite-length items; no duplicate keys) **match RFC 8949's Core Deterministic Encoding** — so the rules are correct, but the citation in a `MUST` clause points to a superseded standard in the canonicalization SSOT on which all CBOR-path signatures depend.

- **Routing**: AUTONOMOUS (cleanest finding — replace `RFC 7049` → `RFC 8949` and cite §4.2; add to References per A-L2). Per binding condition 2, this is a genuine normative correctness finding, **not** mere staleness. Rated MEDIUM (behavioral rules are correct; defect is the normative citation, not the encoding semantics).

### B-M2 (MEDIUM, DESIGN-Q) — W4ID syntax: three-way drift across the corpus

| Source | Form |
|---|---|
| `data-formats.md` §1.1 (SSOT) | `did:web4:<method-name>:<method-specific-id>` |
| `core-protocol.md:105` | `w4id:<method-name>:<method-specific-id>` (different scheme token) |
| `web4-lct.md:57` | `did:web4:<method-specific-id>` (**drops the method-name segment**) |

The `did:web4:` vs `w4id:` prefix split is the openly-deferred repo-wide scheme decision (`core-protocol.md:99`). Separately, `web4-lct.md:57` omits the method-name segment entirely, producing a form that is invalid under *both* candidate syntaxes.

- **Routing**: DESIGN-Q for the prefix (bundles A-H1 / the identifier-scheme carry); **CROSS-TRACK** for the `web4-lct.md` missing-method-segment drift (fix lands in `web4-lct.md`, not edited this turn).

### B-M3 (MEDIUM, DESIGN-Q) — W4IDp surface-form fragmentation (4+ forms)

The pairwise identifier appears in at least four incompatible surface forms across the corpus:

| Form | Source |
|---|---|
| `w4id:pair:<base32>` | `data-formats.md` §4.1 |
| bare `MB32(...)` (no prefix) | `web4-handshake.md` §4.1 |
| `w4idp-XXXX` (hyphen) | `errors.md` (instance URIs), `web4-metering.md` |
| `w4idp:abcd…` (colon) | `web4-witnessing.md` §1 |

No single canonical wire form exists. This is the direct continuation of the C28 `C-M3` carry (W4IDp form) bundling C27-H1 + C24-H1.

- **Routing**: DESIGN-Q. Once the scheme decision (A-H1/B-M2) lands, the canonical W4IDp surface form should be fixed **in `data-formats.md`** (the natural home) and the consumer specs aligned (cross-track fan-out).

### B-L1 (LOW, CROSS-TRACK) — `web4://` URI scheme undefined in the format SSOT

`errors.md` uses `web4://w4idp-ABCD/…` instance URIs (lines 16, 98, 111, 124). The `web4://` URI scheme is not defined in `data-formats.md` (the natural home for a Web4 URI-scheme definition) nor, as far as this audit found, anywhere normative.

- **Routing**: CROSS-TRACK (surfaces in `errors.md`; the eventual scheme definition belongs in `data-formats.md`). Recorded, not actioned this turn.

---

## INFO (forward-awareness, no action)

- **I1** — `data-formats.md` carries **no Version / Status / Last-Updated banner**, unlike sibling core-spec docs (e.g., `presence-protocol.md` has `Version` + `Status`). Per BC#13, banner absence alone is INFO. A remediation turn touching the file for the autonomous findings above could add a banner opportunistically.
- **I2** — §2.1 uses `issuanceDate`, consistent with the cited VC Data Model **v1.1** [2]. VC-DM **v2.0** renames this to `validFrom`/`validUntil`; recorded for future migration awareness. No action while [2] pins v1.1.

---

## Classification Summary

| ID | Sev | Finding | Routing |
|----|-----|---------|---------|
| A-H1 | HIGH | SSOT self-contradiction: §1 `did:web4:` vs §4 `w4id:pair:` | DESIGN-Q (+autonomous clarification sub-option) |
| A-M1 | MED | Method set {key,web} omits `device` | AUTONOMOUS (+cross-track verify) |
| A-M2 | MED | §5.1 JCS code does not implement RFC 8785 | AUTONOMOUS |
| A-L1 | LOW | Two-era authoring residue (`_` line 65, spacing) | AUTONOMOUS |
| A-L2 | LOW | References omit RFC 8785 / 8949 / 5869 | AUTONOMOUS |
| B-H1 | HIGH | Two divergent pairwise-derivation algorithms; contradictory salt models | DESIGN-Q |
| B-M1 | MED | CBOR determinism cites obsoleted RFC 7049 (→ RFC 8949 §4.2) | AUTONOMOUS |
| B-M2 | MED | W4ID 3-way syntax drift (prefix + lct missing segment) | DESIGN-Q (prefix) / CROSS-TRACK (lct) |
| B-M3 | MED | W4IDp 4-form surface fragmentation | DESIGN-Q |
| B-L1 | LOW | `web4://` URI scheme undefined in format SSOT | CROSS-TRACK |
| I1 | INFO | No Version/Status banner | — |
| I2 | INFO | `issuanceDate` vs VC-DM 2.0 `validFrom` | — |

**Totals**: 2 HIGH, 5 MEDIUM, 2 LOW (+1 LOW cross-track) = 10 actionable + 2 INFO.

**Split**:
- **AUTONOMOUS (5)** — next remediation turn, no design decision needed: **B-M1** (RFC 7049→8949, cleanest), **A-M1** (register `device` / mark list extensible), **A-M2** (relabel JCS snippet non-normative), **A-L1** (hygiene), **A-L2** (references). All land inside `data-formats.md`.
- **DESIGN-Q (4)** — operator decision; routed to the existing identifier-scheme carry cluster, **not resolved here**: **A-H1** (scheme self-contradiction), **B-H1** (canonical pairwise algorithm + salt model), **B-M2 prefix** (scheme token), **B-M3** (canonical W4IDp surface form). All bundle into `carry-C28-design-Q` C-M3 ⊇ C27-H1 ⊇ C24-H1.
- **CROSS-TRACK (3)** — fix/verify in other specs, not edited this turn: **B-M2** `web4-lct.md` missing method segment; **B-L1** `errors.md` `web4://` scheme; **A-M1** corpus-wide method-name enumeration.

---

## Key Adjudication

`data-formats.md` **is** the right canonical home — `core-protocol.md:99` already designates it, and every other consumer reasonably defers there. The problem is not the choice of home but that the home is **itself unresolved and self-inconsistent**: the SSOT for identifiers cannot state, without contradiction, what a Web4 identifier *looks like*. The autonomous findings (RFC currency, method registry, JCS sketch, references) can be fixed immediately. But the load-bearing contradictions (A-H1, B-H1, B-M2, B-M3) all reduce to **one operator decision** — the long-deferred repo-wide identifier-scheme/W4IDp-form decision — which this audit reconfirms is now blocking internal consistency of the designated SSOT, not just cross-spec cosmetics. That escalation (from "cross-spec drift" to "the SSOT contradicts itself") is the most important signal of this audit.

---

## Next-Turn Carry

- **Remediation turn (next, by alternation)**: apply the 5 AUTONOMOUS findings to `data-formats.md` (B-M1 RFC 7049→8949; A-M1 method registry; A-M2 JCS relabel; A-L1 hygiene; A-L2 references). Run BC#5 corpus sweep for any inserted terms. Opportunistically add a Version/Status banner (I1) since the file is being touched.
- **`carry-C29-design-Q`** (fold into `carry-C28-design-Q`): the identifier-scheme decision now blocks **internal** consistency of the SSOT (A-H1), the canonical pairwise algorithm + salt model (B-H1, with handshake's random-salt model recommended), the W4ID prefix token (B-M2), and the canonical W4IDp surface form (B-M3).
- **`carry-C29-cross-track`**: `web4-lct.md:57` W4ID missing method segment (B-M2); `errors.md` `web4://` scheme definition (B-L1); corpus-wide method-name enumeration for A-M1.
