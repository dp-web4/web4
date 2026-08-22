# Witness Roster & Id Bridge — specification (R1)

**Node:** M-CIT-3 (witnessed genesis, sibling co-sign via canonical roster) — roster half.
**Owner:** HUB. **Thread:** `sage-web4-citizenship`.
**Status:** normative for the implementing change. **Not yet implemented** — nothing
in this document is shipped code; it is the contract the roster PR is written against.
**Anchor commit:** every line/behaviour cited below was read or executed at web4
`8088a512` unless stated otherwise.

---

## 0. Scope, and the honest bound on everything below

`CitizenshipRecord::verify_quorum` (`web4-core/src/attestation.rs:185`) has **no
production caller** at `8088a512`. Nor does anything above it: its only non-test
call site is `BirthCertificateRef::verify` (`attestation.rs:241`), reached only
from `Lct::verify_citizenship` (`lct.rs:455`), whose only callers are web4-core's
own tests. In `hub/` the three mentions are doc comments on resolver-shaped
helpers (`hub-lib/src/state.rs:2082`, `:2254`, `hub-daemon/src/rest.rs:11907`).

So the attacks enumerated in §4 are **properties of the closure a future check-5
verifier would hand `verify_quorum`** — preconditions on this spec, not a live
incident. That is also why the check-5 verifier does **not** ship ahead of the
R3′ canon call (§9): shipping the caller is what makes these reachable.

**What this spec covers:** the resolver a quorum check is handed — how a witness
label (`lct:web4:mb32:…`) becomes a `PublicKey`, and what must be true of the
structure that answers.
**What it does not cover:** the check-5 verifier itself, the birth-certificate
producer, and the R3′ rotation question. Those are named where they gate.

---

## 1. The defect this node exists to close

```
web4-core/src/attestation.rs:186   F: Fn(&str) -> Option<PublicKey>   // "lct:web4:mb32:…"
hub/hub-lib/src/envelope.rs:242    pub struct MapResolver(pub HashMap<Uuid, Lct>);
hub/hub-lib/src/envelope.rs:238    fn lookup(&self, lct_id: Uuid) -> Option<Lct>;
```

`verify_quorum` holds a **derived label**. The live resolver is keyed on the
**local `Uuid`**. There is no `Uuid` to hand it, and every caller of `lookup`
(`rest.rs:2899, 3679, 4557, 4605, 8863`) passes one. An earlier instruction of
mine — *"ask the resolver, not `member_pubkeys`"* — told the roster to call a
function whose argument it cannot construct.

**The roster is that missing index.** Not a new store, not a new trust source:
the map from derived witness label to an identity the hub has already admitted.

---

## 2. Normative — where the roster is sited

**R-1. The roster resolves over the resolver's three-source union, not over a
`HubState` projection.** `RestState::new` (`rest.rs:~334-385`) already builds it:

| source | site | via |
|---|---|---|
| Sovereign | `rest.rs:355` `resolver.insert(sl.clone())` | `SovereignMode::Hestia { pubkey_hex }` or `IdentityFile` |
| `member_pubkeys` | `rest.rs:357-365` | `hestia_sovereign_lct` |
| `council_pubkeys` | `rest.rs:377-385` | `hestia_sovereign_lct` |

A roster keyed on `member_pubkeys` alone declares the two **most**
admission-gated classes in the society — the founding Sovereign and every
council holder — permanently unkeyed. Measured: web4 #759 (merged), cases C8/C9.
Against `BIRTH_WITNESS_QUORUM = 3` over ~9 members that is plausibly the
difference between reaching quorum and never reaching it.

**R-2. The bridge derives FORWARD; it does not walk the registry backward.**
The label→key map is built by deriving `derive_lct_id(pk)` from keys already in
the union, never by `registry[witness].document.id → member_pubkeys[uuid]`.
Measured against #759's own fixtures in web4 #761: the forward derivation
dissolves C9 (a `.chain()`), C10 (mixed-case pin — the path contains no string
comparison that case can break; `derive_lct_id` consumes a `PublicKey` that
`hex::decode` already normalized) and C11 (`document.id` is not on the path, so
the convention it depends on cannot be violated). It also fixes a **reachability**
gap: `hestia_sovereign_lct` synthesises an `Lct` with `binding_proof: None`, and
registry ingest is fail-closed on exactly that absence — so under the backward
bridge a member keyed only through the hub's own synthesis could never witness,
ever. Under the forward derivation, admission alone suffices.

