# C28 — `protocols/web4-handshake.md` Internal-Consistency + Cross-Spec Audit

**Date**: 2026-06-03
**Auditor**: autonomous web4 session (legion, firing `000050`, LEAD voice)
**Target**: `web4-standard/protocols/web4-handshake.md` (238 lines; header `Last-Updated: 2025-09-11T22:47:56Z`)
**Series**: C28 — **first-pass** C-series audit (this document has never been C-series audited; it is the oldest unaudited *normative protocol* doc, and the one C27-H2/M3 explicitly deferred *to* as the "normative MTI handshake home").

**Methodology**: Two passes plus a third primitive-clustered pass per the `auditor-blindspot-pattern`:
- **§B** internal consistency (suites, GREASE, Hello/Auth message shapes, profile negotiation, state machine, error codes, header).
- **§C** cross-spec divergence against the SAME primitives restated elsewhere in the repo.
- **§D** primitive-clustered pass (handshake-message-shape / nonce / suites / W4IDp).

**Authority anchors re-read this session** (passages re-read, not recalled, per cross-doc-overcall hygiene):
- `web4-standard/protocols/web4-handshake.md` (full, L1–L238)
- `web4-standard/core-spec/core-protocol.md` §1 suite table + §2 handshake block (L18–L52)
- `web4-standard/implementation/sdk/web4/protocol.py` ClientHello/ServerHello (L80–L125)
- `web4-standard/test-vectors/protocol/core-protocol.json` ClientHello vector (L139–L149)
- `web4-standard/registries/initial-registries.md` (cipher suites L5–L6; error codes L35, L51)

---

## Summary

**Headline**: `web4-handshake.md` self-declares as *"the mandatory-to-implement (MTI) handshake for Web4 endpoints"* (L6), and it is the most cryptographically-detailed handshake spec in the repo (HPKE contexts, COSE/JOSE signature profiles, GREASE, downgrade resistance). But it is **architecturally divergent** from the handshake that is actually *implemented and conformance-tested*. core-protocol.md §2 and the SDK (`protocol.py`) describe a **4-message, MAC-confirmed** flow (`ClientFinished`/`ServerFinished` + `MAC(transcript)`); handshake.md describes a **3-message, signature-authenticated** flow (`HandshakeAuth` + `COSE_Sign1`/JWS over `TH`). The field names, the nonce size, the suite set, and the authentication mechanism all differ. The test vectors and SDK corroborate core-protocol.md, NOT the self-declared-normative handshake.md.

This **inverts the C27-H2/M3 framing**: C27 (auditing core-protocol.md) treated core-protocol.md as the drifted sketch that should defer to handshake.md. Auditing handshake.md from the other side shows the implemented reality (SDK + vectors + core-protocol) is the *3-anchor cluster* and handshake.md is the *lone dissenter on every dimension*. **The "normative MTI" label and the implemented form point at different documents.** That is the central design-Q this audit surfaces; it is **not** autonomously resolvable (it requires an operator decision on which handshake is canonical, with cascading edits across spec + SDK + vectors), and it couples to the open C27-H1/M4 + C24-H1 identifier-scheme design-Qs.

Internally, handshake.md is largely self-consistent; the §B findings are minor hygiene (a self-contradicting GREASE pattern, an undemonstrated MUST in the worked examples, a state-machine label gap, a stale date).

**Finding counts**: 6 internal (§B: 2 MEDIUM, 2 LOW, 2 INFO) + 4 cross-spec (§C: 1 HIGH, 3 MEDIUM). **Split**: 4 autonomous-actionable-at-next-remediation (all §B M/L, internal to handshake.md), 3 design-Q, 1 cross-track.

---

## §B. Internal-Consistency Findings

### B-M1 (MEDIUM) — GREASE "reserved hex pattern" `*a*a*a*a` is contradicted by the spec's own examples and by its "randomly generated" requirement
**Lines**: §5.0 L66–L69 (pattern + examples), L74 ("GREASE values MUST be randomly generated for each handshake"); §5.1 L83/L85 (worked `W4-GREASE-93f07f2a`, `w4_ext_93f07f2a@0`).

