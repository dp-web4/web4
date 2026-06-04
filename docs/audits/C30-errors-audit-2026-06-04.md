# C30 — `errors.md` First-Pass Internal-Consistency + Cross-Spec Audit

**Audit ID**: C30
**Target**: `web4-standard/core-spec/errors.md` (144 lines) — the Web4 Error Taxonomy (RFC 9457 Problem Details)
**Date**: 2026-06-04
**Auditor**: autonomous web4 session (legion, slot `000000`), v2 protocol
**Type**: First-pass internal-consistency audit + cross-spec consistency audit
**Prior coverage**: none — `errors.md` is genuinely un-audited. C29 (`data-formats.md`) flagged two items *about* `errors.md` from the data-formats side (its B-L1 `web4://` scheme; B-M3 `w4idp-XXXX` form); this audit examines `errors.md` itself and **adjudicates those inherited carries from the errors.md side**.
**Method note**: executed as a multi-agent audit — five parallel dimension-finders (internal consistency / cross-spec error-systems / identifier-scheme / RFC-9457 conformance / primitive-clustered blindspot pass) each followed by an adversarial verifier instructed to *refute*. 27 candidate findings → **23 survived verification, 4 refuted** (the refuted set is summarized at the end for anti-padding transparency). Every surviving finding below was then re-verified by hand against the live files.

---

## Scope & Methodology

`errors.md` declares itself (line 3) as the document that *"defines a standardized error taxonomy for the Web4 protocol."* It is the RFC-9457-Problem-Details contract every consumer renders and parses. The audit proceeds in the standard three passes:

1. **Internal-consistency pass** (§A) — does the document agree with itself (examples vs. the normative §2 taxonomy; field requirements vs. RFC 9457; the §5 status mapping)?
2. **Cross-spec pass** (§B) — does it agree with the specs and registries that surround it (`registries/error-codes.md`, `web4-metering.md`, `web4-society-authority-law.md`, `acp-framework.md`, `mcp-protocol.md`, `core-protocol.md`, `data-formats.md`, the SDK `errors.py`)?
3. **Primitive-clustered pass** (`auditor-blindspot-pattern`) — re-read through the *error-identity* and *taxonomy-completeness* lenses, hunting cross-section / cross-spec contradictions a section-by-section read misses.

Severity: **HIGH** = correctness/normative contradiction; **MEDIUM** = consumer-affecting inconsistency or wrong normative citation; **LOW** = hygiene/reference discipline; **INFO** = forward-awareness, no action.

Routing: **AUTONOMOUS** (a future remediation turn can fix it inside `errors.md` without a design decision), **DESIGN-Q** (requires an operator-level decision; recorded, *not resolved here* per binding condition 1), **CROSS-TRACK** (fix/verify lands in another file — not edited this turn).

---

## §A — Internal-Consistency Findings

### A-M1 (MEDIUM, AUTONOMOUS) — The document's own examples contradict its normative taxonomy

Two of the four worked examples title an error code **differently from the §2 normative table for that same code**:

| Where | Code | Example `title` | §2 taxonomy `title` |
|---|---|---|---|
| §1 example (line 13) | `W4_ERR_BINDING_EXISTS` | **"Binding Failed"** | §2.1 line 37 → **"Binding Already Exists"** |
| §3.1 example (line 94) | `W4_ERR_AUTHZ_DENIED` | **"Unauthorized"** | §2.4 line 64 → **"Authorization Denied"** |

`title` is a REQUIRED field (§1 line 23). The SSOT *within* the document is the §2 taxonomy; the examples must render it verbatim. An implementer who copies the §1 example ships the wrong title. The `BINDING_EXISTS` case is the worse of the two — "Binding Failed" is a *different* semantic from "Binding Already Exists" (generic failure vs. a 409 conflict), not a synonym.

Relatedly, the §3.1 example pairs `W4_ERR_AUTHZ_DENIED` (401) with `detail` *"Credential lacks scope write:lct"* (line 97) — but §2.4 defines a dedicated **`W4_ERR_AUTHZ_SCOPE`** (403, "Insufficient Scope", line 66) for exactly that condition. The example illustrates a scope failure using the wrong code/status.

