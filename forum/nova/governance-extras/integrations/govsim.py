#!/usr/bin/env python3
import sys, os, math, json, csv

def clamp(x, lo, hi): return max(lo, min(hi, x))

def load_yaml_or_json(path):
    try:
        import yaml  # type: ignore
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception:
        root, _ = os.path.splitext(path)
        jpath = root + ".json"
        if os.path.exists(jpath):
            with open(jpath, "r", encoding="utf-8") as f:
                return json.load(f)
        raise RuntimeError("Install PyYAML or provide JSON at "+jpath)

def compute_controls(cfg_sections, coeffs):
    a, b, c = coeffs["a"], coeffs["b"], coeffs["c"]
    eps = coeffs.get("epsilon", 1e-6)
    rows = []
    for name, v in cfg_sections.items():
        L, C, R = float(v["L"]), float(v["C"]), float(v["R"])
        delta = (a*L + b*R) / (1 + c*C)
        w0 = 1.0 / math.sqrt(eps + L*C)
        change_threshold = clamp(0.50 + 0.35*L + 0.15*R - 0.10*C, 0.50, 0.95)
        review_days      = round(3 + 10*L + 4*delta)
        quorum           = max(1, int(math.ceil(1 + 2*L + 1*R)))
        token_cost       = round(50 * (0.5 + 0.7*L + 0.3*R))
        reject_penalty   = clamp(0.10 + 0.70*R, 0.10, 0.95)
        fast_track_drop  = 0.20 * (1 - L)
        rows.append({
            "section": name, "L": L, "C": C, "R": R,
            "delta": round(delta,4), "omega0": round(w0,4),
            "change_threshold": round(change_threshold,3),
            "review_days": int(review_days), "quorum": int(quorum),
            "token_cost": int(token_cost), "reject_penalty": round(reject_penalty,2),
            "fast_track_drop": round(fast_track_drop,2),
        })
    return rows

def write_tables(rows, out_csv, out_md):
    os.makedirs(os.path.dirname(out_csv), exist_ok=True)
    os.makedirs(os.path.dirname(out_md), exist_ok=True)
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    headers = ["section","L","C","R","delta","omega0","change_threshold","review_days","quorum","token_cost","reject_penalty","fast_track_drop"]
    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join(["---"]*len(headers)) + "|"]
    for r in rows: lines.append("| " + " | ".join(str(r[h]) for h in headers) + " |")
    with open(out_md, "w", encoding="utf-8") as f:
        f.write("# Governance Controls (computed)\n\n" + "\n".join(lines) + "\n")

def main():
    cfg_path = sys.argv[1] if len(sys.argv)>1 else "integrations/governance_map.yaml"
    out_csv  = sys.argv[2] if len(sys.argv)>2 else "docs/collab/governance_controls.csv"
    out_md   = sys.argv[3] if len(sys.argv)>3 else "docs/collab/governance_controls.md"
    cfg = load_yaml_or_json(cfg_path)
    rows = compute_controls(cfg["sections"], cfg["coefficients"])
    write_tables(rows, out_csv, out_md)
    print("computed controls ->", out_csv, out_md)

if __name__ == "__main__":
    main()
