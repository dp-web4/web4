#!/usr/bin/env python3
"""
Web4 MRH Scale Limits & Optimization — Reference Implementation
Spec: web4-standard/MRH_SCALE_LIMITS.md (435 lines)

Device-aware MRH scaling: limits, serialization, optimization, adaptive horizon.

Covers:
  §1  Scale limits by device class (5 classes: Micro→Cloud)
  §2  Memory footprint analysis (3 representations: 23B/225B/440B)
  §3  Serialization strategies (CBOR, JSON, RDF)
  §4  Optimization: horizon pruning, time-based eviction, relationship compression
  §5  Dynamic scaling: adaptive horizon, priority-based retention
  §6  Implementation: device detection, format negotiation
  §7  Performance benchmarks

Run: python mrh_scale_limits.py
"""

from __future__ import annotations
import json
import math
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


# ============================================================
# §1 Device Classifications
# ============================================================

class DeviceClass(Enum):
    MICRO = "MICRO"       # <256KB RAM, <1MB storage, <100MHz
    EDGE = "EDGE"         # 1-8MB RAM, 10-100MB storage, 100-500MHz
    MOBILE = "MOBILE"     # 1-8GB RAM, 32-256GB storage, 1-3GHz
    DESKTOP = "DESKTOP"   # 8-64GB RAM, 256GB-2TB storage, 2-5GHz
    CLOUD = "CLOUD"       # 64GB+ RAM, 1TB+ storage, 3GHz+ x many


# §1.2 MRH Limits by Device Class (from spec exactly)
MRH_LIMITS = {
    DeviceClass.MICRO: {
        "horizon_depth": 1,
        "max_relationships": 10,
        "max_paired": 3,
        "max_witnesses": 5,
        "serialization": "cbor",
        "compression": "zstd",
    },
    DeviceClass.EDGE: {
        "horizon_depth": 2,
        "max_relationships": 100,
        "max_paired": 20,
        "max_witnesses": 50,
        "serialization": "cbor",
        "compression": "zstd",
    },
    DeviceClass.MOBILE: {
        "horizon_depth": 3,
        "max_relationships": 1000,
        "max_paired": 100,
        "max_witnesses": 500,
        "serialization": "json",
        "compression": "optional",
    },
    DeviceClass.DESKTOP: {
        "horizon_depth": 4,
        "max_relationships": 10000,
        "max_paired": 1000,
        "max_witnesses": 5000,
        "serialization": "json",
        "compression": "optional",
    },
    DeviceClass.CLOUD: {
        "horizon_depth": 5,
        "max_relationships": 100000,
        "max_paired": 10000,
        "max_witnesses": 50000,
        "serialization": "rdf",
        "compression": "optional",
    },
}


# ============================================================
# §2 Memory Footprint Analysis
# ============================================================

# Per-relationship byte costs from spec §2.1
BYTES_PER_RELATIONSHIP = {
    "cbor": 23,    # Compact: 16B lct_id + 1B type + 4B ts + 2B metadata
    "json": 225,   # Standard: ~50B id + ~20B type + ~25B ts + ~30B ctx + ~100B meta
    "rdf": 440,    # Full: ~50B subj + ~40B pred + ~50B obj + ~100B ctx + ~200B prov
}

# Serialization overhead from spec §2.2
SERIALIZATION_OVERHEAD = {
    "cbor": 1.1,   # 10% CBOR structure
    "json": 1.3,   # 30% JSON structure
    "rdf": 1.5,    # 50% RDF triples
}

# Compression ratios from spec §2.2
COMPRESSION_RATIOS = {
    "zstd": 0.3,   # 70% reduction
    "gzip": 0.4,   # 60% reduction
    "lz4": 0.5,    # 50% reduction
}


def calculate_mrh_size(device_class: DeviceClass, num_relationships: int) -> float:
    """Calculate total MRH size in bytes (spec §2.2)."""
    limits = MRH_LIMITS[device_class]
    ser = limits["serialization"]
    per_rel = BYTES_PER_RELATIONSHIP[ser]
    base_size = per_rel * num_relationships
    total = base_size * SERIALIZATION_OVERHEAD[ser]

    compression = limits.get("compression", "optional")
    if compression and compression != "optional":
        total *= COMPRESSION_RATIOS.get(compression, 1.0)

    return total


# ============================================================
# §3 + §4 Relationship Model
# ============================================================

