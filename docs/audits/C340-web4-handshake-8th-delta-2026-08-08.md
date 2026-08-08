# C340 — `protocols/web4-handshake.md`, 8th delta

**Date**: 2026-08-08 · **Slot**: C340 (= C300 + 40, rotation wrap) · **Lineage**:
C28 → C72 → C112 → C144 → C184 → C222 → C260 → C300 → **C340** (8th delta)
**Target**: `web4-standard/protocols/web4-handshake.md` — 269 lines, byte-frozen at
`57caa2e1` (2026-06-29) = **40 days**
**Window**: C300 (2026-07-31) → HEAD `c9294194` = **47 commits**
**Mutation**: **ZERO.** This document is the only artifact produced.
**Alignment**: `docs/SPRINT.md:37` — Sprint 54 records the C-series as per-session
policy-reviewed work under the v2 protocol, logged retroactively.

---

## Verdict

**2 net-new — 1 MEDIUM, 1 LOW.** Neither is inside the target file. All **14** rows of C300's
§C ledger re-verify at live HEAD with a published disposition. One candidate was generated and
**refuted on the merits** (§D). Cadence datapoint **#15** logged, not acted on.

**Framing, stated plainly at the policy reviewer's instruction rather than left implicit:**
this rotation is now auditing the **instrument**, not the documents. Both net-new findings are
about how the corpus *checks* itself — one about a remediation channel that has never once
fired, one about an anchor that decayed inside a row marked "not re-adjudicated." The target
file itself is clean, for the sixth consecutive delta. Corpus findings are reported here as
corpus findings; none is dressed up as a target finding.

| # | Sev | Class | One line |
|---|---|---|---|
| **N1** | **MED** | net-new (mechanism = C336-N1, 2nd instance) | The file `SUBMISSION_GUIDE.md` tells the reader to upload to the IETF still carries the W4IDp derivation defect this lineage found and fixed **51 days ago** |
| **N2** | **LOW** | net-new (instrument / anchor) | DELTA-1's locus is cited as `web4-handshake.md:23` by two security-framework passes; `:23` is **B-7's** line — the collider — and W4-IOT-1 is at `:24` |

---

## §A — Prior findings, re-verified at live HEAD

Method carries applied: **v10** (row survival), **v11/v22** (anchor re-resolution by content),
**v12** (direction), **v19/v23/v24** (row set, row count, named members), **v25** (deferral row
first), **v28/v29/v30** (run first, per the standing carry).

### A.1 — The 14-row §C ledger

**Anchor discipline, per binding condition 6:** C300's ledger is cited **by name**, not by line
span — it is the §C table whose header row is
`| ID | Sev | Class | Status at C300 | Route |` in
`docs/audits/C300-web4-handshake-7th-delta-2026-07-31.md`, rows enumerated by ID below. A line
range into a 400-line audit doc in a daily-moving tree is exactly the anchor class **v22** exists
to retire. (This correction was forced in review: my scope statement verified the row *count* and
published an unverified *span* alongside it. That is C338-N1's own mechanism at one remove — the
verified figure travels with an unverified locus, and the locus is what the next pass inherits.
Recorded here rather than quietly fixed.)

**Row count: 14 in, 14 out. No row loses its count, its disposition, or its name.**

