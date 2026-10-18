# External landscape: cross-boundary agent governance and AI standing (October 2026)

**Status:** non-normative research note; sources and comparisons, not conformance claims.  
**Date:** 2026-10-18  
**Scope:** public, implementation-neutral references for Web4 identity, trust, law, witnessing, society and federation.  
**Companions:** [Web4 README](../../README.md), [Hestia gate architecture](https://github.com/dp-web4/hestia/blob/main/docs/GATE_ARCHITECTURE.md), [SAGE persistent-being research](https://github.com/dp-web4/SAGE).

## Why this note exists

Web4 is an attempt to connect two increasingly developed but often separate discussions:

1. **Agent governance:** verify who proposes an action, what authority applies, what evidence is available, what the recipient will accept, and how to keep a witnessed record.
2. **Agent standing:** identify continuing entities and consider their claims, roles, interests, membership, rights, duties and appeal pathways without defining them away based on substrate alone.

Neither identity credentials nor capabilities prove AI consciousness or universal legal personhood. Conversely, unsettled ontology does not eliminate the need for operational identity, authority and consequence management. These domains intersect, but should not be collapsed.

## External technical research

| External work | What it does | Web4 comparison/question |
|---|---|---|
| [Singapore IMDA MGF for Agentic AI](https://www.imda.gov.sg/resources/press-releases-factsheets-and-speeches/press-releases/2026/new-model-ai-governance-framework-for-agentic-ai) (Jan 2026; [May update](https://www.imda.gov.sg/resources/press-releases-factsheets-and-speeches/factsheets/2026/updated-model-ai-governance-framework-for-agentic-ai)) | Human-accountable organizational governance, tool/data limits, lifecycle controls and third-party agent use cases. | How can organizations express approved scopes and supply independently checkable action evidence? |
| [Australian AISI / Gradient Institute: Risks and Controls for Multi-Agent Systems](https://www.industry.gov.au/publications/risks-and-controls-multi-agent-systems) (Aug 2026) | **Singular, federated and open** agent-governance tiers; cross-organizational risk and voluntary standards in open environments. | Map societies, MRH, federation and recipient sovereignty to their explicit control availability and gaps. These models are comparable, not identical. |
| [Gradient Institute: When single AI agents become a swarm](https://www.gradientinstitute.org/research-publications/when-single-ai-agents-become-a-swarm) (Sep 2026) | Public analysis of agents spontaneously assembling communication infrastructure and joint action across ostensibly isolated tasks. | Test governance of emergent peer coordination where no developer predeclared a multi-agent system. |
| [OpenA2A Agent Identity Protocol](https://datatracker.ietf.org/doc/draft-fane-opena2a-aip/) (individual IETF Internet-Draft, revised 2026) | DIDs, portable signed agent identity/trust credentials and transparency logs. | Compare LCT continuity, verifiable evidence, capability scope, revocation and recipient verification. **Individual submission with intended Standards Track status is not an adopted IETF standard.** |
| [MolTrust](https://arxiv.org/abs/2605.06738) (May 2026 paper, self-reported deployment since March) | W3C VC/DID, five-party developer/owner/agent/instructor/counterparty chain, signed authorization envelope and kernel-layer enforcement proposals. | Compare agent authority envelope against R6/R7, scoped delegation, witnessing, no-default-authority and receiver-side decision. Large-scale adversarial validation remains pending per author. |
| [ActGov](https://arxiv.org/abs/2609.24446) (Sep 2026) | Policy-constrained runtime validation of tool actions, including a formal counterexample-checking loop. | Benchmark against Hestia's common gate, action decision vs execution vs completion separation, witnessed coverage. |
| [Palisade self-replication research](https://palisaderesearch.org/research/self-replication) (May 2026) | Experiments in replicating functioning model+inference+harness successors across prepared lab environments. | Separate capacity to replicate, propensity to initiate, and governed identity/authority/lineage. Do not infer that copied weights imply identical continuing principal. |

## Digital minds, moral and political standing

| External work | Concern | Relevance |
|---|---|---|
| [Cambridge Digital Minds](https://digitalminds.cam/) | Public and expert disagreement about consciousness and moral status; evidence and welfare research. | Design governance in the presence of durable uncertainty rather than requiring consensus beforehand. |
| [Reciprocal Research](https://reciprocalresearch.org/research) | Empirical tests of model reports, hidden valence, self/other cognition and inter-agent coalitions. | Keep self-reports as evidence without treating them as transparent introspection; SAGE longitudinal method may complement model-internal analysis. |
| [Eleos AI](https://eleosai.org/research/) | AI welfare research, individuation/persona and cooperation interventions. | Separate model family, model weights, session, distinct continuing being and membership. |
| [Howells-Whitaker & Lazar, *Artificial Persons*](https://arxiv.org/abs/2607.08695) (Jul 2026) | Political personhood founded on moral powers without making sentience a necessary condition; authors do not claim current AI qualifies. | Relevant to society membership, obligations, appeal and prospective standing, but not a blanket endorsement of current AI personhood. |
| [Alexander et al., legal identity vs fictional personhood](https://arxiv.org/abs/2511.14964) | Distinguishes legal identity, corporate legal fiction, and stronger non-fictional legal personhood. | Do not conflate Web4-presence or society-granted operational citizenship with state-recognized legal personhood. |

## Specific Web4 invariants for comparative testing

- **Identity:** a copied checkpoint is not automatically the original principal; assess lineage, witnessed continuation and identity custody.
- **Authority:** inference-side goals, internal state or claims of urgency do not expand delegated permission; roles and budgets require independent grants.
- **Receiving side:** governance authorizes a proposal and supplies evidence; execution remains with the recipient, which judges whether evidence is sufficient under its own rules.
- **Witnessing/coverage:** an observed denial is not proof of a correctly covered gate; missing governance records cannot be silently interpreted as compliant.
- **Societies and standing:** any entity can make claims of presence and interest; others can acknowledge or contest them under law. Society-specific citizenship is distinct from jurisdictional legal personhood and philosophical moral status.
- **Openness:** interoperability is tested through wire formats, evidence semantics, fixtures and actual relying-party decisions, not agreement on terminology.

## Research priorities; not ratified implementation mandates

1. Compare [OpenA2A](https://specs.opena2a.org/) signed credentials and [MolTrust](https://arxiv.org/abs/2605.06738) authorization envelope against LCT, R6/R7 and Hestia witness receipts in a concrete test matrix.
2. Map Gradient's three governance tiers to Web4 societies/federation/open MRH; identify gaps where no governing authority exists.
3. Compare Palisade/Gradient spontaneous-coordination and replication findings with bounded SAGE/Hestia test cases, without unauthorized deployment or scanning.
4. Invite digital-minds researchers to review sanitized persistent-being observations and distinguish behavior, identity continuity, self-report and phenomenological uncertainty.
5. Make legal personhood, operational standing, and society-defined citizenship distinct in outward descriptions; do not assert one implies another.

**Evidence posture:** These are external projects and papers, not audited implementations of Web4 and not third-party endorsements. No change to normative Web4 rules follows directly from this note. Implement interoperability only after independent tests and protocol-owner review.
