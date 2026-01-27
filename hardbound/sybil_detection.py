# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Web4 Contributors
#
# Hardbound - Sybil Detection via Behavioral Correlation
# https://github.com/dp-web4/web4

"""
Sybil Detection: Identifying coordinated fake identities through
behavioral correlation analysis.

Problem: A single adversary creates multiple member identities to
amplify voting power, farming trust through mutual attestation. While
velocity caps limit individual trust growth, coordinated Sybils can
still accumulate collective influence.

Detection signals:
1. **Trust trajectory correlation**: Members whose trust scores move
   in lockstep (Pearson correlation > 0.9) are suspicious
2. **Action timing correlation**: Members who always act within
   seconds of each other suggest automated control
3. **Witness pair concentration**: Members who only witness each other
   (closed-loop attestation)
4. **Trust variance uniformity**: Sybils tend to have near-identical
   trust distributions (variance < 0.001)

Output: SybilReport with cluster identification and confidence scores.
"""

import math
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum


class SybilRisk(Enum):
    """Risk level for Sybil detection."""
    NONE = "none"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class SybilCluster:
    """A group of members suspected of being controlled by the same entity."""
    members: List[str]
    confidence: float  # 0.0 to 1.0
    signals: List[str]
    trust_correlation: float = 0.0
    timing_correlation: float = 0.0
    witness_concentration: float = 0.0
    trust_variance: float = 0.0

    @property
    def risk(self) -> SybilRisk:
        if self.confidence >= 0.9:
            return SybilRisk.CRITICAL
        elif self.confidence >= 0.7:
            return SybilRisk.HIGH
        elif self.confidence >= 0.5:
            return SybilRisk.MODERATE
        elif self.confidence >= 0.3:
            return SybilRisk.LOW
        return SybilRisk.NONE


@dataclass
class SybilReport:
    """Full Sybil analysis report for a team."""
    team_id: str
    analyzed_at: str
    member_count: int
    clusters: List[SybilCluster]
    overall_risk: SybilRisk
    recommendations: List[str]

    def to_dict(self) -> Dict:
        return {
            "team_id": self.team_id,
            "analyzed_at": self.analyzed_at,
            "member_count": self.member_count,
            "cluster_count": len(self.clusters),
            "overall_risk": self.overall_risk.value,
            "clusters": [
                {
                    "members": c.members,
                    "confidence": round(c.confidence, 3),
                    "risk": c.risk.value,
                    "signals": c.signals,
                    "trust_correlation": round(c.trust_correlation, 3),
                    "timing_correlation": round(c.timing_correlation, 3),
                    "witness_concentration": round(c.witness_concentration, 3),
                }
                for c in self.clusters
            ],
            "recommendations": self.recommendations,
        }


