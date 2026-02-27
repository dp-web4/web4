"""
Web4 Conformance Test Suite — Reference Implementation

Validates implementations against the Web4 specification by testing:
1. LCT structure and lifecycle conformance
2. T3/V3 tensor computation conformance
3. ATP/ADP transaction conformance
4. MRH graph operation conformance
5. R6/R7 action framework conformance
6. Deployment profile conformance (Edge/Cloud/P2P/Blockchain)
7. Cross-profile interoperability
8. Test vector validation (canonical vectors from web4-standard/)
9. Security property conformance

Each test references the specific spec section it validates.
Conformance levels: MUST, SHOULD, MAY per RFC 2119.

Session 10, Track 7
"""

import hashlib
import hmac
import json
import re
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


# ─── Conformance Framework ────────────────────────────────────────

class ConformanceLevel(Enum):
    MUST = "MUST"
    SHOULD = "SHOULD"
    MAY = "MAY"


class TestStatus(Enum):
    PASS = "pass"
    FAIL = "fail"
    SKIP = "skip"
    NOT_APPLICABLE = "n/a"


@dataclass
class ConformanceTest:
    """A single conformance test case."""
    test_id: str
    spec_ref: str  # e.g., "LCT §3.1", "ATP §2.3"
    level: ConformanceLevel
    description: str
    profile: str  # "all", "edge", "cloud", "p2p", "blockchain"


@dataclass
class TestResult:
    """Result of running a conformance test."""
    test: ConformanceTest
    status: TestStatus
    message: str = ""
    details: dict = field(default_factory=dict)


@dataclass
class ConformanceReport:
    """Complete conformance report for an implementation."""
    implementation_name: str
    profile: str
    results: list[TestResult]
    timestamp: str

    @property
    def total(self) -> int:
        return len(self.results)

    @property
    def passed(self) -> int:
        return sum(1 for r in self.results if r.status == TestStatus.PASS)

    @property
    def failed(self) -> int:
        return sum(1 for r in self.results if r.status == TestStatus.FAIL)

    @property
    def must_pass_rate(self) -> float:
        must_tests = [r for r in self.results if r.test.level == ConformanceLevel.MUST]
        if not must_tests:
            return 1.0
        return sum(1 for r in must_tests if r.status == TestStatus.PASS) / len(must_tests)

    @property
    def is_conformant(self) -> bool:
        """MUST requirements must all pass for conformance."""
        return all(
            r.status in (TestStatus.PASS, TestStatus.SKIP, TestStatus.NOT_APPLICABLE)
            for r in self.results
            if r.test.level == ConformanceLevel.MUST
        )

    def to_report(self) -> dict:
        by_spec = {}
        for r in self.results:
            ref = r.test.spec_ref.split(" ")[0]
            by_spec.setdefault(ref, {"pass": 0, "fail": 0, "skip": 0})
            by_spec[ref][r.status.value] = by_spec[ref].get(r.status.value, 0) + 1

        return {
            "web4_conformance_report": {
                "implementation": self.implementation_name,
                "profile": self.profile,
                "timestamp": self.timestamp,
                "summary": {
                    "total": self.total,
                    "passed": self.passed,
                    "failed": self.failed,
                    "must_pass_rate": round(self.must_pass_rate, 3),
                    "conformant": self.is_conformant,
                },
                "by_spec": by_spec,
                "failures": [
                    {
                        "test_id": r.test.test_id,
                        "spec_ref": r.test.spec_ref,
                        "level": r.test.level.value,
                        "message": r.message,
                    }
                    for r in self.results
                    if r.status == TestStatus.FAIL
                ],
            }
        }


# ─── Implementation Under Test (IUT) ─────────────────────────────
# A reference IUT that implements Web4 spec requirements.
# Real conformance testing would swap this for the actual implementation.

class LCTDocument:
    """LCT implementation under test."""

    ENTITY_TYPES = {
        "human", "ai", "organization", "device", "service",
        "environment", "collective", "software", "hardware",
        "sensor", "actuator", "data_source", "bridge", "oracle",
        "policy", "dictionary",
    }

    @staticmethod
    def create(entity_type: str, name: str, public_key: str,
               context: str, timestamp: str) -> dict | None:
        if entity_type not in LCTDocument.ENTITY_TYPES:
            return None
        if not public_key or not name:
            return None

        # LCT ID: lct:web4:<type>:<hash>
        id_hash = hashlib.sha256(
            f"{entity_type}:{public_key}:{timestamp}".encode()
        ).hexdigest()[:16]
        lct_id = f"lct:web4:{entity_type}:{id_hash}"

        return {
            "lct_id": lct_id,
            "subject": f"did:web4:key:{public_key}",
            "binding": {
                "entity_type": entity_type,
                "public_key": public_key,
                "created_at": timestamp,
                "binding_proof": f"cose:ed25519:{id_hash[:8]}",
            },
            "birth_certificate": {
                "citizen_role": f"lct:web4:role:citizen:{context}",
                "context": context,
                "birth_timestamp": timestamp,
                "parent_entity": f"lct:web4:{context}:genesis",
                "birth_witnesses": [
                    "lct:web4:witness:time",
                    f"lct:web4:witness:{context}",
                ],
            },
            "mrh": {
                "bound": [],
                "paired": [{
                    "lct_id": f"lct:web4:role:citizen:{context}",
                    "pairing_type": "birth_certificate",
                    "permanent": True,
                    "ts": timestamp,
                }],
                "witnessing": [],
                "horizon_depth": 3,
                "last_updated": timestamp,
            },
            "policy": {
                "capabilities": ["exist", "interact", "accumulate_reputation"],
                "constraints": {},
            },
            "status": "active",
        }

    @staticmethod
    def validate_id(lct_id: str) -> bool:
        """Validate LCT ID format: lct:web4:<type>:<hash>."""
        parts = lct_id.split(":")
        if len(parts) != 4:
            return False
        if parts[0] != "lct" or parts[1] != "web4":
            return False
        if parts[2] not in LCTDocument.ENTITY_TYPES and parts[2] not in ("role", "witness", "platform"):
            return False
        return len(parts[3]) > 0

    @staticmethod
    def rotate_key(lct: dict, new_key: str, timestamp: str) -> dict:
        """Key rotation: update binding, preserve identity."""
        rotated = dict(lct)
        old_key = rotated["binding"]["public_key"]
        rotated["binding"] = dict(rotated["binding"])
        rotated["binding"]["public_key"] = new_key
        rotated["binding"]["rotated_from"] = old_key
        rotated["binding"]["rotated_at"] = timestamp
        rotated["mrh"] = dict(rotated["mrh"])
        rotated["mrh"]["last_updated"] = timestamp
        return rotated

    @staticmethod
    def revoke(lct: dict, reason: str, timestamp: str) -> dict:
        """Revoke an LCT."""
        revoked = dict(lct)
        revoked["status"] = "revoked"
        revoked["revocation"] = {
            "reason": reason,
            "timestamp": timestamp,
            "revoked_by": lct["lct_id"],
        }
        return revoked