- **Routing**: AUTONOMOUS. Align the example `title` values to the §2 table, and switch the §3.1 example to `W4_ERR_AUTHZ_SCOPE`/403 (or change its `detail` so it is genuinely a "denied", not a "scope", case). No design decision required — §2 is plainly canonical within the doc.
- *Severity note (binding condition 2 — honest split)*: two independent finders rated these HIGH; the adversarial pass moderated to MEDIUM because `title` is human-readable display text and machine dispatch keys on `code`+`status` (both correct in the examples). Recorded as MEDIUM (a REQUIRED-field self-contradiction with bounded functional impact), not HIGH.

### A-M2 (MEDIUM, AUTONOMOUS) — Field-requirement set diverges from RFC 9457, and the `code` extension is unlabelled

§1 marks **`type`, `status`, `title`, `code` all REQUIRED** (lines 22–25). RFC 9457 §3.1 makes **`type` OPTIONAL** (default `"about:blank"`), and `title`/`status` are likewise not mandatory members. `code` is **not an RFC 9457 standard member at all** — it is a Web4 **extension member** (RFC 9457 §3.2), but the spec only hints at this in a parenthetical ("Web4-specific", line 25) and never cites §3.2 or states that Web4 *extends* the standard field set.

The `type`-REQUIRED claim is internally self-undermining: **every** example (lines 11, 93, 106, 119) sets `type` to the default `"about:blank"`, and the **SDK itself treats `type` as optional** — `web4/errors.py` parses it with `.get("type", "about:blank")`. So the spec mandates as REQUIRED a field its own reference implementation defaults.

- **Routing**: AUTONOMOUS. Restate `type` as OPTIONAL (default `about:blank`) per RFC 9457 — or, if Web4 deliberately mandates it, say so and show a non-`about:blank` example; add one sentence that `code` is a Web4 extension member (RFC 9457 §3.2) and that Web4 additionally mandates `status`/`title`. A clean, in-file alignment fix.

### A-M3 (MEDIUM, AUTONOMOUS) — `status` is defined as an HTTP code, but Web4 errors travel over non-HTTP transports

§1 line 24 defines `status` as *"HTTP status code (100-599)"* and §5 is an HTTP-status-code mapping. But Web4 errors are serialized over **non-HTTP** transports: `web4-handshake.md` §10 carries Problem Details in **CBOR over TLS/QUIC**, and `core-protocol.md` §5.1 lists BLE GATT and CAN Bus as MUST-support transports. An HTTP status code has no native meaning on a CAN bus frame. The spec never states whether `status` is HTTP-literal or a transport-agnostic HTTP-*analogue*.

- **Routing**: AUTONOMOUS. Add a clarifying note: `status` is modelled on HTTP codes for familiarity but is transport-agnostic; over HTTP it SHOULD equal the response code, over non-HTTP transports it carries the analogous semantic class per §2/§5.

### A-L1 (LOW, AUTONOMOUS) — Instance path segments are ad-hoc, unanchored

Every `instance` URI uses path segments — `/bindings/12345` (line 16), `/messages/123` (98), `/attestations/456` (111), `/api/v1/query` (124) — that are defined **nowhere**. `core-protocol.md` §6.2 gives URI *resolution* but no registry of standard paths. RFC 9457 permits application-specific `instance` URIs, so this is not a defect — but the SSOT for errors should say these paths are illustrative (or document them as conventions).

- **Routing**: AUTONOMOUS (a one-line "paths are illustrative" note). The natural home for any *normative* path conventions is the `web4://` scheme definition (see B-M2), so a convention registry would be CROSS-TRACK.

---

## §B — Cross-Spec Findings

### B-H1 (HIGH, DESIGN-Q) — Two parallel error-code systems; the numeric registry is orphaned

Web4 carries **two disjoint, non-interoperable error-code systems** with no mapping between them:

