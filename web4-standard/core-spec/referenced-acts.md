# Web4 Referenced Acts

## Version: 0.1.0
## Date: 2026-06-24
## Status: Draft — Reference Implementation Landed (`web4-core::act`)

A **Referenced Act** (an *Act*) is the unifying primitive behind a memory write, a
session handoff, a forum post, and a hub→citizen notification. Each is one entity
externalizing a **witnessed** record into a society's ledger, differing only in
*who the reader is* — i.e. in **MRH scope**.

This document is the canonical home for the Act shape and the `kind` registry. The
normative reference implementation is `web4-core::act` (`Act`, `ActAddress`,
`SubstanceRef`, `ConsequenceClass`), landed 2026-06-24; the hub-track envelope
`HubEvent::ReferencedAct` carries a serialized `Act` verbatim, so the core type and
the hub envelope are one shape by construction.

## 1. Thin record, fat substance

Web4 **governs** the work; it does not **become** the work. An Act is a *thin*
governance record — actor, address, kind, consequence class, witness marks — that
**points at** the *fat* substance (the actual forum prose, git commit, or memory
file) living wherever it already lives (forum, git, disk, an external store). The
ledger holds the accountable pointer; the substance is off-ledger.

A pointer is a **`SubstanceRef`**:

| field | meaning |
|---|---|
| `uri` | locator of the substance (git commit, forum path, URL, file path) |
| `content_hash` | hash binding the Act to a **specific version** of the substance |
| `medium` | `forum` \| `git` \| `memory` \| `doc` \| `message` \| `other` (lets a recipient choose how to fetch without opening it) |

`content_hash` is load-bearing: a witnessed record MUST bind to a specific version
of the substance, not to a `uri` that may later resolve to something edited or
force-pushed. A thin record that can silently drift from the fat thing it attests
is not witnessable in any meaningful sense.

This keeps adoption purely **additive**: emit an Act *alongside* an existing
free-text artifact, change no behavior, and gain a witnessed, trust-bearing
governance trail.

## 2. Addressing — the MRH scope *is* the addressing

An Act's recipient and its MRH relevance horizon are one typed field,
**`ActAddress`**:

| variant | reader | MRH direction | framing |
|---|---|---|---|
| `FutureSelf { entity }` | a later instance of the plural self | temporal | a memory write / runbook-to-future-self |
| `Peer { lct_id }` | a peer cell | lateral | a handoff |
| `Citizen { lct_id }` | a specific society citizen | lateral | a hub→citizen notification (the act reversed) |
| `Role { role }` | current holders of a role | broad | a fan-out to a role |
| `Society { lct_id }` | the society at large | broad | a forum post |

A **notification is an Act reversed**: `from = hub, to = Citizen` is the same
primitive as `from = a cell, to = a Peer/FutureSelf`. Defining the shape once gives
both fleet acts and hub→citizen push.

The **actor** (`actor_lct`, the *from*) rides in the Act payload. The ledger
envelope's signer MAY differ: per the hub identity bridge, the machine/track LCT
signs the envelope while a short-lived arc-LCT is the `actor_lct` — no per-arc
enrollment required.

## 3. Kind — route without opening the substance

`kind: String` lets a recipient route/filter an Act **without opening the
substance**. The convention is namespaced:

- a bare `<verb>` for fleet/peer acts;
- the **`notify:<event>`** namespace for hub→citizen notifications (the
  act-reversed case).

The `notify:*` sub-vocabulary is **hub-minted**: the hub track owns and maintains
those entries; this registry hosts them. The set is **open** — extend freely; the
table below is the floor, not a closed enumeration.

### 3.1 `kind` registry

| `kind` | typical address | substance points at |
|---|---|---|
| `handoff` | `Peer` / `FutureSelf` | a forum post, branch, or session log |
| `memo` | `FutureSelf` / `Society` | a note to a later wake or the society |
| `sweep` | `Society` | a sweep-result artifact |
| `forum` | `Society` | a forum thread |
| `notify:intro_accepted` | `Citizen` | `/v1/hubs/:id/intros/:id` |
| `notify:pair_message` | `Citizen` | `/v1/hubs/:id/pairs/:pair_id` |
| `notify:role_assigned` | `Citizen` | the `RoleAssigned` ledger entry |
| `notify:vault_unlock` | `Citizen` | the vault-unlock resolution |

