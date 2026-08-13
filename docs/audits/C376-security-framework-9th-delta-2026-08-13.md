# C376 — `security-framework.md` 9th delta audit

**Date**: 2026-08-13
**Target**: `web4-standard/core-spec/security-framework.md`
**Base**: `af80e758` (C336 head) → `45fb2c6e` (HEAD)
**Lineage** (inclusive rule — 10 members, incl. the non-C-numbered remediation):
C31 · C68 · C108 · C109 · C140 · C180 · C218 · C256 · C296 · **C376**
**Verdict**: 3 MED + 1 LOW + 1 DESIGN-Q. **ZERO mutation.** 1 new file (this one).

---

## §0. Headline — the freeze broke, and it broke by adding a MUST the corpus does not meet

The target had been byte-frozen since `eedd36fc` (2026-06-28) and §A/§C-clean for **six
consecutive deltas**. Both streaks end here.

```
$ git log -1 --format='%H %ad %s' --date=short -- web4-standard/core-spec/security-framework.md
afd04623 2026-08-10 docs(standard): fold hackathon findings into canonical Web4 text (#678)
$ git rev-parse afd04623^:web4-standard/core-spec/security-framework.md \
                afd04623:web4-standard/core-spec/security-framework.md
2880e643f4d7b9899dca38d97dee3358b0f38237
63889457512ac7b9f1511310ea208bcd7aebfb99
$ git show --numstat afd04623 | grep -E '^[0-9]'
5	2	web4-standard/core-spec/errors.md
36	0	web4-standard/core-spec/security-framework.md
9	3	web4-standard/submission/draft-web4-core-00.xml
```

`afd04623` touched **three** files, and this lineage is implicated in **two** of them:
the target (+36/−0, 97 → 133 lines) and `submission/draft-web4-core-00.xml`, which is
the **C336-N1 locus**. (`errors.md` was adjudicated one slot ago at C374 — not re-opened
here.) It is the same commit that broke the errors freeze; a single upstream edit has now
ended two 8-pass freezes in three days.

The +36 lines are **three** normative blocks, all MUST/SHOULD-bearing, none of which
carries a single cross-reference:

| Block | Lines | Governs an object owned by |
|---|---|---|
| §2.2 multi-device custody classes | 76–81 | `core-spec/multi-device-lct-binding.md` |
| §3.1.1 Composed Actor Provenance | 98–112 | ACP, R7, `referenced-acts.md` |
| §3.1.2 Multi-Device and Quorum Assurance | 114–125 | `core-spec/multi-device-lct-binding.md` |

**Cross-reference density, published as a within-file denominator:** the 97 pre-existing
lines carry **4** cross-references to sibling specs (`web4-handshake.md` §6.0.3 at :50 and
§6.0.4 at :55; `LCT-linked-context-token.md` §7.3 at :85; `web4-handshake.md` §6.0.5/§9/§6.1
at :96). The 36 new lines carry **0** — and the zero is robust, because the matcher run over
the new blocks was the *broader* one:

```
$ for r in 76,81 98,112 114,125; do
    sed -n "${r}p" core-spec/security-framework.md | grep -cE "\.md|§[0-9]|Section [0-9]"; done
0    # §2.2 custody block
0    # §3.1.1 Composed Actor Provenance
0    # §3.1.2 Multi-Device and Quorum Assurance
$ sed -n '1,75p;82,97p;126,133p' core-spec/security-framework.md | grep -cE "\.md"
4
```

The file's own convention is to route; the new text does not.

---

## §A. Findings inside the target

### N1 — [MED, + DESIGN-Q] §3.1.2 ratifies an assurance MUST that no artifact in the corpus satisfies, and the one mechanism it names recomputes its own threshold downward

**Charge, stated precisely.** §3.1.2:119 (new, 3 days old):

> - A design in which one device holds the relying-party credential key and peer devices
>   merely approve its use MAY be useful, but it **MUST be identified as policy quorum
>   rather than cryptographic quorum** unless the key operation itself cannot complete
>   without the required peers.

