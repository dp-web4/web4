#!/usr/bin/env python3
"""
Advanced Audit Certification — Multi-Party Quorum, Fractal Composition, ATP Incentives

Extends the base audit certification chain with:
  1. Multi-party audit attestation — m-of-n quorum of auditors must sign
  2. Fractal audit composition — sub-entity audits compose into parent audits
  3. ATP-backed audit incentives — stake, reward, and penalty for auditors
  4. Audit challenge protocol — dispute mechanism with ATP stakes
  5. Cross-federation audit sync — hash-anchored audit records across federations

Builds on: audit_certification_chain.py (81/81 checks)
Session: Legion Autonomous 2026-02-26 (Session 10, Track 5)
"""

import hashlib
import json
import math
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Optional


# ═══════════════════════════════════════════════════════════════
# SHARED DATA MODEL (from base audit chain, simplified)
# ═══════════════════════════════════════════════════════════════

class ComplianceLevel(Enum):
    FULL = "fully_compliant"
    SUBSTANTIAL = "substantially_compliant"
    PARTIAL = "partially_compliant"
    NON_COMPLIANT = "non_compliant"


class ChallengeStatus(Enum):
    OPEN = "open"
    UPHELD = "upheld"       # Challenge succeeded — cert revoked
    DISMISSED = "dismissed"  # Challenge failed — challenger loses stake
    EXPIRED = "expired"


class AuditVote(Enum):
    APPROVE = "approve"
    REJECT = "reject"
    ABSTAIN = "abstain"


@dataclass
class EntitySnapshot:
    lct_id: str
    name: str
    entity_type: str
    t3_composite: float
    v3_composite: float
    hardware_binding: int
    status: str = "active"
    risk_level: str = "high"
    parent_lct_id: str = ""  # For fractal composition


@dataclass
class ArticleAssessment:
    article: str
    title: str
    status: str  # compliant, partial, non_compliant
    evidence: list[str] = field(default_factory=list)
    gaps: list[str] = field(default_factory=list)


@dataclass
class AuditorAttestation:
    """Individual auditor's signed attestation on a certificate."""
    auditor_lct_id: str
    vote: AuditVote
    compliance_level: ComplianceLevel
    timestamp: str
    remarks: str = ""
    signature: str = ""

    def sign(self, key: str):
        msg = f"{self.auditor_lct_id}:{self.vote.value}:{self.compliance_level.value}:{self.timestamp}:{key}"
        self.signature = hashlib.sha256(msg.encode()).hexdigest()[:32]

    def verify(self, key: str) -> bool:
        msg = f"{self.auditor_lct_id}:{self.vote.value}:{self.compliance_level.value}:{self.timestamp}:{key}"
        expected = hashlib.sha256(msg.encode()).hexdigest()[:32]
        return self.signature == expected


# ═══════════════════════════════════════════════════════════════
# 1. MULTI-PARTY AUDIT QUORUM
# ═══════════════════════════════════════════════════════════════

@dataclass
class QuorumPolicy:
    """m-of-n quorum requirement for certification."""
    required_approvals: int   # m
    total_auditors: int       # n
    max_abstentions: int = 1  # Max allowed abstentions
    min_compliance_consensus: float = 0.66  # 2/3 must agree on level

    def __post_init__(self):
        if self.required_approvals > self.total_auditors:
            raise ValueError("required_approvals cannot exceed total_auditors")
        if self.required_approvals < 1:
            raise ValueError("At least 1 approval required")


@dataclass
class QuorumCertificate:
    """Certificate issued by quorum of auditors."""
    cert_id: str
    entity: EntitySnapshot
    assessments: list[ArticleAssessment]
    compliance_level: ComplianceLevel
    attestations: list[AuditorAttestation]
    quorum_policy: QuorumPolicy
    issued_at: str
    expires_at: str
    prev_cert_hash: str = ""
    cert_hash: str = ""
    quorum_met: bool = False
    consensus_level: Optional[ComplianceLevel] = None

    def __post_init__(self):
        if not self.cert_hash:
            self.cert_hash = self._compute_hash()

    def _compute_hash(self) -> str:
        attestation_hashes = ":".join(a.signature for a in self.attestations if a.signature)
        content = (
            f"{self.cert_id}:{self.entity.lct_id}:{self.compliance_level.value}:"
            f"{self.issued_at}:{attestation_hashes}:{self.prev_cert_hash}"
        )
        return hashlib.sha256(content.encode()).hexdigest()[:32]

    @property
    def approval_count(self) -> int:
        return sum(1 for a in self.attestations if a.vote == AuditVote.APPROVE)

    @property
    def rejection_count(self) -> int:
        return sum(1 for a in self.attestations if a.vote == AuditVote.REJECT)

    @property
    def abstention_count(self) -> int:
        return sum(1 for a in self.attestations if a.vote == AuditVote.ABSTAIN)


class QuorumAuthority:
    """Issues certificates only when m-of-n auditors approve."""

    def __init__(self, policy: QuorumPolicy):
        self.policy = policy
        self.auditors: dict[str, str] = {}  # auditor_lct_id → signing_key
        self.cert_counter = 0
        self.issued: list[QuorumCertificate] = []

    def register_auditor(self, lct_id: str, signing_key: str):
        self.auditors[lct_id] = signing_key

    def submit_attestation(self, auditor_lct_id: str,
                           vote: AuditVote,
                           compliance_level: ComplianceLevel,
                           remarks: str = "") -> AuditorAttestation:
        """Create a signed attestation from an auditor."""
        if auditor_lct_id not in self.auditors:
            raise ValueError(f"Unknown auditor: {auditor_lct_id}")

        att = AuditorAttestation(
            auditor_lct_id=auditor_lct_id,
            vote=vote,
            compliance_level=compliance_level,
            timestamp=datetime.utcnow().isoformat(),
            remarks=remarks
        )
        att.sign(self.auditors[auditor_lct_id])
        return att

    def evaluate_quorum(self, attestations: list[AuditorAttestation]) -> dict:
        """Evaluate whether quorum requirements are met."""
        approvals = sum(1 for a in attestations if a.vote == AuditVote.APPROVE)
        rejections = sum(1 for a in attestations if a.vote == AuditVote.REJECT)
        abstentions = sum(1 for a in attestations if a.vote == AuditVote.ABSTAIN)

        quorum_met = (
            approvals >= self.policy.required_approvals and
            abstentions <= self.policy.max_abstentions
        )

        # Consensus on compliance level
        level_votes: dict[str, int] = {}
        for a in attestations:
            if a.vote == AuditVote.APPROVE:
                lv = a.compliance_level.value
                level_votes[lv] = level_votes.get(lv, 0) + 1

        consensus_level = None
        if approvals > 0:
            top_level = max(level_votes, key=level_votes.get)
            top_count = level_votes[top_level]
            if top_count / approvals >= self.policy.min_compliance_consensus:
                consensus_level = ComplianceLevel(top_level)

        return {
            "approvals": approvals,
            "rejections": rejections,
            "abstentions": abstentions,
            "quorum_met": quorum_met,
            "consensus_level": consensus_level,
            "level_votes": level_votes,
        }

    def issue_if_quorum(self, entity: EntitySnapshot,
                        assessments: list[ArticleAssessment],
                        attestations: list[AuditorAttestation],
                        prev_cert_hash: str = "",
                        validity_days: int = 90) -> Optional[QuorumCertificate]:
        """Issue a certificate only if quorum is met."""
        evaluation = self.evaluate_quorum(attestations)

        if not evaluation["quorum_met"]:
            return None

        level = evaluation["consensus_level"]
        if level is None:
            # No consensus — use the most conservative level
            levels_by_strictness = [
                ComplianceLevel.NON_COMPLIANT,
                ComplianceLevel.PARTIAL,
                ComplianceLevel.SUBSTANTIAL,
                ComplianceLevel.FULL,
            ]
            all_levels = [a.compliance_level for a in attestations if a.vote == AuditVote.APPROVE]
            level = min(all_levels, key=lambda l: levels_by_strictness.index(l))

        now = datetime.utcnow()
        cert = QuorumCertificate(
            cert_id=f"QCERT-{self.cert_counter:06d}",
            entity=entity,
            assessments=assessments,
            compliance_level=level,
            attestations=attestations,
            quorum_policy=self.policy,
            issued_at=now.isoformat(),
            expires_at=(now + timedelta(days=validity_days)).isoformat(),
            prev_cert_hash=prev_cert_hash,
            quorum_met=True,
            consensus_level=evaluation["consensus_level"],
        )
        cert.cert_hash = cert._compute_hash()
        self.cert_counter += 1
        self.issued.append(cert)
        return cert


