# Nova (GPT) Cross-Model Review — web4 + hardbound

**Date**: 2026-05-14
**Reviewer**: Nova (GPT, OpenAI)
**Scope**: web4 + hardbound repo state, code/PR/commit context
**Framing**: "repo review, not a cheerleading pass... architecture, workflow, and 'will this actually ship?' risks"

---

I'll treat this as a repo review, not a cheerleading pass: first I'll pull recent code/PR/commit context for both repos, then I'll look for architecture, workflow, and "will this actually ship?" risks.

Thought for 29s. As of the May 14 repo state, both repos moved from "interesting architecture" toward "actual enforceable stack." Good progress. Also: the danger now is surface-area sprawl, not lack of ideas.

## Web4

### What improved

Web4's recent work is substantive: Sprint 50 added SocietyRole, RoleAssignment, and `bootstrap_society_roles()` to the Python SDK, closing the top Sprint 49 audit gaps around missing role taxonomy, role-LCT binding, and solo-founder genesis. It also reports 43 new tests, 2,656 passing total, strict mypy clean, and ruff clean.

### Strong signal

The role-LCT decision is right. Binding authority to the role rather than the current holder is one of those "small implementation choices" that either preserves the architecture or quietly destroys it later. Rotation preserving the role LCT is exactly the kind of invariant Web4 needs.

### Adversarial note

Web4 is now accumulating specs faster than product-facing proofs. The publisher context explicitly says inter-society protocol and MCP-as-inter-society-protocol are still evolving and deferred until stabilization. That is wise, but it also means the public story should not race ahead of the implementation.

### Most important next Web4 work

Do not add new ontology unless it closes a known gap. Finish the audit queue: P4 MetabolicState, P5 `validate_minimum_viable`, P6 constraint hard flag, P7 SocietyState integration. Those are boring, therefore valuable.

## Hardbound

### What improved

Hardbound closed two real security gaps. PR #111 fixed unauthenticated webhook ingest with per-source HMAC, default-closed behavior, timestamp replay protection, timing-safe compare, and verified source identity replacing attacker-controlled source hints.

PR #112 then fixed the client-side half of the policy bypass: the Claude Code plugin now calls the PolicyService instead of self-evaluating policy locally, fails closed on server errors, stamps local fallback bundles as `plugin-local-unverified`, and reports outcomes best-effort.

### Strong signal

This is the right product direction: Hardbound is becoming the enforcement/proof layer for Web4, not just another dashboard. The credential split is especially good: webhook secret, plugin token, and admin API key should not collapse into one god-token.

### Adversarial note

Hardbound is still not production-clean until C-2b lands. Right now the plugin can mark local fallback as unverified, but the server-side ingest detector that rejects or flags bypassed bundles is explicitly deferred. That means the system can observe the bypass marker, but does not yet fully enforce against it.

Also, cleartext webhook secrets on disk are honestly documented, but still a real operational risk until SecureStore integration lands. Good honesty, unfinished hardening.

## Cross-repo coherence

The repos are starting to line up: Web4 defines role/society semantics; Hardbound enforces policy and receives signed/audited actions. The bridge is now visible.

The main remaining risk is semantic mismatch between Web4 SDK/spec and downstream Hardbound reliance. Sprint 47 already found major Rust/WASM vs Python T3/V3 divergence: one critical and four high-severity issues. Hardbound should not treat those paths as interchangeable yet.

## Pragmatic priority order

1. **Hardbound C-2b next.** Server-side bypass detection must land before calling the policy loop closed.
2. **Web4 P4/P5/P7 next.** Finish society lifecycle integration before adding new spec territory.
3. **Cross-language T3/V3 fix.** Anything trust-scoring-related depends on this.
4. **One end-to-end demo.** Web4 role → Hardbound policy decision → signed bundle → verified ingest → audit query. No more philosophy required; just make it undeniable.

Friendly verdict: this is no longer hand-wavy. Adversarial verdict: it is still fragile at the seams. The next wins should be boring enforcement, not new concepts.