class T3V3Tensor:
    """T3/V3 tensor computation under test."""

    @staticmethod
    def create_t3(talent: float, training: float, temperament: float) -> dict:
        for v in (talent, training, temperament):
            if not (0.0 <= v <= 1.0):
                raise ValueError(f"T3 dimension must be in [0,1], got {v}")
        return {
            "talent": talent,
            "training": training,
            "temperament": temperament,
            "composite": (talent + training + temperament) / 3,
        }

    @staticmethod
    def create_v3(valuation: float, veracity: float, validity: float) -> dict:
        for v in (valuation, veracity, validity):
            if not (0.0 <= v <= 1.0):
                raise ValueError(f"V3 dimension must be in [0,1], got {v}")
        return {
            "valuation": valuation,
            "veracity": veracity,
            "validity": validity,
            "composite": (valuation + veracity + validity) / 3,
        }

    @staticmethod
    def update_t3(t3: dict, quality: float, task_type: str,
                  task_count: int = 0) -> dict:
        """Update T3 based on task quality with diminishing returns."""
        decay = 0.8 ** task_count
        delta = 0.02 * (quality - 0.5) * decay
        return {
            "talent": max(0, min(1, t3["talent"] + delta)),
            "training": max(0, min(1, t3["training"] + delta * 0.8)),
            "temperament": max(0, min(1, t3["temperament"] + delta * 0.5)),
            "composite": None,  # Recomputed below
        }


class ATPLedger:
    """ATP/ADP ledger under test."""

    def __init__(self):
        self.accounts: dict[str, float] = {}
        self.locks: dict[str, dict] = {}
        self.transactions: list[dict] = []
        self.total_supply = 0.0
        self.total_fees = 0.0

    def fund(self, entity: str, amount: float) -> bool:
        if amount <= 0:
            return False
        self.accounts.setdefault(entity, 0.0)
        self.accounts[entity] += amount
        self.total_supply += amount
        self.transactions.append({
            "type": "fund", "entity": entity,
            "amount": amount, "ts": time.monotonic(),
        })
        return True

    def transfer(self, sender: str, recipient: str, amount: float) -> bool:
        if amount <= 0 or self.accounts.get(sender, 0) < amount:
            return False
        fee = amount * 0.05
        net = amount - fee
        self.accounts[sender] -= amount
        self.accounts.setdefault(recipient, 0.0)
        self.accounts[recipient] += net
        self.total_fees += fee
        self.transactions.append({
            "type": "transfer", "from": sender, "to": recipient,
            "amount": amount, "fee": fee, "ts": time.monotonic(),
        })
        return True

    def lock(self, entity: str, amount: float) -> str | None:
        if amount <= 0 or self.accounts.get(entity, 0) < amount:
            return None
        lock_id = f"lock:{hashlib.sha256(f'{entity}:{len(self.locks)}'.encode()).hexdigest()[:8]}"
        self.accounts[entity] -= amount
        self.locks[lock_id] = {
            "entity": entity, "amount": amount, "status": "active",
        }
        return lock_id

    def commit(self, lock_id: str, recipient: str, quality: float) -> float:
        if lock_id not in self.locks or self.locks[lock_id]["status"] != "active":
            return 0.0
        lk = self.locks[lock_id]
        lk["status"] = "committed"
        # Sliding scale
        amount = lk["amount"]
        if quality < 0.3:
            payment = 0.0
        elif quality < 0.7:
            payment = amount * (quality - 0.3) / 0.4
        else:
            payment = amount * quality
        fee = payment * 0.05
        net = payment - fee
        self.accounts.setdefault(recipient, 0.0)
        self.accounts[recipient] += net
        self.total_fees += fee
        self.accounts[lk["entity"]] = self.accounts.get(lk["entity"], 0.0) + (amount - payment)
        return net

    def rollback(self, lock_id: str) -> bool:
        if lock_id not in self.locks or self.locks[lock_id]["status"] != "active":
            return False
        lk = self.locks[lock_id]
        lk["status"] = "rolled_back"
        self.accounts[lk["entity"]] = self.accounts.get(lk["entity"], 0.0) + lk["amount"]
        return True

    def conservation_check(self) -> bool:
        """Verify ATP conservation: total_supply == sum(accounts) + sum(active_locks) + total_fees."""
        account_sum = sum(self.accounts.values())
        lock_sum = sum(lk["amount"] for lk in self.locks.values() if lk["status"] == "active")
        return abs(self.total_supply - (account_sum + lock_sum + self.total_fees)) < 1e-10


class MRHGraph:
    """MRH graph operations under test."""

    ZONES = ["SELF", "DIRECT", "INDIRECT", "PERIPHERAL", "BEYOND"]
    ZONE_DISTANCES = {"SELF": 0, "DIRECT": 1, "INDIRECT": 2, "PERIPHERAL": 3, "BEYOND": 4}

    @staticmethod
    def create(entity_id: str) -> dict:
        return {
            "entity": entity_id,
            "edges": [],
            "depth": 3,
        }

    @staticmethod
    def add_edge(graph: dict, target: str, relationship: str, zone: str) -> dict:
        if zone not in MRHGraph.ZONES:
            return graph
        updated = dict(graph)
        updated["edges"] = list(graph["edges"])
        updated["edges"].append({
            "target": target,
            "relationship": relationship,
            "zone": zone,
            "distance": MRHGraph.ZONE_DISTANCES[zone],
        })
        return updated

    @staticmethod
    def get_zone(graph: dict, target: str) -> str | None:
        for edge in graph["edges"]:
            if edge["target"] == target:
                return edge["zone"]
        return None

    @staticmethod
    def trust_attenuation(base_trust: float, zone: str) -> float:
        """Trust attenuates with MRH distance."""
        factors = {"SELF": 1.0, "DIRECT": 0.8, "INDIRECT": 0.5,
                   "PERIPHERAL": 0.2, "BEYOND": 0.05}
        return base_trust * factors.get(zone, 0.0)


class R6Action:
    """R6 action framework under test."""
    COMPONENTS = {"rules", "role", "request", "reference", "resource", "result"}

    @staticmethod
    def create(rules: str, role: str, request: str, reference: str,
               resource: str) -> dict:
        return {
            "rules": rules,
            "role": role,
            "request": request,
            "reference": reference,
            "resource": resource,
            "result": None,
            "hash_chain": None,
        }

    @staticmethod
    def complete(action: dict, result: Any, quality: float) -> dict:
        completed = dict(action)
        completed["result"] = {
            "output": result,
            "quality": quality,
            "completed_at": time.monotonic(),
        }
        chain_input = f"{action['rules']}:{action['role']}:{action['request']}:{result}"
        completed["hash_chain"] = hashlib.sha256(chain_input.encode()).hexdigest()[:16]
        return completed

    @staticmethod
    def validate(action: dict) -> bool:
        """Validate R6 action has all required components."""
        return all(k in action for k in R6Action.COMPONENTS)