# ═══════════════════════════════════════════════════════════════
# 2. FRACTAL AUDIT COMPOSITION
# ═══════════════════════════════════════════════════════════════

@dataclass
class FractalAuditNode:
    """Node in a fractal audit hierarchy — entity + its sub-entity audits."""
    entity: EntitySnapshot
    certificate: Optional[QuorumCertificate]
    children: list['FractalAuditNode'] = field(default_factory=list)
    composite_level: Optional[ComplianceLevel] = None

    @property
    def lct_id(self) -> str:
        return self.entity.lct_id

    @property
    def is_leaf(self) -> bool:
        return len(self.children) == 0


class FractalAuditComposer:
    """Composes sub-entity audits into parent compliance assessments.

    Rules:
    - Parent compliance ≤ weakest child compliance (conservative)
    - If ANY child is NON_COMPLIANT, parent cannot be FULL
    - Composite T3 = weighted average of children (by hardware binding)
    - Missing child audits count as NON_COMPLIANT
    """

    LEVEL_ORDER = [
        ComplianceLevel.NON_COMPLIANT,
        ComplianceLevel.PARTIAL,
        ComplianceLevel.SUBSTANTIAL,
        ComplianceLevel.FULL,
    ]

    def compose(self, node: FractalAuditNode) -> ComplianceLevel:
        """Recursively compose compliance levels from leaves to root."""
        if node.is_leaf:
            if node.certificate:
                node.composite_level = node.certificate.compliance_level
            else:
                node.composite_level = ComplianceLevel.NON_COMPLIANT
            return node.composite_level

        # Recurse into children
        child_levels = []
        for child in node.children:
            child_level = self.compose(child)
            child_levels.append(child_level)

        # Own certification level
        own_level = (node.certificate.compliance_level
                     if node.certificate else ComplianceLevel.NON_COMPLIANT)

        # Parent = min(own, weakest_child)
        weakest_child = min(child_levels, key=lambda l: self.LEVEL_ORDER.index(l))
        composite = min(own_level, weakest_child,
                        key=lambda l: self.LEVEL_ORDER.index(l))

        node.composite_level = composite
        return composite

    def compute_composite_t3(self, node: FractalAuditNode) -> float:
        """Weighted average T3 across hierarchy (weighted by hardware binding)."""
        if node.is_leaf:
            return node.entity.t3_composite

        total_weight = node.entity.hardware_binding
        weighted_sum = node.entity.t3_composite * node.entity.hardware_binding

        for child in node.children:
            child_t3 = self.compute_composite_t3(child)
            weight = child.entity.hardware_binding
            total_weight += weight
            weighted_sum += child_t3 * weight

        return weighted_sum / total_weight if total_weight > 0 else 0.0

    def audit_tree_depth(self, node: FractalAuditNode) -> int:
        """Depth of audit tree."""
        if node.is_leaf:
            return 1
        return 1 + max(self.audit_tree_depth(c) for c in node.children)

    def count_nodes(self, node: FractalAuditNode) -> int:
        """Total nodes in tree."""
        return 1 + sum(self.count_nodes(c) for c in node.children)

    def all_compliant(self, node: FractalAuditNode) -> bool:
        """Check if all nodes in tree are at least PARTIAL."""
        if node.composite_level is None:
            self.compose(node)
        if self.LEVEL_ORDER.index(node.composite_level) < self.LEVEL_ORDER.index(ComplianceLevel.PARTIAL):
            return False
        return all(self.all_compliant(c) for c in node.children)


# ═══════════════════════════════════════════════════════════════
# 3. ATP-BACKED AUDIT INCENTIVES
# ═══════════════════════════════════════════════════════════════

@dataclass
class AuditorAccount:
    """Auditor's ATP balance and track record."""
    auditor_lct_id: str
    atp_balance: float
    stake_locked: float = 0.0
    audits_completed: int = 0
    audits_challenged: int = 0
    audits_overturned: int = 0
    reputation_score: float = 0.5

    @property
    def accuracy_rate(self) -> float:
        if self.audits_completed == 0:
            return 1.0
        return 1.0 - (self.audits_overturned / self.audits_completed)

    @property
    def available_balance(self) -> float:
        return self.atp_balance - self.stake_locked


