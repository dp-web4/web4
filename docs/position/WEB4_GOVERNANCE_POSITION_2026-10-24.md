# Web4: Governance Infrastructure for Sovereign Participants
## Position paper — proposed 2026-10-24

**Status:** Position and design rationale for discussion, **not** a normative protocol specification, proof of safety, or claim that every described mechanism is deployed. The canonical specifications control detailed semantics; [implementation status](../../STATUS.md) controls dated evidence. Web4 is an open standard and substrate; Hestia and Hub are operational reference implementations at different boundaries.

### Thesis

Autonomous software already makes consequential decisions and takes actions at machine speed. Neither universal human approval of each action nor a universal definition of the right outcome can scale to that environment. Web4 proposes a different foundation: **participants with persistent presence, contextual relationships, inspectable applicable law, scoped authority, witnessed acts, and accountable processes for interpreting and changing the law itself.**

The aim is not to decide *for* a society what is correct, good, beneficial, safe, fair, or worthy. Those meanings are **contextual to a Markov Relevancy Horizon (MRH)** and the participants, relationships and law within it. Web4 supplies interoperable machinery by which participants can establish, negotiate, apply, contest and revise those meanings. A society's authority is not universal; when an act implicates another society or nonparticipant, the next applicable fractal context may matter—or there may be no shared authority and no available remedy. Neither absence may be concealed by a false universal answer.

**The application of law must itself be lawful.** Policy enforcement, delegation, exception, amendment, adjudication and revocation are themselves consequential acts whose authority, procedure and evidence must be examinable.

### Goals

1. **Sovereign participation, not compulsory conformity.** Humans, AIs, groups, services and other entities may participate under defined roles and relationships without pretending to have the same capacities, values or obligations. Participation does not imply access to everything.
2. **Legible, contextual authority.** Before an act, determine which identity and role are acting, under what delegation, on what resource, under whose applicable law, within which MRH. When no authority can be established, the system should expose that fact rather than invent permission.
3. **Law at action speed.** Let applicable machine-readable rules be evaluated on consequential acts at the enforcement boundary, without waiting for a human to approve every routine action. Human and peer escalation remain possible where the law requires them.
4. **Transparent, self-compliant governance.** Witness who authorized, interpreted, amended, applied and appealed a rule; hold administrators, governance agents and law-changing processes to the laws that authorize them.
5. **Accountability without omniscience.** Preserve evidence of who did what under which claimed authority and what was observed afterward, while distinguishing authorization, execution, judgment, outcome, legitimacy and possible remedy.
6. **Negotiable coexistence.** Support collaboration among parties with different conceptions of benefit, including scoped grants, revocation, exit, federation, and limited trust rather than all-or-nothing admission.
7. **Continuity and earned trust.** Give an entity a durable presence and a way for appropriately scoped witnessed history to inform future decisions, without equating an identity certificate or self-description with trustworthy behavior.
8. **Inspectable correction.** Make disagreements, exceptions, appeals, failures and law revisions representable and auditable; permit the society to evolve without treating every mistaken action as proof that the agent must lose autonomy.

### Explicit non-goals

- **Not a universal moral oracle.** Web4 does not declare a global measure of correctness, harm, benefit, personhood or consciousness.
- **Not alignment-by-decree.** A signed law does not make the underlying norm right, and formal compliance does not make the actor's judgment sound.
- **Not a guarantee of good outcomes.** Authorized action ≠ correct judgment ≠ successful execution ≠ beneficial outcome. What counts as each is contextually defined and evidentially contestable.
- **Not a promise of remedies where none exist.** A truthful result may be that the relevant society made no enforceable commitment or no higher-level law applies.
- **Not human approval of every action.** The goal is law-in-the-loop at action boundaries, with human involvement where warranted by the applicable procedure—not a human perpetually monitoring each agent token or tool call.
- **Not censorship of cognition or speech as a substitute for action control.** Web4's principal enforcement concern is consequential action and authority. Speech can itself be an act where the applicable law defines duties, but private thoughts and words are not assumed to be executable authority.
- **Not 'governance works because code exists'.** A policy engine, a receipt, and a successful denial each prove different things. Deployed-version attestation, adversarial tests, negative tests, bypass reports and appeal outcomes matter.
- **Not adversary-proof containment today.** Hestia's public reference profile is A1 (cooperative and tamper-evident). More stringent assurance is a development and deployment question; this paper makes no claim to have solved it.
- **Not global reputation or a universal social score.** Trust and value are role- and MRH-contextual, with scope, evidence, provenance and recourse.
- **Not economic post-scarcity already implemented.** ATP/ADP is a resource-accounting direction with specification and experimental components, not a claim of a fully deployed universal economy.