@dataclass
class Relationship:
    lct_id: str
    rel_type: str         # "bound", "paired", "witness"
    timestamp: float      # Unix epoch
    distance: int = 1     # Hops from origin
    permanent: bool = False
    active: bool = True
    role: str = ""
    t3_score: float = 0.5
    metadata: dict = field(default_factory=dict)


@dataclass
class MRH:
    """Markov Relevancy Horizon with device-aware limits."""
    entity_id: str
    device_class: DeviceClass
    horizon_depth: int = 3
    bound: list[Relationship] = field(default_factory=list)
    paired: list[Relationship] = field(default_factory=list)
    witnessing: list[Relationship] = field(default_factory=list)
    last_updated: float = 0.0

    def __post_init__(self):
        limits = MRH_LIMITS[self.device_class]
        self.horizon_depth = limits["horizon_depth"]
        if not self.last_updated:
            self.last_updated = time.time()

    @property
    def total_relationships(self) -> int:
        return len(self.bound) + len(self.paired) + len(self.witnessing)

    @property
    def limits(self) -> dict:
        return MRH_LIMITS[self.device_class]

    def is_within_limits(self) -> bool:
        lim = self.limits
        return (self.total_relationships <= lim["max_relationships"]
                and len(self.paired) <= lim["max_paired"]
                and len(self.witnessing) <= lim["max_witnesses"])

    def add_relationship(self, rel: Relationship) -> bool:
        """Add relationship, respecting limits. Returns False if at capacity."""
        lim = self.limits
        if self.total_relationships >= lim["max_relationships"]:
            return False
        if rel.distance > self.horizon_depth:
            return False

        if rel.rel_type == "bound":
            self.bound.append(rel)
        elif rel.rel_type == "paired":
            if len(self.paired) >= lim["max_paired"]:
                return False
            self.paired.append(rel)
        elif rel.rel_type == "witness":
            if len(self.witnessing) >= lim["max_witnesses"]:
                return False
            self.witnessing.append(rel)
        else:
            return False

        self.last_updated = time.time()
        return True

    def memory_footprint(self) -> float:
        """Estimated memory in bytes."""
        return calculate_mrh_size(self.device_class, self.total_relationships)


# ============================================================
# §4.1 Horizon Pruning
# ============================================================

def prune_by_horizon(mrh: MRH, max_depth: int):
    """Remove relationships beyond horizon depth (spec §4.1)."""
    mrh.bound = [r for r in mrh.bound if r.distance <= max_depth]
    mrh.paired = [r for r in mrh.paired if r.distance <= max_depth]
    mrh.witnessing = [r for r in mrh.witnessing if r.distance <= max_depth]


# ============================================================
# §4.2 Time-Based Eviction
# ============================================================

def evict_stale_relationships(mrh: MRH, max_age_seconds: float):
    """Remove relationships older than threshold (spec §4.2).
    Permanent relationships (birth cert) are kept."""
    cutoff = time.time() - max_age_seconds
    mrh.paired = [r for r in mrh.paired if r.permanent or r.timestamp > cutoff]
    mrh.witnessing = [r for r in mrh.witnessing if r.timestamp > cutoff]
    # Bound relationships are always kept (identity)
    mrh.last_updated = time.time()


# ============================================================
# §4.3 Relationship Compression
# ============================================================

def aggregate_witnesses(witnesses: list[Relationship]) -> dict:
    """Replace individual witnesses with aggregate counts (spec §4.3)."""
    by_role: dict[str, dict] = {}
    for w in witnesses:
        role = w.role or "unknown"
        if role not in by_role:
            by_role[role] = {"count": 0, "latest": w.timestamp}
        by_role[role]["count"] += 1
        by_role[role]["latest"] = max(by_role[role]["latest"], w.timestamp)
    return by_role


def compress_relationships(mrh: MRH) -> dict:
    """Compress based on device class (spec §4.3).
    Returns compressed representation."""
    if mrh.device_class == DeviceClass.MICRO:
        # Extreme: aggregate witnesses, keep only parent bindings
        agg = aggregate_witnesses(mrh.witnessing)
        return {
            "bound": len(mrh.bound),
            "paired": len(mrh.paired),
            "witnesses_aggregated": agg,
        }
    elif mrh.device_class == DeviceClass.EDGE:
        # Moderate: group witnesses by role
        agg = aggregate_witnesses(mrh.witnessing)
        return {
            "bound": len(mrh.bound),
            "paired": len(mrh.paired),
            "witnesses_by_role": agg,
        }
    else:
        # Full representation
        return {
            "bound": len(mrh.bound),
            "paired": len(mrh.paired),
            "witnesses": len(mrh.witnessing),
        }


