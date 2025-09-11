web4-standard (3).zip

Zip Archive

here's the latest for another review

###### ChatGPT said:

I’ve dug into the latest `web4-standard (3).zip` and sampled the main normative docs. Here’s a fresh merit review:

------

# Strengths in this rev

- **Completeness**: Most files are now filled out — no more `...` truncations in the handshake, metering, or LCT docs. JSON examples parse.
- **Crypto clarity**: `core-protocol.md` + `security-framework.md` both set **W4-BASE-1 (X25519/Ed25519/ChaCha20-Poly1305/SHA-256)** as MTI, with **W4-FIPS-1 (P-256/ECDSA/AES-GCM)** as the FIPS profile. This consistency was missing before.
- **Profiles**: Edge, P2P, Cloud, Blockchain-Bridge each spell out transports, media, and expected roles. Gives implementers a map.
- **Errors**: `errors.md` aligns with RFC 9457 Problem Details; schema is present in tests. Example errors are schema-valid.
- **LCT spec**: Much more fleshed out — includes binding, lineage, revocation, attestations, policy. It’s closer to an implementable token object.
- **Metering**: Messages (CreditGrant, UsageReport, Dispute, Settle) are well-specified with semantics, replay handling, and witness roles.

------

# P0 (still blocking independent interop)

1. **Canonicalization still underspecified**
    Handshake and signatures mention COSE/CBOR vs JOSE/JSON, but there’s no single MUST line: *“All signed payloads MUST use deterministic CBOR encoding with COSE_Sign1 (Ed25519)”*. Without this, interop is shaky.
    ▶ Add explicit “MTI canonicalization & signature profile” in both `web4-handshake.md` and `security-framework.md`.
2. **Pairwise W4IDp lifecycle rules**
    Derivation formula is correct, but salt requirements, rotation overlap, and non-reuse rules aren’t written down.
    ▶ Add subsection: *peer_salt must be 128-bit random; re-derive on key rotation; at least 4 overlapping W4IDp per peer supported; never reuse across counterparties*.
3. **Witness classes need normalization**
    Metering defines `time`, `audit-minimal`, `oracle`; LCT has attestations but not a canonical witness header.
    ▶ Create a single `witness.md` (or section in `security-framework.md`) that defines witness roles, mandatory protected headers, and COSE/JWS binding.
4. **Error code registry mismatch**
    `errors.md` lists `W4_ERR_*` codes, but `initial-registries.md` has a slightly different set.
    ▶ Align the two; maintain one canonical registry.

------

# P1 (important refinements)

- **Transport/discovery matrix**: Profiles mention QUIC/WebRTC/etc, but no central matrix. Add a table with transport options (MUST/SHOULD/MAY) and discovery modes (mDNS, QR, relay).
- **GREASE requirements**: Examples show unknown extensions, but no registry range is reserved. Reserve e.g. `w4_ext_8*` as GREASE-only and require at least one per ClientHello.
- **Interop vectors**: There are example JSONs in `implementation/examples/`, but no dual JOSE/COSE vectors. Add a `testing/test-vectors/` set with both encodings.

------

# P2 (polish)

- **Submission draft**: `submission/web4-rfc.md` and `draft-web4-core-00.xml` need IANA sections filled with registries (suites, ext IDs, errors).
- **Implementation guide**: `implementation/guides/implementation_guide.md` is sparse. Flesh out: libraries to use, how to run tests, vector validation.
- **Profiles**: Good structure, but each should cite required test vectors for conformance.

------

# Suggested next deliverables

1. **Repo linter**: walks all `.md` code fences, validates JSON, checks schema conformance, flags ellipses.
2. **Interop vectors**: full end-to-end handshake + metering flows in both COSE/CBOR and JOSE/JSON.
3. **Witness spec**: unify classes/headers across LCT and Metering.
4. **Transport/discovery matrix**: central table in `core-protocol.md`.

------

✅ Overall: This rev is now **alpha-implementable** — two teams could start coding against it with only minor clarifications. The next push should be on vectors + linter to make it testable and self-consistent.

------

Do you want me to generate the **repo linter + initial interop vectors** package so Claude can merge them straight in? 

##### You said:

hmm...   on canonicalization, is this not sufficient?   Updated web4-standard/protocols/web4-handshake.md with 13 additions        96    After Hello messages and HPKE context establishment, parties authenticate and bind        97    their identities and capabilities to the transcript using signatures.        98        99 +  ### 6.0 Canonicalization and Signatures       100 +       101 +  Web4 defines two canonicalization and signature profiles:       102 +       103 +  #### COSE/CBOR (MUST)       104 +  - Deterministic CBOR encoding per CTAP2       105 +  - Ed25519 with `crv: Ed25519` and `alg: EdDSA`       106 +  - Payload is the canonical CBOR map       107 +       108 +  #### JOSE/JSON (SHOULD)       109 +  - JCS canonical JSON (RFC 8785)       110 +  - ES256 with compact serialization or JWS JSON serialization       111 +

