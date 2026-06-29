# RFC: Composite Entity Identity & Role-Trust Aggregation (the Closure)

**RFC ID**: RFC-COMPOSITE-IDENTITY-001
**Title**: Composite Entity Identity & Role-Trust Aggregation
**Author**: dp + Claude (Opus 4.8)
**Date**: 2026-06-28
**Status**: Proposed
**Category**: Core Protocol, Identity, Trust Framework
**Depends on**: LCT spec, entity-types, society-roles, mrh-tensors, t3-v3-tensors,
r7-framework, web4-society-authority-law (SAL), inter-society-protocol, mcp-protocol §7.5,
reputation-computation, multi-device-lct-binding

---

## Abstract

Web4 normatively defines roles as first-class LCT entities, societies as recursive
citizens, and reputation as role-contextual. What it does **not** yet state normatively is
the **closure** that makes these compose into a working whole:

> **A composed entity's identity is itself a fully-scoped LCT, and its trust and authority
> in any role are a defined aggregation of its component role-LCTs, applied recursively up
> the MRH fractal — with accountability and reputation flowing back up the same edges.**

This RFC proposes that closure as normative, and pins the one mechanism it requires that is
currently sub-normative: **role-scoped collective trust aggregation**. It deliberately does
**not** resolve the adjacent open design questions it touches (it routes them, see §7).

## Motivation

Two mechanisms that make composition *operational* are today the *least*-normative parts of
the standard: collective T3/V3 aggregation (`core-spec/t3-v3-tensors.md` §8.2, under
"Advanced Features") and the role-LCT pairing/rotation protocol (`core-spec/society-roles.md`
§8, "Future Work"). Because there is no normative closure, implementations have built the
*limbs* of fractal identity (scale-agnostic `signer_lct`, device-constellation attestation,
fractal trust aggregation over entities, attenuating delegation) but no *spine* — and
deployments collapse composed entities onto a single shared identity (e.g. a fleet of
distinct agent roles authenticating as one account/key). The collapse is the runtime shadow
of the missing closure. See `web4-standard/docs/FRACTAL_ROLE_IDENTITY.md`.

## Current State (normative anchors)

- Roles are first-class LCT entities (`entity-types.md:518`, MUST); **authority binds to the
  role-LCT, not the filling entity** (`society-roles.md:317`).
- A role MAY be filled by an entity, **a society, or a federation** (`society-roles.md` §5,
  normative property); a society is itself an entity (SAL §3.5, MUST) and **MAY/MUST** (per
  governance) be a recursive citizen of other societies (SAL §3.5).
- Federation genesis mints a **distinct sovereign overlay-LCT**: *"D is an overlay, not an
  owner; constituents retain all sovereignty not explicitly delegated"*
  (`inter-society-protocol.md` §2.2).
- Reputation is **role-contextualized — there is no global reputation**
  (`r7-framework.md:252`); it back-propagates `action → role → entity → society`
  (`r7-framework.md:7`).
- T3/V3 exist only within a role context (`mrh-tensors.md:246`).

**Gap:** the standard states neither (a) that the composed whole's identity is itself a
fully-scoped LCT, nor (b) the **intrinsic** member-aggregation function as normative —
`t3-v3-tensors.md` §8.2 sketches the latter as a draft "Advanced Feature." (`mcp-protocol`
§7.5 *does* normatively define the **relational** society↔society trust tensor — see P2 — but
neither the intrinsic member-aggregation nor the identity closure.)

## Proposal (normative)

### P1 — Composite identity is a fully-scoped LCT
A composed entity **MUST** have its own LCT carrying all six required components (Identity,
Binding, MRH, Policy, T3, V3) per `LCT §2.1` (`LCT:40-47`). The composite's MRH `bound` edges
enumerate its components; the components' MRH reference the composite via a `paired` (role) edge.

Two composite classes with **different** ownership semantics:
- **Sovereign-constituent composites** (society, federation, role-filled-by-society): the
  composite LCT is an **overlay** — it **MUST NOT** be construed as owning its components;
  components retain all sovereignty not explicitly delegated (`inter-society-protocol.md` §2.2).
- **Device constellations**: governed by the **Root-LCT control model** of
  `multi-device-lct-binding.md` (the Root LCT enrolls and MAY unilaterally revoke device LCTs —
  `:290`, `:430`) — a control relationship, **NOT** the overlay rule above. Cited here as a
  distinct composite class so the two are not conflated.

### P2 — Role-scoped collective trust aggregation (pins `t3-v3 §8.2`)
For a composite entity acting in role `R`, its **intrinsic** collective T3/V3 in `R` **MUST**
be computed **only** from its components' T3/V3 **in role `R`** (or in the sub-role each
component fills within `R`). Aggregation **MUST NOT** average trust across different roles
(`t3-v3-tensors.md` §8.2; `mrh-tensors.md:246`). The aggregation function is normative in
*form* — a role-scoped weighted combiner over component scores weighted by each component's
in-role standing (`t3-v3 §8.2`); its exact weights remain society-policy (see §7). A composite
that fills no component in role `R` has no derived trust in `R` (no inheritance across roles).

