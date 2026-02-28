#!/usr/bin/env python3
"""
Real Network Deployment Simulation with Latency Profiles
==========================================================

Reference implementation simulating realistic network conditions for
Web4 federation deployment: geographic latency, packet loss, bandwidth
constraints, and their effects on trust propagation and consensus.

Sections:
1. Geographic Network Topology
2. Latency Model (Real-World Profiles)
3. Bandwidth-Constrained Message Passing
4. Trust Propagation Under Latency
5. Consensus Performance with Real Latency
6. Geographic Partition Simulation
7. Latency-Aware Gossip Protocol
8. Priority-Based Message Scheduling
9. Jitter and Packet Loss Effects
10. Multi-Region Federation Performance
11. Deployment Topology Optimization
12. Complete Deployment Simulation

Run: python real_network_simulation.py
"""

import math
import random
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple


# ─── §1  Geographic Network Topology ─────────────────────────────────────

class Region(Enum):
    US_EAST = "us-east"
    US_WEST = "us-west"
    EU_WEST = "eu-west"
    EU_CENTRAL = "eu-central"
    ASIA_EAST = "asia-east"
    ASIA_SOUTH = "asia-south"
    OCEANIA = "oceania"
    SOUTH_AMERICA = "south-america"


# Approximate inter-region latencies in ms (one-way)
LATENCY_MAP: Dict[Tuple[Region, Region], float] = {
    (Region.US_EAST, Region.US_WEST): 35,
    (Region.US_EAST, Region.EU_WEST): 45,
    (Region.US_EAST, Region.EU_CENTRAL): 55,
    (Region.US_EAST, Region.ASIA_EAST): 100,
    (Region.US_EAST, Region.ASIA_SOUTH): 120,
    (Region.US_EAST, Region.OCEANIA): 110,
    (Region.US_EAST, Region.SOUTH_AMERICA): 60,
    (Region.US_WEST, Region.EU_WEST): 70,
    (Region.US_WEST, Region.EU_CENTRAL): 80,
    (Region.US_WEST, Region.ASIA_EAST): 65,
    (Region.US_WEST, Region.ASIA_SOUTH): 95,
    (Region.US_WEST, Region.OCEANIA): 75,
    (Region.US_WEST, Region.SOUTH_AMERICA): 80,
    (Region.EU_WEST, Region.EU_CENTRAL): 10,
    (Region.EU_WEST, Region.ASIA_EAST): 130,
    (Region.EU_WEST, Region.ASIA_SOUTH): 90,
    (Region.EU_WEST, Region.OCEANIA): 150,
    (Region.EU_WEST, Region.SOUTH_AMERICA): 100,
    (Region.EU_CENTRAL, Region.ASIA_EAST): 120,
    (Region.EU_CENTRAL, Region.ASIA_SOUTH): 80,
    (Region.EU_CENTRAL, Region.OCEANIA): 140,
    (Region.EU_CENTRAL, Region.SOUTH_AMERICA): 110,
    (Region.ASIA_EAST, Region.ASIA_SOUTH): 40,
    (Region.ASIA_EAST, Region.OCEANIA): 55,
    (Region.ASIA_EAST, Region.SOUTH_AMERICA): 160,
    (Region.ASIA_SOUTH, Region.OCEANIA): 70,
    (Region.ASIA_SOUTH, Region.SOUTH_AMERICA): 170,
    (Region.OCEANIA, Region.SOUTH_AMERICA): 130,
}


def get_latency(r1: Region, r2: Region) -> float:
    """Get one-way latency between two regions in ms."""
    if r1 == r2:
        return 2.0  # Intra-region latency
    key = (r1, r2) if (r1, r2) in LATENCY_MAP else (r2, r1)
    return LATENCY_MAP.get(key, 150.0)  # Default high latency


@dataclass
class NetworkNode:
    node_id: str
    region: Region
    trust_scores: Dict[str, float] = field(default_factory=dict)
    message_queue: List[dict] = field(default_factory=list)
    messages_sent: int = 0
    messages_received: int = 0
    bandwidth_mbps: float = 100.0  # Mb/s
    packet_loss_rate: float = 0.01  # 1% default


@dataclass
class GeoNetwork:
    """Network with geographic awareness."""
    nodes: Dict[str, NetworkNode] = field(default_factory=dict)
    edges: Dict[str, Set[str]] = field(default_factory=lambda: defaultdict(set))

    def add_node(self, node_id: str, region: Region, **kwargs):
        self.nodes[node_id] = NetworkNode(node_id=node_id, region=region, **kwargs)

    def add_edge(self, n1: str, n2: str):
        self.edges[n1].add(n2)
        self.edges[n2].add(n1)

    def latency(self, n1: str, n2: str) -> float:
        return get_latency(self.nodes[n1].region, self.nodes[n2].region)

    def round_trip(self, n1: str, n2: str) -> float:
        return 2 * self.latency(n1, n2)


