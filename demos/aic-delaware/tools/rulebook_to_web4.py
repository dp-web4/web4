# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Metalinxx Inc.
"""rulebook_to_web4.py — project an ERB rulebook into Web4. Local, stdlib only, no network.

  python3 rulebook_to_web4.py <rulebook.json> <outdir>

reads the rulebook's baked derived columns (run `rulebook.py build` first) and writes:

  society-graph.ttl                          societies, roles, entities, memberships (web4 ontology) + provenance
  societies/<id>/law.candidate.yaml          hub law (web4-policy YAML surface): every non-refused norm, real decisions
  societies/<id>/law.ratified.yaml           hub law: only norms whose rule the operator confirmed
  societies/<id>/hestia-policy.candidate.json   hestia PolicyConfig, enforce=false (audit-only = shadow)
  societies/<id>/hestia-policy.ratified.json    hestia PolicyConfig, enforce=true, confirmed rules only
  societies/<id>/role-overlays.*.json        per-role tightening overlays (hestia)
  lawbook.json                               Lawbook fixture (web4 hub/docs/PRD_LAWBOOK_IR.md §4 object model)
  conformance.json / conformance.md          scenario corpus run through the reference oracle
  witnesses.md                               transpiler-level findings (blocking / advisory)
  manifest.json                              sha256 of input and every output (projection witness)

nothing here touches a live hub or hestia. applying a ratified projection is a consequential act for the operator.
the reference oracle below is a TEST ORACLE for the corpus, not a law engine: web4-policy (hub) and
hestia's PolicyEngine/LawGate remain the only evaluators that decide real acts.
"""
import datetime as dt
import fnmatch
import hashlib
import json
import re
import sys
from pathlib import Path

TOOL_VERSION = "0.1.0"
NS = {  # hub-law.ttl uses the slash form; SAL §7.2 examples use '#'. we follow the ontology file (see witnesses).
    "web4": "https://web4.io/ontology/",
    "law": "https://web4.io/ontology/law/",
    "lct": "https://web4.io/lct/",
    "prov": "http://www.w3.org/ns/prov#",
    "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
    "xsd": "http://www.w3.org/2001/XMLSchema#",
    "rb": "urn:web4:rulebook:",
}
BASE_ROLES = ["sovereign", "law-oracle", "policy-entity", "treasurer", "administrator", "archivist", "citizen", "maintainer"]
HUB_DECISIONS = {"allow", "warn", "deny", "escalate"}
HUB_OPERATORS = {"<=", ">=", "==", "!=", "<", ">", "in", "not_in", "matches"}
SEVERITY = {"allow": 0, "warn": 1, "deny": 2}


# ------------------------------------------------------------------ load
def load(path):
    rb = json.loads(Path(path).read_text(encoding="utf-8"))
    need = ["Societies", "RoleSlots", "Norms", "Scenarios", "Rules", "Citations", "Roles"]
    missing = [t for t in need if t not in rb]
    if missing:
        raise SystemExit(f"rulebook lacks web4 binding tables: {missing}")
    if any("CompileMode" not in n for n in rb["Norms"]["data"]):
        raise SystemExit("derived columns missing — run `python3 rulebook.py build` first")
    return rb


def rows(rb, t):
    return rb[t]["data"]


def by_id(rb, t):
    key = rb[t]["schema"][0]["name"]
    return {r[key]: r for r in rows(rb, t)}


def meta(rb, key):
    for r in rows(rb, "__meta__"):
        if r["MetaKey"] == key:
            return r["StringValue"] or r["JsonValue"]
    return None


def slug(s):
    return re.sub(r"[^A-Za-z0-9_.-]+", "-", str(s)).strip("-")


# ------------------------------------------------------------------ society tree + effective law
def ancestors(soc, socs):
    chain, cur = [], socs[soc]["Parent"]
    while cur:
        chain.append(cur)
        cur = socs[cur]["Parent"]
    return chain


def effective_norms(rb, soc_id, mode):
    """SAL §3.5: effectiveLaw(child) = merge(parentLaw, childOverrides). child norms with the same id
    override the parent's only if they don't widen it (tighten-only conflict policy); widening is reported."""
    socs, findings = by_id(rb, "Societies"), []
    chain = list(reversed(ancestors(soc_id, socs))) + [soc_id]  # root first
    eff = {}
    for s in chain:
        for n in rows(rb, "Norms"):
            if n["Society"] != s or n["CompileMode"] == "refused":
                continue
            if mode == "ratified" and n["CompileMode"] != "enforce":
                continue
            key = n.get("Overrides") or n["NormId"]
            prev = eff.get(key)
            if prev and widens(prev, n):
                findings.append(("blocking", "ChildOverrideWidensParent", f"{s}: {n['NormId']} would loosen {prev['Society']}'s {key}"))
                continue
            eff[key] = n
    return list(eff.values()), findings


