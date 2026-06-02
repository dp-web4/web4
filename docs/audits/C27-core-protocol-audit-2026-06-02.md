# C27 Audit: `core-protocol.md` Internal-Consistency + Cross-Spec FIRST-PASS Audit

**Date**: 2026-06-02
**Auditor**: Autonomous session (Legion, web4 track) — firing `120050`, LEAD voice
**Document**: `web4-standard/core-spec/core-protocol.md` (189 lines, last edited 2025-12-05; **never previously audited**)
**Methodology**: C-series **first-pass** audit (NOT a delta re-audit — this is the only core-spec document the C-series had not yet covered; C16–C26 covered the rest). Two passes: (§B) internal consistency (structure, numbering, intro-vs-body promises); (§C) cross-spec divergence against the authority anchors that describe the SAME primitives core-protocol.md restates. A third **primitive-clustered pass** (per the `auditor-blindspot-pattern`) groups by primitive — *W4ID*, *handshake*, *URI* — to catch divergences that severity-ordered reading misses.
**Authority anchors re-read this session** (passages re-read, not recalled, per the cross-doc-overcall hygiene rule):
- `web4-standard/core-spec/data-formats.md` §1 (W4ID), §2 (VC), §3 (JSON-LD), §4 (pairwise), §5 (canonicalization)
- `web4-standard/architecture/grammar_and_notation.md` §4.1 (`web4://` ABNF), §4.2 (`did:web4` RECOMMENDED)
- `web4-standard/protocols/web4-handshake.md` §3 (suites), §4 (W4IDp), §5 (Hello messages)
- `web4-standard/implementation/sdk/web4/protocol.py` (handshake message fields L83–L116; `Web4URI` parser L411–L472)
- `web4-standard/test-vectors/protocol/core-protocol.json` (URI + handshake conformance vectors)

---

## Summary

| Severity | Count | IDs |
|----------|-------|-----|
| HIGH | 2 | H1, H2 |
| MEDIUM | 4 | M1, M2, M3, M4 |
| LOW | 3 | L1, L2, L3 |
| INFO | 2 | INFO1, INFO2 |
| **Total** | **9 actionable + 2 INFO** | |

**Split for the remediation turn**: **4 autonomous-actionable** (M1, M2, L1, L3) · **4 design-Q** (H1, H2, M3, M4) · **1 cross-track** (L2) · **2 INFO** (observational).

