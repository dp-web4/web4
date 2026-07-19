# C222 — `protocols/web4-handshake.md` Fifth-Delta Re-Audit (growth-edge mirror gate: the name-collision false-mirror)

**Date**: 2026-07-19
**Auditor**: Legion autonomous web4 track (slot `web4-20260719-000036`, LEAD voice)
**Target**: `web4-standard/protocols/web4-handshake.md` (269 lines; `Last-Updated: 2026-06-29`; byte-frozen since C113 `57caa2e1`)
**Lineage**: C28 first-pass (#264/#265 `8b3bbac3`) → C72 first delta (#360) → C73 remediation (#362 `0179c470`) → C112 second delta (#401) → C113 remediation (#404 `57caa2e1`) → C144 third delta (DELTA-1 inversion) → C184 fourth delta (layer-split gate) → **C222** (fifth delta)
**Method**: §A prior-finding verification (C113 N1/N2) + regression sweep + C56 claim-vs-canonical re-read + bidirectional carry re-verify. §B corpus-delta since the C184 snapshot + inbound-carry (DELTA-1) re-verify at live HEAD. **§B′ genuine-mirror gate re-derived at live HEAD against the SDK GROWTH EDGE** (new modules landed since C184: `ratchet.rs`, `attestation.rs`, hub `send_secret` relay). Audit-only — **no spec edits, no SDK edits**.

---

## Headline

**0 net-new internal defects. handshake is CLEAN and CORRECT — 3rd CONSECUTIVE spec-side-clean delta (C144, C184, C222).** The target has not moved a byte in 20 days; the value this fire is entirely in the **§B′ growth-edge mirror-gate result**, which returns the **fourth flavor in the mirror-expansion series applied to handshake**:

- **C178** errors → `error.rs` = **FALSE mirror** (name-collision, no wire taxonomy).
- **C180** security → `crypto.rs` = **GENUINE mirror** (primitives, 5/6 W4-BASE-1).
- **C182/C220** registries → **ABSENT / NEGATIVE gate** (no code consumer; growth edge still 0 tokens).
- **C184** handshake → **SPLIT BY LAYER** (primitives genuine via `crypto.rs`; protocol DIVERGENT via `pair_channel.rs`, HPKE handshake ABSENT).
- **C222** handshake growth edge → **NAME-COLLISION FALSE-MIRROR.** A new `web4-core/src/ratchet.rs` (#529) landed since C184. Its name maps onto handshake **§7 `SessionKeyUpdate` one-way ratchet** — which C184 recorded as "None (deferred; Signal-style ratchet out of scope per PRD §6)". The gate returns **FALSE**: `ratchet.rs` is the **society / sovereign-authority ratchet** (RWOA monotone authority escalation), a *completely different construction* in a *different domain*. The §7 session-key ratchet gap **PERSISTS**; the name would have falsely closed it without the gate. → **C222-N1 (INFO, CROSS-TRACK/SDK)**.

The new hub `send_secret` relay (#545) and `attestation.rs` (#527/#538) are both **DISJOINT** from the handshake surface (verified §B′). `pair_channel.rs`/`crypto.rs` are byte-frozen since `bcff32fb` (2026-06-08) = **exactly C184's scored state** ⇒ the C184 layer-split (primitives genuine / protocol divergent-absent) and **C184-N1 HELD** unchanged. **No spec mutation.**

---

## §A — Prior-finding verification (C113 remediation of C112's N1/N2)

Target byte-frozen since C113 `57caa2e1` (2026-06-29, **20 days**). `git log -1` on the path confirms `57caa2e1` is HEAD-for-this-file; `git log --since=2026-07-11 -- web4-standard/protocols/web4-handshake.md` → empty. Both C113 fixes verified in place at live HEAD:

| C112 finding | C113 fix | Current site | Verdict |
|--------------|----------|--------------|---------|
| **N1** (LOW) — §3 W4-IOT-1 Profile `CBOR`→`COSE` | applied | §3 L24: `W4-IOT-1 (MAY) … COSE` | **HELD — and CORRECT** (re-confirmed §B; C144 inverted DELTA-1 in COSE's favor) |
| **N2** (LOW) — §6.0.3 sig-structure scope contradiction | applied | §6.0.3 L143: general/specific split (`HandshakeAuth` → `Hash(TH‖channel_binding)` per §6.0.5; this § governs the `COSE_Sign1` envelope + CBOR canonicalization) | **HELD** — no regression |

**Regression sweep**: 0 `&#`/HTML-entity artifacts; 269 lines intact; the C113 remediation was single-file, no cross-spec surface disturbed. Full C73 fix set (B1–B10, HELD at C112/C144/C184) remains byte-frozen.

**C56 claim-vs-canonical** (§3 suite table Profile column vs §6.0 vocabulary): re-ran the decisive check at live HEAD. §3 Profile cells = `COSE` (W4-BASE-1), `JOSE` (W4-FIPS-1), `COSE` (W4-IOT-1) — L22–24. §6.0 defines exactly two profiles: `w4_sig_cose@1` (`application/web4+cbor`, L126) and `w4_sig_jose@1` (`application/web4+json`, L127). All three §3 Profile cells draw from that `{COSE, JOSE}` vocabulary. **Clean.** The two test-vector touchpoints (`handshakeauth_cose.json`, `handshakeauth_jose.json`) carry `type: HandshakeAuth`, `suite: W4-BASE-1`, and per-profile signing `alg` (COSE `-8`/EdDSA; JOSE `ES256`) — concordant with §6.1, not findings.

---

## §B — Corpus-delta + inbound-carry re-verify (DELTA-1 stands as inverted)

**The three siblings handshake cites are frozen since the C184 snapshot (2026-07-12).** `git log --since=2026-07-11` on `core-spec/core-protocol.md`, `registries/initial-registries.md`, `protocols/web4-security-framework.md` → all empty. No sibling table changed a cell that could re-open any handshake carry.

**The broader corpus DID move** this window (LCT §1.2 #531 "Inspectable Evidence", W4IP #521/#522/#523/#525, mcp §7.8, SDK `attestation.rs`/`ratchet.rs`/`send_secret`) — but all of it is **DISJOINT from the handshake surface** (§B′ handles the SDK movers; the spec movers touch LCT/SAL/reputation/entity-types, none of which handshake cites or is cited by for its suite/negotiation/auth flow).

**DELTA-1** (W4-IOT-1 Profile `CBOR` vs `COSE`) re-verified cell-by-cell at live HEAD:

| Site | Value | Status |
|------|-------|--------|
| `web4-handshake.md:24` | `… COSE` | **CORRECT** (C113 N1 fix, C144-confirmed) |
| `core-protocol.md:20` | `… HKDF \| CBOR` (Profile col) | serialization written where a profile name belongs — the defect side |
| `initial-registries.md:7` | `… HKDF (CBOR)` | same defect, mirrored |

DELTA-1 was **fully adjudicated + INVERTED at C144** (handshake's own prior slot) and **re-confirmed at C184**: the handshake side is CORRECT; the fix belongs on the `core-protocol` + `registries` side and is routed to the operator-gated crypto-suite SSOT bundle **C-M1 ≡ B-D1** (still UNANSWERED). **This corrects a stale next-session-carry expectation** carried in memory ("DELTA-1 becomes actionable at its owner = handshake → route the fix INTO handshake"): that expectation predates the C144 inversion. The direction is settled — **handshake needs no edit; the defect lives on the two sibling cells and is B-D1-gated.** The carry STANDS as C144/C184 left it. Nothing new this fire.

---

## §B′ — Genuine-mirror gate re-derived at the SDK growth edge (the finding)

The method guard requires re-deriving the SDK mirror set at live HEAD each delta — "the SDK mirror is not a fixed set." Since C184, three new surfaces landed. Each was gated against the handshake spec:

| New surface (since C184) | What it is | Handshake-mirror verdict |
|--------------------------|-----------|--------------------------|
| `web4-core/src/ratchet.rs` (#529) | **Society / sovereign-authority ratchet** — a monotone, provable `RatchetRequirement` measuring how far a society's sovereign authority has climbed away from reachability-as-authority (RWOA `R` clause; genesis-rung → constellation). `satisfied_by(SovereignStructureProof)` = evaluator's bar, not a protocol verdict. | **FALSE MIRROR (name collision).** Name maps onto handshake §7 `SessionKeyUpdate` one-way ratchet; construction is unrelated (governance authority, not session-key forward secrecy). Exhaustive negative grep on the file: `session_key\|SessionKeyUpdate\|forward.secrec\|ChaCha\|X25519\|ClientHello\|ServerHello\|transcript` → **0**. → **C222-N1**. |
| `web4-core/src/attestation.rs` (#527/#538) | TPM/hardware attestation bound to LCT witnessing (genuine-mirror-of-LCT-spec, scored FALSE-for-security at C218). | **DISJOINT.** Grep `ClientHello\|ServerHello\|HandshakeAuth\|HPKE\|pair_channel\|session_key` → **0**. Not a handshake surface. |
| `hub/hub-daemon/src/rest.rs` `send_secret` (#545) | Content-blind member→member **sealed relay** — queues a `SealedNotice{pair_id, sealed}` ciphertext for a citizen; the hub relays without opening. AEAD authenticates the sealer, `ReplayGuard` rejects re-submits. | **DISJOINT / rides the DIVERGENT substitute.** It is a *delivery* concern layered **on top of** the existing `pair_channel` sealed channel (C184's DIVERGENT substitute) — no `ClientHello`/`ServerHello`/HPKE/negotiation/`HandshakeAuth`. It extends the substitute layer, it is **not** a new handshake mirror. |

**Exhaustive negative re-confirmed at live HEAD**: `grep -rlnE 'ClientHello|ServerHello|HandshakeAuth|rfc.?9180|HPKE'` across the tree, excluding `archive/`, `web4-standard/`, `forum/nova/`, `docs/audits/`, `*.md`, `test-vector`/`*.json` → **empty.** The specified HPKE handshake still exists nowhere in executable code.

**C184 layer-split HELD unchanged**: `pair_channel.rs` and `crypto.rs` are both byte-frozen since `bcff32fb` (2026-06-08) — the exact commit C180/C184 scored. Primitives = GENUINE mirror (`crypto.rs`, C180 5/6); protocol = DIVERGENT (`pair_channel.rs`, per-property deltas listed at C184) / HPKE ABSENT. **C184-N1 HELD** (HPKE handshake unimplemented corpus-wide; SDK lags, spec correct).

### Why the name-collision matters (the C222 lesson)

C184 recorded §7 `SessionKeyUpdate` one-way ratchet as "None (deferred)". At C222, a file literally named `ratchet.rs` now exists. The tempting — and **wrong** — move is to mark the §7 gap CLOSED because "the ratchet shipped." The gate forces the discipline: **"is it the SAME ratchet?"** It is not. `ratchet.rs` ratchets *sovereign governance authority* (how many devices/factors/occupants a society requires to exercise sovereign acts — SAL §2.1, RWOA `R`), not *session keys* (per-message forward secrecy / post-compromise recovery). Two orthogonal monotone constructions sharing one English word. This is the **C178/C216 false-mirror-by-name-collision flavor**, now recurring at handshake's growth edge — and it corroborates the standing discipline [[feedback_prose_is_not_ledger]] / [[feedback_enumeration_and_grep_hypotheses]]: **verify the construction, not the label; ask "is it NEW/SAME" before "is it TRUE".**

**Direction**: spec CORRECT, SDK gap PERSISTS. There is no ratified artifact showing the §7 session-key ratchet is *wrong* — only that it remains *unbuilt* (and now easy to mistake as built). This is the C176/C180/C184 direction (spec canonical, SDK incomplete), not a spec-staleness charge. **No spec edit; no SDK edit (audit slot).**

---

## §C — SDK wire-layer readiness synthesis (C222-N1 refines C184-N1)

The three-fire wire-layer synthesis (C180-N1 + C182-N1 + C184-N1) is updated, not reopened:

| Fire | Spec surface | SDK state at live HEAD |
|------|--------------|------------------------|
| **C180-N1** | COSE/CBOR signature encoding (§6.0.3) | web4-core has **no COSE/CBOR codec** — raw Ed25519, not `COSE_Sign1`. |
| **C182/C220-N1** | registry taxonomy (suite/`W4_ERR_`/ext IDs) | web4-core encodes **none** — no loader/enum; growth edge (`attestation.rs`/`ratchet.rs`) still 0 registry tokens. |
| **C184-N1** | HPKE handshake protocol (ClientHello/ServerHello/HandshakeAuth/negotiation/GREASE/TH) | **Unimplemented**; divergent static-ECDH `pair_channel` substitutes. |
| **C222-N1** (refines C184-N1) | §7 `SessionKeyUpdate` one-way session-key ratchet | **Unimplemented AND now name-shadowed** — a governance ratchet (`ratchet.rs`) shares the word but not the construction; `pair_channel` forward secrecy is *pair-lifetime* only, post-compromise ratchet explicitly out-of-scope (PRD §6). The §7 gap is real and unclosed. |

**The pattern holds and sharpens**: web4-core has built the *primitive* layer (`crypto.rs`) but not the *wire/protocol* layer (COSE envelopes, registry taxonomy, negotiated HPKE handshake, session-key ratchet). What ships for endpoint security is a hand-rolled static-key channel (`pair_channel`, now with a content-blind relay `send_secret` on top). Not a spec defect; an **SDK-build-sequencing fact.** C222 adds the caution that a same-word governance ratchet must not be miscounted as the session-key ratchet.

---

## Disposition / Routing

| Item | Disposition this fire |
|------|----------------------|
| §A — C113 N1 + N2 | **HELD** token-by-token; N1 re-confirmed CORRECT. 0 regression over 20-day freeze. |
| §B — DELTA-1 | **STANDS as inverted at C144, re-confirmed C184 + here.** Cited siblings frozen; broader corpus movers DISJOINT. Remains in operator bundle C-M1 ≡ B-D1 (UNANSWERED). handshake needs no edit. |
| §B′ — `ratchet.rs` | **FALSE mirror (name collision)** → **C222-N1 (INFO, CROSS-TRACK/SDK)**: §7 session-key ratchet gap PERSISTS; do NOT count the governance ratchet as closing it. Carry-only. |
| §B′ — `attestation.rs`, `send_secret` | **DISJOINT** from handshake surface (0 handshake tokens; `send_secret` rides the `pair_channel` substitute). No handshake finding. |
| §B′ — `pair_channel.rs` / `crypto.rs` | **HELD** — byte-frozen at C184's scored commit; layer-split + **C184-N1 unchanged.** |
| Net-new internal (handshake) | **0.** handshake clean & correct — **3rd consecutive spec-side-clean delta** (C144, C184, C222). |

**Why no spec edit**: this is an AUDIT slot. The one spec-adjacent item (DELTA-1's two-cell fix) is on the sibling side and operator-gated on the unresolved B-D1 SSOT; the growth-edge item (C222-N1) is SDK/cross-track carry-only. AUDIT surfaces + routes; REMEDIATION (operator-authorized) applies.

---

## Operator memo item (append to the SDK-track / C-M1 wire-layer bundle)

> **A governance ratchet has shipped; the session-key ratchet has not.** `web4-core/src/ratchet.rs` (#529) implements the *society/sovereign-authority* ratchet (RWOA monotone authority), not handshake **§7 `SessionKeyUpdate`** (per-message forward secrecy / post-compromise recovery). The two share the word "ratchet" and nothing else. When the wire-layer build proceeds off B-D1, the §7 session-key ratchet remains a from-scratch item; do not let the name-collision retire it from the owed-work list. This refines C184-N1 (HPKE handshake unbuilt) within the unchanged C180-N1/C182-N1/C184-N1 wire-layer-readiness synthesis.

---

## Pattern note (C222)

**The genuine-mirror gate must be re-run at the growth edge every delta, and its most dangerous outcome is the name-collision false-mirror at a spec surface a prior audit recorded as "deferred/absent."** When a prior fire logs a gap as "None (deferred)" and a later fire finds a file whose *name* matches that gap, the null hypothesis is **collision, not closure** — verify the construction (grep the load-bearing tokens: `session_key`, `SessionKeyUpdate`, `X25519`, `transcript`), not the filename. `ratchet.rs` at C222 is the exact trap: a real, well-built monotone ratchet that is the *wrong* ratchet for this lens. Corollary to C184's layer-split: after splitting by layer, keep re-gating each layer's mirror as new same-named code lands — a growth-edge module can *look* like it fills a layer's gap while belonging to an entirely different subsystem.
