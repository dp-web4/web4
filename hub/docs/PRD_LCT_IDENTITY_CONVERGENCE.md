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

## 7. Done

Done means Hub can answer, without guessing:

> "This request came through Hub member X; X resolves to canonical presence Y through evidence Z; Y currently presents lifecycle/relationship evidence E."

The law can then decide what that evidence licenses.
