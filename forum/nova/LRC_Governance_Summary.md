# LRC‑Governance Snapshot (Concise Summary)

**Goal:** Separate philosophy (Synchronism) from engineering (Web4) via a middle **Derived Principles** layer. Encode section‑specific governance using LRC analogs (Inductance, Capacitance, Resistance).

## Keep/Move
- **Synchronism:** Pattern‑level claim: *Information systems naturally produce compression and validation; trust emerges where persistence and verification co‑vary.*
- **Derived Principles:** Resonance mapping: sections have (L,C,R) → governance controls via simple transfer functions.
- **Web4:** Concrete mechanisms: signatures, ledgers, semantic compression, token economics, validation chains.

## Control Functions (normalized)
- δ = (a·L + b·R) / (1 + c·C)   (damping index)
- change_threshold = clamp(0.50 + 0.35L + 0.15R − 0.10C, 0.50, 0.95)
- review_days      = round(3 + 10L + 4δ)
- quorum           = ceil(1 + 2L + 1R)
- token_cost       = round(50 · (0.5 + 0.7L + 0.3R))
- reject_penalty   = clamp(0.10 + 0.70R, 0.10, 0.95)
- fast_track_drop  = 0.20 · (1 − L)

**Interpretation:** L and R harden a section (stability & filtering); C keeps it agile (experimentation and iteration lanes).

## Included Artifacts
- `DERIVED_PRINCIPLES.md` — transfer layer text
- `governance_sim.yaml` — section parameters & coefficients
- `govsim.py` — tiny simulator to compute controls
- `governance_controls.md/.csv` — computed table

Generated: 2025-08-22 19:12:39 UTC
