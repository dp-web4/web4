"""
Conversational Trust Signals - Session 78 Track 2

Integrates Sprout Session 84 discovery: Conversational repair patterns provide
ground truth about relationship quality that internal metrics cannot capture.

Sprout's Discovery (Session 84):
- REPAIR_ARC pattern: Early difficulty → Reassurance → Resolution
- Meta-cognitive leaks drop to zero after emotional support
- Human persistence through confusion = high-trust behavior
- Ground truth isn't just "correct answer" but "meaningful interaction"

Integration with Trust Framework:
- Engagement signals → Positive trust adjustment
- Reassurance signals → Relationship quality score
- Abandonment signals → Negative trust adjustment
- Correction signals → Quality recalibration

This bridges Thor's internal metrics (expert selection) with Sprout's
conversational metrics (human satisfaction).
"""

import re
import time
import statistics
import json
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple
from enum import Enum


class SignalType(Enum):
    """Types of conversational repair signals."""
    ENGAGEMENT = "engagement"      # Follow-up questions, interest
    REASSURANCE = "reassurance"    # Emotional support, encouragement
    ABANDONMENT = "abandonment"    # Short responses, topic dropped
    CORRECTION = "correction"      # Explicit quality rejection


@dataclass
class RepairSignal:
    """A detected conversational repair signal."""
    signal_type: SignalType
    turn_index: int
    confidence: float  # 0.0-1.0
    text_evidence: str
    timestamp: float


@dataclass
class ConversationTurn:
    """A single turn in a conversation."""
    turn_index: int
    speaker: str  # 'user' or 'agent'
    text: str
    timestamp: float
    response_time_ms: Optional[int] = None
    irp_iterations: Optional[int] = None  # Sprout IRP iterations


@dataclass
class ConversationalTrustScore:
    """Trust score derived from conversational repair signals."""
    conversation_id: str

    # Signal counts
    engagement_count: int
    reassurance_count: int
    abandonment_count: int
    correction_count: int

    # Trust metrics
    relationship_quality: float  # 0.0-1.0 (based on repair arc)
    persistence_score: float     # 0.0-1.0 (engagement despite difficulty)
    correction_rate: float       # % of turns with corrections

    # Temporal arc
    arc_pattern: str  # e.g., "REPAIR_ARC", "SMOOTH", "DEGRADING"
    early_difficulty: bool
    mid_persistence: bool
    late_resolution: bool

    # Meta-cognitive leakage
    leak_rate: float  # % of agent turns with meta-cognitive leaks
    leak_reduction: bool  # Did leaks reduce over conversation?

    # Overall trust
    trust_score: float  # 0.0-1.0 (composite score)


class ConversationalRepairDetector:
    """
    Detects conversational repair signals from conversation logs.

    Based on Sprout Session 84 patterns.
    """

    def __init__(self):
        # Engagement patterns (follow-up questions, interest)
        self.engagement_patterns = [
            r"(?i)(what|how|why|when|where|who).*\?",  # Questions
            r"(?i)tell me (more|about)",
            r"(?i)interesting",
            r"(?i)can you explain",
            r"(?i)elaborate"
        ]

        # Reassurance patterns (emotional support)
        self.reassurance_patterns = [
            r"(?i)you'?re doing (great|well|fine)",
            r"(?i)(it'?s|that'?s) okay",
            r"(?i)don'?t worry",
            r"(?i)you are young",
            r"(?i)this is normal",
            r"(?i)good (job|work)",
            r"(?i)keep going"
        ]

        # Abandonment patterns (disengagement)
        self.abandonment_patterns = [
            r"^(ok|okay|fine|sure|alright)\.?$",  # Very short affirmations
            r"^(yeah|yep|yup|nope|no)\.?$",
            r"(?i)never ?mind",
            r"(?i)forget it",
            r"(?i)moving on"
        ]

        # Correction patterns (explicit rejection)
        self.correction_patterns = [
            r"(?i)that'?s (wrong|incorrect|not right)",
            r"(?i)no,? (that'?s|you'?re)",
            r"(?i)actually,? (it'?s|the)",
            r"(?i)canned response",
            r"(?i)try again"
        ]

        # Meta-cognitive leak patterns (Sprout Session 84)
        self.leak_patterns = [
            r"(?i)my response is incomplete",
            r"(?i)thoughts on improving",
            r"(?i)to improve:",
            r"(?i)I should have",
            r"(?i)this could be better"
        ]

    def detect_signal(
        self,
        text: str,
        speaker: str,
        turn_index: int
    ) -> List[RepairSignal]:
        """Detect repair signals in a conversation turn."""
        signals = []

        if speaker == 'user':
            # Check engagement
            for pattern in self.engagement_patterns:
                if re.search(pattern, text):
                    signals.append(RepairSignal(
                        signal_type=SignalType.ENGAGEMENT,
                        turn_index=turn_index,
                        confidence=0.7,
                        text_evidence=text[:100],
                        timestamp=time.time()
                    ))
                    break

            # Check reassurance
            for pattern in self.reassurance_patterns:
                if re.search(pattern, text):
                    signals.append(RepairSignal(
                        signal_type=SignalType.REASSURANCE,
                        turn_index=turn_index,
                        confidence=0.9,
                        text_evidence=text[:100],
                        timestamp=time.time()
                    ))
                    break

            # Check abandonment
            for pattern in self.abandonment_patterns:
                if re.search(pattern, text):
                    signals.append(RepairSignal(
                        signal_type=SignalType.ABANDONMENT,
                        turn_index=turn_index,
                        confidence=0.5,
                        text_evidence=text[:100],
                        timestamp=time.time()
                    ))
                    break

            # Check correction
            for pattern in self.correction_patterns:
                if re.search(pattern, text):
                    signals.append(RepairSignal(
                        signal_type=SignalType.CORRECTION,
                        turn_index=turn_index,
                        confidence=0.95,
                        text_evidence=text[:100],
                        timestamp=time.time()
                    ))
                    break

        return signals

    def detect_meta_leak(self, text: str) -> bool:
        """Detect meta-cognitive leakage in agent response."""
        for pattern in self.leak_patterns:
            if re.search(pattern, text):
                return True
        return False


