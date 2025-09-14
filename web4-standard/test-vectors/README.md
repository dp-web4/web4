# Web4 Test Vectors

This directory contains test vectors for Web4 protocol implementations to ensure interoperability.

## Structure

- `keys/` - Fixed keypairs for deterministic testing
- `handshake/` - HPKE handshake test vectors
- `lct/` - LCT signing and verification vectors
- `mrh/` - MRH update vectors
- `trust-query/` - ATP-staked trust query vectors

## Usage

```python
import json

# Load test vector
with open("test-vectors/lct/valid-birth-certificate.json") as f:
    vector = json.load(f)

# Verify your implementation produces same output
result = your_implementation.create_lct(vector["input"])
assert result == vector["expected_output"]
```

## Conformance Requirements

Implementations MUST:
1. Pass all vectors in `valid/` directories
2. Reject all vectors in `invalid/` directories
3. Produce bit-identical outputs for deterministic operations
4. Handle edge cases in `edge-cases/` directories

## Test Vector Format

Each vector contains:
- `description`: Human-readable test description
- `input`: Input parameters
- `expected_output`: Expected result
- `should_succeed`: Boolean indicating if operation should succeed
- `notes`: Implementation hints or special considerations