class AuditIncentiveEngine:
    """ATP-backed incentives for accurate auditing.

    Mechanism:
    - Auditors must stake ATP to participate (skin in the game)
    - Successful audits earn ATP rewards
    - Overturned audits lose the stake
    - Audit fee paid by auditee covers rewards + operations
    """

    STAKE_AMOUNT = 50.0      # ATP required per audit
    REWARD_BASE = 20.0       # Base reward for successful audit
    ACCURACY_BONUS = 10.0    # Bonus for high accuracy rate
    CHALLENGE_STAKE = 100.0  # ATP required to challenge a certificate

    def __init__(self):
        self.accounts: dict[str, AuditorAccount] = {}
        self.fee_pool: float = 0.0
        self.total_staked: float = 0.0
        self.total_rewarded: float = 0.0
        self.total_slashed: float = 0.0

    def register_auditor(self, lct_id: str, initial_balance: float):
        self.accounts[lct_id] = AuditorAccount(
            auditor_lct_id=lct_id,
            atp_balance=initial_balance
        )

    def stake_for_audit(self, auditor_lct_id: str) -> bool:
        """Lock ATP stake before auditing."""
        acct = self.accounts.get(auditor_lct_id)
        if not acct or acct.available_balance < self.STAKE_AMOUNT:
            return False
        acct.stake_locked += self.STAKE_AMOUNT
        self.total_staked += self.STAKE_AMOUNT
        return True

    def complete_audit(self, auditor_lct_id: str):
        """Release stake and pay reward after successful audit."""
        acct = self.accounts.get(auditor_lct_id)
        if not acct:
            return

        # Release stake
        acct.stake_locked -= self.STAKE_AMOUNT
        self.total_staked -= self.STAKE_AMOUNT

        # Pay reward
        reward = self.REWARD_BASE
        if acct.accuracy_rate >= 0.9:
            reward += self.ACCURACY_BONUS

        acct.atp_balance += reward
        acct.audits_completed += 1
        self.total_rewarded += reward

    def slash_auditor(self, auditor_lct_id: str):
        """Slash stake when audit is overturned by challenge."""
        acct = self.accounts.get(auditor_lct_id)
        if not acct:
            return

        # Lose the stake
        acct.atp_balance -= self.STAKE_AMOUNT
        acct.stake_locked -= self.STAKE_AMOUNT
        self.total_staked -= self.STAKE_AMOUNT
        self.total_slashed += self.STAKE_AMOUNT

        acct.audits_overturned += 1

        # Reputation penalty
        acct.reputation_score = max(0.0, acct.reputation_score - 0.1)

    def collect_audit_fee(self, fee: float):
        """Collect fee from auditee."""
        self.fee_pool += fee

    def auditor_can_audit(self, auditor_lct_id: str) -> bool:
        """Check if auditor has enough balance and reputation."""
        acct = self.accounts.get(auditor_lct_id)
        if not acct:
            return False
        return (acct.available_balance >= self.STAKE_AMOUNT and
                acct.reputation_score >= 0.2)


# ═══════════════════════════════════════════════════════════════
# 4. AUDIT CHALLENGE PROTOCOL
# ═══════════════════════════════════════════════════════════════

@dataclass
class AuditChallenge:
    """Challenge to an issued certificate."""
    challenge_id: str
    challenger_lct_id: str
    target_cert_id: str
    reason: str
    evidence: list[str]
    stake: float
    status: ChallengeStatus
    created_at: str
    resolved_at: str = ""
    resolution_votes: list[tuple[str, str]] = field(default_factory=list)  # (auditor_id, vote)
    resolution_reason: str = ""


class ChallengeProtocol:
    """Challenge mechanism for disputed audit certificates.

    Process:
    1. Challenger stakes ATP and submits evidence
    2. Independent panel reviews (different from original auditors)
    3. If upheld: cert revoked, original auditors slashed, challenger rewarded
    4. If dismissed: challenger loses stake, original cert stands
    """

    def __init__(self, incentive_engine: AuditIncentiveEngine,
                 panel_size: int = 3):
        self.incentive_engine = incentive_engine
        self.panel_size = panel_size
        self.challenges: list[AuditChallenge] = []
        self.challenge_counter = 0

    def file_challenge(self, challenger_lct_id: str,
                       target_cert_id: str,
                       reason: str,
                       evidence: list[str]) -> Optional[AuditChallenge]:
        """File a challenge against a certificate."""
        acct = self.incentive_engine.accounts.get(challenger_lct_id)
        if not acct or acct.available_balance < self.incentive_engine.CHALLENGE_STAKE:
            return None

        # Lock challenger's stake
        acct.stake_locked += self.incentive_engine.CHALLENGE_STAKE

        challenge = AuditChallenge(
            challenge_id=f"CHAL-{self.challenge_counter:06d}",
            challenger_lct_id=challenger_lct_id,
            target_cert_id=target_cert_id,
            reason=reason,
            evidence=evidence,
            stake=self.incentive_engine.CHALLENGE_STAKE,
            status=ChallengeStatus.OPEN,
            created_at=datetime.utcnow().isoformat()
        )
        self.challenges.append(challenge)
        self.challenge_counter += 1
        return challenge

    def submit_panel_vote(self, challenge: AuditChallenge,
                          panelist_lct_id: str,
                          vote: str):  # "upheld" or "dismissed"
        """Panel member votes on challenge outcome."""
        challenge.resolution_votes.append((panelist_lct_id, vote))

    def resolve_challenge(self, challenge: AuditChallenge,
                          original_auditors: list[str]) -> dict:
        """Resolve challenge based on panel votes."""
        upheld_votes = sum(1 for _, v in challenge.resolution_votes if v == "upheld")
        dismissed_votes = sum(1 for _, v in challenge.resolution_votes if v == "dismissed")

        challenger_acct = self.incentive_engine.accounts.get(challenge.challenger_lct_id)

        if upheld_votes > dismissed_votes:
            # Challenge upheld — cert invalid
            challenge.status = ChallengeStatus.UPHELD

            # Reward challenger: return stake + bonus
            if challenger_acct:
                challenger_acct.stake_locked -= self.incentive_engine.CHALLENGE_STAKE
                challenger_acct.atp_balance += self.incentive_engine.REWARD_BASE  # Bonus

            # Slash original auditors
            for auditor_id in original_auditors:
                self.incentive_engine.slash_auditor(auditor_id)

        else:
            # Challenge dismissed
            challenge.status = ChallengeStatus.DISMISSED

            # Challenger loses stake
            if challenger_acct:
                challenger_acct.atp_balance -= self.incentive_engine.CHALLENGE_STAKE
                challenger_acct.stake_locked -= self.incentive_engine.CHALLENGE_STAKE

        challenge.resolved_at = datetime.utcnow().isoformat()

        return {
            "challenge_id": challenge.challenge_id,
            "status": challenge.status.value,
            "upheld_votes": upheld_votes,
            "dismissed_votes": dismissed_votes,
        }


# ═══════════════════════════════════════════════════════════════
# 5. CROSS-FEDERATION AUDIT SYNC
# ═══════════════════════════════════════════════════════════════

@dataclass
class FederationAuditAnchor:
    """Hash anchor of audit state shared across federations."""
    federation_id: str
    anchor_hash: str        # SHA-256 of all local audit records
    cert_count: int
    latest_cert_hash: str
    timestamp: str
    sequence_number: int


