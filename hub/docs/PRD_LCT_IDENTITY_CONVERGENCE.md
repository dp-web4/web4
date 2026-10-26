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
  resolved] }`. FR5's "unknown is not active" holds by construction: a missing fact is listed in `unknown`,
  never defaulted.
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
- **To the gate:** `R6Request` gains an optional `evidence` field (YAML/JSON, like `payload`). Default
  law ignores it, so behaviour is unchanged. A society's law can match on it (for example, refuse
  `referenced_act` when `caller_auth.method == member_key_pin` once that is law, which is C2's exit, or when
  `claimed_status != active`).
- **To the ledger:** consequential witnessed acts carry the evidence they relied on (accountability clause A).
  First target: `ReferencedAct` gains optional `caller_auth`, `registry_version`, and `evidence_digest`
  (a digest of the canonical `IdentityEvidence` bytes the gate saw). All three are skip-if-none, so old
  entries keep their bytes. That's the same pattern as `on_behalf_of`. `caller_auth` alone records less
  than the gate may have relied on. Once law matches on `claimed_status` or registry state, a replay can
  re-derive the decision only if it can name the exact evidence. Other events follow only where a reviewer
  names one.

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
  rejected: it is a verdict chosen silently, which FR5 rules out.
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
| D2 | where evidence reaches the gate | **an optional `R6Request.evidence`; default law ignores it** | law decides; C2's exit becomes a law rule, not code |
| D3 | which ledger events carry evidence first | **`ReferencedAct` only: `caller_auth` + `registry_version` + `evidence_digest`** | it is the consequential act the channel carries, and the gate's decision must be re-derivable from the entry; the others are named per review |
| D4 | how rotation is verified | **one statement signed by the old key and countersigned by the new, witnessed as `LctRotated`; forks are witnessed and reported as `successor_conflict`; later old-key acts carry `superseded_key_used`** | a `rotated_from` edge signed only by the new key proves nothing about the old one; an old key alone could graft its lineage onto anyone; "first one wins" is a silent verdict |
| D5 | per-member pin refusal | **yes, witnessed, requested over a vouched-key channel, reversible the same way; losing the vouched key afterwards is an accepted lockout (recovery = new canonical)** | delivers C4's cold binding key to early movers without waiting for law |
| D6 | re-rooting a canonical LCT onto a vault identity (`legacy_alias`, C4) | **out of D**; it needs its own design with Legion | it changes what "canonical" means for a member, not just evidence |
| D7 | MRH projection writes anything? | **no: read-only, every edge labelled `ledger` (cites an index), `registry` (cites a version), or `self_declared`; authenticated, pairings visible to their parties only** | FR6: the ledger stays authoritative; the pairing graph is sensitive |

**Tests (per sub-slice):**
- **D-a:**
  - the gate sees `evidence`, and default law is unchanged;
  - a `ReferencedAct` carries `caller_auth`, old entries replay byte for byte;
  - `unknown` lists a missing registry document instead of reporting active;
  - the gate decision can be re-derived from the ledger entry: `evidence_digest` matches the evidence
    replayed at `registry_version`;
  - a non-active `claimed_status` carries `against_interest: true`, and default law is unchanged;
  - a quiet member reports `last_witnessed_act`, never `dormant`.
- **D-b:**
  - a rotation statement signed by the new key alone is refused;
  - one signed by the old key alone is refused, i.e. naming a successor that has not countersigned;
  - a statement with both signatures links `successor` both ways;
  - a second successor for the same old key is witnessed, never overwrites the first, and yields
    `successor_conflict` with no single verified `successor`;
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

*Revised 2026-10-26 after the Legion (6414105527) and Sprout (6414108992) reviews. On forks, the two
reviews differ: Legion proposed "first witnessed, second is conflict evidence", Sprout proposed "both
witnessed, law decides". This draft takes Sprout's, because it keeps Legion's requirement (never overwritten,
never dropped) without the hub choosing a winner.*

## 7. Done

Done means Hub can answer, without guessing:

> "This request came through Hub member X; X resolves to canonical presence Y through evidence Z; Y currently presents lifecycle/relationship evidence E."

The law can then decide what that evidence licenses.