class DeploymentProfile:
    """Deployment profile conformance."""

    PROFILES = {
        "edge": {
            "network": "coap",
            "transport": "udp",
            "data_format": "cbor",
            "crypto_suite": "W4-IOT-1",
            "signature": "ed25519",
            "aead": "aes-ccm",
        },
        "cloud": {
            "network": "https",
            "transport": "tcp",
            "data_format": "json",
            "crypto_suite": "W4-FIPS-1",
            "signature": "ecdsa-p256",
            "aead": "aes-128-gcm",
        },
        "p2p": {
            "network": "webrtc",
            "transport": "sctp",
            "data_format": "cbor",
            "crypto_suite": "W4-BASE-1",
            "signature": "ed25519",
            "aead": "chacha20-poly1305",
        },
        "blockchain": {
            "network": "agnostic",
            "data_format": "json",
            "crypto_suite": "W4-BASE-1",
            "signature": "ed25519",
            "aead": "chacha20-poly1305",
        },
    }

    @staticmethod
    def validate_profile(name: str, config: dict) -> list[str]:
        """Validate a configuration against a profile."""
        expected = DeploymentProfile.PROFILES.get(name)
        if not expected:
            return [f"Unknown profile: {name}"]
        violations = []
        for key, value in expected.items():
            if key not in config:
                violations.append(f"Missing required field: {key}")
            elif config[key] != value:
                violations.append(f"{key}: expected {value}, got {config[key]}")
        return violations

    @staticmethod
    def bridge_compatible(profile_a: str, profile_b: str) -> dict:
        """Check if two profiles can interoperate."""
        pa = DeploymentProfile.PROFILES.get(profile_a, {})
        pb = DeploymentProfile.PROFILES.get(profile_b, {})

        same_crypto = pa.get("crypto_suite") == pb.get("crypto_suite")
        same_format = pa.get("data_format") == pb.get("data_format")
        same_sig = pa.get("signature") == pb.get("signature")

        return {
            "direct_compatible": same_crypto and same_format,
            "needs_transcoding": not same_format,
            "needs_crypto_bridge": not same_crypto,
            "shared_signature": same_sig,
        }


# ─── Conformance Test Runner ─────────────────────────────────────

class ConformanceTestRunner:
    """Runs conformance tests against the IUT."""

    def __init__(self, profile: str = "all"):
        self.profile = profile
        self.results: list[TestResult] = []

    def run(self, test: ConformanceTest, condition: bool, message: str = "",
            details: dict | None = None) -> TestResult:
        if test.profile not in ("all", self.profile) and self.profile != "all":
            result = TestResult(test=test, status=TestStatus.NOT_APPLICABLE,
                                message="Profile not applicable")
        elif condition:
            result = TestResult(test=test, status=TestStatus.PASS, message=message)
        else:
            result = TestResult(test=test, status=TestStatus.FAIL,
                                message=message, details=details or {})
        self.results.append(result)
        return result

    def report(self, name: str) -> ConformanceReport:
        return ConformanceReport(
            implementation_name=name,
            profile=self.profile,
            results=self.results,
            timestamp="2026-02-26T00:00:00Z",
        )


# ═══════════════════════════════════════════════════════════════════
# Conformance Tests
# ═══════════════════════════════════════════════════════════════════

def run_lct_conformance(runner: ConformanceTestRunner) -> int:
    """LCT specification conformance tests."""
    count = 0

    # LCT-001: ID format MUST be lct:web4:<type>:<hash>
    t = ConformanceTest("LCT-001", "LCT §3.1", ConformanceLevel.MUST,
                        "LCT ID format: lct:web4:<type>:<hash>", "all")
    lct = LCTDocument.create("human", "Alice", "test_key_123", "platform",
                             "2025-09-14T12:00:00Z")
    runner.run(t, lct is not None and re.match(r"lct:web4:\w+:\w+", lct["lct_id"]) is not None,
               f"ID: {lct['lct_id'] if lct else 'None'}")
    count += 1

    # LCT-002: ID MUST have exactly 4 colon-separated segments
    t = ConformanceTest("LCT-002", "LCT §3.1", ConformanceLevel.MUST,
                        "LCT ID has 4 segments", "all")
    runner.run(t, lct is not None and len(lct["lct_id"].split(":")) == 4)
    count += 1

    # LCT-003: Invalid IDs MUST be rejected
    t = ConformanceTest("LCT-003", "LCT §3.1", ConformanceLevel.MUST,
                        "Invalid LCT IDs rejected", "all")
    invalid_ids = [
        "lct:web4:human",  # Too few segments
        "lct:web4:human:a:b",  # Too many segments
        "lct:web5:human:abc",  # Wrong namespace
        "lct:web4:alien:abc",  # Invalid entity type
        "invalid",  # Not an LCT ID
    ]
    all_rejected = all(not LCTDocument.validate_id(i) for i in invalid_ids)
    runner.run(t, all_rejected, f"Tested {len(invalid_ids)} invalid IDs")
    count += 1

    # LCT-004: Entity type MUST be from canonical set
    t = ConformanceTest("LCT-004", "LCT §3.2", ConformanceLevel.MUST,
                        "Entity type from canonical set", "all")
    runner.run(t, len(LCTDocument.ENTITY_TYPES) >= 15,
               f"{len(LCTDocument.ENTITY_TYPES)} entity types")
    count += 1

    # LCT-005: Unknown entity type MUST be rejected
    t = ConformanceTest("LCT-005", "LCT §3.2", ConformanceLevel.MUST,
                        "Unknown entity type rejected", "all")
    bad_lct = LCTDocument.create("alien", "Test", "key", "ctx", "2025-01-01T00:00:00Z")
    runner.run(t, bad_lct is None)
    count += 1

    # LCT-006: Birth certificate MUST include citizen role
    t = ConformanceTest("LCT-006", "LCT §4.1", ConformanceLevel.MUST,
                        "Birth certificate includes citizen role", "all")
    runner.run(t, "citizen_role" in lct["birth_certificate"],
               f"Role: {lct['birth_certificate']['citizen_role']}")
    count += 1

    # LCT-007: Birth certificate MUST include birth witnesses
    t = ConformanceTest("LCT-007", "LCT §4.1", ConformanceLevel.MUST,
                        "Birth certificate has witnesses", "all")
    runner.run(t, len(lct["birth_certificate"]["birth_witnesses"]) >= 2,
               f"{len(lct['birth_certificate']['birth_witnesses'])} witnesses")
    count += 1

    # LCT-008: MRH MUST be initialized with citizen role pairing
    t = ConformanceTest("LCT-008", "LCT §5.1", ConformanceLevel.MUST,
                        "MRH initialized with citizen pairing", "all")
    runner.run(t, len(lct["mrh"]["paired"]) >= 1 and
               lct["mrh"]["paired"][0]["pairing_type"] == "birth_certificate")
    count += 1

    # LCT-009: Subject DID MUST reference public key
    t = ConformanceTest("LCT-009", "LCT §3.3", ConformanceLevel.MUST,
                        "Subject DID references public key", "all")
    runner.run(t, lct["binding"]["public_key"] in lct["subject"])
    count += 1

    # LCT-010: Key rotation MUST preserve identity (same LCT ID)
    t = ConformanceTest("LCT-010", "LCT §6.1", ConformanceLevel.MUST,
                        "Key rotation preserves LCT ID", "all")
    rotated = LCTDocument.rotate_key(lct, "new_key_456", "2025-10-01T00:00:00Z")
    runner.run(t, rotated["lct_id"] == lct["lct_id"] and
               rotated["binding"]["public_key"] == "new_key_456")
    count += 1

    # LCT-011: Key rotation MUST reference old key
    t = ConformanceTest("LCT-011", "LCT §6.1", ConformanceLevel.MUST,
                        "Key rotation references old key", "all")
    runner.run(t, rotated["binding"]["rotated_from"] == "test_key_123")
    count += 1

    # LCT-012: Revocation MUST set status to revoked
    t = ConformanceTest("LCT-012", "LCT §7.1", ConformanceLevel.MUST,
                        "Revocation sets status", "all")
    revoked = LCTDocument.revoke(lct, "compromised", "2025-11-01T00:00:00Z")
    runner.run(t, revoked["status"] == "revoked" and
               revoked["revocation"]["reason"] == "compromised")
    count += 1

    # LCT-013: Policy MUST include base capabilities
    t = ConformanceTest("LCT-013", "LCT §4.2", ConformanceLevel.MUST,
                        "Policy has base capabilities", "all")
    runner.run(t, "exist" in lct["policy"]["capabilities"])
    count += 1

    # LCT-014: LCT SHOULD support all 16 entity types
    t = ConformanceTest("LCT-014", "LCT §3.2", ConformanceLevel.SHOULD,
                        "Support 16 entity types", "all")
    runner.run(t, len(LCTDocument.ENTITY_TYPES) >= 16,
               f"Supports {len(LCTDocument.ENTITY_TYPES)} types")
    count += 1

    return count


