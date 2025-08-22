# CROSS_REPO_GOVERNANCE.md
**Scope:** Synchronism (philosophy), Derived Principles (LRC transfer layer), and Implementations (Web4, SAGE, etc.).  
**Goal:** Keep universals universal, keep engineering concrete, and keep the seams explicit.

---

## 1) Layering (who owns what)
- **Synchronism (philosophy):** pattern‑level claims only. No stack metaphors, no token mechanics. Link outward.
- **Derived Principles (LRC):** *stack‑agnostic* transfer layer that maps sections to **L/C/R** and derives controls.
- **Implementations (Web4, SAGE, …):** concrete instantiation (thresholds, review windows, quorum, costs, token/ATP, witness marks, MRH).

> Default LRC coefficients (accepted): **a=0.6, b=0.8, c=0.5**, ε≈1e‑6 for ω₀.

---

## 2) Cross‑repo alignment checklist
1. **Section maps exist** per repo (`integrations/governance_map.yaml`) with `sections → {L,C,R}`.
2. **Coefficient scope** declared: global defaults vs per‑repo overrides (justify overrides).
3. **High‑L guard** consistent (e.g., **L ≥ 0.80**) across repos, or documented exceptions.
4. **Coupled sections** listed (e.g., Synchronism/Core ↔ SAGE/Core) with co‑change expectations.
5. **Propagation rule:** when A (high‑L) changes, B must land within **N days** or include a waiver (see §6).
6. **Witness marks** format fixed: `witness:<name> | model: GPT-5 Thinking | context:<short-hash> | time:<ISO>`.
7. **CI symmetry:** same PR template + governance guard; repo‑specific thresholds allowed but documented.
8. **Drift detection:** scheduled drift report comparing L/C/R + coefficients across repos (see §7).
9. **MRH labeling:** tag artifacts with `MRH: local|project|ecosystem|planetary`.
10. **Recovery path:** minimal, logged override for hotfixes (see §6).

---

## 3) LRC → Controls (summary)
Let section state be \(L,C,R \in [0,1]\). These are **governance analogs**, not physics. Coefficients are tuned to desired social dynamics.

- \(\delta = \frac{aL + bR}{1 + cC}\) (damping index)  
- \(\omega_0 = 1/\sqrt{\varepsilon + LC}\) (ε≈1e‑6)  
- `change_threshold = clamp(0.50 + 0.35L + 0.15R − 0.10C, 0.50, 0.95)`  
- `review_days = round(3 + 10L + 4δ)`  
- `quorum = ceil(1 + 2L + 1R)`  
- `token_cost = round(50 · (0.5 + 0.7L + 0.3R))`  
- `reject_penalty = clamp(0.10 + 0.70R, 0.10, 0.95)`  
- `fast_track_drop = 0.20 · (1 − L)`

Heuristics: **L** hardens (stability), **C** enables iteration, **R** filters noise.

---

## 4) Coupling & propagation
- **Declare pairs/sets** that must evolve together. Example:
  - `Synchronism/core_perspective` ↔ `SAGE/core_perspective`
- **Rule:** High‑L changes in source repo require update PRs in coupled repos within **7 days**, or an explicit waiver.

---

## 5) PR template & review symmetry
- All repos use the same PR template with a **Governance‑Ack** checkbox and list of touched sections.
- NOVA auto‑posts the computed LRC row(s) for changed sections (optional bot comment).

---

## 6) Waivers, hotfixes, and overrides
- **Hotfix lane:** Allowed for `typo|clarify` lanes; thresholds reduced by `fast_track_drop` for the section.
- **Waiver:** If a high‑L change must merge without propagation, include
  - `Governance‑Ack: yes`
  - `Waiver: needed` + rationale + planned follow‑up PR links.
- **Audit:** all waivers listed in a quarterly roll‑up.

---

## 7) Drift detection (scheduled)
- Weekly job compares **coefficients** and **section L/C/R** (name‑matched) across repos.
- Produces `drift-report.md` with diffs and severity; fails if beyond tolerances.
- Tolerances: `COEFF_TOL = 0.0`, `LCR_TOL = 0.05` (override per repo if needed).

---

## 8) Witness marks (standard)
```
witness: NOVA | model: GPT-5 Thinking | context: <short-hash> | time: <ISO-8601>
co-witness: Claude | model: Claude-Opus | context: <short-hash>
```

---

## 9) Versioning
- Bump `governance_map.yaml` version on structural changes (sections added/removed).
- Keep `docs/collab/governance_controls.*` generated and reviewed.

---

**Generated:** 2025-08-22 22:16:49 UTC