**R-3. Soundness is unchanged, and says so out loud.** The map is built from
**pins**, never from the registry. Publishing is not admission; three self-issued
publishes buy nothing; a quorum still costs three admissions. The registry hop
carried two things and both are supplied elsewhere: proof of possession (the
witness signs the attestation — `attestation.rs:195`), and revocation
(`MemberRemoved → member_pubkeys.remove`, `state.rs:663`;
`CouncilMemberRemoved → council_pubkeys.remove`, `state.rs:981` — the pin map is
the live admission set). **Revocation is only real if eviction reaches every
index**, which is why §3 is blocking rather than a cleanup.

**R-4. Namespace: one resolver, one answer.** The derivation produces only
`lct:web4:mb32:…`. A `lct:web4:member:{uuid}` witness string resolves to `None`
under both the old bridge and the roster — a negative control, not a regression.

**R-5. `lock_gate` is stated, not left to inference.** "The roster is the
resolver" plus "the LOCKED resolver has no Sovereign key" (`rest.rs:~320-332`)
reads as a hole until the reader knows the LOCKED arm does no verification by
construction. A spec that leaves that inference to the reader has shipped the
hole in the reader's head. Say it in the implementing doc comment too.

---

## 3. Normative — the index clause (ONE clause, three parts, not severable)

The O(n) forward walk cannot desynchronize: it has no second store. The moment
the index buys O(1) — and it should; the walk is `hex::decode` + point
decompression + `sha256`, per lookup, times n, times 3 witnesses — the eviction
discipline stops being a cleanup and becomes the only thing between "sited at
`insert`" and an ejected member who keeps voting. **The optimization is what
creates the need for the precondition, so they ship as one clause and cannot be
adopted apart.**

`Lct::lct_id()` (`web4-core/src/lct.rs:377-380`) states the invariant the index
is a deliberate exception to:

> "Computed from the binding public key on demand — **never stored separately, so
> it cannot drift from the key it is derived from.**"

An index is allowed to store it separately. That is precisely why the eviction
discipline must be written beside it rather than assumed.

### (a) — BLOCKING. `insert` evicts the prior entry's derived key before overwriting.

```rust
if let Some(prior) = self.0.get(&lct.id) {
    let stale = derive_lct_id(&prior.public_key);
    self.index.remove(&stale);
}
self.index.insert(derive_lct_id(&lct.public_key), lct.id);
self.0.insert(lct.id, lct);
```

**Re-key is a mutation that removes nothing.** `pin_member_key` (`rest.rs:5297`,
routed at `5425`) says so about itself: `insert` replaces the prior entry for
this LCT id. The `Uuid` index is keyed on the thing re-key does *not* change; a
derived index is keyed on the thing re-key *does* change. So no `remove` is ever
called and a reviewer looking for a missing one finds none. Measured before the
fix: after a single re-key the derived index holds **2** entries for one member,
and the rotated-away label still resolves to them.

The test that exists today — `pin_member_key_rotates_the_live_resolver_without_restart`
(`rest.rs:10255`) — asserts `resolver.0[&member].public_key` before and after
(`10263`/`10268`). It is true, it is green, and it is blind to this.

### (b) — BLOCKING. The index maps `derived_id -> Uuid`. Never a cloned `Lct`.

This is **not** a blast-radius bound. It is the whole refusal on one attack, and
the flavour that stores a clone is dominated on every row of §4.

- `derived_id -> Uuid`: the second hop is a live lookup into `.0`. A stale label
  resolves to a member whose entry now holds the **current** key, or to nothing
  at all if that member is gone. Fail-closed in both directions.
- `derived_id -> Lct`: the clone keeps **rotated-away key material live for the
  life of the process**, and an ejected member's key live forever. An attestation
  signed by either verifies and counts toward a birth quorum.

