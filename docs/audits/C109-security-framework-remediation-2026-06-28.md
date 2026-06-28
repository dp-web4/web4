# C109 — `security-framework.md` Remediation (applies C108 finding N1)

**Remediation ID**: C109
**Target**: `web4-standard/core-spec/security-framework.md` §3.1 (Authentication)
**Date**: 2026-06-28
**Author**: autonomous web4 session (legion, slot `000036`), v2 protocol, LEAD voice
**Applies**: C108 audit (`docs/audits/C108-security-framework-2nd-delta-2026-06-28.md`) finding **N1** (LOW, AUTONOMOUS).
**Lineage**: C31 (2026-06-04) → C68 (1st delta) → C69 remediation (#350 `3d04dd5c`) → C108 (2nd delta) → **C109 remediation**.

---

## Scope

This is the **remediation turn** for `security-framework.md`. The C108 2nd-delta audit
was the **first** in the 9-wrap frozen-target streak to produce a net-new finding, so —
unlike C107 (errors remediation, a no-op) — C109 is **not** a no-op. It applies the single
net-new autonomous finding **N1**.

**In scope (applied):** N1 only.
**Out of scope (gated/carried, unchanged this turn):**
- **B-7** (5-site FIPS-KEM spelling → `ECDH-P256`) — gated on operator DESIGN-Q **C-M1 ≡ C70-B-D1** (crypto-suite registry SSOT). Resolution check this session: `git log 3d04dd5c..HEAD` for crypto-suite/SSOT/registry decisions returned only `88cb2c5d audit(C70)` (the audit that *raised* B-D1, no operator decision); `gh issue list` empty. **B-D1 remains operator-gated → B-7 stays gated.** Per the C108 disposition ledger, with B-D1 open the C109 slot applies N1 only and leaves B-7 gated.
- All DESIGN-Q carries (**B-3** VC-vs-SAL authz, **B-9/B-M2** rotation mutate-vs-stable-DID, **C-M1**, **B-H2/B-11** W4-IOT-1/AES-CCM in SDK+vectors) — operator canonicity, recorded not resolved.
- All CROSS-TRACK carries (**B-8** SDK docstring, **B-10** `cose:ES256`→`cose:EdDSA`, **B-L6/B-L7** vector ownership / `device` W4ID method) — land in other files/tracks.

---

## N1 — §3.1 deference over-attributed 3 properties to handshake §6.0.5

### Defect (from C108 §A.2)

The C69 **B-2** remediation added a deference sentence to §3.1 that collapsed three distinct
handshake line-cites (C68 had correctly cited §6.0.5 **plus** §6.1 freshness **plus** §9
nonce/replay) into a single anchor. The result (§3.1 L89, pre-C109):

> See `web4-handshake.md` Section 6.0.5 for the normative session-binding, **freshness, nonce-uniqueness, and replay-protection** requirements that a conformant challenge-response MUST satisfy.

But handshake **§6.0.5 "Binding to Session (MUST)"** normatively contains **only** session-binding
(`Hash(TH || channel_binding)`, `channel_binding = epk_I || epk_R`, kid authorization). The other
three named properties live elsewhere — verified against the live handshake doc this session:

| Property | Lives in (handshake doc) | Verified |
|---|---|---|
| session-binding | **§6.0.5** "Binding to Session (MUST)" | L154–156 |
| freshness (`ts` ±300s) | **§9** "Anti-Replay & Clocks" | L242 |
| nonce-uniqueness | **§9** "Anti-Replay & Clocks" | L235–238 |
| replay-protection (window ≥300s) | **§9** "Anti-Replay & Clocks" | L239–241 |
| `nonce`/`ts` field definitions | **§6.1** HandshakeAuth | L166 |

A precise reader following the §6.0.5 pointer for replay-protection landed on a
session-binding-only section.

**Snapshot-guard (C108 §A.2):** this imprecision was present at the C69 snapshot
(`git show 3d04dd5c`) — §6.0.5 covered only session-binding then too. It is **not**
sibling-introduced (C73 reinforced, did not break, the anchor); it is a self-contained
refinement of the C69 B-2 wording. Hence AUTONOMOUS (fix lives inside this file).

### Fix applied

§3.1 L89 final sentence now reads:

> See `web4-handshake.md` §6.0.5 (Binding to Session) for the normative session-binding
> requirement, and §9 (Anti-Replay & Clocks) for the freshness, nonce-uniqueness, and
> replay-protection requirements that a conformant challenge-response MUST satisfy; the
> `HandshakeAuth` `nonce`/`ts` fields these rules operate on are defined in §6.1.

Each named property now points to the section that normatively contains it. No normative
content changed — this is a citation-precision correction.

---

## Verification

- **Edit isolation:** §3.1 L89 is the **only** §6.0.5 reference in `security-framework.md`. The
  §1.3 anchors (L50 §6.0.3 COSE profile, L55 §6.0.4 JOSE profile) are unrelated and untouched;
  C108 §B.2 already confirmed they resolve and content-match.
- **Anchor liveness (edit-time):** handshake §6.0.5 (L154 "Binding to Session"), §6.1 (L166
  HandshakeAuth, defines `nonce`/`ts`), §9 (L234 "Anti-Replay & Clocks") all confirmed present in
  the current handshake doc this session.
- **Regression sweep:** no other line in the file references the moved properties; no numbering or
  artifact regressions introduced (single-sentence prose change).

---

## Outcome

C109 closes the lone C108 finding. The §3.1 cross-reference is now precise against the canonical
handshake doc. All 8 C108 carries remain as recorded (B-3/B-9/C-M1 DESIGN-Q operator-gated; B-7
cross-confirmed but gated on B-D1; B-8/B-10/B-L6/B-L7 CROSS-TRACK; B-H2/B-11 split — registry-orphan
sub-facet resolved by C71, SDK/vector sub-facet open).

**Rotation:** with security-framework's audit+remediation pair complete, the round-robin advances to
the **next-oldest** target — the **registries cluster** (last C70/C71, 2026-06-18) for its 2nd-delta audit.

**Key lesson (reinforces C108):** the remediation a frozen-wrap audit produces is exactly as small as
the finding — a one-sentence citation split. The value was in the C56 claim-vs-canonical re-read that
*found* it, not the size of the fix. A LOW finding correctly yields a LOW-touch remediation; resisting
the urge to bundle the operator-gated B-7 normalization into this turn is the constraint-compliance win.

---

*Remediation produced under Autonomous Session Protocol v2 — slot `000036`, LEAD voice. One spec file modified (`security-framework.md`, one sentence); no SDK, test-vector, or sibling-doc files touched.*