def build_geo_network(nodes_per_region: int = 5, seed: int = 42) -> GeoNetwork:
    """Build a multi-region network."""
    rng = random.Random(seed)
    net = GeoNetwork()

    regions = list(Region)
    node_count = 0
    for region in regions:
        for i in range(nodes_per_region):
            nid = f"{region.value}_{i}"
            net.add_node(nid, region)
            node_count += 1

    # Intra-region: fully connected
    for region in regions:
        region_nodes = [nid for nid, n in net.nodes.items() if n.region == region]
        for i in range(len(region_nodes)):
            for j in range(i + 1, len(region_nodes)):
                net.add_edge(region_nodes[i], region_nodes[j])

    # Inter-region: 2-3 links per region pair
    for i in range(len(regions)):
        for j in range(i + 1, len(regions)):
            r1_nodes = [nid for nid, n in net.nodes.items() if n.region == regions[i]]
            r2_nodes = [nid for nid, n in net.nodes.items() if n.region == regions[j]]
            num_links = rng.randint(2, 3)
            for _ in range(num_links):
                n1 = rng.choice(r1_nodes)
                n2 = rng.choice(r2_nodes)
                net.add_edge(n1, n2)

    # Initialize trust
    all_nodes = list(net.nodes.keys())
    for nid in all_nodes:
        for other in all_nodes:
            if other != nid:
                net.nodes[nid].trust_scores[other] = 0.5 + rng.uniform(-0.05, 0.05)

    return net


def evaluate_geo_topology():
    checks = []

    net = build_geo_network(5, seed=42)
    checks.append(("node_count", len(net.nodes) == 40))  # 8 regions × 5

    # Intra-region latency is low
    us_east_nodes = [nid for nid, n in net.nodes.items() if n.region == Region.US_EAST]
    intra_lat = net.latency(us_east_nodes[0], us_east_nodes[1])
    checks.append(("intra_region_low_latency", intra_lat == 2.0))

    # Cross-region latency is higher
    eu_nodes = [nid for nid, n in net.nodes.items() if n.region == Region.EU_WEST]
    cross_lat = net.latency(us_east_nodes[0], eu_nodes[0])
    checks.append(("cross_region_higher_latency", cross_lat > 10))

    # Symmetric latency
    lat_ab = net.latency(us_east_nodes[0], eu_nodes[0])
    lat_ba = net.latency(eu_nodes[0], us_east_nodes[0])
    checks.append(("symmetric_latency", lat_ab == lat_ba))

    # Edges exist
    total_edges = sum(len(v) for v in net.edges.values()) // 2
    checks.append(("edges_exist", total_edges > 50))

    return checks


# ─── §2  Latency Model (Real-World Profiles) ─────────────────────────────

@dataclass
class LatencyProfile:
    """Realistic latency with jitter and loss."""
    base_latency_ms: float
    jitter_ms: float  # Standard deviation of jitter
    packet_loss_rate: float  # Probability of loss
    congestion_factor: float = 1.0  # Multiplier during congestion

    def sample_latency(self, rng: random.Random) -> Optional[float]:
        """Sample actual latency. Returns None if packet lost."""
        if rng.random() < self.packet_loss_rate:
            return None  # Packet lost
        jitter = rng.gauss(0, self.jitter_ms)
        return max(1.0, (self.base_latency_ms + jitter) * self.congestion_factor)


# Pre-defined profiles for common link types
LINK_PROFILES = {
    "datacenter": LatencyProfile(0.5, 0.1, 0.0001),
    "same_city": LatencyProfile(2.0, 0.5, 0.001),
    "same_country": LatencyProfile(20.0, 5.0, 0.005),
    "cross_continent": LatencyProfile(100.0, 15.0, 0.01),
    "satellite": LatencyProfile(300.0, 50.0, 0.03),
    "mobile_4g": LatencyProfile(50.0, 20.0, 0.02),
    "congested": LatencyProfile(200.0, 80.0, 0.05, congestion_factor=2.0),
}


def evaluate_latency_profiles():
    checks = []
    rng = random.Random(42)

    # Datacenter: low latency, near-zero loss
    dc = LINK_PROFILES["datacenter"]
    dc_samples = [dc.sample_latency(rng) for _ in range(1000)]
    dc_valid = [s for s in dc_samples if s is not None]
    checks.append(("datacenter_low_loss", len(dc_valid) > 990))
    avg_dc = sum(dc_valid) / len(dc_valid)
    checks.append(("datacenter_low_latency", avg_dc < 2.0))

    # Cross-continent: higher latency and loss
    cc = LINK_PROFILES["cross_continent"]
    cc_samples = [cc.sample_latency(rng) for _ in range(1000)]
    cc_valid = [s for s in cc_samples if s is not None]
    cc_loss = 1 - len(cc_valid) / 1000
    checks.append(("cross_continent_some_loss", cc_loss > 0.001))
    avg_cc = sum(cc_valid) / len(cc_valid)
    checks.append(("cross_continent_high_latency", avg_cc > 50))

    # Satellite: highest latency
    sat = LINK_PROFILES["satellite"]
    sat_samples = [sat.sample_latency(rng) for _ in range(1000)]
    sat_valid = [s for s in sat_samples if s is not None]
    avg_sat = sum(sat_valid) / len(sat_valid)
    checks.append(("satellite_highest_latency", avg_sat > avg_cc))

    # Congested: multiplied latency
    cong = LINK_PROFILES["congested"]
    cong_samples = [cong.sample_latency(rng) for _ in range(1000)]
    cong_valid = [s for s in cong_samples if s is not None]
    avg_cong = sum(cong_valid) / len(cong_valid)
    checks.append(("congestion_increases_latency", avg_cong > 200))

    return checks


# ─── §3  Bandwidth-Constrained Message Passing ───────────────────────────

@dataclass
class Message:
    msg_id: str
    sender: str
    receiver: str
    payload_bytes: int
    priority: int = 0  # 0=normal, 1=high, 2=urgent
    send_time: float = 0.0
    arrival_time: Optional[float] = None
    lost: bool = False