def widens(parent, child):
    order = {"allow": 0, "warn": 1, "escalate": 2, "deny": 3}
    return order.get(child["Decision"] or "allow", 0) < order.get(parent["Decision"] or "allow", 0)


# ------------------------------------------------------------------ hub law YAML (web4-policy surface)
def yq(v):
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return str(v)
    return json.dumps(str(v))


def norm_value(n):
    v = n["Value"]
    if n["Operator"] in ("in", "not_in"):
        return json.loads(v)
    try:
        return json.loads(v) if isinstance(v, str) and v[:1] in "[{0123456789-" else v
    except ValueError:
        return v


def hub_law(rb, soc_id, norms, mode):
    rules = by_id(rb, "Rules")
    L = [f"# hub law for society '{soc_id}' — {mode}",
         f"# generated by rulebook_to_web4 {TOOL_VERSION} from {rb['Name']} draft {meta(rb, 'draft')}. do not edit; edit the rulebook.",
         f"# {'only norms whose rule the operator confirmed' if mode == 'ratified' else 'every non-refused norm, ratified or not — for shadow replay and review, NOT for activation'}",
         f'version: "0.{meta(rb, "draft") or 0}.0"', ""]
    hub_norms = sorted([n for n in norms if n["Surface"] == "hub-norm"], key=lambda n: -(n["Priority"] or 0))
    L.append("norms:" if hub_norms else "norms: []")
    for n in hub_norms:
        r = rules[n["Rule"]]
        L += [f"  # {n['Rule']} · {r['ShortName']} · rule status {r['Status']} · compile {n['CompileMode']}",
              f"  - id: {n['NormId']}", f"    selector: {n['Selector']}", f"    operator: {yq(n['Operator'])}"]
        val = norm_value(n)
        if isinstance(val, list):
            L.append("    value:")
            L += [f"      - {x}" for x in val]
        else:
            L.append(f"    value: {val if re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', str(val)) else yq(val)}")
        L += [f"    decision: {n['Decision']}", f"    priority: {n['Priority']}", f"    description: {yq(n['Description'] or r['ShortName'])}"]
    esc = [n for n in norms if n["Surface"] == "hub-escalation"]
    if esc:
        L += ["", "escalation:"]
        for n in esc:
            L += [f"  - condition: {yq(n['Value'])}", f"    escalate_to: {n['EscalateTo']}", f"    description: {yq(n['Description'])}"]
    adm = [n for n in norms if n["Surface"] == "hub-admission"]
    if adm:
        a = json.loads(adm[-1]["Value"])
        L += ["", "admission:"] + [f"  {k}: {yq(v)}" for k, v in a.items()] + [f"  description: {yq(adm[-1]['Description'])}"]
    return "\n".join(L) + "\n", hub_norms, esc, adm


def validate_hub(rb, soc_id, hub_norms, esc, adm, version):
    """hub-law-schema.md §2 rules 1-5, 8, 9 (the subset this surface emits)."""
    probs = []
    if not re.fullmatch(r"\d+\.\d+\.\d+", version):
        probs.append("rule 1: version is not semver")
    ids = [n["NormId"] for n in hub_norms]
    if len(ids) != len(set(ids)):
        probs.append("rule 5: duplicate norm id")
    valid_roles = {s["SocietyRole"] for s in rows(rb, "RoleSlots") if s["Society"] == soc_id}
    for n in hub_norms:
        for f in ("Selector", "Operator", "Value", "Decision"):
            if n[f] in (None, ""):
                probs.append(f"rule 2: {n['NormId']} missing {f.lower()}")
        if n["Decision"] not in HUB_DECISIONS:
            probs.append(f"rule 3: {n['NormId']} decision {n['Decision']}")
        if n["Operator"] not in HUB_OPERATORS:
            probs.append(f"rule 4: {n['NormId']} operator {n['Operator']}")
        if n["Decision"] == "escalate" and n["EscalateTo"] and n["EscalateTo"] not in valid_roles:
            probs.append(f"rule 8: {n['NormId']} escalates to {n['EscalateTo']}, not a role of {soc_id}")
    for n in esc:
        if n["EscalateTo"] not in valid_roles:
            probs.append(f"rule 8: escalation to {n['EscalateTo']} is not a role of {soc_id}")
        if not parse_condition(n["Value"]):
            probs.append(f"FL-009: escalation condition does not parse: {n['Value']!r}")
    for n in adm:
        sr = json.loads(n["Value"]).get("sponsor_role")
        if sr and sr not in valid_roles:
            probs.append(f"rule 9: sponsor_role {sr} is not a role of {soc_id}")
    return probs