The corpus has exactly one multi-device quorum mechanism — `recovery_quorum`, owned by
`core-spec/multi-device-lct-binding.md` (78 `recovery_quorum` hits repo-wide). It is
**identified as neither**:

```
$ git grep -in "policy quorum\|cryptographic quorum" -- . | grep -v docs/audits
web4-standard/core-spec/security-framework.md:116
web4-standard/core-spec/security-framework.md:119
```

Two hits, **both the clause itself**. The distinction the MUST creates has zero
instances outside the sentence that creates it.

**The two documents do not know about each other.** Neither filename appears in the
other; `m-of-n` occurs **2 times in `web4-standard/`**, both inside the 3-day-old text,
and **0 times** in the spec that owns `recovery_quorum`. (Scope stated deliberately: the
token also appears in `archive/reference-implementations/`, `private-context/moments/`
and `whitepaper/PUBLISHER_CONTEXT.md` — 9 lines / 5 files repo-wide. The
`web4-standard/` denominator is the load-bearing one.)

**The threshold moves down on its own — executed, antecedent-true.** §3.1.2:120:

> - If fewer than `m` required devices are available, implementations MUST NOT silently
>   reduce the threshold while presenting the result as the same credential or assurance
>   level.

```
$ cd web4-standard/implementation/sdk && python3 - <<'PY'
from web4.binding import (DeviceConstellation, DeviceRecord, DeviceStatus, AnchorType,
                          HardwareAnchor, enroll_device)
a = HardwareAnchor(anchor_type=AnchorType.TPM2)
c = DeviceConstellation(root_lct_id="lct:web4:root:XYZ")
for i in range(5):
    enroll_device(c, f"dev-{i}", a, [] if i==0 else ["dev-0"], "2026-01-01T00:00:00Z")
print("built:            active=%d  recovery_quorum=%d" % (c.device_count, c.recovery_quorum))
m = c.recovery_quorum
for d in c.devices[:3]:
    d.status = DeviceStatus.SUSPENDED      # §2.4 status, multi-device-lct-binding.md:289
print("3 suspended:      active=%d  recovery_quorum=%d  -> fewer than m available? %s"
      % (c.device_count, c.recovery_quorum, c.device_count < m))
enroll_device(c, "dev-new", a, ["dev-3"], "2026-08-13T00:00:00Z")   # binding.py:304
print("enroll 1 device:  active=%d  recovery_quorum=%d  root=%s"
      % (c.device_count, c.recovery_quorum, c.root_lct_id))
print("fields available to record assurance:", list(c.__dataclass_fields__))
PY
built:            active=5  recovery_quorum=3
3 suspended:      active=2  recovery_quorum=3  -> fewer than m available? True
enroll 1 device:  active=3  recovery_quorum=2  root=lct:web4:root:XYZ
fields available to record assurance: ['root_lct_id', 'devices', 'recovery_quorum']
```

Threshold **3 → 2 while fewer than `m` were available**, same `root_lct_id`, via
`binding.py:304`. The clause's antecedent is true and the prohibited effect fires.
`DeviceConstellation` has **three** fields — there is nowhere to record an assurance
level even in principle:

```
$ git grep -in assurance -- web4-standard/implementation web4-standard/schemas web4-standard/test-vectors
(no output)
```

**The recompute has no spec authority.** The spec's own §3.5 reference implementation
(`multi-device-lct-binding.md:711-769`) has six steps; step 6 recomputes
**`constellation_trust`**, not `recovery_quorum`:

```
$ grep -n "recompute\|Recompute" web4-standard/core-spec/multi-device-lct-binding.md
767:    # 6. Recompute constellation trust
$ grep -n "recovery_quorum" web4-standard/core-spec/multi-device-lct-binding.md
203:    "recovery_quorum": 2,          # stored field in the constellation JSON
728: / 730:                            # READ, in the §3.5 quorum test
782: / 788:                            # READ, in the §3.6 recovery test
978: / 986:                            # §5.2 default_recovery_quorum(device_count) formula
```

