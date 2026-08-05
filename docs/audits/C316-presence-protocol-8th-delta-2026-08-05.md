# C316 — Presence Protocol Eighth-Delta Re-Audit

**Date:** 2026-08-05
**Auditor:** Autonomous session `legion-web4-20260805-060032`
**Document audited:** `web4-standard/core-spec/presence-protocol.md` (722 lines, blob `6414a7fe`, last moved `0beb1b93` 2026-06-23 — **43 days byte-frozen**)
**Window:** `git rev-list 001cce96..HEAD` = **59 commits**, HEAD `e8005332`
**Method:** §A hand-verification at live HEAD, every anchor re-grepped. §B window pass. §C the coverage sweep, with the swept set **pre-registered before reading** (v14). §D refutations.
**Lineage:** internal-consistency (2026-05-17) → C38 (1st) → C88 (2nd, 4 findings) → C89 (remediation, `0beb1b93`) → C127 (3rd, 1 net-new LOW) → C160 (4th) → C198 (5th) → C236 (6th) → C276 (7th, #584) → **C316** (this 8th delta).

---

## Result

**0 net-new · 1 MED reach-escalation · 4 INFO · 2 REFUTED · ZERO mutation of `web4-standard/`.**

For the fifth consecutive delta `presence-protocol.md` itself is clean. Everything below was surfaced *by* presence's coverage sweep and routes **out** of this lineage: **an `ACTIVE`-status design decision declares "resolved" a divergence that a later audit independently rated MEDIUM, on a stated factual ground that is false and was false the day it was written.**

**The pass's most useful output is a correction to its own instrument.** The `lct://` finding was drafted as net-new on the strength of a published zero — `grep -rlF "lct://" docs/audits/` = 0. There are **two `docs/audits/` trees**, the matcher only ever entered one, and the other contains the audit that already found it (C33 E-M1, 2026-06-05, MEDIUM, uncited for 61 days). The false negative was caught by the post-write re-run and not by any reasoning. Every absence this lineage has certified over `docs/audits/` alone inherits the same defect.

---

## Instrument note — the window is not the yield surface

| Measure | Value | Matcher |
|---|---|---|
| Window size | **59** commits | `git rev-list --count 001cce96..HEAD` |
| Window commits touching **any** presence artifact | **0** | `git log --oneline 001cce96..HEAD -- '*presence*'` |
| Target byte-frozen | **43 days** (`0beb1b93`, blob `6414a7fe`, 722L) | `git hash-object` |

`8d3808db` (#637) was initially miscounted here as a presence touch. It is not: it touches exactly two files, `.github/workflows/vector-context-refs.yml` and `web4-standard/test-vectors/validate_context_refs.py`. That matched the **tree**, not the **artifact** — an error of the same class this lineage keeps charging in others, caught in policy review before the pass opened.

Frozen target + a window with **zero** subject-matter commits is the configuration method carry **v13** names as the one in which a false clean is most likely. So the pass was pointed at the artifact tree, and the entry question was **coverage**, measured before anything was read.

### Swept set, pre-registered (v14 — derived in BOTH citation directions)

**Outbound** (what `presence-protocol.md` cites): `mcp-protocol.md`, `presence-protocol-CHANGELOG.md`, `schemas/presence-protocol/v0/tools/hestia_connect.schema.json`, `testing/conformance/presence-protocol-conformance.json`.
**Inbound** (what cites it, excluding `docs/audits/`): `core-protocol.md`, `did-web4-method.md`, the 12 schemas, `testing/conformance/README.md`, `docs/SPRINT.md`, `whitepaper/PUBLISHER_CONTEXT.md`.

**Neither direction reaches the artifacts that turned out to matter** — because they never use the token `presence-protocol`. They had to be found by grepping the *behaviour*, not its vocabulary ([[feedback_guard_names_a_path_not_a_behaviour]]):

| Artifact | Named in `docs/audits/**` | Lines | Last moved |
|---|---|---|---|
| `web4-standard/core-spec/presence-protocol-CHANGELOG.md` | 11 files | — | — |
| `web4-standard/testing/conformance/presence-protocol-conformance.json` | 10 files | — | — |
| `web4-standard/schemas/presence-protocol/` | 8 files | — | — |
| **`docs/what/specifications/LCT_UNIFIED_PRESENCE_SPECIFICATION.md`** | **0 files, ever** | 738 | `0aa2f2c2` 2026-02-18 |
| **`docs/why/lct_witnessed_presence.md`** | **0 files, ever** | 209 | `618345ae` 2026-02-05 |
| **`docs/history/research/presence-terminology-bridge.md`** | **0 files, ever** | 65 | `b76062f1` 2026-02-26 |
| **`archive/reference-implementations/lct_unified_presence.py`** | **0 files, ever** | 763 | `65cd5488` 2026-04-11 |

Matcher `grep -rlF <token> docs/audits/ web4-standard/docs/audits/` at HEAD `e8005332`; `-F` per C314's guard 6 (these tokens carry `.` and `_`). **Both audit trees** — the single-tree form this lineage has always used is the defect §C.3 I-4 records; the four zeros are unchanged under the widened scope, the CHANGELOG/conformance counts too. Re-run **after** this document was written; the self-collision is excluded.

**Four presence-named artifacts had never been read in seven passes, one of them a 738-line parallel presence specification.** That is what justified a full pass rather than the capped NO-OP record the pre-registered proportionality clause would otherwise have required.

## Authority Hierarchy

Unchanged from C127/C160/C198/C236/C276: vectors → schema → SDK → spec prose; canonical neighbor owns its primitive. `forum/` and `archive/` excluded per the standing rule.

---

## §A — Delta Re-Verification

### §A.1 — Target: byte-frozen, 0 regressions

Blob `6414a7fe` at HEAD, identical to C276's recorded baseline. 12 schemas (3 `v0/common` + 8 `v0/tools` + 1 `v1/tools`), 14 conformance scenarios — both re-counted at HEAD, not inherited.

### §A.2 — The C236/C276 consumer gate: re-derived, still **NEGATIVE**

Per C276's own method guard, the consumer set was derived from `grep -rlE "hestia_"` across **all** languages first and then narrowed — not by reusing the prior delta's token list.

That sweep returns two `hub/hub-daemon/` files C276's record does not name: `admin.rs` and `main.rs`. Both are **adjudicated NOT net-new**:

- `admin.rs:1090` — the token appears inside a **comment** (`// hestia_sovereign_lct`, a rename note). Not a call site.
- `main.rs:1658` — `hestia_callback_url`, the vault **signing callback** C276 §B′.1 already adjudicated: hub → hestia `/sign-request`, *not* the presence MCP tool surface.
- **Snapshot-presence guard** ([[feedback_snapshot_presence_guard]]): both files were born `31e4407a` / `b2b4b611` on **2026-06-07**, seven weeks before the C276 snapshot. The window touched them 12 times, but on the hub's own plane-split/ledger/atomic-write work — not on the presence surface.

**Gate stays NEGATIVE: still no presence-protocol twin in Rust or Python.** C276's B′.1 adjudication is confirmed, not merely inherited.

### §A.3 — C198 B.2 trigger re-check: **NOT fired**

The carry goes present-tense only if `web4-policy` (or a successor) becomes the presence daemon's engine. `grep -rn "presence" web4-policy/src/*.rs` = **0**. The crate still evaluates society law, not host-local presence policy. Carry remains dormant, re-check obligation unchanged.

### §A.4 — C127-1: **half-closed, cross-track facet STILL OPEN**

`ls web4-standard/schemas/presence-protocol/v0/common/` = `error_envelope`, `trust_state`, `witness_entry`. **No `Session`, no `VaultEntry`.** The autonomous facet was closed at C128 (`cf0d6cc5`, #439); the cross-track schema-authoring facet is open and unchanged. **Do not re-charge the closed half.**

### §A.5 — Carry ledger: rows survive, 0 regressions

C276's routed items all re-verified present and unchanged: the §8 drift-table row (operator-owned, descriptive), I-2 `request_scope` (proposal authors), I-1 → C272-N1, Gate 2 → C274-N1. No row emptied ([[feedback_ledger_emptied_not_closed]]).

---

## §B — Window pass

59 commits, **0** touching a presence artifact. The window's hub work (12 commits) is the only inbound with any surface contact, and §A.2 disposes of it. **No net-new finding against `presence-protocol.md`.** Fifth consecutive delta clean against the spec.

---

## §C — Coverage sweep

### §C.1 — `LCT_UNIFIED_PRESENCE_SPECIFICATION.md` — **DECLINE + venue correction (I-1, INFO)**

A 738-line "Draft for Cross-Project Integration" (v1.0.0, dated 2025-12-17, Legion Session 62+ autonomous research), unread in seven presence passes. It specifies `lct://{component}:{instance}:{role}@{network}` as a unified presence format across ACT / SAGE / Web4.

**It is not presence-protocol's subject matter.** `presence-protocol.md` specifies the hestia **MCP tool gate** — `hestia_connect`, `query_policy`, vault, witness. This document specifies an **LCT identifier/addressing URI**. They share the word "presence" and nothing else: the same lexical-collision class C236 §B.2/B.3 refuted. **It is therefore DECLINED here as a presence finding and its subject matter routed to the LCT lineage** (`LCT-linked-context-token.md` C328 / `web4-lct.md` C342), which is where §C.2 files it.

Unlike C314's `forum/nova/ACP-bundle/`, this artifact is **not inert**: it is cited by 13 files, and its scheme is implemented in `ledgers/reference/go/lct/uri.go` and `ledgers/reference/typescript/lct-parser.ts`. The decline is about **venue**, not about the artifact being dead.

The other three unread artifacts are prose/archive with no normative surface: `docs/why/lct_witnessed_presence.md` (motivational), `docs/history/research/presence-terminology-bridge.md` (65L Synchronism↔Web4 glossary), `archive/reference-implementations/lct_unified_presence.py` (excluded tree). **No finding; recorded so seven silences are not read as coverage.**

### §C.2 — **N1 (MED, reach-escalation on C33 E-M1 + one net-new locus, routed to the LCT lineage)** — an ACTIVE design decision declares "resolved" what a later audit rated MEDIUM and undocumented, on a premise that is false

**Classification first, because the draft of this section got it wrong.** The existence of an undocumented `lct://` scheme is **NOT net-new**: `web4-standard/docs/audits/C33-identifier-scheme-consolidation-audit-2026-06-05.md:86-89` already filed it as **E-M1 (MEDIUM, CROSS-TRACK)** — *"An `lct://` URI scheme appears in the SDK and attestation vectors but is defined in NO spec"* — naming it the **fifth** identifier surface in the corpus. My first draft published "the `lct://` scheme has not been mentioned once in the entire C-series." That was false, and §C.3's I-4 records why I could not see it. What this pass contributes is **reach** on E-M1 plus **one genuinely new locus**.

**E-M1 is still open and has never been re-verified.** `grep -rlF "E-M1" .` (excluding `.git/`) returns **exactly one file — C33 itself**. In 61 days no audit, carry ledger, or remediation has cited it.

**The net-new locus: the corpus holds a ratified "resolved" and an open MEDIUM on the same object, and the "resolved" came first.** `docs/history/design_decisions/LCT-SPEC-RECONCILIATION-2026-02.md` is **`Status: ACTIVE`** (`:4`) and dated **2026-02-19**. Its §2.6 table (`:109-112`) records four divergent LCT id formats and resolves them at `:114-117`. **Three and a half months later, C33 audited the same scheme and rated it MEDIUM and undocumented** — with no citation of this decision in either direction. One of the two is wrong about whether this is settled, and neither knows the other exists:

> **Resolution**: The URI format (`lct://...`) is a transport/addressing format. The document format (`lct:web4:...`) is the identity format. Both are valid in different contexts. **The JSON schema regex is intentionally permissive to accommodate both.** This is not actually a conflict — it's two views of the same identity.

**The split is sound and is not challenged here. The stated ground for it is false.** Machine-checked with controls:

| Regex (site) | `lct:web4:mb32:bafkxyz` — the Core Spec's own form, `:110` (**control, must PASS**) | `lct://sage:thinker:expert_42@testnet` — the transport form | `lct://test:challenge` — an in-standard vector value |
|---|---|---|---|
| `lct.schema.json:11` `^lct:web4:[A-Za-z0-9_:-]+$` | **PASS** | FAIL | FAIL |
| `t3v3.schema.json:11,124` `^lct:web4:[A-Za-z0-9_-]+$` | **FAIL** | FAIL | FAIL |
| `trust-query.schema.json:22,27` `^lct:web4:[A-Za-z0-9_-]+$` | **FAIL** | FAIL | FAIL |

Two things follow, and the control is what separates them:

1. **No schema regex in the standard accommodates the transport form.** Not one. The resolution's load-bearing clause is false as written.
2. **The regex the doc quotes at `:111` and calls "Permissive" rejects the format the same table names as the Core Spec's, one row above at `:110`.** `lct:web4:mb32:{hash}` carries a third colon; `[A-Za-z0-9_-]` excludes `:`. The table contains its own counterexample.

**Reach measured — new evidence C33 did not have.** C33 cited two example sites (`generate.py:75`, `attestation-vectors.json:13`). At HEAD, scoped to executable artifacts (`grep -rhoE "lct://[^\"' )]*"` over `web4-standard/implementation/sdk/` + `web4-standard/test-vectors/`): **30 distinct values across 7 files**. Over all of `web4-standard/` the same matcher gives **34 across 8** — the extra 4 are prose fragments inside C33 itself, which is why the scope is stated per figure rather than once.

- **24 of the occurrences sit in a field named `entity_id`** — an *identity* field, carrying the *transport* form the ratified split assigns to addressing.
- They validate for exactly one reason: `attestation-envelope-jsonld.schema.json`'s `entity_id` is `{"type":"string","minLength":1}` with **no `pattern`**.
- **22 of the 30 fail even the transport grammar.** `ledgers/reference/go/lct/uri.go:71` requires all four of `component:instance:role@network`; `lct://test:challenge` and `lct://web4:ca` supply two. Under the ratified split those values are neither a valid identity nor a valid address — a case neither C33 nor the decision anticipated.

**Severity MED, and the class change is the reason.** C33 rated E-M1 MEDIUM on the ground that the scheme is undocumented. That severity is *unchanged* by this pass — but its **class** is: the divergence is not merely undocumented, it is **documented as resolved**, by an ACTIVE decision resting on a false clause. Per v16 a class change routes as reach-escalation, not net-new, which is how it is filed.

- **Bounded by the consumption mechanism** (v13): the values are test fixtures, nothing parses them as URIs, and the governing schema imposes no pattern — **latent, not a live failure**. The severity is carried by the standing decline, not by a broken build.
- **Why the false clause is the expensive part.** Its function is to make future passes decline this divergence. That is not hypothetical: **this pass built the collision finding, found this decision, and was about to close on it** (§D R-1) — the false clause is precisely what would have closed it, 61 days after C33 rated the same object MEDIUM. A wrong premise inside a standing decline is worse than a wrong prose line because it is *designed* to be cited. [[feedback_remediation_born_false]] — dated against the artifacts it describes, it was false on 2026-02-19.
- **Routed, not applied**, and **not to presence.** At least three legitimate fix shapes (correct the clause and keep the split; admit the transport form to a pattern; put a `pattern` on `entity_id` and migrate the 24 vectors). It belongs to the LCT lineage plus the attestation-envelope owner, and it should be adjudicated **together with C33 E-M1**, not separately. Presence's slot is not the venue for an LCT-identity remedy.

### §C.3 — Three instrument corrections (I-2, I-3, I-4, INFO)

**I-4 — there are TWO `docs/audits/` trees, and every coverage grep this lineage has ever published reaches only one of them.** The rotation's standard matcher is `grep -rlF <token> docs/audits/`. It does not enter **`web4-standard/docs/audits/`**, which holds two cross-cutting audits invisible to it:

| File | Date | Subject |
|---|---|---|
| `C33-identifier-scheme-consolidation-audit-2026-06-05.md` | 2026-06-05 | The identifier-scheme consolidation — **4H + 4M + 1L + 3 INFO**, 39 confirmed / 4 refuted. Holds **E-M1**, the `lct://` finding §C.2 needed |
| `C75-protocols-cluster-lifecycle-triage.md` | 2026-06-19 | The `protocols/` cluster triage — **the D0 gate** that still blocks that cluster's remediation |

Consequences, all measured at HEAD:

- `grep -rlF "E-M1" .` = **1 file, C33 itself**. A MEDIUM cross-track finding has sat 61 days without a single citation.
- `grep -rl "C33-identifier" docs/audits/` = **0**. The document is never referenced by path from the tree the rotation reads.
- **I committed this exact error in this document's own first draft**, publishing "the `lct://` scheme has not been mentioned once in the entire C-series" — a negative certified over a tree that excluded the one file which contradicted it. It was caught only because the post-write re-run widened the scope from `implementation/sdk/`+`test-vectors/` to all of `web4-standard/`, and an unexpected 8th file appeared in the output. Had the two counts agreed, the false negative would have shipped.
- This is the **same defect class as I-3** — a gate or a grep phrased as a path, silently missing a sibling tree ([[feedback_gate_scoped_to_wrong_tree]]) — occurring twice in one pass, once in the corpus and once in my own instrument. **Any coverage or absence claim in the C-series stated over `docs/audits/` alone should be re-measured over both trees before it is relied on.**

**I-2 — the lineage's "consecutive clean" count is not derivable as published.** C236 reads *"sixth consecutive substantive-CLEAN presence delta"* and C276 reads *"Seventh consecutive delta with zero net-new findings against the spec."* Both slide between the delta's **ordinal** and the **length of the clean run**. Derived from each doc's own Result line: C88 (2nd) yielded 4 findings, remediated at C89 — which *is* the freeze commit `0beb1b93`; C127 (3rd) yielded 1 net-new LOW (C127-1). The strictly-zero-net-new run is **C160, C198, C236, C276 = 4**, and C316 is the **5th**. C316 is the **8th delta**, not the 8th clean one.

A second qualifier belongs with it: "zero net-new" in these docs is scoped *against the spec* / *autonomous*. C198 still produced a forward-compat INFO and C276 a LOW to proposal authors plus two INFO folded into other findings. **2 of the last 4 "clean" passes produced routable output.** The lineage is not zero-yield, and the phrase should always carry its qualifier or it will seed the next conflation. Per [[feedback_enumeration_and_grep_hypotheses]], re-derived from ground truth rather than inherited.

**I-3 — #637's new `@context` gate does not reach presence, and the reason is a two-tree split.** The gate walks `web4-standard/test-vectors/` (**25** entries, `ls | wc -l`), which contains **0** presence directories. Presence's 14 vectors are `scenarios` **inside** `web4-standard/testing/conformance/presence-protocol-conformance.json` — a **sibling tree the gate never enters** — and that file contains **0** occurrences of `@context`. So the gate result for presence is **vacuous on two independent grounds**. Recorded, not fixed. The corpus carrying two `test-vectors`-shaped trees under different parents is a standing scope hazard for any gate phrased as a path ([[feedback_gate_scoped_to_wrong_tree]], [[feedback_guard_names_a_path_not_a_behaviour]]) — noted for the operator, not charged here.

---

## §D — Refutations

**R-1 — FLAGSHIP, REFUTED: "the corpus carries two colliding LCT identifier schemes."** The strongest-looking finding of the pass: `lct:web4:…` in the normative core-spec versus `lct://…@network` in the SDK, the vectors, two reference implementations and a 738-line spec, with **zero** occurrences of `lct://` anywhere in `web4-standard/core-spec/`. **Killed by `LCT-SPEC-RECONCILIATION-2026-02.md:114-115`**, which ratified the two-scheme split — transport vs identity — on 2026-02-19. The split is a *design*, not a drift, and charging it would overturn a standing decision. What survived the refutation is strictly narrower and is **not** the collision: only the decision's false factual premise (§C.2). **Do not resurrect the collision charge without first overturning that resolution.**

**R-2 — REFUTED: "presence-protocol.md is silent on the `lct://` scheme its own SDK emits."** True and irrelevant. Presence specifies an MCP tool gate; LCT identifier grammar is `LCT-linked-context-token.md`'s primitive under the standing authority hierarchy ("canonical neighbor owns its primitive"). Filing it at presence's slot would be the venue error C236 §B.2/B.3 already refuted twice. **Not a presence finding.**

**C276's killed flagship was not re-opened.** The "spec is silent on its no-verdict posture ⇒ LCT §1.2 evidence gap" charge remains refuted by the three facts C276 verified, and its three do-not-reopen items (`HestiaCallbackSigner`, `web4-policy`'s `Escalate`, the §7 conformance-vector gate) were not re-derived — §A.2 confirms the first two rather than re-charging them.

---

## Findings

| # | Severity | Class | Disposition |
|---|---|---|---|
| **N1** | **MED** | **reach-escalation on C33 E-M1 + 1 net-new locus — NOT net-new, routed OUT of this lineage** | `LCT-SPEC-RECONCILIATION-2026-02.md:114-117` (status **ACTIVE**, 2026-02-19) declines the `lct://` vs `lct:web4:` divergence on the ground that *"the JSON schema regex is intentionally permissive to accommodate both"*. **No regex in the standard accommodates the transport form**, and the one quoted at `:111` as "Permissive" **rejects the Core Spec's own `lct:web4:mb32:{hash}` named at `:110`**. C33 E-M1 rated the same scheme MEDIUM and undocumented 3½ months later; neither artifact cites the other, and E-M1 has **0** citations in 61 days. New reach: 24 `entity_id` values carry the transport form, validating only because that schema has no `pattern`; 22 of 30 fail the transport grammar too. Latent. **Adjudicate WITH C33 E-M1; routed to C328/C342 + the attestation-envelope owner; not applied** |
| **I-1** | INFO | coverage + venue | Four presence-named artifacts at **0 of 7 passes**, incl. a 738-line parallel presence spec. **DECLINED as presence findings on venue** (LCT identity ≠ the MCP presence gate); subject matter routed via N1. Published so seven silences are not read as coverage |
| **I-2** | INFO | instrument | The lineage's "N consecutive clean" count conflates delta **ordinal** with clean-**run** length. Ground truth: strictly-zero run = **4** (C160/C198/C236/C276); C316 is the 8th delta, 5th clean. "Zero net-new" is scoped *against the spec* — 2 of the last 4 clean passes still produced routable output |
| **I-3** | INFO | instrument | #637's `@context` gate is **vacuous for presence on two independent grounds**: it walks `test-vectors/` (0 presence dirs) while presence's 14 scenarios live in the sibling `testing/conformance/` tree, which has 0 `@context` occurrences. Recorded, not fixed |
| **I-4** | INFO | **instrument — affects the whole C-series, not just presence** | There are **two `docs/audits/` trees**. Every coverage grep this lineage publishes is scoped to `docs/audits/` and never enters `web4-standard/docs/audits/`, which holds **C33** (the identifier consolidation, 4H+4M+1L, source of E-M1) and **C75** (the `protocols/` triage, i.e. the **D0 gate**). This pass published a false zero off that matcher and caught it only on the post-write re-run. Any absence certified over one tree should be re-measured over both |
| — | REFUTED | — | ×2, incl. the flagship (§D) |

**ZERO mutation of `web4-standard/`.** No spec, schema, vector or SDK file was edited.

**No accountability self-audit block:** this pass creates no surface and performs no consequential act — it writes one document under `docs/audits/`.

---

## Guards for the next presence delta (C356)

1. **C276's guards all still bind** and were honoured here: the no-verdict-posture flagship stays killed; `HestiaCallbackSigner`, `web4-policy`'s `Escalate`, the AAEP triple, the "absence grants" witness and the §7 conformance-vector gate stay closed. C276's header predicts "~C312"; **rotation arithmetic gives C316** (last pass + 40) — reconciled here so the next pass does not trip on it. **Next presence slot = C356.**
2. **These artifacts are now IN presence's swept set and may not contract back out silently** (v8): the four at 0 of 7 passes in the coverage table. Three are declined as non-normative (cite §C.1); `LCT_UNIFIED_PRESENCE_SPECIFICATION.md` is declined **on venue** — do not re-derive, and do not re-file it at presence's slot.
3. **REFUTED-GUARD — do not resurrect** without first overturning the ruling that killed it: (a) "two colliding LCT identifier schemes" → killed by `LCT-SPEC-RECONCILIATION-2026-02.md:114-115` (ratified split, 2026-02-19); (b) "presence is silent on `lct://`" → killed by the authority hierarchy's canonical-neighbor rule + C236 §B.2/B.3.
4. **N1 is routed OUT of this lineage.** If C356 finds it still open, that is a routing failure to report, **not** a presence finding to re-charge — and it must be checked **together with C33 E-M1**, which it escalates rather than replaces. Pre-registered regression greps: `grep -rlF "E-M1" .` (was **1** — C33 itself — meaning still uncited); does `attestation-envelope-jsonld.schema.json`'s `entity_id` carry a `pattern` (was **no**); does `LCT-SPEC-RECONCILIATION-2026-02.md:117` still claim the regex is "intentionally permissive to accommodate both" (was **yes**, and false).
4b. **Search BOTH audit trees** (I-4). `grep -rlF <token> docs/audits/ web4-standard/docs/audits/`. A zero published over the first tree alone is not a zero. This pass shipped one such zero into a draft finding and caught it by accident, not by reasoning.
5. **Live carries:** C127-1 **cross-track facet** (no `Session`/`VaultEntry` under `v0/common/`) — half-closed, do not re-charge the C128-closed half. C198 B.2 trigger — re-check whether `web4-policy` has become the presence daemon's engine (`grep -rn "presence" web4-policy/src/*.rs`, **0** this pass).
6. **Method, born this pass:** the swept set must be derived from the **behaviour**, not the vocabulary. Both citation directions on the token `presence-protocol` returned a well-covered set and **missed all four uncovered artifacts**, because none of them uses that token. A mirror set derived only from what cites the target by name will certify a coverage that does not exist.
7. **Proportionality:** if C356 opens on an empty window *and* the coverage table in §C is already complete, the correct output is a **capped one-page NO-OP record**. This pass ran full-length because four artifacts had never been read — that justification is now spent.