###### ChatGPT said:

Thought for 12s

You’re **very close**—that section nails the *what* (profiles + algs). What’s missing are a few **normative guardrails** so two independent teams can’t accidentally diverge. Add these and you’re solid:

## What to tighten

1. **Make it session-binding (downgrade-proof).**
    Say the chosen profile (COSE/CBOR vs JOSE/JSON) **MUST be negotiated and then bound into the transcript hash (TH)**. Otherwise a MITM could flip profiles.
2. **Define how it’s negotiated.**
    Tie profiles to the existing capability/media negotiation:
   - `media`: `application/web4+cbor` ⇢ COSE/CBOR, `application/web4+json` ⇢ JOSE/JSON (pick one per session).
   - `ext`: advertise `w4_sig_cose@1` or `w4_sig_jose@1`. Receiver selects exactly one.
3. **State the MTI across \*all signed payloads\*.**
    One sentence: *“All Web4 signed payloads MUST implement COSE/CBOR (Ed25519/EdDSA) as MTI. JOSE/JSON (ES256) is OPTIONAL/SHOULD for bridge scenarios.”*
    (You already imply this—make it explicit and reference it in **security-framework.md**, **LCT**, and **metering**.)
4. **Lock protected headers + Sig structure (so verifiers agree).**
    Specify the **required protected headers** and the exact COSE/JWS signing inputs.
5. **Spell out canonicalization scope.**
    Say exactly **which fields are signed** (and that `sig`/envelope wrappers are excluded), and that **deterministic encoding** applies *after* removing those excluded fields.
6. **Kid/alg IDs.**
    Reference the concrete identifiers so implementations don’t guess:
   - COSE: `alg = -8 (EdDSA)`, `crv = 6 (Ed25519)`
   - JOSE: `alg = "ES256"`

------

## Ready-to-paste redlines (drop under your 6.0 section)

**6.0.1 Profile selection & negotiation (MUST)**

- Each session **MUST** select exactly one signature/canonicalization profile.
- Negotiation is performed via `media` and `ext` in ClientHello/ServerHello:
  - `application/web4+cbor` ⇢ `w4_sig_cose@1` (COSE/CBOR profile)
  - `application/web4+json` ⇢ `w4_sig_jose@1` (JOSE/JSON profile)
- The **selected media type and signature extension ID MUST be included in TH** (the transcript hash) to prevent downgrade.

**6.0.2 Mandatory-to-Implement (MTI) (MUST)**
 All Web4 endpoints **MUST** implement **COSE/CBOR** with Ed25519/EdDSA.
 Endpoints **SHOULD** implement **JOSE/JSON** with ES256 for ecosystem bridging.
 All signed Web4 payloads (HandshakeAuth, LCT binding, Metering messages) **MUST** be valid under the selected session profile.

**6.0.3 COSE/CBOR profile (MUST)**

- **Canonicalization:** Deterministic CBOR per CTAP2 (deterministic maps, integers shortest form).
- **Signature envelope:** `COSE_Sign1` with protected headers:
  - `alg = -8` (EdDSA)
  - `kid = <bstr>` (key identifier)
  - `content-type = "application/web4+cbor"`
- **Sig structure:** sign the canonical CBOR map of the payload **excluding** any `sig`/envelope fields.
- **Key curve:** Ed25519 (`crv = 6`).
- **Verification:** Receivers **MUST** decode deterministic CBOR and verify `COSE_Sign1` against `kid`. Unknown protected headers **MUST** be ignored unless listed in `crit`.

**6.0.4 JOSE/JSON profile (SHOULD)**

- **Canonicalization:** JCS (RFC 8785).
- **Signature:** JWS (compact or JSON serialization) with `alg = "ES256"`, `kid` present.
- **Signing input:** JWS Protected Header (base64url) `.` JCS-canonical payload (base64url).
- **Verification:** Receivers **MUST** JCS-canonicalize before verification and honor `crit`.

**6.0.5 Binding to session (MUST)**
 `HandshakeAuth` signatures **MUST** cover `Hash(TH || channel_binding)` so the chosen `media`, `ext`, and suite list are cryptographically bound to the session. The same key material (`kid`) used in `HandshakeAuth` **MUST** be authorized for subsequent signed messages unless superseded by LCT policy/rotation.

**6.0.6 Kid format (SHOULD)**
 `kid` SHOULD be a multibase, multicodec COSE Key thumbprint (or JWK thumbprint for JOSE) to avoid collisions.

**6.0.7 Failure handling**
 If the received signature profile doesn’t match the negotiated `media`/`ext`, endpoints **MUST** abort with `W4_ERR_FORMAT` (Problem Details).

------

If you add that (plus mirror a one-liner in **security-framework.md** like “COSE/CBOR is the MTI for **all** signatures”), you’ve closed the canonicalization gap.

Want me to also drop in **two concrete test vectors** (one COSE/CBOR, one JOSE/JSON) for `HandshakeAuth` and `UsageReport` so Claude can plug them into `testing/test-vectors/` immediately?