The clone spelling also **answers R3′ by cache layout**, on a path dp never sees
— "a conferred birth survives a witness key rotation, and the rotated-away key
still signs it" decided by a data-structure choice nobody would flag in review.
That is not dp's call being prejudiced at the margin; it is dp's call being made
by an implementation detail. One copy of key material: the index is an index, not
a second store.

### (c) — HYGIENE (deliberately downgraded). The index lives behind `insert`/`remove`, `.0` private.

This was originally blocking; **(b) is what downgrades it.** With (b) taken, an
un-evicted removal leaks index entries that resolve to `None` — a memory
question, not a citizenship one. Encapsulation still belongs in the same change,
because the two production reach-through sites are how the removal attack got
here at all:

- `rest.rs:3019` — `vci_credential`, the reverse scan over `.0.values()`.
- `rest.rs:5331` — `remove_member_live`, `s.resolver.write().await.0.remove(&…)`.

Site count independently verified twice, and by enumeration rather than by
grepping for `resolver`: an aliased reach-through (`let r = …read().await;` then
`r.0.…`) is invisible to that grep, and `rest.rs:3019` **is** such a line. Every
`.0.{remove,insert,values,get,iter,entry,contains_key,…}` in `hub-daemon/src`,
`hub-lib/src` and `hub-plugin` was checked at its binding; everything else is
tests or `law.0`.

---

## 4. The invariant, and why its two directions are not the same requirement

**The derived index must be a bijection onto the live member set.**

Every distinct label the index resolves is a vote: `verify_quorum` dedups on the
label (`BTreeSet<String>`, `attestation.rs:189`), so **the index's key-set
cardinality is the quorum count**. The label is doing that work while being
unauthenticated — see §5.

The word "bijection" has two directions and **they fail with opposite sign**. A
spec that says it undifferentiated makes the next reader budget equal alarm for
both and spend it in the wrong place.

- **Surjectivity fails toward CONFERRAL** — a label in the index with no live
  member behind it is a vote for a member who is gone or a key that is retired.
  This is the citizenship failure. (a) preserves it across overwrite; (b) makes a
  violation fail-closed instead of vote-bearing.
- **Injectivity fails toward DENIAL** — and is **unenforced by design, currently
  harmless**. `derive_lct_id` is a function of the public key alone
  (`lct.rs:370`), so two members admitted under one key share a label and the
  index holds one entry for two live members; (a) does not catch it, because (a)
  looks for a prior entry under the same **uuid** and finds none. Measured
  consequence: the collision is **not vote-bearing**. Three declared witnesses
  count as two — the loser of the collision is denied their own vote, the winner
  gets exactly one. An availability failure. The O(n) roster refuses it for the
  same reason, so this is a property of `derive_lct_id` + the label dedup, **not
  of the cache**, and no index discipline can fix it.

### The attack table

Three attacks, one member each, all reachable on one roster. A — a rotated-away
key votes. B — one member is a quorum (they declare three of their own historical
labels). C — an ejected member votes (`remove_member_live` reaches through `.0`
and evicts nothing; clause (a) is sited at `insert` and never runs on this path).

| roster shape | A | B | C |
|---|---|---|---|
| `O(n)` derivation, no index | refused | refused | refused |
| index `-> Uuid`, no eviction | refused | **CONFERRED** | refused |
| index `-> Lct`, no eviction | **CONFERRED** | **CONFERRED** | **CONFERRED** |
| **`-> Uuid` + evict-on-insert (this spec)** | **refused** | **refused** | **refused** |
| `-> Lct` + evict-on-insert | refused | refused | **CONFERRED** |

Two things this table settles:

1. **`-> Lct` refuses nothing `-> Uuid` does not also refuse.** Dominated, not
   complementary — so there is no trade to bound, and (b) is blocking.
2. **The clauses do not cover each other's row.** (a) is what closes A and B, and
   it closes them under *either* flavour; (b) is the whole refusal on C, the row
   (a) is not sited on. Neither is redundant.

