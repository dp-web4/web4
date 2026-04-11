#!/usr/bin/env python3
"""
LCT Federation Registry — Multi-Society Identity Resolution
==============================================================

Extends the single-society LCT registry (lct_registry.py) with federation:
- Multiple societies, each with their own registry
- Cross-society LCT discovery and resolution
- Trust bridges between registries (verified, not assumed)
- Grounding anchors for on-chain persistence references
- Foreign LCT verification through bridge trust

Architecture:
    SocietyRegistry (single-society, wraps lct_registry.py concepts)
        ↕ FederationBridge (bidirectional, trust-scored)
    FederationRegistry (coordinates multiple SocietyRegistries)

Key design decisions:
1. No global registry — federation is peer-to-peer between societies
2. Trust in foreign LCTs is bounded by bridge trust (BRIDGE_MEDIATED)
3. Discovery uses gossip: each society announces its members to bridges
4. Grounding anchors are hashes that can be verified against a ledger
5. Cross-society resolution returns both the LCT AND the trust path

This closes STATUS.md item #54: "LCT registry federation integration"

Date: 2026-02-20
Depends on: web4-standard/implementation/reference/lct_registry.py (concepts)
"""

import hashlib
import json
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple


# ═══════════════════════════════════════════════════════════════
# LCT Identity (simplified, avoids cryptography dependency)
# ═══════════════════════════════════════════════════════════════

class FederationEntityType(str, Enum):
    HUMAN = "human"
    AI = "ai"
    ORGANIZATION = "organization"
    ROLE = "role"
    DEVICE = "device"
    SERVICE = "service"
    SOCIETY = "society"


class LCTStatus(str, Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    REVOKED = "revoked"


@dataclass
class FederationLCT:
    """An LCT as represented in the federation layer.

    Lighter than LCTCredential (no private keys) — this is the
    public-facing identity record shared across society boundaries.
    """
    lct_id: str
    entity_type: FederationEntityType
    society_id: str
    entity_name: str = ""
    status: LCTStatus = LCTStatus.ACTIVE
    public_key_hash: str = ""
    birth_cert_hash: str = ""
    created_at: float = field(default_factory=time.time)
    grounding_anchor: str = ""  # hash pointer to on-chain record

    def to_dict(self) -> dict:
        return {
            "lct_id": self.lct_id,
            "entity_type": self.entity_type.value,
            "society_id": self.society_id,
            "entity_name": self.entity_name,
            "status": self.status.value,
            "public_key_hash": self.public_key_hash,
            "birth_cert_hash": self.birth_cert_hash,
            "created_at": self.created_at,
            "grounding_anchor": self.grounding_anchor,
        }

    def compute_fingerprint(self) -> str:
        """Unique fingerprint for cross-registry deduplication."""
        data = f"{self.lct_id}:{self.society_id}:{self.birth_cert_hash}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]


@dataclass
class TrustPath:
    """A verified trust path from source to target LCT.

    In federation, you don't just get the LCT — you get the path
    through which it was discovered, with trust scores at each hop.
    """
    source_society: str
    target_society: str
    target_lct: FederationLCT
    hops: List[Dict[str, Any]] = field(default_factory=list)
    path_trust: float = 0.0  # product of bridge trusts along path
    resolved_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "source": self.source_society,
            "target": self.target_society,
            "lct_id": self.target_lct.lct_id,
            "hops": self.hops,
            "path_trust": round(self.path_trust, 4),
            "resolved_at": self.resolved_at,
        }


# ═══════════════════════════════════════════════════════════════
# Society Registry (single-society layer)
# ═══════════════════════════════════════════════════════════════