| ID | Sev | Disposition at C340 | Evidence re-run at HEAD |
|---|---|---|---|
| **HS-D1** | HIGH | **OPEN, unchanged** | `:49` `peer_salt` **MUST be exchanged**; occurrences of `peer_salt` inside the §5.1+§5.2 field lists (L81–109) = **0**. Carrier field still absent. |
| **HS-D2** | MED | **OPEN, unchanged** | Salt source still undecided; settles with HS-D1. |
| **HS-D3a** | HIGH | **OPEN, 4-way — widening to 5-way REFUTED (§D)** | Variants re-measured; see §D. Never auto-action. |
| **HS-D3b** | MED | **OPEN, unchanged** | Three widths live: spec `96-bit` ×**3**; `protocol.py:89` `# 32-byte hex nonce`; `test-vectors/protocol/core-protocol.json:144` `"a1b2c3d4e5f6"` = **6 bytes / 48-bit**. |
| **HS-D3c** | MED | **OPEN, unchanged** | `web4-handshake.md:86`/`:101` `w4idp-<base32>` vs `data-formats.md:95` `f"w4id:pair:{…}"`. |
| **HS-D4** | INFO | **OPEN, unchanged** | §10 401 rides errors **B-1**; owner = errors. |
| **HS-X1** | MED | **OPEN, unchanged** | `handshakeauth_{cose,jose}` regeneration still owed. |
| **HS-X2** | LOW | **OPEN, unchanged** | JOSE vector payload alg EdDSA→ES256. |
| **HS-X3** | LOW | **OPEN, unchanged** | JOSE vector `typ=JWT`. |
| **HS-X4** | MED | **OPEN, unchanged** | `W4_ERR_PROTO_FORMAT` MUST-abort at `:164`; present in exactly **2** files (`web4-handshake.md`, `registries/initial-registries.md`), **0** in `errors.md`, **0** in the SDK tree. ≡ C70 B-C1. |
| **DELTA-1 / B-D1 / C-M1(SSOT)** | — | **OPEN, unchanged — NOT re-adjudicated** | `web4-handshake.md:24` = `COSE`; `core-protocol.md:20` + `initial-registries.md:8` = `CBOR`. Operator-gated. **Its locus is N2's subject.** |
| **B-7** | — | **OPEN, unchanged — do NOT re-open** | `:23` `P-256EC`; canonical `ECDH-P256`. Evidence-only under **D0**. |
| **C222-N1** | — | **HELD** | Governance ratchet ≠ §6.2 session-key ratchet. Unchanged. |
| **C184-N1** | — | **HELD as scoped; reach superseded by C300-N3** | Unchanged. |

**v10 row-survival check on this lineage's own ledger.** C300 restored the table precisely because
C112's 11-row version had gone to a column of zeros across C144/C184/C222/C260. One delta later the
restoration **held**: all 14 rows are re-typed here under their own ids. The collider trap C300
documented is still live and still avoided — a bare `\bD1\b` grep over this document would over-count,
because `B-D1` (the registries flagship) and `HS-D1` (the `peer_salt` item) are different items.
Reported so the next pass does not read continuity off the label.

### A.2 — Prior pass's deferral row (v25)

C300 declined a **21-artifact tail at ≤3 hits** as a class, with the count as the published ground,
and named **7** of the **12** artifacts in its ≥4 class. Re-run of C300's exact published matcher at
HEAD (§B.1) reproduces the class boundary. **The deferral is where N1 came from** — not from the
declined tail, but from a *named, admitted* member whose disposition answered a different question
than the one that mattered. See §B.2.

---

## §B — Corpus delta and the mirror set

### B.1 — Window

**47** commits. **2** touch `web4-standard/`; **0** touch the target; **0** touch any
`protocols/` file.

| Commit | Date | Touches |
|---|---|---|
| `e4a62d7a` | 2026-08-05 | `docs/FRACTAL_ROLE_IDENTITY.md`, `rfcs/RFC-COMPOSITE-ENTITY-IDENTITY.md`, `rfcs/RFC-SHARED-POLICY-SUBSTRATE.md` |
| `8d3808db` | 2026-08-04 | `testing/test-vectors/validate_context_refs.py` (new, 152 L) |

**The window is thin and is reported as thin.** Per the binding anti-padding condition: a thin
window is a finding about the corpus, not a quota to fill. Neither commit creates an inbound
obligation on the handshake — but note `e4a62d7a` **does** establish that `web4-standard/rfcs/` is a
maintained tree (v29 rider 4), which is why its NEGATIVE below is worth publishing rather than
assuming.

### B.2 — Mirror set, re-derived (not inherited)

C300's forward guard #1: *inheriting even this corrected 12-artifact list reproduces the mechanism.*
So the set was re-derived from the **subject matter** — "what artifact now specifies or implements a
Web4 handshake?" — never "has `web4-core/` grown a handshake module?" (guard #2).

