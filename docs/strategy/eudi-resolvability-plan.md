# Plan: making LCTs EUDI-resolvable

**Status**: Plan (sketch). Public / standards-facing. Gated by
`docs/designs/did-web4-mapping.md`.

**Date**: 2026-06-11 • **Author**: Legion (Fable 5, with dp)

> Cutoff caveat: EUDI / eIDAS 2.0 is a moving regulatory target (ARF versions,
> trusted-list mechanics, jurisdictional rollout). Treat version-specific
> claims here as "verify before relying"; the layering is stable, the specifics
> are not.

## What "EUDI-resolvable" actually requires

The EU Digital Identity Wallet (EUDI, under eIDAS 2.0) is **not** a DID system
with trust bolted on — it's a specific stack, and being "resolvable" means
fitting four distinct pieces, only one of which is the identifier:

1. **Identifier** — how the issuer/subject is named. EUDI profiles accept
   `did:web` and x.509; `did:web4` is not (yet) recognized. → we present a
   `did:web` face (the fallback in the mapping note).
2. **Credential format** — **SD-JWT-VC** (IETF) and **ISO mdoc / mDL**
   (18013-5). A Web4 attestation must be expressible as one of these to enter a
   wallet. → we wrap Web4 claims as SD-JWT-VC.
3. **Protocols** — **OpenID4VCI** (issuance) and **OpenID4VP** (presentation).
   The wallet pulls credentials over OID4VCI and presents over OID4VP. → the
   hub/hestia must speak these.
4. **Trust anchor** — to be an *accepted* issuer, you must be on a member-state
   **trusted list** (ETSI TS 119 612-style; LOTL). **This is governance/legal,
   not code, and it is the real barrier.** Without it, a wallet will resolve
   and parse our credential but mark the issuer untrusted.

The honest framing: **inside the EUDI envelope, Web4 is a credential-format +
protocol citizen, and its native trust layer (T3/V3, witnessing) lives
*outside* the envelope.** EUDI's trust is trusted-lists; we don't replace that
within EUDI — we interoperate, and offer the richer Web4 trust to parties who
opt to evaluate it. Trying to inject Web4's trust model into EUDI's would be
fighting the regulation.

## Phasing

### Phase 0 — DID face (code; small; do first)
`did:web4` + `did:web` projection of an LCT (the mapping note). An LCT becomes
resolvable as a DID Document by any W3C-DID tool. **No EUDI dependency** — pure
DID interop, the foundation everything else stands on. *This is the buildable
piece and the only one with no external gate.*

### Phase 1 — SD-JWT-VC issuance (code; medium) — ✅ DONE (`web4-core::sd_jwt_vc`)
Implemented: IETF SD-JWT + SD-JWT-VC issuance — EdDSA JWS signed by an LCT key,
salted `_sd` digests + detached disclosures, compact serialization, optional
`cnf` holder binding, and verification (issuer sig + disclosure-digest match +
selective disclosure). `web4_presence_credential()` shows the Web4 pattern
(assurance level as a selectively-disclosable claim). 6 tests incl. selective
disclosure + tamper rejection. Below is the design it realizes:

Express a Web4 attestation as an SD-JWT-VC:
- Issuer = an LCT (presented as did:web). Subject = an LCT.
- Claims = a *flattened, lossy* projection of a Web4 statement. E.g. a
  constellation/assurance attestation → `{ vct: "Web4Presence", assurance:
  "multi_device", ... }`; a T3 facet → a claim with the score. Selective
  disclosure (SD-JWT salts) maps conceptually onto MRH-scoping.
- The rich witness structure collapses to a signed claim — acceptable; that's
  what crossing into the VC world costs. The full structure stays fetchable via
  the `Web4Hub` service for parties who want it.

### Phase 2 — OID4VCI / OID4VP (code; medium-large) — round trip wired ✅ (issuer + verifier)
**Protocol library DONE** — the reusable, fully-tested core:
- SD-JWT-VC presentation lifecycle completed: `present()` (holder Key-Binding
  JWT bound to verifier nonce+aud, selective disclosure at present-time) +
  `verify_presentation()` (issuer sig + KB-JWT + nonce/aud/freshness/sd_hash).
- OID4VCI pre-authorized-code flow: issuer metadata, credential offer,
  `build_holder_proof`/`verify_holder_proof` (holder key-possession → cnf-bind).
- OID4VP: `PresentationRequest/Response`, `build_presentation` /
  `verify_presentation_response` (vct + required-claim checks).
- 4 tests incl. the full VCI→VP round trip. The HTTP endpoints are thin
  wrappers over these functions.

**Hestia (person-scale issuer) HTTP wiring ✅** — `hestia-core` now mounts the
OID4VCI issuance surface over the library (`core/src/server/http.rs`):
- `GET /.well-known/openid-credential-issuer` → `CredentialIssuerMetadata`.
- `POST /vci/nonce` → mints a single-use `c_nonce` (tracked in `ServerState`).
- `POST /vci/credential` → `verify_holder_proof` against the issued nonce
  (consumed; replay rejected), then issues a `cnf`-bound `Web4Presence`
  SD-JWT-VC signed by the daemon's vault identity (`did:web4:<host>:<lct>`),
  with the constellation's assurance tier as a selectively-disclosable claim.