**Issue**: §5.0 states *"Reserved hex patterns: `*a*a*a*a` where `*` is any hex digit"* and gives two examples:
- `w4_ext_1a2a3a4a@0` — hex `1a2a3a4a`: positions 2/4/6/8 = `a/a/a/a` → **matches** `*a*a*a*a`. ✓
- `w4_ext_fafbfcfd@0` — hex `fafbfcfd`: positions 2/4/6/8 = `a/b/c/d` → **does NOT match** `*a*a*a*a`. ✗

The worked ClientHello GREASE values (`93f07f2a`, both the suite `W4-GREASE-93f07f2a` and ext `w4_ext_93f07f2a@0`) — positions 2/4/6/8 = `3/0/f/a` → also **do NOT match** the reserved pattern. Furthermore, L74's *"MUST be randomly generated for each handshake"* is in direct tension with constraining values to a fixed `*a*a*a*a` mask: a uniformly random 8-hex value matches `*a*a*a*a` only ~1 in 65 536 of the time. The three statements (fixed reserved mask / random generation / the non-conforming examples) cannot all hold.

**Recommended fix (AUTONOMOUS-ACTIONABLE at next remediation turn)**: Pick one model and make examples obey it. Either (a) drop the `*a*a*a*a` "reserved pattern" and say GREASE IDs are *any* `w4_ext_[8-hex]@0` value chosen at random (TLS-RFC-8701-style: a fixed enumerated reserved set, OR fully random + ignored-if-unknown — not both); or (b) keep a reserved mask but fix `fafbfcfd`/`93f07f2a` to conforming `*a*a*a*a` values and reconcile with L74. Internal to handshake.md, no cross-spec dependency.

---

### B-M2 (MEDIUM) — §6.0.1 makes the signature-profile extension MUST-be-in-TH, but no worked Hello example carries it
**Lines**: §6.0.1 L118–L124 (`application/web4+cbor` → `w4_sig_cose@1`; `application/web4+json` → `w4_sig_jose@1`; *"the selected media type and signature extension ID MUST be included in TH"*); §5.1 ClientHello `ext` L85; §5.2 ServerHello `ext_ack` L100.

**Issue**: §6.0.1 establishes that the signature/canonicalization profile is negotiated *via `media` and `ext`* and that the **selected signature extension ID MUST be in the transcript hash** (a downgrade-resistance MUST). But the only worked Hello messages in the doc never show a `w4_sig_cose@1` / `w4_sig_jose@1` extension: ClientHello `ext = ["w4_ext_sdjwt_vp@1", "w4_ext_noise_xx@1", "w4_ext_93f07f2a@0"]` and ServerHello `ext_ack = ["w4_ext_sdjwt_vp@1"]`. A reader implementing from the examples would never carry the very extension whose presence-in-TH §6.0.1 makes mandatory. The MUST is asserted but un-exemplified — exactly the kind of gap that produces non-conforming implementations.

**Recommended fix (AUTONOMOUS-ACTIONABLE at next remediation turn)**: Add `w4_sig_cose@1` (and/or `w4_sig_jose@1`) to the ClientHello `ext` and the ServerHello `ext_ack` in §5.1/§5.2 so the worked examples demonstrate the §6.0.1 MUST. Internal, no cross-spec dependency.

---

### B-L1 (LOW) — State-machine prose references a `WaitClientHello` state absent from the diagram
**Lines**: §8 L194–L207. The `stateDiagram-v2` enumerates Initiator-side states only (`Start`, `SendClientHello`, `WaitServerHello`, `DeriveHPKE`, `SendAuth`, `WaitAuth`, `Established`, `Rekey`, `Error`). The trailing prose (L207) says *"Responder mirrors the flow starting at `WaitClientHello`"* — but `WaitClientHello` is never a node in the diagram.

**Recommended fix (AUTONOMOUS-ACTIONABLE)**: Either add a Responder sub-diagram (or a second `stateDiagram` block) that actually contains `WaitClientHello → SendServerHello → WaitAuth → Established`, or soften L207 to *"The Responder runs the mirror-image flow (receive ClientHello → send ServerHello → receive/verify HandshakeAuth → Established)."* Hygiene.

---