| | `core-spec/errors.md` | `registries/error-codes.md` |
|---|---|---|
| Code form | string `W4_ERR_BINDING_EXISTS` | numeric `0x0008` |
| Model | RFC 9457 Problem Details, HTTP-status-keyed | wire-level, class-ranged (0x0000–0x00FF protocol, …) |
| Naming | hierarchical `W4_ERR_<CAT>_<COND>` | flat `BINDING_FAILED` |
| Reference | — | `"[Web4 Standard Section X.Y]"` (**unfilled placeholder**, line 10); all rows cite generic `[Web4]` |
| Coverage | 24 codes across 6 live categories | 11 codes (~4 % of the declared class space; classes 0x0100–0x03FF entirely empty) |
| Usage | SDK `errors.py` + test vectors + **all** consumer specs use it | **zero** references anywhere in the corpus or SDK |

The same concepts appear in **both with different names and no documented relationship**: `0x0008 BINDING_FAILED` ↔ `W4_ERR_BINDING_EXISTS`; `0x0009 PAIRING_FAILED` ↔ `W4_ERR_PAIRING_*`; `0x0004 INVALID_WITNESS` ↔ `W4_ERR_WITNESS_INVALID`. And several numeric codes (`0x0003 INSUFFICIENT_TRUST`, `0x0006 METERING_FAILED`, `0x0007 MRH_VIOLATION`, `0x000A BROADCAST_FAILED`) have **no** `errors.md` equivalent at all.

The evidence overwhelmingly indicates the **string `W4_ERR_*` system is the live, canonical one** (it is what every spec, the SDK, and the conformance vectors use) and that `registries/error-codes.md` is an **orphaned early-draft registry** (unfilled reference, zero adoption). But formally retiring or re-homing a registry is an operator-level decision.

- **Routing**: DESIGN-Q — canonicity between the two systems must be decided at operator level. This audit **does not unilaterally pick a winner** (binding condition 2) but records the analysis: the `W4_ERR_*` system dominates on adoption, completeness, and active maintenance.
- **Autonomous sub-option (non-binding on the decision)**: a remediation turn could, without deciding canonicity, add one cross-reference sentence — `errors.md` noting the numeric registry's existence/scope (or its superseded status), and/or filling the registry's `Section X.Y` placeholder with a pointer to `errors.md`. Flagged for the remediator's judgment.

### B-M1 (MEDIUM, DESIGN-Q + autonomous clarification) — `errors.md` claims to be "the" taxonomy but is only the core subset; subsystem codes drift

§1 line 3 states `errors.md` *"defines a standardized error taxonomy for the Web4 protocol"* — unqualified. In fact **23+ `W4_ERR_*` codes live in subsystem specs and are neither enumerated nor cross-referenced here**:

| Subsystem | Spec | New codes | Count |
|---|---|---|---|
| Metering | `web4-metering.md` §6 | `GRANT_EXPIRED`, `RATE_LIMIT`, `SCOPE_DENIED`, `BAD_SEQUENCE`, `WITNESS_REQUIRED`, `FORMAT` | 6 |
| Society/Authority | `web4-society-authority-law.md` §9 | `LEDGER_WRITE`, `AUDIT_EVIDENCE`, `LAW_CONFLICT` (+ **reuses** core codes — the good model) | 3 |
| ACP | `acp-framework.md` §10 | `W4_ERR_ACP_*` (8 codes) | 8 |
| Cross-society | `mcp-protocol.md` §7.6 (in SDK `errors.py`) | `CROSS_SOCIETY_*`, `R7_REPUTATION_INVALID`, `PROPAGATION_SCOPE_UNSUPPORTED` | 6 |

Worse than omission, there is **parallel-naming drift** for concepts `errors.md` *already* covers:

- metering `W4_ERR_RATE_LIMIT` vs. errors.md `W4_ERR_AUTHZ_RATE` (both 429 rate-limiting)
- metering `W4_ERR_SCOPE_DENIED` vs. errors.md `W4_ERR_AUTHZ_SCOPE`
- metering `W4_ERR_GRANT_EXPIRED` vs. errors.md `W4_ERR_AUTHZ_EXPIRED`
- metering `W4_ERR_BAD_SEQUENCE` vs. errors.md `W4_ERR_PROTO_SEQUENCE`
- metering `W4_ERR_WITNESS_REQUIRED` — **absent** from errors.md §2.3 (which has `WITNESS_UNAVAIL/REJECTED/INVALID/QUORUM`)
- SAL `W4_ERR_LEDGER_WRITE` vs. ACP `W4_ERR_ACP_LEDGER_WRITE` (two ledger-write codes)