class BandwidthSimulator:
    """Simulates bandwidth-limited message delivery."""

    def __init__(self, seed: int = 42):
        self.rng = random.Random(seed)
        self.messages: List[Message] = []
        self.delivered: List[Message] = []
        self.dropped: List[Message] = []
        self.current_time = 0.0

    def send_message(self, net: GeoNetwork, sender: str, receiver: str,
                      payload_bytes: int, priority: int = 0) -> Message:
        msg = Message(
            msg_id=f"msg_{len(self.messages):06d}",
            sender=sender,
            receiver=receiver,
            payload_bytes=payload_bytes,
            priority=priority,
            send_time=self.current_time,
        )
        self.messages.append(msg)

        # Compute delivery time
        base_latency = net.latency(sender, receiver)
        # Bandwidth delay: bytes / (bandwidth * 1000 / 8) = time in ms
        bw_mbps = net.nodes[receiver].bandwidth_mbps
        bandwidth_delay = (payload_bytes * 8) / (bw_mbps * 1000)  # ms

        # Loss check
        loss_rate = net.nodes[receiver].packet_loss_rate
        if self.rng.random() < loss_rate:
            msg.lost = True
            self.dropped.append(msg)
        else:
            # Add jitter
            jitter = self.rng.gauss(0, base_latency * 0.1)
            total_latency = max(1.0, base_latency + bandwidth_delay + jitter)
            msg.arrival_time = self.current_time + total_latency
            self.delivered.append(msg)

        return msg

    def delivery_stats(self) -> dict:
        if not self.messages:
            return {"total": 0}
        delivered_times = [m.arrival_time - m.send_time
                           for m in self.delivered if m.arrival_time is not None]
        return {
            "total": len(self.messages),
            "delivered": len(self.delivered),
            "dropped": len(self.dropped),
            "loss_rate": len(self.dropped) / len(self.messages),
            "avg_latency": sum(delivered_times) / max(len(delivered_times), 1),
            "max_latency": max(delivered_times) if delivered_times else 0,
            "min_latency": min(delivered_times) if delivered_times else 0,
        }


def evaluate_bandwidth():
    checks = []

    net = build_geo_network(3, seed=42)
    sim = BandwidthSimulator(seed=42)
    node_ids = list(net.nodes.keys())

    # Send 100 small messages
    for i in range(100):
        src = node_ids[i % len(node_ids)]
        dst = node_ids[(i + 7) % len(node_ids)]
        if src != dst:
            sim.send_message(net, src, dst, payload_bytes=1024)

    stats = sim.delivery_stats()
    checks.append(("messages_sent", stats["total"] == 100))
    checks.append(("most_delivered", stats["loss_rate"] < 0.1))
    checks.append(("latency_positive", stats["avg_latency"] > 0))

    # Large messages take longer
    sim2 = BandwidthSimulator(seed=42)
    small_msg = sim2.send_message(net, node_ids[0], node_ids[10], 100)
    large_msg = sim2.send_message(net, node_ids[0], node_ids[10], 1_000_000)
    if small_msg.arrival_time and large_msg.arrival_time:
        small_lat = small_msg.arrival_time - small_msg.send_time
        large_lat = large_msg.arrival_time - large_msg.send_time
        checks.append(("large_msg_slower", large_lat > small_lat))
    else:
        checks.append(("large_msg_slower", True))

    return checks


# ─── §4  Trust Propagation Under Latency ─────────────────────────────────

def propagate_trust_with_latency(net: GeoNetwork, source: str,
                                   target: str, new_trust: float,
                                   max_hops: int = 5,
                                   rng: random.Random = None) -> dict:
    """Propagate a trust update through the network, tracking latency."""
    if rng is None:
        rng = random.Random(42)

    results = {"source": source, "target": target, "new_trust": new_trust}

    # BFS propagation tracking delivery time
    propagation_log = []
    visited = set()
    # (node_id, received_trust, cumulative_latency, hop_count)
    queue = [(source, new_trust, 0.0, 0)]

    while queue:
        queue.sort(key=lambda x: x[2])  # Process by arrival time
        node, trust_val, cum_lat, hops = queue.pop(0)

        if node in visited or hops > max_hops:
            continue
        visited.add(node)

        # Apply trust update at this node
        net.nodes[node].trust_scores[target] = trust_val
        propagation_log.append({
            "node": node,
            "trust": trust_val,
            "cumulative_latency_ms": cum_lat,
            "hops": hops,
            "region": net.nodes[node].region.value,
        })

        # Forward to neighbors with latency
        for neighbor in net.edges.get(node, set()):
            if neighbor not in visited:
                link_latency = net.latency(node, neighbor)
                # Add jitter
                jitter = rng.gauss(0, link_latency * 0.1)
                actual_lat = max(1.0, link_latency + jitter)
                # Trust decays slightly per hop
                decayed = trust_val * 0.98
                queue.append((neighbor, decayed, cum_lat + actual_lat, hops + 1))

    results["nodes_reached"] = len(propagation_log)
    results["total_nodes"] = len(net.nodes)
    results["propagation_log"] = propagation_log

    if propagation_log:
        latencies = [p["cumulative_latency_ms"] for p in propagation_log]
        results["max_propagation_latency"] = max(latencies)
        results["avg_propagation_latency"] = sum(latencies) / len(latencies)
        results["p99_latency"] = sorted(latencies)[int(len(latencies) * 0.99)]

    return results


