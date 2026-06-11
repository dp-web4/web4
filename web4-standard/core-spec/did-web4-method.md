# Web4 DID Method Specification (`did:web4`)

**Version**: 1
**Status**: Draft — Phase 0 implemented in `web4-core::did` (reference).
**Companion**: [`LCT-linked-context-token.md`](./LCT-linked-context-token.md) — the LCT this method projects.
**Design note**: `docs/designs/did-web4-mapping.md`. **Adoption plan**: `docs/strategy/eudi-resolvability-plan.md`.

This document defines the **`did:web4` DID Method**: how a Web4 LCT is presented
as a W3C [DID Core 1.0] identifier and resolved to a conformant DID Document. It
is **normative** for the identifier syntax, the LCT→DID-Document mapping, and
the resolution procedure.

> Notation: MUST/SHOULD/MAY per RFC 2119.

---

## 1. Scope and intent

`did:web4` is the **interop face** of an LCT — the identifier-and-keys
projection that lets W3C DID / Verifiable Credential / EUDI tooling resolve a
Web4 entity. It is **deliberately lossy**: it exposes only what DID Core
standardizes (identifiers, public keys, verification relationships, service
endpoints). Web4's trust and relationship layer (T3/V3, MRH, witnessing,
ATP/ADP) has **no DID Document representation** and MUST NOT be encoded into
one; it is reached only via the `Web4Hub` service endpoint (§6).

Design principle: *an LCT can present a DID face; a DID cannot present an LCT
face.* The DID Document is a one-way projection.

## 2. Method name

The method name is `web4`. A DID that uses this method MUST begin with
`did:web4:`.

## 3. Identifier syntax

```
did-web4         = "did:web4:" authority ":" lct-id
authority        = host                      ; the resolving hub's host authority
lct-id           = UUID                       ; RFC 4122 string form
```

- `authority` is the host of the **hub** that resolves the LCT→pubkey binding
  (§5). It MUST be a DNS host (optionally with port, percent-encoded per
  `did:web` conventions if a port is present).
- `lct-id` is the entity's LCT id in canonical RFC 4122 string form.
- The `lct-id` MUST be the final `:`-delimited segment; `authority` is
  everything between `did:web4:` and the last `:`.

Example: `did:web4:hub.example.com:550e8400-e29b-41d4-a716-446655440000`

### 3.1 Single resolution authority (normative)

A `did:web4` identifier names **exactly one** resolution authority. An LCT MAY
be vouched by multiple hubs (a constellation of vouchers — see
`docs/specs/heterogeneous-identity.md`), but the DID string designates a single
hub for *resolution*; additional vouchers are discoverable via that hub (§6).
This keeps the identifier self-contained and resolvable from the string alone.

### 3.2 `did:web` fallback

Where `did:web4` is not recognized, the same entity SHOULD be presentable as a
`did:web` identifier hosting the equivalent DID Document at a well-known path,
for lowest-common-denominator interop. `did:web4` is the native form;
`did:web` is the fallback.

## 4. DID Document mapping (normative)

A resolver MUST construct the DID Document as follows:

| DID Document field | Source |
|---|---|
| `@context` | `["https://www.w3.org/ns/did/v1", "https://web4.io/ns/did/v1"]` |
| `id` | the `did:web4:…` string |
| `verificationMethod[0]` | the LCT's Ed25519 public key as `Multikey` (§4.1) |
| `authentication` | `["<id>#key-0"]` |
| `assertionMethod` | `["<id>#key-0"]` |
| `capabilityInvocation` | `["<id>#key-0"]` |
| `capabilityDelegation` | `["<id>#key-0"]` |
| `service` | `Web4Hub` and optionally `Web4Channel` (§6) |

The single verification method has fragment `#key-0`.

### 4.1 Verification material

The Ed25519 public key MUST be encoded as a `Multikey` `publicKeyMultibase`
value: multicodec `ed25519-pub` header `0xed 0x01`, followed by the 32-byte raw
key, encoded base58btc with a leading `z`. (This yields the conventional
`z6Mk…` form.)

### 4.2 What MUST NOT appear

