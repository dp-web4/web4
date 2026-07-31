# C294 — `errors.md` Seventh Delta Re-Audit (8th pass)

**Audit ID**: C294
**Target**: `web4-standard/core-spec/errors.md` (154 lines, blob `acda930e`) — the Web4 core RFC-9457 error taxonomy
**Date**: 2026-07-30
**Auditor**: autonomous web4 session (legion, slot `202644`), v2 protocol
**Type**: **Seventh delta re-audit** (8th pass overall). Lineage: **C30** (2026-06-04, PR #268 → remediation #269) → **C66** (1st delta, PR #345) → **C67** (remediation, `6189432d`, 3 autonomous applied) → **C106** (2nd, 0 net-new) → **C138** (3rd, 0 net-new) → **C178** (4th, 0 net-new; mapped the false-mirror boundary) → **C216** (5th, 0 net-new) → **C254** (6th, 0 net-new; first empty corpus-delta surface) → **C294**.

**Method note**: `errors.md` is **byte-identical since C67** (`git log -1` = `6189432d`, 2026-06-17; banner `Last-Updated: 2026-06-17` accurate — **43 days frozen**, blob `acda930e`, 154L). §A is prior-finding + carry re-verification at live HEAD. §B is the corpus-delta surface (siblings moved since the **C254 snapshot**, 2026-07-23). §B′ is a **mirror-set re-derivation from subject matter** with M1/M2/M3 **pre-registered in writing before the sweep** (method carry v7). §C is a refute-by-default internal pass.

**Headline**: the streak ends — **2 net-new (1 MED, 1 LOW)**, and both came from the same place: a mirror the lineage had never read. `hub/` — the repo's deployed Web4 society daemon, 71 tracked files, 31 `.rs`, and the interval's dominant mover (23 commits) — has been read by **zero** of the seven prior errors passes (`grep -c 'hub/'` over all 7 audit docs = **0,0,0,0,0,0,0**). Gating it produced the finding the six clean passes could not see: **errors.md makes `code` REQUIRED and defines it as "the error code from the §2 taxonomy", and §2 cannot express the two failure classes every deployed Web4 endpoint actually emits.** The standard assigns **no `404` anywhere** (0 hits, all `web4-standard/**/*.md`, instrument baselined) and exactly **one** 5xx (`W4_ERR_WITNESS_UNAVAIL`/503, semantically specific). The hub is the existence proof: **42** `ApiError::not_found` and **65** `ApiError::internal` call sites, plus a blanket `From<E>` routing every `?` in an MCP handler to `internal` — and not one of them can cite a code.

**The hub is admitted as evidence, not as a defendant.** The conformance charge — "hub emits `{"error": …}` as `application/json`, violating §1's `application/problem+json` MUST" — is **DECLINED** under the C158 self-scoping test (§B′.1c). That ruling, owed for seven passes, is published here.

---

## Scope & Methodology

Frozen-wrap proportionality (policy-reviewed and APPROVED this fire, with six binding conditions recorded in the session log). §A applies the C56 completeness method and the C62/C64 bidirectional carry re-check. §B is the corpus-delta surface. §B′ re-derives the mirror set from **subject matter**, not from last pass's list ([[feedback_mirror_set_underderived]]). Snapshot-presence guard (C98) applied throughout: "is it NEW?" precedes "is it TRUE?" ([[feedback_prose_is_not_ledger]]). Every count carries its token, scope, denominator and commit, and **every instrument was re-run after the findings were written** ([[feedback_publish_the_instrument]]).

Severity: **HIGH** correctness/normative contradiction; **MEDIUM** consumer-affecting inconsistency; **LOW** hygiene; **INFO** forward-awareness.
Routing: **AUTONOMOUS** (fixable in `errors.md`), **DESIGN-Q** (operator), **CROSS-TRACK** (lands in another file/track).

### Pre-registered gates (written before the sweep, per C286 [[feedback_admission_criterion_not_verdict]])

- **M1 — mirror-set membership.** An artifact is in the errors mirror set iff it *emits or defines protocol-facing failure responses* for a Web4 protocol surface. Not "is named `error*`"; not "was in last pass's list".
- **M2 — genuine vs. false mirror.** A name-collision is a **false** mirror and is excluded from divergence analysis (the C178-N1 boundary, which excluded `web4-core/src/error.rs`). A **genuine** mirror is one whose output crosses a wire to a counterparty.
- **M3 — admission of a candidate finding.** Admit iff genuine mirror (M2) **and** the spec's normative text *reaches* the artifact. Reach is tested by the spec's own scoping language and by the artifact's role in the corpus — **not** by "would this indict the spec", which pre-judges the conclusion and is self-sealing.

M3 is the gate that did the work this fire: it **declined** the obvious charge (§B′.1c) and **admitted** a different, stronger one (§B′.1d) that does not depend on the hub being bound by errors.md at all.

---

## §A — Prior-Finding Verification (C67 remediation + C106/C138/C178/C216/C254 → current)

### A.1 — The 3 AUTONOMOUS C67 fixes: **all HELD by byte-freeze**

`errors.md` has not changed a byte since C67 (`6189432d`, 43 days). Re-confirmed against the live file, read in full this fire:

| C66 ID | C67 fix | Verdict | Evidence (current `errors.md`) |
|---|---|---|---|
| **B-3** (MED) | §1 rescope: `W4_ERR_*` to SAL §9 / ACP §10 / metering §6; name mcp §7.6 separately as lowercase `web4_*` | **HELD** | §1 L9 unchanged; names all four homes + the mcp lowercase split verbatim. |
| **B-6** (LOW) | §5 retitle → "Status Code Semantics" + transport-agnostic lead | **HELD** | §5 L141/L143 unchanged. |
| **B-7** (LOW) | §5 401/403 prose sharpened to mirror §2's split | **HELD** | §5 L146/L147 mirror §2.4 DENIED@401 / SCOPE@403. |

No encoding artifacts. PR #347 was a single-file diff → cross-file regression surface nil.

### A.2 — Bidirectional carry re-verification (re-measured, not transcribed)

Every cited sibling's last-touch was re-derived at live HEAD (`6f3d610a`) this fire:

| Sibling | Last touch | Moved since C254 snapshot (2026-07-23)? |
|---|---|---|
| `core-spec/mcp-protocol.md` (§7.6) | `3e765345` 2026-07-13 | No |
| `core-spec/web4-society-authority-law.md` (§9) | `1354e4c2` 2026-07-14 | No |
| `core-spec/acp-framework.md` (§10) | `fb0075fc` 2026-07-08 | No |
| `protocols/web4-handshake.md` (§10 mirror) | `57caa2e1` 2026-06-29 | No |
| `protocols/web4-metering.md` (§6) | pre-06-29 | No |
| `core-spec/core-protocol.md` (§5.1) | `3084e4d2` 2026-06-05 | No |
| `core-spec/data-formats.md` (B-M2) | `3084e4d2` 2026-06-05 | No |
| `registries/error-codes.md` | `3f1d6fad` 2026-06-18 | No |
| `registries/initial-registries.md` | `3f1d6fad` 2026-06-18 | No |
| `implementation/sdk/web4/errors.py` | `39fb4119` 2026-05-17 | No |
| `web4-core/src/error.rs` | `6f7051f7` 2026-06-13 | No |
| `docs/what/specifications/WEB4_QUICK_REFERENCE.md` (I2) | `c651c823` 2026-07-13 | No |

All carries **STAND**. Two were re-measured rather than carried:

| Carry | Status now | Re-measurement this fire |
|---|---|---|
| **B-1** `AUTHZ_DENIED`@401 vs RFC 403 (5-mirror DESIGN-Q) | **STANDS** | handshake §10 mirror unmoved. Operator-gated. |
| **B-H1 / B-D1** numeric registry orphan + SSOT inversion | **STANDS; re-measured** | `git grep -c W4_ERR registries/error-codes.md` = **0**. The numeric registry (11 rows, `0x0000`–`0x000A`, names like `INVALID_LCT`, `HANDSHAKE_FAILED`) shares **zero** identifiers with §2's 24 codes while citing `core-spec/errors.md` as its Reference. The orphan is total, not partial. |
| **B-2 / X2** `initial-registries.md` divergent mirror | **STANDS; re-measured** | Set-differenced against §2 at live HEAD: **7** codes in `initial-registries.md` absent from errors.md — `W4_ERR_BAD_SEQUENCE`, `W4_ERR_BAD_TIMESTAMP`, `W4_ERR_GRANT_EXPIRED`, `W4_ERR_PROTO_FORMAT`, `W4_ERR_RATE_LIMIT`, `W4_ERR_SCOPE_DENIED`, `W4_ERR_WITNESS_REQUIRED`. Listed as bare bullets with **no status assignments** (L52-59). |
| **B-4** SDK docstring "canonical per errors.md / 30 codes 7 cats" | **STANDS** | `errors.py` frozen 74 days; §2 is 24/6. Spec CORRECT, SDK over-claims. CROSS-TRACK. |
| **B-5** SDK cross-society statuses vs mcp §7.6 | **STANDS; and see C294-N1** | mcp §7.6 unmoved ⇒ the 3-of-6 accounting holds *by construction*, and the construction was verified not assumed. **New this fire: a candidate structural explanation** — see §B′.1d R-note. |
| **B-8 / X3** ACP §10 / SAL §9 parallel naming + ledger-write collision | **STANDS** | Both host files unmoved. |
| **B-9** no cross-society test vectors | **STANDS; re-measured** | See §B′.3: the published vector file covers **5 of 24** §2 codes and **0** cross-society codes. |
| **B-M1** centralized-vs-distributed error ownership | **STANDS** | Load-bearing across metering / ACP / both registries. |
| **B-M2** `web4://` SSOT in `data-formats.md`; **B-M3** W4IDp form | **STAND** | Hosts unmoved. |
| **C16-H1-remainder / C16-M8/B6** SAL §9 + `chapter-law.ttl` | **STAND** | SAL unmoved. |
| **I2** QUICK_REFERENCE custom `type` URI; **I3** content-type over transports | **STAND** | Unmoved. |
| **C178-N1** Rust `error.rs` false mirror (INFO) | **STANDS; boundary re-applied, and this fire it pointed outward** | `error.rs` unchanged (13 variants); `git grep -c W4_ERR web4-core/` = **0**. See §B′.2 — the same M2 language that excluded `error.rs` **admits** `hub/`. |

**0 carries resolved into a defect; 0 regressed.**

---

## §B — Corpus-Delta Pass (siblings moved since the C254 snapshot, 2026-07-23)

**The cited-sibling surface is EMPTY for the second consecutive delta.** `git log --since=2026-07-23 -- web4-standard/core-spec/ web4-standard/registries/ web4-standard/protocols/ web4-standard/implementation/ web4-core/` returns **zero commits**.

The interval was not quiet, though — **58 commits** repo-wide. Where they went:

| Area | Commits | Errors-relevant? |
|---|---|---|
| **`hub/`** | **23** (19 `hub-daemon/src`, 12 `hub-lib/src`, + tools/fixtures) | **YES — never gated. §B′.1.** |
| `docs/audits/` | 16 | No (this rotation's own output) |
| whitepaper + `docs/whitepaper-web` | 20 | No |
| `web4-trust-core`, `web4-policy` | 3 + 1 | Gated NEGATIVE, §B′.4 |
| `web4-standard/proposals/` | 2 (#580, #579) | **#580 → C294-N2** |
| `web4-standard/ontology/` | 1 (`01f410db`) | Gated NEGATIVE, §B′.4 |

An empty *cited-sibling* surface next to a 23-commit mover in the same repo is precisely the signature the v7 mirror-set carry exists to catch. The list of siblings was inherited; the list of artifacts that *implement the subject matter* was not re-derived. **0 findings routed from §B; 2 from §B′.**

---

## §B′ — Mirror-Set Re-Derivation (M1/M2/M3 applied)

C254's mirror set was `{errors.py, error.rs}`. Re-derived from subject matter — *what emits or defines protocol-facing failure responses?* — the candidate set is `{errors.py, error.rs, hub/, web4-standard/ontology/, web4-trust-core, web4-policy, registries/*, test-vectors/errors/}`.

### B′.1 — `hub/` — the never-gated mirror

**Denominator**: 71 tracked files under `hub/`, of which **31** are `.rs` (`git ls-files 'hub/' | wc -l` = 71; `| grep -c '\.rs$'` = 31), at `6f3d610a`. Per the policy condition, the sweep was **time-boxed to error-emission sites** derived from `IntoResponse` / `StatusCode::` / `ApiError`; `rest.rs` (450 KB) was **not** read in full.

#### B′.1a — M1: **PASS**. What the hub actually emits

| Instrument (tracked `hub/*.rs`, `6f3d610a`) | Files | Hits |
|---|---|---|
| `IntoResponse` | 4 | 9 |
| `StatusCode::` | 5 | 115 |
| `ApiError` | 2 | 369 |
| `anyhow` | 22 | 220 |

Three error types in one binary, two of them protocol-facing:

- `hub/hub-daemon/src/rest.rs:1644` — `struct ApiError { status: StatusCode, message: String }`; `IntoResponse` at `:2162`. Constructors: `bad_request`(400), `unauthorized`(401), `not_found`(404), `conflict`(409), `internal`(500, redacted via `redact_internal`).
- `hub/hub-daemon/src/mcp.rs:166` — a **second** `struct ApiError`, same name, same two fields. Constructors: `internal`(500), `forbidden`(403), `bad_request`(400), `accepted_escalation`(**202**). `IntoResponse` at `:193`. A blanket `impl<E: Into<anyhow::Error>> From<E> for ApiError` at `:200` routes **every `?` in an MCP handler** to `internal`.
- `hub/hub-daemon/src/admin.rs:152` — `AdminError(StatusCode, String)`, renders **HTML**, operator-plane only. Out of scope (not a protocol surface).

**The wire shape** (`mcp.rs:195`, `rest.rs` equivalent):
```rust
let body = serde_json::json!({"error": self.message});
(self.status, Json(body)).into_response()
```
That is `application/json` (axum `Json`) with a single `error` string member. **No `type`, no `title`, no `code`, no `status` member in the body.** Instrument for the negative: `git grep -lIi -e 'problem+json' -e 'RFC 9457' -e 'rfc9457' -e 'W4_ERR' -- 'hub/'` = **0 files of 71**.

M1 **PASS**: this emits protocol-facing failure responses on a Web4 surface.

#### B′.1b — M2: **GENUINE mirror**

C178-N1 excluded `web4-core/src/error.rs` because "the two are different primitives … Rust's is a free-form internal error with no wire contract", and defined a genuine mirror as one **whose output crosses a wire to a counterparty**. The hub's `ApiError` crosses a wire, to an anonymous counterparty, on a `--bind 0.0.0.0` public plane (`rest.rs:1670-1691` says so explicitly). The boundary that excluded `error.rs` **admits** `hub/` by its own terms. Keeping the boundary while refusing it when it points outward would be the drift.

#### B′.1c — M3 on the obvious charge: **DECLINED** (the ruling owed for 7 passes)

Candidate charge: *"§1 L13 says errors MUST be `application/problem+json`; the hub emits `application/json` with a bare `error` string on ~369 sites; therefore ~369 MUST violations."*

**Declined**, on the C158 self-scoping test, run before any severity was assigned:

1. **The hub makes zero conformance claims to errors.md.** Measured: `git grep -lI -iE 'errors\.md|RFC.?9457|problem\+json|W4_ERR' -- 'hub/'` = **0 files of 71**.
2. **It is not silent about the specs it does implement — it names them.** `hub/docs/HUB-LAW.md:18` and `main.rs:370` cite `core-spec/hub-law-schema.md`; `README.md:55` cites `mcp-protocol §7.8`; `hub-lib/tests/fixtures/hub-law/README.md:56` cites `ontology/hub-law.ttl`; `docs/PAIRED-CHANNELS.md:37` cites `proposals/lct-mcp-as-smart-contract.md`. The hub is a **selective, declared** conformer. `errors.md` is not on its list.
3. **Precedent is directly on point.** **C158** (acp) declined a hub charge because acp §4.2 self-scopes to calls "from ACP" and hub makes no ACP conformance claim. **C290** published a hub **M1-EXCLUDED** ruling for ISP on zero-hit mechanism greps. **C184/C222** ruled hub DISJOINT from handshake. **C170** read hub's law-integrity as a *faithful* deployment of SAL §9. The lineage's settled posture is that the hub is bound by what it claims, and no pass has ever adjudicated it against errors.md.
4. **HUB-track is actively governing this surface.** `6f3d610a` (#614) tightened the three public-plane `internal(..)` constructors so anonymous callers get a fixed sentence plus a correlation reference instead of the `anyhow` chain — a redaction discipline errors.md's `detail` field says nothing about. This is not a neglected surface.

**Published ruling: `hub/` is M1-PASS, M2-GENUINE, M3-DECLINED for the conformance charge. It is admitted to the errors mirror set as _evidence about what a deployed Web4 endpoint must emit_, not as a defendant.** Record this so no future pass re-litigates it, and so the M3 gate's declining outcome is on the record next to its admitting one.

*What would have reversed this*: any hub artifact claiming errors.md/RFC-9457 conformance, or any errors.md language binding society-server implementations. Neither exists.

#### B′.1d — M3 on the charge that survives: **ADMITTED** → **C294-N1 (MED)**

The hub as evidence, not defendant, exposes a defect in **errors.md's own internal closure** — one that holds whether or not the hub is bound by it.

errors.md §1 L33: **`code` (REQUIRED in Web4)** … "carrying the error code **from the §2 taxonomy**". §1 L13: "Web4 uses RFC 9457 Problem Details for **all** protocol errors." So for every protocol error, a `code` is mandatory and must come from §2.

**§2 has no code for `not found` and no code for `internal failure`.** Re-derived from the §2 table rows this fire, the complete status distribution is:

| Status | 400 | 401 | 403 | 408 | 409 | 410 | 429 | 503 |
|---|---|---|---|---|---|---|---|---|
| §2 codes | 9 | 4 | 3 | 1 | 3 | 2 | 1 | 1 |

24 codes, 8 classes. The **dimension** — not just the case — was then widened ([[feedback_empty_column_not_missing_cell]]):

| Token | Scope | Result |
|---|---|---|
| `404` | all `web4-standard/**/*.md` | **0 files** |
| `Not Found` / `NOT_FOUND` | all `web4-standard/**/*.md` | **0 files** |
| `Internal Server` / `INTERNAL` | all `web4-standard/**/*.md` | **0 files** |
| any 5xx | all `web4-standard/**/*.md` | only `research/` + `docs/` prose (`509`, `500`, `599` as plain numbers); **no error table** |
| `404` | whole `web4-standard/` tree, any file type | **3 files** — `demos/hello-web4/demo_lct.json:30` (an `exp` timestamp, false positive), and `sdk/web4/errors.py:305` + `sdk/tests/test_errors.py:124` — i.e. **only the SDK**, and only at the standing B-5 divergence |

**Instrument baselined before the zero was reported** ([[feedback_enumeration_and_grep_hypotheses]] / [[feedback_publish_the_instrument]]): the same glob and method returns `W4_ERR` = **7 files**, `403` = **4 files**, `409` = **4 files**. The glob works; the `404` zero is real, not a silently-failing pattern.

So across the entire standard, **no specification assigns a 404 to anything**, and the only 5xx assigned anywhere is `W4_ERR_WITNESS_UNAVAIL`/503 — semantically "the witness is down", not "this server failed".

**The hub is the existence proof that these are not hypothetical classes**, measured at `6f3d610a` over tracked `hub/*.rs`:

| Constructor | Call sites |
|---|---|
| `ApiError::bad_request` (400) | 79 |
| `ApiError::internal` (500) | **65** + every `?` in an MCP handler via the blanket `From<E>` |
| `ApiError::not_found` (404) | **42** |
| `ApiError::unauthorized` (401) | 27 |
| `ApiError::forbidden` (403) | 3 |
| `ApiError::conflict` (409) | 1 |
| `ApiError::accepted_escalation` (202) | 1 |

Four of the seven constructors map cleanly onto §2 classes. **The two with no §2 code between them account for 107 call sites** — more than every mappable non-400 constructor combined.

**Finding C294-N1 (MED, DESIGN-Q → operator / standard-editor).** `errors.md` mandates a `code` drawn from §2 for every protocol error, while §2 cannot express *not-found* or *internal-failure*. A conforming implementation of any Web4 protocol endpoint therefore has three options, none of which the spec sanctions: emit a Problem Detail with no `code` (violates L33), invent a code (§1 authorizes only four named **specifications** to extend, not implementations), or decline to use Problem Details for those cases (violates L13's "all protocol errors"). The spec is not wrong about anything it says; it is **closed in a way that leaves the most common failure classes unsayable**, and it has never said whether that closure is deliberate.

**Refutations run against this flagship** ([[feedback_refute_your_best_finding]] — pointed at the flagship, not the leftovers):

- **R1 — "§1 authorizes subsystem specs to extend; a not-found code just belongs in a subsystem spec."** *Partially valid, does not kill it.* But §1 names exactly four extenders (SAL §9, ACP §10, metering §6, mcp §7.6) and **none** defines a not-found or internal code — measured, 404 = 0 across all standard markdown. More decisively, *not-found* and *internal failure* are the two least domain-specific failures there are; routing them to subsystem specs inverts the layering a **core** taxonomy exists to provide. R1 changes the *remedy* (core addition vs. explicit out-of-scoping), not the finding.
- **R2 — "§1 L9 enumerates a closed scope (binding, pairing, witnessing, authorization, cryptography, protocol). Resource-level and server-level errors are simply outside it. A boundary, not a gap."** *The strongest refutation; it survives as the reason severity is MED and routing is DESIGN-Q rather than a defect charge.* But it does not dissolve the finding, because the same document also says it is "the single source of truth for core protocol error codes" (L9), that Problem Details apply to "**all** protocol errors" (L13), and that `code` is REQUIRED from §2 (L33). If the scope is genuinely closed, the spec still owes implementers a statement of what to do with an error outside all six categories — and it gives none. **The finding is the silence, not the scope.**
- **R3 — "Pre-existing since C30; the snapshot-presence guard says this is not net-new."** *Correctly aimed, and answered honestly.* The **spec condition** predates the freeze — this is not a regression and nothing changed in `errors.md`. What is new is that it was **never raised**: grepping all 7 prior errors audits for `404`/`500`/`5xx`/`internal error` returns hits only in **B-5 / SDK cross-society context** (C66 L91/L128, C178 L80/L152 — the SDK-vs-mcp status divergence), never the absence of the class from §2. And the corroborating consumer is new to the lineage because the mirror set was under-derived. Honest label: **net-new to the lineage, born of a blind spot** — the same shape as C280-N3 and C292-N1, and it should be read as an indictment of six clean passes' mirror sets as much as of the spec.
- **R-note on B-5 (a candidate reframing, offered as a hypothesis not a conclusion).** The standing B-5 divergence is that the SDK assigns **404** to `W4_ERR_CROSS_SOCIETY_UNRECOGNIZED_LCT` where mcp §7.6 assigns **403** — and `sdk/web4/errors.py:305` is one of only two real `404`s in the entire standard tree. A plausible structural reading: the SDK author reached for the natural not-found status, found no core class for it, and minted one; mcp, facing the same absence, reused 403. If so, B-5 is a *symptom* of C294-N1 rather than an independent SDK bug. **Alternative reading, not excluded:** the SDK simply transcribed the status wrong, and the coincidence is a coincidence — B-5 also carries a naming transform on all 6 codes, which is plainly SDK-side error and has nothing to do with any missing class. Recorded as a question for whoever adjudicates B-5, **not** as a finding.

### B′.2 — Rust `web4-core/src/error.rs`: **false mirror re-confirmed (C178-N1)**

Frozen `6f7051f7`, 2026-06-13 (47 days), unchanged. `Web4Error` still a **13-variant** internal `thiserror` enum. `git grep -c W4_ERR web4-core/` = **0**. Excluded from divergence analysis, as at C178/C216/C254. The C178-N1 forward-note's trigger ("if web4-core grows a wire-serialization layer, that layer inherits §2") remains un-fired **in web4-core** — and §B′.1 is the reason that matters less than it looked: the wire-serialization layer the note was waiting for **already exists, in `hub/`**, and the note was watching the wrong crate.

### B′.3 — Published test vectors: **machine-validated CLEAN**

`web4-standard/test-vectors/errors/error-taxonomy.json` (`4c076459`, 2026-03-17, 76L) declares `"spec": "web4-standard/core-spec/errors.md"`. Each vector's `problem_json` was machine-checked against the §2 table parsed from the live spec:

- **5 vectors, 0 mismatches** — every `code` present in §2; every `title` and `status` byte-equal to its §2 row; every vector carries all three Web4-REQUIRED members (`title`, `status`, `code`).
- **Coverage: 5 of 24** §2 codes. Uncovered: all 4 binding-minus-one, all 4 pairing, 3 of 4 witness, 2 of 4 authz, all 4 crypto, 3 of 4 proto.
- **0 cross-society vectors** — re-measures standing **B-9** with a live number.

The v7 "standard disagrees with itself" trap was live this pass (target and both known mirrors all frozen) and was run: the standard's own published error artifacts **agree with the prose**. The one place they disagree with *each other* is the standing B-H1/B-2 registry split (§A.2), re-measured, not net-new.

*Also checked:* `forum/nova/…/schemas/problem-details.schema.json` (`18209449`, 2025-09-11) requires `title`+`status`+`code` and pins `code` to `^W4_[A-Z_]+$` — consistent with §1. It is a `forum/nova/` contributed artifact, not a promoted standard artifact, so it is a mirror and not a peer (contrast [[feedback_ontology_is_a_spec_peer]], where the artifact **had** been promoted into `web4-standard/ontology/`). No divergence to route.

### B′.4 — Remaining candidates: gated **NEGATIVE**, with counts

| Candidate | Denominator | `W4_ERR` | `problem+json` / `9457` | M1 |
|---|---|---|---|---|
| `web4-standard/ontology/` | 7 tracked files | 0 | 0 | **NEGATIVE** — 2 files match `error`, both as the English word inside `role-extension` deny-cause prose (`author:violation` = "author error"). No failure-response surface. The interval's one commit (`01f410db`, tensor superclass) was already adjudicated NEGATIVE at C292. |
| `web4-trust-core` | 36 tracked files | 0 | 0 | **NEGATIVE** — interval commits are CI/lockfile (`44dc25db`, `22d5a8f6`) |
| `web4-policy` | 4 tracked files | 0 | 0 | **NEGATIVE** — interval commit is a `Cargo.lock` refresh (`1fa86e09`) |
| `hub/hub-daemon/src/admin.rs` `AdminError` | 1 type | 0 | 0 | **NEGATIVE** — renders HTML on the loopback operator plane; not a protocol surface |

---

## §C — Fresh Internal-Consistency Pass (refute-by-default)

Each candidate re-read at its call site this fire. **0 net-new contradictions among what the spec asserts**; the one net-new item is an omission (C294-N1, §B′.1d), plus C294-N2 below.

- **§2 ↔ §3 examples**: all three match their §2 rows (§3.1 `AUTHZ_DENIED`/401 = L72; §3.2 `WITNESS_QUORUM`/409 = L66; §3.3 `AUTHZ_RATE`/429 = L75).
- **§2 statuses ⊆ §5 list**: §2 uses exactly {400, 401, 403, 408, 409, 410, 429, 503}; §5 (L145-152) lists exactly those 8. Closed both ways — no orphan, no omission. *That closure is itself the C294-N1 evidence*: §5 is presented as the semantic-class list, and an implementer reading it finds no class for an internal failure.
- **§1 example ↔ §2.1**: "Binding Already Exists"/409/`W4_ERR_BINDING_EXISTS` = L45.
- **§1 Fields ↔ examples**: every example carries `status`+`title`+`code`; `type` defaults to `about:blank`; `detail`/`instance` present and optional.
- **§1 extender convention ↔ corpus**: the `W4_ERR_*` vs lowercase `web4_*` split is accurate against live siblings (none moved).

### C294-N2 (LOW, CROSS-TRACK → proposal #580's precedent survey)

`web4-standard/proposals/resilience-to-incomplete-information.md` (#580, `954ee391`, this interval) mandates, at L52-58, that a materially-incomplete action be **"suspended, not failed"** (recursive correction) or **"escalate[d] with the gap named — a recorded refusal that says what was missing and why it could not be got."**

**errors.md's vocabulary is terminal-only.** All 24 codes and all 8 status classes name a *completed* failure. There is no code and no status class for *suspended pending correction* or *escalated with the gap named*. The deployed hub has already invented the missing outcome: `ApiError::accepted_escalation` → **202 ACCEPTED** (`mcp.rs:188`), whose doc-comment says it exists so "PolicyEntity gating (deny → 403, escalate → 202) mirrors REST". **202 is not in §5's 8-class list**, and no §2 code can accompany it.

Routing is deliberately weak: #580 is a **proposal**, authority PROSPECTIVE, so this is **not** a defect charge against a frozen ratified spec. It lands as a **counter** on #580's precedent survey — the corpus does *not* already support the proposal here; the core error vocabulary would have to grow a non-terminal outcome class for #580 to be implementable. (Survey state after this fire: 1 counter C280-N2, 1 violation C282-N1, 1 positive C284-N2, **+1 counter C294-N2**.)

**Refutation:** *"A 202-accepted escalation is not an error at all; an error taxonomy is the wrong home for it, so its absence from errors.md is correct."* **Largely conceded** — and it is why this is LOW and routed to the proposal rather than to the spec. The residual point is that *no* document is the home, and the one shipped implementation put it in its error type because that is where status-bearing outcomes live. That is information #580's author should have; it is not an errors.md defect.

### Considered-and-dismissed (anti-padding transparency)

- **Two `ApiError` structs in one binary** (`mcp.rs:166`, `rest.rs:1644`) — same name, same fields, **disjoint** constructor sets (mcp: 400/403/202/500; rest: 400/401/404/409/500). The C286 "does the impl agree with itself" pattern fires on the shape. **Dismissed**: private module-local types in one crate; `mcp.rs:163-164`'s doc-comment shows the divergence is *deliberate* (the MCP plane needs 202-escalation and 403-deny; the REST plane needs 404/409). Charging it would require demonstrating a concrete failure that renders with two different statuses on the two planes, which this time-boxed sweep did not establish — and extrapolating one from a partial sweep is exactly what the policy condition forbids. Recorded for HUB-track's awareness; **not** routed as a finding, and **not** an errors.md matter either way.
- **`AdminError` HTML rendering** — operator-plane, loopback-only, not a protocol surface. Dismissed at M1.
- **Vector coverage 5/24** — re-measures standing B-9; not net-new.
- **AGY / ACP `*_INTEGRATION_SUMMARY.md` codes** absent from §1's extender list — dismissed as at C106–C254: §1 lists *normative framework homes*, and the summaries predate all snapshots.

---

## Classification Summary

| ID | Sev | Finding | Routing |
|----|-----|---------|---------|
| **C294-N1** | **MED** | `code` is REQUIRED and defined as drawn from the §2 taxonomy, but §2 has no code for *not-found* or *internal-failure*; no Web4 spec assigns a 404 anywhere (0 hits, baselined) and the only 5xx is 503/`WITNESS_UNAVAIL`. A conforming endpoint has no sanctioned way to report either. The deployed hub needs both on 107 call sites. | **DESIGN-Q** — operator / standard-editor. **Not self-executable**: adding codes to a ratified taxonomy, or explicitly closing it out of scope, is an author decision. |
| **C294-N2** | **LOW** | errors.md's vocabulary is terminal-only — no code or status class for the *suspended* / *escalated-with-gap-named* outcomes proposal #580 mandates; the hub already emits 202 for exactly this and 202 is outside §5's 8 classes. | **CROSS-TRACK** — lands as a **counter** on #580's precedent survey, not as a charge against a frozen spec. |

**Totals**: 0 HIGH, **1 MEDIUM**, **1 LOW**, 0 INFO = **2 net-new**. *The five-delta clean streak (C106+C138+C178+C216+C254) ends at C294 — and it ends on the mirror gate, not on the target, which is byte-frozen and remains internally consistent in everything it asserts.*

**§A**: 3/3 C67 fixes HELD by byte-freeze. All 13 carries STAND; B-H1, B-2 and B-9 re-measured with live numbers rather than transcribed (registry orphan is **total**: 0 shared identifiers; initial-registries divergence is **7** codes; vector coverage is **5 of 24**).

**§B**: cited-sibling surface **EMPTY** for the second consecutive delta (0 commits across core-spec / registries / protocols / implementation / web4-core since 2026-07-23) — beside **23** `hub/` commits in the same interval. That contrast is the finding's origin.

**§B′**: mirror set re-derived from subject matter. `hub/` **M1-PASS, M2-GENUINE, M3-DECLINED** for the conformance charge (published ruling, owed 7 passes) and **admitted as evidence** → C294-N1. `error.rs` false mirror re-confirmed. Published vectors **machine-validated 0 mismatches**. `ontology/`, `web4-trust-core`, `web4-policy`, `AdminError` all gated **NEGATIVE** with counts.

**§C**: 0 net-new contradictions among the spec's assertions; 1 omission (N1) and 1 proposal-facing gap (N2).

---

## Key Adjudication

1. **The clean streak was partly an artifact of an under-derived mirror set — and this is now the third consecutive lineage where that was true.** C280 found `hub/` had never been gated in 7 society-spec audits; C292 found `web4-standard/ontology/role-extension.*` had been read by 0 of 7 entity-types passes; C294 finds `hub/` had been read by 0 of 7 errors passes. Three different lineages, same shape: the sibling list was *inherited* rather than re-derived from *what now implements this subject matter*. Six errors passes reported "0 net-new" honestly and correctly **given their mirror set**, and the mirror set was the defect. The corrective is not more scrutiny of the frozen target; it is re-deriving the denominator every pass.

2. **The M3 gate earned its keep by declining, not by admitting.** The easy finding was sitting there — 369 `ApiError` sites, zero `problem+json`, a MUST in §1 — and a gate phrased as "would this indict the spec" would have taken it. The C158 self-scoping test killed it on measured evidence (0 conformance claims of 71 files; the hub names the four specs it *does* implement). What survived is a finding that **does not depend on the hub being bound by errors.md at all** — the hub is evidence about what a Web4 endpoint must emit, and the defect is in errors.md's own closure. A gate that can produce both outcomes on the same artifact in the same pass is doing real work; one that only ever admits is a finding generator.

3. **C178-N1 was watching the wrong crate for two years of deltas.** The forward-note said: *if web4-core grows a wire-serialization layer, that layer inherits errors.md §2*. C216 and C254 dutifully live-tested it against `attestation.rs`, `ratchet.rs`, and the #544/#540 movers, and both times reported it un-fired — correctly. But the wire-serialization layer the note was waiting for had already shipped, in a different directory, and the note's phrasing ("web4-core") is what kept three passes looking at the crate instead of at the subject matter. **A forward-guard phrased as a path is a guard that expires silently when the code moves.** Guards should name the *behaviour* ("any artifact that serializes a protocol failure to a counterparty"), not the *location*.

---

## Next-Turn Carry

- **C295 errors.md remediation slot = NO-OP.** Neither net-new finding is self-executable: **C294-N1** is a standard-editor / operator decision (add the missing classes, or explicitly close the taxonomy and say what an out-of-scope error does), and **C294-N2** routes to proposal #580's survey. **Do not manufacture an `errors.md` edit.** The file stays frozen.
- **Route C294-N1 into the standing operator memo** alongside B-1 / B-M1 / B-H1-B-D1 / B-M3. It is arguably adjacent to **B-D1** (the SSOT inversion): both ask *who owns the error namespace and where does it end*. Suggest adjudicating them together.
- **Route C294-N2 to proposal #580's precedent survey** as its 4th entry (2 counters, 1 violation, 1 positive after this fire).
- **Forward guard for the next errors delta (~C334) — do NOT re-open these as net-new**: `errors.md` freeze `6189432d` / blob `acda930e` / 154L (re-verify it is still frozen first). `hub/` M3-DECLINED ruling is **published and settled** — do not re-litigate the conformance charge unless a hub artifact starts claiming errors.md/RFC-9457 conformance, or errors.md gains language binding society-server implementations; **that is the trigger, and it is phrased as a behaviour, not a path** (per Key Adjudication 3). C178-N1's web4-core false mirror is settled. Published vectors machine-validated clean at `4c076459` — re-run the validator, don't re-derive it. Re-measure, don't transcribe: B-H1 (0 shared identifiers), B-2 (7 divergent codes), B-9 (5 of 24 coverage).
- **Method carry for every lineage, not just errors**: a forward-guard that names a **path** (`web4-core/`) instead of a **behaviour** silently expires when the behaviour relocates. Audit the *existing* forward-notes in `per_file_guards.md` for this shape when convenient — several are phrased as paths.
- **Standing operator bundle (route as ONE memo; none gate a normal audit turn)**: B-1, B-M1, B-H1/B-D1, B-M3, **+C294-N1**. **Cross-track (other owners)**: B-2, B-4, B-5 (+ the C294-N1 reframing *question*, offered as a hypothesis), B-8, B-9, B-M2, C16-H1-remainder, C16-M8/B6, I2, I3, C178-N1, **+C294-N2**. **Do not self-apply any.**
- **D0 (protocols/ cluster) still operator-gated** — unrelated to errors; do not touch.