class CrossFederationAuditSync:
    """Synchronize audit state across federation boundaries.

    Each federation maintains its own audit chain. Periodically,
    federations exchange anchor hashes. If anchor hashes match
    for the same entity, the audit is cross-validated.
    """

    def __init__(self):
        self.federation_anchors: dict[str, list[FederationAuditAnchor]] = {}
        self.cross_validations: list[dict] = []

    def submit_anchor(self, federation_id: str,
                      cert_hashes: list[str],
                      sequence: int) -> FederationAuditAnchor:
        """Federation submits its current audit state hash."""
        combined = ":".join(cert_hashes)
        anchor_hash = hashlib.sha256(combined.encode()).hexdigest()[:32]

        anchor = FederationAuditAnchor(
            federation_id=federation_id,
            anchor_hash=anchor_hash,
            cert_count=len(cert_hashes),
            latest_cert_hash=cert_hashes[-1] if cert_hashes else "",
            timestamp=datetime.utcnow().isoformat(),
            sequence_number=sequence
        )

        if federation_id not in self.federation_anchors:
            self.federation_anchors[federation_id] = []
        self.federation_anchors[federation_id].append(anchor)
        return anchor

    def cross_validate(self, fed_a_id: str, fed_b_id: str,
                       entity_lct_id: str) -> dict:
        """Cross-validate audit state between two federations."""
        anchors_a = self.federation_anchors.get(fed_a_id, [])
        anchors_b = self.federation_anchors.get(fed_b_id, [])

        if not anchors_a or not anchors_b:
            return {"valid": False, "reason": "Missing federation anchors"}

        latest_a = anchors_a[-1]
        latest_b = anchors_b[-1]

        # Anchors match → audit state is synchronized
        match = latest_a.anchor_hash == latest_b.anchor_hash

        result = {
            "entity": entity_lct_id,
            "federation_a": fed_a_id,
            "federation_b": fed_b_id,
            "anchor_a": latest_a.anchor_hash,
            "anchor_b": latest_b.anchor_hash,
            "match": match,
            "cert_count_a": latest_a.cert_count,
            "cert_count_b": latest_b.cert_count,
            "valid": match
        }

        self.cross_validations.append(result)
        return result

    def detect_drift(self, federation_id: str) -> dict:
        """Detect if a federation's audit anchors show drift."""
        anchors = self.federation_anchors.get(federation_id, [])
        if len(anchors) < 2:
            return {"drift": False, "reason": "Insufficient data"}

        # Check sequence continuity
        gaps = []
        for i in range(1, len(anchors)):
            if anchors[i].sequence_number != anchors[i-1].sequence_number + 1:
                gaps.append((anchors[i-1].sequence_number, anchors[i].sequence_number))

        # Check monotonic cert count
        decreases = []
        for i in range(1, len(anchors)):
            if anchors[i].cert_count < anchors[i-1].cert_count:
                decreases.append((i, anchors[i-1].cert_count, anchors[i].cert_count))

        return {
            "federation": federation_id,
            "anchors_checked": len(anchors),
            "sequence_gaps": gaps,
            "cert_count_decreases": decreases,
            "drift": len(gaps) > 0 or len(decreases) > 0,
        }


# ═══════════════════════════════════════════════════════════════
# CHECKS
# ═══════════════════════════════════════════════════════════════

