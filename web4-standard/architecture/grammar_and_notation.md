





# Formal Grammar and Notation

This document defines the formal grammar and notational conventions used in the Web4 Internet Standard. A consistent and well-defined grammar is essential for ensuring interoperability and unambiguous interpretation of the protocol.

## 1. Notational Conventions

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "NOT RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as described in RFC 2119 [1].

All data values in this specification are in network byte order (big-endian).

## 2. Augmented Backus-Naur Form (ABNF)

The formal grammar for the Web4 protocol is defined using Augmented Backus-Naur Form (ABNF) as specified in RFC 5234 [2]. The ABNF notation provides a standard and unambiguous way to define the syntax of the protocol.

### Core ABNF Rules

The following core ABNF rules are used throughout this specification:

- **ALPHA:** %x41-5A / %x61-7A (A-Z / a-z)
- **DIGIT:** %x30-39 (0-9)
- **HEXDIG:** DIGIT / "A" / "B" / "C" / "D" / "E" / "F"
- **CRLF:** %x0D.0A (carriage return followed by line feed)
- **SP:** %x20 (space)
- **VCHAR:** %x21-7E (visible ASCII characters)

## 3. JSON Data Formats

Web4 messages and credentials MAY be represented in JSON format. When JSON is used, it MUST be valid according to RFC 8259 [3].

## 4. URI Scheme

Web4 supports two URI schemes for identifying and locating resources:

### 4.1. `web4://` Scheme

This scheme is used for clean, human-readable URIs.

```abnf
web4-URI = "web4://" w4-authority path-abempty [ "?" query ] [ "#" fragment ]
w4-authority = w4id-label / hostname
w4id-label = "w4-" base32nopad   ; base32 encoding of pairwise W4ID
```

### 4.2. `did:web4` Scheme (RECOMMENDED)

This scheme is based on the W3C DID specification and is the recommended way to identify Web4 entities.

```abnf
web4-did-url = did-url
did-url = "did:web4:" method-specific-id [ path ] [ "?" query ] [ "#" fragment ]
method-specific-id = base32nopad
```

## References

[1] Bradner, S., "Key words for use in RFCs to Indicate Requirement Levels", BCP 14, RFC 2119, DOI 10.17487/RFC2119, March 1997, <https://www.rfc-editor.org/info/rfc2119>.

[2] Crocker, D., Ed., and P. Overell, "Augmented BNF for Syntax Specifications: ABNF", STD 68, RFC 5234, DOI 10.17487/RFC5234, January 2008, <https://www.rfc-editor.org/info/rfc5234>.

[3] Bray, T., Ed., "The JavaScript Object Notation (JSON) Data Interchange Format", STD 90, RFC 8259, DOI 10.17487/RFC8259, December 2017, <https://www.rfc-editor.org/info/rfc8259>.

[4] Berners-Lee, T., Fielding, R., and L. Masinter, "Uniform Resource Identifier (URI): Generic Syntax", STD 66, RFC 3986, DOI 10.17487/RFC3986, January 2005, <https://www.rfc-editor.org/info/rfc3986>.