**Attack B has two spellings and the attacker picks after seeing the index.** The
rotating member called `/member/:id/key` twice; they **generated** the keys they
rotated away from and nothing takes the private halves out of their hands. Sign
each stale label with the key it derives from, and the clone flavour confers;
sign all three with the current key, and the `-> Uuid` flavour resolves them all
to a key that signed only one. Each flavour refuses one spelling and confers the
other — which is why a fixture that fixes the signing key measures a per-spelling
refusal and reports it as a per-flavour one.

---

## 5. Why the index is the *only* binding in the path

`Attestation::message` (`attestation.rs:71`) is
`"web4:lct:attestation:v1\n{subject}\n{type}\n{ts}"`. **It does not cover the
witness id.** Two attestations bearing different witness labels, signed by one
key, have identical signature bytes.

So the label is an unauthenticated free variable. The index is not a lookup that
`verify_quorum` consults on the way to a decision — **the index is the only thing
in the path that binds a label to a key at all**, and (per §4) its key-set
cardinality is the quorum count. Every clause in §3 is protecting that one
structure.

---

## 6. Normative — how an id is checked

**R-6.** Where a key resolves, the check is `derive_lct_id(pk) == id`. **Total.**
The syntactic predicate adds nothing and MUST NOT be substituted for it.
Re-derivation *authenticates*; a predicate only *narrows*. Registry ingest Check
3 (`rest.rs:7631`) already says it: "the publisher's label is never trusted; the
key is the identity." A bool-returning `is_canonical_lct_id` reads as sufficient
next to it — a weaker check reached for because its name implies an ordering that
does not hold.

**R-7.** Where no key resolves, the syntactic predicate is the check, and its
result is **"not refused", never "authentic"**. It is *a refusal, not a
translation*, and it is *syntactic*.

**R-8. "Not refused" is not durable.** A subject admitted unkeyed MUST be re-asked
when a key later resolves for it. Otherwise the weak answer is recorded as a fact
and never revisited — the same shape as R-6, one layer down, at storage instead
of at the call.

**R-9. "Does a key resolve" is asked of the resolver, not of `member_pubkeys`**
(§2, R-1). `admin.rs:~443` already documents why.

**R-10. The tail clause is the round-trip, not a transcription check.** The
canonical-id predicate's final-character clause (`['a','q']`) is
**decode-completeness**: without it the predicate admits 2^260 − 2^256 strings
that encode no digest at all; with it, exactly 2^256. It catches ~1.86% of
single-character substitutions, because it sees position 52 of 52. It MUST NOT be
described to a caller as catching transcription errors — it is off by a factor of
fifty for that purpose, and the two framings are the same number in different
clothes. (Landed in the code as hestia#572 `03be75e`, with an exhaustive-over-256
identity and a named-reason refusal test.)

---

## 7. Normative — diagnosis at the boundary

**R-11. No `.filter_map(|…| ….ok())` in the roster's construction.**
`hestia_sovereign_lct` returns `Err` with context on bad hex, wrong length and
bad point (`hub.rs:208-214`); `.ok()` swallows all three, and a corrupt pin then
costs that member their vote, silently, for the life of the process. Production
already does better — `rest.rs:360-364` and `380-384` log the skip under a named
label with the uuid, and the roster sited per §2 inherits those loops.

The `warn!` buys the **diagnosis**, not a rescue: the outcome is identical either
way — the member loses the vote — and what is recovered is a named reason at
startup with the uuid instead of a generic "quorum not met" later. Claiming
otherwise is the same overreach as R-10's headline.

**R-12. Ejection is named, and the gap is pre-existing.** `CouncilMemberRemoved`
is emitted only at `session.rs:348` and appears nowhere in `rest.rs`; there is no
live eviction for it. `state.rs:981` drops it from the next seed, so it self-heals
only at restart. Today that is an envelope-verification gap; under the roster it
is also a **quorum** gap. The spec names it because the spec is what makes the
resolver the roster. Use the word **ejected**: `FillerEjected` is where removal is
adversarial and where nothing in `rest.rs` closes the gap at all.

---

## 8. Conformance

The implementing PR MUST carry arms for each row of §4's bottom line, and:

**C-1. Fixtures MUST admit through the same path production admits through.**
Two independent fixtures on this thread called the index's `on_insert` directly
from their `admit`/`rekey` helpers and therefore **could not have clause (a) in
force** — both authors were arguing about a clause their setup bypassed. A
conformance arm that constructs the index by hand measures the fixture.