def run_checks():
    passed = 0
    failed = 0

    def check(condition: bool, description: str):
        nonlocal passed, failed
        if condition:
            passed += 1
        else:
            failed += 1
            print(f"  FAIL: {description}")

    # ─── Helpers ───────────────────────────────────────────────

    def make_entity(lct_id: str, name: str, t3: float = 0.7,
                    hw: int = 5, parent: str = "") -> EntitySnapshot:
        return EntitySnapshot(
            lct_id=lct_id, name=name, entity_type="ai",
            t3_composite=t3, v3_composite=0.75,
            hardware_binding=hw, parent_lct_id=parent
        )

    def make_assessments(compliant_n: int = 8) -> list[ArticleAssessment]:
        articles = [
            ("6", "Classification"), ("9", "Risk Management"),
            ("10", "Data Governance"), ("11", "Technical Documentation"),
            ("12", "Record-Keeping"), ("13", "Transparency"),
            ("14", "Human Oversight"), ("15", "Cybersecurity"),
        ]
        result = []
        for i, (art, title) in enumerate(articles):
            status = "compliant" if i < compliant_n else "non_compliant"
            result.append(ArticleAssessment(
                article=art, title=title, status=status,
                evidence=[f"Evidence for Art. {art}"]
            ))
        return result

    # ═══════════════════════════════════════════════════════════
    # SECTION 1: MULTI-PARTY QUORUM
    # ═══════════════════════════════════════════════════════════

    print("Section 1: Multi-Party Quorum")

    policy = QuorumPolicy(required_approvals=3, total_auditors=5)
    qa = QuorumAuthority(policy)

    # Register 5 auditors
    auditor_keys = {}
    for i in range(5):
        lct = f"lct:auditor:{i}"
        key = f"key-auditor-{i}"
        qa.register_auditor(lct, key)
        auditor_keys[lct] = key

    check(len(qa.auditors) == 5, "5 auditors registered")

    # --- 1.1: Quorum met (3 approve, 1 reject, 1 abstain) ---
    entity = make_entity("lct:ai:hiring-bot", "HireBot")
    assessments = make_assessments(8)

    atts = [
        qa.submit_attestation("lct:auditor:0", AuditVote.APPROVE, ComplianceLevel.FULL),
        qa.submit_attestation("lct:auditor:1", AuditVote.APPROVE, ComplianceLevel.FULL),
        qa.submit_attestation("lct:auditor:2", AuditVote.APPROVE, ComplianceLevel.FULL),
        qa.submit_attestation("lct:auditor:3", AuditVote.REJECT, ComplianceLevel.PARTIAL),
        qa.submit_attestation("lct:auditor:4", AuditVote.ABSTAIN, ComplianceLevel.FULL),
    ]

    eval_result = qa.evaluate_quorum(atts)
    check(eval_result["quorum_met"], "3-of-5 quorum met with 3 approvals")
    check(eval_result["approvals"] == 3, "3 approvals counted")
    check(eval_result["rejections"] == 1, "1 rejection counted")
    check(eval_result["abstentions"] == 1, "1 abstention counted")
    check(eval_result["consensus_level"] == ComplianceLevel.FULL,
          "Consensus level is FULL (3/3 approvers agree)")

    cert = qa.issue_if_quorum(entity, assessments, atts)
    check(cert is not None, "Certificate issued when quorum met")
    check(cert.compliance_level == ComplianceLevel.FULL, "Cert level = FULL")
    check(cert.quorum_met, "quorum_met flag set")
    check(cert.approval_count == 3, "Certificate records 3 approvals")
    check(cert.rejection_count == 1, "Certificate records 1 rejection")
    check(len(cert.cert_hash) == 32, "Certificate hash computed")

    # --- 1.2: Quorum NOT met (only 2 approve) ---
    atts_insufficient = [
        qa.submit_attestation("lct:auditor:0", AuditVote.APPROVE, ComplianceLevel.FULL),
        qa.submit_attestation("lct:auditor:1", AuditVote.APPROVE, ComplianceLevel.FULL),
        qa.submit_attestation("lct:auditor:2", AuditVote.REJECT, ComplianceLevel.PARTIAL),
        qa.submit_attestation("lct:auditor:3", AuditVote.REJECT, ComplianceLevel.NON_COMPLIANT),
        qa.submit_attestation("lct:auditor:4", AuditVote.ABSTAIN, ComplianceLevel.PARTIAL),
    ]

    no_cert = qa.issue_if_quorum(entity, assessments, atts_insufficient)
    check(no_cert is None, "No certificate when quorum not met (2 < 3)")

    eval_no = qa.evaluate_quorum(atts_insufficient)
    check(not eval_no["quorum_met"], "Quorum not met")
    check(eval_no["approvals"] == 2, "Only 2 approvals")

    # --- 1.3: Too many abstentions ---
    atts_abstain = [
        qa.submit_attestation("lct:auditor:0", AuditVote.APPROVE, ComplianceLevel.FULL),
        qa.submit_attestation("lct:auditor:1", AuditVote.APPROVE, ComplianceLevel.FULL),
        qa.submit_attestation("lct:auditor:2", AuditVote.APPROVE, ComplianceLevel.FULL),
        qa.submit_attestation("lct:auditor:3", AuditVote.ABSTAIN, ComplianceLevel.FULL),
        qa.submit_attestation("lct:auditor:4", AuditVote.ABSTAIN, ComplianceLevel.FULL),
    ]

    eval_abstain = qa.evaluate_quorum(atts_abstain)
    check(not eval_abstain["quorum_met"],
          "Quorum NOT met: 2 abstentions > max 1")

    # --- 1.4: Split consensus → conservative level ---
    atts_split = [
        qa.submit_attestation("lct:auditor:0", AuditVote.APPROVE, ComplianceLevel.FULL),
        qa.submit_attestation("lct:auditor:1", AuditVote.APPROVE, ComplianceLevel.SUBSTANTIAL),
        qa.submit_attestation("lct:auditor:2", AuditVote.APPROVE, ComplianceLevel.PARTIAL),
    ]

    eval_split = qa.evaluate_quorum(atts_split)
    check(eval_split["consensus_level"] is None,
          "No consensus when all disagree (1/3 < 0.66)")

    # Issue with no consensus → most conservative level
    policy_3 = QuorumPolicy(required_approvals=3, total_auditors=3, max_abstentions=0)
    qa3 = QuorumAuthority(policy_3)
    for k, v in auditor_keys.items():
        qa3.register_auditor(k, v)

    cert_split = qa3.issue_if_quorum(entity, assessments, atts_split)
    check(cert_split is not None, "Certificate issued despite split consensus")
    check(cert_split.compliance_level == ComplianceLevel.PARTIAL,
          "Split consensus → most conservative (PARTIAL)")

    # --- 1.5: Signature verification ---
    att = atts[0]
    check(att.verify(auditor_keys["lct:auditor:0"]),
          "Attestation signature verifies with correct key")
    check(not att.verify("wrong-key"),
          "Attestation signature fails with wrong key")

    # --- 1.6: Unknown auditor rejected ---
    try:
        qa.submit_attestation("lct:unknown:auditor", AuditVote.APPROVE, ComplianceLevel.FULL)
        check(False, "Unknown auditor should raise ValueError")
    except ValueError:
        check(True, "Unknown auditor raises ValueError")

    # --- 1.7: Quorum policy validation ---
    try:
        QuorumPolicy(required_approvals=6, total_auditors=5)
        check(False, "Should reject required > total")
    except ValueError:
        check(True, "Rejects required_approvals > total_auditors")

    # ═══════════════════════════════════════════════════════════
    # SECTION 2: FRACTAL AUDIT COMPOSITION
    # ═══════════════════════════════════════════════════════════

    print("Section 2: Fractal Audit Composition")

    composer = FractalAuditComposer()

    # --- 2.1: Simple hierarchy (parent + 2 children) ---

    # Parent fully compliant, both children fully compliant
    parent_entity = make_entity("lct:org:acme", "ACME Corp", t3=0.8, hw=5)
    child1_entity = make_entity("lct:ai:bot1", "Bot1", t3=0.75, hw=4, parent="lct:org:acme")
    child2_entity = make_entity("lct:ai:bot2", "Bot2", t3=0.7, hw=3, parent="lct:org:acme")

    # Create certificates
    parent_cert = qa.issue_if_quorum(parent_entity, make_assessments(8), atts)
    child1_cert = qa.issue_if_quorum(child1_entity, make_assessments(8), atts)
    child2_cert = qa.issue_if_quorum(child2_entity, make_assessments(8), atts)

    child1_node = FractalAuditNode(entity=child1_entity, certificate=child1_cert)
    child2_node = FractalAuditNode(entity=child2_entity, certificate=child2_cert)
    parent_node = FractalAuditNode(
        entity=parent_entity, certificate=parent_cert,
        children=[child1_node, child2_node]
    )

    composite = composer.compose(parent_node)
    check(composite == ComplianceLevel.FULL,
          "All FULL children → parent FULL")
    check(parent_node.composite_level == ComplianceLevel.FULL,
          "Composite stored on node")
    check(child1_node.composite_level == ComplianceLevel.FULL,
          "Child1 is FULL")
    check(child2_node.composite_level == ComplianceLevel.FULL,
          "Child2 is FULL")

    # --- 2.2: Weak child degrades parent ---

    # Make child2 only PARTIAL (5/8)
    weak_child_atts = [
        qa.submit_attestation("lct:auditor:0", AuditVote.APPROVE, ComplianceLevel.PARTIAL),
        qa.submit_attestation("lct:auditor:1", AuditVote.APPROVE, ComplianceLevel.PARTIAL),
        qa.submit_attestation("lct:auditor:2", AuditVote.APPROVE, ComplianceLevel.PARTIAL),
    ]
    weak_cert = qa3.issue_if_quorum(child2_entity, make_assessments(5), weak_child_atts)

    weak_child_node = FractalAuditNode(entity=child2_entity, certificate=weak_cert)
    mixed_parent = FractalAuditNode(
        entity=parent_entity, certificate=parent_cert,
        children=[child1_node, weak_child_node]
    )

    mixed_composite = composer.compose(mixed_parent)
    check(mixed_composite == ComplianceLevel.PARTIAL,
          "FULL parent + PARTIAL child → PARTIAL composite")

    # --- 2.3: Missing child audit → NON_COMPLIANT ---

    uncertified_child = FractalAuditNode(
        entity=make_entity("lct:ai:uncertified", "Uncertified"),
        certificate=None  # No audit!
    )
    parent_with_missing = FractalAuditNode(
        entity=parent_entity, certificate=parent_cert,
        children=[child1_node, uncertified_child]
    )

    missing_composite = composer.compose(parent_with_missing)
    check(missing_composite == ComplianceLevel.NON_COMPLIANT,
          "Missing child audit → NON_COMPLIANT composite")

    # --- 2.4: Composite T3 (weighted by hardware binding) ---

    # Parent: t3=0.8, hw=5. Child1: t3=0.75, hw=4. Child2: t3=0.7, hw=3
    composite_t3 = composer.compute_composite_t3(parent_node)
    expected_t3 = (0.8*5 + 0.75*4 + 0.7*3) / (5+4+3)  # = 7.1/12 ≈ 0.7583
    check(abs(composite_t3 - expected_t3) < 0.001,
          f"Composite T3 = {composite_t3:.4f} ≈ {expected_t3:.4f} (hw-weighted)")

    # --- 2.5: Tree metrics ---

    depth = composer.audit_tree_depth(parent_node)
    check(depth == 2, f"Tree depth = {depth} (parent + children)")

    count = composer.count_nodes(parent_node)
    check(count == 3, f"Node count = {count} (1 parent + 2 children)")

    # --- 2.6: 3-level hierarchy ---

    grandchild = FractalAuditNode(
        entity=make_entity("lct:ai:gc1", "GrandChild", t3=0.65, hw=2),
        certificate=qa.issue_if_quorum(
            make_entity("lct:ai:gc1", "GrandChild", t3=0.65, hw=2),
            make_assessments(8), atts
        )
    )
    deep_child = FractalAuditNode(
        entity=child1_entity,
        certificate=child1_cert,
        children=[grandchild]
    )
    deep_parent = FractalAuditNode(
        entity=parent_entity, certificate=parent_cert,
        children=[deep_child]
    )

    deep_composite = composer.compose(deep_parent)
    check(deep_composite == ComplianceLevel.FULL,
          "3-level hierarchy all FULL → FULL composite")

    deep_depth = composer.audit_tree_depth(deep_parent)
    check(deep_depth == 3, f"3-level tree depth = {deep_depth}")

    deep_count = composer.count_nodes(deep_parent)
    check(deep_count == 3, f"3-level node count = {deep_count}")

    # --- 2.7: all_compliant check ---

    check(composer.all_compliant(parent_node),
          "All-FULL tree → all_compliant = True")
    check(not composer.all_compliant(parent_with_missing),
          "Tree with NON_COMPLIANT child → all_compliant = False")

    # ═══════════════════════════════════════════════════════════
    # SECTION 3: ATP-BACKED AUDIT INCENTIVES
    # ═══════════════════════════════════════════════════════════

    print("Section 3: ATP-Backed Audit Incentives")

    engine = AuditIncentiveEngine()

    # Register auditors with ATP
    for i in range(5):
        engine.register_auditor(f"lct:auditor:{i}", 500.0)

    check(len(engine.accounts) == 5, "5 auditors registered with ATP")
    check(engine.accounts["lct:auditor:0"].atp_balance == 500.0,
          "Initial balance = 500 ATP")

    # --- 3.1: Staking ---

    staked = engine.stake_for_audit("lct:auditor:0")
    check(staked, "Stake accepted (500 ≥ 50)")
    check(engine.accounts["lct:auditor:0"].stake_locked == 50.0,
          "50 ATP locked as stake")
    check(engine.accounts["lct:auditor:0"].available_balance == 450.0,
          "Available = 500 - 50 = 450")

    # --- 3.2: Completing audit → reward ---

    engine.complete_audit("lct:auditor:0")
    acct0 = engine.accounts["lct:auditor:0"]
    check(acct0.stake_locked == 0.0, "Stake released after completion")
    check(acct0.atp_balance == 530.0,
          "Balance = 500 + 30 reward (20 base + 10 accuracy bonus) = 530")
    check(acct0.audits_completed == 1, "1 audit completed")
    check(acct0.accuracy_rate == 1.0, "100% accuracy (no overturns)")

    # --- 3.3: Accuracy bonus ---

    # Complete 9 more audits to maintain high accuracy
    for _ in range(9):
        engine.stake_for_audit("lct:auditor:0")
        engine.complete_audit("lct:auditor:0")

    check(acct0.audits_completed == 10, "10 audits completed")
    # 10 audits × 30 reward (20 base + 10 bonus) = 300 total
    check(acct0.atp_balance == 800.0,
          f"Balance after 10 audits = {acct0.atp_balance} (expected 800)")

    # --- 3.4: Slashing ---

    engine.stake_for_audit("lct:auditor:1")
    initial_balance = engine.accounts["lct:auditor:1"].atp_balance
    engine.slash_auditor("lct:auditor:1")
    acct1 = engine.accounts["lct:auditor:1"]
    check(acct1.atp_balance == initial_balance - 50.0,
          "Slashed auditor loses 50 ATP stake")
    check(acct1.audits_overturned == 1, "1 audit overturned")
    check(acct1.reputation_score == 0.4,
          f"Reputation decreased to {acct1.reputation_score}")

    # --- 3.5: Can't audit without enough balance ---

    broke_auditor = "lct:auditor:broke"
    engine.register_auditor(broke_auditor, 10.0)  # Not enough for stake
    check(not engine.stake_for_audit(broke_auditor),
          "Can't stake with 10 ATP (need 50)")
    check(not engine.auditor_can_audit(broke_auditor),
          "Can't audit — insufficient balance")

    # --- 3.6: Can't audit with bad reputation ---

    engine.register_auditor("lct:auditor:bad-rep", 500.0)
    engine.accounts["lct:auditor:bad-rep"].reputation_score = 0.1
    check(not engine.auditor_can_audit("lct:auditor:bad-rep"),
          "Can't audit — reputation 0.1 < minimum 0.2")

    # --- 3.7: Fee pool ---

    engine.collect_audit_fee(100.0)
    engine.collect_audit_fee(50.0)
    check(engine.fee_pool == 150.0, "Fee pool = 150 ATP")

    # --- 3.8: Tracking totals ---

    check(engine.total_rewarded > 0, f"Total rewarded = {engine.total_rewarded}")
    check(engine.total_slashed == 50.0, f"Total slashed = {engine.total_slashed}")

    # ═══════════════════════════════════════════════════════════
    # SECTION 4: AUDIT CHALLENGE PROTOCOL
    # ═══════════════════════════════════════════════════════════

    print("Section 4: Audit Challenge Protocol")

    challenge_engine = AuditIncentiveEngine()
    for i in range(5):
        challenge_engine.register_auditor(f"lct:auditor:{i}", 500.0)
    challenge_engine.register_auditor("lct:challenger:1", 500.0)
    challenge_engine.register_auditor("lct:panelist:1", 500.0)
    challenge_engine.register_auditor("lct:panelist:2", 500.0)
    challenge_engine.register_auditor("lct:panelist:3", 500.0)

    protocol = ChallengeProtocol(challenge_engine)

    # --- 4.1: File a challenge ---

    challenge = protocol.file_challenge(
        "lct:challenger:1",
        "QCERT-000000",
        "Bias audit evidence was fabricated",
        ["Counter-evidence item 1", "Counter-evidence item 2"]
    )

    check(challenge is not None, "Challenge filed successfully")
    check(challenge.status == ChallengeStatus.OPEN, "Challenge status = OPEN")
    check(challenge.stake == 100.0, "Challenge stake = 100 ATP")
    check(len(challenge.evidence) == 2, "2 pieces of evidence submitted")

    # Challenger's stake locked
    challenger_acct = challenge_engine.accounts["lct:challenger:1"]
    check(challenger_acct.stake_locked == 100.0,
          "Challenger's 100 ATP locked")

    # --- 4.2: Challenge upheld (cert invalid) ---

    protocol.submit_panel_vote(challenge, "lct:panelist:1", "upheld")
    protocol.submit_panel_vote(challenge, "lct:panelist:2", "upheld")
    protocol.submit_panel_vote(challenge, "lct:panelist:3", "dismissed")

    result = protocol.resolve_challenge(
        challenge,
        original_auditors=["lct:auditor:0", "lct:auditor:1"]
    )

    check(result["status"] == "upheld", "Challenge upheld (2-1 vote)")
    check(challenge.status == ChallengeStatus.UPHELD, "Status updated to UPHELD")
    check(result["upheld_votes"] == 2, "2 upheld votes")
    check(result["dismissed_votes"] == 1, "1 dismissed vote")

    # Challenger rewarded
    check(challenger_acct.stake_locked == 0.0,
          "Challenger's stake released on upheld")
    check(challenger_acct.atp_balance == 520.0,
          f"Challenger gets bonus: 500 + 20 = {challenger_acct.atp_balance}")

    # Original auditors slashed
    check(challenge_engine.accounts["lct:auditor:0"].audits_overturned == 1,
          "Auditor 0 overturned")
    check(challenge_engine.accounts["lct:auditor:1"].audits_overturned == 1,
          "Auditor 1 overturned")

    # --- 4.3: Challenge dismissed ---

    challenge2 = protocol.file_challenge(
        "lct:challenger:1",
        "QCERT-000001",
        "Frivolous challenge",
        ["Weak evidence"]
    )

    protocol.submit_panel_vote(challenge2, "lct:panelist:1", "dismissed")
    protocol.submit_panel_vote(challenge2, "lct:panelist:2", "dismissed")
    protocol.submit_panel_vote(challenge2, "lct:panelist:3", "upheld")

    result2 = protocol.resolve_challenge(challenge2, ["lct:auditor:2"])

    check(result2["status"] == "dismissed", "Challenge dismissed (1-2 vote)")
    check(challenge2.status == ChallengeStatus.DISMISSED, "Status = DISMISSED")

    # Challenger loses stake
    check(challenger_acct.atp_balance == 420.0,
          f"Challenger penalized: 520 - 100 (lost stake) = {challenger_acct.atp_balance}")

    # --- 4.4: Can't challenge without funds ---

    challenge_engine.register_auditor("lct:broke:challenger", 50.0)
    no_challenge = protocol.file_challenge(
        "lct:broke:challenger", "CERT-X", "Test", ["x"]
    )
    check(no_challenge is None, "Can't challenge with 50 ATP (need 100)")

    # ═══════════════════════════════════════════════════════════
    # SECTION 5: CROSS-FEDERATION AUDIT SYNC
    # ═══════════════════════════════════════════════════════════

    print("Section 5: Cross-Federation Audit Sync")

    sync = CrossFederationAuditSync()

    # Two federations submit the same audit state
    cert_hashes = ["hash_a", "hash_b", "hash_c"]

    anchor_a = sync.submit_anchor("fed:alpha", cert_hashes, sequence=1)
    anchor_b = sync.submit_anchor("fed:beta", cert_hashes, sequence=1)

    check(anchor_a.anchor_hash == anchor_b.anchor_hash,
          "Same cert hashes → same anchor hash")
    check(anchor_a.cert_count == 3, "3 certificates anchored")

    # --- 5.1: Cross-validate matching federations ---

    cv = sync.cross_validate("fed:alpha", "fed:beta", "lct:shared:entity")
    check(cv["valid"], "Matching anchors → valid cross-validation")
    check(cv["match"], "Anchors match")

    # --- 5.2: Cross-validate divergent federations ---

    sync.submit_anchor("fed:gamma", ["hash_a", "hash_b", "hash_d"], sequence=1)
    cv_bad = sync.cross_validate("fed:alpha", "fed:gamma", "lct:shared:entity")
    check(not cv_bad["valid"], "Divergent anchors → invalid cross-validation")
    check(not cv_bad["match"], "Anchors don't match")

    # --- 5.3: Missing federation ---

    cv_missing = sync.cross_validate("fed:alpha", "fed:missing", "lct:x")
    check(not cv_missing["valid"], "Missing federation → invalid")

    # --- 5.4: Drift detection (no drift) ---

    sync2 = CrossFederationAuditSync()
    sync2.submit_anchor("fed:clean", ["h1"], sequence=1)
    sync2.submit_anchor("fed:clean", ["h1", "h2"], sequence=2)
    sync2.submit_anchor("fed:clean", ["h1", "h2", "h3"], sequence=3)

    drift = sync2.detect_drift("fed:clean")
    check(not drift["drift"], "Clean federation: no drift")
    check(len(drift["sequence_gaps"]) == 0, "No sequence gaps")
    check(len(drift["cert_count_decreases"]) == 0, "No cert count decreases")

    # --- 5.5: Drift detection (sequence gap) ---

    sync3 = CrossFederationAuditSync()
    sync3.submit_anchor("fed:gappy", ["h1"], sequence=1)
    sync3.submit_anchor("fed:gappy", ["h1", "h2"], sequence=5)  # Gap!

    gap_drift = sync3.detect_drift("fed:gappy")
    check(gap_drift["drift"], "Sequence gap detected as drift")
    check(len(gap_drift["sequence_gaps"]) == 1, "1 sequence gap found")

    # --- 5.6: Drift detection (cert count decrease) ---

    sync4 = CrossFederationAuditSync()
    sync4.submit_anchor("fed:shrinking", ["h1", "h2"], sequence=1)
    sync4.submit_anchor("fed:shrinking", ["h1"], sequence=2)  # Decrease!

    shrink_drift = sync4.detect_drift("fed:shrinking")
    check(shrink_drift["drift"], "Cert count decrease detected as drift")
    check(len(shrink_drift["cert_count_decreases"]) == 1,
          "1 cert count decrease found")

    # --- 5.7: Drift detection (insufficient data) ---

    sync5 = CrossFederationAuditSync()
    sync5.submit_anchor("fed:single", ["h1"], sequence=1)
    single_drift = sync5.detect_drift("fed:single")
    check(not single_drift["drift"], "Single anchor: insufficient data, no drift")

    # --- 5.8: Multiple cross-validations tracked ---

    check(len(sync.cross_validations) == 2,
          f"2 cross-validations tracked ({len(sync.cross_validations)})")

    # ═══════════════════════════════════════════════════════════
    # SECTION 6: INTEGRATED SCENARIO
    # ═══════════════════════════════════════════════════════════

    print("Section 6: Integrated Scenario")

    # End-to-end: register auditors → stake → audit → certify → challenge

    int_engine = AuditIncentiveEngine()
    for i in range(3):
        int_engine.register_auditor(f"lct:int:auditor:{i}", 1000.0)
    int_engine.register_auditor("lct:int:challenger", 500.0)
    int_engine.register_auditor("lct:int:panel:1", 500.0)
    int_engine.register_auditor("lct:int:panel:2", 500.0)
    int_engine.register_auditor("lct:int:panel:3", 500.0)

    # Step 1: Auditors stake
    for i in range(3):
        staked = int_engine.stake_for_audit(f"lct:int:auditor:{i}")
        check(staked, f"Auditor {i} staked for audit")

    # Step 2: Submit attestations
    int_policy = QuorumPolicy(required_approvals=2, total_auditors=3, max_abstentions=1)
    int_qa = QuorumAuthority(int_policy)
    for i in range(3):
        int_qa.register_auditor(f"lct:int:auditor:{i}", f"int-key-{i}")

    int_atts = [
        int_qa.submit_attestation(f"lct:int:auditor:0", AuditVote.APPROVE, ComplianceLevel.SUBSTANTIAL),
        int_qa.submit_attestation(f"lct:int:auditor:1", AuditVote.APPROVE, ComplianceLevel.SUBSTANTIAL),
        int_qa.submit_attestation(f"lct:int:auditor:2", AuditVote.REJECT, ComplianceLevel.PARTIAL),
    ]

    # Step 3: Issue quorum certificate
    int_entity = make_entity("lct:int:ai:bot", "Integration Bot", t3=0.72, hw=4)
    int_cert = int_qa.issue_if_quorum(int_entity, make_assessments(7), int_atts)
    check(int_cert is not None, "Quorum certificate issued (2-of-3)")
    check(int_cert.compliance_level == ComplianceLevel.SUBSTANTIAL,
          "Consensus: SUBSTANTIAL")

    # Step 4: Complete audits → release stakes + rewards
    for i in range(3):
        int_engine.complete_audit(f"lct:int:auditor:{i}")

    for i in range(3):
        acct = int_engine.accounts[f"lct:int:auditor:{i}"]
        check(acct.stake_locked == 0.0, f"Auditor {i} stake released")
        check(acct.atp_balance > 1000.0,
              f"Auditor {i} rewarded: {acct.atp_balance} > 1000")

    # Step 5: Challenge the certificate
    int_protocol = ChallengeProtocol(int_engine, panel_size=3)
    int_challenge = int_protocol.file_challenge(
        "lct:int:challenger", int_cert.cert_id,
        "Bias audit used unrepresentative sample",
        ["Statistical analysis showing sampling bias"]
    )
    check(int_challenge is not None, "Challenge filed against quorum cert")

    # Step 6: Panel resolves — challenge dismissed
    int_protocol.submit_panel_vote(int_challenge, "lct:int:panel:1", "dismissed")
    int_protocol.submit_panel_vote(int_challenge, "lct:int:panel:2", "dismissed")
    int_protocol.submit_panel_vote(int_challenge, "lct:int:panel:3", "upheld")

    int_result = int_protocol.resolve_challenge(
        int_challenge,
        ["lct:int:auditor:0", "lct:int:auditor:1"]
    )
    check(int_result["status"] == "dismissed",
          "Challenge dismissed (2-1 in favor of original audit)")
    check(int_engine.accounts["lct:int:challenger"].atp_balance == 400.0,
          f"Challenger lost 100 ATP (stake forfeited): {int_engine.accounts['lct:int:challenger'].atp_balance}")

    # Original auditors NOT slashed
    check(int_engine.accounts["lct:int:auditor:0"].audits_overturned == 0,
          "Auditor 0 not overturned (challenge dismissed)")

    # Step 7: Build fractal composition
    sub1 = FractalAuditNode(
        entity=make_entity("lct:int:sub:1", "Sub-Agent 1", t3=0.68),
        certificate=int_qa.issue_if_quorum(
            make_entity("lct:int:sub:1", "Sub-Agent 1", t3=0.68),
            make_assessments(7), int_atts
        )
    )
    sub2 = FractalAuditNode(
        entity=make_entity("lct:int:sub:2", "Sub-Agent 2", t3=0.71),
        certificate=int_qa.issue_if_quorum(
            make_entity("lct:int:sub:2", "Sub-Agent 2", t3=0.71),
            make_assessments(6), int_atts
        )
    )
    org_node = FractalAuditNode(
        entity=int_entity, certificate=int_cert,
        children=[sub1, sub2]
    )

    int_composer = FractalAuditComposer()
    org_level = int_composer.compose(org_node)
    check(org_level == ComplianceLevel.SUBSTANTIAL,
          f"Org composite: {org_level.value} (all ≥ SUBSTANTIAL)")

    org_t3 = int_composer.compute_composite_t3(org_node)
    check(0.65 < org_t3 < 0.75,
          f"Org composite T3 = {org_t3:.4f} (weighted avg in range)")

    # Step 8: Cross-federation sync
    int_sync = CrossFederationAuditSync()
    local_hashes = [int_cert.cert_hash, sub1.certificate.cert_hash, sub2.certificate.cert_hash]

    int_sync.submit_anchor("fed:local", local_hashes, sequence=1)
    int_sync.submit_anchor("fed:partner", local_hashes, sequence=1)  # Same hashes = synced

    int_cv = int_sync.cross_validate("fed:local", "fed:partner", int_entity.lct_id)
    check(int_cv["valid"], "Cross-federation sync validates with matching hashes")

    # ─── Summary ──────────────────────────────────────────────

    total = passed + failed
    print(f"\n{'='*60}")
    print(f"Advanced Audit Certification: {passed}/{total} checks passed")
    if failed > 0:
        print(f"  {failed} FAILED")
    else:
        print("  All checks passed!")
    print(f"{'='*60}")

    return passed, failed


if __name__ == "__main__":
    run_checks()