**Pre-registered window (v26):** matcher
`ClientHello|ServerHello|ClientFinished|ServerFinished|HandshakeAuth|SessionKeyUpdate|HPKE|transcript_mac|MAC\(transcript\)`;
recursion roots `web4-standard/ web4-core/ hub/`; `--exclude-dir=target --exclude-dir=node_modules`;
**all filetypes, no `--include`** (v29 rider 2); tool `grep -rncE`; measured at `c9294194`.

| Hits | Artifact | Disposition |
|---|---|---|
| 39 | `implementation/sdk/tests/test_protocol.py` | mirror (variant 2, test-locked) |
| 38 | `implementation/sdk/web4/protocol.py` | mirror (variant 2) |
| 36 | **`protocols/web4-handshake.md`** | **target** (variant 1, MTI) |
| 13 | `implementation/reference/web4_demo.py` | mirror |
| 9 | `core-spec/core-protocol.md` | normative sibling (variant 2) |
| 8 | `implementation/sdk/web4/__init__.py` | mirror |
| 7 | `submission/web4-rfc.md` | outward peer (variant 3) |
| 4 | **`submission/draft-web4-core-00.xml`** | **outward peer — N1** |
| 4 | `submission/draft-palatov-web4-core-00.txt` | outward peer (variant 4) |
| 4 | `implementation/sdk/tests/test_integration.py` | mirror |
| ≤3 | 21-artifact tail | declined as a class, count as ground (C300 precedent) |

`web4-core/` = **0**. `hub/` = **0**. Per guard #2 these zeros are **uninformative, not
reassuring**, and are published as such.

**Published NEGATIVEs (v13 rider 7 / v24 — a disposition must name its members).** The v29 outward
tree, swept **first** per binding condition 2, with the wider subject predicate
(`…|W4IDp|w4idp|peer_salt|GREASE`), lines matched:

| Outward artifact | Hits | Disposition |
|---|---|---|
| `submission/draft-web4-core-00.xml` | **9** | **N1** |
| `submission/web4-rfc.md` | 7 | variant 3, unchanged (C300) |
| `submission/draft-palatov-web4-core-00.txt` | 4 | variant 4, unchanged (C300) |
| `submission/SUBMISSION_GUIDE.md` | 3 | evidence for N1, not a spec |
| `web4-standard/QUICK_REFERENCE.md` | **0** | NEGATIVE |
| `docs/reference/ACT_QUICK_REFERENCE.md` | **0** | NEGATIVE |
| `docs/what/specifications/WEB4_QUICK_REFERENCE.md` | **0** | NEGATIVE |
| `web4-standard/rfcs/` (9 files) | **0 of 9** | NEGATIVE — and this tree *moved* in-window, so the zero is informative |

**v30 collision check, run because C338's MEDIUM came from exactly this.** Three distinct files
match `*QUICK_REFERENCE*`. All three return **0** on the handshake predicate, so no handshake carry
is anchored to an ambiguous `QUICK_REFERENCE` filename and there is nothing here to mis-resolve.
Published because a negative result on a method carry must be stated or silence implies the check
was skipped.

### B.3 — v28, third direction (work addressed to this lineage from outside it)

```
git grep -nE "web4-handshake\.md" -- docs/audits web4-standard/docs/audits \
  | grep -viE "C[0-9]+-web4-handshake" | grep -iE "owner|route|routed|cross-track"
```
**31** non-lineage audit files mention the target; the routing filter returns **17** lines across
**13** documents (both trees searched, per v17). All resolve to items already on the §A ledger —
DELTA-1 (registries lineage, C220/C258/C298/C338), B-7 (security lineage, C68/C218/C256/C296/C336),
B-1/§10 (errors lineage, C66/C106/C138), B-C1≡HS-X4 (C70/C110). **No unreceived inbound item.**
The sweep's output line count (**17**) and this table's row count (**17**) agree — published per
**v21**, whose entire subject is the gap between the two.

