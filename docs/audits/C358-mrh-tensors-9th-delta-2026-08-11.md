# C358 Audit: `mrh-tensors.md` Ninth Delta Re-Audit

**Date**: 2026-08-11
**Target**: `web4-standard/core-spec/mrh-tensors.md` (422 lines, blob `581e9b48`)
**Prior pass**: C318 (2026-08-05, `c3976cec`) — 8th delta, 0 net-new, zero mutation
**HEAD at audit**: `360c3660`
**Window**: `c3976cec..360c3660` = **53 commits**, of which **0** touch any mrh subject-matter artifact
**Mutation**: **ZERO**

---

## What a complete pass looks like here (stated before §A, not after)

The target has been byte-frozen since `b8740803` (2026-07-09, **33 days**). The 53-commit window
touches **none** of the five artifacts this lineage owns. Eight prior passes have read this file and
returned 0 net-new for the last four consecutive fires. Under the freeze-check instrument every one
of those passes was correct and this one would be too.

So this pass does not open by reading. Per method-carry **v43** (*coverage is not execution*, born
C356), it opens by **executing the artifacts against each other**: the document's own fenced turtle
blocks are loaded into an RDF store and the document's own fenced SPARQL blocks are run against them.
Nine passes have argued about this file's RDF — its undefined vocabulary (C40-D1/D2/X1/X2/X3), its
entailment regime (C40-F7), its missing `PREFIX` declarations (C40-F6/F12) — and **none of them ran
any of it.**

The instrument found the file is not clean. Both of the document's `lct:`-referencing example queries
return empty against the document's own example data, and have since **2025-09-13** — 332 days, nine
passes, and one ratified remediation commit that touched the very lines involved.

Every number below is published with its instrument and the rule that generates it. The repro script
is published verbatim in §E and is re-executable. Three of this pass's own drafted claims did not
survive review; they are corrected in §F, not buried.

### Instrument caveat (published, per the C278 §D-4 precedent)

System `python3` on this host has **no `rdflib`**. All RDF/SPARQL results below were produced with
`rdflib 7.6.0` installed into a scratch venv (`~/.web4/venv`). This is instrumentation, not a
deliverable — no package manifest, lockfile, or CI config was modified, and the script in §E declares
its own dependency. `pytest` was installed to the same venv to re-run the SDK suite.

### Pre-registered window and admission criterion (written before the sweep, unchanged after)

- **Window**: `c3976cec..360c3660`, `git log` rooted at repo root, all filetypes, `docs/audits/` **and**
  `web4-standard/docs/audits/` both searched by absolute path on every coverage grep (v17).
- **Artifact set** (the denominator for "0 touching"): `web4-standard/core-spec/mrh-tensors.md`,
  `implementation/sdk/web4/mrh.py`, `implementation/sdk/tests/test_mrh.py`,
  `test-vectors/mrh/graph-operations.json`, `web4-standard/ontology/`.
- **M1/M2/M3** carried unchanged from C318 §B′ (in-standard surface · mrh subject matter · consumed
  by a harness/validator/normative citation). The mirror set is **re-derived** in §C, not re-read.

---

## Summary

| Item | Disposition |
|---|---|
| Target byte-freeze | **HELD** — blob `581e9b48`, 422L, unmoved since `b8740803` (2026-07-09) |
| `mrh.py` / `graph-operations.json` / `web4-core-ontology.ttl` | **HELD** — blobs `dea3fb4a` / `cd322c61` / `fc4b4c36`, untouched this window |
| SDK suite | **55/55 green** (`tests/test_mrh.py`) |
| Spec's own turtle → RDF store | **4 blocks, 52 triples, all parse** |
| **Spec's own SPARQL → that store** | **§3.3 = 0 rows · §6 ASK = False.** See **N2**, **N1** |
| **C318-N1 (5 stale `:246` inbound anchors)** | **CLOSED** — applied by C319 `5f267641`; all five now resolve to `#51-critical-principle-trust-is-role-specific`. X4's anchor-migration precondition is **discharged** |
| C238-N2 (`edge_type` free `String`) | **OPEN, unchanged** — `web4-core/src/lct.rs:211` |
| C40-D1/D2/D3/X1/X2/X3 (ontology vocabulary) | **OPEN, deliberately NOT re-filed** — re-measured and confirmed as D1-REFRESH, not net-new |
| X4 / C278-N2 / D4 | **OPEN, operator-gated** — untouched by this pass |
| Net-new findings | **3** (N2 MEDIUM, N1 MEDIUM, N3 LOW) + 1 INFO |