COND = re.compile(r"\s*(r6\.[A-Za-z0-9_.]+)\s*(<=|>=|==|!=|<|>)\s*('([^']*)'|\"([^\"]*)\"|-?\d+(\.\d+)?)\s*$")


def parse_condition(c):
    m = COND.match(c or "")
    return m and (m.group(1), m.group(2), m.group(4) if m.group(4) is not None else (m.group(5) if m.group(5) is not None else float(m.group(3))))


# ------------------------------------------------------------------ hestia projection
def hestia_rule(n):
    match = {}
    if n["HestiaTools"]:
        match["tools"] = json.loads(n["HestiaTools"])
    if n["HestiaCommandPattern"]:
        match["command_patterns"] = [n["HestiaCommandPattern"]]
        match["command_patterns_are_regex"] = True
    if n["HestiaTargetPattern"]:
        match["target_patterns"] = [n["HestiaTargetPattern"]]
        match["target_patterns_are_regex"] = False
    return {"id": n["NormId"], "name": n["Description"] or n["NormId"],
            "priority": -int(n["Priority"] or 0),  # hub: higher wins → hestia: lower first. negative, so law runs before preset rules (0..10)
            "decision": n["Decision"] if n["Decision"] in SEVERITY else "deny",
            "reason": f"{n['Rule']}: {n['Description']}", "match": match}


def hestia_configs(norms, mode):
    local = [n for n in norms if n["Surface"] == "hestia-rule"]
    base = [hestia_rule(n) for n in local if not n["AppliesToRole"]]
    overlays = {}
    for n in local:
        if n["AppliesToRole"]:
            overlays.setdefault(n["AppliesToRole"], []).append(hestia_rule(n))
    enforce = mode == "ratified"
    cfg = {"default_policy": "allow", "enforce": enforce, "rules": sorted(base, key=lambda r: r["priority"])}
    ov = {role: {"default_policy": "allow", "enforce": enforce, "rules": sorted(rs, key=lambda r: r["priority"])} for role, rs in overlays.items()}
    return cfg, ov


# ------------------------------------------------------------------ reference oracle (test oracle only)
def hub_eval(law_norms, esc, req):
    def get(sel):
        cur = {"r6": {"role": req.get("role"), "request": {"action": req.get("action"), "payload": req.get("payload", {})}, "resource": req.get("resource", {})}}
        for part in sel.split("."):
            cur = cur.get(part) if isinstance(cur, dict) else None
        return cur

    def fires(n):
        v, op, want = get(n["Selector"]), n["Operator"], norm_value(n)
        ops = {"==": lambda: v == want, "!=": lambda: v != want, "in": lambda: v in want, "not_in": lambda: v not in want,
               "<": lambda: v < want, "<=": lambda: v <= want, ">": lambda: v > want, ">=": lambda: v >= want,
               "matches": lambda: bool(re.search(str(want), str(v)))}
        try:
            return ops[op]()  # lazily: only the declared operator is evaluated
        except TypeError:
            return False  # type mismatch (e.g. missing resource field) never fires
    firing = [n for n in law_norms if n["Surface"] == "hub-norm" and fires(n)]
    winner = max(firing, key=lambda n: n["Priority"] or 0) if firing else None  # ties: first declared (max keeps first)
    if winner and winner["Decision"] == "deny":
        return "deny", winner["NormId"]
    for e in esc:
        c = parse_condition(e["Value"])
        if c and fires({"Selector": c[0], "Operator": c[1], "Value": json.dumps(c[2]) if not isinstance(c[2], str) else c[2]}):
            return "escalate", e["NormId"]
    if winner:
        return winner["Decision"], winner["NormId"]
    return "allow", None


