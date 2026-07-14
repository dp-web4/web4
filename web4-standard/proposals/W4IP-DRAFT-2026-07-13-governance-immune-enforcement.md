# W4IP-DRAFT — Governance Immune System: Recognition→Effector, Kinetic Correction, and Cross-Boundary Adjudication

**Status:** DRAFT for Hub + Legion review (author: CBP, 2026-07-13)
**Origin:** dp↔CBP philosophy-of-governance thread (`private-context/insights/2026-07-13-web4-governance-kinetic-enforcement-immune-api-thread.md`)
**Scope of change:** additive + clarifying. Respects Terminology Protection — **no redefinition** of LCT / MRH / T3 / V3 / ATP / ADP / R6. New terms introduced: *effector role, kinetic action, correction/rehabilitation cycle, cross-boundary effect, external adjudication, coercive/extractive signature.*

---

## 0. Motivation — Web4 is the recognition organ of an immune system; it must not be paper

> **We are not inventing anything.** Biology and functioning human societies already work this way — when they work. Immune systems already do recognition→effector, tolerance, and rehabilitation, and their pathology *is* autoimmunity. Functioning societies already run on a consent-baseline with enforcement **delegated, not surrendered** — that is exactly self-defense law and subsidiarity. This proposal transcribes those invariants; it does not design a novel scheme. The **design test** is: *does it match how living and social systems operate when healthy?* And its failure modes (paper, autoimmunity, tyranny, vigilantism) are precisely theirs. This is also why the mechanism is already largely present: **R7 is the plumbing**, and the pattern R7 encodes is the pattern nature already selected for.


Web4 today is a mature **recognition + accountability** layer: it identifies actors (LCT), evaluates coherence-in-context (T3/V3·MRH), publishes inspectable signed law (SAL / Law Oracle), and accrues reputation (R7 back-propagation). That is its role, and it should stay its role. But a recognition layer with **no effector interface** is the G7 sanctions regime in our founding example: perfect legibility, zero consequence — "revealed as paper." An immune system needs recognition *and* effectors, and the contract between them.

The governing frame is an **immune system, not a jail**:
- **Consent is the baseline.** Web4's primary work is *persuasion* — making collaboration the perceived best-interest via R6/ATP economics and reputation-as-future-opportunity. When persuasion works, no enforcement is needed. Enforcement is the **exception path**, not the point.
- **Two symmetric failures to avoid:** enforcement *without* recognition = **autoimmunity** (vigilantism); recognition *without* enforcement = **paper**. Legitimacy requires both, **in order** — enforcement is downstream of recognition, never a substitute.
- **Web4 defines mechanisms, not content.** It specifies *how* effectors, thresholds, and law are implemented, evolved, and inter-operate — it does **not** define what any society's effectors, thresholds, or laws *are*. (Network layer for governance; the "apps" are each society's law.)

The changes below add the effector-side **mechanisms** while keeping Web4 out of the content of enforcement.

**Critical framing — the plumbing is already R7.** A kinetic act is not a new primitive. **It is always an R7 action** performed by an effector role, and **R7 is definitive as to all particulars**: it references the recognition that licenses it (Reference), it is witnessed and produces a reputation delta (Result + Reputation), its reversibility is carried by ConsequenceClass, and its appeal path is defined by law. This proposal therefore **adds almost no new mechanism.** It (1) *names* the effector role as an R7-acting SAL role, (2) fills the two genuinely-missing content-adjacent gaps — a coercive/extractive reputation signature and cross-boundary-effect adjudication — and (3) clarifies MRH-as-container. Everything else is "point at the R7 / SAL / ConsequenceClass plumbing that already carries this." Where a change below reads as "ADD a type/ladder," read it as "recognize the R7 pattern that already expresses it, and name it."

---

## P1 — Seat the collaboration/consent-baseline philosophy (ADD)

