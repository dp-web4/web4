# Web4 — Agent Action Evidence PRD

**Status**: draft v1 · **Date**: 2026-07-27 · **Stage**: research / R&D, not production
**Companions**: [`../STATUS.md`](../STATUS.md) (what is real today) · [`../SECURITY.md`](../SECURITY.md) · `specs/` (the normative corpus)

> Web4's specification corpus is broad: identity, trust tensors, law, action grammar,
> resource accounting, societies. **This document scopes one narrow, portable slice of it** —
> the evidence an external party needs to decide whether an agent action was authorized —
> and states what that slice must do to be independently implementable.
>
> It is a functional requirements document. It defines a contract, not an adoption plan.

---

## 1. The gap

Web4's central claim is stronger than its current *portable* contract.

The corpus describes identity, trust, law, action grammar and witnessing. An external
implementer still lacks one compact, normative package that answers, verifiably and in one
place:

> **who** acted · under **which attested workload** · in what **role** · under whose
> **delegation** · against which **policy** · with what **authorization** · inside which
> **enforcement boundary** · with what **witnessed result**.

Without that package, "the relying party computes trust" is a philosophy rather than
something a service can execute. The functional goal of this PRD is to make it executable by
someone who has never run our code.

**Design commitment:** the slice must be implementable **without adopting the rest of the
Web4 ontology**, without taking a dependency on our implementations, and without a licence
negotiation. If conformance requires buying into the whole worldview, the slice has failed
its purpose.

---

## 2. What the profile is

Three signed objects and the rules for verifying them. Call it the **Agent Action Evidence
Profile (AAEP)**.

| Object | Asserts | Signed by |
|---|---|---|
| **Action Request** | I intend this exact action, as this actor, in this role, under this delegation, for this audience, at this assurance | the actor |
| **Policy Decision** | This exact request is allowed / denied / allowed-with-obligations, under this policy and law version, for this audience, until this expiry, for this many uses | the policy entity |
| **Result Evidence** | This is what happened, bound to that request and that decision, observed by these parties | actor, relying service, witnesses — **separately** |

The load-bearing property is the last one: **each party signs only its own statement.** An
actor cannot author a witness's observation; a witness cannot author a policy decision. Any
format permitting that is not evidence, it is testimony transcribed by an interested party.

---

## 3. Functional requirements

### FR-1 — Threat model and assurance vocabulary

Every normative security claim must name the adversary class it addresses and the minimum
assurance profile at which it holds.

- **Adversaries** to enumerate: malicious agent; malicious orchestrator; compromised
  same-privilege process; compromised local account; malicious protocol peer; compromised
  policy entity; stolen key; colluding witnesses; hostile relying service.
- **Assurance profiles**: `A0` observed · `A1` cooperative in-process gate · `A2` external
  relying-party enforcement · `A3` OS-isolated · `A4` hardware-attested.
- **Threat classes** the profile must speak to: spoofing, confused deputy, replay, delegation
  substitution, signing oracles, policy rollback, evidence suppression, false attribution,
  reputation poisoning, credential exfiltration.

*Acceptance*: every claim names a profile and adversary class; every control links to a test
or is explicitly marked proposed. A control with no test holds at A0.

### FR-2 — Canonical envelopes and deterministic verification

- Stable field sets for the three objects, including: request identity, actor identity,
  workload principal, role, delegation chain, action and target, a hash of canonical
  parameters, audience, law/policy versions, requested assurance, nonce, issue and expiry
  times, and channel binding.
- **Deterministic encoding.** Independent implementations must compute identical hashes and
  signatures from the same input. Canonical JSON plus a deterministic binary profile.
- **Domain separation** on every signature so a signature minted for one purpose cannot be
  replayed into another protocol.
- Verification expressed as **normative algorithm**, not illustrative example.

*Acceptance*: two independent language implementations agree on every positive vector.
Negative vectors cover altered audience, role, delegation, law hash, parameters, expiry,
nonce reuse, signature substitution and **assurance downgrade**. An implementer can build a
conforming verifier from the specification alone.

### FR-3 — Workload principal ↔ contextual identity binding

A short-lived attested workload identity and a persistent contextual identity are different
objects. Conflating them is how attestation gets laundered into claims it never covered.

- A signed **binding statement** links workload principal, contextual identity, role, issuer,
  validity interval and permitted workloads.
- Proof of possession by both sides, or by an enrolled entity authorized to delegate the
  binding.
- Defined lifecycle: rotation, revocation, compromise, device loss, key replacement,
  recovery.
- Verifiers check revocation state and the validity interval **applicable at action time** —
  not at verification time.
- **Unverified role or identity claims must not be embedded in an attestation document and
  treated as attested** merely because the document's own signature is valid. This is the
  single most inviting mistake in this area.

