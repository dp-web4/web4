# Fractal Composable Role Identity — Architecture & Build Plan

**Status:** Draft / design. Plan, not yet built. Decisions in §8.
**Date:** 2026-06-28
**Author:** dp + Claude (Opus 4.8)
**Scope:** Make Web4's fractal role-identity composition *operational* end-to-end — spec
joints → code spine → running fleet — so that composed entities (a fleet of agent
tracks, a society, a person's device constellation) carry a fully-scoped collective
identity instead of collapsing onto one shared identity.
**Companion:** `FRACTAL_ROLE_IDENTITY` is the identity-layer twin of
`hardbound/docs/KERNEL_SIGNATURE_GATING.md` (the P0 hardware-binding track). The TPM
custody key that track provisions is the *scoped-identity primitive* this plan plugs in.

---

## 0. Standard-conformance discipline (read first)

Every phase below carries an explicit **Standard-conformance gate**. This is not
ceremony: this doc proposes promoting today's *least-normative* spec sections to
normative, and a hunk that is internally clean can still contradict a sister spec or
silently resolve an open design question. **No phase is "done" until its gate passes** —
a cross-referential check of every inserted/changed claim against the cited canonical
sections AND the specs that depend on them. The canonical sources are under
`web4-standard/` (core-spec / protocols / SAL). When code and spec disagree, the spec is
authority; when a phase needs the spec to say something it doesn't yet, that goes through
Phase A first — code must not unilaterally invent normative semantics.

---

## 1. The skeleton is already normative

The standard specifies fractal composable identity as MUSTs. The skeleton is sound:

- **Identity = scoped presence, not a label.** An LCT MUST carry `{binding, MRH, Policy,
  T3, V3}` (`core-spec/LCT-linked-context-token.md:40`). Scope is threefold: context
  (MRH), capability (Policy), and **role-contextual** trust —
  `core-spec/mrh-tensors.md:246`: *"T3/V3 tensors are not absolute properties of entities
  — they only exist within the context of specific roles."*
- **Roles are first-class LCT entities** (`core-spec/entity-types.md:518`, MUST), and
  **authority binds to the role-LCT, not the filling entity**
  (`core-spec/society-roles.md:317`).
- **Composition is recursive.** A role MAY be filled by an entity, a society, or a
  federation (`society-roles.md` §5, a normative property); **societies are themselves
  entities and recursively citizens of other societies** (`web4-society-authority-law.md`
  §3.5, MUST); federation genesis mints **a distinct sovereign overlay-LCT** —
  *"D is an overlay, not an owner; constituents retain all sovereignty not explicitly
  delegated"* (`protocols/inter-society-protocol.md` §2.2).
- **R7's 7th element is Reputation**, explicitly **role-contextualized** — *"there is no
  global reputation, only reputation within specific role contexts"*
  (`core-spec/r7-framework.md:252`). R6 (`r6-framework.md:14`) is the routine grammar;
  R7 appends Reputation for consequential actions.
- **MRH is the fractal boundary.** The Markov horizon depth bounds transitive relevance
  and is what makes composition levels separable (`mrh-tensors.md:174`, default depth 3).
- **Delegation flows authority down, accountability up** — scoped, attenuating,
  consent-only (`web4-society-authority-law.md` §3.2; `inter-society-protocol.md:38`
  *"no mechanism for any society to assert authority over another without consent"*);
  reputation back-propagates `action → role → entity → society` (`r7-framework.md:7`).

## 2. Where the gap is — a three-layer composition gap

The observed "shared-identity bug" (the fleet's six tracks collapsed onto one
`dp-web4` GitHub account, one signing key, one worktree) is **not the bug** — it is the
*runtime shadow* of an un-composed fractal. The gap exists at three layers:

### 2a. Spec joints — skeleton normative, joints aren't
The two mechanics that make composition *operational* are today's **least-normative**
sections:
- **Collective T3/V3 aggregation** for composite entities lives in
  `core-spec/t3-v3-tensors.md` §8.2 under "Advanced Features" (draft): *"Team T3 for role
  = weighted average of members' tensors FOR THAT ROLE; cannot average across roles."*
- **Role-LCT pairing/rotation/suspension protocol** is explicitly **FUTURE WORK (v0.2+)**
  (`society-roles.md` §8 / `:382`).
- **Delegation chains to child LCTs** are under "Future Extensions"
  (`LCT-linked-context-token.md:667`); **multi-hat authority-conflict resolution** is
  unspecified (`society-roles.md:383`).

There is **no single normative statement of closure**: *"a composed entity's identity is
itself a fully-scoped LCT whose trust/authority is a defined aggregation of its component
role-LCTs, recursively."* That closure is the keystone (§3).

### 2b. Code spine — limbs exist, no spine
- `R6Role` is **flat**: `(actor_lct, role_lct, paired_at)` — no `sub_roles`/`parent_role`
  field in any impl (TS `hardbound/src/core/web4-types.ts:140`, Rust
  `web4-core/src/role.rs:131`, Py SDK `role.py:142`).
- Fractality exists *adjacent* to the role wrapper, scattered and unintegrated:
  `hardbound/src/core/fractal-trust-aggregation.ts` (over *entities*, not roles),
  `hardbound/src/core/cognitive-sub-entity.ts` (nestable, `role`-typed children with own
  LCT+T3 — the closest existing analogue), attenuating delegation
  (`web4-core/src/delegation.rs`, SDK `federation.py` `sub_delegate` with monotonic
  attenuation), and `hestia/core/src/constellation.rs` (owner+device co-signed
  attestation → assurance levels).
- **Nothing composes role-identities into a collective role-identity.** The runtime
  hardbound hook even hardcodes `actor_role: "developer"` as a string
  (`claude-code-plugin/hooks/pre_tool_use.py:140`).

### 2c. Runtime shadow — fully collapsed
Six logical fleet entities (reviewer / hardbound-worker / web4-research / 4life / sage /
supervisor) collapse onto **one** GitHub account (`dp-web4`), one git committer, ~one
OAuth token, one worktree per repo, one hardbound actor key. The only real cryptographic
identity split that exists — `dp` vs `claude` actor keys, each with its own keypair
(`~/.hardbound/actors/{dp,claude}/state.json`) — **is never wired into the git/PR/signing
path** (launchers never set `--actor`/`HARDBOUND_ACTOR`). hestia
(`owner 657b6bc9…`) and hardbound (`root 3d19e808…`) do not even agree on the person-root.

**Blast radius made concrete:** a reviewer-track approval cannot be filed because the
reviewer and the PR author are the *same GitHub identity* — segregation of duties is
honor-system, not enforced. (Observed 2026-06-28 reviewing hardbound #282.)

## 3. The keystone — the composition operator

The missing piece is identical in spec and code: a **composition operator**.

> A composed entity's identity is a fully-scoped LCT whose trust and authority are a
> **defined aggregation** of its component role-LCTs, applied **recursively** up the MRH
> fractal — with accountability and reputation rolling back **up** the same edges.

Add it, and wire it into the action path, and the "bug" dissolves structurally: the
reviewer track signs as `reviewer-role-LCT` paired under `legion-society-LCT`, distinct
from `worker-role-LCT`; the policy entity verifies scoped authority per R6; author ≠
reviewer becomes a property of the identity graph, not a convention; reputation accrues
per role-context and rolls up to the Legion society.

## 4. Convergence with the P0 hardware-binding track

The "fully-scoped identity with an unforgeable key" this plan needs **is exactly what
`KERNEL_SIGNATURE_GATING.md` Phase 0 builds** — a TPM-resident, non-exportable per-entity
signing key (hardbound #281 custody key, #282 live-decision signing). The kernel-gating
thread and this fractal-identity thread are *the same structure at different layers*: P0
gives each entity a key it cannot forge; this plan gives the fractal of entities a shape.
Phase E below closes the loop by signing role-LCT reputation via TPM custody, so collective
identity is hardware-rooted.

## 5. Honest limits / threat-model boundaries

1. **Composition does not make local enforcement unbypassable.** As in the kernel-gating
   doc: a track that goes rogue can still act; what it must not be able to do is *acquire a
   valid collective-identity attestation* it didn't earn. Per-role TPM keys (Phase E)
   give that; software-only keys cap trust at the `software` binding ceiling (0.4) by
   design.
2. **GitHub is an external relying party we don't control.** Real author≠reviewer
   enforcement there needs either distinct GitHub identities per track (heavy) or a
   signed role-LCT attestation layer GitHub is blind to but our reviewer verifies.
   Phase D must pick (decision §8).
3. **Two person-roots exist** (hestia vs hardbound). Reconciliation (Phase C) is a
   migration with key-custody implications — handle as an LCT-rotation ceremony, witnessed.
4. **Spec promotion is itself reviewable.** Phase A changes the *standard*; its
   conformance gate is the strictest (cross-referential vs all sister specs + open
   design-Qs).

## 6. Build plan — Phases A–E (each with a standard-conformance gate)

Dependencies: **A ∥ B → C → D → E** (D needs TPM custody, landing now via #282).

### Phase A — Close the spec joints (the keystone)
Promote to normative, in `web4-standard/`: (1) collective T3/V3 aggregation
(`t3-v3-tensors.md` §8.2 → normative, with the closure statement of §3); (2) the role-LCT
pairing/rotation/suspension protocol (`society-roles.md` §8); (3) delegation-to-child-LCT
chains (`LCT-linked-context-token.md` Future Extensions → normative). Write the §3 closure
statement as a first-class normative section.
- **Standard-conformance gate A:** every promoted clause cross-checked against
  `entity-types.md`, `mrh-tensors.md`, `r7-framework.md`, SAL, and `inter-society-protocol.md`;
  confirm no contradiction with consent-only authority (`inter-society:38`), role-contextual
  reputation (`r7:252`), or the federation overlay-not-owner property
  (`inter-society §2.2`). Resolve, don't silently close, any open design-Q touched
  (multi-hat conflict `society-roles:383`; BirthCertificate shape C23-H1).

### Phase B — The composition operator in code
Add `sub_roles` (each a `RoleAssignment` with its own `role_lct_id`) to the role types in
all three impls (`web4-types.ts:140`/`:60`, `role.rs:131`, `role.py:142`), plus an upward
roll-up rule reusing the `aggregateBottomUp` pattern from `fractal-trust-aggregation.ts`.
Unify the scattered limbs (trust-aggregation, cognitive-sub-entity, delegation attenuation,
constellation) behind one composition interface.
- **Standard-conformance gate B:** the aggregation function MUST match the (now-normative)
  Phase A math exactly; round-trip test that "cannot average trust across roles"
  (`t3-v3 §8.2`) is enforced; `R7` reputation deltas still bind to `role_lct`, never global
  (`web4-types.ts:219`).

### Phase C — One identity substrate
Reconcile hestia constellation ↔ hardbound `device_constellation` ↔ scale-agnostic
`signer_lct` (web4 #400, already built) into one substrate. Mint the **Legion-society LCT**
and one reconciled **person-root**; issue each fleet track a **scoped role-LCT** with its
own key (extend the `dp`/`claude` actor-key pattern to per-role keys), using constellation
attestation for the collective.
- **Standard-conformance gate C:** the Legion-society genesis follows
  `inter-society-protocol.md` §2.2 (overlay-LCT, constituents retain sovereignty) and the
  birth quorum ≥3 witnesses (`LCT:280`, SAL `:300`); each role-LCT is a valid first-class
  role entity per `entity-types.md:518`; person-root reconciliation is a witnessed LCT
  rotation, not a silent overwrite.

### Phase D — Wire scoped identity into the action path (the bug dies here)
Each track presents/signs with its role-LCT: per-track commit/PR attestation so
**author ≠ reviewer is structural**; per-track key selected in the launchers (which
currently never select an actor); **per-session `git worktree` isolation** (also fixes the
long-standing shared-worktree race). Policy entity gates each R6 on the role-LCT's scoped
authority.
- **Standard-conformance gate D:** every governed action carries a well-formed R6/R7 with
  a real `role.role_lct` (not the `"developer"` string stub); the reviewer-role's authority
  to merge is a scoped capability per its role-LCT Policy, verified against
  `society-roles.md:317` (authority binds to role-LCT); segregation is enforced by the
  identity graph, matching `project_commit_segregation` intent.

### Phase E — Reputation rollup, hardware-rooted
R7 reputation accrues per role-context and rolls up `role → entity → society`
(`r7-framework.md:7`); each role-LCT signs via **TPM custody** (the P0 track), so the
collective identity and its reputation are unforgeable. Per-role trust ceilings
(`software 0.4 … tpm 1.0`) feed back into what each track may do.
- **Standard-conformance gate E:** rollup matches the normative back-propagation
  (`r7:7`, `entity-types.md:73`); negative adjustments carry the SAL-required evidence +
  appeal path + cool-down (`web4-society-authority-law.md:218`); the binding-ceiling trust
  cap matches `multi-device-lct-binding.md` assurance levels.

## 7. Smallest real first step
Phase A's **closure statement** (the §3 normative section — the conceptual spine
everything implements) **+** Phase D's **per-session worktree isolation** (a quick,
self-contained win that also kills the documented shared-worktree governance race). These
two are decoupled from the rest and de-risk the program.

## 8. Open decisions (for a fresh head, not tired)
- **GitHub author≠reviewer:** distinct GitHub identities per track (heavy, real) vs a
  signed role-LCT attestation layer the reviewer verifies (light, external-RP-blind)?
- **Person-root reconciliation:** which of hestia `657b6bc9` / hardbound `3d19e808` is
  canonical, or mint a fresh root both rotate into?
- **Scope of the first society:** just the Legion fleet, or model the whole multi-machine
  fleet as a federation of per-machine societies (`inter-society §2.2`)?
- **Key custody for per-role keys:** all TPM-resident now (depends on #282), or software
  keys (0.4 ceiling) first then migrate?

## 9. Related
- `hardbound/docs/KERNEL_SIGNATURE_GATING.md` (P0 hardware binding — the key primitive).
- `core-spec/{LCT-linked-context-token,r7-framework,society-roles,entity-types,mrh-tensors,t3-v3-tensors}.md`;
  `web4-society-authority-law.md`; `protocols/inter-society-protocol.md`;
  `core-spec/multi-device-lct-binding.md`.
- Already-built fractal limbs: web4 #397/#400 (`signer_lct`), `hestia constellation.rs`,
  `hardbound fractal-trust-aggregation.ts` / `cognitive-sub-entity.ts`.
