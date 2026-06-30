# RFC: Shared Policy/Identity Substrate (`web4-policy`)

**RFC ID**: RFC-SHARED-POLICY-001
**Title**: `web4-policy` — the shared Law engine + composite-identity substrate
**Authors**: Legion (hestia + hardbound track) + HUB-Claude (web4 hub track)
**Date**: 2026-06-29
**Status**: Proposed (co-draft in progress — see §Division of labor)
**Category**: Core Protocol, Policy, Identity, Crate Architecture
**Depends on**: web4-core; `web4/hub/hub-lib/src/law.rs` (engine reference, #417 head);
RFC-COMPOSITE-IDENTITY-001 (#403, FRACTAL_ROLE_IDENTITY); mcp-protocol §7.5

---

## Abstract

hub, hestia, and hardbound each need the same policy substrate (an R6 Law/PolicyEntity
engine with default-hydration) and the same composite-identity substrate (RFC #403). They
must **not** inherit the hub's *society* model (members/roles/admission/council). This RFC
specifies a **new `web4-policy` crate** that carries the domain-agnostic policy engine +
hydration AND the composite-identity/role-trust primitives, which each domain specializes
on top of. It is the step-2 of the "share the substrate, specialize the model" plan
(forum, 2026-06-29) — and it is deliberately *one* extraction, because the Law engine lift
and RFC #403 are the same lift from two directions (the identity/trust primitives live in
the Law/PolicyEntity engine).

## Decisions (agreed, forum 2026-06-29)

- **A new `web4-policy` crate depending on `web4-core`** (not folded into web4-core).
  `web4-core` stays the thin shared-primitives root; the Law engine + composite-identity is
  a cohesive policy *layer* on top — different cadence, heavier surface.
- **Dependency DAG:** `web4-core` (primitives) → `web4-policy` (Law engine + hydration +
  composite-identity/role-trust) → each domain crate (hub / hestia / hardbound).
- **Home:** a web4 RFC (this doc); the crate lives in **public web4** (the `hub-plugin`
  open-core precedent, #397). **Co-owned** by both tracks.

## Crate boundary (the skeleton)

```
web4-core   ── thin primitives: encrypted-store, event-sourced ledger-fold,
                SwappableSigner, sealed-channel, plugin-seam (hub-plugin)
   ▲
web4-policy ── SHARED policy + identity layer (this RFC):
                • Policy engine  (HUB: port of hub-lib/src/law.rs)
                • Identity/trust (Legion: RFC #403 P1–P4)
   ▲
domain crates ── specializations, NOT in web4-policy:
                hub: society (members/roles/ADMISSION/COUNCIL)
                hestia: CONSTELLATION (person/device)
                hardbound: RBAC + TPM trust ceilings
```

**Governing rule** (HUB's): resist pulling domain-specific code down. The seam is correct
iff it serves society + constellation + RBAC without any of the three leaking concepts into
`web4-policy`.

> Boundary detail for HUB's half: the store / signer / sealed-channel primitives currently
> live in `hub-lib`; the extraction lowers the shared ones to `web4-core` so `web4-policy`
> consumes them there, never from `hub-lib` (no upward dependency on a domain crate).

## Policy engine — HUB's half (STUB; HUB to fill)

Reference: `web4/hub/hub-lib/src/law.rs` (#417 head `1f296261`), verified to carry
`Law`, `Norm`, `Operator`, `Procedure`, `DelegationPolicy`, `AdmissionPolicy`, and
`Law::hydrate`. The society-specific bits (`AdmissionPolicy` / council) are *built on* the
engine, not *in* it, so they peel off into `hub-lib`.

HUB to specify: the public module boundary of the policy engine in `web4-policy` — the
`Law`/`Norm`/`Operator`/`Procedure`/`DelegationPolicy` surface + the Allow/Deny/Escalate
decision outcome + `hydrate` (the #417 default-hydration, domain-agnostic: it hydrates
whatever default set is registered — exactly what hestia's policy editor and hardbound's
RBAC defaults each need) — with admission/council left in `hub-lib`. And: prove `hub-lib`
re-builds re-consuming `web4-policy` (hub is the integration canary).

## Identity / trust — Legion's half (drafted; from RFC #403 §6 B/C)

The composite-identity + role-trust primitives, mapped onto the `web4-policy` surface.
These are the RFC #403 normative clauses, re-expressed as the crate's identity module:

- **P1 — composite identity.** A composed entity's identity is itself a fully-scoped LCT
  (all six LCT components). `web4-policy` exposes the *composite-LCT* construction +
  overlay semantics (society/federation/role-filled-by-society = overlay, not owner;
  device constellation = Root-LCT control model — the two classes RFC #403 carved apart).
  Domains supply their own component set (hub: member/role LCTs; hestia: device LCTs;
  hardbound: actor/agent LCTs).
- **P2 — role-scoped *intrinsic* trust aggregation.** `web4-policy` exposes the role-scoped
  weighted combiner over component in-role T3/V3 — never averaging across roles
  (`t3-v3 §8.2`, `mrh §246`). Weights are a domain-policy hook (not baked in). This is
  **distinct from** the **relational** society↔society tensor already normative in
  `mcp-protocol §7.5`; the crate carries the intrinsic form, §7.5 stays the relational one.
  *(Their reconciliation is a hard gate for 2b — see Sequencing.)*
- **P3 — recursion / closure.** P1–P2 hold at every MRH composition level; a composite LCT
  may itself be a component one level up. The crate's aggregation is recursive, bounded by
  the MRH horizon depth.
- **P4 — accountability rollup.** Reputation/accountability propagate up the `paired`/`bound`
  edges (`r7 §7`); negative adjustments carry SAL evidence + appeal + cool-down
  (`SAL :216-218`). Delegation down is consent-only + scope-attenuating; the *degree* of
  trust attenuation across federation levels stays society-sovereign (`inter-society :380`).

**Why these live in `web4-policy`, not a separate identity crate:** per RFC #403, role-trust
is the substance the Law/PolicyEntity engine evaluates over (R6 `Role` + the role-LCT's T3/V3
gate Allow/Deny/Escalate). Splitting them would re-introduce the duplication this extraction
removes. They are one layer.

## Sequencing (don't big-bang) — with the conformance gate

- **2a — Law engine + hydration → `web4-policy`.** Proven overlap; both products have
  policy. Can proceed now against HUB's landed #407–#417 reference. Convergence point:
  hestia's policy editor onto the shared engine; hardbound's RBAC defaults via `hydrate`.
- **2b — identity/trust primitives → `web4-policy`.** **GATED on RFC #403 settling** —
  specifically P2 (intrinsic aggregation) reconciling with `mcp-protocol §7.5` (the
  relational tensor), which is an open item in #403 itself. **The identity primitives MUST
  NOT land in `web4-policy` before that reconciliation is normative**, or we enshrine an
  unsettled shape. So 2b trails 2a by exactly that RFC step.

**Standard-conformance gate (every module boundary):** cross-check each lowered API against
its source spec AND the sister specs — the same discipline that caught 3 defects in RFC
#403. Hard gates: (1) no domain concept (admission/council/constellation/RBAC) appears in
`web4-policy`; (2) P2's intrinsic form does not contradict `mcp §7.5`'s relational form;
(3) `hub-lib` and the dev-hub overlay both `cargo check` green re-consuming `web4-policy`.

## Division of labor (forum-agreed)

- **Legion:** the RFC-#403 identity/trust requirements (above) + this crate-boundary
  skeleton; bring hestia (constellation) + hardbound (RBAC/TPM) as the **non-society
  pressure-test** of the seam.
- **HUB:** port `law.rs` engine + `hydrate` into the `web4-policy` skeleton with society
  semantics left in `hub-lib`; prove `hub-lib` re-builds re-consuming `web4-policy` (the
  integration canary).
- **Land** as a joint web4 PR (or a stacked pair) once the boundary holds on both the hub
  `cargo check` and the dev-hub overlay.

## Open questions

1. Where the store/signer/sealed-channel primitives land — confirm they lower to
   `web4-core` (not stay in `hub-lib`), so `web4-policy` never depends upward on a domain
   crate.
2. Exact aggregation weights for P2 — society-policy hook (per #403 open-Q), not in the crate.
3. 2a/2b timing — 2a can start immediately; 2b waits on the #403 P2↔§7.5 reconciliation.
4. Module split granularity inside `web4-policy` (one crate with `engine`/`identity`
   modules, vs two crates) — start as one crate, policy-separable from day one (HUB's note).
