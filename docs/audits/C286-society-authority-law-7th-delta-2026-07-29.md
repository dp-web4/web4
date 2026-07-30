# C286: web4-society-authority-law.md (SAL) — Seventh Delta Re-Audit

**Date**: 2026-07-29
**Auditor**: Autonomous session (legion-web4-20260729-180011)
**Document**: `web4-standard/core-spec/web4-society-authority-law.md` (SAL, 419 lines, blob `0849ebbe`)
**Prior audit**: C246 (`docs/audits/C246-society-authority-law-6th-delta-2026-07-22.md`, merged #564, commit `a79a80cf`)
**Prior remediation**: C59 / PR #330 (`0d756773`)
**Window**: `a79a80cf..HEAD` (`8b0b133d`) — 46 commits, **9** in `hub/`

**Lineage**: C16 → C21 → C23 → C58 → C98 → C134 → C170 → C208 → C246 → **C286**.

---

## Framing

SAL is byte-frozen at blob `0849ebbe` and has been since `1354e4c2` (#523, 2026-07-14) — **15 days**,
not the 47 that authorized C282's §A collapse. The collapse is still legitimate here, but on a
different warrant: **C208** read the #523 diff and established it was purely additive with both hunks
(the L230 boundary and the L270 triple list) sitting outside all ten C59-remediated sites — "the C98
site-table stands verbatim" — and **C246** re-verified the freeze. §A therefore rests on the
**C208+C246 chain**, and does not re-derive the C59 remediation a sixth time.

The substance of this pass is §B, and it was set by a single observation made **before** the sweep:

```
$ for f in C23 C58 C98 C134 C170 C208 C246; do grep -ci 'hub-lib\|hub/hub\|hub-daemon' docs/audits/$f-society-authority-law*.md; done
0 0 0 0 0 0 0
```

**No SAL pass has ever read `hub/`** — across seven audits spanning C16→C246. The bare-word `hub`
hits in C134/C170/C208/C246 are all `hub-law-schema.md` / `hub-law.ttl`, *documents* SAL cites at
L234/235/238. The running Rust law engine has never been gated. This is the C280 (`hub/` unread in 7
society-spec passes) and C284 (`ledgers/` unread in 7 metabolic passes) blind-spot class, on the one
spec in the corpus whose subject matter *is* society law.

**Counts**:
- **§A**: freeze verified by construction (`git diff 1354e4c2..HEAD` = **0 lines**; 0 encoding
  artifacts; `hasEffector` and `respondedBy` grep-count = 1 each). C59-rem **10/10 HELD** via
  C208+C246. All standing carries re-verified against **live-HEAD** referents — 0 closed, 0 regressed.
- **§B**: **0 net-new defects on SAL — 6th consecutive fully-clean SAL delta** (C98, C134, C170, C208,
  C246, C286). The `hub/` gate returned **GENUINE MIRROR, ADMITTED — and it diverges**, but the
  divergence indicts the *implementation*, not the spec. 1 MEDIUM routed (**C286-N1**), 1 INFO routed
  (**C286-N2**), 1 status note (**C286-N3**), 4 candidates DECLINED with recorded reasons, 4 refutations.
- **§C**: **ZERO autonomous-actionable, ZERO mutation of any kind.** SAL is correct throughout.

---

## §0. Pre-registered genuine-mirror criterion

*Written before any candidate file was opened, per method carry v7. M3 is C284's wording verbatim —
an earlier draft used a "would it indict the spec" test, which the policy review correctly rejected as
a verdict criterion masquerading as an admission criterion: it would have made `law.rs` declinable at
the gate on the grounds that `780af6ef` calls the hub's admission law an independent design, a
self-sealing false negative on the exact surface this pass exists to reach.*

- **M1 — it implements or enforces SAL's subject matter**: it holds a society role set, an authority-
  derivation or delegation rule, a law-publication/interpretation path, an admission/citizenship
  decision, a witness-quorum rule, or a law-record anchoring rule. Mentioning the vocabulary is not enough.
- **M2 — it is normative or product-bearing in the corpus's own taxonomy**: standard text, SDK/crate
  code shipped as a library, or a running daemon. `CLAUDE.md` classifies `simulations/` as *Python
  research* and the primer classifies standalone research scripts as non-integrating; **research/
  reference code is a consumer of the ideas, not a mirror** — a divergence there is a research
  observation at most, never a spec defect.
- **M3 — a divergence in it would misinform a relying party acting on the spec**: it is reachable by
  someone implementing Web4.

**Adjudication axis, not an admission gate**: "reading-of-SAL vs independent-design" is the
spec-vs-implementer split, resolved *after* admission under M2 (C284's handling of its third implementer).

---

## §A. Prior-Finding Verification (frozen HEAD `0849ebbe`)

### A.1 — Freeze proof

`git diff 1354e4c2..HEAD -- <SAL>` = **empty**. `grep -cE '&#|&amp;|â€|Â '` = **0**. `hasEffector` = 1,
`respondedBy` = 1 (no duplication or malformation). The C59 remediation's 10/10 holds by the C208+C246
chain described above; the C98 site-table stands verbatim.

### A.2 — Standing carries re-verified against live referents

| Carry | Live-side re-check at HEAD | Verdict |
|---|---|---|
| **B7** (SAL makes Authority/Witness/Auditor conformance-MUST — §12.1, §7.1 `hasAuthority`, §11 discovery — while `society-roles.md` tiers all three **Optional** §4.1/§4.3) | Re-derived independently this pass before consulting the ledger, and it reproduced exactly. `society-roles.md` §1.3 Optional = "not required for basic function"; §4.3 Authority = "Scoped delegation powers (finance, safety, membership)" — **verbatim SAL §5.2's scope language**. Both docs unmoved in-window. | **STANDS — and now has a measured victim (§B.2)** |
| **C16-M1** (role taxonomy N-way) | `federation.RoleType`=5, `role.SocietyRole`=9, `society-roles.md`=7 base-mandatory — unchanged; **+1 leg found this pass**: `hub-lib/src/law.rs KNOWN_ROLES`=7-but-a-different-7 | **STANDS — widened, see C286-N1** |
| **C16-M8 / B6** (SAL §7.1/§7.1.1 `web4:` triple family absent from the ontology; no `sal-ontology.ttl`) | `grep -rnE 'hasWitness\|hasAuditor\|hasEffector\|respondedBy\|recordsOn\|adjustedBy\|attestedBy\|hasLawOracle\|hasAuthority' web4-standard/ontology/` = **0 hits**. Directory holds `hub-law.ttl`, `r7-action.jsonld`, `role-extension{-schema.md,.ttl}`, `t3v3{.jsonld,-ontology.ttl}`, `web4-core-ontology.ttl` — still no `sal-ontology.ttl`. In-window ontology mover `01f410db` touched `t3v3-ontology.ttl` only. | **STANDS — re-verified, not re-discovered** |
| **C23-H1** (birth-certificate shape N-way divergence) | SAL §2.2/§2.3 frozen; no new representation leg in-window (`#538`/`#544` are pre-window and were consumed at C246/C248) | **STANDS as REFRESHED at C246** |
| **C58-B10 / B15** (§3.6 dormant-defer ↔ SMS §4.1 new_citizen wake) | `SOCIETY_METABOLIC_STATES.md` byte-frozen (confirmed independently at C284, blob `5e3f7203`); two-sided contradiction intact | **STANDS — do NOT re-open** (dual-anchored) |
| **B15** (law-composition: SAL §3.5 child-override-ranked vs SOCIETY_SPEC §3.2.1 extend-not-contradict vs role-extension strictest-wins) | `role-extension-schema.md` unmoved in-window | **STANDS** — three models, one operator answer |
| **C246-N1** (`authority_ratchet` forward-note) | `grep -ci ratchet <SAL>` = **0**; SAL still has no ratchet/assurance-primitive concept | **STANDS — reach widened, see C286-N3** |
| **C33** (`lct:web4:` example strings) | unchanged in-window | **STANDS** |
| C50-B13/B14/B15, SDK-track C92-N1 / C164-N1 / C22-M3 | referents frozen | **STAND** per C246 §A.2 |

Zero carries closed; zero regressed.

---

## §B. Mirror-Set Re-Derivation and Corpus-Delta Sweep

### B.1 — Candidate derivation and per-candidate verdict

Candidates came from a **corpus-wide subject-matter term sweep**, not a directory list. Every candidate
gets a recorded verdict so the next SAL delta inherits a *derived* set.

| Candidate | Verdict | Reason |
|---|---|---|
| **`hub/hub-lib/src/law.rs`, `hub/hub-daemon/src/{main,rest,admin}.rs`, `hub/hub-lib/src/init.rs`** | **ADMIT (M1+M2+M3)** | Running daemon; holds a society role set, delegation/escalation/admission/ATP-authority rules, and a law-file validator. **First admission in the lineage's history.** See B.2. |
| `hub/hub-lib/src/charter.rs` | **DECLINE (M1)** | Charter storage; `law.rs:43` notes rules are "empty in MVP". Was on this pass's *pre-review* candidate list purely on filename — the policy review was right that the list was filename-derived. |
| `governance/` (`governance_map.yaml`, `generate_dashboard.py`, `dashboard.md`) | **DECLINE (M1)** | LRC change-review tuning over whitepaper section paths. Governs *document review thresholds*, not society law. **Recorded once so no future pass re-opens the corpus's other "governance" directory.** |
| `ledgers/reference/python/governance_audit.py` (632L) | **DECLINE (M1)** | Predicted by the policy review as an expected *M2* decline (the C284 `heartbeat_ledger.py` shape). It declines **earlier, at M1**: `grep -ciE 'law.?oracle\|birth.?certificate\|citizen\|hasAuthority\|delegat\|quorum'` = **0**. It is a *federation decision* append-only log (Track BX), not a reading of society law. The prediction was reasonable and wrong; recording the correction. |
| `web4-trust-core/src/witnessing/chain.rs` | **DECLINE (M1)** | Sole hit for `law\|oracle\|authority\|SAL` is the module doc line `//! Witnessing chain traversal`. |
| `core/pattern_source_identity.py` | **DECLINE (M1)** | `trust oracles` / `value oracles` / `ORACLE = "oracle"` / an `lct:web4:oracle:trust:` example — **data-plane oracle**, the exact class **C246 §B.2** already refuted for `4f76f110`. Do not re-adjudicate. |
| `archive/**` (≈120 files incl. `sal_society_authority_law.py`, `law_oracle.py`) | **DECLINE (M2)** | The documented academic sprawl the primer names; archived, non-product-bearing. |
| `simulations/` | **DECLINE (M2)** | `CLAUDE.md` classifies as Python research; declined by construction per C284. |
| `forum/nova/web4-sal-bundle/sal-ontology.ttl` | **DECLINE (M2)** | Static inbound Nova proposal, not canonical. **Note for C16-M8/B6**: a `sal-ontology.ttl` *does* exist here — it is not in `web4-standard/ontology/`, so the carry's claim ("no `sal-ontology.ttl`") should be read as scoped to the canonical set. Wording nit for whoever adjudicates B6; not a defect. |
| `web4-core/src/{role,society,lct,r6}.rs`, SDK `web4/{role,society}.py`, `web4-policy/src/lib.rs` | **ADMIT — unmoved** | Pre-existing mirror set; 0 commits in-window. C208 §B.3 convergence results STAND by construction. |

### B.2 — **The hub gate: ADMITTED, and it diverges** → C286-N1

The hub carries **two society-role vocabularies in one binary, and they disagree.**

**Vocabulary 1 — `hub-daemon/src/main.rs:720-737 parse_role()`**, the role-assignment CLI. Accepts
**9**: `sovereign, law_oracle, policy_entity, treasurer, administrator, archivist, citizen, witness,
auditor`. Maps to `web4_core::SocietyRole`. **Faithful** to `society-roles.md` §2 + §4.1.
Corroborated by `hub-lib/src/init.rs:585`, whose unfilled-role census iterates
`["law_oracle", "policy_entity", "treasurer", …]`.

**Vocabulary 2 — `hub-lib/src/law.rs:39 KNOWN_ROLES`**, the law-file validator. Accepts a **different
7**: `sovereign, administrator, treasurer, archivist, witness, citizen, applicant`.

| Role | `society-roles.md` tier | `main.rs` CLI | `law.rs` law validator |
|---|---|---|---|
| sovereign | base-mandatory §2.1 | ✅ | ✅ |
| **law_oracle** | **base-mandatory §2.2** | ✅ | ❌ **rejected** |
| **policy_entity** | **base-mandatory §2.3** | ✅ | ❌ **rejected** |
| treasurer / administrator / archivist / citizen | base-mandatory §2.4–§2.7 | ✅ | ✅ |
| witness | optional §4.1 | ✅ | ✅ |
| **auditor** | optional §4.1 | ✅ | ❌ **rejected** |
| **applicant** | **absent from `society-roles.md` entirely** (grep = 0) | ❌ | ✅ |

`is_known_role()` (`law.rs:49-51`) is a closed `contains` check, and it gates **four role-typed law
fields**: `delegation.allowed_roles` (`:263`), `escalation[].escalate_to` (`:275`),
`admission.sponsor_role` (`:287`), `atp_issuance.mint_authority` (`:307`). Each miss is a hard
`return Err` — **the law file is rejected at load.**

**The concrete consequence.** A society may assign its Law Oracle (`main.rs` accepts it), and the hub
will list `law_oracle` among the base-mandatory roles it reports unfilled (`init.rs:585`) — and then a
law file containing `escalation: [{escalate_to: law_oracle}]` **fails to load**. The society cannot
express, in law, escalation to the one role SAL §4 and §5.3 make constitutive of law itself. SAL §9's
own error guidance for `W4_ERR_LAW_CONFLICT` reads "*request parent/child oracle mediation*" — the
remedy SAL prescribes is the one the hub's law validator forbids naming. The same holds for delegating
to the Auditor and for `mint_authority: policy_entity`.

**Why it survived.** `law.rs:35` documents the list as "Known SocietyRole names **per web4-core**" — a
fidelity claim it does not meet. `hub/examples/starter-law.yaml` uses only `sovereign` (`:147`) and
`treasurer` (`:175`), so the shipped example never exercises any of the four divergent names. And the
**only** test touching this set (`law.rs:447-459`,
`constellation_roles_are_a_separate_namespace_from_society_roles`) asserts that `KNOWN_ROLES` does not
*overlap* its sibling list — never that it *matches the standard*. This is the C270-N2 pattern exactly:
a testable invariant with a comment where an assertion should be.

**Age**: `KNOWN_ROLES` was born `6aa52d8a` (2026-06-07, "V2-8 Step 1 — chapter law module"), 52 days
ago and well pre-window. **Net-new as a FACT: no. Net-new as a FINDING: yes** — no SAL pass has read
this file.

**Direction — SAL is not defective.** SAL §5's role registrations are correct and internally coherent.
The divergence is an implementation defect, routed to HUB. Its *SAL-side* value is as **evidence
upgrading standing carry B7**: B7 has been an unanswered DESIGN-Q since C58 (2026-06-15, **44 days**),
argued from spec-vs-spec prose. It now has a measured victim — an implementer reading both SAL's role
MUSTs and `society-roles.md`'s Optional tier produced a **third** role set satisfying neither, and
split it across two vocabularies **inside a single binary**. That is B7's cost, demonstrated. Per
`feedback_carry_gains_reach_not_truth`, this routes as a demonstrated upgrade to the standing carry,
not as a new defect.

### B.3 — Per-mover adjudication of the window's authority-claiming inbounds

| Mover | Adjudication vs SAL |
|---|---|
| **`780af6ef`** `docs/strategy/hub-position-review-and-plan-2026-07-28.md` (dp) — "the admission law section is declarative theater" | Read **first**, before any candidate, per the approved ordering. Its §2.1 diagnoses fields that are *validated but never read* (`min_trust_score`, `open`, `requires_sponsor`, `sponsor_role`), disposition **deferred to HUB**. That is an internal-consistency defect and **not a SAL finding**. It is also **disjoint from C286-N1**: `grep -in 'KNOWN_ROLES\|role vocab\|law_oracle\|role set'` over the whole document = **0**. Over-declaration (theater) vs under-acceptance (rejecting a mandatory role) are inverse defects on the same file. **No competing routing**: C286-N1 is a fresh surface, not a restatement. |
| **`a135a597`** #587 — `KNOWN_CONSTELLATION_ROLES` asserted an enforcement with zero callers | **Refutes the "already found" objection, and sharpens N1.** #587 corrected the doc comment on the *constellation* list — explicitly "a **distinct namespace** from `KNOWN_ROLES`". It landed 2026-07-29 (in-window), and its own added text at `law.rs:57-58` *names* `KNOWN_ROLES` and enumerates its first two entries. The pass that fixed the **published-not-enforced** list wrote a cross-reference to the **enforced-and-wrong** list 44 lines above it and did not check it. |
| **`d5bd10b2` + `8b0b133d`** #591/#592 AssuranceReceipt | Lands in `hub-lib/src/constellation.rs:406` — constellation-tier MFA assurance, PRD_ASSURANCE A2. Not a SAL surface. It is a **second** assurance primitive sitting beneath SAL §4's abstract "witness thresholds" (the ratchet was the first) → **status note C286-N3** on C246-N1, widening its reach from 1 primitive to 2. Not net-new. |
| **`4665a430`** #579 Dictionary → context-mandatory | Does **not** collide with SAL directly (SAL has no Dictionary role; the proposal never mentions SAL — `grep -cw 'SAL'` = 0, `grep -c 'society-authority-law'` = 0). But it exercises the very tiering mechanism B7 says is unreconciled with SAL, without citing SAL. Its own argument — an outside actor must be able to discover "act kinds, **role names**, event types" before forming a Request, and "the failure mode of guessing is not a clean rejection: it is a silent or late one" — is **satisfied verbatim** by C286-N1 → **C286-N2**. |
| **`954ee391`** #580 resilience-to-incomplete-information | No SAL-side instance this pass. SAL's dormant-state handling (§3.6) is already dual-anchored under C58-B10/B15; adding a #580 lens would duplicate an open carry. Deliberately not charged. |
| **`752eadde`** AAEP evidence PRD | SAL §5.6 already requires an Enactment Transcript binding recognition evidence; AAEP's Action Request → Policy Decision → Result Evidence triple is compatible, not contradictory. Forward-note only. |
| **`5df662a5`** relying party must compute trust | Reinforces the LCT §1.2 discipline C246-N1 leaned on. No SAL clause prescribes a trust threshold. Clean. |
| **`01f410db`** ontology (`web4:Tensor` superclass, closes #581) | Touches `t3v3-ontology.ttl` only (14+/4−); 0 SAL triples added. Method carry v6's emitted-examples obligation is **thin here and deliberately not padded**. Does not disturb C16-M8/B6. |
| `206dd004` + `1fa86e09` (Rust CI), `1fc873d1` / `7fea33a5` (hardening wave), `9aedd2b7`, `5c2dd39f` #578, `f10d2999` #588, `22d5a8f6` | No SAL surface. `206dd004` is relevant context for N1 — the workspace has only just acquired CI, so a fidelity test for `KNOWN_ROLES` would now actually run. |

### B.4 — Refutations (do NOT resurrect)

- **R1 — "C286-N1 is `780af6ef`'s declarative-theater finding under a new name."** **REFUTED**: zero
  lexical overlap (grep above), and the two defects point in opposite directions — theater is a field
  declared and not read; N1 is a value the validator actively rejects while the rest of the binary
  accepts it.
- **R2 — "C286-N1 is #587."** **REFUTED**: #587's own text declares the two vocabularies distinct
  namespaces and changed only the constellation list's doc comment (`git show a135a597` = doc-only).
- **R3 — "B7 is a naming artifact: SAL's Authority ≡ `society-roles.md`'s base-mandatory Sovereign."**
  **REFUTED**: the taxonomy lists **both** separately (Sovereign §2.1 = charter amendment, identity
  recovery, extraordinary inter-society decisions; Authority §4.3 = "Scoped delegation powers (finance,
  safety, membership)"), and §4.3's wording is verbatim SAL §5.2's ("Scopes: domain-bounded (e.g.,
  finance, safety, membership)"). They are the same role, tiered Optional.
- **R4 — "`governance_audit.py` is a second governance-law reading (the C284 shape)."** **REFUTED at
  M1**, against this pass's own prior expectation and the policy review's: 0 hits for every SAL
  subject-matter term. Recording the miss so the next delta does not re-open it.

---

## §C. Findings and Routing

**ZERO autonomous-actionable. ZERO mutation.** SAL is correct throughout; this pass edits nothing.

- **C286-N1 — MEDIUM → HUB track (fresh surface), + evidence on operator DESIGN-Q B7.**
  `hub-lib/src/law.rs:39 KNOWN_ROLES` rejects `law_oracle`, `policy_entity`, and `auditor` — two of
  them base-mandatory — as values for four role-typed law fields, while `hub-daemon/src/main.rs:724`
  and `hub-lib/src/init.rs:585` in the same binary accept and report them; and it admits `applicant`,
  which `society-roles.md` does not define. The doc comment at `law.rs:35` claims fidelity "per
  web4-core" that the list does not have. Consequence: a society cannot express in law an escalation
  or delegation to its own Law Oracle — the remedy SAL §9 prescribes for `W4_ERR_LAW_CONFLICT`.
  *Not* the `780af6ef` item (R1) and *not* #587 (R2). Cheapest fix is a fidelity test now that
  `206dd004` gives the workspace CI. **Auditor MUST NOT self-apply — hub is another track's code.**
- **C286-N2 — INFO → #579's authors (CBP / dp).** #579 argues a society must publish discoverable
  "act kinds, **role names**, event types" before an outsider can form a valid Request, and that the
  failure mode of guessing is a late rejection rather than a clean one. C286-N1 is a **fourth
  instance** for its evidence base, and the sharpest one: the vocabulary split is not between two
  societies but **inside one binary**, so even a correct reading of the hub's published role set is
  rejected by its law loader. Same routing shape as C284-N2 / C282-N1 into #580's survey.
- **C286-N3 — status note on C246-N1 (not net-new).** `AssuranceReceipt` (#591/#592,
  `constellation.rs:406`) is a **second** assurance primitive beneath SAL §4's abstract witness
  thresholds; the `authority_ratchet` was the first. C246-N1's forward-note ("should §5.2/§4.2 name
  it") gains reach, not truth.
- **B7 severity should be re-set on adjudication.** Open 44 days as a prose-argued spec-vs-spec
  DESIGN-Q; it now has a demonstrated implementation cost. Adjudicate **with** C16-M1 (same class —
  N1 adds a fourth taxonomy leg) and with #579, which is an operator-directed proposal to move a role
  between the very tiers B7 disputes.

---

## §D. Carries and Method Lessons

**Next SAL delta ~C326.** Re-baseline from `8b0b133d`.

**Guard for the next pass — the mirror set is now DERIVED, do not re-derive from scratch:**
`hub/hub-lib/src/law.rs` + `hub-daemon/src/{main,rest,admin}.rs` + `hub-lib/src/init.rs` are **IN** the
SAL mirror set as of C286. `charter.rs`, `governance/`, `ledgers/reference/python/governance_audit.py`,
`web4-trust-core/src/witnessing/chain.rs`, `core/pattern_source_identity.py`, `archive/**`,
`simulations/`, and `forum/nova/web4-sal-bundle/` are **DECLINED with reasons recorded in §B.1** — do
not re-open without new evidence. First check at C326: did `KNOWN_ROLES` change, and did a fidelity
test appear?

**Open carries, all STANDING**: B7 (upgraded — see §C), C16-M1 (widened, 4th leg), C16-M8/B6
(re-verified, + the `forum/nova/sal-ontology.ttl` wording nit), C23-H1, C58-B10/B15, B15
law-composition, C33, C50-B13/B14/B15, C246-N1 (reach widened), SDK-track C92-N1/C164-N1/C22-M3.
D0 (`protocols/` cluster) still gates on an unanswered operator decision.

**Method lessons:**

1. **A verdict criterion is not an admission criterion.** This pass's first draft of M3 read "a
   divergence would indict the SPEC, not just the artifact." That makes the *output* of §B a
   precondition for opening the file, and it would have declined `law.rs` on the grounds that the
   operator's own strategy doc frames the hub's admission law as an independent design — a
   self-sealing false negative on the one surface the whole pass existed to reach. C284's reach
   wording ("would misinform a relying party acting on the spec") is the correct gate. The
   reading-of-spec-vs-independent-design distinction is real but belongs downstream, under M2.
2. **An inflated premise makes a sound lead look reverse-engineered.** This pass initially reported
   "15 of 46 commits landed in `hub/`"; the true number is **9** (the error was an `awk` counting
   files, not commits). The lead survived without the inflation. Check the arithmetic on the number
   that motivates the sweep — it is the number a reviewer will test first.
3. **Two vocabularies in one binary is a findable shape.** The productive question was not "does the
   hub's role set match the standard" but "**does the hub agree with itself**" — a check that needs no
   spec at all, and that surfaced the spec-side carry as a consequence. When a codebase holds two
   lists of the same thing, diff them before diffing either against the spec.
4. **A sibling correction is a signal, not a substitute.** #587 fixed the doc comment on the
   non-enforced list and wrote a cross-reference *to* the enforced-and-wrong list in the same commit.
   When a window contains a correction to one member of a pair, check the other member.
5. **Record declines with reasons, including the ones you predicted wrong.**
   `governance_audit.py` was expected to decline at M2 (the C284 `heartbeat_ledger.py` shape) and
   actually declines at M1. Writing down which criterion fired, and that the prediction missed, is
   what stops the next pass re-deriving the same list.