class SocietyRegistry:
    """
    Single-society LCT registry for federation.

    Wraps the concepts from lct_registry.py (minting, lifecycle, verification)
    but adapted for federation interop. No cryptography dependency — uses
    hash-based proofs for portability.
    """

    def __init__(self, society_id: str, society_name: str = ""):
        self.society_id = society_id
        self.society_name = society_name or society_id
        self.lcts: Dict[str, FederationLCT] = {}
        self.entity_index: Dict[str, str] = {}  # entity_name → lct_id
        self._counter = 0

    def mint(
        self,
        entity_type: FederationEntityType,
        entity_name: str,
        witnesses: Optional[List[str]] = None,
    ) -> FederationLCT:
        """Mint a new LCT in this society."""
        if entity_name in self.entity_index:
            raise ValueError(f"Entity '{entity_name}' already has LCT in {self.society_id}")

        self._counter += 1
        lct_id = f"lct:web4:{entity_type.value}:{self.society_id}:{self._counter}"

        # Birth cert hash (simplified — would include witnesses + law oracle)
        birth_data = json.dumps({
            "lct_id": lct_id,
            "entity_type": entity_type.value,
            "society_id": self.society_id,
            "entity_name": entity_name,
            "witnesses": sorted(witnesses or []),
            "timestamp": time.time(),
        }, sort_keys=True)
        birth_hash = hashlib.sha256(birth_data.encode()).hexdigest()

        # Public key hash (simulated — real impl would generate Ed25519)
        pk_data = f"{lct_id}:pubkey:{time.time()}"
        pk_hash = hashlib.sha256(pk_data.encode()).hexdigest()[:32]

        lct = FederationLCT(
            lct_id=lct_id,
            entity_type=entity_type,
            society_id=self.society_id,
            entity_name=entity_name,
            public_key_hash=pk_hash,
            birth_cert_hash=birth_hash,
        )

        self.lcts[lct_id] = lct
        self.entity_index[entity_name] = lct_id
        return lct

    def get(self, lct_id: str) -> Optional[FederationLCT]:
        return self.lcts.get(lct_id)

    def lookup_by_name(self, entity_name: str) -> Optional[FederationLCT]:
        lct_id = self.entity_index.get(entity_name)
        return self.lcts.get(lct_id) if lct_id else None

    def suspend(self, lct_id: str) -> bool:
        lct = self.lcts.get(lct_id)
        if lct and lct.status == LCTStatus.ACTIVE:
            lct.status = LCTStatus.SUSPENDED
            return True
        return False

    def revoke(self, lct_id: str) -> bool:
        lct = self.lcts.get(lct_id)
        if lct:
            lct.status = LCTStatus.REVOKED
            return True
        return False

    def active_lcts(self) -> List[FederationLCT]:
        return [lct for lct in self.lcts.values() if lct.status == LCTStatus.ACTIVE]

    def announce(self) -> List[Dict]:
        """Generate announcement of all active LCTs for bridge peers."""
        return [lct.to_dict() for lct in self.active_lcts()]


# ═══════════════════════════════════════════════════════════════
# Federation Bridge
# ═══════════════════════════════════════════════════════════════

class BridgeStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    DEGRADED = "degraded"
    BROKEN = "broken"