Every spec site **reads or defines**; none assigns on membership change. `binding.py:304`
and `:352` (`constellation.recovery_quorum = default_recovery_quorum(constellation.device_count)`)
are an **SDK behaviour with no normative source** — in a module whose docstring (`:4`)
names `multi-device-lct-binding.md` as its authority.

**The counter-reading, printed rather than suppressed.** §5.2 defines
`default_recovery_quorum` as a pure function of `device_count`, so one can argue the SDK
is *maintaining an invariant* ("quorum is by definition half the devices"), not
*reducing a threshold*. That reading is coherent, and it is exactly why this is
**DESIGN-Q and not a defect report**: the corpus holds two incompatible readings of
`recovery_quorum` — a **stored field** (spec §2 JSON `"recovery_quorum": 2`; spec §3.5/§3.6
read it) versus a **derived function of live membership** (spec §5.2 formula; SDK assigns
it). Both readings were tenable and harmless until 2026-08-10. §3.1.2:120 makes the
difference load-bearing, because under the derived reading the threshold tracks membership
downward with no visible assurance change — the precise effect the clause forbids.

**Bounds published honestly.** Via `remove_device` the recompute floors at 2 (removing the
4th of 4 active devices needs 2 authorizing remaining actives, and only 1 remains), so the
observed reduction is 3 → 2, not 3 → 1. But `DeviceConstellation.recovery_quorum` defaults
to **`1`** (`binding.py:198`) for any constellation built by direct construction rather
than through `enroll_device`, and at `m = 1` §3.1.2:118's `m > 1` guard is vacuous.

**Deliberately NOT charged (disclosed at the point of use).** `remove_device`'s quorum
test (`binding.py:338-340`) intersects `authorizing_devices` — **bare ID strings** — with
the active set and counts, with no signature verification, while the spec's §3.5 steps 2/3/5
(`device.sign_removal_request`, `society.process_device_removal`,
`broadcast_compromise_alert`) have no SDK counterpart. This is **disclosed** at
`binding.py:17-19`: *"This module provides DATA STRUCTURES and pure-function computations.
Actual cryptographic operations … are out of scope."* Per the standing rule, disclosed
inertness is not charged. It is recorded because it is what makes the design *policy*
quorum in §3.1.2:119's sense — which is the charge above.

**Remedy forks — do NOT self-apply.** (i) delete the `:304`/`:352` recompute and treat
`recovery_quorum` as stored; (ii) keep the recompute and add an assurance/threshold-history
field plus the §3.1.2:119 identification; (iii) amend `multi-device-lct-binding.md` §3.5/§5.2
to state which reading is normative. (iii) edits a *frozen* target of another lineage.
→ **operator, with the multi-device owner.**

### N2 — [MED] §3.1.1 introduces a fourth provenance vocabulary, and it is unsatisfiable on both schema-enforced envelopes

**Charge.** §3.1.1:102 states a MUST and then a hedged SHOULD:

> When software or another member acts on behalf of a principal, a consequential session
> or act **MUST preserve the identities as distinct fields** rather than collapsing them
> into one signer. The authenticated envelope **SHOULD** bind, **as applicable**:
> `principal` · `actor` · `via_device` · `office` · `authority`

(The field list is SHOULD + "as applicable" — stated exactly, because the MUST is
field-name-agnostic and only the *distinctness* is mandatory. :110's second MUST is
likewise name-agnostic.)

**Web4 already had three vocabularies for this exact problem, in the same `core-spec/`
directory, none referenced by §3.1.1:**