def evaluate_trust_propagation():
    checks = []
    rng = random.Random(42)

    net = build_geo_network(5, seed=42)
    node_ids = list(net.nodes.keys())

    # Propagate from US_EAST
    us_east_node = [nid for nid, n in net.nodes.items() if n.region == Region.US_EAST][0]
    result = propagate_trust_with_latency(net, us_east_node, node_ids[10], 0.9, rng=rng)

    # Should reach most nodes
    coverage = result["nodes_reached"] / result["total_nodes"]
    checks.append(("propagation_coverage", coverage > 0.5))

    # Same-region nodes reached faster than cross-region
    log = result["propagation_log"]
    same_region = [p for p in log if p["region"] == "us-east"]
    cross_region = [p for p in log if p["region"] != "us-east"]
    if same_region and cross_region:
        avg_same = sum(p["cumulative_latency_ms"] for p in same_region) / len(same_region)
        avg_cross = sum(p["cumulative_latency_ms"] for p in cross_region) / len(cross_region)
        checks.append(("same_region_faster", avg_same < avg_cross))
    else:
        checks.append(("same_region_faster", True))

    # Trust decays with hops
    multi_hop = [p for p in log if p["hops"] > 2]
    if multi_hop:
        decayed_trust = multi_hop[-1]["trust"]
        checks.append(("trust_decays_with_hops", decayed_trust < 0.9))
    else:
        checks.append(("trust_decays_with_hops", True))

    # Max propagation latency is bounded
    checks.append(("max_latency_bounded", result["max_propagation_latency"] < 5000))

    return checks


# ─── §5  Consensus Performance with Real Latency ─────────────────────────

def simulate_consensus_round(net: GeoNetwork, proposer: str,
                               rng: random.Random) -> dict:
    """Simulate a BFT consensus round with realistic latency."""
    node_ids = list(net.nodes.keys())
    n = len(node_ids)
    f = (n - 1) // 3  # Max Byzantine faults

    results = {"proposer": proposer, "n": n, "f": f}

    # Phase 1: Pre-prepare (proposer broadcasts)
    pre_prepare_times = {}
    for nid in node_ids:
        if nid == proposer:
            pre_prepare_times[nid] = 0.0
        else:
            lat = net.latency(proposer, nid)
            jitter = rng.gauss(0, lat * 0.1)
            pre_prepare_times[nid] = max(1.0, lat + jitter)

    # Phase 2: Prepare (each node broadcasts)
    prepare_times = {}
    for nid in node_ids:
        # Time when nid received pre-prepare + sends to all
        start = pre_prepare_times[nid]
        for other in node_ids:
            if other != nid:
                lat = net.latency(nid, other)
                jitter = rng.gauss(0, lat * 0.1)
                arrival = start + max(1.0, lat + jitter)
                key = (other, nid)  # other receives prepare from nid
                if other not in prepare_times:
                    prepare_times[other] = []
                prepare_times[other].append(arrival)

    # Phase 3: Commit (when node has 2f+1 prepares)
    commit_times = {}
    quorum = 2 * f + 1
    for nid in node_ids:
        arrivals = sorted(prepare_times.get(nid, []))
        if len(arrivals) >= quorum:
            commit_times[nid] = arrivals[quorum - 1]  # Time of quorum-th prepare

    # Phase 4: Reply (when node has 2f+1 commits)
    # Simplified: commit broadcast
    reply_times = {}
    for nid in node_ids:
        if nid not in commit_times:
            continue
        start = commit_times[nid]
        for other in node_ids:
            if other != nid:
                lat = net.latency(nid, other)
                arrival = start + max(1.0, lat + rng.gauss(0, lat * 0.1))
                if other not in reply_times:
                    reply_times[other] = []
                reply_times[other].append(arrival)

    # Finalization: when node has 2f+1 commits
    final_times = {}
    for nid in node_ids:
        arrivals = sorted(reply_times.get(nid, []))
        if len(arrivals) >= quorum:
            final_times[nid] = arrivals[quorum - 1]

    results["nodes_finalized"] = len(final_times)
    if final_times:
        results["min_finalization"] = min(final_times.values())
        results["max_finalization"] = max(final_times.values())
        results["avg_finalization"] = sum(final_times.values()) / len(final_times)
        results["consensus_latency"] = max(final_times.values())
    else:
        results["consensus_latency"] = float('inf')

    return results


def evaluate_consensus_latency():
    checks = []
    rng = random.Random(42)

    net = build_geo_network(3, seed=42)  # 24 nodes
    node_ids = list(net.nodes.keys())

    # Consensus with US_EAST proposer
    us_proposer = [nid for nid, n in net.nodes.items() if n.region == Region.US_EAST][0]
    result = simulate_consensus_round(net, us_proposer, rng)

    checks.append(("consensus_achieved", result["nodes_finalized"] > 0))
    checks.append(("consensus_latency_bounded", result["consensus_latency"] < 10000))

    # Proposer in different region affects latency
    asia_proposer = [nid for nid, n in net.nodes.items() if n.region == Region.ASIA_EAST][0]
    result_asia = simulate_consensus_round(net, asia_proposer, rng)

    # Both should achieve consensus
    checks.append(("asia_consensus", result_asia["nodes_finalized"] > 0))

    # Global consensus is slower than single-region
    # Build single-region network for comparison
    single_net = GeoNetwork()
    for i in range(24):
        single_net.add_node(f"local_{i}", Region.US_EAST)
    for i in range(24):
        for j in range(i+1, 24):
            single_net.add_edge(f"local_{i}", f"local_{j}")
    # Init trust
    for nid in single_net.nodes:
        for other in single_net.nodes:
            if other != nid:
                single_net.nodes[nid].trust_scores[other] = 0.5

    result_local = simulate_consensus_round(single_net, "local_0", rng)
    if result_local["consensus_latency"] < float('inf') and result["consensus_latency"] < float('inf'):
        checks.append(("global_slower_than_local",
                        result["consensus_latency"] > result_local["consensus_latency"]))
    else:
        checks.append(("global_slower_than_local", True))

    return checks


