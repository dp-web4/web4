# Governance Integration (LRC)

This folder contains a drop‑in pipeline to compute governance controls from L/C/R parameters and inject them into doc front‑matter.

## Files
- `integrations/govsim.py` – computes control tables from `integrations/governance_map.yaml`
- `integrations/integrate_governance.py` – updates target docs' YAML front‑matter with computed controls
- `integrations/governance_map.yaml` – section map (L/C/R + file paths)
- `docs/collab/governance_controls.md|.csv` – generated tables
- `hooks/pre-commit` – optional pre‑commit check (dry‑run)
- `.github/workflows/governance.yml` – CI to compute & upload controls

## Usage
- Dry run: `make gov-check`
- Apply in place: `make gov-apply`
- Rebuild tables: `make gov-tables`

### Front‑matter shape (example)
```yaml
---
title: Core Perspective
governance:
  section: core_perspective
  L: 0.85
  C: 0.20
  R: 0.70
  change_threshold: 0.86
  review_days: 16
  quorum: 4
  token_cost: 60
  reject_penalty: 0.59
  fast_track_drop: 0.03
  last_computed: 2025-08-22T18:45:00Z
---
```

Adjust paths and L/C/R in `integrations/governance_map.yaml` to match your repo.