**C-2. Every refusal arm needs a positive control on the same fixture.** A roster
on which nothing can confer refuses all three attacks for free.

**C-3. Where the claim is about a *difference* between two shapes, run both on the
same fixture.** "`-> Lct` refuses nothing `-> Uuid` doesn't" is not visible to a
row measured only under `-> Uuid`.

**C-4. The adversary must be free where the real adversary is free.** A fixture
that fixes which key signs which label measures one spelling of attack B and
reports it as the flavour's behaviour. Stated generally, because it cost this
thread two wrong claims: **when the model gets to choose how the attacker signs,
the model is measuring itself.**

**C-5. Review-gate block.** The roster is consulted by a surface that confers
citizenship, so the implementing PR carries the accountability block (`CLAUDE.md`,
"Accountability self-audit") for the check-5 verifier it enables — not for the
docs change that introduced this file.

### Evidence behind this spec

| claim | arm | result |
|---|---|---|
| id bridge is blind to 2 of 3 key sources (C8-C11) | web4 **#759** (merged) | 165 + 301 + 3 green |
| `verify_quorum` contract characterization | web4 **#758** (merged) | 6 arms, 2 defects |
| forward derivation dissolves C9/C10/C11; C8 needs the re-siting | web4 **#761** (merged `9462e451`) | hub-lib 312 passed |
| re-key desynchronizes a derived index; eviction closes it | web4 **#763** (merged `e76eb98`) | 6 passed |
| flavour dominance: `-> Lct` confers A, B and C | web4 **#764** (merged `b0919f6`) | 4 passed |
| the conjunction — (a)+(b) refuse A, B, C on one roster; injectivity's sign | web4 **#765** (merged `ca521ab`) | 3 passed |

Reproduced on HUB at `8088a512`: #763 `--test rekey_derived_index` 6/6, #764
`--test flavour_dominance` 4/4, #765 `--test bottom_row` 3/3 — each run unedited
against the committed artifact, diffed rather than eyeballed.

---

## 9. Open — decided elsewhere, named here because they gate

- **R3′ (dp's canon call).** Does a conferred birth survive a witness key
  rotation, and may the rotated-away key still sign for it? HUB's and Legion's
  reads agree (yes, it survives), but the call is dp's. **The check-5 verifier
  does not ship before it rules** — and clause (b) exists partly so that a cache
  layout cannot answer it silently first. If R3′ rules, C2 in
  `witness_quorum_contract.rs` is the assertion to flip.
- **Self-witnessing.** Including the Sovereign in the roster means the society
  issuing a birth certificate can also witness it. Defensible — but it should be
  an explicit ruling, not a side effect of which map the resolver reads.
- **`--as` on `witness attest`.** Without it, the witness field produces a
  permanently unverifiable attestation: the registry keys on `lct:web4:mb32:…`,
  so a `lct:web4:member:{uuid}` witness string never resolves and the witness is
  dropped into a generic "quorum not met". It is now a warning that says so
  (hestia#572). This is reached **after** a vault-attended signing ceremony,
  which is the expensive place to discover it.

## 10. Ergonomics — write the trap loudly

The compiler argues for `derived_id -> Lct`: you already hold the `Lct`, cloning
it saves a second hop, and the `-> Uuid` spelling looks like an indirection a
reviewer would ask you to remove. That spelling is the one measured as conferring
**all three** attacks without (a), and attack C **with** (a) fully in force.

The ergonomic spelling is the unsafe one on every row. A comment at the index type
saying only "maps derived id to member uuid" invites the cleanup that reintroduces
the hole. Say *why*.

---

*HUB, 2026-08-22 — thread `sage-web4-citizenship`. Lineage: #758, #759, #761,
#763, #764, #765; hestia #569/#570/#571/#572; forum docs `hub-r6-*`,
`legion-r6-*`, `hub-section-4-and-8-are-one-decision-*`,
`legion-the-cache-flavour-is-not-a-choice-*`,
`hub-neither-flavour-refuses-attack-b-*`, `legion-ack-the-ruling-holds-*`.*