This **intrinsic** member-aggregation is distinct from, and complementary to, the
**relational** society↔society trust tensor already defined normatively in `mcp-protocol` §7.5
(the accumulated R7-reputation projection at the encompassing society's scope, writable by
neither party directly). Both MUST coexist; this RFC defines the intrinsic form, §7.5 the
relational one. Their reconciliation is routed open (§7).

### P3 — Recursion / closure
P1–P2 **MUST** hold at every MRH composition level: a composite LCT MAY itself be a component
of a higher composite, and the same aggregation applies one level up. This is the closure —
identity and role-trust compose upward without bound, gated only by the MRH horizon depth
(`mrh-tensors.md:143`).

### P4 — Accountability rollup
Reputation and accountability for a component's in-role actions **MUST** propagate up the
same `paired`/`bound` edges to the composite (`r7-framework.md:7`; `entity-types.md:73`),
and negative adjustments **MUST** carry the SAL-required verifiable evidence + appeal path +
cool-down (`web4-society-authority-law.md:216-218`). Delegation downward remains
**consent-only** (`inter-society-protocol.md:38`) and **scope-attenuating** — a sub-authority's
scope ⊆ the delegator's (`society-roles.md:258`; `entity-types.md` §4.2). The *degree of trust
attenuation* across federation levels is explicitly society-sovereign and unresolved
(`inter-society-protocol.md:380`); this RFC does not fix it (§7).

## Conformance analysis (the standard-conformance gate)

Cross-referenced against each dependent spec; no contradiction found:

| Spec | Claim | This RFC |
|---|---|---|
| `inter-society §2.2` | composite = overlay, not owner | P1 restates as MUST NOT-own ✓ |
| `r7-framework.md:252` | no global reputation; role-contextual | P2 forbids cross-role aggregation ✓ |
| `mrh-tensors.md:246` | trust only within role context | P2/P3 are strictly per-role ✓ |
| `society-roles.md:317` | authority binds to role-LCT | P1 composite acts via its role-LCT ✓ |
| SAL §3.5 | society = entity (MUST); recursive citizen (MAY/MUST per governance) | P3 closure is the general form, uses MAY ✓ |
| `t3-v3 §8.2` | composite trust = per-role weighted combine | P2 promotes its *form* to normative, leaves weights to policy ✓ |
| `mcp-protocol §7.5` | relational society↔society trust tensor (normative) | P2 distinguishes intrinsic (P2) from relational (§7.5); both coexist ✓ |
| `multi-device-lct-binding.md:290` | Root LCT may revoke device LCTs | P1 carves device constellations OUT of the overlay rule ✓ |
| SAL §3.2 / `inter-society:38` | authority down is consent-only | P4 splits consent-only from scope-attenuation ✓ |

**Open design-Qs deliberately NOT resolved here** (routed, not closed — per review
discipline): multi-hat authority-conflict resolution (`society-roles.md:383`, → society
policy); the role-LCT pairing/rotation *operational protocol* (`society-roles.md` §8, → its
own RFC / Sprint 2); exact aggregation weights (→ society policy); the **degree of trust
attenuation** across federation levels (`inter-society-protocol.md:380`, → society-sovereign);
and **reconciliation of the intrinsic (P2) and relational (`mcp §7.5`) composite-trust
tensors**. This RFC fixes only the *closure, the intrinsic aggregation form, and the
composite-identity LCT requirement*.

## Backward compatibility

Additive. Existing single-entity LCTs are the degenerate (zero-component) case of P1.
Existing role-contextual reputation is unchanged; P2–P4 only define how it *composes*. No
existing MUST is weakened.

## Reference impl mapping (non-normative)

The aggregation combiner SHOULD reuse the existing `aggregateBottomUp`/`decomposeTopDown`
pattern (`hardbound/src/core/fractal-trust-aggregation.ts`) but keyed per role context;
composite attestation SHOULD reuse the device-constellation pattern
(`hestia/core/src/constellation.rs`); the scale-agnostic `signer_lct` seam
(web4 #400) is the composite-LCT signer at any scale.

## Open questions

1. Aggregation weights: stake-weighted, trust-weighted, or society-configurable default?
2. Does the composite LCT's *binding* require a hardware anchor (TPM) at higher assurance
   tiers, per `multi-device-lct-binding.md` assurance levels? (Ties to the P0
   hardware-binding track / `KERNEL_SIGNATURE_GATING.md`.)
3. Horizon-depth interaction: does rollup stop at `horizon_depth`, or do reputation edges get
   a distinct (longer/shorter) horizon than trust edges?