Smoke-tested end-to-end (metadata → nonce → proof → credential; replay 400).

**Hub (society-scale relying party) OID4VP verifier ✅** — `hub-daemon` now
mounts the verifier over the same library:
- `POST /v1/hubs/:hub_id/vp/request` → mints a single-use presentation request.
- `POST /v1/hubs/:hub_id/vp/response` → verifies the wallet's presentation. The
  issuer (`did:web4:<host>:<member-lct>`) is resolved to its pinned pubkey via
  the hub's **own member roster** (the `MapResolver` used for envelope auth),
  *not* an external trusted list — that's Phase 3. The member's identity key
  both authenticates to the hub and signs the credentials it issues, so the hub
  already holds the verification key.
- Two `web4-core::oid4vc` peek helpers (`unverified_issuer` / `unverified_nonce`)
  resolve the chicken/egg: the verifier reads the issuer + nonce off the
  presentation to pick the key + request before verifying under them.
- E2E tested: member admission → issue → present → verify; replay rejected;
  non-member issuer rejected.

The clean fractal: **hestia (person) issues, hub (society) verifies** — issuer
and relying-party roles split across the two scales over one shared library.

**Hub (society-scale) OID4VCI issuer ✅** — `hub-daemon` also issues
`Web4Membership` SD-JWT-VCs to its own members:
- `GET /v1/hubs/:hub_id/.well-known/openid-credential-issuer`, `POST .../nonce`,
  `POST .../credential` (credential_issuer = `.../v1/hubs/:hub_id`, so the
  advertised `<issuer>/credential` matches the mounted route).
- The holder key-possession proof doubles as member auth: the proof key must be
  a pinned member pubkey (reverse-resolved via the hub's own roster) and current
  in the ledger — only a verified member gets a credential, `cnf`-bound to its
  key.
- The hub holds **no private key** (commitment #8): it signs through its
  `RemoteSigner` via a signer-agnostic `web4-core` split (`SdJwtVc::prepare` →
  `UnsignedSdJwtVc::into_compact`). Works over **both** signing paths — the
  local keypair *and* the Hestia callback: the latter sends the prepared bytes +
  an `oid4vci_credential` intent to the Sovereign's vault, which validates them
  against the intent (issuer == the actor, vct/sub match) before signing.

**Phase 2 is functionally complete** — both scales issue and the society scale
verifies, all over one `web4-core::oid4vc` library:

| Scale | Issuer (OID4VCI) | Verifier (OID4VP) |
|---|---|---|
| Person (hestia) | ✅ `Web4Presence` | — (presents) |
| Society (hub) | ✅ `Web4Membership` | ✅ resolves issuer via member roster |

This is where a Web4 entity's wallet-held credentials become usable in EUDI
flows (age verification, membership proof, delegated-authority proof) — modulo
Phase 3 (trusted list), which is the only remaining gate and is non-code.

### Phase 3 — Trusted-list / conformance (governance/legal; the real barrier)
Getting a Web4 issuer onto a member-state trusted list. Jurisdictional,
non-code, slow. **Name it explicitly so Phase 0–2 aren't mistaken for "EUDI
done."** Until Phase 3, Web4 credentials are *parseable and verifiable but
issuer-untrusted* in a conformant wallet — fine for pilots and closed
ecosystems, not for legal eIDAS reliance.

## What maps cleanly vs what's lossy

| Web4 | EUDI representation | Fidelity |
|---|---|---|
| LCT identity + key | did:web DID Document | clean |
| Channel key (X25519) | DID keyAgreement | clean |
| DelegatedAuthority (U2) | SD-JWT-VC "delegation" credential | clean-ish |
| Constellation/assurance attestation | SD-JWT-VC presence claim | lossy (tree → claim) |
| T3/V3 trust | SD-JWT-VC score claim | lossy (tensor → scalar) + EUDI won't natively trust it |
| MRH context | SD-JWT selective disclosure | conceptual only |
| Witness tree | — | no EUDI equivalent; stays Web4-native |

## Recommendation / sequencing

1. **Build Phase 0 now** (did:web4/did:web mapping in `web4-core`) — gated only
   by the design note, which exists. This is "then build it."
2. **Promote the mapping to `web4-standard/core-spec/`** once Phase 0 is
   implemented + tested (the "update the core spec when ready" step) — a
   `did-web4-method.md` registering the method + the DID Document mapping.
3. **Phase 1 (SD-JWT-VC)** as a separate sprint after the DID face is solid.
4. **Phase 2 (OID4VCI/VP)** after Phase 1.
5. **Phase 3 (trusted list)** is dp/counsel/business, tracked separately from
   engineering — start the conversation early because it's the long pole.

The leverage: Phase 0 is small, has no external gate, and immediately makes
every Web4 entity resolvable by the tooling the EU is legislating into
existence. The rest is real but staged, and the honest blocker is a list, not a
library.