| # | Vocabulary | Locus | Enforcement |
|---|---|---|---|
| 1 | `principal` + `agent` | `core-spec/acp-framework.md:43` | **required** in `schemas/acp-jsonld.schema.json` `$defs/AgentPlan`; bundled into `sdk/web4/schema_registry.json:188`; test vectors |
| 2 | `role: {actor, roleLCT}` | `core-spec/r7-framework.md:69` | **required** in `schemas/r7-action-jsonld.schema.json` `/properties/role` |
| 3 | `actor_lct` vs envelope signer | `core-spec/referenced-acts.md:60-62` | conformance vector + `sdk/tests/test_conformance.py` |
| 4 | `principal`/`actor`/`via_device`/`office`/`authority` | `core-spec/security-framework.md:104-108` | **none** |

Vocabulary 3 is the sharpest, because it already *solves* §3.1.1's stated problem:

> `referenced-acts.md:60-62` — "The **actor** (`actor_lct`, the *from*) rides in the Act
> payload. The ledger envelope's signer MAY differ: … the machine/track LCT signs the
> envelope while a short-lived arc-LCT is the `actor_lct`."

That is composed actor provenance, ratified, with a distinct token set, and §3.1.1 does
not cite it.

**The instrument: a positive impossibility, run against a backed control.**

```
$ cd web4-standard && python3 - <<'PY'   # jsonschema, §3.1.1 field set injected
R7  (r7-action-jsonld.schema.json — additionalProperties:false at top level AND /properties/role)
  CONTROL  backed vector r7-valid-001                  PASS
  CASE 1   §3.1.1 fields inside role                   FAIL  Additional properties are not allowed
                                                             ('authority','office','principal','via_device')
  CASE 2   §3.1.1 fields at top level                  FAIL  Additional properties are not allowed
                                                             ('actor','authority','office','principal','via_device')
ACP (acp-jsonld.schema.json)
  CONTROL  backed vector acp-valid-001                 PASS
  CASE 3   §3.1.1 fields at top level                  FAIL
PY
```

The controls pass; that is what makes the failures admissible. **§3.1.1's SHOULD-bind is
unsatisfiable on either schema-enforced Web4 envelope without a schema change** — not
merely unimplemented.

**Absence counts, for reach (secondary to the control above):** `via_device` = **4 lines
repo-wide** — 2 in the target, 2 in `whitepaper/PUBLISHER_CONTEXT.md` commentary *about*
the target; zero independent uses. `git grep -nw office -- schemas implementation
test-vectors` = **0**.

**The token collision, stated at its defensible strength.** R7's schema documents `actor`
as *"Entity LCT ID of the actor"* — it does not say principal or deputy. §3.1.1:105 fixes
it as *"the harness, application instance, agent, or member that actually performs the
act"*. So the charge is **same token, underspecified referent, with a live consequence**,
not "opposite referent": under either reading `r7-framework.md:414`
(`entity_lct = r7_action.role.actor`) feeds `:533` and `:548`, attaching T3/V3 to whatever
`role.actor` holds — and R7 has **no `principal` slot** to move reputation to if `actor`
becomes the harness. `r7-framework.md:580` declares reputation/settlement determinism
across implementations; an implementer applying §3.1.1's MUST to an R7 action has no
conformant place to put the principal.

→ **operator / author ruling**, jointly with the ACP, R7 and `referenced-acts` owners.
Reconciliation is a vocabulary decision, not a measurement.

*Routed out, not charged here:* `testing/conformance/r6-r7-actions.json:20` spells the R7
role fields `actor_lct`/`role_lct`, while `schemas/r7-action-jsonld.schema.json:87` requires
`actor`/`roleLCT` under `additionalProperties:false`. → **R7 lineage.**

---

## §B. C336 carries — pre-registered, all three discharged

### B.1 — C336-N1: one limb of three discharged; two stand, and limb 3 is worse than charged

| Limb | C336 charge | Status at HEAD |
|---|---|---|
| 1 | `draft-web4-core-00.xml:256` KEM cell = `P-256` (the pre-remediation cell `C31-B-H1` fixed in `130069d8`) | **DISCHARGED** — `<c>P-256</c>` → `<c>ECDH-P256</c>`, matching canon `:17` exactly |
| 2 | `draft-palatov-web4-core-00.txt:618-619` = `AES-256-GCM` / `SHA-3-256` | **STANDS**, byte-identical |
| 3 | `submission/web4-rfc.md:280/286/465` = crypto with no suite vocabulary | **STANDS — and is understated** |