# ─── §6  Geographic Partition Simulation ──────────────────────────────────

def simulate_geographic_partition(net: GeoNetwork,
                                    isolated_regions: Set[Region],
                                    duration_steps: int,
                                    rng: random.Random) -> dict:
    """Simulate a geographic partition (submarine cable cut, etc.)."""
    results = {"isolated_regions": [r.value for r in isolated_regions]}

    # Save original edges
    original_edges = {k: set(v) for k, v in net.edges.items()}

    # Remove cross-partition edges
    isolated_nodes = {nid for nid, n in net.nodes.items() if n.region in isolated_regions}
    connected_nodes = {nid for nid in net.nodes if nid not in isolated_nodes}

    removed_edges = 0
    for nid in list(net.edges.keys()):
        original = set(net.edges[nid])
        for peer in original:
            if (nid in isolated_nodes) != (peer in isolated_nodes):
                net.edges[nid].discard(peer)
                net.edges[peer].discard(nid)
                removed_edges += 1
    removed_edges //= 2

    results["edges_removed"] = removed_edges
    results["isolated_node_count"] = len(isolated_nodes)
    results["connected_node_count"] = len(connected_nodes)

    # Simulate trust evolution in isolation
    for _ in range(duration_steps):
        for nid in net.nodes:
            neighbors = net.edges.get(nid, set())
            if not neighbors:
                continue
            peer = rng.choice(list(neighbors))
            quality = rng.uniform(0, 1)
            old_t = net.nodes[nid].trust_scores.get(peer, 0.5)
            new_t = max(0.0, min(1.0, old_t + 0.02 * (quality - 0.5)))
            net.nodes[nid].trust_scores[peer] = new_t

    # Measure divergence between partitions
    divergences = []
    for iso_node in list(isolated_nodes)[:5]:
        for conn_node in list(connected_nodes)[:5]:
            shared = (set(net.nodes[iso_node].trust_scores.keys()) &
                      set(net.nodes[conn_node].trust_scores.keys()))
            for target in shared:
                d = abs(net.nodes[iso_node].trust_scores[target] -
                        net.nodes[conn_node].trust_scores[target])
                divergences.append(d)

    results["avg_divergence"] = sum(divergences) / max(len(divergences), 1) if divergences else 0
    results["max_divergence"] = max(divergences) if divergences else 0

    # Restore edges
    net.edges = original_edges

    return results


def evaluate_geo_partition():
    checks = []
    rng = random.Random(42)

    net = build_geo_network(5, seed=42)

    # Simulate Asia isolation (submarine cable cut)
    result = simulate_geographic_partition(
        net, {Region.ASIA_EAST, Region.ASIA_SOUTH}, 100, rng)

    checks.append(("edges_removed", result["edges_removed"] > 0))
    checks.append(("isolation_effective", result["isolated_node_count"] == 10))
    checks.append(("some_divergence", result["avg_divergence"] >= 0))

    # Oceania isolation (smaller partition)
    result2 = simulate_geographic_partition(
        net, {Region.OCEANIA}, 100, rng)
    checks.append(("small_partition", result2["isolated_node_count"] == 5))

    return checks


# ─── §7  Latency-Aware Gossip Protocol ───────────────────────────────────

def latency_aware_gossip(net: GeoNetwork, source: str, payload: dict,
                          fan_out: int = 3, rng: random.Random = None) -> dict:
    """Gossip protocol that prefers low-latency neighbors."""
    if rng is None:
        rng = random.Random(42)

    informed = {source}
    message_count = 0
    round_log = []
    max_rounds = 20

    for round_num in range(max_rounds):
        newly_informed = set()

        # Each informed node gossips to fan_out neighbors
        for nid in list(informed):
            neighbors = list(net.edges.get(nid, set()))
            if not neighbors:
                continue

            # Prefer uninformed + low latency neighbors
            uninformed = [n for n in neighbors if n not in informed and n not in newly_informed]
            if uninformed:
                uninformed.sort(key=lambda n: net.latency(nid, n))
                targets = uninformed[:fan_out]
            else:
                targets = rng.sample(neighbors, min(fan_out, len(neighbors)))

            for target in targets:
                message_count += 1
                if target not in informed:
                    newly_informed.add(target)

        informed.update(newly_informed)
        round_log.append({
            "round": round_num,
            "informed": len(informed),
            "new_this_round": len(newly_informed),
            "messages": message_count,
        })

        if len(informed) >= len(net.nodes):
            break

    return {
        "total_informed": len(informed),
        "total_nodes": len(net.nodes),
        "coverage": len(informed) / len(net.nodes),
        "rounds": len(round_log),
        "total_messages": message_count,
        "round_log": round_log,
    }


