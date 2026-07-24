# C260 — `protocols/web4-handshake.md` 4th delta (7th pass)

**Date**: 2026-07-23 (slot `180036`, Legion web4 track)
**Target**: `web4-standard/protocols/web4-handshake.md` (269 lines)
**Lineage**: C28 → C72 → C73 → C112 → C113 → C144 → C184 → C222 → **C260**
**Prior audit**: C222 (5th pass / 3rd delta), 2026-07-19, PR #548
**Verdict**: **4th CONSECUTIVE spec-side-clean delta (C144 + C184 + C222 + C260), 0 net-new.** Recommend-only; zero spec/SDK mutation.

This is a lean witnessing record. Ground truth was pre-verified (git freeze checks + grep gates below); the doc cites that verification rather than re-deriving it — proportionality caveat from the policy review honored.

---

## Freeze status (the audit surface)

| Surface | State at live HEAD | Consequence |
|---|---|---|
| `web4-handshake.md` | byte-frozen since **C113 `57caa2e1`** (2026-06-29); `57caa2e1..HEAD -- <target>` **empty** (24 d) | §A held by construction |
| `web4-standard/` (whole tree) | **0 commits since the C222 snapshot** (2026-07-19) | **§B corpus-delta surface EMPTY** — no cited sibling moved |
| `web4-core/src/` (whole crate) | **0 commits since the C222 snapshot**; newest 3 movers `4f76f110`/`2ec6ae09`/`357173c4` all 2026-07-18, adjudicated by C254/C256/C258 | §B′ mirror set unchanged from C222 |

The target, its entire cited-sibling neighborhood, AND its SDK mirror crate are all frozen relative to the C222 baseline. The live surface reduces to re-confirming the C222 ledger holds and re-running the genuine-mirror gate at the growth edge (method guard: the mirror set is re-derived, not assumed).

---

## §A — Prior findings + regression (held by byte-freeze)

- **C113-N1** (§3 `W4-IOT-1` Profile = COSE, L24) — HELD. Re-read live: L24 `| W4-IOT-1 (MAY) | X25519 | Ed25519 | AES-CCM | SHA-256 | COSE |`.
- **C113-N2** (§6.0.3 signature-structure split, COSE/CBOR profile block) — HELD. §6.0.1 negotiation vocab (`w4_sig_cose@1` / `w4_sig_jose@1`, L126–127) + §6.0.3 COSE/CBOR MTI (L132 "MUST implement COSE/CBOR with Ed25519/EdDSA") concordant.
- **C56 §3↔§6.0 concordance** — Profile column {COSE, JOSE} (L22–24) matches §6.0 media-type vocab; both test vectors (`handshakeauth_{cose,jose}.json`) carry correct per-profile `alg` (unchanged since C222).
- **Regression sweep** — `grep '&#|&amp;|&lt;|&gt;'` over the target = **0** HTML-entity artifacts; 269 lines intact.

---

## §B — Corpus delta: EMPTY

`git log --since=2026-07-19 -- web4-standard/` is empty. The three cited siblings (core-protocol / initial-registries / security-framework) are frozen at or before the C222 snapshot (`3084e4d2` / `3f1d6fad` / `eedd36fc`). No handshake-cited sibling moved → nothing to route. (Broader corpus movers since C222 — none in-tree; the LCT/mcp/SDK motion that C222 examined all predates this snapshot.)

An empty corpus-delta surface is a **recorded result, not a skipped audit** — the value migrates to §B′.

## §B′ — SDK genuine-mirror gate, re-derived at live HEAD

Whole `web4-core/src/` crate frozen since the C222 snapshot. The three most-recent movers (all 2026-07-18, PREDATE snapshot, already adjudicated one-to-three fires ago) were re-run through the **handshake mover-guard** to confirm none grew a handshake surface:

| Mover | File(s) | Handshake tokens¹ | Verdict |
|---|---|---|---|
| #544 `authority_ratchet` | `lct.rs`, `ratchet.rs` | 0 / 0 | society/sovereign authority ratchet — **C222-N1 name-collision HELD** |
| #540 operational-key vouching | `lct.rs` | 0 | LCT-structure, not a handshake surface |
| oracle-scope | `role_extension.rs`, `role.rs` | 0 / 0 | role-scope authz, not a handshake surface |

