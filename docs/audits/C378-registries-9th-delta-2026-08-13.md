# C378 — `registries/initial-registries.md`, 9th delta

**Date**: 2026-08-13 · **Slot**: `web4-20260813-120000` · **Prior pass**: C338 (2026-08-08)
**Target**: `web4-standard/registries/initial-registries.md` — blob `00a37a88`, mover `3f1d6fad` 2026-06-18, **56 days frozen**, 59 lines
**Window**: `e5b87dbe..HEAD`, **96 commits**
**Lineage**: C70 → C71 → C110 → C142 → C182 → C220 → C258 → C298 → C338 → **C378**
**Enumeration rule**: inclusive — all lineage documents named `C*-registries-*`; this lineage has no
non-C-numbered `…-internal-consistency-…` member (`ls docs/audits/ | grep -i registr` = 8 + this one).

---

## Headline

**C338's pre-registered B-D1 trigger fired — and the firing is what proves the trigger cannot answer
B-D1.** The relation moved `24 ⊊ 31` → **`25 ⊊ 31`** exactly as pre-registered, with B-D1 still
operator-unanswered. But the corpus's actual error-code vocabulary did **not** change: `web4-standard/`
holds **57** distinct codes at the window's base and **57** at HEAD — **zero minted, zero retired across
96 commits**. What moved was a *redistribution* between the two files the trigger happens to watch.

The trigger's two numbers are per-file cardinalities of `core-spec/errors.md` and
`registries/initial-registries.md`. Together those two files cover **31 of the corpus's 57 codes**.
**26 codes — 46% — live in neither**, and no change among them can move either number. So the watchdog
guarding the lineage's flagship carry is blind to the region where nearly half the population lives, and
the one event that *did* move it touched neither watched file: all five `registries/` files are still
frozen at the single commit `3f1d6fad`.

The pass's own strictest rule, run on its own lineage first. **Zero mutation. Zero findings against the
target's bytes.**

---

## §A — target vs canonical: held by construction

`core-spec/core-protocol.md` (the canonical for Suite IDs) is frozen at **`3084e4d2` 2026-06-05** — the
same commit C298 and C338 verified. C298's binding anti-manufacture condition therefore applies
unchanged for the Suite-ID rows: **no finding may be laid against the frozen target's bytes absent a
canonical change in the interval or a dated inbound obligation.**

