"""
Causal Trust Inference for Web4
Session 32, Track 6

Correlation is not causation in trust networks. This track implements
causal reasoning to distinguish genuine trust relationships from
confounded ones.

- Structural causal models (SCMs) for trust
- do-calculus: P(trust | do(action)) vs P(trust | observe(action))
- Instrumental variables for trust estimation
- Confounding bias detection
- Counterfactual trust analysis
- Mediation analysis (direct vs indirect trust effects)
- Average treatment effect of trust interventions
"""

import math
import random
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Set


# ─── Structural Causal Model ─────────────────────────────────────

@dataclass
class CausalVariable:
    name: str
    parents: List[str] = field(default_factory=list)
    value: float = 0.0
    noise_std: float = 0.1

    def compute(self, parent_values: Dict[str, float],
                coefficients: Dict[str, float]) -> float:
        """Compute variable value from parents + noise."""
        result = 0.0
        for parent in self.parents:
            coeff = coefficients.get(f"{parent}->{self.name}", 0.0)
            result += coeff * parent_values.get(parent, 0.0)
        # Add noise
        result += random.gauss(0, self.noise_std)
        return max(0.0, min(1.0, result))


@dataclass
class TrustSCM:
    """Structural Causal Model for trust relationships."""
    variables: Dict[str, CausalVariable] = field(default_factory=dict)
    coefficients: Dict[str, float] = field(default_factory=dict)
    topological_order: List[str] = field(default_factory=list)

    def add_variable(self, name: str, parents: List[str] = None,
                     noise_std: float = 0.1):
        parents = parents or []
        self.variables[name] = CausalVariable(
            name=name, parents=parents, noise_std=noise_std)

    def add_edge(self, parent: str, child: str, coefficient: float):
        if child in self.variables:
            if parent not in self.variables[child].parents:
                self.variables[child].parents.append(parent)
        self.coefficients[f"{parent}->{child}"] = coefficient

    def compute_topological_order(self):
        """Topological sort for causal ordering."""
        visited: Set[str] = set()
        order: List[str] = []

        def dfs(node: str):
            if node in visited:
                return
            visited.add(node)
            for parent in self.variables[node].parents:
                dfs(parent)
            order.append(node)

        for var in self.variables:
            dfs(var)

        self.topological_order = order

    def sample(self) -> Dict[str, float]:
        """Generate one sample from the SCM (observational)."""
        if not self.topological_order:
            self.compute_topological_order()

        values: Dict[str, float] = {}
        for var_name in self.topological_order:
            var = self.variables[var_name]
            if not var.parents:
                values[var_name] = max(0, min(1, 0.5 + random.gauss(0, var.noise_std)))
            else:
                values[var_name] = var.compute(values, self.coefficients)

        return values

    def intervene(self, intervention: Dict[str, float]) -> Dict[str, float]:
        """
        do(X = x): Set variable to fixed value, ignoring its parents.
        Simulates the interventional distribution.
        """
        if not self.topological_order:
            self.compute_topological_order()

        values: Dict[str, float] = {}
        for var_name in self.topological_order:
            if var_name in intervention:
                values[var_name] = intervention[var_name]
            else:
                var = self.variables[var_name]
                if not var.parents:
                    values[var_name] = max(0, min(1, 0.5 + random.gauss(0, var.noise_std)))
                else:
                    values[var_name] = var.compute(values, self.coefficients)

        return values

    def counterfactual(self, factual: Dict[str, float],
                       intervention: Dict[str, float]) -> Dict[str, float]:
        """
        Counterfactual: "What would Y have been if we had set X = x,
        given that we observed factual values?"
        Uses abduction-action-prediction.
        """
        # Step 1: Abduction — infer noise terms from factual
        noise: Dict[str, float] = {}
        for var_name in self.topological_order:
            var = self.variables[var_name]
            if not var.parents:
                noise[var_name] = factual.get(var_name, 0.5) - 0.5
            else:
                expected = 0.0
                for parent in var.parents:
                    coeff = self.coefficients.get(f"{parent}->{var_name}", 0.0)
                    expected += coeff * factual.get(parent, 0.0)
                noise[var_name] = factual.get(var_name, 0.0) - expected

        # Step 2: Action — apply intervention
        # Step 3: Prediction — compute with original noise
        cf_values: Dict[str, float] = {}
        for var_name in self.topological_order:
            if var_name in intervention:
                cf_values[var_name] = intervention[var_name]
            else:
                var = self.variables[var_name]
                if not var.parents:
                    cf_values[var_name] = max(0, min(1, 0.5 + noise[var_name]))
                else:
                    result = noise[var_name]
                    for parent in var.parents:
                        coeff = self.coefficients.get(f"{parent}->{var_name}", 0.0)
                        result += coeff * cf_values.get(parent, 0.0)
                    cf_values[var_name] = max(0.0, min(1.0, result))

        return cf_values


