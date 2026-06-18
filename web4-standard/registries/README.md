# Web4 Registries
Status: Draft • Last-Updated: 2026-06-18

## Overview

These registries define the IANA considerations for Web4 protocol parameters.

## Registry Files

- [**cipher-suites.md**](cipher-suites.md) - Cryptographic cipher suite registry
- [**error-codes.md**](error-codes.md) - Protocol error code registry  
- [**extensions.md**](extensions.md) - Protocol extension registry
- [**initial-registries.md**](initial-registries.md) - Initial registry values

## Registration Process

Registration policies follow [RFC 8126](https://www.rfc-editor.org/rfc/rfc8126).
Each registry selects a single policy; they are not all universal:

| Registry | Registration Policy (RFC 8126) |
|----------|-------------------------------|
| cipher-suites.md | Expert Review |
| error-codes.md | Expert Review |
| extensions.md | Specification Required |
| initial-registries.md | N/A — initial seed values, not a registration target |

- **Expert Review**: a designated expert reviews each request before assignment.
- **Specification Required**: the request must reference a stable, publicly available specification (also implies Expert Review of that specification).

## Contact

Registry questions: TBD-before-IANA-submission
