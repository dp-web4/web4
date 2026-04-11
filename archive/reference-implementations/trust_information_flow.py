"""
Trust Information Flow Control for Web4
Session 34, Track 3

Lattice-based information flow control for trust data:
- Security lattice (levels and dominance relation)
- Non-interference property verification
- Trust classification labels (public, confidential, secret, top-secret)
- Information flow rules for trust attestations
- Declassification and endorsement
- Covert channel detection
- Trust data tainting and propagation
- Bell-LaPadula (no read up, no write down) for trust
"""

from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Set, FrozenSet
from collections import defaultdict
from enum import IntEnum


# ─── Security Lattice ────────────────────────────────────────────

class TrustLevel(IntEnum):
    """Security levels for trust information (ordered lattice)."""
    PUBLIC = 0
    INTERNAL = 1
    CONFIDENTIAL = 2
    SECRET = 3
    TOP_SECRET = 4


@dataclass(frozen=True)
class SecurityLabel:
    """A security label with level and compartments."""
    level: TrustLevel
    compartments: FrozenSet[str] = frozenset()

    def dominates(self, other: 'SecurityLabel') -> bool:
        """self >= other in the lattice (can read other's data)."""
        return (self.level >= other.level and
                self.compartments >= other.compartments)

    def __le__(self, other):
        return other.dominates(self)

    def __ge__(self, other):
        return self.dominates(other)

    def __repr__(self):
        comps = ",".join(sorted(self.compartments)) if self.compartments else ""
        suffix = f":{{{comps}}}" if comps else ""
        return f"{self.level.name}{suffix}"


def join_labels(a: SecurityLabel, b: SecurityLabel) -> SecurityLabel:
    """Least upper bound (join) in the lattice."""
    return SecurityLabel(
        level=TrustLevel(max(a.level, b.level)),
        compartments=a.compartments | b.compartments
    )


def meet_labels(a: SecurityLabel, b: SecurityLabel) -> SecurityLabel:
    """Greatest lower bound (meet) in the lattice."""
    return SecurityLabel(
        level=TrustLevel(min(a.level, b.level)),
        compartments=a.compartments & b.compartments
    )


# ─── Information Flow Graph ──────────────────────────────────────

@dataclass
class FlowVariable:
    """A variable in the information flow analysis."""
    name: str
    label: SecurityLabel
    value: object = None


@dataclass
class FlowEdge:
    """An information flow from source to sink."""
    source: str
    sink: str
    flow_type: str = "explicit"  # "explicit", "implicit", "covert"


class InformationFlowGraph:
    """Track information flows between labeled variables."""

    def __init__(self):
        self.variables: Dict[str, FlowVariable] = {}
        self.flows: List[FlowEdge] = []

    def add_variable(self, name: str, label: SecurityLabel, value=None):
        self.variables[name] = FlowVariable(name, label, value)

    def add_flow(self, source: str, sink: str, flow_type: str = "explicit"):
        self.flows.append(FlowEdge(source, sink, flow_type))

    def check_flow_allowed(self, source: str, sink: str) -> bool:
        """
        Check if information can flow from source to sink.
        Allowed only if sink.label >= source.label (no downward flow).
        """
        src = self.variables.get(source)
        snk = self.variables.get(sink)
        if not src or not snk:
            return False
        return snk.label.dominates(src.label)

    def find_violations(self) -> List[FlowEdge]:
        """Find all flows that violate the security policy."""
        violations = []
        for flow in self.flows:
            if not self.check_flow_allowed(flow.source, flow.sink):
                violations.append(flow)
        return violations

    def tainted_from(self, source: str) -> Set[str]:
        """Find all variables transitively tainted by source."""
        tainted = set()
        queue = [source]
        while queue:
            current = queue.pop(0)
            if current in tainted:
                continue
            tainted.add(current)
            for flow in self.flows:
                if flow.source == current and flow.sink not in tainted:
                    queue.append(flow.sink)
        return tainted - {source}


# ─── Non-Interference Checker ────────────────────────────────────

@dataclass
class Program:
    """A simple imperative program for non-interference analysis."""
    statements: List[Tuple[str, ...]]
    # ("assign", target, source)
    # ("if", condition_var, then_target, then_value)
    # ("output", source, channel)