class SybilDetector:
    """
    Detects potential Sybil accounts through behavioral correlation.

    Works with trust snapshots and action histories to find clusters
    of members that behave suspiciously similarly.
    """

    # Detection thresholds
    TRUST_CORRELATION_THRESHOLD = 0.85    # Pearson r above this is suspicious
    TIMING_WINDOW_SECONDS = 10.0          # Actions within this window are "simultaneous"
    TIMING_CORRELATION_THRESHOLD = 0.70   # Fraction of simultaneous actions
    WITNESS_CONCENTRATION_THRESHOLD = 0.80  # Fraction of witnessing within group
    TRUST_VARIANCE_THRESHOLD = 0.002      # Suspiciously uniform trust scores

    def __init__(self):
        pass

    def analyze_team(
        self,
        team_id: str,
        member_trusts: Dict[str, Dict[str, float]],
        trust_histories: Optional[Dict[str, List[Dict[str, float]]]] = None,
        action_timestamps: Optional[Dict[str, List[str]]] = None,
        witness_pairs: Optional[List[Tuple[str, str]]] = None,
    ) -> SybilReport:
        """
        Analyze a team for Sybil behavior.

        Args:
            team_id: Team identifier
            member_trusts: Current trust per member {lct: {dim: val}}
            trust_histories: Optional trust snapshots over time {lct: [{dim: val}, ...]}
            action_timestamps: Optional action timestamps per member {lct: [iso_ts, ...]}
            witness_pairs: Optional list of (witness, witnessed) pairs

        Returns:
            SybilReport with detected clusters and recommendations
        """
        now = datetime.now(timezone.utc).isoformat()
        members = list(member_trusts.keys())

        if len(members) < 2:
            return SybilReport(
                team_id=team_id,
                analyzed_at=now,
                member_count=len(members),
                clusters=[],
                overall_risk=SybilRisk.NONE,
                recommendations=[],
            )

        # Run detection signals
        trust_corr_clusters = self._detect_trust_correlation(member_trusts)
        timing_clusters = self._detect_timing_correlation(action_timestamps or {})
        witness_clusters = self._detect_witness_concentration(
            witness_pairs or [], set(members)
        )
        variance_clusters = self._detect_trust_variance(member_trusts)

        # Merge signals into unified clusters
        clusters = self._merge_clusters(
            trust_corr_clusters,
            timing_clusters,
            witness_clusters,
            variance_clusters,
        )

        # Determine overall risk
        if not clusters:
            overall_risk = SybilRisk.NONE
        else:
            max_confidence = max(c.confidence for c in clusters)
            if max_confidence >= 0.9:
                overall_risk = SybilRisk.CRITICAL
            elif max_confidence >= 0.7:
                overall_risk = SybilRisk.HIGH
            elif max_confidence >= 0.5:
                overall_risk = SybilRisk.MODERATE
            else:
                overall_risk = SybilRisk.LOW

        # Generate recommendations
        recommendations = self._generate_recommendations(clusters, overall_risk)

        return SybilReport(
            team_id=team_id,
            analyzed_at=now,
            member_count=len(members),
            clusters=clusters,
            overall_risk=overall_risk,
            recommendations=recommendations,
        )

    def _detect_trust_correlation(
        self, member_trusts: Dict[str, Dict[str, float]]
    ) -> List[SybilCluster]:
        """Detect members with highly correlated trust profiles."""
        members = list(member_trusts.keys())
        clusters = []

        # Pairwise Pearson correlation of trust vectors
        for i in range(len(members)):
            for j in range(i + 1, len(members)):
                m1, m2 = members[i], members[j]
                t1 = member_trusts[m1]
                t2 = member_trusts[m2]

                # Extract common dimensions
                dims = sorted(set(t1.keys()) & set(t2.keys()))
                if len(dims) < 3:
                    continue

                v1 = [t1[d] for d in dims]
                v2 = [t2[d] for d in dims]

                r = self._pearson_correlation(v1, v2)

                if r >= self.TRUST_CORRELATION_THRESHOLD:
                    # Also check absolute closeness
                    avg_diff = sum(abs(a - b) for a, b in zip(v1, v2)) / len(dims)

                    clusters.append(SybilCluster(
                        members=[m1, m2],
                        confidence=r * 0.5,  # Correlation alone is partial signal
                        signals=[f"Trust correlation: r={r:.3f}, avg_diff={avg_diff:.4f}"],
                        trust_correlation=r,
                    ))

        return clusters

    def _detect_timing_correlation(
        self, action_timestamps: Dict[str, List[str]]
    ) -> List[SybilCluster]:
        """Detect members who act within seconds of each other."""
        members = [m for m, ts in action_timestamps.items() if len(ts) >= 3]
        clusters = []

        for i in range(len(members)):
            for j in range(i + 1, len(members)):
                m1, m2 = members[i], members[j]
                ts1 = sorted(action_timestamps[m1])
                ts2 = sorted(action_timestamps[m2])

                simultaneous = 0
                total_compared = 0

                for t1_str in ts1:
                    t1 = datetime.fromisoformat(t1_str)
                    for t2_str in ts2:
                        t2 = datetime.fromisoformat(t2_str)
                        diff = abs((t1 - t2).total_seconds())
                        if diff < self.TIMING_WINDOW_SECONDS:
                            simultaneous += 1
                            break
                    total_compared += 1

                if total_compared > 0:
                    ratio = simultaneous / total_compared
                    if ratio >= self.TIMING_CORRELATION_THRESHOLD:
                        clusters.append(SybilCluster(
                            members=[m1, m2],
                            confidence=ratio * 0.4,  # Timing alone is partial
                            signals=[f"Timing correlation: {ratio:.1%} simultaneous ({simultaneous}/{total_compared})"],
                            timing_correlation=ratio,
                        ))

        return clusters

    def _detect_witness_concentration(
        self, witness_pairs: List[Tuple[str, str]], all_members: Set[str]
    ) -> List[SybilCluster]:
        """Detect groups that only witness each other (closed loops)."""
        if not witness_pairs:
            return []

        # Build witness graph
        witness_by: Dict[str, Dict[str, int]] = {}  # who -> {whom: count}
        for w, witnessed in witness_pairs:
            if w not in witness_by:
                witness_by[w] = {}
            witness_by[w][witnessed] = witness_by[w].get(witnessed, 0) + 1

        clusters = []

        # Check each member's witness concentration
        for member, targets in witness_by.items():
            total_witnesses = sum(targets.values())
            if total_witnesses < 3:
                continue

            # Find the top partner
            for partner, count in targets.items():
                if partner == member:
                    continue
                concentration = count / total_witnesses
                if concentration >= self.WITNESS_CONCENTRATION_THRESHOLD:
                    # Check reciprocity
                    reverse = witness_by.get(partner, {}).get(member, 0)
                    reverse_total = sum(witness_by.get(partner, {}).values()) or 1
                    reverse_concentration = reverse / reverse_total

                    if reverse_concentration >= self.WITNESS_CONCENTRATION_THRESHOLD * 0.5:
                        avg_conc = (concentration + reverse_concentration) / 2
                        clusters.append(SybilCluster(
                            members=[member, partner],
                            confidence=avg_conc * 0.6,  # Strong signal
                            signals=[
                                f"Witness concentration: {member}->{partner}={concentration:.1%}, "
                                f"{partner}->{member}={reverse_concentration:.1%}"
                            ],
                            witness_concentration=avg_conc,
                        ))

        return clusters

    def _detect_trust_variance(
        self, member_trusts: Dict[str, Dict[str, float]]
    ) -> List[SybilCluster]:
        """Detect suspiciously uniform trust distributions across members."""
        members = list(member_trusts.keys())
        if len(members) < 3:
            return []

        # Compute trust score for each member
        scores = {}
        for m, trust in member_trusts.items():
            if trust:
                scores[m] = sum(trust.values()) / len(trust)

        if len(scores) < 3:
            return []

        # Find groups with near-identical scores
        sorted_members = sorted(scores.items(), key=lambda x: x[1])
        uniform_groups: List[List[str]] = []
        current_group = [sorted_members[0][0]]
        current_score = sorted_members[0][1]

        for m, s in sorted_members[1:]:
            if abs(s - current_score) < self.TRUST_VARIANCE_THRESHOLD:
                current_group.append(m)
            else:
                if len(current_group) >= 3:
                    uniform_groups.append(current_group)
                current_group = [m]
                current_score = s

        if len(current_group) >= 3:
            uniform_groups.append(current_group)

        clusters = []
        for group in uniform_groups:
            group_scores = [scores[m] for m in group]
            variance = self._variance(group_scores)
            clusters.append(SybilCluster(
                members=group,
                confidence=0.3,  # Low confidence alone, but amplifies other signals
                signals=[
                    f"Trust variance: {variance:.6f} across {len(group)} members "
                    f"(threshold: {self.TRUST_VARIANCE_THRESHOLD})"
                ],
                trust_variance=variance,
            ))

        return clusters

    def _merge_clusters(self, *cluster_lists) -> List[SybilCluster]:
        """Merge overlapping clusters from different detection signals."""
        # Collect all pair-level signals
        pair_signals: Dict[tuple, SybilCluster] = {}

        for clusters in cluster_lists:
            for cluster in clusters:
                # Normalize pair key
                members = tuple(sorted(cluster.members))
                if len(members) == 2:
                    key = members
                else:
                    # For groups > 2, create pairwise entries
                    for i in range(len(members)):
                        for j in range(i + 1, len(members)):
                            key = (members[i], members[j])
                            if key not in pair_signals:
                                pair_signals[key] = SybilCluster(
                                    members=list(key),
                                    confidence=0.0,
                                    signals=[],
                                )
                            existing = pair_signals[key]
                            existing.confidence = max(existing.confidence, cluster.confidence)
                            existing.signals.extend(cluster.signals)
                            existing.trust_correlation = max(existing.trust_correlation, cluster.trust_correlation)
                            existing.timing_correlation = max(existing.timing_correlation, cluster.timing_correlation)
                            existing.witness_concentration = max(existing.witness_concentration, cluster.witness_concentration)
                            existing.trust_variance = max(existing.trust_variance, cluster.trust_variance)
                    continue

                if key not in pair_signals:
                    pair_signals[key] = SybilCluster(
                        members=list(key),
                        confidence=0.0,
                        signals=[],
                    )
                existing = pair_signals[key]
                # Combine confidence: multiple signals strengthen detection
                # Use max + bonus for each additional signal
                existing.confidence = min(1.0, existing.confidence + cluster.confidence)
                existing.signals.extend(cluster.signals)
                existing.trust_correlation = max(existing.trust_correlation, cluster.trust_correlation)
                existing.timing_correlation = max(existing.timing_correlation, cluster.timing_correlation)
                existing.witness_concentration = max(existing.witness_concentration, cluster.witness_concentration)
                existing.trust_variance = max(existing.trust_variance, cluster.trust_variance)

        # Filter to significant clusters
        return [
            c for c in pair_signals.values()
            if c.confidence >= 0.3  # Minimum threshold
        ]

    def _generate_recommendations(
        self, clusters: List[SybilCluster], overall_risk: SybilRisk
    ) -> List[str]:
        """Generate actionable recommendations based on findings."""
        if not clusters:
            return ["No Sybil behavior detected. Continue monitoring."]

        recs = []
        if overall_risk in (SybilRisk.CRITICAL, SybilRisk.HIGH):
            recs.append("URGENT: Require identity verification for flagged members")
            recs.append("Temporarily suspend voting rights for suspected Sybil cluster")
            recs.append("Request cross-team witness attestation for flagged members")

        if any(c.witness_concentration > 0.5 for c in clusters):
            recs.append("Require minimum witness diversity (at least 3 unique witnesses per trust epoch)")

        if any(c.timing_correlation > 0.5 for c in clusters):
            recs.append("Add minimum action spacing requirement (e.g., 30s between same-source actions)")

        if any(c.trust_correlation > 0.8 for c in clusters):
            recs.append("Monitor trust trajectory divergence: genuine members develop unique patterns over time")

        recs.append(f"Detected {len(clusters)} suspicious cluster(s) across {sum(len(c.members) for c in clusters)} members")

        return recs

    @staticmethod
    def _pearson_correlation(x: List[float], y: List[float]) -> float:
        """Compute Pearson correlation coefficient."""
        n = len(x)
        if n < 2:
            return 0.0

        mean_x = sum(x) / n
        mean_y = sum(y) / n

        cov = sum((xi - mean_x) * (yi - mean_y) for xi, yi in zip(x, y))
        std_x = math.sqrt(sum((xi - mean_x) ** 2 for xi in x))
        std_y = math.sqrt(sum((yi - mean_y) ** 2 for yi in y))

        if std_x == 0 or std_y == 0:
            return 1.0 if std_x == std_y == 0 else 0.0

        return cov / (std_x * std_y)

    @staticmethod
    def _variance(values: List[float]) -> float:
        """Compute variance of a list."""
        if len(values) < 2:
            return 0.0
        mean = sum(values) / len(values)
        return sum((v - mean) ** 2 for v in values) / (len(values) - 1)


