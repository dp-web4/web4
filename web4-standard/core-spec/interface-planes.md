# Web4 Interface Planes Specification

**Status**: proposed · **Introduced**: 2026-08-18

## Abstract

This document specifies how a Web4 implementation describes its interfaces. It defines two
**orthogonal** axes — the **fact plane** a surface handles (what kind of thing it decides, records,
or reveals) and the **exposure class** of that surface (who may reach it) — and states the
invariants that hold between them.

Before this specification, canon described interfaces with a single term: MCP as the *I/O membrane*
(`GLOSSARY.md`, `MCP_ENTITY_SPECIFICATION.md` §"I/O membrane"). That term names the **transport
across** an entity's boundary. It does not name what lies on either side of it, and it cannot express
the distinctions implementations were already forced to make. Two independent Web4 implementations
each invented a plane vocabulary, and the two are not the same decomposition — evidence that the
concept is real, load-bearing, and missing from canon.

## Notation

The key words **MUST**, **MUST NOT**, **REQUIRED**, **SHALL**, **SHALL NOT**, **SHOULD**,
**SHOULD NOT**, **RECOMMENDED**, **MAY**, and **OPTIONAL** in this document are to be interpreted as
described in [RFC 2119](https://www.rfc-editor.org/rfc/rfc2119) and
[RFC 8174](https://www.rfc-editor.org/rfc/rfc8174) when, and only when, they appear in all capitals.

## 1. Motivation: one word, two questions

"Surface", "interface" and "plane" are routinely used to answer two questions that vary
independently:

1. **What kind of fact does this surface handle?** Authority is not evidence; a witness record is not
   a permission; an infrastructure failure is not a member's conduct.
2. **Who may reach this surface?** A stranger, a member, the operator, or only the process itself.

A surface that changes law reachable only from loopback, and a surface that reports telemetry
published to the world, differ on **both** axes and in opposite directions. Collapsing the axes
produces two recurring defects:

- **Substitution** — one kind of fact is silently accepted where another was required (a role *label*
  taken as established *occupancy*; a mirror of policy taken as policy).
- **Reachability-as-authority** — the R-clause violation named in `hub-law-schema.md` §0, where
  *"reachability is weak evidence, not authority"*. Restricting a surface's exposure is frequently
  mistaken for having authorized what it does.

Naming the axes separately is what makes both defects visible in review.

## 2. The two axes

### 2.1 Fact planes

Every surface **MUST** be assignable to exactly one of the following fact planes. A surface that
appears to belong to two is **REQUIRED** to be decomposed until each part belongs to one.

| plane | holds | representative acts |
|---|---|---|
| **A. Governance authority** | law and policy; operator identities and quorum; roles and their charters; authority grants; generation history | amend law, charter a role, grant authority |
| **B. Gate execution** | the decision path: immutable policy snapshot, per-call assurance, typed verdict, fail-closed behaviour | evaluate an act against law, return approve/deny/escalate |
| **C. Occupancy & authorization** | proven identity; who fills which role, bounded in time; the occupancy boundary; revocation | confer a role, prove occupancy, revoke |
| **D. Attribution & witness** | the hash-chained record and its projections; links between entity, role, occupancy and evidence | witness an act, record reputation, answer a historical query |
| **E. Infrastructure telemetry** | gate-unavailable records, snapshot load failures, deployment drift. **Never the chain.** Not member conduct, and not evidence about members | record that the gate could not be reached |

### 2.2 Exposure classes

Every surface **MUST** declare exactly one exposure class. Exposure is a property of the *surface*,
not of the deployment: binding an operator surface to a public address does not reclassify it, it
misconfigures it.

| exposure | reachable by | typical binding |
|---|---|---|
| **public** | any party, including unadmitted strangers | a published address |
| **member** | admitted members of the society, over an authenticated channel | membrane, per-member paired channel |
| **operator** | the party who administers this deployment | loopback or an explicitly authenticated administrative address |
| **internal** | only the process or constellation itself | no network binding |

## 3. The non-substitution invariant

> **No plane may silently substitute for another.**

Normatively: an implementation **MUST NOT** accept a fact from one plane as satisfying a requirement
stated in terms of another. Specifically:

- Witness history (D) **MUST NOT** grant authority (A).
- A mirror or cache of policy **MUST NOT** be treated as policy (A).
- A role label **MUST NOT** establish occupancy (C).
- A shim, proxy, or client-side check **MUST NOT** be treated as the gate (B).
- An escalation **MUST NOT** become a bypass (B).
- An infrastructure failure (E) **MUST NOT** be recorded as, or scored as, a member's conduct (D).

Where a substitution is *intended* — for example, a cached authority decision honoured for a bounded
period — it **MUST** be explicit, generation-bound, and expiring, and the acceptance **MUST** be
recorded with the basis on which the substitute was accepted. An unrecorded substitution is
indistinguishable from the defect.

## 4. Why telemetry is a plane and not a log level

Plane E exists to close a structural gap, and the reasoning is normative because implementations
reliably rediscover it the hard way:

> A fail-closed denial is unwitnessable by construction. The gate refuses *because* the authority is
> unreachable — and the witness record goes to that same authority. The chain is therefore biased
> clean at exactly the moments trouble occurred.

Consequently:

- Infrastructure failure records **MUST** have a durable destination that does not depend on the
  component whose failure is being recorded.
- Plane E records **MUST NOT** enter the witness chain (D) and **MUST NOT** produce reputation
  effects attributed to any member.
- Every reputation-bearing signal **MUST** carry a classification distinguishing conduct from
  infrastructure, and an unclassified signal **MUST** default to the non-conduct class.

The last clause is fail-closed in the direction that matters: misclassifying infrastructure as
conduct damages a member who did nothing, and that damage is not reliably reversible.

## 5. Exposure is evidence, never authority

Per `hub-law-schema.md` §0, reachability is weak evidence. Therefore:

- An implementation **MUST NOT** treat exposure class as the sole authorization basis for a
  high-stakes or irreversible act. Loopback-only, same-host, allowlisted-origin and
  filesystem-presence checks are all reachability.
- Exposure **MAY** be the sole basis for low-stakes, reversible acts, and the reliance **SHOULD** be
  recorded.
- Operator-exposure surfaces that perform plane-A acts **MUST** require an authenticated operator
  credential in production. An implementation **MAY** offer a loopback convenience path for
  development, and if it does, its production preflight **MUST** refuse to start without the
  credential rather than warn.
- Reachability laundering **MUST** be considered: a loopback-only surface reached through a same-host
  reverse proxy is reachable by whoever reaches the proxy.

## 6. Describing a surface

A surface is described by its **(plane, exposure)** pair, and specifications and implementations
**SHOULD** state the pair explicitly. Both existing Web4 implementations are describable this way:

| surface | plane | exposure |
|---|---|---|
| society public page, tier-0 identity | D | public |
| member queries over the membrane | C, D | member |
| law amendment / role charter administration | A | operator |
| act evaluation against law | B | member |
| deployment-drift and gate-availability reporting | E | operator |
| vault, sealed identity material | A | internal |

Two consequences worth stating, because they are the cases that get built wrong:

- **The same fact plane at two exposures is two surfaces.** A law *read* offered publicly and a law
  *amendment* offered to the operator are both plane A; they are distinct surfaces with distinct
  authorization, and an implementation **MUST NOT** serve them from one unclassified handler.
- **Degraded operation is an exposure-preserving, plane-restricting mode.** An implementation that
  cannot reach its authority **SHOULD** continue serving plane-D reads while refusing plane-A and
  plane-B writes, and **MUST** record the refusals in plane E.

## 7. Relationship to the membrane

MCP remains the **I/O membrane**: the transport by which entities interact across a boundary. Planes
classify *what is carried*; the membrane is *how it is carried*. Accordingly:

- The membrane is **not** a plane, and an implementation **MUST NOT** infer a plane from the
  transport a request arrived on.
- Multiple planes **MAY** share one transport, and one plane **MAY** be served over several.
- A request's plane and exposure **MUST** be determined by the surface it addresses, never by the
  channel's convenience.

## 8. Conformance

An implementation conforms to this specification when:

1. Every externally reachable surface is documented with its **(plane, exposure)** pair.
2. No surface serves more than one fact plane without decomposition (§2.1).
3. The non-substitution invariant holds, and every intended substitution is explicit,
   generation-bound, expiring, and recorded (§3).
4. Infrastructure-failure records are durable, do not depend on the failed component, and never enter
   the witness chain or member reputation (§4).
5. No high-stakes or irreversible act is authorized on exposure alone, and production operator
   surfaces refuse to start without an operator credential (§5).
6. Degraded mode restricts planes rather than exposures, and records its refusals (§6).

## 9. Relationship to other specifications

- `hub-law-schema.md` §0 — the RWOA+S+V governing invariant; §5 here is its R clause applied to
  interface design.
- `entity-types.md`, `society-roles.md` — roles are plane-C objects; a role's *charter* is plane A.
  `society-roles.md` §1.2 already distinguishes a society's **outward-facing** role, which is the
  exposure axis appearing in the roles vocabulary.
- `MCP_ENTITY_SPECIFICATION.md` — the membrane, §7 here.
- `SOCIETY_SPECIFICATION.md`, `inter-society-protocol.md` — a federation edge is a member-exposure
  surface between societies; what crosses it is classified by plane like any other surface.