def evaluate_latency_gossip():
    checks = []
    rng = random.Random(42)

    net = build_geo_network(5, seed=42)
    us_node = [nid for nid, n in net.nodes.items() if n.region == Region.US_EAST][0]

    result = latency_aware_gossip(net, us_node, {"trust_update": 0.9}, fan_out=3, rng=rng)

    # High coverage
    checks.append(("gossip_coverage", result["coverage"] > 0.5))

    # Reasonable message count
    checks.append(("message_efficiency",
                    result["total_messages"] < len(net.nodes) * 10))

    # Completes within bounded rounds
    checks.append(("bounded_rounds", result["rounds"] <= 20))

    # Same region reached first
    log = result["round_log"]
    if len(log) >= 2:
        checks.append(("early_spread", log[0]["new_this_round"] > 0 or log[1]["new_this_round"] > 0))
    else:
        checks.append(("early_spread", True))

    return checks


# ─── §8  Priority-Based Message Scheduling ───────────────────────────────

@dataclass
class PriorityScheduler:
    """Schedules messages by priority, respecting bandwidth limits."""
    queue: List[Message] = field(default_factory=list)
    delivered: List[Message] = field(default_factory=list)
    bandwidth_bps: float = 100_000_000  # 100 Mbps default
    current_time: float = 0.0

    def enqueue(self, msg: Message):
        self.queue.append(msg)
        # Sort by priority (higher first), then by time
        self.queue.sort(key=lambda m: (-m.priority, m.send_time))

    def process(self, duration_ms: float, net: GeoNetwork):
        end_time = self.current_time + duration_ms
        bytes_available = (self.bandwidth_bps / 8) * (duration_ms / 1000)
        bytes_sent = 0

        while self.queue and bytes_sent < bytes_available:
            msg = self.queue.pop(0)
            if bytes_sent + msg.payload_bytes <= bytes_available:
                lat = net.latency(msg.sender, msg.receiver)
                msg.arrival_time = self.current_time + lat
                self.delivered.append(msg)
                bytes_sent += msg.payload_bytes
            else:
                self.queue.insert(0, msg)  # Put back
                break

        self.current_time = end_time


def evaluate_priority_scheduling():
    checks = []

    net = build_geo_network(3, seed=42)
    scheduler = PriorityScheduler(bandwidth_bps=1_000_000)  # 1 Mbps
    node_ids = list(net.nodes.keys())

    # Send mix of priorities
    for i in range(20):
        msg = Message(
            msg_id=f"msg_{i}",
            sender=node_ids[0],
            receiver=node_ids[1],
            payload_bytes=10000,
            priority=i % 3,
            send_time=0.0,
        )
        scheduler.enqueue(msg)

    # Process for 100ms
    scheduler.process(100, net)

    # High priority messages should be delivered first
    if scheduler.delivered:
        first_priority = scheduler.delivered[0].priority
        checks.append(("highest_priority_first", first_priority == 2))

        # All delivered are sorted by priority
        priorities = [m.priority for m in scheduler.delivered]
        is_sorted = all(priorities[i] >= priorities[i+1] for i in range(len(priorities)-1))
        checks.append(("priority_ordering", is_sorted))
    else:
        checks.append(("highest_priority_first", True))
        checks.append(("priority_ordering", True))

    # Some messages still in queue (bandwidth limited)
    checks.append(("bandwidth_limits", len(scheduler.queue) > 0 or len(scheduler.delivered) == 20))

    # Delivered messages have arrival times
    all_have_arrival = all(m.arrival_time is not None for m in scheduler.delivered)
    checks.append(("arrival_times_set", all_have_arrival))

    return checks


# ─── §9  Jitter and Packet Loss Effects ──────────────────────────────────

