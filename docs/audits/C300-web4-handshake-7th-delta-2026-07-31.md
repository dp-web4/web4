# C300 — `protocols/web4-handshake.md`, 7th delta

**Date**: 2026-07-31
**Target**: `web4-standard/protocols/web4-handshake.md` (269 lines; blob `75aa965e`; `Last-Updated: 2026-06-29`)
**Lineage**: C28 first-pass (#264/#265 `8b3bbac3`) → C72 1st delta (#360 `248a6c3e`) → C73 remediation (#362 `0179c470`) → C112 2nd delta (#401) → C113 remediation (#404 `57caa2e1`) → C144 3rd (#…) → C184 4th → C222 5th → C260 6th → **C300 (7th delta)**
**Method**: §A prior-fix hold vs the byte-frozen target · §B corpus delta since the C260 snapshot · **§B′ mirror set re-derived inward, not re-read** (method carry v8) with every gate publishing the paths it searched (v9) · §C internal consistency + carry ledger
**Mutation**: **ZERO.** No spec, SDK, vector, Rust, or registry file was edited. Audit-only.

---

## Headline

The target is byte-frozen for 32 days and §A/§C are clean for the 5th consecutive delta. The
findings are not in the target's bytes — they are in **the instrument that has been certifying
it clean**.

1. **The handshake lineage's carry ledger emptied at C144.** C112 published an 11-row §C
   routing table. **All 8 labelled carry rows (D1 D2 D3 D4 X1 X2 X3 X4) drop to zero at C144 and
   remain zero through C184, C222 and C260** — four consecutive passes, two of the dropped rows
   HIGH. Each of those four passes published "0 net-new / spec-side clean," and the streak was
   read forward as evidence of health. All four D-series items **re-verify as still true at live
   HEAD** in this pass.

2. **C-H1's split is 4-way at live HEAD, not 2-way.** C28 framed the canonical-handshake
   design-Q as `protocols/web4-handshake.md` (3-message, signature) vs `core-spec/core-protocol.md`
   (4-message, MAC). Two further handshake specifications live inside `web4-standard/` and have
   been read by **0 of the 7 lineage audit documents** — both in `submission/`, the outward-facing
   IETF tree, neither marked superseded.

3. **The mirror gate was pointed at two trees that contain no handshake at all.** The
   candidate-generation grep returns **`web4-core/` = 0 hits and `hub/` = 0 hits**, while the four
   highest-hit artifacts in the corpus all sit in `web4-standard/` itself. Five passes ran the
   gate over `web4-core/` and published the resulting zero as a property of the handshake.

**This pass's own flagship was killed by the snapshot guard before it was written.** The
3-message-vs-4-message contradiction reads as a spectacular net-new find; `grep -rn
"ClientFinished" docs/audits/` returns **C27 and C28**, which settled it on the merits in June and
routed it correctly. It is not net-new and is not re-opened here. What follows is what survived
that guard.

---

## §A — Prior-fix hold and regression (target byte-frozen)

`git log -1 -- web4-standard/protocols/web4-handshake.md` → `57caa2e1` (2026-06-29, C113
remediation). Blob at HEAD = `75aa965e` — identical to the blob C222 and C260 each verified.
**32 days frozen**; C113's two fixes therefore hold *by construction*, and were re-read anyway
rather than presumed:

| C112 finding | C113 fix | Site at HEAD | Verdict |
|---|---|---|---|
| N1 — W4-IOT-1 Profile column read `CBOR` | → `COSE` | `:24` `\| W4-IOT-1 (MAY) \| X25519 \| Ed25519 \| AES-CCM \| SHA-256 \| COSE \|` | **HELD** |
| N2 — §6.0.3 signing-input scope | scoped vs §6.0.5 | `:139` sig-structure clause names §6.0.5 for `HandshakeAuth` | **HELD** |

Regression sweep: `grep -c '&amp;\|&lt;\|&gt;\|&quot;'` = **0** HTML-entity artifacts; **269**
lines intact; C73's B1–B10 fix set remains inside the frozen blob. **0 regression.**

**Anti-manufacture condition:** the target's bytes are unchanged and no §A finding is claimed
against them. Every finding below is charged against an artifact *other* than the target.

## §B — Corpus delta since the C260 snapshot (2026-07-23)

```
git log --oneline --since=2026-07-23                     → 70 commits repo-wide
git log --oneline --since=2026-07-23 -- web4-standard/   → 3
git log --oneline --since=2026-07-23 -- web4-core/       → 0
```

The three `web4-standard/` commits: `01f410db` (ontology `web4:Tensor` superclass +
`web4:observationCount`, closes #581), `954ee391` (proposal #580), `4665a430` (proposal #579).
**None touches `protocols/`, `core-spec/core-protocol.md`, the SDK, the vectors, or `submission/`.**

**§B is EMPTY** — 3rd consecutive delta with no handshake-relevant corpus movement. Which is
precisely why this pass's yield had to come from re-deriving the gate rather than re-running it:
a `--since` window over a frozen neighbourhood cannot see a divergence that predates the lineage.

## §B′ — Mirror set, RE-DERIVED (method carry v8)

### B′.1 Candidate generation — one grep, published in full

```
tokens: ClientHello|ServerHello|ClientFinished|ServerFinished|HandshakeAuth
        |SessionKeyUpdate|HPKE|transcript_mac|MAC(transcript)          (case-insensitive)
trees:  web4-standard/  web4-core/  hub/
excl:   */target/  node_modules      (archive/ and forum/ excluded by standing rule)
```

| hits | artifact |
|---:|---|
| 39 | `web4-standard/implementation/sdk/tests/test_protocol.py` |
| 38 | `web4-standard/implementation/sdk/web4/protocol.py` |
| 36 | `web4-standard/protocols/web4-handshake.md` *(the target)* |
| 13 | `web4-standard/implementation/reference/web4_demo.py` |
| 9 | `web4-standard/core-spec/core-protocol.md` |
| 8 | `web4-standard/implementation/sdk/web4/__init__.py` |
| 7 | `web4-standard/submission/web4-rfc.md` |
| 5 | `web4-standard/testing/test-vectors/README.md` |
| 4 | `web4-standard/submission/draft-web4-core-00.xml` |
| 4 | `web4-standard/submission/draft-palatov-web4-core-00.txt` |
| 4 | `web4-standard/implementation/sdk/tests/test_integration.py` |
| 4 | `web4-standard/implementation/reference/web4_reference_client.py` |
| ≤3 | 21 further artifacts (guides, validators, READMEs, `extensions.md`, `mcp-protocol.md`, two vector files) |
| **0** | **`web4-core/`  — entire tree** |
| **0** | **`hub/`  — entire tree** |

**Stopping rule (declared before verdicts, so the tail is capped by a published number, not by
taste):** M-gate verdicts are argued for every artifact at **≥4 hits** (12 artifacts). The 21
artifacts at ≤3 hits are **declined as a class**, ground = hit count, with the class named:
tooling/READMEs/guides that *reference* the handshake without specifying or implementing one.
Two members of that tail — `testing/test-vectors/handshakeauth_{cose,jose}.json` (1 each) — are
**not** declined but are already on the ledger as C112 X1 and are treated there.

### B′.2 The gate's own history

```
grep -c 'implementation/sdk' over the 7 lineage audit docs:
  C28:1  C72:1  C112:0  C144:0  C184:0  C222:0  C260:0
grep -c 'protocol\.py'      over the same 7:
  C28:4  C72:1  C112:0  C144:0  C184:0  C222:0  C260:0
```

**Correction to this pass's own first draft, recorded rather than silently fixed:** the draft
said "no delta pass has read `protocol.py`." That is **false** — C72 is a delta pass and it read
the SDK (its C-M1 row cites the SDK's `nonce[32]`). The true statement is narrower: **no delta
pass since C72 — five consecutive** — has referenced it. The draft reached the wrong figure by
counting over "the 5 delta docs," a set that silently excluded C72. Publishing a mis-scoped count
inside a finding *about* mis-scoped counts would have been self-refuting; the per-doc row above
replaces the adjective.

Second instrument correction, same class: the draft said "9 lineage audit docs." There are
**7**. C73 and C113 are *remediation commits*, not audit documents — `ls docs/audits/*handshake*`
returns 7 files.

### B′.3 M-gate verdicts (≥4 hits)

| artifact | M1 subject matter | M2 genuine | M3 admitted | verdict |
|---|---|---|---|---|
| `implementation/sdk/web4/protocol.py` | PASS | GENUINE (type layer) | **ADMITTED** | implements **variant 2**; docstring self-declares *"Canonical types per core-spec/core-protocol.md"* |
| `implementation/sdk/tests/test_protocol.py` | PASS | GENUINE | **ADMITTED** | **test-locks** variant 2: `:65 assert len(phases) == 4` |
| `implementation/sdk/web4/__init__.py` | PASS | re-export only | ADMITTED (evidence) | re-exports the 4 phase classes |
| `implementation/reference/web4_reference_client.py` | PASS | GENUINE | **ADMITTED** | implements **variant 1** (`:18 {"type":"HandshakeAuth"}`) |
| `implementation/reference/web4_demo.py` | PASS | GENUINE | ADMITTED | variant 1; source of C72's §6.2 directional-KDF fix |
| `core-spec/core-protocol.md` | PASS | n/a (spec peer) | ADMITTED | **variant 2** §2 |
| `submission/web4-rfc.md` | PASS | n/a (spec peer) | **ADMITTED** — see B′.4 | **variant 3** §1.2 |
| `submission/draft-palatov-web4-core-00.txt` | PASS | n/a (spec peer) | **ADMITTED** — see B′.4 | **variant 4** §4.2 |
| `submission/draft-web4-core-00.xml` | PASS | n/a | ADMITTED (evidence) | names HPKE, specifies no message set |
| `implementation/sdk/tests/test_integration.py` | PASS | GENUINE | ADMITTED (evidence) | exercises variant 2 |
| `testing/test-vectors/README.md` | PASS | n/a | ADMITTED (evidence) | documents both vector families |
| `web4-core/` **(whole tree)** | **FAIL — 0 hits** | — | — | **not a handshake mirror.** The negative is correct *for this tree*; see N3 for what was published off it |
| `hub/` **(whole tree)** | **FAIL — 0 hits** | — | — | argued fresh for handshake, not imported from C294/C296 |

### B′.4 Admission argument for `submission/` (argued, not assumed)

The submission tree is the one M3 call that could go either way, so it is argued rather than
asserted:

- It is **inside `web4-standard/`**, not in `archive/` or `forum/` (both excluded by standing rule).
- `grep -rniE "supersed|obsolet|historical|archiv|deprecat|do not use|outdated"` over
  `web4-standard/submission/*.md` → **0 hits**. Nothing marks these documents as retired.
- `SUBMISSION_GUIDE.md` declares **"Status: Ready for initial submission · Target: Standards
  Track."** That is a live forward-looking claim, not a historical note.
- It is the **outward-facing** surface — the artifact an external reader or an IETF reviewer meets.

⇒ **ADMITTED.** The counter-argument deserves recording: `draft-palatov-web4-core-00.txt` is
dated "September 2025" and stamped *"Expires March 15, 2026"* — it is, on its own face, an
**expired** Internet-Draft. That weakens "actively authoritative" but does not reach admission:
an expired draft that nothing marks superseded, sitting in a directory whose guide says "ready
to submit," is still what a reader finds. It argues for *severity down*, not for exclusion — and
the severity assigned in N2 reflects that.

---

## §C — Findings

### C300-N1 (HIGH → operator; instrument) — the handshake carry ledger emptied at C144, and four passes then certified the target clean without it

C112 §C published an 11-row routing table. Row survival, measured per document:

```
doc     D1*  D2   D3   D4   X1   X2   X3   X4
C112     4    6    3    4    4    3    3    5
C144     0    0    0    0    0    0    0    0
C184     0    0    0    0    0    0    0    0
C222     0    0    0    0    0    0    0    0
C260     0    0    0    0    0    0    0    0
```
*`D1*` = bare-`\bD1\b` count minus `B-D1` count (see the collision note below).

Cross-checked on the **constructs** rather than the labels, because a label can be dropped while
the subject survives under other words:

```
              peer_salt   w4idp   nonce   3-msg|4-msg
  C112            2         6       7          1
  C144            0         0       0          0
  C184            0         0       0          0
  C222            0         0       0          0
  C260            0         0       0          0
```

Both instruments agree: **the ledger is not merely unlabelled after C144, it is absent.**

**Two traps in the measurement, published because either one alone would have hidden this:**

- **Token collision manufacturing false continuity.** A naive `\bD1\b` grep returns 5, 5, 5, 4
  hits in C144/C184/C222/C260 — the carry looks alive. But in each of those documents the
  bare-`D1` count **equals the `B-D1` count exactly** (5=5, 5=5, 5=5, 4=4): every hit is the
  unrelated registries flagship `B-D1`. Handshake-`D1` references: **zero**. (In C112, 6 total −
  2 `B-D1` = 4 genuine.)
- **A label re-bound mid-lineage.** `C-M1` denotes the **nonce-size design-Q** in C72/C112 and
  the **crypto-suite SSOT flagship (`C-M1 ≡ B-D1`)** from C144 onward. One label, two items. A
  reader tracking "C-M1 still carried: 4, 4, 3, 3" would conclude the nonce design-Q is tracked.
  It is not.

**Mechanism, stated fairly.** C144 did **not** assert the carries were closed, and C144 is a
strong pass on its own subject — it inverted the DELTA-1 adjudication with owner-side evidence
and its reasoning holds. What it did was narrow the pass to DELTA-1 and publish
`:82 "Net-new internal (handshake) | 0. handshake is clean and correct."` with **no carry
section at all**. C184 inherited "clean and correct" plus an empty ledger, and C222 and C260
reproduced it. This is [[feedback_prose_is_not_ledger]] at lineage scale: the items lived in
C112's §C table, were never promoted forward, and vanished without any pass ever ruling on them.
The "4 consecutive spec-side-clean deltas" streak is, to this extent, an artifact of the ledger
having emptied rather than of the questions having been answered.

**All four D-series items re-verify as STILL TRUE at live HEAD** (binary re-verification only —
no re-argument, no fresh severity; the owning records are C28 §C-H1 → C72 D3 → C112 §C):

| item | claim | live-HEAD check | status |
|---|---|---|---|
| **D1** (HIGH) | `peer_salt` MUST be exchanged in the handshake but has no carrier field | `:49` states the MUST; `peer_salt` appears **0** times in the §5.1/§5.2 field lists (`:84–113`) | **still true** |
| **D2** (MED) | random-exchanged vs `H(peer_id)` salt source undecided | §4.2 mandates random+unique; no derivation alternative resolved | **still true** |
| **D3/C-H1** (HIGH) | 3-msg-sig vs 4-msg-MAC | see N2 — now **4-way** | **still true, wider** |
| **D3/C-M1** (MED) | nonce size 96 / 32 / 48 | spec `<random 96-bit>` ×3; `protocol.py:89 # 32-byte hex nonce`; vector `core-protocol.json:144 "a1b2c3d4e5f6"` = 6 bytes = **48-bit** | **still true, all three** |
| **D3/C-M3** (MED) | `w4idp` surface form | handshake `w4idp-<base32>` vs `data-formats.md:95` `w4id:pair:{base32}` | **still true** |
| **D4** (INFO) | §10 `AUTHZ_DENIED`@401 rides errors B-1 | `:262` unchanged | **still true** |
| **X1–X4** | vector regeneration + `PROTO_FORMAT` registration | X4 verified in §C-carry below | **still true** |

**Route**: operator. **Not auditor-applicable** — these are design questions about which
handshake is canonical, and remediation is additionally gated by **D0**. The *ledger* defect,
however, is auditor-applicable and is fixed by the §C ledger below.

### C300-N2 (MED → operator; reach-escalation on C-H1 — NOT net-new as a defect) — two further handshake specifications, never read by the lineage, both in the outward-facing tree

Per [[feedback_carry_gains_reach_not_truth]], a standing carry that acquires new surfaces routes
as a reach-escalation, never as net-new. C-H1's *truth* is C28's. Its *reach* is understated by a
factor of two:

| # | artifact | messages | authentication | ever read by lineage |
|---|---|---|---|---|
| 1 | `protocols/web4-handshake.md` §5–6 **(self-declared MTI, `:6`)** | ClientHello · ServerHello · **HandshakeAuth** (bidirectional) | signature over `Hash(TH ‖ channel_binding)`, COSE_Sign1/JWS | target |
| 2 | `core-spec/core-protocol.md` §2 | ClientHello · ServerHello · **ClientFinished · ServerFinished** | **MAC(transcript)** | C28, C72 |
| 3 | `submission/web4-rfc.md` §1.2 `:168–171` | same four names as #2 | **"a signature of the handshake messages"** — *not* a MAC | **0 of 7** |
| 4 | `submission/draft-palatov-web4-core-00.txt` §4.2 `:501–535` | **ANNOUNCE · INTEREST · CONFIRM · ACK** | `encrypted_payload: "HPKE:…"`, `witness_attestations` | **0 of 7** |

Variant 4 **shares no message name with any of the other three.** Variant 3 shares variant 2's
message names but contradicts its authentication mechanism (signature vs MAC) — so it is not a
restatement of #2, it is a third answer.

Two implementations, each faithful to a different variant, both inside the standard:
`implementation/sdk/` → variant 2, **test-locked** at `test_protocol.py:65 assert len(phases) == 4`;
`implementation/reference/web4_reference_client.py` → variant 1 (`:18 {"type":"HandshakeAuth"}`).

A further contradiction inside variant 3: `web4-rfc.md` §2.3 `:456–461` instructs implementers to
"Perform **ECDH** to establish shared secret" and §2.4 to encrypt with **AES-256-GCM** — where
the MTI spec §1 mandates **HPKE (RFC 9180)** and neither §3 suite offers AES-256-GCM (W4-BASE-1 =
ChaCha20-Poly1305, W4-FIPS-1 = AES-128-GCM). **The AES-256-GCM orphan is NOT charged here** — it
is already on the registries ledger as **≡ A-3**, and this is simply a new face of it.

**Severity MED, not HIGH, and the argument is recorded both directions.** *For HIGH*: this is the
outward-facing surface, nothing marks it superseded, and `SUBMISSION_GUIDE.md` says "ready for
initial submission." *For MED*: variant 4 is on its face an **expired** draft ("Expires March 15,
2026"), and both submission documents are frozen (`4a0dce74` 2026-04-29, `84f069a0` 2026-02-16) —
they are stale artifacts rather than actively-diverging ones, and no implementation follows either.
MED taken.

**Route**: operator, bundled with D3/C-H1 — same adjudication ("which handshake is canonical"),
now with four candidates instead of two. **NEVER auto-action:** variants 1 and 2 both carry
conformance vectors (C72 headline 2), so any "fix" deletes a vector-backed flow. That is a
standards decision, not an auditor's.

### C300-N3 (MED → instrument; supersedes the published *reach* of C184-N1) — the mirror gate was aimed at the only two trees with zero handshake content

Five passes (C112, C144, C184, C222, C260) ran the handshake mirror gate over `web4-core/`. This
pass's candidate generation returns **`web4-core/` = 0 hits and `hub/` = 0 hits** on the handshake
token set, while the four highest-hit artifacts in the corpus are all inside `web4-standard/`
itself — including two the gate would have had to *pass through* to reach the crate.

C184-N1's finding, restated precisely: *"HPKE-handshake wire negative grep over web4-core
executable = empty."* **As scoped, that is TRUE and is re-confirmed here** (`web4-core/` = 0).
What does not survive is the *reach* it was read at across C222 and C260 — that the handshake
wire protocol is unbuilt. It is built twice, in two mutually non-interoperable versions, inside
the standard's own tree. Per [[feedback_gate_scoped_to_wrong_tree]], the three repeats of the
`web4-core/`-scoped grep are **one error, not corroboration**.

C260's forward guard is stale in both halves and is the mechanism that would have repeated this:

> `:82` — "Next handshake delta **~C296**. Guard C296: re-run the mover-guard grep
> (`session.?key|HKDF|X25519|ClientHello`) over any *new* **web4-core** module."

(a) the slot is wrong — the rotation is last-pass + 40, so the next delta is **C300**, not C296;
(b) the guard names a **path** (`web4-core`) rather than a **behaviour**, which is exactly
[[feedback_guard_names_a_path_not_a_behaviour]] — the handshake never relocated *into* the crate,
it was never there, and the guard could only ever have returned zero.

**Route**: instrument fix, applied in the §C ledger below. Auditor-applicable, no operator gate.

### C300-N4 (LOW → instrument) — lineage ordinal collision

`C260-web4-handshake-4th-delta-…md` and `C184-web4-handshake-4th-delta-…md` both claim "4th
delta." True chain: C28 (first pass) → C72 (1st delta) → C112 (2nd) → C144 (3rd) → C184 (4th) →
C222 (5th) → C260 (**6th**, mislabelled 4th) → **C300 (7th)**. Filenames are **not** renamed
(they are cited from other documents); recorded so the next pass computes from the chain, not
from the filename. Consistent with the sibling lineages, where C298 shipped as "7th delta."

---

## §C-carry — the ledger, restored

Reported as a table with stable greppable labels, because the failure being reported is an item
that lived in prose and never reached a ledger. **Forward guards are phrased as behaviours, not
paths** ([[feedback_guard_names_a_path_not_a_behaviour]]).

| ID | Sev | Class | Status at C300 | Route |
|---|---|---|---|---|
| **HS-D1** (C112 D1) | HIGH | design-Q | **OPEN** — `peer_salt` MUST-exchange with no carrier field; re-verified | operator |
| **HS-D2** (C112 D2) | MED | design-Q | **OPEN** — salt source undecided | operator (settle with HS-D1) |
| **HS-D3a** (C28 C-H1) | HIGH | design-Q | **OPEN, WIDENED to 4-way** (N2) | operator — NEVER auto-action |
| **HS-D3b** (C72/C112 C-M1 — *the nonce item, not `B-D1`*) | MED | design-Q | **OPEN** — 96-bit / 32-byte / 48-bit | operator |
| **HS-D3c** (C112 C-M3) | MED | design-Q | **OPEN** — `w4idp-` vs `w4id:pair:` | operator |
| **HS-D4** (C112 D4) | INFO | design-Q | **OPEN** — §10 401 rides errors B-1 | errors owner |
| **HS-X1** (C112 X1) | MED | cross-track | **OPEN** — regenerate `handshakeauth_{cose,jose}` | vector maintainer |
| **HS-X2** (C112 X2) | LOW | cross-track | **OPEN** — JOSE vector payload alg EdDSA→ES256 | vector maintainer |
| **HS-X3** (C112 X3) | LOW | cross-track | **OPEN** — JOSE vector `typ=JWT` | vector maintainer |
| **HS-X4** (C112 X4 ≡ C70 B-C1) | MED | cross-track | **OPEN, gains a code-side face** — see below | errors owner |
| **DELTA-1 / B-D1 / C-M1(SSOT)** | — | design-Q | **OPEN, unchanged** — handshake `:24` COSE is correct; the defect is on the sibling cells | operator |
| **B-7** (`P-256EC` at `:23`) | — | cross-track | **OPEN, unchanged** — do NOT re-open net-new | operator |
| **C222-N1** (ratchet name-collision) | — | — | **HELD** — governance ratchet ≠ §6.2 session-key ratchet | — |
| **C184-N1** (HPKE absent from `web4-core/`) | — | — | **HELD as scoped; published reach superseded by N3** | — |

**HS-X4, verified at its owning target this pass (goal 4 of the approved scope).**
`W4_ERR_PROTO_FORMAT` is a **MUST** at `web4-handshake.md:164` (§6.0.7). Paths searched and
results: `grep -rl --include=*.md 'W4_ERR_PROTO_FORMAT' web4-standard/` → **2 files**
(`protocols/web4-handshake.md`, `registries/initial-registries.md`); `grep -rn
'W4_ERR_PROTO_FORMAT\|PROTO_FORMAT' web4-standard/implementation/sdk/` → **0 hits**. So the code
is registered but has **no home in `errors.md` and no SDK implementation**. This is **C112 X4 ≡
C70 B-C1, re-verified and gaining a code-side face from C298-N1** — explicitly **not** a C300
net-new.

### Forward guards for C340 (next handshake delta = 300 + 40)

1. **Re-derive the mirror set again.** Inheriting even this corrected 12-artifact list reproduces
   the mechanism. Re-run candidate generation and diff the artifact list against this one.
2. **Guard the behaviour, not the tree.** The question is *"what artifact now specifies or
   implements a Web4 handshake?"* — never *"has `web4-core/` grown a handshake module?"* Both
   `web4-core/` and `hub/` returned 0 hits at C300; a zero from either is uninformative, not
   reassuring.
3. **Carry the §C-carry table forward verbatim.** If a row is closed, say which pass closed it
   and on what evidence. An item that leaves this table without a disposition is the C144 defect
   recurring.
4. **Baseline every `D`-label grep against `B-D1`** before reading continuity off it, and note
   that `C-M1` names two different items depending on the pass.
5. **Do NOT re-open as net-new**: the 3-msg/4-msg split (C27/C28), `:23` `P-256EC` (B-7), `:24`
   DELTA-1, the AES-256-GCM orphan (registries A-3), the ratchet name-collision (C222-N1).

---

## Instrument note — counts re-run after the findings were written

Per [[feedback_publish_the_instrument]], every count above was re-executed after this document
was drafted. Two numbers changed under re-run and the text was corrected rather than kept:
"9 lineage docs" → **7**, and "no delta pass has read `protocol.py`" → **"none since C72"**
(C72 = 1 hit). Both errors were of the same class as the finding being reported — a count taken
over a set that silently excluded a member — which is why they are recorded here instead of
quietly fixed.

The candidate-generation grep, the D-row survival table, the construct table, the `B-D1`
collision figures, and the `W4_ERR_PROTO_FORMAT` path counts were each re-run against live HEAD
after drafting and were unchanged (`web4-core/` 0, `hub/` 0, ≥4-hit artifacts 12, ≤3-hit tail 21,
superseded-marker grep 0, top four 39/38/36/13).

**A third self-correction, from the re-run itself.** The verification command for the per-artifact
hit counts was written as `grep -ncieE <pattern> <file>`; the flag cluster consumed the pattern as
a filename, so `grep` silently counted *lines* and returned 406 / 389 / 191 / 123 — four
plausible-looking numbers that were not measurements of anything. They were caught only because
they disagreed with the values already in the document. Re-run as `grep -c -i -E` they are
39 / 38 / 36 / 13, matching. Recorded because it is the same failure mode as N3 one level up: **the
verifier is also a hypothesis, and a silently-failing one returns numbers rather than an error.**
The general guard: a verification run that *agrees* with the draft has confirmed nothing until you
have confirmed the verifier ran.

## Disposition

- **Mutation**: none. **Net-new findings**: 4 (1 HIGH, 2 MED, 1 LOW) — **none inside the
  byte-frozen target**.
- **C301 = NO-OP.** N1 and N2 are operator-owned design questions additionally gated by D0; N3
  and N4 are instrument fixes discharged by this document's §C-carry table and forward guards.
  Do **not** manufacture a `protocols/` edit.
- **One operator memo**, bundling **HS-D1 + HS-D2 + HS-D3a/b/c** under the single question they
  all reduce to: *which of the four handshakes is canonical, and what happens to the conformance
  vectors and the two implementations of the other three?*
