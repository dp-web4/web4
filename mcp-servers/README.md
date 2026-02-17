# Web4 MCP Servers (TypeScript)

Modular Model Context Protocol servers exposing Web4 trust infrastructure.

## Servers

| Server | Tools | Description |
|--------|-------|-------------|
| `web4-identity` | 8 | LCT identity operations (create, verify, bind, revoke, delegate, witness, chain, query) |
| `web4-trust` | 6 | T3/V3 trust tensors (query, update, history, compare, aggregate, decay) |
| `web4-economy` | 8 | ATP/ADP attention tokens (balance, transfer, price, charge, discharge, demurrage, history, budget) |

## Installation

Each server is a standalone package:

```bash
cd web4-identity
npm install
npm run build
```

## Usage

### With Claude Code

Add to `~/.claude/settings.json`:

```json
{
  "mcpServers": {
    "web4-identity": {
      "command": "node",
      "args": ["/path/to/web4/mcp-servers/web4-identity/dist/server.js"]
    },
    "web4-trust": {
      "command": "node",
      "args": ["/path/to/web4/mcp-servers/web4-trust/dist/server.js"]
    },
    "web4-economy": {
      "command": "node",
      "args": ["/path/to/web4/mcp-servers/web4-economy/dist/server.js"]
    }
  }
}
```

### Development Mode

```bash
cd web4-identity
npm run dev  # Uses tsx for hot reload
```

## Tool Namespaces

All tools use the `web4.io/` namespace for consistency:

- `web4.io/identity/*` - Identity operations
- `web4.io/trust/*` - Trust tensor operations
- `web4.io/atp/*` - Economy/token operations

## Architecture

These TypeScript servers complement the existing Python MCP server (`../mcp-server/server.py`).

**Why both?**
- Python server: Monolithic, integrates with existing Python codebase
- TypeScript servers: Modular, better for production deployments with isolation

## License

AGPL-3.0 - See LICENSE in repository root.

## Related

- [Hardbound](https://github.com/dp-web4/hardbound) - Enterprise trust accountability layer (proprietary MCP servers)
- [Web4 Standard](../web4-standard/) - Core specifications