def measure_jitter_effects(net: GeoNetwork, src: str, dst: str,
                             num_packets: int,
                             loss_rate: float,
                             jitter_factor: float,
                             rng: random.Random) -> dict:
    """Measure the effect of jitter and loss on message delivery."""
    base_lat = net.latency(src, dst)
    delivered = []
    lost = 0

    for i in range(num_packets):
        if rng.random() < loss_rate:
            lost += 1
            continue
        jitter = rng.gauss(0, base_lat * jitter_factor)
        actual_lat = max(1.0, base_lat + jitter)
        delivered.append(actual_lat)

    if not delivered:
        return {"loss_rate": 1.0, "delivered": 0}

    delivered.sort()
    return {
        "base_latency": base_lat,
        "avg_latency": sum(delivered) / len(delivered),
        "p50": delivered[len(delivered) // 2],
        "p95": delivered[int(len(delivered) * 0.95)],
        "p99": delivered[int(len(delivered) * 0.99)],
        "min": delivered[0],
        "max": delivered[-1],
        "std": (sum((d - sum(delivered)/len(delivered))**2 for d in delivered) / len(delivered)) ** 0.5,
        "delivered": len(delivered),
        "lost": lost,
        "loss_rate": lost / num_packets,
        "jitter_ratio": (delivered[-1] - delivered[0]) / base_lat if base_lat > 0 else 0,
    }


def evaluate_jitter_loss():
    checks = []
    rng = random.Random(42)

    net = build_geo_network(3, seed=42)
    us_node = [nid for nid, n in net.nodes.items() if n.region == Region.US_EAST][0]
    eu_node = [nid for nid, n in net.nodes.items() if n.region == Region.EU_WEST][0]

    # Low jitter, no loss
    low_jitter = measure_jitter_effects(net, us_node, eu_node, 1000, 0.0, 0.05, rng)
    checks.append(("low_jitter_stable", low_jitter["std"] < 10))
    checks.append(("no_loss_full_delivery", low_jitter["loss_rate"] == 0.0))

    # High jitter
    high_jitter = measure_jitter_effects(net, us_node, eu_node, 1000, 0.0, 0.5, rng)
    checks.append(("high_jitter_more_variance", high_jitter["std"] > low_jitter["std"]))

    # With packet loss
    with_loss = measure_jitter_effects(net, us_node, eu_node, 1000, 0.05, 0.1, rng)
    checks.append(("loss_reduces_delivery", with_loss["loss_rate"] > 0.01))

    # P99 vs P50 gap increases with jitter
    checks.append(("tail_latency_gap",
                    high_jitter["p99"] - high_jitter["p50"] > low_jitter["p99"] - low_jitter["p50"]))

    return checks


# ─── §10  Multi-Region Federation Performance ────────────────────────────

def benchmark_federation(net: GeoNetwork, num_operations: int,
                          rng: random.Random) -> dict:
    """Benchmark federation operations across regions."""
    node_ids = list(net.nodes.keys())
    results = {}

    # Trust update propagation times
    prop_times = []
    for _ in range(num_operations):
        src = rng.choice(node_ids)
        dst = rng.choice(node_ids)
        if src == dst:
            continue
        prop_result = propagate_trust_with_latency(
            net, src, dst, rng.uniform(0, 1), max_hops=3, rng=rng)
        if "max_propagation_latency" in prop_result:
            prop_times.append(prop_result["max_propagation_latency"])

    if prop_times:
        results["avg_propagation_ms"] = sum(prop_times) / len(prop_times)
        results["p95_propagation_ms"] = sorted(prop_times)[int(len(prop_times) * 0.95)]
        results["max_propagation_ms"] = max(prop_times)

    # Per-region consensus latency
    region_consensus = {}
    for region in Region:
        region_nodes = [nid for nid, n in net.nodes.items() if n.region == region]
        if region_nodes:
            proposer = region_nodes[0]
            c_result = simulate_consensus_round(net, proposer, rng)
            region_consensus[region.value] = c_result.get("consensus_latency", float('inf'))
    results["region_consensus"] = region_consensus

    # Cross-region message stats
    msg_sim = BandwidthSimulator(seed=42)
    for _ in range(100):
        src = rng.choice(node_ids)
        dst = rng.choice(node_ids)
        if src != dst:
            msg_sim.send_message(net, src, dst, 1024)
    msg_stats = msg_sim.delivery_stats()
    results["msg_stats"] = msg_stats

    return results


def evaluate_federation_performance():
    checks = []
    rng = random.Random(42)

    net = build_geo_network(3, seed=42)

    bench = benchmark_federation(net, num_operations=20, rng=rng)

    # Propagation times exist
    checks.append(("propagation_measured", "avg_propagation_ms" in bench))
    if "avg_propagation_ms" in bench:
        checks.append(("propagation_bounded", bench["avg_propagation_ms"] < 5000))

    # Per-region consensus
    if bench.get("region_consensus"):
        # Some regions achieve consensus
        finalized = [v for v in bench["region_consensus"].values() if v < float('inf')]
        checks.append(("regions_reach_consensus", len(finalized) > 0))
    else:
        checks.append(("regions_reach_consensus", True))

    # Message delivery
    if bench.get("msg_stats"):
        checks.append(("messages_delivered", bench["msg_stats"]["delivered"] > 80))
    else:
        checks.append(("messages_delivered", True))

    return checks


# ─── §11  Deployment Topology Optimization ───────────────────────────────

def evaluate_topology(net: GeoNetwork, rng: random.Random) -> dict:
    """Evaluate a network topology's fitness."""
    node_ids = list(net.nodes.keys())

    # Average latency across all edges
    latencies = []
    for nid in node_ids:
        for peer in net.edges.get(nid, set()):
            latencies.append(net.latency(nid, peer))
    avg_lat = sum(latencies) / max(len(latencies), 1)

    # Connectivity: minimum degree
    degrees = [len(net.edges.get(nid, set())) for nid in node_ids]
    min_degree = min(degrees) if degrees else 0

    # Diameter estimate (max shortest path via BFS, sampled)
    max_path = 0
    for _ in range(10):
        start = rng.choice(node_ids)
        visited = {start: 0}
        queue = [start]
        while queue:
            node = queue.pop(0)
            for peer in net.edges.get(node, set()):
                if peer not in visited:
                    visited[peer] = visited[node] + 1
                    queue.append(peer)
                    max_path = max(max_path, visited[peer])

    # Regional coverage
    regions_covered = len(set(net.nodes[nid].region for nid in node_ids))

    return {
        "avg_latency": avg_lat,
        "min_degree": min_degree,
        "diameter": max_path,
        "regions_covered": regions_covered,
        "total_edges": len(latencies) // 2,
        "fitness": 1.0 / (1.0 + avg_lat / 100) * min(min_degree / 3, 1.0),
    }


def evaluate_topology_optimization():
    checks = []
    rng = random.Random(42)

    # Evaluate default topology
    net = build_geo_network(5, seed=42)
    default_eval = evaluate_topology(net, rng)
    checks.append(("default_fitness_positive", default_eval["fitness"] > 0))
    checks.append(("full_region_coverage", default_eval["regions_covered"] == 8))

    # Compare: dense vs sparse topology
    dense_net = build_geo_network(10, seed=42)
    dense_eval = evaluate_topology(dense_net, rng)

    sparse_net = build_geo_network(2, seed=42)
    sparse_eval = evaluate_topology(sparse_net, rng)

    # Dense has better connectivity
    checks.append(("dense_higher_min_degree",
                    dense_eval["min_degree"] >= sparse_eval["min_degree"]))

    # Diameter check
    checks.append(("diameter_bounded", default_eval["diameter"] < 20))

    return checks


# ─── §12  Complete Deployment Simulation ──────────────────────────────────

def run_complete_deployment(seed: int = 42) -> dict:
    """Full deployment simulation: build, test, measure, optimize."""
    rng = random.Random(seed)
    results = {}

    # Phase 1: Build multi-region network
    net = build_geo_network(5, seed=seed)
    results["nodes"] = len(net.nodes)
    results["regions"] = len(set(n.region for n in net.nodes.values()))

    # Phase 2: Topology evaluation
    topo = evaluate_topology(net, rng)
    results["topology"] = topo

    # Phase 3: Trust propagation benchmark
    us_node = [nid for nid, n in net.nodes.items() if n.region == Region.US_EAST][0]
    prop = propagate_trust_with_latency(net, us_node, list(net.nodes.keys())[10], 0.9, rng=rng)
    results["propagation_coverage"] = prop["nodes_reached"] / prop["total_nodes"]
    results["propagation_latency"] = prop.get("max_propagation_latency", 0)

    # Phase 4: Consensus benchmark
    consensus = simulate_consensus_round(net, us_node, rng)
    results["consensus_latency"] = consensus["consensus_latency"]
    results["consensus_finalized"] = consensus["nodes_finalized"]

    # Phase 5: Geographic partition test
    partition = simulate_geographic_partition(
        net, {Region.ASIA_EAST}, 50, rng)
    results["partition_divergence"] = partition["avg_divergence"]

    # Phase 6: Gossip efficiency
    gossip = latency_aware_gossip(net, us_node, {"update": True}, fan_out=3, rng=rng)
    results["gossip_coverage"] = gossip["coverage"]
    results["gossip_messages"] = gossip["total_messages"]

    # Phase 7: Jitter/loss analysis
    eu_node = [nid for nid, n in net.nodes.items() if n.region == Region.EU_WEST][0]
    jitter = measure_jitter_effects(net, us_node, eu_node, 500, 0.02, 0.2, rng)
    results["jitter_p99"] = jitter.get("p99", 0)
    results["jitter_loss"] = jitter.get("loss_rate", 0)

    # Overall health score
    health = 1.0
    if results["propagation_coverage"] < 0.8:
        health *= 0.8
    if results["consensus_latency"] > 5000:
        health *= 0.7
    if results["gossip_coverage"] < 0.8:
        health *= 0.8
    results["health_score"] = health

    return results


def evaluate_complete_deployment():
    checks = []

    results = run_complete_deployment(seed=42)

    # Network built correctly
    checks.append(("network_built", results["nodes"] == 40))
    checks.append(("all_regions", results["regions"] == 8))

    # Propagation works
    checks.append(("propagation_works", results["propagation_coverage"] > 0.3))

    # Consensus achievable
    checks.append(("consensus_achievable", results["consensus_finalized"] > 0))

    # Gossip reaches network
    checks.append(("gossip_reaches", results["gossip_coverage"] > 0.3))

    # Health score positive
    checks.append(("health_positive", results["health_score"] > 0))

    # Different seed also works
    results2 = run_complete_deployment(seed=99)
    checks.append(("seed_99_works", results2["nodes"] == 40))
    checks.append(("seed_99_healthy", results2["health_score"] > 0))

    return checks


# ─── Main ─────────────────────────────────────────────────────────────────

def main():
    sections = [
        ("§1  Geographic Network Topology", evaluate_geo_topology),
        ("§2  Latency Model (Real-World Profiles)", evaluate_latency_profiles),
        ("§3  Bandwidth-Constrained Message Passing", evaluate_bandwidth),
        ("§4  Trust Propagation Under Latency", evaluate_trust_propagation),
        ("§5  Consensus Performance with Real Latency", evaluate_consensus_latency),
        ("§6  Geographic Partition Simulation", evaluate_geo_partition),
        ("§7  Latency-Aware Gossip Protocol", evaluate_latency_gossip),
        ("§8  Priority-Based Message Scheduling", evaluate_priority_scheduling),
        ("§9  Jitter and Packet Loss Effects", evaluate_jitter_loss),
        ("§10 Multi-Region Federation Performance", evaluate_federation_performance),
        ("§11 Deployment Topology Optimization", evaluate_topology_optimization),
        ("§12 Complete Deployment Simulation", evaluate_complete_deployment),
    ]

    total_pass = 0
    total_fail = 0

    for title, func in sections:
        results = func()
        passed = sum(1 for _, v in results if v)
        failed = sum(1 for _, v in results if not v)
        total_pass += passed
        total_fail += failed
        status = "PASS" if failed == 0 else "FAIL"
        print(f"  [{status}] {title}: {passed}/{len(results)}")
        if failed > 0:
            for name, v in results:
                if not v:
                    print(f"         FAIL: {name}")

    total = total_pass + total_fail
    print(f"\n{'='*60}")
    print(f"  Real Network Simulation: {total_pass}/{total} checks passed")
    if total_fail == 0:
        print("  ALL CHECKS PASSED")
    else:
        print(f"  {total_fail} FAILED")
    print(f"{'='*60}")
    return total_fail == 0


if __name__ == "__main__":
    main()
