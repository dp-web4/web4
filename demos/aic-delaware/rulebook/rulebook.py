# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Metalinxx Inc.
"""rulebook.py — local stand-in for the effortless toolchain, stdlib only.

the rulebook JSON is the source of truth. this script only derives from it:

  python3 rulebook.py check                 lint the rulebook against the ERB dialect + referential integrity
  python3 rulebook.py build                 recompute every derived column into the JSON, then write the projections
  python3 rulebook.py answer q-02 "text"    record the operator's answer to an interview question (then rebuild)
  python3 rulebook.py confirm r-013 [...]   mark rules confirmed by the operator today (then rebuild)
  python3 rulebook.py set Table RowId Field value   edit one raw cell (then rebuild)

projections written by build:
  rulespeak/<name>-rulebook.md  human-readable rulebook + live witnesses
  interview.md                  the open operator questions

it evaluates the subset of the excel dialect this rulebook uses (comparisons, AND/OR/NOT/IF,
CONCAT, COUNTIFS/SUMIFS, INDEX/MATCH, ROUND). EJ's rulebook-to-postgres / -python / -rulespeak
transpilers are the real substrates; this is one more projection, and should agree with them.
"""
import datetime as dt
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RB = next((HERE / "effortless-rulebook").glob("*rulebook.json"))
TODAY = dt.date.today().isoformat()

TRAPS = [(r"\bISBLANK\(", "ISBLANK is emitted as NULL — use {{X}} = \"\""),
         (r"\bNULLIF\(", "NULLIF is not translated — guard with IF(x = 0, 0, ...)"),
         (r"(?<![A-Z])LOOKUP\(", "bare LOOKUP is not translated — use INDEX/MATCH"),
         (r"\bCOUNTIF\(", "single COUNTIF is mis-emitted — use COUNTIFS"),
         (r"\b(AND|OR)\([^()]*\bIF\(", "IF nested in AND/OR is emitted as text")]


def load():
    return json.loads(RB.read_text(encoding="utf-8"))