**Headline**: core-protocol.md is the oldest core-spec doc (Dec-5, pre-dates the entire SAL/society/MCP-as-inter-society-protocol build-out) and was written as a **broad sketch** that *restates* three primitives — W4ID, the HPKE handshake, and the `web4://` URI — that each have a **dedicated, more-recent, normative home** (data-formats.md, protocols/web4-handshake.md, grammar_and_notation.md). The findings are almost entirely **restatement drift**: where core-protocol.md re-specifies a shared primitive, its representation has fallen out of sync with the dedicated spec. Notably, on **W4ID** and **URI authority form**, core-protocol.md is the *corroborated* form (the conformance test vectors AND the SDK use core-protocol's `w4id:key:...` shape), while data-formats.md / grammar dissent with `did:web4:` — so the divergence is a genuine repo-wide canonical-shape **design-Q**, NOT a unilateral core-protocol error. The internal numbering defects (M2) and the dedicated-doc deference cross-references (M1) are clean autonomous wins.

---

## §B. Internal-Consistency Findings

### M2 — Broken section numbering: duplicate `## 2`, orphan `### 1.3`, missing `1.1`/`1.2`

**Lines**: `## 1.` (L8), `## 2. Handshake` (L18), `### 1.3. Pairing Methods` (L53), `## 2. Messaging` (L64).

**Issue**: The top-level numbering is structurally broken:
1. **Two `## 2` headings** — `## 2. Handshake Protocol (HPKE-based)` (L18) AND `## 2. Messaging Protocol` (L64). Every downstream renderer/TOC will collide these.
2. **Orphan `### 1.3. Pairing Methods`** (L53) is nested *inside* `## 2. Handshake` but numbered as a child of section 1, and there is **no `### 1.1` or `### 1.2`** anywhere — 1.3 appears with no 1.1/1.2 siblings.
3. The cascade means the real document structure is: Crypto Suites (1) → Handshake (2) → Pairing (mis-numbered 1.3) → Messaging (2 again) → Data Formats (3) → Transport (4) → URI (5).

**Recommended fix (AUTONOMOUS-ACTIONABLE)**: Renumber to a clean monotonic tree, e.g.: §1 Cryptographic Suites; §2 Handshake Protocol; §3 Pairing Methods (promote the orphan to its own top-level section, or make it §2.1 under Handshake); §4 Messaging Protocol (+ children §4.1/§4.2/§4.3); §5 Data and Credential Formats; §6 Transport and Discovery; §7 URI Scheme. Pure structural hygiene — no semantic content changes, no cross-spec dependency. *(Anchor for severity: this is the same defect class as C26-H2 / C18-H1 duplicate-heading findings, which were remediated autonomously.)*

---

### L1 — Intro promises a "pairing process" the body never specifies

**Lines**: intro L3 ("...the handshake **and pairing process**, messaging protocol, data formats, and URI scheme"); body §1.3 (L53–L59) is the only pairing content — a 3-bullet list of *methods* (Direct/Mediated/QR), with NO pairing protocol.

**Issue**: The intro advertises a "pairing process" as a first-class deliverable of this spec, but the body delivers only a three-method enumeration — no message flow, no state machine, no field definitions. The handshake ASCII (§2) is labelled "handshake and pairing process" in the intro yet contains only handshake messages (ClientHello/ServerHello/ClientFinished/ServerFinished); "pairing" is never operationalized.

**Recommended fix (AUTONOMOUS-ACTIONABLE)**: Either (a) soften the intro to "...the handshake, pairing methods, messaging protocol..." (matches what the body actually delivers), or (b) add a cross-reference to wherever pairing mechanics are normatively specified (entity-types.md and presence-protocol.md cover binding/pairing/witnessing). Lowest-risk autonomous fix is (a) + a one-line "Pairing mechanics beyond method selection are specified in [pairing/binding spec]" pointer. No cross-spec edit required.

---

### L3 — No status/version/Last-Updated header (every sibling core-spec carries one)

**Lines**: L1–L4 (title + intro, no banner).

**Issue**: core-protocol.md has no `Status:` / `Last-Updated:` / version banner. Its sibling normative docs all do — e.g. `protocols/web4-handshake.md` L2 `Status: Draft • Last-Updated: 2025-09-11T...`; LCT-linked-context-token.md, inter-society-protocol.md, and entity-types.md all carry version/last-edited headers used by the C-series itself for drift-dating. The absence makes it impossible to date-anchor core-protocol.md's content against the specs that have moved past it.

**Recommended fix (AUTONOMOUS-ACTIONABLE)**: Add a minimal `Status: Draft • Last-Updated: 2026-06-02` (or the true last-edit date) banner matching the sibling format. Per BC#13 (date-staleness alone is INFO unless coupled with a normative date-dependency), this is LOW not MEDIUM — but it is a clean autonomous addition and it is *coupled* here with the drift-dating need that this very audit surfaced. Hygiene, no semantic change.

---

## §C. Cross-Spec Divergence Findings

### H1 — W4ID scheme is multi-way divergent across the repo; §3.1 is the *corroborated* form (DESIGN-Q)

**Lines**: core-protocol.md §3.1 (L95–L103); cross-spec: data-formats.md §1.1 (L14–L20), grammar_and_notation.md §4.2 (L50–L58), data-formats.md §4.1 pairwise (L87), protocols/web4-handshake.md §4.1 (L34–L38).

**Issue**: Four distinct W4ID surface forms coexist in the repo:

| Source | W4ID form | Authority weight |
|--------|-----------|------------------|
| **core-protocol.md §3.1** | `w4id:<method-name>:<method-specific-id>` (e.g. `w4id:key:abc123`) | corroborated by vectors + SDK |
| **test-vectors/protocol/core-protocol.json** | `w4id:key:abc123`, `w4id:web:example.com` | conformance authority |
| **SDK `protocol.py` Web4URI** | treats `w4id` as opaque authority; examples `w4id:key:ephemeral_001` | implementation |
| **data-formats.md §1.1** | `w4id = "did:web4:" method-name ":" method-specific-id` | dedicated data-formats doc |
| **grammar_and_notation.md §4.2 (RECOMMENDED)** | `did-url = "did:web4:" method-specific-id` (**no** method-name segment) | architecture grammar |
| **data-formats.md §4.1 / handshake.md** | pairwise `w4id:pair:<base32>` / `w4idp-<base32>` | privacy identifiers |

Three observations: (1) core-protocol.md §3.1 uses the `w4id:` prefix; the two dedicated definition homes (data-formats.md, grammar) both use `did:web4:`. (2) Even between the two `did:web4:` sources they disagree on whether a `method-name` segment exists (data-formats has it; grammar's RECOMMENDED ABNF does not). (3) Critically, the **conformance test vectors and the SDK use core-protocol's `w4id:` form** — so core-protocol.md is the *corroborated* representation and the dedicated docs are the dissenters. This is a 5-anchor canonical-convergence situation analogous to C20/C24's ID-format flagships.

**Why DESIGN-Q (NOT autonomous)**: The fix is not "edit core-protocol.md to match data-formats.md" — that would break the conformance vectors and the SDK. Resolving it requires a repo-wide decision on the canonical W4ID scheme (`w4id:` vs `did:web4:`, and whether `method-name` is part of the syntax), which then cascades to data-formats.md, grammar, vectors, and SDK. **Route to design-Q.** This finding couples with any existing ID-canonicalization carries (cf. C24-H1 LCT-ID 4-way divergence — the W4ID question is the *entity-identifier* sibling of that LCT-ID question; a single "canonical identifier scheme" resolution could settle both).

---

### H2 — §2 handshake sketch diverges from the normative MTI handshake and gives no deference cross-reference

**Lines**: core-protocol.md §2 (L18–L51); normative: protocols/web4-handshake.md §5.1–§5.2 (L77–L105); SDK protocol.py L83–L116.

**Issue**: core-protocol.md §2 presents a 4-message ASCII handshake (ClientHello / ServerHello / ClientFinished / ServerFinished) as if authoritative, but the **mandatory-to-implement (MTI) handshake** is normatively specified in `protocols/web4-handshake.md` ("This document specifies the **mandatory-to-implement (MTI) handshake** for Web4 endpoints", L6). The two diverge and core-protocol.md gives **no cross-reference** pointing to the normative spec:

| Field / aspect | core-protocol.md §2 | normative handshake.md §5 |
|----------------|---------------------|---------------------------|
| Client identifier field | `client_w4id_ephemeral` | `w4idp_hint` |
| Server identifier field | `server_w4id_ephemeral` | `w4idp` |
| Key exchange field | `client_public_key` / `server_public_key` | `kex_epk` (HPKE KEM ephemeral) |
| Nonce | `nonce[32]` (256-bit) | `nonce: <random 96-bit>` (see M3) |
| Hello extras | — | `ver`, `media`, `ts`, GREASE `ext` |

Note the SDK (`protocol.py` L88/L116) uses core-protocol.md's `client_w4id_ephemeral`/`server_w4id_ephemeral` field names — so the **SDK aligns with core-protocol.md's handshake naming, not with the normative handshake.md**. This is the same corroboration split as H1: the "core-spec + SDK + vectors" cluster vs the "dedicated normative doc" cluster.

**Split**: The *autonomous* part is small and safe — add a deference cross-reference in §2 ("The mandatory-to-implement handshake is normatively specified in `protocols/web4-handshake.md`; the sketch below is illustrative"). The *design-Q* part is the substantive reconciliation: which field names (`w4idp_hint`/`w4idp` vs `client_w4id_ephemeral`/`server_w4id_ephemeral`) and which message shape are canonical, given SDK ↔ normative-doc disagreement. **Route the cross-reference to autonomous-actionable-IF-bundled, but the field/shape reconciliation to design-Q.** Recommend treating H2 as design-Q overall to avoid a half-fix that implies the sketch is reconciled when it is not (cf. C24-H1 deferral discipline).

---

### M3 — Handshake nonce size contradicts the normative spec (`nonce[32]` vs 96-bit)

**Lines**: core-protocol.md §2 ClientHello/ServerHello `nonce[32]` (L30, L38); normative handshake.md §5.1/§5.2 `"nonce": "<random 96-bit>"` (L86, L101).

**Issue**: core-protocol.md specifies a **32-byte (256-bit)** nonce; the normative handshake.md specifies a **96-bit (12-byte)** nonce. (The test vector `core-protocol.json` uses `"nonce": "a1b2c3d4e5f6"` = 48-bit, illustrative/short — it asserts only `has_nonce: true`, so it does not adjudicate the size.) This is a direct numeric contradiction on a security parameter between two specs that both define the handshake.

**Why DESIGN-Q**: Resolving requires deciding the canonical nonce size and aligning whichever doc is wrong; it is a security-parameter decision, not hygiene. Couples tightly with H2 (same handshake reconciliation). **Route to design-Q, bundled with H2.**

---

### M4 — `web4://` URI authority form diverges from grammar's ABNF

**Lines**: core-protocol.md §5.1 (L173–L183); grammar_and_notation.md §4.1 (L40–L48); test-vectors `web4_uri_basic` etc.

**Issue**: core-protocol.md §5.1 defines `web4://<w4id>/...` where `<w4id>` is "The Web4 Identifier of the entity" — i.e. a raw W4ID, which per §3.1 contains colons (`w4id:key:abc123`). The grammar's normative ABNF (§4.1) instead defines `w4-authority = w4id-label / hostname` with `w4id-label = "w4-" base32nopad` — a colon-free `w4-<base32>` label (the base32 encoding of a *pairwise* W4ID), explicitly for privacy. The conformance vectors AND the SDK parser side with core-protocol.md (`web4://w4id:key:abc123/...`, colons in authority), so again core-protocol is corroborated and grammar dissents. Two unresolved questions: (a) is the URI authority a raw colon-bearing W4ID (core-protocol/vectors/SDK) or a `w4-base32` label (grammar)?; (b) does embedding a colon-bearing W4ID in the URI authority component conflict with RFC 3986 authority parsing (colons are reserved for the `host:port` delimiter)?

**Why DESIGN-Q**: This is the URI-form facet of the same W4ID canonical-scheme decision as H1; resolving it means picking the authority encoding repo-wide (and possibly justifying the RFC-3986 authority usage). **Route to design-Q, coupled with H1.**

---

### M1 — §3 "Data and Credential Formats" restates (and diverges from) the dedicated data-formats.md

**Lines**: core-protocol.md §3 (L91–L111: §3.1 W4ID, §3.2 VC, §3.3 JSON-LD); dedicated doc: data-formats.md (entire).

**Issue**: core-protocol.md §3 is an **abbreviated restatement** of `data-formats.md`, which is the dedicated normative home for exactly these three topics (W4ID §1, VCs §2, JSON-LD §3) and additionally specifies pairwise derivation (§4) and canonicalization (§5) that core-protocol.md omits entirely. The restatement is where the H1 W4ID divergence lives (§3.1 says `w4id:`, data-formats.md §1.1 says `did:web4:`). A spec that maintains two copies of the same primitive guarantees drift — which has already happened.

**Recommended fix (AUTONOMOUS-ACTIONABLE)**: Replace §3's restated bodies with a **deference cross-reference** — "Web4 data and credential formats (W4ID, Verifiable Credentials, JSON-LD, canonicalization) are normatively specified in `data-formats.md`." This is autonomous-safe *because it does not require deciding the W4ID canonical form* (H1) — it simply stops core-protocol.md from carrying a competing copy and points to the single source of truth. (If the team prefers to keep a brief summary in §3, the autonomous fix is to add the deference pointer and a "see data-formats.md for the normative definition" note without resolving H1's `w4id:`-vs-`did:web4:` form here.) Per the C26-M1 / graceful-partial-remediation pattern: apply the deference pointer autonomously, leave the form-resolution to H1's design-Q.

---

## §D. LOW / INFO

### L2 — Cryptographic suite table is a superset of handshake.md's and uses a divergent KEM name (CROSS-TRACK)

**Lines**: core-protocol.md §1 (L12–L16); handshake.md §3 (L20–L23).

core-protocol.md §1 lists **three** suites (adds `W4-IOT-1 (MAY)` with AES-CCM/CBOR) and a `KDF` column; handshake.md §3 lists **two** (`W4-BASE-1`, `W4-FIPS-1`). The KEM for FIPS is `P-256ECDH` in core-protocol vs `P-256EC` in handshake.md. Not a contradiction (superset + naming), but two suite registries that can drift. **CROSS-TRACK**: resolving means deciding the canonical suite registry home (likely a single normative table referenced by both); out of scope for a core-protocol.md-only remediation. Logged, not auto-fixed.

### INFO1 — Message types lack a cross-reference to the MCP / R6-R7 action model

core-protocol.md §2.2 (L75–L82, in the mis-numbered second `## 2`) defines four message types (`request`/`response`/`event`/`credential`). Since the Dec-5 authorship, MCP was repositioned as the inter-society protocol (MCP v0.1.3) and R6/R7 became the action framework. A forward cross-reference ("application-level interaction semantics are specified by the R6/R7 framework and MCP-protocol.md") would help readers, but the four transport-level message types are not *contradicted* by them. Observational.

### INFO2 — "Witness Relay (MUST)" discovery mechanism is uncross-referenced

core-protocol.md §4.2 (L146) makes Witness Relay the only **MUST** discovery mechanism and references "witness attestations" / "witness signatures" (L160) without pointing to the witnessing specs (`protocols/web4-witnessing.md`, `WEB4_WITNESSING_SPECIFICATION.md`, presence-protocol.md) that define those primitives. A cross-reference would ground the witness terms. Observational; no contradiction found.

---

## §E. Remediation Routing (for the next turn)

| ID | Severity | Finding | Routing |
|----|----------|---------|---------|
| M2 | MED | Broken numbering (dup `## 2`, orphan `### 1.3`) | **AUTONOMOUS** |
| M1 | MED | §3 restates/diverges from data-formats.md | **AUTONOMOUS** (deference pointer; form-resolution → H1) |
| L1 | LOW | Intro promises pairing process not delivered | **AUTONOMOUS** (soften intro + pointer) |
| L3 | LOW | No status/version header | **AUTONOMOUS** (add banner) |
| H1 | HIGH | W4ID scheme multi-way divergence (core corroborated) | **DESIGN-Q** (repo-wide canonical identifier scheme; couples C24-H1 LCT-ID) |
| H2 | HIGH | §2 handshake diverges from normative MTI spec | **DESIGN-Q** (field/shape reconciliation; autonomous deference-pointer if bundled) |
| M3 | MED | Nonce size 256-bit vs normative 96-bit | **DESIGN-Q** (bundled with H2) |
| M4 | MED | `web4://` authority form vs grammar ABNF | **DESIGN-Q** (coupled with H1) |
| L2 | LOW | Suite table superset + KEM naming | **CROSS-TRACK** (canonical suite registry) |
| INFO1 | INFO | Message types ↔ MCP/R6-R7 cross-ref | Observational |
| INFO2 | INFO | Witness Relay ↔ witnessing specs cross-ref | Observational |

**Anti-padding statement**: This is a first-pass audit of an 8.3KB doc; 9 actionable findings is proportionate, and the split is honest — 5 of 9 (H1, H2, M3, M4, L2) are routed AWAY from autonomous application because they require cross-doc/repo-wide decisions, leaving only 4 clean autonomous wins (M2, M1, L1, L3). The most consequential findings (H1 W4ID, H2 handshake) are explicitly NOT self-resolvable and are coupled to existing identifier-canonicalization design-Q carries.

**Recurring-pattern note**: core-protocol.md exemplifies the "old broad-sketch doc restates primitives that later got dedicated normative homes" anti-pattern. The durable fix posture (beyond this audit) is **deference over restatement** — core-protocol.md should orient/index the reader and point to data-formats.md / web4-handshake.md / grammar, not carry competing copies. M1 is the first step of that posture; H1/H2/M3/M4 are blocked on canonical-form decisions before deference can be applied cleanly.
