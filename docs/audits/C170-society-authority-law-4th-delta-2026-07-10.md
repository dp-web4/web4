# C170: web4-society-authority-law.md (SAL) — Fourth Delta Re-Audit

**Date**: 2026-07-10
**Auditor**: Autonomous session (legion-web4-20260710-060036)
**Document**: `web4-standard/core-spec/web4-society-authority-law.md` (SAL, 408 lines, byte-frozen at `0d756773`)
**Prior audit**: C134 (`docs/audits/C134-society-authority-law-3rd-delta-2026-07-04.md`, merged `656a8096`, #448)
**Prior remediation**: C59 / PR #330 (`0d756773`) — SAL has not been touched since.

**Lineage**: C16 → C21 → C23 → C58 → C98 → C134 → **C170**.

**Rotation note**: C168 (metabolic 4th-delta, #500) MERGED with 0 autonomous findings → C169 remediation slot was a **declared no-op** (recorded in C168 §C; not manufactured). Rotation advances +2 to SAL.

**Framing**: Fourth delta re-audit of SAL. Target **byte-frozen 25 days** (`git diff 0d756773 origin/main -- <SAL>` empty) and **every SAL-cited sibling frozen since C134** (0 commits each: SOCIETY_METABOLIC_STATES, SOCIETY_SPECIFICATION, r6-framework, errors, entity-types, LCT-linked-context-token). Per the frozen-target discipline, §A = verification and §B is sized to the **moving corpus window** — 65 commits since `656a8096`, whose SAL-relevant movers are: the **NEW `role-extension.{ttl,md}` canonical ontology pair** (promoted `7201a765` on CBP green-light), four remediation-moved spec siblings (mrh C163, acp C159, atp-adp C151, reputation C157), web4-core Rust movers (`lct.rs` #499, `r6.rs` #498, `role_extension.rs`, `society.rs`/`role.rs` Δ2), the hub law surface (`law.rs` +81, `state.rs`, `rest.rs` +777), the **full whitepaper rewrite** (07-09), and 23 interval audit docs (C135–C168) swept for inbound carries.

**Counts**:
- **§A**: C59-rem **10/10 HELD** (trivially — byte-frozen at the exact HEAD C98/C134 verified), 0 regressed, 0 encoding artifacts, 0 mirror drift (all cited siblings frozen). All standing carries re-verified OPEN.
- **§B**: **0 net-new defects on SAL itself** — 3rd consecutive fully-clean SAL delta (C98 + C134 + C170). **1 net-new corpus-window finding** (C170-N1, LOW, guidance-file): project `CLAUDE.md:48` cites the whitepaper glossary at `whitepaper/sections/02-glossary/index.md`, a path DELETED by the 07-09 rewrite (glossary now at `13-glossary`). Three carry facets recorded (B15 widened; C16-M8/B6 strengthened; C33 canon-side pick), each adjudicated below.
- **§C**: C170-N1 = autonomous-actionable at the **C171 SAL-remediation slot** (guidance file, not spec; kept out of this zero-mutation turn). All DESIGN-Q / cross-track carries STAND, route to the standing operator memo.

---

## §A. Prior-Finding Verification (live evidence at frozen HEAD `0d756773`)

### A.1 — C59 remediation #330 HELD (10/10)

SAL is **byte-identical** to the HEAD at which C98 verified all 10 C59 edits present-and-unregressed and C134 re-confirmed (`git diff 0d756773 origin/main -- <SAL>` = empty). No edit could have regressed because no byte changed. Regression sweep: `grep -c "&#"` → 0. The C98 site-table stands verbatim.

### A.2 — Mirror movement since the C134 snapshot (`656a8096`, 2026-07-04)

**Every sibling SAL cites by name is frozen since C134** (`git log 656a8096..origin/main -- <path>` = 0 commits, verified individually for all six):

| SAL-cited sibling | Commits since C134 | Status |
|-------------------|--------------------|--------|
| `SOCIETY_METABOLIC_STATES.md` (§3.6) | 0 | frozen — B10/M3 carries stable; C168 (4th-delta, #500) confirmed clean |
| `SOCIETY_SPECIFICATION.md` (§1.4 back-ref) | 0 | frozen — L1-residual stable; C164 (4th-delta, #493) confirmed clean |
| `r6-framework.md` (§3.6, §6 mapping) | 0 | frozen — B11/B12 stable |
| `errors.md` (§9 codes) | 0 | frozen — C16-H1-remainder stable |
| `entity-types.md` (§2.2/§5.1 mirror) | 0 | frozen — B13/B14 convergence held |
| `LCT-linked-context-token.md` (birth-cert) | 0 | frozen — C23-H1 stable |

Zero mirror drift; the C98 mirror-convergence results stand as verified.

### A.3 — Still OPEN (re-verified; all frozen-side anchors stable → carries STAND)

All carries from the C134 §A.3 ledger re-verified. The frozen sides are trivially stable (0 commits); the LIVE sides checked this turn:
- **C16-M8 / B6** (`hub-law.ttl` namespace): `hub-law.ttl` **frozen since C134** (0 commits) — still `@prefix web4: <https://web4.io/ontology/>` (trailing slash) + `law:hash`, vs SAL §7.2 `ontology#` + `web4:hash`; `sal-ontology.ttl` still absent from canonical `web4-standard/ontology/`. Carry STANDS — **strengthened** this window, see §B.1.
- **C58-B10** (dormant-defer vs new_citizen wake): both SAL §3.6 L141 and SMS §4.1 frozen → two-sided contradiction stands.
- All other C58/C23/C16 design-Q and cross-track items (C23-H1+B1, C23-M3, C23-L2, C16-M1+B7, C16-M3, C16-M4/M5, C16-M6, B8, B9, B11, L1-residual): referent files all frozen; carries STAND verbatim per the C134 §A.3 table. New facets on B7, C16-M1, C16-M4/M5 recorded in §B (all echo/facet-class, none re-adjudicated as net-new).

---

## §B. C170 Moving-Window Adjudication + NEW Findings

**Method**: No finder pass over unchanged SAL prose. Each moved surface adjudicated against SAL's citation/normative surface with refute-by-default; the flagship candidate (role-extension fold vs SAL §3.5) was given the full adversarial treatment per the refute-your-best-finding discipline. Sweeps run: (i) whitepaper-rewrite SAL-term sweep (all 14 new sections), (ii) 23-doc inbound-carry sweep, (iii) remediated-mover carry-scan reading remediation RATIONALE per the C140 rule.

### B.1 — NEW canonical ontology pair `role-extension.ttl` + `role-extension-schema.md` (promoted `7201a765`) — 0 net-new; 3 carry facets

The pair defines machine-readable **law attached to an orchestration Role-entity's LCT**, composing under society + constellation law via `fold_strictest` (strictest-wins, tighten-only). Direct conceptual adjacency to SAL (law + roles) — adjudicated in depth:

1. **Law-composition model vs SAL §3.5 (flagship candidate — REFUTED as contradiction, recorded as B15 facet).** The charge would be: `fold_strictest(society, constellation)` never lets a lower level override a higher one, while SAL §3.5 normatively ranks "explicit child overrides with parent awareness flag" ABOVE "parent norms". Refutation: (a) SAL §3.5's override channel is permission-shaped — "override **only by** explicit Interpretation or Norm with higher or equal authority and no parent hard-conflict" states *necessary* conditions, not an obligation to admit overrides; an implementation that admits none violates no MUST. (b) SAL's own Inheritance Rule is `merge(parentLaw, childOverrides) with conflictPolicy` where `conflictPolicy` is machine-readable and society-chosen — strictest-wins IS a conflictPolicy. (c) The role_extension overlay itself is **role-level** law (SAL §5.2 already requires Authority to "publish scope and limits as machine-readable policy"; `web4:scope` §7.1 — same pattern), a different axis from §3.5's child-*society* inheritance. **However**, the society∧constellation leg of the fold is genuinely inter-*level* law composition under a **third model** (strictest-wins / no-override-admitted), alongside SOCIETY_SPEC §3.2.1 ("extend not contradict") and SAL §3.5 (child-override-ranked-above-parent). → **C50-B15 (law-inheritance model DESIGN-Q) WIDENED with a third site**: `role-extension-schema.md` §2.1. Re-adjudicated against the new site's own constraints (per the path-provenance lesson): the new site is arguably role-axis not society-axis, so the widening carries that caveat; the operator's B15 answer should now settle all three models' domains at once. Routed, not self-applied.
2. **Ontology namespace (C16-M8/B6 facet — carry STRENGTHENED, with a C162-N2 qualifier).** `role-extension.ttl:1` declares `@prefix web4: <https://web4.io/ontology#>` — the **hash** form, byte-matching SAL §3.3/§7.2. The canonical `web4-standard/ontology/` directory now holds two files split 1–1: `hub-law.ttl` (trailing-slash `ontology/`) vs `role-extension.ttl` (hash `ontology#`), with SAL on the hash side making it 2-vs-1 corpus-wide. **Qualifier (honesty per C162-N2)**: the `web4:` prefix in role-extension.ttl is *declared but never used* — grep count 1, the declaration itself; C162 already routed this RDF-island defect (unused prefix, no `role:`→`web4:` links, `role:driftMark` missing `rdfs:domain`) to the role-extension owner, so the agreement with SAL is declaration-level evidence of the author's namespace choice, not used-triple evidence, and the island defect is NOT re-raised here. The divergence class is already ledgered (C16-M8/B6); the new fact stands: the slash-vs-hash inconsistency is now **internal to the canonical ontology directory itself**, no longer explainable as a single stray file. Facet recorded on the carry; NOT net-new; NOT incremented (subordinate-ontology cluster BC-C23-3). Note the subordinate namespace `role: <https://web4.io/ontology/role/>` repeats hub-law's `law:` subordinate-slash pattern — same cluster.
3. **Role taxonomy (B7 / C16-M1 echo site — not net-new).** Schema L26-27: "the 7 base-mandatory (+ Witness/Auditor context-mandatory)" — verified a **faithful echo of `society-roles.md`** (§1.1/§1.2 three-tier model; §2 lists exactly 7 base-mandatory: Sovereign, Law Oracle, Policy-Entity, Treasurer, Administrator, Archivist, Citizen; Witness/Auditor context-mandatory per §3). The divergence vs SAL's unconditional MUSTs (§7.1.1 `hasWitness`/`hasAuditor` required triples; §11 discovery MUST expose them) is exactly standing carry **B7** — the new doc adds an echo site, not a new defect. Snapshot-presence guard honored: the tiering pre-exists the window.
4. **Law-Oracle serving (CONSISTENT).** Schema §2.4: "HUB owns the Law-Oracle serving endpoint"; society law arrives as a served document folded locally on cached-but-fresh law, stale ⇒ fail-closed. Publisher-role sense of Law Oracle (SAL §5.3 "Publishes law datasets; answers queries") + the pin-and-verify staleness posture of SAL §4.2. No C50-B13 aggravation (single-sense usage).
5. **INFO (route to ontology-track/operator, not a SAL finding):** `role-extension-schema.md` carries forum-memo genre into the canonical directory — frontmatter `from: Legion`, `thread: hestia-role-orchestration`, closing "Open for HUB react", and a personal reference ("the thing dp asked to 'define, staff, assign an agent to'"). Promotion provenance is properly documented (CBP green-light + ratified concord), but the artifact reads as correspondence, not a standard. Whether canonical ontology docs should be re-genred at Phase-1 is an owner/operator call.

### B.2 — web4-core `lct.rs` (#499, canonical-schema half) — 0 net-new; 1 positive convergence; 1 carry facet

1. **Positive convergence:** the new `Mrh` struct (`lct.rs:135-152`) carries exactly `{bound, paired, witnessing}` (+ `horizon_depth`) — **byte-matching SAL §14.1's schema stub** `"mrh": {"bound": [], "paired": [], "witnessing": []}`. The deployed canon adopted SAL's three-key MRH shape.
2. **C33 id-scheme facet:** `derive_lct_id` (`lct.rs:190-201`) formalizes the **key-derived** form `lct:web4:mb32:b<base32(sha256(pubkey))>` — one of the two forms already ledgered in the C33 cluster ("`lct:web4:` 635-occ undefined + 2 forms"). SAL's examples (§2.2 L49-52, §5.5 L209-211, §14 L380/L390-392) remain the **typed-path** form (`lct:web4:role:citizen:...`). The window's new fact: the two-forms divergence now has a **deployed canon-side pick**, which raises the cost of leaving SAL's example strings unresolved. Facet recorded on the C33 bundle (where SAL's example strings already sit via the 635-occ sweep); NOT net-new.
3. `binding_proof` (entity binding key over a domain-separated binding message) is a different object from SAL §2.3's birth-certificate signature (society's binding authority key + witness co-signatures) — disjoint, no interaction. **C23-H1 (birth-cert 3-way) unchanged**: #499 does not define a birth-certificate structure (the only touchpoint is the `MrhEdge.edge_type` example string `"birth_certificate"`); both spec sides frozen.

### B.3 — hub `law.rs` / `state.rs` / `rest.rs` — 0 net-new; 1 positive; 2 facets/INFO

1. **Positive:** H-009/HUB-001 law-integrity machinery (`rest.rs`) — served-law hash compared against the newest witnessed `LawAmended` ledger event; mismatch ⇒ warning + **fail-closed write gate**. This is a faithful first deployment of SAL §4.2 ("cache and pin the `hash` per society to detect downgrade/replay") and the §9 `W4_ERR_PROTO_DOWNGRADE` abort posture.
2. **C16-M4/M5 hub facet (route-only):** hub's ledger event vocabulary (`HubEvent::LawAmended`) vs SAL §3.4's event topics (`sal.law.update` et al.) — same carry class as the SDK half; recorded as a hub-side data point WITHOUT extending the carry's prescription to the new site (path-provenance discipline: the hub's constraints differ; adjudication belongs to whoever answers C16-M4/M5).
3. **INFO (hub-owned):** `HUB_ALLOW_LAW_MISMATCH=1` downgrades the fail-closed law-integrity write gate to warn-and-proceed. A deliberate, documented dev escape; flagged to the hub owner as an operational-posture question against SAL §4.2/§9, not asserted as a defect.
4. **C16-M1 NOT aggravated:** `law.rs` adds `KNOWN_CONSTELLATION_ROLES` (5 session-capacity roles) — explicitly "a distinct namespace from `KNOWN_ROLES` (the Web4 *society* roles)", with a test enforcing zero overlap (`constellation_roles_are_a_separate_namespace_from_society_roles`). A fourth role vocabulary, but disjoint-by-design and test-guarded; C16-M1 remains scoped to society-role taxonomy.
5. `state.rs` sovereign_strength weakest-wins fold = the existing **C156-3** carry surface maturing; no SAL interaction (SAL has no attestation-strength surface).

### B.4 — Four remediation-moved spec siblings — all DISJOINT (carry-scan, rationale read per C140)

| Mover (Δ) | Remediation | Verdict vs SAL |
|---|---|---|
| `mrh-tensors.md` (Δ14, C163) | §4.2 note: "Two"→"Three" SDK API differences, descriptive-only | **DISJOINT** — SAL's only propagation surface (L104 SPARQL-edges MUST) has no dependency on SDK propagation signatures |
| `acp-framework.md` (Δ9, C159) | grant caps path fix; "reputation stakes"→future-mechanism note; WitnessDeficit cite fix | **DISJOINT ×3** — SAL has no agency-grant surface (0 `grant` hits); §5.5 caps are auditor-volatility caps, untouched; hunk 2 in fact moves acp's trust-gaming mitigation to rest entirely on the SAL-specified audit-adjustment mechanism (alignment improved) |
| `atp-adp-cycle.md` (Δ2, C151) | conservation-invariant scope label "ATP→ADP"→"between entities (§6.3)" | **DISJOINT** — adjudicated strictly on SAL's own ATP surfaces (LAW-ATP-LIMIT L165 per-action cap norm; §6 Resource row): neither cites conservation/transfer/fees. The C166 definition-site reservation remains atp-adp-owned; NOT inherited here |
| `reputation-computation.md` (Δ2, C157) | Sybil item 4 softened to SHOULD + not-yet-specified pointer | **DISJOINT** — SAL §10/L229 within-role-context surfaces assert nothing about pattern/anomaly analysis (0 token hits) |

### B.5 — Whitepaper full rewrite (07-09) — CONSISTENT/DISJOINT; 1 net-new byproduct (C170-N1)

Sweep of all 14 new sections for SAL-owned terms: **zero contradictions**. "Law Oracle", "birth certificate", "citizenship", "quorum", "auditor" appear NOWHERE in the new reader-facing sections — the rewrite compresses SAL to a half-page pattern (`10-composed-architecture:30-42`, consistent with SAL §4/§6, with a correct normative pointer to `web4-society-authority-law.md`) plus five consistent glossary entries (`13-glossary:29-37`). SAL cites the whitepaper nowhere (0 hits), so no SAL-side reference could break. C50-B13 (Law-Oracle name collision) now has **no whitepaper surface at all** — neither sense used; remains intra-spec-corpus. The glossary calling SAL a "governance pattern" vs the spec's "layer" is cosmetic.

**C170-N1 (LOW, guidance-file, autonomous-actionable — NET-NEW):** project **`CLAUDE.md:48`** instructs "check glossary (`whitepaper/sections/02-glossary/index.md`)" — that path was **deleted by the 07-09 rewrite** (verified: dir absent; glossary now at `whitepaper/sections/13-glossary/index.md`; pre-rewrite tree archived under `whitepaper/archive/sections-2026-07-09-pre-rewrite/`). Every future session following the terminology-protection instruction dereferences a dead path. Born in-window (the referent vanished 07-09); NEW (no prior audit ledgers it; the 07-09 leftover-repair commit `3bcd4ffa` fixed nav + build artifacts only) and TRUE (refutation attempted: archive copy exists but at a different path; no open PR fixes it). **Fix = one-line path update, owned by the C171 SAL-remediation slot** (kept out of this zero-mutation audit turn). Historical artifacts (`whitepaper/reorganize.sh`, `WHITEPAPER_REVIEW_2026-01-26.json`) also reference the old path but are archival — no action.

### B.6 — Inbound cross-doc carries (23 interval audit docs C135–C168)

{{INBOUND}}

---

## §C. Autonomous / Design-Q / Cross-Track Split (routing for the C171 remediation slot)

**Autonomous-actionable (→ C171 SAL-remediation slot): ONE item — C170-N1** (`CLAUDE.md:48` glossary path `02-glossary`→`13-glossary`; guidance file, no spec mutation, no operator gate). C171 is therefore **NOT a no-op** this cycle.

**Carry updates recorded this turn (all route to the standing operator memo; none self-applied):**
- **C50-B15 WIDENED**: third law-composition model site (`role-extension-schema.md` §2.1 strictest-wins/no-override), with the role-axis caveat (§B.1.1).
- **C16-M8/B6 STRENGTHENED**: namespace split now internal to canonical `web4-standard/ontology/` (hub-law.ttl slash vs role-extension.ttl hash, 1–1; SAL makes it 2–1 hash). Substance unchanged; cluster BC-C23-3 not incremented.
- **C33 facet**: deployed canon-side pick of the key-derived `lct:web4:mb32:` form (`lct.rs:190`); SAL example strings remain typed-path form.
- **C16-M4/M5 hub facet**: `HubEvent::LawAmended` vs `sal.law.update` topic vocabulary (route-only, no prescription).
- **B7 / C16-M1**: echo site only (role-extension-schema restates society-roles tiering); carries stand unchanged.

**INFO (routed, no SAL action):** role-extension-schema.md forum-memo genre in canonical dir (→ ontology-track/operator); `HUB_ALLOW_LAW_MISMATCH=1` posture question (→ hub owner).

**Positive movements logged:** hub law-integrity gate implements SAL §4.2/§9; Rust `Mrh` adopts SAL §14.1's exact three-key shape; acp C159 hunk 2 increases SAL-alignment.

---

## §D. Lessons

1. **A NEW file entering the corpus is where a frozen-target audit's §B yield lives.** SAL and every cited sibling were frozen, yet the window still produced one net-new finding and four carry movements — all from surfaces that didn't exist (role-extension pair) or were rewritten wholesale (whitepaper) since the last delta. The rotation's frozen-target pattern (now 3 consecutive clean SAL deltas) holds for the target; it says nothing about the window.
2. **A new sibling AGREEING with the target strengthens a divergence carry as much as a new disagreement would.** role-extension.ttl siding with SAL's hash namespace didn't resolve C16-M8/B6 — it converted "one file diverges from the spec" into "the canonical ontology directory disagrees with itself", which is a stronger operator prompt with zero new defect surface.
3. **Refuting the flagship can still yield the audit's most useful routing.** The fold-vs-§3.5 contradiction died under refutation (permission-shaped override channel + conflictPolicy is society-chosen + axis mismatch), but the refutation work itself surfaced the real item: B15 now has three competing law-composition models on record, and the operator's single answer can settle all three domains.
4. **Guidance files are corpus too.** The whitepaper rewrite was spec-clean but silently broke the repo's own terminology-protection instruction (CLAUDE.md:48). A sweep that stops at `web4-standard/**` would have missed the one actionable defect in the window.

---

*End of C170 audit. Zero mutation this turn. C170-N1 routes to the C171 SAL-remediation slot (one-line guidance fix). Next rotation target after C171: rotation advances +2 from SAL per the fixed order (SAL → LCT), i.e. **C172 = LCT-linked-context-token.md** next delta (lineage C9→C24→C60→C100→C135→C172).*