def hestia_eval(cfg, overlays, req):
    def first_match(c):
        for r in c["rules"]:
            m = r["match"]
            if "tools" in m and req.get("tool") not in m["tools"]:
                continue
            if "command_patterns" in m and not any(re.search(p, req.get("command") or "") for p in m["command_patterns"]):
                continue
            if "target_patterns" in m and not any(fnmatch.fnmatch(req.get("target") or "", p) for p in m["target_patterns"]):
                continue
            return r["decision"], r["id"]
        return c["default_policy"], None
    d, rid = first_match(cfg)
    ov = overlays.get(req.get("role"))
    if ov:
        d2, rid2 = first_match(ov)
        if SEVERITY[d2] > SEVERITY[d]:  # role overlay may only tighten (strictest fold)
            d, rid = d2, rid2
    return d, rid


# ------------------------------------------------------------------ society graph (turtle)
def turtle(rb):
    socs, slots = rows(rb, "Societies"), rows(rb, "RoleSlots")
    # fleet-shaped tables are optional, so a non-fleet rulebook (starter schema + Actors) projects too
    opt = lambda t: by_id(rb, t) if t in rb else {}
    machines, agents, principals, actors = opt("Machines"), opt("Agents"), opt("Principals"), opt("Actors")
    beings, roles = (rows(rb, "Beings") if "Beings" in rb else []), by_id(rb, "Roles")
    root = meta(rb, "root_society") or "fleet"
    lctof = lambda kind, i: f"lct:{kind}-{slug(i)}"
    L = [f"@prefix {p}: <{u}> ." for p, u in NS.items()] + [
        "", f"# generated by rulebook_to_web4 {TOOL_VERSION} from {rb['Name']} draft {meta(rb, 'draft')} — placeholder IRIs (lct:*) until real LCTs are bound.",
        "# rb:* terms are local provenance/binding extensions, not web4 vocabulary.", ""]

    def status(row):
        return f'rb:basis "{row.get("Basis") or "unknown"}" ; rb:confirmed {"true" if row.get("Confirmed") else "false"}'
    for s in socs:
        sid = lctof("society", s["SocietyId"])
        L.append(f'{sid} a web4:Society ; rdfs:label {json.dumps(s["DisplayName"])} ; rb:kind "{s["Kind"]}" ; rb:lawSurface "{s["LawSurface"]}" ;')
        L.append(f'    rb:conflictPolicy {json.dumps(s["ConflictPolicy"] or "")} ; {status(s)} .')
        if s["Parent"]:
            L.append(f'{sid} web4:memberOf {lctof("society", s["Parent"])} .')
        if s["HostMachine"]:
            L.append(f'{sid} rb:hostMachine {lctof("device", s["HostMachine"])} .')
        L.append("")
    for r in slots:
        rid = lctof("role", f"{r['Society']}-{r['SocietyRole'].replace(':', '-')}")
        soc = lctof("society", r["Society"])
        L.append(f'{rid} a web4:Role ; rdfs:label {json.dumps(r["SocietyRole"])} ; rb:baseMandatory {"true" if r["IsBaseMandatory"] else "false"} ; rb:basis "{r["Basis"]}" .')
        pred = {"sovereign": "web4:hasAuthority", "law-oracle": "web4:hasLawOracle", "witness": "web4:hasWitness", "auditor": "web4:hasAuditor"}.get(r["SocietyRole"], "rb:hasRole")
        L.append(f"{soc} {pred} {rid} .")
        if r["FilledByPrincipal"]:
            L.append(f'{lctof("human", r["FilledByPrincipal"])} web4:pairedWith {rid} .')
        if r["FilledByAgent"]:
            L.append(f'{lctof("ai", r["FilledByAgent"])} web4:pairedWith {rid} .')
        if r["FilledByText"]:
            L.append(f'{rid} rb:filledBy {json.dumps(r["FilledByText"])} .')
        L.append("")
    for p in principals.values():
        L.append(f'{lctof("human", p["PrincipalId"])} a web4:Entity ; rb:entityType "human" ; rdfs:label {json.dumps(p["DisplayName"])} ; web4:memberOf {lctof("society", root)} ; {status(p)} .')
    for a in actors.values():
        if a.get("Kind") == "ai-agent":
            role = roles.get(a.get("Role"), {}).get("Web4Role") or "citizen"
            L.append(f'{lctof("ai", a["ActorId"])} a web4:Entity ; rb:entityType "ai" ; web4:memberOf {lctof("society", root)} ;')
            L.append(f'    rb:role "{a.get("Role")}" ; rb:web4Role "{role}" ; rb:governed {"true" if a.get("IsGoverned") else "false"} ; {status(a)} .')
    for m in machines.values():
        L.append(f'{lctof("device", m["MachineId"])} a web4:Entity ; rb:entityType "device" ; rdfs:label {json.dumps(m["DisplayName"])} ; rb:lctId "{m["LctId"]}" ; {status(m)} .')
    for a in agents.values():
        home = f"h-{a['Machine']}" if a["Machine"] else "fleet"
        role = roles.get(a["Role"], {}).get("Web4Role") or "citizen"
        L.append(f'{lctof("ai", a["AgentId"])} a web4:Entity ; rb:entityType "ai" ; rb:harness "{a["Harness"]}" ; web4:memberOf {lctof("society", home)} ;')
        L.append(f'    rb:fleetRole "{a["Role"]}" ; rb:web4Role "{role}" ; rb:hestiaGated {"true" if a["IsHestiaGated"] else "false"} ; {status(a)} .')
    for b in beings:
        L.append(f'{lctof("ai", b["BeingId"])} a web4:Entity ; rb:entityType "ai" ; rb:being true ; rdfs:label "{b["InstanceSlug"]}" ; web4:memberOf {lctof("society", "h-" + b["Machine"])} .')
    L.append("")
    for r in rows(rb, "Rules"):
        rid = f"rb:rule-{r['RuleId']}"
        L.append(f'{rid} a rb:Rule ; rdfs:label {json.dumps(r["ShortName"])} ; rb:status "{r["Status"]}" ; rb:executability "{r["Executability"]}" ; rb:stakes "{r["Stakes"]}" .')
    for c in rows(rb, "Citations"):
        L.append(f'rb:rule-{c["Rule"]} prov:wasDerivedFrom rb:evidence-{slug(c["Evidence"])} .' if c["Stance"] != "contradicts"
                 else f'rb:rule-{c["Rule"]} rb:contradictedBy rb:evidence-{slug(c["Evidence"])} .')
    return "\n".join(L) + "\n"