def check_non_interference(program: Program,
                             labels: Dict[str, SecurityLabel],
                             output_level: TrustLevel) -> List[str]:
    """
    Check if high-security inputs can influence low-security outputs.
    Returns list of violation descriptions.

    Non-interference: changing high inputs doesn't change low outputs.
    """
    violations = []
    output_label = SecurityLabel(output_level)

    for stmt in program.statements:
        if stmt[0] == "assign":
            _, target, source = stmt
            src_label = labels.get(source, SecurityLabel(TrustLevel.PUBLIC))
            tgt_label = labels.get(target, SecurityLabel(TrustLevel.PUBLIC))
            # Source must not be higher than target
            if not tgt_label.dominates(src_label):
                violations.append(
                    f"Illegal flow: {source}({src_label}) → {target}({tgt_label})")

        elif stmt[0] == "if":
            _, cond_var = stmt[1], stmt[1]
            cond_label = labels.get(stmt[1], SecurityLabel(TrustLevel.PUBLIC))
            # Implicit flow: condition influences what gets executed
            if len(stmt) > 2:
                target = stmt[2]
                tgt_label = labels.get(target, SecurityLabel(TrustLevel.PUBLIC))
                if not tgt_label.dominates(cond_label):
                    violations.append(
                        f"Implicit flow: if({stmt[1]}({cond_label})) → {target}({tgt_label})")

        elif stmt[0] == "output":
            _, source = stmt[0], stmt[1]
            src_label = labels.get(stmt[1], SecurityLabel(TrustLevel.PUBLIC))
            if not output_label.dominates(src_label):
                violations.append(
                    f"Output leak: {stmt[1]}({src_label}) → output({output_label})")

    return violations


# ─── Bell-LaPadula Model ────────────────────────────────────────

@dataclass
class Subject:
    """An entity (agent/user) with a clearance level."""
    name: str
    clearance: SecurityLabel


@dataclass
class Object:
    """A data object with a classification."""
    name: str
    classification: SecurityLabel


class BellLaPadula:
    """
    Bell-LaPadula mandatory access control:
    - Simple Security (no read up): subject can read object only if clearance >= classification
    - *-Property (no write down): subject can write object only if classification >= clearance
    """

    def __init__(self):
        self.subjects: Dict[str, Subject] = {}
        self.objects: Dict[str, Object] = {}
        self.access_log: List[Tuple[str, str, str, bool]] = []

    def add_subject(self, name: str, clearance: SecurityLabel):
        self.subjects[name] = Subject(name, clearance)

    def add_object(self, name: str, classification: SecurityLabel):
        self.objects[name] = Object(name, classification)

    def can_read(self, subject_name: str, object_name: str) -> bool:
        """Simple Security Property: no read up."""
        s = self.subjects.get(subject_name)
        o = self.objects.get(object_name)
        if not s or not o:
            return False
        allowed = s.clearance.dominates(o.classification)
        self.access_log.append((subject_name, "read", object_name, allowed))
        return allowed

    def can_write(self, subject_name: str, object_name: str) -> bool:
        """*-Property: no write down."""
        s = self.subjects.get(subject_name)
        o = self.objects.get(object_name)
        if not s or not o:
            return False
        allowed = o.classification.dominates(s.clearance)
        self.access_log.append((subject_name, "write", object_name, allowed))
        return allowed

    def violations(self) -> List[Tuple[str, str, str]]:
        """Return all denied access attempts."""
        return [(s, op, o) for s, op, o, allowed in self.access_log if not allowed]


# ─── Declassification ───────────────────────────────────────────

@dataclass
class DeclassificationPolicy:
    """Policy for controlled declassification of trust data."""
    from_label: SecurityLabel
    to_label: SecurityLabel
    condition: str           # e.g., "approved_by_admin", "after_embargo"
    approved: bool = False

    @property
    def is_downgrade(self) -> bool:
        return self.from_label.level > self.to_label.level


def declassify(variable: FlowVariable, policy: DeclassificationPolicy) -> FlowVariable:
    """Apply declassification if policy is approved."""
    if not policy.approved:
        return variable  # No change
    if not policy.from_label.dominates(variable.label):
        return variable  # Variable not at required level
    return FlowVariable(variable.name, policy.to_label, variable.value)


# ─── Covert Channel Analysis ────────────────────────────────────

