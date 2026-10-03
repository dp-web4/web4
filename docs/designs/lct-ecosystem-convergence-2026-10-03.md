# LCT Ecosystem Convergence

**Date:** 2026-10-03  
**Status:** Working convergence note  
**Tracking:** [web4#874](https://github.com/dp-web4/web4/issues/874), [Hub#875](https://github.com/dp-web4/web4/issues/875), [hestia#1202](https://github.com/dp-web4/hestia/issues/1202), [SAGE#340](https://github.com/dp-web4/SAGE/issues/340)

## Executive summary

The Web4 ecosystem now contains real key-bound LCT presence documents, but several live operational surfaces still use **LCT** to mean older routing/member identifiers.

Three identifier classes coexist:

```text
HubMemberId       = Hub-local UUID used for membership/routing
LegacyLctId       = lct:web4:member:<hex>, Hestia's pre-presence member label
Canonical LctId   = lct:web4:mb32:b..., key-derived presence identifier
```

The first two are useful references. They are not the same object as the third.

The convergence target is therefore **resolution, not replacement**:

```text
name / HubMemberId / LegacyLctId
              |
              v
        Canonical LctId
              |
              v
        verified LCT document
              |
              v
binding + operational keys + MRH + citizenship + lifecycle evidence
```

Compatibility aliases may remain indefinitely. They must stop occupying positions of semantic authority where a relying party believes it is holding the entity's Web4 presence itself.

The governing principle remains:

> Web4 makes identity, relationship, authority and history evidence inspectable. It does not turn an identifier, tensor or lifecycle label into a universal trust verdict.

---

## 1. What is already working

### 1.1 Canonical-ish key-derived presence exists

`web4-core::derive_lct_id` derives:

```text
lct:web4:mb32:b + base32_lower_no_pad(sha256(raw_public_key))
```

Hub registry ingest verifies the binding and identifier rather than trusting a claimed id.

SAGE beings now publish real documents with:
- Ed25519 public keys;
- binding proofs;
- key-derived `mb32` ids;
- MRH;
- citizenship references for some beings;
- registry-publish provenance.

Hestia now mints persistent member LCTs in `member_registry.rs`, signs their bindings, and preserves the historical `lct:web4:member:<hex>` value as a verifiable `LegacyAlias::HestiaMember`.

This means the migration substrate exists. The remaining work is primarily to make the older identifiers resolve into that substrate instead of competing with it.

### 1.2 Hub already separates presence registry from reputation projection

Hub's `RegistryEntry` stores verified LCT documents.

Hub's role-contextual reputation is separately projected as:

```text
(subject_lct, role_lct) -> T3/V3
```

That separation is valuable and should not be collapsed merely to satisfy older prose that depicts one global T3/V3 block embedded directly in every LCT.

### 1.3 Existing aliases preserve continuity

The Hestia legacy-alias mechanism is the right pattern:

- old identifier remains resolvable;
- the alias is re-derived and verified;
- trust/action history can remain attributable to the same entity;
- the new canonical LCT is not forced to reuse the old identifier format.

This should be generalized rather than bypassed.

---

## 2. Clear ecosystem gaps

## 2.1 Hub member UUIDs are references, not LCT presence

Hub membership and hub-mesh use UUID values in fields and variables named as LCTs, e.g. `member_lct_id` and `MY_LCT`.

The sealed channel is not unauthenticated: the Hub pins an operational key to the member UUID and verifies signed envelopes.

The semantic gap is narrower but important:

> A cryptographically authenticated Hub member reference is not automatically a canonical Web4 LCT presence document.

### Convergence

Use explicit vocabulary:

- `HubMemberId` — Hub-local UUID membership/routing reference;
- `LegacyLctId` — compatibility identity alias;
- `LctId` / `CanonicalLctId` — key-derived Web4 presence id.

A HubMemberId should resolve to canonical presence where such presence has been published. An unresolved old member remains an explicitly lower-evidence member; the resolver must not fabricate an LCT.

Tracked by [Hub#875](https://github.com/dp-web4/web4/issues/875).

---

## 2.2 Canonical identifier prose is behind the implementation

The current LCT core spec still describes deriving `lct_id` from the binding proof. The running Rust implementation and registry ingest derive it from the public key.

The implementation contract is preferable because:
- the same key deterministically produces the same id;
- `created_at` / signature randomness cannot change the id;
- possession of the key remains the cryptographic root of the identifier;
- offline/global minting requires no allocator.

[web4#819](https://github.com/dp-web4/web4/pull/819) contains the correct identifier correction but also contains MRH/adjudication claims that have been held for overstatement.

### Convergence

Land the identifier correction independently or rewrite the MRH section to preserve:
- bits determine identifier equality;
- graph/history provide contextual presence/continuity evidence;
- counterparty evidence is externally checkable only where it is independently signed/corroborated;
- law/adjudication decides what that evidence means.

Do not make raw MRH richness, edge count or a copied-key fork into an automatic identity oracle.

---

## 2.3 T3/V3 placement is internally inconsistent in canon

The LCT core spec says every LCT MUST contain `t3_tensor` and `v3_tensor`.

The same canonical family says:
- trust/value is role-contextual;
- implementations MUST NOT compute global role-agnostic trust scores;
- each role maintains separate T3/V3 state.

Hub's `(subject_lct, role_lct)` projection follows the latter rule.

### Convergence direction

The LCT should carry or resolve **role-contextual reputation evidence**, rather than one authoritative global tensor.

Acceptable shapes include:
- references/indexes to role-contextual tensor records;
- a non-authoritative summary explicitly marked as such;
- registry/ledger resolution keyed by entity-role pair.

Do not regress Hub to one global score simply to satisfy the current LCT example.

This requires a canonical ruling under [web4#874](https://github.com/dp-web4/web4/issues/874).

---

## 2.4 Lifecycle currently mixes two different dimensions

The current core spec describes revocation:

```text
active | revoked
reason = compromise | superseded | expired | violation
```

`web4-core::LctStatus` and the whitepaper also use:

```text
Active | Dormant | Void | Slashed
```

These can represent different facts.

### Proposed separation

```text
participation_state = active | dormant | void | slashed

revocation = {
    revoked: bool,
    reason: compromise | superseded | expired | violation | ...,
    ts,
    successor?
}
```

Examples:
- rotated key: old LCT is revoked/superseded, not necessarily slashed;
- natural conclusion: void;
- punitive conclusion: slashed;
- temporarily inactive entity: dormant.

This keeps accountability history while avoiding one enum carrying both participation and credential-validity semantics.

Canonical decision remains tracked by [web4#874](https://github.com/dp-web4/web4/issues/874).

---

## 2.5 Hardware assurance is still evidence-poor

[web4#730](https://github.com/dp-web4/web4/issues/730) already owns this gap.

Key points:
- assurance must be derived from evidence, not merely declared;
- level 5 requires a real carrier for hardware evidence;
- capability/provenance level and key-custody assurance may be orthogonal axes;
- older published documents can carry stale software-bound ceilings.

Do not duplicate #730. Repo-local migration work should treat its answer as an upstream dependency.

---

## 2.6 Operational surfaces do not consistently consume lifecycle/presence evidence

A name or member UUID can currently be sufficient to route a message even though the canonical LCT registry may contain richer information:
- binding;
- operational-key vouchers;
- rotation lineage;
- citizenship;
- lifecycle state.

### Convergence

Consequential routing should resolve the reference to canonical presence and surface that evidence to the relying law/gate.

Important distinction:

```text
resolver -> evidence
law/relying party -> decision
```

The resolver MUST NOT become a hidden trust policy engine.

---

## 3. Repo-specific convergence

### 3.1 Hub

Tracked by [Hub#875](https://github.com/dp-web4/web4/issues/875) and `hub/docs/PRD_LCT_IDENTITY_CONVERGENCE.md`.

Main tasks:
1. introduce `HubMemberId` vs `CanonicalLctId`;
2. persist witnessed member -> canonical-LCT mapping;
3. provide one alias/member/canonical resolver;
4. prefer LCT-vouched operational keys;
5. expose lifecycle evidence before consequential actions;
6. project existing witnessed Hub relationships into MRH rather than inventing a second mutable relationship truth.

### 3.2 Hestia

Tracked by [hestia#1202](https://github.com/dp-web4/hestia/issues/1202).

Main tasks:
1. prefer canonical member LCT outward;
2. keep `lct:web4:member:<hex>` only as verified migration alias;
3. preserve trust-grain continuity;
4. use canonical operational-key vouchers;
5. make rotation/lifecycle alias-safe;
6. keep #840 as the separate copied-seed/presence-uniqueness lane.

### 3.3 SAGE

Tracked by [SAGE#340](https://github.com/dp-web4/SAGE/issues/340).

Main tasks:
1. one source of truth for live being canonical identity;
2. inventory/deprecate old LCT-shaped formats from live paths;
3. map routing/member IDs to being LCTs explicitly;
4. complete citizenship/provenance when Hub can verify it;
5. republish stale assurance fields reproducibly;
6. preserve lineage across being key rotation.

---

## 4. Migration sequence

Recommended order:

1. **Name the identifier layers correctly.**
   No behavior change required; stop semantic overload first.

2. **Land public-key-derived canonical ID semantics.**
   Recut/narrow #819.

3. **Introduce one resolver boundary in Hub.**
   Member UUID / legacy alias / canonical id -> verified LCT document.

4. **Move operational-key verification behind canonical presence.**
   Preserve UUID key pins as compatibility evidence until migrated.

5. **Make consequential routing lifecycle-aware.**
   Surface evidence; keep decision in law/gate.

6. **Project existing witnessed relationships into MRH.**
   Membership, role occupancy, pairings/intros and witnessing already exist as ledger facts.

7. **Resolve canonical T3/V3 placement and lifecycle vocabulary.**

8. **Finish hardware-derived assurance under #730.**

---

## 5. Non-goals

This convergence does **not** require:

- deleting Hub UUIDs;
- rewriting historical ledgers;
- making hardware identity mandatory;
- rejecting self-issued or weakly witnessed LCTs by protocol fiat;
- forcing one global trust score;
- treating every MRH edge as independent or bidirectionally co-signed;
- changing a being/member's local human-readable name during key rotation.

The intended result is simpler:

> Routing identifiers point to presence. Presence exposes evidence. Law decides what the evidence permits.
