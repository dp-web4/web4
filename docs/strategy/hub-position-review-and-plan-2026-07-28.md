# Hub position review and plan — hub vs. recent hestia progress and the web4 corpus

**Status**: Review + plan (one-pass, read-only) · **Date**: 2026-07-28 · **Author**: kimi-code (kimi)
**Scope**: `web4/hub/` at `752eadd`, read against hestia `main` (`bc24d82` and the week's merges) and the web4 corpus (specs, W4IP, `docs/PRD_ACTION_EVIDENCE.md`)
**Method**: two independent exploration passes over `hub/` and the repo, with the load-bearing claims re-verified by hand (`min_trust_score` references, CI inventory, starter-law). Nothing here ran the hub test suite — pass/fail of the 282 tests is unverified by this document; that gap is item P0-1 and the reason it comes first.

---

## 1. Why this review exists

Three bodies of work have been converging without a map of the convergence:

1. **Hestia** spent the last week turning governance defects into a taxonomy and then into instruments: published operating law, attribution-without-fallback, witnessed disclosure, fail-closed normalization, CI as a drawn boundary, sabotage-verified census tests.
2. **web4/hub** spent July productionizing: the H-001…H-011 security wave, durable mailbox, content-blind relay, LCT registry, admission repair path — 67 commits in 30 days, the repo's most active code area.
3. **The web4 corpus** froze its specs (the C-series audit machine, ~C270, mostly zero-net-new) while opening a new front: the **Agent Action Evidence Profile** (`docs/PRD_ACTION_EVIDENCE.md`, 2026-07-27), which needs independent implementations to be claimable as interoperable.

The hub sits in the middle of all three and belongs fully to none of them yet. This document says where it actually stands and what to do next, in order.

## 2. Where the hub code sits — verified state

**What is real and strong.** A coherent single-binary society hub: hash-chained witnessed ledger on three storage backends, generic `web4-policy` law engine gating acts and reads, sealed member↔hub and paired member↔member channels with anti-replay, crash-safe park-before-ACK mailbox, encrypted-at-rest vault with governed unlock, Sovereign Council M-of-N, pluggable signer including a Hestia callback mode (`hub/docs/HESTIA-MODE.md`), operator GUI, `hub up` deploy profiles. **282 test functions, zero `#[ignore]`, zero `todo!`/`unimplemented!`** in the tree. The July security wave (H-001…H-011, HUB-001/002) is thorough, traceable in code comments, and fully landed.

**The four gaps that matter** (each verified; each is a defect class hestia spent the week naming):

1. **The admission law section is declarative theater.** `AdmissionPolicy.min_trust_score` (`hub/hub-lib/src/law.rs:123`) is range-validated at load (`law.rs:275-282`), appears in test fixtures, is documented in `HUB-LAW.md` — and **nothing at admission reads it**. The join decision (`hub/hub-daemon/src/rest.rs:4632, 4731-4762`) gates on the generic norm engine only. Worse, this is not one field: `open`, `requires_sponsor`, and `sponsor_role` are equally advisory — `admin.rs:181-185` documents that the *display* of the gap was fixed while the gap was kept. Only `repeat_limit`/`review_limit` execute. And `hub/examples/starter-law.yaml:168` ships `min_trust_score: 0.0`, quietly canonicalizing the no-op. This is precisely "silently dead law" — the inverse of the `policy/extract.rs` defect hestia caught 2026-07-06, and the exact class hestia's PRD §6 names with the disposition "wire it with escalate-not-deny semantics, or delete it," deferred to HUB.
2. **Hub is CI-dark.** `web4/.github/workflows/` holds `sdk-test.yml` (Python SDK, path-filtered — hub changes don't even trigger it) and `build_whitepaper.yml`. The entire Rust workspace — hub, web4-core, web4-policy — runs tests only when a person types the command. Every green the hub has ever had was a person choosing to check. Hestia drew this boundary for itself two days ago (hestia#78) with the argument that transfers verbatim: which targets a green covers must be a property of the repo, not a per-session choice.
3. **The `hub-plugin` seam is published but unconsumed.** `ToolPlugin`/`PluginRegistry::dispatch` (`hub/hub-plugin/src/lib.rs:125-147`) is the canonical gate→handle→scope contract — and the daemon does not depend on the crate; it reimplements the contract inline. An instrument that exists and is not wired, again.
4. **Framing drift.** `hub/README.md` calls the hub a "reference proof-of-concept… production continues in a separate private repository" and elsewhere reads pilot-ready; the top-level `web4/hub-daemon/` directory is a dead sprint-0 leftover; `README.md:286` still says council threshold enforcement "is Phase 2" though H-002 shipped it 2026-07-06. Small, but this is the corpus that just spent a week proving small doc-code drifts are where the large failures incubate.

## 3. Hub vs. recent hestia progress

The two codebases are converging on the same contracts from opposite directions, and each holds the other's missing half:

| plane | hestia (this week) | hub (today) |
|---|---|---|
| **Law legibility** | operating law *published and quotable* (`hestia_operating_law`, per-layer hashes, NOT ENFORCED stamps, launch injection) — hestia#50/#69 | law is witnessed into the ledger and inspectable via API, but its most expressive fields **don't execute** (§2.1) |
| **Transport identity** | caller-asserted strings; transport auth is the known open hole (HST-005) | sealed channels + pubkeys + anti-replay **already shipped** (H-005…H-008) |
| **Attribution discipline** | latest-session fallback abolished on authority-bearing surfaces (FR-1, `PRD_ASSURANCE.md`); five residual sites enumerated and being swept | sealed-channel identity is strong; but admission is allow-by-default with no law, and trust-threshold law is unread |
| **CI** | boundary drawn 2026-07-28 (#78), scope-noted (CI exists ≠ CI gates) | none (§2.2) |
| **Test instruments** | sabotage-verified (censuses shown red before trusted; #79's three sabotage classes) | 282 hand-verified tests; no adversarial instrument tradition yet |
| **Shared vocabulary** | constellation roles fail-closed normalized at connect (#70) | same vocabulary co-spec'd and fail-closed on the hub side (`law.rs:53-97`) — **the one place convergence is already done** |

Two seams are explicitly waiting on each other:

- **Hub's signer already anticipates hestia** (`SwappableSigner::HestiaCallback`), and hub's v2 reputation subject pattern `constellation:<emitter>` is deliberately inert, "parked waiting on hestia's constellation-publish" (`law.rs:160-165`). Hestia's member registry and the web4 constellation-enrollment-registry spec (`docs/specs/`, 2026-07-21) are the two halves of that publish. **This is the highest-leverage convergence point: one design session, not a project.**
- Hestia's remaining authorization gaps (G4-auth egress, `mesh_egress` gate with no rules — hestia#63) are cases where hub-side experience with sealed, roster-resolved addressing (`resolve_peer`) is directly relevant.

## 4. Hub vs. the web4 corpus

- **AAEP (`docs/PRD_ACTION_EVIDENCE.md`)** needs a second, independent implementation before "interoperable" is claimable; hestia is named as the first reference. **The hub is the natural second** — and currently not one. Its witnessed ledger ≈ Result Evidence; its law engine verdicts ≈ Policy Decisions; but nothing binds an Action Request → Policy Decision → Result Evidence triple into signed, separately-attributable objects, and admission (the hub's most consequential decision) is exactly where the decision record is thinnest. An AAEP gap-mapping of the hub's join path is cheap and would tell both codebases what they actually have.
- **W4IP governance enforcement** is ahead of hestia on the hub side: response vocabulary (`notice|quarantine|correct|rehabilitate`) is already in the hub law schema (`87377c3`), the Effector role is registered, RWOA+S+V+F is folded into starter law. Hestia's conduct/adjudication machinery is where those verbs would actually bite. The seam between them (C232-N1: recognition→response unbridged for `reputation.delta.category`) is named and open.
- **Spec freeze** shifts the hub's risk profile: with the corpus byte-frozen and audited clean, the hub's drift risk is no longer spec-vs-code but **code-vs-its-own-docs** (§2.4) and law-vs-enforcement (§2.1).

## 5. Plan — sequenced next steps

Ordered by (honesty value ÷ cost). P0 is days, P1 is a week or two, P2 is design work, P3 restates the standing roadmap.

**P0 — draw the boundaries that cost almost nothing**

1. **CI for the Rust workspace.** Transplant hestia#78 verbatim: one workflow, `cargo test --locked`, unqualified (hub + web4-core + web4-policy), with the same scope note — it makes green a machine property of the commit, and does not make red block merges (branch protection is steward-side). Until this exists, every claim in §2 is hand-verified, including this document's.
2. **Retire the dead and the stale in writing.** Delete `web4/hub-daemon/` (sprint-0 leftover); fix `README.md:286` (council threshold shipped); mark `docs/SPRINT.md`/`SESSION_FOCUS.md` retired-as-of-2026-05-19 (the numbered-sprint apparatus stopped while 114+ commits landed — an abandoned tracker that still reads as live is the same null-state defect wearing a process coat).
3. **Name the starter-law no-op.** `starter-law.yaml:168` (`min_trust_score: 0.0`) should carry a comment stating the field is not yet enforced — one line, or the shipped example canonicalizes theater.

**P1 — make the law honest, in either direction**

4. **Disposition the admission section, HUB's call, both arms prepared.** Either wire `min_trust_score`/`open`/`requires_sponsor` into `submit_join` with **escalate-not-deny** semantics (a threshold its author owns is judgment; a threshold nobody wired is a hidden gate — the PRD §6 language), or stamp the section `NOT ENFORCED` on the served-law surface — the hestia#69 pattern, including the test that an absent marker never demotes and only an explicit one does. What is not acceptable is the third state, which is the current one.
5. **Sabotage-verify the hub's own instruments.** The hub has 282 tests and no adversarial tradition. Port the cheapest lesson from hestia#79: any future census/gauge test ships with a shown-red demonstration, or it is a decoration.
6. **AAEP gap-map of the join path.** One document: for a hub join, what plays Action Request, what plays Policy Decision, what plays Result Evidence, who signs what, what is missing (almost certainly: separately-signed decision records, revocation-at-action-time, and the decision-evidence binding). This is the entry ticket to hub-as-second-AAEP-implementation and it costs a day, not a sprint.

**P2 — converge the two halves that are waiting on each other**

7. **Constellation-publish design session.** Hub's parked `constellation:<emitter>` pattern + the enrollment-registry spec + hestia's member registry + the member-presence census instrument. Output: who publishes what, verified how, and what the v2 reputation subject becomes when it leaves fail-closed.
8. **Wire or narrow the `hub-plugin` seam.** Either the daemon dispatches through `PluginRegistry` or the README stops presenting the seam as the daemon's mechanism. Same disposition rule as P1-4: real or labelled.
9. **Share the authorization residue.** hestia#63 (the empty `mesh_egress` rule set — who may drain) and hub's admission-without-law are the same question at two scales: *gateability is not authorization*. A joint answer (who authors rules, where they live, how they're witnessed) prevents two incompatible local answers.

**P3 — the standing roadmap, restated not expanded**

10. DynamoDB validated against real AWS or un-shipped; sqlite proposal storage; Postgres per V2-15/B6; HTTPS convention (V2-17/B10); multi-tenancy (B6); AI role-fillers (V2-13/B8, C1-C4); federation (V3). None of these should start before P0-1 exists — features landing on an unmeasured base is how this corpus got its July.

## 6. Risks and honesty notes

- **This review ran no code.** §2's claims are read-verified with citations; the hub suite's actual pass/fail is unknown until P0-1. Treat every "works" above as "reads as working."
- **The comparison flatters no one if read carefully.** Hestia's legibility lead is real and its transport hole (HST-005) is equally real; the hub's crypto is real and its admission law is theater. The plan is written so each side's strength closes the other's hole rather than so either "wins."
- **The framing question is ducked nowhere.** `hub/README.md`'s "public POC, production elsewhere" versus pilot-ready claims needs dp's disposition, not a code change; it is listed under P0-2's honesty sweep rather than decided here.
- **Scope.** Hestia claims reference merged PRs (#42–#81) and `docs/PRD_ASSURANCE.md`; web4 claims reference commits at ≤`752eadd`. Later work may have moved any of these; the citations are the check.

---

*Placement per repo convention: cross-cutting review/plan documents live in `docs/strategy/` (model: `eudi-resolvability-plan.md`). This document asserts no requirements; P-numbered items are proposals for the respective owners (P1-4 is explicitly HUB's call; P2-7 and P2-9 are joint).*