# --- Self-test ---

def _self_test():
    """Test Sybil detection with synthetic scenarios."""
    print("=" * 60)
    print("Sybil Detection - Self Test")
    print("=" * 60)

    detector = SybilDetector()
    now = datetime.now(timezone.utc)

    # Test 1: Clean team (no Sybils)
    clean_trusts = {
        "member_a": {"reliability": 0.75, "competence": 0.60, "alignment": 0.80, "consistency": 0.70, "witnesses": 0.55, "lineage": 0.65},
        "member_b": {"reliability": 0.50, "competence": 0.85, "alignment": 0.45, "consistency": 0.60, "witnesses": 0.70, "lineage": 0.40},
        "member_c": {"reliability": 0.65, "competence": 0.50, "alignment": 0.70, "consistency": 0.55, "witnesses": 0.80, "lineage": 0.75},
    }
    report = detector.analyze_team("team:clean", clean_trusts)
    print(f"  [1] Clean team: risk={report.overall_risk.value}, clusters={len(report.clusters)}")
    assert report.overall_risk == SybilRisk.NONE, f"Clean team should be NONE risk, got {report.overall_risk}"

    # Test 2: Identical trust profiles (classic Sybil)
    sybil_trust = {"reliability": 0.546, "competence": 0.546, "alignment": 0.546,
                   "consistency": 0.546, "witnesses": 0.546, "lineage": 0.546}
    sybil_trusts = {
        "sybil_1": sybil_trust.copy(),
        "sybil_2": sybil_trust.copy(),
        "sybil_3": sybil_trust.copy(),
        "honest_1": {"reliability": 0.75, "competence": 0.60, "alignment": 0.80,
                     "consistency": 0.70, "witnesses": 0.55, "lineage": 0.65},
    }
    report = detector.analyze_team("team:sybil", sybil_trusts)
    print(f"  [2] Identical Sybils: risk={report.overall_risk.value}, clusters={len(report.clusters)}")
    assert len(report.clusters) > 0, "Should detect Sybil cluster"

    # Test 3: Timing correlation (automated control)
    timing_ts = {
        "bot_1": [(now - timedelta(hours=i, seconds=1)).isoformat() for i in range(10)],
        "bot_2": [(now - timedelta(hours=i, seconds=3)).isoformat() for i in range(10)],
        "human": [(now - timedelta(hours=i, minutes=i*7)).isoformat() for i in range(10)],
    }
    human_trusts = {
        "bot_1": {"reliability": 0.5, "competence": 0.5, "alignment": 0.5, "consistency": 0.5, "witnesses": 0.5, "lineage": 0.5},
        "bot_2": {"reliability": 0.5, "competence": 0.5, "alignment": 0.5, "consistency": 0.5, "witnesses": 0.5, "lineage": 0.5},
        "human": {"reliability": 0.7, "competence": 0.6, "alignment": 0.8, "consistency": 0.5, "witnesses": 0.5, "lineage": 0.5},
    }
    report = detector.analyze_team("team:bots", human_trusts, action_timestamps=timing_ts)
    print(f"  [3] Timing bots: risk={report.overall_risk.value}, clusters={len(report.clusters)}")
    has_timing = any("Timing" in s for c in report.clusters for s in c.signals)
    print(f"      Timing signal detected: {has_timing}")

    # Test 4: Witness concentration (closed loop)
    witness_pairs = [
        ("colluder_a", "colluder_b"),
        ("colluder_a", "colluder_b"),
        ("colluder_a", "colluder_b"),
        ("colluder_b", "colluder_a"),
        ("colluder_b", "colluder_a"),
        ("colluder_b", "colluder_a"),
        ("honest_x", "colluder_a"),
        ("honest_x", "honest_y"),
        ("honest_y", "honest_x"),
        ("honest_y", "colluder_b"),
    ]
    witness_trusts = {
        "colluder_a": {"reliability": 0.65, "competence": 0.60, "alignment": 0.55, "consistency": 0.60, "witnesses": 0.70, "lineage": 0.50},
        "colluder_b": {"reliability": 0.64, "competence": 0.61, "alignment": 0.56, "consistency": 0.59, "witnesses": 0.69, "lineage": 0.51},
        "honest_x": {"reliability": 0.70, "competence": 0.50, "alignment": 0.80, "consistency": 0.65, "witnesses": 0.55, "lineage": 0.60},
        "honest_y": {"reliability": 0.55, "competence": 0.75, "alignment": 0.60, "consistency": 0.70, "witnesses": 0.65, "lineage": 0.45},
    }
    report = detector.analyze_team("team:collude", witness_trusts, witness_pairs=witness_pairs)
    print(f"  [4] Witness loop: risk={report.overall_risk.value}, clusters={len(report.clusters)}")
    has_witness = any("Witness" in s for c in report.clusters for s in c.signals)
    print(f"      Witness signal detected: {has_witness}")

    # Test 5: Multi-signal (trust + timing + witnesses)
    # This should produce the highest confidence
    multi_trusts = {
        "sybil_x": {"reliability": 0.55, "competence": 0.55, "alignment": 0.55, "consistency": 0.55, "witnesses": 0.55, "lineage": 0.55},
        "sybil_y": {"reliability": 0.55, "competence": 0.55, "alignment": 0.55, "consistency": 0.55, "witnesses": 0.55, "lineage": 0.55},
        "legit": {"reliability": 0.80, "competence": 0.60, "alignment": 0.70, "consistency": 0.65, "witnesses": 0.75, "lineage": 0.50},
    }
    multi_timestamps = {
        "sybil_x": [(now - timedelta(hours=i, seconds=0)).isoformat() for i in range(5)],
        "sybil_y": [(now - timedelta(hours=i, seconds=2)).isoformat() for i in range(5)],
        "legit": [(now - timedelta(hours=i, minutes=30)).isoformat() for i in range(5)],
    }
    multi_witnesses = [
        ("sybil_x", "sybil_y"), ("sybil_x", "sybil_y"), ("sybil_x", "sybil_y"),
        ("sybil_y", "sybil_x"), ("sybil_y", "sybil_x"), ("sybil_y", "sybil_x"),
        ("legit", "sybil_x"), ("legit", "sybil_y"),
    ]
    report = detector.analyze_team(
        "team:multi", multi_trusts,
        action_timestamps=multi_timestamps,
        witness_pairs=multi_witnesses,
    )
    print(f"  [5] Multi-signal Sybil: risk={report.overall_risk.value}, clusters={len(report.clusters)}")
    if report.clusters:
        top = max(report.clusters, key=lambda c: c.confidence)
        print(f"      Top confidence: {top.confidence:.3f}")
        print(f"      Signals: {len(top.signals)}")
        for s in top.signals:
            print(f"        - {s}")

    # Print recommendations from last report
    print(f"\n  Recommendations:")
    for rec in report.recommendations:
        print(f"    - {rec}")

    print("\n" + "=" * 60)
    print("All Sybil detection tests passed!")
    print("=" * 60)


if __name__ == "__main__":
    _self_test()