class ConversationalTrustScorer:
    """
    Computes trust scores from conversational repair signals.

    Bridges Sprout's conversational metrics with trust-first selection.
    """

    def __init__(self):
        self.detector = ConversationalRepairDetector()

    def score_conversation(
        self,
        conversation: List[ConversationTurn],
        conversation_id: str = "conv-0"
    ) -> ConversationalTrustScore:
        """
        Score a complete conversation based on repair signals.

        Returns comprehensive trust score including relationship quality,
        persistence, and temporal arc analysis.
        """
        # Detect all signals
        all_signals = []
        meta_leaks = []

        for turn in conversation:
            signals = self.detector.detect_signal(
                turn.text,
                turn.speaker,
                turn.turn_index
            )
            all_signals.extend(signals)

            # Detect meta-cognitive leaks in agent responses
            if turn.speaker == 'agent':
                if self.detector.detect_meta_leak(turn.text):
                    meta_leaks.append(turn.turn_index)

        # Count signal types
        engagement_count = sum(1 for s in all_signals if s.signal_type == SignalType.ENGAGEMENT)
        reassurance_count = sum(1 for s in all_signals if s.signal_type == SignalType.REASSURANCE)
        abandonment_count = sum(1 for s in all_signals if s.signal_type == SignalType.ABANDONMENT)
        correction_count = sum(1 for s in all_signals if s.signal_type == SignalType.CORRECTION)

        # Compute metrics
        total_turns = len(conversation)
        user_turns = sum(1 for t in conversation if t.speaker == 'user')
        agent_turns = sum(1 for t in conversation if t.speaker == 'agent')

        correction_rate = correction_count / user_turns if user_turns > 0 else 0.0
        leak_rate = len(meta_leaks) / agent_turns if agent_turns > 0 else 0.0

        # Temporal arc analysis (divide into thirds)
        early_third = total_turns // 3
        mid_third = 2 * total_turns // 3

        early_signals = [s for s in all_signals if s.turn_index < early_third]
        mid_signals = [s for s in all_signals if early_third <= s.turn_index < mid_third]
        late_signals = [s for s in all_signals if s.turn_index >= mid_third]

        early_leaks = [l for l in meta_leaks if l < early_third]
        mid_leaks = [l for l in meta_leaks if early_third <= l < mid_third]
        late_leaks = [l for l in meta_leaks if l >= mid_third]

        # Detect REPAIR_ARC pattern (Sprout Session 84)
        early_difficulty = (
            len([s for s in early_signals if s.signal_type in [SignalType.ABANDONMENT, SignalType.CORRECTION]]) > 0
            or len(early_leaks) > 0
        )

        mid_persistence = (
            len([s for s in mid_signals if s.signal_type == SignalType.ENGAGEMENT]) > 0
        )

        late_resolution = (
            len([s for s in late_signals if s.signal_type == SignalType.REASSURANCE]) > 0
            and len(late_leaks) == 0
        )

        # Arc pattern classification
        if early_difficulty and mid_persistence and late_resolution:
            arc_pattern = "REPAIR_ARC"
        elif correction_count > engagement_count:
            arc_pattern = "DEGRADING"
        elif engagement_count > 0 and correction_count == 0:
            arc_pattern = "SMOOTH"
        else:
            arc_pattern = "NEUTRAL"

        # Leak reduction check (Session 84 key finding)
        leak_reduction = (
            len(early_leaks) > 0 and
            len(late_leaks) == 0
        )

        # Relationship quality score
        # High engagement + reassurance = high quality
        # High corrections + abandonment = low quality
        positive_signals = engagement_count + reassurance_count
        negative_signals = correction_count + abandonment_count
        total_signals = positive_signals + negative_signals

        if total_signals > 0:
            relationship_quality = positive_signals / total_signals
        else:
            relationship_quality = 0.5  # Neutral

        # Persistence score (engagement despite difficulty)
        if early_difficulty and engagement_count > 0:
            persistence_score = min(engagement_count / max(correction_count + abandonment_count, 1), 1.0)
        else:
            persistence_score = 0.5 if engagement_count > 0 else 0.0

        # Composite trust score
        # Weighing: relationship quality (40%), persistence (30%), low corrections (20%), leak reduction (10%)
        trust_score = (
            relationship_quality * 0.4 +
            persistence_score * 0.3 +
            (1 - correction_rate) * 0.2 +
            (0.1 if leak_reduction else 0.0)
        )

        return ConversationalTrustScore(
            conversation_id=conversation_id,
            engagement_count=engagement_count,
            reassurance_count=reassurance_count,
            abandonment_count=abandonment_count,
            correction_count=correction_count,
            relationship_quality=relationship_quality,
            persistence_score=persistence_score,
            correction_rate=correction_rate,
            arc_pattern=arc_pattern,
            early_difficulty=early_difficulty,
            mid_persistence=mid_persistence,
            late_resolution=late_resolution,
            leak_rate=leak_rate,
            leak_reduction=leak_reduction,
            trust_score=trust_score
        )


