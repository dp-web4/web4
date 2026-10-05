# Web4 / Hestia: technical introduction for agent identity and authorization reviewers

**Open reference work for persistent agent identity, delegated authority, runtime governance, provenance, and witnessed accountability**

AI agents can now act across tools, networks, credentials, and other agents. The control problem is no longer only "is this credential valid?" It is also:

> Which entity is acting, under whose authority, in what role, against which law, with what scope, and what evidence will exist afterward?

Web4 is an open protocol / ontology for expressing that evidence. Hestia is the local runtime that exercises the governance path.

## What exists now

The public stack includes working or actively exercised mechanisms for:

- persistent human and agent identity;
- role / authority separation;
- signed, scoped, revocable delegation;
- per-member policy and least-privilege constraints;
- allow / deny runtime decisions;
- human escalation and witnessed rulings;
- hash-linked action evidence;
- contextual trust derived from recorded conduct;
- local vault / credential custody;
- multi-agent society and governance semantics;
- explicit incident classification / investigation-scope governance;
- destination-binding semantics so authorization follows the actual effect rather than only the requested tool call.

## What we do not claim

The current open Hestia reference deployment is **A1**: cooperative and tamper-evident, not tamper-proof against a determined same-UID actor.

A2 separate-principal enforcement, broader OS / network enforcement, hardware binding, and full federation remain work in progress.

That boundary is documented because a useful standard must distinguish evidence semantics from enforcement strength.

## Why it may be relevant to NIST / NCCoE

The NCCoE *Software and AI Agent Identity and Authorization* concept paper asks about:

- agent identification and identity metadata;
- authentication and key management;
- least privilege;
- dynamic authorization;
- proof of authority;
- "on behalf of" delegation;
- binding human authorization to agent action;
- auditing and non-repudiation;
- controls that reduce prompt-injection impact.

The implementation has direct counterparts for each of those questions, with gaps called out explicitly.

## Review path

Start here:

https://github.com/dp-web4/web4/tree/main/docs/standards

Primary repositories:

- Web4: https://github.com/dp-web4/web4
- Hestia: https://github.com/dp-web4/hestia
- SAGE: https://github.com/dp-web4/SAGE

NIST-specific crosswalk:

https://github.com/dp-web4/web4/blob/main/docs/standards/NIST_NCCOE_AI_AGENT_IDENTITY_AUTHORIZATION_CROSSWALK.md

Implementation evidence:

https://github.com/dp-web4/web4/blob/main/docs/standards/IMPLEMENTATION_EVIDENCE.md

## Useful evaluation question

Rather than asking whether the project vocabulary should be adopted, ask whether the underlying mechanisms are useful in a standards-based demonstration:

1. Can an agent prove identity and delegated authority for one action?
2. Can the relying party reject insufficient evidence?
3. Can scope be revoked?
4. Can an out-of-scope act be denied and witnessed?
5. Can a human or independent peer adjudicate the exact recorded act?
6. Can the system distinguish the requested target from the destination actually reached?
7. Can the record state honestly which assurance level produced it?

If those mechanisms are useful, they can be mapped onto existing identity / authorization standards rather than requiring adoption of the full Web4 ontology.