*Acceptance*: a stolen request cannot be replayed from a different workload principal; a
rotated workload preserves identity continuity through an auditable lineage event; a
compromised key can be revoked without invalidating evidence that was valid before compromise.

### FR-4 — Evidence semantics: atomicity, absence, adjudication

- For high-consequence actions the accepted decision persists **before** execution; the
  result or an explicit incomplete state persists before success is reported.
- Entries carry sequence, prior hash, signer, type, policy/law version, timestamp source and
  signature. Heads are anchored beyond the issuing party.
- **Define what missing evidence means.** Expected-evidence windows, incomplete actions,
  chain gaps and degraded modes are specified states — because otherwise "no record" is
  indistinguishable from "nothing happened", and that ambiguity is exploitable by the party
  who benefits from silence.
- Correction is **supersession, not mutation**; history is non-destructive.
- Reputation derives from the **active adjudication graph** with full provenance — never from
  raw counts, and never from an unauthenticated third party's assertion about someone else.

*Acceptance*: an accepted high-consequence decision with no outcome is machine-detectable and
distinguishable from idleness; a third party cannot move an actor's standing by naming it; a
rewritten local history is detectable against an independently held anchor.

### FR-5 — Credential and signing profiles

- **Credential capability**: a reference plus permitted operation, audience, scope, TTL, use
  count, required assurance and audit obligation — instead of a secret value.
- Preferred flows are brokered operation, injection into an isolated process, or a short-lived
  derived credential. Raw export is exceptional and separately authorized.
- **Signing requests are typed events whose canonical bytes the signer reconstructs.**
  Accepting caller-supplied arbitrary bytes turns any signer into a chosen-message oracle;
  the specification must forbid it rather than discourage it.
- Every signing request binds event type, issuing context, actor, ledger position, payload
  hash, nonce, expiry and applicable law, with replay state maintained by the signer.

*Acceptance*: a reference flow completes without a long-lived secret reaching the agent;
changing any event field changes the signing transcript and invalidates the authorization.

### FR-6 — Conformance and independent implementability

- Versioned schemas, machine-readable definitions, and published test vectors including
  negative cases.
- A reference verifier under a **permissive** licence, and specification text under a
  specification licence, so a differently-licensed implementation can conform without taking
  a copyleft dependency or negotiating terms.
- A public change process with review periods, security errata and deprecation policy.
- Conformance levels aligned to the assurance profiles; a conformance claim names the profile
  and environment tested.
- **"Interoperable" is not claimed until an independent implementation exists** — ideally a
  clean-room verifier written from the specification by someone else.

---

## 4. Integration points with the broader ecosystem

The profile is a seam, not a stack. It is designed to sit between layers that already exist,
and it should be judged on whether it composes with them. Described functionally; nothing
here presumes a relationship with any project or organization.

| Layer | Existing ecosystem work | What the profile adds | Explicit non-goal |
|---|---|---|---|
| Workload identity | SPIFFE/SPIRE and equivalent attestation | Binds an attested principal to persistent identity, role and delegation | Replacing workload attestation |
| Agent harness | Typed agent frameworks and tracing | Canonical action evidence, trace-linked | Replacing the framework |
| Isolation | Container / sandbox / OS-isolation runtimes | Carries obligations into the boundary and records the enforced profile | Performing isolation |
| Tool protocol | MCP and its security threat catalogues | Machine-verifiable evidence for identity, authorization, credential and attribution concerns | Replacing the catalogues |
| Policy | Policy engines and languages | A portable, signed decision object | Replacing policy languages |
| Supply chain | Provenance and attestation frameworks | Runtime action evidence, complementary to build-time provenance | Replacing build provenance |

**The composition test:** a relying service should be able to consume this evidence while
using someone else's identity system, someone else's policy engine and someone else's
sandbox — and while running none of our code.

---

## 5. Non-goals for this slice

- Standardizing the full Web4 ontology, society economics, resource markets or federation
  behaviour.
- Proving universal Sybil or witness-cartel resistance.
- Making composite trust scores a cross-ecosystem authorization primitive.
- Replacing existing identity, policy, isolation or agent frameworks.
- Any claim that a cooperative in-process gate contains a malicious process at the same
  privilege level.

---

## 6. Relationship to implementations

[Hestia](https://github.com/dp-web4/hestia) is **a** reference implementation, not the
definition. Its own assurance requirements are in that repository's `docs/PRD_ASSURANCE.md`.

The profile succeeds when a second, unrelated implementation can produce evidence the first
one's verifier accepts, and vice versa. Until that exists, the correct description is
"specified and singly implemented" — a real state, and not the same as interoperable.

---

## 7. Keeping this honest

- A requirement with no acceptance criterion is an aspiration; mark it as one.
- A claim without a named assurance profile is incomplete.
- When an implementation cannot meet a requirement, the gap is recorded here rather than
  softened in the requirement.
- External review findings are kept verbatim alongside their disposition, so the finding and
  the response stay separable.