Note that SAL §9 demonstrates the **intended healthy pattern** — it *reuses* core errors.md codes (`BINDING_INVALID`, `PROTO_DOWNGRADE`, `WITNESS_QUORUM`, `AUTHZ_SCOPE`, `BINDING_REVOKED`) and only adds three domain-specific codes. Metering, by contrast, *re-invents* parallel names.

- **Routing**: a coupled split —
  - **AUTONOMOUS**: rescope §1 line 3 — `errors.md` defines the **core protocol** error taxonomy; subsystem specs (SAL, ACP, metering, MCP cross-society) extend it. Converts a false claim of comprehensiveness into an accurate one.
  - **DESIGN-Q**: the architectural choice — *one centralized error SSOT* (errors.md enumerates everything via §2.7+ sections) vs. *core + distributed extension* (the de-facto pattern). Operator-level.
  - **CROSS-TRACK**: the metering parallel-naming drift should be reconciled in `web4-metering.md` (prefer reusing the existing `W4_ERR_AUTHZ_*`/`W4_ERR_PROTO_*` codes), and `W4_ERR_WITNESS_REQUIRED` reconciled with errors.md §2.3 — not edited this turn.

### B-M2 (LOW, CROSS-TRACK) — `web4://` scheme home — **and a correction to C29 B-L1**

C29's B-L1 stated that the `web4://` URI scheme used in every `errors.md` `instance` field is *"not defined in `data-formats.md` … nor, as far as this audit found, anywhere normative."* **The second half is factually incorrect, and C30 corrects the record:**

`web4://` **is** normatively defined —
- `core-protocol.md` **§6 "URI Scheme"** (lines 175–194): §6.1 syntax `web4://<w4id>/<path-abempty>[?query][#fragment]`, §6.2 resolution;
- `architecture/grammar_and_notation.md` **§4.1 "`web4://` Scheme"** (full ABNF: `web4-URI = "web4://" w4-authority path-abempty …`);
- `submission/web4-rfc.md` §4.

So `errors.md`'s `instance` URIs are **not** referencing an undefined scheme. The genuine residual issue is narrower: the scheme is **absent from `data-formats.md`**, which `core-protocol.md:99` designates as the SSOT for *"Web4 data and credential formats … the single source of truth."* A reader consulting the format SSOT for the URI scheme will not find it; it lives in the protocol and grammar documents instead.

- **Routing**: CROSS-TRACK. The fix (if any) is an SSOT-placement decision landing in `data-formats.md` / `core-protocol.md`, not in `errors.md`. **Severity reduced from C29's framing**: the scheme is defined and usable, so this is a hygiene/placement concern (LOW), not a missing-primitive defect.
- **Adjudication of the C29 carry**: `carry-C29-cross-track`'s "`errors.md web4://` scheme definition" item should be **rewritten** — not "define the undefined scheme" but "decide whether the *already-defined* scheme should be mirrored/cross-referenced from the data-formats SSOT." (This is exactly the kind of overclaim a first-pass audit makes when it cannot find a cross-doc definition; a wider cross-spec sweep located it. Logged as a continuation of the `auditor-blindspot-pattern` evidence base.)

### B-M3 (MEDIUM, DESIGN-Q — inherited from C29 B-M3) — W4IDp surface-form fragmentation

`errors.md` renders the pairwise identifier in the **`w4idp-ABCD` hyphen form** in all four `instance` URIs (lines 16, 98, 111, 124). This is one of the **four+ incompatible W4IDp surface forms** C29 B-M3 catalogued across the corpus (`w4id:pair:` in data-formats §4.1; bare `MB32` in web4-handshake §4.1; `w4idp-` hyphen in errors.md + web4-metering; `w4idp:` colon in web4-witnessing §1). `errors.md` is internally consistent (one form throughout) but uses a form the SSOT has not blessed.