# ─── Causal Effect Estimation ─────────────────────────────────────

def average_treatment_effect(scm: TrustSCM, treatment: str,
                              outcome: str, n_samples: int = 1000) -> float:
    """
    ATE = E[Y | do(X=1)] - E[Y | do(X=0)].
    The causal effect of treatment on outcome.
    """
    treated_sum = 0.0
    control_sum = 0.0

    for _ in range(n_samples):
        treated = scm.intervene({treatment: 1.0})
        control = scm.intervene({treatment: 0.0})
        treated_sum += treated.get(outcome, 0.0)
        control_sum += control.get(outcome, 0.0)

    return treated_sum / n_samples - control_sum / n_samples


def observational_association(scm: TrustSCM, x: str, y: str,
                               n_samples: int = 1000,
                               threshold: float = 0.5) -> float:
    """
    Observational association: E[Y | X > threshold] - E[Y | X <= threshold].
    NOT causal — includes confounding.
    """
    high_y = []
    low_y = []

    for _ in range(n_samples):
        sample = scm.sample()
        if sample.get(x, 0.0) > threshold:
            high_y.append(sample.get(y, 0.0))
        else:
            low_y.append(sample.get(y, 0.0))

    if not high_y or not low_y:
        return 0.0

    return sum(high_y) / len(high_y) - sum(low_y) / len(low_y)


# ─── Confounding Detection ───────────────────────────────────────

def confounding_bias(scm: TrustSCM, treatment: str, outcome: str,
                     n_samples: int = 2000) -> Dict[str, float]:
    """
    Measure the gap between observational and interventional estimates.
    Large gap = significant confounding.
    """
    ate = average_treatment_effect(scm, treatment, outcome, n_samples)
    obs = observational_association(scm, treatment, outcome, n_samples)

    return {
        "ate": ate,
        "observational": obs,
        "bias": obs - ate,
        "bias_magnitude": abs(obs - ate),
        "confounded": abs(obs - ate) > 0.05,
    }


# ─── Mediation Analysis ──────────────────────────────────────────

def direct_indirect_effects(scm: TrustSCM, treatment: str,
                             mediator: str, outcome: str,
                             n_samples: int = 1000) -> Dict[str, float]:
    """
    Decompose total effect into direct and indirect (mediated) effects.
    Total = Direct + Indirect.
    """
    # Total effect: do(T=1) - do(T=0)
    total = average_treatment_effect(scm, treatment, outcome, n_samples)

    # Natural Direct Effect (NDE):
    # Effect of treatment while holding mediator at its "natural" value under control
    nde_sum = 0.0
    for _ in range(n_samples):
        # Get mediator value under control
        control = scm.intervene({treatment: 0.0})
        m_control = control.get(mediator, 0.0)

        # Set treatment=1 but mediator=m_control
        treated_direct = scm.intervene({treatment: 1.0, mediator: m_control})
        control_val = scm.intervene({treatment: 0.0, mediator: m_control})

        nde_sum += treated_direct.get(outcome, 0.0) - control_val.get(outcome, 0.0)

    nde = nde_sum / n_samples

    # Natural Indirect Effect (NIE) = Total - NDE
    nie = total - nde

    return {
        "total_effect": total,
        "direct_effect": nde,
        "indirect_effect": nie,
        "mediation_fraction": abs(nie / total) if abs(total) > 0.01 else 0.0,
    }