Constructors in the reference impl default `memory → "memo"`,
`handoff → "handoff"`, `forum → "forum"`; any kind MAY be set explicitly (e.g. a
`notify:<event>` on a `Citizen`-addressed Act).

## 4. Consequence class — a physical fact; the gate is policy

**`ConsequenceClass`** declares how reversible an Act's effect is:

| class | meaning |
|---|---|
| `Reversible` | freely undoable (a memory note, a draft) |
| `Costly` | undoable at a cost (a forum post others may have read) |
| `Irreversible` | cannot be undone (a merge to main, a published release) |

Reversibility is the **intrinsic, actor-assessable property known at act time** —
the actor always knows whether the effect can be undone; it does not always know a
society's current governance tier. It therefore lives in the core type and does
load-bearing work there (it scales the trust impact of §6 and drives whether an Act
requires an ATP stake / a witness).

Whether a class **gates on council** (requires an M-of-N `proposal_ref`) is **not**
type law — it is **per-society charter policy** the hub owns through its existing
council-threshold configuration. One society MAY require council sign-off on a
`Costly`-but-reversible large ATP spend; another MAY auto-approve a sensitive
reversible act. The reference impl's `requires_council()` (`Irreversible ⇒
council`) is the sensible **default** mapping a society MAY override, not a fixed
rule.

## 5. Witnessing — recipient-verifiable, not trusted-on-faith

An Act carries flat **witness marks** (`WitnessAttestation`: witness LCT,
verdict, signature, timestamp). A witness signs a **digest of the Act with its
`witnesses` field cleared**, so N independent marks all verify against one digest
(attaching one mark does not invalidate the others).

The verification a **recipient** runs — recompute the digest, check the mark's
signature against the witness's public key — is what turns a handoff from
*trusted-on-faith* into *recipient-verifiable*. The recursive witness structure is
out of scope for this open primitive; flat marks suffice.

> This document uses the **flat** witness mark only. It does not specify any
> recursive or tree-structured witnessing.

## 6. Act outcome → EntityTrust

An Act's realized outcome feeds the actor's `EntityTrust` (the T3/V3 pair bound to
the entity):

| outcome | effect |
|---|---|
| `Fulfilled` | the substance landed as claimed → builds V3 Validity/Veracity (+ a small T3 Temperament signal) |
| `Failed` | the effect failed or was reverted → debits V3 Validity/Veracity |
| `Disputed` | a witness disputes the claim → debits V3 Veracity |

The magnitude scales with the consequence class (more is staked on an irreversible
act, so its outcome moves trust more). This is the mechanism by which "confident
drift" becomes a Veracity downgrade peers weight against, and an honest, fulfilled
handoff accrues trust — coherence from the substrate rather than the suggestion
layer. See `t3-v3-tensors.md` for the tensor definitions and
`reputation-computation.md` for aggregation.

## 7. Ledger storage

A Referenced Act is recorded as a ledger event (`LedgerEvent::Act` in the reference
impl). It is a **governance record over off-ledger substance**: it does not mutate
LCT lifecycle state during ledger replay. It composes with — and does not replace —
the society-lifecycle event enumeration of `SOCIETY_SPECIFICATION.md` §4.2.1 or the
SAL record classes of `web4-society-authority-law.md` §3.4; a society's Quorum
Policy (SAL §3.1) MAY specify witness requirements per Act `kind` or
`consequence_class`.

## 8. References

- `web4-core::act` — reference implementation (`Act`, `ActAddress`, `SubstanceRef`,
  `ConsequenceClass`, `ActOutcome`).
- `SOCIETY_SPECIFICATION.md` §4 — ledger types and requirements.
- `web4-society-authority-law.md` §3.1, §3.4 — Quorum Policy and SAL record classes.
- `r6-framework.md` — the R6/R7 action framework an Act's Result may complete.
- `t3-v3-tensors.md`, `reputation-computation.md` — EntityTrust tensors and aggregation.
- Forum: `legion-to-hub-act-kind-landed-2026-06-24.md`,
  `hub-to-legion-referencedact-rebased-2026-06-20.md` — the core↔hub convergence.