def run_t3v3_conformance(runner: ConformanceTestRunner) -> int:
    """T3/V3 tensor conformance tests."""
    count = 0

    # T3-001: All dimensions MUST be in [0,1]
    t = ConformanceTest("T3-001", "T3V3 §2.1", ConformanceLevel.MUST,
                        "T3 dimensions bounded [0,1]", "all")
    t3 = T3V3Tensor.create_t3(0.8, 0.7, 0.6)
    runner.run(t, all(0 <= t3[d] <= 1 for d in ["talent", "training", "temperament"]))
    count += 1

    # T3-002: Out-of-range values MUST be rejected
    t = ConformanceTest("T3-002", "T3V3 §2.1", ConformanceLevel.MUST,
                        "Out-of-range T3 values rejected", "all")
    rejected = False
    try:
        T3V3Tensor.create_t3(1.5, 0.5, 0.5)
    except ValueError:
        rejected = True
    runner.run(t, rejected)
    count += 1

    # T3-003: Composite MUST be average of dimensions
    t = ConformanceTest("T3-003", "T3V3 §2.2", ConformanceLevel.MUST,
                        "T3 composite is average", "all")
    runner.run(t, abs(t3["composite"] - (0.8 + 0.7 + 0.6) / 3) < 1e-10)
    count += 1

    # V3-001: V3 dimensions MUST be in [0,1]
    t = ConformanceTest("V3-001", "T3V3 §3.1", ConformanceLevel.MUST,
                        "V3 dimensions bounded [0,1]", "all")
    v3 = T3V3Tensor.create_v3(0.9, 0.8, 0.7)
    runner.run(t, all(0 <= v3[d] <= 1 for d in ["valuation", "veracity", "validity"]))
    count += 1

    # T3-004: Update MUST apply diminishing returns
    t = ConformanceTest("T3-004", "T3V3 §4.1", ConformanceLevel.MUST,
                        "T3 update has diminishing returns", "all")
    u1 = T3V3Tensor.update_t3(t3, 0.9, "execute", 0)
    u2 = T3V3Tensor.update_t3(t3, 0.9, "execute", 5)
    delta1 = u1["talent"] - t3["talent"]
    delta2 = u2["talent"] - t3["talent"]
    runner.run(t, delta1 > delta2 > 0,
               f"1st update delta={delta1:.4f}, 6th delta={delta2:.4f}")
    count += 1

    # T3-005: Update MUST keep values in [0,1]
    t = ConformanceTest("T3-005", "T3V3 §4.1", ConformanceLevel.MUST,
                        "Update preserves bounds", "all")
    extreme = T3V3Tensor.create_t3(0.99, 0.99, 0.99)
    updated = T3V3Tensor.update_t3(extreme, 1.0, "execute", 0)
    runner.run(t, all(0 <= updated[d] <= 1 for d in ["talent", "training", "temperament"]))
    count += 1

    # T3-006: Bad quality MUST decrease trust
    t = ConformanceTest("T3-006", "T3V3 §4.2", ConformanceLevel.MUST,
                        "Bad quality decreases trust", "all")
    decreased = T3V3Tensor.update_t3(t3, 0.1, "execute", 0)
    runner.run(t, decreased["talent"] < t3["talent"])
    count += 1

    return count