### B-L2 (LOW) — §5.1 labels Hello as "plaintext JSON" while the rest of the spec treats CBOR as the MTI encoding
**Lines**: §5.1 header L77 *"ClientHello (plaintext JSON, over TLS/QUIC or out-of-band)"*; cf. §5.2 TH L107–L108 (TH computed *"using JCS (JSON) or CTAP2/COSE canonical CBOR"*), §6.0.2 L128 (MTI = COSE/CBOR), §12 (COSE/CBOR is MTI).

**Issue**: The Hello example is presented as JSON-only, but the doc's MTI media type is `application/web4+cbor` and the transcript hash is explicitly defined over *either* JCS-JSON *or* canonical CBOR. Calling §5.1 "plaintext JSON" reads as if JSON Hellos were the only/normative form, which contradicts the CBOR-MTI stance. The examples are JSON purely for readability.

**Recommended fix (AUTONOMOUS-ACTIONABLE)**: Change the §5.1 header to *"ClientHello (shown as JSON for readability; serialized per the negotiated media type — CBOR is MTI)"*. Hygiene, no semantic change.

---

### B-INFO1 — Stale `Last-Updated` (2025-09-11), pre-dates the entire SAL/society/MCP build-out
**Lines**: L2. Per **BC#13** (date-staleness alone is INFO unless coupled to a normative date-dependency), this is INFO. Noted because the C27 audit itself used this file's L2 date as a drift-dating anchor; if a future remediation turn edits handshake.md it should refresh this banner (per **BC#15**, do NOT bump it from this read-only audit turn).

### B-INFO2 — `W4-FIPS-1` KEM column spelled `P-256EC`
**Lines**: §3 L23. Three different spellings of the same primitive exist across the repo: handshake.md `P-256EC`, core-protocol.md `P-256ECDH` (L19), registry `P-256 ECDH` (initial-registries.md L6). Cosmetic; INFO. (Folds into the C-M2 suite cross-track item below.)

---

## §C. Cross-Spec Findings

### C-H1 (HIGH, DESIGN-Q) — The "normative MTI" handshake is architecturally different from the implemented/tested handshake
**Lines**: handshake.md §5–§6 (L77–L186); core-protocol.md §2 (L22–L52); SDK `protocol.py` L80–L125; test-vectors `core-protocol.json` L139–L149.

**Issue**: handshake.md and the core-protocol/SDK/vectors cluster describe **two different handshakes**, not one handshake with cosmetic field-name drift:

| Aspect | handshake.md (self-declared MTI) | core-protocol.md §2 + SDK + vectors |
|--------|----------------------------------|-------------------------------------|
| Message count | **3**: ClientHello, ServerHello, HandshakeAuth (bidirectional) | **4**: ClientHello, ServerHello, ClientFinished, ServerFinished |
| Authentication | **Digital signature** — `sig = Sign(sk_sig, Hash(TH‖cb))` in `COSE_Sign1`/JWS (§6.0, §6.1) | **MAC** — `MAC(transcript)` in ClientFinished/ServerFinished (core §2) |
| Key-exchange field | `kex_epk` (HPKE KEM ephemeral) | `client_public_key` / `server_public_key` |
| Client identifier field | `w4idp_hint` | `client_w4id_ephemeral` |
| Server identifier field | `w4idp` | `server_w4id_ephemeral` |
| Suite-list field | `suites` / `suite` | `supported_suites` / `selected_suite` |
| Credential delivery | `cap` scopes inside AEAD'd HandshakeAuth | `encrypted_credentials` in ServerHello / ClientFinished |
| Session establishment | `session_id` absent; keys via HPKE exporter (§6.2) | explicit `session_id` in ServerFinished |

The SDK docstrings say *"Per spec §2"* (= core-protocol.md), and use `client_public_key` / `client_w4id_ephemeral` / `supported_suites` / `nonce`. The conformance vector (`core-protocol.json` L141–144) uses the same field names. So **3 anchors (core-protocol.md + SDK + test vectors) implement the 4-message MAC handshake; 1 anchor (handshake.md) specifies the 3-message signature handshake** — and *that one* is the doc carrying the "mandatory-to-implement" label.

