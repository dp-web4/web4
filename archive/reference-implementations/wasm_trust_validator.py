"""
Web4 WebAssembly Trust Validator — Session 17, Track 4
======================================================

Python simulation of a WASM-targetable trust validator.
Models what a browser-based conformance tester would do:
- Trust tensor validation (T3/V3 bounds, dimension correctness)
- ATP transaction validation (conservation, fee rules, balance bounds)
- LCT structure validation (required fields, signature verification)
- MRH distance validation (zone classification, decay rules)
- Cross-module conformance (trust→ATP gating, MRH→policy mapping)

This is NOT actual WASM — it's a pure Python model of the validation
logic that would be compiled to WASM for browser execution.

12 sections, ~85 checks expected.
"""

import hashlib
import math
import random
import json
import struct
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Set, Tuple, Any
from collections import defaultdict


# ============================================================
# §1 — Validation Result Framework
# ============================================================

class Severity(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ValidationResult:
    field: str
    valid: bool
    severity: Severity = Severity.ERROR
    message: str = ""
    expected: Any = None
    actual: Any = None


@dataclass
class ValidationReport:
    validator_name: str
    results: List[ValidationResult] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add(self, result: ValidationResult):
        self.results.append(result)

    def is_valid(self) -> bool:
        return all(r.valid for r in self.results if r.severity in [Severity.ERROR, Severity.CRITICAL])

    def error_count(self) -> int:
        return sum(1 for r in self.results if not r.valid and r.severity in [Severity.ERROR, Severity.CRITICAL])

    def warning_count(self) -> int:
        return sum(1 for r in self.results if not r.valid and r.severity == Severity.WARNING)

    def summary(self) -> Dict:
        return {
            "validator": self.validator_name,
            "valid": self.is_valid(),
            "total_checks": len(self.results),
            "passed": sum(1 for r in self.results if r.valid),
            "errors": self.error_count(),
            "warnings": self.warning_count(),
        }


def test_section_1():
    checks = []

    report = ValidationReport("test_validator")
    report.add(ValidationResult("field_a", True, message="OK"))
    report.add(ValidationResult("field_b", False, Severity.ERROR, "Bad value"))
    report.add(ValidationResult("field_c", False, Severity.WARNING, "Minor issue"))

    checks.append(("report_not_valid", not report.is_valid()))
    checks.append(("error_count_1", report.error_count() == 1))
    checks.append(("warning_count_1", report.warning_count() == 1))

    s = report.summary()
    checks.append(("summary_total_3", s["total_checks"] == 3))
    checks.append(("summary_passed_1", s["passed"] == 1))

    # All valid report
    report2 = ValidationReport("good")
    report2.add(ValidationResult("x", True))
    report2.add(ValidationResult("y", True))
    checks.append(("all_valid", report2.is_valid()))

    # Warnings don't block validity
    report3 = ValidationReport("warn_only")
    report3.add(ValidationResult("a", True))
    report3.add(ValidationResult("b", False, Severity.WARNING, "just a warning"))
    checks.append(("warnings_dont_block", report3.is_valid()))

    # Critical blocks
    report4 = ValidationReport("critical")
    report4.add(ValidationResult("a", False, Severity.CRITICAL, "critical failure"))
    checks.append(("critical_blocks", not report4.is_valid()))

    return checks


# ============================================================
# §2 — T3/V3 Trust Tensor Validation
# ============================================================

T3_DIMENSIONS = ["talent", "training", "temperament"]
V3_DIMENSIONS = ["valuation", "veracity", "validity"]


def validate_trust_tensor(tensor: Dict, tensor_type: str = "T3") -> ValidationReport:
    """Validate a T3 or V3 trust tensor."""
    report = ValidationReport(f"{tensor_type}_validator")
    dims = T3_DIMENSIONS if tensor_type == "T3" else V3_DIMENSIONS

    # Check required dimensions present
    for dim in dims:
        present = dim in tensor
        report.add(ValidationResult(
            f"{dim}_present", present, Severity.ERROR,
            f"Missing dimension: {dim}" if not present else "OK"
        ))

    # Check values in [0, 1]
    for dim in dims:
        if dim in tensor:
            val = tensor[dim]
            is_number = isinstance(val, (int, float)) and not math.isnan(val) and not math.isinf(val)
            report.add(ValidationResult(
                f"{dim}_numeric", is_number, Severity.ERROR,
                f"Non-numeric value: {val}" if not is_number else "OK"
            ))
            if is_number:
                in_range = 0.0 <= val <= 1.0
                report.add(ValidationResult(
                    f"{dim}_range", in_range, Severity.ERROR,
                    f"Out of range [0,1]: {val}" if not in_range else "OK",
                    expected="[0.0, 1.0]", actual=val
                ))

    # Check no extra dimensions (warning)
    extra = set(tensor.keys()) - set(dims) - {"composite", "metadata", "sub_dimensions"}
    if extra:
        report.add(ValidationResult(
            "no_extra_dims", False, Severity.WARNING,
            f"Extra dimensions: {extra}"
        ))

    # Composite score validation
    if "composite" in tensor:
        comp = tensor["composite"]
        is_number = isinstance(comp, (int, float)) and not math.isnan(comp) and not math.isinf(comp)
        if is_number:
            in_range = 0.0 <= comp <= 1.0
            report.add(ValidationResult(
                "composite_range", in_range, Severity.ERROR,
                f"Composite out of range: {comp}" if not in_range else "OK"
            ))
            # Composite should be derivable from dimensions
            dim_vals = [tensor.get(d, 0) for d in dims if isinstance(tensor.get(d, 0), (int, float))]
            if dim_vals:
                avg = sum(dim_vals) / len(dim_vals)
                reasonable = abs(comp - avg) < 0.5
                report.add(ValidationResult(
                    "composite_reasonable", reasonable, Severity.WARNING,
                    f"Composite {comp} far from dimension average {avg:.3f}"
                ))

    return report


def test_section_2():
    checks = []

    # Valid T3
    good_t3 = {"talent": 0.8, "training": 0.6, "temperament": 0.7}
    r1 = validate_trust_tensor(good_t3, "T3")
    checks.append(("valid_t3", r1.is_valid()))

    # Valid V3
    good_v3 = {"valuation": 0.5, "veracity": 0.9, "validity": 0.7}
    r2 = validate_trust_tensor(good_v3, "V3")
    checks.append(("valid_v3", r2.is_valid()))

    # Missing dimension
    missing = {"talent": 0.8, "training": 0.6}
    r3 = validate_trust_tensor(missing, "T3")
    checks.append(("missing_dim_fails", not r3.is_valid()))

    # Out of range
    bad_range = {"talent": 1.5, "training": 0.6, "temperament": -0.1}
    r4 = validate_trust_tensor(bad_range, "T3")
    checks.append(("out_of_range_fails", not r4.is_valid()))
    checks.append(("two_range_errors", r4.error_count() == 2))

    # NaN value
    nan_tensor = {"talent": float('nan'), "training": 0.6, "temperament": 0.7}
    r5 = validate_trust_tensor(nan_tensor, "T3")
    checks.append(("nan_fails", not r5.is_valid()))

    # Extra dimensions (warning only)
    extra = {"talent": 0.8, "training": 0.6, "temperament": 0.7, "charisma": 0.5}
    r6 = validate_trust_tensor(extra, "T3")
    checks.append(("extra_warns_only", r6.is_valid()))
    checks.append(("extra_has_warning", r6.warning_count() > 0))

    # With composite
    with_comp = {"talent": 0.8, "training": 0.6, "temperament": 0.7, "composite": 0.7}
    r7 = validate_trust_tensor(with_comp, "T3")
    checks.append(("composite_valid", r7.is_valid()))

    return checks


# ============================================================
# §3 — ATP Transaction Validation
# ============================================================

@dataclass
class ATPTransaction:
    sender: str
    receiver: str
    amount: float
    fee: float
    timestamp: float
    signature: str = ""
    tx_id: str = ""

    def __post_init__(self):
        if not self.tx_id:
            data = f"{self.sender}:{self.receiver}:{self.amount}:{self.timestamp}"
            self.tx_id = hashlib.sha256(data.encode()).hexdigest()[:16]


def validate_atp_transaction(tx: ATPTransaction, sender_balance: float,
                              fee_rate: float = 0.05,
                              max_amount: float = 10000.0) -> ValidationReport:
    """Validate an ATP transaction."""
    report = ValidationReport("atp_transaction_validator")

    # Amount positive
    report.add(ValidationResult(
        "amount_positive", tx.amount > 0, Severity.ERROR,
        f"Amount must be positive: {tx.amount}"
    ))

    # Amount not NaN/Inf
    valid_amount = isinstance(tx.amount, (int, float)) and not math.isnan(tx.amount) and not math.isinf(tx.amount)
    report.add(ValidationResult(
        "amount_finite", valid_amount, Severity.CRITICAL,
        f"Amount is not finite: {tx.amount}"
    ))

    # Amount within max
    if valid_amount:
        report.add(ValidationResult(
            "amount_within_max", tx.amount <= max_amount, Severity.ERROR,
            f"Amount {tx.amount} exceeds max {max_amount}"
        ))

    # Fee matches expected
    expected_fee = tx.amount * fee_rate
    fee_correct = abs(tx.fee - expected_fee) < 0.01
    report.add(ValidationResult(
        "fee_correct", fee_correct, Severity.ERROR,
        f"Fee {tx.fee} != expected {expected_fee:.4f}",
        expected=expected_fee, actual=tx.fee
    ))

    # Sender has sufficient balance
    total_cost = tx.amount + tx.fee
    sufficient = sender_balance >= total_cost
    report.add(ValidationResult(
        "sufficient_balance", sufficient, Severity.ERROR,
        f"Balance {sender_balance} < cost {total_cost}"
    ))

    # Sender != receiver (no self-transfer)
    report.add(ValidationResult(
        "no_self_transfer", tx.sender != tx.receiver, Severity.WARNING,
        "Self-transfer detected"
    ))

    # TX ID present
    report.add(ValidationResult(
        "tx_id_present", len(tx.tx_id) > 0, Severity.ERROR,
        "Missing transaction ID"
    ))

    # Timestamp valid
    report.add(ValidationResult(
        "timestamp_positive", tx.timestamp > 0, Severity.ERROR,
        f"Invalid timestamp: {tx.timestamp}"
    ))

    return report


def test_section_3():
    checks = []

    # Valid transaction
    good_tx = ATPTransaction("alice", "bob", 100.0, 5.0, 1000.0)
    r1 = validate_atp_transaction(good_tx, 200.0)
    checks.append(("valid_tx", r1.is_valid()))

    # Insufficient balance
    r2 = validate_atp_transaction(good_tx, 50.0)
    checks.append(("insufficient_balance", not r2.is_valid()))

    # Wrong fee
    bad_fee_tx = ATPTransaction("alice", "bob", 100.0, 2.0, 1000.0)
    r3 = validate_atp_transaction(bad_fee_tx, 200.0)
    checks.append(("wrong_fee", not r3.is_valid()))

    # Negative amount
    neg_tx = ATPTransaction("alice", "bob", -50.0, -2.5, 1000.0)
    r4 = validate_atp_transaction(neg_tx, 200.0)
    checks.append(("negative_amount", not r4.is_valid()))

    # NaN amount (critical)
    nan_tx = ATPTransaction("alice", "bob", float('nan'), 0.0, 1000.0)
    r5 = validate_atp_transaction(nan_tx, 200.0)
    checks.append(("nan_critical", not r5.is_valid()))

    # Self-transfer (warning only)
    self_tx = ATPTransaction("alice", "alice", 50.0, 2.5, 1000.0)
    r6 = validate_atp_transaction(self_tx, 200.0)
    checks.append(("self_transfer_warns", r6.is_valid()))
    checks.append(("self_transfer_warning", r6.warning_count() > 0))

    # TX ID generated
    checks.append(("tx_id_generated", len(good_tx.tx_id) == 16))

    return checks


# ============================================================
# §4 — LCT Structure Validation
# ============================================================

REQUIRED_LCT_FIELDS = ["lct_id", "entity_type", "created_at", "public_key"]
OPTIONAL_LCT_FIELDS = ["display_name", "metadata", "witnesses", "trust_tensor", "society_id"]
VALID_ENTITY_TYPES = [
    "human", "ai_agent", "organization", "device", "service",
    "society", "dictionary", "role", "resource", "law",
    "contract", "sensor", "actuator", "gateway", "policy", "composite"
]


def validate_lct(lct: Dict) -> ValidationReport:
    """Validate an LCT document structure."""
    report = ValidationReport("lct_validator")

    # Required fields
    for field_name in REQUIRED_LCT_FIELDS:
        present = field_name in lct and lct[field_name] is not None
        report.add(ValidationResult(
            f"required_{field_name}", present, Severity.ERROR,
            f"Missing required field: {field_name}"
        ))

    # LCT ID format
    if "lct_id" in lct:
        lct_id = lct["lct_id"]
        valid_format = isinstance(lct_id, str) and len(lct_id) >= 8
        report.add(ValidationResult(
            "lct_id_format", valid_format, Severity.ERROR,
            f"Invalid LCT ID format: {lct_id}"
        ))

    # Entity type
    if "entity_type" in lct:
        valid_type = lct["entity_type"] in VALID_ENTITY_TYPES
        report.add(ValidationResult(
            "entity_type_valid", valid_type, Severity.ERROR,
            f"Unknown entity type: {lct['entity_type']}",
            expected=VALID_ENTITY_TYPES, actual=lct.get("entity_type")
        ))

    # Public key format
    if "public_key" in lct:
        pk = lct["public_key"]
        valid_pk = isinstance(pk, str) and len(pk) >= 16
        report.add(ValidationResult(
            "public_key_format", valid_pk, Severity.ERROR,
            f"Invalid public key format (too short or wrong type)"
        ))

    # Timestamp
    if "created_at" in lct:
        ts = lct["created_at"]
        valid_ts = isinstance(ts, (int, float)) and ts > 0
        report.add(ValidationResult(
            "created_at_valid", valid_ts, Severity.ERROR,
            f"Invalid timestamp: {ts}"
        ))

    # Trust tensor if present
    if "trust_tensor" in lct and lct["trust_tensor"] is not None:
        tt = lct["trust_tensor"]
        if isinstance(tt, dict):
            tt_report = validate_trust_tensor(tt, "T3")
            for r in tt_report.results:
                r.field = f"trust_tensor.{r.field}"
                report.add(r)

    # Witnesses list
    if "witnesses" in lct:
        ws = lct["witnesses"]
        valid_ws = isinstance(ws, list)
        report.add(ValidationResult(
            "witnesses_list", valid_ws, Severity.WARNING,
            "Witnesses should be a list"
        ))

    return report


def test_section_4():
    checks = []

    # Valid LCT
    good_lct = {
        "lct_id": "lct:web4:abc123def456",
        "entity_type": "human",
        "created_at": 1709000000.0,
        "public_key": "ed25519:abcdef1234567890abcdef",
        "display_name": "Alice",
    }
    r1 = validate_lct(good_lct)
    checks.append(("valid_lct", r1.is_valid()))

    # Missing required field
    missing = {"lct_id": "lct:abc", "entity_type": "human"}
    r2 = validate_lct(missing)
    checks.append(("missing_fields_fails", not r2.is_valid()))

    # Invalid entity type
    bad_type = {**good_lct, "entity_type": "robot_overlord"}
    r3 = validate_lct(bad_type)
    checks.append(("bad_entity_type", not r3.is_valid()))

    # All 16 valid entity types
    for etype in VALID_ENTITY_TYPES:
        lct = {**good_lct, "entity_type": etype}
        r = validate_lct(lct)
        checks.append((f"type_{etype}_valid", r.is_valid()))

    # Short public key
    short_pk = {**good_lct, "public_key": "abc"}
    r4 = validate_lct(short_pk)
    checks.append(("short_pk_fails", not r4.is_valid()))

    # With trust tensor
    with_tt = {**good_lct, "trust_tensor": {"talent": 0.8, "training": 0.6, "temperament": 0.7}}
    r5 = validate_lct(with_tt)
    checks.append(("lct_with_tensor", r5.is_valid()))

    # With invalid trust tensor
    bad_tt = {**good_lct, "trust_tensor": {"talent": 1.5, "training": 0.6}}
    r6 = validate_lct(bad_tt)
    checks.append(("lct_bad_tensor_fails", not r6.is_valid()))

    return checks


# ============================================================
# §5 — MRH Distance Validation
# ============================================================

MRH_ZONES = {
    "SELF": (0.0, 0.0),
    "DIRECT": (0.01, 1.0),
    "INDIRECT": (1.01, 3.0),
    "PERIPHERAL": (3.01, 7.0),
    "BEYOND": (7.01, float('inf')),
}


def validate_mrh_distance(distance: float, claimed_zone: str) -> ValidationReport:
    """Validate MRH distance and zone classification."""
    report = ValidationReport("mrh_validator")

    valid_dist = isinstance(distance, (int, float)) and not math.isnan(distance) and distance >= 0
    report.add(ValidationResult(
        "distance_valid", valid_dist, Severity.ERROR,
        f"Invalid distance: {distance}"
    ))

    valid_zone = claimed_zone in MRH_ZONES
    report.add(ValidationResult(
        "zone_exists", valid_zone, Severity.ERROR,
        f"Unknown zone: {claimed_zone}"
    ))

    if valid_dist and valid_zone:
        lo, hi = MRH_ZONES[claimed_zone]
        zone_match = lo <= distance <= hi
        report.add(ValidationResult(
            "zone_matches_distance", zone_match, Severity.ERROR,
            f"Distance {distance} not in {claimed_zone} range [{lo}, {hi}]",
            expected=f"[{lo}, {hi}]", actual=distance
        ))

    if valid_dist:
        max_trust = max(0.0, 1.0 - distance * 0.1)
        report.add(ValidationResult(
            "decay_bounded", True, Severity.INFO,
            f"Max trust at distance {distance}: {max_trust:.3f}"
        ))

    return report


def classify_mrh_zone(distance: float) -> str:
    for zone, (lo, hi) in MRH_ZONES.items():
        if lo <= distance <= hi:
            return zone
    return "UNKNOWN"


def test_section_5():
    checks = []

    r1 = validate_mrh_distance(0.0, "SELF")
    checks.append(("self_valid", r1.is_valid()))

    r2 = validate_mrh_distance(0.5, "DIRECT")
    checks.append(("direct_valid", r2.is_valid()))

    r3 = validate_mrh_distance(5.0, "DIRECT")
    checks.append(("wrong_zone_fails", not r3.is_valid()))

    checks.append(("classify_self", classify_mrh_zone(0.0) == "SELF"))
    checks.append(("classify_direct", classify_mrh_zone(0.5) == "DIRECT"))
    checks.append(("classify_indirect", classify_mrh_zone(2.0) == "INDIRECT"))
    checks.append(("classify_peripheral", classify_mrh_zone(5.0) == "PERIPHERAL"))
    checks.append(("classify_beyond", classify_mrh_zone(10.0) == "BEYOND"))

    r4 = validate_mrh_distance(-1.0, "SELF")
    checks.append(("negative_distance_fails", not r4.is_valid()))

    r5 = validate_mrh_distance(float('nan'), "SELF")
    checks.append(("nan_distance_fails", not r5.is_valid()))

    return checks


# ============================================================
# §6 — Cross-Module Conformance
# ============================================================

def validate_trust_atp_gating(trust_score: float, action: str,
                               required_trust: Dict[str, float]) -> ValidationReport:
    report = ValidationReport("trust_atp_gating")

    min_trust = required_trust.get(action, 0.0)
    allowed = trust_score >= min_trust
    report.add(ValidationResult(
        "trust_sufficient", allowed, Severity.ERROR,
        f"Trust {trust_score} < required {min_trust} for action '{action}'"
    ))
    report.add(ValidationResult(
        "trust_bounded", 0.0 <= trust_score <= 1.0, Severity.ERROR,
        f"Trust out of bounds: {trust_score}"
    ))

    return report


def validate_mrh_policy_mapping(distance: float, zone: str,
                                 policy_actions: List[str]) -> ValidationReport:
    report = ValidationReport("mrh_policy_validator")

    ZONE_ALLOWED = {
        "SELF": {"read", "write", "delegate", "admin", "transfer"},
        "DIRECT": {"read", "write", "delegate", "transfer"},
        "INDIRECT": {"read", "write", "transfer"},
        "PERIPHERAL": {"read"},
        "BEYOND": set(),
    }

    allowed = ZONE_ALLOWED.get(zone, set())
    for action in policy_actions:
        is_allowed = action in allowed
        report.add(ValidationResult(
            f"action_{action}_in_{zone}", is_allowed,
            Severity.ERROR if not is_allowed else Severity.INFO,
            f"Action '{action}' not allowed in zone {zone}" if not is_allowed else "OK"
        ))

    return report


def test_section_6():
    checks = []

    trust_reqs = {"transfer": 0.3, "delegate": 0.6, "admin": 0.8}

    r1 = validate_trust_atp_gating(0.9, "admin", trust_reqs)
    checks.append(("high_trust_admin", r1.is_valid()))

    r2 = validate_trust_atp_gating(0.4, "admin", trust_reqs)
    checks.append(("low_trust_blocks_admin", not r2.is_valid()))

    r3 = validate_trust_atp_gating(0.4, "transfer", trust_reqs)
    checks.append(("low_trust_allows_transfer", r3.is_valid()))

    r4 = validate_mrh_policy_mapping(0.0, "SELF", ["read", "write", "admin"])
    checks.append(("self_allows_all", r4.is_valid()))

    r5 = validate_mrh_policy_mapping(5.0, "PERIPHERAL", ["read"])
    checks.append(("peripheral_read_only", r5.is_valid()))

    r6 = validate_mrh_policy_mapping(5.0, "PERIPHERAL", ["write"])
    checks.append(("peripheral_blocks_write", not r6.is_valid()))

    r7 = validate_mrh_policy_mapping(10.0, "BEYOND", ["read"])
    checks.append(("beyond_blocks_all", not r7.is_valid()))

    return checks


# ============================================================
# §7 — Conformance Test Suite
# ============================================================

@dataclass
class ConformanceTest:
    name: str
    category: str
    input_data: Dict
    expected_valid: bool
    validator: str


def build_conformance_suite() -> List[ConformanceTest]:
    tests = []

    tests.append(ConformanceTest(
        "valid_t3", "trust_tensor",
        {"talent": 0.8, "training": 0.6, "temperament": 0.7},
        True, "T3"
    ))
    tests.append(ConformanceTest(
        "missing_dim_t3", "trust_tensor",
        {"talent": 0.8, "training": 0.6},
        False, "T3"
    ))
    tests.append(ConformanceTest(
        "out_of_range_t3", "trust_tensor",
        {"talent": 1.5, "training": 0.6, "temperament": 0.7},
        False, "T3"
    ))
    tests.append(ConformanceTest(
        "nan_t3", "trust_tensor",
        {"talent": float('nan'), "training": 0.6, "temperament": 0.7},
        False, "T3"
    ))
    tests.append(ConformanceTest(
        "valid_v3", "trust_tensor",
        {"valuation": 0.5, "veracity": 0.9, "validity": 0.7},
        True, "V3"
    ))

    good_lct = {
        "lct_id": "lct:web4:test12345678",
        "entity_type": "human",
        "created_at": 1709000000.0,
        "public_key": "ed25519:0123456789abcdef0123",
    }
    tests.append(ConformanceTest("valid_lct", "lct", good_lct, True, "lct"))
    tests.append(ConformanceTest("missing_pk", "lct",
        {k: v for k, v in good_lct.items() if k != "public_key"},
        False, "lct"))

    tests.append(ConformanceTest(
        "valid_mrh_self", "mrh",
        {"distance": 0.0, "zone": "SELF"},
        True, "mrh"
    ))
    tests.append(ConformanceTest(
        "wrong_zone", "mrh",
        {"distance": 5.0, "zone": "DIRECT"},
        False, "mrh"
    ))

    return tests


def run_conformance_suite(tests: List[ConformanceTest]) -> Dict:
    results = {"passed": 0, "failed": 0, "errors": [], "total": len(tests)}

    for test in tests:
        try:
            if test.validator in ("T3", "V3"):
                report = validate_trust_tensor(test.input_data, test.validator)
            elif test.validator == "lct":
                report = validate_lct(test.input_data)
            elif test.validator == "mrh":
                report = validate_mrh_distance(test.input_data["distance"], test.input_data["zone"])
            else:
                results["errors"].append(f"Unknown validator: {test.validator}")
                continue

            actual_valid = report.is_valid()
            if actual_valid == test.expected_valid:
                results["passed"] += 1
            else:
                results["failed"] += 1
                results["errors"].append(
                    f"{test.name}: expected valid={test.expected_valid}, got {actual_valid}"
                )
        except Exception as e:
            results["failed"] += 1
            results["errors"].append(f"{test.name}: exception {e}")

    return results


def test_section_7():
    checks = []

    suite = build_conformance_suite()
    checks.append(("suite_not_empty", len(suite) > 0))

    results = run_conformance_suite(suite)
    checks.append(("all_conformance_pass", results["failed"] == 0))
    checks.append(("no_errors", len(results["errors"]) == 0))
    checks.append(("tests_ran", results["passed"] + results["failed"] == results["total"]))

    categories = set(t.category for t in suite)
    checks.append(("covers_trust", "trust_tensor" in categories))
    checks.append(("covers_lct", "lct" in categories))
    checks.append(("covers_mrh", "mrh" in categories))

    return checks


# ============================================================
# §8 — Serialization Validation (WASM-friendly formats)
# ============================================================

def validate_json_serialization(obj: Dict, schema: Dict[str, str]) -> ValidationReport:
    report = ValidationReport("json_validator")

    for field_name, expected_type in schema.items():
        present = field_name in obj
        report.add(ValidationResult(
            f"field_{field_name}_present", present, Severity.ERROR,
            f"Missing field: {field_name}"
        ))

        if present:
            val = obj[field_name]
            type_ok = False
            if expected_type == "string":
                type_ok = isinstance(val, str)
            elif expected_type == "number":
                type_ok = isinstance(val, (int, float)) and not math.isnan(val)
            elif expected_type == "boolean":
                type_ok = isinstance(val, bool)
            elif expected_type == "array":
                type_ok = isinstance(val, list)
            elif expected_type == "object":
                type_ok = isinstance(val, dict)

            report.add(ValidationResult(
                f"field_{field_name}_type", type_ok, Severity.ERROR,
                f"Expected {expected_type}, got {type(val).__name__}",
                expected=expected_type, actual=type(val).__name__
            ))

    return report


def validate_binary_encoding(data: bytes, expected_fields: int) -> ValidationReport:
    report = ValidationReport("binary_validator")

    report.add(ValidationResult(
        "min_size", len(data) >= 4, Severity.ERROR,
        f"Too small: {len(data)} bytes"
    ))

    if len(data) >= 4:
        field_count = struct.unpack(">I", data[:4])[0]
        report.add(ValidationResult(
            "field_count_matches", field_count == expected_fields, Severity.ERROR,
            f"Field count {field_count} != expected {expected_fields}"
        ))
        report.add(ValidationResult(
            "data_present", len(data) > 4, Severity.ERROR,
            "No field data after header"
        ))

    return report


def test_section_8():
    checks = []

    schema = {"lct_id": "string", "trust": "number", "active": "boolean", "witnesses": "array"}
    good_obj = {"lct_id": "abc123", "trust": 0.8, "active": True, "witnesses": []}
    r1 = validate_json_serialization(good_obj, schema)
    checks.append(("json_valid", r1.is_valid()))

    missing = {"lct_id": "abc123", "trust": 0.8}
    r2 = validate_json_serialization(missing, schema)
    checks.append(("json_missing_fails", not r2.is_valid()))

    wrong_type = {"lct_id": 123, "trust": "high", "active": True, "witnesses": []}
    r3 = validate_json_serialization(wrong_type, schema)
    checks.append(("json_wrong_type_fails", not r3.is_valid()))

    good_binary = struct.pack(">I", 3) + b"field1field2field3"
    r4 = validate_binary_encoding(good_binary, 3)
    checks.append(("binary_valid", r4.is_valid()))

    r5 = validate_binary_encoding(good_binary, 5)
    checks.append(("binary_wrong_count", not r5.is_valid()))

    r6 = validate_binary_encoding(b"\x00", 1)
    checks.append(("binary_too_small", not r6.is_valid()))

    return checks


# ============================================================
# §9 — Trust Chain Validation
# ============================================================

def validate_trust_chain(chain: List[Dict]) -> ValidationReport:
    report = ValidationReport("trust_chain_validator")

    if not chain:
        report.add(ValidationResult("non_empty", False, Severity.ERROR, "Empty chain"))
        return report

    report.add(ValidationResult("non_empty", True))

    for i, link in enumerate(chain):
        has_from = "from" in link
        has_to = "to" in link
        has_trust = "trust_score" in link
        has_ts = "timestamp" in link

        report.add(ValidationResult(
            f"link_{i}_complete", has_from and has_to and has_trust and has_ts,
            Severity.ERROR, f"Link {i} missing fields"
        ))

        if has_trust:
            t = link["trust_score"]
            report.add(ValidationResult(
                f"link_{i}_trust_bounded", isinstance(t, (int, float)) and 0 <= t <= 1,
                Severity.ERROR, f"Link {i} trust out of bounds: {t}"
            ))

    for i in range(len(chain) - 1):
        continuous = chain[i].get("to") == chain[i+1].get("from")
        report.add(ValidationResult(
            f"continuity_{i}_{i+1}", continuous, Severity.ERROR,
            f"Chain break: {chain[i].get('to')} != {chain[i+1].get('from')}"
        ))

    for i in range(len(chain) - 1):
        t1 = chain[i].get("timestamp", 0)
        t2 = chain[i+1].get("timestamp", 0)
        monotonic = t2 >= t1
        report.add(ValidationResult(
            f"timestamp_order_{i}_{i+1}", monotonic, Severity.WARNING,
            f"Non-monotonic timestamps: {t1} > {t2}"
        ))

    if len(chain) >= 2:
        first_trust = chain[0].get("trust_score", 0)
        last_trust = chain[-1].get("trust_score", 0)
        report.add(ValidationResult(
            "trust_decay_hint", last_trust <= first_trust + 0.2,
            Severity.WARNING,
            f"Trust increased significantly along chain: {first_trust} → {last_trust}"
        ))

    return report


def test_section_9():
    checks = []

    good_chain = [
        {"from": "root", "to": "alice", "trust_score": 0.9, "timestamp": 100},
        {"from": "alice", "to": "bob", "trust_score": 0.8, "timestamp": 200},
        {"from": "bob", "to": "carol", "trust_score": 0.7, "timestamp": 300},
    ]
    r1 = validate_trust_chain(good_chain)
    checks.append(("valid_chain", r1.is_valid()))

    broken = [
        {"from": "root", "to": "alice", "trust_score": 0.9, "timestamp": 100},
        {"from": "bob", "to": "carol", "trust_score": 0.7, "timestamp": 200},
    ]
    r2 = validate_trust_chain(broken)
    checks.append(("broken_chain_fails", not r2.is_valid()))

    r3 = validate_trust_chain([])
    checks.append(("empty_chain_fails", not r3.is_valid()))

    incomplete = [
        {"from": "root", "trust_score": 0.9, "timestamp": 100},
    ]
    r4 = validate_trust_chain(incomplete)
    checks.append(("incomplete_link_fails", not r4.is_valid()))

    bad_trust_chain = [
        {"from": "root", "to": "alice", "trust_score": 1.5, "timestamp": 100},
    ]
    r5 = validate_trust_chain(bad_trust_chain)
    checks.append(("out_of_bounds_trust", not r5.is_valid()))

    single = [{"from": "root", "to": "alice", "trust_score": 0.9, "timestamp": 100}]
    r6 = validate_trust_chain(single)
    checks.append(("single_link_valid", r6.is_valid()))

    return checks


# ============================================================
# §10 — Batch Validation
# ============================================================

def batch_validate(items: List[Dict], item_type: str) -> Dict:
    results = {
        "total": len(items),
        "valid": 0,
        "invalid": 0,
        "reports": [],
    }

    for item in items:
        if item_type == "T3":
            report = validate_trust_tensor(item, "T3")
        elif item_type == "V3":
            report = validate_trust_tensor(item, "V3")
        elif item_type == "lct":
            report = validate_lct(item)
        else:
            continue

        results["reports"].append(report.summary())
        if report.is_valid():
            results["valid"] += 1
        else:
            results["invalid"] += 1

    results["validity_rate"] = results["valid"] / results["total"] if results["total"] > 0 else 0
    return results


def test_section_10():
    checks = []

    tensors = [
        {"talent": 0.8, "training": 0.6, "temperament": 0.7},
        {"talent": 0.5, "training": 0.5, "temperament": 0.5},
        {"talent": 1.5, "training": 0.6, "temperament": 0.7},  # Invalid
        {"talent": 0.3},  # Missing dims
    ]
    result = batch_validate(tensors, "T3")
    checks.append(("batch_total", result["total"] == 4))
    checks.append(("batch_valid_2", result["valid"] == 2))
    checks.append(("batch_invalid_2", result["invalid"] == 2))
    checks.append(("batch_rate_50", abs(result["validity_rate"] - 0.5) < 0.01))

    all_good = [
        {"talent": 0.1 * i, "training": 0.5, "temperament": 0.5}
        for i in range(1, 6)
    ]
    result2 = batch_validate(all_good, "T3")
    checks.append(("all_valid_batch", result2["validity_rate"] == 1.0))

    result3 = batch_validate([], "T3")
    checks.append(("empty_batch", result3["total"] == 0))

    return checks


# ============================================================
# §11 — Performance Benchmarks
# ============================================================

def benchmark_validation(num_items: int, rng: random.Random) -> Dict:
    import time

    tensors = []
    for _ in range(num_items):
        tensors.append({
            "talent": rng.random(),
            "training": rng.random(),
            "temperament": rng.random(),
        })

    start = time.monotonic()
    valid_count = 0
    for t in tensors:
        r = validate_trust_tensor(t, "T3")
        if r.is_valid():
            valid_count += 1
    elapsed = time.monotonic() - start

    lcts = []
    for i in range(num_items):
        lcts.append({
            "lct_id": f"lct:web4:bench{i:08d}",
            "entity_type": "ai_agent",
            "created_at": 1709000000.0 + i,
            "public_key": f"ed25519:{'0' * 16}{i:08x}",
        })

    start2 = time.monotonic()
    lct_valid = 0
    for lct in lcts:
        r = validate_lct(lct)
        if r.is_valid():
            lct_valid += 1
    elapsed2 = time.monotonic() - start2

    return {
        "tensor_count": num_items,
        "tensor_valid": valid_count,
        "tensor_time_ms": elapsed * 1000,
        "tensor_tps": num_items / elapsed if elapsed > 0 else 0,
        "lct_count": num_items,
        "lct_valid": lct_valid,
        "lct_time_ms": elapsed2 * 1000,
        "lct_tps": num_items / elapsed2 if elapsed2 > 0 else 0,
    }


def test_section_11():
    checks = []
    rng = random.Random(42)

    result = benchmark_validation(1000, rng)

    checks.append(("all_tensors_valid", result["tensor_valid"] == 1000))
    checks.append(("all_lcts_valid", result["lct_valid"] == 1000))
    checks.append(("tensor_throughput", result["tensor_tps"] > 1000))
    checks.append(("lct_throughput", result["lct_tps"] > 1000))
    checks.append(("tensor_time_recorded", result["tensor_time_ms"] > 0))
    checks.append(("lct_time_recorded", result["lct_time_ms"] > 0))

    return checks


# ============================================================
# §12 — Complete Validator Pipeline
# ============================================================

def run_complete_validator_pipeline(rng: random.Random) -> List[Tuple[str, bool]]:
    checks = []

    # 1. Trust tensor
    good_t3 = {"talent": 0.8, "training": 0.6, "temperament": 0.7}
    checks.append(("pipeline_t3_valid", validate_trust_tensor(good_t3, "T3").is_valid()))

    bad_t3 = {"talent": 2.0, "training": -1.0, "temperament": float('nan')}
    checks.append(("pipeline_t3_invalid", not validate_trust_tensor(bad_t3, "T3").is_valid()))

    # 2. ATP transaction
    good_tx = ATPTransaction("alice", "bob", 100.0, 5.0, 1000.0)
    checks.append(("pipeline_tx_valid", validate_atp_transaction(good_tx, 200.0).is_valid()))

    # 3. LCT
    good_lct = {
        "lct_id": "lct:web4:pipeline12345",
        "entity_type": "ai_agent",
        "created_at": 1709000000.0,
        "public_key": "ed25519:pipeline_key_1234567890",
    }
    checks.append(("pipeline_lct_valid", validate_lct(good_lct).is_valid()))

    # 4. MRH
    checks.append(("pipeline_mrh_valid", validate_mrh_distance(2.5, "INDIRECT").is_valid()))

    # 5. Cross-module
    checks.append(("pipeline_gating_valid",
                    validate_trust_atp_gating(0.9, "admin", {"admin": 0.8}).is_valid()))

    # 6. Conformance suite
    suite = build_conformance_suite()
    results = run_conformance_suite(suite)
    checks.append(("pipeline_conformance", results["failed"] == 0))

    # 7. Trust chain
    chain = [
        {"from": "root", "to": "alice", "trust_score": 0.9, "timestamp": 100},
        {"from": "alice", "to": "bob", "trust_score": 0.8, "timestamp": 200},
    ]
    checks.append(("pipeline_chain_valid", validate_trust_chain(chain).is_valid()))

    # 8. Batch
    batch_result = batch_validate([good_t3] * 10, "T3")
    checks.append(("pipeline_batch_all_valid", batch_result["validity_rate"] == 1.0))

    # 9. Benchmark
    bench = benchmark_validation(100, rng)
    checks.append(("pipeline_benchmark_ran", bench["tensor_count"] == 100))

    return checks


def test_section_12():
    rng = random.Random(42)
    return run_complete_validator_pipeline(rng)


# ============================================================
# Main runner
# ============================================================

def run_all():
    sections = [
        ("§1 Validation Framework", test_section_1),
        ("§2 T3/V3 Trust Tensor", test_section_2),
        ("§3 ATP Transaction", test_section_3),
        ("§4 LCT Structure", test_section_4),
        ("§5 MRH Distance", test_section_5),
        ("§6 Cross-Module Conformance", test_section_6),
        ("§7 Conformance Suite", test_section_7),
        ("§8 Serialization", test_section_8),
        ("§9 Trust Chain", test_section_9),
        ("§10 Batch Validation", test_section_10),
        ("§11 Performance Benchmarks", test_section_11),
        ("§12 Complete Pipeline", test_section_12),
    ]

    total = 0
    passed = 0
    failed_checks = []

    for name, fn in sections:
        checks = fn()
        section_pass = sum(1 for _, v in checks if v)
        section_total = len(checks)
        total += section_total
        passed += section_pass
        status = "✓" if section_pass == section_total else "✗"
        print(f"  {status} {name}: {section_pass}/{section_total}")
        for cname, cval in checks:
            if not cval:
                failed_checks.append(f"    FAIL: {name} → {cname}")

    print(f"\nTotal: {passed}/{total}")
    if failed_checks:
        print("\nFailed checks:")
        for f in failed_checks:
            print(f)

    return passed, total


if __name__ == "__main__":
    run_all()