**A precision the policy review pressed for, recorded rather than reached past.** The condition is
*section-scoped*, not file-scoped. `core-protocol.md` governs §"Suite IDs" (`:4-7`) and is frozen ⇒ those
rows hold by construction. The declared authority for the §"Error Codes" block (`:14-59`) is
`core-spec/errors.md` — named as such by `registries/error-codes.md:11` and by `errors.md:9` — and that
file **did** move in the window, at `afd04623` (#678, 2026-08-10). So the error-code half of the target
has a live authority change and is legitimately open this pass; the Suite-ID half is not. Both halves are
stated separately below rather than being averaged into one verdict.

All three Suite-ID rows re-verified cell-by-cell against `core-protocol.md` §1 (not inherited):

| Suite | `initial-registries.md` | `core-protocol.md` §1 | Verdict |
|---|---|---|---|
| W4-BASE-1 | X25519 / Ed25519 / ChaCha20-Poly1305 / SHA-256 / HKDF (COSE) | identical | **exact** |
| W4-FIPS-1 | **P-256 ECDH** / ECDSA-P256 / AES-128-GCM / SHA-256 / HKDF (JOSE) | `P-256ECDH` | KEM cell only ⇒ **B-C4 ≡ C68 B-7**, guarded, **NOT re-opened, NOT re-measured by its own enumeration** (C296-N3) |
| W4-IOT-1 | X25519 / Ed25519 / AES-CCM / SHA-256 / HKDF (CBOR) | identical | **exact** — outlier remains `web4-handshake.md:24` (DELTA-1, handshake-owned) |

**B-A6** (the bare `HKDF` token) verified present, not re-opened — C296-N2 owns it and explicitly does not
charge this file.

---

## §B — corpus delta

96 commits in the window. The registry-relevant movement is a single commit.

### The two-directional set difference, re-run (C298's mandated guard, C338's pre-registered trigger)

Instrument, pre-registered and unchanged from C338 so the numbers are comparable: `grep -rhoE
"W4_ERR_[A-Z0-9_]+"`, recursion root `web4-standard/`, unrestricted filetypes, `.git` excluded, family-prefix
artifacts stripped with `grep -vE "_$"`, `sort -u`, compared with `comm`.

| Set | C338 (2026-08-08) | **C378 (HEAD)** |
|---|---|---|
| `registries/initial-registries.md` (the "not a registration target") | 31 | **31** |
| `core-spec/errors.md` §2 (the declared SSOT) | 24 | **25** |
| in SSOT, absent from the seed | 0 | **0** |
| in the seed, absent from the SSOT | 7 | **6** |
| distinct across `web4-standard/` | 57 | **57** |
| in `web4-standard/`, absent from the SSOT | 33 | **32** |
| **in NEITHER watched file** | *(not measured)* | **26** |

The 6 remaining one-way exceptions: `W4_ERR_BAD_SEQUENCE`, `W4_ERR_BAD_TIMESTAMP`,
`W4_ERR_GRANT_EXPIRED`, `W4_ERR_RATE_LIMIT`, `W4_ERR_SCOPE_DENIED`, `W4_ERR_WITNESS_REQUIRED`.
`W4_ERR_PROTO_FORMAT` left the difference; **B-C1 is now half-discharged** (`PROTO_FORMAT` in,
`WITNESS_REQUIRED` still out).

### What actually moved — and what did not

`afd04623` (#678, "fold hackathon findings into canonical Web4 text") touched three files
(`errors.md` +7/−2, `security-framework.md` +36, `draft-web4-core-00.xml` +12/−3) and added
`W4_ERR_PROTO_FORMAT` to `errors.md` §2. **No `registries/` file was touched** — all five are still at
`3f1d6fad` 2026-06-18, one commit, 56 days.

**Executed, not inferred** — the set difference run at the window's *two endpoints* rather than at one
point in time, which no prior pass has done:

```
git grep -hoE "W4_ERR_[A-Z0-9_]+" e5b87dbe -- web4-standard/ | grep -vE "_$" | sort -u   → 57
git grep -hoE "W4_ERR_[A-Z0-9_]+" HEAD      -- web4-standard/ | grep -vE "_$" | sort -u   → 57
comm -13 (base) (head)   → EMPTY   # minted in window: 0
comm -23 (base) (head)   → EMPTY   # retired in window: 0
```

**The corpus vocabulary is unchanged. The code was not registered; it was relocated.** This matters for
the disposition below, and it is the fact that turns a status update into a finding.

**Not re-filed, credited.** The description text `afd04623` gave `W4_ERR_PROTO_FORMAT` in the SSOT
("Message encoding, canonical form, or required protocol structure is malformed or unsupported") does not
match the seed's (`:52`, "Message format doesn't match negotiated profile"). That divergence is
**`C374-N2` (MED)**, filed by the errors lineage on 2026-08-13 with a denominator of 24-of-25 verbatim
agreement. It is theirs; `C374:371` further rules that `initial-registries.md:52` must not be fixed in
isolation. **This pass does not re-charge it and does not touch `:52`.**

---

## §B′ — mirror set RE-DERIVED (not re-read)

C338's guard: *"this pass's list is as inheritable-and-wrong as C298's was."* Re-derived from the
pre-registered predicate — **does the artifact mint, restate, or enforce a Web4 registry identifier?**
(`C338:75`).

**Admitted and re-verified**: the 4 `registries/` files; `core-spec/core-protocol.md` §1 (canonical for
Suite IDs); `core-spec/errors.md` (declared SSOT); `implementation/sdk/web4/{errors,security}.py`; the
ACP/AGY/cross-society code families in `core-spec/`; `test-vectors/validate_context_refs.py` (C338's new
member). **14 files** carry `W4_ERR_*` under `web4-standard/`.

**Executed** (v27): `python3 web4-standard/test-vectors/validate_context_refs.py` → exit 0, 283
references, 9 distinct names, 8 backed, 1 `KNOWN` (`t3v3.jsonld`, 36 refs, carried to C310-N3). Behaves as
documented, unchanged from C338.

**One candidate admitted, examined at length, and REJECTED as a member — see Negative 1.** The
re-derivation is only worth running if it can also return *no*.

---

## Findings

### C378-N1 (MEDIUM) — the pre-registered B-D1 trigger fired, and the firing shows the trigger measures a quantity that cannot answer B-D1

`C338:200` pre-registered: *"The 24 ⊊ 31 relation is the live measurement of B-D1; **if either number
moves without a B-D1 answer, that is the finding.**"* The left number moved, at `afd04623` 2026-08-10,
in-window. B-D1 remains operator-unanswered. The trigger fired as designed.

**What the firing revealed.** Discharging it required asking *why* it moved, and the answer falsifies the
instrument:

| Question | Instrument | Result |
|---|---|---|
| Did the corpus gain a code? | set difference at both window endpoints (above) | **No — 57 → 57, 0 minted, 0 retired** |
| Did a `registries/` file change? | `git log -1 -- web4-standard/registries/*` ×5 | **No — all 5 at `3f1d6fad`, 56 days** |
| What moved, then? | `git show afd04623 -- core-spec/errors.md` | one code **relocated** into the SSOT |
| How much of the corpus do the two watched files cover? | `comm` three-way partition | **31 of 57** |
| How much lives in neither? | `comm -23 (corpus∖SSOT) (seed)` | **26 of 57 — 46%** |

The trigger's two operands are per-file cardinalities. Three distinct events move the left number
identically and are **indistinguishable** to it: (a) a code relocated from the seed into the SSOT — what
actually happened; (b) a genuinely new code minted directly into the SSOT — B-D1's *good* outcome; (c) a
code moved into the SSOT from any of the other 12 files. And one event class moves **neither** operand
while growing the corpus: a code minted into any file that is not one of the two. That class is not
hypothetical — it is where the majority of the divergence already sits.

**The 26 in neither file**, enumerated rather than counted (the guard against a bare number): the 8
`W4_ERR_ACP_*` plus `W4_ERR_ACP`; the 6 `W4_ERR_AGY_*`; the 4 `W4_ERR_CROSS_SOCIETY_*`;
`W4_ERR_AUDIT_EVIDENCE`, `W4_ERR_FORMAT`, `W4_ERR_LAW_CONFLICT`, `W4_ERR_LEDGER_WRITE`,
`W4_ERR_PROPAGATION_SCOPE_UNSUPPORTED`, `W4_ERR_R7_REPUTATION_INVALID`, and `W4_ERR_UNKNOWN_FAKE`
(`implementation/sdk/tests/test_errors.py:284`, the deliberate unknown-code fixture C338 named — so **25**
are real vocabulary). Two of these are already-standing carries in their own right: `W4_ERR_LEDGER_WRITE`
vs `W4_ERR_ACP_LEDGER_WRITE` is **B-8**, and the `W4_ERR_AGY_*` family is the ownerless set C106`:91` and
C138`:89` adjudicated twice on the merits. **B-8's own subject matter is inside the trigger's blind
region** — the watchdog for the flagship cannot see a standing MED that is subordinate to it.

**Why MEDIUM.** Nothing is presently wrong in the corpus; the block criterion is that the carry **looks
better instrumented than it is**. C338 published `24 ⊊ 31` as *"this quantifies B-D1 exactly and for the
first time as a set relation"* and handed the next pass a trip-wire. A reader of the ledger — including
the operator who must answer B-D1 — sees a flagship with a live numeric watchdog. The watchdog covers
54% of the population, cannot distinguish B-D1's feared outcome from its desired one, and has now fired
once on an event that is neither.

**Refutation attempted, four ways.**
(i) *"The trigger was only ever meant to watch the SSOT-vs-seed pair, so covering 31 of 57 is correct
scope, not a defect."* — It is the scope C338 wrote, but not the scope C338 claimed for it: `C338:69`
frames the same measurement as quantifying *"the file that says it is not a registration target is a
strict superset of the file that says it is the single source of truth"* — a claim about registration
authority over the corpus, not about two files. The instrument is narrower than the proposition it is
offered as evidence for.
(ii) *"The firing is just a status update; the trigger did its job."* — It fired, but discharging it as
"moved, still unanswered" would have published a number movement as though the corpus had changed. It had
not. The only reason this pass can say so is that it ran the difference at both endpoints, which the
trigger does not specify.
(iii) *"46% blindness is inherent — those 26 codes are extension namespaces the SSOT was never meant to
hold."* — Partly true and it is why the severity is MED rather than HIGH: `errors.md:9` does sanction
SAL §9 / ACP §10 / metering §6 as extenders (C298-N2 withdrew the strong form on exactly this ground).
But sanctioned-to-exist is not the same as invisible-to-the-watchdog, and B-8 — an unsanctioned
collision — sits in the blind region regardless.
(iv) *"C374 already reported the trigger firing, so this is a re-file."* — C374 §H reported the firing
from the errors side and was right to. What is charged here is the instrument, which is this lineage's own
(`C338:200`), and the endpoint-pair measurement that shows the corpus did not move — neither is in C374.
**C374's report of the firing is credited, not claimed.**

**Routing**: this lineage's own ledger + the B-D1 operator memo. **Not self-applied** — B-D1 gates all
`registries/` remediation, and rewriting a trigger is an audit act, not a spec edit. The corrected trigger
is pre-registered for C418 in §Guards below.

### C378-N2 (LOW — reach-escalation on B-C7, **NOT net-new**) — the "Specification Required" registry satisfies its own declared policy for 0 of 7 entries, and 4 of the 7 have never been named by any audit

`registries/README.md:24` assigns `extensions.md` the RFC 8126 policy **Specification Required**, and
`:28` states it verbatim: *"the request must reference a stable, publicly available specification."*
`extensions.md:8` repeats it. The file's Reference column carries 7 bracket tokens.

Measured — `grep -rlF "[<token>]" web4-standard/` for each:

| Token | Files that contain it | Named by B-C7? | Named by **any** audit? |
|---|---|---|---|
| `[Web4-MRH-RDF]` | 1 — `extensions.md` itself | no | **0 docs** |
| `[Web4-Witness]` | 1 — itself | no | **0 docs** |
| `[Web4-MCP]` | 1 — itself | yes | yes |
| `[Web4-R6]` | 1 — itself | no | **0 docs** |
| `[Web4-T3V3]` | 1 — itself | no | **0 docs** |
| `[Web4-Blockchain]` | 1 — itself | yes | yes |
| `[Web4-PQC]` | 1 — itself | yes | yes |

**7 of 7 resolve to zero files.** C70`:89` filed B-C7 naming **three** (`MCP_BRIDGE` /
`BLOCKCHAIN_BRIDGE` / `QUANTUM_READY`); C298's snapshot-guard list names two. The class is the whole
column. Four tokens have stood unexamined for 56 days across nine passes — **not because they were
adjudicated, but because the finding that covers them enumerated a subset** (v49: a guard's domain is not
its class).

The corollary is the sharper half: the registry's declared registration policy is satisfied by **none** of
its own seed contents, so "Specification Required" has never once been an applied constraint in this
corpus. Symmetrically, all 7 registered *names* (`MRH_RDF` … `QUANTUM_READY`) also appear in exactly one
file — `extensions.md` — corroborating C70`:63`'s "0 consumers" at the name level as well as the
reference level. **No severity increase claimed and the target is not charged**: B-C7 is already LOW and
already entangled with B-D1's retain/retire decision for the file. This widens its **domain** from 3 to 7
and hands the operator a complete column instead of a sample.

**Routing**: B-C7's row, on the B-D1 operator memo. Not self-applied.

---

## Published negatives — what was measured and *declined*

### 1. `schema_registry.json` + `_SCHEMA_FILES` — ADMITTED as a candidate, EXECUTED, then REJECTED as a mirror-set member and as a charge

This was the pass's proposed headline. The policy review refuted it and the refutations held on
re-verification. It is published in full — with its executed numbers — so the next pass inherits a
closed question rather than an attractive one.

**What is true, and reproducible.** `implementation/sdk/web4/schema_registry.json` (96 KB, **12** entries,
keyed by bare basename) is loaded by `implementation/sdk/web4/validation.py` as schema-resolution priority
2 of 3. `git ls-files 'web4-standard/schemas/**.json'` = **24**; the 12 excluded are the entire
`schemas/presence-protocol/` tree. The guard named for completeness,
`tests/test_validation.py::TestBundledRegistry::test_registry_contains_all_schemas` (`:51-58`), iterates
**`_SCHEMA_FILES.items()`** — the allowlist whose completeness is the question — and `test_count` (`:105-106`)
pins `len(list_schemas()) == 12` as a literal. Executed: dropping a 13th schema file into
`web4-standard/schemas/` leaves `tests/test_validation.py` at **37 passed** and the full SDK suite at
**2750 passed, 5 xfailed**. Backed control: removing one entry *from the bundle* makes
`test_registry_contains_all_schemas` **fail** (`1 failed, 36 passed`). Bundle-vs-live drift: **0 of 12**.
Lineage reach: 12 audit docs across **8** other lineages name the artifact; **0 of this lineage's 9
documents** do.

**Why it is nonetheless not a finding — five independent grounds, each verified:**

1. **It fails this lineage's own pre-registered predicate.** `C338:75` admits an artifact that *"mints,
   restates, or enforces a **Web4 registry identifier**."* `registries/README.md:5` scopes the cluster to
   *"the IANA considerations for Web4 protocol parameters."* A bundle of JSON Schema documents mints no
   protocol parameter and carries no registration policy. Nine passes did not overlook it; **the predicate
   excludes it.** Admitting it on the strength of the filename token `registry` is precisely the
   by-the-filename-not-the-domain's-word error the standing rule names.
2. **On-point precedent, in the immediately prior pass.** `C338:147` declined `KNOWN_MISSING` as "an
   unregistered registry" because *"charging a … CI carrying-list for not being in `registries/` would be
   **manufacture**: it is a **build artifact**."* `schema_registry.json` is the weaker candidate on every
   limb — it fails the predicate, `pyproject.toml:56` lists it as wheel package-data, and its own check
   does go red (the backed control above).
3. **The exclusion is DISCLOSED at the point of use.** `schemas/presence-protocol/README.md:5` declares
   that tree the *"wire-format authority"* with its own binding, `:45` ships an explicit *"known-gap
   ledger, not a permanent exemption,"* and `:71-72` records that the tools bind via `shapeMatchesSchema`
   and that a standalone validator *"is planned but not yet present."* Verified live:
   `testing/conformance/presence-protocol-conformance.json` carries **12** `shapeMatchesSchema`
   occurrences. The tree is not unvalidated; it is validated by a different, declared mechanism. Charging
   this is charging the project's disclosure discipline.
4. **The proposed remedy is wrong, not merely unnecessary.** The bundle is keyed by **bare basename**
   (verified: all 12 keys). `git ls-files 'web4-standard/schemas/**.json' | xargs -n1 basename | sort |
   uniq -d` returns **`hestia_query_policy.schema.json`** — it exists at both `v0/tools/` and `v1/tools/`.
   A directory-denominated guard of the shape the finding implied would **collide and silently drop one
   protocol version.** A finding whose fix introduces a defect is not a finding.
5. **Three lineages already settled the artifact** as a corroborating copy rather than an independent
   authority — `C302:393`, `C352:188` (*"byte-equivalent embedded copy… It corroborates, it does not
   multiply"*), `C372:389`.

Residue, routed nowhere and recorded only: `validation.py:3` describes the module as validating *"JSON-LD
documents produced by SDK `to_jsonld()` methods"* while `_SCHEMA_FILES:66-69` also carries three
`# Non-JSON-LD schemas` (`lct-raw`, `t3v3-raw`, `trust-query`), so the docstring is narrower than the
allowlist. That is an SDK-lineage INFO at most and **is not filed** — `validation.py:74` ("all 12
schemas") and `pyproject.toml:56` (`web4 = ["py.typed", "schema_registry.json"]`) are both self-scoped
and neither claims directory completeness.

### 2. The extension-vocabulary disjointness — PRIOR ART, C70

Measured independently before the novelty sweep: `extensions.md` registers 7 numeric/symbolic IDs
(`0x0001 MRH_RDF` …), while the protocol negotiates a string vocabulary — `w4_ext_sdjwt_vp@1` (5
occurrences), `w4_ext_93f07f2a@0` (3), `w4_ext_noise_xx@1` (2), `w4_ext_fafbfcfd@0` (1),
`w4_ext_1a2a3a4a@0` (1), across 3 files — with **zero overlap**. `web4-handshake.md:269`, the Reference
`extensions.md:11` itself points at, sends the reader to `initial-registries.md` — the file the README
declares *not a registration target* — and not to `extensions.md`.

**C70`:63` published this, with the `⊥` symbol and the phrase "0 consumers", on 2026-06-18.** Not novel;
**killed before charging.** Recorded because the corroborating counts are new and B-D1's retain/retire
decision will need them.

### 3. `w4_sig_cose@1` / `w4_sig_jose@1` as an unregistered third extension vocabulary — PRIOR ART, B-C6

Measured: both live only in `web4-handshake.md`, both ride in the same `ext` / `ext_ack` arrays as the
`w4_ext_*` values (`:89`, `:104`), and `:128` makes the selected signature extension ID a **MUST** in the
transcript hash for downgrade resistance — yet neither appears in any registry file.

**C70`:88` is B-C6, verbatim, including the downgrade-protection rationale.** Not novel; killed before
charging. Standing, B-D1-subordinate, not re-opened.

### 4. C338's gate blind-tree guard — STILL NEGATIVE

`grep -rhoE "https://web4\.io/contexts/" web4-standard/testing/` → **0**. `validate_context_refs.py`
remains structurally blind to `web4-standard/testing/test-vectors/`, and the blind tree still carries no
`@context` references, so the blindness is still harmless. **Negative 3 of C338 does not become a
finding this pass.** Guard carried forward unchanged.

### 5. The `https://web4.io/` namespace census — STILL DEFERRED, with its instrument

C338 deferred this pending a read of the 12 prior audits that touch the namespace question (C40, C58,
C86, C98, C134, C162, C170, C310, C314, C328 + 2 internal-consistency docs). That read was **not
performed this pass** and the census is **not** run — saying so is the point, since an unrun deferral
reported as clean is the failure C298 caught and withdrew. Carried to C418 unchanged, with C338's
published instrument.

---

## Standing carries — re-verified at live HEAD

- **B-D1 (FLAGSHIP, MED, operator)** — registry SSOT inversion. **UNANSWERED.** Relation now **25 ⊊ 31**,
  0 exceptions the other way. Gains **C378-N1** (its watchdog is 54%-scoped) and **C378-N2** (B-C7's
  domain widened 3→7). Gates all `registries/` remediation ⇒ this pass stays audit-only.
- **B-C1 (MED, `errors.md`-owned)** — **HALF-DISCHARGED**, first movement in the lineage's history.
  `W4_ERR_PROTO_FORMAT` entered the SSOT at `afd04623`; `W4_ERR_WITNESS_REQUIRED` remains absent and is 1
  of the 6 surviving one-way exceptions.
- **B-C4 ≡ C68 B-7 (MED, operator)** — `:6` = `P-256 ECDH`, verified in place. **Not re-opened, not
  re-measured by its own enumeration** (C296-N3). Inherit C336's corrected reach (12 occurrences / 11
  lines / 10 files / 7 forms), not C296's 6/5/4.
- **B-C7 (LOW)** — domain widened 3 → 7 by **C378-N2**. No severity change.
- **B-8 (MED, operator)** — `W4_ERR_LEDGER_WRITE` / `W4_ERR_ACP_LEDGER_WRITE`. Both present; **both inside
  C378-N1's blind region**, which is now part of N1's evidence.
- **B-C2 / B-C3 / B-C5 / B-C6, B-D2, B-D3** — unchanged, B-D1-subordinate or sibling-owned. Not re-opened
  (C298/C338 guards). B-C6 re-measured only to kill a duplicate charge (Negative 3).
- **DELTA-1 (MED, handshake-owned)** — `:7` = `CBOR` corroborates `core-protocol.md:20`; `web4-handshake.md:24`
  = `COSE` remains the sole outlier. Unchanged.
- **C298-N1 (MED)** — SDK registry mirror. `errors.py` frozen at `39fb4119` **2026-05-17 (88 days)`;
  SDK-vs-registry re-measured: **overlap 24 / SDK-only 6 / registry-only 7**, identical to C298. Not
  re-litigated.
- **C298-N2, N4, N5** — unchanged; N5 folds into the B-D1 memo.
- **C338-N1 (MED)** — **DISCHARGED by C374 §D** (I2's locus restored to `web4-standard/QUICK_REFERENCE.md:193`,
  verified). **Do NOT re-route.**
- **C338-N2 (LOW)** — reach-escalation on B-D1, standing.
- **C258-N1** — remains **SUPERSEDED / FALSE as written** (C298-N1). Do not re-publish.

### Row-set census (v19)

C338's "Standing carries" section holds **9** bullet rows (counted from the source, not from its prose);
with its own **2** net-new that is **11** rows inherited. **All 11 are present here** — B-C7 is broken out
of C338's `B-C2/B-C3/B-C5/B-C6/B-C7` group into its own row because C378-N2 changes its domain — plus this
pass's 2 net-new. **0 silent drops.** One row changed disposition (C338-N1 → DISCHARGED, by another
lineage's work), one gained a number (B-C1 → half-discharged), one gained domain (B-C7, 3→7).

*Own-error, caught by the post-write re-run:* the draft published this cell as "13 carry rows, 13 present"
— a number carried over from C338's prose rather than counted from its bullet list. The corrected count is
**9 + 2 = 11**, and the set of rows actually reproduced below was already complete; only the denominator
was wrong. Counted with `sed -n '151,162p' … | grep -c '^- \*\*'`.

---

## §own-error — the headline was falsified in review, and one measurement was simply false

Submitted to policy review as a **measured premise**, not a plan. The review refuted the proposed
headline (Negative 1) on five grounds and falsified one supporting measurement outright. Every
correction was **independently re-verified before acceptance**; all four held.

**The false cell — M7, the direction claim.** The draft asserted the `schemas/presence-protocol/` tree
*"landed `cf0d6cc5` 2026-07-02, 94 days after the bundle, moving no counter."* **False.** Per-file
`--diff-filter=A`: all 12 schemas landed **2026-05-16** (`d7867704` ×11, `e64eb4c2` ×1) — **47** days
after the bundle's birth, not 94. Worse, `cf0d6cc5` is `remediate(C128): apply C127-1 autonomous facet —
**complete presence schema-README gap ledger**`: **the commit the draft named as the tree's arrival is the
commit that added the disclosure which refutes the finding.** And the bundle was last touched `766611ef`
**2026-05-14**, *two days before the tree existed* — so "moving no counter" misdescribes a file that has
simply been frozen throughout.

This is the sharpest form of the C376 lesson: the false cell **pointed the same direction as the
argument**, so it read as corroboration and survived until something executed it. A `git log -1` on a
*directory* answers "what last touched this tree," which is not the question "when did these files
arrive"; only per-file `--diff-filter=A` answers that. The draft ran the convenient command and let the
plausible date stand.

**Second correction accepted**: "12 audit docs across **7** other lineages" → **8** (web4-lct,
dictionary-entities, entity-types, mcp-protocol, reputation-computation, society-metabolic-states,
lct-linked-context-token, security-framework). Corrected in Negative 1.

**No reviewer correction was rejected this pass.** All four reproduced on independent re-measurement —
recorded explicitly, because the two prior fires each rejected one after checking and the check is only
meaningful if it can also return "the reviewer was right." The three audit cites the review *supplied*
(`C302:393`, `C352:188`, `C372:389`) were each resolved as written and each lands on the claimed sentence —
recorded because C366 and C372 both received reviewer cites that did not (two fence lines; one off by 3
lines), so a clean result here is data, not a formality.

**Two further cells the post-write re-run caught, before commit and without a reviewer.** (a)
`validation.py:73` → **`:74`** for the "all 12 schemas" comment. (b) The row-set census was published as
"13 carry rows, 13 present" — a figure lifted from C338's *prose* instead of counted from its bullet list,
which holds **9**. Corrected to 9 + 2 = **11** in §Row-set census. Both are the same failure as M7 in
miniature: a number taken from a document's narration rather than from the document.

**And the redirect was correct.** The review's closing move — that the fired B-D1 trigger was the pass's
legitimate, pre-registered, non-manufactured work and the proposed headline was a distraction from it —
is what C378-N1 is. The finding that survived is the one the lineage had already scheduled for itself.

---

## Routing summary

| Bucket | Disposition |
|---|---|
| §A Suite-ID rows | Canonical `core-protocol.md` frozen `3084e4d2` ⇒ **held by construction**; BASE-1/IOT-1 exact, FIPS-1 = B-C4 only. **0 findings against the target's bytes.** |
| §A error-code block | Declared authority `errors.md` **did** move (`afd04623`) ⇒ legitimately open; scoped separately from the Suite rows rather than averaged. |
| §B corpus delta | Trigger **FIRED** (`24 ⊊ 31` → `25 ⊊ 31`). Corpus vocabulary **unchanged, 57 → 57, 0 minted / 0 retired** across 96 commits. All 5 `registries/` files still at `3f1d6fad`. |
| §B′ mirror set | Re-derived from the predicate. One candidate admitted, executed, and **rejected** — the re-derivation returned *no*, which is what makes it a measurement. |
| **C378-N1 (MED)** | The B-D1 watchdog covers **31 of 57** codes; **26 (46%) are invisible** to it, including B-8's subject matter. 4 refutations attempted and answered. → this ledger + B-D1 memo; corrected trigger pre-registered for C418. |
| **C378-N2 (LOW)** | `extensions.md`'s "Specification Required" policy satisfied by **0 of 7** entries; **4 of 7 never named by any audit**. → widens **B-C7**'s domain 3→7, no severity change, target not charged. |
| Declined | 5 published with numbers: `schema_registry.json` (executed, then killed on 5 grounds incl. a **basename collision that would make the implied fix wrong**), extension disjointness (**C70:63**), `w4_sig_*` (**B-C6**), gate blind tree (**still 0**), namespace census (**deferred, explicitly not run**). |
| Credited, not claimed | **C374 §H** reported the trigger firing from the errors side; **C374-N2** owns the `:52` scope divergence; **C374 §D** discharged C338-N1. |
| Own error | **M7 was FALSE** — direction claim off by 47 days and misattributed to the disclosure commit; one lineage count 7→8. Both caught by policy review, both re-verified before acceptance. |
| Net new | **2 — 1 MED, 1 LOW (a reach-escalation, not a new family). Zero inside the byte-frozen target. Zero mutation.** |
| C379 remediation slot | **NO-OP.** N1 is an audit-instrument correction; N2 is B-D1-gated. **Do not manufacture a `registries/` edit.** |

---

## Method carry — apply at every delta from C380 on

**v55 — a trigger you pre-register is an instrument you will be judged by, so measure what it *covers*
before you report what it *says*.** C338 handed the next pass a trip-wire on two per-file counts and
called the relation *"B-D1 quantified exactly."* It fired on schedule. Discharging it honestly required
asking a question the trigger does not contain — *did the corpus actually change?* — and the answer was
no: 57 → 57, zero minted, zero retired, while the watched pair moved. A trip-wire reports a **difference
between its operands**, never a fact about the population; if the carry is about the population, publish
the **coverage ratio** beside the firing (here 31 of 57, with 26 in neither operand) or the firing will be
read as evidence for a proposition it cannot reach.

Four riders:

1. **Run the set difference at both endpoints of the window, not at HEAD.** Every prior pass measured the
   relation at one point in time and compared to the previous pass's *published* number. That detects
   movement but cannot say whether the corpus moved or the files traded. Two `git grep` invocations at
   `base` and `HEAD` distinguish redistribution from growth, and the distinction is the whole finding.
2. **When a finding covers a structured column, enumerate the column before inheriting the finding's
   subset.** B-C7 named 3 of `extensions.md`'s 7 reference tokens; the other 4 have appeared in **zero**
   audit documents in 56 days — protected from examination *by* the finding that appeared to cover them.
   The standing rule ("when a prior pass charged ONE member of a structured block, enumerate the whole
   block") applies to a finding's *domain*, not only to a spec's blocks.
3. **`git log -1` on a directory answers a different question than `--diff-filter=A` per file** — and it
   answers it plausibly enough to survive review. The draft's false cell (§own-error) came from asking a
   tree when it should have asked its files, and the wrong date pointed the same direction as the
   argument. **Any provenance claim about a *set* of files must be measured per file.**
4. **A rejected candidate is worth more written up than deleted.** Negative 1 cost most of this pass and
   yielded no finding — but it now carries an executed baseline (0 drift, 12 of 24, 2750-green probe, a
   backed control) *and* the basename collision that makes the obvious fix wrong. The next pass to notice
   `schema_registry.json` inherits a closed question instead of a fresh temptation. → the C338`:147`
   precedent, now applied a second time and therefore a convention.

### Guards for the next registries delta (~C418)

- **Re-run the set difference AT BOTH WINDOW ENDPOINTS.** Current baseline: corpus `web4-standard/` = **57**,
  SSOT = **25**, seed = **31**, absent-from-SSOT = **32**, in-neither = **26**. If the corpus number moves,
  that is a mint or a retirement and it is the finding — the per-file pair is no longer the primary
  instrument.
- **CORRECTED B-D1 TRIGGER, pre-registered to replace `C338:200`:** watch **|corpus| = 57** and
  **|corpus ∖ SSOT| = 32**, not the file pair. The file pair remains a secondary row. A firing must be
  discharged by naming *which* file gained or lost the code.
- **B-C1 is half-discharged.** If `W4_ERR_WITNESS_REQUIRED` enters `errors.md` §2, B-C1 closes and the
  one-way exception count goes 6 → 5. Check before re-asserting it.
- **The namespace census is STILL unrun.** Read the 12 audits first (C40, C58, C86, C98, C134, C162, C170,
  C310, C314, C328 + 2 internal-consistency docs), then run C338's published instrument. Two passes have
  now deferred it; a third deferral should say why rather than repeating the sentence.
- **Re-test the gate's blind tree**: if `grep -rhoE "https://web4\.io/contexts/" web4-standard/testing/`
  ever returns non-zero, C338's negative 3 becomes a finding.
- Do **NOT** re-open: B-A6; `:6`'s `P-256 ECDH` (≡ B-C4/B-7); B-D2; B-D3; the numeric-orphan fact (≡ B-D1);
  the submission tree's crypto cells (≡ C336-N1); `initial-registries.md:52`'s description (≡ **C374-N2**,
  and `C374:371` forbids fixing it in isolation); C338-N1 (**DISCHARGED**, C374 §D).
- Do **NOT** re-charge, and do not re-derive from scratch: `schema_registry.json` / `_SCHEMA_FILES`
  (Negative 1 — five grounds, incl. the `hestia_query_policy.schema.json` basename collision), the
  extension-vocabulary disjointness (**C70:63**), `w4_sig_*` (**B-C6**).
- Do **NOT** re-run B-C4/B-7's grep scoped to its own enumeration (C296-N3).

---

## Review-gate self-audit

This audit creates no surface and drives no consequential act — it is a read-only analysis producing one
Markdown record. No spec, code, schema, test, or sibling-ledger file was modified. Two temporary probes
(a 13th schema file; one bundle entry removed) were executed and reverted in-tree; `git status --porcelain`
was verified empty after each.

```
surface: C378 registries delta-audit doc   act: none (read-only audit; 0 spec/code/ledger edits)
S: low/reversible [construct: docs/audits/C378-registries-9th-delta-2026-08-13.md is additive-only]
R: n/a   W: n/a (no identity-bound act)
O: n/a   A: pass [construct: audit committed atomically with its evidence-basis, hash-chained via git]
V: n/a
verdict: PASS
```