- T3/V3 trust scores, MRH context, ATP/ADP balances, and witness attestations
  MUST NOT be encoded in the DID Document.
- `DelegatedAuthority` grants the subject has **issued** MUST NOT appear as
  verification methods (they are not the subject's own keys). `capabilityDelegation`
  declares only that `#key-0` MAY delegate, per DID Core semantics. Issued
  grants are retrievable via the `Web4Hub` service or presented as separate
  verifiable objects.

### 4.3 `keyAgreement` (v1: absent)

This version does not emit `keyAgreement`. The Web4 sealed-channel key
(`pair_channel`) is an **independent** X25519 key, not derived from the Ed25519
identity key, so it cannot be expressed as a derived verification method. The
channel is advertised as a `Web4Channel` service (§6). A future version MAY add
`keyAgreement` if an LCT carries a declared X25519 channel public key.

## 5. Resolution (normative)

To resolve `did:web4:<authority>:<lct-id>`:

1. `GET https://<authority>/v1/members/<lct-id>/pubkey`.
2. On success the hub returns a signed binding
   `{ pubkey_hex, hub_lct, issued_at, hub_signature }`.
3. The resolver MUST verify `hub_signature` against the hub's public key from
   `https://<authority>/.well-known/web4-hub.json` (`hub_pubkey_hex`).
4. The resolver MUST assemble the DID Document (§4) from the **verified** key.
5. Resolution metadata SHOULD include `hub_attested: true`.

This is the Web4 member-pubkey resolver viewed as DID resolution. Because the
binding is **hub-signed**, `did:web4` resolution is *attested* — stronger than
`did:web`, which trusts TLS/DNS alone.

### 5.1 Not found / privacy

If the LCT is not a member of the authority hub, or the member has not opted in
to public key resolution, the resolver MUST return `notFound`. The two cases
MUST be **indistinguishable** (same status, same body) so resolution cannot be
used to enumerate membership.

### 5.2 Deactivation

If the LCT status is `Void` or `Slashed`, resolution MUST set
`didDocumentMetadata.deactivated = true`. The status change is itself a
ledger-witnessed Web4 event.

## 6. Service endpoints

| `type` | `serviceEndpoint` | Meaning |
|---|---|---|
| `Web4Hub` | `https://<authority>/v1` | The door into the Web4-native layer: trust, witness, membership, issued delegations. |
| `Web4Channel` | the sealed-channel endpoint | E2E-encrypted messaging (`pair_channel`). |

`Web4Hub` SHOULD be present. `Web4Channel` MAY be present.

## 7. Conformance

- DID Documents MUST be valid W3C [DID Core 1.0] JSON-LD.
- Resolution MUST follow [DID Resolution] (`didResolutionMetadata`,
  `didDocumentMetadata`).
- Verification material MUST use `Multikey` per §4.1.

## 8. Security considerations

- **Attested resolution.** The hub-signed binding (§5) defends against the
  `did:web` weakness of TLS-only trust. Verifiers MUST check `hub_signature`.
- **Non-transferability is not expressible.** DID Core has no field for it; an
  LCT's non-transferability is a Web4-layer guarantee (presence semantics,
  coherence thresholds, witnessing) and holds only for consumers that also
  evaluate the Web4 trust layer. A DID-only consumer sees an ordinary key.
- **Enumeration.** §5.1 — `notFound` MUST be uniform across non-member and
  opted-out cases.

## 9. Reference implementation

`web4-core::did` (`web4-core/src/did.rs`): `did_web4`, `parse_did_web4`,
`ed25519_multikey`, `DidDocument::from_lct`, `DidDocumentMetadata::for_lct`.
Phase 0 (DID Document construction + identifier + deactivation) is implemented
and tested. Resolution (§5) is provided by the hub's member-pubkey endpoint.

## 10. References

- [DID Core]: W3C Decentralized Identifiers (DIDs) v1.0.
- [DID Resolution]: W3C DID Resolution.
- `did:web` Method Specification (the fallback form, §3.2).
- Companion Web4 specs: `LCT-linked-context-token.md`,
  `presence-protocol.md`; `docs/specs/heterogeneous-identity.md`.