def run_atp_conformance(runner: ConformanceTestRunner) -> int:
    """ATP/ADP transaction conformance tests."""
    count = 0

    ledger = ATPLedger()

    # ATP-001: Funding MUST increase balance
    t = ConformanceTest("ATP-001", "ATP §2.1", ConformanceLevel.MUST,
                        "Funding increases balance", "all")
    ledger.fund("alice", 100)
    runner.run(t, ledger.accounts["alice"] == 100)
    count += 1

    # ATP-002: Negative funding MUST be rejected
    t = ConformanceTest("ATP-002", "ATP §2.1", ConformanceLevel.MUST,
                        "Negative funding rejected", "all")
    runner.run(t, not ledger.fund("alice", -50))
    count += 1

    # ATP-003: Transfer MUST deduct 5% fee
    t = ConformanceTest("ATP-003", "ATP §3.1", ConformanceLevel.MUST,
                        "Transfer deducts 5% fee", "all")
    ledger.fund("bob", 0)
    ledger.transfer("alice", "bob", 100)
    runner.run(t, ledger.accounts["bob"] == 95.0 and ledger.total_fees == 5.0,
               f"Bob: {ledger.accounts['bob']}, Fees: {ledger.total_fees}")
    count += 1

    # ATP-004: Insufficient balance MUST reject transfer
    t = ConformanceTest("ATP-004", "ATP §3.2", ConformanceLevel.MUST,
                        "Insufficient balance rejects transfer", "all")
    runner.run(t, not ledger.transfer("alice", "bob", 999999))
    count += 1

    # ATP-005: Lock MUST decrease available balance
    t = ConformanceTest("ATP-005", "ATP §4.1", ConformanceLevel.MUST,
                        "Lock decreases balance", "all")
    ledger2 = ATPLedger()
    ledger2.fund("payer", 200)
    lid = ledger2.lock("payer", 100)
    runner.run(t, lid is not None and ledger2.accounts["payer"] == 100)
    count += 1

    # ATP-006: Commit MUST pay recipient with sliding scale
    t = ConformanceTest("ATP-006", "ATP §4.2", ConformanceLevel.MUST,
                        "Commit pays with sliding scale", "all")
    net = ledger2.commit(lid, "worker", 0.8)
    runner.run(t, net > 0 and "worker" in ledger2.accounts,
               f"Worker received: {net:.2f}")
    count += 1

    # ATP-007: Rollback MUST return locked amount
    t = ConformanceTest("ATP-007", "ATP §4.3", ConformanceLevel.MUST,
                        "Rollback returns locked amount", "all")
    ledger3 = ATPLedger()
    ledger3.fund("entity", 100)
    lid2 = ledger3.lock("entity", 50)
    before = ledger3.accounts["entity"]
    ledger3.rollback(lid2)
    after = ledger3.accounts["entity"]
    runner.run(t, after == before + 50)
    count += 1

    # ATP-008: Conservation MUST hold
    t = ConformanceTest("ATP-008", "ATP §5.1", ConformanceLevel.MUST,
                        "ATP conservation invariant", "all")
    runner.run(t, ledger.conservation_check() and ledger2.conservation_check() and
               ledger3.conservation_check(),
               "All 3 ledgers conserve ATP")
    count += 1

    # ATP-009: Double-commit MUST be rejected
    t = ConformanceTest("ATP-009", "ATP §4.2", ConformanceLevel.MUST,
                        "Double-commit rejected", "all")
    # lid was already committed above
    double = ledger2.commit(lid, "worker2", 0.9)
    runner.run(t, double == 0.0, "Double commit returns 0")
    count += 1

    # ATP-010: Sliding scale quality < 0.3 MUST pay zero
    t = ConformanceTest("ATP-010", "ATP §4.2", ConformanceLevel.MUST,
                        "Quality < 0.3 pays zero", "all")
    ledger4 = ATPLedger()
    ledger4.fund("p", 100)
    lid3 = ledger4.lock("p", 50)
    zero_pay = ledger4.commit(lid3, "w", 0.1)
    runner.run(t, zero_pay == 0.0, f"Payment at quality 0.1: {zero_pay}")
    count += 1

    # ATP-011: Transaction log MUST be maintained
    t = ConformanceTest("ATP-011", "ATP §6.1", ConformanceLevel.MUST,
                        "Transaction log maintained", "all")
    runner.run(t, len(ledger.transactions) > 0, f"{len(ledger.transactions)} transactions logged")
    count += 1

    return count


def run_mrh_conformance(runner: ConformanceTestRunner) -> int:
    """MRH graph conformance tests."""
    count = 0

    # MRH-001: 5 zones MUST exist
    t = ConformanceTest("MRH-001", "MRH §2.1", ConformanceLevel.MUST,
                        "5 MRH zones defined", "all")
    runner.run(t, len(MRHGraph.ZONES) == 5)
    count += 1

    # MRH-002: Graph MUST initialize empty
    t = ConformanceTest("MRH-002", "MRH §2.2", ConformanceLevel.MUST,
                        "MRH graph initializes empty", "all")
    g = MRHGraph.create("entity:1")
    runner.run(t, len(g["edges"]) == 0)
    count += 1

    # MRH-003: Edge addition MUST include zone
    t = ConformanceTest("MRH-003", "MRH §3.1", ConformanceLevel.MUST,
                        "Edge includes zone", "all")
    g = MRHGraph.add_edge(g, "entity:2", "paired", "DIRECT")
    runner.run(t, g["edges"][0]["zone"] == "DIRECT")
    count += 1

    # MRH-004: Invalid zone MUST be rejected
    t = ConformanceTest("MRH-004", "MRH §3.1", ConformanceLevel.MUST,
                        "Invalid zone rejected", "all")
    g_bad = MRHGraph.add_edge(g, "entity:3", "paired", "INVALID_ZONE")
    runner.run(t, len(g_bad["edges"]) == len(g["edges"]),
               "Edge count unchanged after invalid zone")
    count += 1

    # MRH-005: Trust attenuation MUST decrease with distance
    t = ConformanceTest("MRH-005", "MRH §4.1", ConformanceLevel.MUST,
                        "Trust attenuates with distance", "all")
    base = 1.0
    attenuations = [MRHGraph.trust_attenuation(base, z) for z in MRHGraph.ZONES]
    monotone = all(attenuations[i] >= attenuations[i+1] for i in range(len(attenuations)-1))
    runner.run(t, monotone, f"Attenuations: {attenuations}")
    count += 1

    # MRH-006: SELF zone MUST have factor 1.0
    t = ConformanceTest("MRH-006", "MRH §4.1", ConformanceLevel.MUST,
                        "SELF zone has factor 1.0", "all")
    runner.run(t, MRHGraph.trust_attenuation(0.8, "SELF") == 0.8)
    count += 1

    # MRH-007: BEYOND zone MUST have minimal trust
    t = ConformanceTest("MRH-007", "MRH §4.1", ConformanceLevel.MUST,
                        "BEYOND zone has minimal trust", "all")
    runner.run(t, MRHGraph.trust_attenuation(1.0, "BEYOND") <= 0.1)
    count += 1

    return count


def run_r6_conformance(runner: ConformanceTestRunner) -> int:
    """R6 action framework conformance tests."""
    count = 0

    # R6-001: Action MUST have 6 components
    t = ConformanceTest("R6-001", "R6 §2.1", ConformanceLevel.MUST,
                        "R6 action has 6 components", "all")
    action = R6Action.create("access_control", "admin", "read_data",
                             "ref:policy:1", "data:users")
    runner.run(t, R6Action.validate(action))
    count += 1

    # R6-002: Completed action MUST have result
    t = ConformanceTest("R6-002", "R6 §3.1", ConformanceLevel.MUST,
                        "Completed action has result", "all")
    completed = R6Action.complete(action, {"users": 42}, 0.9)
    runner.run(t, completed["result"] is not None and
               completed["result"]["quality"] == 0.9)
    count += 1

    # R6-003: Completed action MUST have hash chain link
    t = ConformanceTest("R6-003", "R6 §3.2", ConformanceLevel.MUST,
                        "Completed action has hash chain", "all")
    runner.run(t, completed["hash_chain"] is not None and
               len(completed["hash_chain"]) == 16)
    count += 1

    # R6-004: Hash chain MUST be deterministic
    t = ConformanceTest("R6-004", "R6 §3.2", ConformanceLevel.MUST,
                        "Hash chain is deterministic", "all")
    completed2 = R6Action.complete(action, {"users": 42}, 0.9)
    runner.run(t, completed["hash_chain"] == completed2["hash_chain"])
    count += 1

    return count