---

## §A — Freeze and window

```
$ git log --oneline c3976cec..360c3660 | wc -l
53
$ git log --oneline c3976cec..360c3660 -- \
    web4-standard/core-spec/mrh-tensors.md \
    web4-standard/implementation/sdk/web4/mrh.py \
    web4-standard/implementation/sdk/tests/test_mrh.py \
    web4-standard/test-vectors/mrh/ web4-standard/ontology/
(empty)
```

| artifact | blob at HEAD | last moved |
|---|---|---|
| `core-spec/mrh-tensors.md` | `581e9b48` | `b8740803` 2026-07-09 |
| `implementation/sdk/web4/mrh.py` | `dea3fb4a` | 2026-04-17 |
| `test-vectors/mrh/graph-operations.json` | `cd322c61` | — |
| `ontology/web4-core-ontology.ttl` | `fc4b4c36` | — |

`web4-standard/implementation/sdk/tests/test_mrh.py`: **55 passed in 0.11s**.

Under the freeze instrument alone, this pass is clean. §B is what the freeze instrument cannot see.

---

## §B — Net-new findings

### N2 (MEDIUM) — flagship — `<lct:origin>`: the §3.3 horizon query's subject has no referent in the document's data, in any notation

**Locus**: `web4-standard/core-spec/mrh-tensors.md:159`, `:162`, `:166` (inside the §3.3 SPARQL block
`:146-171`). Data block: §1.1 `:34-49`.

§1.1 binds `@prefix lct: <https://web4.io/lct/>` (`:35`) and publishes the document's only MRH graph:

```turtle
lct:alice web4:boundTo lct:hardware1 .
lct:alice web4:pairedWith lct:bob .
lct:alice web4:witnessedBy lct:timeserver .
```

The §3.3 query traverses from `<lct:origin>`. Two independent problems, and the second is fatal on its
own:

1. `<lct:origin>` is an **angle-bracketed absolute IRI** with scheme `lct:`. It denotes the IRI string
   `lct:origin`. The CURIE `lct:origin` would denote `https://web4.io/lct/origin`. These are different
   resources, and RDF/SPARQL treat them as such — no error, no warning, just no match.
2. **Neither form has a referent.** `origin` appears nowhere in §1.1's data under any spelling. The
   §1.1 hub entity is `alice`. So unlike N1, the IRI-form correction alone does not repair §3.3 — the
   term itself is dangling.

**Executed** (rdflib 7.6.0; graph = the doc's own 4 turtle blocks, 52 triples; "D1-GRANTED" =
§2.1's 12 `rdfs:subPropertyOf` axioms materialised, +3 triples — i.e. the open C40-D1 finding
resolved in full):

| §3.3 `:146-171` variant | RAW | C40-D1 GRANTED |
|---|---|---|
| **as written** — `<lct:origin>` + `web4:hasRelationship` | **0 rows** | **0 rows** |
| IRI-form fix only — `lct:origin` | 0 rows | 0 rows |
| term-identity fix — `lct:alice` | 0 rows | **3 rows** |
| **the spec's own `:150-151` workaround, as written** | **0 rows** | **0 rows** |
| the `:150-151` workaround **+** term-identity fix | **3 rows** | 3 rows |

Read the last two rows together, because they are the finding.

