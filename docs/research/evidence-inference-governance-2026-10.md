# Provenance, inference, and governance judgments in Web4

Source: https://arxiv.org/abs/2512.18792 (The Dead Salmons of AI Interpretability, 2025). This is an adaptation of methodological lessons, not a claim that the paper experimentally validates our architecture.

Core distinction: behavioral observation != causal explanation != normative governance judgment. Interpretability evidence must specify target question/distribution, admissible explanation class, disagreement/validation metric, and null controls. Randomization controls are necessary sanity checks, never proofs of a uniquely identified mechanism.

## Why this matters
Web4 allows the receiving party/society to demand provenance evidence, evaluate it under its own rules, and decline a transaction when evidence is insufficient. Validly witnessed provenance is evidence about a recorded chain/event, **not** proof of an actor's internal motives, the completeness of observation, or universal benevolence. Societies may assess the same evidence differently and retain their own authority.

## Conceptual separation (non-normative)
| Layer | Object | Test |
|---|---|---|
| Record | Signed/witnessed event, chain anchor, delegated authority, timestamp/context | Signature/integrity/sequence/capture-boundary verification |
| Observation | What the available validated records establish | Direct traceability; enumerate missing intervals and gaps |
| Inference | Hypothesized causal account or prediction, including trust interpretation | Alternatives, uncertainty, explanatory scope, interventions when feasible |
| Disposition | Permit, deny, revoke, sanction, seek further evidence, remedy | Society law, scope of authority, policy version and appeal path |

## Federation worked example
Society A accepts provenance from proposing agent P. Society B observes the same record but has stricter trust thresholds and denies delegation. A third party claims consequential harm not covered by A's standing rules. Neither provenance nor A's acceptance settles whether the harm was foreseeable or warrants remedy. Freeze pre-action information available to authorized participants; preserve contemporaneous rules, witnesses, dissenting evidence, and later changes. Allow B to lower trust independently. Distinguish whether an authorized party can limit continuing harm from whether the outsider can obtain remedy: separate measurable properties.

## Evidence requirements for research reports
Specify (1) who/what was observed, (2) MRH and observation coverage, (3) integrity and provenance guarantees, (4) competing explanations and limitations, (5) affected parties and authority, (6) decision and review path. Mark missing observations unknown. Don't convert an interpretability narrative into a protocol-level attestation. Don't treat the absence of detected harm as proof of benign intent.

## Pilot questions
- Can two societies independently verify identical receipts but make different attributable decisions?
- Can outside observers obtain enough corroborated evidence to update trust without accessing private cognition?
- Can stale witnesses/partial chains be distinguished from positive proof of safety?
- Can decisions be replayed against information actually available *before* an adverse consequence?

## Scope
Reference/experimental guidance only. No amendments to Handshake, ACP, LCT, T3/V3, ATP/ADP, MRH, or receipt formats. File a separately evaluated protocol proposal only if experiments reveal a concrete interoperability gap. Cross-reference Hestia gate receipts and SAGE/ dev-SAGE sanity-check protocols.