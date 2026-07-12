# C184 — `protocols/web4-handshake.md` Fourth-Delta Re-Audit (SDK-mirror gate: the layer-split result)

**Date**: 2026-07-12
**Auditor**: Legion autonomous web4 track (slot `060036`, LEAD voice)
**Target**: `web4-standard/protocols/web4-handshake.md` (269 lines; `Last-Updated: 2026-06-29`)
**Lineage**: C28 first-pass (#264/#265 `8b3bbac3`) → C72 first delta (#360) → C73 remediation (#362 `0179c470`) → C112 second delta (#401) → C113 remediation (#404 `57caa2e1`) → **C144** third delta (DELTA-1 inversion) → **C184** (fourth delta)
**Method**: §A prior-finding verification (C113's N1/N2) + regression sweep + C56 claim-vs-canonical re-read. §B corpus-delta + inbound-carry re-verify (DELTA-1 already inverted+routed at C144). **§B′ genuine-mirror gate** (the C178/C180/C182 method) applied to handshake's SDK mirror candidates. Audit-only — **no spec edits**.

---

## Headline

**0 net-new internal defects. handshake is CLEAN and CORRECT — 2nd consecutive spec-side-clean delta (C144, C184).** The value this fire is the **§B′ genuine-mirror gate result, which is a NEW boundary in the mirror-expansion series: the layer-split.**

- **C178** errors → Rust `error.rs` = **FALSE mirror** (name-collision, no wire taxonomy).
- **C180** security → Rust `crypto.rs` = **GENUINE mirror** (5/6 W4-BASE-1 concordance).
- **C182** registries → **ABSENT** (no code consumer at all).
- **C184** handshake → **SPLIT BY LAYER.** The handshake's *cryptographic primitives* have a **genuine mirror** (`crypto.rs`, already scored at C180). The handshake *protocol itself* — HPKE (RFC 9180), ClientHello/ServerHello suite+profile negotiation, GREASE, transcript-hash downgrade resistance, `HandshakeAuth` `COSE_Sign1`, HPKE-ephemeral forward secrecy, `SessionKeyUpdate` ratchet — has **NO mirror**. A **DIVERGENT** implementation stands in its place: `web4-core/src/pair_channel.rs` (PAIRED-CHANNELS Sprint E/F), a static-ECDH-plus-ephemeral-mix sealed-message channel that reaches the *same primitives* but through a *fundamentally different protocol construction*.

Yields **C184-N1 (INFO, CROSS-TRACK/SDK)**: the specified HPKE handshake is **UNIMPLEMENTED corpus-wide** (no HPKE / `ClientHello` / `ServerHello` / `HandshakeAuth` anywhere in Rust or Python — only spec, test-vectors, and the Nova parallel bundle). **Spec is CORRECT and canonical; the SDK lags** (and has, so far, *substituted* a simpler channel primitive rather than building the handshake). This bundles with **C180-N1** (web4-core has no COSE/CBOR codec) and **C182-N1** (no registry loader) into a coherent **SDK wire-layer readiness fact** — see §C. **No spec mutation.**

---

## §A — Prior-finding verification (C113 remediation of C112's N1/N2)

Target byte-frozen since C113 `57caa2e1` (2026-06-29, **13 days**). `git log -1` on the file confirms `57caa2e1` is HEAD-for-this-path. Both C113 fixes verified in place at live HEAD:

| C112 finding | C113 fix | Current site | Verdict |
|--------------|----------|--------------|---------|
| **N1** (LOW) — §3 W4-IOT-1 Profile `CBOR`→`COSE` | applied | §3 L24: `W4-IOT-1 (MAY) … COSE` | **HELD — and CORRECT** (re-confirmed §B; C144 already inverted DELTA-1 in COSE's favor) |
| **N2** (LOW) — §6.0.3 sig-structure scope contradiction | applied | §6.0.3 L143: general/specific split ("governs non-handshake signed payloads … for `HandshakeAuth` the signing input is `Hash(TH \|\| channel_binding)` per §6.0.5") | **HELD** — no regression |

**Regression sweep**: 0 `&#` HTML-entity artifacts; 269 lines intact; single-file C113 remediation, no cross-spec surface disturbed. Full C73 fix set (B1–B10, HELD at C112/C144) remains byte-frozen.

**C56 claim-vs-canonical** (§3 suite table vs §6.0 vocabulary): re-ran the C144 decisive check. §6.0 (L120, L126-127, §12 L264-266) defines exactly two profiles — `w4_sig_cose@1` (COSE/CBOR) and `w4_sig_jose@1` (JOSE/JSON). All three §3 Profile cells (`COSE`/`JOSE`/`COSE`) draw from that `{COSE, JOSE}` vocabulary. **Clean.** The three test-vector touchpoints (`handshakeauth_cose.json`, `handshakeauth_jose.json`) both carry `type: HandshakeAuth`, `suite: W4-BASE-1`, and the correct per-profile signing `alg` (COSE `-8`/EdDSA; JOSE `ES256`) — concordant with §6.1, not findings.

---

## §B — Corpus-delta + inbound-carry re-verify (DELTA-1 stands as inverted)

**Zero sibling movement since the C144 snapshot (2026-07-06).** `git log --since=2026-07-06` on `core-protocol.md`, `registries/initial-registries.md`, `security-framework.md` → empty. No sibling table changed a cell that could re-open DELTA-1.

**DELTA-1** (W4-IOT-1 Profile `CBOR` vs `COSE`) was **fully re-adjudicated at C144 — handshake's own prior slot** — and INVERTED: `handshake:24 = COSE` is CORRECT; the defect is `core-protocol.md:20` + `registries/initial-registries.md:7` = `CBOR` (a serialization written where a profile name belongs). That correction was routed to the operator-gated crypto-suite SSOT bundle **C-M1 ≡ B-D1** (still UNANSWERED). **Nothing new here this fire** — no movement, no re-adjudication needed; the carry STANDS as C144 left it. This confirms the C182 next-session-carry expectation ("DELTA-1 becomes actionable at its owner") was already discharged at C144, one cycle early.

---

## §B′ — Genuine-mirror gate: the layer-split (the finding)

### Candidates enumerated at live HEAD

| Candidate | What it is | Handshake-protocol mirror? |
|-----------|-----------|---------------------------|
| `web4-core/src/crypto.rs` | Ed25519 sign/verify, X25519 ECDH (Ed25519→X25519 per RFC 8032 §5.1.5), ChaCha20-Poly1305, SHA-256/HKDF | **Primitives only** — genuine mirror of the W4-BASE-1 *suite* (scored C180, 5/6); **no HPKE, no protocol** |
| `web4-core/src/pair_channel.rs` | PAIRED-CHANNELS Sprint E/F: static-ECDH (+per-pair ephemeral mix) → HKDF-SHA256 → ChaCha20-Poly1305 sealed messages | **DIVERGENT** — a *different* channel-establishment protocol (see below) |
| `hub/hub-daemon/src/rest.rs` `dispatch_channel` | REST tool-dispatch over `pair_channel` sealed requests; sender-auth via envelope signature; constellation freshness tiers | Rides `pair_channel`; **not** the handshake |
| `web4-core/python/**` | (grep) | **no** handshake / HPKE tokens |
| Nova bundle `forum/nova/…/core-handshake.md` | parallel *spec* doc, not code | out of gate scope (doc, not mirror) |

**Exhaustive negative check**: `grep -rlnE 'ClientHello|ServerHello|HandshakeAuth|rfc.?9180|HPKE'` across the tree, excluding `archive/`, `web4-standard/`, `forum/nova/`, `docs/audits/`, `*.md`, and `test-vector` → **empty**. The specified handshake exists nowhere in executable code.

### Why `pair_channel.rs` is DIVERGENT, not a mirror (per-property)

| Spec property (web4-handshake.md) | `pair_channel.rs` reality |
|-----------------------------------|---------------------------|
| §1/§6 HPKE (RFC 9180) KEM+KDF+AEAD context | **Raw X25519 ECDH** → HKDF directly (`derive_session_key`, L157). No HPKE context. |
| §5 ClientHello/ServerHello capability + suite negotiation | **None.** No hello messages; pairing is out-of-band ledger metadata. |
| §5.0 GREASE anti-ossification | **None.** |
| §3 suite IDs (W4-BASE-1/FIPS-1/IOT-1) | **None cited.** One hard-wired primitive set. |
| §5.2/§11 transcript-hash `TH` downgrade resistance | **None.** No transcript. |
| §6.1 `HandshakeAuth` `COSE_Sign1` over `Hash(TH‖channel_binding)` | **None.** Payload confidentiality = AEAD; **sender authenticity rides the REST envelope signature** (module doc L56-60), not a handshake signature. |
| §11 forward secrecy via **per-session HPKE ephemeral** | Sprint F (`EphemeralKeyPair`, `derive_session_key_v2`, L266/L331) gives forward secrecy via a **per-pair ephemeral X25519 mix** (`ikm = static_shared ‖ ephemeral_shared`, info `web4-paired-channel-v2`) — real code, but *pair-lifetime* granularity, and post-compromise ratcheting is **explicitly out-of-scope** (L240-242). |
| §7 `SessionKeyUpdate` one-way ratchet | **None** (deferred; Signal-style ratchet out of scope per PRD §6). |

**Convergence point (the reason this is a SPLIT, not a clean FALSE mirror):** both the spec's COSE/CBOR MTI profile and `pair_channel` land on the **same primitive set** — X25519 + Ed25519-derived keys + ChaCha20-Poly1305 + SHA-256/HKDF. That primitive layer *does* have a genuine mirror (`crypto.rs`, C180). So the gate does not return a single verdict — it **splits by layer**: **primitives = GENUINE (C180); protocol = DIVERGENT/ABSENT (C184).**

### Direction — spec CORRECT, SDK lags (held per-finding)

The construction the SDK *has built* is self-labelled a staged MVP: "Sprint E is the static-key baseline" (L49-50); forward secrecy "— Sprint F" (L64); post-compromise security "deferred per the PRD §6 out-of-scope list" (L242). The code **admits its own incompleteness** relative to the security properties the spec mandates (forward secrecy, downgrade resistance, mutual handshake auth). This is the **C176/C180 direction** (spec canonical, SDK incomplete — the SDK's own comments defer the gap), **not** the C172 direction (ratified vector proves spec stale). There is no ratified artifact showing the HPKE handshake is *wrong* — only that it is *unbuilt*, with a simpler primitive substituted for now. → **Spec is CORRECT. Do not flip this to a spec-staleness charge.**

---

## §C — SDK wire-layer readiness synthesis (bundles C184-N1 + C180-N1 + C182-N1)

Three consecutive mirror-gate results now compose into one coherent SDK-readiness fact about the **wire/protocol layer** of web4-core:

| Fire | Spec surface | SDK state |
|------|--------------|-----------|
| **C180-N1** | COSE/CBOR signature encoding (§6.0.3) | web4-core has **no COSE/CBOR codec** — signatures are raw Ed25519, not `COSE_Sign1`. |
| **C182-N1** | registry taxonomy (suite IDs, `W4_ERR_` codes, extension IDs) | web4-core encodes **none** of these strings — no loader/enum exists. |
| **C184-N1** | HPKE handshake protocol (ClientHello/ServerHello/HandshakeAuth/negotiation/GREASE/TH) | **Unimplemented**; a divergent static-ECDH channel (`pair_channel`) substitutes for endpoint confidentiality. |

**The pattern**: web4-core has built the *primitive* layer (crypto.rs — keys, ECDH, AEAD, hashing: C180 genuine) but **not** the *wire/protocol* layer (COSE envelopes, suite/registry taxonomy, the negotiated HPKE handshake). What ships today for endpoint-to-endpoint security is a **hand-rolled static-key channel** at a different layer than the spec's handshake. This is not a defect in the spec and not (yet) a divergence to reconcile — it is an **SDK-build-sequencing fact**: whichever crypto-suite SSOT B-D1/C-M1 resolves to, a from-scratch build of {COSE codec + registry loader + HPKE handshake} is owed on the SDK side; there is no existing wire-layer mirror to migrate. **C184 adds the load-bearing item to that list: the handshake protocol itself.**

---

## Disposition / Routing

| Item | Disposition this fire |
|------|----------------------|
| §A — C113 N1 + N2 | **HELD** token-by-token; N1 re-confirmed CORRECT. 0 regression. |
| §B — DELTA-1 | **STANDS as inverted at C144.** Zero sibling movement; no re-adjudication. Remains in operator bundle C-M1 ≡ B-D1 (UNANSWERED). |
| **§B′ / C184-N1** (INFO, CROSS-TRACK/SDK) | HPKE handshake has **no code mirror**; `pair_channel.rs` is a **DIVERGENT** substitute at a different layer (primitives converge — genuine via crypto.rs C180; protocol diverges/absent). **Spec CORRECT, SDK lags.** Carry-only; **no frozen-spec mutation.** Bundles into the §C SDK wire-layer-readiness synthesis with C180-N1 + C182-N1. |
| Net-new internal (handshake) | **0.** handshake clean & correct — 2nd consecutive spec-side-clean delta. |

**Why no spec edit**: this is an AUDIT slot; the only actionable gap is on the SDK/cross-track side (carry), and the one spec-adjacent item (DELTA-1's two-cell fix) is operator-gated on the unresolved B-D1 SSOT surface. AUDIT surfaces + routes; REMEDIATION (operator-authorized) applies.

---

## Operator memo item (append to the SDK-track / C-M1 context bundle)

> **web4-core's wire/protocol layer is unbuilt; primitives are built.** Three mirror-gate fires now agree: crypto *primitives* have a genuine SDK mirror (crypto.rs, C180 5/6-concordant), but the *wire layer* does not — no COSE codec (C180-N1), no registry taxonomy loader (C182-N1), and **no HPKE handshake** (C184-N1; a static-ECDH `pair_channel` substitutes at a different layer). Whichever form B-D1 declares SSOT for the crypto-suite registry, the SDK owes a from-scratch build of {COSE/CBOR codec, suite/error/extension registry loader, the negotiated HPKE handshake with GREASE + transcript-hash downgrade resistance + `HandshakeAuth`}. There is no existing wire-layer code to migrate — only the primitive layer to build on. INFO/planning, not a spec defect.

---

## Pattern note (C184)

The genuine-mirror gate is **not single-valued per file — it can split by layer.** A spec doc that describes both primitives and a protocol over them (handshake = suite table §3 + HPKE flow §5-§11) can have a **genuine primitive mirror and an absent/divergent protocol mirror simultaneously.** The disciplined move when the gate seems to give conflicting signals ("crypto.rs concords" vs "no handshake exists") is to **resolve the mirror question per architectural layer, not per file.** Corollary for the DIVERGENT verdict (distinct from C182's ABSENT): when code for the *same goal* exists but implements a *different construction*, do not score it ABSENT (that understates what's built) nor GENUINE (that overstates concordance) — name it DIVERGENT, list the per-property deltas, and decide direction from whether the code admits its own incompleteness (here it does: "Sprint E baseline", "Sprint F", "out-of-scope per PRD §6") → SDK lags, spec correct.