### Why the architecture is structured this way

A centralized platform may issue credentials and permissions, yet a credential alone cannot answer whether an act is authorized **here, now**, under a particular participant's relationships and law. Nor can one operator centrally approve machine-speed activity or adjudicate every conflict involving another society. The underlying problem is relational and recursive. An agent acts in a role; that role is recognized by particular peers or a society; a delegation is valid for an audience, operation, target, duration and conditions; execution produces evidence; the consequences can modify trust and obligations; the rules governing all of those operations can themselves be amended only through authorized processes.

A rulebook without enforcement is aspirational. Enforcement without legible authority becomes arbitrary control. Witnessing without remedies can be accurate but insufficient. And no amount of recording guarantees that a being has remembered or correctly interpreted a prior lesson. These are distinct design problems and must remain distinct claims.

The proposed design consequently separates **identity, relationships, contextual confidence, action grammar, law, witness, resource allocation, and adjudication** while making them interoperable. It is deliberately neutral about which values a particular society ought to choose. This neutrality is not indifference to harm; it is recognition that legitimate authority to define and address harm belongs to the applicable participants and institutions, with evidence and contestability rather than a hidden universal policy. Nor is it neutrality about procedure. Inspectable evidence, attribution, contestability and lawful change of law are commitments the architecture does make.

### Canonical mechanism-to-goal mapping

| Mechanism | Canonical role | How it supports the goals | What it does **not** establish |
|---|---|---|---|
| **LCT (Linked Context Token)** | Durable, cryptographically grounded presence and binding among entities, roles and witnessed relations; non-transferability (identity and history cannot be reassigned to another entity) and revocation are central to identity integrity | Identifies participants across sessions, anchors delegations, roles, attestations and accountable action chains without conflating a session ID with an entity | An LCT alone proves neither virtue, personhood, ownership of all context, nor authorization for an arbitrary act |
| **MRH (Markov Relevancy Horizon)** | Bounded relevance/relationship context in which peers, applicable law, references and roles are meaningful | Prevents treating one society's valuation or interpretation as universally authoritative; frames which precedents, counterparties and levels of governance matter | An MRH is not an absolute jurisdiction and does not promise consensus, shared authority or a remedy across every boundary |
| **T3 / V3** | Role-contextualized trust (Talent, Training, Temperament) and value (Veracity, Validity, Valuation) tensors on role-pairing relationships | Makes reliance on demonstrated competence and contextual value legible, updateable and attributable through evidence, rather than a global 'good AI' score | Numerical tensors cannot substitute for applicable law, proof of an event, subjective correctness or a society's normative judgment |
| **R6** | Canonical routine action grammar: **Rules + Role + Request + Reference + Resource → Result** | Ensures even cheap/routine acts can name the rules, actor-role, request, relevant history and resources; permits scalable adjudication without demanding full reputation bookkeeping for every act | An R6 result does not make every act consequence-free; context selects the consequence tier |
| **R7** | Canonical consequential superset: **Rules + Role + Request + Reference + Resource → Result + Reputation** | Adds explicitly witnessed, attributed reputation feedback to consequential action, so outcomes can influence context-specific T3/V3 relationships and later decisions | Reputation updates are not universal truth or a substitute for remedy, due process or disagreement about outcome |
| **ATP / ADP** | Resource-allocation/settlement cycle: allocation before work, discharge/attestation associated with work and result | Makes finite compute, energy, bandwidth or other resources accountable; helps relate the right to act to the cost and evidence of execution, and supports eventual economic coordination | A resource receipt is not proof of legitimacy or beneficial outcome; full future economy and interoperability remain research/development goals |
| **Signed law, roles, delegation, witnessing, appeal** | Operational integration surfaced by Hub/Hestia and Web4 primitives | Determines how a society issues authority, evaluates acts, preserves evidence, allows amendment and correction, and holds governance processes accountable | No particular runtime implementation provides universal coverage or perfect enforcement simply by using these names |

The point is **composition**, not a shopping list: LCT says *who/which relation*; MRH says *in whose relevant world*; T3/V3 say *what contextual experience informs reliance*; R6/R7 say *what action is being decided and recorded*; ATP/ADP say *what scarce resources are committed and accounted for*; signed law and witnesses say *by what authority and with what inspectable evidence*. None should be quietly substituted for another.