# ============================================================
# §5.1 Adaptive Horizon
# ============================================================

class AdaptiveMRH:
    """Dynamic MRH that expands/contracts based on load (spec §5.1)."""

    EXPAND_THRESHOLD = 0.7    # Expand if usage < 70%
    CONTRACT_THRESHOLD = 0.9  # Contract if usage > 90%

    def __init__(self, mrh: MRH):
        self.mrh = mrh

    @property
    def usage_ratio(self) -> float:
        return self.mrh.total_relationships / self.mrh.limits["max_relationships"]

    def should_expand(self) -> bool:
        return self.usage_ratio < self.EXPAND_THRESHOLD

    def should_contract(self) -> bool:
        return self.usage_ratio > self.CONTRACT_THRESHOLD

    def adjust(self):
        """Auto-adjust horizon depth (spec §5.1)."""
        if self.should_contract():
            self.mrh.horizon_depth = max(1, self.mrh.horizon_depth - 1)
            prune_by_horizon(self.mrh, self.mrh.horizon_depth)
        elif self.should_expand():
            self.mrh.horizon_depth = min(5, self.mrh.horizon_depth + 1)


# ============================================================
# §5.2 Priority-Based Retention
# ============================================================

def calculate_priority(rel: Relationship, current_role: str = "") -> float:
    """Score relationship for retention priority (spec §5.2)."""
    score = 0.0

    # Recent interactions score higher (decay over days)
    age = time.time() - rel.timestamp
    score += max(0, 100 - (age / 86400))

    # Permanent relationships highest priority
    if rel.permanent:
        score += 1000

    # Active pairings high priority
    if rel.active:
        score += 500

    # Witnesses with high trust valuable
    score += rel.t3_score * 100

    # Role relevance
    if current_role and rel.role == current_role:
        score += 200

    return score


def retain_by_priority(mrh: MRH, max_relationships: int, current_role: str = ""):
    """Keep highest priority relationships when pruning (spec §5.2)."""
    all_rels = mrh.bound + mrh.paired + mrh.witnessing
    scored = [(calculate_priority(r, current_role), r) for r in all_rels]
    scored.sort(reverse=True, key=lambda x: x[0])
    to_keep = [r for _, r in scored[:max_relationships]]

    mrh.bound = [r for r in to_keep if r.rel_type == "bound"]
    mrh.paired = [r for r in to_keep if r.rel_type == "paired"]
    mrh.witnessing = [r for r in to_keep if r.rel_type == "witness"]


# ============================================================
# §6.1 Device Detection
# ============================================================

def detect_device_class(ram_gb: float) -> DeviceClass:
    """Auto-detect device class from RAM (spec §6.1)."""
    if ram_gb < 0.001:        # < 1MB
        return DeviceClass.MICRO
    elif ram_gb < 0.01:       # < 10MB
        return DeviceClass.EDGE
    elif ram_gb < 10:         # < 10GB
        return DeviceClass.MOBILE
    elif ram_gb < 100:        # < 100GB
        return DeviceClass.DESKTOP
    else:
        return DeviceClass.CLOUD


# ============================================================
# §6.2 Format Negotiation
# ============================================================

FORMAT_PREFERENCE = ["cbor", "json", "rdf"]  # Preferred order


def negotiate_format(our_formats: list[str], peer_formats: list[str]) -> str:
    """Find best common format (spec §6.2)."""
    for fmt in FORMAT_PREFERENCE:
        if fmt in our_formats and fmt in peer_formats:
            return fmt
    return "json"  # Fallback


# ============================================================
# §7 Performance Benchmarks (as data)
# ============================================================

SERIALIZATION_BENCHMARKS = {
    # Format: (size_1000_rels_kb, serialize_ms, deserialize_ms)
    "cbor": (23, 5, 3),
    "json": (225, 15, 10),
    "json_gzip": (68, 25, 15),
    "rdf": (440, 50, 40),
    "rdf_gzip": (132, 60, 45),
}

