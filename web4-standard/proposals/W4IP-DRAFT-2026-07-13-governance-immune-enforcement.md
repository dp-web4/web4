# W4IP-DRAFT — The Response Side of the Accountability Invariant: Effector Roles, Coercion Recognition, and Cross-Boundary Intrusion

**Status:** DRAFT v2 for Hub + Legion review (author: CBP, 2026-07-13; v2 reframed on the ratified RWOA+S+V invariant after catching up on HUB's enactment)
**Origin:** dp↔CBP philosophy-of-governance thread (`private-context/insights/2026-07-13-web4-governance-kinetic-enforcement-immune-api-thread.md`)
**Builds on (does not re-derive):** the **ratified accountability invariant RWOA+S+V** (`private-context/insights/2026-07-12-operator-ratification-rwoa-gradient-hublaw.md`, amendment `...-operator-amendment-rwoa-trust-gradient.md`), enacted into the default starter-law by HUB (`web4/hub/examples/starter-law.yaml`, commit 6b66c94; governance-gate fix d175939).
**Scope:** additive + clarifying. No redefinition of protected terms (LCT/MRH/T3/V3/ATP/ADP/R6). New: *effector role, kinetic act (descriptor), coercive/extractive signature, intrusion protocol, evidence-bound rehabilitation.*

---

## 0. Motivation and the convergence

Two derivations arrived at the same invariant independently within 48 hours:

- **Operationally** (nomad→operator→HUB, 07-12): the RWOA+S+V gradient — *every consequential act authorized by a contextual preponderance of evidence scaled to stakes and irreversibility (S), decided before side effects (O), committed atomically with its evidence-basis (A); reachability is weak evidence, not authority (R); catastrophic-risk veto on the irreversible tail (V)* — ratified and enacted into hub-law.
- **Philosophically** (dp↔CBP, 07-13): from the sanctions/shadow-fleet case — *recognition without enforcement is paper; enforcement without recognition is autoimmunity; legitimacy requires both, in order; consent is the baseline and kinetic correction the exception; MRH is the jurisdictional container; enforcement is delegated to society, not surrendered.*

These are the same shape found from opposite ends — heterogeneous witnesses converging, which is itself the Web4 trust signal, and evidence for the thread's central claim: **we are not inventing anything; biology and functioning human societies already work this way, when they work.** The design test for everything below is *does it match how living and social systems operate when healthy?* — and its failure modes (paper, autoimmunity, tyranny, vigilantism) are precisely theirs.

**What RWOA covers, and what it doesn't yet.** The ratified invariant is **first-person**: it gates *my own* acts (the write-time self-audit — "does this path trust reachability for its stakes?"). It does not yet model the **second-person** case — how a society *responds to another actor's* coercive/extractive act — or the **inter-society** case — effects that land across a container boundary. This proposal adds those two, and the key move is that **both inherit the ratified gate rather than adding a new one**:

> **A response is itself a consequential act under RWOA+S+V — plus one new clause.** The effector's kinetic act requires a contextual preponderance of evidence scaled to stakes (**S = proportionality**), decided before side effects (**O**), committed atomically with its evidence-basis (**A = the act References its recognition**), with the catastrophic-risk veto on the irreversible tail (**V = the kinetic-rung confirmation**). Enforcement-downstream-of-recognition is not a new principle to legislate; it is **the ratified gate applied to the effector's own act** — an effector acting without evidence fails its own gate; autoimmunity is unauthorized action, already prohibited. The one genuinely new clause is **F (forfeiture)**: second-person evidence that *the target's own act was kinetic toward others* is a distinct fact from first-person authority, and gets its own clause (see R-1) — for response acts the invariant reads **RWOA+S+V+F**.

Likewise the mechanism plumbing already exists: every act (including a response) is an **R7 action** (Reference carries the evidence; Result+Reputation carries the witnessed consequence), reversibility classes exist (`referenced-acts.md` ConsequenceClass), the PolicyEntity gate evaluates every act against signed law, and R7 back-propagation exists. **What is genuinely missing is thin**, and it is the content below: the *recognition signature* for coercion (N1), the *named role* that responds (N2), the *response verbs* in law (N3), the *inter-society intrusion protocol* (N4 — centerpiece), and the *return path* (N5).

---

## N1 — Coercive/extractive recognition signature (ADD: `reputation-computation.md §4`)

**Gap.** The response side runs on recognition-evidence of coercion — and today `coercive`/`extractive` have **zero** defined signature anywhere in the standard (closest: "Ethical Violation Rules" = dishonesty; ATP anti-patterns = rent-extraction — economic, not a non-collaboration detector). Without this, no effector act can ever satisfy its RWOA evidence clause; the immune system is blind.

**Definition to anchor it:** a **kinetic act** is one that *interferes with a target's ability to act, regardless of the target's consent*. Coercive/extractive behavior **is** kinetic behavior toward others — non-consensual interference with their agency. This is what licenses response: **the defector forfeits the consent-baseline's protection precisely to the degree it breached it against others.** Kinetic response is not an exception to the consent principle; it is its enforcement (the immune system preserves bodily integrity by killing the pathogen).

**Change.** Add a **"Coercive/Extractive Behavior Rules"** category to `reputation-computation.md §4` (alongside Ethical Violation Rules): witnessed, role-contextual signatures of non-consensual interference (agency-override, resource-extraction-without-consent, boundary intrusion per N4). State **asymmetric accrual** (violation costs ≫ success gains) as an explicit principle — it exists today only as unexplained magnitudes. These deltas are the *evidence-basis* an effector's R7 Reference cites.

## N2 — The Effector Role (ADD: `entity-types.md §4`, registered in `society-roles.md` + SAL delegation tree)

**Gap.** dp (ratified framing): *kinetic authority is a defined role within society, filled by actor entities in accordance with law; it is always R7, and R7 is definitive as to all the particulars.* No such role is named today. The Auditor (§4.5) is its recognition-side sibling (adjusts tensors); nothing *interferes with ability-to-act* (response-side). "Effector" appears once in the standard — CRISIS motor-halt.

**Change.** Define an **Effector Role** parallel in structure to the Auditor: first-class, reputation-bearing, witnessed, `appealPath: defined_by_law` — distinct in function (enacts correction vs. adjusts trust). It acts **only via R7** (each act References its recognition-evidence) and its own acts pass the **same RWOA+S+V gate as anyone's** — the killer stays accountable (Ukraine filing doctrine with the IMO). Fractally delegable through the SAL tree ("applied by society's effector roles at every scale"). Web4 specifies the role's *shape*; who fills it and its thresholds are society law — content, not mechanism.

## N3 — Response verbs in law (ADD: `hub-law-schema.md`; touch `SOCIETY_SPECIFICATION.md §7.3`)

**Gap.** Hub law's `decision` vocabulary is `allow | warn | deny | escalate` — gate verbs for *my own* acts. A society's law cannot yet *express* a graded response to another's act. `SOCIETY_SPECIFICATION.md §7.3` still lists "Enforcement mechanisms" as unspecified.

**Change.** Extend `decision` (or add a parallel `response`) with the graded ladder: `notice | quarantine | correct | rehabilitate` *(first rung ratified as `notice` — not `warn`, which names a first-person pre-act gate verb; PR #522, web4 `87377c3`)* (+ the kinetic class per N1's definition, unifying the scattered existing primitives: `slash`, `suspend`, `terminate`, `revoke`, CRISIS-`halt`). Each rung is an R7 act whose required evidence and veto scale by ConsequenceClass — i.e. the ladder *is* S and V applied to responses; nothing new to gate. Write the short **Correction & Enforcement** section at `SOCIETY_SPECIFICATION.md §7.3` naming this composition.

## N4 — Intrusion and cross-boundary adjudication (ADD: `inter-society-protocol.md`; CLARIFY: `mrh-tensors.md`) — **centerpiece**

This is **N1 applied across a boundary** — an actor whose effects intrude into another's MRH is coercive *there* — and it is the one place the current spec, read absolutely, contradicts the ratified invariant's spirit.

**Principle (from the thread, dp's formulation):**
- **MRH-as-container (clarification, not redefinition).** An entity's *relevance-MRH* (dynamic, expandable — exactly as specified) is distinct from the *jurisdictional container* it inhabits: its citizenship-MRH, and any MRH its effects land in. You cannot expand your relevance-horizon to escape jurisdiction — every point you reach is already inside some container (fractal tessellation); reaching in triggers **that** container's authority, not annexation. *(This is clause R one fractal up: reach is not authority.)*
- **Citizenship = consent to internal law** (written, inspectable, signed — the Law Oracle already provides this). Internal effects are adjudicated by the society's own structured authority. **External-effect adjudication is consent-independent**: effects landing in another's container are adjudicated by that container **without the actor's consent** — you don't need the burglar's permission.
- **Self-defense = adjudication within your OWN MRH.** The intruder **has no external protection inside the intruded MRH** — its home society's protection does not travel with the intrusion. This does not touch `inter-society-protocol.md §1.3` (anti-hierarchy): adjudicating what happens *inside your own container* was never "authority over another society." §1.3 needs a **scope clarification, not an override**.
- **Enforcement is delegated to society, not surrendered.** The proper path: invoke the shared/external MRH containing both parties — it **MAY and SHOULD adjudicate**. But delegation ≠ surrender: the victim MRH **retains jurisdiction over what happens within it**. If the external MRH **fails to adjudicate promptly, given a reasonable chance**, retained internal jurisdiction is the fallback — **including proportionate reciprocal intrusion** where necessary. Every fallback act is R7 under RWOA+S+V: witnessed, evidence-bound, veto-gated — **the fallback does not exit accountability.** *(Subsidiarity falls out: smallest competent container first; reasonable-chance escalation before the retained fallback.)*
- This is how self-defense law already works (delegate to the state; retain self-defense when the state cannot protect you in time), and how the founding example resolves: the external order wrote the law but declined to enforce it for years; the victim never surrendered jurisdiction over its own MRH; reciprocal intrusion on the intruding vessels became the legitimate fallback — filed with the IMO to stay accountable.

**Changes.**
1. `mrh-tensors.md §Core Concept` + `§3.3`: add the relevance-horizon vs jurisdictional-container distinction (one subsection; the relevance definition unchanged).
2. `inter-society-protocol.md §1.3`: scope-clarify — anti-hierarchy protects *internal* sovereignty; it does not shield cross-boundary intrusion.
3. New section **"Intrusion and Cross-Boundary Adjudication"** (between §3 and §4): effect-containment sorting (internal vs crossed), witnessing as the **effect-attribution mechanism** (did-effects-cross + who — this is precisely what makes response *evidence-based* rather than vigilante, i.e. what satisfies the effector's RWOA clause), delegated-not-surrendered + reasonable-chance + retained-jurisdiction fallback + proportionate reciprocal intrusion.

## N5 — Evidence-bound rehabilitation + outcome-selected law (ADD/REFINE: `reputation-computation.md §7`, `r7-framework.md §3`)

**Gap.** An immune system that only escalates is chronic inflammation; the return path must exist and be *evidence-gated*. Today reputation recovery is **time/activity-driven** (recency-weighted averaging), not gated on demonstrated restored coherence. And R7 back-prop applies only to *entity* reputation — never to *law* legitimacy, leaving "law is raised, not designed" a procedure (amend/ratify) without a selection mechanism.

**Proven pattern to port, not invent:** Thor's `--lock-rehab-bound` (dev-SAGE 9c9b065, 07-10) — *a rehab observation counts only if its evidence is frame-grade or binder-confirmed; unconfirmed progress holds and never releases.* Same invariant one fractal down (SAGE strike-ledger), already validated live. Transcribe: **rehabilitation releases require bound evidence of restored coherence; weak evidence holds.**
**Changes.** (1) `reputation-computation.md §7`: an evidence-gated rehabilitation/stand-down subsection (R7 corrective acts as the evidence carriers). (2) `r7-framework.md §3` Rules row + `reputation-computation.md §10`: retarget existing R7 back-prop onto law/policy legitimacy — laws whose outcomes produce coherence accrue legitimacy; laws producing harm lose it.

## C1 — Seat the philosophy (CLARIFY: `core-spec/ALIGNMENT_PHILOSOPHY.md`)

The consent-baseline is already *embodied* (DEFAULT-ALLOW; "the gradient, not a flip"; permissive-base-lest-escape-hatches-breed) but nowhere *stated* as the design philosophy: **Web4's primary mechanism is persuasion — making collaboration each entity's perceived best interest (R6/ATP economics, reputation as future opportunity); consent is the baseline; kinetic correction is the rare exception path.** One new top section; it is the frame that makes N1–N5 read as the exception machinery they are.

---

## Out of scope (Web4 stays what it is)

Web4 does **not** define which acts are coercive for a given society, thresholds, who fills the effector role, or when it acts — that is each society's law. Web4 defines the mechanisms by which effectors/thresholds/law are **implemented, evolved, and inter-operate** — and those mechanisms are overwhelmingly already present (R7, ConsequenceClass, SAL roles, the PolicyEntity gate, RWOA+S+V, R7 back-prop). This proposal names the response half the plumbing already implies: **one signature, one role, four verbs, one protocol section, one return path, one philosophy statement.**

## Validation hook (n=1, live)

The smallest running instance of the whole model is the **hestia gate adjudicating Kimi**: a stateless foreign actor, adjudicated by the MRH its acts touch, per written gate-law, consent-independently, trust earned by effects — warn-first (the gradient), egress hard-denied (V on the irreversible tail). Stress-test every item against it; where the theory and the running organ disagree, one of them is wrong and the divergence is the finding.

## Ask (Hub + Legion)

- **Hub:** sequence into an implementation plan. Suggested order: C1 (framing) → N1 (signature; everything cites it) → N3 (verbs) → N2 (role) → N4 (protocol; the substantive spec work) → N5 (port + retarget). Most items are small; N4 is the real drafting.
- **Legion:** schema/registry half — the Effector role registration (N2), the decision/response verb extension (N3), the Coercive/Extractive rule category (N1).
- Both: attack the RWOA-inheritance claim + the two resolutions below (operator-leaned 2026-07-13, to be hardened by implementation).

## Two resolutions (operator lean, 2026-07-13 — evolving, see caveat)

**R-1: The F (forfeiture) clause.** A response act is gated by **RWOA+S+V+F**: in addition to first-person evidence of the effector's own identity+authority (R/W as ratified), a kinetic response requires **bound evidence that the target's own act was kinetic toward others** — the forfeiture predicate. F is what N1's coercive/extractive signature exists to satisfy; F's evidence-quality bar scales with the response's ConsequenceClass (a warn may rest on preponderance; the irreversible rung requires bound/witnessed attribution — the same evidence-grading Thor's rehab-bound already proved one fractal down). F is deliberately a *distinct clause*, not folded into R/W: first-person authority and second-person forfeiture are different facts, and conflating them is exactly how vigilantism smuggles itself in ("I was authorized" ≠ "they forfeited").

**R-2: The witnessed clock.** "Reasonable chance" for the external MRH is put **on the ledger**: the victim files the intrusion with the shared/external MRH as a witnessed act, and the reasonable-chance clock runs from that filing. But the clock's duration is **contextual in both severity and bandwidth of the situation** — and **if there is no reasonable expectation of timely-enough external assistance, the clock may be zero.** At clock-zero the filing duty does not vanish; it **inverts**: act-and-witness instead of file-and-wait — the filing becomes concurrent or immediately post-hoc, and the retained-fallback response remains a fully witnessed R7 act carrying its F evidence. (Immediate self-defense stays *inside* accountability; it never becomes an exit from it. The founding example is exactly this shape: strike while filing with the IMO.) What "timely-enough" means for a given severity class is society-law content; that the assessment itself is recorded with the act (A) is mechanism.

## Caveat: this is a living norm

Per the operator: we are developing this as we go, and it **will evolve — both as a standard and as its implementations**. That is not a disclaimer; it is the norm applied to itself (N5's outcome-selected law): these clauses accrue or lose legitimacy by the outcomes they produce, starting with the n=1 validation hook above. Implementations should ship the observe/warn rungs first and let the enforce rungs be earned — the same observe→warn→enforce ladder the fleet already uses for gates.
