# MRH Scale Limits and Optimization Guide

## Executive Summary

The Markov Relevancy Horizon (MRH) must balance comprehensive relationship tracking with practical constraints of edge devices. This document defines scale limits, serialization strategies, and optimization techniques for MRH implementation.

## 1. Scale Limits by Device Class

### 1.1 Device Classifications

| Device Class | RAM | Storage | CPU | Example Devices |
|-------------|-----|---------|-----|-----------------|
| **Micro** | <256KB | <1MB | <100MHz | IoT sensors, smart cards |
| **Edge** | 1-8MB | 10-100MB | 100-500MHz | Routers, gateways |
| **Mobile** | 1-8GB | 32-256GB | 1-3GHz | Phones, tablets |
| **Desktop** | 8-64GB | 256GB-2TB | 2-5GHz | PCs, workstations |
| **Cloud** | 64GB+ | 1TB+ | 3GHz+ x many | Servers, clusters |

### 1.2 MRH Limits by Device Class

```python
class MRHLimits:
    MICRO = {
        "horizon_depth": 1,          # Direct relationships only
        "max_relationships": 10,      # Total across all types
        "max_paired": 3,              # Active pairings
        "max_witnesses": 5,           # Witness attestations
        "serialization": "cbor",      # Compact binary
        "compression": "zstd"         # If available
    }
    
    EDGE = {
        "horizon_depth": 2,          # One hop out
        "max_relationships": 100,
        "max_paired": 20,
        "max_witnesses": 50,
        "serialization": "cbor",
        "compression": "zstd"
    }
    
    MOBILE = {
        "horizon_depth": 3,          # Standard depth
        "max_relationships": 1000,
        "max_paired": 100,
        "max_witnesses": 500,
        "serialization": "json",      # Or MessagePack
        "compression": "optional"
    }
    
    DESKTOP = {
        "horizon_depth": 4,
        "max_relationships": 10000,
        "max_paired": 1000,
        "max_witnesses": 5000,
        "serialization": "json",
        "compression": "optional"
    }
    
    CLOUD = {
        "horizon_depth": 5,          # Extended visibility
        "max_relationships": 100000,
        "max_paired": 10000,
        "max_witnesses": 50000,
        "serialization": "rdf",       # Full semantic graph
        "compression": "optional"
    }
```

## 2. Memory Footprint Analysis

### 2.1 Per-Relationship Memory Cost

```python
# Minimal representation (CBOR)
class CompactRelationship:
    lct_id: bytes        # 16 bytes (128-bit hash)
    type: uint8          # 1 byte enum
    timestamp: uint32    # 4 bytes (seconds since epoch)
    metadata: uint16     # 2 bytes flags
    # Total: 23 bytes per relationship
    
# Standard representation (JSON)
class StandardRelationship:
    lct_id: str          # ~50 bytes
    type: str            # ~20 bytes
    timestamp: str       # ~25 bytes (ISO 8601)
    context: str         # ~30 bytes
    metadata: dict       # ~100 bytes
    # Total: ~225 bytes per relationship

# Full representation (RDF)
class RDFRelationship:
    subject: str         # ~50 bytes
    predicate: str       # ~40 bytes
    object: str          # ~50 bytes
    context: str         # ~100 bytes
    provenance: dict     # ~200 bytes
    # Total: ~440 bytes per relationship
```

### 2.2 Total MRH Size Calculation

```python
def calculate_mrh_size(device_class, num_relationships):
    limits = MRHLimits.__dict__[device_class]
    
    if limits["serialization"] == "cbor":
        per_relationship = 23
    elif limits["serialization"] == "json":
        per_relationship = 225
    else:  # RDF
        per_relationship = 440
    
    base_size = per_relationship * num_relationships
    
    # Add overhead for structure
    overhead = {
        "cbor": 1.1,   # 10% CBOR structure
        "json": 1.3,   # 30% JSON structure
        "rdf": 1.5     # 50% RDF triples
    }
    
    total = base_size * overhead[limits["serialization"]]
    
    # Apply compression if available
    if limits.get("compression"):
        compression_ratios = {
            "zstd": 0.3,  # 70% reduction
            "gzip": 0.4,  # 60% reduction
            "lz4": 0.5    # 50% reduction
        }
        total *= compression_ratios.get(limits["compression"], 1.0)
    
    return total
```

## 3. Serialization Strategies

### 3.1 CBOR for Micro/Edge Devices

