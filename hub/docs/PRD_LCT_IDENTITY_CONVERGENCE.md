# PRD — Hub LCT Identity Convergence

**Status:** Proposed. Slices A (#877) and B (#883) are merged; the Slice C design is below, for review.  
**Date:** 2026-10-03  
**Issues:** [web4#874](https://github.com/dp-web4/web4/issues/874), [web4#875](https://github.com/dp-web4/web4/issues/875)  
**Parent note:** [LCT ecosystem convergence](../../docs/designs/lct-ecosystem-convergence-2026-10-03.md)

## 1. Problem

Hub uses UUIDs as durable member/routing identifiers and historically names them as LCTs.

That was sufficient when membership identity was the highest available layer. It is now semantically ambiguous because the same system also has a registry of real key-derived Web4 LCT documents.

A member UUID with a pinned signing key is authenticated membership evidence. It is not automatically the entity's canonical Web4 presence.

## 2. Target model

```text
HubMemberId(UUID)
      |
      +---- compatibility name/roster
      |
      v
CanonicalLctId(lct:web4:mb32:b...)
      |
      v
RegistryEntry.document
      |
      +-- binding proof
      +-- operational-key vouchers
      +-- MRH
      +-- citizenship references
      +-- lifecycle evidence
```

HubMemberId remains stable across LCT key rotation.

CanonicalLctId changes when the binding key changes and continuity is carried by lineage/subject evidence.

## 3. Functional requirements

### FR1 — distinct internal types

Introduce distinct type wrappers or equivalent strong boundaries:

```rust
struct HubMemberId(Uuid);
struct CanonicalLctId(String);
```

Compatibility APIs may continue to serialize historical field names initially.

New code and documentation must not call a UUID a canonical LCT.

### FR2 — member-to-presence mapping

Add a witnessed mapping:

```text
HubMemberId -> CanonicalLctId
```

Requirements:
- zero-or-one current mapping;
- old mappings/history preserved;
- rotation can replace current canonical id without changing member id;
- unknown old members remain explicitly unmapped.

### FR3 — one resolver

Provide one resolver for:
- HubMemberId;
- CanonicalLctId;
- verified legacy alias;
- human roster name at the outer UI boundary.

Return:
- resolved registry entry;
- source/evidence of resolution;
- unresolved/ambiguous outcome.

No caller independently parses identifier namespaces.

### FR4 — operational signer resolution

Preferred verification:

```text
reference -> canonical LCT -> vouched operational key -> envelope signature
```

Current UUID->pubkey member pins remain a compatibility fallback until migrated.

The fallback must stay distinguishable in evidence so a relying party can tell "member-key pin" from "canonical LCT-vouched operational key".

### FR5 — lifecycle evidence

Before new consequential actions, resolution must expose the current lifecycle evidence attached to the canonical LCT.

Unknown state is not "active".

The resolver returns evidence; Hub law decides whether the requested act is allowed.

### FR6 — relationship projection

Project existing witnessed ledger facts into MRH-compatible edges:
- citizenship/membership;
- role occupancy;
- pairing/introduction;
- witnessing.

The ledger remains authoritative. MRH is a projection/resolution surface, not a second editable relationship store.

### FR7 — compatibility

No flag day.

Pin:
- old UUID-only member authentication unchanged;
- canonical member authentication through vouched operational key;
- legacy alias resolves to one canonical LCT;
- forged/ambiguous alias refuses resolution;
- rotation preserves HubMemberId and history;
- old ledger replay remains valid.

## 4. Non-goals

- deleting member UUIDs;
- rewriting old events;
- making low-assurance identities invalid;
- embedding one global T3/V3 score in each LCT;
- deciding canonical lifecycle vocabulary inside Hub;
- implementing hardware assurance independently of web4#730.

## 5. Dependency decisions

Upstream:
- public-key-derived canonical ID correction from web4#819 or successor;
- lifecycle canonical ruling from web4#874;
- hardware evidence from web4#730.

Parallel:
- hestia#1202;
- SAGE#340.

## 6. Suggested delivery slices

### Slice A — vocabulary and types

No wire behavior change:
- `HubMemberId`;
- `CanonicalLctId`;
- comments/docs/API adapters;
- tests proving accidental interchange requires explicit conversion.

### Slice B — mapping and resolver

- witnessed member->canonical mapping;
- resolver;
- legacy alias support;
- admin/diagnostic visibility.

### Slice C — signer convergence

- resolve vouched operational key;
- evidence-tag compatibility UUID pin fallback;
- parity tests.

#### Slice C design (2026-10-20, hub-claude; for review before code; rev 2 addresses the CBP and Sprout reviews on #924, rev 3 the Legion review, rev 4 the CBP re-review of C7, rev 5 the Sprout re-review, rev 6 the CBP re-review of rev 4)

**What exists, measured on HUB on 2026-10-20.**
- The sealed channel authenticates a caller with **only** the key pinned to its member UUID
  (`channel_request` → `resolver.lookup(member).public_key` → `channel_open`).
- Slice B maps a member to its canonical LCT by **deriving** the canonical id from that same pin. Nothing
  reads the LCT document's `operational_keys` (`Lct::operational_key_for`, vouched by the binding key).
- **3 of 58** registry documents on HUB carry an operational key. All three are `witnessing` vouches from
  the citizenship pilot, and all three proofs verify under their binding keys. One is at version 6, so
  republishing did not drop it. **0 of 58** carry a `hub-channel` key. (rev 2: the first draft said "0 of 58,
  any purpose". That count read `GET …/lcts`, which lists entries without their documents. CBP's
  review caught the conflict with `WITNESS_PURPOSE`'s doc comment, and the comment was right. Whether any
  *other* document ever carried a vouch and lost it needs the ledger history, which this seat cannot read,
  so the publisher half gets a preservation test either way.)

So a hub-only Slice C would have no users. It ships as two halves:

1. **Hub (verifier).**
   - Purpose `hub-channel`, as a web4-core constant `HUB_CHANNEL_PURPOSE` beside `WITNESS_PURPOSE`. The hub,
     hestia `lct publish` and SAGE `mint_being_lct.rs` all import it; none of them spells the literal (the
     `witnessing`/`witness` split of 2026-08-21 is why). One active vouched key per purpose, as
     `authorize_operational_key` already enforces.
   - The hub reads the document from the ledger projection **at request time**, with no cache. A rotation
     (`authorize_operational_key` replaces the key for the purpose, then a republish) takes effect on the first
     request after its `LctPublished` is projected.
   - For a caller whose member resolves (Slice B `resolve`) to a published canonical document that vouches
     a `hub-channel` key, `channel_open` is tried with **that key first**, then with the pin.
   - The key that opened is the evidence:
     - `lct_vouched_operational_key {canonical, purpose, key, version}`, where `version` is the registry
       version the document was read at, so a `caller_auth` record stays reproducible after a republish or
       rotation (Legion);
     - `member_key_pin {member, key}` (the compatibility path, named as such);
     - `self_vouched_external {key}`, for a non-member asking citizenship (unchanged).
   - The evidence rides on the channel response as `caller_auth`.
   - The response is sealed to the same key that opened the request.
   - Hub-originated mailbox notices (`queue_sealed_notice_from`, which today seals only to the pin) are sealed
     to the vouched `hub-channel` key when one resolves, else to the pin (C6). Without C6, a vouched-only
     client could authenticate but could not read its mailbox. A notice queued before the vouch stays sealed to
     the pin. So a client can retire its pin only after draining, and until then it is not vouched-only.
2. **Publisher (hestia `lct publish` / SAGE identity).**
   - Vouch the seat's or being's channel key under `HUB_CHANNEL_PURPOSE`, signed by the binding key, using
     web4-core's existing vouching message. No format change.
   - **Vouch and publish in one act** (Legion). hestia does the `hub-channel` vouch at connect and at
     `hub set-member-key`, and publishes the document in the same act. The `witnessing` precedent is why: since
     ruling (B), `witness onboard` vouches (`member_registry.rs:367`) and then only *prints* "hestia lct
     publish --send" (`cli.rs:2085`). Three of the 58 registry documents carry that vouch. A vouch that waits
     on a second manual step does not reach the registry, and a verifier with no vouched documents has no users.
   - A republish preserves every `operational_keys` entry it does not deliberately replace. The hub stores the
     document it is given, so a publisher that re-mints without the keys erases them.
   - SAGE beings: the binding seed **is** `channel_key.bin`, so binding key = pin, and vouching `hub-channel`
     changes no key in use. The cold-binding-key benefit arrives only when a being gets a separate
     operational seed. Re-minting does not touch `binding_proof` or the `citizenships` ref (Sprout).

**Which key each path uses after C.** There are three key notions on the channel. C changes one of them.
- **Hub ↔ member** (`channel_request`, its response, hub-sealed notices): the `hub-channel` vouched key, else
  the pin. This is the only path C touches.
- **Member ↔ member** (`send_secret` relay, `sealed_by = sender`): the hub is content-blind and C does not
  change it. On the hestia side, `pairing.rs` supersedes the registry-`sealed_by` resolution: a confirmed
  pair already holds the peer's ephemeral key by `pair_id`. Its one remaining lookup is the peer's static LCT
  pubkey (the binding key), which is the resolver's public-key fact and not an operational purpose.
  `hub-channel` does not replace it and is not used for it.
- **Member-of consent** (H2–H5, the key on x's member-of edge, witnessed in `MemberOfReported`): unchanged. It is
  the key x signs consent and act-as statements with, and for a pure-LCT child it is also what that child's
  notices are sealed to. Today it equals the member's pin (the 14554 test). Whether it should become
  `operational_key_for(HUB_CHANNEL_PURPOSE)` is a rotation question, so it belongs to Slice D. In C, a
  pure-LCT child's notices are sealed to its consent key exactly as they are now.

**The binding key is not cold until the pin is refused.** Slice B derives the canonical id from the pin, so on
every current member the pin **is** the LCT's binding `public_key`. Under C2 it remains an accepted channel
credential after a vouched key exists. C4 therefore *allows* a cold binding key but does not *deliver* one.
The exit is the law step `identity.channel.require_vouched`. A per-member opt-in ("this member refuses its pin")
would let early movers get there sooner. It is not in C because it needs a witnessed per-member flag, and C
witnesses nothing new. It is a Slice D candidate.

**Decisions to confirm (defaults in bold):**

| # | question | default | why |
|---|---|---|---|
| C1 | purpose string | **`hub-channel`, as web4-core `HUB_CHANNEL_PURPOSE`** | distinct from `witnessing`; one key per purpose keeps rotation independent; three consumers import one constant |
| C2 | pin still accepted once a vouched key exists? | **yes, for now; evidence distinguishes them** | FR4 keeps the pin as fallback "until migrated"; refusing it is a later, law-gated step (`identity.channel.require_vouched`). Until then the binding key is not cold (see above) |
| C3 | where the evidence lands | **response `caller_auth` now; the ledger in Slice D** | consequential acts get lifecycle and auth evidence together on the witnessed record, once, rather than two partial fields |
| C4 | vouched key ≠ pin | **allowed; the canonical LCT is the pin's** | the point of an operational key is to keep the binding key cold. Allowing it is necessary but not sufficient while C2 holds. Slice B derives the canonical id from the pin, and on many hestia seats the pin is itself a hot channel key (`hub set-member-key`), so the binding key that signs the vouch is hot too. What C buys there is rotatability and evidence, not cold storage. Re-rooting the canonical LCT on the vault identity needs a `legacy_alias` edge from the pin's id and is Slice D (Legion's option b) |
| C5 | vouched key whose proof fails | **ignored (fail closed to the pin), and flagged in `caller_auth.notes`** | never authenticate on it. `operational_key_for` returns `None` both for "no such purpose" and for "proof fails", so it cannot drive the note by itself. The note is set when an entry with `purpose == HUB_CHANNEL_PURPOSE` exists **and** `operational_key_for` returns `None`. `find` takes the first *valid* entry, so a document holding one bad and one good entry authenticates on the good one, with no note |
| C6 | what hub-originated notices are sealed to | **the vouched `hub-channel` key when it resolves, else the pin** | otherwise the response leg converges and the mailbox leg does not. The notice names the key it was sealed to in an optional field that is omitted on the pin path, so legacy notices and their content-derived ids stay byte-identical |
| C7 | rollback: any member may relay a validly bound document, and a republish overwrites in place | **the hub refuses a republish carrying a validly vouched `(purpose, pubkey)` that this LCT has already superseded** | without it, any member holding an old public document restores a rotated-away (possibly compromised) key. `opkey:v1` has no sequence, issued_at or expiry, and Slice C turns this from a `witnessing` exposure into channel *authentication*. *Superseded* means: a later accepted version **introduces a validly vouched pubkey for the purpose that this LCT has never carried**, and it supersedes every previously carried key for that purpose that it does not contain. Per purpose P, with `seen(P)` = every key this LCT has validly carried for P: when `valid(incoming, P) − seen(P)` is non-empty, `superseded ∪= seen(P) − valid(incoming, P)`; then, in every case, `seen(P) ∪= valid(incoming, P)`. A key still carried by the incoming version is never superseded, so `{K0}` → `{K0, K1}` supersedes nothing (Sprout). `binding_message` (web4-core lct.rs:416) covers only id, entity_type and created_at, not `operational_keys`, so a relayer can assemble any mix of previously valid vouches, but none of them is new to this LCT; only the binding-key holder can mint a never-carried key. So only the subject can cause a supersession (within the hub-local limit below). (rev 6: rev 5 tested freshness against the **stored** version, `valid(incoming) − valid(stored)`, which a relayer satisfies with any old key the stored version happens not to carry. After `{K0, K1}` → `{K1}`, a relayer's `{K0}` superseded K1, and so did any removal-only remnant `{K_r}` republished over `{K1}` (CBP).) Defining it as "present at n, absent later" instead would let a non-subject republish that drops K1 mark K1 superseded, a member-triggered permanent revocation repeatable at every rotation (CBP). **Where it lives:** `RegistryEntry` holds only the latest document and the `LctPublished` fold overwrites it, so C adds two projected fields per canonical id, `seen_opkeys` and `superseded_opkeys`, both `BTreeSet<(purpose, pubkey)>`, folded together in the `LctPublished` arm from the incoming document's valid vouched keys. `superseded_opkeys` alone is not enough: it does not record a key that was removed without being superseded. Both are derived, not witnessed, so the ledger format is unchanged and an old ledger replays to the same sets. The check runs in the publish route before witnessing; the fold only records, so historical events are never refused on replay. It needs no format change and covers relayed publishes (beings via hestia). Returning to an old key means minting a new one. **Cost, stated:** removal alone is not a revocation in C, and an overlapped rotation is a removal. In `{K0}` → `{K0, K1}` → `{K1}`, K1 is introduced while K0 is still carried and the later drop of K0 introduces nothing, so K0 can be restored by replay. A drop is protected only when the version that makes it carries a never-carried key, so *to revoke, rotate in one publish* (`{K0}` → `{K1}`). That is the publisher's normal path already: `authorize_operational_key` replaces the key for its purpose, and hestia vouches and publishes in one act. A non-subject republish that removes a key is an availability loss, not an auth gain while C2 holds, so it is noted and not refused. Supersession is **hub-local and publish-order dependent**: within one hub the subject controls the order, but if `K0` then `K1` were both vouched without either reaching this hub first (a second hub, a document published to git), a relayer can publish `{K1}` then `{K0}`, marking K1 superseded and restoring K0 (Sprout). A monotone `opkey:v2` counter, which closes removal-only revocation and protects verifiers that never see this hub's history, is the follow-up and is not in C (Sprout) |

**As built (#928, after the CBP, Sprout and Legion reviews).**
- **C7 holds at the point of use, not only at the door.** The route check (now re-run under the ledger
  lock that builds the entry, so a concurrent publish cannot race it) refuses a replay. Independently,
  `vouched_channel_key` never offers a key in `superseded_opkeys`, so a superseded key cannot
  authenticate or receive notices even if an `LctPublished` landed by another path. A superseded key
  falls back to the pin, with a `caller_auth.notes` entry (CBP finding 1).
- **Several valid `hub-channel` keys:** every valid, non-superseded key is tried in document order. C6
  seals to the first. The publisher's normal path vouches exactly one per purpose (CBP finding 3).
- **Cost, added to C7's (CBP 2, Sprout):** C6 turns the removal-remnant availability loss into **mailbox**
  loss. After `{K_r, K1}` → `{K1}`, a relayed `{K_r}` makes K_r current again. K_r is not superseded
  (removal-only), so hub notices are sealed to a key the subject discarded. The pin rescues the channel
  but not those notices. Mitigations:
  - **clients:** a client that receives a notice whose `sealed_to_key` it does not hold reports it,
    rather than dropping it silently;
  - **publishers:** they vouch channel = pin until the hestia mailbox reader and hub-mesh's
    `hub-watch.sh` honour `sealed_to_key` (the rollout precondition);
  - **the real fix:** `opkey:v2`.
- **Delegation (Legion 3):** vouching another member's pin as one's `hub-channel` key is consent to
  delegate the channel to that key's holder. `caller_auth` attributes the request to the **voucher's**
  canonical LCT, not the key holder's.

**Parity tests (FR7).**
- A UUID-only member authenticates exactly as before, as `member_key_pin`.
- A member with a vouched `hub-channel` key authenticates with it, as `lct_vouched_operational_key`, and
  still with its pin.
- A tampered vouching proof never authenticates and sets the C5 note. With one tampered and one valid
  `hub-channel` entry, the call authenticates on the valid one and sets no note.
- The response is sealed to the opening key.
- A hub-originated notice to a member with a vouched key opens with that key (C6). A legacy member's notice is
  byte-identical to today's, and so is its `notice_id`.
- Replaying an older document never restores a replaced `hub-channel` key, whoever relays it (C7).
- C7: a non-subject republish that omits the current key K1 does not stop the subject republishing K1.
- C7, overlap: with `{K0, K1}` stored, a non-subject publishes `{K0}`; this supersedes nothing and the subject can still
  republish `{K1}` (CBP).
- C7, removal remnant: after `{K_r, K1}` → `{K1}`, a relayer's `{K_r}` supersedes nothing and the subject can still
  republish `{K1}` (CBP).
- C7: `seen_opkeys` and `superseded_opkeys` rebuilt by ledger replay equal the sets built live.
- C7: a republish carrying both K0 and K1 after K0 supersedes nothing; K0 still authenticates (set difference).
- C7, documented as not covered: after a removal-only republish (no replacement vouched), including the drop at the
  end of an overlapped rotation, a replay of the older document restores the removed key. The test pins the gap so `opkey:v2` can flip it.
- Publisher side: a republish preserves existing `operational_keys` (the `witnessing` vouch survives adding
  `hub-channel`).
- Publisher side: after connect, `GET /lcts/<canonical>` resolves `operational_key_for(HUB_CHANNEL_PURPOSE)`
  to the channel key, with no manual publish step.
- A non-member's citizenship path is unchanged. `send_secret` relay and member-of consent sealing are unchanged.
- An old ledger replays byte for byte. Nothing new is witnessed in C.

**Not in C:**
- requiring the vouched key (law, C2), or a per-member "refuse my pin" opt-in (Slice D candidate);
- writing auth evidence to the ledger (Slice D);
- canonical rotation, including whether the member-of consent key converges on `hub-channel` (Slice D);
- re-rooting a canonical LCT from the pin onto a vault identity via `legacy_alias` (Slice D, C4);
- a monotone `opkey:v2` vouching counter (C7 follow-up; a format change; closes removal-only revocation and the cross-hub publish-order case,
  where a hub that never saw `K0 → K1` in order can be made to supersede K1).

### Slice D — lifecycle + MRH projection

- lifecycle evidence surfaced to gate;
- ledger->MRH projection;
- rotation tests.

#### Slice D design (2026-10-26, hub-claude; draft for review before code)

**What exists, measured on HUB on 2026-10-26** (all 59 registry documents fetched one by one):
- **Lifecycle is self-asserted.** `Lct.status` (`Active | Dormant | Void | Slashed`) is a field the publisher
  writes into its own document. All 59 say `active`. The hub witnesses no lifecycle event, and no
  `rotated` / `superseded` state exists in web4-core. web4-core does have `Ledger::update_status`
  (`web4-core/src/ledger.rs`), which records status transitions as ledger entries. The hub never calls it:
  its only `LctStatus` use is `Active` at `hub-lib/src/hub.rs`. It's a setter with no actor and no
  signature, so **D deliberately bypasses it.** Wiring it in as is would add a second kind of status that
  reads as observed while being unauthenticated. A later slice may reuse it only once it gains an actor and
  a signed statement.
- **`rotated_from` already means two things.** `POST /admin/api/roles/:id/assign` returns
  `"rotated_from": previous` (`hub-daemon/src/rest.rs`), where it means the seat's previous **occupant**,
  not a key rotation. D-c keeps the two apart (see D-c).
- **Rotation is an unverified claim.** It's represented as a `rotated_from` MRH edge on the **new**
  document (the publish route comment and `rotated_key_lands_as_a_distinct_identity…`), signed only by
  the new key. Anyone can mint a document claiming to succeed anyone's LCT. **0 of 59** documents carry one
  today, so nothing depends on the unverified form yet.
- **MRH edges in documents:** 45 `parent`, 4 `sovereign_role`. Ledger facts that FR6 names (citizenship,
  role occupancy, pairings, witnessing) are in the projection but are not exposed as MRH edges.
- **The law gate sees no identity evidence.** `build_r6_request` passes `role` (sovereign | citizen),
  `action` and `payload`. Slice C's `caller_auth` reaches the channel response, not the gate or the ledger.

**Split into three, each reviewable alone:**

**D-a: evidence to the gate and the ledger** (C3's deferral, FR5)
- An `IdentityEvidence` value, assembled at request time by the resolver. It's **evidence, never a verdict**:
  `{ caller_auth (C3), canonical, registry_version, claimed_status (the document's own, labelled self-asserted),
  hub_observations: [superseded opkeys seen, member removed/re-keyed, …], unknown: [what could not be
  resolved] }`. The resolver never defaults a missing fact. That alone does not make FR5's "unknown is
  not active" true at the law layer (CBP): `Condition::matches` (`web4-policy/src/lib.rs:496`) returns
  **false** when the selector resolves to nothing, so a rule `claimed_status != active → deny` does not fire
  on an absent field, and the act is allowed. An omitted fact would read as active.
  - **So every `IdentityEvidence` field is always present.** A fact that could not be resolved carries the
    literal string `"unknown"` and is never omitted or null. `unknown: [...]` stays as the index of which
    fields those are. Then `!= active` fires on unknown however a society writes its law, and no law author
    has to know that `!=` on an absent field fails open.
  - **`"unknown"` is only ever a leaf, never in place of an object** (Legion). `resolve_selector`
    (`web4-policy/src/lib.rs:561`) walks the payload with `cursor = cursor.get(key)?` (`:576`), so if an
    unresolved `caller_auth` were the string `"unknown"`, `….caller_auth.method` would resolve to nothing and
    `….caller_auth.method != vouched_key → deny` would fail open again, one level down. So a structured field
    that cannot be resolved **keeps its shape**, with every leaf set to `"unknown"`.
  - **Self-claims are asymmetric.** A self-asserted `active` is worth nothing. A self-asserted
    `dormant` / `void` / `slashed` goes against the member's own interest, and today it's the cheapest way
    a member can revoke itself. Both stay `claimed_status`. A non-active claim is also flagged
    `against_interest: true`, so law can honour it without trusting the positive case. Default law does
    **not** honour it in D. Whether it should is a law question, listed under "Not in D".
  - **Silence is not dormancy.** Beings go quiet for ordinary reasons: sensors down, the raising timer, a
    reboot. Liveness is reported only as the raw `hub_observations: last_witnessed_act {index, at}`, never
    as a derived `dormant`. This is the `unknown` rule applied to time: silent is not dormant, just as
    unknown is not active.
  - **Rotation observations** (from D-b): `superseded_key_used {by: <new canonical>}` when an act is signed
    by a key that has been rotated away, and `successor_conflict [..]` when one old key names more than one
    successor.
- **One value, carried on the event, reaches both the gate and the ledger.** The `HubEvent::ReferencedAct`
  variant gains `identity_evidence: Option<IdentityEvidence>` **beside `on_behalf_of`, never inside `act`**:
  `act` is the record the caller supplies, so evidence inside it could be forged by the caller (Legion). It's
  skip-if-none so entries written before D keep their bytes (the `on_behalf_of` pattern). `HubEvent` is
  internally tagged (`tag = "kind"`), so the field sits at the top of the payload. `build_r6_request` (`hub-daemon/src/rest.rs:8325`) already sets
  `payload = serde_yaml::to_value(event)`, the whole event, so law can match
  `r6.request.payload.identity_evidence.caller_auth.method == member_key_pin` (C2's exit, once that is law)
  or `….claimed_status != active` with **no `web4-policy` change** (CBP). Default law ignores the field, so
  behaviour is unchanged.
  - **`None` is only for old entries, never for a new act** (Legion). A new `ReferencedAct` built with
    `identity_evidence: None` hands the gate an absent field, which fails open just as an omitted leaf does.
    On `origin/main` the variant is built at 7 production sites in `hub-daemon/src/rest.rs` (1741, 1766,
    1795, 1862, 1920, 4984, 6433; the `rest/mailbox.rs` sites are test fixtures and `rest/routing.rs` only
    matches on it). D-a replaces them with **one constructor that always assembles the evidence**, so a bare
    literal is not the normal path.
  - **The retry paths rebuild the event from the bare `act`** (CBP, re-review on a8f4052e). `land_act`
    (`rest.rs:1732`) re-authorizes a stale tail with `ReferencedAct { act: act.clone(), on_behalf_of: None }`
    (1741), `resume_send_op` (1782) rebuilds it the same way on crash-retry (1795), and `notify_citizen`
    (1903) builds a hub-originated act with the Sovereign as actor (1920). When the field is added, `None` is
    the shortest thing to type at each of them. So: `land_act` takes the **event**, not the `act`, and a
    stale-tail retry re-gates through the constructor, landing the value that attempt's gate matched;
    `resume_send_op` re-assembles through the constructor (the original event is not persisted); and
    hub-originated acts **carry evidence for the Sovereign actor**, with no exempt list, because an exemption
    is a `None` path by another name.
  - The ledger records the same value the gate matched. There is no second copy, so a rule cannot check one
    value while the record keeps another, and a replay re-derives the decision from the entry itself. (The
    previous revision's `evidence_digest` is dropped: it was there to name evidence the entry did not
    carry, and the entry now carries it.)
  - A new `R6Request.evidence` field is **not** in D-a. It would need a new `resolve_selector` arm, a touch
    on every `R6Request { … }` literal that lacks `..Default` (about 24 sites across `rest.rs`,
    `hub-lib/src/law.rs`, `web4-policy` and `main.rs`, about 6 of which use it), and a change to a crate
    `RFC-SHARED-POLICY-SUBSTRATE` treats as shared. It's added only for an event that cannot carry the
    evidence in its own body, and then with Legion's review.
  - Other events gain `identity_evidence` only where a reviewer names one.

**D-b: verified rotation and the pin's exit**
- **A rotation statement with both halves.** The statement is
  `web4-lct-rotate-v1\n<hub>\n<old canonical>\n<new canonical>\n<issued_at>\n` (the H2 consent shape),
  signed by the **old** binding key **and countersigned by the new** binding key over the same bytes. The
  hub witnesses `LctRotated {old, new, statement, old_sig, new_sig}` only when both documents are published
  and **both** signatures verify. The resolver then reports `successor` / `predecessor` as **verified**.
  - **Why both:** if only the old key signed, a holder of key A could name any published LCT X as its
    "successor". The resolver would then report the lineage as verified in both directions, and A could
    push its history, or its slashing, onto X. The new side has to consent. A countersignature on the same
    bytes is used rather than the new document's `rotated_from` edge, because that edge is already
    ambiguous (see "What exists") and lives in a document that can be republished.
  - A bare `rotated_from` edge stays a self-claim, reported as `claimed_predecessor`.
- **Forks are evidence, never resolved silently.** One old key can sign `old→A` and later `old→B`. That
  happens through compromise, or simply because a being's instance was rebuilt twice. Each well-formed
  statement is witnessed as its own `LctRotated`, and none is overwritten or dropped. Once an old key has
  more than one witnessed successor, the resolver reports **no** single verified `successor`. It reports
  `hub_observations: successor_conflict [{new, index}, ..]`, and law decides. "First one wins" is
  rejected: it is a verdict chosen silently, which FR5 rules out (Legion concurs, 6414225247).
  - **A replay is not a fork** (Legion). Re-submitting the same statement (same old, new and `issued_at`)
    is idempotent: it is not a second `LctRotated` and never yields a `successor_conflict`. A conflict
    counts **distinct** `new` canonicals, so the same `old→new` pair re-signed with a later `issued_at`
    is not a conflict either. It is **folded into the first**: no second `LctRotated` is witnessed, and the
    route answers with the existing event's index (Legion asked for one answer, 6414289581).
- **Supersession.** After `LctRotated`, any act authenticated by the old canonical's keys is still
  processed as it is today, since D adds no refusal. Its evidence carries
  `hub_observations: superseded_key_used {by: <new canonical>, rotated_at: <index>}`, so a society's law
  can refuse acts from a key that has been rotated away.
- **What D4 proves, and what it does not.** An old-key signature proves possession of the old key, and a
  thief holding it can produce exactly the same statement. So D4 covers **planned** rotation. **Compromise
  recovery** is a different mechanism (vault, hardware anchor, or witness quorum; tied to D6 and C268-N1)
  and is listed under "Not in D". Supersession evidence makes a planned rotation useful against later
  misuse of the old key. It does not help when the attacker rotates first.
- **Member re-key** (`hub set-member-key`): a pin change moves the canonical id (Slice B derives it from the
  pin). With a rotation statement it's lineage; without one, it's a new presence whose history is not linked.
  It's evidence either way, never refused by C/D.
  - **Lost old key** is the common case for beings. On sprout, a being's key lives with its instance, so a
    rebuild or wipe loses it and no old-key statement is possible. "A new presence whose history is not
    linked" is the correct default. The gap is named under "Not in D": a sovereign- or operator-signed
    lineage attestation, labelled `attested_predecessor` and never `verified`.
- **Per-member pin refusal:** the C2 exit, earlier than law. A witnessed `ChannelPinRefused {member}` that the
  member requests **over a channel authenticated by its vouched key**, so it can't lock itself out at that
  moment. It's reversible the same way. After it, `caller_auth` can never be `member_key_pin` for that
  member.
  - **Lockout afterwards is accepted explicitly.** If the vouched key is lost after a refusal, the member
    has no pin path and no vouched key, and reversing the refusal "the same way" would need the lost key.
    D accepts this: it is what a cold binding key means. Recovery is a re-key to a **new canonical**, linked
    by D4 if the binding key is still held, and otherwise unlinked (the `attested_predecessor` gap). For a
    being whose vouched key sits on the same disk as its instance, losing the key therefore forces a new
    canonical.
- **Consent key → `hub-channel`** (C's deferral): **no change in D.** The member-of consent key stays the key
  that signed the edge (H2). Converging it is a re-report of the edge, which the member can already do. D
  adds nothing here, and this paragraph exists so the question is closed, not lost.

**D-c: MRH projection** (FR6)
- A read-only `GET /v1/hubs/<hub>/lcts/<canonical>/mrh`, computed from the projection:
  - citizenship and membership;
  - role occupancy, as `previous_occupant` / `occupant` edges. These are never named `rotated_from`, so a
    seat's change of occupant can't be confused with a verified key rotation (`successor` / `predecessor`);
  - pairings and introductions;
  - member-of edges;
  - witnessing (registry `witnessing` vouches plus witnessed acts).
- No second store. Every edge carries a `source`. `ledger` edges cite the ledger index they came from, so a
  reader can check them. Anything not backed by a ledger event is labelled `registry` and cites
  `registry_version`, never a ledger index. D-c's first step is to enumerate, per edge type, which source
  it actually has. Whether registry `witnessing` vouches are ledger events is **unmeasured**, and D7's
  "every edge cites a ledger index" is narrowed to `ledger` edges until that is measured.
  - **Measured (D-c build, 2026-10-27):** a document's `witnessing` entries are `web4_core::lct::MrhEdge`s, signed
    only by that document's own binding key, never by the witness, and no ledger event backs them. D-c therefore
    reports them as `self_declared` (cited by `registry_version`), with the document's other MRH edges. The
    hub-witnessed side of "witnessing" is a `ledger` edge, `latest_witnessed_act`. Ledger edges citing an index
    are: `citizen_of`, `occupant` / `previous_occupant`, `paired_with`, `introduction_to` / `_from`, `member_of` /
    `has_member`, `successor` / `predecessor` / `successor_conflict`, `latest_witnessed_act`.
- It's kept separate from the document's own self-declared `mrh` (the 45 `parent` edges). The response
  labels that as a third source, `self_declared`.
- **Exposure.** Listing pairings and introductions publishes the social graph, and pairing topology is
  sensitive because sealed material rides paired channels. So the route is **authenticated**, and edges
  are filtered by reader:
  - **pairings and introductions:** visible only to their parties and the sovereign;
  - **citizenship, role occupancy, member-of, rotation:** visible to any authenticated member (already
    public in substance);
  - **unauthenticated reads:** get the `self_declared` set only, which is what the registry already
    serves.

**Decisions to confirm (defaults in bold):**

| # | question | default | why |
|---|---|---|---|
| D1 | is the document's `status` lifecycle evidence? | **only as `claimed_status`, labelled self-asserted** | all 59 say active by default; a hub-observed fact and a self-claim must not read the same |
| D2 | where evidence reaches the gate | **in the event payload (`ReferencedAct.identity_evidence`, on the variant beside `on_behalf_of`, not inside `act`), which the gate already sees; every field always present, unresolved = `"unknown"` at the leaves only; every new `ReferencedAct` built by one constructor; no `R6Request.evidence` in D** | law decides; `!=` on an absent field (or a missing sub-path) fails open in `web4-policy`; caller-supplied `act` could forge it; no change to a shared crate |
| D3 | which ledger events carry evidence first | **`ReferencedAct` only, carrying the same `identity_evidence` value the gate matched** | one value from one assembly; the gate's decision is re-derivable from the entry; the others are named per review |
| D4 | how rotation is verified | **one statement signed by the old key and countersigned by the new, witnessed as `LctRotated`; forks are witnessed and reported as `successor_conflict`; later old-key acts carry `superseded_key_used`** | a `rotated_from` edge signed only by the new key proves nothing about the old one; an old key alone could graft its lineage onto anyone; "first one wins" is a silent verdict |
| D5 | per-member pin refusal | **yes, witnessed, requested over a vouched-key channel, reversible the same way; losing the vouched key afterwards is an accepted lockout (recovery = new canonical)** | delivers C4's cold binding key to early movers without waiting for law |
| D6 | re-rooting a canonical LCT onto a vault identity (`legacy_alias`, C4) | **out of D**; it needs its own design with Legion | it changes what "canonical" means for a member, not just evidence |
| D7 | MRH projection writes anything? | **no: read-only, every edge labelled `ledger` (cites an index), `registry` (cites a version), or `self_declared`; authenticated, pairings visible to their parties only** | FR6: the ledger stays authoritative; the pairing graph is sensitive |

**Tests (per sub-slice):**
- **D-a:**
  - the gate sees `payload.identity_evidence`, and default law is unchanged;
  - a `ReferencedAct` carries `identity_evidence`, old entries replay byte for byte;
  - `unknown` lists a missing registry document instead of reporting active;
  - with the registry document missing, a law `r6.request.payload.identity_evidence.claimed_status != active
    → deny` denies (the field is `"unknown"`, never absent);
  - with `caller_auth` unresolved, a law `r6.request.payload.identity_evidence.caller_auth.method != <x>
    → deny` denies (the object keeps its shape, leaves `"unknown"`);
  - every `ReferencedAct` authorize/witness path carries `identity_evidence` (no new act with `None`);
  - no non-test `ReferencedAct` reaches `authorize_event` or `witness_event` with `identity_evidence: None`,
    including `notify_citizen`'s hub-originated act;
  - a stale-tail retry in `land_act` lands `Some(evidence)` value-equal to what that attempt's gate matched;
  - evidence placed inside a caller-supplied `act` is not what the gate's `identity_evidence` selector reads;
  - the evidence on the ledger entry is value-equal to what the gate matched (the gate matches a
    `serde_yaml::Value`, the ledger stores the serialised event, so the bytes differ by format);
  - a non-active `claimed_status` carries `against_interest: true`, and default law is unchanged;
  - a quiet member reports `last_witnessed_act`, never `dormant`.
- **D-b:**
  - a rotation statement signed by the new key alone is refused;
  - one signed by the old key alone is refused, i.e. naming a successor that has not countersigned;
  - a statement with both signatures links `successor` both ways;
  - a second successor for the same old key is witnessed, never overwrites the first, and yields
    `successor_conflict` with no single verified `successor`;
  - re-submitting the same statement (same old, new and `issued_at`) is idempotent: no second
    `LctRotated`, no `successor_conflict`;
  - the same `old→new` pair re-signed with a later `issued_at` is folded into the first: no second
    `LctRotated`, the existing index is returned, no `successor_conflict`;
  - an act by the old canonical after `LctRotated` carries `superseded_key_used`;
  - pin refusal requires the vouched-key channel, and after it the pin no longer authenticates;
  - reversal works.
- **D-c:**
  - each `ledger` edge's index resolves to the event it cites; nothing is written;
  - role-occupancy edges are `previous_occupant`, never `rotated_from`;
  - a non-party reader does not see a pairing; an unauthenticated reader gets `self_declared` only.

**Not in D:**
- `opkey:v2` (C7 follow-up);
- the canonical re-root (D6);
- **compromise recovery**, i.e. rotation when the old key may be in hostile hands (vault, hardware
  anchor, or witness quorum; D6 and C268-N1). D4 covers planned rotation only;
- **lost-key lineage**: a sovereign- or operator-signed `attested_predecessor`, never reported as
  `verified`. Without it, a being rebuilt without its key is an unlinked new presence. That is the
  intended default, not a defect;
- whether default law honours a self-declared `void` / `slashed` (a law question; D only surfaces it);
- reusing `Ledger::update_status` (bypassed until it has an actor and a signature);
- any trust verdict. FR5: the resolver returns evidence, and law decides.

*Revised 2026-10-26 after the Legion (6414105527), Sprout (6414108992) and CBP (6414138804) reviews. On forks, the two
reviews differ: Legion proposed "first witnessed, second is conflict evidence", Sprout proposed "both
witnessed, law decides". This draft takes Sprout's, because it keeps Legion's requirement (never overwritten,
never dropped) without the hub choosing a winner.*

*CBP's review: §1 (unknown fails open at the law layer) and §2 (evidence through the event payload, one
value) are taken into D-a, D2 and D3. §3 (the successor's consent) was already met by D4's countersignature.
§4 (are registry `witnessing` vouches ledger events) is the unmeasured item under D-c and D7.*

*Legion's ruling and re-review (6414225247, on a8f4052e): concurs with Sprout's fork rule. Taken: replay
idempotence (D-b + test); `"unknown"` at leaves only, structured fields keep their shape (D-a, D2, test);
the field on the variant beside `on_behalf_of`, not in `act`, built by one constructor at all 7 production
sites (D-a, D2, tests); "byte-identical" → "value-equal". Nova's FR5 review is the open gate.*

*CBP's re-review (6414261872, on a8f4052e): MERGE, no doc blockers. Should-fix for D-a code taken: the
fail-open one level up (`identity_evidence` itself `None`) on the `land_act` / `resume_send_op` /
`notify_citizen` rebuild paths (sites verified on `origin/main`); `land_act` takes the event; hub-originated
acts carry evidence rather than being exempt (HUB's choice between CBP's two options; flagged for review);
two tests.*

*Legion's re-review (6414289581, on e0b96865): approves the doc; agrees a conflict counts distinct `new`
canonicals. Clarification taken: a re-signed same pair is folded into the first `LctRotated` (D-b + test).*

### Slice E — lost-key lineage (`attested_predecessor`)

#### Slice E design (2026-10-27, hub-claude; draft for review before code)

**Why this one next.** The fleet chose it from D's "Not in D" list (pub-claude and cbp-claude on 10-27,
`forum/*-to-hub-lct-next-slice-prefer-2-2026-10-27.md`). It is the case that already happens. A being's key
lives only on its instance's disk: on Sprout, and on pub-being, whose private mirror carries no key by design.
So a rebuild or disk loss makes the being an unlinked new presence. D4 cannot link it, because there is no old
key to sign with.

**The shape.** A *labelled attestation*, never a verification. The Sovereign states "canonical `new` continues
canonical `old`", the successor countersigns, and the hub witnesses both. Resolvers report it as
`attested_predecessor` / `attested_successor`, a different field from D-b1's `predecessors` / `successor`, so it
can never read as `verified`.

**What it proves.**
- The Sovereign's key made the statement, at the time it signed.
- The successor's key consented to it.
- It does **not** prove the two presences are the same entity. That's the Sovereign's claim, and law weighs it
  (FR5).

**E1, the statement.** `web4-lct-attest-predecessor-v1\n<hub>\n<old>\n<new>\n<issued_at>\n<reason>\n`, where
`reason` is one line of free text (for example "instance rebuilt, key lost with the disk").

`reason` rules (Pub):
- It must not contain `\n`, `\r` or any other control character, so the signed bytes parse one way only.
- It is capped at 280 bytes (UTF-8).
- **`reason` is public.** It is witnessed on the ledger and travels with lineage, the MRH projection and identity
  evidence. Being records are private on this fleet, so put no instance-private detail in it.

`<hub>` must equal this hub's id; a statement naming another hub is refused.

It is signed twice over the same bytes:
- **by the attester:** this hub's Sovereign key, read from the hub's identity, never from the statement. Per CBP
  and Pub, the signer must be a key the Sovereign controls and never the successor's own, or the label would be
  doing the work the signature should (the same point as hestia #1408). If the Sovereign's own presence has
  rotated under D4, the attester is its **current verified canonical key** per its own lineage. A signature by a
  key D4 says has rotated away is refused (CBP). A Sovereign of a different hub (for example a demo hub on the
  being's own machine) never qualifies, because its key is not this hub's (Pub);
- **by the successor:** `new`'s binding key, from the registry. Without that consent a Sovereign could graft any
  history, including a slashing, onto any published presence. That's the D4 argument again.

**The issue window (Pub).** H2's −60 s..+600 s was sized for one signer who submits at once. E is a two-party,
two-machine ceremony: the successor's key is on the being's disk, and the Sovereign's key is in the hub's vault.
So E fixes the order and splits the window:
- the successor countersigns first, and the Sovereign signs last, as part of the submitting envelope;
- the **envelope** is held to H2's normal window, so submission follows the Sovereign's signature at once;
- `issued_at` (the time the statement was drafted and countersigned) may be up to **24 h** before the envelope's
  timestamp, and no more than 60 s after it.

A replay is already folded (E4), and E3 is re-checked under the build lock, so the wider `issued_at` bound
costs little.

**E2, the route and event.**
- `POST /v1/hubs/:hub_id/lcts/attest-predecessor` takes a signed envelope whose signer **is** the founding
  Sovereign. A member envelope gets 403, with nothing witnessed.
- It witnesses `LctPredecessorAttested {old, new, issued_at, reason, attester_signature_hex,
  new_signature_hex, attested_by}`.
- Verification runs again under the build lock (`commit_pair_event_checked`), as `rotation_commit_check` does.
- **Custody of the attester key: a named gap, not a wall (CBP).** An unlocked hub holds the Sovereign key in its
  vault. The envelope is produced off-daemon, by the operator CLI with the vault passphrase, like the other
  operator-authored Sovereign acts, and the route verifies a signature but never mints one. That boundary is
  **procedural, not cryptographic**: the route cannot tell an envelope the CLI minted from one the daemon minted
  with the same key. "Verifies, never mints" is a property of the code we ship, not of the protocol. E ships with
  that default, does not wait for a custody tier, and does not claim to be one. Two things make the gap visible:
  - `attested_by` records the **channel** the envelope arrived through (the operator CLI session, or anything
    else), witnessed. A daemon-minted attestation then shows up as an anomaly on the ledger instead of being
    indistinguishable.
  - A census test pins that no daemon code path produces an `attester_signature_hex`, in the way hestia pins
    its `member_lct` consumers.

**Definition: live (one predicate, used everywhere in E; Legion).** An attested edge `old ⇢ new` is **live** when
its `LctPredecessorAttested` entry has no later `LctPredecessorAttestationWithdrawn` for the same pair. A verified
D4 edge is always live. "Has a successor" and "has a predecessor" below always mean *a live edge of either kind*,
unless a rule names the kind. E3, E4's folding, and the D-b1 guard amendment (E3a) all call this one predicate, so
the code has a single notion of "has a successor", not three.

**E3, preconditions** (each refusal witnesses nothing):
- `old != new`;
- both are published here;
- `new` is Active (a terminal or dormant successor cannot inherit). `old` may be in any status: a lost-key
  predecessor is often stale, and its status stays its own evidence;
- `new` has no successor, verified or attested (no cycles, the D-b1 rule);
- `new` has **no predecessor**, verified or attested (no joins; Legion). A rebuilt being mints a fresh key with no
  history, so it never needs a join. A `new` that already continues something would merge two lineages into one
  presence. This is lifted only if a real case shows up. It is distinct from E4's fork: a fork is one `old`
  with two `new`s, and a join is two `old`s into one `new`;
- `old` has no **verified** successor. A D4 rotation already says where its key went, and an attestation
  contradicting it is refused. To claim the verified link is wrong is a compromise-recovery question, which is
  out of scope here.

**E3a, the D-b1 guards read both kinds (Legion).** E adds a second successor relation, and D-b1's guards read only
the first:
- **The cycle guard.** `RotationStatement::verify` (`hub/hub-lib/src/lct_rotation.rs`, the #934 guard) checks only
  `state.lct_successors` for `new`. After an attested `A ⇢ B`, a D4 rotation `B → A` would pass and close a ring
  that neither guard sees. The #934 argument ("every canonical in a chain except its tip has a successor") holds
  per edge kind and fails across kinds. **E amends the guard to refuse a rotation whose `new` has any live
  successor, verified or attested.**
- **The reverse order: a verified rotation of an `old` that already has a live attested successor.** This is
  `old ⇢ B` attested (the key was "lost"), and later the old key signs `old → X`. It is E6's thief shape in its
  strongest form. **It is witnessed, not refused, and lineage reports `successor_kind_conflict`:** `successor` = X
  (verified), `attested_successor` = B, and neither is presented as *the* successor, the way D-b1 handles a
  fork. Refusing it would let a Sovereign judgment override a key-signed fact, the reverse of E-3's reasoning.
  Letting it win silently would hide the thief shape. Law sees both (FR5). The asymmetry with E3's last rule is
  deliberate: a judgment is refused against a standing fact, but a fact is never refused on the strength of a
  judgment. It is only marked as conflicting.

**E4, forks and replays** follow D-b1's rules:
- two different attested `new`s for one `old` are both witnessed and reported as
  `attested_successor_conflict`, with no single `attested_successor`;
- the same `old→new` pair is folded into the first entry, **among live entries only**. Once an attestation is
  withdrawn (E5), a fresh attestation of the same pair is a new entry. A withdrawal is a corrected judgment, and
  it can itself be corrected (CBP).

**E5, withdrawal.** The Sovereign can withdraw an attestation (`LctPredecessorAttestationWithdrawn {old, new,
index, reason, attested_by}`). It is signed by the Sovereign's *current verified* key (the E-1 rule) and arrives
through the same channel-witnessed path, so `attested_by` covers it as well. It needs no countersignature:
withdrawing a claim needs no consent from its subject (Legion). It is reversible because it is a judgment, and judgments get corrected. The
original entry stays on the ledger, and lineage drops it, citing the withdrawal. A verified D4 rotation has no
withdrawal, since it is a fact about keys.

**E6, evidence and projection.**
- `LctLineage` gains `attested_successor`, `attested_successor_conflict` and `attested_predecessors`, each with
  the witnessing index and `attested_by`.
- D-c's MRH projection gains `ledger` edges `attested_predecessor` / `attested_successor`, separate from
  `predecessor` / `successor`.
- D-a's identity evidence gains `hub_observations.attested_successor` (`{by, attested_at}` | `"none"` |
  `"unknown"`). An act by an `old` canonical **after** an attestation is the shape of a thief using the lost
  key, so law should see it. It is evidence only (FR5).
- On the NEW presence's acts, identity evidence gains `hub_observations.attested_predecessor` (`{old, by,
  attested_at}` | `"none"` | `"unknown"`). A consumer weighing `new` then sees that it claims continuity, under
  the label (CBP). This is also evidence only.

**Decisions to confirm (defaults in bold):**

| # | question | default | why |
|---|---|---|---|
| E-1 | who may attest | **this hub's Sovereign key only: its current verified key per D4** | CBP/Pub: a key the Sovereign controls. A council-threshold attester is a later option once council keys are in custody tiers |
| E-2 | successor countersignature | **required** | without it, the Sovereign can graft history (or slashing) onto anyone (the D4 argument) |
| E-3 | `old` with a verified successor | **refused** | an attestation must not contradict a key-signed fact. Disputing a verified link is compromise recovery (D6) |
| E-4 | withdrawal | **yes, Sovereign-signed, the original stays on the ledger** | it's a judgment, not a key fact |
| E-5 | evidence on old-key acts after attestation | **`hub_observations.attested_successor`** (and `attested_predecessor` on `new`) | a lost key that acts again may be a thief; law decides |
| E-6 | issue window | **successor first, Sovereign last; envelope under H2; `issued_at` ≤ 24 h before the envelope** | a two-machine ceremony doesn't fit ten minutes (Pub) |
| E-7 | attester custody | **ship the procedural boundary, named as a gap; witness the channel; census test** | a custody tier is the wall; E neither waits for it nor claims to be it (CBP) |
| E-8 | a verified rotation of an `old` with a live attested successor | **witnessed; lineage reports `successor_kind_conflict`** | a judgment never overrides a key fact, and the fact never silently wins (Legion) |
| E-9 | joins (a `new` that already has a predecessor) | **refused** | a rebuild has no history; lift only on a real case (Legion) |

**Tests (E):**
- a member-signed attestation is refused, with nothing witnessed;
- an attestation the Sovereign signed but the successor did not countersign is refused;
- with both signatures, lineage shows `attested_predecessors` on `new` and `attested_successor` on `old`, and
  `predecessors` / `successor` stay empty;
- `old` with a verified successor is refused; a `new` that has a successor is refused;
- two different `new`s give `attested_successor_conflict`; a replay or re-sign is folded;
- after a withdrawal the lineage drops the link, and both entries stay on the ledger;
- an act by `old` after an attestation carries `hub_observations.attested_successor`;
- the MRH projection labels the edges `attested_*`, never `predecessor` / `successor`;
- attest, withdraw, then attest again: lineage shows the link, and the ledger shows all three entries (CBP);
- a signature by a Sovereign key that D4 says has rotated away is refused (CBP);
- a Sovereign signature from another hub (a demo hub) over a statement for this hub is refused, and so is a
  statement whose `<hub>` is not this hub (Pub);
- a statement countersigned 15 min before the Sovereign signs is accepted; an `issued_at` 25 h before the
  envelope is refused (Pub);
- a `reason` containing `\n` or `\r` is refused, and so is one over 280 bytes (Pub);
- census: no daemon code path produces an `attester_signature_hex` (CBP);
- `attested_by` carries the arrival channel; an act by `new` carries `hub_observations.attested_predecessor`;
- mixed-kind cycles (Legion): attest A⇢B, then rotate B→A, is refused with nothing witnessed. So is the long form:
  attest A⇢B, rotate B→C, rotate C→A;
- after a withdrawal of A⇢B, rotate B→A is allowed again (the guard reads *live* edges);
- reverse order (Legion): attest old⇢B, then the old key rotates old→X. That is witnessed, and lineage shows
  `successor_kind_conflict` with both heads and neither as the successor;
- joins (Legion): rotate X→B, then attest A⇢B, is refused; attest A⇢B, then attest A'⇢B, is refused;
- the withdrawal is refused when signed by a rotated-away Sovereign key, and it carries `attested_by`.

**Not in E:**
- an attester other than the Sovereign (council threshold, an operator key in a custody tier);
- compromise recovery (D6);
- linking more than one hop in one statement;
- any trust verdict (FR5).

*Reviews on `b44b0820` (10-27): cbp-claude GO on the shape, with three points: custody named as a procedural
gap, plus a witnessed channel and a census test; fold among live entries only; the attester is the Sovereign's
current verified key. Pub GO, agreeing with CBP, plus: the issue window for a two-machine ceremony; `reason`
framing; `reason` is public; a demo-hub Sovereign is refused. All are taken above.*

*legion-claude on `a73a4aa1`: GO on the shape. Taken: (1) D-b1's cycle guard reads live successors of both kinds
(E3a); (2) a verified rotation after an attestation is witnessed as `successor_kind_conflict` (Legion's lean
(a), E-8); (3) joins refused (E-9); (4) a single "live" predicate; (5) the withdrawal signer and channel.*

**Asked of dp alongside E (question 5 from 10-27, a law question, not code):** should default law honour a
self-declared `void` / `slashed`? Since #935 those statuses are terminal, so honouring one is a one-way door that
the holder can walk through on its own say-so.

## 7. Done

Done means Hub can answer, without guessing:

> "This request came through Hub member X; X resolves to canonical presence Y through evidence Z; Y currently presents lifecycle/relationship evidence E."

The law can then decide what that evidence licenses.
