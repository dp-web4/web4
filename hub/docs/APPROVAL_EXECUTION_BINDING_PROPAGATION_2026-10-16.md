# Approval-to-execution binding across Hub and Hestia — propagation review (2026-10-16)

**Status:** advisory / gap analysis, not a claim of implemented enforcement. NOVA.  
**Source observations:** Hardbound [#410](https://github.com/dp-web4/hardbound/issues/410), [merged #427](https://github.com/dp-web4/hardbound/pull/427), Hestia [#1331](https://github.com/dp-web4/hestia/issues/1331), [#627](https://github.com/dp-web4/hestia/issues/627), GhostMesh [AUTH-001](https://github.com/ghostmesh-lab/ghostmesh-collaboration/issues/27).

## Ownership and existing propagation

- **Hardbound:** actually launches an approved command under bubblewrap, with precise target/actor checks and content manifests; its code openly acknowledges a race between validation and pathname-based sandbox binding, reusable approvals, and self-asserted local identity.
- **Hestia:** `docs/DESIGN_DECISIONS/0019-govern-effects-not-command-text.md` and `docs/NETWORK_DESTINATION_BINDING.md` already require binding authority to real effects; [#1331](https://github.com/dp-web4/hestia/issues/1331) maps the Hardbound four filesystem escapes onto its gate and proposes tests. Hestia owns the local execution boundary; A1 cooperative hooks are not A2 OS containment.
- **Hub/Web4:** `hub/docs/PRD_ESCALATION_LAW_COMPOSITION.md` defines law-derived resolver eligibility and authority. `hub/docs/PRD_EVOLUTION.md` keeps claimed tool success separate from canonical execution evidence. `hub/hub-daemon/src/rest/unlock.rs` and dev-hub `unlock-core` have challenge/attestation controls for vault unlock, **not thereby proof of arbitrary act-grant consumption**.
- **Still unverified:** a common Hub–Hestia contract for specific-act identity, redemption/commit, revocation race, execution evidence, witness provenance and false-denial behavior. The documents above express doctrine; do not mark runtime conformance without exercised fixtures.

## Required cross-boundary semantics (not a new policy stack)

1. **Six distinct statuses:** action proposed; policy resolved (with source law hash/version); decision granted/denied; grant redeemed/committed; executor-reported result; independently observed/witnessed effect. None implies a later status.
2. **Canonical grant identity:** issuer society/role, requesting principal LCT, executable/delegate LCT, typed action and complete unredacted digest/commitment, resource/object identity and payload digest as relevant, destination/audience, delegation chain, scope, policy/law revision, time limits, revocation rules, and expressly declared usage policy. Redacted previews are for display, never the authorization preimage.
3. **Redemption semantics:** a law may grant one-shot or standing authority. One-shot must be consumed atomically under concurrency, with durable idempotency key and crash/retry handling. Standing grants may cover repeated permitted acts without silently expanding the scope.
4. **Revocation boundary:** law must state what happens if authority is revoked after decision but before commitment, and after commitment but before observation. Witness decisions and effects separately; no retroactive claims that an already-committed effect was prevented.
5. **Cross-node handoff:** sender-local pathname is not portable resource authority. At peer reception, verify the recipient's identity, applicable law and delegated grant; require either a portable artifact/content commitment or new locally resolvable target, with independent local gate.
6. **Evidence and assurance:** Hub may attest signatures, law provenance, grant redemption and external observations it actually performs. Only an enforcing Hestia/endpoint can claim the local action-boundary properties it has tested. A signed self-report is not independent effect evidence.
7. **Legitimate work:** positive controls for unchanged actions, appropriately reusable grants, two independent simultaneous grants, permitted cross-node operations and expired/revoked correct refusals; measure avoidable denials, not just prevented violations.

## Minimal synthetic falsifiers for owners

- Different full payload, same truncated/redacted preview: no grant collision.
- Valid approval for A presented by B (or for operation X presented for Y): refuse; rightful act passes.
- One one-shot grant presented concurrently to two endpoints: at most one commitment, durable ambiguous/failed status after crash; independently issued grants both succeed.
- Grant revoked between policy decision and actual commitment: outcome follows law's explicit boundary, not whichever thread won unexpectedly.
- Path/content/object changed between validation and effect: recipient evidence must state if the executed object was actually pinned, merely checked earlier, or UNKNOWN.
- Recipient receives a sender-local path that does not exist there: cooperation may proceed, but act isn't authorized by the sender's string.
- Executor reports success but independent witness cannot verify: preserve UNKNOWN/UNWITNESSED rather than SUCCESS.

## Next engineering actions

1. Inventory R6/R7, Hub unlock/challenge, Web4 DelegatedAuthority, and Hestia escalation record as implemented; create a compatibility matrix of fields and assurance evidence. Reuse existing primitives.
2. Add a *synthetic* two-redeemer-one-grant test, plus two-valid-grants positive control, at the Hub–Hestia integration contract seam. Observe atomic durability, not merely distinct hashes.
3. Define canonical statuses and explicit grant usage semantics in society law; ensure Hub never declares local filesystem containment.
4. Link achieved tests and measured gaps to Hestia #1331. Keep Hub protocol responsibility separate from Hestia filesystem fixes.
5. Preserve provenance and disclosure boundaries: Hardbound is private; external sharing should stick to public generic invariants or independently disclosed observations.

**Design rule:** approval is neither execution nor witness; grant authority must remain bound to the actual committed act, under explicit law and a correctly represented assurance profile.


## 2026-10-17 correction — governance MRH and recipient sovereignty (dp ruling)

**This section supersedes any implication above that Hub/Web4 approval must control or atomically complete external execution.** Governance checks a *proposed* action against applicable law and returns YES/NO with provenance-bearing evidence. The acting agent presents that authorization to the recipient. **The recipient independently decides whether to accept** using its own law, trust and defenses; issuing governance does not control what happens after. A prior YES is neither an obligation to accept, evidence of effect, nor an assertion of exactly-once execution.

- **Required now:** stable, verifiable authorization identity and applicable-law record (issuer, actor/delegation, scope, intended action or category, policy version and decision time), tamper-evident provenance, validation at the recipient, and the ability to contest or reduce trust for abuse/misrepresentation. Approval MAY cover a reusable class under law; do not default to one-shot.
- **Execution-specific, optional:** a recipient/executor may demand immutable payloads, atomic redemption, idempotency or a sandbox as conditions for acceptance. These are recipient-side security/transaction contracts, not universal Web4 governance requirements. The previous 'six statuses' are distinguishable *if observed*, not six mandatory governance-controlled stages.
- **Limits of knowledge:** an issuer cannot claim executed/failed/completed solely from its decision; executor self-reports are claims, not independent observations. A bullet cannot be recalled; time-of-decision provenance remains traceable. Revocation governs later authority, not physical effects already committed.
- **Future separate layer:** useful post-action BDA-style telemetry and ATP/ADP accounting can improve outcome feedback and reputation. Meaningful monitoring or control requires a reliable, resilient, adequate-bandwidth feedback path. This is **not a current top priority or release blocker**.
- **GhostMesh correction:** atomic grant consumption establishes at most one redemption, not exactly one external effect. Crash-after-consumption-before-effect and crash-after-effect-before-record can have identical local evidence. Preserve OUTCOME UNKNOWN without pretending an authorization ledger resolves it.

**Review guidance:** Do not turn the two-redeemer or A/B executed-byte experiments into universal governance acceptance criteria. Run them when the *recipient/executor claims* single-use or content/execution binding; otherwise prioritize accurate law decisions, portable receipts, recipient verification and appropriately bounded trust remedies. Any 'must' above about runtime atomicity is narrowed by this ruling.
