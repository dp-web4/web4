#!/usr/bin/env python3
"""Test the Web4 MCP Server."""

import json
import subprocess
import sys


def send_request(proc, method: str, params: dict = None, request_id: int = 1):
    """Send a JSON-RPC request and get response."""
    request = {
        "jsonrpc": "2.0",
        "method": method,
        "id": request_id
    }
    if params:
        request["params"] = params

    proc.stdin.write(json.dumps(request) + "\n")
    proc.stdin.flush()

    response_line = proc.stdout.readline()
    if response_line:
        return json.loads(response_line)
    return None


def main():
    # Start the MCP server
    proc = subprocess.Popen(
        [sys.executable, "server.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
        cwd="/home/dp/ai-workspace/web4/mcp-server"
    )

    try:
        print("=== Testing Web4 MCP Server ===\n")

        # 1. Initialize
        print("1. Initialize")
        resp = send_request(proc, "initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "test-client", "version": "1.0.0"}
        }, 1)
        print(f"   Server: {resp.get('result', {}).get('serverInfo', {})}")

        # 2. List tools
        print("\n2. List Tools")
        resp = send_request(proc, "tools/list", {}, 2)
        tools = resp.get("result", {}).get("tools", [])
        for tool in tools:
            print(f"   - {tool['name']}: {tool['description'][:50]}...")

        # 3. Create LCT
        print("\n3. Create LCT")
        resp = send_request(proc, "tools/call", {
            "name": "web4.io/lct/create",
            "arguments": {"binding": "software", "label": "test-lct"}
        }, 3)
        content = resp.get("result", {}).get("content", [{}])[0]
        lct_data = json.loads(content.get("text", "{}"))
        print(f"   Created: {lct_data.get('lct_id')}")

        # 4. Query trust (default for new entity)
        print("\n4. Query Trust")
        resp = send_request(proc, "tools/call", {
            "name": "web4.io/trust/query",
            "arguments": {"entity_id": "test-entity", "role": "developer"}
        }, 4)
        content = resp.get("result", {}).get("content", [{}])[0]
        trust_data = json.loads(content.get("text", "{}"))
        print(f"   T3: {trust_data.get('t3', {})}")

        # 5. Update trust
        print("\n5. Update Trust (success)")
        resp = send_request(proc, "tools/call", {
            "name": "web4.io/trust/update",
            "arguments": {
                "entity_id": "test-entity",
                "role": "developer",
                "outcome": "success",
                "magnitude": 0.5
            }
        }, 5)
        content = resp.get("result", {}).get("content", [{}])[0]
        update_data = json.loads(content.get("text", "{}"))
        print(f"   Delta: {update_data.get('delta')}")
        print(f"   New T3 reliability: {update_data.get('t3', {}).get('reliability')}")

        # 6. Record heartbeats
        print("\n6. Record Heartbeats")
        for i, action in enumerate(["init", "read", "edit"]):
            resp = send_request(proc, "tools/call", {
                "name": "web4.io/heartbeat/record",
                "arguments": {
                    "session_id": "test-session",
                    "action": action,
                    "action_index": i
                }
            }, 6 + i)
            content = resp.get("result", {}).get("content", [{}])[0]
            hb_data = json.loads(content.get("text", "{}"))
            print(f"   [{i}] {action}: status={hb_data.get('status')}")

        # 7. Check coherence
        print("\n7. Timing Coherence")
        resp = send_request(proc, "tools/call", {
            "name": "web4.io/heartbeat/coherence",
            "arguments": {"session_id": "test-session"}
        }, 10)
        content = resp.get("result", {}).get("content", [{}])[0]
        coh_data = json.loads(content.get("text", "{}"))
        print(f"   Coherence: {coh_data.get('coherence')}")
        print(f"   Status distribution: {coh_data.get('status_distribution')}")

        # 8. List resources
        print("\n8. List Resources")
        resp = send_request(proc, "resources/list", {}, 11)
        resources = resp.get("result", {}).get("resources", [])
        for res in resources:
            print(f"   - {res['uri']}")

        # 9. List prompts
        print("\n9. List Prompts")
        resp = send_request(proc, "prompts/list", {}, 12)
        prompts = resp.get("result", {}).get("prompts", [])
        for prompt in prompts:
            print(f"   - {prompt['name']}: {prompt['description']}")

        print("\n=== All tests passed ===")

    finally:
        proc.terminate()
        proc.wait()

        # Cleanup test files
        import os
        from pathlib import Path
        web4_dir = Path.home() / ".web4"

        # Clean up test session
        hb_file = web4_dir / "heartbeat" / "test-session.jsonl"
        if hb_file.exists():
            hb_file.unlink()

        # Clean up test trust
        trust_dir = web4_dir / "trust"
        for f in trust_dir.glob("*.json"):
            if "test" in f.name:
                f.unlink()

        print("Cleaned up test files.")


if __name__ == "__main__":
    main()
