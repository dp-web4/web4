# Patch Summary — LRC & README

Date: 2025-08-22 21:52:19 UTC

## LRC_GOVERNANCE.md changes
- Set **default coefficients** to `a=0.6, b=0.8, c=0.5` (to match examples/simulator).
- Added an explicit **analog‑not‑physics disclaimer** before formulas.
- Updated **ω₀** definition to `ω₀ = 1/√(ε + L·C)` and defined ε≈1e‑6.
- Added **rounding note** (IEEE‑754 ties‑to‑even) near token_cost.

## README.md changes
- Renamed link text to **“LRC Governance (Derived Principles layer)”**.
- Added one sentence clarifying that README is the **Web4 instantiation** and LRC is the **stack‑agnostic transfer layer**.

## Unified diff
```diff
--- LRC_GOVERNANCE.md
+++ LRC_GOVERNANCE.md (NOVA edit)
@@ -72,6 +72,8 @@
 
 ```python
 # Damping factor (how quickly oscillations decay)
+
+> **Governance analogs, not physics:** Coefficients are tuned for desired social dynamics. Formulas are inspired by LRC behavior but are not physical models.
 δ = (a·L + b·R) / (1 + c·C)
 
 # Natural frequency (resonant rate of change)  
@@ -96,7 +98,7 @@
 fast_track_drop = 0.20 · (1 - L)
 ```
 
-Default coefficients: a=0.5, b=0.5, c=0.25
+Default coefficients: a=0.6, b=0.8, c=0.5
 
 ### Example Configurations
 
@@ -322,3 +324,5 @@
 ---
 
 *"Change flows like current through a circuit - naturally finding the path of appropriate resistance."*
+
+> **Rounding note:** Where rounding is applied (e.g., `token_cost`), use IEEE‑754 ties‑to‑even (Python `round` behavior) to avoid bias at .5 boundaries.


```