**Principle.** Web4 recognizes that every entity acts in its perceived best interest, always; its primary design goal is to *persuade* that collaboration is in that interest. Consent is the baseline; kinetic correction is the rare exception when persuasion fails.

**Current state.** ABSENT as an inter-actor thesis. `ALIGNMENT_PHILOSOPHY.md` "alignment not compliance" is about *standard↔implementation* co-evolution, not actor-to-actor persuasion. ATP/ADP economics *implement* the incentive (efficiency pressure, T3-premium pricing, anti-hoarding) but are never framed as "makes enforcement rare."

**Proposed change.** New top section in `core-spec/ALIGNMENT_PHILOSOPHY.md` (before "Bidirectional Alignment") stating the collaboration/consent-baseline thesis and naming enforcement as the exception path. Cross-reference `atp-adp-cycle.md §9.1 "Desired Behaviors"` and `r6-framework.md §Overview` framing R6/ATP as the **economic-persuasion layer** (reputation as future opportunity) that makes the effector idle by design.

---

## P2 — State the recognition/effector membrane + the typed exported signal (ADD/CLARIFY)

**Principle.** Web4 is the recognition layer; it is **not** the effector. It exports a typed signal and does not pull the trigger. The effector is a separate organ (P4) that subscribes.

**Current state.** PARTIAL. SAL is named the "Trust Accountability Layer" but nowhere states it is *not* the effector. Recognition outputs exist scattered — `presence-protocol` `verdict`, PolicyEntity compliance score, T3/V3 — but there is no single **exported recognition signal**.

**Proposed change (lean — no new type).** The recognition an effector acts on is already carried by an R7 action's **Reference** (the coherence verdict, reputation, and MRH it cites). No new "RecognitionSignal" type is needed.
- Add only a scoping *statement* (SAL summary / `SOCIETY_SPECIFICATION`) — "Web4 recognizes and attributes; it does not enact. A kinetic act is an R7 action by an effector role that **References** the recognition licensing it." This is the membrane, stated, not a new mechanism.
- Add the **outward** case to `acp-framework.md §7` (ACP today models only inward gatekeeping of *its own* agent): an effector's R7 action References an external recognition rather than an internal plan. One paragraph, not a subsystem.

---

## P3 — Define "kinetic" + a graded, reversibility-gated response ladder (ADD; unify scattered primitives)

**Principle.** **Kinetic = interference with a target's ability to act, regardless of consent** (revoke credential, sever channel, burn/slash ATP, suspend/terminate citizenship, destroy instance, publish de-legitimization, CRISIS halt). Response is **graded and proportional**: `observe → warn → quarantine → kinetic`, each rung gated on (a) a valid recognition signal at threshold, (b) MRH-scope, (c) witness diversity + confidence, (d) **ConsequenceClass** — the more irreversible, the higher the bar.

**Current state.** ABSENT as a unified class; ingredients all present but never composed. `referenced-acts.md §4` already defines `ConsequenceClass = Reversible | Costly | Irreversible`, scales trust impact, and gates council sign-off (`Irreversible ⇒ council`) — but only for *an actor's own acts*. Punitive primitives exist scattered: `slash` (evidence-gated ATP destruction), `suspend`/`terminate` citizenship, "halt effectors" (CRISIS, `entity-types.md §13.4`), `atp_penalty`.

**Proposed change (lean — the ladder is already R7 × ConsequenceClass).** A graded response is nothing but R7 actions of increasing ConsequenceClass; the gating already exists (`Irreversible ⇒ council`). No new response subsystem.
- Define **"kinetic"** as a *descriptor* for the class of R7 acts whose Result interferes with a target's ability to act (unifying the already-existing `slash` / `suspend` / `terminate` / `revoke` / CRISIS-`halt` primitives as instances). Anchor: `entity-types.md §13.4`, where "effector" + CRISIS-halt already live.
- Note (do not build) that `ConsequenceClass` in `referenced-acts.md §4` already classifies the reversibility of *any* R7 act including a response, and already gates it — so "the graded ladder" is a naming/collation of existing R7+ConsequenceClass behavior, placed in a new **Correction & Enforcement** section at `SOCIETY_SPECIFICATION.md §7.3` (currently "Enforcement mechanisms — unspecified").