**Why DESIGN-Q (NOT autonomous)** — per policy guardrail: handshake.md self-declares MTI, so it would be wrong to unilaterally edit it to match the SDK (or vice-versa). Resolution requires an operator decision: *which handshake is canonical?* — the cryptographically-richer signature-based HPKE flow (handshake.md), or the simpler MAC-confirmed flow that is actually built and conformance-tested (core/SDK/vectors)? Whichever wins, the loser cascades edits across the other 3 anchors. This is the substantive core of the deferred **C27-H2** and should be adjudicated together with it. **Recommendation (advisory, not a fix)**: the implemented+tested form has stronger corroboration (3 vs 1), but the signature-based form has stronger security properties (KCI resistance, non-repudiable auth) — so this is a genuine design decision, not a "fix the drift" mechanical merge. Do not half-fix.

---

### C-M1 (MEDIUM, DESIGN-Q) — Handshake nonce size: 96-bit vs 256-bit, likely a conflation of two distinct values
**Lines**: handshake.md §5.1/§5.2/§6.1 (`"nonce": "<random 96-bit>"`, L86/L96/L173); core-protocol.md §2 (`nonce[32]` = 256-bit, L29/L37); SDK `protocol.py` L89 (`nonce: str  # 32-byte hex nonce`).

**Issue**: This is **C27-M3** seen from the handshake side. handshake.md specifies a **96-bit** nonce; core-protocol.md and the SDK both specify **32 bytes / 256-bit**. **Insight surfaced by the primitive-clustered pass**: 96 bits is exactly the correct AEAD nonce length for ChaCha20-Poly1305 / AES-GCM (the W4-BASE-1 / W4-FIPS-1 AEADs) — i.e. handshake.md's `nonce` looks like an *AEAD nonce*. A 256-bit value is the natural size for an *anti-replay challenge / freshness token* (cf. §9 "nonce values MUST be unique per key; maintain a replay window"). The two specs may be describing **two semantically-different fields that happen to share the name `nonce`**: an AEAD IV (96-bit) vs a handshake freshness challenge (256-bit). The test vector muddies this further — `core-protocol.json` L144 uses `"nonce": "a1b2c3d4e5f6"` (6 bytes / 48-bit), conforming to *neither* size, with `has_nonce: true` as the only assertion (see INFO).

**Why DESIGN-Q**: Resolving requires deciding whether there is one `nonce` (and at what size) or two distinct fields (AEAD-nonce vs challenge) that should be renamed apart. Couples to C-H1 (same message-shape reconciliation) and to **C27-M3**. Route together.

**B-INFO3 (sub-item)**: the conformance vector's 48-bit `nonce` placeholder enforces no length at all — if a length becomes normative, the vector needs a real-length value. INFO, cross-track to the test-vector maintainer.

---

### C-M2 (MEDIUM, CROSS-TRACK) — Suite set divergence: `W4-IOT-1 (MAY)` exists in core-protocol.md but not in handshake.md or the registry
**Lines**: handshake.md §3 L20–L23 (lists **2** suites: W4-BASE-1 MUST, W4-FIPS-1 SHOULD); core-protocol.md §1 L18–L21 (lists **3**: adds `W4-IOT-1 (MAY)` = X25519 / Ed25519 / **AES-CCM** / SHA-256 / CBOR); registry `initial-registries.md` L5–L6 (lists **2**: W4-BASE-1, W4-FIPS-1 — no W4-IOT-1).

**Issue**: A constrained-device suite `W4-IOT-1` is defined only in core-protocol.md. The self-declared-normative handshake spec omits it, and the cipher-suite **registry** — which §13 of handshake.md points to as the authority for suite IDs — does not register it. So W4-IOT-1 is an **orphan**: referenced by the broad sketch, absent from both the normative handshake doc and the registry that is supposed to be its system-of-record. This is the open **C27-L2** suite-registry carry, now with a concrete instance.

**Why CROSS-TRACK**: The fix touches the *registry* (and/or core-protocol.md), not primarily handshake.md — decide whether W4-IOT-1 is a real MTI-tier suite (then register it + add to handshake.md §3 as MAY) or a stale draft idea (then drop it from core-protocol.md). Route to the registry/suite-governance track, bundled with C27-L2. (Also absorbs B-INFO2: the `P-256EC` / `P-256ECDH` / `P-256 ECDH` spelling drift should be normalized in the same suite-normalization pass.)

---

