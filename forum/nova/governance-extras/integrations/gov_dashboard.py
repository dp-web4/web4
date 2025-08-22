#!/usr/bin/env python3
import os, sys, yaml

def tint(val):
    if val < 0.33: return "🟢"
    if val < 0.66: return "🟡"
    if val < 0.85: return "🟠"
    return "🔴"

def main():
    cfg = sys.argv[1] if len(sys.argv) > 1 else "integrations/governance_map.yaml"
    out = sys.argv[2] if len(sys.argv) > 2 else "docs/collab/governance_dashboard.md"
    with open(cfg, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    rows = []
    for sec, node in data["sections"].items():
        L, C, R = float(node["L"]), float(node["C"]), float(node["R"])
        paths = node.get("paths", [])
        rows.append((sec, L, C, R, paths))
    rows.sort(key=lambda r: -r[1])
    lines = ["# Governance Dashboard", "", "| section | L | C | R | paths |", "|---|---:|---:|---:|---|"]
    for sec, L, C, R, ps in rows:
        lines.append(f"| **{sec}** | {L:.2f} {tint(L)} | {C:.2f} {tint(C)} | {R:.2f} {tint(R)} | " + "<br/>".join(ps) + " |")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print("wrote", out)

if __name__ == "__main__":
    main()
