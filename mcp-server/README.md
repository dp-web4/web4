# Web4 MCP Server

Model Context Protocol server exposing Web4 capabilities to Claude Code and other MCP clients.

## Tools (web4.io/ namespace)

| Tool | Description |
|------|-------------|
| `web4.io/trust/query` | Query T3/V3 trust tensor for entity in role |
| `web4.io/trust/update` | Update trust based on action outcome |
| `web4.io/lct/create` | Create a new Linked Context Token |
| `web4.io/lct/verify` | Verify LCT signature |
| `web4.io/heartbeat/record` | Record timing heartbeat |
| `web4.io/heartbeat/coherence` | Query session timing coherence |
| `web4.io/session/status` | Get session status and health |

## Resources

- `web4://trust/{entity_id}` - Trust tensor for entity
- `web4://heartbeat/{session_id}` - Heartbeat ledger
- `web4://session/{session_id}` - Session state

## Prompts

- `web4.io/analyze-trust` - Analyze trust patterns
- `web4.io/audit-session` - Generate audit report

## Installation

Add to Claude Code settings:

```json
{
  "mcpServers": {
    "web4": {
      "command": "python3",
      "args": ["/path/to/web4/mcp-server/server.py"]
    }
  }
}
```

## Testing

```bash
python3 test_mcp.py
```

## License

MIT - Copyright (c) 2025 Web4 Contributors
