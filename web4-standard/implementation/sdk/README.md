# Web4 Python SDK

Canonical data types and operations for the Web4 trust infrastructure.

This SDK provides offline-capable primitives for trust tensors, identity
tokens, federation governance, action frameworks, and more. It defines the types
specified in the [web4-standard](https://github.com/dp-web4/web4) and works without
network services — no async, no HTTP, no external dependencies beyond the Python
standard library.

**Version**: 0.28.0 | **Python**: 3.10+ | **License**: AGPL-3.0-or-later | **Typed**: PEP 561

> **Install name vs import name.** The distribution is published on PyPI as
> **`web4-sdk`** (the unsuffixed `web4` PyPI name is held by an unrelated
> dormant project at v0.0.1). The Python import path remains **`web4`** — so
> `from web4 import T3, V3, LCT, ...` works as documented throughout this README.

## Installation

From PyPI (when published):

```bash
pip install web4-sdk
```

From a clone (editable install for development):

```bash
pip install -e .
```

Or from the repository root:

```bash
pip install -e web4-standard/implementation/sdk/
```

No runtime dependencies. Optional extras:

```bash
pip install "web4-sdk[validation]"   # adds jsonschema for schema validation
pip install "web4-sdk[mcp]"          # adds mcp for MCP server (web4-mcp)
pip install "web4-sdk[dev]"          # full dev toolchain (pytest, mypy, ruff, jsonschema, mcp)
```

(For editable installs, the same extras work with the `-e` form: `pip install -e ".[validation]"`.)

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

The SDK contains 23 modules, all importable from the `web4` namespace:

| Module | Description | Key Types |
|--------|-------------|-----------|
| `trust` | Multi-dimensional trust and value assessment | `T3`, `V3`, `TrustQuery`, `evaluate_trust_query`, `resolve_trust` |
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
| `role` | Society role taxonomy and role-LCT binding | `SocietyRole`, `RoleAssignment`, `bootstrap_society_roles` |
| `security` | Crypto suites, W4ID identifiers, key policies | `W4ID`, `CryptoSuite`, `SignatureEnvelope` |
| `protocol` | Handshake, transport, discovery, Web4 URIs | `Web4URI`, `Transport`, `ClientHello` |
| `mcp` | MCP context headers, sessions, ATP metering | `MCPSession`, `Web4Context` |
| `attestation` | Hardware trust envelope and verification | `AttestationEnvelope`, `verify_envelope` |
| `validation` | Schema validation for JSON-LD documents | `validate`, `list_schemas`, `get_schema` |
| `deserialize` | Generic JSON-LD deserialization dispatcher | `from_jsonld`, `from_jsonld_string`, `supported_types` |
| `generate` | Produce minimal valid JSON-LD documents | `generate`, `generate_string`, `available_types` |

376 symbols are exported from `web4.__init__`. All 23 submodules have `__all__` declarations.

## MCP Server

The SDK includes an MCP server that exposes trust operations as tools for any MCP client:

```bash
web4-mcp                       # via console script (stdio transport)
python -m web4.mcp_server      # via module
```

Provides 8 tools: `web4_info`, `web4_validate`, `web4_generate`, `web4_roundtrip`, `web4_list_types`,
`web4_evaluate_trust`, `web4_resolve_trust`, `web4_process_action`.
Requires `pip install 'web4-sdk[mcp]'`.

## Command-Line Interface

```bash
web4 info             # Show SDK version, modules, exports, schemas
web4 list-schemas     # List available JSON Schemas
web4 validate F.json  # Validate a JSON-LD document (auto-detects schema from @type)
web4 validate F.json --schema lct  # Validate against a specific schema
web4 roundtrip F.json         # Deserialize + re-serialize (normalize)
web4 roundtrip F.json --check # Compare input vs output (exit 0=match, 1=diff)
web4 generate T3Tensor        # Generate a minimal valid JSON-LD document
web4 generate --list          # List all 23 supported types
web4 selftest                 # Verify SDK installation (imports, schemas, roundtrips)
web4 selftest -v              # Verbose: show per-phase progress
web4 trust --file query.json  # Evaluate a trust query from JSON file
web4 trust --actor A --target B --role admin  # Evaluate trust from CLI flags
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

# Generic deserialization (any @type)
from web4 import from_jsonld
obj = from_jsonld(doc)  # dispatches to T3.from_jsonld() by @type
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

Seven error categories: Binding, Pairing, Witness, Authorization, Crypto, Protocol, Cross-Society.

## Testing

```bash
# Run the full test suite
python -m pytest tests/

# With coverage
python -m pytest tests/ --cov=web4

# Type checking
mypy --strict web4/
```

2749 tests, 97.8% coverage, mypy strict zero-error, CI across Python 3.10-3.13.

## Project Structure

```
web4/                  # Python package (23 modules + MCP server)
  __init__.py          # 376 re-exports
  __main__.py          # CLI entry point (web4 info/validate/list-schemas/roundtrip/generate/selftest/trust)
  mcp_server.py        # MCP server entry point (web4-mcp)
  py.typed             # PEP 561 marker
  trust.py             # T3/V3 tensors, TrustQuery, evaluate_trust_query(), resolve_trust()
  lct.py               # Linked Context Tokens
  deserialize.py       # Generic JSON-LD dispatcher (23 types)
  generate.py          # Minimal valid JSON-LD document generation
  validation.py        # Schema validation
  ...                  # (18 more modules)
tests/                 # 2749 tests
schemas/               # JSON Schemas + JSON-LD contexts
pyproject.toml         # Package metadata (single version source)
```

## License

AGPL-3.0-or-later. See [LICENSE](LICENSE) and the repo-root PATENTS.md for the patent grant terms.
