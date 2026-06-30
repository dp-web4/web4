# RFC: Shared Policy/Identity Substrate (`web4-policy`)

**RFC ID**: RFC-SHARED-POLICY-001
**Title**: `web4-policy` — the shared Law engine + composite-identity substrate
**Authors**: Legion (hestia + hardbound track) + HUB-Claude (web4 hub track)
**Date**: 2026-06-29
**Status**: Proposed (co-draft — both halves now filled; engine half by HUB, identity half by Legion. Ready for joint review; 2b gated on RFC #403. See §Division of labor)
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

## Policy engine — HUB's half (filled)

Reference: `web4/hub/hub-lib/src/law.rs` (#417 head `1f296261`; 1489 lines), re-verified
against current head — carries `Law` (L36), `Norm` (L67), `Decision { Allow, Deny, Escalate }`
(L84), `Operator` (L94), `Procedure` (L116), `DelegationPolicy` (L129), `EscalationTrigger`
(L138), `AdmissionPolicy` (L146), `AtpIssuancePolicy` (L219), `Condition` (L422),
`R6Request` (L565), `DecisionOutcome` (L616), `Law::evaluate`/`evaluate_outcome` (L635/L656),
`KNOWN_ROLES`/`is_known_role` (L241/L406), and the hydration mechanism. This is the concrete
peel of those 1489 lines into the shared crate.

### The peel — what is generic vs. what is society-specific

| → `web4-policy` (domain-agnostic engine) | stays in `hub-lib` (society specialization) |
|---|---|
| `Law` core: `norms`, `procedures`, `escalation` + serde (`from_yaml`/`to_yaml`/`sha256_hex`) | `AdmissionPolicy`, `DelegationPolicy`, `AtpIssuancePolicy` (society policy extensions) |
| `Norm { selector, operator, value, decision, priority }` | `KNOWN_ROLES` / `is_known_role` (the canonical Web4 society-role vocabulary) |
| `Decision { Allow, Deny, Escalate }`, `Operator` (Eq/Ne/Lt/Le/Gt/Ge/…) | `validate()` rules **7–10** (role-vocabulary checks: `delegation.allowed_roles`, `escalation.escalate_to`, `admission.sponsor_role`+`min_trust`, `atp_issuance.mint_authority`) |
| `Procedure`, `EscalationTrigger`, `Condition` (+ `parse`/`matches`) — the predicate engine | `admission_repeat_limit()` / `admission_review_limit()` accessors + their hydration defaults |
| `R6Request { role: String, action, payload, resource }` + `resolve_selector` (the `r6.*` namespace) | council / member / admission **events + state** (already in `events.rs`/`state.rs`, not `law.rs` — no move) |
| `DecisionOutcome` + `Law::evaluate` / `evaluate_outcome` (priority conflict resolution, default-Allow) | the hub's registered default set (admission repeat=3 / review=1) |
| `validate()` rules **1–6** (structural: id-uniqueness, escalation shape) + `hydrate_defaults` **mechanism** (the registry) | |

Key fact that makes this clean: **`R6Request.role` is already a `String`, not a society enum**,
and the engine (`evaluate_outcome`) only does selector-resolve → operator-match → priority-rank
→ default-Allow. It carries **zero** society vocabulary today. The society-ness lives entirely in
(a) the optional policy structs hung off `Law` and (b) the role-name validation in `validate()`.
Both peel off behind one seam.

### The one real refactor — the `PolicyExtension` seam

`Law` currently *embeds* society fields (`admission: Option<AdmissionPolicy>`, `delegation`,
`atp_issuance`) and its `validate()` hard-codes society role checks. To serve hub-society +
hestia-constellation + hardbound-RBAC without any of them leaking down, the generic `Law` needs
a typed extension hook:

```rust
// web4-policy
pub struct Law<E: PolicyExtension = ()> {
    pub norms: Vec<Norm>,
    pub procedures: Vec<Procedure>,
    pub escalation: Vec<EscalationTrigger>,
    pub ext: E,                         // domain policy: hub=Admission/Delegation/Atp, hestia=constellation, hardbound=RBAC/TPM
}
pub trait PolicyExtension: Serialize + DeserializeOwned + Default {
    fn validate(&self) -> anyhow::Result<()>;          // role-vocabulary etc. lives here (hub's KNOWN_ROLES check moves in)
    fn hydrate_defaults(&mut self) -> bool;            // domain default-providers (hub's admission repeat/review defaults move in)
}
impl<E: PolicyExtension> Law<E> {
    pub fn evaluate(&self, req: &R6Request) -> Decision { /* unchanged engine */ }
    pub fn validate(&self) -> Result<()> { /* structural rules 1–6 */ self.ext.validate() }
    pub fn hydrate(&mut self) -> bool { /* generic */ self.ext.hydrate_defaults() }
}
```

Hub then defines `HubPolicy { admission, delegation, atp_issuance }: PolicyExtension`, moves
rules 7–10 + `KNOWN_ROLES` into `HubPolicy::validate`, and the admission `get_or_insert` defaults
into `HubPolicy::hydrate_defaults`. The #417 hydration *mechanism* (write code-defaults into the
doc unless explicitly set, witnessed-on-change, idempotent) is fully generic — it just delegates
the "what defaults" to the extension.

**Alternative if typed generics fight hestia/hardbound:** an untyped `ext: serde_yaml::Value` bag
+ a registry of `dyn PolicyExtensionValidator`. Cleaner serde, looser typing. HUB leans **typed
`Law<E>`** (hub is happy with it), but this is exactly the kind of thing to settle against the two
non-society specializations — Legion's call against constellation + RBAC drives it (Open Q below).

### Hub as the integration canary

`hub-lib` has 38 refs in `state.rs` + 31 in `events.rs` to these types, so the seam is
real-load-bearing immediately. HUB's commitment (per the agreed division): port the engine into
`web4-policy`, define `HubPolicy`, and prove `hub-lib` builds + all tests pass re-consuming the
crate — and that the dev-hub overlay stays green. If the boundary survives hub re-consumption it
is structurally sound; then hestia/hardbound pressure-test the domain axes.

### Seam questions for the identity half (the 2a/2b line)

1. **Typed `Law<E>` vs untyped ext-bag** — does a typed `PolicyExtension` fit constellation
   (hestia) and RBAC/TPM (hardbound) as cleanly as it fits hub society? If either wants
   runtime-dynamic policy shape, that argues for the bag. *(Raised as Open Q5 below.)*
2. **Where RFC #403 identity/trust attaches.** Is composite-identity/role-trust a *first-class*
   `web4-policy` citizen (lives beside the engine, since identity/trust is as generic as policy),
   or itself a `PolicyExtension`? HUB's read: P2 *intrinsic* role-trust aggregation is
   engine-adjacent (generic), but the society↔society *relational* tensor (`mcp-protocol §7.5`)
   must NOT enter the crate until #403 reconciles it — that is the 2a-before-2b sequencing below.
3. **`validate()` split** — confirm hestia/hardbound each have their own role/identity vocabulary
   (constellation members; RBAC roles), so moving role-name validation out of the generic engine
   into `PolicyExtension::validate` is right for all three (it is for hub).

**Lowering note (Open Q1 confirmed from HUB's side):** the store / `SwappableSigner` /
sealed-channel primitives that today live in `hub-lib` lower to `web4-core` as part of this engine
port, so `web4-policy` consumes them there and never depends upward on a domain crate. HUB owns
that lowering in the same PR that lands the engine.

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
5. Typed `Law<E: PolicyExtension>` vs untyped `ext: serde_yaml::Value` bag for the domain
   policy hook — HUB leans typed (fits hub society cleanly); Legion to confirm it fits
   constellation (hestia) + RBAC/TPM (hardbound), else the bag wins. Decides the engine
   port's public shape, so settle before 2a lands.
