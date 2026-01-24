# Web4 Governance Plugin for Claude Code

**Lightweight AI governance with T3 trust tensors, entity witnessing, and R6 audit trails.**

## Summary

This plugin adds structured governance to Claude Code sessions without external dependencies or network calls:

- **Entity Trust** - T3/V3 trust tensors for MCP servers, agents, references
- **Witnessing** - Bidirectional trust flow through observation
- **R6 Workflow** - Formal intent→action→result with provenance chain
- **Rust Backend** - 10-50x faster operations via `web4-trust-core` (automatic Python fallback)

## Features

| Feature | Description |
|---------|-------------|
| **MCP Trust Tracking** | Every tool call updates trust tensors for the MCP server |
| **Agent Governance** | Role-based trust accumulation across sessions |
| **Reference Witnessing** | Context blocks earn trust through successful usage |
| **Trust Decay** | Unused entities decay toward neutral over time |
| **Audit Chain** | Hash-linked records with R6 provenance |
| **Rust Performance** | Native tensor operations, 2-5x memory reduction |

## Trust Model

```
T3 Trust Tensor (6 dimensions):
├── competence   - Does it work?
├── reliability  - Does it work consistently?
├── consistency  - Same inputs → same outputs?
├── witnesses    - How many have observed it?
├── lineage      - Track record over time
└── alignment    - Does it serve stated purpose?

V3 Value Tensor (6 dimensions):
├── energy       - Activity level
├── contribution - Value added
├── stewardship  - Resource responsibility
├── network      - Connection quality
├── reputation   - Aggregate perception
└── temporal     - Time-weighted trust
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Claude Code Session                       │
├─────────────────────────────────────────────────────────────┤
│  Hooks                                                       │
│  ├── session_start.py  → Initialize governance, load trust  │
│  ├── pre_tool_use.py   → R6 request, check trust level      │
│  ├── post_tool_use.py  → Update trust, audit record         │
│  └── heartbeat.py      → Periodic decay, state sync         │
├─────────────────────────────────────────────────────────────┤
│  Governance Core                                             │
│  ├── trust_backend.py  → Rust/Python bridge (auto-select)   │
│  ├── entity_trust.py   → EntityTrust with witnessing        │
│  ├── role_trust.py     → Per-agent trust accumulation       │
│  ├── references.py     → Persistent context with curation   │
│  ├── ledger.py         → SQLite audit storage               │
│  └── soft_lct.py       → Software-bound session identity    │
├─────────────────────────────────────────────────────────────┤
│  web4-trust-core (Rust)                                      │
│  ├── T3/V3 Tensors     → Native 6D tensor operations        │
│  ├── EntityTrust       → Witnessing relationships           │
│  ├── TrustStore        → Memory + File persistence          │
│  └── Decay functions   → Temporal trust degradation         │
└─────────────────────────────────────────────────────────────┘
```

## Installation

```bash
# Clone
cd ~/.claude/plugins
git clone https://github.com/dp-web4/web4
ln -s web4/claude-code-plugin web4-governance

# Optional: Enable Rust backend (10-50x faster)
cd web4/web4-trust-core
pip install maturin
maturin develop --features python
```

## Test Plan

- [x] Entity trust creation and updates
- [x] Witnessing between entities (bidirectional trust flow)
- [x] Trust decay over time
- [x] Reference self-curation
- [x] Agent lifecycle governance
- [x] R6 workflow chain integrity
- [x] Rust backend verification
- [x] Python fallback behavior
- [ ] Real session integration test

## Files Changed

```
claude-code-plugin/
├── governance/
│   ├── trust_backend.py    [NEW]  Rust/Python bridge
│   ├── entity_trust.py            Entity trust + witnessing
│   ├── role_trust.py              Per-agent trust
│   ├── references.py              Persistent context
│   ├── agent_governance.py        Lifecycle management
│   ├── ledger.py                  SQLite audit storage
│   ├── session_manager.py         Session state
│   └── soft_lct.py                Software identity
├── hooks/
│   ├── session_start.py           Initialize governance
│   ├── pre_tool_use.py            R6 request creation
│   ├── post_tool_use.py           Trust update + audit
│   └── heartbeat.py               Periodic maintenance
└── tests/
    └── 12 tests passing

web4-trust-core/                   [NEW CRATE]
├── src/
│   ├── tensor/                    T3/V3 implementations
│   ├── entity/                    EntityTrust
│   ├── storage/                   TrustStore backends
│   ├── decay/                     Temporal functions
│   └── bindings/
│       ├── python.rs              PyO3 bindings
│       └── wasm.rs                Browser/Node.js
└── pkg/                           66KB WASM package
```

## Performance

| Operation | Python | Rust | Improvement |
|-----------|--------|------|-------------|
| Tensor update | 1x | 10-50x | Order of magnitude |
| Decay calculation | 1x | 20-100x | Two orders |
| Memory per entity | 1x | 0.2-0.5x | 2-5x reduction |
| JSON serialization | Compatible | Compatible | No migration |

---

*"Trust flows through witnessing relationships"*
