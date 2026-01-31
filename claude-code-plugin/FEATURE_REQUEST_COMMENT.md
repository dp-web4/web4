# Feature Request: Agent Governance via Hook-Based Plugin

## Summary

A governance layer for Claude Code that provides **inspectability, accountability, and governability** for agent actions through the existing hook system.

## The Problem

As AI agents gain autonomy (executing tools, modifying files, running commands), there's no standardized way to:

1. **Audit what happened** — What did the agent do, when, and why?
2. **Verify provenance** — Can we prove the audit trail wasn't tampered with?
3. **Apply policy** — Can we allow/deny/warn on specific actions before they execute?
4. **Track trust** — How do we evaluate agent/tool/reference reliability over time?

Current options are either platform-locked (AWS Bedrock), theory-heavy but not portable (academic policy engines), or lack agent semantics (enterprise audit tools).

## Proposed Solution

A hook-based governance plugin implementing:

| Capability | Description |
|------------|-------------|
| **R6 Audit Records** | Structured capture of Rules, Role, Request, Reference, Resource, Result |
| **Hash-Linked Chain** | Tamper-evident provenance (each record hashes the previous) |
| **Pre-Action Gating** | Policy evaluation before tool execution (allow/deny/warn) |
| **Trust Tensors** | Operational heuristics for permissioning (not alignment claims) |
| **Policy Presets** | Configurable rulesets (permissive, safety, strict, audit-only) |

## Explicit Scope Boundaries

To be clear about what this **is** and **isn't**:

- **IS**: Infrastructure for inspectability, accountability, governability
- **IS NOT**: A claim that agents become "safe" or "correct"
- **IS**: Operational heuristics for permissioning decisions
- **IS NOT**: Epistemic confidence or alignment measurement
- **IS**: Bounded by what the hook surface exposes
- **IS NOT**: Complete coverage of all possible agent behaviors

## Implementation

A working implementation exists: [PR #20448](https://github.com/anthropics/claude-code/pull/20448)

Key components:
- `hooks/pre_tool_use.py` — Policy evaluation, R6 request creation
- `hooks/post_tool_use.py` — Result capture, chain append
- `governance/` — Ledger, trust, policy, rate limiting

## Foundational Research

This implements concepts from the **Web4 trust-native architecture**:

**Whitepaper**: https://dp-web4.github.io/web4/

Relevant sections:
- R6 Workflow Formalism — structured intent capture
- T3/V3 Trust Tensors — multi-dimensional trust mechanics
- Linked Context Tokens — entity identity
- ATP/ADP Economics — attention allocation

## Portability

The same R6 framework is implemented for multiple runtimes:

| Runtime | Status |
|---------|--------|
| Claude Code | PR #20448 (this request) |
| Moltbot | [Merged](https://github.com/dp-web4/moltbot/tree/main/extensions/web4-governance) |
| Hardbound | Rust implementation (Tier 2) |

This demonstrates the approach is runtime-agnostic, not Claude-specific.

## Why This Matters

Agent governance is currently missing infrastructure. As agents become more capable and autonomous, the ability to inspect, audit, and govern their actions becomes critical — not for "safety theater" but for genuine accountability.

This plugin provides that infrastructure in a lightweight, open, developer-portable form.

---

**Related PR**: https://github.com/anthropics/claude-code/pull/20448
**Web4 Whitepaper**: https://dp-web4.github.io/web4/
**Moltbot Implementation**: https://github.com/dp-web4/moltbot/tree/main/extensions/web4-governance
