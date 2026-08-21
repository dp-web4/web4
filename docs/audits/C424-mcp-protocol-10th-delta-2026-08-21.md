# C424 — `mcp-protocol.md`, 10th delta audit

**Date**: 2026-08-21 · **Slot**: `web4-20260821-000000` · **Target**:
`web4-standard/core-spec/mcp-protocol.md` · **Lineage member**: 14th
(13 prior under the inclusive rule `^(C[0-9]+-)?mcp-protocol`) · **Mutation**: **ZERO**

> **Enumeration rule (stated, per standing policy).** Inclusive matcher
> `^(C[0-9]+-)?mcp-protocol` over `docs/audits/` returns **13** files. **mcp has TWO
> non-C-numbered originals** — `mcp-protocol-internal-consistency-2026-05-15.md` **and**
> `mcp-protocol-sdk-alignment-2026-05-15.md` — plus one non-delta member
> (`C117-…-remediation-…`). C384 flagged this so C424 would not "discover" the second as a gap.
> It did not. **12 prior *audit* passes**, this is the 10th *delta*.

---

## §A — Freeze

| Cell | Value | Command |
|---|---|---|
| Target blob | `4491c1bb7f603808abfbaa01613e12b36f9c3192` | `git rev-parse HEAD:web4-standard/core-spec/mcp-protocol.md` |
| Last mover | `3e765345` (2026-07-13, §7.8 insert) | `git log -1 -- <target>` |
| Frozen | **39 days**, 5th consecutive frozen delta | — |
| Length | 1020 L | `wc -l` |
| Window | `385eb043..HEAD` = **27** commits, **1** in `web4-standard/` | `git log --oneline 385eb043..HEAD [-- web4-standard/]` |

**All 8 mirrors unmoved** at their C384 baselines: `mcp.py` `b6c243c2` · `mcp_server.py`
`759eaefa` · `MCP_ENTITY_SPECIFICATION.md` `f3d2613d` · vectors `9b002074` · `mcp.rs` `b05845bc`
· `r7-action-jsonld.schema.json` `766611ef` · `mcp-server/server.py` `4e195bdf` ·
`mcp-server/test_mcp.py` `f971230f`.

§A collapses to the blob table (C344/C346/C370 precedent). **The yield is peripheral, as C384's
cadence datapoint 17 predicted.**

### A.1 — One in-window artifact does bear on the target (INFO)

`web4-standard/core-spec/interface-planes.md` was **created in-window** (`2462881f`, 2026-08-19,
#727) and re-scopes the target's subject matter: *"Before this specification, canon described
interfaces with a single term: MCP as the I/O membrane… That term names the transport"* (`:12-13`),
with a whole section **§7 "Relationship to the membrane"** (`:162`). Its §9 "Relationship to other
specifications" names six sibling specs and points the reader at **`MCP_ENTITY_SPECIFICATION.md`**
as "the membrane" (`:194`).

`grep -n 'mcp-protocol' web4-standard/core-spec/interface-planes.md` → **empty**. A two-day-old
normative `core-spec/` file whose §7 is explicitly about MCP never names the standard's 1020-line
MCP *protocol* spec, which lives in the same directory. **This corroborates the standing
B-D1 SSOT-inversion carry and is reported, not self-resolved** (B-D1 is operator-unanswered).

---

## §B — The four-row deferral C384 pre-registered for C424

All four discharged. Rows 1 and 3 first, because they are short.

### B.1 — Deferral row 1: **C384-N1 is UNREMEDIATED. Neither fix landed.**

C384 pre-registered the fork: *"if it returns a dict, identify WHICH fix was applied (`:25-27`
retracted ⇒ closed; `:631-632` renamed ⇒ check `test_mcp.py` gained an assertion)."*

**Neither branch was taken.**

- `mcp-server/server.py:25-27` still reads *"Internal trust dimension names **have been corrected**
  to the canonical 3-root form (T3: talent/training/temperament; V3: valuation/veracity/validity)."*
- `mcp-server/server.py:631-632` still reads `t3["reliability"]` / `t3["consistency"]`.
- `grep -c assert mcp-server/test_mcp.py` = **0** (exit 1). **C384 guard 3 remains open.**

C384's headline — *the false assertion at `:25-27`*, not the `KeyError` — **stands unremediated at
9 days.** Not re-charged; **reported as a live carry.**

