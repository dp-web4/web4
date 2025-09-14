# Web4 Cipher Suite Registry

## Registry Name
Web4 Cipher Suites

## Registration Procedure
Expert Review (RFC 8126)

## Reference
[Web4 Standard Section X.Y]

## Registry Contents

| Value | Name | AEAD | KDF | DH | Reference |
|-------|------|------|-----|----| ----------|
| 0x0001 | WEB4_AES128_GCM_SHA256 | AES-128-GCM | HKDF-SHA256 | X25519 | [Web4] |
| 0x0002 | WEB4_AES256_GCM_SHA384 | AES-256-GCM | HKDF-SHA384 | X25519 | [Web4] |
| 0x0003 | WEB4_CHACHA20_POLY1305_SHA256 | ChaCha20-Poly1305 | HKDF-SHA256 | X25519 | [Web4] |

## Notes

- Values 0x0000 and 0xFFFF are reserved
- Private use: 0xF000-0xFFFE