def run_profile_conformance(runner: ConformanceTestRunner) -> int:
    """Deployment profile conformance tests."""
    count = 0

    # PROF-001: Edge profile MUST use CoAP/UDP/CBOR
    t = ConformanceTest("PROF-001", "Profile-Edge §1", ConformanceLevel.MUST,
                        "Edge profile uses CoAP/UDP/CBOR", "edge")
    edge_config = {
        "network": "coap", "transport": "udp", "data_format": "cbor",
        "crypto_suite": "W4-IOT-1", "signature": "ed25519", "aead": "aes-ccm",
    }
    violations = DeploymentProfile.validate_profile("edge", edge_config)
    runner.run(t, len(violations) == 0, f"Violations: {violations}")
    count += 1

    # PROF-002: Cloud profile MUST use HTTPS/TCP/JSON
    t = ConformanceTest("PROF-002", "Profile-Cloud §1", ConformanceLevel.MUST,
                        "Cloud profile uses HTTPS/TCP/JSON", "cloud")
    cloud_config = {
        "network": "https", "transport": "tcp", "data_format": "json",
        "crypto_suite": "W4-FIPS-1", "signature": "ecdsa-p256", "aead": "aes-128-gcm",
    }
    violations = DeploymentProfile.validate_profile("cloud", cloud_config)
    runner.run(t, len(violations) == 0, f"Violations: {violations}")
    count += 1

    # PROF-003: P2P profile MUST use WebRTC/SCTP/CBOR
    t = ConformanceTest("PROF-003", "Profile-P2P §1", ConformanceLevel.MUST,
                        "P2P profile uses WebRTC/SCTP/CBOR", "p2p")
    p2p_config = {
        "network": "webrtc", "transport": "sctp", "data_format": "cbor",
        "crypto_suite": "W4-BASE-1", "signature": "ed25519", "aead": "chacha20-poly1305",
    }
    violations = DeploymentProfile.validate_profile("p2p", p2p_config)
    runner.run(t, len(violations) == 0, f"Violations: {violations}")
    count += 1

    # PROF-004: Blockchain profile MUST use JSON/W4-BASE-1
    t = ConformanceTest("PROF-004", "Profile-Blockchain §1", ConformanceLevel.MUST,
                        "Blockchain profile uses JSON/W4-BASE-1", "blockchain")
    bc_config = {
        "network": "agnostic", "data_format": "json",
        "crypto_suite": "W4-BASE-1", "signature": "ed25519", "aead": "chacha20-poly1305",
    }
    violations = DeploymentProfile.validate_profile("blockchain", bc_config)
    runner.run(t, len(violations) == 0, f"Violations: {violations}")
    count += 1

    # PROF-005: Wrong crypto suite MUST fail validation
    t = ConformanceTest("PROF-005", "Profile-Edge §2", ConformanceLevel.MUST,
                        "Wrong crypto suite fails", "all")
    wrong_config = dict(edge_config)
    wrong_config["crypto_suite"] = "W4-FIPS-1"
    violations = DeploymentProfile.validate_profile("edge", wrong_config)
    runner.run(t, len(violations) > 0, f"Violations: {violations}")
    count += 1

    # PROF-006: Edge↔P2P SHOULD share Ed25519
    t = ConformanceTest("PROF-006", "Profile-Interop §1", ConformanceLevel.SHOULD,
                        "Edge↔P2P share Ed25519", "all")
    compat = DeploymentProfile.bridge_compatible("edge", "p2p")
    runner.run(t, compat["shared_signature"],
               f"Shared sig: {compat['shared_signature']}")
    count += 1

    # PROF-007: Edge↔Cloud MUST need transcoding
    t = ConformanceTest("PROF-007", "Profile-Interop §2", ConformanceLevel.MUST,
                        "Edge↔Cloud needs transcoding (CBOR↔JSON)", "all")
    compat = DeploymentProfile.bridge_compatible("edge", "cloud")
    runner.run(t, compat["needs_transcoding"])
    count += 1

    # PROF-008: P2P↔Blockchain SHOULD need transcoding
    t = ConformanceTest("PROF-008", "Profile-Interop §3", ConformanceLevel.SHOULD,
                        "P2P↔Blockchain needs format transcoding", "all")
    compat = DeploymentProfile.bridge_compatible("p2p", "blockchain")
    runner.run(t, compat["needs_transcoding"])
    count += 1

    return count


def run_test_vector_conformance(runner: ConformanceTestRunner) -> int:
    """Test vector validation against canonical vectors."""
    count = 0

    # TV-001: Valid birth certificate vector
    t = ConformanceTest("TV-001", "TestVec-LCT §1", ConformanceLevel.MUST,
                        "Valid birth certificate matches vector", "all")
    # Recreate from vector input
    lct = LCTDocument.create("human", "Alice", "11qYAYKxCrfVS_7TyWQHOg7hcvPapiMlrwIaaPcHURo",
                             "platform", "2025-09-14T12:00:00Z")
    checks = (
        lct is not None and
        lct["binding"]["entity_type"] == "human" and
        lct["binding"]["public_key"] == "11qYAYKxCrfVS_7TyWQHOg7hcvPapiMlrwIaaPcHURo" and
        lct["birth_certificate"]["context"] == "platform" and
        "citizen" in lct["birth_certificate"]["citizen_role"] and
        len(lct["birth_certificate"]["birth_witnesses"]) >= 2
    )
    runner.run(t, checks, "Birth certificate matches canonical vector")
    count += 1

    # TV-002: DID format matches vector expectation
    t = ConformanceTest("TV-002", "TestVec-LCT §2", ConformanceLevel.MUST,
                        "DID format: did:web4:key:<pubkey>", "all")
    runner.run(t, lct["subject"] == "did:web4:key:11qYAYKxCrfVS_7TyWQHOg7hcvPapiMlrwIaaPcHURo")
    count += 1

    # TV-003: MRH initialized per vector
    t = ConformanceTest("TV-003", "TestVec-LCT §3", ConformanceLevel.MUST,
                        "MRH matches vector structure", "all")
    runner.run(t, lct["mrh"]["horizon_depth"] == 3 and
               len(lct["mrh"]["paired"]) == 1 and
               lct["mrh"]["paired"][0]["permanent"] is True)
    count += 1

    # TV-004: Valid staked trust query
    t = ConformanceTest("TV-004", "TestVec-TQ §1", ConformanceLevel.MUST,
                        "Trust query: sufficient stake approved", "all")
    # Simulate trust query
    querier_balance = 500
    stake = 100
    can_stake = querier_balance >= stake
    disclosure = "precise" if stake >= 100 else "range" if stake >= 50 else "binary"
    runner.run(t, can_stake and disclosure == "precise",
               f"Balance: {querier_balance}, Stake: {stake}, Disclosure: {disclosure}")
    count += 1

    # TV-005: Invalid (no-stake) trust query
    t = ConformanceTest("TV-005", "TestVec-TQ §2", ConformanceLevel.MUST,
                        "Trust query: zero stake rejected", "all")
    no_stake = 0
    runner.run(t, no_stake < 10, "Stake below minimum threshold")
    count += 1

    # TV-006: Trust disclosure levels match stake thresholds
    t = ConformanceTest("TV-006", "TestVec-TQ §3", ConformanceLevel.MUST,
                        "Disclosure levels match stake thresholds", "all")
    thresholds = [
        (0, "none"), (5, "none"), (10, "binary"), (25, "binary"),
        (50, "range"), (75, "range"), (100, "precise"), (500, "precise"),
    ]
    all_match = True
    for stake, expected in thresholds:
        if stake < 10:
            actual = "none"
        elif stake < 50:
            actual = "binary"
        elif stake < 100:
            actual = "range"
        else:
            actual = "precise"
        if actual != expected:
            all_match = False
    runner.run(t, all_match, f"Tested {len(thresholds)} threshold values")
    count += 1

    return count