- **Routing**: DESIGN-Q, **credited to C29 B-M3** — bundles into the repo-wide identifier-scheme decision (`carry-C28/C29-design-Q`). No novel action; once the canonical W4IDp form is chosen, `errors.md` examples align (CROSS-TRACK fan-out at that time).

---

## INFO (forward-awareness, no action)

- **I1** — `errors.md` carries **no Version / Status / Last-Updated banner**, unlike several sibling core-spec docs. Per BC#13, banner absence alone is INFO. A remediation turn touching the file could add one opportunistically.
- **I2** — All `errors.md` examples set `type` to `"about:blank"` (error semantics carried in the `code` extension, not the `type` URI). This is RFC-9457-valid and a reasonable design, **but** `QUICK_REFERENCE.md` (line ~193) shows a *custom* type URI (`"type": "https://web4.io/errors/invalid-lct"`) under its "Error Handling (RFC 9457)" section — a divergent practice. If `errors.md`'s `about:blank` convention is canonical, `QUICK_REFERENCE.md` should align (CROSS-TRACK, recorded only).
- **I3** — Content-type over media-negotiated transports is under-specified: `errors.md` §4 mandates `application/problem+json`/`+cbor`, while `web4-handshake.md` §5.1 negotiates `application/web4+json`/`+cbor` for protocol messages. Which content-type labels an error inside a negotiated session is not stated. Minor clarity gap.

---

## Classification Summary

| ID | Sev | Finding | Routing |
|----|-----|---------|---------|
| A-M1 | MED | Example titles contradict the normative §2 taxonomy (`BINDING_EXISTS`, `AUTHZ_DENIED`); §3.1 uses wrong code for a scope error | AUTONOMOUS |
| A-M2 | MED | `type`/`title`/`status` marked REQUIRED vs RFC 9457 optionality; `code` extension unlabelled; SDK defaults `type` | AUTONOMOUS |
| A-M3 | MED | `status` defined as HTTP code but errors travel over non-HTTP transports | AUTONOMOUS |
| A-L1 | LOW | `instance` path segments ad-hoc / unanchored | AUTONOMOUS |
| B-H1 | HIGH | Two parallel error-code systems; numeric `registries/error-codes.md` orphaned (0 refs, unfilled placeholder) | DESIGN-Q (+autonomous cross-ref sub-option) |
| B-M1 | MED | `errors.md` claims to be "the" taxonomy but is core-only; 23+ subsystem codes uncatalogued + metering parallel-naming drift | AUTONOMOUS (rescope §1) / DESIGN-Q (central vs distributed) / CROSS-TRACK (metering) |
| B-M2 | LOW | `web4://` scheme home — defined in core-protocol §6 + grammar §4.1, absent from data-formats SSOT; **corrects C29 B-L1** | CROSS-TRACK |
| B-M3 | MED | W4IDp `w4idp-` hyphen form (inherited C29 B-M3) | DESIGN-Q |
| I1 | INFO | No Version/Status banner | — |
| I2 | INFO | `about:blank` convention vs QUICK_REFERENCE custom type URI | — |
| I3 | INFO | Content-type over negotiated transports under-specified | — |

**Totals**: 1 HIGH, 5 MEDIUM, 2 LOW = **8 actionable + 3 INFO**.

**Split**:
- **AUTONOMOUS (5)** — next remediation turn, inside `errors.md`, no design decision: **A-M1** (align example titles + fix §3.1 code), **A-M2** (RFC 9457 field-requirement relabel + `code`-as-extension note), **A-M3** (status transport-agnostic note), **A-L1** (paths-illustrative note), **B-M1 §1 rescope** (taxonomy is "core protocol" errors).
- **DESIGN-Q (3)** — operator decision, recorded not resolved: **B-H1** (numeric registry canonicity; string system recommended on the evidence), **B-M1 architecture** (centralized vs distributed error ownership), **B-M3** (canonical W4IDp form — inherited C29).
- **CROSS-TRACK (3)** — fix/verify in other files, not edited this turn: **B-M2** (`web4://` SSOT mirroring in `data-formats.md` + the C29 B-L1 record correction), **B-M1 metering** (reconcile parallel `W4_ERR_*` names in `web4-metering.md`), **I2** (`QUICK_REFERENCE.md` type-URI alignment).

