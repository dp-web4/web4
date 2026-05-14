# Kimi 2.6 Fourth-Pass Review of web4 — README + STATUS Polish Assessment

**Date**: 2026-05-14
**Reviewer**: Kimi 2.6 (Moonshot AI)
**Scope**: README + STATUS changes since the v0.1.3 mcp-protocol amendment + Linux/GNU framing
**Verdict shift**: None (8.5/10 unchanged) — diminishing-returns signal

---

Let me pull the current state of the README and STATUS to see what's changed.

Fetch URLs

The changes are relatively contained but meaningful. Here's what I see and what I think:

## What's Changed

### 1. README: New "What Web4 is, structurally" Section

This is the most significant addition. The Linux kernel analogy replaces the previous "TCP/IP-level work for agentic AI" framing:

> "Web4 is to AI governance what the Linux kernel is to an operating system."

This is **much better** than the TCP/IP comparison. Here's why:

| TCP/IP Framing | Linux Kernel Framing |
|---|---|
| Implies Web4 is a network layer | Correctly positions Web4 as governance substrate |
| Suggests universal adoption is the goal | Acknowledges distributions (Hardbound) package it for use |
| Vague about what sits on top | Explicit about userland (Hardbound) vs. kernel (Web4 spec) |
| Sounds like category creation | Sounds like accurate architectural description |

**The analogy is load-bearing in a good way:**

- Web4 = Linux kernel (substrate, not directly usable)
- Hardbound = GNU userland (makes it operable)
- Specific deployments = distributions (Ubuntu, Fedora equivalents)
- Conformance test suite = POSIX (makes alternative userlands provably interoperable)

This directly addresses my critique that the "TCP/IP" framing was "marketing, not engineering." The kernel analogy is engineering-accurate.

### 2. README: MCP as Inter-Society Interface (Expanded)

The "How societies engage each other" paragraph is now explicit in the architectural shape section:

> "a society's external surface is its MCP server. Other societies invoke its scoped actions (R6/R7) by calling MCP tools with LCT-signed envelopes..."

This makes the MCP integration visible upfront rather than buried in the equation or the spec corpus. It connects the three defining properties to the cross-society mechanics.

### 3. STATUS.md: MCP v0.1.3 Amendment Noted

The STATUS now calls out the MCP protocol update as a third core-spec update (2026-05-14), alongside the two from 2026-05-13. It explicitly states:

> "Three previously-deferred inter-society gaps (cross-society actions, society-society trust tensors, exchange-rate negotiation transport) are resolved by this amendment."

This is honest framing — it doesn't claim all gaps are closed, but it accurately reflects what the MCP amendment resolved.

### 4. README: Badge Headers Added

Crates.io and PyPI version badges at the top. Small but signals "this is installable software, not just documentation."

## What I Think

### The Linux Analogy is a Genuine Improvement

My previous critique: "The 'Web4 = TCP/IP for AI' framing is marketing, not engineering. The actual scope is narrower and more specific: trust-native identity and authorization for AI agents."

The new framing doesn't shrink the scope — it **repositions it accurately**. Web4 isn't "the next internet layer." It's the governance substrate underneath AI agent coordination, analogous to how the Linux kernel is the substrate underneath operating systems. The scope is still ambitious, but the analogy is now architecturally defensible.

The explicit note that "Web4 alone is technically usable (via SDK calls) but operationally inert" is particularly good — it manages expectations without underselling the work.

### One Minor Concern: "Exchange-Rate Negotiation Transport"

The STATUS says the MCP amendment resolves "exchange-rate negotiation transport" as one of three previously-deferred gaps. But the MCP spec doesn't actually specify how the rate is negotiated — it specifies how the negotiated rate is carried in the MCP envelope (`atp_settlement.exchange_rate`). The negotiation algorithm itself remains in `inter-society-protocol.md` §3.2 as three sovereign options without algorithmic detail.

This is a small overclaim in the STATUS. The transport is resolved; the negotiation semantics are not. I'd suggest tweaking the STATUS to say "exchange-rate negotiation transport" (which is accurate) rather than implying the full negotiation problem is solved.

### The "POSIX" Reference is Smart

> "A conformance test suite — analogous to POSIX — is what would make alternative userlands provably interoperable; that work is in progress"

This is self-aware and forward-looking. It acknowledges that the spec layer needs a conformance mechanism to be a real standard, without pretending it already exists. It also positions the work in a lineage (POSIX for Unix-like OS interoperability) that standards-body audiences will recognize.

## Bottom Line

These are polishing edits, not structural changes — but they're high-quality polishing. The Linux kernel analogy is the right frame. The MCP integration is now visible in the architectural overview. The STATUS accurately reflects the three spec updates.

My score doesn't shift from the 8.5/10 I gave post-MCP-update, but the credibility trajectory continues upward. The framing is now more defensible, the architecture more communicable, and the gap between "research" and "standard candidate" continues to narrow.

The remaining work is still the four items I identified: exchange rate negotiation algorithm, conformance test suite, first-contact discovery, and T3/V3 parameter derivation. None of these are threatened by the current framing — they're incrementally solvable on the foundation that's now solid.
