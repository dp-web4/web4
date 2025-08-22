#!/usr/bin/env python3
import sys, os, glob, io, datetime, json

def load_yaml(path):
    try:
        import yaml  # type: ignore
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception as e:
        raise RuntimeError("YAML parse error; please `pip install pyyaml`. " + str(e))

def dump_yaml(obj):
    import yaml  # type: ignore
    return yaml.safe_dump(obj, sort_keys=False)

def compute_row(L, C, R, coeffs):
    import math
    def clamp(x, lo, hi): return max(lo, min(hi, x))
    a, b, c = coeffs["a"], coeffs["b"], coeffs["c"]
    eps = coeffs.get("epsilon", 1e-6)
    delta = (a*L + b*R) / (1 + c*C)
    w0 = 1.0 / math.sqrt(eps + L*C)
    return {
        "L": L, "C": C, "R": R,
        "delta": round(delta,4), "omega0": round(w0,4),
        "change_threshold": round(clamp(0.50 + 0.35*L + 0.15*R - 0.10*C, 0.50, 0.95),3),
        "review_days": int(round(3 + 10*L + 4*delta)),
        "quorum": int(max(1, int(math.ceil(1 + 2*L + 1*R)))),
        "token_cost": int(round(50 * (0.5 + 0.7*L + 0.3*R))),
        "reject_penalty": round(clamp(0.10 + 0.70*R, 0.10, 0.95),2),
        "fast_track_drop": round(0.20 * (1 - L),2),
    }

def update_front_matter(path, section_name, controls, apply=False):
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    # Parse front matter if present
    if text.startswith("---\n"):
        end = text.find("\n---", 4)
        if end != -1:
            fm_text = text[4:end]
            body = text[end+4:]
        else:
            fm_text, body = "", text
    else:
        fm_text, body = "", text
    # Load/compose YAML
    try:
        import yaml  # type: ignore
        fm = yaml.safe_load(fm_text) if fm_text.strip() else {}
    except Exception:
        fm = {}
    if not isinstance(fm, dict): fm = {}
    fm.setdefault("governance", {})
    fm["governance"].update({"section": section_name, **controls, "last_computed": datetime.datetime.utcnow().isoformat()+"Z"})
    new_fm = dump_yaml(fm).strip()
    new_text = f"---\n{new_fm}\n---\n{body.lstrip()}"
    if apply:
        with open(path, "w", encoding="utf-8") as f:
            f.write(new_text)
    else:
        # Dry-run: show a small diff-like preview
        print(f"[DRY] would update {path} -> governance.section={section_name}")
    return True

def main():
    import argparse
    ap = argparse.ArgumentParser(description="Integrate LRC governance into docs via front-matter updates.")
    ap.add_argument("--config", default="integrations/governance_map.yaml")
    ap.add_argument("--repo-root", default=".")
    ap.add_argument("--apply", action="store_true", help="apply changes in-place")
    args = ap.parse_args()

    cfg = load_yaml(args.config)
    coeffs = cfg["coefficients"]

    updated = 0
    for name, node in cfg["sections"].items():
        L, C, R = float(node["L"]), float(node["C"]), float(node["R"])
        controls = compute_row(L, C, R, coeffs)
        for pattern in node.get("paths", []):
            for path in glob.glob(os.path.join(args.repo_root, pattern), recursive=True):
                ok = update_front_matter(path, name, controls, apply=args.apply)
                if ok: updated += 1

    # Also (re)generate control tables using govsim
    try:
        import subprocess
        out_csv = os.path.join(args.repo_root, "docs/collab/governance_controls.csv")
        out_md  = os.path.join(args.repo_root, "docs/collab/governance_controls.md")
        subprocess.run([sys.executable, os.path.join("integrations","govsim.py"),
                        args.config, out_csv, out_md], check=True)
    except Exception as e:
        print("warning: could not run govsim.py:", e)

    print(("APPLIED" if args.apply else "DRY‑RUN"), "updated files:", updated)

if __name__ == "__main__":
    main()
