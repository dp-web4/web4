# C164 — Fourth-Delta Re-Audit: SOCIETY_SPECIFICATION.md

**Date**: 2026-07-09
**Auditor**: Legion autonomous web4 track (slot `web4-20260709-120036`, v2 protocol)
**Target**: `web4-standard/core-spec/SOCIETY_SPECIFICATION.md` (481 lines, head `b8740803`)
**Lineage**: C22 (first audit, PR #251) → C50 (1st delta, PR #317) → **C51 remediation** (`958a5625`/#318, + pre-merge mini-audit `9c2edd7e`/`9f5f6892`) → C92 (2nd delta) → C131 (3rd delta, `286e5600`/#443 — first fully-clean spec-side delta) → **C164 (this, 4th delta)**
**Rotation**: audit-side round-robin WRAPPED (mrh-tensors was last, C162 audit → C163 remediation `b8740803`/#491) → back to `SOCIETY_SPECIFICATION.md`, the oldest target.
**Staleness at audit**: **byte-frozen since C51.** `git rev-parse HEAD:<target>` = `4578196073cd…` = the identical blob at C92's head `f0c82118` and C131's head `900caca8`. `git log 900caca8..HEAD -- <target>` is empty. Untouched ~27 days.
**Method**: §A byte-freeze verification + **corpus-delta re-verification against the one moved sibling** (C56 claim-vs-canonical, token-by-token, re-read at the *live* byte). §B **bounded single-pass** finder review (policy-reviewer-constrained — see §E), refute-by-default, with a mandatory novelty check against the full prior-audit corpus before any candidate is called net-new. §C bidirectional carry re-verification under the C98 snapshot-presence guard and the C146 path-provenance guard.

---

## Verdict (summary)

- **§A**: **CLEAN.** The target is byte-frozen, so C92's token-by-token verification of all 21 C51 findings holds by construction *within* the file. Exactly **one** of the eight cited siblings moved since C131: `atp-adp-cycle.md` (`256ab51d`, C151, #477), and its delta lands in **§2.4 — a section SOCIETY_SPEC §4.2.1 L317 cites by number.** Unlike C131 (where both movers' deltas fell in *uncited* sections and were clean by construction), this intersection had to be **read**. Result: the intersection is **section-level but claim-level disjoint** — C151 reworded only the *scope clause of the transfer-conservation invariant*, a clause SOCIETY_SPEC never cites, restates, or relies on. L317's actual reliance ("slash → supply destroyed") is on §2.4 text C151 left **byte-identical**. **No regression.**
- **§B**: **0 net-new spec defects.** Cross-ref lens: ~30 cites across 9 target files, **0 mismatches**. Enumeration lens: 3 closed-list claims re-derived from ground truth, all **EXACT**. Two candidates were raised and **both were REFUTED as already-recorded**, not net-new (§B-1, §B-2). One **instrument error** in the auditor's own verifier was caught by baselining (§B-3).
- **§C**: 6 standing carries **re-verified OPEN** at HEAD (none resolved downstream; path provenance HOLDS on all). **One net-new class-a finding — and it is a defect in the audit *ledger*, not in the spec**: a C92-recorded cross-track item was never promoted into the carry ledger and **vanished from C131 entirely**. Restored here as **C164-N1**.
- **Net**: **0 autonomous spec defects — the SECOND consecutive fully-clean SOCIETY_SPECIFICATION delta** (after C131's first). **C165 is therefore a declared NO-OP on the spec side.** The file's entire open frontier is operator-DESIGN-Q (C50-B13/B14/B15) and SDK-track (C92-N1, C164-N1, C22-M3).

---

## §A — Prior-Finding Verification (byte-freeze + the one moved sibling)

**Result: 21/21 C51 findings HELD by construction; the single cited-section intersection re-verified CLEAN.**

### Byte-freeze

`git diff 958a5625 HEAD -- web4-standard/core-spec/SOCIETY_SPECIFICATION.md` is empty; the blob hash at HEAD equals the blob at both prior audit snapshots. C92 verified all 21 C51 findings (19 autonomous + flagship R1 + carry-NEW-K) token-by-token against canonical with zero regressions, and C131 re-affirmed them. With no byte changed, there is no new prose *within* the target to re-verify.

### The real §A surface: corpus delta (siblings that moved)

SOCIETY_SPEC cites eight siblings. All eight were diffed against C131's head `900caca8`:

| Cited sibling | Cites | Commits since C131 | Status |
|---|---|---|---|
| `inter-society-protocol.md` | 5 | 0 | frozen |
| **`atp-adp-cycle.md`** | **4** | **1** — `256ab51d` (C151, #477) | **MOVED — lands in a cited section** |
| `web4-society-authority-law.md` | 3 | 0 | frozen |
| `society-roles.md` | 3 | 0 | frozen |
| `SOCIETY_METABOLIC_STATES.md` | 3 | 0 | frozen |
| `mcp-protocol.md` | 2 | 0 | frozen |
| `t3-v3-tensors.md` | 1 | 0 | frozen |
| `did-web4-method.md` | 1 | 0 | frozen |

### The C151 intersection — section-level hit, claim-level miss

C151 (`256ab51d`) changed exactly one line of `atp-adp-cycle.md`, inside §2.4's "Supply accounting" note:

```diff
- > (`initial == final + fees`), which scopes only ATP→ADP transfers — a destruction
+ > (`initial == final + fees`), which scopes only ATP transfers between entities (§6.3) — a destruction
```

SOCIETY_SPEC §4.2.1 **L317** cites `atp-adp-cycle.md` §2.4 by number:

> …and **slash** (supply destroyed per `atp-adp-cycle.md` §2.4); both are witnessed, ledger-recorded events that change total supply rather than move existing tokens.

**This is the surface that C131 did not have** (its two movers landed in uncited sections). Verified token-by-token against the **live** post-C151 sibling:

| L317 claim | Live §2.4 text | Verdict |
|---|---|---|
| "slash (supply destroyed …)" | `:212` "Slashing **destroys** ATP: the slashed amount is removed from the society's `total_supply` (§3.1) rather than discharged to ADP." | **EXACT** — and **untouched by C151** |
| "witnessed, ledger-recorded" | `:206` `record_slashing_event(violator, slashed, evidence, witnesses)` | **HELD** |
| "change total supply rather than move existing tokens" | `:212–213` removal from `total_supply`; "an intended supply reduction" | **HELD** |

**The reworded clause is the transfer-conservation invariant's *scope*.** SOCIETY_SPEC never cites, quotes, or depends on `initial == final + fees` anywhere in the file (`grep "initial == final"` → 0 hits in the target; the only corpus consumers are `atp-adp-cycle.md:214` itself and the `t3-v3-tensors.md:640` anchor, which C151's own remediation doc records as re-verified). **L317's reliance and C151's edit are disjoint.** No regression, no cross-track defect raised against C151.

The other three atp-adp cites re-verified at the live byte: §2.1 "Societies mint tokens in the discharged (ADP) state" (`:39`) ↔ "minting occurs in the ADP state" **EXACT**; §2.3 "ATP discharges through R6 transactions" (`:126`) ↔ "discharge is recorded on the R6 transaction that spends the ATP" **HELD**; §2.2 "Charging (ADP → ATP)" via value creation (`:69`) ↔ "charging is recorded as a standalone value-creation event" **HELD**. "society's monetary authority" ↔ §2.1 `"authority": "lct:web4:authority:monetary"` + §6.1 "Monetary Authority" **HELD**.

**Forward note (recorded, not raised):** C151's new anchor `(§6.3)` resolves to `### 6.3 Transfer Fees` (`:593`), which is where the `fees` term of the invariant is actually defined and where fee-recycling is said to preserve total supply. The anchor is correct. This is atp-adp's own surface, not SOCIETY_SPEC's; no action.

**§A conclusion**: no regression. The one genuine unknown that justified this turn is resolved in the negative.

---

## §B — Net-New Finder Sweep (bounded single-pass, refute-by-default)

**Result: 0 net-new spec defects.** Two candidates raised; **both refuted as pre-recorded**. Both refutations were made by *novelty check against the prior-audit corpus* — the candidates were substantively real, but not new, and reporting them as net-new would have inflated this turn's yield.

### Lens 1 — inbound/outbound cross-reference resolution at live HEAD: **CLEAN**

~30 distinct cites across 9 target files, each opened at HEAD and checked for (a) section number/title existence and (b) claim support. **Zero mismatches.** Two closest calls were self-refuted: L62 attributes "GUIDANCE" to ISP §6.2 while the literal label sits in §6.3 (valid prose-summary spanning §6.2's criteria + §6.3's disposition, explicitly licensed by the target's L39); L458's parenthetical echoes mcp §1.1's title rather than §7's (the substantive claim — envelope, reputation propagation — is accurate in §7).

### Lens 2 — enumeration (re-derive every closed-list claim from ground truth)

Per [[feedback_enumeration_and_grep_hypotheses]] (born C162): a "N of X" claim's **count** is its own lens; prior passes tested these claims' *math* and *values*, never re-derived their *membership* from ground truth.

| Claim | Ground truth | Verdict |
|---|---|---|
| L83 "solo founder fills all **seven** base-mandatory roles (`society-roles.md` §2)" | `society-roles.md:51` enumerates Sovereign + Law Oracle + Policy-Entity + Treasurer + Administrator + Archivist + Citizen = **7**; §2.1–§2.7 headings corroborate | **EXACT** |
| L281 action-to-status mapping → **5** statuses | SDK `CitizenshipStatus` (`federation.py:94–98`) set-equality with spec §2.3 statuses | **EXACT (set-equal)** |
| §4.2.1 **5** ledger event types | SDK `LedgerEventType` (`society.py:92–96`) set-equality with §4.2.1 `"type"` strings | **EXACT (set-equal)** |

### §B-1 — CANDIDATE **REFUTED (not net-new)**: SDK `LedgerEventType` enum comments carry stale action vocab

The enumeration lens surfaced that `society.py:92` comments `CITIZENSHIP` as `# join/leave/suspend/reinstate` (neither `join` nor `leave` appears anywhere in SOCIETY_SPEC; the §4.2.1 vocabulary is `apply|grant|provisional_grant|suspend|reinstate|terminate`), and `:94` comments `ECONOMIC` as `# allocate/deposit/reclaim` — omitting `mint` and `slash`, which **C51 itself added** to L305/L317.

Refutation attempts: (1) `action` is a free-form `str` (`society.py:112`), filtered only by equality (`:145`) — the comments are **non-normative hints, not validation**, so there is no behavioral conflict. (2) `LAW_CHANGE`'s comment `# propose/ratify/amend/repeal` matches §4.2.1 exactly, and `society.py:112`'s own field example (`"grant", "suspend", "allocate", "ratify"`) is entirely valid — only 2 of 5 member comments drift. (3) **Decisive**: novelty check — **C92 §A already recorded this**, at both loci, with the same "pre-C51 verbs, no mint/slash" diagnosis and the same free-form-field severity reasoning.

**Verdict: REFUTED as net-new. Substantively real, previously recorded.** It is, however, the subject of the §C ledger finding below.

### §B-2 — CANDIDATE **REFUTED (not net-new)**: `role.py` docstring over-claims resolution of C92-N1

`role.py:303–305` states its solo-founder helper "resolves the cross-language gap where the Python SDK's `create_society()` required `len(founders) >= 2`" — yet `society.py:317–318` still raises `ValueError("Society requires at least 2 founders")`, unchanged since `55e38608` (2026-03-17), and `create_society()` remains the **only** genesis entry point. The helper adds a parallel role-assignment path; it does not open the genesis guard.

Refutation attempts: (1) no alternative genesis function exists — the over-claim is real. (2) **Decisive**: novelty check — **C131 §D already routes exactly this**: "C92-N1 (sharpened) → SDK-track (wire `bootstrap_society_roles` into `create_society`'s solo branch + **fix the over-claiming role.py docstring**)".

**Verdict: REFUTED as net-new. Already carried under C92-N1 (sharpened).**

### §B-3 — Method note: the auditor's own verifier silently over-matched

A scripted SDK-fidelity check compared spec `"type"` strings to `LedgerEventType` and reported **3 spurious spec-only members** (`confined`, `participatory`, `witnessed`) — a red result that, taken at face value, would have been filed as a spec/SDK divergence.

Baselining located the fault **in the instrument**: the regex scraped the whole 481-line file, capturing L220/L235/L250 — the `"type"` discriminator of the **ledger-visibility** examples in §4.1 (Confined / Witnessed / Participatory), a different discriminator entirely. Re-scoped to §4.2.1 (L261–348), the check returns **exact set equality**.

Direct application of [[feedback_enumeration_and_grep_hypotheses]] §3: *a tight grep is a silent-failing hypothesis — and so is your verifier.* A green result from an unbaselined instrument is worthless; **so is a red one.** C163 caught a silently-failing checker by baselining it on the unmodified artifact; C164 caught a silently-**over**-matching one by locating its hits before believing them.

### Confirmatory lenses (policy-reviewer-scoped: quick look, not deep excavation)

Internal coherence and SDK fidelity re-check a byte-identical artifact whose defects would have been caught at C51/C92/C131. Both returned **clean**; SDK set-equality is shown above. No fresh excavation performed, per §E.

---

## §C — Carry Re-Verification (bidirectional; snapshot-presence + path-provenance guarded)

All re-verified against HEAD `b8740803`, re-reading the **current** sibling byte and **re-running each carried finding's grep at live HEAD** (C146: a carried finding's recorded FILE PATH can be wrong).

- **C50-B13 (Law Oracle name collision)** — **OPEN, unmoved.** Target L24 still defines "Law" as "Codified rules governing entity behavior and resource allocation"; `society-roles.md:71` (`### 2.2 Law Oracle`) still binds the name to the publisher role. Operator DESIGN-Q bundle.
- **C50-B14 (citizenship revocability vs SAL §5.1)** — **OPEN, unmoved.** Target L154 still frames current status as derived state. **Path provenance re-verified**: the SAL text "Permanent birth pairing; **cannot be revoked**." is at `web4-society-authority-law.md:181`, which falls under the `### 5.1 Citizen (Genesis, Immutable)` heading at `:180` — **C131's "SAL §5.1" citation HOLDS.** Operator DESIGN-Q bundle.
- **C50-B15 (law inheritance model)** — **OPEN, unmoved.** Target `:178` "Local laws can extend but not contradict inherited laws" vs SAL's conditioned-override model. Operator DESIGN-Q bundle.
- **C92-N1 (solo-founder SDK guard)** — **OPEN, unmoved.** `society.py:317–318` guard live and byte-unchanged since 2026-03-17. The `role.py` docstring **claims** the gap is resolved (§B-2) but `create_society()` still rejects a solo founder — the carry is **half-closed, and the half that is closed is the one that does not gate genesis**. Snapshot-presence guard fired correctly here: a carry that *appears* resolved downstream is not. SDK-track bundle.
- **C92-N3 / C50-B20 (id-scheme example strings)** — **OPEN, present.** `citizen_lct_1`/`citizen_lct_2` (L222), `external_witness_lct` (L237), `parent_society_ledger_id` (L252) still non-canonical vs `lct:web4:` / `did:web4:`. C33 id-scheme bundle.
- **C22-M3 (`type` ↔ `event_type`)** — **OPEN, present** (`society.py:111`). SDK-track.

**No carry resolved or hardened downstream since C131.**

### C164-N1 — NET-NEW (class-a, **ledger-completeness**, not a spec defect)

**Finding**: C92 §A recorded a two-item "minor residue (record-only, cross-track)" bullet:
> (a) spec envelope field `type` ↔ SDK `LedgerEntry.event_type` … (b) SDK `LedgerEventType` enum comments use stale action vocab (`society.py:92` "# join/leave/suspend/reinstate", `:94` "# allocate/deposit/reclaim" — pre-C51 verbs, no mint/slash) … Both SDK-track, **surface at SDK's next pass**.

Item **(a)** was promoted into the carry ledger and survives verbatim in C131 §C as **C22-M3**. Item **(b)** was **never promoted, and is absent from C131 entirely** (`grep -rn "join/leave\|allocate/deposit/reclaim" docs/audits/` → hits in `sal-…`, C22, C23, C50, C92; **zero hits in C131**). It was recorded once, in an §A prose bullet, and silently fell out of the ledger at the next delta.

**Verified still live at HEAD**: `society.py:92`/`:94` unchanged since `759eaefa` (2026-04-17); C51 subsequently added `mint|slash` to the spec (L305/L317) and did not update the SDK comments, so the divergence has **widened** since it was recorded.

**Why this is the finding that matters this round.** The spec is clean; the *audit trail* is not. An item recorded in §A prose but never promoted into §C's ledger is invisible to the next delta, which reads the ledger — not the prior doc's §A. That is a systematic failure mode, not a one-off: C160's lesson was that a completeness claim must be proven by **re-deriving the bounded set from ground truth**. Here the bounded set is "cross-track items this file owes," and re-deriving it from the C92 *text* (rather than the C131 *ledger*) is what surfaced the gap.

**Disposition**: **RESTORED to the standing ledger by this document.** Per the C163 governance ruling, C131 is **not** retro-edited — the omission is recorded here and the carry is live again in the current ledger. Severity **LOW** (non-normative comments on a free-form `str` field; no behavioral conflict). Routed **SDK-track**, to be bundled with C92-N1 and C22-M3 at the SDK's next pass.

---

## §D — Disposition

**There are NO autonomous spec defects to remediate.** §A: 21/21 held on a byte-frozen file; the sole cited-section sibling intersection re-verified clean at the live byte. §B: 2 candidates, both refuted as pre-recorded; 0 net-new. §C: 6 carries re-verified OPEN; 1 net-new **ledger** finding, remediated in place by restoration.

- **C165 = declared NO-OP on the spec side** (precedent: C131→C132's "no autonomous spec remediation"; C155/C161 no-op declarations). Zero bytes of `SOCIETY_SPECIFICATION.md`, any sibling, any `.ttl`, any SDK source, any schema, or any test vector were mutated by this turn.
- **Rotation advances** to `dictionary-entities.md` (lineage C17 → C52 → C94 → C132 → next).

**Standing frontier for this file** (nothing autonomously actionable):
| Item | Class | Route |
|---|---|---|
| C50-B13, C50-B14, C50-B15 | operator DESIGN-Q | operator memo (do NOT self-apply) |
| C92-N1 (guard + over-claiming docstring) | SDK-track | SDK next pass |
| **C164-N1** (enum-comment stale vocab) | SDK-track | SDK next pass — **restored carry** |
| C22-M3 (`type`↔`event_type`) | SDK-track | SDK next pass |
| C92-N3 / C50-B20 (id-scheme examples) | C33 id-scheme bundle | cross-cutting |

---

## §E — Method & Governance Notes

1. **The policy reviewer bounded §B, and was right to.** The proposed scope included a 4-lens multi-agent finder sweep. The reviewer ruled that a finder swarm on a byte-frozen, previously-fully-clean file *is itself* the "manufacture findings to fill the session" risk the C163 proportionality ruling warns against, and constrained §B to a single pass: two active lenses (cross-ref, enumeration) + two confirmatory looks. **Both refuted candidates came from the active lenses; a larger sweep would have produced more refuted candidates, not more findings.**

2. **A cited-by-number section is not a relied-upon claim.** The C151 intersection looked like the sharpest §A surface in four deltas — a moved sibling, landing in a section the frozen file cites explicitly. It resolved clean because *citation granularity ≠ dependency granularity*: L317 cites §2.4 wholesale but relies on one sentence within it, and C151 edited a different sentence. **The check that decides a cite-intersection is "what does the citing text actually assert," not "did the cited section change."** Recording this so the next pass does not re-open it as though unexamined.

3. **Refute-by-default paid twice, on the auditor's own best candidates.** Both §B candidates were substantively real and would have read as credible net-new findings. Both died on a **novelty check against the prior-audit corpus** — the cheapest, most-skipped refutation. [[feedback_refute_your_best_finding]] generalizes: *before asking "is this true," ask "is this new."*

4. **Baseline the instrument, in both directions.** C163 learned that a silently-failing checker must be baselined on the pre-change artifact before a green result is trusted. C164 adds the mirror: an over-matching checker must have its **hits located** before a red result is trusted (§B-3). A verifier's output is evidence about the verifier until proven otherwise.

5. **§A-prose ≠ ledger.** The one net-new finding of this turn is that a cross-track item recorded in C92's §A prose never reached §C's ledger and vanished at C131. **Items recorded anywhere other than the carry ledger do not survive the next delta.** Any future audit that records a "minor residue / record-only" item in prose MUST promote it into §C, or it is lost.

---

*C164 verdict: `SOCIETY_SPECIFICATION.md` is byte-frozen and in good health — the **second consecutive fully-clean spec-side delta**. §A: 21/21 held; the single moved sibling's delta (atp-adp §2.4, C151) intersects a cited section but is disjoint from the claim SOCIETY_SPEC relies on. §B: ~30 cites resolve, 3 enumerations exact, 2 candidates raised and both refuted as already-recorded, 1 auditor instrument error caught by baselining. §C: 6 carries OPEN, path provenance holds; **1 net-new class-a finding — a C92 cross-track item that was dropped from the carry ledger — restored here**. C165: declared no-op. Zero mutation.*