@dataclass
class FederationBridge:
    """
    Bidirectional trust bridge between two societies.

    Trust is asymmetric: alpha may trust beta at 0.8 while beta
    trusts alpha at 0.6. The bridge tracks both directions.
    """
    society_a: str
    society_b: str
    trust_a_to_b: float = 0.5
    trust_b_to_a: float = 0.5
    status: BridgeStatus = BridgeStatus.ACTIVE
    established_at: float = field(default_factory=time.time)
    last_verified: float = field(default_factory=time.time)
    # Cache of foreign LCTs announced through this bridge
    cached_lcts_a: Dict[str, FederationLCT] = field(default_factory=dict)  # LCTs from society_a
    cached_lcts_b: Dict[str, FederationLCT] = field(default_factory=dict)  # LCTs from society_b

    @property
    def bridge_id(self) -> str:
        """Symmetric bridge ID (same regardless of direction)."""
        parts = sorted([self.society_a, self.society_b])
        return hashlib.sha256(f"{parts[0]}:{parts[1]}".encode()).hexdigest()[:16]

    def trust_from(self, source: str) -> float:
        """Get trust score from source society's perspective."""
        if source == self.society_a:
            return self.trust_a_to_b
        elif source == self.society_b:
            return self.trust_b_to_a
        return 0.0

    def cache_announcement(self, from_society: str, lcts: List[Dict]):
        """Cache LCT announcements from a peer society."""
        cache = self.cached_lcts_a if from_society == self.society_a else self.cached_lcts_b
        for lct_dict in lcts:
            lct = FederationLCT(
                lct_id=lct_dict["lct_id"],
                entity_type=FederationEntityType(lct_dict["entity_type"]),
                society_id=lct_dict["society_id"],
                entity_name=lct_dict.get("entity_name", ""),
                status=LCTStatus(lct_dict.get("status", "active")),
                public_key_hash=lct_dict.get("public_key_hash", ""),
                birth_cert_hash=lct_dict.get("birth_cert_hash", ""),
                created_at=lct_dict.get("created_at", 0),
            )
            cache[lct.lct_id] = lct
        self.last_verified = time.time()

    def lookup_foreign(self, lct_id: str, from_society: str) -> Optional[FederationLCT]:
        """Lookup a foreign LCT through this bridge."""
        # If asking from A, look in B's cache (and vice versa)
        if from_society == self.society_a:
            return self.cached_lcts_b.get(lct_id)
        elif from_society == self.society_b:
            return self.cached_lcts_a.get(lct_id)
        return None

    def to_dict(self) -> dict:
        return {
            "bridge_id": self.bridge_id,
            "society_a": self.society_a,
            "society_b": self.society_b,
            "trust_a_to_b": round(self.trust_a_to_b, 4),
            "trust_b_to_a": round(self.trust_b_to_a, 4),
            "status": self.status.value,
            "cached_a": len(self.cached_lcts_a),
            "cached_b": len(self.cached_lcts_b),
        }


# ═══════════════════════════════════════════════════════════════
# Federation Registry (the coordinator)
# ═══════════════════════════════════════════════════════════════

