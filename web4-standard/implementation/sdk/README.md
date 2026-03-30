# Web4 Python SDK

Canonical data types and operations for the Web4 trust infrastructure.

The `web4` package provides offline-capable primitives for trust tensors, identity
tokens, federation governance, action frameworks, and more. It defines the types
specified in the [web4-standard](https://github.com/dp-web4/web4) and works without
network services — no async, no HTTP, no external dependencies beyond the Python
standard library.

**Version**: 0.16.0 | **Python**: 3.10+ | **License**: MIT | **Typed**: PEP 561

## Installation

```bash
pip install -e .
```

Or from the repository root:

```bash
pip install -e web4-standard/implementation/sdk/
```

No runtime dependencies. For schema validation support:

```bash
pip install -e ".[validation]"  # adds jsonschema
```

For development (includes validation + pytest, mypy):

```bash
pip install -e ".[dev]"
```

## Quick Start

```python
from web4 import T3, LCT, EntityType, ATPAccount

# Create a trust tensor
trust = T3(talent=0.8, training=0.7, temperament=0.9)
print(trust.composite)  # weighted composite score

# Create an identity token
lct = LCT.create(entity_type=EntityType.AI, public_key="test-key")
print(lct.lct_id)  # auto-generated UUID-based ID

# ATP energy accounting
account = ATPAccount(available=1000.0)
print(account.available)  # 1000.0

# Serialize to JSON-LD (RDF-compatible)
doc = trust.to_jsonld()
reconstructed = T3.from_jsonld(doc)
assert reconstructed.talent == trust.talent
```

## Modules

The SDK contains 20 modules, all importable from the `web4` namespace:

| Module | Description | Key Types |
|--------|-------------|-----------|
| `trust` | Multi-dimensional trust and value assessment | `T3`, `V3`, `TrustProfile` |
| `lct` | Linked Context Tokens — identity and presence | `LCT`, `EntityType`, `BirthCertificate` |
| `atp` | ATP/ADP energy metabolism | `ATPAccount`, `transfer`, `energy_ratio` |
| `federation` | Society, Authority, Law governance | `Society`, `LawDataset`, `Delegation` |
| `r6` | R7 Action Framework (Rules/Role/Request/Reference/Resource/Result/Reputation) | `R7Action`, `ActionChain`, `ReputationDelta` |
| `mrh` | Markov Relevancy Horizon context graphs | `MRHGraph`, `MRHNode`, `MRHEdge` |
| `acp` | Agentic Context Protocol for autonomous agents | `AgentPlan`, `Intent`, `Decision` |
| `dictionary` | Semantic bridges with trust-tracked translation | `DictionaryEntity`, `DictionarySpec` |
| `reputation` | Rule-based reputation engine | `ReputationRule`, `ReputationEngine` |
| `entity` | Entity type taxonomy and behavioral modes | `EntityTypeInfo`, `BehavioralMode` |
| `capability` | 6-level capability framework (Stub to Hardware) | `CapabilityLevel`, `LevelRequirement` |
| `errors` | RFC 9457 error types for Web4 protocols | `Web4Error`, `ErrorCode` |
| `metabolic` | Society operational modes and energy effects | `MetabolicState`, `MetabolicProfile` |
| `binding` | Multi-device constellation management | `DeviceConstellation`, `DeviceRecord` |
| `society` | Core organizational primitive | `SocietyState`, `Treasury`, `SocietyLedger` |
| `security` | Crypto suites, W4ID identifiers, key policies | `W4ID`, `CryptoSuite`, `SignatureEnvelope` |
| `protocol` | Handshake, transport, discovery, Web4 URIs | `Web4URI`, `Transport`, `ClientHello` |
| `mcp` | MCP context headers, sessions, ATP metering | `MCPSession`, `Web4Context` |
| `attestation` | Hardware trust envelope and verification | `AttestationEnvelope`, `verify_envelope` |
| `validation` | Schema validation for JSON-LD documents | `validate`, `list_schemas`, `get_schema` |

344 symbols are exported from `web4.__init__`. All 20 submodules have `__all__` declarations.

## Command-Line Interface

```bash
web4 info             # Show SDK version, modules, exports, schemas
web4 list-schemas     # List available JSON Schemas
web4 validate F.json  # Validate a JSON-LD document (auto-detects schema from @type)
web4 validate F.json --schema lct  # Validate against a specific schema
```

Also available as `python -m web4`.

## Import Patterns

```python
# Root namespace — convenient for scripts
from web4 import T3, V3, LCT, R7Action, Society

# Submodule imports — recommended for applications
from web4.trust import T3, V3, TrustProfile
from web4.federation import Society, LawDataset
from web4.security import W4ID, parse_w4id
```

## JSON-LD Serialization

All core types support bidirectional JSON-LD serialization for RDF interoperability:

```python
from web4 import T3, LCT, AttestationEnvelope, R7Action

# Every core type has to_jsonld() and from_jsonld()
trust = T3(talent=0.8, training=0.7, temperament=0.9)
doc = trust.to_jsonld()
# {
#   "@context": "https://web4.io/ns/",
#   "@type": "T3Tensor",
#   "talent": 0.8,
#   "training": 0.7,
#   "temperament": 0.9
# }

# Round-trip fidelity
assert T3.from_jsonld(doc) == trust
```

JSON Schemas for all 10 types are in `schemas/` with 278 cross-language validation
vectors in `../../test-vectors/`.

## Error Handling

```python
from web4 import Web4Error, make_error, ErrorCode

# Structured errors with RFC 9457 Problem Details
try:
    raise make_error(ErrorCode.BINDING_REVOKED, detail="Binding was revoked")
except Web4Error as e:
    print(e.to_problem_json())
    # {"type": "about:blank", "title": "...", "status": 403, "detail": "Binding was revoked"}
```

Six error categories: Binding, Pairing, Witness, Authorization, Crypto, Protocol.

## Testing

```bash
# Run the full test suite
python -m pytest tests/

# With coverage
python -m pytest tests/ --cov=web4

# Type checking
mypy --strict web4/
```

1770 tests, 98% coverage, mypy strict compliant, CI across Python 3.10-3.13.

## Client SDK

The `web4_sdk.py` module (separate from the `web4` package) provides an async HTTP
client for connecting to Web4 infrastructure services. It requires `aiohttp` and
`pynacl` and is intended for applications that communicate with running Web4 nodes.

```python
from web4_sdk import Web4Client

client = Web4Client(
    identity_url="http://localhost:8001",
    auth_url="http://localhost:8003",
    lct_id="lct:web4:ai:society:001",
    private_key=key_bytes
)
```

The client SDK re-exports canonical types from the `web4` package, so both
`from web4 import T3` and `from web4_sdk import T3` resolve to the same objects.

## Project Structure

```
web4/                  # Python package (20 modules)
  __init__.py          # 344 re-exports
  __main__.py          # CLI entry point (web4 info/validate/list-schemas)
  py.typed             # PEP 561 marker
  trust.py             # T3/V3 tensors
  lct.py               # Linked Context Tokens
  validation.py        # Schema validation
  ...                  # (17 more modules)
tests/                 # 1770 tests
schemas/               # JSON Schemas + JSON-LD contexts
web4_sdk.py            # Async HTTP client (separate)
pyproject.toml         # Package metadata (single version source)
```

## License

MIT License. See [LICENSE](LICENSE).