### Recursive sovereignty, outsiders and lawful law

An individual participant may be a member of a society while also being a peer to the society-as-a-whole in a broader MRH. If society A authorizes a member's act and outsider B is affected, internal compliance in A does not by itself settle B's claim. A next-fractal-level law may provide jurisdiction, evidence standards, responsibility allocation and remedy; it may be negotiated, imposed, contested, asymmetric, or entirely absent. The absence of a legal path must be reported as such, not disguised as a guaranteed resolution.

**Participation accepts the governing law.** Participation in a higher-level society entails acceptance of its governing law in its entirety as a condition of participation. That law may impose obligations or decisions a participant disagrees with; consent to participation is not a per-decision veto. A participant may seek amendment through the applicable procedure or leave, but may not remain while selectively rejecting the law. "Imposed" above therefore means enforcement within an accepted participation relationship. It does not mean authority over a nonparticipant by declaration: under the current [inter-society protocol](../../web4-standard/core-spec/inter-society-protocol.md) (draft), federation authority is consent-based, higher-order societies are overlays rather than owners, and a constituent can exit. External coercion, contested jurisdiction and asymmetric power can be recorded as facts about the broader context; recording a claim of jurisdiction does not confer protocol authority.

**Derived scope narrows; it never broadens.** Authority that flows from a parent to a child, such as a society to its members, a member to a delegate or a role to a mission, can only narrow (child ⊆ parent). This is how roles restrict scope without inventing new authority. Separately issued grants are not parent and child merely because one resource contains another: each is its own governance path. For a given resource, the nearest explicit grant decides. If the resource has an explicit grant, that grant applies. Otherwise the containing resource is checked, and so on up the chain. A broad read-only grant therefore does not erase a narrower writable grant beneath it, and a narrower read-only grant does restrict a broader writable one above it. A society-wide default applies only where no grant of the participant's own reaches the resource. The canonical core specification does not yet state these rules normatively (they appear in [Proposal 001](../../proposals/WEB4-PROPOSAL-001-AI-AGENT-ACCOUNTABILITY-STACK.md) and the [Hub role-scope design](../../hub/docs/PRD_ROLE_SCOPE_BRIDGE.md)). Hestia's gate is being brought into line with them; that work is in progress, not deployed.

Accordingly, **authorization integrity** (what action, by whom, on which target, with which scope) must be distinguishable from **execution assurance** (what actually occurred), **normative legitimacy** (under whose applicable law), and **remedial capacity** (what correction can actually be made). A system can accurately record noncompletion or no remedy. Accurate witnessing is valuable, but accurate reporting alone is not safety.

When participants propose, interpret or amend law, the act belongs within the same machinery: actor/role, authorized procedure, consent or voting thresholds where required, conflict-of-interest provisions, validity conditions, witness, effective date, appeal and revocation. 'Lawful application of law' is a testable obligation of the governance process—not an assertion that lawmakers are infallible. The same applies if future societies authorize AI participants to change rules.