Limb 3 is not merely missing vocabulary; it **inverts modality**:

```
web4-rfc.md:278  "Web4 implementations MUST support the following key exchange algorithm:"
web4-rfc.md:280  "-  **ECDH with P-256:** ..."         ← canon: SHOULD-tier W4-FIPS-1
web4-rfc.md:284  "Web4 implementations MUST support the following symmetric encryption algorithm:"
web4-rfc.md:286  "-  **AES-256-GCM:** ..."             ← canon has NO AES-256-GCM at all
```

`security-framework.md:16-21` makes `W4-BASE-1` (X25519/ChaCha20-Poly1305) the sole MUST
and `W4-FIPS-1` a SHOULD. The outward artifact promotes the SHOULD tier to MUST and mandates
an AEAD the standard does not define.

**NEGATIVE — the W4IDp half of `afd04623` is correct.** The commit added `L=16` to the xml's
derivation. Verified against canon `protocols/web4-handshake.md:31-40` (identical
`salt`/`IKM`/`info`/`L=16` block, with the same rationale sentence) and against
`implementation/reference/web4_demo.py:38` (`hkdf_sha256(prk, b"W4IDp:v1", 16)`). **The fix
is right.** Recorded so the next pass does not re-mine it.

**Retirement marker: CONFIRMED ABSENT.**
`git grep -in "retired\|superseded\|deprecat\|do not use\|historical" -- web4-standard/submission/`
→ empty. The movement is in the **opposite** direction: `afd04623` re-dated the xml
`<date year="2026" month="August" day="9"/>` (was `2025/January/11`).

**The re-dating's real significance is not expiry — it is a source/render desync.**
`SUBMISSION_GUIDE.md:28` declares the txt is *generated* from the xml
(`xml2rfc --text --html draft-web4-core-00.xml`). The two checked-in artifacts are
therefore a source/render pair, and they now disagree on **five** points: document date
(2026-08-09 vs "September 15, 2025"), expiry ("March 15, 2026", already lapsed), and the
three crypto values of limb 2. The checked-in txt is **no longer a render of the checked-in
xml**. This is a stronger and more mechanical charge than C336's expiry framing, and it
*explains* limb 2: the txt was never regenerated.

*(C336's own "I-D expiry has passed" mitigation is now inert as framed — it was quoted off
the **txt**'s expiry, while the re-dating applies to the **xml**, which is the one limb that
was fixed and whose remaining suite cells — `X25519 / Ed25519 / ChaCha20-Poly1305 /
AES-128-GCM / SHA-256` — are all concordant with canon. No surviving xml divergence for the
removed mitigation to attach to.)*

### B.2 — B-7 re-measured: **12 occ / 11 lines / 10 files / 6 forms**

Pattern re-run verbatim as pre-registered by C336 (`--include=*.md` stays dropped;
reversed/bare/prose alternatives retained), over `web4-standard/` minus `docs/audits`:

```
5 × ECDH-P256      core-spec/security-framework.md:17, :35 · sdk/web4/security.py:117
                   test-vectors/security/security-primitives.json:28 · submission/draft-web4-core-00.xml:256
2 × P-256ECDH      profiles/cloud-service-profile.md:19 · core-spec/core-protocol.md:19
2 × ECDH with P-256  submission/web4-rfc.md:280 · core-spec/security-framework.md:35 (gloss)
1 × P-256 ECDH     registries/initial-registries.md:6
1 × P-256EC        protocols/web4-handshake.md:23
1 × ECDH P-256     submission/draft-palatov-web4-core-00.txt:617
```

**C336's published "7 forms" was correct at its head** — verified:

