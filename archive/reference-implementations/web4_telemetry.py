"""
Web4 Production Telemetry and Monitoring
========================================

Production telemetry system for Web4 infrastructure monitoring.

Tracks:
- Authorization decisions (grant/deny rates)
- Attack mitigation triggers  
- Trust score queries
- LCT identity operations
- ATP transactions
- Witness attestations
- Performance metrics

Enables:
- Real-time monitoring dashboards
- Security incident detection
- Performance optimization
- Capacity planning
- Audit trail

Author: Legion Autonomous Research
Date: 2025-12-07
Track: 21 (Production Deployment Preparation)
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
from collections import defaultdict
import time
import json


@dataclass
class MetricPoint:
    """Single telemetry metric data point"""
    metric_name: str
    value: float
    timestamp: float = field(default_factory=time.time)
    tags: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "metric": self.metric_name,
            "value": self.value,
            "timestamp": self.timestamp,
            "tags": self.tags
        }


@dataclass
class SecurityEvent:
    """Security-relevant event"""
    event_type: str
    severity: str  # info, warning, critical
    description: str
    actor_lct: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict:
        return {
            "type": self.event_type,
            "severity": self.severity,
            "description": self.description,
            "actor": self.actor_lct,
            "details": self.details,
            "timestamp": self.timestamp
        }


class Web4Telemetry:
    """
    Central telemetry system for Web4 infrastructure
    
    Collects metrics from all Web4 components and provides
    real-time monitoring, alerting, and audit capabilities.
    """
    
    def __init__(self, society_id: str):
        self.society_id = society_id
        self.start_time = time.time()
        
        # Metric storage (in-memory for now, would use TimeSeries DB in production)
        self.metrics: List[MetricPoint] = []
        self.security_events: List[SecurityEvent] = []
        
        # Counters for common metrics
        self.counters = defaultdict(int)
        
        # Gauges for current state
        self.gauges: Dict[str, float] = {}
        
        # Performance histograms
        self.histograms = defaultdict(list)
    
    # ========================================================================
    # Authorization Metrics
    # ========================================================================
    
    def record_authorization_decision(
        self,
        decision: str,  # granted, denied, deferred
        action: str,
        requester_lct: str,
        denial_reason: Optional[str] = None,
        trust_score: Optional[float] = None,
        atp_cost: Optional[int] = None
    ):
        """Record authorization decision"""
        self.counters[f"auth_decision_{decision}"] += 1
        self.counters[f"auth_action_{action}"] += 1
        
        # Record metric
        self.metrics.append(MetricPoint(
            metric_name="authorization_decision",
            value=1.0,
            tags={
                "decision": decision,
                "action": action,
                "requester": requester_lct
            }
        ))
        
        # Record trust score if available
        if trust_score is not None:
            self.metrics.append(MetricPoint(
                metric_name="trust_score",
                value=trust_score,
                tags={"requester": requester_lct, "action": action}
            ))
        
        # Record denial as security event if denied
        if decision == "denied":
            self.security_events.append(SecurityEvent(
                event_type="authorization_denied",
                severity="warning",
                description=f"Authorization denied for {action}",
                actor_lct=requester_lct,
                details={"reason": denial_reason, "action": action}
            ))
    
    # ========================================================================
    # Attack Mitigation Metrics
    # ========================================================================
    
    def record_mitigation_trigger(
        self,
        mitigation_id: int,  # 1-8
        mitigation_name: str,
        actor_lct: str,
        details: Dict[str, Any]
    ):
        """Record attack mitigation being triggered"""
        self.counters[f"mitigation_{mitigation_id}_triggered"] += 1
        
        self.security_events.append(SecurityEvent(
            event_type=f"mitigation_{mitigation_id}",
            severity="warning",
            description=f"Attack mitigation triggered: {mitigation_name}",
            actor_lct=actor_lct,
            details=details
        ))
        
        print(f"⚠️  Mitigation #{mitigation_id} triggered: {mitigation_name} (actor: {actor_lct})")
    
    # ========================================================================
    # Trust Oracle Metrics
    # ========================================================================
    
    def record_trust_query(
        self,
        lct_id: str,
        trust_score: float,
        cache_hit: bool,
        query_time_ms: float
    ):
        """Record trust score query"""
        self.counters["trust_queries_total"] += 1
        if cache_hit:
            self.counters["trust_cache_hits"] += 1
        else:
            self.counters["trust_cache_misses"] += 1
            
        self.histograms["trust_query_latency_ms"].append(query_time_ms)
        
        self.metrics.append(MetricPoint(
            metric_name="trust_query_latency",
            value=query_time_ms,
            tags={"cache_hit": str(cache_hit)}
        ))
    
    # ========================================================================
    # LCT Registry Metrics
    # ========================================================================
    
    def record_lct_minted(
        self,
        lct_id: str,
        entity_type: str,
        lineage: Optional[List[str]] = None
    ):
        """Record new LCT creation"""
        self.counters["lcts_minted"] += 1
        self.counters[f"lcts_type_{entity_type}"] += 1
        
        self.security_events.append(SecurityEvent(
            event_type="lct_minted",
            severity="info",
            description=f"New LCT minted: {lct_id}",
            details={"entity_type": entity_type, "lineage": lineage}
        ))
    
    # ========================================================================
    # ATP Transaction Metrics
    # ========================================================================
    
    def record_atp_transaction(
        self,
        from_lct: str,
        to_lct: str,
        amount: int,
        transaction_type: str,  # transfer, demurrage, delegation
        success: bool
    ):
        """Record ATP transaction"""
        self.counters["atp_transactions"] += 1
        if success:
            self.counters["atp_transactions_success"] += 1
        else:
            self.counters["atp_transactions_failed"] += 1
            
        self.histograms["atp_transfer_amounts"].append(amount)
        
        self.metrics.append(MetricPoint(
            metric_name="atp_transaction",
            value=float(amount),
            tags={
                "type": transaction_type,
                "success": str(success),
                "from": from_lct,
                "to": to_lct
            }
        ))
    
    # ========================================================================
    # Witness Metrics
    # ========================================================================
    
    def record_witness_attestation(
        self,
        witness_did: str,
        attestation_type: str,
        verified: bool,
        reputation_score: Optional[float] = None
    ):
        """Record witness attestation"""
        self.counters["witness_attestations"] += 1
        if verified:
            self.counters["witness_attestations_verified"] += 1
        else:
            self.counters["witness_attestations_failed"] += 1
            
        if reputation_score is not None:
            self.metrics.append(MetricPoint(
                metric_name="witness_reputation",
                value=reputation_score,
                tags={"witness": witness_did}
            ))
    
    # ========================================================================
    # Performance Metrics
    # ========================================================================
    
    def record_operation_latency(
        self,
        operation: str,
        latency_ms: float,
        tags: Optional[Dict[str, str]] = None
    ):
        """Record operation latency"""
        if tags is None:
            tags = {}
            
        self.histograms[f"latency_{operation}"].append(latency_ms)
        
        self.metrics.append(MetricPoint(
            metric_name=f"{operation}_latency",
            value=latency_ms,
            tags=tags
        ))
    
    # ========================================================================
    # Query and Reporting
    # ========================================================================
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of all metrics"""
        runtime = time.time() - self.start_time
        
        # Calculate cache hit rate
        total_queries = self.counters.get("trust_queries_total", 0)
        cache_hits = self.counters.get("trust_cache_hits", 0)
        cache_hit_rate = (cache_hits / total_queries * 100) if total_queries > 0 else 0
        
        # Calculate auth success rate
        granted = self.counters.get("auth_decision_granted", 0)
        denied = self.counters.get("auth_decision_denied", 0)
        total_auth = granted + denied
        auth_success_rate = (granted / total_auth * 100) if total_auth > 0 else 0
        
        return {
            "society_id": self.society_id,
            "runtime_seconds": runtime,
            
            "authorization": {
                "total_decisions": total_auth,
                "granted": granted,
                "denied": denied,
                "success_rate_pct": auth_success_rate
            },
            
            "trust_oracle": {
                "total_queries": total_queries,
                "cache_hits": cache_hits,
                "cache_hit_rate_pct": cache_hit_rate
            },
            
            "lct_registry": {
                "lcts_minted": self.counters.get("lcts_minted", 0),
            },
            
            "atp": {
                "total_transactions": self.counters.get("atp_transactions", 0),
                "successful": self.counters.get("atp_transactions_success", 0),
                "failed": self.counters.get("atp_transactions_failed", 0)
            },
            
            "witness": {
                "total_attestations": self.counters.get("witness_attestations", 0),
                "verified": self.counters.get("witness_attestations_verified", 0),
                "failed": self.counters.get("witness_attestations_failed", 0)
            },
            
            "security": {
                "events": len(self.security_events),
                "critical": len([e for e in self.security_events if e.severity == "critical"]),
                "warnings": len([e for e in self.security_events if e.severity == "warning"])
            },
            
            "mitigations_triggered": {
                f"mitigation_{i}": self.counters.get(f"mitigation_{i}_triggered", 0)
                for i in range(1, 9)
            }
        }
    
    def get_security_events(
        self,
        severity: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """Get recent security events"""
        events = self.security_events[-limit:]
        
        if severity:
            events = [e for e in events if e.severity == severity]
            
        return [e.to_dict() for e in events]
    
    def export_metrics(self, filepath: str):
        """Export metrics to JSON file"""
        export_data = {
            "summary": self.get_metrics_summary(),
            "metrics": [m.to_dict() for m in self.metrics[-1000:]],  # Last 1000 metrics
            "security_events": [e.to_dict() for e in self.security_events[-100:]],  # Last 100 events
            "exported_at": time.time()
        }
        
        with open(filepath, 'w') as f:
            json.dump(export_data, f, indent=2)
            
        print(f"✅ Metrics exported to {filepath}")


# Example usage
if __name__ == "__main__":
    print("=" * 70)
    print("  Web4 Production Telemetry System")
    print("=" * 70)
    
    telemetry = Web4Telemetry("society:demo")
    
    # Simulate some activity
    print("\nSimulating Web4 activity...")
    
    # Authorization events
    telemetry.record_authorization_decision(
        decision="granted",
        action="read",
        requester_lct="lct:user:001",
        trust_score=0.85
    )
    
    telemetry.record_authorization_decision(
        decision="denied",
        action="transfer_funds",
        requester_lct="lct:user:002",
        denial_reason="insufficient_trust",
        trust_score=0.45
    )
    
    # Mitigation triggers
    telemetry.record_mitigation_trigger(
        mitigation_id=4,
        mitigation_name="Budget Fragmentation Prevention",
        actor_lct="lct:agent:001",
        details={"atp_cost": 0.1, "min_required": 1}
    )
    
    # Trust queries
    telemetry.record_trust_query(
        lct_id="lct:user:001",
        trust_score=0.85,
        cache_hit=True,
        query_time_ms=2.5
    )
    
    # LCT minting
    telemetry.record_lct_minted(
        lct_id="lct:web4:ai:society:demo:1",
        entity_type="AI",
        lineage=["dp", "autonomous"]
    )
    
    # ATP transactions
    telemetry.record_atp_transaction(
        from_lct="lct:user:001",
        to_lct="lct:user:002",
        amount=100,
        transaction_type="transfer",
        success=True
    )
    
    # Display metrics
    print("\n" + "=" * 70)
    print("Metrics Summary")
    print("=" * 70)
    summary = telemetry.get_metrics_summary()
    print(json.dumps(summary, indent=2))
    
    # Display security events
    print("\n" + "=" * 70)
    print("Recent Security Events")
    print("=" * 70)
    events = telemetry.get_security_events(limit=10)
    for event in events:
        print(f"\n[{event['severity'].upper()}] {event['type']}")
        print(f"  {event['description']}")
        if event.get('actor'):
            print(f"  Actor: {event['actor']}")
    
    # Export
    export_path = "/tmp/web4_telemetry_export.json"
    telemetry.export_metrics(export_path)
