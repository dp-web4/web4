# `did:web4` — the DID interop face of an LCT

**Status**: Design note (sketch). Public / standards-facing. Companion to
`docs/specs/heterogeneous-identity.md` (the Web4-native identity model) and the
`get_member_public_key` resolver proposal (`shared-context/forum/
legion-proposal-member-pubkey-resolver-2026-06-11.md`).

**Date**: 2026-06-11 • **Author**: Legion (Fable 5, with dp)

---

## Purpose

W3C DID Core is an **identifier-and-key** layer: a DID resolves to a DID
Document listing public keys, verification relationships, and service
endpoints — nothing more. Web4's LCT *contains* that function and keeps going
(T3/V3 trust, MRH context, witnessing, ATP). `did:web4` is the **projection**
that lets the existing DID/VC/EUDI ecosystem resolve a Web4 entity without
Web4 having to reinvent wire formats.

**An LCT can present a DID face; a DID cannot present an LCT face.** The DID
Document is a lossy view — the identifier+keys slice — of the full LCT. The
trust/relationship layer has, by design, **no DID Document representation**; a
verifier who wants it must speak Web4.

## Method name + identifier syntax

```
did:web4:<authority>:<lct-uuid>
            │           └─ the entity's LCT id (UUID)
            └─ the resolving hub's host authority (e.g. hub.example.com)
```

Mirrors `did:web` (domain-anchored), but resolution returns a **hub-signed**
binding, not a TLS-only fetch. The authority is the hub that vouches for the
LCT→pubkey binding (a Web4 hub *is* a witness — see the resolver proposal). The
identifier is self-contained: a resolver needs only the DID string.

`did:web4:hub.example.com:550e8400-e29b-41d4-a716-446655440000`

Degradation path: where `did:web4` isn't recognized, the same entity can
present a plain `did:web:hub.example.com:lct:550e8400...` face (a DID Document
served at a well-known path). `did:web4` is the native form; `did:web` is the
lowest-common-denominator fallback for maximum interop.

## DID Document mapping

| DID Document field | Source in Web4 |
|---|---|
| `id` | the `did:web4:...` string |
| `verificationMethod[0]` | the LCT's Ed25519 public key, as `Multikey` / `Ed25519VerificationKey2020` |
| `authentication`, `assertionMethod` | reference `#key-0` (the LCT signs as itself) |
| `keyAgreement` | **(v0: omitted)** — the Web4 channel key (`pair_channel`) is an *independent* X25519 key, NOT derived from the Ed25519 identity key, so it can't be a derived DID verification method. The channel is advertised as a `Web4Channel` *service* instead. (A future option: bind a declared X25519 channel pubkey into the LCT and expose it as `keyAgreement`.) |
| `capabilityInvocation`, `capabilityDelegation` | reference `#key-0` — the LCT is authorized to invoke and to delegate (the *grants* it has issued are separate objects, below) |
| `service[].Web4Hub` | the hub REST base (`https://<authority>/v1`) — where trust/witness/membership live |
| `service[].Web4Channel` | the sealed-channel endpoint (the `pair_channel` surface) for E2E messaging |

### What is deliberately NOT in the DID Document
- **T3/V3 trust** — no DID field; computed, Web4-native.
- **MRH context** — no DID field.
- **Witness attestations** — a VC is the closest DID-world analogue (a single
  signed claim); the recursive witness structure stays Web4-native. A verifier
  may fetch a VC-shaped *leaf* via the `Web4Hub` service, but the tree is not
  expressed in the DID Document.
- **DelegatedAuthority grants** the LCT has *issued* — these are ZCAP-like
  objects, not the subject's own keys, so they don't belong in the subject's
  DID Document. They're retrievable via the `Web4Hub` service or presented as
  separate verifiable objects. (`capabilityDelegation` only declares that
  `#key-0` *may* delegate — standard DID semantics.)

### Non-transferability — honest gap
W3C DID has no field for "this identifier cannot be transferred." Non-
transferability is a **Web4-layer guarantee** (presence semantics + coherence
thresholds + witnessing), not expressible in the DID Document. A DID-only
consumer sees an ordinary key; the non-transferability holds only for
consumers who also evaluate the Web4 trust layer. State this plainly — it is
the one place the projection silently drops a core property.

## Resolution

```
resolve(did:web4:<authority>:<lct-uuid>):
  1. GET https://<authority>/v1/members/<lct-uuid>/pubkey   (the resolver endpoint)
  2. hub returns { pubkey_hex, hub_lct, issued_at, hub_signature }   (or 404/null, opt-in)
  3. verify hub_signature against <authority>/.well-known/web4-hub.json → hub_pubkey_hex
  4. assemble the DID Document from the verified pubkey + service endpoints
  → didDocument + didResolutionMetadata{ contentType, retrieved, hub_attested:true }
```

This is exactly the `get_member_public_key` resolver indirection, viewed as DID
resolution. The hub-signed binding makes `did:web4` resolution **attested**,
addressing the `did:web` weakness (which trusts TLS/DNS alone). Enumeration
defense and opt-in carry over from the resolver proposal: a non-opted-in or
non-member LCT resolves to `notFound`, indistinguishable from a stranger.

### Deactivation
`LctStatus::Voided | Slashed` → resolution returns
`didDocumentMetadata.deactivated = true`. The void/slash is itself a
ledger-witnessed Web4 event; the DID metadata reflects it.

## Conformance

- DID Documents are W3C DID Core 1.0 conformant JSON-LD (`@context`:
  `https://www.w3.org/ns/did/v1` + a `https://web4.io/ns/did/v1` extension for
  the `Web4Hub`/`Web4Channel` service types).
- Resolution follows the DID Resolution spec (didResolutionMetadata,
  didDocumentMetadata).
- Verification material uses `Multikey` (multibase/multicodec), the current
  Data Integrity convention, so EUDI / Veramo / Entra tooling consumes it
  unmodified.

## Where this sits relative to the private work

This mapping is **generic and public-eligible** — it discloses no novel
mechanism. It exposes only the identifier+keys+endpoints slice that DID
standardizes. The witness tree, constellation-MFA, replicated log, and SITL
machinery are *not* referenced here and stay behind the dev-hub boundary. The
`Web4Hub` service endpoint is the single door from the DID world into the
Web4-native layer; what's behind that door is Web4's, not the DID Document's.

## Open questions

- **Authority binding**: one canonical hub per LCT in the DID string, or
  multi-hub (an LCT vouched by several hubs)? Multi-hub = stronger (constellation
  of vouchers) but complicates a single resolvable identifier. Likely: the DID
  string names one *resolution* authority; additional vouchers are discoverable
  via that hub. (Mirrors the heterogeneous-identity constellation, one level up.)
- **did:web fallback document hosting**: served by the hub at a well-known
  path, or generated on demand? On-demand keeps it consistent with the live
  resolver.
- **keyAgreement**: `pair_channel` uses independent X25519 keys (confirmed in
  code), so there's no Ed25519→X25519 derivation to expose. To offer
  `keyAgreement` (DIDComm encryption to a Web4 entity), the LCT would need to
  *carry* a declared X25519 channel pubkey. Decide whether that belongs in the
  LCT or stays a service-level concern.