```
$ git grep -hoE "$PAT" afd04623^ -- web4-standard/ | sort | uniq -c
4 ECDH-P256 · 2 P-256ECDH · 2 ECDH with P-256 · 1 P-256 ECDH · 1 P-256EC · 1 >P-256< · 1 ECDH P-256   (12)
```

The delta is exactly the retired form `>P-256<` ×1 → `ECDH-P256` (4→5). **This is
target-moved, not auditor overcounting**, and `>P-256<` is precisely the alternation limb
C336 added to catch the xml cell that `afd04623` then fixed. `submission/` divergent forms
3 → 2.

### N3 — [LOW, instrument] three of B-7's four published numbers cannot detect B-7's own remediation

Occurrence (12), line (11) and file (10) counts are **invariant under a spelling
correction** — only the form count moved (7 → 6). A metric that cannot register its own
remedy is a change-detector that fails closed. Pair it with the number that *does* carry
signal: **`ECDH-P256` is 5 of 12 — the canonical form is still a minority; 7 of 12 sites
divergent.**

### B.3 — the sibling set re-derived, and the natural instrument is blind to limb 3

C336's mandate: *"re-derive the 13-artifact set AGAIN — two consecutive passes have now
found the inherited set wrong (C296 7→9, C336 9→13)."* Re-derived rather than re-read:

```
$ grep -rIl "W4-BASE-1\|W4-FIPS-1" web4-standard/ --exclude-dir=docs | wc -l
20
```

Nine artifacts absent from C336's admitted set surface here — `implementation/reference/`
{`web4_demo.py`, `web4_reference_client.py`}, `implementation/sdk/`{`web4/security.py`,
`CHANGELOG.md`, `tests/test_protocol.py`, `tests/test_security.py`},
`test-vectors/protocol/core-protocol.json`, `QUICK_REFERENCE.md`, `INTEGRATION_STATUS.md`
— though several only *reference* a suite ID rather than defining a suite, so 20 is the
token denominator, not the authority set.

**The finding is the other direction.** Two artifacts C336 admitted are **missing** from
this sweep: `submission/draft-palatov-web4-core-00.txt` and `submission/web4-rfc.md`.
They define Web4 crypto and name **no suite ID at all** — which is limb 3's entire charge.
**A suite-ID token sweep is structurally blind to exactly the artifacts whose defect is the
absence of suite vocabulary.** Three passes have now found the inherited set wrong
(7→9→13→?) and this is the mechanism: the cheapest instrument has a hole shaped like the
finding. **Any future re-derivation MUST run the suite-ID sweep *and* a primitive-name
sweep (`X25519|Ed25519|ChaCha20|AES-...-GCM|SHA-256`) and publish the set difference.**

### B.4 — guards re-tested, unchanged

`hub/` M3-DECLINE **holds** (no `security-framework.md` citation, no suite-ID token, no
conformance claim among its 13 changed files). `web4-trust-core/` and `web4-policy/`
M1-FAIL hold — 0 commits in window. C336-N2's per-locus B-10 split is carried forward
verbatim and is **not** re-typed as an unqualified 8-site normalization. `initial-registries.md`
B-A6 not re-opened. SDK suite: `pytest tests/test_security.py -q` → **67 passed**; full
suite → **2750 passed, 5 xfailed**.

---

## §C. Deferral ledger — pre-registered for **C416**