def detect_covert_channels(ifg: InformationFlowGraph) -> List[FlowEdge]:
    """
    Detect potential covert channels: flows through shared resources,
    timing, or implicit paths that bypass the label check.
    """
    covert = []
    for flow in ifg.flows:
        if flow.flow_type in ("covert", "implicit"):
            if not ifg.check_flow_allowed(flow.source, flow.sink):
                covert.append(flow)
    return covert


# ══════════════════════════════════════════════════════════════════
#  TESTS
# ══════════════════════════════════════════════════════════════════

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
    print("Trust Information Flow Control for Web4")
    print("Session 34, Track 3")
    print("=" * 70)

    # ── §1 Security Lattice ──────────────────────────────────────
    print("\n§1 Security Lattice\n")

    pub = SecurityLabel(TrustLevel.PUBLIC)
    conf = SecurityLabel(TrustLevel.CONFIDENTIAL)
    sec = SecurityLabel(TrustLevel.SECRET)
    ts = SecurityLabel(TrustLevel.TOP_SECRET)

    check("pub_le_conf", pub <= conf)
    check("conf_le_sec", conf <= sec)
    check("sec_le_ts", sec <= ts)
    check("pub_le_ts", pub <= ts)
    check("ts_not_le_pub", not (ts <= pub))
    check("reflexive", sec <= sec)

    # Compartments
    sci = SecurityLabel(TrustLevel.SECRET, frozenset({"SCI"}))
    sar = SecurityLabel(TrustLevel.SECRET, frozenset({"SAR"}))
    both = SecurityLabel(TrustLevel.SECRET, frozenset({"SCI", "SAR"}))

    check("sci_not_dom_sar", not sci.dominates(sar))  # incomparable
    check("both_dom_sci", both.dominates(sci))
    check("both_dom_sar", both.dominates(sar))

    # ── §2 Join and Meet ─────────────────────────────────────────
    print("\n§2 Join and Meet\n")

    j = join_labels(pub, sec)
    check("join_level", j.level == TrustLevel.SECRET)

    m = meet_labels(conf, sec)
    check("meet_level", m.level == TrustLevel.CONFIDENTIAL)

    j_comp = join_labels(sci, sar)
    check("join_compartments", j_comp.compartments == frozenset({"SCI", "SAR"}))

    m_comp = meet_labels(sci, sar)
    check("meet_compartments", m_comp.compartments == frozenset())

    # ── §3 Information Flow Graph ────────────────────────────────
    print("\n§3 Information Flow Graph\n")

    ifg = InformationFlowGraph()
    ifg.add_variable("trust_score", sec)
    ifg.add_variable("public_summary", pub)
    ifg.add_variable("audit_log", conf)

    # Legal: public → confidential (upward)
    ifg.add_flow("public_summary", "audit_log")
    check("upward_flow_legal", ifg.check_flow_allowed("public_summary", "audit_log"))

    # Illegal: secret → public (downward)
    ifg.add_flow("trust_score", "public_summary")
    check("downward_flow_illegal", not ifg.check_flow_allowed("trust_score", "public_summary"))

    # Find violations
    violations = ifg.find_violations()
    check("one_violation", len(violations) == 1)
    check("violation_is_downward", violations[0].source == "trust_score")

    # ── §4 Taint Propagation ─────────────────────────────────────
    print("\n§4 Taint Propagation\n")

    ifg2 = InformationFlowGraph()
    ifg2.add_variable("source", sec)
    ifg2.add_variable("mid1", sec)
    ifg2.add_variable("mid2", sec)
    ifg2.add_variable("sink", sec)

    ifg2.add_flow("source", "mid1")
    ifg2.add_flow("mid1", "mid2")
    ifg2.add_flow("mid2", "sink")

    tainted = ifg2.tainted_from("source")
    check("taint_reaches_sink", "sink" in tainted)
    check("taint_reaches_mid", "mid1" in tainted and "mid2" in tainted)
    check("taint_count", len(tainted) == 3)

    # Isolated variable not tainted
    ifg2.add_variable("isolated", sec)
    tainted2 = ifg2.tainted_from("source")
    check("isolated_not_tainted", "isolated" not in tainted2)

    # ── §5 Non-Interference ──────────────────────────────────────
    print("\n§5 Non-Interference\n")

    labels = {
        "secret_key": SecurityLabel(TrustLevel.SECRET),
        "public_input": SecurityLabel(TrustLevel.PUBLIC),
        "result": SecurityLabel(TrustLevel.PUBLIC),
    }

    # Violation: assigning secret to public
    prog1 = Program(statements=[
        ("assign", "result", "secret_key"),  # illegal
    ])
    violations_ni = check_non_interference(prog1, labels, TrustLevel.PUBLIC)
    check("ni_violation_detected", len(violations_ni) > 0)

    # Legal: public to public
    prog2 = Program(statements=[
        ("assign", "result", "public_input"),
    ])
    violations_ok = check_non_interference(prog2, labels, TrustLevel.PUBLIC)
    check("ni_no_violation", len(violations_ok) == 0)

    # Implicit flow via conditional
    labels2 = {
        "secret_flag": SecurityLabel(TrustLevel.SECRET),
        "output": SecurityLabel(TrustLevel.PUBLIC),
    }
    prog3 = Program(statements=[
        ("if", "secret_flag", "output"),
    ])
    violations_imp = check_non_interference(prog3, labels2, TrustLevel.PUBLIC)
    check("implicit_flow_detected", len(violations_imp) > 0)

    # ── §6 Bell-LaPadula ────────────────────────────────────────
    print("\n§6 Bell-LaPadula Model\n")

    blp = BellLaPadula()
    blp.add_subject("analyst", SecurityLabel(TrustLevel.CONFIDENTIAL))
    blp.add_subject("admin", SecurityLabel(TrustLevel.TOP_SECRET))
    blp.add_subject("guest", SecurityLabel(TrustLevel.PUBLIC))

    blp.add_object("trust_report", SecurityLabel(TrustLevel.CONFIDENTIAL))
    blp.add_object("public_page", SecurityLabel(TrustLevel.PUBLIC))
    blp.add_object("secret_keys", SecurityLabel(TrustLevel.SECRET))

    # No read up
    check("analyst_reads_report", blp.can_read("analyst", "trust_report"))
    check("analyst_cant_read_secret", not blp.can_read("analyst", "secret_keys"))
    check("admin_reads_all", blp.can_read("admin", "secret_keys"))
    check("guest_reads_public", blp.can_read("guest", "public_page"))
    check("guest_cant_read_conf", not blp.can_read("guest", "trust_report"))

    # No write down
    check("analyst_writes_report", blp.can_write("analyst", "trust_report"))
    check("analyst_cant_write_public", not blp.can_write("analyst", "public_page"))
    check("guest_writes_public", blp.can_write("guest", "public_page"))
    # Admin (TS) can't write down to SECRET (no write down!)
    check("admin_cant_write_down", not blp.can_write("admin", "secret_keys"))

    # ── §7 Declassification ──────────────────────────────────────
    print("\n§7 Declassification\n")

    var = FlowVariable("sensitive_trust", sec, value=0.85)

    policy = DeclassificationPolicy(sec, pub, "admin_approval", approved=False)
    check("declass_is_downgrade", policy.is_downgrade)

    # Not approved — no change
    unchanged = declassify(var, policy)
    check("unapproved_no_change", unchanged.label == sec)

    # Approved — declassified
    policy.approved = True
    declassed = declassify(var, policy)
    check("approved_declassified", declassed.label == pub)
    check("value_preserved", declassed.value == 0.85)

    # ── §8 Covert Channels ──────────────────────────────────────
    print("\n§8 Covert Channel Detection\n")

    ifg3 = InformationFlowGraph()
    ifg3.add_variable("secret", sec)
    ifg3.add_variable("public", pub)
    ifg3.add_flow("secret", "public", flow_type="covert")

    covert = detect_covert_channels(ifg3)
    check("covert_detected", len(covert) == 1)
    check("covert_type", covert[0].flow_type == "covert")

    # Explicit legal flow — not covert
    ifg4 = InformationFlowGraph()
    ifg4.add_variable("a", pub)
    ifg4.add_variable("b", conf)
    ifg4.add_flow("a", "b", flow_type="explicit")
    check("no_covert_in_legal", len(detect_covert_channels(ifg4)) == 0)

    # ── Summary ──────────────────────────────────────────────────
    print(f"\n{'='*70}")
    print(f"Results: {passed} passed, {failed} failed out of {passed + failed}")
    print(f"{'='*70}")
    return passed, failed


if __name__ == "__main__":
    run_checks()