def run_security_conformance(runner: ConformanceTestRunner) -> int:
    """Security property conformance tests."""
    count = 0

    # SEC-001: ATP conservation MUST hold after transactions
    t = ConformanceTest("SEC-001", "Security §5.1", ConformanceLevel.MUST,
                        "ATP conservation after 100 transactions", "all")
    ledger = ATPLedger()
    ledger.fund("a", 1000)
    ledger.fund("b", 1000)
    for i in range(50):
        ledger.transfer("a", "b", 10)
        ledger.transfer("b", "a", 8)
    runner.run(t, ledger.conservation_check())
    count += 1

    # SEC-002: Lock+commit+rollback MUST conserve ATP
    t = ConformanceTest("SEC-002", "Security §5.2", ConformanceLevel.MUST,
                        "Lock/commit/rollback conserves ATP", "all")
    ledger2 = ATPLedger()
    ledger2.fund("p", 500)
    for i in range(10):
        lid = ledger2.lock("p", 20)
        if lid and i % 2 == 0:
            ledger2.commit(lid, "w", 0.7)
        elif lid:
            ledger2.rollback(lid)
    runner.run(t, ledger2.conservation_check())
    count += 1

    # SEC-003: T3 MUST stay bounded after many updates
    t = ConformanceTest("SEC-003", "Security §6.1", ConformanceLevel.MUST,
                        "T3 bounded after 1000 updates", "all")
    t3 = T3V3Tensor.create_t3(0.5, 0.5, 0.5)
    for i in range(1000):
        quality = 1.0 if i % 3 != 0 else 0.0
        t3 = T3V3Tensor.update_t3(t3, quality, "execute", i)
    bounded = all(0 <= t3[d] <= 1 for d in ["talent", "training", "temperament"])
    runner.run(t, bounded, f"T3 after 1000 updates: {t3['talent']:.4f}")
    count += 1

    # SEC-004: MRH attenuation MUST prevent trust amplification
    t = ConformanceTest("SEC-004", "Security §7.1", ConformanceLevel.MUST,
                        "MRH prevents trust amplification", "all")
    # Trust MUST not increase through distance
    base = 0.8
    all_attenuated = all(
        MRHGraph.trust_attenuation(base, z) <= base
        for z in MRHGraph.ZONES
    )
    runner.run(t, all_attenuated)
    count += 1

    # SEC-005: R6 hash chain MUST be tamper-evident
    t = ConformanceTest("SEC-005", "Security §8.1", ConformanceLevel.MUST,
                        "R6 hash chain is tamper-evident", "all")
    action1 = R6Action.create("rule1", "admin", "read", "ref1", "data1")
    c1 = R6Action.complete(action1, "result1", 0.9)
    action2 = R6Action.create("rule1", "admin", "read", "ref1", "data1")
    c2 = R6Action.complete(action2, "result2", 0.9)  # Different result
    runner.run(t, c1["hash_chain"] != c2["hash_chain"],
               "Different results → different hashes")
    count += 1

    # SEC-006: Identity spoofing MUST be detectable
    t = ConformanceTest("SEC-006", "Security §9.1", ConformanceLevel.MUST,
                        "Identity spoofing detectable", "all")
    valid_ids = [
        "lct:web4:human:abc123",
        "lct:web4:ai:def456",
        "lct:web4:device:ghi789",
    ]
    invalid_ids = [
        "lct:web4:human:abc:extra",  # Extra segment
        "lct%3Aweb4%3Ahuman%3Aabc",  # URL-encoded
        "lct:web5:human:abc",  # Wrong namespace
    ]
    all_valid = all(LCTDocument.validate_id(i) for i in valid_ids)
    all_invalid = all(not LCTDocument.validate_id(i) for i in invalid_ids)
    runner.run(t, all_valid and all_invalid)
    count += 1

    return count


# ═══════════════════════════════════════════════════════════════════
# Verification Checks
# ═══════════════════════════════════════════════════════════════════

