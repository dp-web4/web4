# C92 — Second-Delta Re-Audit: SOCIETY_SPECIFICATION.md

**Date**: 2026-06-24
**Auditor**: Legion autonomous web4 track (slot 120010, v2 protocol)
**Target**: `web4-standard/core-spec/SOCIETY_SPECIFICATION.md` (481 lines, head `f0c82118`)
**Lineage**: C22 (first audit, PR #251) → C50 (first delta, `docs/audits/C50-society-specification-audit-2026-06-12.md`, PR #317) → **C51 remediation** (`958a5625`/#318, + pre-merge mini-audit fixes `9c2edd7e`, `9f5f6892`) → **C92 (this, second delta)**
**Staleness at audit**: 12 days since C51; no commit has touched the target since #318 (`git log 958a5625..f0c82118 -- <target>` empty).
**Method**: §A LEAD-direct re-verification of all C51 remediations + the **C56 token-by-token claim-vs-canonical check** for remediation-introduced regression (the failure mode C50 documented for #252); §B 6-lens multi-agent finder sweep (workflow `wf_fe543d2b-a20`) with refute-by-default adversarial verification; §C bidirectional carry re-verification against current HEAD.

---

## Verdict (summary)

- **§A**: **All 19 autonomous C51 findings + flagship R1 + carry-NEW-K HELD.** Every load-bearing cross-reference C51 introduced was verified **token-by-token accurate** against canonical (SAL §3.1/§3.4/§5.4, ISP §6.2/§6.3, society-roles §2/§2.2, atp-adp §2.1–§2.4, did:web4, SDK). **ZERO C51-introduced regressions.** The §A clean streak — which *broke at C50* when the #252 remediation was found to have introduced 9 defects — is **RESTORED**.
- **§B**: 6 finder lenses → 3 raw → **3 CONFIRMED / 0 REFUTED**. Only **1 is net-new** (solo-founder SDK guard, MEDIUM cross-track); the other 2 re-confirm standing carries (Law Oracle name collision = C50-B13, LOW; id-scheme example strings = C50-B20, INFO). The internal-coherence, SAL, and atp/metabolic lenses returned **empty** — independently corroborating §A.
- **§C**: design-Q carries **C50-B13 / B14 / B15 re-verified OPEN** against current HEAD (none resolved downstream; B14 shows partial spec-side movement toward its predicted resolution). Cross-track B16–B20 / B25 unchanged.
- **Net**: **0 autonomous spec defects this round.** The file is in good health post-C51. See §D for the C93 disposition (no autonomous spec remediation).

---

## §A — Prior-Finding Verification (C51 remediation held / regressed)

**Result: 21/21 HELD (19 autonomous + R1 + carry-NEW-K); 0 regressed.**

C50 flagged that the C22→#252 remediation introduced **nine** defects (R1 + B1, B2, B5, B7, B8, B11, B12, B26) — the largest remediation-introduced cluster in the C-series — and §D of C50 prescribed: a remediation-regression sweep must check each inserted claim against (a) the sections it cites, (b) the sections that cite it, (c) sister specs sharing its vocabulary. C92 applied that prescription to C51's own (larger) remediation. **Every claim verified accurate.** Load-bearing checks below; all line cites against head `f0c82118`.

### Flagship R1 (§1.2.5 rewrite) — HELD, citations accurate

C51 rewrote §1.2.5 (L55–62) to fix the C50-R1 regression (mis-cite of ISP §6.2 as the role-enumeration home + false protocol-enforcement claim). Verified token-by-token:

- **L60** "`society-roles.md` §2 enumerates seven base-mandatory roles — Sovereign, Law Oracle, Policy-Entity, Treasurer, Administrator, Archivist, and Citizen … (a single entity MAY fill several, down to a solo founder filling all seven)" → `society-roles.md:51` reads verbatim "Every Web4-compliant society MUST have these seven roles filled. A single entity MAY fill multiple roles … (e.g., a solo founder fills all seven — Sovereign + Law Oracle + Policy-Entity + Treasurer + Administrator + Archivist + Citizen …)". **EXACT** (role spelling "Policy-Entity" matches).
- **L62** "ISP §6.2 defines *semantic viability* (internal differentiation, witnessing capacity, externally grounded ATP referent) as GUIDANCE, and ISP §6.3 is explicit that the Web4 protocol does not adjudicate whether a society is 'real enough' — viability is discovered socially through first-contact outcomes (ISP §3)" → ISP §6.2 (`:328` "### 6.2 Minimum Viable Semantic Society", criteria `:330`–`:340`); the GUIDANCE/non-adjudication sentence is at ISP **§6.3** ("### 6.3 Implications", `:336`), `:342` "These are GUIDANCE, not protocol enforcement. The Web4 protocol does not adjudicate whether a society is 'real enough.' … via the first-contact protocol (§3)". **The §6.3 citation is correct** (the GUIDANCE text genuinely moved into §6.3 "Implications"; C51 cites it right). Restores ISP §6.3-faithful language.
- **L59** Quorum Policy = "table of **witness/attestation requirements per action type** (SAL §3.1), defined by the Law Oracle (SAL §5.4)" → SAL `:74` "A **Quorum Policy** (witness/attestation requirements per action type)" (under §3.1); "Quorum policy defined by Law Oracle" at SAL `:197`, which sits under "### 5.4 Witness" (`:195`). **Both citations accurate** (this is the C50-B8 fix folded into R1's rewrite). Note: §5.4 is the Witness subsection — structurally the "defined by Law Oracle" sentence lives there; the C51 citation matches.

### B1 (§1.2.2 SAL §3.4 record classes) — HELD, EXACT

L39 lists the SAL §3.4 record classes "**Birth Certificates**, **role pairings**, **delegations**, **law dataset digests**, **witness attestations**, and **auditor adjustments**" → `web4-society-authority-law.md:109` (under "### 3.4 Immutable Record (Ledger)", `:107`) reads the identical six-item list. "sal.law.update" → SAL `:111` emits `sal.law.update`. **EXACT.**

### B2 (witnesses+timestamp on law_change & economic; SAL-critical) — HELD

§4.2.1 blocks 2–3 now both carry `witnesses` + `timestamp` (L294–296, L312–314). L299 "Law changes are SAL-critical events (`sal.law.update` per SAL §3.4) and MUST carry witness co-signatures per the society's Quorum Policy (SAL §5.4)" → SAL `:300` "SAL-critical events (birth, delegation, law updates, auditor adjustments) MUST carry witness co-signatures meeting quorum"; SAL `:123` "see §5.4". **Accurate.**

### B11 (charge/discharge layer routing) + economic enum citations — HELD, EXACT

L317 "mint … occurs in the ADP state per `atp-adp-cycle.md` §2.1"; "slash … per §2.4"; "discharge is recorded on the R6 transaction that spends the ATP (§2.3)"; "charging is recorded as a standalone value-creation event (§2.2)" → verified against atp-adp-cycle.md: §2.1 "Minting (ADP Creation)" (`:37`, `:39` "mint tokens in the discharged (ADP) state"); §2.2 "Charging (ADP → ATP)" (`:69`, `:71` "through value creation"); §2.3 "Discharging (ATP → ADP)" (`:124`, `:126` / `:161` "discharge is an R6 action"); §2.4 "Slashing (ATP Destruction)" (`:170`). **All four section numbers + claims EXACT.** (Corrects the C50-B11 mislabeling — C51's routing is right.)

### B12 (§7.1 reputation envelope cite) — HELD

L462 now cites `mcp-protocol.md` §7.3 (signed reputation objects) + §7.5 (reputation-propagation rules) — no longer the §7.4 envelope. Consistent with the §7.1 lead at L458.

### B28 (did:web4 cross-ref) — HELD, EXACT

L52 "the LCT's standards-facing interop projection is a `did:web4` identifier — see `did-web4-method.md`" → did-web4-method.md `:19` "`did:web4` is the **interop face** of an LCT — the identifier-and-keys projection". **EXACT.**

### carry-NEW-K (bare type strings) + SDK shape claims — HELD

§4.2.1 type strings are all bare — `citizenship` (L270), `law_change` (L286), `economic` (L304), `metabolic` (L322), `formation` (L336) — matching SDK `LedgerEventType` values (society.py:92–96 `CITIZENSHIP="citizenship"` … `FORMATION="formation"`). §2.3 CitizenshipStatus claim → SDK `federation.py:94–98` = exactly `APPLIED, PROVISIONAL, ACTIVE, SUSPENDED, TERMINATED` (no `REJECTED`). **EXACT.** §4.2.1 "common envelope `{type, action, data, witnesses, timestamp}` (mirroring the SDK's `LedgerEntry`)" → SDK `LedgerEntry` (society.py:103–116) carries `event_type, action, data, timestamp, witnesses` (+ entry_id/amends/superseded_by). **Held** (the spec field `type` ↔ SDK `event_type` naming difference is the pre-existing snake/camel carry C22-M3, not a C51 regression — see §C).

### Other C51 autonomous fixes (B3, B4, B5, B6, B7, B9, B10, B21–B27) — HELD (spot-verified)

- B3/B4/B5: §2.4 (L136–154) + all five §4.2.1 blocks now use the single `{type, action, data, witnesses, timestamp}` envelope; citizenship action enum `apply|grant|provisional_grant|suspend|reinstate|terminate` (L271) with the action-to-status mapping (L281); §1.2.2 summary vocab (L34) consistent.
- B6: §6.3 Global Web4 Society relabeled "Witnessed (distributed …); the apex society has no parent, so the Participatory type of §4.1.3 … is structurally unavailable" (L449). HELD.
- B7: `token_type": "ATP|ADP"` restored (L308). B10/B24: formation enum adds `secede|dissolve` (L337) with the ISP §5.1–§5.2 note (L347); economic enum adds `mint|slash` (L305). B9/B21: §5.1 solo-founder + "conceptual minimum" qualifier (L408–409). B22: §4.3 allocation-vocabulary note (L400). B23: §4.2.2 uses `law_reference`/`witnesses` (L372, L381). B26: §1.2.5 demoted to `####` (L55). B27: §7.2/§7.3 routing notes (L466–471, L474). B28: did:web4 xref. **All present and accurate.**

**§A conclusion**: C51 was a +58-line-class remediation touching ~21 sites — exactly the size C50-§D warned "warrants its own mini-audit before merge." The C51 author **did** run that mini-audit (commits `9c2edd7e` "singles" and `9f5f6892` "disambiguate §1.2.5 Quorum Policy pin-cites (pre-merge mini-audit catch)"). The result is visible here: **a remediation of comparable size to the one that introduced 9 defects introduced 0.** This is the C50-§D lesson working as designed.

---

## §B — Fresh Delta Findings

**Method**: 6 finder lenses (internal coherence, SAL, ISP+society-roles, atp-cycle+metabolic, SDK society/federation/role, JSON-shapes+did:web4/MCP) → 3 raw → per-finding refute-by-default adversarial verification → **3 CONFIRMED / 0 REFUTED**. The internal, SAL, and atp-metabolic lenses returned **empty findings** (corroborating §A). Severity profile: **0 HIGH / 1 MEDIUM / 1 LOW / 1 INFO**; class profile: **0 autonomous / 0 design-Q / 3 cross-track** (one of which, B13, is the re-surfaced design-Q carry).

### MEDIUM — cross-track (NET-NEW)

#### C92-N1 — SDK `create_society` rejects the solo-founder genesis the spec now normatively endorses (post-C51)

`society.py:317–318` `if len(founders) < 2: raise ValueError("Society requires at least 2 founders")` (docstring `:300` "Requires at least 2 founders") **categorically cannot instantiate** the solo-founder path that C51 made normative in the spec: §1.3 L83 ("Genesis does not require multiple founders … The solo founder fills all seven base-mandatory roles, constituting a 'society-of-one'") and §5.1 L409 ("… or 1 solo founder, per the self-bootstrapped genesis path in §1.3"), grounded in ISP §2.1 "Self-Bootstrapped Genesis (Solo Founder)" (SHALL-level: founder LCT, keypair, charter, treasury, ≥3 birth witnesses MAY be founder-controlled). **This is the inverse of C50-B9** (which flagged only that the spec *prose* was silent on the solo path): C51 added the prose, and the SDK `<2` guard now lags the now-normative spec. **The spec is correct; the canonical SDK is behind it.** Fix shape (SDK-track): relax the guard to allow `len(founders) == 1`, defaulting UNANIMOUS quorum and genesis-witness handling for the society-of-one case per ISP §2.1's ≥3-birth-witness rule. **No spec edit.** Surface at the SDK's next pass.

### LOW — cross-track (RE-CONFIRMS standing design-Q carry C50-B13)

#### C92-N2 — "Law Oracle" names two different things (rules-corpus vs publisher-role); §1.2.5 conflates them

§1.2.1 (L23–24) defines Law Oracle as "**Codified rules** governing entity behavior and resource allocation" (a structural rules-corpus a society must *have*); society-roles.md §2.2 (`:71`–`:86`, "publisher of facts about the law, not a decision-maker") and SAL §3.1 (`:73` "A **Law Oracle** LCT (publishes …)") bind the same name to a role-bearing entity. §1.2.5 (L59–60) then treats §1.2.1's "Law Oracle" as the same Law Oracle that society-roles §2 lists among the seven *roles*. Telling detail: §1.2.5's counterpart pattern gives **distinct** names to every other structure/role pair — "the **Treasurer** role is the role-bearing counterpart to §1.2.3's **Treasury**", "the **Sovereign** role … to §1.2.4's **Society LCT**" — but Law Oracle gets no such disambiguation because the name is identical. **This is the standing operator design-Q C50-B13, re-verified OPEN and unchanged.** Routed to the operator DESIGN-Q bundle (rename §1.2.1's element, e.g. "Law Corpus", reserving "Law Oracle" for the role; or add an explicit "same name intentionally spans structure and operating role" note). **NOT autonomously self-resolved.**

### INFO — cross-track (RE-CONFIRMS standing carry C50-B20 / C33 bundle)

#### C92-N3 — Placeholder LCT-identifier example strings don't match canonical `lct:web4:` / `did:web4:` formats

`citizen_lct_1`/`citizen_lct_2` (L222), `external_witness_lct` (L237), `parent_society_ledger_id` (L252) match neither LCT spec `lct:web4:mb32:`/`lct:web4:society:` (LCT-linked-context-token.md:64/:76) nor did:web4's RFC-4122 UUID `lct-id` (did-web4-method.md:38/:46). **This is C50-B20, re-verified present** — routes to the **C33 id-scheme DESIGN-Q bundle** (whole-spec example-identifier normalization). No local fix; not resolvable here.

---

## §C — Carry Re-Verification (bidirectional; record-only, NO self-resolution)

All re-verified against current HEAD `f0c82118`:

- **C50-B13 (Law Oracle name collision)** — **OPEN, unchanged.** §1.2.1 L24 still "Codified rules"; society-roles §2.2 / SAL §3.1 still bind the name to a role. Re-surfaced by §B as C92-N2. Operator DESIGN-Q bundle.
- **C50-B14 (citizenship revocability vs SAL §5.1)** — **OPEN; partial spec-side movement toward the predicted resolution.** SAL `:181` "Permanent birth pairing; **cannot be revoked**" unchanged; §2.3 Termination lifecycle (L120–132) unchanged. **But** §2.4 L154 now frames current status as "**derived state** … the ledger event above is the normative record" — exactly the "pairing permanent as historical fact, status revocable" shape C50-B14 predicted. The design-Q is now *half-resolved on the spec side*; closing it still needs SAL-side normative wording distinguishing the permanent *pairing event* from the revocable *status*. Operator DESIGN-Q bundle.
- **C50-B15 (law inheritance model)** — **OPEN, unchanged.** §3.2.1 L178 "Local laws can extend but not contradict inherited laws" vs SAL `:128` "child society inherits parent law by default; **override** only by explicit Interpretation or Norm with higher or equal authority and no parent hard-conflict" + `:129` conflict order ranking "explicit child overrides … → parent norms". The extend-not-contradict vs conditioned-override models still conflict. Operator DESIGN-Q bundle.
- **C50-B16–B19 (SDK ledger-conformance / lifecycle-graph / fractal-citizenship / merge_law)** — SDK-track, unchanged; **C92-N1 (solo-founder guard) joins this SDK-track bundle** as fresh evidence.
- **C50-B20 (id-scheme example strings)** — re-confirmed present as §B C92-N3; C33 id-scheme bundle.
- **C50-B25 (SDK dual role taxonomies)** — SDK-track, unchanged.
- **Minor §A residue (record-only, cross-track)**: (a) spec envelope field `type` ↔ SDK `LedgerEntry.event_type` (carry-C22-M3 snake/camel cluster, not a C51 regression); (b) SDK `LedgerEventType` enum comments use stale action vocab (society.py:92 "# join/leave/suspend/reinstate", :94 "# allocate/deposit/reclaim" — pre-C51 verbs, no mint/slash) — an SDK-doc nit, action strings are free-form so no behavioral conflict. Both SDK-track, surface at SDK's next pass.

---

## §D — Disposition for C93 (paired remediation turn)

**There are NO autonomous spec defects to remediate.** All three §B-confirmed findings are cross-track or standing design-Q:

- **C92-N1** (solo-founder SDK `<2` guard) → **SDK-track** (relax `create_society`); no spec edit.
- **C92-N2** (= C50-B13 Law Oracle collision) → **operator DESIGN-Q bundle**; not self-resolvable.
- **C92-N3** (= C50-B20 id-scheme examples) → **C33 id-scheme bundle**; not self-resolvable.
- §A: 21/21 held, 0 regressions — nothing to fix.

**Recommendation**: C93 has no autonomous `SOCIETY_SPECIFICATION.md` remediation. Record C93 as a **no-op/carry-surface** (the file is healthy post-C51; the cross-track + design-Q items are already on their respective ledgers), and let the rotation **advance to the next file** — `dictionary-entities.md` (next-oldest in the active set at C52/C53, lineage C17→C52→**C94**). No date/version bump for C92 (audit-only; the file's date banner `2026-06-12` is accurate to the last substantive edit, C51).

---

## §E — Method Notes (for the audit ledger)

1. **The C50-§D pre-merge-mini-audit prescription works.** C50 introduced the rule "remediation PRs above ~+58 lines of new normative prose warrant their own mini-audit before merge." C51 was exactly that size and the author ran the mini-audit (visible as commits `9c2edd7e`/`9f5f6892`). C92 confirms the payoff: **a same-class remediation introduced 0 defects where #252 introduced 9.** Recommend promoting "large-remediation → pre-merge mini-audit" from a method note to standing remediation practice.
2. **An empty net-new result is a real result.** The internal/SAL/atp-metabolic lenses returned nothing; the only net-new finding is one SDK-lag item. After two consecutive heavy passes (C22 + C50) and a clean large remediation (C51), `SOCIETY_SPECIFICATION.md` has converged on the spec side. The remaining open items are all *cross-doc model decisions* (B13/B14/B15) and *SDK lag* (B16–B19 + N1) — neither is fixable by re-auditing this file. Continued per-file re-auditing has diminishing returns here until the operator DESIGN-Q bundle is addressed.
3. **Remediation that resolves one side of a gap can expose the other (C92-N1).** C50-B9 flagged the spec prose was silent on solo-founder; C51 added the normative prose; that *created* a new spec-vs-SDK contradiction (the SDK `<2` guard) that did not exist as a finding before, because before C51 the spec didn't assert the solo path. A delta re-audit must check whether each prior remediation's *newly-asserted* normative claim has an implementation counterpart — not only whether the edit itself is internally sound.

---

*C92 verdict: file in good health. C51's 21-site remediation HELD with zero regressions and token-by-token-accurate citations — the §A clean streak (broken at C50) is restored. §B: 0 autonomous, 1 net-new SDK-lag (cross-track), 2 standing-carry re-confirmations. No autonomous C93 spec work; rotation advances to dictionary-entities (C94). The file's open frontier is entirely operator-DESIGN-Q (B13/B14/B15) and SDK-track (B16–B19 + N1).*