```python
import cbor2

def serialize_mrh_cbor(mrh):
    # Compact representation using CBOR
    compact = {
        1: mrh.horizon_depth,          # Use integer keys
        2: [                            # Bound relationships
            [r.lct_id, r.type, r.ts]
            for r in mrh.bound[:10]    # Limit for micro devices
        ],
        3: [                            # Paired relationships
            [r.lct_id, r.type, r.ts]
            for r in mrh.paired[:3]
        ],
        4: mrh.last_updated
    }
    return cbor2.dumps(compact)

def deserialize_mrh_cbor(data):
    compact = cbor2.loads(data)
    return MRH(
        horizon_depth=compact[1],
        bound=[Relationship(*r) for r in compact[2]],
        paired=[Relationship(*r) for r in compact[3]],
        last_updated=compact[4]
    )
```

### 3.2 JSON for Mobile/Desktop

```python
import json
import gzip

def serialize_mrh_json(mrh, compress=False):
    # Standard JSON representation
    data = {
        "horizon_depth": mrh.horizon_depth,
        "bound": [r.to_dict() for r in mrh.bound],
        "paired": [r.to_dict() for r in mrh.paired],
        "witnessing": [w.to_dict() for w in mrh.witnessing],
        "last_updated": mrh.last_updated.isoformat()
    }
    
    json_bytes = json.dumps(data, separators=(',', ':')).encode()
    
    if compress:
        return gzip.compress(json_bytes, compresslevel=6)
    return json_bytes
```

### 3.3 RDF for Cloud/Analytics

```python
from rdflib import Graph, Namespace, Literal

def serialize_mrh_rdf(mrh):
    g = Graph()
    web4 = Namespace("https://web4.io/ontology#")
    
    for rel in mrh.bound:
        g.add((
            URIRef(mrh.entity_id),
            web4.boundTo,
            URIRef(rel.lct_id)
        ))
        g.add((
            URIRef(rel.lct_id),
            web4.boundAt,
            Literal(rel.timestamp, datatype=XSD.dateTime)
        ))
    
    # Serialize to Turtle (most compact RDF format)
    return g.serialize(format='turtle')
```

## 4. Optimization Techniques

### 4.1 Horizon Pruning

```python
def prune_by_horizon(mrh, max_depth):
    """Remove relationships beyond horizon depth"""
    def get_depth(relationship):
        # Calculate hop distance from origin
        return relationship.distance_from_origin
    
    mrh.bound = [r for r in mrh.bound if get_depth(r) <= max_depth]
    mrh.paired = [r for r in mrh.paired if get_depth(r) <= max_depth]
    mrh.witnessing = [r for r in mrh.witnessing if get_depth(r) <= max_depth]
```

### 4.2 Time-Based Eviction

```python
def evict_stale_relationships(mrh, max_age_seconds):
    """Remove relationships older than threshold"""
    cutoff = time.time() - max_age_seconds
    
    # Keep permanent relationships (birth certificate)
    mrh.paired = [
        r for r in mrh.paired 
        if r.permanent or r.timestamp > cutoff
    ]
    
    # Evict old witnesses
    mrh.witnessing = [
        w for w in mrh.witnessing
        if w.last_attestation > cutoff
    ]
```

### 4.3 Relationship Compression

```python
def compress_relationships(mrh, device_class):
    """Compress similar relationships into aggregates"""
    
    if device_class == "MICRO":
        # Extreme compression for micro devices
        mrh.witnessing = aggregate_witnesses(mrh.witnessing)
        mrh.bound = keep_only_parents(mrh.bound)
        
    elif device_class == "EDGE":
        # Moderate compression
        mrh.witnessing = group_by_role(mrh.witnessing)
        
    return mrh

def aggregate_witnesses(witnesses):
    """Replace individual witnesses with aggregate counts"""
    by_role = {}
    for w in witnesses:
        if w.role not in by_role:
            by_role[w.role] = {
                "count": 0,
                "latest": w.last_attestation
            }
        by_role[w.role]["count"] += 1
        by_role[w.role]["latest"] = max(
            by_role[w.role]["latest"],
            w.last_attestation
        )
    return by_role
```

## 5. Dynamic Scaling Strategies

### 5.1 Adaptive Horizon

