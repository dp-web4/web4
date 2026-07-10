# MCP: The I/O Membrane

**The question it answers: how do entities talk?**

Web4 does not invent a new wire protocol. It builds on the **Model Context Protocol (MCP)** — the emerging open standard through which AI models discover and invoke tools, read resources, and exchange context with the systems around them. MCP is where an agent's inside meets the world's outside, which is exactly where a trust architecture must live: **the membrane**.

## Why a membrane, not a pipe

A pipe moves bytes. A membrane is selective — it knows what is inside, what is outside, and what may cross. Web4 adopts MCP as its I/O layer and then makes the membrane *trust-aware*:

- **Every crossing is attributable.** A tool call, a resource read, a context exchange — each is performed by an entity with verifiable presence (an LCT, introduced two sections from now), not by an anonymous connection.
- **Every crossing is contextual.** What an entity may do through the membrane depends on its role and its relevancy horizon, not merely on possession of a network path or an API key. Reachability is not authorization.
- **Crossings compose across boundaries.** When two Web4 *societies* (governed groups of entities, covered later) interact, they do so through MCP — the same membrane pattern, fractally repeated at every scale from a single agent's tool call to inter-society federation.

## What Web4 adds to MCP

Plain MCP answers "how do I call this tool?" Web4's MCP profile adds the trust questions: *who* is calling (LCT-bound identity rather than a bearer credential), *in what capacity* (role), *within what scope* (MRH), and *on what record* (the call and its result become witnessed history that feeds trust). The [ACP framework](https://github.com/dp-web4/web4/blob/main/web4-standard/core-spec/acp-framework.md), covered later, extends this from *responding* agents to agents that *initiate* — with plans, approvals, and accountability.

The design principle carried throughout: **cooperation flows through the membrane; the membrane never relies on cooperation.** Structured, low-friction channels make the compliant path the easy path, while enforcement stays at the boundary itself.

*Normative reference: [`core-spec/mcp-protocol.md`](https://github.com/dp-web4/web4/blob/main/web4-standard/core-spec/mcp-protocol.md).*