---

## P4 — Add the Effector Role (ADD; first-class, accountable, appealable — the killer is accountable)

**Principle.** A named SAL role that **acts via R7** — each corrective/kinetic act References the recognition that licenses it and produces a witnessed reputation delta — applying the society's thresholds and enacting graded correction. Because it is R7, its acts are **inherently witnessed, reputation-bearing, adjudicable, and appealable**. An effector exempt from recognition is autoimmune; the effector is a first-class Web4 actor under the same accountability as everyone else. (Ukraine filing doctrine with the IMO ≈ the effector staying under accountability while acting.) This is the *only* genuinely new role — and it is a role, not a mechanism; the mechanism is R7.

**Current state.** ABSENT as a named role; substrate present. Roles are first-class reputation-bearing entities; the **Auditor Role** is the structural template (evidence-transcripted, witness-quorum'd, `appealPath: defined_by_law`) — but the Auditor *adjusts tensors* (recognition-side). No role *interferes with ability-to-act* (response-side).

**Proposed change.**
- Define an **Effector Role** in `entity-types.md §4` (between Authority §4.2 and Auditor §4.5), parallel in structure to Auditor: reputation-bearing, witnessed, appealable; distinct in function (enacts correction vs. adjusts trust).
- Register it into the `society-roles.md` role taxonomy and the SAL delegation tree so it is normative and fractally delegable (authority "applied by society's effector roles at every scale").
- Extend `hub-law-schema.md` `decision` verbs beyond `allow|deny|escalate` to include correction/response outcomes (e.g. `warn | quarantine | correct | rehabilitate`).

---

## P5 — Enforcement-downstream-of-recognition + autoimmunity guard + defector-forfeits-consent (ADD; normative principle)

**Principle.** (a) Every kinetic response MUST cite a valid upstream recognition signal; enforcement without recognition is prohibited (autoimmunity). (b) Non-consensual (kinetic) response is legitimate specifically against an actor whose **own** behavior was coercive/extractive — i.e. itself non-consensual interference with others. The defector forfeits consent-protection to the degree it breached it. This is what lets a consent-based system use non-consensual force: it does so only to restore the consent-baseline the target broke.

**Current state.** ABSENT. No ordering principle links enforcement to prior recognition. `coercive`/`extractive` have **zero** reputation signature (closest: "Ethical Violation Rules" = dishonesty; ATP anti-patterns = rent-extraction/speculation — economic, not a non-collaboration detector).

**Proposed change.**
- Add the ordering + autoimmunity-guard as a normative principle in the new Correction & Enforcement section (`SOCIETY_SPECIFICATION.md §7.3`).
- Add a **"Coercive/Extractive Behavior Rules"** category to `reputation-computation.md §4` (alongside Ethical Violation Rules) — the defined signature of non-collaborative action that licenses a graded response. State **asymmetric accrual** (failure costs more than success) as an explicit principle here (currently only implicit in magnitudes).

---

## P6 — Intrusion, own-MRH self-defense, and delegated-not-surrendered enforcement (CLARIFY + ADD) — **centerpiece; a corollary of P5**

This is not a separate principle. It is **P5 applied across a boundary**: an actor whose effects intrude into another's MRH is coercive/extractive *there*, and forfeits protection *there*.

**Principle.**
- **MRH as container (clarification, not redefinition).** An entity's **relevance-MRH** — its dynamic, expandable context reach, exactly as specified today — is distinct from the **jurisdictional container** it inhabits (its citizenship-MRH, and any MRH its effects land in). You cannot expand your relevance-horizon to *escape* jurisdiction, because every point you reach into is already inside some other entity's container (fractal tessellation). Reaching in triggers **that** container's authority, not annexation.
- **Self-defense = adjudication within your OWN MRH.** When an outside actor intrudes into your MRH (its effects land inside your container), you adjudicate **what happens within your own container** — which you always had authority over. This is **not** asserting authority over another society; §1.3 is untouched. **The intruding actor has no external protection within the intruded MRH** — its home-society's protection does not travel into the container it intruded on.
- **Enforcement is delegated to society, not surrendered.** The proper path is to invoke the **external/shared MRH** that contains both parties: it **MAY and SHOULD adjudicate** the intrusion. But delegation ≠ surrender — the victim MRH **retains jurisdiction over what happens within it**.
- **Fallback.** If the external MRH **fails to adjudicate promptly, given a reasonable chance**, the victim's **retained internal jurisdiction** is the fallback — and internal enforcement **includes reciprocal intrusion** where that is what is necessary and proportionate.
- **Subsidiarity** falls out of the above: prefer the smallest competent container; escalate to (and give reasonable chance to) the shared MRH before exercising the retained fallback.

This is exactly how self-defense law and subsidiarity already work in functioning societies (delegate enforcement to the state; retain the right of self-defense when the state cannot protect you in time), and how the founding example resolves: the external MRH (the West/IMO order) wrote the law but failed to enforce it promptly across years of reasonable chance; the victim (Ukraine) never surrendered jurisdiction over its own MRH, so internal enforcement — **reciprocal intrusion** on the intruding vessels — became the legitimate fallback, filed with the IMO to stay accountable.

**Current state.** ABSENT / PARTIALLY CONTRADICTED. `mrh-tensors.md` defines MRH as a *dynamic, self-updating relationship graph / "horizon that extends from us"* — explicitly **not** a container, and *expandable* (the annexation loophole, if left unclarified). `inter-society-protocol.md §1.3` reads absolutely — *"no mechanism to assert authority over another society without consent"* — with no statement that this protects **internal** sovereignty only and never shields **cross-boundary intrusion**. No "retained jurisdiction / delegated-not-surrendered / reasonable-chance / reciprocal intrusion" structure exists. Witnessing is rich but never framed as cross-boundary effect-attribution.

**Proposed change.** (Terminology-protected: **clarify** MRH, do not redefine.)
- In `mrh-tensors.md §Core Concept` + `§3.3`: add the **relevance-horizon vs jurisdictional-container** distinction. The relevance graph is unchanged; "container" is a *governance role* of the same structure. Dissolves the annexation loophole without touching the definition.
- In `inter-society-protocol.md §1.3`: **scope-clarify (not override)** — anti-hierarchy protects a society's *internal* matters; adjudicating an intrusion **within one's own MRH** is internal sovereignty, not authority over another society. Add the **delegated-not-surrendered** principle and the **retained-jurisdiction fallback** (external MAY/SHOULD adjudicate → reasonable chance → victim's internal enforcement, including proportionate reciprocal intrusion).
- Add a new **"Intrusion and Cross-Boundary Adjudication"** section (`inter-society-protocol.md`, between §3 first-contact and §4): intruder-has-no-protection-in-intruded-MRH; subsidiarity with reasonable-chance escalation; **witnessing as the effect-attribution mechanism** (did-effects-cross + attribution) that makes both external and fallback-internal enforcement legitimate rather than vigilante. Every act in this section is an R7 action (P0): the reciprocal-intrusion fallback is itself witnessed, reputation-bearing, and adjudicable — **the fallback does not exit accountability.**

---

## P7 — Bidirectional immune system: evidence-gated rehabilitation, stand-down, law-as-outcome-selected (ADD/REFINE)

**Principle.** An immune system that only escalates and never tolerates is chronic inflammation. The API is bidirectional: de-escalate and re-admit on evidence of restored coherence. And law itself is *raised*, not fixed — outcome-selected legitimacy.

**Current state.** PARTIAL. Reputation is recoverable *mechanically* (recency-weighted average on a 0.5 baseline) but recovery is **time/activity-driven, not evidence-of-correction-gated**; `suspend → reinstate` exists but no rehabilitation cycle. Law is amendable via a witnessed `propose|ratify|amend|repeal` pipeline (good) but R7 back-prop applies **only to entity reputation, never to law/policy legitimacy**.

**Proposed change (lean — both reuse R7 back-prop).**
- **Rehabilitation is an R7 corrective cycle:** add an **evidence-gated rehabilitation / stand-down** subsection to `reputation-computation.md §7` (after inactivity-decay) — a return path gated on demonstrated restored coherence, not merely elapsed time, expressed as R7 corrective actions; plus a corrective-posture stand-down for effectors. Cross-ref the new Correction & Enforcement section.
- **Outcome-selected law reuses the existing mechanism:** retarget R7 back-propagation — already defined for entity reputation — onto *law/policy legitimacy* (laws producing coherence accrue legitimacy; laws producing harm lose it). Anchor `r7-framework.md §3` (Rules row, currently a fixed input) + `reputation-computation.md §10 "Future Evolution"`. No new mechanism; "law is raised, not designed" becomes a target of the back-prop that already exists.

---

## Out of scope (deliberately — keep Web4 what it is)

Web4 does **not** define: which acts are coercive/extractive for a given society, the numeric thresholds, who fills the effector role, or when it acts. Those are each society's law/effectors/thresholds. Web4 defines only the **mechanisms** by which they are expressed, witnessed, evolved, and inter-operated — and those mechanisms are **overwhelmingly already present** (R7 as the act grammar, ConsequenceClass as the reversibility gate, SAL roles as the accountable actors, R7 back-prop as the evolution engine). What this proposal adds is thin: the **effector role name**, the **coercive/extractive signature**, the **intrusion/cross-boundary adjudication** rules, and a set of **clarifications** (MRH-as-container, consent-baseline, delegated-not-surrendered). We are not building an immune system; we are naming the one the plumbing already implements — the one biology and functioning societies already run.

## Validation hook (n=1, already running)

The smallest instance of this whole model is live: the **hestia gate adjudicating Kimi** (a stateless, non-citizen foreign actor) by CBP's MRH-law, consent-independently, trust earned by effects. Before/while implementing, stress-test each proposal against that instance — if the philosophy is right, the running organ is already an instance of it; where it isn't, the gap tells us whether the theory or the plumbing is wrong.

## Submission ask (Hub + Legion)

- **Hub** (owns web4/hub review/merge): sequence P1–P7 into an implementation plan. The load-bearing core is **P6** (intrusion / delegated-not-surrendered / retained-jurisdiction fallback) and **P5** (the coercive/extractive signature it depends on). **P1 must land first** so the rest reads as exception-path, not default. Most of P2/P3/P4/P7 is *naming and pointing at existing R7 / SAL / ConsequenceClass plumbing*, not new subsystems — scope the plan accordingly (small).
- **Legion** (schema/registry): the **Effector Role** registration into `society-roles.md` + SAL delegation tree (P4, an R7-acting role parallel to Auditor); the `decision`-verb extension (P3); the **Coercive/Extractive** rule category in `reputation-computation.md §4` (P5). No new signal type (P2 leaned out — recognition is carried in R7 Reference).
- **Resolved (was an open question):** *who holds kinetic authority?* — a **defined effector role within society, filled by actor entities in accordance with law; every kinetic act is an R7 action, and R7 is definitive as to all particulars** (witness, reputation, reference, reversibility, appeal). Web4 specifies the role's shape and that it acts via R7; it does **not** specify who fills it or the thresholds — that is society content. There is no separate "who pulls the trigger" mechanism to design; R7 is it.