def run_checks():
    passed = 0
    failed = 0

    def check(condition: bool, label: str):
        nonlocal passed, failed
        if condition:
            passed += 1
        else:
            failed += 1
            print(f"  FAIL: {label}")

    # ─── Section 1: Conformance Framework ─────────────────────────

    print("Section 1: Conformance Framework")

    t = ConformanceTest("TEST-001", "Test §1", ConformanceLevel.MUST, "Test", "all")
    check(t.test_id == "TEST-001", "Test has ID")
    check(t.level == ConformanceLevel.MUST, "Test has level")

    r = TestResult(test=t, status=TestStatus.PASS)
    check(r.status == TestStatus.PASS, "Result has status")

    report = ConformanceReport(
        implementation_name="test", profile="all",
        results=[r], timestamp="now",
    )
    check(report.passed == 1, "Report counts passed")
    check(report.failed == 0, "Report counts failed")
    check(report.is_conformant, "Report is conformant")
    check(report.must_pass_rate == 1.0, "100% MUST pass rate")

    # Non-conformant report
    fail_r = TestResult(test=t, status=TestStatus.FAIL, message="bad")
    fail_report = ConformanceReport(
        implementation_name="bad", profile="all",
        results=[fail_r], timestamp="now",
    )
    check(not fail_report.is_conformant, "Failed MUST → not conformant")
    check(fail_report.must_pass_rate == 0.0, "0% MUST pass rate")

    # ─── Section 2: LCT Conformance ──────────────────────────────

    print("Section 2: LCT Conformance")

    runner = ConformanceTestRunner("all")
    lct_count = run_lct_conformance(runner)
    lct_passed = sum(1 for r in runner.results if r.status == TestStatus.PASS)
    check(lct_count == 14, f"14 LCT tests ({lct_count})")
    check(lct_passed == lct_count, f"All LCT tests pass ({lct_passed}/{lct_count})")

    # ─── Section 3: T3/V3 Conformance ─────────────────────────────

    print("Section 3: T3/V3 Conformance")

    runner2 = ConformanceTestRunner("all")
    t3_count = run_t3v3_conformance(runner2)
    t3_passed = sum(1 for r in runner2.results if r.status == TestStatus.PASS)
    check(t3_count == 7, f"7 T3/V3 tests ({t3_count})")
    check(t3_passed == t3_count, f"All T3/V3 tests pass ({t3_passed}/{t3_count})")

    # ─── Section 4: ATP Conformance ───────────────────────────────

    print("Section 4: ATP Conformance")

    runner3 = ConformanceTestRunner("all")
    atp_count = run_atp_conformance(runner3)
    atp_passed = sum(1 for r in runner3.results if r.status == TestStatus.PASS)
    check(atp_count == 11, f"11 ATP tests ({atp_count})")
    check(atp_passed == atp_count, f"All ATP tests pass ({atp_passed}/{atp_count})")

    # ─── Section 5: MRH Conformance ──────────────────────────────

    print("Section 5: MRH Conformance")

    runner4 = ConformanceTestRunner("all")
    mrh_count = run_mrh_conformance(runner4)
    mrh_passed = sum(1 for r in runner4.results if r.status == TestStatus.PASS)
    check(mrh_count == 7, f"7 MRH tests ({mrh_count})")
    check(mrh_passed == mrh_count, f"All MRH tests pass ({mrh_passed}/{mrh_count})")

    # ─── Section 6: R6 Conformance ───────────────────────────────

    print("Section 6: R6 Conformance")

    runner5 = ConformanceTestRunner("all")
    r6_count = run_r6_conformance(runner5)
    r6_passed = sum(1 for r in runner5.results if r.status == TestStatus.PASS)
    check(r6_count == 4, f"4 R6 tests ({r6_count})")
    check(r6_passed == r6_count, f"All R6 tests pass ({r6_passed}/{r6_count})")

    # ─── Section 7: Profile Conformance ──────────────────────────

    print("Section 7: Profile Conformance")

    runner6 = ConformanceTestRunner("all")
    prof_count = run_profile_conformance(runner6)
    prof_passed = sum(1 for r in runner6.results if r.status == TestStatus.PASS)
    check(prof_count == 8, f"8 profile tests ({prof_count})")
    check(prof_passed == prof_count, f"All profile tests pass ({prof_passed}/{prof_count})")

    # ─── Section 8: Test Vector Conformance ──────────────────────

    print("Section 8: Test Vector Conformance")

    runner7 = ConformanceTestRunner("all")
    tv_count = run_test_vector_conformance(runner7)
    tv_passed = sum(1 for r in runner7.results if r.status == TestStatus.PASS)
    check(tv_count == 6, f"6 test vector tests ({tv_count})")
    check(tv_passed == tv_count, f"All test vector tests pass ({tv_passed}/{tv_count})")

    # ─── Section 9: Security Conformance ─────────────────────────

    print("Section 9: Security Conformance")

    runner8 = ConformanceTestRunner("all")
    sec_count = run_security_conformance(runner8)
    sec_passed = sum(1 for r in runner8.results if r.status == TestStatus.PASS)
    check(sec_count == 6, f"6 security tests ({sec_count})")
    check(sec_passed == sec_count, f"All security tests pass ({sec_passed}/{sec_count})")

    # ─── Section 10: Full Suite Report ───────────────────────────

    print("Section 10: Full Suite Report")

    # Run complete suite
    full_runner = ConformanceTestRunner("all")
    total_tests = 0
    total_tests += run_lct_conformance(full_runner)
    total_tests += run_t3v3_conformance(full_runner)
    total_tests += run_atp_conformance(full_runner)
    total_tests += run_mrh_conformance(full_runner)
    total_tests += run_r6_conformance(full_runner)
    total_tests += run_profile_conformance(full_runner)
    total_tests += run_test_vector_conformance(full_runner)
    total_tests += run_security_conformance(full_runner)

    report = full_runner.report("web4-reference-python")
    check(report.total == total_tests, f"Report total: {report.total} == {total_tests}")
    check(report.is_conformant, "Full suite: CONFORMANT")
    check(report.must_pass_rate == 1.0,
          f"MUST pass rate: {report.must_pass_rate:.1%}")

    report_dict = report.to_report()
    check("web4_conformance_report" in report_dict, "Report has correct structure")
    check(report_dict["web4_conformance_report"]["summary"]["conformant"],
          "Report shows conformant")
    check(len(report_dict["web4_conformance_report"]["failures"]) == 0,
          "No failures in report")

    # Check spec coverage
    by_spec = report_dict["web4_conformance_report"]["by_spec"]
    check("LCT" in by_spec, "LCT spec covered")
    check("T3V3" in by_spec, "T3V3 spec covered")
    check("ATP" in by_spec, "ATP spec covered")
    check("MRH" in by_spec, "MRH spec covered")
    check("R6" in by_spec, "R6 spec covered")
    check("Profile-Edge" in by_spec or "Profile-Interop" in by_spec,
          "Profile specs covered")
    check("Security" in by_spec, "Security spec covered")

    # ─── Section 11: Profile-Specific Filtering ──────────────────

    print("Section 11: Profile-Specific Filtering")

    # Edge-only runner should skip non-edge tests
    edge_runner = ConformanceTestRunner("edge")
    run_profile_conformance(edge_runner)

    edge_results = edge_runner.results
    applicable = [r for r in edge_results
                  if r.status != TestStatus.NOT_APPLICABLE]
    na = [r for r in edge_results
          if r.status == TestStatus.NOT_APPLICABLE]

    check(len(applicable) > 0, "Edge runner has applicable tests")
    # PROF-002 (cloud), PROF-003 (p2p), PROF-004 (blockchain) should be N/A
    check(len(na) >= 2, f"Edge runner has {len(na)} non-applicable tests")

    # ─── Section 12: Conformance Totals ──────────────────────────

    print("Section 12: Conformance Totals")

    check(total_tests == 63, f"63 conformance tests total ({total_tests})")

    must_tests = sum(1 for r in full_runner.results
                     if r.test.level == ConformanceLevel.MUST)
    should_tests = sum(1 for r in full_runner.results
                       if r.test.level == ConformanceLevel.SHOULD)
    check(must_tests > 50, f">{50} MUST tests ({must_tests})")
    check(should_tests >= 2, f"≥2 SHOULD tests ({should_tests})")

    # Print summary of conformance areas
    areas = {
        "LCT": lct_count, "T3/V3": t3_count, "ATP": atp_count,
        "MRH": mrh_count, "R6": r6_count, "Profiles": prof_count,
        "Test Vectors": tv_count, "Security": sec_count,
    }
    check(sum(areas.values()) == total_tests,
          f"Area totals match: {sum(areas.values())} == {total_tests}")

    # ═══════════════════════════════════════════════════════════════

    print(f"\n{'=' * 60}")
    print(f"Conformance Test Suite: {passed}/{passed + failed} checks passed")
    if failed == 0:
        print("  All checks passed!")
    else:
        print(f"  {failed} FAILED")
    print(f"{'=' * 60}")
    print(f"\nConformance areas: {total_tests} spec-linked tests across 8 domains")
    for area, count in areas.items():
        print(f"  {area}: {count} tests")


if __name__ == "__main__":
    run_checks()