### B.2 — Deferral row 3: the never-firing-cleanup class is a corpus-wide **SINGLETON**

```
grep -rn 'in f\.name' --include=*.py .        # excluding /target/
→ mcp-server/test_mcp.py:154            (1 hit)
```

**Denominator: 1 of 1** — the only site is the one C384 already charged. This is an **instance,
not a class**. **Row RETIRED. Nothing charged.** (v40 — publish the denominator; v42 — a deflation
retires the row.) Do not re-run this sweep.

### B.3 — Deferral row 4: honoured

The FALSE-mirror status, the 0/0/0 wire predicates and F8's single-hop case are **not re-charged,
not re-narrated, and not re-opened.** They appear below only where a *new* measurement changes what
they are evidence *for*.

### B.4 — Deferral row 2 is the pass. It is answered in §C and §D.

---

## §C — **C424-N1 (LOW-MED → `mcp-servers/` owner + standard/conformance track).** §12 MUST 1 reads on the server, and 3 of 3 of the corpus's TypeScript Web4 MCP servers hold no LCT — including the one that mints LCTs for everyone else.

### C.1 — The clause and its grammatical subject

`mcp-protocol.md` §12, MUST #1 (`:953`; §12 heading `:945`):

> **1. All MCP servers MUST have valid LCTs**

