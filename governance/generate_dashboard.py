#!/usr/bin/env python3
"""
Generate Governance Dashboard for Web4
Based on Nova's LRC governance visualization
"""

import os
import sys
import yaml
import math

def tint(val):
    """Color code based on value thresholds"""
    if val < 0.33: return "🟢"
    if val < 0.66: return "🟡"
    if val < 0.85: return "🟠"
    return "🔴"

def compute_controls(section_data, coefficients):
    """Compute governance controls from LRC values"""
    L = float(section_data["L"])
    C = float(section_data["C"])
    R = float(section_data["R"])
    
    a = coefficients["a"]
    b = coefficients["b"] 
    c = coefficients["c"]
    epsilon = coefficients.get("epsilon", 1e-6)
    
    # Compute derived values
    delta = (a * L + b * R) / (1 + c * C)
    omega0 = 1.0 / math.sqrt(epsilon + L * C)
    
    # Compute governance parameters
    change_threshold = max(0.50, min(0.95, 0.50 + 0.35*L + 0.15*R - 0.10*C))
    review_days = round(3 + 10*L + 4*delta)
    quorum = max(1, int(math.ceil(1 + 2*L + 1*R)))
    token_cost = round(50 * (0.5 + 0.7*L + 0.3*R))
    reject_penalty = max(0.10, min(0.95, 0.10 + 0.70*R))
    fast_track_drop = 0.20 * (1 - L)
    
    return {
        "delta": round(delta, 4),
        "omega0": round(omega0, 4),
        "change_threshold": round(change_threshold, 3),
        "review_days": int(review_days),
        "quorum": int(quorum),
        "token_cost": int(token_cost),
        "reject_penalty": round(reject_penalty, 2),
        "fast_track_drop": round(fast_track_drop, 2)
    }

def main():
    # Load governance map
    map_file = "governance/governance_map.yaml"
    if not os.path.exists(map_file):
        print(f"Error: {map_file} not found")
        sys.exit(1)
    
    with open(map_file, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    
    sections = data["sections"]
    coefficients = data["coefficients"]
    
    # Build dashboard content
    lines = [
        "# Web4 Governance Dashboard",
        "",
        "*Generated from LRC governance model parameters*",
        "",
        "## Section Overview",
        "",
        "| Section | L | C | R | Threshold | Review Days | Quorum | Description |",
        "|---------|---|---|---|-----------|-------------|--------|-------------|"
    ]
    
    # Process sections sorted by L value (most protected first)
    sorted_sections = sorted(sections.items(), key=lambda x: -x[1]["L"])
    
    for section_name, section_data in sorted_sections:
        controls = compute_controls(section_data, coefficients)
        description = section_data.get("description", "")
        
        lines.append(
            f"| **{section_name}** | "
            f"{section_data['L']:.2f} {tint(section_data['L'])} | "
            f"{section_data['C']:.2f} {tint(section_data['C'])} | "
            f"{section_data['R']:.2f} {tint(section_data['R'])} | "
            f"{controls['change_threshold']*100:.1f}% | "
            f"{controls['review_days']} | "
            f"{controls['quorum']} | "
            f"{description} |"
        )
    
    # Add legend
    lines.extend([
        "",
        "## Legend",
        "",
        "### Color Coding",
        "- 🟢 Low (< 0.33): Minimal resistance/protection",
        "- 🟡 Medium (0.33-0.66): Moderate resistance/protection",
        "- 🟠 High (0.66-0.85): Significant resistance/protection",
        "- 🔴 Critical (> 0.85): Maximum resistance/protection",
        "",
        "### Parameters",
        "- **L (Inductance)**: Resistance to change - higher values mean more stability",
        "- **C (Capacitance)**: Experimentation capacity - higher values mean more flexibility",
        "- **R (Resistance)**: Quality filtering - higher values mean stronger noise rejection",
        "- **Threshold**: Minimum approval percentage required for changes",
        "- **Review Days**: Time required before changes can be approved",
        "- **Quorum**: Minimum number of reviewers required",
        "",
        "## Detailed Controls",
        "",
        "| Section | Token Cost | Reject Penalty | Fast-Track | ω₀ (Hz) | δ (damping) |",
        "|---------|------------|----------------|------------|---------|-------------|"
    ])
    
    # Add detailed controls table
    for section_name, section_data in sorted_sections:
        controls = compute_controls(section_data, coefficients)
        
        lines.append(
            f"| **{section_name}** | "
            f"{controls['token_cost']} | "
            f"{controls['reject_penalty']*100:.0f}% | "
            f"{controls['fast_track_drop']*100:.0f}% | "
            f"{controls['omega0']:.2f} | "
            f"{controls['delta']:.3f} |"
        )
    
    # Add footer
    lines.extend([
        "",
        "---",
        "",
        f"*Dashboard generated using coefficients: a={coefficients['a']}, b={coefficients['b']}, c={coefficients['c']}*",
        "",
        f"*Last updated: {data['metadata']['last_updated']}*"
    ])
    
    # Write dashboard
    output_file = "governance/dashboard.md"
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    
    print(f"✅ Dashboard generated: {output_file}")
    print(f"   Processed {len(sections)} sections")
    print(f"   Using coefficients: a={coefficients['a']}, b={coefficients['b']}, c={coefficients['c']}")

if __name__ == "__main__":
    main()