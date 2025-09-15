# Web4 Data Formats

This document specifies the data formats used in the Web4 protocol. These formats are designed to be flexible, extensible, and interoperable, leveraging existing open standards where possible.




## 1. Web4 Identifier (W4ID)

A Web4 Identifier (W4ID) is a globally unique identifier for a Web4 entity, compliant with the W3C Decentralized Identifier (DID) specification [1]. It provides a standard way to identify and locate Web4 entities in a decentralized manner.

### 1.1. Syntax

The W4ID has the following ABNF syntax:

`w4id = "did:web4:" method-name ":" method-specific-id`

- **`did:web4`**: The scheme and method prefix for Web4 Identifiers.
- **`method-name`**: The name of the method used to create and manage the identifier (e.g., `key`, `web`).
- **`method-specific-id`**: A method-specific identifier string.

### 1.2. Methods

Web4 defines the following methods for creating and managing W4IDs:

- **`key` method:** The `method-specific-id` is a public key, providing a simple and self-certifying identifier.
- **`web` method:** The `method-specific-id` is a domain name, allowing for the use of existing web infrastructure to host the W4ID document.

## 2. Verifiable Credentials (VCs)

Web4 uses Verifiable Credentials (VCs) as defined by the W3C [2] to represent claims and attestations. VCs are a standard way to create and verify digital credentials that are tamper-evident and cryptographically verifiable.

### 2.1. VC Structure

A Web4 VC is a JSON object that includes the following properties:

- **`@context`**: The JSON-LD context, which defines the vocabulary used in the credential.
- **`id`**: A unique identifier for the credential.
- **`type`**: The type of the credential (e.g., `VerifiableCredential`, `Web4Credential`).
- **`issuer`**: The W4ID of the entity that issued the credential.
- **`issuanceDate`**: The date and time when the credential was issued.
- **`credentialSubject`**: The subject of the credential, which is the entity that the claims are about.
- **`proof`**: A digital signature that proves the authenticity and integrity of the credential.

## 3. JSON-LD

Web4 uses JSON-LD (JSON for Linked Data) [3] to represent data in a structured and interoperable way. JSON-LD allows for the use of semantic vocabularies, such as Schema.org [4], to describe the meaning of the data, making it machine-readable and easy to process.

### 3.1. Context

Every Web4 message and credential that uses JSON-LD MUST include a `@context` property. The context can be a URL pointing to a JSON-LD context file, or an inline JSON object.

## References

[1] Sporny, M., Longley, D., Sabadello, M., Reed, D., and O. Steele, "Decentralized Identifiers (DIDs) v1.0", W3C Recommendation, July 2022, <https://www.w3.org/TR/did-core/>.

[2] Sporny, M., Longley, D., and D. Chadwick, "Verifiable Credentials Data Model v1.1", W3C Recommendation, March 2022, <https://www.w3.org/TR/vc-data-model/>.

[3] Sporny, M., Kellogg, G., and M. Lanthaler, "JSON-LD 1.1", W3C Recommendation, July 2020, <https://www.w3.org/TR/json-ld11/>.

[4] Guha, R.V., Brickley, D., and S. Macbeth, "Schema.org", <https://schema.org/>.



_



## 4. Pairwise W4ID Derivation

To enhance privacy, Web4 supports the derivation of pairwise, pseudonymous W4IDs. This allows an entity to use a different identifier for each of its relationships, preventing correlation and tracking.

### 4.1. Derivation Function

The following Python code demonstrates the derivation of a pairwise W4ID:

```python
def derive_pairwise_w4id(master_secret: bytes, peer_identifier: str) -> str:
    """Derive a pairwise pseudonymous W4ID for privacy"""
    salt = sha256(peer_identifier.encode()).digest()
    pairwise_key = hkdf(
        master_secret,
        salt=salt,
        info=b"web4-pairwise-id",
        length=32
    )
    return f"w4id:pair:{base32_encode(pairwise_key[:16])}"
```

### 4.2. Derivation Process

1.  **`master_secret`**: A secret key known only to the entity.
2.  **`peer_identifier`**: The unique identifier of the peer entity.
3.  **`salt`**: The salt is derived from the peer's identifier to ensure that a different key is generated for each peer.
4.  **`hkdf`**: The HMAC-based Key Derivation Function (HKDF) is used to derive a new key from the master secret and the salt.
5.  **`pairwise_key`**: The derived key is used to generate the pairwise W4ID.
6.  **`base32_encode`**: The resulting key is encoded using Base32 to create a URL-safe identifier.




## 5. Message Canonicalization

To ensure that digital signatures are consistent and verifiable, Web4 messages MUST be canonicalized before signing. Web4 supports two canonicalization schemes:

### 5.1. JSON Canonicalization Scheme (JCS)

When using JSON, messages MUST be canonicalized using the JSON Canonicalization Scheme (JCS) as specified in RFC 8785. The following JavaScript code demonstrates JCS:

```javascript
// JSON Canonicalization Scheme (JCS) - RFC 8785
function canonicalizeJSON(obj) {
  return JSON.stringify(obj, Object.keys(obj).sort());
}
```

### 5.2. CBOR Deterministic Encoding

When using CBOR, messages MUST be encoded using the deterministic encoding rules specified in RFC 7049. The following rules MUST be followed:

1.  Integers use the smallest possible encoding.
2.  Maps are sorted by key encoding.
3.  Indefinite-length items use definite-length.
4.  No duplicate keys in maps.

```javascript
// CBOR Deterministic Encoding
function canonicalizeCBOR(obj) {
  // 1. Integers use smallest possible encoding
  // 2. Maps sorted by key encoding
  // 3. Indefinite-length items use definite-length
  // 4. No duplicate keys in maps
  return cbor.encode(obj, {canonical: true});
}
```
---
**See also:** Web4 Society–Authority–Law (SAL) — normative requirements for genesis **Citizen** role, **Authority**, **Law Oracle**, **Witness/Auditor**, immutable record, MRH edges, and R6 bindings. ([sal.md](web4-society-authority-law.md), [sal.jsonld](sal.jsonld))