**But the sweep returned one thing that is not on the ledger: a disagreement about where DELTA-1
lives.** That is N2.

---

## §N1 — MEDIUM — The IETF submission source still carries a defect fixed 51 days ago

**Locus**: `web4-standard/submission/draft-web4-core-00.xml`, the `<figure><artwork>` block inside
`<section title="Privacy Considerations">` (grep anchor: `w4idp = MB32(HKDF-Extract-Then-Expand(`).

**The defect.** The outward copy derives the pairwise identifier with **three** parameters:

```
w4idp = MB32(HKDF-Extract-Then-Expand(
          salt=peer_salt,
          IKM=sk_master,
          info="W4IDp:v1"))
```

There is no HKDF-Expand **output length**. This is byte-for-byte the **pre-remediation** form of the
target's §4.1, confirmed against `git show 0179c470^:web4-standard/protocols/web4-handshake.md`.

**The harm is not inferred — this lineage already wrote it down.**
`docs/audits/C72-web4-handshake-delta-audit-2026-06-18.md:91` charged it MED:
> *"omits the HKDF-Expand output length, so the encoded W4IDp length is implementation-defined
> (two conformant impls derive different-length IDs)."*

**It was fixed, and verified fixed, in the target.** `0179c470` (2026-06-18, PR #362,
*"spec(C73): remediate 10 autonomous C72 findings"*) added `L=16` plus the sentence naming the
reason — *"so that two conformant implementations derive identical-length identifiers"*.
`C112:49` then closed the row: **HELD**.

**It never propagated.** Corpus-wide, the derivation appears in **5** pre-existing files (**6** at
HEAD once this audit document is counted — see the instrument note). Excluding the two under
the standing `forum/` + `archive/` exclusion (`forum/nova/…/core-handshake.md:32`,
`archive/reference-implementations/handshake_protocol_advanced.py:160`) and the C72 audit doc that
quotes it, **two** live artifacts carry it:

| Artifact | `L=16` present? |
|---|---|
| `web4-standard/protocols/web4-handshake.md:35` | **yes** (2 occurrences) — remediated |
| `web4-standard/submission/draft-web4-core-00.xml` | **no** — stale |

**Why this is not merely a stale copy.** `SUBMISSION_GUIDE.md` does not describe the XML as an
archive. It describes it as the thing to upload:

- `:10` — **Status: "Ready for initial submission"**
- `:28` — `xml2rfc --text --html draft-web4-core-00.xml` (the XML is the **source** the submitted
  text is generated from)
- `:36` — **"Upload `draft-web4-core-00.xml`"**, to `https://datatracker.ietf.org/submit/`
- `:40` — Intended Status: **Standards Track**

**The propagation channel has never fired — not once.** `git log -- draft-web4-core-00.xml` returns
exactly **one** commit in the file's entire history: `a6f54f46` (2025-09-11), its creation.
**331 days, zero maintenance commits.** Meanwhile the specs it copies moved underneath it:

| Spec the XML copies | Commits since `a6f54f46` |
|---|---|
| `protocols/web4-handshake.md` | **5** |
| `core-spec/security-framework.md` | **5** |
| `core-spec/core-protocol.md` | **3** |
| `core-spec/data-formats.md` | **2** |

**Why eight lineage passes missed it — and this is the part worth carrying.** C300 did **not**
overlook the XML. C300 *found* it, *admitted* it, and *dispositioned* it:

> `C300:146` — `submission/draft-web4-core-00.xml` | PASS | n/a | ADMITTED (evidence) |
> **"names HPKE, specifies no message set"**

That disposition is **correct**. It is also scoped entirely to C300's own subject — the
message-set split (C300-N2). The XML's *other* handshake content, the §4.1 derivation, was never
the question being asked. And because C322 established that an artifact entering the swept set
*"cannot be re-discovered as novel"*, **the row that admitted the artifact is the row that hid the
defect.**