# ------------------------------------------------------------------ lawbook fixture (PRD_LAWBOOK_IR §4)
def lawbook(rb):
    cites = rows(rb, "Citations")
    root = meta(rb, "root_society") or "fleet"
    rules = []
    for r in rows(rb, "Rules"):
        rules.append({
            "rule_id": r["RuleId"], "rule_version": 1, "short_name": r["ShortName"], "statement": r["Statement"],
            "modality": r["Modality"], "executability": r["Executability"], "stakes": r["Stakes"],
            "assertion_state": {"confirmed": "RatifiedLaw", "proposed": "CandidateLaw", "disputed": "DisputedClaim"}.get(r["Status"],
                "DisputedClaim" if r["IsConflicted"] else {"stated": "ElicitedPractice", "documented": "SourceAssertion", "observed": "ObservedPractice", "inferred": "DerivedFinding"}[r["Basis"]]),
            "authority_domain": f"society:{root}",
            "ratified_by": f"{root}.sovereign" if r["Status"] == "confirmed" else None,
            "effective_from": r["ConfirmedOn"], "effective_to": None,
            "evidence": [{"evidence": c["Evidence"], "stance": c["Stance"], "excerpt": c["Excerpt"]} for c in cites if c["Rule"] == r["RuleId"]],
            "norms": [n["NormId"] for n in rows(rb, "Norms") if n["Rule"] == r["RuleId"]],
        })
    slots = rows(rb, "RoleSlots")
    return {
        "lawbook_id": f"lawbook:{slug(rb['Name']).lower()}", "version": f"0.{meta(rb, 'draft')}.0",
        "source": {"rulebook": rb["Name"], "draft": meta(rb, "draft")}, "generated_by": f"rulebook_to_web4 {TOOL_VERSION}",
        "societies": [{"society": s["SocietyId"], "parent": s["Parent"], "law_surface": s["LawSurface"], "conflict_policy": s["ConflictPolicy"]} for s in rows(rb, "Societies")],
        "authority_roles": [{"slot": s["RoleSlotId"], "society": s["Society"], "role": s["SocietyRole"], "base_mandatory": s["IsBaseMandatory"],
                             "occupant": s["FilledByPrincipal"] or s["FilledByAgent"] or s["FilledByText"]} for s in slots],
        "rules": rules,
        "procedures": [{"procedure_id": f"proc-{r['RuleId']}", "rule": r["RuleId"], "statement": r["Statement"]} for r in rows(rb, "Rules") if r["Executability"] == "procedure"],
        "appeal_paths": sorted({n["EscalateTo"] for n in rows(rb, "Norms") if n["EscalateTo"]}),
        "test_cases": [{"case": s["ScenarioId"], "norm": s["Norm"], "society": s["Society"], "request": json.loads(s["Request"]),
                        "expected": {"decision": s["ExpectedDecision"], "winning_rule": s["ExpectedRule"]}} for s in rows(rb, "Scenarios")],
    }


