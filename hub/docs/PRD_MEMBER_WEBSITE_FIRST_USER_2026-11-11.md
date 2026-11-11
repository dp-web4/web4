# PRD - Hub as a Community Website

**Date:** 2026-11-11  
**Status:** Proposed product direction; no release readiness claim or partner commitment  
**Canonical repo:** `dp-web4/web4/hub/` (not the `4-hub` mirror)  
**Companion:** [Hestia Personal App PRD](https://github.com/dp-web4/hestia/blob/main/docs/PRD_FIRST_USER_APP_2026-11-11.md)  
**Related:** [Hub original PRD](PRD.md), [federated north star](PRD_HUB_V2_FEDERATED.md), [Hub README](../README.md).

## 1. Product thesis

**To users, a Hub is a website.** It has a URL, identity, purpose, public pages, people, membership, profiles, participation, relationships and activities. They should not be required to understand Web4's protocol primitives to join a community.

Web4 remains the substrate; Hub remains a sovereign society runtime with signed law and witnessed consequences. A web frontend is a consumer of real governed capabilities, not a parallel authoritative database or a permission bypass.

**Each society has its own site, branding and governance**; Hub is not one centralized social network. A public visitor can learn about a society without installing Hestia. Hestia is an optional personal app for durable presence, approvals and governed AI activity.

## 2. Baseline, product gap and motivation

The existing Hub README records a runnable Rust reference daemon, membership, roles, signed law, ledger, sealed channels, introduction flows, REST/MCP APIs and operator admin GUI. The original PRD explicitly deferred a **public member-facing web UI**; an operator dashboard is **not** that UI. Federated R1-R6 work is specified but unbuilt; advanced production and assurance claims must remain calibrated.

External discovery illustrates the gap: COWONDER's founder described a proposed Relationship Intelligence Engine matching members by needs, knowledge and offers, and separately expressed interest in witnessed contributions/contextual trust. No joint pilot is agreed. This is a use case, not a request to bake COWONDER matching logic into Hub.

The product problem: a functioning society runtime is not yet an accessible place people can visit and participate in.

## 3. Personas

| Persona | Wants to | First visible success |
|---|---|---|
| Anonymous visitor | Learn whether this society fits | Public home, purpose, law and membership expectations |
| Prospective member | Decide whether and how to join | Understand disclosures; submit request; see accurate status |
| Member | Find people by interests/skills and contribute | Profile, search/discovery, introduction and participation records |
| Organizer | Establish and run a community | Configure society, membership workflow and moderation under law |
| Auditor/member | Understand a consequential decision | Inspect status, authority, explanation, receipt and recourse |
| Developer/integrator | Add a domain-specific product | Stable scoped API and extension points without copying the trust engine |

## 4. Experience requirements

**W1 - Public site:** Each Hub has a canonical configurable HTTPS origin, name, icon, society description, charter, member/admission expectations, public activity and relevant disclosures. Public pages must work without JavaScript-heavy private credentials where possible. Lock/maintenance/degraded mode should communicate accurate availability and not fabricate memberships or allow writes.

**W2 - First-user flow:** Landing -> society law/expectations -> join choice -> identity/disclosure -> request -> governed admission -> member home. All states and denials must be explicit; no silent consent. A society may define different admission rules, but site presentation must remain honest about them.

**W3 - Membership and privacy:** Public, members-only and self-only profile fields are distinct. Members can declare skills, needs, interests and offers; disclosures are opt-in and enforced server-side. Do not put private profile data, secrets or full trust histories in SEO pages. Retention, withdrawal and witness immutability must be explained accurately.

**W4 - Discovery and intros:** Search using authorized member-visible fields with meaningful filters (skills, interests, offers, relevance). Distinguish declared attributes from verified contributions. A *proposed* introduction, a *consented* introduction and an *established* relationship are different events. Prevent unilateral publication of another member's relationship.

**W5 - Contextual trust:** Reputation evidence belongs to context and source: what was claimed, witnessed, verified, disputed or corrected. Show the reason for a signal and avoid universal ranking, opaque gamification or inferred trust from mere activity.

**W6 - Activity and recourse:** Plain-language history of proposals, approvals/denials, contributions, introductions, role changes and law amendments (filtered by entitlement). Where a receipt is available, reveal who acted, relevant authority and witness evidence. An allowed act is not a verified external result.

**W7 - Admin/operator separation:** Preserve existing local loopback and privileged surfaces; public member writes must use authenticated, governed, server-validated endpoints. No browser client may call local admin ports, unlock endpoints, secret APIs or privileged MCP writes. Maintain CSRF/session, replay, least privilege and rate/abuse protections.

**W8 - Self-hosting and portability:** The site and runtime should be deployable under a society-controlled domain with no mandatory centralized Web4 account or recurring platform fee. Document open-source license and optional Hardbound/commercial boundaries, backup/recovery and operational limitations.

**W9 - Accessibility and mobile:** Responsive website, semantic controls, keyboard navigation, accessible messages, localization-ready text and safe partial/offline states.

**W10 - API-first extensibility:** Third-party matching/recommendation systems can consume authorized, consented data and return *suggestions*. They never acquire governance, identity or relationship truth by inference. Avoid entangling proprietary matching code with AGPL-covered modules without reviewing license terms.

## 5. Acceptance scenario: synthetic community

Create an isolated, repeatable demo Hub with **no live member records and no access to any external business platform**.

1. Operator creates a society with name, purpose, charter and public site; a fresh browser sees the public page.
2. At least three synthetic profiles declare complementary interests, skills, needs and offers, with field-level visibility.
3. A visitor sees only public information; an authenticated member sees only fields permitted by law and disclosure.
4. An external toy matcher (or manual search) suggests an introduction based on authorized declared fields, explicitly labeled as a *suggestion*, not a Web4 trust decision.
5. Both synthetic participants choose whether to accept; only consented outcomes appear as relationships.
6. A participant records a synthetic contribution; a witness record is produced and a contextual evidence-backed signal is displayed. Self-asserted skills alone do not confer earned reputation.
7. A deliberate unauthorized read/write and a declined introduction are tested: neither leaks private data or creates a relationship; attempted acts/denials are recorded according to law.
8. One member uses the companion Hestia app to inspect membership, disclosure and receipts. Another visits in an ordinary browser without Hestia.
9. Reset the demo deterministically and verify that the resulting published data reflects only intended disclosures.

**Pass gates:** An independent nondeveloper completes browser visit, join, discovery, introduction and contribution journeys; all consequential server writes traverse the actual Hub law/ledger; automated tests establish privacy and authority boundaries; a second test subject can decline without public reputation penalty for merely declining.

**Not a pass:** Static mock screens, invented receipts, direct DB mutations bypassing law, a demo needing real member data, or assuming working federation that is not deployed.

## 6. Delivery plan

| Slice | Deliverable | Verification |
|---|---|---|
| F0 - Inventory | Existing REST/member/auth/intro/status/law capabilities mapped to screens and missing APIs | Endpoint-to-journey matrix, permissions review |
| F1 - Society website | Public landing, law, identity, configurable branding and locked/read-only state | Browser test without Hestia |
| F2 - Member lifecycle | Identity presentation, disclosures, join/pending/admitted/refused, member home | Real admission receipt end-to-end |
| F3 - People and relationships | Consent-scoped profiles, skills/interests, authorized search, intro request/response | Two-party acceptance and refusal tests |
| F4 - Evidence and trust | Contributions, witnessed records, contextual evidence and recourse | Full provenance chain, no fabricated outcome |
| F5 - Deployment and pilot | Self-host setup wizard, sample-data import/reset, accessibility, ops docs | Fresh deployment + synthetic external pilot |

Measure first-society launch time, browser-only understanding, join completion, successful consented introductions, false trust inferences, unauthorized data exposure, and percentage of consequential actions accompanied by attributable evidence. Establish baselines before assigning numerical targets.

## 7. Ownership, interfaces and boundaries

- **Hub:** society-specific public/member website, governed membership, law enforcement, admission, intros, society receipts.
- **Hestia:** personal identity/governance app, local controls, agent permissions, participation receipts; not a compulsory website dependency.
- **Web4 core:** canonical trust, law, identity and witness primitives.
- **Integrators:** independently owned business logic and domain-specific UX; expose only authorized data through APIs. A proposed COWONDER exploration would begin with synthetic profiles and without COWONDER infrastructure or member data.
- **Hardbound:** separate private/proprietary higher-assurance product; not required for this first community test.

No third-party NDA, license variation, commercial commitment or ownership transfer is established by this PRD. Open-source AGPL-3.0-or-later obligations and separate commercial licensing possibilities must be stated precisely.

## 8. Open questions

1. What minimal browser-held identity is acceptable for member writes when Hestia is absent?
2. Which endpoint/profile semantics already implement field disclosure versus need protocol/runtime work?
3. What is the authoritative lifecycle for proposed, mutual and revoked introductions?
4. Which context/evidence is appropriate for a public reputation display, and who can dispute/correct?
5. How can operators deploy a secure HTTPS Hub without being Rust/Linux specialists?
6. Which parts of federation are demonstrable today versus prospective?

**Release gate:** A public website is not a trustworthy Hub merely because it renders cards. The actual runtime must verify identity, law, consent and witnessed consequences at every consequential boundary.
