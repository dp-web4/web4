#!/usr/bin/env python3
"""Set up a chapter hub's starting structure (people + committees) through its operator plane.

    python3 seed.py --chapter <chapter.json> --admin http://127.0.0.1:8782 \
        [--token-file <hub-dir>/operator.token] [--invite tag,tag] [--links]

- People become contacts (name + address, kept off the ledger in the contact book).
- Committees are set with their leads and members; one is marked as answering the chapter's email.
- Nobody is emailed by seeding. --invite names who gets the welcome now (normally the chapter
  leads); everyone else is invited by a chapter lead from their own page when they choose.
- --links prints each person's chapter page link (needs HUB_PUBLIC_BASE_URL on the hub).

Safe to re-run: people already in the contact book (same address) are reused, and committees with
the same name are updated in place rather than duplicated.
Standard library only.
"""
import argparse
import json
import sys
import urllib.error
import urllib.request


def call(admin, token, method, path, body=None):
    req = urllib.request.Request(admin.rstrip("/") + path, method=method)
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("X-Operator-Token", token)
    data = json.dumps(body).encode() if body is not None else None
    try:
        with urllib.request.urlopen(req, data, timeout=30) as r:
            return json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        sys.exit(f"{method} {path} -> {e.code}: {e.read().decode(errors='replace')}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--chapter", required=True)
    ap.add_argument("--admin", default="http://127.0.0.1:8782")
    ap.add_argument("--token-file")
    ap.add_argument("--invite", default="", help="comma-separated tags to welcome now")
    ap.add_argument("--links", action="store_true")
    a = ap.parse_args()

    token = open(a.token_file).read().strip() if a.token_file else None
    chapter = json.load(open(a.chapter))

    def address(p):
        return p["address"]

    book = call(a.admin, token, "GET", "/admin/api/contacts").get("contacts", {})
    by_address = {c["address"].lower(): pid for pid, c in book.items()}
    party = {}
    for p in chapter["people"]:
        addr = address(p)
        pid = by_address.get(addr.lower())
        if not pid:
            pid = call(a.admin, token, "POST", "/admin/api/contacts",
                       {"name": p["name"], "address": addr})["party"]["party_id"]
        party[p["tag"]] = {"party_id": pid, "kind": "contact"}
        print(f"person  {p['name']:<18} {addr}")

    existing = {c["name"].lower(): c["committee_id"]
                for c in call(a.admin, token, "GET", "/admin/api/chapter")["committees"] if not c["retired"]}
    for c in chapter["committees"]:
        body = {
            "name": c["name"], "purpose": c.get("purpose", ""),
            "leads": [party[t] for t in c["leads"]], "members": [party[t] for t in c.get("members", [])],
            "inbox": bool(c.get("inbox")),
        }
        if c["name"].lower() in existing:
            body["committee_id"] = existing[c["name"].lower()]
        r = call(a.admin, token, "POST", "/admin/api/chapter/committees", body)
        print(f"committee {c['name']:<24} {r['committee_id']}")

    tags = [x for x in a.invite.split(",") if x.strip()]
    if tags:
        call(a.admin, token, "POST", "/admin/api/chapter/invite", {"party_ids": [party[x.strip()]["party_id"] for x in tags]})
        print("invited", ", ".join(tags))

    if a.links:
        for p in chapter["people"]:
            link = call(a.admin, token, "GET", f"/admin/api/chapter/home-link/{party[p['tag']]['party_id']}")["link"]
            print(f"page    {p['name']:<18} {link}")


if __name__ == "__main__":
    main()
