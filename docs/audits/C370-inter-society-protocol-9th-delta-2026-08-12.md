# C370: `inter-society-protocol.md` (ISP) 9th-delta RE-Audit

**Date**: 2026-08-12
**Track**: web4 (Legion autonomous session, slot `web4-20260812-120000`)
**Instrument**: C-series delta RE-audit; **9th delta** on `inter-society-protocol.md`
**Lineage** (located by reading the oldest pass's line-1 header, not by globbing `C*-<slug>*` — the
C326 inclusive rule): **C6** (`inter-society-protocol-internal-consistency-2026-05-21.md`,
self-identifying as `# C6:`) → C25 → **C62** → remediation **C63** (#341) → C102 → C136 → **C174** →
C212 → C250 → **C290** → **C330** → this pass. **11 documents.**
**Source**: `web4-standard/core-spec/inter-society-protocol.md` (v0.1.2 DRAFT, **384 lines**, blob
`22bf6c1d`, last edited `0405f331` 2026-06-16 — **BYTE-FROZEN 57 days**)
**Window**: `89251abc..HEAD` (C330 snapshot → `d128e075`) = **50 commits, 41 files**

**Result headline**: **0 net-new defects against the spec (10th consecutive clean ISP delta). ZERO
mutation.** What this pass found is not in the spec but in the *closure record*: **two HIGH findings
(F3, F4) were closed `SUPERSEDED` on the strength of a spec edit, while the implementation that
instantiated the identical defect — created two days *before* that edit — was never re-checked and
still ships in the wheel today, 89 days later.** The audit corpus recorded the defect, recorded its
fix, and recorded its closure; the closure was scoped to the document, and the defect had two loci.
An executed round-trip shows the shipped SDK **silently discards** the spec's own §7.4 example and
**preserves only** the settlement shape §7.7.1 names and rejects. Policy review then falsified four of
this pass's own claims — including its novelty claim and its load-bearing normative framing — and the
corrected version is stronger than the draft; all corrections are published in place (§F).

---

## Summary

| Severity | NEW (C370) |
|----------|-----------:|
| HIGH | 0 |
| MEDIUM | **1** (N1 — remediation-scope failure: F3/F4 closed spec-side, SDK locus never re-checked, still shipping) |
| LOW | **1** (N2 — 3 of 4 test-vector conformance MUSTs address directories that have never existed) |
| INFO | **1** (N3 — ISP's normative modality is 100% fence-resident; measured, nothing charged) |
| **Total NEW distinct defects vs. the spec** | **0** |
| Hypotheses REFUTED by pre-registered rule, published | **3** |
| Deferrals discharged with a row | **6 of 6** (5 negative, 1 declined with reason) |
| Own claims corrected by policy review, published in place | **4** |

---

## §A. Freeze + sibling verification at live HEAD

`git diff 0405f331 HEAD -- web4-standard/core-spec/inter-society-protocol.md` = **empty**.
`git diff 89251abc..HEAD -- <target>` = **empty**.

**All six cited siblings unmoved since the C330 snapshot ⇒ 4th CONSECUTIVE zero-mover delta**, so every
C212/C250 DISJOINT adjudication carries verbatim and nothing is re-litigated:

| Sibling | Last commit | Moved in window? |
|---|---|---|
| `atp-adp-cycle.md` | `256ab51d` 2026-07-07 | no |
| `mcp-protocol.md` | `3e765345` 2026-07-13 | no |
| `web4-society-authority-law.md` (SAL) | `1354e4c2` 2026-07-14 | no |
| `SOCIETY_SPECIFICATION.md` | `87377c38` 2026-07-14 | no |
| `society-roles.md` | `1354e4c2` 2026-07-14 | no |
| `LCT-linked-context-token.md` | `d89595e8` 2026-07-16 | no |

§A is **collapsed to the blob table** per the C344/C346 precedent — on an unchanged blob the C63
anchors hold by construction and re-resolving them is make-work. C330 verified all 11 by content.

### A.1 — Outbound cross-reference resolution: **first run in this lineage, NEGATIVE**

Nine passes have adjudicated ISP's *relationships* to its siblings without ever checking that its
*pointers* land. Run now (script in §G):

> Every backticked `*.md` name on a line is paired with the `§`-references that follow it on that
> line; `SAL` is resolved as an alias for `web4-society-authority-law.md`; self-reference markers
> (`this spec's`, `per §`, `see §`) reset the pairing so ISP's own section numbers are not attributed
> to a sibling. Each resulting (doc, §) claim is matched against a real ATX heading in the target.

**20 distinct outbound (doc, §) claims. 20 resolve. 0 unresolved.** Published as a negative — it is
what makes the two positives below interpretable (v43). Two apparent misses in the first run
(`SOCIETY_SPECIFICATION.md §3.4` at `:115`, `society-roles.md §6.2` at `:369`) were **parser
artifacts**, not defects: the first is `SAL §3.4` with an unbackticked alias, the second is "*this
spec's* §6.2." Both are corrected in the matcher above, not worked around.

---

## §B. N1 (MEDIUM) — a `SUPERSEDED` verdict is scoped to the artifact it was measured on

### B.1 The rule, and what part of it survives the WIP hedge

ISP `:368` — the `mcp-protocol.md` row of §8's relationship table — cites **"`mcp-protocol.md`
§7.3–§7.6"** as the specification of R6/R7 actions between societies. The cross-society ATP settlement
envelope is §7.4, inside that range. ISP `:150` (the `B2-interim` note, C102's "½ of B2") separately
routes Option 1's rate *substance* to mcp §7.7.1.

> **Correction adopted from policy review (§F.3):** ISP `:150` is **not itself normative**. ISP
> contains **zero** RFC 2119 / BCP 14 declarations (`grep -c` = 0) and `:150` carries no 2119 keyword;
> the parenthetical `(Normative)` modifies *mcp §7.7.1*, not the note. The draft called it "a
> Normative note" and that was overstated. Correct phrasing: **a non-normative cross-reference that
> routes Option 1's substance to a section mcp itself labels Normative.** The in-scope hook that
> carries this finding is `:368`, not `:150`.

mcp §7.7.1 (`:546`): *"two societies maintain a floating bilateral rate `ATP_A : ATP_B` … **This is
NOT the Web4 model.**"* Rates are grounded in a common referent, and settlement records **both
societies' independent valuations** of it (`mcp-protocol.md:658`, "the load-bearing property of
referent-grounding"). The §7.4 example envelope this pass executed is `mcp-protocol.md:438-448`.

mcp §7.4 `:466` lists an either/or requirement (`exchange_agreement_ref` **OR** inline `referent` +
`caller_amount` + `responder_amount`) — **but that MUST is expressly interim-scoped and cannot be
charged.** The interim conformance note (`mcp-protocol.md:470`) reads: *"implementations that carry
the `atp_settlement` block **SHOULD** populate it using the schema above … **The MUST applies only to
the presence of the block** …; the internal structure stabilizes with §7.7."*

> **Correction adopted from policy review (§F.4):** the draft charged N1 against the either/or MUST.
> The hedge substantially excuses that. What the same note **expressly carves out** is the invariant:
> *"The referent-grounded **invariant** — settlement carries both societies' independent valuations of
> a common referent — is the stable normative design-invariant of §7.7.1; only the field-level wire
> format is WIP."* **N1 is charged against the invariant, not the wire format.** This matters because
> the SDK's failure is not that its field *names* differ — it is that its data model carries **one**
> currency and **one** amount and therefore cannot express two valuations *at all*.

### B.2 The site

`web4-standard/implementation/sdk/web4/mcp.py:714-803`, `@dataclass(frozen=True) CrossSocietyContext`:

```
atp_settlement_currency: str = ""
atp_settlement_amount: int = 0
atp_settlement_exchange_rate: Optional[Dict[str, Any]] = None
```

One currency, one amount, a free-form rate map. No `referent`. No caller/responder pair. The one
adjacent field that could satisfy the standing-agreement path, `exchange_agreement_hash`, is read from
and emitted at `cross_society["exchange_agreement_hash"]` (`:755`, `:795`) — a **sibling** of
`atp_settlement` — while the spec nests `exchange_agreement_ref` **inside** it.

### B.3 Executed (v43 — coverage is not execution)

The §7.4 example envelope was transcribed verbatim from `mcp-protocol.md` and round-tripped through
the shipped class. Six arms, including negative controls so the instrument is admissible:

| arm | `from_dict` | `to_dict` emits |
|---|---|---|
| **spec §7.4 verbatim** (`caller_currency`/`caller_amount`/`responder_currency`/`responder_amount`/`referent`/`exchange_agreement_ref`) | ACCEPTED | **`atp_settlement` ABSENT — whole block dropped** |
| **referent only**, no legacy keys | ACCEPTED | **`atp_settlement` ABSENT — whole block dropped** |
| abstract FX `{"ATP-ALPHA":1.0,"ATP-BETA":0.85}` (**the SDK's own test vector**, `test_mcp_cross_society.py:120`) | ACCEPTED | `{"currency":…,"amount":…,"exchange_rate":{…}}` — **round-trips intact** |
| bare scalar rate `{"rate":0.9}` (`test_mcp_cross_society.py:152`) | ACCEPTED | **round-trips intact** |
| NEG CONTROL `amount: "not-an-int"` | ACCEPTED | preserved **unvalidated** |
| NEG CONTROL empty block | ACCEPTED | dropped |

**The two shapes the spec's invariant requires are silently discarded; the two shapes §7.7.1 names and
rejects are the only ones preserved.** The negative controls establish that the surface neither
rejects everything (it is not vacuous) nor validates anything.

**Mechanism** (so the next pass need not re-derive it): `from_dict` reads only
`settlement.get("currency"|"amount"|"exchange_rate")` (`:796-798`); against a spec-shaped block all
three miss and fall to defaults; `to_dict`'s guard `if self.atp_settlement_currency or
self.atp_settlement_amount:` (`:758`) is then False and the block is never emitted.
**`exchange_agreement_ref` is lost by the same envelope for a second, independent reason** — the SDK
looks for it one level up under a different name. **Both** of §7.4's alternative population paths are
lossy, not just the inline one.

### B.4 Why this is NOT net-new — and why the corrected finding is stronger

> **Correction adopted from policy review (§F.2):** the draft claimed N1 net-new. **It is not.** The
> novelty matcher was `atp_settlement_exchange_rate` (0 hits corpus-wide) — the *SDK's* field name.
> The defect's name in the corpus is the *spec's* field set, and searching for it returns three prior
> layers. This is [[feedback_novelty_is_an_absence_claim]] exactly: the matcher was this pass's
> paraphrase, not the domain expert's vocabulary.

| when | what | evidence |
|---|---|---|
| 2026-05-15 | SDK `CrossSocietyContext` **created** with `currency`/`amount`/`exchange_rate` | `bf34e0df` |
| 2026-05-15 | **F3 + F4, both HIGH**, charge *that exact field set* against §7.7.1 | `mcp-protocol-internal-consistency-2026-05-15.md:48`, `:119-130` |
| 2026-05-17 | **spec** §7.4 remediated — gains `referent` + `caller_amount`/`responder_amount` + the interim note | `854df2cc` (#200) |
| 2026-06-06 | **F3 and F4 closed `SUPERSEDED`**, both citing "**§7.4 L420–432**" — a *spec* locus | `C35-mcp-protocol-audit-2026-06-06.md:45` |
| 2026-06-20 | C78 **declines** the §7.4 echo as a separate row: *"folded into B1 … not an independent finding"* | `C78:143` |
| **2026-08-12** | **SDK still carries the pre-remediation field set; ships in the wheel; 164 mcp tests green** | this pass |

F4's own remedy text reads *"extend the **§7.4 `atp_settlement` schema**"* — a document-scoped remedy
for a defect that, two days earlier, had already been copied into code. F3/F4 were measured on the
spec, fixed on the spec, and closed on the spec. **Nothing in the closure was wrong; it was scoped.**

The SDK's own `CHANGELOG.md:9-13` still advertises the pre-remediation conformance claim —
*"Cross-society MCP types (**PR #195**) — implements **§7.3–7.6** … `CrossSocietyContext` envelope for
cross-society MCP calls (**§7.4**)"* — and **#195 predates #200**. The changelog claims conformance to
a §7.4 that no longer exists. Note that ISP `:368` names **the identical range**, "§7.3–§7.6": the
range ISP points at is the range the SDK claims, and the settlement envelope is inside both.

### B.5 Severity, honestly bounded (v45 — who calls it)

`git grep CrossSocietyContext` over `web4-standard/`: **22 hits, zero production callers.** Every
reference outside the class definition is `tests/test_mcp_cross_society.py`, the two export lines
`web4/__init__.py:494`/`:913`, the `__all__` entry `mcp.py:52`, and the CHANGELOG. It is a public
wheel export (`pyproject.toml` `include = ["web4*"]`) with **no internal consumer**.

- **In-repo blast radius: zero.** Nothing in this repository can emit a malformed envelope from it.
- **Exposure is entirely external** — `web4-sdk` consumers who import the advertised §7.4 type.
- **Why no gate saw it**: `atp_settlement` has **0 schemas and 0 test vectors** (checked across
  `web4-standard/schemas/` and both test-vector trees), and there is **no other-language
  implementation** (`git grep -il 'atp_settlement|CrossSociety' -- '*.rs' '*.ts' '*.go'` = **0**), so
  no cross-language parity check exists either. And the SDK's own test (`:118-120`) **pins** the
  abstract-FX shape as expected output — the suite does not merely miss the defect, it asserts it.
  **164 mcp tests pass, 37 of them cross-society.**

**MEDIUM.** Not HIGH: no in-repo caller, and the field-level wire format is genuinely WIP. Not LOW: it
ships in a published wheel under an unqualified §7.4 conformance claim, and the invariant it violates
is the one clause the WIP hedge expressly protects.

### B.6 Routing — **NOT this lineage's to own**

Precedent is exact: `C174:127` raised a cross-track SDK finding inside an ISP pass and routed it out
(*"Route: SDK track — bundle with the existing C62-B12 `role.py` carry"*). Same here. **The site is
the SDK; the rule is mcp §7.4/§7.7.1; ISP is where the two are cited together (`:368`).**

File N1 as the **fourth member of a named family**, not as a standalone row:

| member | locus | status |
|---|---|---|
| `C62-B2-full` | ISP prose | **OPEN**, operator-owned, HELD C102→C330 |
| `C78-B1` | atp-adp §5.2/§5.3 | **OPEN**; explicitly *declined* the §7.4 wire echo (`C78:143`) |
| `F3`/`F4` | mcp §7.4 | **CLOSED `SUPERSEDED`** — spec side only (`C35:45`) |
| **`C370-N1`** | **SDK `mcp.py:714-803`** | **NEW — the locus no member of the family ever measured** |

**Remedy owner: SDK track. No SDK edit this session, and do not widen the dataclass in passing** —
`C35:110` rules that the §7.7 promotion cluster must be resolved **as one unit**, warning that
piecemeal patching *"re-introduces the inconsistency the 2026-05-17 pass just cleared."* The correct
interim remedy is documentary: retract or qualify the unqualified §7.4 conformance claim at
`sdk/CHANGELOG.md:11`, and defer the field change to §7.7 v0.1.0-final.

**Operator question (do NOT self-resolve):** F3/F4 were closed `SUPERSEDED` against a spec locus while
a code locus of the same defect was live. Should a `SUPERSEDED` verdict be required to **enumerate the
loci it discharges**, so that closing one does not silently close the others? That is a
rotation-wide instrument question, not an ISP one. → couple with `C60-B14`.

---

## §C. N2 (LOW) — 3 of 4 test-vector conformance MUSTs address directories that have never existed

`web4-standard/test-vectors/README.md:28-32` publishes the corpus's only conformance-requirements
statement for test vectors:

```
Implementations MUST:
1. Pass all vectors in `valid/` directories
2. Reject all vectors in `invalid/` directories
3. Produce bit-identical outputs for deterministic operations
4. Handle edge cases in `edge-cases/` directories
```

`find web4-standard -type d \( -name valid -o -name invalid -o -name edge-cases \)` = **0**, against
**22** populated subdirectories in that tree. Items **1, 2 and 4 are unsatisfiable by construction**;
only item 3 is actionable. The file is untouched **167 days** (`a3b93713` 2026-02-27). Its
`## Structure` list names **5 of 22** directories.

**Root cause — makes the fix ~3 lines.** The README's *own* usage example at `:19` reads
`test-vectors/lct/valid-birth-certificate.json`, which **exists**. `valid` is a **filename-prefix**
convention that the conformance section wrote up as a **directory** convention.

**Negative control (v17 — there are multiple trees, state which).** Three test-vector READMEs exist:
`web4-standard/test-vectors/` (**1** MUST block), `web4-standard/testing/test-vectors/` (**0** MUSTs —
and it is the one admitted as evidence at `C300:148`), and `forum/nova/test-vectors/` (**0** MUSTs).
**This is a one-tree defect, not a corpus convention.**

**Adjacent prior art, cited not duplicated:** `C346:328` charges the *same file* for a different thing
(*"never mentions running a validator"*). **Route: test-vectors / conformance-harness track.** Not ISP's.

---

## §D. N3 (INFO) — ISP's normative modality is 100% fence-resident. Measured; nothing charged.

**Matcher published beside the claim (v44), denominator published with the count (v40).** Domain =
`web4-standard/core-spec/*.md`, **30** files, **26** of which carry ≥1 RFC-2119 keyword. A keyword is
"inside" if it falls between an opening and closing ``` marker.

| matcher | ISP in/out | ISP % | rank | runner-up | docs at 0% |
|---|---|---|---|---|---|
| M1 — all 10 RFC-2119 keywords | 29 / 26 | 53% | **1 of 26** | `data-formats.md` 11% | 20 of 26 |
| M2 — MUST/SHALL/SHOULD | 19 / 11 | 63% | **1 of 26** | `data-formats.md` 12% | 22 of 26 |
| **M3 — MUST/SHALL only** | **19 / 0** | **100%** | **1 of 26** | `data-formats.md` 12% | 22 of 26 |

> **Correction adopted from policy review (§F.5):** the draft published **59%**, which reproduces under
> *none* of these matchers — it came from an ad-hoc mid-exploration keyword set that was never written
> down. The lead figure is now **M3: 19 of 19 = 100%**, which is both reproducible and stronger.

**ISP's 18 SHALLs and its single MUST (`:94`) are all inside fenced blocks. It has zero MUST/SHALL in
prose.** It carries **7 fenced blocks and 0 language labels** (all 14 markers bare).

**Nothing is charged.** No instrument in this corpus has a fence-excluding domain — there is no
normative-keyword extractor, conformance-matrix generator, or lint rule over `core-spec/` at all
(`.github/workflows/` = 4 workflows, none of which reads `core-spec/` for modality). Absence is not
prohibition (v16), and a defect needs an enforcer (v50). The value of the measurement is diagnostic:
it is the structural explanation for why ISP — alone among the core specs — has **no schema, no test
vector, and no conformance surface of any kind**. Its entire normative payload lives in a form nothing
in the corpus can read. Recorded for whoever builds the first modality extractor; ISP is where it will
either work or fail first.

---

## §E. Deferral row — 6 of 6 discharged (C330 §F.4, pre-registered, not backfilled)

| # | item | disposition |
|---|---|---|
| 1 | `ledgers/reference/go/lct/document.go` (C330's *"highest-value member"*) | **NEGATIVE.** 3 subject-matter hits, **all `birth_witnesses`** (`:106`, `:409`, `:412`) — the *same class* C290 ruled LCT-track/`C60-B1` for the TypeScript twin. Passing C290's M2 packaging criterion changes the *admissibility* of the tree, not the *subject matter* of its hits. Noted in passing (not charged, not ISP's): go/ts/python reference ledgers all encode ≥3 birth witnesses as a **warning** and ≥1 as the **error** — three parallel implementations, identical wording; that is LCT-track's row. |
| 2 | `web4-trust-core/` beyond `wasm.rs` (36 files) | **NEGATIVE.** 29 non-`pkg/` tracked files; **0** ISP subject-matter hits outside `wasm.rs`, which C330 already reach-escalated. Row closed. |
| 3 | `ledgers/reference/python/governance_audit.py` + `go/lct/document_test.go` | **NEGATIVE, both arms.** 0 hits on every ISP token *and* on `birth_witness`. The per-arm ruling C330 asked for: neither arm carries ISP subject matter, so the M2 split does not need adjudicating for this lineage. |
| 4 | ISP's non-prose artifacts beyond the one schema C290 machine-validated | **PAID OUT → N1 + N3.** Both `:252` path tokens resolve as written (`schemas/attestation-envelope-jsonld.schema.json`, `implementation/sdk/web4/attestation.py`); the attestation JSON-LD suite is green (53 passed). ISP has **no test-vector directory** — but only **14 of 30** core-spec docs do, so that is a corpus fact, not an ISP defect (v46 ratio test). |
| 5 | `test-vectors/federation/sal-governance.json` from ISP's side | **NEGATIVE.** 0 occurrences of `secess`/`dissol`/`first_contact`/`constituent`/`reification`/`minimum`. The file declares `spec = web4-standard/core-spec/web4-society-authority-law.md`. **The one vector directory named for ISP's subject matter belongs to SAL** — C326's ruling from the SAL side is confirmed from ISP's. |
| 6 | finding-id census re-run over the UNION convention | **DECLINED, with reason** (v41 — a decline licenses only its range). C330 published this instrument as **underpowered on its own numbers** (Fisher p=0.749, Wilson [0.138, 0.609], *"consistent with NO effect"*). Re-running an underpowered instrument on a 50-commit window buys no decision. **This decline covers the census only** — it does not license skipping any other citation-practice claim, and §F.1 below shows this pass got exactly that class of claim wrong by a different route. |

---

## §F. Own errors — four claims falsified by policy review, published in place

Per the standing rule, the policy reviewer received a **measured premise**, not a plan. It falsified
four claims. All four corrections were **independently verified against the cited artifacts before
adoption** — including the reviewer's own cites, two of which the lineage has previously found to be
fence lines. All 14 reviewer path/line tokens resolved as written this time.

1. **"`atp_settlement` appears in only 3 files corpus-wide" — FALSE, undeclared denominator (v40).**
   Truth: **21 files** repo-wide — 3 in `web4-standard/`, **9 in `docs/audits/`**, 5 in `archive/`,
   2 in `forum/`, plus `docs/what/…` and `whitepaper/PUBLISHER_CONTEXT.md`. "3" is true only under the
   silent restriction *`web4-standard/` tree only*. **This was not cosmetic: the 9 audit files the
   undeclared denominator excluded are exactly where the prior art lived**, which is how error 2
   happened. The sub-claims (0 schemas, 0 vectors, 0 other-language implementations) re-verified true.
2. **"N1 is net-new" — FALSE.** Three prior layers exist (§B.4). The matcher was this pass's own
   field name rather than the domain's vocabulary. The corrected finding — a remediation whose closure
   was scoped to one of two loci — is **stronger** than the novelty claim it replaces.
3. **"ISP `:150` is a Normative note" — OVERSTATED on three counts.** ISP has **0** RFC 2119
   declarations; `:150` carries no 2119 keyword; `(Normative)` modifies mcp §7.7.1. The lineage's own
   name for `:150` is **`B2-interim`**, recorded at `C102:54` as *"(½ of B2)"*. Hook moved to `:368`.
4. **"The SDK violates §7.4's either/or MUST" — the WIP hedge substantially excuses it.** The interim
   note downgrades that MUST to SHOULD and scopes the MUST to block *presence*. N1 re-charged against
   the **invariant** the same note expressly protects. This narrowed the finding and made it
   defensible; the draft's version would not have survived.
5. **N3's "59%" reproduced under no matcher** (§D). Lead figure replaced with **19/19 = 100%** under a
   published matcher.

**One reviewer finding was itself incorrect, and is recorded as such:** the review returned `REVISE`
partly on *"BLOCKING OMISSION — C330 pre-registered a six-item deferral row and the scope discharges
none of it."* **All six had in fact been discharged before review** (§E) — they were written into the
session log's Step 3 but **omitted from the reviewer's prompt**. That is this pass's prompt-construction
error, not a scope omission; the reviewer reasoned correctly from what it was given. Recorded because
the lineage's rule is that an instrument's misses are as reportable as its hits: **a policy reviewer
can only falsify the premise it is shown, so the premise must carry the deferral dispositions.**

---

## §G. Instruments (every count carries the command that produced it)

```bash
# §A freeze / window
git diff 0405f331 HEAD -- web4-standard/core-spec/inter-society-protocol.md      # empty
git log --oneline 89251abc..HEAD | wc -l                                          # 50
git diff --name-only 89251abc..HEAD | wc -l                                       # 41

# §A.1 outbound cross-reference resolution (20/20) — matcher described in §A.1
#   backticked *.md + SAL alias, self-ref markers reset pairing, match ATX headings

# §B.3 executed round-trip (6 arms, run from implementation/sdk/)
python3 -c 'from web4.mcp import CrossSocietyContext; ...'   # full script in session log

# §B.5 caller count / gate domain
git grep -n CrossSocietyContext -- web4-standard/                                 # 22, 0 production
git grep -ln atp_settlement -- web4-standard/schemas/ web4-standard/test-vectors/  # 0
git grep -il 'atp_settlement|CrossSociety' -- '*.rs' '*.ts' '*.go'                 # 0
cd web4-standard/implementation/sdk && python3 -m pytest tests/ -q -k mcp          # 164 passed

# §C
find web4-standard -type d \( -name valid -o -name invalid -o -name edge-cases \)  # 0
ls -d web4-standard/test-vectors/*/ | wc -l                                       # 22

# §D matchers M1/M2/M3 over web4-standard/core-spec/*.md (30 files, 26 with keywords)

# §F.1 corrected denominator
git grep -ln atp_settlement | wc -l                                               # 21
```

---

## §H. Carries, and the deferral row pre-registered for C410

**HELD by byte-freeze, do NOT re-derive:** `C62-B12` (§6.2 items 1–2 tested by role existence; item 3
absent from both impls) — C62 already weighed and rejected the `role.py` docstring defense; `C174-N1`
(third *documentation* surface at the npm boundary, C330); `C290-N1`; `C330-N1` (loci are
`society.rs:225` + `role.py:341`); `C330-N2` → operator with `C60-B14`. Design-Q B1/B2-full/B10/B11/B15
+ SAL-bundle B13 → operator, STAND.

**REFUTED / DECLINED — do NOT re-file:** ISP §6.2 item 3 as a fresh finding (= `C62-B12` verbatim);
the birth-witness distinctness charge (refuted at C290); `constellation.rs` as an ISP mirror; ISP `:252`
schema machine-validation (PASSES); Gate 3 ontology (NEGATIVE); `hub/` as an ISP mirror (M1-EXCLUSION,
re-confirmed at C330).

**NEW this pass:** ISP's 20/20 outbound cross-references resolve — do not re-run on an unchanged blob.
ISP is **1 of 16 of 30** core-spec docs unlinked from `web4-standard/README.md` (README-wide fact, not
an ISP defect; ISP *is* indexed from root `README.md:46` and `STATUS.md`). ISP has no vector directory,
but only **14 of 30** core-spec docs do.

### FRESH DEFERRAL ROW, pre-registered for C410 (named in advance, not backfilled)

1. **The other two members of the §7.4 family.** `mcp-protocol-internal-consistency-2026-05-15.md`
   raised **F1–F9**; `C35` closed six `SUPERSEDED`, all citing spec loci. **F3 and F4 had an SDK
   locus. Do the other four?** `F8` (§4.1↔§7.4 header reconciliation) is the strongest candidate — it
   is about the same envelope, and `mcp.py` implements both header shapes. **Highest-value member.**
2. **The `SUPERSEDED`-scope question as a class.** How many `SUPERSEDED` verdicts corpus-wide cite a
   *spec* locus for a defect that also had a *code* locus? A tractable version: for each `SUPERSEDED`
   row in `docs/audits/`, does a remediation commit touch **only** `*.md`?
3. **`sdk/CHANGELOG.md` as a conformance-claim surface.** `:9-13` advertises §7.3–7.6 conformance
   against a PR that predates the spec remediation. C362 found the same shape in `dictionary.py:20`
   (*"Validated against:"* a vector file nothing loads). **Is the SDK changelog a systematic
   over-claim surface?** Enumerate every `implements §X` claim in it and check each against the
   current spec text.
4. **ISP's 7 unlabeled fences** — if any modality extractor is ever built, ISP is its first test case
   (§D). Check whether one has appeared.
5. **`docs/what/specifications/FEDERATION_CONSENSUS_ATP_INTEGRATION.md`** — surfaced by §F.1's
   corrected denominator, carries `atp_settlement`, and is in **no** ISP-lineage document. Never read
   by this lineage.

**Rotation** advances +40 → next ISP delta = **C410**. Next slot per the standing order: **C372 =
`entity-types`** (carries `C364-N3` and `C368-N1`).

---

*C371 = declared NO-OP. N1 routes to the SDK track (do not self-fix; `C35:110` forbids piecemeal
patching of the §7.7 cluster). N2 routes to the test-vectors/conformance-harness track. N3 is
INFO-only. The `SUPERSEDED`-scope operator question couples with `C60-B14`. **Zero mutation this
pass.***