def save(rb):
    RB.write_text(json.dumps(rb, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def tables(rb):
    return {k: v for k, v in rb.items() if isinstance(v, dict) and "schema" in v}


def pk(t):
    return t["schema"][0]["name"]


# ------------------------------------------------------------------ evaluator
class Col(list):
    pass


class SelfRef:
    """Table!{{F}} naming the row's own table: a criterion/key where a value is wanted,
    the whole column where a range is wanted (COUNTIFS ranges, MATCH/INDEX ranges)."""
    def __init__(self, val, col):
        self.val, self.col = val, col


def _v(x):
    return x.val if isinstance(x, SelfRef) else x


def _c(x):
    return x.col if isinstance(x, SelfRef) else x


def _eq(a, b):
    if a is None or b is None:
        return a is b
    if isinstance(a, bool) or isinstance(b, bool):
        return bool(a) == bool(b)
    try:
        return float(a) == float(b)
    except (TypeError, ValueError):
        return str(a) == str(b)


def COUNTIFS(*args):
    pairs = [(_c(r), _v(c)) for r, c in zip(args[0::2], args[1::2])]
    n = len(pairs[0][0])
    return sum(1 for i in range(n) if all(_eq(rng[i], crit) for rng, crit in pairs))


def SUMIFS(total, *args):
    total = _c(total)
    pairs = [(_c(r), _v(c)) for r, c in zip(args[0::2], args[1::2])]
    return sum(float(total[i] or 0) for i in range(len(total)) if all(_eq(r[i], c) for r, c in pairs))


def MATCH(val, rng, _mode=0):
    val, rng = _v(val), _c(rng)
    for i, v in enumerate(rng):
        if _eq(v, val):
            return i
    return None


def INDEX(rng, i):
    rng = _c(rng)
    return None if i is None else rng[i]


FUNCS = {
    "AND": lambda *a: all(bool(x) for x in a), "OR": lambda *a: any(bool(x) for x in a),
    "NOT": lambda a: not bool(a), "IF": lambda c, a, b=None: a if c else b,
    "CONCAT": lambda *a: "".join("" if x is None else str(x) for x in a),
    "COALESCE": lambda *a: next((x for x in a if x not in (None, "")), None),
    "ROUND": lambda x, n: round(float(x or 0), int(n)), "COUNTIFS": COUNTIFS, "SUMIFS": SUMIFS,
    "INDEX": INDEX, "MATCH": MATCH, "__BLANK": lambda x: x is None or x == "",
}


def to_python(formula):
    s = formula.strip().lstrip("=")
    s = re.sub(r"(\w+)!\{\{(\w+)\}\}", r'__C("\1","\2")', s)
    s = re.sub(r"\{\{(\w+)\}\}", r'__R("\1")', s)
    s = s.replace("TRUE()", "True").replace("FALSE()", "False")
    # ERB blank checks are null-safe: {{X}} = "" is true for null and for ""
    s = re.sub(r'(__R\("\w+"\))\s*<>\s*""', r'(not __BLANK(\1))', s)
    s = re.sub(r'(__R\("\w+"\))\s*=\s*""', r'__BLANK(\1)', s)
    out, i, inq = [], 0, False
    while i < len(s):
        ch = s[i]
        if ch == '"':
            inq = not inq
            out.append(ch)
        elif not inq and s.startswith("<>", i):
            out.append("!=")
            i += 1
        elif not inq and ch == "=" and (i == 0 or s[i - 1] not in "<>!=") and s[i + 1:i + 2] != "=":
            out.append("==")
        else:
            out.append(ch)
        i += 1
    return "".join(out)


def _cmp_safe(expr):
    # None-safe comparisons: wrap numeric comparisons so None counts as 0
    return expr


def evaluate(rb, passes=8):
    T = tables(rb)
    compiled = {}
    for tn, t in T.items():
        for f in t["schema"]:
            if f.get("formula"):
                compiled[(tn, f["name"])] = compile(to_python(f["formula"]), f"{tn}.{f['name']}", "eval")
    for _ in range(passes):
        before = json.dumps({k: v["data"] for k, v in T.items()}, sort_keys=True, default=str)
        for tn, t in T.items():
            for f in t["schema"]:
                if f["type"] == "relationship" and f.get("isReversed"):
                    child = T[f["RelatedTo"]]
                    for row in t["data"]:
                        ids = [c[pk(child)] for c in child["data"] if c.get(f["InverseField"]) == row[pk(t)]]
                        row[f["name"]] = ", ".join(ids) or None
            for f in t["schema"]:
                code = compiled.get((tn, f["name"]))
                if not code:
                    continue
                for row in t["data"]:
                    def C(table, field, _row=row, _tn=tn):
                        col = Col(r.get(field) for r in T[table]["data"])
                        return SelfRef(_row.get(field), col) if table == _tn else col
                    env = dict(FUNCS, __C=C, __R=lambda field, _row=row: _row.get(field))
                    try:
                        v = eval(code, {"__builtins__": {}}, env)
                    except TypeError:
                        v = None  # comparison against a not-yet-computed value; settles next pass
                    if f["datatype"] in ("number", "integer") and isinstance(v, (int, float)) and not isinstance(v, bool):
                        v = int(v) if float(v).is_integer() else v
                    row[f["name"]] = v
        after = json.dumps({k: v["data"] for k, v in T.items()}, sort_keys=True, default=str)
        if after == before:
            return
    raise SystemExit("derived columns did not settle — circular formula?")


# ------------------------------------------------------------------ lint
def check(rb):
    T, problems = tables(rb), []
    for tn, t in T.items():
        names = [f["name"] for f in t["schema"]]
        key = pk(t)
        if not key.endswith("Id") and tn != "__meta__":
            problems.append(f"{tn}: first column {key} should be a raw <Entity>Id (cr-25)")
        ids = [r.get(key) for r in t["data"]]
        if len(ids) != len(set(ids)):
            problems.append(f"{tn}: duplicate {key}")
        for r in t["data"]:
            for k in r:
                if k not in names:
                    problems.append(f"{tn}.{r.get(key)}: stray key {k}")
            for f in t["schema"]:
                if f["type"] == "raw" and f.get("nullable") is False and r.get(f["name"]) in (None, ""):
                    problems.append(f"{tn}.{r.get(key)}: {f['name']} is required")
        for f in t["schema"]:
            rel = f.get("RelatedTo")
            if rel and rel not in T:
                problems.append(f"{tn}.{f['name']}: RelatedTo {rel} missing")
                continue
            if f["type"] == "relationship" and not f.get("isReversed"):
                target_ids = {r[pk(T[rel])] for r in T[rel]["data"]}
                for r in t["data"]:
                    v = r.get(f["name"])
                    if v not in (None, "") and v not in target_ids:
                        problems.append(f"{tn}.{r.get(key)}.{f['name']}: {v} not in {rel}")
                inv = [g for g in T[rel]["schema"] if g.get("isReversed") and g.get("InverseField") == f["name"] and g["RelatedTo"] == tn]
                if not inv:
                    problems.append(f"{tn}.{f['name']}: no reverse relationship declared on {rel}")
            fm = f.get("formula")
            if not fm:
                continue
            for pat, why in TRAPS:
                if re.search(pat, fm):
                    problems.append(f"{tn}.{f['name']}: {why}")
            for ref_t, ref_f in re.findall(r"(\w+)!\{\{(\w+)\}\}", fm):
                if ref_t not in T or ref_f not in [g["name"] for g in T[ref_t]["schema"]]:
                    problems.append(f"{tn}.{f['name']}: unknown ref {ref_t}!{{{{{ref_f}}}}}")
            for ref_f in re.findall(r"(?<!!)\{\{(\w+)\}\}", fm):
                if ref_f not in names:
                    problems.append(f"{tn}.{f['name']}: unknown ref {{{{{ref_f}}}}}")
            m = re.search(r"MATCH\(\w+!\{\{\w+\}\}, (\w+)!\{\{(\w+)\}\}", fm)
            if m and m.group(2) != pk(T[m.group(1)]):
                problems.append(f"{tn}.{f['name']}: MATCH must target {m.group(1)}'s Id")
    return problems


# ------------------------------------------------------------------ projections
def rows(rb, tn):
    return rb[tn]["data"]


def md_table(head, body):
    out = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    for b in body:
        out.append("| " + " | ".join("" if c is None else str(c).replace("|", "/").replace("\n", " ") for c in b) + " |")
    return "\n".join(out)


def meta(rb, key):
    return next((r["StringValue"] or r["JsonValue"] or "" for r in rows(rb, "__meta__") if r["MetaKey"] == key), "")


def witnesses(rb):
    """every boolean derived column whose Description starts with 'Witness:' is a computed check.
    returns [(table, label, [row names where true])]."""
    out = []
    for tn, t in tables(rb).items():
        for f in t["schema"]:
            d = f.get("Description", "")
            if f.get("formula") and f["datatype"] == "boolean" and d.startswith("Witness:"):
                hits = [str(r.get("Name") or r[pk(t)]) for r in t["data"] if r.get(f["name"])]
                out.append((tn, d[len("Witness:"):].strip().rstrip("."), hits))
    return out


def projection_columns(rb):
    raw = meta(rb, "projection_columns")
    return json.loads(raw) if raw else {}


def rule_section(rb):
    R = rows(rb, "Rules")
    cites = rows(rb, "Citations") if "Citations" in rb else []
    L = ["## rules", ""]
    domains = rows(rb, "RuleDomains") if "RuleDomains" in rb else [{"DomainId": None, "Title": "rules"}]
    for d in domains:
        rs = [r for r in R if d["DomainId"] is None or r.get("Domain") == d["DomainId"]]
        if not rs:
            continue
        L += [f"### {d['Title']}", ""]
        for r in rs:
            flags = [r["RuleState"], r["Basis"], f"enforced by {r['Enforcement']}", f"{r['Stakes']} stakes"]
            if r.get("AppliesTo") and r["AppliesTo"] != "all agents":
                flags.append(f"applies to {r['AppliesTo']}")
            L.append(f"**{r['RuleId']} · {r['ShortName']}** — {r['Statement']}  ")
            L.append(f"<sub>{' · '.join(flags)} · evidence {r['SupportCount']} for / {r['ContradictCount']} against</sub>")
            for c in cites:
                if c["Rule"] == r["RuleId"] and c["Stance"] != "supports":
                    L.append(f"<sub>↳ {c['Stance']}: {c['EvidenceTitle']} — {c['Excerpt']}</sub>")
            L.append("")
    return L


def rulespeak(rb):
    R = rows(rb, "Rules")
    Q = rows(rb, "OpenQuestions") if "OpenQuestions" in rb else []
    state = {}
    for r in R:
        state[r["RuleState"]] = state.get(r["RuleState"], 0) + 1
    L = [f"# {rb['Name']}", "", f"_{meta(rb, 'tagline')}_", "",
         f"draft {meta(rb, 'draft')} · situated {meta(rb, 'situated_on')} by {meta(rb, 'situated_by')} · generated {TODAY} from `{RB.relative_to(HERE).as_posix()}` — do not edit this file.", "",
         f"> {meta(rb, 'authority_rule')}", "",
         "## where it stands", "",
         f"{len(R)} rules — " + (", ".join(f"{n} {s}" for s, n in sorted(state.items())) or "none yet") + ". "
         f"{sum(1 for q in Q if q['IsOpen'])} open questions (see `interview.md`).", "",
         "### computed witnesses", "", "derived by formula from the rows, not asserted. each one is a gap, a conflict, or a modelling error to check.", ""]
    for tn, label, hits in witnesses(rb):
        L.append(f"- **{label}** ({len(hits)}){'' if hits else ''}: " + (", ".join(hits) if hits else "none"))
    L += [""] + rule_section(rb)
    skip = {"__meta__", "Rules", "OpenQuestions", "Citations", "RuleDomains"}
    cols = projection_columns(rb)
    for tn, t in tables(rb).items():
        if tn in skip or not t["data"]:
            continue
        names = cols.get(tn) or [f["name"] for f in t["schema"] if f["type"] in ("raw", "relationship") and not f.get("isReversed")][:7]
        L += [f"## {tn}", "", t["Description"], "",
              md_table(names, [[_fmt(r.get(c)) for c in names] for r in t["data"]]), ""]
    nr = json.loads(meta(rb, "evidence_not_reached") or "[]")
    if nr:
        L += ["**evidence not reached in this pass** (rows touching these are weaker than they look):", ""] + [f"- {x}" for x in nr] + [""]
    return "\n".join(L)


def _fmt(v):
    if v is True:
        return "yes"
    if v is False:
        return "no"
    return "—" if v in (None, "") else v


def interview(rb):
    Q = rows(rb, "OpenQuestions")
    R = {r["RuleId"]: r for r in rows(rb, "Rules")}
    open_q = [q for q in Q if q["IsOpen"]]
    L = [f"# {rb['Name']} — operator interview", "",
         f"generated {TODAY} · {len(open_q)} open of {len(Q)}. ",
         "answer in any form (a word is fine). each answer gets recorded with `python3 rulebook.py answer <id> \"...\"` and the rows it touches are confirmed, amended, or retired.", ""]
    for q in open_q:
        L.append(f"### {q['QuestionId']} · {q['Question']}")
        L.append("")
        L.append(f"why: {q['WhyItMatters']}  ")
        if q["Rule"]:
            r = R[q["Rule"]]
            L.append(f"draft rule {r['RuleId']}: _{r['Statement']}_  ")
        L.append(f"likely answers: {q['SuggestedAnswers']}")
        L.append("")
    done = [q for q in Q if not q["IsOpen"]]
    if done:
        L += ["## answered", ""] + [f"- **{q['QuestionId']}** ({q['AnsweredOn']}): {q['Answer']}" for q in done] + [""]
    return "\n".join(L)


def build():
    rb = load()
    problems = check(rb)
    if problems:
        raise SystemExit("check failed:\n  " + "\n  ".join(problems))
    evaluate(rb)
    save(rb)
    (HERE / "rulespeak").mkdir(exist_ok=True)
    (HERE / "rulespeak" / f"{RB.stem}.md").write_text(rulespeak(rb), encoding="utf-8")
    (HERE / "interview.md").write_text(interview(rb), encoding="utf-8")
    print(f"built {RB.name}: {len(rows(rb, 'Rules'))} rules, "
          f"{sum(1 for q in rows(rb, 'OpenQuestions') if q['IsOpen'])} open questions")


def set_cell(table, row_id, field, value):
    rb = load()
    t = rb[table]
    f = next((g for g in t["schema"] if g["name"] == field), None)
    if not f or f["type"] not in ("raw", "relationship") or f.get("isReversed"):
        raise SystemExit(f"{table}.{field} is not a raw column")
    row = next((r for r in t["data"] if r[pk(t)] == row_id), None)
    if not row:
        raise SystemExit(f"no {table} row {row_id}")
    if f["datatype"] == "boolean":
        value = value.lower() in ("1", "true", "yes", "y")
    elif f["datatype"] in ("number", "integer") and value != "":
        value = float(value) if "." in value else int(value)
    row[field] = None if value == "" else value
    save(rb)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    cmd, args = (sys.argv[1] if len(sys.argv) > 1 else "build"), sys.argv[2:]
    if cmd == "check":
        p = check(load())
        print("\n".join(p) if p else "ok")
        sys.exit(1 if p else 0)
    elif cmd == "build":
        build()
    elif cmd == "answer":
        set_cell("OpenQuestions", args[0], "Answer", " ".join(args[1:]))
        set_cell("OpenQuestions", args[0], "AnsweredOn", TODAY)
        set_cell("OpenQuestions", args[0], "Status", "answered")
        build()
    elif cmd == "confirm":
        for rid in args:
            set_cell("Rules", rid, "Status", "confirmed")
            set_cell("Rules", rid, "ConfirmedOn", TODAY)
        build()
    elif cmd == "set":
        set_cell(*args[:3], " ".join(args[3:]))
        build()
    else:
        print(__doc__)