`:147-151` is a note added by **this lineage's own remediation commit** `ab1aec64` (2026-06-09,
*"remediate(C41): apply autonomous-actionable findings to mrh-tensors.md"*, #290), discharging C40-F7.
It tells the reader the query needs an RDFS sub-property entailment regime and supplies a substitution
for a plain store: `(web4:boundTo|web4:pairedWith|web4:witnessedBy)`.

**That workaround is correct and it does fire.** Row 5 proves it: applied to a raw non-inferencing
store it yields 3 rows, exactly as advertised. It fully repairs the defect it was written to repair.
The charge here is *not* that C41 shipped a broken repair — that would be this lineage applying a
strict reading to C58 and a loose one to itself, which v31/v41 forbid.

The charge is narrower and harder to dismiss: **the repair is correct, the example it repairs still
returns nothing, and in the fourteen months since `bf01ac7c` (2025-09-13, where `<lct:origin>` was
introduced) no pass ever ran it.** C41 fixed the half it was pointed at, and the half nobody was
pointed at was invisible because the only instrument anyone used on this block was reading it. That is
method-carry **v43** instantiated against this lineage's own remediation.

**Severity MEDIUM, not higher.** Held below HIGH by C40's own published reasoning — *"No runtime
impact — SDK uses `MRHEdge` relation strings, not RDF inference"* — re-verified here at 55/55 green.
Held above LOW because the example returns **silence rather than an error**: a reader who copies §3.3
into a store gets an empty result set and no diagnostic pointing anywhere. Flagship status here is an
**ordering** (this is the finding no prior pass could have reached by reading), not a severity grade.

**Not covered by any open finding.** C40-F5 = a dead FILTER. C40-F7 = entailment, falsified as
sufficient by the D1-GRANTED column. C40-F6 = missing `PREFIX web4:` in §6. C40-D1/D2/D3/X1/X2/X3 =
undefined vocabulary. None reaches IRI form or a dangling subject.

