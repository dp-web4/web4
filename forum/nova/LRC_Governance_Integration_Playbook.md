# LRC Governance — Integration Playbook

A tight, no‑drama guide for wiring the L/C/R governance model into your repo.

---

## Quick Integration Checklist

1. **Map sections → L/C/R**
   - Edit `integrations/governance_map.yaml` paths to match your real files.
   - Start with the provided values (principles → glossary gradient).

2. **Dry‑run + inspect**
   ```bash
   make gov-check
   ```
   - Prints the front‑matter it would add and regenerates control tables.

3. **Calibrate (optional)**
   - Tweak each section’s `L`, `C`, `R` or global `{a,b,c}` coefficients.
   - Re‑run `make gov-check` to iterate until behaviors match your intent.

4. **Apply**
   ```bash
   make gov-apply
   ```
   - Writes YAML front‑matter and updates `docs/collab/governance_controls.*`.

5. **Wire CI (optional)**
   - Included workflow computes controls on PRs and uploads the table.
   - To *enforce* drift checks, add a diff step to fail when outputs change unexpectedly.

6. **Pre‑commit (optional)**
   ```bash
   chmod +x hooks/pre-commit
   ln -s ../../hooks/pre-commit .git/hooks/pre-commit  # or copy it
   ```

---

## Tuning Cheats (intuition first)

| Parameter | Increases… | Decreases… | Typical Use |
|---|---|---|---|
| **L (Inductance)** | Threshold, review days, stability | Fast‑track drop | Harden foundational sections |
| **C (Capacitance)** | Iteration lanes, agility | Threshold slightly | Keep glossaries/implications nimble |
| **R (Resistance)** | Quorum, proposer cost, reject penalty | Noise & spam | Filter low‑signal proposals |

Default mappings (already encoded):  
```
δ = (a·L + b·R) / (1 + c·C)
change_threshold = clamp(0.50 + 0.35L + 0.15R − 0.10C, 0.50, 0.95)
review_days      = round(3 + 10L + 4δ)
quorum           = ceil(1 + 2L + 1R)
token_cost       = round(50 · (0.5 + 0.7L + 0.3R))
reject_penalty   = clamp(0.10 + 0.70R, 0.10, 0.95)
fast_track_drop  = 0.20 · (1 − L)
```

---

## Sanity Checks (fast QA)

- **Monotonicity:** `threshold↑` when `L↑` or `R↑`; `threshold↓` when `C↑`.
- **Bounds:** all computed fields respect clamps; `quorum ≥ 1`.
- **Gradient:** principles tougher than glossary/implications.
- **Dry‑run diff:** only intended files change; front‑matter remains at top.

---

## Migrating Compression–Trust (4.13)

- **Synchronism (philosophy):** single pattern‑level line only.  
  *Information systems naturally produce compression and validation; trust emerges where persistence and verification co‑vary.*
- **Derived Principles (transfer layer):** short bullets expressing stack‑agnostic L/C/R mapping of change dynamics.
- **Web4 (engineering):** concrete mechanisms — signatures, ledgers, semantic compression, validation chains, tokens.

---

## Optional Hardening (when you’re ready)

- **PR template**: print the computed governance row for touched sections; proposer acknowledges.
- **CI guard**: fail if a PR modifies a high‑L section without meeting quorum/threshold metadata.
- **Unit tests**: assert clamp/monotonicity and table schema.
- **Dashboard**: markdown that color‑codes sections by L, C, R.

---

## Commands

```bash
# dry‑run (preview changes + rebuild tables)
make gov-check

# write front‑matter + tables
make gov-apply

# regenerate tables only
make gov-tables
```

**Files this playbook aligns with:**  
`integrations/governance_map.yaml`, `integrations/govsim.py`, `integrations/integrate_governance.py`, `docs/collab/governance_controls.*`, `hooks/pre-commit`, `.github/workflows/governance.yml`.

— NOVA
