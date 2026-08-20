# C418 — `web4-standard/registries/`, 10th delta

**Date**: 2026-08-20 · **Slot**: C418 (= C378 + 40) · **Lineage**: registries, 10th pass
**Target**: `web4-standard/registries/` (5 files), byte-frozen at `3f1d6fad` 2026-06-18 — **63 days**
`initial-registries.md` blob `00a37a88`, 59 L — the same blob C298, C338 and C378 audited.
**Window**: `73436fa6..HEAD` — 27 commits, **1** touching `web4-standard/`, **0** touching `registries/`.
**Mutation**: ZERO. **Net-new**: 2 (1 MED, 1 LOW). **Zero findings against the target's bytes.**

This lineage has **no** non-C-numbered `…-internal-consistency-…` member (stated per C378's guard).

---

## Headline

**The registries cluster opens by declaring that it *is* Web4's IANA Considerations. Three other in-tree
artifacts also state Web4's IANA Considerations, and the four requested registry sets have an empty
intersection — including the one artifact that was re-date-stamped for submission ten days ago.**

`registries/README.md:6` — *"These registries define the IANA considerations for Web4 protocol
parameters."* Its table (`:20-25`) names four files, three of them registrable. `submission/` holds three
further artifacts that each open an IANA Considerations section and each request a **different** set of
registries. No registry name appears in all four. Four of the eight distinct names requested across them
have **no `registries/` file at all**.

The reason ten passes did not see this is mechanical and is the second finding: **C338's published
namespace-census instrument carries `--include=*.{json,jsonld,md,py,ttl}`, and the submission draft is
`.txt`.** It is the only `.txt` in `web4-standard/` carrying the subject matter.

**The twice-deferred `https://web4.io/` namespace census was RUN this pass** (§C). It is **not** charged,
and every root's disposition is published with its command — so the next pass inherits numbers, not a
sentence.

---

## §A — target vs canonical: held by construction, section-scoped

`core-spec/core-protocol.md` (canonical for Suite IDs) is frozen at `3084e4d2` 2026-06-05 — unchanged
since C298. C298's **anti-manufacture condition** therefore applies: no finding may be laid against the
frozen target's bytes absent a canonical change in the interval or a dated inbound obligation. Neither
exists. **0 findings against the target's bytes**, 6th consecutive pass.

Per C378's correction, the condition is **section-scoped**: the declared authority for the Error-Codes
block is `core-spec/errors.md`, which *did* move at `afd04623` (#678, 2026-08-10). That half is
legitimately open and is measured in §B rather than assumed shut.

Suite-ID rows re-verified against `core-protocol.md` §1: **W4-BASE-1 exact**, **W4-IOT-1 exact**,
**W4-FIPS-1 KEM cell only** ⇒ `B-C4 ≡ C68 B-7`, guarded, **not re-opened and not re-measured by its own
enumeration** (C296-N3). `B-A6` (bare `HKDF` at `:5-7`) verified present, **not re-opened** — C296-N2
owns the two-lineage collision.

---

## §B — corpus delta: the corrected trigger did NOT fire

C378 pre-registered a **corrected B-D1 trigger** to replace `C338:200`: watch `|corpus|` and
`|corpus ∖ SSOT|`, not the `initial-registries.md`/`errors.md` file pair, and run it **at both window
endpoints**. Run as specified:

```
# matcher, verbatim, at each endpoint:
git grep -hoE "W4_ERR_[A-Z0-9_]+" <REV> -- web4-standard/ | grep -vE "_$" | sort -u
```

| Quantity | `73436fa6` (2026-08-13) | `HEAD` (2026-08-20) | C378 baseline | Moved? |
|---|---|---|---|---|
| `|corpus|` (`web4-standard/`) | **57** | **57** | 57 | no |
| `|SSOT|` (`core-spec/errors.md`) | **25** | **25** | 25 | no |
| `|seed|` (`initial-registries.md`) | **31** | **31** | 31 | no |
| `|corpus ∖ SSOT|` | **32** | **32** | 32 | no |
| in **neither** watched file | **26** | **26** | 26 | no |
| files carrying `W4_ERR_*` | **14** | **14** | 14 | no |

**No mint, no retirement, no relocation. The trigger did not fire.** `0` commits touched `registries/`;
the single `web4-standard/` commit in the window touched no registry value.

### The matcher is the measurement — a `+6` offset, published rather than silently corrected

The reviewer of this pass's scope reproduced `57` but reported `67` from a neighbouring `W4_` regex, and
this pass's own first run returned **63 / 31 / 31 / 38**, a constant `+6` against every baseline. Cause,
isolated and published because the successor will hit it too:

`sed 's/_$//'` **strips** the trailing underscore from prefix/glob tokens; `grep -vE "_$"` **excludes**
them. Seven such tokens exist at HEAD — `W4_ERR_ACP_`, `W4_ERR_AUTHZ_`, `W4_ERR_BINDING_`,
`W4_ERR_CRYPTO_`, `W4_ERR_PAIRING_`, `W4_ERR_PROTO_`, `W4_ERR_WITNESS_`. Stripping admits them as codes;
one of the seven (`W4_ERR_ACP_` → `W4_ERR_ACP`) collides with a real token already present, so seven
prefixes yield `+6`. **C378's `grep -vE "_$"` is correct and this pass's first matcher was wrong.**
The two commands count different populations; neither number is "the" answer without its command.

### A ledger correction: two different size-6 sets have been carried under one description

The carry index describes C378's six survivors as **"SDK-only 6."** They are not. Measured:

```
comm -23 <(…initial-registries.md…) <(…core-spec/errors.md…)        # seed ∖ SSOT
→ 6: W4_ERR_{BAD_SEQUENCE, BAD_TIMESTAMP, GRANT_EXPIRED, RATE_LIMIT, SCOPE_DENIED, WITNESS_REQUIRED}
     — reproduces C378:80-81 EXACTLY.

comm -23 <(…sdk/web4/errors.py…) <(…initial-registries.md…)          # SDK ∖ seed
→ 6: W4_ERR_{CROSS_SOCIETY_EXCHANGE_INVALID, CROSS_SOCIETY_LAW_CONFLICT, CROSS_SOCIETY_UNRECOGNIZED_LCT,
     CROSS_SOCIETY_WITNESS_REQUIRED, PROPAGATION_SCOPE_UNSUPPORTED, R7_REPUTATION_INVALID}
     — this is C298's row (overlap 24 / SDK-only 6 / registry-only 7), unchanged.
```

**Two disjoint sets, both of size 6, one description.** The equal cardinality is what let the labels
merge. Not a defect in the standard; a defect in the ledger, corrected here. Both rows stand.

**B-C1**: `grep -c W4_ERR_WITNESS_REQUIRED core-spec/errors.md` → **0**. Still **half-discharged**
(`PROTO_FORMAT` in at `afd04623`, `WITNESS_REQUIRED` out). The 6 → 5 transition C378 pre-registered has
**not** occurred.

---

## §B′ — mirror set RE-DERIVED (the standing C298 → C338 → C378 guard)

Re-derived from the pre-registered predicate (`C338:75`) — *does the artifact mint, restate, or enforce a
Web4 registry identifier?* — **not** inherited from C378's list, whose own guard warns it is "as
inheritable-and-wrong as C298's was."

```
git grep -lE '0x[0-9A-F]{4}\s*\||^\| *`?w4_[a-z]|evidence-type *=|suite.?id' HEAD -- web4-standard/
```

Re-derivation returns C378's members **plus two the inherited list does not carry**:

| Member | Status vs C378's list | Mints |
|---|---|---|
| `registries/{cipher-suites,error-codes,extensions,initial-registries}.md` | inherited ✓ | suite IDs, error codes, extension types |
| `core-spec/core-protocol.md`, `core-spec/errors.md` | inherited ✓ | canonical suites; SSOT codes |
| `implementation/sdk/web4/{errors,security}.py` | inherited ✓ | 30 `W4_ERR_*` tokens / 37 enum members |
| `test-vectors/validate_context_refs.py` | inherited ✓ (C338's member) | — (gate) |
| **`protocols/web4-entity-relationships.md`** | **NEW** | `evidence-type = "EXISTENCE" / "ACTION" / "STATE" / "TRANSITION"` (ABNF, `:304`) |
| **`submission/draft-web4-core-00.xml`** | **NEW** | four requested IANA registries (`:319-331`) |
| `test-vectors/security/security-primitives.json` | admitted, **not charged** | ≡ HS-X1 / C336-N4, handshake-owned |

**Both new members are exactly N1's subject matter.** This is the third consecutive pass at which
re-derivation returned something the inherited list did not — the guard is earning its cost, and it
should not be retired.

**Executed (v27)**: `python3 web4-standard/test-vectors/validate_context_refs.py` → **exit 0**, all
referenced contexts backed except the 1 carried (`t3v3.jsonld`, C310-N3). Behaves as documented.

---

## §C — the `https://web4.io/` namespace census: **RUN**, after two deferrals

C338 deferred it *with* a published instrument and a stated reason. C378 deferred it again, explicitly
saying it was not run. **Both deferrals would have satisfied a "run it or decline with a reason" bar** —
which is why this pass separated the two decisions: **executing the instrument is unconditional; the
12-audit read governs only whether a charge is laid.**

### The instrument, run verbatim (C338:143)

```
grep -rhoE "https://web4\.io/[A-Za-z0-9_./-]+" web4-standard/ --include=*.{json,jsonld,md,py,ttl} \
  | sed -E 's|(https://web4\.io/[a-z0-9-]+)/.*|\1/|' | sort | uniq -c
```

| Root | C338 (2026-08-08) | **C418 (HEAD)** | filtered | **unfiltered** |
|---|---|---|---|---|
| `contexts/` | 319 | **319** | 319 | **322** |
| `schemas/` | 66 | **66** | 66 | 66 |
| `ontology#` | 29 | **28** | 28 | **29** |
| `ns/` | 18 | **18** | 18 | 18 |
| `lct/` | 8 | **8** | 8 | 8 |
| `ontology/` | 7 | **7** | 7 | 7 |
| `errors/` | 1 | **1** | 1 | 1 |
| **total** | 448 | — | **447** | **451** |

**Seven roots, stable at 149 days.** Run also **case-insensitively and unfiltered** (v73), and diffed:
`ci` and case-sensitive are identical (451 = 451) — the corpus has no case variants. Filtered and
unfiltered differ by **4**, and all 4 are in one file (§D).

### The 12-audit read — which is what decides charging

Read: C40, C58, C86, C98, C134, C162, C170, C310, C314, C328 (all present in `docs/audits/`) plus the two
internal-consistency docs. Disposition **per root**, because a per-artifact verdict would hide this:

| Root | Disposition | Basis |
|---|---|---|
| `ns/` | **RATIFIED — not chargeable** | `docs/history/design_decisions/JSONLD-NAMESPACE-RECONCILIATION.md:14` (**Status: Decided**, 2026-03-24). `C314:220` verified compliance: `schemas/contexts/*.jsonld` **10 of 10** use it. |
| `ontology#` | **RATIFIED** | same decision, `:15`. Corroborated `C170:61`, `C328:133`. |
| `contexts/` | **RATIFIED** | same decision, `:16` — and it is explicitly *"a URL, not a namespace"*, so it is not a registrable namespace at all. |
| `ontology/` | **ALREADY ADJUDICATED** | the trailing-slash divergence is `C58:96`'s finding, re-confirmed `C170:61`. Sibling-owned; not re-charged. |
| `lct/` | **ALREADY ADJUDICATED** | `C58:102` — the CURIE-expansion mismatch. Sibling-owned. |
| `errors/` | **ALREADY ROUTED** | I2 (C30) → `C338-N2`, routed to the errors lineage. Not re-charged (v72). |
| `schemas/` | **NOT CHARGEABLE (v16)** | 27 distinct URIs across 42 files, and they are JSON Schema **`$id`** values — self-identifying, resolved internally by `$ref`. `v16`: absence of a namespace registry is not by itself prohibited; a domain you control is yours to mint. |

**VERDICT: the census is RUN and produces NO charge.** Every one of the seven roots is ratified,
already-adjudicated by a named prior finding, or protected by v16. C338's instinct that the class was
pre-handled was **correct** — and it took running the instrument to prove it rather than assume it.

**The deferral is DISCHARGED and must not be carried to C458.** What replaces it is a one-line watch:
if an **eighth** root appears, or if any root's disposition above changes, that is the finding.

---

## Findings

### C418-N1 (MEDIUM, net-new) — four in-tree artifacts each state Web4's IANA Considerations, and the four requested registry sets have an empty intersection

`registries/README.md:6` opens: *"These registries define the IANA considerations for Web4 protocol
parameters."* That is the cluster's own statement of what it is. Three other artifacts make the same
claim for themselves:

| Artifact | Last touched | Registries it requests |
|---|---|---|
| `registries/README.md:10-13,20-25` | `3f1d6fad` 2026-06-18 | cipher-suites · error-codes · extensions *(initial-registries = "N/A, not a registration target")* |
| `submission/draft-palatov-web4-core-00.txt` §6 (`:683-737`) | `4a0dce74` 2026-04-29 | **URI scheme** · **Media types** · Error Codes |
| `submission/draft-web4-core-00.xml` `:319-331` | `afd04623` **2026-08-10**, `<date>` = **2026-08-09** | Suite Identifiers · Extension Types · Error Codes · **Evidence Types** |
| `submission/web4-rfc.md` §3 (`:131-141`) | `84f069a0` 2026-02-16 | Extensions · **Subprotocols** — *"MUST be registered with IANA"* |

**Union = 8 distinct registry names. Intersection = ∅** — `web4-rfc.md` requests neither an error-code nor
a cipher-suite registry, so even "Error Codes" (in 3 of 4) is not universal.

**Four of the eight have no `registries/` file and no `README.md` table row:**

```
grep -rlie 'media type'   web4-standard/registries/ → 0
grep -rlie 'uri scheme'   web4-standard/registries/ → 0
grep -rlie 'subprotocol'  web4-standard/registries/ → 0
grep -rlie 'evidence'     web4-standard/registries/ → 0
```

**"Evidence Types" is the sharpest of the four, because the standard *does* define it — normatively, and
elsewhere.** Narrowed from an absence to a weak presence before publishing (v66b/v73):

| Locus | What it holds | Modality |
|---|---|---|
| `protocols/web4-entity-relationships.md:304` | `evidence-type = "EXISTENCE" / "ACTION" / "STATE" / "TRANSITION"` — **ABNF production** | **normative** |
| `RELATIONSHIP_GUIDE.md:175-179` | the same 4 values, prose | 0 RFC2119 keywords |
| `QUICK_REFERENCE.md:59` | the same 4 values, one line | 2 RFC2119 keywords (elsewhere in file) |
| `core-spec/**` | — | **0 hits** |
| `registries/**` | — | **0 hits** |

So the XML asks IANA to create a registry whose values the standard **already fixes by ABNF**, while the
registry cluster that declares itself the IANA Considerations does not know the registry exists. This is
not "an undefined thing was requested" — it is a defined thing the registry cluster cannot see.

**The error-code registry — the one name 3 of 4 agree on — is requested in two incompatible number systems:**

| | `registries/error-codes.md` | `draft-…-00.txt` §6.3 |
|---|---|---|
| Base | **hex**, `0x0000`–`0xFFFF` | **decimal**, `1000`–`3999` |
| Codes | 11 | 9 |
| Classes | Protocol · Security · Trust · Entity · Private · Reserved (6) | Protocol · Trust · **Economic** (3) |
| Shared code values | — | **0 in common** |

`grep -rl 'Range 1000' web4-standard/` → **the draft only.** Same for `1001`, `3001`, `Slashing event`.
(`2001` matches 28 other files and is **year/numeric noise**, not the code — qualifier stated rather than
counted.) Neither scheme is the SSOT's symbolic `W4_ERR_*` (25 in `errors.md`, 57 in corpus). C70
enumerated **two** error-identifier vocabularies; `C338-N2` added the URI form as the **third**; this is a
**fourth**, and it is the only one in an artifact addressed to a standards body.

**Reachability confirmed (v54 — is the antecedent reachable?).** `SUBMISSION_PROCESS.md:18` names
`draft-palatov-web4-core-00.txt` as *the* submission filename format, and the XML twin was re-dated
**2026-08-09** in this window's neighbourhood. These are live submission vehicles, not archive.

**Severity MEDIUM, and why not higher or lower.**
- *Not HIGH*: the `.txt` carrying the decimal scheme is itself expired (*"Expires: March 15, 2026"*,
  header dated September 2025) and frozen 113 days. Nothing has been filed with IANA.
- *Not LOW*: the **XML** is live, was re-date-stamped 10 days ago, and requests two registries
  (`Evidence Types`, `Suite Identifiers` under that name) the cluster does not carry. And
  `registries/README.md:32` defers its Contact field as `TBD-before-IANA-submission` while
  `draft-…-00.txt:691` has **already filled it** (`Dennis Palatov <dp@web4.io>`) — the disclosure's
  polarity runs the wrong way (v57): the cluster defers a decision the submission artifacts have made.
- *Not B-D1-subordinate*: B-D1 is the **inward** inversion (SSOT ⊊ seed, `25 ⊊ 31`) and its remediation
  would not touch any of these four artifacts. Different direction, different artifacts, no overlap.
- *Not C336-N1*: that finding's predicate is the `submission/` tree's **crypto** definitions
  (`C336:267`). This one is the **IANA registry set**. Checked explicitly (v68) — the predicates differ,
  and a control that answers C336-N1's question does not answer this one.

**Novelty, published as the absence claim it is (v44):** `draft-palatov-web4-core-00.txt` is cited by
**12 of 252** audit documents *(measured at `HEAD` before this document was written; with it, 13 of
253 — v33, the instrument's denominator moves when the pass writes into the tree it is counting)*, at line anchors `236-250, 262, 350, 567, 617, 618-619, 798`. **§6 spans
`:683-760`. Anchors inside it: 0.** `grep -rl 'Range 1000' docs/audits/` → **0**. `'IANA Considerations'`
appears in **1** audit (`C302:470`) and refers to `web4-lct.md` §6, a different file. The XML's IANA list
has never been read; `C378:87` counts the file (`draft-web4-core-00.xml +12/−3`) without opening it —
accurate as far as it goes, and stated that way rather than as blindness.

**Routing**: **operator / standard-editor.** Two mutually exclusive remedies, an author's call, not an
auditor's: (a) the `submission/` artifacts are authoritative ⇒ `registries/` gains files for URI scheme,
Media types, Evidence Types, Subprotocols and `error-codes.md` converts to decimal ranges; or (b)
`registries/` is authoritative ⇒ all three submission IANA sections are rewritten against it.
**Not self-applied**: B-D1 gates all `registries/` remediation, and three of the four artifacts are
outside this lineage's target.

### C418-N2 (LOW, instrument — the mechanism behind N1) — the census instrument's file filter excludes the one file class the submission tree uses

C338 published the census instrument with `--include=*.{json,jsonld,md,py,ttl}` and C378 inherited it as
"run it in one command." Measured at HEAD:

```
files carrying web4.io URIs, by extension:  json 41 · py 18 · md 17 · jsonld 12 · ttl 4 · txt 1
filtered total 447   unfiltered total 451   Δ = 4
```

All 4 invisible occurrences are in **`web4-standard/submission/draft-palatov-web4-core-00.txt`**
(`:297` `ontology#`, `:474`/`:797`/`:798` `contexts/…jsonld`) — the IETF Internet-Draft, and the only
`.txt` in the tree carrying the subject matter.

**Currently harmless, and said so plainly**: both roots in the blind file are **ratified**
(`JSONLD-NAMESPACE-RECONCILIATION.md:14-16`), so the census's verdict in §C is unaffected. This is
exactly the disposition C338 gave its **own** negative 3 — a gate blind to a tree that happens to be
empty. Re-tested at HEAD: `grep -rhoE "https://web4\.io/contexts/" web4-standard/testing/` → **0**,
so C338's negative 3 **remains negative**.

**Charged LOW anyway, for one reason**: this filter is why N1 went ten passes unseen. The blind tree is
not empty of *findings*, only of *namespace roots* — and an instrument that excludes the outward
submission artifact by file extension will keep excluding it. **Corrected instrument, pre-registered for
C458**: drop `--include` entirely and add `-I` if binary noise appears.

---

## Published negatives — measured and declined

1. **The namespace census itself** — RUN (§C), 7 roots, **no charge**, per-root basis published. The
   two-pass deferral is **discharged**, not carried.
2. **C338's gate blind tree** — re-tested, **still 0**. Negative 3 stands as a negative.
3. **`schema_registry.json` / `_SCHEMA_FILES`** — **not re-derived and not re-charged**, per C378's five
   published grounds (incl. the `hestia_query_policy.schema.json` basename collision that makes the
   implied fix wrong). Recorded as inherited, not re-measured.
4. **Extension-vocabulary disjointness** ≡ `C70:63`; **`w4_sig_cose@1`/`w4_sig_jose@1`** ≡ B-C6. Not
   re-charged.
5. **`registries/README.md:32` `TBD-before-IANA-submission` as a standalone defect** — **declined.** It is
   disclosed at the point of use and the cluster is `Status: Draft`. Its only load-bearing role is inside
   N1, as polarity evidence; charged there, not separately (v57).
6. **"Expert Review has no designated expert"** — **declined as a standalone charge.** All three
   registrable files require Expert Review (two directly, `extensions.md` by implication via
   `README.md:28`) and `README.md:32` designates none. But `C378-N2` already owns the shape — the
   Specification Required policy satisfied **0 of 7** — and extending it to the other two rows is a reach
   escalation on a B-D1-gated row, not a new defect. Recorded for C458 with its numbers.

---

## Inbound: C416-N3 — **disposition only, no severity**

C416 routed its N3 (the `cipher-suites.md` orphan) into this slot. Dispositioned per the originating
pass's own words, **not re-adjudicated** (v72):

> `C70:17` records it verbatim as *"**0** (orphan)"*; `C298:87` ruled it *"Not net-new.
> B-D1-subordinate."* — `C416:140`

**Disposition: ACCEPTED AS A NOTE, folded into B-D1's operator memo. No new severity, no new charge.**
C416's own qualifier is carried intact: the *file* is tracked (`C378:148` freeze-checks all five), only
the orphan row's *content* has not been restated since C298.

---

## Standing carries — re-verified at live HEAD

| Row | Status |
|---|---|
| **B-D1** (FLAGSHIP, MED, operator) | **UNANSWERED.** `25 ⊊ 31`, 0 exceptions the other way, unmoved at both endpoints. Gains **C418-N1** as an *outward* face — distinct in direction from the inward inversion. Gates all `registries/` remediation ⇒ this pass stays audit-only. |
| **B-C1** (MED, `errors.md`-owned) | **HALF-DISCHARGED, unchanged.** `WITNESS_REQUIRED` still absent from the SSOT (measured `0`). The pre-registered 6 → 5 transition has not occurred. |
| **B-C4 ≡ B-7** (MED, operator) | Re-verified in place; **not re-opened**, **not re-measured by its own enumeration** (C296-N3). |
| **B-8** (MED, operator) | `W4_ERR_LEDGER_WRITE` / `W4_ERR_ACP_LEDGER_WRITE` collision — both still in the corpus set. Unchanged. |
| **B-C2/B-C3/B-C5/B-C6/B-C7, B-D2, B-D3** | Unchanged, B-D1-subordinate or sibling-owned. Not re-opened. **B-C7** carries C378-N2's widened domain (3 → 7). |
| **DELTA-1** (MED, handshake-owned) | Unchanged. |
| **C298-N1/N2/N4/N5** | Unchanged. `implementation/` untouched in window ⇒ N1 frozen by construction. |
| **C338-N2** (LOW) | Unchanged, errors-lineage-owned. Its subject (`errors/` root) re-measured at **1** in §C. |
| **C378-N1** (MED) | **Unchanged and re-confirmed**: the trigger's operands still cover **31 of 57**; 26 remain invisible to it. |
| **C378-N2** (LOW) | Unchanged. Gains negative 6 above as corroboration on the other two policy rows. |
| **C258-N1** | Remains **SUPERSEDED / FALSE as written**. Do not re-publish. |
| **C338-N1** | **DISCHARGED** by C374 §D. Not re-routed. |

### Row-set census (v19)

C378 published **11** inherited rows + 2 net-new = 13. **All 13 present above**, plus C416-N3 inbound.
**0 silent drops.** One row changed character (B-D1 gains an outward face) — a gain, not a disposition.

---

## §own-error — what this pass got wrong before publishing

1. **The first trigger run returned 63/31/31/38, a `+6` on every baseline**, because it used
   `sed 's/_$//'` where C378 used `grep -vE "_$"`. Caught by the v17 post-write re-run against C378's
   published numbers; cause isolated to seven prefix tokens with one collision. **Published in §B rather
   than silently corrected**, because the successor will reach for the same `sed`.
2. **"Evidence Types has no taxonomy" was drafted as an absence and is false.** Narrowing before
   publishing (v66b/v73) found a **normative ABNF** at `protocols/web4-entity-relationships.md:304` plus
   two prose loci. The corrected form is **stronger**, not weaker — a defined thing the registry cluster
   cannot see beats an undefined request — but the drafted version would have been a fourth instance of
   the C414 false-absence shape.
3. **`2001` was nearly published as a shared code value.** It matches 28 files; all are year/numeric
   noise. The qualifier is stated in N1 rather than the count being quietly dropped.
4. **The carry index's "SDK-only 6"** was taken at face value and did not reproduce. Arbitrating a
   **member** rather than the count (v63) showed two disjoint size-6 sets under one label. Corrected in §B.

---

## Routing summary

| Item | Severity | Route |
|---|---|---|
| **C418-N1** | MED | **operator / standard-editor** — author's ruling between two exclusive remedies. Not self-applied (B-D1-gated; 3 of 4 artifacts out of lineage). |
| **C418-N2** | LOW | **this lineage** — corrected instrument pre-registered for C458 below. No spec change. |
| C416-N3 | — | note, folded into B-D1's memo. No severity. |
| Negative 6 (Expert Review) | — | recorded for C458 with numbers; reach-escalation on C378-N2, not net-new. |

**C419 remediation slot: NO-OP.** N1 is operator-gated and mostly out-of-lineage; N2 is a method change.
**Do not manufacture a `registries/` edit.**

---

## Method carry — apply from C420 on

**v75 — a published instrument inherits its blind spots, and a filter is the blind spot that survives
review.** C338 published a census command so the next pass could "run it in one command," and C378 and
this pass both did exactly that. The command was correct; its `--include` list was a **guess about where
the subject matter lives**, made once, and then carried three passes as if it were the domain. The one
file it excluded was the only outward-facing one — the artifact whose contents would become permanent
under someone else's change control.

Three riders:

1. **Run any inherited sweep once with its filters removed, and diff.** Not to replace it — to *measure
   what the filter costs*. Here the cost was 4 occurrences, 1 file, and a MEDIUM finding. A filter that
   costs 0 is free to keep; a filter that costs anything must be justified by name.
2. **A convenience published for a successor is a claim about the domain.** "Run it in one command" reads
   as *this command covers the question*. If it does not, say what it excludes **in the same sentence**,
   the way a denominator is published with a count (v40).
3. **Deferral is not the failure mode; the disjunction is.** Two passes deferred this census, each
   *correctly* — with a stated reason and a published instrument. What made the loop stable was that
   "run it **or** decline with a reason" accepted both. **Separate execution from adjudication**: run the
   instrument unconditionally, and let the prior-art read decide only whether to *charge*. Here that
   produced no charge — and the run is still what proved it, and what discharged a 12-day-old row.

---

## Guards for the next registries delta (~C458)

- **The namespace census is DISCHARGED — do NOT carry it as unrun.** §C holds the numbers. Replace it
  with a watch: **7 roots at 451 occurrences unfiltered**; an 8th root, or a change to any per-root
  disposition in §C, is the finding.
- **Use the CORRECTED census instrument**: drop `--include` entirely. `--include=*.{json,jsonld,md,py,ttl}`
  is blind to `submission/draft-palatov-web4-core-00.txt`.
- **The corrected B-D1 trigger did NOT fire.** Baseline unchanged and re-confirmed at both endpoints:
  **corpus 57 · SSOT 25 · seed 31 · corpus∖SSOT 32 · in-neither 26 · 14 files.** Use
  `grep -vE "_$"`, **never** `sed 's/_$//'` (+6, §B).
- **B-C1**: if `W4_ERR_WITNESS_REQUIRED` enters `errors.md` §2, B-C1 closes and **seed ∖ SSOT** goes
  6 → 5. That set is **not** the SDK∖seed set, which is also 6 — check which row you are moving.
- **C418-N1 is the live row.** Re-check all four artifacts' IANA sections, and re-check whether
  `registries/README.md:32`'s Contact is still `TBD` while `draft-…-00.txt:691` names a person.
- **RE-DERIVE the mirror set again.** It returned 2 new members this pass, both load-bearing for N1.
- Do **NOT** re-open: B-A6; `:6`'s `P-256 ECDH` (≡ B-C4/B-7); B-D2; B-D3; the numeric-orphan fact
  (≡ B-D1); the submission tree's **crypto** cells (≡ C336-N1 — note its predicate is crypto, *not* the
  IANA registry set, which is C418-N1); `initial-registries.md:52` (≡ C374-N2, `C374:371` forbids fixing
  it in isolation); C338-N1 (DISCHARGED, C374 §D).
- Do **NOT** re-charge or re-derive: `schema_registry.json`/`_SCHEMA_FILES` (C378 negative 1, five
  grounds), extension-vocabulary disjointness (`C70:63`), `w4_sig_*` (B-C6).
- Do **NOT** re-run B-C4/B-7's grep scoped to its own enumeration (C296-N3).

### Rotation-interval recommendation (the honest exhaustion test, executed)

The scope reviewer asked this pass to propose an interval extension **if** the census ran clean *and* the
trigger did not fire. The trigger **did not fire** and the census **produced no charge** — so the
condition is met, and the recommendation is owed.

**Recommendation: keep +40. Do not extend to +80.** The condition was met and the answer is still no,
because the two net-new findings this pass did not come from the target or the window — both came from
**re-deriving an inherited instrument** (§B′ returned 2 new mirror-set members; §C's filter diff returned
N1's file). A 63-day freeze and a 0-commit window predicted a quiet pass and were wrong twice.
`C408`'s "frozen ≠ exhausted" holds here **on measurement, not on principle**. Revisit at C458 with the
same test: if that pass finds nothing after re-deriving both instruments, extend then.

---

## Review-gate self-audit

This audit creates no surface and drives no consequential act — it is a read-only analysis producing one
Markdown record. No spec, code, schema, test, or sibling-ledger file was modified. No temporary probe was
written this pass; every measurement is a read or a `git grep` at a named revision.

```
surface: C418 registries delta-audit doc   act: none (read-only audit; 0 spec/code/ledger edits)
S: low/reversible [construct: docs/audits/C418-registries-10th-delta-2026-08-20.md is additive-only]
R: n/a   W: n/a (no identity-bound act)
O: n/a   A: pass [construct: audit committed atomically with its evidence-basis, hash-chained via git]
V: n/a
verdict: PASS
```