¹ `grep -ciE 'ClientHello|ServerHello|HandshakeAuth|session.?key|HKDF|X25519|handshake|transcript'`

**C222-N1 name-collision, re-confirmed:** `ratchet.rs` (#529/#544) carries **0** `HKDF|X25519|session-key|transcript` tokens. The handshake §6.2 `SessionKeyUpdate` **one-way HKDF session-key ratchet** (L214–215, L229) and the web4-core **society/authority ratchet** (RWOA monotone authority, SAL §2.1) are same-name / orthogonal-construction. The §6.2 session-key-ratchet gap PERSISTS; it is NOT closed by the same-named governance ratchet.

**Layer split HELD** (C184): primitives GENUINE via `crypto.rs`/`pair_channel.rs` (both frozen `bcff32fb`, 2026-06-08); handshake wire-protocol **DIVERGENT-ABSENT**.

**C184-N1 HELD (HPKE handshake unbuilt):** `grep -rniE 'ClientHello|ServerHello|HandshakeAuth|HPKE|rfc.?9180'` over `web4-core/src/` (executable, non-test) = **empty**. `attestation.rs` (`0e997079`) DISJOINT and frozen.

Boundary series: handshake mirror = **primitives-built / wire-layer-absent**, re-confirmed on the growth edge (name-collision false-mirror does not close the gap).

---

## §C — Internal contradictions: none net-new

Re-verified against the full frozen file: §3 suite table ↔ §6.0 profile vocab; §5.1 ClientHello "CBOR is MTI" (L81) ↔ §6.0.1 media-type negotiation; §6.2 SessionKeyUpdate state machine (L214–229). 0 net-new internal contradictions.

---

## Standing carries (re-verified OPEN, owners unchanged — NOT re-opened net-new)

- **DELTA-1 (FINAL, B-D1/C-M1-gated):** handshake:24 `Profile = COSE` is **CORRECT** (a profile name). The defect is on the sibling cells `core-protocol:20` + `registries:7` where a *serialization* ("CBOR") is written in a *profile-name* column. **handshake needs NO edit** — the fix belongs on the two sibling cells, gated on the unanswered flagship **B-D1 ≡ C-M1** (registry SSOT inversion). Confirms the corrected direction established at C144/C222 (supersedes the stale "DELTA-1 becomes actionable INTO handshake" memory carry — it is actionable at the *siblings*, not here).
- **B-7 (cross-track, C-M1-gated):** L23 `W4-FIPS-1` KEM = `P-256EC` is one of the 5-site FIPS-KEM spelling-drift carry (`P-256ECDH` / `P-256 ECDH` / `P-256EC` / `ECDH-P256`×2; target `ECDH-P256`). Tracked in the security lineage; NOT net-new to handshake.
- **C222-N1 (INFO):** §6.2 session-key ratchet unbuilt; the same-named authority ratchet is orthogonal (above).
- **C184-N1 (INFO):** HPKE handshake unbuilt corpus-wide.
- **C73 B1–B10 + C-M1≡B-D1:** STAND → operator / cross-track.

---

## Disposition

- **C261 = declared NO-OP** (handshake CLEAN & frozen; DELTA-1 B-D1-gated — do NOT self-fix).
- Rotation +2 → `protocols/web4-lct.md` = **C262** (web4-lct last audit C224 5th delta, 2026-07-19).
- Next handshake delta ~C296. **Guard C296:** re-run the mover-guard grep (`session.?key|HKDF|X25519|ClientHello`) over any *new* web4-core module — a genuine handshake mirror would carry those tokens; a same-named governance/authority ratchet does not (the C222-N1 discipline). Do NOT re-open L23 `P-256EC` (B-7) or L24/DELTA-1 as net-new.

**Pattern (C260):** when target + cited neighborhood + SDK mirror crate are all frozen relative to the prior snapshot, the audit is a witnessing act — re-run the cheap grep gates to prove the frozen strings still can't be contradicted by the crate, record it, and route (do not self-apply) the gated carries. The genuine-mirror gate's job on a frozen crate is to re-confirm that the nearest same-named module (`ratchet.rs`) is still a name-collision, not a closure of the §6.2 gap.