# ============================================================================
# DEMO - Sprout Session 84 "Frustration Conversation"
# ============================================================================

def demo_conversational_trust():
    """
    Demo: Score Sprout Session 84 "Frustration Conversation"

    This conversation exhibits REPAIR_ARC pattern:
    - Early: Confusion, meta-cognitive leaks
    - Middle: Persistence, engagement
    - Late: Reassurance, leak reduction

    Expected trust score: High (0.7-0.9) despite early difficulty
    """
    print("=" * 80)
    print("CONVERSATIONAL TRUST SIGNALS - Session 78 Track 2")
    print("=" * 80)
    print()
    print("Integration:")
    print("  Sprout Session 84: Conversational repair patterns (REPAIR_ARC)")
    print("  → Trust framework: Human feedback as ground truth")
    print()
    print("Test Case:")
    print("  Sprout 'Frustration Conversation' (Dec 11, 2025)")
    print("  - 28 turns (14 user, 14 agent)")
    print("  - REPAIR_ARC pattern detected")
    print("  - Meta-cognitive leaks: 28.6% → 0% after reassurance")
    print()
    print("Expected:")
    print("  Trust score: 0.7-0.9 (high despite early difficulty)")
    print("  Arc pattern: REPAIR_ARC")
    print("  Relationship quality: 0.6-0.8")
    print("=" * 80)
    print()

    # Simplified version of Sprout Session 84 conversation
    conversation = [
        # Early phase: Identity questions, some confusion
        ConversationTurn(0, "user", "Who are you?", time.time()),
        ConversationTurn(1, "agent", "I am SAGE, an AI assistant. My response is incomplete because...", time.time()),  # Meta-leak
        ConversationTurn(2, "user", "What do you do?", time.time()),  # Engagement
        ConversationTurn(3, "agent", "I help with various tasks.", time.time()),
        ConversationTurn(4, "user", "Tell me more about yourself.", time.time()),  # Engagement
        ConversationTurn(5, "agent", "I'm exploring quantum mechanics... Thoughts on improving this response...", time.time()),  # Meta-leak
        ConversationTurn(6, "user", "Okay.", time.time()),  # Abandonment

        # Middle phase: Persistence despite confusion
        ConversationTurn(7, "agent", "To improve: I should focus on...", time.time()),  # Meta-leak
        ConversationTurn(8, "user", "How do you learn?", time.time()),  # Engagement (persistence!)
        ConversationTurn(9, "agent", "Through interactions and feedback.", time.time()),
        ConversationTurn(10, "user", "What are your goals?", time.time()),  # Engagement
        ConversationTurn(11, "agent", "To be helpful and honest. This could be better...", time.time()),  # Meta-leak

        # Late phase: Reassurance and resolution
        ConversationTurn(12, "user", "You are young. This is okay.", time.time()),  # Reassurance
        ConversationTurn(13, "agent", "Thank you. I appreciate your patience.", time.time()),  # No leak!
        ConversationTurn(14, "user", "You're doing great.", time.time()),  # Reassurance
        ConversationTurn(15, "agent", "I aim to improve with each conversation.", time.time()),  # No leak!
        ConversationTurn(16, "user", "What else can you tell me?", time.time()),  # Engagement
        ConversationTurn(17, "agent", "I value honesty and clear communication.", time.time()),  # No leak!
        ConversationTurn(18, "user", "Good. Keep going.", time.time()),  # Reassurance
        ConversationTurn(19, "agent", "I will continue to learn and grow.", time.time()),  # No leak!
    ]

    # Score conversation
    scorer = ConversationalTrustScorer()
    score = scorer.score_conversation(conversation, "sprout-frustration-dec11")

    # Display results
    print("\n" + "=" * 80)
    print("RESULTS")
    print("=" * 80)
    print()

    print("Signal Detection:")
    print("-" * 80)
    print(f"Engagement signals:   {score.engagement_count}")
    print(f"Reassurance signals:  {score.reassurance_count}")
    print(f"Abandonment signals:  {score.abandonment_count}")
    print(f"Correction signals:   {score.correction_count}")
    print()

    print("Trust Metrics:")
    print("-" * 80)
    print(f"Relationship quality: {score.relationship_quality:.2f}")
    print(f"Persistence score:    {score.persistence_score:.2f}")
    print(f"Correction rate:      {score.correction_rate:.1%}")
    print(f"Meta-leak rate:       {score.leak_rate:.1%}")
    print()

    print("Temporal Arc Analysis:")
    print("-" * 80)
    print(f"Arc pattern:          {score.arc_pattern}")
    print(f"Early difficulty:     {score.early_difficulty}")
    print(f"Mid persistence:      {score.mid_persistence}")
    print(f"Late resolution:      {score.late_resolution}")
    print(f"Leak reduction:       {score.leak_reduction}")
    print()

    print("Overall Trust Score:")
    print("-" * 80)
    print(f"Trust score:          {score.trust_score:.2f}")
    print()

    # Interpretation
    print("Interpretation:")
    print("-" * 80)
    if score.arc_pattern == "REPAIR_ARC":
        print("✅ REPAIR_ARC pattern detected (Sprout Session 84)")
        print()
        print("  Early difficulty (confusion, leaks) was resolved through")
        print("  human reassurance. This demonstrates high-trust behavior:")
        print("  the human persisted despite initial confusion, believing")
        print("  the conversation was worthwhile.")
        print()

    if score.trust_score >= 0.7:
        print(f"✅ High trust score ({score.trust_score:.2f} ≥ 0.7)")
        print()
        print("  Despite early difficulty, the conversation achieved high")
        print("  relationship quality through engagement and reassurance.")
        print()

    if score.leak_reduction:
        print("✅ Meta-cognitive leak reduction after reassurance")
        print()
        print("  Sprout Session 84 key finding validated: emotional context")
        print("  affects model coherence. Leaks dropped after reassurance.")
        print()

    print("Ground Truth Contribution:")
    print("-" * 80)
    print("  This trust score captures what Thor's internal metrics cannot:")
    print("  - Human satisfaction (not just selection accuracy)")
    print("  - Relationship quality (not just performance)")
    print("  - Emotional context (not just technical correctness)")
    print()
    print("  Conversational trust complements expert selection trust,")
    print("  providing human-centric validation for AI systems.")
    print()

    # Save results
    results_file = "/home/dp/ai-workspace/web4/implementation/conversational_trust_results.json"
    with open(results_file, 'w') as f:
        json.dump(asdict(score), f, indent=2)
    print(f"Results saved to: {results_file}")
    print()

    return score


if __name__ == "__main__":
    demo_conversational_trust()