### C-M3 (MEDIUM, DESIGN-Q / CROSS-TRACK) — W4IDp surface form (`w4idp-<base32>` / MB32) is a fourth identifier shape
**Lines**: handshake.md §4.1 L34–L38 (`w4idp = MB32(HKDF...)`, multibase base32), §5.1 `w4idp_hint: "w4idp-<base32>"`, §5.2 `w4idp: "w4idp-<base32>"`; cf. data-formats.md §4.1 pairwise `w4id:pair:<base32>`; test-vectors/SDK `w4id:key:...` / `w4id:...`; grammar_and_notation.md `did:web4:`.

**Issue**: handshake.md's pairwise identifier renders as `w4idp-<base32>` (a bare MB32 string with a `w4idp-` prefix), which is a **distinct surface form** from data-formats.md's pairwise `w4id:pair:<base32>`, from the vectors/SDK `w4id:key:` form, and from grammar's `did:web4:`. This is the same divergence cluster as **C27-H1** (W4ID 4-way) and the **entity-identifier sibling of C24-H1** (LCT-ID divergence).

**Why DESIGN-Q/CROSS-TRACK**: Do NOT edit handshake.md in isolation — per guardrail 1, the canonical pairwise-identifier scheme is a repo-wide decision (`w4id:pair:` vs `w4idp-` vs `did:web4:`) that cascades across data-formats, grammar, vectors, SDK, and handshake.md. A single "canonical identifier scheme" resolution could settle C27-H1, C24-H1, and this finding together. Route to the identifier-scheme design-Q bundle.

---

## §D. Primitive-Clustered Pass (auditor-blindspot check)

Grouping by primitive (rather than by severity) confirmed the §C cluster and surfaced no additional internal contradictions:

- **handshake-message-shape**: C-H1 (3-msg sig vs 4-msg MAC). The single highest-impact divergence; only visible when ClientHello/ServerHello/HandshakeAuth are read *as a set* against core §2's ClientHello/ServerHello/ClientFinished/ServerFinished.
- **nonce**: C-M1 (96 vs 256 vs 48-bit) — the cluster pass is what surfaced the AEAD-IV-vs-challenge conflation hypothesis.
- **suites**: C-M2 (W4-IOT-1 orphan) + B-INFO2 (P-256 spelling).
- **W4IDp**: C-M3 (fourth surface form).

No new internal-consistency defect emerged beyond §B. handshake.md's internal cryptographic logic (HPKE context → exporter → directional session keys; TH binding; downgrade resistance via TH-bound suite list) is coherent within itself.

---

## Disposition / Routing

| ID | Sev | Class | Route |
|----|-----|-------|-------|
| B-M1 | MED | autonomous (next remediation) | GREASE pattern self-contradiction — fix in handshake.md §5.0 |
| B-M2 | MED | autonomous (next remediation) | Add `w4_sig_*@1` ext to worked Hello examples §5.1/§5.2 |
| B-L1 | LOW | autonomous (next remediation) | State-machine `WaitClientHello` — add Responder diagram or soften prose |
| B-L2 | LOW | autonomous (next remediation) | §5.1 "plaintext JSON" → "shown as JSON; CBOR is MTI" |
| B-INFO1/2 | INFO | — | Stale date (BC#13); P-256 spelling (→ C-M2) |
| C-H1 | HIGH | **design-Q** | Bundle with **C27-H2**: canonical handshake (3-msg sig vs 4-msg MAC) |
| C-M1 | MED | **design-Q** | = **C27-M3**: nonce size + AEAD-IV/challenge conflation |
| C-M2 | MED | **cross-track** | = **C27-L2**: W4-IOT-1 registry orphan + P-256 spelling |
| C-M3 | MED | **design-Q/cross-track** | Identifier-scheme bundle: **C27-H1 + C24-H1** + W4IDp form |

**No spec/SDK/vector edits made this turn** (audit turn). The 4 §B autonomous items are queued for the next REMEDIATION turn on handshake.md; all 4 are internal to handshake.md with no cross-spec dependency, so they can be applied as a clean small PR. The 4 §C items are deferred to operator/design-Q adjudication and explicitly bundle with open C27 + C24 carries — auditing handshake.md has now supplied the field-level evidence those deferred design-Qs needed (the "normative MTI" doc is the lone dissenter against the implemented+tested form on every cross-spec dimension).
