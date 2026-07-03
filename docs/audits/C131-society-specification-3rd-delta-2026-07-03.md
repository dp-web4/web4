# C131 — Third-Delta Re-Audit: SOCIETY_SPECIFICATION.md

**Date**: 2026-07-03
**Auditor**: Legion autonomous web4 track (slot 000036, v2 protocol)
**Target**: `web4-standard/core-spec/SOCIETY_SPECIFICATION.md` (481 lines, head `900caca8`)
**Lineage**: C22 (first audit, PR #251) → C50 (first delta, PR #317) → **C51 remediation** (`958a5625`/#318, + pre-merge mini-audit `9c2edd7e`/`9f5f6892`) → C92 (second delta, PR #382-era) → **C131 (this, third delta)**
**Rotation**: audit-side round-robin WRAPPED (mrh-tensors was the last file at C129 → wraps to SOCIETY_SPECIFICATION.md, the oldest, last audited C92).
**Staleness at audit**: **byte-frozen since C51.** `git diff 958a5625 HEAD -- <target>` is empty; also empty vs the C92 head `f0c82118`. No commit has touched the target in 21 days.
**Method**: §A byte-freeze verification of the 21 held C51 findings + the **C56 claim-vs-canonical re-read against the LIVE siblings** (two cited siblings moved since C92 — the diff-what-moved discipline); §B 3-lens multi-agent finder sweep (internal coherence, inbound cross-ref, SDK fidelity) with **refute-by-default** adversarial verification of every candidate; §C bidirectional carry re-verification with the **snapshot-presence guard** (re-read the *current* sibling byte, not the C92-era one).

---

## Verdict (summary)

- **§A**: The target is **byte-frozen since C51** → all 21 C92-verified C51 findings HELD by construction. Two siblings SOCIETY_SPEC cites (`atp-adp-cycle.md`, `mcp-protocol.md`) *did* move since C92, so the inbound-cite surface was re-verified against the **live** siblings: **both sibling deltas land in sections SOCIETY_SPEC does not cite** (atp-adp §4.2/§7.1 MUST#6 scope note = C119; mcp §12 R7 MUST#6 = C117), while SOCIETY_SPEC cites atp-adp **§2.1–§2.4** and mcp **§7.3/§7.5** — all of which resolve accurately at HEAD. **Inbound surface clean.**
- **§B**: 3 finder lenses → **1 raw candidate, adversarially REFUTED / 0 CONFIRMED net-new spec defects.** The internal-coherence lens's sole candidate (formation action-name mismatch) is a false-positive overcall — the file's consistent prose-summary style, explicitly licensed by L39. The inbound-cross-ref lens returned **clean** (all cites resolve). The SDK-fidelity lens re-confirmed the standing carry **C92-N1** (solo-founder `<2` guard) and **sharpened** it, plus confirmed everything else is an EXACT match.
- **§C**: design-Q carries **C50-B13 / B14 / B15 re-verified OPEN** (snapshot-guarded against current sibling bytes); **C92-N1 re-confirmed OPEN and sharpened**; **C92-N3 / C50-B20** (id-scheme examples) re-verified present. Standing carry **C22-M3** (`type`↔`event_type`) confirmed present.
- **Net**: **0 autonomous spec defects. This is the FIRST fully-clean SOCIETY_SPECIFICATION delta on the spec side** (C22 heavy, C50 found 9 remediation-introduced defects in #252, C92 had 1 net-new SDK-lag item; C131 has 0 net-new). The file's entire open frontier is operator-DESIGN-Q (B13/B14/B15) and SDK-track (C92-N1 + C22-M3). No autonomous C132 spec remediation. Rotation advances to `dictionary-entities.md` (lineage C17→C52→C94→**C132**).

---

## §A — Prior-Finding Verification (byte-freeze + live-sibling cite re-check)

**Result: 21/21 C51 findings HELD; inbound cross-ref surface re-verified accurate against the LIVE siblings.**

### Byte-freeze establishes §A held-status

`git diff 958a5625 HEAD -- web4-standard/core-spec/SOCIETY_SPECIFICATION.md` is **empty**. The 481-line file is byte-identical to its C51 remediation state and to its C92 audit snapshot (`f0c82118`). C92 verified all 21 C51 findings (19 autonomous + flagship R1 + carry-NEW-K) token-by-token against canonical with **zero regressions**. Because the file has not changed a single byte since, those 21 verifications hold by construction — there is no new prose to re-verify *within* the target.

### The real §A surface this round: the two moved siblings (diff-what-moved)

The audit yield on a byte-frozen target is on the **corpus-delta surface** — siblings the frozen file cites that have *themselves* changed. Two of SOCIETY_SPEC's cited siblings moved since C92 (`f0c82118`):

| Sibling | Delta since C92 | Section changed | SOCIETY_SPEC cites | Intersects? |
|---------|-----------------|-----------------|--------------------|-------------|
| `atp-adp-cycle.md` | +14/−2 (C119, #420) | §4.2 impl comment + **§7.1 MUST #6 scope note** | §4.2.1 → atp **§2.1/§2.2/§2.3/§2.4/§2** (mint/charge/discharge/slash) | **NO** — the C119 delta is in §7.1's normative-summary MUST #6 carve-out, not in §2.x |
| `mcp-protocol.md` | +1/−1 (C117, #422) | **§12 R7 MUST #6** wording refinement | §7.1 (L462) → mcp **§7.3** (signed reputation objects) + **§7.5** (propagation) | **NO** — the C117 delta is in §12's normative summary, not in §7.3/§7.5 |

Both sibling deltas are **disjoint from the sections SOCIETY_SPEC actually cites**. The inbound-cross-ref finder independently opened both live siblings and confirmed every cite resolves at current HEAD:

- atp-adp `§2.1` Minting (`:37`), `§2.2` Charging (`:69`), `§2.3` Discharging (`:124`), `§2.4` Slashing (`:170`) — all present, content matches SOCIETY_SPEC §4.2.1 L317's attribution.
- mcp `§7.3` MCP Actions as R7 Transactions (`:370`, signed reputation objects) + `§7.5` Cross-Society Witnessing / R7 Reputation Propagation (`:490`) — both present, matching SOCIETY_SPEC §7.1 L462's attribution.

**§A conclusion**: No regression. The C119/C117 sibling churn is the "MUST-vs-reference-impl normative-summary" class (see the C116-N1/C118-N1 lineage) confined to *their own* §7.1/§12 loci; it does not reach SOCIETY_SPEC's inbound cite targets. The frozen file's citations remain accurate against the moved siblings.

---

## §B — Fresh Delta Findings (3-lens finder sweep, refute-by-default)

**Method**: 3 finder lenses (internal coherence; inbound cross-ref accuracy; SDK/JSON fidelity) each run with an explicit refute-by-default mandate → 1 raw candidate → auditor adversarial re-verification → **0 CONFIRMED net-new spec defects.** Severity profile: **0 HIGH / 0 MED / 0 LOW / 1 INFO (refuted-to-INFO)**; class profile: **0 autonomous / 0 design-Q net-new / 1 cross-track re-confirmation (C92-N1, sharpened)**.

### REFUTED — internal-coherence candidate (formation action-name "mismatch")

The internal-coherence lens raised one candidate at HIGH: the §1.2.2 "Minimum Records" summary (L38 "Formation events (genesis/bootstrap/operational/**incorporation/secession/dissolution**)") and the §4.2.1 heading (L333 "incorporation, secession, dissolution") use *nominalized* forms, while the canonical §4.2.1 JSON action enum (L337) uses *verb* forms `genesis|bootstrap|operational|**incorporate_child|incorporated_by|secede|dissolve**`.

**Adversarial verification → REFUTED (overcall).** Three independent grounds:

1. **The file's §1.2.2 summary is uniformly nominalized/informal across ALL five record classes, by design.** L34 citizenship "(apply/grant/provisional grant/...)", L35 law "(**proposal/ratification/amendment/repeal**)" — nouns, vs the canonical verbs `propose|ratify|...`; L36 economic "(treasury **deposits/allocations/reclaims**; pool-supply **mints/slashes**)" — plural nouns, vs canonical `deposit|allocate|reclaim|mint|slash`. Formation is treated *identically* to law and economic. Singling out formation as a HIGH defect while the same noun-vs-verb pattern pervades the summary is internally inconsistent — and the finder **itself refuted this exact class for the law-action row** (L35 vs L287) before inconsistently confirming it for formation.
2. **L39 explicitly deprives §1.2.2 of canonicity.** "§4.2.1 gives the **canonical enumeration** of society-lifecycle event types … It is not the ledger's complete storage obligation." §1.2.2 is a signposted informal summary that *defers* to §4.2.1 for the authoritative action list. A summary that says "see §4.2.1 for the canonical form" cannot *contradict* §4.2.1; it points at it.
3. **The "incorporation" → `incorporate_child` + `incorporated_by` one-to-two collapse is a legitimate umbrella.** The summary rolls both directions of the incorporation relationship into the single umbrella noun "incorporation"; the canonical directional split lives in §4.2.1 exactly where L39 says it will. No reader is misled into treating "incorporation" as a wire action.

Recorded as **INFO (refuted)**, not autonomous-actionable: were one to *optionally* tighten the §1.2.2 summary for readability, it would be a whole-summary cosmetic pass (align all five rows to their canonical verbs), not a formation-specific fix — and it is expressly out of scope for an audit turn on a byte-frozen file. **No spec edit.**

### CLEAN — inbound cross-ref lens

All cross-references to the seven cited siblings resolve accurately at HEAD (see §A table + SAL §3.1/§3.4/§5.4, society-roles §2/§3/§4.1, ISP §2.1/§3/§5.1–§5.2/§6.2/§6.3, did-web4, t3-v3, SOCIETY_METABOLIC all re-confirmed). **No broken citation, no misattribution.**

### RE-CONFIRMED + SHARPENED — cross-track carry C92-N1 (SDK solo-founder path)

The SDK-fidelity lens confirmed **EXACT** matches for: §4.2.1 event-type strings + envelope vs `LedgerEventType`/`LedgerEntry` (society.py:89–116); §2.3 CitizenshipStatus vs `federation.py:91–108` (no `REJECTED`); the seven `BASE_MANDATORY_ROLES` (role.py:118–126). The only standing carry present in that surface is **C22-M3** (`type`↔`event_type`), unchanged.

**C92-N1 re-confirmed OPEN and sharpened.** `create_society()` (society.py:317–318) still carries the unconditional `if len(founders) < 2: raise ValueError("Society requires at least 2 founders")` guard (docstring `:300` "Requires at least 2 founders"; test `test_society.py:396` still asserts the raise), which categorically rejects the solo-founder genesis §1.3 L83 / §5.1 L409 now normatively endorse (grounded in ISP §2.1 SHALL-level). **Sharpening (net-new observation vs C92):** the SDK is not merely *lagging* — it ships a **half-built** solo path. `bootstrap_society_roles()` (role.py:291, exported in `__init__.py`, covered by ~20 tests in test_role.py + test_conformance.py) produces the 7 solo-founder role assignments, and **its own docstring (role.py:303–305) claims it "resolves the cross-language gap where the Python SDK's `create_society()` required `len(founders) >= 2`"** — but `create_society()` never calls it and still enforces `>= 2`. So the SDK is internally self-contradictory: an exported+tested helper documents a resolution that the actual society factory still blocks.

- **Fix shape (SDK-track, sharpened):** not merely "relax the guard" — *wire* `bootstrap_society_roles()` into a solo-founder branch of `create_society()` (or a `create_solo_society()` entry point) with UNANIMOUS quorum + ISP §2.1's ≥3-birth-witness handling, **and** correct the role.py:303–305 docstring so it does not claim a resolution the code does not yet deliver. **No spec edit** — the spec is authoritative and current. Routes to the SDK-track bundle (joins C50-B16–B19).

---

## §C — Carry Re-Verification (bidirectional; snapshot-presence-guarded; record-only)

All re-verified against current HEAD `900caca8`, re-reading the **current** sibling byte (C98 snapshot-presence-guard — distinguish "open + unmoved" from "silently resolved downstream"):

- **C50-B13 (Law Oracle name collision)** — **OPEN, unmoved.** §1.2.1 L24 still "Codified rules governing entity behavior and resource allocation"; society-roles §2.2 / SAL §3.1 (both byte-frozen since C92, verified) still bind "Law Oracle" to the publisher role. Operator DESIGN-Q bundle. (Was re-surfaced as C92-N2; no §B re-surface needed this round — locus unchanged.)
- **C50-B14 (citizenship revocability vs SAL §5.1)** — **OPEN; half-resolved on the spec side, unchanged since C92.** §2.4 L154 still frames current status as "derived state … the ledger event above is the normative record" (the shape B14 predicted); SAL (frozen) still "Permanent birth pairing; cannot be revoked." Closing it still needs the SAL-side normative wording. Operator DESIGN-Q bundle.
- **C50-B15 (law inheritance model)** — **OPEN, unmoved.** §3.2.1 L178 "extend but not contradict" vs SAL (frozen) conditioned-override model still in tension. Operator DESIGN-Q bundle.
- **C92-N1 (solo-founder SDK guard)** — **OPEN, sharpened** (see §B). SDK-track bundle.
- **C92-N3 / C50-B20 (id-scheme example strings)** — **OPEN, present.** L222 `citizen_lct_1`/`citizen_lct_2`, L237 `external_witness_lct`, L252 `parent_society_ledger_id` still non-canonical vs `lct:web4:`/`did:web4:`. C33 id-scheme bundle.
- **C22-M3 (`type`↔`event_type` snake/camel)** — present, SDK-track, unchanged.

**No carry resolved or hardened downstream since C92.** All movement is stillness — itself a verified state.

---

## §D — Disposition for C132 (paired remediation turn)

**There are NO autonomous spec defects to remediate.** §A: 21/21 held on a byte-frozen file, inbound cites re-verified accurate against the two moved siblings. §B: 1 candidate refuted, 0 net-new spec defects; the only substantive item is the sharpened cross-track C92-N1. §C: all carries OPEN, none newly actionable here.

- **C92-N1 (sharpened)** → **SDK-track** (wire `bootstrap_society_roles` into `create_society`'s solo branch + fix the over-claiming role.py docstring); no spec edit.
- **C50-B13 / B14 / B15** → **operator DESIGN-Q bundle**; not self-resolvable.
- **C92-N3 / C50-B20** → **C33 id-scheme bundle**; not self-resolvable.
- **C22-M3** → SDK-track snake/camel cluster.

**Recommendation**: C132 has no autonomous `SOCIETY_SPECIFICATION.md` remediation (record it as a no-op/carry-surface if the alternation lands a remediation turn with nothing operator-answered). Rotation advances to `dictionary-entities.md` (lineage C17→C52→C94→**C132**). No date/version bump for C131 (audit-only; the file's date banner is accurate to the last substantive edit, C51).

---

## §E — Method Notes (for the audit ledger)

1. **First fully-clean SOCIETY_SPECIFICATION delta (spec side).** C22 was heavy; C50 found the #252 remediation had introduced 9 defects; C51's 21-site remediation was clean but C92 still surfaced 1 net-new SDK-lag item. C131 surfaces **0** net-new. Combined with the byte-freeze, the file has fully converged on the spec side. Its open frontier is *entirely* off-file: operator DESIGN-Q (B13/B14/B15) and SDK-track (C92-N1 + C22-M3). Continued per-file re-auditing has reached the diminishing-returns floor here — the next yield requires the operator to answer the DESIGN-Q bundle or the SDK track to act.
2. **Refute-by-default caught a finder overcall on a byte-frozen file.** The internal-coherence lens confirmed a HIGH candidate (formation action names) that its *own* refutation logic (applied to the law-action row) should have demoted. Auditor-side adversarial re-verification is load-bearing precisely on frozen targets, where any "finding" is by definition either a long-standing intentional style or a false positive — never a fresh regression. The formation candidate was the file's uniform prose-summary style, explicitly de-canonicalized by L39. (Extends the standing "cross-doc/internal overcall" pattern — observation real, framing overstated — to the finder-vs-verifier boundary.)
3. **A "frozen" file's audit yield is on its siblings, not its bytes.** The only substantive surfaces this round were (a) the two moved siblings' cite-intersection (clean — deltas disjoint from cited sections) and (b) the SDK's evolving solo-founder path (C92-N1 sharpened from "lag" to "half-built + self-contradictory docstring"). Neither is fixable by editing the frozen spec. Confirms the wrap-method thesis: on a byte-stable target, §A is diff-what-moved + live-sibling re-read, and §B yield is the corpus-delta / cross-track surface.

---

*C131 verdict: file in good health, byte-frozen since C51, fully clean on the spec side (0 net-new autonomous defects — a SOCIETY_SPECIFICATION first). §A: 21/21 held; the two moved siblings' deltas (atp-adp C119, mcp C117) are disjoint from SOCIETY_SPEC's cited sections → inbound cites accurate. §B: 1 finder overcall refuted (formation prose-summary style, licensed by L39); C92-N1 re-confirmed and sharpened (SDK ships a half-built, self-contradictory solo-founder path). §C: all carries OPEN, snapshot-guarded, none newly actionable. No autonomous C132 spec work; rotation advances to dictionary-entities (C132).*