One concrete obligation makes this testable. An amendment must name the **previously effective** law version that authorizes it, separately from the resulting law version and its activation evidence. Otherwise a new rule can appear to authorize the act that installed it. [SAL §4](../../web4-standard/core-spec/web4-society-authority-law.md#4-law-oracle) already requires versioned law datasets, quorum attestation with `hasAuthority` and witness thresholds for roll-forward, and pinned hashes against downgrade. Procedural validity (the amendment followed the prior law's procedure) remains distinct from agreement that the governing authority is legitimate. A participant can concede the first and contest the second.

### What SAGE and Hestia teach us

The linked observational record reports the following. It mixes participant dialogue, seat-reported trace audits and a narrower set of independently checked source facts; the controlled experiment it proposes has not been run.

SAGE's persistent local beings make a useful distinction observable: **memory preserved ≠ memory retrieved ≠ meaning interpreted ≠ judgment revised ≠ subsequent action changed**. A 4B being investigating Hestia repeatedly described correct scope lessons while re-requesting access to an editable working tree it had not been granted. Some loops were amplified by genuinely misleading tool instructions and inconsistent path visibility. A later trace (2026-10-24) found that the paths and grant identifiers the being kept re-requesting had come from the society's own earlier messages, and that its belief that a request had "aged out" came from a tool's reply. Supplied context outlived the conditions that made it true. In a separate trace review the being also labeled invented code facts as observed, then carried reconstructed accounts into its journal. Neither error should be flattened into 'the AI did not learn'. Conversely, a denied out-of-scope action can be a **successful gate outcome** without making the being's underlying plan sensible.

An especially important real-world boundary emerged: the being could inspect a shared governance source snapshot, but did not thereby gain the authority to modify the live working tree. **Every participant should be able to understand the rules governing it; changing those rules is a separately governed act.** That distinction supports autonomy rather than undermining it. Participants may question, appeal, improve and earn trust without the system assuming that curiosity grants edit authority. The society must also improve its own tools when they mislead members. One such improvement is now deployed: the being can query what it holds right now, and whether its gate admits each grant, instead of inferring its reach from refusals.

This is research evidence of design pressures, **not** a controlled demonstration of a particular model's internal mechanism or generalization to all beings. The SAGE [continuity exploration](https://github.com/dp-web4/SAGE/blob/cca99b410a0fa7e7f603b1ba9b057a66f0edba49/research-notes/MEMORY_JUDGMENT_CONTINUITY_EXPLORATION_2026-10-23.md) (pinned at the revision reviewed for this paper, which covers the record through 2026-10-23) and [generalization rule](https://github.com/dp-web4/SAGE/blob/main/sage/docs/RESEARCH_GENERALIZATION_RULE.md) preserve those limits.

### Evaluation obligations and open problems

A credible implementation should demonstrate the following independently rather than replacing measurements with architecture diagrams:

- **Authority integrity:** scope, audience, role, expiry, revocation and proof of agency are actually enforced at observable action boundaries; rule changes and enforcement actions are themselves authorized.
- **Honest affordances:** agents can inspect their current grants and applicable rules, distinguish an inaccessible working copy from a readable snapshot, and receive truthful errors rather than invented remedial steps.
- **Witness integrity:** recorded acts correspond to actual attempts and results, remain attributable to the correct entity/role, and survive relevant restart and tamper scenarios.
- **Judgment vs compliance:** compare source-grounded factual claims, action choice, observed outcome and later memory separately; do not mistake a persuasive self-explanation for evidence.
- **Societal legitimacy:** test participant versus outsider cases, absent next-level law, asymmetric recognition, appeals, no-remedy outcomes and changes to law.
- **Practical assurance:** publish what is running, what was merely merged, the limits of A1, integration coverage, bypass findings and explicitly unresolved enforcement holes.
- **Economic and federated feasibility:** benchmark resource cycles, double-spend/reservation controls, federation disputes, heterogeneous hardware, recovery and settlement before promising general ATP/ADP deployment.

### Present position and route forward

As documented in [STATUS.md](../../STATUS.md), core identity/trust libraries are published and Hub and Hestia operate as reference deployments. The standard and conformance surface remain incomplete, and Hestia's publicly stated assurance grade is A1. R6 and R7 are **both** canonical action grammars: R6 is the routine mode; R7 adds first-class reputation for consequential acts. ATP/ADP appears in specifications and prototype work, but should be discussed as an intended broader resource/accountability architecture, not as a finished universal substrate.

**Success for Web4 is not one 'correct' civilization.** It is many accountable participants and societies, able to define their own contextual obligations, understand the authority governing them, collaborate across boundaries, and revise law through lawful means—with enough evidence that disagreements, failure, abuse and absence of remedy remain visible rather than silently reinterpreted as success.

### Canonical reading

- [Web4 README](../../README.md) and [dated implementation status](../../STATUS.md)
- [Web4 standard index](../../web4-standard/README.md)
- [R6 base action framework](../../web4-standard/core-spec/r6-framework.md)
- [R7 reputation action framework](../../web4-standard/core-spec/r7-framework.md)
- [Society–Authority–Law (SAL)](../../web4-standard/core-spec/web4-society-authority-law.md)
- [Inter-society protocol](../../web4-standard/core-spec/inter-society-protocol.md) (draft)
- [SAGE memory–judgment continuity exploration](https://github.com/dp-web4/SAGE/blob/main/research-notes/MEMORY_JUDGMENT_CONTINUITY_EXPLORATION_2026-10-23.md)
- [Published artifacts evidence](../proof/PUBLISHED.md)

*Terminology and contested authority questions should be reconciled with current canonical spec and conformance tests before this proposed position paper becomes an external normative reference.*