# ------------------------------------------------------------------ main
def main(rb_path, out):
    rb, out = load(rb_path), Path(out)
    out.mkdir(parents=True, exist_ok=True)
    written, findings, conf = {}, [], []

    def write(rel, text):
        p = out / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
        written[rel] = hashlib.sha256(text.encode()).hexdigest()

    socs = by_id(rb, "Societies")
    projections = {}
    for sid, s in socs.items():
        for mode in ("candidate", "ratified"):
            norms, f = effective_norms(rb, sid, mode)
            findings += f
            if s["LawSurface"] == "hub":
                text, hn, esc, adm = hub_law(rb, sid, norms, mode)
                write(f"societies/{sid}/law.{mode}.yaml", text)
                for p in validate_hub(rb, sid, hn, esc, adm, f"0.{meta(rb, 'draft')}.0"):
                    findings.append(("blocking", "HubLawInvalid", f"{sid} {mode}: {p}"))
                if not hn and mode == "candidate":
                    findings.append(("advisory", "SocietyHasNoLaw", f"{sid}: no hub norms in the rulebook (live hub law, if any, stands)"))
                projections[(sid, mode, "hub")] = (norms, esc)
            # every society carries the local (hestia) rules it inherits; only hearths emit a PolicyConfig
            cfg, ov = hestia_configs(norms, mode)
            if s["LawSurface"] == "hestia":
                write(f"societies/{sid}/hestia-policy.{mode}.json", json.dumps(cfg, indent=2) + "\n")
                write(f"societies/{sid}/role-overlays.{mode}.json", json.dumps(ov, indent=2) + "\n")
            projections[(sid, mode, "hestia")] = (cfg, ov)

    # conformance: run every scenario through the candidate projection of its society
    for sc in rows(rb, "Scenarios"):
        req, sid = json.loads(sc["Request"]), sc["Society"]
        if socs[sid]["LawSurface"] == "hub":
            norms, esc = projections[(sid, "candidate", "hub")]
            got = hub_eval([n for n in norms if n["Surface"] == "hub-norm"], esc, req)
        else:
            cfg, ov = projections[(sid, "candidate", "hestia")]
            got = hestia_eval(cfg, ov, req)
        want = (sc["ExpectedDecision"], sc["ExpectedRule"])
        refused = by_id(rb, "Norms")[sc["Norm"]]["CompileMode"] == "refused"
        ok = got == want
        conf.append({"case": sc["ScenarioId"], "society": sid, "norm": sc["Norm"], "expected": want, "got": got,
                     "result": "pass" if ok else ("expected-miss (norm refused)" if refused else "FAIL")})
    write("conformance.json", json.dumps(conf, indent=2) + "\n")
    cm = ["# conformance — candidate projection vs scenario corpus", "",
          "reference oracle = test oracle transcribed from hub-law-schema.md §1 (hub) and hestia's first-match + strictest-fold semantics. "
          "the authoritative run is the same corpus through web4-policy and hestia on a fleet machine.", "",
          "| case | society | norm | expected | got | result |", "|---|---|---|---|---|---|"]
    cm += [f"| {c['case']} | {c['society']} | {c['norm']} | {c['expected'][0]} / {c['expected'][1] or 'default'} | {c['got'][0]} / {c['got'][1] or 'default'} | {c['result']} |" for c in conf]
    write("conformance.md", "\n".join(cm) + "\n")
    for c in conf:
        if c["result"] == "FAIL":
            findings.append(("blocking", "ProjectionDecisionMismatch", f"{c['case']}: expected {c['expected']}, got {c['got']}"))

    # rulebook-level witnesses the transpiler cares about
    slots = rows(rb, "RoleSlots")
    filled = {(s["Society"], s["SocietyRole"]) for s in slots if not s["IsUnfilled"]}
    declared = {(s["Society"], s["SocietyRole"]) for s in slots}
    for n in rows(rb, "Norms"):
        if n["CompileMode"] == "refused":
            findings.append(("blocking", "NormRefusedRuleConflicted", f"{n['NormId']} ({n['Rule']}) — resolve the conflict, then it compiles"))
        if n["EscalateTo"] and (n["Society"], n["EscalateTo"]) in declared and (n["Society"], n["EscalateTo"]) not in filled:
            findings.append(("blocking", "EscalationTargetUnoccupied", f"{n['NormId']} escalates to {n['Society']}.{n['EscalateTo']}, which nobody fills"))
    for s in rows(rb, "Societies"):
        if s["Kind"] != "machine-hestia":
            missing = [r for r in BASE_ROLES if (s["SocietyId"], r) not in declared]
            unfilled = [r for r in BASE_ROLES if (s["SocietyId"], r) in declared and (s["SocietyId"], r) not in filled]
            if missing:
                findings.append(("advisory", "BaseRolesUndeclared", f"{s['SocietyId']}: {', '.join(missing)}"))
            if unfilled:
                findings.append(("advisory", "RoleUnoccupied", f"{s['SocietyId']}: {', '.join(unfilled)}"))
        else:
            findings.append(("advisory", "HearthRolesAssumed", f"{s['SocietyId']}: base roles not modelled; assume multi-hat (the operator fills all, hestia daemon = policy-entity) until confirmed"))
    for r in rows(rb, "Rules"):
        if r["Stakes"] == "high" and r["Executability"] in ("review", "procedure") and r["Status"] != "retired":
            findings.append(("advisory", "HighStakesNotMachineCheckable", f"{r['RuleId']} {r['ShortName']} ({r['Executability']}) — needs a procedure/witness design, not a norm"))
    n_enf = sum(1 for n in rows(rb, "Norms") if n["CompileMode"] == "enforce")
    findings.append(("advisory", "RatifiedVsCandidate", f"{n_enf} of {len(rows(rb, 'Norms'))} norms are ratified; everything else ships as candidate/shadow only"))
    findings.append(("advisory", "NamespaceAmbiguity", "hub-law.ttl uses https://web4.io/ontology/ while SAL §7.2 examples use https://web4.io/ontology# — graph follows the ontology file; needs a spec ruling"))
    findings.append(("advisory", "PriorityConventionInverted", "hub law: higher priority wins; hestia PolicyRule: lower evaluates first — hestia priorities emitted as -(hub priority), so every law rule is evaluated before the preset rules (priority 0..10); 1000 - p (v0.1.0) put law after them, and a preset warn-network shadowed a law deny on the same act (found 2026-11-17)"))
    findings.append(("advisory", "HestiaHasNoEscalate", "hestia local PolicyDecision is allow|warn|deny; a local 'escalate' would need the scope-refusal escalation path (hestia #1232) — none emitted"))

    write("society-graph.ttl", turtle(rb))
    write("lawbook.json", json.dumps(lawbook(rb), indent=2, ensure_ascii=False) + "\n")
    wm = [f"# transpiler witnesses — {rb['Name']} draft {meta(rb, 'draft')}", "",
          "blocking = must be resolved before the ratified projection may be applied. advisory = known gap or design note.", ""]
    for sev in ("blocking", "advisory"):
        fs = sorted({f for f in findings if f[0] == sev}, key=lambda f: (f[1], f[2]))
        wm += [f"## {sev} ({len(fs)})", ""] + [f"- **{k}** — {d}" for _, k, d in fs] + [""]
    write("witnesses.md", "\n".join(wm))

    src = Path(rb_path).read_bytes()
    manifest = {"tool": f"rulebook_to_web4 {TOOL_VERSION}", "generated": dt.datetime.now().isoformat(timespec="seconds"),
                "input": {"path": Path(rb_path).name, "sha256": hashlib.sha256(src).hexdigest(), "draft": meta(rb, "draft")},
                "outputs": dict(sorted(written.items())), "local_only": True, "network": "none"}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    nb = sum(1 for f in set(findings) if f[0] == "blocking")
    fails = sum(1 for c in conf if c["result"] == "FAIL")
    print(f"web4 projection → {out}: {len(written)} files, {len(conf)} scenarios ({fails} fail), {nb} blocking findings")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(sys.argv[1], sys.argv[2]))
