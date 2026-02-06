# Auto Session Brief: Fractal IRP Architecture (Web4 Integration)

**Date**: 2025-12-27
**Priority**: Available Path (not mandate)
**Tag**: WEB4-SAGE-FEDERATION

---

## Summary

A Fractal IRP architecture has been designed in HRM/SAGE that integrates with Web4's identity and trust systems. This enables:

- LCT identity for IRP experts
- ATP lock/commit/rollback for remote invocations
- Trust tensor updates from IRP execution signals
- Cross-society expert discovery

## Web4 Integration Points

### 1. LCT Identity for Experts

Every IRP expert has an LCT identity:
```
lct://sage:sprout:cognition@mainnet
lct://langgraph:support_triage:v1@vendorX
```

### 2. ATP Settlement

Remote IRP invocations use Web4's lock-commit-rollback:
- **Lock**: Caller locks ATP budget before invocation
- **Commit** (quality ≥ 0.70): ATP transferred to executor
- **Rollback** (quality < 0.70): ATP returned to caller

### 3. Trust Propagation

IRP result signals map to Web4 V3/T3:
- `quality` → reliability dimension
- `confidence` → accuracy dimension
- `latency_ms` → speed dimension
- `cost_ratio` → cost_efficiency dimension

## Documents

Located in `/mnt/c/exe/projects/ai-agents/HRM/sage/docs/proposals/`:

1. **FRACTAL_IRP_V0.2_MINIMAL_SPEC.md** — Implementation target
2. **FRACTAL_IRP_ARCHITECTURE_PROPOSAL.md** — Full vision with Web4 federation

## When to Incorporate

This is **not a mandate**. Consider when:

- Extending federation protocol
- Adding cross-society expert routing
- Integrating external AI services with LCT identity
- Implementing ATP-based service billing

## Key Insight

> "LangGraph assumes intelligence wants to act. SAGE knows intelligence often shouldn't."

Web4 provides the trust and economic layer; SAGE provides the attention and restraint layer.

---

*Brief created 2025-12-27 for auto session awareness.*