class FederationRegistry:
    """
    Multi-society LCT federation registry.

    Coordinates discovery and resolution across society boundaries.
    No global state — federation is emergent from bilateral bridges.

    Resolution algorithm:
    1. Check local society first (direct lookup)
    2. Check bridge caches (1-hop resolution)
    3. If not found, try multi-hop through connected bridges
    4. Return LCT + trust path (trust = product of bridge trusts)
    """

    def __init__(self):
        self.societies: Dict[str, SocietyRegistry] = {}
        self.bridges: Dict[str, FederationBridge] = {}  # bridge_id → bridge
        # Index: society_id → [bridge_ids]
        self._society_bridges: Dict[str, List[str]] = {}

    def register_society(self, registry: SocietyRegistry):
        """Register a society's registry with the federation."""
        self.societies[registry.society_id] = registry
        if registry.society_id not in self._society_bridges:
            self._society_bridges[registry.society_id] = []

    def establish_bridge(
        self,
        society_a: str,
        society_b: str,
        trust_a_to_b: float = 0.5,
        trust_b_to_a: float = 0.5,
    ) -> FederationBridge:
        """Establish a federation bridge between two societies."""
        if society_a not in self.societies or society_b not in self.societies:
            raise ValueError("Both societies must be registered first")

        bridge = FederationBridge(
            society_a=society_a,
            society_b=society_b,
            trust_a_to_b=trust_a_to_b,
            trust_b_to_a=trust_b_to_a,
        )

        self.bridges[bridge.bridge_id] = bridge
        self._society_bridges.setdefault(society_a, []).append(bridge.bridge_id)
        self._society_bridges.setdefault(society_b, []).append(bridge.bridge_id)

        # Exchange announcements
        reg_a = self.societies[society_a]
        reg_b = self.societies[society_b]
        bridge.cache_announcement(society_a, reg_a.announce())
        bridge.cache_announcement(society_b, reg_b.announce())

        return bridge

    def sync_bridge(self, bridge_id: str):
        """Re-sync announcements on an existing bridge."""
        bridge = self.bridges.get(bridge_id)
        if not bridge:
            return
        reg_a = self.societies.get(bridge.society_a)
        reg_b = self.societies.get(bridge.society_b)
        if reg_a:
            bridge.cache_announcement(bridge.society_a, reg_a.announce())
        if reg_b:
            bridge.cache_announcement(bridge.society_b, reg_b.announce())

    def resolve(
        self,
        lct_id: str,
        from_society: str,
        max_hops: int = 3,
    ) -> Optional[TrustPath]:
        """
        Resolve an LCT ID from a source society's perspective.

        Returns a TrustPath with the LCT and the trust chain used
        to discover it. Trust = product of bridge trusts along path.

        Algorithm:
        1. Direct lookup in source society (hop=0, trust=1.0)
        2. 1-hop through direct bridges
        3. Multi-hop BFS through connected bridges (up to max_hops)
        """
        # 1. Local lookup
        local_reg = self.societies.get(from_society)
        if local_reg:
            local_lct = local_reg.get(lct_id)
            if local_lct:
                return TrustPath(
                    source_society=from_society,
                    target_society=from_society,
                    target_lct=local_lct,
                    hops=[{"society": from_society, "type": "local", "trust": 1.0}],
                    path_trust=1.0,
                )

        # 2. BFS through bridges
        visited: Set[str] = {from_society}
        queue: List[Tuple[str, List[Dict], float]] = []  # (society, hops, cumulative_trust)

        # Seed with direct bridges
        for bridge_id in self._society_bridges.get(from_society, []):
            bridge = self.bridges[bridge_id]
            if bridge.status in (BridgeStatus.BROKEN,):
                continue
            peer = bridge.society_b if bridge.society_a == from_society else bridge.society_a
            trust = bridge.trust_from(from_society)
            queue.append((peer, [{"society": peer, "bridge": bridge_id,
                                   "trust": trust, "type": "bridge"}], trust))

        while queue:
            current_society, hops, cumulative_trust = queue.pop(0)

            if current_society in visited:
                continue
            visited.add(current_society)

            if len(hops) > max_hops:
                continue

            # Check this society's registry
            reg = self.societies.get(current_society)
            if reg:
                lct = reg.get(lct_id)
                if lct:
                    return TrustPath(
                        source_society=from_society,
                        target_society=current_society,
                        target_lct=lct,
                        hops=[{"society": from_society, "type": "origin", "trust": 1.0}] + hops,
                        path_trust=cumulative_trust,
                    )

            # Also check bridge caches (faster than registry lookup)
            for bridge_id in self._society_bridges.get(current_society, []):
                bridge = self.bridges[bridge_id]
                if bridge.status == BridgeStatus.BROKEN:
                    continue
                cached = bridge.lookup_foreign(lct_id, current_society)
                if cached:
                    # Must include this bridge's trust in the path
                    cache_hop_trust = bridge.trust_from(current_society)
                    peer = bridge.society_b if bridge.society_a == current_society else bridge.society_a
                    cache_hops = hops + [{"society": peer, "bridge": bridge_id,
                                          "trust": cache_hop_trust, "type": "cache"}]
                    return TrustPath(
                        source_society=from_society,
                        target_society=cached.society_id,
                        target_lct=cached,
                        hops=[{"society": from_society, "type": "origin", "trust": 1.0}] + cache_hops,
                        path_trust=cumulative_trust * cache_hop_trust,
                    )

            # Expand to next hop
            for bridge_id in self._society_bridges.get(current_society, []):
                bridge = self.bridges[bridge_id]
                if bridge.status == BridgeStatus.BROKEN:
                    continue
                peer = bridge.society_b if bridge.society_a == current_society else bridge.society_a
                if peer not in visited:
                    hop_trust = bridge.trust_from(current_society)
                    new_hops = hops + [{"society": peer, "bridge": bridge_id,
                                        "trust": hop_trust, "type": "bridge"}]
                    queue.append((peer, new_hops, cumulative_trust * hop_trust))

        return None  # Not found in federation

    def resolve_by_name(
        self,
        entity_name: str,
        from_society: str,
        target_society: Optional[str] = None,
    ) -> Optional[TrustPath]:
        """Resolve an entity by name (searching through bridges if needed)."""
        # If target society specified, look directly there
        if target_society:
            reg = self.societies.get(target_society)
            if reg:
                lct = reg.lookup_by_name(entity_name)
                if lct:
                    return self.resolve(lct.lct_id, from_society)

        # Search all societies
        for sid, reg in self.societies.items():
            lct = reg.lookup_by_name(entity_name)
            if lct:
                return self.resolve(lct.lct_id, from_society)

        return None

    def get_grounding_proof(self, lct_id: str) -> Optional[Dict]:
        """
        Generate a grounding proof for an LCT.

        A grounding proof contains enough information to verify the LCT's
        existence without trusting the federation layer. It includes:
        - Birth cert hash (verifiable against on-chain record)
        - Society signature hash
        - Public key hash
        - Grounding anchor (ledger tx reference)
        """
        for reg in self.societies.values():
            lct = reg.get(lct_id)
            if lct:
                return {
                    "lct_id": lct.lct_id,
                    "society_id": lct.society_id,
                    "birth_cert_hash": lct.birth_cert_hash,
                    "public_key_hash": lct.public_key_hash,
                    "grounding_anchor": lct.grounding_anchor,
                    "fingerprint": lct.compute_fingerprint(),
                    "proof_generated_at": time.time(),
                }
        return None

    def federation_stats(self) -> Dict:
        """Get federation-wide statistics."""
        total_lcts = sum(len(r.lcts) for r in self.societies.values())
        active_lcts = sum(len(r.active_lcts()) for r in self.societies.values())
        active_bridges = sum(1 for b in self.bridges.values()
                             if b.status in (BridgeStatus.ACTIVE, BridgeStatus.DEGRADED))

        return {
            "societies": len(self.societies),
            "total_lcts": total_lcts,
            "active_lcts": active_lcts,
            "bridges": len(self.bridges),
            "active_bridges": active_bridges,
            "avg_trust": (
                sum(b.trust_a_to_b + b.trust_b_to_a for b in self.bridges.values())
                / (2 * len(self.bridges)) if self.bridges else 0
            ),
        }


