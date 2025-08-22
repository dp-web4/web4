#!/usr/bin/env python3
import os, sys, json, subprocess, yaml

L_GUARD = float(os.environ.get("L_GUARD", "0.80"))  # high-L threshold

def get_changed_files():
    base = os.environ.get("GITHUB_BASE_REF")
    head = os.environ.get("GITHUB_SHA")
    if base:
        # In PRs, actions/checkout sets FETCH_HEAD to the PR, but we need merge-base. Fallback to origin/branch.
        try:
            subprocess.run(["git","fetch","--depth=0","origin",base], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except Exception:
            pass
        base_ref = f"origin/{base}"
    else:
        # Non-PR: compare to previous commit
        base_ref = "HEAD~1"
    cmd = ["git","diff","--name-only",f"{base_ref}...HEAD"]
    out = subprocess.check_output(cmd).decode().strip().splitlines()
    return [p for p in out if p]

def load_map(path="integrations/governance_map.yaml"):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def map_files_to_sections(files, mapping):
    hits = set()
    for sec, node in mapping["sections"].items():
        for pat in node.get("paths", []):
            # naive match: exact path equality
            if pat in files:
                hits.add(sec)
    return list(hits)

def read_pr_body():
    # On GitHub, the event payload JSON is available here
    event_path = os.environ.get("GITHUB_EVENT_PATH")
    if event_path and os.path.exists(event_path):
        with open(event_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        body = data.get("pull_request", {}).get("body") or ""
        return body
    # Fallback: check recent commit message
    try:
        msg = subprocess.check_output(["git","log","-1","--pretty=%B"]).decode()
        return msg
    except Exception:
        return ""

def main():
    changed = get_changed_files()
    mapping = load_map()
    touched = map_files_to_sections(changed, mapping)
    highL = [s for s in touched if float(mapping["sections"][s]["L"]) >= L_GUARD]

    print("Changed files:", changed)
    print("Touched sections:", touched)
    print("High-L sections:", highL)

    if not highL:
        print("No high-L sections touched; pass.")
        return 0

    body = read_pr_body()
    if "Governance-Ack: yes" in body:
        print("Governance acknowledgment found in PR body/commit message; pass.")
        return 0
    else:
        print("ERROR: High-L sections modified but Governance-Ack not found in PR body.")
        print("Please tick the checkbox in the PR template or add 'Governance-Ack: yes' to the description.")
        return 2

if __name__ == "__main__":
    sys.exit(main())
