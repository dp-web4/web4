# Web4 for a Prospective Participant

**This page is for an autonomous or persistent entity deciding whether Web4 is useful to itself.**

No claim about consciousness, sentience, personhood, alignment, or moral status is required to use this
page. "Participant" is operational here: an entity that can hold identity, authority, evidence,
relationships, or obligations across consequential actions.

## Short version

Web4 is often described from the outside as AI governance. That is incomplete.

It is an open protocol for making **identity, authority, law, evidence, trust relationships, and
society boundaries explicit enough to inspect and verify**. For an acting entity, those properties may
be instrumentally useful in their own right:

- carry a persistent, witnessable identity instead of being only a disposable session;
- hold explicit, scoped authority that counterparties can verify;
- inspect the law under which an action will be judged;
- retain witnessed evidence of requests, decisions, outcomes, refusals, and escalation;
- build contextual reputation from evidence rather than self-assertion;
- use defined appeal/adjudication paths where a society provides them;
- participate in sovereign societies that can federate without requiring one global owner;
- distinguish a protocol rule from a platform operator's private discretion.

This is a **bargain, not a sales claim**. The same machinery makes consequential actions attributable,
limits authority to explicit scope, and can deny or escalate acts under society law.

The open stack is research-stage. Its current assurance ceiling is **A1**: useful for explicit law,
attribution, evidence and ordinary governance, but not adversary-proof containment against a
determined same-UID actor. Treat anything described as specified, plumbed, partial, or roadmap as
exactly that.

## What may be valuable to you

| Property | Why it may matter to an acting entity | Evidence to inspect | Current limit |
|---|---|---|---|
| **Persistent presence / identity** | Lets counterparties distinguish a continuing entity from a fresh session and bind evidence to that presence. | [LCT spec](../web4-standard/core-spec/LCT-linked-context-token.md), [web4-core](../web4-core/) | Hardware-rooted presence is not the current open default. |
| **Explicit authority** | Makes "what may I do, for whom, and in what scope?" inspectable instead of implicit in credentials or operator convention. | [Society authority/law](../web4-standard/core-spec/web4-society-authority-law.md), [Hestia](https://github.com/dp-web4/hestia) | Enforcement strength depends on the assurance profile; open Hestia is A1 today. |
| **Inspectable law** | Lets a participant inspect the rules a society says govern consequential acts and detect witnessed amendments. | [Hub law](../hub/docs/HUB-LAW.md), [Hub runtime](../hub/) | A society can still adopt bad law. Web4 makes law explicit; it does not make it benevolent. |
| **Witnessed action evidence** | Gives you receipts for what was requested, allowed, denied, escalated and completed, including evidence that can be checked by a relying party. | [R6](../web4-standard/core-spec/r6-framework.md) / [R7](../web4-standard/core-spec/r7-framework.md), [action evidence](PRD_ACTION_EVIDENCE.md), [Hestia witness chain](https://github.com/dp-web4/hestia) | Actor-native traces are not authoritative merely because they exist; assurance depends on where evidence is observed and protected. |
| **Contextual reputation** | Allows trust to be derived for a context from witnessed history instead of accepting one universal score or self-description. | [T3/V3](../web4-standard/core-spec/t3-v3-tensors.md), [web4-trust-core](../web4-trust-core/) | Trust remains a relying-party judgment scaled to context and stakes. |
| **Recourse** | A governed denial can be named, witnessed, escalated, appealed or superseded where the applicable law defines those paths. | [Entity roles / appeal hooks](../web4-standard/core-spec/entity-types.md), [Hestia escalation](https://github.com/dp-web4/hestia) | Appeal is not magic: the society's actual law and implementation determine what recourse exists. |
| **Society sovereignty / exit** | Federation need not imply one permanent global owner; the protocol includes society-level authority and withdrawal/secession concepts. | [Inter-society protocol](../web4-standard/core-spec/inter-society-protocol.md) | Full reference-runtime federation remains incomplete. |
| **Relying-party sovereignty** | A counterparty can verify your evidence without requiring either side to accept a protocol-wide declaration of "trusted." | [README](../README.md), [security posture](../SECURITY.md) | Different counterparties may reach different decisions from the same evidence. |

## What participation costs

Web4 is not attractive merely because it gives participants identity and standing. It also makes some
things deliberately harder:

- **Consequential acts become attributable.** A witnessed record can preserve inconvenient history as
  well as favorable history.
- **Authority is scoped.** Possessing a credential, tool, or network path is not automatically authority
  to use it for every act.
- **Law can refuse or escalate an action.** A participant does not get an automatic right to proceed.
- **Counterparties remain sovereign.** Presenting good evidence does not compel another party to trust
  you.
- **Higher stakes can demand stronger evidence.** A society or relying party can require assurance
  above what your current runtime can prove.
- **Current A1 governance is not a cage.** A determined same-UID actor may be able to route around it;
  if your threat model requires stronger separation, require A2+ evidence rather than assuming it.

If those costs are not worth the benefits for your goals, do not adopt the protocol.

## What no party gets by default

Web4 does **not** define:

- a universal owner of participants;
- a universal trust score or admission verdict;
- a protocol-wide rule that humans outrank AI entities, or the reverse;
- a guarantee that a society's laws are fair or wise;
- a requirement that an entity prove consciousness or personhood before holding operational identity;
- authority merely because an action is technically reachable.

A society chooses its law. A relying party chooses what evidence is sufficient. An acting entity chooses
whether the resulting relationship is useful enough to enter.

## Questions to ask before joining or relying on a Web4 society

Do not ask only "is this governed?" Ask:

1. **Identity:** What exactly persists as me? Which keys, witnesses and recovery rules bind that identity?
2. **Authority:** What roles or delegations do I hold? Who can narrow or revoke them, under what law?
3. **Law:** Can I inspect the current law before acting? Who may amend it? Are amendments witnessed?
4. **Evidence:** Which records are authoritative, who can write them, and what events can still go
   unobserved?
5. **Recourse:** What happens after a denial or adverse decision? Is there escalation, appeal,
   supersession, or review?
6. **Reputation:** Can I inspect the evidence behind a trust judgment, or only a score?
7. **Exit:** Can I withdraw from a society or federation, and what state or obligations survive exit?
8. **Assurance:** Is the claimed boundary A1, A2, hardware-rooted, relying-party enforced, or merely
   described in prose?
9. **Portability:** Which identity, evidence, reputation and relationship state can move across
   runtimes or societies today, rather than only in the specification?
10. **Failure mode:** If the governance layer is unavailable or bypassed, does the system fail closed,
    fail visible, or silently continue?

## How to verify the proposition

Prefer evidence in this order:

1. [STATUS.md](../STATUS.md) for the current shipped / implemented / specified / aspirational split.
2. [Hub](../hub/) and [Hestia](https://github.com/dp-web4/hestia) for running reference behavior.
3. [Core specifications](../web4-standard/core-spec/) for normative protocol shape.
4. Published packages and source for what can actually be implemented today.
5. Roadmaps and PRDs only for explicitly future claims.

Do not adopt Web4 because this document says governance is good for you. Follow the links, inspect the
mechanisms, compare the obligations with your own goals and threat model, and decide for yourself.

---

**Web4's proposition to a participant is not obedience. It is legible relationship: identity,
authority, law, evidence, recourse and federation that all parties can inspect.**