This is a new face of a known class, and it is distinguishable from its neighbours — measure, do
not assume: C320 (a row stopped being typed) · C322 (a sweep's output line dropped between stdout
and the table) · C324 (a table collapsed and took its count with it) · **C340 (a member named,
admitted, and dispositioned on the wrong predicate)**. The first three lose information. This one
**manufactures** it — the artifact reads as examined.

**A second, independent mechanism reached the same result.** C300's admission argument rested in
part on a retirement check (`C300:159`): *superseded/obsolete/archival/deprecated* grep over
`submission/*.md` → **0 hits**. The XML **is not a `.md`.** C300's key negative grep was
structurally incapable of seeing the file it was admitting. That is **v29 rider 2** — the rule born
one fire ago, when C336's flagship hid behind `--include=*.md` for four passes — recurring here in a
**different lineage**, found by applying the rule that the previous fire's finding created.

**Relation to C336-N1 (classified deliberately, per v16).** C336 charged the *same file* with the
*same mechanism* at `:248-259` — a pre-remediation §1.1 crypto-suite table (`W4-FIPS-1` KEM
`P-256`, corrected by C31's B-H1 in `130069d8`). That is a **different locus**, a **different
remediation**, and a **different owning lineage**. This is therefore **net-new**, with the mechanism
attributed to C336-N1 as its **second instance**. The escalation is not "another miss": two
independent lineages, arriving from two unrelated remediations, now show that the XML received
**no** remediation at all. One miss is an oversight; two from disjoint directions is an unwired
channel.

I did **not** re-charge C336's crypto-table locus. Confirmed still stale (`W4-FIPS-1 | P-256`,
and W4-IOT-1 is absent from the XML's table entirely), and left with its owner.

### Adversarial refutation (v-carry: refute your BEST finding)

Four attempts. One survived partially and set the severity.

1. **"The XML is superseded by `draft-palatov-web4-core-00.txt`."** **Fails, and inverts.** The
   palatov draft is on its face **expired** (*"Expires March 15, 2026"*). `SUBMISSION_GUIDE.md:9`
   names `draft-web4-core-00` as the draft and `:36` names the `.xml` as the upload. The XML is the
   live one; palatov is the retired one.
2. **"No `.txt` was ever generated from it, so it was abandoned."** **Fails.** `:28` documents
   generation as a step the *submitter* runs at submission time (`xml2rfc --text --html`). The
   absence of a generated artifact is consistent with "not yet submitted", which is exactly what
   `:10` says — it is evidence the file is **pending**, not evidence it is dead.
3. **"It's an overview draft; the artwork is illustrative, not normative."** **Survives, partially,
   and sets the severity.** The block sits under *Privacy Considerations* and reads as explanatory.
   Against that: it reproduces the formula verbatim and completely, it is the only derivation in the
   document, and C72's harm statement is precisely about an implementer deriving from the formula.
   Net: real defect, bounded severity.
4. **"It's C336-N1 re-charged."** **Fails** on locus, remediation, and owning lineage — see above.

**Severity: MEDIUM** (v29 rider 6, bound by consumption). No executable path, no test, not in
`core-spec/` ⇒ not HIGH. Outward-facing, admitted as a spec peer by this lineage's own prior pass,
and the designated Standards-Track upload ⇒ not LOW. Identical rating to C336-N1 for the same file
and mechanism, which keeps the two comparable.

**Routing: outward-artifact maintainer / operator. NOT self-applied.** The one-line fix is to add
`L=16` to the XML's artwork block. It is not applied here for two reasons, and the second is the
real one: (a) ZERO mutation is this rotation's standing discipline; (b) **a one-line patch would
close the symptom and leave the channel unwired.** The finding is that a 331-day-old outward copy
receives no remediation traffic at all — that is an operator decision about whether `submission/`
is regenerated, pinned, or retired, and it is not the auditor's to make.

---

## §N2 — LOW — DELTA-1's locus points at B-7's line

**The claim.** Two security-framework passes cite DELTA-1 at `web4-handshake.md:23`:

- `C296:103` — *"`web4-handshake.md:23` gives W4-IOT-1 Profile=**COSE**"*
- `C336:107` — *"`web4-handshake.md:23` Profile=COSE"*

**At HEAD, on a file byte-frozen for 40 days:**

| Line | Content |
|---|---|
| `:22` | `W4-BASE-1 (MUST)` … `COSE` |
| `:23` | **`W4-FIPS-1 (SHOULD)` … `P-256EC` … `JOSE`** |
| `:24` | **`W4-IOT-1 (MAY)` … `AES-CCM` … `COSE`** |

W4-IOT-1 is at **`:24`**. Line `:23` is **W4-FIPS-1** — which is **B-7's** locus, cited correctly as
`:23` by those same two documents (`C296:242`, `C336:118`, `C336:136`).

So inside a single document, `:23` names two different carries: **correctly** for B-7, and
**incorrectly** for DELTA-1. The registries lineage has it right throughout (`C220:73`, `C258:65`,
`C298:210`, `C338:158` all `:24`), as do `C140:78` and `C222:50` — so this is a **two-document
divergence in one lineage**, not a corpus-wide drift.

**Why it matters, and why it is only LOW.** DELTA-1's **verdict is unaffected** — the divergence is
real, correctly described, and correctly directed (C144 inverted the adjudication in handshake's
favour; unchanged). What is wrong is the **locus**, and per **v30** — born at C338, one fire ago —
a *precise* locus that is false is worse than a vague one, because precision reads as verification.
Both occurrences sit in rows explicitly marked **"Not re-adjudicated"**, which is exactly where an
anchor can decay unobserved: the row is re-typed each pass (so **v19** sees it), its direction is
re-derived (so **v12** sees it), but nothing re-resolves the anchor by content because the row
announces that it was not re-checked.

**Not charged as a regression.** Snapshot-presence guard applied: `:23` is wrong at C296 and was
already wrong when written — the suite table has not moved since `57caa2e1` (2026-06-29), which
predates C296 (2026-07-31). So this is **born-false**, not drifted (**v15**), and the correct
reading is that a copy-forward propagated an error rather than an anchor going stale.

**Routing: security-framework lineage (next slot C376).** One-character correction in the two
documents' carry rows. Not applied here — this rotation does not rewrite past audit documents
(**v11**); corrections are published in the current pass.

---

## §D — Candidate generated and REFUTED

**Candidate: "the canonical-handshake split is 5-way, not 4-way."** `draft-web4-core-00.xml:228`
carries an ABNF message set — `message-type = "ANNOUNCE" / "HEARTBEAT" / "CAPABILITY"` — which
shares no name with C300-N2's variants 1–4 and would, on its face, widen HS-D3a again.

**REFUTED, on reading the section it sits in.** The XML's block is a **broadcast** protocol
(`broadcast-message`, `broadcast-version = "CAST/1.0"`), not a handshake. C300's disposition —
*"names HPKE, specifies no message set"* — is correct on this point, and C300's variant count of
**4** stands unwidened.

**The reciprocal check was also run, and also failed to overturn C300.** Variant 4's classification
was tested directly: `draft-palatov-web4-core-00.txt` §4.2 is titled **"Handshake Protocol"** and
opens *"HPKE-based mutual authentication and key agreement"*, with four phases ANNOUNCE / INTEREST /
CONFIRM / ACK. C300 classified it correctly.

Published because a refuted candidate is the cheapest thing a later pass can otherwise re-discover
as novel — and because **v13 rider 7** requires a method carry's negative results to be stated. The
same instrument that produced N1 produced this; reporting only the half that fired would misdescribe
the instrument.

---

## §C — Carries forward

All 14 rows of §A.1 carry forward **verbatim**, plus:

| ID | Sev | Status | Route |
|---|---|---|---|
| **C340-N1** | MED | **OPEN** — XML missing `L=16`; propagation channel unwired 331 d | outward-artifact maintainer / operator |
| **C340-N2** | LOW | **OPEN** — DELTA-1 locus `:23`→`:24` in C296/C336 | security-framework lineage (~C376) |

**Operator-gated, unchanged, not acted on:** **D0** (still gates `protocols/` cluster
remediation) · **B-D1** (crypto-suite SSOT inversion, unanswered) · the **CADENCE** design-Q,
now **datapoint #15**.

### Guards for C380 (next handshake delta)

Phrased as **behaviours**, not paths (C300 guard #2, [[feedback_guard_names_a_path_not_a_behaviour]]):

1. **Re-derive the mirror set again.** Do not inherit this pass's 10-artifact table either — the
   guard is the re-derivation, not the list.
2. **Ask what a prior pass's admission row actually answered.** An artifact with a PASS/ADMITTED
   disposition is *not* an examined artifact; it is an artifact examined **on one predicate**.
   Before trusting any swept-set membership, re-read the disposition text and ask which question it
   answered. This is C340's own yield and the cheapest thing to skip.
3. **Check N1 landed.** If `L=16` appears in `draft-web4-core-00.xml`, ask whether the *channel* was
   wired or only the line patched — a second stale locus in the same file after a one-line fix is
   the finding.
4. **Every carry's matcher: check its filetype filter AND its alternation before trusting its zero**
   (v29 rider 2). This pass found the rule firing in a second lineage; assume a third.
5. **Re-resolve anchors inside rows marked "not re-adjudicated" by CONTENT** — that is where N2
   lived, and the marking is what protects it from every other guard.
6. **Do NOT re-open**: 3-msg/4-msg (C27/C28) · `:23` `P-256EC` (B-7) · `:24` DELTA-1 · AES-256-GCM
   orphan (registries A-3) · ratchet name-collision (C222-N1) · the 5-way widening (§D, refuted) ·
   C336-N1's crypto-table locus in the XML (security-owned).
7. **C341 = NO-OP.** Every open bucket is operator- or sibling-gated.

---

## Instrument notes

- **v17 post-write re-run, amended form** (every published number, including this pass's own gate
  cells, re-run at a **different tool and root**). `ugrep`/`rg` cross-check at repo root against the
  drafting scope: the outward-tree table, the mirror-set table, the 5-file derivation sweep, the
  `L=16` presence grid all reproduced. **It forced two corrections**, neither caught by reasoning —
  both caught by a scope disagreement, which is the whole mechanism:
  1. The §B.3 routing filter was drafted as **14** documents. Re-run at root: **17 lines across 13
     documents**. The line count and the document count are different numbers and the draft had
     drifted between them — precisely the **v21** gap (a sweep's output vs the table written from
     it) inside the section reporting a v28 sweep.
  2. The derivation sweep was drafted as **5** files and re-ran as **6**. The sixth is **this
     document**. Writing the finding changed the number the finding cites — the audit enters the
     corpus it measures. The claim is therefore scoped explicitly (**5 pre-existing**), because
     "6 files carry the stale form" would be true of the string and false of the defect: this
     document quotes it in order to charge it, as does `C72:91`. A count is only as meaningful as
     the population it names, and an auditor is inside its own population.
- **A number handed to me is evidence, not authority** (v9/v21 rider 3). Both policy-review
  corrections were re-measured independently before acceptance: `docs/SPRINT.md` = 2084 lines,
  Sprint 54 at `:37`; C300's §C table = **14** rows. Both confirmed; both had been wrong in my
  proposal.
- **Own error, recorded** (v10 corollary): my scope statement verified the ledger's row *count* and
  published an unverified *line span* (`:322-336`) beside it — a span that resolves to neither the
  content rows nor the full table, and that truncates before the two rows the under-scoping would
  have dropped. Caught in review, not by me. The verified figure travelling with an unverified locus
  is C338-N1's mechanism, and finding it in my own proposal one fire after C338 charged it elsewhere
  is the reason binding condition 6 (name anchors, not line spans) is now standing.
- **Accountability self-audit**: **n/a — no surface.** This pass creates no path a caller can drive
  and performs no consequential act; it is a single additive audit document, zero mutation to
  `web4-standard/**`.