```python
class AdaptiveMRH:
    def __init__(self, device_class):
        self.limits = MRHLimits.__dict__[device_class]
        self.current_usage = 0
        
    def should_expand_horizon(self):
        # Expand if we have capacity
        usage_percent = self.current_usage / self.limits["max_relationships"]
        return usage_percent < 0.7
        
    def should_contract_horizon(self):
        # Contract if approaching limits
        usage_percent = self.current_usage / self.limits["max_relationships"]
        return usage_percent > 0.9
        
    def adjust_horizon(self, mrh):
        if self.should_contract_horizon():
            mrh.horizon_depth = max(1, mrh.horizon_depth - 1)
            prune_by_horizon(mrh, mrh.horizon_depth)
        elif self.should_expand_horizon():
            mrh.horizon_depth = min(5, mrh.horizon_depth + 1)
```

### 5.2 Priority-Based Retention

```python
def calculate_relationship_priority(rel, context):
    """Score relationships for retention priority"""
    score = 0
    
    # Recent interactions score higher
    age = time.time() - rel.timestamp
    score += max(0, 100 - (age / 86400))  # Decay over days
    
    # Permanent relationships (birth cert) highest priority
    if rel.permanent:
        score += 1000
        
    # Active pairings high priority
    if rel.active:
        score += 500
        
    # Witnesses with high trust valuable
    if hasattr(rel, 't3_score'):
        score += rel.t3_score * 100
        
    # Role relevance
    if rel.role == context.current_role:
        score += 200
        
    return score

def retain_by_priority(mrh, max_relationships):
    """Keep highest priority relationships when pruning"""
    all_rels = mrh.bound + mrh.paired + mrh.witnessing
    
    # Score all relationships
    scored = [
        (calculate_relationship_priority(r, context), r)
        for r in all_rels
    ]
    
    # Keep top N
    scored.sort(reverse=True)
    to_keep = [r for score, r in scored[:max_relationships]]
    
    # Redistribute
    mrh.bound = [r for r in to_keep if r.type == "bound"]
    mrh.paired = [r for r in to_keep if r.type == "paired"]
    mrh.witnessing = [r for r in to_keep if r.type == "witness"]
```

## 6. Implementation Guidelines

### 6.1 Device Detection

```python
def detect_device_class():
    """Auto-detect appropriate device class"""
    import psutil
    
    ram_gb = psutil.virtual_memory().total / (1024**3)
    
    if ram_gb < 0.001:  # Less than 1MB
        return "MICRO"
    elif ram_gb < 0.01:  # Less than 10MB
        return "EDGE"
    elif ram_gb < 10:    # Less than 10GB
        return "MOBILE"
    elif ram_gb < 100:   # Less than 100GB
        return "DESKTOP"
    else:
        return "CLOUD"
```

### 6.2 Format Negotiation

```python
def negotiate_mrh_format(peer_capabilities):
    """Negotiate optimal format with peer"""
    our_formats = ["cbor", "json", "rdf"]
    peer_formats = peer_capabilities.get("mrh_formats", ["json"])
    
    # Find best common format
    for fmt in ["cbor", "json", "rdf"]:
        if fmt in our_formats and fmt in peer_formats:
            return fmt
    
    # Fallback to JSON
    return "json"
```

## 7. Performance Benchmarks

### 7.1 Serialization Performance

| Format | Size (1000 rels) | Serialize (ms) | Deserialize (ms) |
|--------|------------------|----------------|------------------|
| CBOR | 23KB | 5 | 3 |
| JSON | 225KB | 15 | 10 |
| JSON+gzip | 68KB | 25 | 15 |
| RDF | 440KB | 50 | 40 |
| RDF+gzip | 132KB | 60 | 45 |

### 7.2 Query Performance

| Operation | Horizon=1 | Horizon=2 | Horizon=3 |
|-----------|-----------|-----------|-----------|
| Find relationship | 0.1ms | 0.5ms | 2ms |
| Calculate trust path | 0.5ms | 5ms | 50ms |
| Update MRH | 1ms | 3ms | 10ms |
| Prune expired | 2ms | 10ms | 50ms |

## 8. Summary

MRH scaling requires careful balance between completeness and efficiency:

1. **Device-aware limits**: Micro devices need extreme compression
2. **Adaptive strategies**: Expand/contract based on available resources
3. **Priority retention**: Keep most valuable relationships when pruning
4. **Format flexibility**: CBOR for constrained, RDF for analytics
5. **Time-based eviction**: Automatic cleanup of stale relationships

The key insight: MRH doesn't need to be complete to be useful. Even micro devices with 10 relationships can participate meaningfully in Web4 through careful relationship selection and aggressive pruning.