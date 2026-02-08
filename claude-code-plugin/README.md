# Claude Code Plugin

Web4 governance integration for [Claude Code](https://github.com/anthropics/claude-code).

## Implementation

The canonical implementation is maintained as a PR to the Anthropic claude-code repository:

**Pull Request**: [anthropics/claude-code#20448](https://github.com/anthropics/claude-code/pull/20448)

**Branch**: `dp-web4/web4-governance-plugin`

## Features

The web4-governance plugin provides:

| Feature | Description |
|---------|-------------|
| **Soft LCT Identity** | Session-based identity tokens for agent actions |
| **Trust Tensors** | T3 (competence, reliability, integrity) scoring |
| **Action Witnessing** | Cryptographic attestation of tool calls |
| **Rate Limiting** | Persistent rate limits with witness tracking |
| **Event Streaming** | Real-time governance event monitoring |
| **Audit Ledger** | Hash-chained action provenance |

## Architecture

```
Claude Code Session
       │
       ▼
┌──────────────────┐
│  Governance Hook │ ← Pre/post tool call interception
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│   Soft LCT       │ ← Session identity binding
│   Trust Tensor   │ ← Action trust scoring
│   Witness Chain  │ ← Cryptographic attestation
│   Rate Limiter   │ ← Resource governance
└──────────────────┘
         │
         ▼
┌──────────────────┐
│  Audit Ledger    │ ← Immutable action log
└──────────────────┘
```

## Installation

Once merged, the plugin will be available via:

```bash
# Clone claude-code with the plugin
git clone https://github.com/anthropics/claude-code.git
cd claude-code

# Enable web4-governance plugin
# (configuration instructions will be in the merged PR)
```

## Local Development

To use the plugin before merge:

```bash
# Clone the PR branch
git clone https://github.com/anthropics/claude-code.git
cd claude-code
git fetch origin pull/20448/head:web4-governance
git checkout web4-governance

# Plugin is in plugins/web4-governance/
```

## Module Structure

```
plugins/web4-governance/
├── governance/
│   ├── agent_governance.py    # Main governance engine
│   ├── soft_lct.py            # Soft LCT identity
│   ├── tensors.py             # T3/V3 trust tensors
│   ├── ledger.py              # Hash-chained audit log
│   ├── signing.py             # Ed25519 attestation
│   ├── rate_limiter.py        # Resource governance
│   ├── event_stream.py        # Real-time monitoring
│   └── ...
└── hooks/
    └── heartbeat.py           # Session heartbeat
```

## Related

- [Web4 Ledgers](../ledgers/) - Immutable record infrastructure
- [Web4 Standard](../web4-standard/) - Core protocol specifications
- [ACT Chain](https://github.com/dp-web4/ACT) - Distributed ledger implementation

## Status

| Milestone | Status |
|-----------|--------|
| Core governance engine | Complete |
| Soft LCT identity | Complete |
| Trust tensor integration | Complete |
| Witness chain | Complete |
| Rate limiting | Complete |
| Event streaming | Complete |
| PR submitted | Complete |
| PR merged | Pending review |
