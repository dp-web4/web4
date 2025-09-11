# Web4 Error Taxonomy

This document defines a standardized error taxonomy for the Web4 protocol. A consistent error format is essential for debugging, interoperability, and providing a good developer experience.




## 1. Error Format

Web4 errors are represented as JSON objects with the following properties:

```json
{
  "type": "https://web4.dev/errors/",
  "title": "Binding Failed",
  "status": 409,
  "code": "W4_ERR_BINDING_EXISTS",
  "detail": "Entity already has an active binding",
  "instance": "/bindings/device-12345",
  "extensions": {
    "existing_lct": "lct:web4:abc123",
    "suggested_action": "revoke_existing"
  }
}
```

-   **`type`**: A URI that identifies the error type.
-   **`title`**: A short, human-readable summary of the error.
-   **`status`**: The HTTP status code associated with the error.
-   **`code`**: A Web4-specific error code.
-   **`detail`**: A human-readable explanation of the error.
-   **`instance`**: A URI that identifies the specific occurrence of the error.
-   **`extensions`**: An object containing additional information about the error.

## 2. Error Codes

Web4 defines the following error codes:

-   **`W4_ERR_BINDING_*`**: Errors related to the BINDING protocol.
-   **`W4_ERR_PAIRING_*`**: Errors related to the PAIRING protocol.
-   **`W4_ERR_WITNESS_*`**: Errors related to the WITNESSING protocol.
-   **`W4_ERR_TRUST_*`**: Errors related to trust validation.
-   **`W4_ERR_CRYPTO_*`**: Errors related to cryptographic operations.