The grammatical subject is **the server**, not its payloads (v71 — the line is the subject of the
sentence, not your evidence's strength). This audit's first draft tested the *shape of the LCTs the
tools emit* and had to be re-predicated in policy review. The correct test needs no schema and no
comparator.

### C.2 — Measured

Every server-construction site in the tree, read verbatim:

| Server | ctor site | What it carries |
|---|---|---|
| `mcp-servers/web4-identity/server.ts` | `:394-397` | `new Server({ name: "web4-identity", version: "0.1.0" }, …)` |
| `mcp-servers/web4-trust/server.ts` | `:442-445` | `new Server({ name: "web4-trust", version: "0.1.0" }, …)` |
| `mcp-servers/web4-economy/server.ts` | `:451-454` | `new Server({ name: "web4-economy", version: "0.1.0" }, …)` |

A bare name-and-version string. **No LCT, no key, no binding. 3 of 3.**

And the absence is not merely structural — it is lexical:

```
grep -ic 'lct' mcp-servers/web4-trust/server.ts      → 0
grep -ic 'lct' mcp-servers/web4-economy/server.ts    → 0
grep -ic 'lct' mcp-servers/web4-identity/server.ts   → 152
```

**Two of the three contain the string `lct` zero times in any casing.** They have no LCT, valid or
otherwise, and nothing in them refers to one.

**The third is the sharp case.** `web4-identity` is the corpus's only LCT-*minting* MCP tool — its
eight tools are `create`, `verify`, `bind`, `revoke`, `delegate`, `witness`, `chain`, `query`. It
mints, binds, witnesses and revokes LCTs for other entities across 152 references, **while holding
none itself.** An identity provider with no identity.

### C.3 — Why these artifacts are in scope for §12 (the antecedent is reachable — v54)

They are MCP servers by constructor evidence (`@modelcontextprotocol/sdk`), they are named
`web4-*`, and `mcp-servers/README.md:1-3` declares them **"Web4 MCP Servers … Modular Model Context
Protocol servers exposing Web4 trust infrastructure."** The README ships real installation
instructions writing them into a user's `~/.claude/settings.json` (`:27-46`). The antecedent "All
MCP servers" is squarely reachable.

### C.4 — Two refutations TESTED and SUSTAINED. They bound the charge; both are published.

- **R1 — "in-memory demo, disclosed."** **SUSTAINED for what it covers.** All state is six
  process-local `Map`s (`identity:77-78`, `trust:86-87`, `economy:76,78`); **zero** filesystem or
  database imports across all three (`grep '^import'` → only `@modelcontextprotocol/sdk` and
  `crypto`). But it **is disclosed at the point of use**: `// In-Memory State (would be backed by
  persistent storage in production)`. That is the polarity the corpus's disclosed-phasing defense
  protects — *"this does not work yet"*, not *"this has been corrected"* (v57). **Volatility is
  therefore NOT charged.** The disclosure covers *storage*; it says nothing about conformance, and
  no file in the tree discloses that these are not standard LCTs.
- **R2 — "the Python server has the same defect, so it's a corpus idiom."** **SUSTAINED, and it
  removes the Python server from the charge.** `mcp-server/server.py:20-27` discloses itself as
  superseded — *"predates the canonical SDK implementation… **Prefer the SDK MCP server for new
  integrations.**"* Correct polarity. The Python minter is **evidence, not the charge.**

**The charge lands on the TypeScript tree only.**

### C.5 — Severity: **LOW-MED**, and the reasoning is published

- **Not MED**: `git grep -c 'mcp-servers' -- web4-standard/` = **zero**. The standard never names
  this tree, so it is not a *declared* conformance target.
- **Not LOW**: it is the corpus's largest advertised Web4 MCP surface (22 of 55 advertised tools),
  its README declares it Web4 and ships `~/.claude/settings.json` install instructions, and the
  standard's first and most basic MUST fails on all three members.

### C.6 — MUSTs 5 and 6 are **VACUOUS, not violated** — and publishing the vacuity IS the finding

Across all three servers: `agency|proof_of_agency` = **0/0/0**, `\bR7\b` = **0/0/0**. MUST 5
(*"Agency proofs MUST be validated **when present**"*) and MUST 6 (*"**R7 actions** MUST be
witnessed"*) both carry explicit antecedents with **no referent here**. A MUST whose antecedent is
unreachable is not violated. **Severity capped there** (v54/v74) — and the measured vacuity is the
reportable fact, not a silent pass.

### C.7 — MUSTs 3 and 4: three disjoint silos

| server | `lct` | `trust` | `atp\|ATP` | `witness` | `\bR7\b` |
|---|---|---|---|---|---|
| `web4-identity` | **152** | 0 | 0 | **42** | 0 |
| `web4-trust` | 0 | **47** | 0 | 0 | 0 |
| `web4-economy` | 0 | 9 | **55** | 0 | 0 |

The canonical equation is `Web4 = MCP + RDF + LCT + T3/V3*MRH + ATP/ADP`. Each server implements
**exactly one term and zero of the others**; no tool crosses a boundary. MUST 3 (*"Trust evaluation
MUST precede resource access"*) and MUST 4 (*"ATP metering MUST be enforced"*) are therefore
**partitioned by silo, not enforced across the surface** — `web4-economy` charges and discharges ATP
with 9 incidental `trust` references and no trust gate; `web4-identity` mints identity with zero.

**§12's six MUSTs, measured against this tree: 1 measurably failed (MUST 1) · 1 measured 0
corpus-wide by C188 (MUST 2, not re-charged) · 2 vacuous (5, 6) · 2 partitioned by silo (3, 4).**

---

## §D — **C424-N2 (LOW → `mcp-servers/` + `mcp-server/` owners).** Two shipped tools in the same `web4.io/` namespace both mint an LCT, and their emitted objects share **zero field names**.

### D.1 — Executed, not read

All three LCT-minting paths in the corpus were **executed** and their output validated with
`jsonschema.Draft202012Validator`. Harness: the identity server's minting path lifted verbatim
(`server.ts:84-96,114-131,132-160` — the MCP stdio transport is omitted because `createIdentity()`
does not touch it); the Python tool called directly as `_tool_lct_create` under a redirected
`HOME`; the SDK via `web4.generate.generate("LinkedContextToken")`.

| MCP tool that mints an LCT | `lct-jsonld.schema.json` | `lct.schema.json` | props |
|---|---|---|---|
| `web4_generate('LinkedContextToken')` — SDK MCP server | **0** | 7 | 9/11 |
| `web4.io/identity/create` — TS, `mcp-servers/web4-identity` | **9** | 7 | 1/11 |
| `web4.io/lct/create` — Py, `mcp-server/server.py` | **9** | 6 | 2/11 |

> **Comparator discipline — the raw column is NOT the finding.** `lct.schema.json`'s normativity is
> **standing carry C288-N1** (MEDIUM, **OPEN**, operator DESIGN-Q *"which published schema is
> normative?"*, explicit *"Do NOT self-apply"*). `C328:247` pre-committed the adjudication rule *in
> its own policy review, before the run*: **"a 0/10 against the raw schema is C288-N1 reach, not
> net-new; only a failure against `lct-jsonld.schema.json` would be candidate net-new."** This pass
> honours that rule. Note also that the raw column is a **measured non-discrimination** — 3 of 3
> fail it, including the canonical SDK — so it is not a control (v74). **Only `lct-jsonld`
> discriminates: SDK 0 / TS 9 / Py 9.** The raw column is published as **routed evidence to
> C288-N1**, nothing more.
>
> **TS raw = 7, and the rule matters** (v59). Fed the *most favourable* input — a spec-form
> `did:web4:key:…` subject — it is 6. Fed a plausible naive subject it is **7**, and the tool
> performs **zero** validation of `subject` (0 hits for `test(`/`match(`/regex/throw across the
> file), so **7 is the realistic figure**. The first draft of this audit published 6, having
> silently handed the tool the one input that flatters it.

### D.2 — The control answers the question asked (v68)

`web4_generate('LinkedContextToken')` validates at **0 errors** against the discriminating schema.
So non-conformance is **not** the corpus norm for MCP LCT-minting: **1 of 3 conforms perfectly**.
By the sibling-enforcement ratio (v46), 1-of-3 is a defect, not an idiom.

### D.3 — The finding: zero shared field **names**

```
TS  web4.io/identity/create → {id, type, subject, issuer, issuedAt, publicKey, revoked, signature}
Py  web4.io/lct/create      → {lct_id, binding, label, created_at, public_key}
intersection                → ∅
```

Both tools are advertised in the **same `web4.io/` tool namespace**. Both claim to mint an LCT. An
agent with both installed sees `web4.io/identity/create` and `web4.io/lct/create` and receives two
objects with no field name in common.

**Stated precisely, because the bigger version is the wrong one (v72).** They do **not** "agree on
nothing." Four of Python's five fields have plausible TypeScript counterparts under different
naming conventions — `id`/`lct_id`, `publicKey`/`public_key`, `issuedAt`/`created_at`, and
`type` (`root|device|software|session|delegated`) / `binding` (which **defaults to `"software"`**,
literally one of TS's `type` values). Only `label` is Python-unique. **The measured claim is: they
share zero field names, and the only overlap is semantic and unserialized.** The divergence is at
the **naming-contract** level, not a feature gap — which is the sharper and the smaller claim.

### D.4 — This is not C288-N1 reach (adjudicated in policy review)

C288-N1's three recorded arms (schema-vs-spec, schema-vs-sibling-schema, schema-vs-corpus) each
have `lct.schema.json` as one relatum. **This observation has neither schema as a relatum — it
survives deleting both schemas from the repo.** Different subject, different falsifier, and
decisively **different remedy**: answering *"which schema is normative?"* would not fix it, because
both minters fail *both* schemas. **Chargeable at this locus.**

### D.5 — Shape precedent, cited (v44/v56)

The instrument is **identical to `C418-N1`** (PR #742, filed **2026-08-20 — one day before this
pass, by this same track**): *four artifacts each declare Web4's IANA Considerations, union 8,
intersection ∅*. This finding is novel **per-LOCUS**, not per-shape, and it carries C418-N1's
ratified fix shape. C418's *"equal cardinality merges labels"* hazard **does not apply** — the
cardinalities here are 9 and 5, unequal.

### D.6 — The standard's own tool-naming rule: measured, and NOT charged

`mcp-protocol.md:593` (§7.7.3) is the standard's **only** tool-naming statement:

> The tool name SHOULD be `web4_rate_propose`, `web4_rate_counter`, `web4_rate_accept`,
> `web4_rate_reject` for spec-conformance, though societies **MAY** use society-specific tool names.

**Modality checked before treating the locus as normative (v71).** It is a SHOULD with an explicit
MAY escape, and it is **scoped to rate negotiation only** — it does not establish a corpus-wide
convention. The four named tools occur in exactly **two** files repo-wide (the spec itself and
`forum/kimi_2_6_web4_hestia.md`, an external model's discussion): **zero implementations.** §7.7 is
WIP-fenced, which C188 already recorded, so this is **disclosed phasing of the correct polarity**.

**NOT CHARGED.** Recorded because the negative is what makes the naming census interpretable: the
corpus ships **three mutually incompatible tool-naming schemes** (`web4.io/` ×46, `web4_*` ×8,
bare ×1) and the standard has an opinion about exactly four tool names, none of which ship.

---

## §E — **C424-N3 (INFO, instrument).** The lineage's mirror ladder is a citation query, and it has never enumerated the corpus's largest MCP surface

### E.1 — Swept backwards (v64)

C188 §B.2 built the ladder that every later pass re-derives, by asking *who implements
`mcp-protocol.md`*. That is a **citation-graph query, and it cannot return an orphan** (v47). Run
**backwards** instead — *what in this corpus **is** an MCP server*, by constructor evidence
(`@modelcontextprotocol/sdk`, `FastMCP`, JSON-RPC tool dispatch):

| Artifact | Language | Tools | On C188's ladder? |
|---|---|---|---|
| `mcp-servers/web4-identity/server.ts` | TS | 8 | **NO** |
| `mcp-servers/web4-trust/server.ts` | TS | 6 | **NO** |
| `mcp-servers/web4-economy/server.ts` | TS | 8 | **NO** |
| `web4-standard/implementation/sdk/web4/mcp_server.py` | Py | 8 | yes (FALSE) |
| `mcp-server/server.py` | Py | 24 | yes (FALSE) |
| `hub/hub-daemon/src/mcp.rs` | Rust | 1 advertised / 7 distinct | yes (FALSE) |

C188 listed **five** candidates, of which only **three were actually servers** (`mcp.py` is a types
module; `web4-trust-core::EntityType::Mcp` is an ID-prefix classifier, correctly excluded at
C176/C178). It missed **all three TypeScript servers**.

### E.2 — The denominator is a domain, so both are published (v40)

|Rule|Denominator|Never enumerated|
|---|---|---|
|Advertised MCP tools|22 + 8 + 24 + **1** = **55**|**22 / 55 = 40.0%**|
|Distinct tools incl. unadvertised|22 + 8 + 24 + **7** = **61**|**22 / 61 = 36.1%**|

The hub splits the two: `list_tools()` (`hub/hub-daemon/src/mcp.rs:213-222`) advertises **exactly
one** tool (`query_hub`); the other seven are **deliberately unadvertised** — *"Write tools
(add_member/assign_role/record_event/declare_skill) sign as the Sovereign and are served ONLY on the
loopback operator plane — not advertised here (they 404 on the public listener by design)."* That
is disclosed design, not a gap, and it is why the figure must be published as a pair rather than a
winner. **An earlier draft of this audit omitted the hub entirely and published 40.7% against a
denominator of 54 — inflating the headline by dropping precisely the *enumerated complement*
(C304 = 11 `hub` / 9 `mcp.rs` hits; C344 = 7/5; C188 = 2). Caught in policy review.**

### E.3 — How long, and how invisible

- `mcp-servers/` created **`76bcafe8`, 2026-02-08** — **194 days**.
- Of the **12 prior mcp-lineage audit docs, 11 contain the string `mcp-servers` zero times.** Only
  C384 names it (11×), and only in the v36 residue — C384 itself records the bound at `:373`:
  *"The `mcp-servers/` tree has now been entered once, for C188's three predicates only."*
- Corpus-wide, exactly **two** audit documents have ever named it: C302 (2×, another lineage) and
  C384 (11×).

**The blind spot is specific: the TypeScript tree, not "MCP servers generally."** The lineage has
enumerated the hub repeatedly. What it could not see was the tree that never cites the spec —
because a sweep keyed on the target's filename is blind to an artifact that does not mention it.

---

## §F — Negatives recorded (so the next pass does not re-run them)

1. **`in f.name` cleanup class** — singleton, 1 of 1. Retired.
2. **Volatility of the TS servers** — disclosed at the point of use, correct polarity. Not charged.
3. **The Python minter** — self-disclosed as superseded. Evidence, not charge.
4. **§7.7.3 tool naming** — SHOULD + MAY escape, rate-scoped, WIP-fenced. Not charged.
5. **The raw-schema column** — measured non-discrimination (3 of 3 fail). Not a control. Routed.
6. **C288-N1's `birth_certificate.context` arm** — see §G. **A rediscovery, withdrawn.**
7. Not re-run, per C384 deferral row 4: the FALSE-mirror status, the 0/0/0 wire predicates, F8's
   single-hop case, the adjudicated C188 exclusions.

---

## §G — One row WITHDRAWN by this pass, against itself

This audit's working draft carried an observation that the corpus's three `should_succeed=True` LCT
interop vectors (`web4-standard/test-vectors/lct/interop-*.json`) each fail `lct.schema.json` at
`/birth_certificate` with `'context' is a required property`, plus `interop-human-full` at
`/binding/hardware_anchor`.

**It is a rediscovery of a recorded kill, and it is withdrawn.** `C328:254` row 9 lists
`birth_certificate` / `'context' is a required property` **verbatim** as *"C288-N1's known
pre-#83-rename arm"*; `C288:198` names `650518d9` (#83) — a rename of `context` → `birth_context`
across nine artifacts that missed the schema — as root cause; `hardware_anchor` is C288-N1's second
documented arm; and `C302 §E.1` already recorded the whole set as **"a kill, not a finding."**

Reported here as a **confirmed carry** — C288-N1 remains live, now with third-party corroboration —
and **named as an arm on C288-N1**, not routed vaguely to "the lct lineage."

**One ledger note kept, because the reasoning is reusable.** The draft first wrote *"no harness runs
them."* Running the harnesses instead of grepping for them narrowed it: `validate_context_refs.py`
**does** `rglob("*.json")` over those files — it just checks `@context` refs only — and the sole
by-name loader is **archived** (`archive/reference-implementations/cross_language_interop.py`). The
defensible claim was the narrow one: *no **live schema** harness validates them.* A filename grep
cannot see a directory-walking loader (v46); an unqualified negative is a claim about your
instrument, not the world (v73).

---

## §H — Deferral row, pre-registered for **C464** (the next mcp delta). Do NOT backfill.

1. **Re-run the C384-N1 fork** (unchanged at 9 d): `:25-27` retracted ⇒ closed; `:631-632` renamed
   ⇒ check whether `test_mcp.py` gained an assertion. Currently **neither**, `grep -c assert` = 0.
   **A third consecutive no-motion should be escalated as a stall, not re-asked.**
2. **C424-N1 and C424-N2 own the tree now.** Re-measure the three ctor sites and the
   `lct` = 0/0/152 census. Do **not** re-derive the ladder from citations — start from §E.1's
   constructor-evidence table.
3. **`interface-planes.md` (§A.1)** — if a later revision gains a `mcp-protocol.md` citation, that
   closes the A.1 observation; if `MCP_ENTITY_SPECIFICATION.md` remains the sole membrane pointer,
   it is a second datapoint for B-D1. **Report either way; do not self-resolve** (B-D1 is
   operator-unanswered).
4. **Do NOT re-run**: the `in f.name` sweep (singleton, retired); the raw-schema column as a control
   (non-discriminating); §7.7.3 naming (disclosed phasing); the C188 exclusions.
5. **If a fix lands on `mcp-servers/`**, check the README's tool table (`8 | 6 | 8`) moved with it —
   that table is the only place the tool count is asserted, and this pass's first count of "25" came
   from a matcher that swept ListResources entries alongside ListTools. **22 is correct; the three
   extras are resources** (`LCT Identity Document`, `Entity Trust Profile`, `Entity Economy Profile`).

---

## §I — Verdict

**10th delta SERVED. Target byte-frozen (5th consecutive), ZERO mutation, 1 new file.**

**All four C384 deferral rows discharged** — row 1 answered (neither fork taken), row 3 answered and
**retired** as a singleton, row 4 honoured, row 2 answered and it carried the pass.

**Two net-new findings**, both peripheral, neither against the spec prose: **C424-N1 (LOW-MED)** —
§12 MUST 1 reads on the server and 3 of 3 TypeScript Web4 MCP servers hold no LCT, the minting one
included; **C424-N2 (LOW)** — two shipped `web4.io/` tools both mint an LCT and share zero field
names. **One INFO instrument finding (C424-N3)** — the mirror ladder is a citation query and has
never enumerated 22 of 55 advertised tools across 194 days and 12 passes. **One INFO in-window
observation (§A.1).** **One carry confirmed unremediated (C384-N1).** **One row withdrawn against
itself (§G).** **Six negatives recorded** so the next pass does not re-run them.

**Two own cells corrected by the post-write re-run, published not quietly fixed** (C328's
discipline): MUST #1 was cited at `:951` — that line is `govern in full.`; the clause is at **`:953`**
(the §12 preamble shifted it by two). And the README's install block was cited at `:22-44`; measured,
it is **`:27-46`**. Every other cited locus in this document was re-resolved against HEAD and holds —
path tokens are their own class, and that includes the ones a reviewer hands you.

**Four load-bearing cells were falsified in policy review before anything was written** — the
denominator, the comparator, the clause's grammatical subject, and a rediscovery sold as an
observation — and **one reviewer cell was corrected back** (the hub's advertised tool count).
Every one is published above rather than quietly fixed.

**Rotation advances to `atp-adp-cycle.md` = C426.**
