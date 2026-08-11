# C356 — Presence Protocol Ninth-Delta Re-Audit

**Date:** 2026-08-10
**Auditor:** Autonomous session `legion-web4-20260810-180000`
**Document audited:** `web4-standard/core-spec/presence-protocol.md` (722 lines, blob `6414a7fe`, last moved `0beb1b93` 2026-06-23 — **48 days byte-frozen**)
**Window:** `git rev-list e8005332..HEAD` = **55** commits, HEAD `9958fc6a`
**Form:** SHORT. C316 guard 7 caps this slot at a NO-OP record unless the pass asks a question no instrument has asked. It did, so one finding is filed; the full coverage-table / mirror-set apparatus is **not** re-run, per that guard.
**Lineage:** internal-consistency (2026-05-17) → C38 → C88 → C89 (remediation, `0beb1b93`) → C127 → C160 → C198 → C236 → C276 (#584) → C316 (#644) → **C356** (this 9th delta).

---

## Result

**1 net-new LOW · 2 INFO · 2 REFUTED (one of them this pass's own first draft) · ZERO mutation of `web4-standard/`.**

The spec is clean for the sixth consecutive delta. The one finding is against the **schema tree's own authority rule**, and it is this: `presence-protocol.md` §7 supplies a precedence procedure — *"where this document's prose and the JSON Schemas disagree about a wire shape, the Schemas and vectors are normative and the prose is in error"* — and **for 14 of the tree's 20 declared value constraints, "disagree" has no determinate answer.** Those 14 are `format`, which the tree's own declared draft makes annotation-only; the other 6 are `pattern`, which always assert. The standard nowhere states which reading applies, and the document's single elision convention lands on **both sides of that line**.

---

## §A — Delta re-verification

### §A.1 — Target and window

| Measure | Value | Matcher |
|---|---|---|
| Blob | `6414a7feecf1ef7760bbed0ae2cc279317c4006e`, 722 L — identical to C316's baseline | `git hash-object` |
| Byte-frozen | **48 days** (`0beb1b93`, 2026-06-23, #380) | `git log -1 --format=%ad -- <path>` |
| Window | **55** commits (`e8005332..HEAD`, HEAD `9958fc6a`) | `git rev-list --count` |
| Window commits touching a presence artifact | **0 of the 16 non-audit artifacts** | `git log e8005332..HEAD -- $(git ls-files \| grep presence-protocol \| grep -v '^docs/audits')` |

**Denominator stated, per v40.** `git ls-files | grep -i presence-protocol` returns **25** paths, of which **9 are this lineage's own audit documents**. Run unfiltered, the same `git log` returns **1** commit — `2ec8e9b3`, which is C316 adding *itself*. The artifact window is empty; the unfiltered window is not, and the difference is entirely self-reference. Both numbers are published so neither is mistaken for the other.

### §A.2 — Inbound sweep (v36/v40): the residue is **empty**, and that is the recorded result

| Sweep | Matcher | Result |
|---|---|---|
| Filename | `grep -rln "presence-protocol" docs/audits/ web4-standard/docs/audits/` | **37** docs |
| Artifact-token | `grep -rlniE "presence.protocol\|hestia_connect\|hestia_begin_action\|hestia_vault\|hestia_record_outcome\|hestia_request_witness\|hestia_query_\|trust_state\|witness_entry\|error_envelope" <same two trees>` | **37** docs |
| Set difference, **both directions** | `comm -13` and `comm -23` | **empty — the two sets are identical** |

Six consecutive fires took their entire yield from this sweep, and on C350 the artifact-token form found four findings the filename form could not see. **Here it finds nothing the filename matcher missed.** Published as a negative because it is what makes the positives elsewhere interpretable: the v40 hazard is real but not universal, and on a target whose artifacts are all named after it, the cheap matcher happens to be complete. Both audit trees were swept (C316 I-4).

### §A.3 — C316's routed N1: **already discharged, by another lineage**

C316 guard 4 pre-registered *"if C356 finds it still open, that is a routing failure to report."* It is not this pass's to report.

| C316's pre-registered check | C316's value | At HEAD `9958fc6a` |
|---|---|---|
| `grep -rlF "E-M1" .` (excl. `.git`) | **1** (C33 itself) | **3** — `C33`, `C316`, **`C342-web4-lct-8th-delta-2026-08-08.md`** |
| `attestation-envelope-jsonld.schema.json` `entity_id` carries a `pattern`? | no | **no** (`:39-42`, `type/minLength/description` only) — unchanged |
| `LCT-SPEC-RECONCILIATION-2026-02.md` still claims the regex is *"intentionally permissive to accommodate both"*? | yes, and false | **yes**, `:116`, status ACTIVE — unchanged |

`C342` §F **received `C316-N1` and `C33 E-M1` into its ledger by name**, re-ran all three of these greps itself, adjudicated that C328 — C316's *first* named addressee — received none of it, and pre-registered its own regression set for C382. That work is two days old and belongs to the web4-lct lineage.

**So the correct disposition here is silence, not a second report.** Re-filing it would be the census-over-held-labels error: the row is discharged, and a lineage that re-reports a discharged row inflates its own yield with another's work. Recorded, not charged.

### §A.4 — Standing guards, re-verified positive

- **C127-1 cross-track facet — STILL OPEN.** `ls web4-standard/schemas/presence-protocol/v0/common/` = `error_envelope`, `trust_state`, `witness_entry`. No `Session`, no `VaultEntry`. The C128-closed half is **not** re-charged.
- **C198 B.2 trigger — NOT fired.** `grep -rn "presence" web4-policy/src/*.rs` = **0**. `web4-policy` still evaluates society law, not host-local presence policy. Carry stays dormant; the per-delta re-check obligation stands.
- **Consumer gate — NEGATIVE, 8th time.** Re-derived per C276's method guard from `grep -rlE "hestia_"` across **all** languages first, then narrowed — not by reusing a prior token list. Same set C316 adjudicated (`hub/hub-daemon/{admin,main,rest}.rs`, `hub/hub-lib/{envelope,hub,init,session,signer}.rs`, `web4-core/src/lct.rs`). No presence-protocol twin in Rust or Python.

---

## §B — The question no instrument has asked

Nine passes have argued *about* the presence schemas. **None has executed anything against them.** Three executions were run; `jsonschema` 4.26.0, `Draft202012Validator` selected from each schema's own declared `$schema`, `RefResolver` over the 12-schema store. Validator scope published per C163.

**1. Conformance inputs vs `$defs/input` — CLEAN.** All **17** tool-bearing nodes validate under the default vocabulary. *(The object is **nodes**, not scenarios: the file has **14 scenarios**; `tool` occurs in `steps` (14 nodes, 12 tool-bearing) **and in `setup` (5 nodes, all 5 tool-bearing)**. My first run walked `steps` only and reported 12 — see §E.)*

**2. The §6.1 error registry vs every `hestia.*` token in the repo — CLOSED.** The table holds exactly 10 codes; a repo-wide `grep -rhoE 'hestia\.[a-z_]+'` (excluding `.git/`, `archive/`, `forum/`, `target/`, `node_modules/`) returns exactly those 10, plus `hestia.rs` and `hestia.md`, which are filenames. **Zero unregistered codes.** This is the C354 shape and it does **not** fire here; published so the negative is on record.

**3. The spec's own fenced blocks vs the 12 schemas — this is where it lands.** 24 fenced blocks, **all 24 tagged `json`**; **20 parse**, **4 do not** (they carry `/* … */` comments: `:234-239`, `:400-405`, `:503-510`, `:560-570`). After comment-stripping, 20 of the 24 map to a schema.

---

## §C — N1 (LOW, net-new): §7's precedence procedure is undefined over 70% of the constraints it arbitrates

### The rule

Two artifacts, both presence's own, state the authority:

- `presence-protocol.md` §7 `:668-673` — *"Where this document's prose and the JSON Schemas at `web4-standard/schemas/presence-protocol/` … **disagree** about a wire shape — including key casing — the Schemas and vectors are normative and **the prose is in error**. The Schemas directory is normatively bound by this clause."*
- `schemas/presence-protocol/README.md:5-7` — *"These schemas are the **wire-format authority**: if a SDK or daemon serializes a shape that doesn't validate against the schema, the implementation is **non-conforming**."*

`grep -rniE "non-?conform" web4-standard/ --include=*.md | grep -iE "valid|schema"` returns **exactly one line in the entire standard** — README `:7`. No canonical neighbour owns this rule; presence invented it, so this is presence's venue and not a routed one.

### The defect

§7 is a **decision procedure**, and it runs on the predicate "disagree". For 14 of the tree's 20 declared value constraints, that predicate has no determinate value.

| Constraint kind | Sites | Asserts? |
|---|---|---|
| `format` — 11 × `uuid`, 3 × `date-time` | **14** | **No.** JSON Schema 2020-12 makes `format` an annotation by default |
| `pattern` | **6** | **Yes**, always |

All 12 schemas declare `"$schema": "https://json-schema.org/draft/2020-12/schema"`, and README `:78-79` names *"JSON Schema Draft 2020-12"* explicitly — so the annotation-only reading is the one the tree's own artifacts select. **`grep -rn '\$vocabulary' web4-standard/` = 0 occurrences.** Nothing anywhere in the standard enables a format-assertion vocabulary or states which reading a validator must use.

**Consequence.** Two implementers can both truthfully report "it validates against the schema" and disagree about conformance. A daemon emitting `"sessionId": "not-a-uuid"` is conforming under python-`jsonschema`'s default and non-conforming under Ajv with `ajv-formats`. §7 says the Schemas decide; the Schemas decline to.

### The demonstration — the document's one elision convention lands on both sides

The spec elides example values in a single style: `"97a3-..."`, `"ae27-..."`, `"abc..."`, `"sha256-hex"`, `"uuid-of-vault-entry"`. Validated against the tree that governs them:

| | Default vocabulary | Format-asserting |
|---|---|---|
| 17 mappable parsing examples | **1 failure** | **10 failures** |
| 17 tool-bearing conformance nodes | **0 failures** | 12 failures — **explained by templating, see below** |
| §5.6 WitnessEntry (comment-stripped) | **2 failures** | 2 failures |
| §3.3 `record_outcome` Output (comment-stripped) | **9 failures** | 9 failures |

- `"sha256-hex"` at §5.6 `:562-563` and `"abc..."` at §3.8 `:429` fail **under both readings**, because `witnessEntryHash`/`hash`/`prevHash` are `pattern: ^[0-9a-f]{64}$`.
- `"97a3-..."` and `"ae27-..."` pass under one reading and fail under the other, because `sessionId`/`action_id` are `format: uuid`.

**Same convention, opposite verdicts, decided by a choice the standard never makes.** That asymmetry is the evidence; it is not itself the charge.

### What is *not* charged, and why

- **The elided examples are not the finding.** §7 pre-adjudicates them: prose that disagrees with a schema *is already declared to be in error*. Charging them would re-file a verdict the spec has already entered against itself. The finding is that §7's procedure cannot be **run** on 14 of 20 sites, not that it produces an unwelcome answer on 6.
- **The 12 conformance failures under format assertion are not evidence.** Every one is an un-substituted template (`{{P0-001.sessionId}}`); a runner substitutes a real UUID first. Named and discarded rather than counted — it is the weaker arm and would have inflated the number.
- **No elision convention is disclosed.** `grep -niE "illustrativ|abbreviat|elid|truncat|placeholder|for brevity|non-normative"` over the spec and the README returns **one** hit, `:408`, about `hasMore`. So a reader supplies the placeholder-vs-literal distinction themselves; neither artifact supplies it.
- **The absent in-repo validator is NOT load-bearing and is not charged.** README `:72-74` **self-discloses** it: *"A standalone reference validator script … is planned but not yet present in this repo."* Resting weight there would re-raise the zero-repo-executors shape **C276 Gate 1 killed** (`C276:147` — §7 places the burden on the out-of-repo daemon). The finding rests solely on the vocabulary arm and would stand unchanged if a validator shipped tomorrow.

### Severity: **LOW**

Latent. The only consumer is the out-of-repo hestia daemon; the consumer gate is NEGATIVE for an eighth delta; the README discloses its own missing validator. MED would be an overcall. **Routed, not applied** — the remedy forks (declare `$vocabulary` with format-assertion; or convert the 14 `format` sites to `pattern`; or add one sentence to README `:78-79` stating the validation mode), and picking among them is a standard-owner decision, not an auditor's.

---

## §D — Corpus arm, routed (I-1, INFO) — not presence's to fix

The same question over the whole standard: **48 `format` sites vs 28 `pattern` sites across 24 `*.schema.json` files**, and `$vocabulary` = **0** anywhere.

**Disambiguation rule published with the number** (v39 — a bare count is a fork): raw `grep -rho '"format"' --include=*.schema.json web4-standard/` = **50**; subtract the **2** non-keyword positions at `attestation-envelope-jsonld.schema.json:82` (a `required` list member) and `:84` (a property *name*) ⇒ **48**. `contexts/attestation-envelope.jsonld:52` is a JSON-LD term definition and is outside the `*.schema.json` glob by filetype, not by judgement. Breakdown of the 48: `uri` 20, `date-time` 17, `uuid` 11.

Presence is the only tree with a README asserting the non-conformance rule, so presence is the only tree where the gap is *stated*. The corpus-wide version belongs to the schema-tree owner and is recorded here, not charged. Filing it at presence's slot would be the venue error C316 §C.1/R-2 charges twice.

---

## §E — REFUTED, including this pass's own drafts

**R-1 — REFUTED: "`status: evaluating` cannot be serialized without asserting a verdict."** The strongest-looking draft finding. `v1/tools/hestia_query_policy.schema.json` makes `decision` **required** with a closed 3-value enum `{allow, deny, warn}`, so an engine that has *no* verdict must still emit one — apparently a state the standard cannot serialize, in the C350/C352/C354 shape. **Killed by §3.4.1 `:296-297`**: *"When `status == "evaluating"`, `decision` carries the engine's current **tentative** verdict (usually the default policy)."* The spec answers the exact question, in the paragraph that defines the state. Drafted, then refuted by reading four lines further. It would also have grazed C276's killed flagship.

**R-2 — REFUTED: "the §3.8 output example fails its own schema" as a standalone finding.** True (`"abc..."` vs `^[0-9a-f]{64}$`) and, alone, worth nothing: §7 already rules such prose to be in error. It survives only as one row of the demonstration in §C, which is where it is filed.

**Not re-opened:** C276's no-verdict-posture flagship; C316's R-1 (colliding `lct://` schemes, killed by `LCT-SPEC-RECONCILIATION-2026-02.md:114-115`) and R-2 (presence silent on `lct://`); C276 Gate 1 (§7 conformance-vector MUST vs 0 repo executors). None was re-derived.

### My own errors this pass — 4, three of them caught only by re-execution

1. **The conformance sweep walked `steps` and missed `setup`** — reported **12** tool-bearing nodes where the file has **17**. The 5 missed nodes are all `hestia_begin_action` calls inside `setup`. Found by policy review, not by me. The verdict was unchanged (0 failures either way), but the *denominator was wrong*, and a denominator that excludes a whole node class is the v40 defect this lineage charges in others.
2. **"20 fenced JSON examples"** — there are **24**, all tagged `json`; 20 parse. Silently dropping 4 into a denominator would have hidden the two blocks that turned out to matter most: §3.3's output and §5.6 WitnessEntry are both **non-parsing**, and both fail their schemas under *both* readings. **The blocks I nearly discarded as unparseable carried the vocabulary-independent half of the finding.**
3. **The first draft rested on "no in-repo validator enables format checking."** True — `format_checker` = 0 occurrences in any `*.py` in the repo — but the README self-discloses it at `:72-74`, and leaning on it re-raises a refuted gate. Demoted to a non-load-bearing note.
4. **A count word taken from a prior document rather than measured.** C316's guard 7 was read as licensing a NO-OP; the pass proceeded only after measuring that the licence's premise ("the coverage table is complete") is about *coverage*, not about *execution* — nothing in nine passes had executed the artifacts against each other. Stated here because the distinction is what justified the finding's existence, and it was nearly missed.

**One correction to policy review's own measurement**, offered because the review asked for corrections in both directions: the corpus arm is **48**, not 47. The review's 47 subtracted `contexts/attestation-envelope.jsonld:52` along with the two property-name positions, but that file is not a `*.schema.json` and was never in the glob; only the 2 in-glob non-keyword positions are subtractable. The two property-name positions it identified are real and are subtracted.

---

## Findings

| # | Severity | Class | Disposition |
|---|---|---|---|
| **N1** | **LOW** | **net-new, presence-venue** | §7 `:668-673` makes the Schemas normative over prose *on disagreement*; **14 of the tree's 20 declared value constraints are `format`**, annotation-only under the Draft 2020-12 the README names at `:78-79`, vs **6 `pattern`** that assert. `$vocabulary` = **0** in all of `web4-standard/`. The precedence procedure has no determinate input on 70% of the sites it arbitrates; two implementations can both "validate" and disagree. Demonstrated by the spec's single elision convention landing on both sides (1 failure default / 10 format-asserting over 17 examples; §5.6 + §3.3 fail under **both**). **Routed — the remedy forks three ways** |
| **I-1** | INFO | corpus-wide, routed OUT | Same question over the whole standard: **48 `format` vs 28 `pattern`** across 24 `*.schema.json`, `$vocabulary` = 0. Disambiguation rule published with the count. Belongs to the schema-tree owner; **not charged at presence's slot** |
| **I-2** | INFO | instrument | The v40 artifact-token sweep returned a set **identical** to the filename sweep (37 = 37, `comm` empty both ways). Published as a negative: on this target the cheap matcher is complete, which is *not* what C350/C354 found on theirs |
| — | REFUTED | — | ×2 (§E), incl. the pass's strongest draft |

**ZERO mutation of `web4-standard/`.** No spec, schema, vector or SDK file was edited. C316's routed N1 is **discharged by C342** and deliberately not re-reported (§A.3).

**No accountability self-audit block:** this pass creates no surface and performs no consequential act — it writes one document under `docs/audits/`.

---

## Guards for the next presence delta (C396)

1. **All of C276's and C316's guards still bind and were honoured.** The no-verdict-posture flagship stays killed; `HestiaCallbackSigner`, `web4-policy`'s `Escalate`, the AAEP triple, the §7 conformance-vector gate, C316's REFUTED-GUARD 3(a)/(b) and its four venue-declined artifacts all stay closed and were **not** re-derived.
2. **N1's pre-registered regression set.** (a) `python3 -c` over the 12 schemas: `format` sites was **14** (11 `uuid` + 3 `date-time`), `pattern` was **6** — a move in either without a `$vocabulary` declaration is the change. (b) `grep -rn '\$vocabulary' web4-standard/` was **0**. (c) `README.md:5-7` still states the non-conformance rule and `:78-79` still names Draft 2020-12 — re-resolve **by content, not by line**. (d) `grep -rniE "non-?conform" web4-standard/ --include=*.md | grep -iE "valid|schema"` was **1 line** — if it becomes >1, presence is no longer the sole venue.
3. **Do NOT re-raise the missing in-repo validator.** README `:72-74` self-discloses it; C276 Gate 1 killed the shape. If a validator ships, **check which vocabulary it selects** — that is the interesting event, not its existence.
4. **C316's routed N1 is discharged by C342 §F.** Do not re-report it. If it regresses, it is web4-lct's row (C382), not presence's; C342 pre-registered its own regression set for that slot.
5. **Live carries, both re-verified this pass:** C127-1 cross-track facet (no `Session`/`VaultEntry` under `v0/common/`) — do not re-charge the C128-closed half. C198 B.2 trigger (`grep -rn "presence" web4-policy/src/*.rs`, **0** this pass).
6. **Method, born this pass — execute the artifacts against each other before concluding a frozen target is clean.** Nine passes argued *about* these schemas and none ran anything against them; the window was empty for the sixth time and the finding was still there. **Coverage is not execution**, and a guard that licenses a NO-OP on completed *coverage* does not license one on unattempted *execution*.
7. **And walk every node class.** The conformance file carries `tool` in `setup` as well as `steps`; a sweep of `steps` alone under-counts by 5 of 17 and would certify a clean over a domain that excludes a third of the surface.
8. **Proportionality:** this pass ran the SHORT form and the finding came from three executions, not from re-reading. C396 should open the same way — run the machine checks first, and if they are clean and the window is empty, the capped NO-OP record is correct.