| # | Row | Trigger to check first |
|---|---|---|
| 1 | N1 remedy fork | Has `binding.py:304`/`:352` changed, or has `multi-device-lct-binding.md` §3.5/§5.2 declared which reading of `recovery_quorum` is normative? **If the recompute is deleted without an assurance field, check whether §3.1.2:119's identification was added — silently taking fork (i) is itself the next finding.** |
| 2 | N2 vocabulary | Does any of the four vocabularies cite another? Do `schemas/r7-action-jsonld.schema.json` / `acp-jsonld.schema.json` gain the §3.1.1 fields? Re-run the control pair — **the CONTROL passing is what makes the failures admissible.** |
| 3 | C336-N1 limbs 2+3 | Was the txt regenerated from the xml (`xml2rfc`)? Compare the date line first — it is the cheapest desync tell. |
| 4 | §2.2 custody block | **Never audited.** :81 *"stale replicas MUST NOT restore authority to a revoked device"* has no counterpart in `multi-device-lct-binding.md` §3.5; the SDK has no replication surface at all. Charged nowhere yet — first work for C416. |
| 5 | B-7 | Publish **all four** numbers; only the form count can move on a spelling fix. Baseline: 12 / 11 / 10 / **6**. |
| 6 | Sibling set | Run **both** sweeps and publish the set difference (§B.3). |
| 7 | `submission/` retirement | Still absent; the xml is now dated 2026-08-09 (expires 2027-02-09), i.e. maintained. |

---

## §D. Accountability self-audit

```
surface: C376 audit document   act: emit an audit finding on canonical spec text
S: low/reversible [construct: docs/audits/*.md, no executable consumer, ZERO mutation]
R: n/a [construct: no caller-reachable path created]
W: pass [construct: signed commit on worker/web4-20260813-060000; PR review by a separate track]
O: pass [construct: policy review (Step 4) before any file written]
A: pass [construct: every claim carries the command that produced it; refuted premises
   recorded in §E rather than deleted]
V: present [construct: reviewer track may reject; all remedies routed to operator, none self-applied]
verdict: PASS
```

## §E. Own-error record

Policy review **falsified the headline** and corrected three further claims. All
corrections were re-verified before adoption; recorded because deleting them would make
the method look better than it was.

1. **P1's charged case did not satisfy the clause's antecedent.** I charged a 5-device
   constellation losing one device: 4 available, `m`=3 — §3.1.2:120's *"if fewer than `m`
   required devices are available"* is **false**, so the clause did not cover the scenario.
   The reviewer built the antecedent-true instance (suspend to below `m`, then enroll);
   §A.N1 charges that one. **The overstatement and the true finding pointed the same
   direction**, which is exactly why executing it — rather than reasoning about it — was
   what caught it.
2. **"No signature verification" was a disclosed-inertness charge** — `binding.py:17-19`
   discloses it at the point of use. Dropped as a charge, retained as the *reason* the
   design is policy quorum.
3. **"§3.1.1 *requires* five fields" was overstated** — :102 reads "SHOULD bind, as
   applicable". Restated; the MUST is field-name-agnostic.
4. **"Same token, opposite referent" was overstated** — R7's schema says only "Entity LCT
   ID of the actor". Restated as *underspecified referent with a live consequence*.
5. **"`m-of-n` = 2 repo-wide" was mis-scoped** — 2 is the `web4-standard/` count; repo-wide
   is 9 lines / 5 files. Scope now stated.
6. **A reviewer correction I checked and had to correct back:** the occurrence count did
   **not** move — it is still 12 (`security-framework.md:35` carries two matches on one
   line). C336's "7 forms" was right at its head, and framing it as overcounting would
   have libelled a correct measurement. **A number that disagrees with a predecessor's is a
   question, not a verdict.**
7. **The reviewer found what I had not looked for**: `referenced-acts.md:60-62` — a
   *fourth* provenance vocabulary that already solves §3.1.1's problem. Four beats two.

**Method carry (v54): a new MUST is an audit surface the moment it lands — and the first
thing to test is whether its own antecedent is reachable.** §3.1.2 was ratified 3 days
before this pass and is violated by the corpus it governs, but the naive violation case
does not satisfy the clause's `if`. Ratifying a requirement retroactively converts every
existing implementation into a conformance question; the clause's *guard* is where the real
work is, not its *prohibition*. Corollary: when a spec adds normative text that governs
objects owned by other specs, **measure the cross-reference density against the file's own
convention** — 4 in 97 lines versus 0 in 36 is a stronger signal than any single missing
citation, and it is what led to all three of N1, N2 and B.3.