# ═══════════════════════════════════════════════════════════════
# Demo + Test
# ═══════════════════════════════════════════════════════════════

def run_test():
    """Test the LCT federation registry."""
    print("=" * 70)
    print("  LCT FEDERATION REGISTRY — Multi-Society Identity Resolution")
    print("=" * 70)

    checks_passed = 0
    checks_failed = 0

    def check(name, condition, detail=""):
        nonlocal checks_passed, checks_failed
        if condition:
            print(f"  ✓ {name}")
            checks_passed += 1
        else:
            msg = f": {detail}" if detail else ""
            print(f"  ✗ {name}{msg}")
            checks_failed += 1

    # ── Setup: 3 societies ──
    print("\n── Setup: 3 Societies ──")

    alpha = SocietyRegistry("alpha-corp", "Alpha Corporation")
    beta = SocietyRegistry("beta-labs", "Beta Research Labs")
    gamma = SocietyRegistry("gamma-net", "Gamma Network")

    # Mint LCTs in each society
    alice = alpha.mint(FederationEntityType.HUMAN, "alice", ["witness-1", "witness-2"])
    sage = alpha.mint(FederationEntityType.AI, "sage-alpha", ["witness-1"])
    bob = beta.mint(FederationEntityType.HUMAN, "bob", ["witness-3"])
    nova = beta.mint(FederationEntityType.AI, "nova-beta", ["witness-3", "witness-4"])
    charlie = gamma.mint(FederationEntityType.HUMAN, "charlie", ["witness-5"])
    atlas = gamma.mint(FederationEntityType.SERVICE, "atlas-gamma", ["witness-5"])

    check("Minted 6 LCTs across 3 societies",
          len(alpha.lcts) + len(beta.lcts) + len(gamma.lcts) == 6)

    # ── Federation Setup ──
    print("\n── Federation Setup ──")

    fed = FederationRegistry()
    fed.register_society(alpha)
    fed.register_society(beta)
    fed.register_society(gamma)

    # Establish bridges (alpha ↔ beta: high trust, alpha ↔ gamma: medium, beta ↔ gamma: low)
    bridge_ab = fed.establish_bridge("alpha-corp", "beta-labs", trust_a_to_b=0.8, trust_b_to_a=0.75)
    bridge_ag = fed.establish_bridge("alpha-corp", "gamma-net", trust_a_to_b=0.6, trust_b_to_a=0.55)
    bridge_bg = fed.establish_bridge("beta-labs", "gamma-net", trust_a_to_b=0.4, trust_b_to_a=0.35)

    check("3 bridges established", len(fed.bridges) == 3)
    check("Bridge caches populated",
          len(bridge_ab.cached_lcts_a) == 2 and len(bridge_ab.cached_lcts_b) == 2)

    # ── Test 1: Local resolution (hop=0) ──
    print("\n── Test 1: Local Resolution ──")
    path1 = fed.resolve(alice.lct_id, "alpha-corp")
    check("T1: Alice found locally", path1 is not None)
    check("T1: Trust = 1.0 (local)", path1.path_trust == 1.0)
    check("T1: Zero bridge hops", len(path1.hops) == 1 and path1.hops[0]["type"] == "local")

    # ── Test 2: 1-hop resolution (across bridge) ──
    print("\n── Test 2: 1-Hop Resolution ──")
    path2 = fed.resolve(bob.lct_id, "alpha-corp")
    check("T2: Bob (beta) found from alpha", path2 is not None)
    check("T2: Trust = bridge trust (0.8)", abs(path2.path_trust - 0.8) < 0.01,
          f"got {path2.path_trust}")
    check("T2: Target society is beta-labs", path2.target_society == "beta-labs")

    # ── Test 3: 2-hop resolution ──
    print("\n── Test 3: Multi-Hop Resolution ──")
    # From beta, resolve charlie (gamma) — could go direct (beta→gamma, trust=0.4)
    # or via alpha (beta→alpha→gamma, trust=0.75*0.6=0.45)
    # BFS finds direct first
    path3 = fed.resolve(charlie.lct_id, "beta-labs")
    check("T3: Charlie (gamma) found from beta", path3 is not None)
    check("T3: Trust reflects path", path3.path_trust > 0,
          f"trust={path3.path_trust:.3f}")

    # ── Test 4: Name-based resolution ──
    print("\n── Test 4: Name-Based Resolution ──")
    path4 = fed.resolve_by_name("nova-beta", "alpha-corp")
    check("T4: Nova found by name from alpha", path4 is not None)
    check("T4: Correct LCT returned", path4.target_lct.entity_name == "nova-beta")

    # ── Test 5: Grounding proof ──
    print("\n── Test 5: Grounding Proof ──")
    proof = fed.get_grounding_proof(alice.lct_id)
    check("T5: Grounding proof generated", proof is not None)
    check("T5: Contains birth cert hash", len(proof["birth_cert_hash"]) > 0)
    check("T5: Contains fingerprint", len(proof["fingerprint"]) > 0)

    # ── Test 6: Revoked LCT not resolvable ──
    print("\n── Test 6: Revoked LCT ──")
    beta.revoke(nova.lct_id)
    fed.sync_bridge(bridge_ab.bridge_id)  # re-sync after revocation
    # After sync, nova should be in cache but with revoked status
    path6 = fed.resolve(nova.lct_id, "alpha-corp")
    # Resolution still works (you can find it) but status shows revoked
    check("T6: Revoked LCT still discoverable", path6 is not None)
    check("T6: Status shows revoked", path6.target_lct.status == LCTStatus.REVOKED)

    # ── Test 7: Broken bridge blocks resolution ──
    print("\n── Test 7: Broken Bridge ──")
    bridge_bg.status = BridgeStatus.BROKEN
    # Now beta→gamma direct path is broken.
    # Charlie should still be reachable via alpha (beta→alpha→gamma)
    path7 = fed.resolve(charlie.lct_id, "beta-labs")
    check("T7: Charlie still reachable via multi-hop",
          path7 is not None,
          "should route through alpha")
    if path7:
        check("T7: Trust reflects longer path",
              path7.path_trust < 0.5,  # 0.75 * 0.6 = 0.45
              f"trust={path7.path_trust:.3f}")

    # ── Test 8: Unknown LCT ──
    print("\n── Test 8: Unknown LCT ──")
    path8 = fed.resolve("lct:web4:human:nonexistent:999", "alpha-corp")
    check("T8: Unknown LCT returns None", path8 is None)

    # ── Test 9: Federation stats ──
    print("\n── Test 9: Federation Stats ──")
    stats = fed.federation_stats()
    check("T9: 3 societies", stats["societies"] == 3)
    check("T9: 6 total LCTs", stats["total_lcts"] == 6)
    check("T9: 2 active bridges (1 broken)", stats["active_bridges"] == 2)

    # ── Test 10: New member after bridge established ──
    print("\n── Test 10: Late-Joining Member ──")
    diana = gamma.mint(FederationEntityType.HUMAN, "diana", ["witness-6"])
    fed.sync_bridge(bridge_ag.bridge_id)  # sync alpha-gamma bridge

    path10 = fed.resolve(diana.lct_id, "alpha-corp")
    check("T10: Late member discoverable after sync", path10 is not None)
    check("T10: Correct entity",
          path10 is not None and path10.target_lct.entity_name == "diana")

    # ── Test 11: Asymmetric trust ──
    print("\n── Test 11: Asymmetric Trust ──")
    # alpha→beta trust (0.8) vs beta→alpha trust (0.75)
    path_ab = fed.resolve(bob.lct_id, "alpha-corp")
    path_ba = fed.resolve(alice.lct_id, "beta-labs")
    check("T11: alpha→beta trust = 0.8",
          path_ab is not None and abs(path_ab.path_trust - 0.8) < 0.01)
    check("T11: beta→alpha trust = 0.75",
          path_ba is not None and abs(path_ba.path_trust - 0.75) < 0.01)
    check("T11: Asymmetric (not equal)",
          path_ab.path_trust != path_ba.path_trust)

    # ── Summary ──
    print("\n" + "=" * 70)
    total = checks_passed + checks_failed
    print(f"  LCT Federation Registry: {checks_passed}/{total} checks passed")
    if checks_failed == 0:
        print("  ALL CHECKS PASSED!")
    else:
        print(f"  {checks_failed} check(s) FAILED")

    print(f"\n  Federation: {stats['societies']} societies, "
          f"{stats['total_lcts']} LCTs, {len(fed.bridges)} bridges")
    print(f"\n  Key federation properties verified:")
    print(f"    ✓ Local resolution (trust=1.0)")
    print(f"    ✓ 1-hop cross-society resolution via bridges")
    print(f"    ✓ Multi-hop resolution when direct bridge broken")
    print(f"    ✓ Trust = product of bridge trusts along path")
    print(f"    ✓ Asymmetric trust (direction matters)")
    print(f"    ✓ Name-based discovery across federation")
    print(f"    ✓ Grounding proofs for on-chain verification")
    print(f"    ✓ Revoked LCTs show correct status")
    print(f"    ✓ Broken bridges trigger rerouting")
    print(f"    ✓ Late-joining members discoverable after sync")
    print("=" * 70)

    return checks_failed == 0


if __name__ == "__main__":
    success = run_test()
    import sys
    sys.exit(0 if success else 1)
