## Web4 Governance Plugin for Claude Code

Lightweight AI governance with T3 trust tensors, entity witnessing, and R6 audit trails.

### Features

- **Entity Trust** - T3/V3 tensors (6D each) for MCP servers, agents, references
- **Witnessing** - Bidirectional trust flow through observation
- **R6 Workflow** - Formal intent→action→result with hash-linked provenance
- **Rust Backend** - 10-50x faster via `web4-trust-core` (auto Python fallback)
- **Trust Decay** - Unused entities decay toward neutral over time

### Components

- `governance/` - Trust tensors, witnessing, R6 ledger, session management
- `hooks/` - session_start, pre/post_tool_use, heartbeat
- `web4-trust-core/` - Rust crate with PyO3 + WASM bindings

### Test Plan

- [x] Entity trust + witnessing (12 tests passing)
- [x] Rust backend verification + Python fallback
- [ ] Real session integration

See [README.md](README.md) for full documentation.
