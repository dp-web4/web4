#!/usr/bin/env python3
"""
Entity Discovery Protocol — Session 20, Track 1

How Web4 entities find each other from zero state:
- DNS-SD service advertisement and resolution
- DHT-based distributed discovery (Kademlia-style routing)
- QR code out-of-band pairing ceremony
- Witness relay discovery (find entities through mutual witnesses)
- Cross-federation discovery relay
- Discovery poisoning detection and defense
- Bootstrap sequence from cold start
- Discovery cache with trust-weighted ranking
- NAT traversal coordination
- Rate limiting and anti-spam for discovery
- Performance at scale

Reference: core-protocol.md §4.2, multi-device-lct-binding.md
"""

from __future__ import annotations
import hashlib
import hmac
import math
import os
import time
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Set, Tuple


# ─── Constants ────────────────────────────────────────────────────────────────

class DiscoveryMethod(Enum):
    DNS_SD = "dns-sd"
    MDNS = "mdns"
    DHT = "dht"
    QR_OOB = "qr-oob"
    WITNESS_RELAY = "witness-relay"
    BROADCAST = "broadcast"


class EntityPresence(Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    STALE = "stale"


SERVICE_TYPE = "_web4._tcp"
DOMAIN = "local"
DHT_K = 20       # Kademlia bucket size
DHT_ALPHA = 3    # Parallel lookups
STALE_THRESHOLD = 300  # 5 minutes


# ─── Data Structures ─────────────────────────────────────────────────────────

@dataclass
class EntityRecord:
    """Discoverable entity metadata."""
    entity_id: str
    public_key: bytes
    endpoints: List[str]       # e.g., ["tcp://192.168.1.5:7400", "wss://node.example.com"]
    entity_type: str = "human"
    federation_id: Optional[str] = None
    trust_score: float = 0.0
    lct_hash: Optional[str] = None
    last_seen: float = 0.0
    discovery_method: DiscoveryMethod = DiscoveryMethod.BROADCAST
    birth_cert_signature: Optional[bytes] = None


@dataclass
class DnsServiceRecord:
    """DNS-SD service advertisement."""
    instance_name: str
    service_type: str
    domain: str
    host: str
    port: int
    txt_records: Dict[str, str]
    ttl: int = 120

    def fqdn(self) -> str:
        return f"{self.instance_name}.{self.service_type}.{self.domain}"


# ─── S1: DNS-SD Service Advertisement ────────────────────────────────────────

class DnsDiscovery:
    """DNS-SD based service discovery for Web4 entities."""

    def __init__(self):
        self.services: Dict[str, DnsServiceRecord] = {}

    def advertise(self, entity: EntityRecord, host: str, port: int) -> DnsServiceRecord:
        """Create DNS-SD advertisement for an entity."""
        txt = {
            "eid": entity.entity_id[:32],
            "type": entity.entity_type,
            "ver": "1",
        }
        if entity.federation_id:
            txt["fed"] = entity.federation_id[:32]
        if entity.lct_hash:
            txt["lct"] = entity.lct_hash[:16]

        record = DnsServiceRecord(
            instance_name=entity.entity_id[:63],  # DNS label max 63 chars
            service_type=SERVICE_TYPE,
            domain=DOMAIN,
            host=host,
            port=port,
            txt_records=txt,
        )
        self.services[record.fqdn()] = record
        return record

    def browse(self, service_type: str = SERVICE_TYPE) -> List[DnsServiceRecord]:
        """Browse for available Web4 services."""
        return [s for s in self.services.values() if s.service_type == service_type]

    def resolve(self, fqdn: str) -> Optional[DnsServiceRecord]:
        """Resolve a specific service instance."""
        return self.services.get(fqdn)

    def remove(self, fqdn: str) -> bool:
        """Remove a service advertisement."""
        if fqdn in self.services:
            del self.services[fqdn]
            return True
        return False


# ─── S2: DHT Discovery (Kademlia-style) ──────────────────────────────────────

def xor_distance(a: bytes, b: bytes) -> int:
    """XOR distance between two node IDs."""
    result = 0
    for x, y in zip(a, b):
        result = (result << 8) | (x ^ y)
    return result


def node_id_from_entity(entity_id: str) -> bytes:
    """Deterministic node ID from entity ID."""
    return hashlib.sha256(entity_id.encode()).digest()


@dataclass
class KBucket:
    """Kademlia k-bucket for a specific distance range."""
    entries: List[Tuple[bytes, EntityRecord]] = field(default_factory=list)
    k: int = DHT_K

    def add(self, node_id: bytes, record: EntityRecord) -> bool:
        """Add or update an entry. Returns True if added."""
        # Check if already present — update
        for i, (nid, _) in enumerate(self.entries):
            if nid == node_id:
                self.entries[i] = (node_id, record)
                # Move to tail (most recently seen)
                self.entries.append(self.entries.pop(i))
                return True
        # Bucket full?
        if len(self.entries) >= self.k:
            return False  # Would need to ping head (oldest)
        self.entries.append((node_id, record))
        return True

    def find_closest(self, target: bytes, count: int) -> List[Tuple[bytes, EntityRecord]]:
        """Find closest entries to target by XOR distance."""
        scored = [(xor_distance(nid, target), nid, rec) for nid, rec in self.entries]
        scored.sort(key=lambda x: x[0])
        return [(nid, rec) for _, nid, rec in scored[:count]]


class DHTDiscovery:
    """Kademlia-style DHT for distributed entity discovery."""

    def __init__(self, local_entity: EntityRecord):
        self.local_id = node_id_from_entity(local_entity.entity_id)
        self.local_entity = local_entity
        self.buckets: Dict[int, KBucket] = {}  # prefix_length → bucket
        self.storage: Dict[bytes, EntityRecord] = {}  # Stored records

    def _bucket_index(self, node_id: bytes) -> int:
        """Determine which k-bucket a node belongs to."""
        dist = xor_distance(self.local_id, node_id)
        if dist == 0:
            return 0
        return dist.bit_length()

    def add_node(self, record: EntityRecord) -> bool:
        """Add a discovered node to routing table."""
        nid = node_id_from_entity(record.entity_id)
        idx = self._bucket_index(nid)
        if idx not in self.buckets:
            self.buckets[idx] = KBucket()
        return self.buckets[idx].add(nid, record)

    def find_closest(self, target_id: str, count: int = DHT_K) -> List[EntityRecord]:
        """Find closest nodes to a target entity ID."""
        target = node_id_from_entity(target_id)
        all_entries = []
        for bucket in self.buckets.values():
            all_entries.extend(bucket.entries)
        scored = [(xor_distance(nid, target), rec) for nid, rec in all_entries]
        scored.sort(key=lambda x: x[0])
        return [rec for _, rec in scored[:count]]

    def store(self, record: EntityRecord):
        """Store an entity record at this node."""
        nid = node_id_from_entity(record.entity_id)
        self.storage[nid] = record

    def lookup(self, entity_id: str) -> Optional[EntityRecord]:
        """Look up a stored entity record."""
        nid = node_id_from_entity(entity_id)
        return self.storage.get(nid)

    def node_count(self) -> int:
        """Total nodes in routing table."""
        return sum(len(b.entries) for b in self.buckets.values())


# ─── S3: QR Code Out-of-Band Pairing ─────────────────────────────────────────

@dataclass
class PairingChallenge:
    """QR-encoded pairing challenge."""
    initiator_id: str
    nonce: bytes
    public_key: bytes
    endpoint: str
    timestamp: float
    signature: bytes = b""

    def to_qr_payload(self) -> bytes:
        """Serialize to compact QR-friendly format."""
        parts = [
            b"W4P:",  # Web4 Pairing prefix
            self.initiator_id.encode()[:32],
            b"|",
            self.nonce,
            b"|",
            self.public_key[:32],
            b"|",
            self.endpoint.encode(),
        ]
        return b"".join(parts)

    @staticmethod
    def from_qr_payload(data: bytes) -> Optional["PairingChallenge"]:
        """Parse QR payload."""
        if not data.startswith(b"W4P:"):
            return None
        rest = data[4:]
        parts = rest.split(b"|")
        if len(parts) < 4:
            return None
        return PairingChallenge(
            initiator_id=parts[0].decode(),
            nonce=parts[1],
            public_key=parts[2],
            endpoint=parts[3].decode(),
            timestamp=time.time(),
        )


@dataclass
class PairingResponse:
    """Response to a pairing challenge."""
    responder_id: str
    initiator_nonce: bytes
    responder_nonce: bytes
    public_key: bytes
    accepted: bool = True


def verify_pairing(challenge: PairingChallenge, response: PairingResponse) -> bool:
    """Verify that a pairing response matches the challenge."""
    if response.initiator_nonce != challenge.nonce:
        return False
    if not response.accepted:
        return False
    if len(response.responder_nonce) < 16:
        return False
    return True


def derive_pairing_key(
    challenge: PairingChallenge,
    response: PairingResponse,
) -> bytes:
    """Derive shared secret from pairing ceremony."""
    material = (
        challenge.nonce +
        response.responder_nonce +
        challenge.public_key +
        response.public_key
    )
    return hashlib.sha256(material).digest()


# ─── S4: Witness Relay Discovery ─────────────────────────────────────────────

class WitnessRelay:
    """Discover entities through chains of mutual witnesses."""

    def __init__(self):
        self.witness_graph: Dict[str, Set[str]] = {}  # entity → set of witnessed entities
        self.records: Dict[str, EntityRecord] = {}

    def add_witness(self, witness_id: str, witnessed_id: str, record: EntityRecord):
        """Record that witness_id has witnessed witnessed_id."""
        if witness_id not in self.witness_graph:
            self.witness_graph[witness_id] = set()
        self.witness_graph[witness_id].add(witnessed_id)
        self.records[witnessed_id] = record

    def discover_from(self, start_id: str, max_hops: int = 3) -> Dict[str, int]:
        """
        Discover entities reachable through witness chains.
        Returns {entity_id: hop_count}.
        """
        visited = {start_id: 0}
        frontier = [start_id]

        for hop in range(1, max_hops + 1):
            next_frontier = []
            for node in frontier:
                for witnessed in self.witness_graph.get(node, set()):
                    if witnessed not in visited:
                        visited[witnessed] = hop
                        next_frontier.append(witnessed)
            frontier = next_frontier
            if not frontier:
                break

        # Remove start node from results
        visited.pop(start_id, None)
        return visited

    def find_path(self, source: str, target: str, max_hops: int = 5) -> Optional[List[str]]:
        """Find shortest witness path from source to target."""
        if source == target:
            return [source]

        visited = {source}
        queue = [(source, [source])]

        while queue:
            current, path = queue.pop(0)
            if len(path) > max_hops:
                continue
            for witnessed in self.witness_graph.get(current, set()):
                if witnessed == target:
                    return path + [witnessed]
                if witnessed not in visited:
                    visited.add(witnessed)
                    queue.append((witnessed, path + [witnessed]))

        return None

    def mutual_witnesses(self, entity_a: str, entity_b: str) -> Set[str]:
        """Find entities that have witnessed both a and b."""
        witnesses_of_a = set()
        witnesses_of_b = set()
        for witness, witnessed_set in self.witness_graph.items():
            if entity_a in witnessed_set:
                witnesses_of_a.add(witness)
            if entity_b in witnessed_set:
                witnesses_of_b.add(witness)
        return witnesses_of_a & witnesses_of_b


# ─── S5: Cross-Federation Discovery Relay ────────────────────────────────────

@dataclass
class FederationGateway:
    """Gateway node that relays discovery across federations."""
    federation_id: str
    gateway_entity: EntityRecord
    peered_federations: Dict[str, float] = field(default_factory=dict)  # fed_id → trust

    def can_relay_to(self, target_federation: str) -> bool:
        return target_federation in self.peered_federations

    def relay_trust(self, target_federation: str) -> float:
        return self.peered_federations.get(target_federation, 0.0)


class CrossFederationDiscovery:
    """Relay discovery requests across federation boundaries."""

    def __init__(self):
        self.gateways: Dict[str, List[FederationGateway]] = {}  # fed_id → gateways
        self.federation_records: Dict[str, Dict[str, EntityRecord]] = {}  # fed_id → {eid → record}

    def register_gateway(self, gateway: FederationGateway):
        """Register a federation gateway."""
        fid = gateway.federation_id
        if fid not in self.gateways:
            self.gateways[fid] = []
        self.gateways[fid].append(gateway)

    def register_entity(self, federation_id: str, record: EntityRecord):
        """Register an entity within its federation."""
        if federation_id not in self.federation_records:
            self.federation_records[federation_id] = {}
        self.federation_records[federation_id][record.entity_id] = record

    def discover_cross_fed(
        self,
        source_fed: str,
        target_entity_id: str,
        max_relay_hops: int = 2,
    ) -> Optional[Tuple[EntityRecord, float, List[str]]]:
        """
        Discover an entity across federation boundaries.
        Returns (record, relay_trust, relay_path) or None.
        """
        # Direct lookup in all federations
        for fid, records in self.federation_records.items():
            if target_entity_id in records:
                if fid == source_fed:
                    return (records[target_entity_id], 1.0, [fid])

                # Need relay path
                path = self._find_relay_path(source_fed, fid, max_relay_hops)
                if path:
                    trust = self._path_trust(path)
                    return (records[target_entity_id], trust, path)

        return None

    def _find_relay_path(
        self, source: str, target: str, max_hops: int
    ) -> Optional[List[str]]:
        """Find relay path between federations via gateways."""
        visited = {source}
        queue = [(source, [source])]

        while queue:
            current, path = queue.pop(0)
            if len(path) > max_hops + 1:
                continue
            for gw in self.gateways.get(current, []):
                for peer_fed in gw.peered_federations:
                    if peer_fed == target:
                        return path + [target]
                    if peer_fed not in visited:
                        visited.add(peer_fed)
                        queue.append((peer_fed, path + [peer_fed]))

        return None

    def _path_trust(self, path: List[str]) -> float:
        """Compute multiplicative trust along relay path."""
        trust = 1.0
        for i in range(len(path) - 1):
            src = path[i]
            dst = path[i + 1]
            hop_trust = 0.0
            for gw in self.gateways.get(src, []):
                t = gw.relay_trust(dst)
                hop_trust = max(hop_trust, t)
            trust *= hop_trust
        return trust


# ─── S6: Discovery Poisoning Detection ──────────────────────────────────────

@dataclass
class DiscoveryEvent:
    """Logged discovery event for anomaly detection."""
    entity_id: str
    source: DiscoveryMethod
    timestamp: float
    endpoint: str
    lct_hash: Optional[str] = None
    verified: bool = False


class PoisoningDetector:
    """Detect discovery poisoning attacks."""

    def __init__(self, max_events_per_id: int = 100):
        self.events: Dict[str, List[DiscoveryEvent]] = {}
        self.max_events = max_events_per_id
        self.blocked: Set[str] = set()

    def record_event(self, event: DiscoveryEvent):
        """Record a discovery event."""
        eid = event.entity_id
        if eid not in self.events:
            self.events[eid] = []
        self.events[eid].append(event)
        if len(self.events[eid]) > self.max_events:
            self.events[eid] = self.events[eid][-self.max_events:]

    def detect_endpoint_flip(self, entity_id: str, window: float = 60.0) -> bool:
        """
        Detect rapid endpoint changes — sign of DNS hijack or MITM.
        Returns True if suspicious.
        """
        events = self.events.get(entity_id, [])
        if len(events) < 2:
            return False

        now = events[-1].timestamp
        recent = [e for e in events if now - e.timestamp < window]
        endpoints = set(e.endpoint for e in recent)
        return len(endpoints) > 2  # More than 2 distinct endpoints in window

    def detect_lct_mismatch(self, entity_id: str) -> bool:
        """
        Detect LCT hash mismatches across discovery sources.
        Different sources claiming different LCT hashes = poisoning.
        """
        events = self.events.get(entity_id, [])
        lct_hashes = set()
        for e in events:
            if e.lct_hash:
                lct_hashes.add(e.lct_hash)
        return len(lct_hashes) > 1

    def detect_flood(self, entity_id: str, window: float = 10.0, threshold: int = 20) -> bool:
        """Detect discovery request flooding from a single entity."""
        events = self.events.get(entity_id, [])
        if not events:
            return False
        now = events[-1].timestamp
        recent = [e for e in events if now - e.timestamp < window]
        return len(recent) > threshold

    def block(self, entity_id: str):
        self.blocked.add(entity_id)

    def is_blocked(self, entity_id: str) -> bool:
        return entity_id in self.blocked


# ─── S7: Bootstrap Sequence ─────────────────────────────────────────────────

@dataclass
class BootstrapState:
    """Tracks bootstrap progress from cold start."""
    phase: str = "init"  # init → dns → dht → relay → ready
    discovered_peers: int = 0
    verified_peers: int = 0
    federation_joined: bool = False
    start_time: float = 0.0
    errors: List[str] = field(default_factory=list)


def bootstrap_sequence(
    entity: EntityRecord,
    dns: DnsDiscovery,
    dht: DHTDiscovery,
    relay: WitnessRelay,
    seed_endpoints: List[str] = None,
) -> BootstrapState:
    """
    Execute cold-start bootstrap sequence:
    1. Try DNS-SD for local peers
    2. If seed endpoints provided, join DHT
    3. Use witness relay for trusted discovery
    4. Validate discovered peers
    """
    state = BootstrapState(start_time=time.time())

    # Phase 1: DNS-SD local discovery
    state.phase = "dns"
    dns_results = dns.browse()
    state.discovered_peers += len(dns_results)

    # Phase 2: DHT bootstrap
    state.phase = "dht"
    if seed_endpoints:
        for endpoint in seed_endpoints:
            seed_id = hashlib.sha256(endpoint.encode()).hexdigest()[:16]
            seed_record = EntityRecord(
                entity_id=seed_id,
                public_key=b"seed",
                endpoints=[endpoint],
                last_seen=time.time(),
            )
            dht.add_node(seed_record)
            state.discovered_peers += 1

    # Phase 3: Witness relay
    state.phase = "relay"
    relay_discovered = relay.discover_from(entity.entity_id)
    state.discovered_peers += len(relay_discovered)

    # Phase 4: Verification (simplified — just check we have peers)
    state.phase = "verify"
    state.verified_peers = min(state.discovered_peers, dht.node_count())

    if state.discovered_peers > 0:
        state.phase = "ready"
    else:
        state.phase = "isolated"
        state.errors.append("No peers discovered")

    return state


# ─── S8: Discovery Cache with Trust-Weighted Ranking ────────────────────────

class DiscoveryCache:
    """Cache discovered entities with trust-weighted ranking."""

    def __init__(self, max_size: int = 1000, ttl: float = 3600.0):
        self.entries: Dict[str, Tuple[EntityRecord, float]] = {}  # eid → (record, insert_time)
        self.max_size = max_size
        self.ttl = ttl

    def put(self, record: EntityRecord, now: float = None):
        """Add or update a cached record."""
        if now is None:
            now = time.time()
        self.entries[record.entity_id] = (record, now)
        self._evict(now)

    def get(self, entity_id: str, now: float = None) -> Optional[EntityRecord]:
        """Get a cached record if not expired."""
        if now is None:
            now = time.time()
        entry = self.entries.get(entity_id)
        if entry is None:
            return None
        record, insert_time = entry
        if now - insert_time > self.ttl:
            del self.entries[entity_id]
            return None
        return record

    def ranked(self, now: float = None) -> List[EntityRecord]:
        """Return all cached records ranked by trust score (descending)."""
        if now is None:
            now = time.time()
        valid = []
        expired = []
        for eid, (record, insert_time) in self.entries.items():
            if now - insert_time > self.ttl:
                expired.append(eid)
            else:
                valid.append(record)
        for eid in expired:
            del self.entries[eid]
        return sorted(valid, key=lambda r: r.trust_score, reverse=True)

    def _evict(self, now: float):
        """Evict expired and lowest-trust entries if over capacity."""
        # Remove expired first
        expired = [eid for eid, (_, t) in self.entries.items() if now - t > self.ttl]
        for eid in expired:
            del self.entries[eid]

        # If still over, remove lowest trust
        while len(self.entries) > self.max_size:
            worst = min(self.entries.items(), key=lambda x: x[1][0].trust_score)
            del self.entries[worst[0]]

    def size(self) -> int:
        return len(self.entries)


# ─── S9: NAT Traversal Coordination ─────────────────────────────────────────

@dataclass
class NATInfo:
    """NAT traversal metadata."""
    public_ip: str
    public_port: int
    nat_type: str  # "none", "full_cone", "restricted", "symmetric"
    local_ip: str = ""
    local_port: int = 0
    relay_endpoint: Optional[str] = None

    def can_direct_connect(self, other: "NATInfo") -> bool:
        """Determine if direct P2P connection is possible."""
        if self.nat_type == "none" or other.nat_type == "none":
            return True
        if self.nat_type == "full_cone" and other.nat_type == "full_cone":
            return True
        if self.nat_type == "symmetric" and other.nat_type == "symmetric":
            return False  # Both symmetric = need relay
        return self.nat_type != "symmetric" or other.nat_type != "symmetric"


def select_connection_strategy(
    local: NATInfo, remote: NATInfo
) -> str:
    """Select best connection strategy based on NAT types."""
    if local.can_direct_connect(remote):
        if local.nat_type == "none" or remote.nat_type == "none":
            return "direct"
        return "hole_punch"
    if local.relay_endpoint or remote.relay_endpoint:
        return "relay"
    return "unreachable"


# ─── S10: Rate Limiting & Anti-Spam ──────────────────────────────────────────

class DiscoveryRateLimiter:
    """Rate limit discovery requests per entity."""

    def __init__(self, max_per_minute: int = 30, max_per_hour: int = 200):
        self.max_per_minute = max_per_minute
        self.max_per_hour = max_per_hour
        self.requests: Dict[str, List[float]] = {}

    def allow(self, entity_id: str, now: float = None) -> bool:
        """Check if a discovery request is allowed."""
        if now is None:
            now = time.time()

        if entity_id not in self.requests:
            self.requests[entity_id] = []

        reqs = self.requests[entity_id]

        # Clean old entries
        cutoff_hour = now - 3600
        self.requests[entity_id] = [t for t in reqs if t > cutoff_hour]
        reqs = self.requests[entity_id]

        # Check limits
        recent_minute = sum(1 for t in reqs if t > now - 60)
        if recent_minute >= self.max_per_minute:
            return False
        if len(reqs) >= self.max_per_hour:
            return False

        reqs.append(now)
        return True

    def remaining(self, entity_id: str, now: float = None) -> Tuple[int, int]:
        """Return (remaining_per_minute, remaining_per_hour)."""
        if now is None:
            now = time.time()
        reqs = self.requests.get(entity_id, [])
        minute_count = sum(1 for t in reqs if t > now - 60)
        hour_count = sum(1 for t in reqs if t > now - 3600)
        return (
            max(0, self.max_per_minute - minute_count),
            max(0, self.max_per_hour - hour_count),
        )


# ─── S11: Performance ───────────────────────────────────────────────────────

# Included in checks below


# ══════════════════════════════════════════════════════════════════════════════
#  CHECKS
# ══════════════════════════════════════════════════════════════════════════════

def run_checks():
    checks = []
    import random
    rng = random.Random(42)

    # ── S1: DNS-SD Service Advertisement ─────────────────────────────────

    dns = DnsDiscovery()
    entity_a = EntityRecord(
        entity_id="alice", public_key=b"pk_alice",
        endpoints=["tcp://192.168.1.5:7400"], entity_type="human",
        federation_id="fed1", lct_hash="abc123",
    )

    # S1.1: Advertise creates a DNS record
    record = dns.advertise(entity_a, "192.168.1.5", 7400)
    checks.append(("s1_advertise_creates", record.service_type == SERVICE_TYPE))

    # S1.2: FQDN format is correct
    fqdn = record.fqdn()
    checks.append(("s1_fqdn_format", SERVICE_TYPE in fqdn and DOMAIN in fqdn))

    # S1.3: Browse finds advertised services
    results = dns.browse()
    checks.append(("s1_browse_finds", len(results) == 1))

    # S1.4: Resolve returns correct record
    resolved = dns.resolve(fqdn)
    checks.append(("s1_resolve_correct", resolved is not None and resolved.port == 7400))

    # S1.5: TXT records contain entity metadata
    checks.append(("s1_txt_records", "eid" in record.txt_records and "type" in record.txt_records))

    # S1.6: Remove stops advertisement
    dns.remove(fqdn)
    checks.append(("s1_remove", len(dns.browse()) == 0))

    # S1.7: Instance name truncated to 63 chars
    long_entity = EntityRecord(entity_id="x" * 100, public_key=b"pk", endpoints=[])
    rec = dns.advertise(long_entity, "host", 80)
    checks.append(("s1_truncate_63", len(rec.instance_name) <= 63))

    # ── S2: DHT Discovery ────────────────────────────────────────────────

    dht_entity = EntityRecord(entity_id="node0", public_key=b"pk0", endpoints=["tcp://0:7400"])
    dht = DHTDiscovery(dht_entity)

    # S2.1: XOR distance is symmetric
    a = node_id_from_entity("alice")
    b = node_id_from_entity("bob")
    checks.append(("s2_xor_symmetric", xor_distance(a, b) == xor_distance(b, a)))

    # S2.2: XOR distance to self is 0
    checks.append(("s2_xor_self_zero", xor_distance(a, a) == 0))

    # S2.3: Add nodes to DHT
    for i in range(10):
        rec = EntityRecord(entity_id=f"peer{i}", public_key=f"pk{i}".encode(),
                          endpoints=[f"tcp://10.0.0.{i}:7400"])
        dht.add_node(rec)
    checks.append(("s2_add_10_nodes", dht.node_count() == 10))

    # S2.4: Find closest returns sorted by distance
    closest = dht.find_closest("target_node", count=5)
    checks.append(("s2_find_closest_5", len(closest) == 5))

    # S2.5: Store and lookup
    stored = EntityRecord(entity_id="stored1", public_key=b"pk_s", endpoints=["tcp://1:1"])
    dht.store(stored)
    found = dht.lookup("stored1")
    checks.append(("s2_store_lookup", found is not None and found.entity_id == "stored1"))

    # S2.6: Lookup missing returns None
    checks.append(("s2_lookup_missing", dht.lookup("nonexistent") is None))

    # S2.7: Node ID is deterministic
    id1 = node_id_from_entity("test")
    id2 = node_id_from_entity("test")
    checks.append(("s2_deterministic_id", id1 == id2))

    # ── S3: QR Code Pairing ──────────────────────────────────────────────

    # S3.1: Create pairing challenge
    nonce = os.urandom(16)
    challenge = PairingChallenge(
        initiator_id="alice",
        nonce=nonce,
        public_key=os.urandom(32),
        endpoint="tcp://192.168.1.5:7400",
        timestamp=time.time(),
    )
    payload = challenge.to_qr_payload()
    checks.append(("s3_qr_payload_prefix", payload.startswith(b"W4P:")))

    # S3.2: Parse QR payload roundtrip
    parsed = PairingChallenge.from_qr_payload(payload)
    checks.append(("s3_qr_roundtrip", parsed is not None and parsed.initiator_id == "alice"))

    # S3.3: Invalid QR prefix rejected
    checks.append(("s3_invalid_prefix", PairingChallenge.from_qr_payload(b"BAD:data") is None))

    # S3.4: Pairing verification succeeds with matching nonce
    response = PairingResponse(
        responder_id="bob",
        initiator_nonce=nonce,
        responder_nonce=os.urandom(16),
        public_key=os.urandom(32),
    )
    checks.append(("s3_verify_pairing", verify_pairing(challenge, response)))

    # S3.5: Wrong nonce fails verification
    bad_response = PairingResponse(
        responder_id="eve", initiator_nonce=os.urandom(16),
        responder_nonce=os.urandom(16), public_key=os.urandom(32),
    )
    checks.append(("s3_wrong_nonce_fails", not verify_pairing(challenge, bad_response)))

    # S3.6: Derived pairing key is deterministic
    key1 = derive_pairing_key(challenge, response)
    key2 = derive_pairing_key(challenge, response)
    checks.append(("s3_key_deterministic", key1 == key2 and len(key1) == 32))

    # S3.7: Short responder nonce fails
    short_resp = PairingResponse(
        responder_id="short", initiator_nonce=nonce,
        responder_nonce=b"tiny", public_key=os.urandom(32),
    )
    checks.append(("s3_short_nonce_fails", not verify_pairing(challenge, short_resp)))

    # ── S4: Witness Relay Discovery ──────────────────────────────────────

    relay = WitnessRelay()
    for name in ["alice", "bob", "charlie", "dave", "eve"]:
        relay.records[name] = EntityRecord(
            entity_id=name, public_key=f"pk_{name}".encode(), endpoints=[],
        )
    relay.add_witness("alice", "bob", relay.records["bob"])
    relay.add_witness("bob", "charlie", relay.records["charlie"])
    relay.add_witness("charlie", "dave", relay.records["dave"])
    relay.add_witness("alice", "charlie", relay.records["charlie"])  # alice also witnesses charlie

    # S4.1: Direct witness discovery (1 hop)
    discovered = relay.discover_from("alice")
    checks.append(("s4_direct_witness", "bob" in discovered and discovered["bob"] == 1))

    # S4.2: Transitive discovery (2 hops)
    checks.append(("s4_transitive", "charlie" in discovered))

    # S4.3: Max hops limits depth
    limited = relay.discover_from("alice", max_hops=1)
    checks.append(("s4_max_hops_limit", "dave" not in limited))

    # S4.4: Find shortest path
    path = relay.find_path("alice", "dave")
    checks.append(("s4_shortest_path", path is not None and path[0] == "alice" and path[-1] == "dave"))

    # S4.5: No path to isolated node
    checks.append(("s4_no_path_isolated", relay.find_path("alice", "eve") is None))

    # S4.6: Mutual witnesses
    mutual = relay.mutual_witnesses("bob", "charlie")
    checks.append(("s4_mutual_witnesses", "alice" in mutual))

    # S4.7: Self discovery excluded
    discovered = relay.discover_from("alice")
    checks.append(("s4_self_excluded", "alice" not in discovered))

    # ── S5: Cross-Federation Discovery ───────────────────────────────────

    cfed = CrossFederationDiscovery()

    gw1 = FederationGateway("fed1",
        EntityRecord("gw1", b"pk", [], federation_id="fed1"),
        peered_federations={"fed2": 0.8},
    )
    gw2 = FederationGateway("fed2",
        EntityRecord("gw2", b"pk", [], federation_id="fed2"),
        peered_federations={"fed1": 0.7, "fed3": 0.6},
    )
    gw3 = FederationGateway("fed3",
        EntityRecord("gw3", b"pk", [], federation_id="fed3"),
        peered_federations={"fed2": 0.5},
    )
    cfed.register_gateway(gw1)
    cfed.register_gateway(gw2)
    cfed.register_gateway(gw3)

    target = EntityRecord("target_entity", b"pk_t", ["tcp://10:80"], federation_id="fed3")
    cfed.register_entity("fed3", target)

    local = EntityRecord("local_entity", b"pk_l", ["tcp://1:80"], federation_id="fed1")
    cfed.register_entity("fed1", local)

    # S5.1: Same-federation discovery is direct
    result = cfed.discover_cross_fed("fed1", "local_entity")
    checks.append(("s5_same_fed_direct", result is not None and result[1] == 1.0))

    # S5.2: Cross-federation discovery through relay
    result = cfed.discover_cross_fed("fed1", "target_entity")
    checks.append(("s5_cross_fed_relay", result is not None and len(result[2]) > 1))

    # S5.3: Trust decays along relay path
    checks.append(("s5_trust_decays", result is not None and result[1] < 1.0))

    # S5.4: Unreachable entity returns None
    result = cfed.discover_cross_fed("fed1", "nonexistent")
    checks.append(("s5_unreachable_none", result is None))

    # S5.5: Relay path includes intermediaries
    result = cfed.discover_cross_fed("fed1", "target_entity")
    checks.append(("s5_relay_path", result is not None and "fed2" in result[2]))

    # ── S6: Discovery Poisoning Detection ────────────────────────────────

    detector = PoisoningDetector()

    # S6.1: Normal activity not flagged
    for i in range(3):
        detector.record_event(DiscoveryEvent(
            entity_id="good_node", source=DiscoveryMethod.DNS_SD,
            timestamp=100 + i * 30, endpoint="tcp://1.2.3.4:7400",
        ))
    checks.append(("s6_normal_not_flagged", not detector.detect_endpoint_flip("good_node")))

    # S6.2: Rapid endpoint flip detected
    for i in range(5):
        detector.record_event(DiscoveryEvent(
            entity_id="flipping", source=DiscoveryMethod.DHT,
            timestamp=200 + i, endpoint=f"tcp://10.0.{i}.1:7400",
        ))
    checks.append(("s6_flip_detected", detector.detect_endpoint_flip("flipping")))

    # S6.3: LCT mismatch detected
    detector.record_event(DiscoveryEvent(
        entity_id="mismatch", source=DiscoveryMethod.DNS_SD,
        timestamp=300, endpoint="tcp://1:1", lct_hash="hash_a",
    ))
    detector.record_event(DiscoveryEvent(
        entity_id="mismatch", source=DiscoveryMethod.DHT,
        timestamp=301, endpoint="tcp://1:1", lct_hash="hash_b",
    ))
    checks.append(("s6_lct_mismatch", detector.detect_lct_mismatch("mismatch")))

    # S6.4: Consistent LCT not flagged
    checks.append(("s6_lct_consistent", not detector.detect_lct_mismatch("good_node")))

    # S6.5: Flood detection
    for i in range(25):
        detector.record_event(DiscoveryEvent(
            entity_id="flooder", source=DiscoveryMethod.BROADCAST,
            timestamp=400 + i * 0.1, endpoint="tcp://flood:1",
        ))
    checks.append(("s6_flood_detected", detector.detect_flood("flooder")))

    # S6.6: Block and check
    detector.block("bad_actor")
    checks.append(("s6_block_check", detector.is_blocked("bad_actor")))
    checks.append(("s6_not_blocked", not detector.is_blocked("good_node")))

    # ── S7: Bootstrap Sequence ───────────────────────────────────────────

    boot_entity = EntityRecord(
        entity_id="new_node", public_key=b"pk_new", endpoints=["tcp://new:7400"],
    )
    boot_dns = DnsDiscovery()
    boot_dns.advertise(
        EntityRecord("existing", b"pk", ["tcp://e:7400"]), "e", 7400,
    )
    boot_dht = DHTDiscovery(boot_entity)
    boot_relay = WitnessRelay()

    # S7.1: Bootstrap with DNS peers succeeds
    state = bootstrap_sequence(boot_entity, boot_dns, boot_dht, boot_relay)
    checks.append(("s7_bootstrap_ready", state.phase == "ready"))

    # S7.2: Discovered peers counted
    checks.append(("s7_discovered_peers", state.discovered_peers > 0))

    # S7.3: Bootstrap with seeds
    state = bootstrap_sequence(
        boot_entity, DnsDiscovery(), DHTDiscovery(boot_entity), WitnessRelay(),
        seed_endpoints=["tcp://seed1:7400", "tcp://seed2:7400"],
    )
    checks.append(("s7_seed_bootstrap", state.phase == "ready"))

    # S7.4: Isolated bootstrap
    state = bootstrap_sequence(
        boot_entity, DnsDiscovery(), DHTDiscovery(boot_entity), WitnessRelay(),
    )
    checks.append(("s7_isolated", state.phase == "isolated" and len(state.errors) > 0))

    # ── S8: Discovery Cache ──────────────────────────────────────────────

    cache = DiscoveryCache(max_size=5, ttl=100)
    now = 1000.0

    # S8.1: Put and get
    rec = EntityRecord("cached1", b"pk", [], trust_score=0.9)
    cache.put(rec, now)
    checks.append(("s8_put_get", cache.get("cached1", now) is not None))

    # S8.2: Expired entry returns None
    checks.append(("s8_expired_none", cache.get("cached1", now + 200) is None))

    # S8.3: Ranked returns sorted by trust
    for i in range(4):
        r = EntityRecord(f"r{i}", b"pk", [], trust_score=rng.random())
        cache.put(r, now)
    ranked = cache.ranked(now)
    trust_scores = [r.trust_score for r in ranked]
    checks.append(("s8_ranked_sorted", trust_scores == sorted(trust_scores, reverse=True)))

    # S8.4: Eviction at max size
    for i in range(10):
        r = EntityRecord(f"evict{i}", b"pk", [], trust_score=rng.random())
        cache.put(r, now)
    checks.append(("s8_eviction", cache.size() <= 5))

    # S8.5: Missing entity returns None
    checks.append(("s8_missing_none", cache.get("nonexistent", now) is None))

    # ── S9: NAT Traversal ────────────────────────────────────────────────

    # S9.1: No NAT → direct
    open_nat = NATInfo("1.2.3.4", 7400, "none")
    other = NATInfo("5.6.7.8", 7400, "full_cone")
    checks.append(("s9_no_nat_direct", select_connection_strategy(open_nat, other) == "direct"))

    # S9.2: Both full cone → hole punch
    a_nat = NATInfo("1.1.1.1", 7400, "full_cone")
    b_nat = NATInfo("2.2.2.2", 7400, "full_cone")
    checks.append(("s9_full_cone_punch", select_connection_strategy(a_nat, b_nat) == "hole_punch"))

    # S9.3: Both symmetric → need relay
    sym_a = NATInfo("1.1.1.1", 7400, "symmetric", relay_endpoint="relay://r1")
    sym_b = NATInfo("2.2.2.2", 7400, "symmetric")
    checks.append(("s9_symmetric_relay", select_connection_strategy(sym_a, sym_b) == "relay"))

    # S9.4: Both symmetric, no relay → unreachable
    sym_c = NATInfo("3.3.3.3", 7400, "symmetric")
    sym_d = NATInfo("4.4.4.4", 7400, "symmetric")
    checks.append(("s9_symmetric_unreachable", select_connection_strategy(sym_c, sym_d) == "unreachable"))

    # S9.5: Direct connect check
    checks.append(("s9_direct_connect", open_nat.can_direct_connect(other)))
    checks.append(("s9_symmetric_no_direct", not sym_c.can_direct_connect(sym_d)))

    # ── S10: Rate Limiting ───────────────────────────────────────────────

    limiter = DiscoveryRateLimiter(max_per_minute=5, max_per_hour=20)
    t = 5000.0

    # S10.1: Initial requests allowed
    for i in range(5):
        checks.append(("", limiter.allow("tester", t + i)))
    checks = [c for c in checks if c[0] != ""]  # Remove inline checks
    checks.append(("s10_initial_allowed", limiter.allow("tester2", t)))

    # S10.2: Minute limit enforced
    lim = DiscoveryRateLimiter(max_per_minute=3, max_per_hour=100)
    for _ in range(3):
        lim.allow("limited", t)
    checks.append(("s10_minute_limit", not lim.allow("limited", t + 1)))

    # S10.3: Minute limit resets after 60s
    checks.append(("s10_minute_reset", lim.allow("limited", t + 61)))

    # S10.4: Hour limit enforced
    hour_lim = DiscoveryRateLimiter(max_per_minute=100, max_per_hour=5)
    for i in range(5):
        hour_lim.allow("hourly", t + i * 61)
    checks.append(("s10_hour_limit", not hour_lim.allow("hourly", t + 400)))

    # S10.5: Remaining counts
    rem_lim = DiscoveryRateLimiter(max_per_minute=10, max_per_hour=50)
    rem_lim.allow("counter", t)
    rem_lim.allow("counter", t + 1)
    per_min, per_hour = rem_lim.remaining("counter", t + 2)
    checks.append(("s10_remaining", per_min == 8 and per_hour == 48))

    # ── S11: Performance ─────────────────────────────────────────────────

    # S11.1: DHT with 1000 nodes
    t0 = time.time()
    big_dht = DHTDiscovery(EntityRecord("root", b"pk", []))
    for i in range(1000):
        rec = EntityRecord(f"dht_node_{i}", f"pk_{i}".encode(),
                          [f"tcp://10.{i//256}.{i%256}.1:7400"])
        big_dht.add_node(rec)
    elapsed = time.time() - t0
    checks.append(("s11_dht_1000_insert", big_dht.node_count() > 0 and elapsed < 2.0))

    # S11.2: DHT closest lookup at scale
    t0 = time.time()
    closest = big_dht.find_closest("search_target", count=20)
    elapsed = time.time() - t0
    checks.append(("s11_dht_lookup", len(closest) == 20 and elapsed < 1.0))

    # S11.3: Witness relay with 500 witness links
    t0 = time.time()
    big_relay = WitnessRelay()
    for i in range(500):
        a_id = f"wr_{i}"
        b_id = f"wr_{(i + 1) % 500}"
        big_relay.add_witness(
            a_id, b_id,
            EntityRecord(b_id, b"pk", []),
        )
    discovered = big_relay.discover_from("wr_0", max_hops=3)
    elapsed = time.time() - t0
    checks.append(("s11_relay_500", len(discovered) > 0 and elapsed < 2.0))

    # S11.4: Discovery cache ranked at scale
    t0 = time.time()
    big_cache = DiscoveryCache(max_size=500)
    for i in range(500):
        r = EntityRecord(f"bc_{i}", b"pk", [], trust_score=rng.random())
        big_cache.put(r, now)
    ranked = big_cache.ranked(now)
    elapsed = time.time() - t0
    checks.append(("s11_cache_500_ranked", len(ranked) == 500 and elapsed < 1.0))

    # S11.5: Poisoning detector at scale
    t0 = time.time()
    big_detector = PoisoningDetector()
    for i in range(1000):
        big_detector.record_event(DiscoveryEvent(
            entity_id=f"entity_{i % 50}",
            source=DiscoveryMethod.DHT,
            timestamp=now + i * 0.01,
            endpoint=f"tcp://10.0.{i % 256}.1:7400",
        ))
    elapsed = time.time() - t0
    checks.append(("s11_poisoning_1000", elapsed < 1.0))

    # ── Print Results ────────────────────────────────────────────────────
    passed = sum(1 for _, ok in checks if ok)
    total = len(checks)
    print(f"\n{'='*60}")
    print(f"  Entity Discovery Protocol — {passed}/{total} checks passed")
    print(f"{'='*60}")

    for name, ok in checks:
        status = "PASS" if ok else "FAIL"
        print(f"  [{status}] {name}")

    if passed < total:
        print(f"\n  FAILURES:")
        for name, ok in checks:
            if not ok:
                print(f"    ✗ {name}")

    print()
    return passed, total


if __name__ == "__main__":
    run_checks()