---

## Key Adjudication

Two signals dominate this audit:

1. **The error layer has two parallel taxonomies, and the wire-level numeric one is dead on arrival (B-H1).** Unlike C29's identifier cluster — where the *contents* were contested — here the contest is *which system exists at all*. The string `W4_ERR_*` taxonomy is fully alive (SDK, vectors, every consumer); the numeric `0x*` registry has zero adopters, an unfilled reference placeholder, and ~4 % population. This is cheaper to resolve than the identifier cluster: the evidence already names the winner; what's missing is an operator decision to **retire or re-home** the orphan and a one-line cross-reference.

2. **`errors.md` advertises completeness it does not have (B-M1).** It calls itself *the* Web4 error taxonomy while four subsystems define ~23 more codes elsewhere — and metering re-invents parallel names for codes `errors.md` already owns. SAL shows the right pattern (reuse core + extend); metering shows the drift. The autonomous half (rescope §1 to "core protocol errors") is trivial and high-value; the architectural half (centralize vs distribute) is the real design question.

A third, methodological result: **C30 corrected a factual error in the merged C29 audit (B-L1).** A single-file first-pass audit could not locate the `web4://` definition and concluded it was undefined; a five-dimension cross-spec sweep found it in `core-protocol.md §6` and the grammar. This is the `auditor-blindspot-pattern` operating across audits, not just within one — and the reason the C-series runs RE-audits and wide cross-spec passes rather than trusting any single first-pass conclusion.

---

## Refuted Candidates (anti-padding transparency)

Four candidate findings were dropped by the adversarial pass and are **not** counted above:

- *"error-codes.md has an unresolved reference placeholder"* — **file conflation**: the placeholder is in `registries/error-codes.md`, not `errors.md`; folded into B-H1 instead of double-counted.
- *"BINDING_FAILED (0x0008) scope-drift vs the W4_ERR_BINDING_* quartet"* — real literal mismatch but the numeric registry is non-normative/orphaned, so this is a facet of B-H1, not an independent consumer-affecting defect.
- *"RFC 9457 instance URIs are syntactically correct"* — a *positive* compliance observation, not a finding.
- *"web4:// scheme used but undefined"* — **refuted on the facts**: the scheme is defined (see B-M2); the verifier correctly caught that the inherited C29 claim was wrong.

---

## Next-Turn Carry

- **Remediation turn (next, by alternation)**: apply the 5 AUTONOMOUS findings to `errors.md` (A-M1 example titles + §3.1 code; A-M2 RFC 9457 field requirements + `code` extension note; A-M3 status transport note; A-L1 paths note; B-M1 §1 rescope to "core protocol errors"). Run BC#5 corpus sweep for any inserted term. Opportunistically add a Version/Status banner (I1).
- **`carry-C30-design-Q`**: (a) **B-H1** numeric-vs-string error-system canonicity (string system recommended; decision = retire/re-home `registries/error-codes.md`); (b) **B-M1** centralized-vs-distributed error-code ownership; (c) **B-M3** canonical W4IDp form — **folds into `carry-C28/C29-design-Q`** (identifier cluster).
- **`carry-C30-cross-track`**: (a) **B-M2** mirror/cross-reference the *already-defined* `web4://` scheme from the `data-formats.md` SSOT — **and rewrite the C29 `carry-C29-cross-track` `web4://` item** (the scheme is defined, not undefined; the task is SSOT placement); (b) **B-M1 metering** reconcile parallel `W4_ERR_RATE_LIMIT`/`SCOPE_DENIED`/`GRANT_EXPIRED`/`BAD_SEQUENCE`/`WITNESS_REQUIRED` names in `web4-metering.md` against existing errors.md codes; (c) **I2** align `QUICK_REFERENCE.md` error `type` URI with the `about:blank` convention.
- **Coverage note**: with C30, first-pass core-spec error/format/identifier coverage is broad. Remaining un-audited normative core-spec files: `r6-implementation-guide.md`, `r6-security-analysis.md`, `security-framework.md`.