**Route**: autonomous-actionable, single file, no design decision. `<lct:origin>` → `lct:alice` (or
introduce `lct:origin` into §1.1's data), plus `PREFIX lct: <https://web4.io/lct/>` in the block. The
ratified fix pattern is C59 `0d756773` — see N1.

---

### N1 (MEDIUM) — `<lct:alice>` / `<lct:bob>`: the §6 reachability ASK names two entities the document publishes, in a form that denotes neither

**Locus**: `web4-standard/core-spec/mrh-tensors.md:387` (inside the §6 SPARQL block `:378-388`).

```sparql
PREFIX web4: <https://web4.io/ontology#>

ASK {
    <lct:alice> (web4:hasRelationship+) <lct:bob> .
}
```

§1.1 `:40` publishes `lct:alice web4:pairedWith lct:bob` — the exact reachability this ASK tests. But
`<lct:alice>` denotes `lct:alice`, while §1.1's `lct:alice` denotes `https://web4.io/lct/alice`. The
block also declares no `PREFIX lct:`, so the CURIE form is not even available to it.

| §6 `:378-388` variant | RAW | C40-D1 GRANTED |
|---|---|---|
| **as written** — `<lct:alice>` / `<lct:bob>` | **False** | **False** |
| IRI-form fix — `lct:alice` / `lct:bob` (+ `PREFIX lct:`) | False | **True** |
| IRI-form fix + §3.3-style property path | **True** | True |

The placeholder defence does not reach this block: `alice` and `bob` are not placeholders, they are
the document's two named example entities, and the query asks precisely the question §1.1's data
answers.

**Class precedent, ratified.** This is not a novel defect class in this corpus. **C58-B5(b)**
(`docs/audits/C58-society-authority-law-audit-2026-06-15.md:102`) charged it verbatim against the SAL
spec — *"the queries reference subjects as full IRIs `<lct:societyRoot>` … but the §3.3 example data
writes them as CURIEs `lct:societyRoot` which under `@prefix lct: <https://web4.io/lct/>` expand to
`https://web4.io/lct/societyRoot` — different IRIs, so the example ASK/SELECT would never match the
example triples."* It was remediated by **C59 `0d756773`** (2026-06-15, #330). The live SAL spec today
declares both prefixes inside its SPARQL and uses CURIE subjects
(`web4-society-authority-law.md:286-287`, `:299-300`).

So the angle-bracket form is a defect **by ratified corpus precedent**, not a matter of house
convention — and the fix shape is already agreed. C59 remediated the live SAL spec and did not sweep
the one other live normative artifact holding the identical contradiction: this file. See N3 for why
that omission is worse than an oversight.

**Route**: autonomous-actionable, apply the C59 pattern.

---

### N3 (LOW) — inbound carry: C58 named `mrh-tensors.md` the exemplar of the practice it was charging the sibling for failing

**Locus**: `docs/audits/C58-society-authority-law-audit-2026-06-15.md:102`, half (a).

C58-B5 is a two-facet finding. Half (b) is N1's class precedent. Half (a) reads:

> *"Neither SPARQL block declares `PREFIX web4: <...>` (nor `lct:`), **unlike the house style in
> sibling mrh-tensors.md where every block opens with the PREFIX lines** → a parser rejects the
> undeclared prefix."*

Measured against the target at HEAD:

| | count |
|---|---|
| SPARQL blocks in `mrh-tensors.md` | **6** |
| declaring `PREFIX web4:` | **6 of 6** |
| declaring `PREFIX lct:` | **0 of 6** |
| using an `lct:`-scheme term | **2 of 6** (§3.3 ×3, §6 ×2) |

C58-B5(a) is therefore **true about `web4:` and blind about `lct:`**. It canonised as the exemplar a
file that carries, in two of its six blocks, the exact defect B5(b) was charging one paragraph later —
and the exemplar status is very likely *why* the sweep stopped at the SAL spec.

Compounding it: `ab1aec64` (C41, 2026-06-09) added `PREFIX web4:` to five SPARQL blocks in this file,
six days *before* C58 wrote the exemplar sentence. C41's F6 fix text named only `web4:`; the
remediator applied exactly what was named; `lct:` survived. That is **v31** operating exactly as
described — a remediation licenses only the predicate it named — and it is the reason C58 found a
file that genuinely *looked* like the house style.

Seven mrh passes since (C90, C129, C162, C200, C238, C278, C318) never tested a sibling audit's
published claim about their own target. **Standing carry for the next mrh delta and a general one:
when another lineage's audit cites your target as an exemplar, that citation is a measurable claim —
measure it.**

**Route**: no mutation of C58 (audit records are historical). Discharged by fixing N1/N2, at which
point B5(a) becomes true.

---

### INFO-1 — mirror routing: two `forum/nova/` bundle files carry the same contradiction; leave them

Derived in §C. `forum/nova/web4-sal-bundle/mrh-tensors.md` (`:38` binds `lct:`, `:146/:149/:153/:338`
use `<lct:...>`) and `forum/nova/web4-sal-bundle/web4-society-authority-law.md` (the pre-C59 source of
the file C59 fixed) both hold it.

**These are frozen inbound contribution records — a bundle-as-received should not be retro-patched.**
Recorded here so a future sweep does not mistake them for live divergence, and explicitly **not**
charged against C59.

---

## §C — Mirror set, re-derived with its denominator

The question the freeze instrument cannot ask: *how far does this defect class reach?* Answered by
sweep, not assertion.

```
$ for f in $(git ls-files '*.md' '*.ttl' '*.rq' | grep -v '^archive/'); do
    grep -q '<lct:' "$f" || continue
    grep -qE '@prefix lct:|PREFIX lct:' "$f" && echo "CONTRADICTORY: $f" || echo "consistent:    $f"
  done
```

**Denominator: 13 files** contain an `<lct:...>` term. **Exactly 4** also bind `lct:` as a prefix and
therefore hold the contradiction:

| file | status |
|---|---|
| **`web4-standard/core-spec/mrh-tensors.md`** | **the target — the only LIVE NORMATIVE artifact in the set** |
| `docs/audits/C58-society-authority-law-audit-2026-06-15.md` | quotes both forms while charging the defect — not a defect |
| `forum/nova/web4-sal-bundle/mrh-tensors.md` | frozen inbound bundle — INFO-1 |
| `forum/nova/web4-sal-bundle/web4-society-authority-law.md` | frozen inbound bundle, pre-C59 source — INFO-1 |

The remaining **9** (2 `web4-standard/rfcs/`, 5 `docs/audits/`, `docs/how/`, `proposals/`,
`forum/nova/agency-bundle/`) bind no `lct:` prefix at all and are internally consistent. Their use of
`<lct:...>` as a URN-style scheme is coherent on its own terms; only a file that does both is
contradictory.

**Result**: the live normative surface holds this defect in **exactly one file**, and it is the file
C58-B5(a) had named as the exemplar of correct practice. That is the whole finding — no corpus sweep
is warranted, and the "N+1th artifact a remediation missed" is a single, unimpeachable one.

### `lct:` token census in the target — with the rule that generates each number

- **Rule 1** — `/lct:[A-Za-z0-9_]+/` (local name required); `<…>` wrapper decides angle vs CURIE:
  **21 tokens = 16 CURIE uses + 5 angle uses**.
  - CURIE at `:39 :40 :41 :45 :47 :256 :257 :261 :270 :320 :322 :328 :330`
  - angle at `:159 :162 :166` (`<lct:origin>` ×3) and `:387` (`<lct:alice>`, `<lct:bob>`)
- **Rule 2** — drop the local-name requirement: recovers **2 further bare `lct:` mentions**, the
  `:35` `@prefix` declaration and the `:81-82` comment ⇒ **23 strings total**.

Both published. Rule 1 does **not** generate 23 and Rule 2 does not generate 21; picking one number
silently is the defect class this lineage charges others with (v40 — *a metric's denominator is a
domain*). This pass's own first two drafts published counts that followed from neither rule; see §F.3.

---

## §D — Standing carries, re-measured

| carry | status at `360c3660` |
|---|---|
| **C318-N1** — 5 stale `mrh-tensors.md:246` inbound anchors | **CLOSED.** Applied by **C319 `5f267641`**. `grep -rn "mrh-tensors.md:246\|mrh §246" web4-standard/ --include=*.md` = **0**. All five loci (`docs/FRACTAL_ROLE_IDENTITY.md:37`, `rfcs/RFC-COMPOSITE-ENTITY-IDENTITY.md:54/:82/:117`, `rfcs/RFC-SHARED-POLICY-SUBSTRATE.md:165`) now carry `#51-critical-principle-trust-is-role-specific`, which resolves — `:246` is `### 5.1 Critical Principle: Trust is Role-Specific`. **X4's stated anchor-migration precondition is discharged.** |
| C129-O1 (`FRACTAL_ROLE_IDENTITY:53` → `:174`) | **CLOSED, re-verified** — reads `mrh-tensors.md:174` at HEAD |
| C238-N2 (`edge_type` free `String`) | **OPEN, unchanged** — `web4-core/src/lct.rs:211` `pub edge_type: String` |
| C40-D1 / D2 / D3 / X1 / X2 / X3 | **OPEN, deliberately NOT re-filed.** This pass independently re-measured `web4:hasRelationship` = **0** in every `.ttl`, `rdfs:subPropertyOf` = **0** in all four published ontologies, and `web4:pairedWith` absent (only `pairedWithRole`). All three are D1/D2/X1 verbatim ⇒ **D1-REFRESH, not net-new.** Recorded so the next pass need not re-derive it. |
| C40-D4 / C318-N2 (zone taxonomy) | **OPEN, operator-gated** — untouched |
| C278-N2 | **OPEN** — #581 closed with its general ask unanswered |
| X4 / N1(a) (§5 shrink) | **OPEN, operator-gated.** Its anchor precondition is now discharged (above); the shrink decision is not this pass's. |
| C318-N3 (`validate_vectors.py` exits 0 on an unknown suite) | **OPEN, re-verified** — `validate_vectors.py mrh` → *"0 passed, 0 failed"*, **exit 0** |

---

## §E — Repro (verbatim, re-executable)

Requires `rdflib` (system `python3` on the audit host has none — see the instrument caveat). Run from
repo root.

```python
#!/usr/bin/env python3
"""C358 repro — execute mrh-tensors.md's own SPARQL against mrh-tensors.md's own turtle."""
import re
from rdflib import Graph, RDFS
SPEC = "web4-standard/core-spec/mrh-tensors.md"
src = open(SPEC).read().split("\n")

blocks, i = [], 0
while i < len(src):
    m = re.match(r'^```([a-zA-Z-]*)\s*$', src[i])
    if m:
        lang, s, j = m.group(1) or "(none)", i + 1, i + 1
        while j < len(src) and not re.match(r'^```\s*$', src[j]): j += 1
        blocks.append((lang, s + 1, j, "\n".join(src[s:j]))); i = j + 1
    else: i += 1
print("A. fenced-block inventory:",
      {l: sum(1 for b in blocks if b[0] == l) for l in sorted({b[0] for b in blocks})})

# §2.1/§5.2/§5.4 turtle omit the prefixes §1.1 declares; the spec says so at :81-82.
PRE = ("@prefix web4: <https://web4.io/ontology#> .\n@prefix lct: <https://web4.io/lct/> .\n"
       "@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .\n")
raw = Graph()
print("\nB. turtle blocks:")
for lang, a, b, body in blocks:
    if lang != 'turtle': continue
    try: Graph().parse(data=body, format='turtle'); solo = "parses standalone"
    except Exception: solo = "needs §1.1 prefixes (per the spec's own :81-82 note)"
    n0 = len(raw); raw.parse(data=PRE + body, format='turtle')
    print(f"   L{a}-{b}: +{len(raw)-n0:2d} triples  ({solo})")
print(f"   MERGED: {len(raw)} triples")

# C40-D1 GRANTED: materialise the subPropertyOf closure §2.1 declares.
ent = Graph(); [ent.add(t) for t in raw]
sub = [(s, o) for s, p, o in ent if p == RDFS.subPropertyOf]
ch = True
while ch:
    ch = False
    for s, o in sub:
        for x, _, y in list(ent.triples((None, s, None))):
            if (x, o, y) not in ent: ent.add((x, o, y)); ch = True
print(f"\nC. C40-D1 granted: {len(sub)} subPropertyOf axioms -> +{len(ent)-len(raw)} entailed triples")

q33 = "\n".join(src[145:171]); q6 = "\n".join(src[377:388])
LCT = "PREFIX lct: <https://web4.io/lct/>\n"
PATH = "(web4:boundTo|web4:pairedWith|web4:witnessedBy)"
def run(g, q):
    r = list(g.query(q))
    return f"ASK -> {r[0]}" if r and isinstance(r[0], bool) else f"{len(r)} row(s)"
cases = [
 ("§3.3", "as written                    <lct:origin>", q33),
 ("§3.3", "IRI-form fix only             lct:origin ", LCT + q33.replace("<lct:origin>", "lct:origin")),
 ("§3.3", "term-identity fix             lct:alice  ", LCT + q33.replace("<lct:origin>", "lct:alice")),
 ("§3.3", "spec's OWN :150-151 workaround, as written", q33.replace("web4:hasRelationship", PATH)),
 ("§3.3", ":150-151 workaround + term-identity fix  ",
   LCT + q33.replace("<lct:origin>", "lct:alice").replace("web4:hasRelationship", PATH)),
 ("§6  ", "as written           <lct:alice>/<lct:bob>", q6),
 ("§6  ", "IRI-form fix           lct:alice/lct:bob  ",
   LCT + q6.replace("<lct:alice>", "lct:alice").replace("<lct:bob>", "lct:bob")),
 ("§6  ", "IRI-form fix + §3.3-style property path   ",
   LCT + q6.replace("<lct:alice>", "lct:alice").replace("<lct:bob>", "lct:bob")
        .replace("web4:hasRelationship", PATH)),
]
print("\nD. RESULT MATRIX                                        RAW GRAPH   C40-D1 GRANTED")
for sec, name, q in cases:
    print(f"   {sec}  {name}   {run(raw,q):>12}   {run(ent,q):>12}")
```

Output at `360c3660`, `rdflib 7.6.0`:

```
A. fenced-block inventory: {'python': 3, 'sparql': 6, 'turtle': 4}

B. turtle blocks:
   L34-49: + 9 triples  (parses standalone)
   L81-107: +15 triples  (needs §1.1 prefixes (per the spec's own :81-82 note))
   L255-274: +14 triples  (needs §1.1 prefixes (per the spec's own :81-82 note))
   L318-333: +14 triples  (needs §1.1 prefixes (per the spec's own :81-82 note))
   MERGED: 52 triples

C. C40-D1 granted: 12 subPropertyOf axioms -> +3 entailed triples

D. RESULT MATRIX                                        RAW GRAPH   C40-D1 GRANTED
   §3.3  as written                    <lct:origin>       0 row(s)       0 row(s)
   §3.3  IRI-form fix only             lct:origin        0 row(s)       0 row(s)
   §3.3  term-identity fix             lct:alice         0 row(s)       3 row(s)
   §3.3  spec's OWN :150-151 workaround, as written       0 row(s)       0 row(s)
   §3.3  :150-151 workaround + term-identity fix         3 row(s)       3 row(s)
   §6    as written           <lct:alice>/<lct:bob>   ASK -> False   ASK -> False
   §6    IRI-form fix           lct:alice/lct:bob     ASK -> False    ASK -> True
   §6    IRI-form fix + §3.3-style property path       ASK -> True    ASK -> True
```

Also executed and **clean**, recorded as negatives so the coverage is legible:

- All 4 turtle blocks parse (3 of them only with §1.1's prefixes prepended, which the spec's `:81-82`
  note explicitly licenses — not a finding).
- All 3 `python` blocks are valid Python (`ast.parse` OK).
- All 6 SPARQL blocks **parse** (`prepareQuery` OK). The defect is semantic, not syntactic — which is
  exactly why nine passes of reading missed it.
- The 4 remaining SPARQL blocks (§5.5 ×2, §6 ×2) return 1/0/0/0 rows against this graph; those zeros
  are expected (the graph has no `web4:memberOf`, `web4:witnessRole` or `interactionType` data) and
  are **not** charged.

---

## §F — This pass's own errors (3, all caught in policy review, all published)

### F.1 — "Zero prior art" was false, and the matcher is why

The draft claimed this defect class had never been charged in the corpus, evidenced by four tokens
returning 0 across both audit trees: `lct:origin`, `absolute IRI`, `prefixed name`, `angle-bracket`.

**C58-B5(b) is the defect verbatim**, filed 2026-06-15 and remediated the same day. It matched none of
the four tokens because C58 says *"full IRIs"* and *"CURIEs"* — the standard vocabulary for exactly
this distinction, and the pair of terms most likely to be used by anyone who actually knows RDF.

This is [[feedback_loose_matcher_certifies_absence]] firing on a **novelty** claim rather than an
absence claim, which is the more dangerous direction: a false absence understates coverage, a false
novelty **overstates the finding and steals another pass's credit**. The correction made the finding
stronger — a ratified precedent with an agreed fix shape beats an unprecedented one.

**Rule for the next pass**: before claiming a defect class is unprecedented, search for it in the
vocabulary *a domain expert* would use, not the vocabulary *you* used to describe it. For RDF: full
IRI / CURIE / QName / prefixed name / absolute IRI — all of them.

### F.2 — The published repro did not reproduce

The draft stated *"changing only the IRI form yields 3 rows / True."* It does not. The script that
produced "3 rows" had also substituted `origin` → `alice`, with the substitution noted in a code
comment and dropped from the write-up. Two independent defects were compressed into one, which is how
the finding came to be framed as a single flagship instead of the correct N1/N2 split.

**Rule**: a repro cited in prose must be the repro that ran. Publish the matrix, not the cell that
flatters the framing. Cf. v41.4 — *if correcting your own cite strengthens your argument, the original
was guessed.* Here the correction strengthened it into two findings.

### F.3 — The census arithmetic did not follow from its own stated rule

The draft published "21 prefixed + 5 angle," then a corrected "1 declaration + 16 CURIE + 5 angle =
22." Neither follows from the stated matcher `/lct:[A-Za-z0-9_]+/`: that rule **requires a local
name**, so the bare `@prefix lct:` at `:35` cannot be the `+1`. The script silently used a *second*
line-level rule to find declarations and summed across both.

Corrected in §C: Rule 1 ⇒ 21, Rule 2 ⇒ +2 = 23 strings, both published with the rule that generates
them. A count that its own published rule cannot regenerate is the v40 defect this lineage charges
other documents with — committed here by the pass writing the charge.

### F.4 — the overclaim that survived two drafts and was killed by review

The draft's §B lead read: *"a ratified remediation shipped a repair that provably cannot fire."*
Row 5 of this pass's **own matrix** refutes it — the C41 property-path workaround yields 3 rows on a
raw store, fully repairing the entailment defect it was scoped to. Applying a strict
predicate-scope reading to C58 while granting a loose one to C41 is precisely the self-exemption
v31/v41 warn against, and the pass was one review away from publishing it.

The surviving charge — *the repair is correct, and the example still returns nothing, because nobody
ran it* — is narrower and strictly stronger, because it cannot be dismissed by a defender.

---

## §G — Carry to C398 (next mrh delta)

1. **Run the machine checks first, again.** They are cheap (one script, <2s) and they found the only
   net-new findings in five passes. Extend the harness: this pass executed turtle + SPARQL + Python
   syntax. It did **not** execute `graph-operations.json`'s `expected` blocks against `mrh.py`'s
   actual outputs independently of `test_mrh.py` (CI does it, but CI tests what the SDK does, not what
   the spec says).
2. **N1/N2/N3 status.** If unremediated, re-measure rather than re-file. If remediated, verify the fix
   with the §E script — the whole lesson of this pass is that a remediation to an example is not
   validated by reading the diff.
3. **The exemplar rule (from N3), general**: when another lineage's audit cites your target as an
   exemplar of good practice, that is a measurable claim about your file. Measure it. Nobody else
   will — the citing lineage has no reason to re-check, and yours has no reason to look outward.
4. **C40-D1 is now testable, not just arguable.** The §E harness can answer "would resolving D1 make
   these examples work?" mechanically. The answer today is **no** for both blocks — which is new
   information for the operator decision D1 has been waiting on since 2026-06-09.
5. Unchanged and untouched: X4 (§5 shrink — anchor precondition now discharged, decision still
   operator's), D4/C318-N2, C238-N2, C278-N2, C318-N3.

---

## Verdict

**9th consecutive pass with zero mutation. Not spec-clean.** Three net-new findings (2 MEDIUM, 1 LOW)
plus one INFO, all produced by the v43 opening — executing the artifacts instead of reading them —
against a target byte-frozen for 33 days that eight prior passes had certified clean, and a defect
that has been in the file for **332 days**.

The freeze instrument was never wrong. It was answering a different question.