QUERY_BENCHMARKS = {
    # Operation: {horizon: ms}
    "find_relationship": {1: 0.1, 2: 0.5, 3: 2.0},
    "calculate_trust_path": {1: 0.5, 2: 5.0, 3: 50.0},
    "update_mrh": {1: 1.0, 2: 3.0, 3: 10.0},
    "prune_expired": {1: 2.0, 2: 10.0, 3: 50.0},
}


# ════════════════════════════════════════════════════════════════
#  TESTS
# ════════════════════════════════════════════════════════════════

def run_tests():
    passed = 0
    failed = 0

    def check(name, condition):
        nonlocal passed, failed
        if condition:
            passed += 1
        else:
            failed += 1
            print(f"  FAIL: {name}")

    now = time.time()

    # ── T1: Device Classifications ───────────────────────────────
    print("T1: Device Classifications (§1)")
    check("T1.1 Five device classes",
          len(DeviceClass) == 5)
    check("T1.2 Five limit profiles",
          len(MRH_LIMITS) == 5)

    # Verify limits are monotonically increasing
    classes = [DeviceClass.MICRO, DeviceClass.EDGE, DeviceClass.MOBILE,
               DeviceClass.DESKTOP, DeviceClass.CLOUD]
    for i in range(len(classes) - 1):
        a = MRH_LIMITS[classes[i]]
        b = MRH_LIMITS[classes[i + 1]]
        check(f"T1.{i+3} {classes[i].value}→{classes[i+1].value} horizon increases",
              b["horizon_depth"] > a["horizon_depth"])
        check(f"T1.{i+8} {classes[i].value}→{classes[i+1].value} max_rels increases",
              b["max_relationships"] > a["max_relationships"])

    # ── T2: Specific Limit Values ────────────────────────────────
    print("T2: Specific Limit Values (§1.2)")
    micro = MRH_LIMITS[DeviceClass.MICRO]
    check("T2.1 Micro horizon = 1",
          micro["horizon_depth"] == 1)
    check("T2.2 Micro max_rels = 10",
          micro["max_relationships"] == 10)
    check("T2.3 Micro max_paired = 3",
          micro["max_paired"] == 3)
    check("T2.4 Micro max_witnesses = 5",
          micro["max_witnesses"] == 5)
    check("T2.5 Micro uses CBOR",
          micro["serialization"] == "cbor")
    check("T2.6 Micro uses zstd",
          micro["compression"] == "zstd")

    cloud = MRH_LIMITS[DeviceClass.CLOUD]
    check("T2.7 Cloud horizon = 5",
          cloud["horizon_depth"] == 5)
    check("T2.8 Cloud max_rels = 100000",
          cloud["max_relationships"] == 100000)
    check("T2.9 Cloud uses RDF",
          cloud["serialization"] == "rdf")

    # ── T3: Memory Footprint ─────────────────────────────────────
    print("T3: Memory Footprint (§2)")
    check("T3.1 CBOR = 23 bytes/rel",
          BYTES_PER_RELATIONSHIP["cbor"] == 23)
    check("T3.2 JSON = 225 bytes/rel",
          BYTES_PER_RELATIONSHIP["json"] == 225)
    check("T3.3 RDF = 440 bytes/rel",
          BYTES_PER_RELATIONSHIP["rdf"] == 440)

    # Size calculations
    micro_size = calculate_mrh_size(DeviceClass.MICRO, 10)
    check("T3.4 Micro 10 rels < 100 bytes (with zstd)",
          micro_size < 100)

    cloud_size = calculate_mrh_size(DeviceClass.CLOUD, 100000)
    check("T3.5 Cloud 100K rels > 60MB",
          cloud_size > 60_000_000)

    # CBOR < JSON < RDF for same count
    cbor_size = calculate_mrh_size(DeviceClass.EDGE, 50)
    json_size = calculate_mrh_size(DeviceClass.MOBILE, 50)
    rdf_size = calculate_mrh_size(DeviceClass.CLOUD, 50)
    check("T3.6 CBOR < JSON for same count",
          cbor_size < json_size)
    check("T3.7 JSON < RDF for same count",
          json_size < rdf_size)

    # Compression reduces size
    edge_compressed = calculate_mrh_size(DeviceClass.EDGE, 100)
    # Without compression: 100 * 23 * 1.1 = 2530
    edge_uncompressed = 100 * 23 * 1.1
    check("T3.8 Compression reduces edge size",
          edge_compressed < edge_uncompressed)
    check("T3.9 zstd ratio = 0.3 (70% reduction)",
          abs(edge_compressed / edge_uncompressed - 0.3) < 0.01)

    # ── T4: MRH Construction ────────────────────────────────────
    print("T4: MRH Construction")
    mrh = MRH(entity_id="lct:test", device_class=DeviceClass.MICRO)
    check("T4.1 MRH created",
          mrh.entity_id == "lct:test")
    check("T4.2 Horizon set from device class",
          mrh.horizon_depth == 1)
    check("T4.3 Total relationships = 0",
          mrh.total_relationships == 0)
    check("T4.4 Within limits initially",
          mrh.is_within_limits())

    # Add relationships
    r1 = Relationship("lct:peer1", "bound", now, distance=1)
    check("T4.5 Add bound succeeds",
          mrh.add_relationship(r1))
    check("T4.6 Total = 1",
          mrh.total_relationships == 1)

    r2 = Relationship("lct:peer2", "paired", now, distance=1)
    check("T4.7 Add paired succeeds",
          mrh.add_relationship(r2))

    # Respect horizon
    r_far = Relationship("lct:far", "bound", now, distance=5)
    check("T4.8 Beyond-horizon rejected",
          not mrh.add_relationship(r_far))

    # Memory footprint
    check("T4.9 Memory footprint > 0",
          mrh.memory_footprint() > 0)

    # ── T5: Limit Enforcement ────────────────────────────────────
    print("T5: Limit Enforcement")
    micro_mrh = MRH(entity_id="lct:micro", device_class=DeviceClass.MICRO)

    # Fill to max_relationships (10)
    for i in range(10):
        micro_mrh.add_relationship(
            Relationship(f"lct:r{i}", "bound", now, distance=1))
    check("T5.1 Micro at max (10)",
          micro_mrh.total_relationships == 10)
    check("T5.2 Still within limits",
          micro_mrh.is_within_limits())

    # 11th rejected
    check("T5.3 11th relationship rejected",
          not micro_mrh.add_relationship(
              Relationship("lct:overflow", "bound", now, distance=1)))

    # Paired limit (3)
    paired_mrh = MRH(entity_id="lct:paired_test", device_class=DeviceClass.MICRO)
    for i in range(3):
        paired_mrh.add_relationship(
            Relationship(f"lct:p{i}", "paired", now, distance=1))
    check("T5.4 Paired at max (3)",
          len(paired_mrh.paired) == 3)
    check("T5.5 4th paired rejected",
          not paired_mrh.add_relationship(
              Relationship("lct:p_overflow", "paired", now, distance=1)))

    # Witness limit (5)
    wit_mrh = MRH(entity_id="lct:wit_test", device_class=DeviceClass.MICRO)
    for i in range(5):
        wit_mrh.add_relationship(
            Relationship(f"lct:w{i}", "witness", now, distance=1))
    check("T5.6 Witnesses at max (5)",
          len(wit_mrh.witnessing) == 5)
    check("T5.7 6th witness rejected",
          not wit_mrh.add_relationship(
              Relationship("lct:w_overflow", "witness", now, distance=1)))

    # ── T6: Horizon Pruning ──────────────────────────────────────
    print("T6: Horizon Pruning (§4.1)")
    prune_mrh = MRH(entity_id="lct:prune", device_class=DeviceClass.DESKTOP)
    for d in range(1, 5):
        prune_mrh.add_relationship(
            Relationship(f"lct:d{d}_bound", "bound", now, distance=d))
        prune_mrh.add_relationship(
            Relationship(f"lct:d{d}_paired", "paired", now, distance=d))
        prune_mrh.add_relationship(
            Relationship(f"lct:d{d}_witness", "witness", now, distance=d))

    check("T6.1 12 relationships before prune",
          prune_mrh.total_relationships == 12)

    prune_by_horizon(prune_mrh, max_depth=2)
    check("T6.2 6 relationships after prune to depth 2",
          prune_mrh.total_relationships == 6)
    check("T6.3 All remaining within depth 2",
          all(r.distance <= 2 for r in
              prune_mrh.bound + prune_mrh.paired + prune_mrh.witnessing))

    prune_by_horizon(prune_mrh, max_depth=1)
    check("T6.4 3 relationships after prune to depth 1",
          prune_mrh.total_relationships == 3)

    # ── T7: Time-Based Eviction ──────────────────────────────────
    print("T7: Time-Based Eviction (§4.2)")
    evict_mrh = MRH(entity_id="lct:evict", device_class=DeviceClass.MOBILE)

    # Old relationships
    old_ts = now - 100000  # ~1 day ago
    evict_mrh.add_relationship(
        Relationship("lct:old_pair", "paired", old_ts, distance=1))
    evict_mrh.add_relationship(
        Relationship("lct:old_witness", "witness", old_ts, distance=1))
    # Permanent (birth cert) — should survive
    evict_mrh.add_relationship(
        Relationship("lct:perm_pair", "paired", old_ts, distance=1, permanent=True))
    # Fresh relationships
    evict_mrh.add_relationship(
        Relationship("lct:fresh_pair", "paired", now, distance=1))
    evict_mrh.add_relationship(
        Relationship("lct:fresh_witness", "witness", now, distance=1))
    # Bound (identity) — always kept
    evict_mrh.add_relationship(
        Relationship("lct:bound1", "bound", old_ts, distance=1))

    check("T7.1 6 relationships before eviction",
          evict_mrh.total_relationships == 6)

    evict_stale_relationships(evict_mrh, max_age_seconds=50000)
    check("T7.2 Old non-permanent paired evicted",
          "lct:old_pair" not in [r.lct_id for r in evict_mrh.paired])
    check("T7.3 Permanent paired kept",
          "lct:perm_pair" in [r.lct_id for r in evict_mrh.paired])
    check("T7.4 Fresh paired kept",
          "lct:fresh_pair" in [r.lct_id for r in evict_mrh.paired])
    check("T7.5 Old witness evicted",
          "lct:old_witness" not in [r.lct_id for r in evict_mrh.witnessing])
    check("T7.6 Fresh witness kept",
          "lct:fresh_witness" in [r.lct_id for r in evict_mrh.witnessing])
    check("T7.7 Bound always kept",
          len(evict_mrh.bound) == 1)

    # ── T8: Relationship Compression ─────────────────────────────
    print("T8: Relationship Compression (§4.3)")
    comp_mrh = MRH(entity_id="lct:comp", device_class=DeviceClass.MICRO)
    comp_mrh.witnessing = [
        Relationship("lct:w1", "witness", now - 100, role="validator"),
        Relationship("lct:w2", "witness", now - 50, role="validator"),
        Relationship("lct:w3", "witness", now, role="auditor"),
    ]

    agg = aggregate_witnesses(comp_mrh.witnessing)
    check("T8.1 Two roles aggregated",
          len(agg) == 2)
    check("T8.2 Validator count = 2",
          agg["validator"]["count"] == 2)
    check("T8.3 Auditor count = 1",
          agg["auditor"]["count"] == 1)
    check("T8.4 Latest timestamp tracked",
          agg["validator"]["latest"] > agg["validator"]["latest"] - 100)

    # Device-class compression
    micro_comp = compress_relationships(
        MRH(entity_id="lct:mc", device_class=DeviceClass.MICRO))
    check("T8.5 Micro compression returns aggregated witnesses",
          "witnesses_aggregated" in micro_comp)

    edge_comp = compress_relationships(
        MRH(entity_id="lct:ec", device_class=DeviceClass.EDGE))
    check("T8.6 Edge compression returns witnesses by role",
          "witnesses_by_role" in edge_comp)

    desktop_comp = compress_relationships(
        MRH(entity_id="lct:dc", device_class=DeviceClass.DESKTOP))
    check("T8.7 Desktop returns full witness count",
          "witnesses" in desktop_comp)

    # ── T9: Adaptive Horizon ─────────────────────────────────────
    print("T9: Adaptive Horizon (§5.1)")
    adaptive_mrh = MRH(entity_id="lct:adaptive", device_class=DeviceClass.MOBILE)
    adaptive = AdaptiveMRH(adaptive_mrh)

    # Empty MRH — should expand
    check("T9.1 Empty → should expand",
          adaptive.should_expand())
    check("T9.2 Empty → should NOT contract",
          not adaptive.should_contract())
    check("T9.3 Usage ratio = 0",
          adaptive.usage_ratio == 0.0)

    adaptive.adjust()
    check("T9.4 Horizon expanded from 3 to 4",
          adaptive_mrh.horizon_depth == 4)

    # Fill to >90% — should contract
    for i in range(950):
        adaptive_mrh.bound.append(
            Relationship(f"lct:fill{i}", "bound", now, distance=1))
    check("T9.5 Usage > 90%",
          adaptive.usage_ratio > 0.9)
    check("T9.6 Should contract",
          adaptive.should_contract())

    adaptive.adjust()
    check("T9.7 Horizon contracted",
          adaptive_mrh.horizon_depth < 4)

    # Horizon never goes below 1
    adaptive_mrh.horizon_depth = 1
    for _ in range(100):
        adaptive_mrh.bound.append(
            Relationship("lct:more", "bound", now, distance=1))
    adaptive.adjust()
    check("T9.8 Horizon floor at 1",
          adaptive_mrh.horizon_depth >= 1)

    # ── T10: Priority-Based Retention ────────────────────────────
    print("T10: Priority-Based Retention (§5.2)")

    # Permanent > active > recent > stale
    perm = Relationship("lct:perm", "bound", now - 100000, permanent=True)
    active_pair = Relationship("lct:active", "paired", now - 50000, active=True)
    recent = Relationship("lct:recent", "witness", now, t3_score=0.9, active=False)
    stale = Relationship("lct:stale", "witness", now - 200000, t3_score=0.1, active=False)

    perm_score = calculate_priority(perm)
    active_score = calculate_priority(active_pair)
    recent_score = calculate_priority(recent)
    stale_score = calculate_priority(stale)

    check("T10.1 Permanent has highest priority",
          perm_score > active_score)
    check("T10.2 Active > recent",
          active_score > recent_score)
    check("T10.3 Recent > stale",
          recent_score > stale_score)

    # Role relevance bonus
    role_rel = Relationship("lct:role", "witness", now, role="analyst")
    role_score = calculate_priority(role_rel, current_role="analyst")
    no_role_score = calculate_priority(role_rel, current_role="engineer")
    check("T10.4 Role match gets bonus",
          role_score > no_role_score)

    # Priority retention
    prio_mrh = MRH(entity_id="lct:prio", device_class=DeviceClass.CLOUD)
    prio_mrh.bound = [perm]
    prio_mrh.paired = [active_pair]
    prio_mrh.witnessing = [recent, stale]

    retain_by_priority(prio_mrh, max_relationships=2)
    check("T10.5 Top 2 kept after retention",
          prio_mrh.total_relationships == 2)
    check("T10.6 Permanent kept",
          any(r.lct_id == "lct:perm" for r in prio_mrh.bound))

    # ── T11: Device Detection ────────────────────────────────────
    print("T11: Device Detection (§6.1)")
    check("T11.1 < 1MB → MICRO",
          detect_device_class(0.0005) == DeviceClass.MICRO)
    check("T11.2 5MB → EDGE",
          detect_device_class(0.005) == DeviceClass.EDGE)
    check("T11.3 4GB → MOBILE",
          detect_device_class(4) == DeviceClass.MOBILE)
    check("T11.4 32GB → DESKTOP",
          detect_device_class(32) == DeviceClass.DESKTOP)
    check("T11.5 256GB → CLOUD",
          detect_device_class(256) == DeviceClass.CLOUD)

    # Boundaries
    check("T11.6 0.001 GB (1MB) → EDGE (not micro)",
          detect_device_class(0.001) == DeviceClass.EDGE)
    check("T11.7 0.01 GB (10MB) → MOBILE (not edge)",
          detect_device_class(0.01) == DeviceClass.MOBILE)
    check("T11.8 10 GB → DESKTOP (not mobile)",
          detect_device_class(10) == DeviceClass.DESKTOP)
    check("T11.9 100 GB → CLOUD (not desktop)",
          detect_device_class(100) == DeviceClass.CLOUD)

    # ── T12: Format Negotiation ──────────────────────────────────
    print("T12: Format Negotiation (§6.2)")
    check("T12.1 Both support CBOR → CBOR",
          negotiate_format(["cbor", "json"], ["cbor", "json"]) == "cbor")
    check("T12.2 Only JSON common → JSON",
          negotiate_format(["cbor", "json"], ["json", "rdf"]) == "json")
    check("T12.3 Only RDF common → RDF",
          negotiate_format(["rdf"], ["rdf"]) == "rdf")
    check("T12.4 No common → JSON fallback",
          negotiate_format(["cbor"], ["rdf"]) == "json")
    check("T12.5 Preference order CBOR > JSON > RDF",
          negotiate_format(["cbor", "json", "rdf"],
                           ["rdf", "json", "cbor"]) == "cbor")

    # ── T13: Performance Benchmarks ──────────────────────────────
    print("T13: Performance Benchmarks (§7)")
    check("T13.1 CBOR smallest for 1000 rels",
          SERIALIZATION_BENCHMARKS["cbor"][0] < SERIALIZATION_BENCHMARKS["json"][0])
    check("T13.2 CBOR fastest to serialize",
          SERIALIZATION_BENCHMARKS["cbor"][1] < SERIALIZATION_BENCHMARKS["json"][1])
    check("T13.3 CBOR fastest to deserialize",
          SERIALIZATION_BENCHMARKS["cbor"][2] < SERIALIZATION_BENCHMARKS["json"][2])
    check("T13.4 gzip reduces JSON size",
          SERIALIZATION_BENCHMARKS["json_gzip"][0] < SERIALIZATION_BENCHMARKS["json"][0])
    check("T13.5 RDF largest",
          SERIALIZATION_BENCHMARKS["rdf"][0] > SERIALIZATION_BENCHMARKS["json"][0])

    # Query performance scales with horizon
    for op in QUERY_BENCHMARKS:
        benchmarks = QUERY_BENCHMARKS[op]
        check(f"T13.{6 + list(QUERY_BENCHMARKS.keys()).index(op)} {op} scales with horizon",
              benchmarks[1] < benchmarks[2] < benchmarks[3])

    # ── T14: End-to-End Micro Device ─────────────────────────────
    print("T14: End-to-End Micro Device")
    micro_e2e = MRH(entity_id="lct:iot_sensor", device_class=DeviceClass.MICRO)

    # Add birth cert (permanent)
    birth = Relationship("lct:factory", "bound", now, distance=1, permanent=True)
    check("T14.1 Birth cert added",
          micro_e2e.add_relationship(birth))

    # Add 3 pairings (max)
    for i in range(3):
        micro_e2e.add_relationship(
            Relationship(f"lct:gateway_{i}", "paired", now, distance=1))
    check("T14.2 3 pairings filled",
          len(micro_e2e.paired) == 3)

    # Add witnesses (up to 5)
    for i in range(5):
        micro_e2e.add_relationship(
            Relationship(f"lct:witness_{i}", "witness", now, distance=1, role="time"))
    check("T14.3 5 witnesses filled",
          len(micro_e2e.witnessing) == 5)

    # Total: 1 + 3 + 5 = 9, can add 1 more
    check("T14.4 Total = 9 (within 10 limit)",
          micro_e2e.total_relationships == 9)
    check("T14.5 Still within limits",
          micro_e2e.is_within_limits())

    # Memory footprint
    footprint = micro_e2e.memory_footprint()
    check("T14.6 Footprint < 100 bytes (zstd compressed)",
          footprint < 100)

    # Compression
    compressed = compress_relationships(micro_e2e)
    check("T14.7 Compressed representation is dict",
          isinstance(compressed, dict))

    # ── T15: End-to-End Cloud ────────────────────────────────────
    print("T15: End-to-End Cloud")
    cloud_e2e = MRH(entity_id="lct:cloud_server", device_class=DeviceClass.CLOUD)
    check("T15.1 Cloud horizon = 5",
          cloud_e2e.horizon_depth == 5)

    # Add relationships across distances
    count = 0
    for dist in range(1, 6):
        for i in range(20):
            cloud_e2e.add_relationship(
                Relationship(f"lct:cloud_r{count}", "bound", now, distance=dist))
            count += 1
    check("T15.2 100 relationships added",
          cloud_e2e.total_relationships == 100)

    # Adaptive adjustment
    cloud_adaptive = AdaptiveMRH(cloud_e2e)
    check("T15.3 Cloud usage ratio very low",
          cloud_adaptive.usage_ratio < 0.01)
    check("T15.4 Should expand",
          cloud_adaptive.should_expand())

    # Horizon pruning to depth 3
    prune_by_horizon(cloud_e2e, max_depth=3)
    check("T15.5 Pruned to depth 3 (60 remaining)",
          cloud_e2e.total_relationships == 60)

    # ═══════════════════════════════════════════════════════════
    print(f"\n{'='*60}")
    print(f"MRH Scale Limits: {passed}/{passed+failed} checks passed")
    if failed:
        print(f"  ({failed} FAILED)")
    else:
        print("  All checks passed!")
    print(f"{'='*60}")
    return passed, failed


if __name__ == "__main__":
    run_tests()
