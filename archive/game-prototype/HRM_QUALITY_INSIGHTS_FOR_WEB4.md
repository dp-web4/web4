# HRM Quality-Aware Selection: Insights for Web4

**Date**: November 25, 2025 (Session #72)
**Source**: HRM `quality_aware_edge_experiment.py`
**Relevance**: Resource allocation, ATP costing, MRH profiles, V3 veracity

## Executive Summary

HRM's quality-aware plugin selection experiment reveals a **critical design principle for Web4**: **Quality requirements should be hard constraints, not soft optimization goals**.

**Key Finding**: MRH-only selection achieved 95% ATP savings but **67% quality failure rate**. Quality-aware selection achieved **0% failures** at 7x ATP cost.

**Implication for Web4**: When allocating ATP for critical operations (insurance claims, authorization decisions, cross-society coordination), **quality must gate selection**, not just optimize cost.

---

## Experimental Results

### Setup

**3 Plugin Options** (all at same MRH horizon: local/session/agent-scale):
- `qwen-0.5b`: Quality 0.70, Cost 10 ATP
- `qwen-7b`: Quality 0.90, Cost 100 ATP
- `cloud-gpt`: Quality 0.95, Cost 200 ATP

**12 Test Queries**:
- 4 simple (min quality 0.50)
- 4 medium (min quality 0.75)
- 4 complex (min quality 0.90)

### Baseline: MRH-Only Selection (Experiment 3)

**Strategy**: Minimize ATP cost within MRH horizon

**Results**:
- Total ATP: **120**
- Plugin: `qwen-0.5b` for all 12 queries (cheapest option)
- Quality failures: **8/12 (67%)**
  - All medium queries failed (0.70 < 0.75 required)
  - All complex queries failed (0.70 < 0.90 required)

**Problem**: MRH horizon matching doesn't encode quality requirements. Cost optimization dominates, leading to systematic underperformance.

### Quality-Aware Selection

**Strategy**: Filter by quality first, then minimize ATP cost

**Algorithm**:
```python
def select_plugin_with_quality_edge(
    query, quality_required, plugins, trust_scores, atp_costs, atp_budget=None
):
    # Step 1: Filter to qualified plugins
    qualified = [p for p in plugins if trust_scores[p] >= quality_required]

    if not qualified:
        raise NoQualifiedPluginError()

    # Step 2: Filter by ATP budget if specified
    if atp_budget:
        affordable = [p for p in qualified if atp_costs[p] <= atp_budget]
        if not affordable:
            raise InsufficientATPBudgetError()
        qualified = affordable

    # Step 3: Select cheapest qualified plugin
    selected = min(qualified, key=lambda p: atp_costs[p])
    return selected, atp_costs[selected], "quality_then_cost"
```

**Results**:
- Total ATP: **840** (+600% vs baseline)
- Quality failures: **0/12 (0%)**
- Plugin usage: `qwen-0.5b` (4), `qwen-7b` (8)
- **Key**: Correct plugin selection based on query complexity

**Trade-off Analysis**:
- ATP cost increased 7x (120 → 840)
- Quality compliance improved from 33% → 100%
- **Conclusion**: On edge devices, quality failure cost exceeds ATP cost

### Budget-Constrained Quality-Aware

**Strategy**: Quality gates with ATP budget hard constraint

**Budget**: 50 ATP/query (vs 100 needed for medium/complex)

**Results**:
- Queries within budget: 4/12 (simple queries only)
- Budget violations: 8/12 (**fail fast**, no compromises)
- Total ATP used: **40** (only for successful queries)

**Edge Philosophy**: Better to **fail fast with clear error** than succeed with degraded quality.

### Auto Quality Inference

**Strategy**: Infer quality requirement from query text, then apply quality-aware selection

**Quality Inference**:
```python
def infer_quality_requirement(text):
    # Simple heuristic based on query characteristics
    if any(word in text.lower() for word in ["analyze", "explain", "comprehensive"]):
        return 0.85  # Complex
    elif any(word in text.lower() for word in ["describe", "summarize", "how"]):
        return 0.70  # Medium
    else:
        return 0.50  # Simple
```

**Results**:
- Total ATP: **480** (optimal balance)
- Quality successes: 12/12
- Plugin usage: `qwen-0.5b` (8), `qwen-7b` (4)
- **40% more efficient** than explicit quality requirements

---

## Implications for Web4

### 1. ATP Allocation Must Encode Quality Requirements

**Current Web4 State** (Session #68 MRH profiles):
```python
ATP_COSTS = {
    ("local", "session", "simple"): 5,
    ("local", "session", "agent-scale"): 15,
    ("regional", "session", "society-scale"): 50,
    ("regional", "epoch", "society-scale"): 75,
}
```

**Problem**: No quality encoding! Two operations at same MRH horizon cost the same ATP, regardless of quality requirements.

**HRM Insight**: MRH dimensions (deltaR, deltaT, deltaC) describe **scope**, not **quality**. Need separate quality dimension.

**Proposed Enhancement**:
```python
ATP_COSTS = {
    # (spatial, temporal, complexity, quality)
    ("local", "session", "simple", "low"): 5,
    ("local", "session", "simple", "high"): 10,      # 2x cost for quality
    ("local", "session", "agent-scale", "low"): 15,
    ("local", "session", "agent-scale", "high"): 30, # 2x cost for quality
    ("regional", "session", "society-scale", "low"): 50,
    ("regional", "session", "society-scale", "high"): 100,  # 2x cost
}
```

**Quality Levels**:
- **Low** (0.5-0.7): Approximate, cached, best-effort
- **Medium** (0.7-0.85): Validated, recent, reliable
- **High** (0.85-1.0): Cryptographically verified, multi-witness, critical

### 2. V3 Veracity Maps to Quality Requirements

**V3 Veracity** (Session #71):
- Range: 0.0 to 1.0
- Measures: Truthfulness, accuracy, reproducibility
- Updates: External validation and witness attestation

**Connection to HRM Quality**:
```python
# V3 veracity determines minimum quality threshold
if operation.criticality == "high":
    min_quality = 0.90  # Insurance claims, authorization
elif operation.criticality == "medium":
    min_quality = 0.75  # Cross-society coordination
else:
    min_quality = 0.50  # Best-effort operations

# Select agent/plugin with V3 veracity >= min_quality
qualified_agents = [
    a for a in agents
    if a.value_axes["V3"]["veracity"] >= min_quality
]
```

**Example**:
```python
# Insurance claim processing (critical operation)
def process_insurance_claim(claim, insurance_pool, agents):
    # Quality requirement: 0.90 (high veracity needed)
    auditors = [
        a for a in agents
        if a.value_axes["V3"]["veracity"] >= 0.90
    ]

    if not auditors:
        raise NoQualifiedAuditorError("No agent meets veracity requirement 0.90")

    # Select cheapest qualified auditor
    selected = min(auditors, key=lambda a: a.atp_cost)
    return selected.audit(claim)
```

### 3. Fail-Fast Better Than Degraded Quality

**HRM Finding**: Budget-constrained selection fails fast rather than compromising quality.

**Web4 Application**: Treasury operations, role bindings, insurance claims

**Current Problem** (speculative):
```python
# Anti-pattern: Degrade quality to stay within budget
def bind_role(society, agent, role, atp_budget):
    if high_quality_verification_cost > atp_budget:
        # BAD: Silently use low-quality verification
        use_cached_trust_score(agent)  # Might be stale!
    else:
        verify_agent_trustworthiness(agent)
```

**HRM-Inspired Solution**:
```python
# Pattern: Fail fast with clear error
def bind_role(society, agent, role, atp_budget, min_quality=0.85):
    verification_cost = estimate_verification_cost(agent, min_quality)

    if verification_cost > atp_budget:
        raise InsufficientATPBudgetError(
            f"Role binding requires {verification_cost} ATP (quality {min_quality}), "
            f"but budget is {atp_budget}. Increase budget or reduce quality requirement."
        )

    # Proceed with quality-assured verification
    verified = verify_agent_trustworthiness(agent, min_quality)
    if verified.v3_veracity >= min_quality:
        society.bind_role(agent, role)
```

### 4. Quality Inference from Operation Type

**HRM Pattern**: Automatically infer quality requirements from query text.

**Web4 Mapping**: Infer quality from operation type

```python
OPERATION_QUALITY_REQUIREMENTS = {
    # Critical operations (high veracity)
    "insurance_claim": 0.90,
    "role_binding": 0.85,
    "treasury_transfer": 0.90,
    "cross_society_authorization": 0.90,

    # Important operations (medium veracity)
    "audit_request": 0.75,
    "reputation_update": 0.75,
    "federation_join": 0.80,

    # Routine operations (low veracity)
    "event_logging": 0.50,
    "cache_update": 0.50,
    "metrics_collection": 0.60,
}

def get_quality_requirement(operation_type):
    return OPERATION_QUALITY_REQUIREMENTS.get(operation_type, 0.75)  # Default medium
```

### 5. ATP Cost Model with Quality Multiplier

**Proposed Formula**:
```python
def calculate_atp_cost(mrh_profile, quality_level):
    # Base cost from MRH dimensions
    base_cost = get_base_cost(
        mrh_profile["deltaR"],
        mrh_profile["deltaT"],
        mrh_profile["deltaC"]
    )

    # Quality multiplier
    quality_multipliers = {
        "low": 1.0,      # 0.5-0.7 veracity
        "medium": 1.5,   # 0.7-0.85 veracity
        "high": 2.0,     # 0.85-1.0 veracity
        "critical": 3.0  # 0.95+ veracity with multi-witness
    }

    multiplier = quality_multipliers.get(quality_level, 1.5)
    return base_cost * multiplier
```

**Example**:
```python
# Low-quality local operation
cost_low = calculate_atp_cost(
    {"deltaR": "local", "deltaT": "session", "deltaC": "simple"},
    quality_level="low"
)  # 5 ATP

# High-quality local operation (same scope, higher quality)
cost_high = calculate_atp_cost(
    {"deltaR": "local", "deltaT": "session", "deltaC": "simple"},
    quality_level="high"
)  # 10 ATP (2x multiplier)
```

---

## Proposed Web4 Enhancements

### Enhancement 1: Quality-Aware Agent Selection

**File**: `game/engine/agent_selection.py` (new)

```python
from typing import List, Optional, Dict
from dataclasses import dataclass
from engine.lct import LCT

class InsufficientQualityError(Exception):
    """No agent meets minimum quality requirement"""
    pass

class InsufficientATPBudgetError(Exception):
    """No qualified agent within ATP budget"""
    pass

@dataclass
class SelectionResult:
    agent_lct: str
    atp_cost: float
    v3_veracity: float
    reason: str

def select_agent_with_quality(
    operation_type: str,
    agents: List[LCT],
    atp_costs: Dict[str, float],
    min_quality: Optional[float] = None,
    atp_budget: Optional[float] = None
) -> SelectionResult:
    """
    Select agent with quality-first, then ATP-optimal strategy

    Args:
        operation_type: Type of operation (determines quality requirement)
        agents: Available agent LCTs
        atp_costs: ATP cost per agent
        min_quality: Minimum V3 veracity (or auto-infer from operation_type)
        atp_budget: Maximum ATP to spend

    Returns:
        SelectionResult with agent, cost, quality, reason

    Raises:
        InsufficientQualityError: No agent meets quality requirement
        InsufficientATPBudgetError: No qualified agent within budget
    """
    # Auto-infer quality if not specified
    if min_quality is None:
        min_quality = get_quality_requirement(operation_type)

    # Step 1: Filter by quality
    qualified = [
        a for a in agents
        if a.value_axes.get("V3", {}).get("veracity", 0.0) >= min_quality
    ]

    if not qualified:
        raise InsufficientQualityError(
            f"No agent meets veracity requirement {min_quality} for {operation_type}"
        )

    # Step 2: Filter by budget if specified
    if atp_budget:
        affordable = [a for a in qualified if atp_costs[a.lct_id] <= atp_budget]
        if not affordable:
            cheapest = min(qualified, key=lambda a: atp_costs[a.lct_id])
            raise InsufficientATPBudgetError(
                f"Operation requires {atp_costs[cheapest.lct_id]} ATP (quality {min_quality}), "
                f"but budget is {atp_budget}"
            )
        qualified = affordable

    # Step 3: Select cheapest qualified agent
    selected = min(qualified, key=lambda a: atp_costs[a.lct_id])

    return SelectionResult(
        agent_lct=selected.lct_id,
        atp_cost=atp_costs[selected.lct_id],
        v3_veracity=selected.value_axes["V3"]["veracity"],
        reason=f"quality_first (Q>={min_quality})"
    )
```

### Enhancement 2: Extended MRH Profiles with Quality

**File**: `game/engine/mrh_profiles.py` (update)

```python
# Add quality dimension to MRH profiles
def get_mrh_for_situation_with_quality(*,
                                       spatial_scope: str = "local",
                                       temporal_scope: str = "session",
                                       complexity: str = "agent-scale",
                                       quality_level: str = "medium") -> Dict[str, str]:
    """
    Construct MRH profile with quality dimension

    Args:
        spatial_scope: "local" | "regional" | "global"
        temporal_scope: "ephemeral" | "session" | "day" | "epoch"
        complexity: "simple" | "agent-scale" | "society-scale"
        quality_level: "low" | "medium" | "high" | "critical"

    Returns:
        MRH profile dict with quality
    """
    return {
        "deltaR": spatial_scope,
        "deltaT": temporal_scope,
        "deltaC": complexity,
        "deltaQ": quality_level  # NEW: Quality dimension
    }

# Updated ATP cost model
ATP_COSTS_WITH_QUALITY = {
    # (spatial, temporal, complexity, quality): cost
    ("local", "session", "simple", "low"): 5,
    ("local", "session", "simple", "medium"): 8,
    ("local", "session", "simple", "high"): 10,

    ("local", "session", "agent-scale", "low"): 15,
    ("local", "session", "agent-scale", "medium"): 22,
    ("local", "session", "agent-scale", "high"): 30,

    ("regional", "session", "society-scale", "low"): 50,
    ("regional", "session", "society-scale", "medium"): 75,
    ("regional", "session", "society-scale", "high"): 100,

    ("regional", "epoch", "society-scale", "low"): 75,
    ("regional", "epoch", "society-scale", "medium"): 112,
    ("regional", "epoch", "society-scale", "high"): 150,
}
```

### Enhancement 3: Quality-Aware Insurance Claims

**File**: `game/engine/insurance.py` (update)

```python
def file_fraud_claim_with_quality(
    world: World,
    society: Society,
    insurance_pool: InsurancePool,
    atp_lost: float,
    attributed_to_lct: str,
    auditors: List[LCT],
    min_auditor_quality: float = 0.90  # High quality for claims
) -> Optional[Dict[str, Any]]:
    """
    File insurance claim with quality-assured auditor selection

    Quality requirement: 0.90 veracity (insurance claims are critical)
    """
    try:
        # Select qualified auditor
        result = select_agent_with_quality(
            operation_type="insurance_claim",
            agents=auditors,
            atp_costs={a.lct_id: 50 for a in auditors},  # Standard audit cost
            min_quality=min_auditor_quality
        )

        # Process claim with qualified auditor
        claim = insurance_pool.file_claim(
            society_lct=society.society_lct,
            atp_lost=atp_lost,
            auditor_lct=result.agent_lct,
            auditor_veracity=result.v3_veracity
        )

        return claim

    except InsufficientQualityError as e:
        # Fail fast: No qualified auditor available
        print(f"❌ Claim rejected: {e}")
        return None
```

---

## Testing Strategy

### Test 1: Quality Gates

```python
def test_quality_gates():
    """Verify quality requirements are enforced"""

    # Create agents with varying V3 veracity
    alice = create_agent_lct(
        agent_id="alice",
        initial_value={"valuation": 0.8, "veracity": 0.95, "validity": 0.9}
    )
    bob = create_agent_lct(
        agent_id="bob",
        initial_value={"valuation": 0.6, "veracity": 0.65, "validity": 0.7}
    )

    agents = [alice, bob]
    atp_costs = {alice.lct_id: 100, bob.lct_id: 10}

    # Test: High quality operation should select alice (expensive but qualified)
    result = select_agent_with_quality(
        operation_type="insurance_claim",  # Requires 0.90 veracity
        agents=agents,
        atp_costs=atp_costs
    )

    assert result.agent_lct == alice.lct_id  # Alice selected (0.95 >= 0.90)
    assert result.atp_cost == 100  # Expensive but necessary

    # Test: Low quality operation should select bob (cheap and sufficient)
    result = select_agent_with_quality(
        operation_type="event_logging",  # Requires 0.50 veracity
        agents=agents,
        atp_costs=atp_costs
    )

    assert result.agent_lct == bob.lct_id  # Bob selected (0.65 >= 0.50, cheaper)
    assert result.atp_cost == 10  # Optimal choice
```

### Test 2: Fail-Fast Behavior

```python
def test_fail_fast():
    """Verify fail-fast on insufficient quality"""

    # Only low-quality agent available
    bob = create_agent_lct(
        agent_id="bob",
        initial_value={"veracity": 0.65}
    )

    # Test: Should fail fast for high-quality operation
    with pytest.raises(InsufficientQualityError) as exc:
        select_agent_with_quality(
            operation_type="insurance_claim",  # Requires 0.90
            agents=[bob],  # Only 0.65 available
            atp_costs={bob.lct_id: 10}
        )

    assert "No agent meets veracity requirement 0.90" in str(exc.value)
```

---

## Conclusion

HRM's quality-aware selection experiment provides critical insights for Web4's resource allocation:

1. **Quality must gate ATP allocation**, not just optimize it
2. **V3 veracity maps naturally to quality requirements**
3. **Fail-fast is superior to degraded quality** for critical operations
4. **Operation type determines quality requirement** (auto-inference)
5. **MRH profiles need quality dimension** (deltaQ)

**Next Steps**:
1. Implement `select_agent_with_quality()` function
2. Extend MRH profiles with deltaQ dimension
3. Update ATP cost model with quality multipliers
4. Add quality gates to insurance claims processing
5. Test quality enforcement in federation demos

**Key Principle**: On edge devices (and in Web4 societies), **quality failure cost exceeds ATP cost**. Better to spend 7x ATP for 100% reliability than save ATP and fail 67% of the time.
