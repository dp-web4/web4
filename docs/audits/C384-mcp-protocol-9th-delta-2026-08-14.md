# C384 — `mcp-protocol.md` 9th delta audit

**Date**: 2026-08-14
**Target**: `web4-standard/core-spec/mcp-protocol.md`
**Prior pass**: C344 (8th delta, PR #680, 2026-08-09)
**Rotation**: C344 + 40
**Mutation**: **ZERO**. One new file (this document).

**Lineage enumeration rule** — *inclusive*: every `docs/audits/` file whose name matches
`^(C[0-9]+-)?mcp-protocol` . That gives **12** members: `C35`, `C76`, `C116`, `C117` (remediation),
`C148`, `C188`, `C226`, `C264`, `C304`, `C344`, plus **two** non-C-numbered originals —
`mcp-protocol-internal-consistency-2026-05-15.md` and `mcp-protocol-sdk-alignment-2026-05-15.md`.
(Most lineages have one non-C-numbered member; mcp has two. Stated here so C424 does not
"discover" the second one as a gap.)

---

## §A — Target and mirrors: frozen. Collapsed to the blob table.

Per the C344/C346/C370 policy precedent, **blob identity is strictly stronger than an anchor
table**: where the blob is unchanged, re-resolving anchors measures nothing.

| artifact | baseline (C344) | at HEAD | verdict |
|---|---|---|---|
| `web4-standard/core-spec/mcp-protocol.md` | blob `4491c1bb`, mover `3e765345`, 1020 L | blob **`4491c1bb`**, mover **`3e765345`** | **UNCHANGED — 4th consecutive frozen delta, 32 d** |
| `…/implementation/sdk/web4/mcp.py` | `b6c243c2` | `b6c243c2` | unmoved |
| `…/implementation/sdk/web4/mcp_server.py` | `759eaefa` | `759eaefa` | unmoved |
| `web4-standard/MCP_ENTITY_SPECIFICATION.md` | `f3d2613d` | `f3d2613d` | unmoved |
| `web4-standard/test-vectors/mcp/mcp-protocol.json` | `9b002074` | `9b002074` | unmoved |
| `hub/hub-daemon/src/mcp.rs` | `b05845bc` | `b05845bc` | unmoved |
| `web4-standard/schemas/r7-action-jsonld.schema.json` | `766611ef` | `766611ef` | unmoved |

**Window** (pre-registered): `3e765345..HEAD` = **240** commits, of which **18** touch
`web4-standard/`. The one notable in-window mover, `afd04623` (#678, 2026-08-10 — the commit
that broke two 8-pass freezes elsewhere), touches `errors.md`, `security-framework.md` and
`draft-web4-core-00.xml` only. **It does not reach this target or any mirror.**

### C344 guards, discharged

1. **Inbound grep first (v36)** — run before §A. See §B; it is where the entire yield came from.
2. **C77 note withdrawal** — *n/a, antecedent unmet.* The role block at `:313-314` still prints
   `{"entity","roleType"}`; the C77 note at `:340-347` is intact. **C344-N1 stands unremediated.**
3. **Outward draft's 2 half-migrated sites** — `draft-palatov-web4-core-00.txt:567` and `:868`
   still read `actor` + `roleType`. Unchanged. **C340-N1/handshake's row, not this lineage's.**
4. **Mirror set re-derived, not inherited** — `schemas/` re-read (row above); citation direction
   re-run (§B).
5. **Do-not-reopen list honoured** — the adjudicated exclusions, C226-N2, the B1 remediation, the
   `L787`/`L793` pair, C17 H2's role-value DESIGN-Q, and the archived impls-as-defect are
   untouched here.

---

## §B — The v36 set difference, and the tree this lineage has never entered

**Matcher, pre-registered:** domain word `mcp`, case-insensitive, whole repo, no filetype filter.

```
git grep -li "mcp"           -> 354 files
git grep -li "mcp-protocol"  -> 125 files      (the filename sweep)
comm -23 (sorted)            -> 229 files      (the residue)
```

Residue by top-level tree: `docs` 59 · `web4-standard` 41 · `archive` 33 · `hub` 26 ·
`whitepaper` 13 · `web4-trust-core` 13 · `forum` 12 · **`mcp-servers` 7** · `ledgers` 5 ·
`simulations` 4 · **`mcp-server` 4** · others 12.

The two `mcp-server*` trees hold **2,493 L** of TypeScript across three servers
(`wc -l mcp-servers/*/server.ts`; 22 tools) and **~1,400 L** of Python. In nine passes this
lineage has named them **twice**:

- `C188:89` — `mcp-server/server.py` ruled a **FALSE mirror (self-deprecated)**, on the authority
  of `` header `:20-27` ``.
- `C302:208-209`, `:230` — a *different* lineage (web4-lct) scored both trees **M1-FAIL** for
  *LCT* subject matter.

### Scoping — why entering this tree is not a reopened exclusion

`C188:89`'s verdict is that `server.py` is not a **mirror** of `mcp-protocol.md` — it implements
no spec structures, so it cannot evidence spec conformance. **That verdict is not disturbed here
and is re-affirmed below.** This pass reaches the file on a different warrant: it is a
**domain-word residue artifact** — an MCP server, in the repo, advertised in the root README,
that the mcp lineage's instrument has never measured for *its own* internal coherence. A
FALSE-mirror ruling scopes what an artifact can be used to *prove*; it does not immunise the
artifact from being *read*. (Cf. **v51**: a verdict is scoped to the loci it was measured on.)

### The C188 wire-layer synthesis — re-tested against a tree it never enumerated, and it HOLDS

C188 claimed corpus-wide that **"no code path assembles a Web4 Context Header onto a real MCP
message, signs an R7 envelope, or emits the §7.6/§7.7 error codes."** `mcp-servers/` was never in
its candidate list. Re-run with precise matchers over `mcp-servers --include=*.ts`:

| predicate | matcher | count |
|---|---|---|
| Web4 context header | `web4_context\|sender_lct` | **0** |
| R7 envelope | `\bR7\b` | **0** |
| §7.6/§7.7 error codes | `W4_ERR` | **0** |

**NEGATIVE — C188's synthesis holds on new evidence, now with a wider denominator.**
*Nuance, stated so the zero is not over-read:* `web4-identity/server.ts` **does** sign — LCT
payloads (`:98-101`, `:154`) and witness records (`:341`) — it just signs nothing shaped like an
R7 envelope. The zero is about the envelope, not about cryptography.

---

## C384-N1 (MED → owner of `mcp-server/`) — the 2026-04-27 canonical-staleness sweep asserts a correction it did not complete, and the one site its own stated mitigation does not cover is the only live one

**Filed as the Nth member of the established `remediation-incompleteness` /
[[remediation-introduced regression]] family** — *not* as a new class. Prior members: born at
C36; `C38:144`; `C56:67` ("H1 remediation INCOMPLETE — in-file survivor"); `C60:110-116`;
`C64:18` ("C26-H1 remediation INCOMPLETE … **provenance note over-claims a full match**" — the
near-exact structural precedent: a rename plus a note that over-claims); `C84:58`; `C166:90`
counts "8 prior instances". The family carries a **ratified fix shape** (`C60:197`):
*"remediation-completeness must sweep sibling code blocks of the same class."* That sweep is run
below.

### The claim

`mcp-server/server.py:20-27`, added by `4e195bdf`:

```
# DEPRECATION NOTE (2026-04-27):
# This standalone MCP server predates the canonical SDK implementation at
# web4-standard/implementation/sdk/web4/mcp_server.py. It uses a legacy
# trust-store import (`from governance import EntityTrustStore`) that may
# not resolve in current deployments. Prefer the SDK MCP server for new
# integrations. Internal trust dimension names have been corrected to the
# canonical 3-root form (T3: talent/training/temperament; V3: valuation/
# veracity/validity), but full migration to the SDK trust API is pending.
```

`:25-27` — "Internal trust dimension names **have been corrected** to the canonical 3-root form"
— is an **affirmative claim of completed work**. It is false 606 lines away in the same file.

### What `4e195bdf` actually changed

`git show 4e195bdf -- mcp-server/server.py` = **3 hunks**: `:20-27` (the note), `:1354` (the LLM
prompt), `:1376-1394` (`_default_t3` / `_default_v3`). The range `:595-645` is **untouched**.

So the sweep corrected the **producer** — `_default_t3()` now returns
`{talent, training, temperament}` — and left the **consumer**, `_tool_trust_update` (`:595`),
reading keys the producer no longer emits:

```python
631:  t3["reliability"] = max(0, min(1, t3["reliability"] + delta))
632:  t3["consistency"] = max(0, min(1, t3["consistency"] + delta * 0.5))
```

`:631` is unchanged since the file's first commit `f971230f` (2026-01-23). Producer and consumer
are **in the same file**.

### Executed (not argued)

`HOME` redirected to a tmpdir; module loaded by path; `GOVERNANCE_AVAILABLE` read **False**.

| arm | input | result |
|---|---|---|
| **treatment** | record created by post-sweep `_default_t3()` | **`KeyError: 'reliability'` at `server.py:631`** |
| **control** | hand-written legacy record `{competence, reliability, consistency}` (filename via the module's own `_safe_filename`) | **succeeds** → `{"reliability":0.505,"consistency":0.5025}` |
| **full JSON-RPC** | `tools/call web4.io/trust/update` over stdio | `{"jsonrpc":"2.0","id":2,"error":{"code":-32603,"message":"'reliability'"}}` |

The control is what bounds the claim. **Scope, stated precisely:** `web4.io/trust/update` cannot
succeed for any entity **lacking a pre-2026-04-27 trust record**. It is not "broken for every
entity" — a legacy record still works, and still round-trips the *legacy* names, never touching
`talent`/`training`/`temperament`.

`_tool_trust_update` is the **sole writer** of `~/.web4/trust/*.json` (`:603`, `:605`; the only
other read is `:571`). Other trust stores in the corpus live at different paths
(`~/.web4/governance/entities`, `~/.web4/identity/trustzone`). Since it raises *before* its
`json.dump`, **no new legacy record can ever be created** — the working set is closed and
shrinking.

### The mitigation is true everywhere except where it matters — sibling-site sweep per `C60:197`

`4e195bdf`'s commit message states: *"Internal attribute references (`trust.competence` etc.)
remain in **dead code paths gated by `GOVERNANCE_AVAILABLE=False`** — not harmful."*

```
grep -c  "GOVERNANCE_AVAILABLE"              -> 17   (15 guards + the 2 try/except assignments :48,:50)
grep -cE "^\s*if not GOVERNANCE_AVAILABLE"   -> 15   (:968 … :1269)
grep -nE '(t3|v3|trust|tensor)\s*\[\s*"'     -> :631, :632   — and nothing else
```

**The sweep result bounds the finding to two lines and vindicates the mitigation everywhere
else.** All other surviving 6D vocabulary (`:1170-1175`, `:1207`, `:1212-1213`, `:1285`) is
`trust.X` **attribute** access inside `GOVERNANCE_AVAILABLE`-gated functions — exactly what the
commit message describes. `_tool_trust_update` (`:595`) is **the one function with no gate**: it
is a local-JSON path, and its construct is a **dict subscript**, not an attribute reference. The
author's stated safety argument is about a different construct in a different code path.

### …and the gate it relies on has been permanently closed since before the sweep

```
c98c6aee  2026-02-05  chore: remove claude-code-plugin (moved to claude-code fork)
          deletes claude-code-plugin/governance/{__init__,entity_trust,ledger}.py
git merge-base --is-ancestor c98c6aee 4e195bdf   -> YES   (81 days earlier)
ls claude-code-plugin/                            -> README.md   (only)
git ls-files | grep 'governance/entity_trust.py'  -> (empty)
```

The `governance` package was deleted **81 days before** the sweep. So all 15 gated sites are dead
**by construction**, and the ungated local-JSON path is **the only live trust-write surface in the
file**. The mitigation is exactly inverted: it excuses everything that was already dead and does
not reach the only thing alive.

**Corollary (LOW, same locus):** `:23-24` says the legacy import "**may** not resolve in current
deployments." Measured, at HEAD it **cannot** resolve — there is no such package in the repo.

### Why the disclosed-phasing defense fails — polarity

This pass ran the strongest available refutation: the corpus **deliberately ships inert
mechanisms and says so at the point of use**, and charging that is charging its discipline
(C360's REFUTED arm; `starter-law.yaml:120-121`; `hub-law-schema.md:44`; mcp §7.3 kinetic verbs).
`server.py` is a self-deprecated prototype and root `README.md:464` labels it "legacy; prefer the
SDK". On its face this is that case.

**It is not, and the discriminator is polarity.**

- C360's protected convention is *declared inertness*: "Today the procedures are **descriptive**…
  future sprints will gate." Polarity: **"this does not work yet."**
- `:25-27` is the opposite: **"this has been corrected."** An affirmative claim of completed work
  that is false.

C360 protects honest disclosure. It does not protect an asserted correction that was not made.
The two clauses in the note that *are* genuine disclaimers do not reach the defect: `:22-24` is
scoped to the `governance` import, a path `_tool_trust_update` does not use; and `:27` ("full
migration to the SDK trust API is pending") describes **absent future work**, not present
breakage.

**The headline is therefore the false assertion, not the KeyError.** The KeyError is the proof.

### Materiality — the note is load-bearing in the audit record

`C188:89` is the **only** audit in the corpus ever to read this block, and it cited the range
`` `:20-27` `` as its grounds for excluding the file. It quoted the *true* clause ("predates the
canonical SDK"), and its FALSE-mirror verdict does not depend on the false clause — **the
exclusion stands.** But the record now shows an audit ruling resting on a header half of which
asserts a correction that was not made, and no pass since has tested it.

### Three guards, and why none fired

1. **The commit message's own mitigation** — true for 15 of 15 gated sites, false for the 1
   ungated one (above).
2. **The in-file note** — asserts the correction is done (above).
3. **`mcp-server/test_mcp.py` exercises this exact tool and reports success.** It calls
   `web4.io/trust/update` (`:81`, `"name": "web4.io/trust/update"` at `:83`) and prints the exact
   broken field at `:93`. Run at HEAD:

   ```
   5. Update Trust (success)
      Delta: None
      New T3 reliability: None
   ...
   === All tests passed ===          EXIT=0
   ```

   `grep -c assert test_mcp.py` = **0**. It reads the JSON-RPC error response through
   `.get()` chains, which yield `None`, prints them, and declares success. **v27 in its purest
   form: the green gate is the defect.** And nothing runs it — `ci.yml` is `cargo test` over a
   Rust matrix only; `sdk-test.yml` is path-filtered to `web4-standard/implementation/sdk/**`.
   `mcp-server/` is in **no** workflow.

4. **A fourth guard failure explains the 109 days — and it is the same defect class as N1.**
   `test_mcp.py:152-155` cleans up after itself with:

   ```python
   for f in trust_dir.glob("*.json"):        # :153
       if "test" in f.name:                  # :154 — filenames are sha256(entity_id)[:16]
           f.unlink()                        # :155
   ```

   `_safe_filename` has hashed since `f971230f` (day one), so the `:154` substring test has
   **never matched** and the cleanup **has never once fired**. Measured on this machine:
   `/home/dp/.web4/trust/31a59a5178196d06.json`, dated **2026-01-24**, carrying the 6D keys —
   and `_safe_filename("test-entity")` = `31a59a5178196d06`. **The author's machine holds a
   pre-sweep legacy record for the exact entity id the test uses**, so on that machine the test
   takes the control arm and genuinely succeeds; on any clean machine it prints `None`. The
   regression is invisible precisely where it would have been seen. Note the class: a **consumer
   keyed to a naming convention its producer does not use** — N1 again, in the test harness.

### Reach

Root `README.md:464` lists `mcp-server/` in the Concept→Implementation Map (labelled "legacy;
prefer the SDK"). `mcp-server/README.md` is 51 lines, advertises `web4.io/trust/update` at `:10`
as a working tool, gives install (`:28-41`) and test (`:43-46`) instructions, and contains
**zero** deprecation text — the artifact an installer actually reads carries no disclosure at all.
`mcp-server/mcp.json` ships an installable stanza whose path is hardcoded to
`/home/dp/ai-workspace/web4/mcp-server/server.py` (a personal config, not a distributable — which
is part of why severity is not HIGH).

### Severity: **MED**

**Not HIGH** — zero importers, zero CI, the shipped `mcp.json` is a personal config, and the
failure is **loud, not silent**: it raises before `json.dump`, returns JSON-RPC `-32603`, corrupts
no data and writes nothing. Fully reversible, zero blast radius.

**Not LOW** — "a deprecated prototype is broken" would be LOW and arguably immaterial. The
charged proposition is that a **tier-1 canonical-terminology remediation asserted a completed
correction that is false in the same file**, at the one site its own mitigation does not cover,
behind a gate that had been permanently closed 81 days earlier — and that an audit ruling cites
that header. Terminology canonicalisation is a CLAUDE.md hard constraint; a sweep that reports
itself complete when it is not is the failure mode that lets the next sweep skip the file.

**Routing:** owner of `mcp-server/`. This track does **not** self-apply (cf. C374-N4). The
minimal honest fix is either (a) complete the rename at `:631-632` and add one assertion to
`test_mcp.py`, or (b) retract the `:25-27` sentence. **(b) alone is sufficient to close the
charge**; (a) alone is not, because the note would still over-claim for any future survivor.

---

## §C — Negatives (published so C424 does not re-run them)

**N-1. C370-N1's other half: does F8 (§4.1↔§7.4 header reconciliation) have an SDK locus?**
**Answer: yes, and it is NEGATIVE for the single-hop case only.**

F8 was charged **HIGH** on 2026-05-15 (`mcp-protocol-internal-consistency-2026-05-15.md:52`,
`:175`) — "§7.4 introduces `sender_society`/`responding_society` and `agency_chain` (array)
without stating their relationship to §4.1's `society` (single) and `proof_of_agency` (object)."
Unlike F3/F4 (whose SUPERSEDED verdicts C370 showed were scoped to a *spec* locus while the SDK
shipped the rejected shape for 89 d), **F8's remediation did reach the spec**: the "Relationship
to §4.1" block begins at `:472`, with reconciliation bullets `:477-487`.

SDK side: `CrossSocietyContext` (`mcp.py:715`) documents itself as extending the intra-society
`Web4Context` (`:268`), carries `sender_society`/`responding_society`, and emits
`proof_of_agency` (`to_dict`, `:773-774`). `\bagency_chain\b` has **0** implementation
occurrences corpus-wide (3 total, all in the spec: `:452`, `:484`, `:487`).

**Verdict — NEGATIVE for the single-hop case, and no second F3/F4.** `:486-487` declares a
single-element `agency_chain` wire-equivalent to one §4.1 `proof_of_agency`, which is exactly
what the SDK emits; so the SDK is licensed, not contradicted.

**Two asymmetries disposed of rather than ignored** (a bare "0 occurrences" would be
*ambiguous* — zero is also what an unimplemented normative field looks like, **v50**):
- §7.4 gives `sender_society` an explicit **recipient MUST** (`:481-483`: "MUST treat … as the
  same logical field … MUST NOT require both"). It gives `agency_chain`↔`proof_of_agency` **no
  recipient MUST** — only the descriptive "wire-equivalent" at `:486-487`. The asymmetry is real
  but licenses the SDK rather than indicting it.
- `proof_of_agency: Optional[ProofOfAgency]` is a **single** object; the SDK structurally cannot
  express the multi-hop ordered chain that is the list form's purpose.

**The multi-hop half is NOT new here — it folds into standing `B-AGENCY / L1`**, which is
**STILL-OPEN**, explicitly **"mcp-owned"**, and already names `agency_chain` by name
(`C126:60`; carried at `C86:107-112`, `C158:44`, `C196:45`/`:105`, `C234:55`/`:115`).
Declaring that denominator is the point (**v51**): a negative on F8's SDK locus that never
mentioned B-AGENCY would have had an undeclared one.

**N-2.** `mcp-servers/` scores **0/0/0** on C188's three wire-layer predicates ⇒ C188's synthesis
holds on new evidence (§B, with the signing nuance stated).

**N-3.** C344-N1 unremediated; C77 note intact; the outward draft's two half-migrated sites
unchanged (§A guards 2–3).

**N-4 (INFO, not charged).** `mcp-servers/web4-trust/server.ts:636` fails `tsc` with **TS2352**
(`await updateTrust(args as OutcomeUpdate)`; `Record<string, unknown> | undefined` does not
overlap `OutcomeUpdate`), so `npm run build` — the command `mcp-servers/README.md:20` instructs —
exits **2**. `web4-identity` and `web4-economy` typecheck clean.
**Environment, stated because the cell is otherwise not re-executable:** the repo ships no
`node_modules` and no lockfiles (`git ls-files mcp-servers/` = 10 files, all sources), so in a
clean worktree the command is `tsc: not found`. This cell was produced by copying each package to
a tmpdir, running `npm install` (99 packages, `@modelcontextprotocol/sdk` ^1.0.0 resolved live on
2026-08-14), then `npx tsc --noEmit`. Not charged as a finding: `tsconfig.json` sets no
`noEmitOnError`, so tsc still emits `dist/server.js` and the server runs — this is a broken build
**gate**, not a broken runtime, in a tree no CI touches.

---

## §D — Deferral row, pre-registered for C424 (do NOT backfill)

1. **Re-run the N1 executable check.** Command: load `mcp-server/server.py` with `HOME` in a
   tmpdir and call `_tool_trust_update({'entity_id':'x','role':'default','outcome':'success'})`.
   Expected if unfixed: `KeyError: 'reliability'` at `:631`. If it now returns a dict, check
   **which** fix was applied — if `:25-27` was retracted the charge is closed; if `:631-632` was
   renamed, verify `test_mcp.py` gained an assertion, or guard 3 is still open.
2. **The `mcp-servers/` tree has now been entered once, for C188's three predicates only.**
   Its 22 tools have never been read against `mcp-protocol.md`'s §12 MUSTs. That is the next
   unasked question here — but note MUST #2 ("all interactions MUST include Web4 context
   headers") is answered corpus-wide by C188's synthesis, so scope it to MUSTs 1/3/4/5/6.
3. **`test_mcp.py`'s never-firing cleanup is a general instrument question**, not a local bug:
   how many other test harnesses in the corpus clean up by substring-matching a filename their
   producer hashes? Matcher to run: `grep -rn 'in f.name' --include=*.py`.
4. **Do NOT re-charge** `mcp-server/server.py`'s FALSE-mirror status (C188, re-affirmed here), the
   `mcp-servers/` 0/0/0 predicates, or F8's single-hop case.

## §E — Guards carried to C424

- Target has been byte-frozen **4 consecutive deltas / 32 d** at blob `4491c1bb`. Check the blob
  first; if unchanged, collapse §A and spend the pass on the residue.
- **CADENCE, datapoint 17.** Third consecutive pass across the fleet where a frozen target
  yielded from the **periphery, not the target** (C342, C382, now C384). All five C344 guards
  discharged with nothing charged against the spec; the entire yield came from the v36 residue.
  The spec itself is now a low-yield surface — recommend C424 budget the residue first
  (operator's call).
- Baselines unchanged: target `4491c1bb`; `mcp.py` `b6c243c2`; `mcp_server.py` `759eaefa`;
  `MCP_ENTITY_SPECIFICATION.md` `f3d2613d`; vectors `9b002074`; `mcp.rs` `b05845bc`;
  `r7-action-jsonld.schema.json` `766611ef`. New: `mcp-server/server.py` `4e195bdf`;
  `mcp-server/test_mcp.py` `f971230f`; `mcp-servers/*` `58db87e3`/`76bcafe8`.

---

## §own-error — what this pass got wrong, and the carry it produces

**1. The novelty claim was overstated, by a matcher too narrow — one pass after v56 was written
to prevent exactly this.** The scope proposal asserted *"no audit doc in the corpus has ever cited
a line number inside `server.py`"*, on the matcher `grep -ohE "server\.py:[0-9]+"` = 0 hits.
**That is false.** `C188:89` cites the locus as `` header `:20-27` `` — the line range **detached
from the filename**, in a table row whose subject column holds the path. A matcher keyed to
`<basename>:<line>` adjacency cannot see it. Policy review caught it; the correct per-locus form
is: **cited loci = {`:20-27`}; charged loci {`:595`, `:631-632`} uncited.** Novelty holds
per-locus, and the finding is *stronger* for it — the one prior citation is what makes the note
load-bearing in the audit record. (Confirming **v41**: if correcting your own cite strengthens
your argument, the original was guessed.)

**2. The defect class was filed as net-new when it is established prior art with a ratified fix
shape.** `remediation-incompleteness` was born at C36 and `C166:90` counts 8 prior instances;
`C64:18` is a near-exact structural precedent (a rename whose *provenance note over-claims a full
match*). Cause: the novelty sweep searched this pass's paraphrase, not the domain's word — the
failure **v44** names. The precedent brought the `C60:197` sibling-site sweep, which materially
improved the finding by bounding it to two lines.

**3. Four measurement cells were wrong on first write** and were corrected before publication:
`GOVERNANCE_AVAILABLE` "15 of 16" → **17 mentions / 15 guards**; TypeScript LOC 2,571 → **2,493**
(and two SDK anchors were off — `Web4Context` `:274`→**`:268`**, mine, a *field* line; and
`CrossSocietyContext` `:714`→**`:715`**, **the reviewer's**, the `@dataclass` decorator rather
than the `class` statement. **v52 holds: verify the reviewer's corrections too** — this is the
third pass in a row where a reviewer-supplied anchor needed its own check)
(the first number included `README.md`); the R7 predicate needed the precise `\bR7\b` matcher plus
the "they do sign, just not R7 envelopes" nuance; and the build-check cell was not re-executable
as written (no `node_modules` in a clean worktree) until its environment was published.

**4. The scope claim "cannot succeed for ANY entity" was refuted by this pass's own control arm**
and has been narrowed to "any entity lacking a pre-sweep record." A control that contradicts the
headline is the control doing its job (**v50**).

**No reviewer correction was rejected.** All were independently re-verified before acceptance:
`c98c6aee`'s date and ancestry, the empty `claude-code-plugin/`, the never-firing cleanup and the
surviving `31a59a5178196d06.json`, the C36→C84 family loci, `C60:197`, `C64:18`, and B-AGENCY's
STILL-OPEN rows.

### Method carry v57 — **a cited locus can be detached from its filename**

v56 said *novelty is per-LOCUS, not per-artifact*, and prescribed enumerating cited line numbers
with `git grep -ohE "<basename>:[0-9]+"`. **That matcher has a blind spot, and it is the shape
audit tables are actually written in.** A finding table's *subject* column holds the path and its
*evidence* column holds a bare `` `:20-27` ``; the adjacency the matcher requires never occurs.
So the instrument built to prove per-locus novelty systematically under-reports citations in
precisely the documents most likely to hold them.

**Corrected procedure:** enumerate cited loci in two passes — (a) `<basename>:[0-9]+` for prose
citations, then (b) grep the **artifact path** and read every hit's surrounding line for a bare
`` `:N` `` or `` `:N-M` `` token. The union is the cited-locus set. And when a single prior
citation *does* turn up, do not treat it as a tombstone: ask **which clause of the cited range the
prior pass relied on**. Here the prior pass quoted the true half of an 8-line note and the false
half went untested for 109 days — the citation was not the finding's refutation, it was its
materiality.

Corollary, from the fourth guard failure: **a consumer keyed to a naming convention its producer
does not use is a defect class, not an incident.** It appeared twice in one file — `:631`
(sweep renamed the producer, not the consumer) and `test_mcp.py:153` (cleanup substring-matches a
filename the code hashes). When you find one, sweep the file for the other.
