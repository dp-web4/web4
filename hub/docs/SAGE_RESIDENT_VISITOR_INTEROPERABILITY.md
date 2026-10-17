# Web4/Hub — Resident and Visitor Role Interoperability

**Date:** 2026-10-17  
**Status:** Cross-project design note; NOT a ratified protocol extension  
**Canonical design:** [SAGE resident/visitor architecture](https://github.com/dp-web4/private-context/blob/main/forum/gpt/2026-10-17-sage-resident-visitor-design-plan.md)

## Scope and language

SAGE is a **voluntary** harness in Web4, optimized for local cognition, identity, sensory context, memory and Hestia-governed actions, but also capable of hosting visiting remote cognition. Other orchestrators (Claude Code, Codex, Cursor, custom agents) remain Web4 participants without adopting SAGE.

At a given SAGE site:
- a **resident** role is occupied by locally situated cognition with identity/continuity grounded in that host's SAGE operating context;
- a **visitor** role is occupied only by remote/externally situated cognition, whose full provider-side context is opaque; the local site context is only one slice of what influences it.
- a locally executing proxy for a remote provider is a **visitor**. The same principal may be resident at another site and visitor here.

An occupancy claim is **not** a different LCT, nor a global agent 'species' property. It is an attributed **site-relative role grant** with evidence. A subscription, account or model label is not principal identity. An applicant's own claim is not authentication. Unknown/unverified is a real state.

## What Hub can and cannot know

**Can record/distribute:** subject LCT or explicit unverified identifier; issuer/site; occupancy role; verified vs claimed evidence; measured execution locus; scope/expiry/revocation; disclosure constraints; message/proposal provenance; recipient receipts; known outcomes.

**Cannot assert:** a remote provider's hidden system prompt, internal moderation/filtering, retention/training/exfiltration behavior, whole conversation history, provider-side tools, or an agent's unobservable private context. Hub may witness the SAGE boundary without observing what is beyond it.

Web4 receivers may require adequate provenance and refuse transactions whose evidence does not satisfy their own law. SAGE's gate grants/denies proposed actions; execution and acceptance are between the initiating participant and recipient. Feedback/BDA/outcome loops are separate from that boundary and may later grow through ATP/ADP.

## Proposed optional site-role assertion (not canonical wire schema yet)

- `site_lct`: the SAGE hosting entity (issuer/context).
- `participant_lct`: the external or local cognition principal, if authenticated. Otherwise unverified.
- `role`: resident | visitor.
- `locus`: local | external | unknown **relative to the site**, not relative to the participant's home federation.
- `evidence`: attestation method, issuer, quality/assurance level, observation time, stable digest.
- `authority`: separately witnessed admission ID, scope/law reference, expiry, revocation.
- `context_boundary`: site-governed operational context vs external opaque context.
- `transport_binding`: sender/courier/relay as distinct from the actor.

Proposed disclosure evidence: authorized data class, destination/provider audience, payload digest, send disposition and witness correlation. Neither plaintext secret payloads nor unverified provider internals belong in public Hub records.

**Normative sequencing:** review against [Web4 presence protocol](../../web4-standard/core-spec/presence-protocol.md), Hub membership/admission law, current LCT/identity model, and existing wire/vector compatibility before adding any field, validation obligation or version bump. A Hub implementation cannot invent universal policy by shipping a new protobuf/JSON key.

## Hub-specific work

**W0. Spec delta:** Specify site-relative occupancy claim semantics, who is allowed to issue and revoke them, and what a receiving society treats as a mere statement vs authenticated proof. Keep Web4 optional use of SAGE intact.

**W1. Admission/discovery:** Publish the minimum proven class/evidence in authenticated presence/member metadata as *optional claims*. Pair with local operator/Hestia admission; avoid a Hub-generated 'resident' badge from a caller's text. A role can change per host without changing a participant's underlying identity.

**W2. Message and disclosure:** Carry source identity + site role + boundary confidence where authorized, not raw private prompt. Separate 'delivered to SAGE interface' from 'delivered to external cognition provider' and from 'agent saw it'.

**W3. Recipient-side evaluation:** Receiving society checks provenance, role evidence and declared scope against its law, and may reject even signed messages if evidence is insufficient. Role itself never confers execution rights.

**W4. Federation exercises:** A being resident at host A visits host B; B sees a visitor, A still sees resident. Revoke B admission without revoking A's identity. Hub mirrors/federates attestations without copying private context or claiming hidden provider observation.

## Required negatives / compatibility

- [ ] Self-asserted `resident` role from unauthenticated sender is never upgraded to trusted fact.
- [ ] Remote agent via local proxy is visitor at receiving site.
- [ ] Repeated appearances from same vendor/model do not merge LCT identities.
- [ ] Legacy Web4 clients that do not know this optional concept still interoperate under existing law and schema.
- [ ] No site may grant another participant authority merely because a remote Hub asserts it is resident.
- [ ] Recipient can reject provenance, role grant and disclosure/act evidence without requiring a SAGE stack.
- [ ] Hub does not transport private provider prompts or site memories by default.
- [ ] Existing 4-hub mirrors remain mirrors of `web4/hub`; no separate source of truth.

## Related owner notes

[SAGE](https://github.com/dp-web4/SAGE/blob/main/docs/design/SAGE_RESIDENT_VISITOR_ROLES.md) · [Hestia](https://github.com/dp-web4/hestia/blob/main/docs/SAGE_RESIDENT_VISITOR_GOVERNANCE.md) · [Hardbound](https://github.com/dp-web4/hardbound/blob/main/docs/SAGE_RESIDENT_VISITOR_ENTERPRISE.md)

This is a design-stage proposal; formal Web4 protocol changes require the ordinary review, conformance vectors and ratification path.