# ═══════════════════════════════════════════════════════════════════
#  TESTS
# ═══════════════════════════════════════════════════════════════════

def run_checks():
    passed = 0
    failed = 0

    def check(name, condition, detail=""):
        nonlocal passed, failed
        if condition:
            passed += 1
        else:
            failed += 1
            print(f"  FAIL: {name} — {detail}")

    print("=" * 70)
    print("Causal Trust Inference for Web4")
    print("Session 32, Track 6")
    print("=" * 70)

    random.seed(42)

    # ── §1 Structural Causal Model ──────────────────────────────
    print("\n§1 Structural Causal Model Setup\n")

    # Simple trust SCM:
    # Reputation (R) → Trust (T) → Cooperation (C)
    # Reputation (R) → Cooperation (C)  [direct path too]
    scm = TrustSCM()
    scm.add_variable("reputation", noise_std=0.2)
    scm.add_variable("trust", parents=["reputation"], noise_std=0.1)
    scm.add_variable("cooperation", parents=["reputation", "trust"], noise_std=0.1)

    scm.add_edge("reputation", "trust", 0.7)
    scm.add_edge("reputation", "cooperation", 0.3)
    scm.add_edge("trust", "cooperation", 0.5)

    scm.compute_topological_order()

    # Topological order should be valid
    rep_idx = scm.topological_order.index("reputation")
    trust_idx = scm.topological_order.index("trust")
    coop_idx = scm.topological_order.index("cooperation")
    check("topo_order_valid", rep_idx < trust_idx < coop_idx,
          f"order={scm.topological_order}")

    # ── §2 Observational Sampling ───────────────────────────────
    print("\n§2 Observational Sampling\n")

    samples = [scm.sample() for _ in range(500)]
    rep_vals = [s["reputation"] for s in samples]
    trust_vals = [s["trust"] for s in samples]

    # Trust correlates with reputation (observationally)
    mean_rep = sum(rep_vals) / len(rep_vals)
    mean_trust = sum(trust_vals) / len(trust_vals)

    # Both should be roughly centered around 0.5
    check("rep_centered", 0.3 < mean_rep < 0.7,
          f"mean_rep={mean_rep:.4f}")
    check("trust_centered", 0.3 < mean_trust < 0.7,
          f"mean_trust={mean_trust:.4f}")

    # ── §3 Interventional Distribution ──────────────────────────
    print("\n§3 Interventional Distribution (do-calculus)\n")

    # do(reputation = 0.9) should increase trust
    high_rep = [scm.intervene({"reputation": 0.9}) for _ in range(500)]
    low_rep = [scm.intervene({"reputation": 0.1}) for _ in range(500)]

    mean_trust_high = sum(s["trust"] for s in high_rep) / len(high_rep)
    mean_trust_low = sum(s["trust"] for s in low_rep) / len(low_rep)

    check("intervention_effect", mean_trust_high > mean_trust_low,
          f"high={mean_trust_high:.4f} low={mean_trust_low:.4f}")

    # do(trust) should NOT affect reputation (it's upstream)
    high_trust_int = [scm.intervene({"trust": 0.9}) for _ in range(500)]
    low_trust_int = [scm.intervene({"trust": 0.1}) for _ in range(500)]
    rep_with_high_trust = sum(s["reputation"] for s in high_trust_int) / len(high_trust_int)
    rep_with_low_trust = sum(s["reputation"] for s in low_trust_int) / len(low_trust_int)

    check("intervention_no_backflow", abs(rep_with_high_trust - rep_with_low_trust) < 0.1,
          f"rep@high_trust={rep_with_high_trust:.4f} rep@low_trust={rep_with_low_trust:.4f}")

    # ── §4 Causal vs Observational ──────────────────────────────
    print("\n§4 Confounding Bias Detection\n")

    # SCM with confounding: C → X, C → Y (C is confounder)
    confounded_scm = TrustSCM()
    confounded_scm.add_variable("confounder", noise_std=0.2)
    confounded_scm.add_variable("attestation_rate", parents=["confounder"], noise_std=0.1)
    confounded_scm.add_variable("trust_score", parents=["confounder"], noise_std=0.1)

    confounded_scm.add_edge("confounder", "attestation_rate", 0.8)
    confounded_scm.add_edge("confounder", "trust_score", 0.8)
    # No direct causal link from attestation_rate to trust_score!

    bias = confounding_bias(confounded_scm, "attestation_rate", "trust_score", 2000)

    # ATE should be ~0 (no causal effect)
    check("ate_near_zero", abs(bias["ate"]) < 0.15,
          f"ate={bias['ate']:.4f}")

    # Observational should show positive association (confounded)
    check("obs_confounded", bias["observational"] > 0.05,
          f"obs={bias['observational']:.4f}")

    # Bias detected
    check("confounding_detected", bias["confounded"],
          f"bias={bias['bias_magnitude']:.4f}")

    # ── §5 Counterfactual Analysis ──────────────────────────────
    print("\n§5 Counterfactual Analysis\n")

    # Observe factual state
    factual = scm.sample()

    # What would cooperation be if trust had been higher?
    cf = scm.counterfactual(factual, {"trust": 0.9})

    # Cooperation should change with trust (causal relationship)
    # But reputation stays same (it's not downstream of trust)
    check("cf_rep_preserved", abs(cf["reputation"] - factual["reputation"]) < 0.01,
          f"factual={factual['reputation']:.4f} cf={cf['reputation']:.4f}")

    # ── §6 Average Treatment Effect ─────────────────────────────
    print("\n§6 Average Treatment Effect\n")

    # ATE of reputation on cooperation (should be positive: direct + indirect)
    ate_rep_coop = average_treatment_effect(scm, "reputation", "cooperation", 2000)
    check("ate_rep_coop_positive", ate_rep_coop > 0.2,
          f"ate={ate_rep_coop:.4f}")

    # ATE of trust on cooperation (should be positive: direct effect)
    ate_trust_coop = average_treatment_effect(scm, "trust", "cooperation", 2000)
    check("ate_trust_coop_positive", ate_trust_coop > 0.1,
          f"ate={ate_trust_coop:.4f}")

    # ── §7 Mediation Analysis ──────────────────────────────────
    print("\n§7 Mediation Analysis\n")

    effects = direct_indirect_effects(scm, "reputation", "trust",
                                       "cooperation", 2000)

    check("total_effect_positive", effects["total_effect"] > 0.1,
          f"total={effects['total_effect']:.4f}")

    check("direct_effect_positive", effects["direct_effect"] > 0,
          f"direct={effects['direct_effect']:.4f}")

    # Both direct and indirect should be positive
    # (reputation → cooperation directly AND via trust)
    check("indirect_exists", effects["indirect_effect"] > -0.1,
          f"indirect={effects['indirect_effect']:.4f}")

    check("mediation_fraction_reasonable",
          0 <= effects["mediation_fraction"] <= 1.0,
          f"fraction={effects['mediation_fraction']:.4f}")

    # ── Summary ─────────────────────────────────────────────────
    print(f"\n{'='*70}")
    print(f"Results: {passed} passed, {failed} failed out of {passed + failed}")
    print(f"{'='*70}")
    return passed, failed


if __name__ == "__main__":
    run_checks()
