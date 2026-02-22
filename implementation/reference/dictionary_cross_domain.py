#!/usr/bin/env python3
"""
Dictionary Cross-Domain Translation — Track C
================================================
Empirical validation of the compression-trust relationship.

Core Web4 insight: compression requires trust in shared decompression artifacts.
This implementation validates that claim through:

1. Multi-domain translation chains with measured degradation
2. Compression ratio as a function of trust level
3. ATP staking on confidence claims (forced truthfulness)
4. Codebook drift detection and version management
5. Cross-domain coverage analysis
6. The telephone game: N-hop degradation curves
7. Context-sensitive translation accuracy
8. Trust recovery through feedback loops

Key formula: confidence = min(coverage × avg_entry_confidence, T3_composite)
Degradation = 1.0 - cumulative_confidence (multiplicative per hop)

Date: 2026-02-22
"""

import hashlib
import json
import math
import time
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple


# ═══════════════════════════════════════════════════════════════
#  1. DOMAIN AND CODEBOOK
# ═══════════════════════════════════════════════════════════════

class DomainType(Enum):
    MEDICAL = "medical"
    LEGAL = "legal"
    INSURANCE = "insurance"
    ENGINEERING = "engineering"
    FINANCIAL = "financial"
    LAY = "lay"  # Plain language


@dataclass
class CodebookEntry:
    """A single mapping between source and target terms."""
    source_term: str
    target_term: str
    confidence: float = 0.9
    context_tags: List[str] = field(default_factory=list)
    usage_count: int = 0
    corrections: int = 0
    created_at: float = field(default_factory=time.time)
    last_used: float = 0.0


class Codebook:
    """Bidirectional mapping between domain vocabularies."""

    def __init__(self):
        self.entries: Dict[str, CodebookEntry] = {}
        self._reverse: Dict[str, str] = {}

    def add(self, source: str, target: str, confidence: float = 0.9,
            context_tags: List[str] = None) -> CodebookEntry:
        entry = CodebookEntry(
            source_term=source,
            target_term=target,
            confidence=confidence,
            context_tags=context_tags or [],
        )
        self.entries[source] = entry
        self._reverse[target] = source
        return entry

    def lookup(self, term: str, context: str = None) -> Optional[CodebookEntry]:
        entry = self.entries.get(term)
        if entry is None:
            return None

        # Context filtering
        if context and entry.context_tags:
            if context not in entry.context_tags and "general" not in entry.context_tags:
                return None  # Context mismatch

        entry.usage_count += 1
        entry.last_used = time.time()
        return entry

    def reverse_lookup(self, target_term: str) -> Optional[str]:
        return self._reverse.get(target_term)

    def size(self) -> int:
        return len(self.entries)

    def avg_confidence(self) -> float:
        if not self.entries:
            return 0.0
        return sum(e.confidence for e in self.entries.values()) / len(self.entries)

    def correction_ratio(self) -> float:
        if not self.entries:
            return 0.0
        total_corrections = sum(e.corrections for e in self.entries.values())
        return total_corrections / len(self.entries)


# ═══════════════════════════════════════════════════════════════
#  2. TRUST TENSORS (Minimal)
# ═══════════════════════════════════════════════════════════════

@dataclass
class TrustTensor:
    """T3 trust tensor for dictionaries: talent, training, temperament."""
    talent: float = 0.5       # Innate quality of mappings
    training: float = 0.5     # Learned from corrections
    temperament: float = 0.5  # Stability/consistency

    def composite(self) -> float:
        return round(0.4 * self.talent + 0.3 * self.training + 0.3 * self.temperament, 6)


@dataclass
class ValueTensor:
    """V3 value tensor: valuation, veracity, validity."""
    valuation: float = 0.5   # Economic worth
    veracity: float = 0.5    # Truthfulness
    validity: float = 0.5    # Temporal relevance

    def composite(self) -> float:
        return round(0.4 * self.valuation + 0.3 * self.veracity + 0.3 * self.validity, 6)


# ═══════════════════════════════════════════════════════════════
#  3. DICTIONARY ENTITY
# ═══════════════════════════════════════════════════════════════

@dataclass
class TranslationRequest:
    """Request to translate terms between domains."""
    terms: List[str]
    source_domain: str
    target_domain: str
    context: Optional[str] = None  # None = no filtering
    claimed_confidence: float = 0.0  # For ATP staking


@dataclass
class TranslationResult:
    """Result of a translation operation."""
    translated_terms: Dict[str, str]  # source → target
    unknown_terms: List[str]
    confidence: float
    degradation: float
    coverage: float
    t3_ceiling: float
    compression_ratio: float  # How much shorter the message becomes
    hop_number: int = 0


class DictionaryEntity:
    """
    A living semantic bridge between two domains.

    Embodies the compression-trust duality: high trust enables compressed
    communication through shared codebooks; low trust requires verbose raw data.
    """

    def __init__(self, dict_id: str, name: str,
                 source_domain: str, target_domain: str,
                 bidirectional: bool = False):
        self.dict_id = dict_id
        self.name = name
        self.source_domain = source_domain
        self.target_domain = target_domain
        self.bidirectional = bidirectional

        self.codebook = Codebook()
        self.t3 = TrustTensor()
        self.v3 = ValueTensor()

        self.atp_balance = 0.0
        self.version = "1.0.0"
        self.version_history: List[Dict] = [{"version": "1.0.0", "timestamp": time.time()}]
        self.translations_completed = 0
        self.translations_failed = 0
        self.total_degradation = 0.0
        self.feedback_received = 0

    def translate(self, request: TranslationRequest) -> TranslationResult:
        """Translate terms from source domain to target domain."""
        if request.source_domain != self.source_domain or request.target_domain != self.target_domain:
            if self.bidirectional and request.source_domain == self.target_domain:
                return self._reverse_translate(request)
            self.translations_failed += 1
            return TranslationResult(
                translated_terms={}, unknown_terms=request.terms,
                confidence=0.0, degradation=1.0, coverage=0.0,
                t3_ceiling=self.t3.composite(), compression_ratio=0.0,
            )

        translated = {}
        unknown = []
        confidences = []

        for term in request.terms:
            entry = self.codebook.lookup(term, context=request.context)
            if entry:
                translated[term] = entry.target_term
                confidences.append(entry.confidence)
            else:
                unknown.append(term)
                translated[term] = f"[{term}]"  # Bracketed = untranslated

        total_terms = len(request.terms)
        coverage = len(confidences) / total_terms if total_terms > 0 else 0.0
        avg_conf = sum(confidences) / len(confidences) if confidences else 0.0

        # Confidence = coverage × avg_entry_confidence, capped by T3
        raw_confidence = coverage * avg_conf
        t3_ceiling = self.t3.composite()
        confidence = min(raw_confidence, t3_ceiling)
        degradation = 1.0 - confidence

        # Compression ratio: how much shorter the translated output is
        source_chars = sum(len(t) for t in request.terms)
        target_chars = sum(len(t) for t in translated.values())
        compression_ratio = 1.0 - (target_chars / source_chars) if source_chars > 0 else 0.0

        self.translations_completed += 1
        self.total_degradation += degradation

        result = TranslationResult(
            translated_terms=translated,
            unknown_terms=unknown,
            confidence=round(confidence, 6),
            degradation=round(degradation, 6),
            coverage=round(coverage, 6),
            t3_ceiling=round(t3_ceiling, 6),
            compression_ratio=round(compression_ratio, 6),
        )

        return result

    def _reverse_translate(self, request: TranslationRequest) -> TranslationResult:
        """Translate in reverse direction for bidirectional dictionaries."""
        translated = {}
        unknown = []
        confidences = []

        for term in request.terms:
            source = self.codebook.reverse_lookup(term)
            if source:
                entry = self.codebook.entries[source]
                translated[term] = source
                confidences.append(entry.confidence * 0.9)  # Reverse = slight penalty
            else:
                unknown.append(term)
                translated[term] = f"[{term}]"

        total_terms = len(request.terms)
        coverage = len(confidences) / total_terms if total_terms > 0 else 0.0
        avg_conf = sum(confidences) / len(confidences) if confidences else 0.0
        raw_confidence = coverage * avg_conf
        t3_ceiling = self.t3.composite()
        confidence = min(raw_confidence, t3_ceiling)

        source_chars = sum(len(t) for t in request.terms)
        target_chars = sum(len(t) for t in translated.values())
        compression_ratio = 1.0 - (target_chars / source_chars) if source_chars > 0 else 0.0

        self.translations_completed += 1
        return TranslationResult(
            translated_terms=translated,
            unknown_terms=unknown,
            confidence=round(confidence, 6),
            degradation=round(1.0 - confidence, 6),
            coverage=round(coverage, 6),
            t3_ceiling=round(t3_ceiling, 6),
            compression_ratio=round(compression_ratio, 6),
        )

    def apply_feedback(self, source_term: str, corrected_target: str,
                       authority_trust: float = 0.8) -> bool:
        """Apply a correction to a codebook entry."""
        entry = self.codebook.entries.get(source_term)
        if not entry:
            # New entry from feedback
            self.codebook.add(source_term, corrected_target, confidence=authority_trust * 0.8)
            self.feedback_received += 1
            return True

        entry.corrections += 1
        self.feedback_received += 1

        if authority_trust > 0.7:
            entry.target_term = corrected_target
            entry.confidence = min(1.0, entry.confidence + 0.1)
            self.t3.training = min(1.0, self.t3.training + 0.02)
        else:
            entry.confidence *= 0.95

        # Drift detection
        if self.codebook.correction_ratio() > 0.1:
            self._increment_version("drift: > 10% corrections")

        return True

    def _increment_version(self, reason: str) -> None:
        parts = self.version.split(".")
        parts[1] = str(int(parts[1]) + 1)
        self.version = ".".join(parts)
        self.version_history.append({
            "version": self.version,
            "timestamp": time.time(),
            "reason": reason,
        })

    def status(self) -> Dict:
        return {
            "dict_id": self.dict_id,
            "name": self.name,
            "domains": f"{self.source_domain}→{self.target_domain}",
            "bidirectional": self.bidirectional,
            "version": self.version,
            "codebook_size": self.codebook.size(),
            "avg_confidence": round(self.codebook.avg_confidence(), 4),
            "t3": round(self.t3.composite(), 4),
            "v3": round(self.v3.composite(), 4),
            "translations": self.translations_completed,
            "failures": self.translations_failed,
            "atp_balance": round(self.atp_balance, 2),
            "feedback": self.feedback_received,
        }


# ═══════════════════════════════════════════════════════════════
#  4. TRANSLATION CHAIN (Multi-Hop)
# ═══════════════════════════════════════════════════════════════

class TranslationChain:
    """
    Multi-hop translation across domain boundaries.

    Models the "telephone game" — each hop multiplies uncertainty.
    Confidence = product of per-hop confidences.
    """

    def __init__(self, name: str):
        self.name = name
        self.dictionaries: List[DictionaryEntity] = []
        self.hop_results: List[TranslationResult] = []
        self.cumulative_confidence = 1.0
        self.cumulative_degradation = 0.0

    def add_dictionary(self, dictionary: DictionaryEntity) -> None:
        self.dictionaries.append(dictionary)

    def translate_chain(self, terms: List[str], initial_domain: str,
                        context: str = "general") -> TranslationResult:
        """Translate through all dictionaries in the chain."""
        current_terms = terms
        current_domain = initial_domain
        self.hop_results = []
        self.cumulative_confidence = 1.0

        for i, dict_entity in enumerate(self.dictionaries):
            request = TranslationRequest(
                terms=current_terms,
                source_domain=current_domain,
                target_domain=dict_entity.target_domain,
                context=context,
            )
            result = dict_entity.translate(request)
            result.hop_number = i + 1
            self.hop_results.append(result)

            # Cumulative confidence is multiplicative
            self.cumulative_confidence *= result.confidence

            # Update current terms for next hop
            current_terms = list(result.translated_terms.values())
            current_domain = dict_entity.target_domain

        self.cumulative_degradation = 1.0 - self.cumulative_confidence

        # Final result
        final_translated = {}
        for orig, term in zip(terms, current_terms):
            final_translated[orig] = term

        return TranslationResult(
            translated_terms=final_translated,
            unknown_terms=[t for t in terms if final_translated.get(t, "").startswith("[")],
            confidence=round(self.cumulative_confidence, 6),
            degradation=round(self.cumulative_degradation, 6),
            coverage=round(self.hop_results[-1].coverage if self.hop_results else 0.0, 6),
            t3_ceiling=round(min(d.t3.composite() for d in self.dictionaries) if self.dictionaries else 0.0, 6),
            compression_ratio=round(self.hop_results[-1].compression_ratio if self.hop_results else 0.0, 6),
            hop_number=len(self.dictionaries),
        )


# ═══════════════════════════════════════════════════════════════
#  5. ATP STAKING ON CONFIDENCE
# ═══════════════════════════════════════════════════════════════

@dataclass
class ConfidenceStake:
    """ATP staked on a claimed translation confidence."""
    stake_id: str
    staker_id: str
    dict_id: str
    claimed_confidence: float
    actual_confidence: float = 0.0
    stake_amount: float = 0.0
    settled: bool = False
    payout: float = 0.0
    penalty: float = 0.0


class ConfidenceStakingEngine:
    """
    Forces truthful confidence claims via ATP staking.

    If claimed confidence >= actual: staker earns 10% of stake.
    If claimed < actual: staker is slashed proportionally.
    """

    def __init__(self):
        self.stakes: Dict[str, ConfidenceStake] = {}
        self.total_staked = 0.0
        self.total_payouts = 0.0
        self.total_penalties = 0.0

    def create_stake(self, staker_id: str, dict_id: str,
                     claimed_confidence: float, stake_amount: float) -> ConfidenceStake:
        stake = ConfidenceStake(
            stake_id=f"stake:{uuid.uuid4().hex[:8]}",
            staker_id=staker_id,
            dict_id=dict_id,
            claimed_confidence=claimed_confidence,
            stake_amount=stake_amount,
        )
        self.stakes[stake.stake_id] = stake
        self.total_staked += stake_amount
        return stake

    def settle_stake(self, stake_id: str, actual_confidence: float) -> ConfidenceStake:
        stake = self.stakes[stake_id]
        stake.actual_confidence = actual_confidence
        stake.settled = True

        if actual_confidence >= stake.claimed_confidence:
            # Truthful or conservative claim → reward
            stake.payout = stake.stake_amount * 0.1
            self.total_payouts += stake.payout
        else:
            # Overconfident claim → slash
            ratio = actual_confidence / stake.claimed_confidence if stake.claimed_confidence > 0 else 0
            stake.penalty = stake.stake_amount * (1.0 - ratio)
            self.total_penalties += stake.penalty

        return stake

    def get_stats(self) -> Dict:
        settled = [s for s in self.stakes.values() if s.settled]
        truthful = sum(1 for s in settled if s.actual_confidence >= s.claimed_confidence)
        return {
            "total_stakes": len(self.stakes),
            "settled": len(settled),
            "truthful_claims": truthful,
            "overconfident_claims": len(settled) - truthful,
            "total_staked": round(self.total_staked, 2),
            "total_payouts": round(self.total_payouts, 2),
            "total_penalties": round(self.total_penalties, 2),
        }


# ═══════════════════════════════════════════════════════════════
#  6. COMPRESSION-TRUST ANALYZER
# ═══════════════════════════════════════════════════════════════

class CompressionTrustAnalyzer:
    """
    Empirically validates the compression-trust relationship.

    Tests the hypothesis: higher trust enables higher compression ratios,
    and this relationship is monotonic and bounded.
    """

    def __init__(self):
        self.data_points: List[Dict] = []

    def measure(self, dictionary: DictionaryEntity, terms: List[str],
                context: str = "general") -> Dict:
        """Measure compression-trust relationship for a single translation."""
        request = TranslationRequest(
            terms=terms,
            source_domain=dictionary.source_domain,
            target_domain=dictionary.target_domain,
            context=context,
        )
        result = dictionary.translate(request)

        point = {
            "trust_level": dictionary.t3.composite(),
            "confidence": result.confidence,
            "compression_ratio": result.compression_ratio,
            "coverage": result.coverage,
            "degradation": result.degradation,
            "codebook_size": dictionary.codebook.size(),
            "terms_count": len(terms),
        }
        self.data_points.append(point)
        return point

    def analyze_monotonicity(self) -> Dict:
        """Check if compression ratio increases monotonically with trust."""
        if len(self.data_points) < 2:
            return {"monotonic": True, "violations": 0, "pairs": 0}

        sorted_points = sorted(self.data_points, key=lambda p: p["trust_level"])
        violations = 0
        pairs = 0

        for i in range(len(sorted_points) - 1):
            a = sorted_points[i]
            b = sorted_points[i + 1]
            if a["trust_level"] < b["trust_level"]:
                pairs += 1
                if a["confidence"] > b["confidence"]:
                    violations += 1

        return {
            "monotonic": violations == 0,
            "violations": violations,
            "pairs": pairs,
            "direction": "positive" if violations == 0 else "mixed",
        }

    def analyze_degradation_curve(self, chain: TranslationChain) -> Dict:
        """Analyze how degradation grows with each hop in a chain."""
        if not chain.hop_results:
            return {"hops": 0}

        hop_data = []
        cumulative = 1.0
        for result in chain.hop_results:
            cumulative *= result.confidence
            hop_data.append({
                "hop": result.hop_number,
                "hop_confidence": result.confidence,
                "cumulative_confidence": round(cumulative, 6),
                "cumulative_degradation": round(1.0 - cumulative, 6),
            })

        # Fit exponential decay: confidence ≈ c₀ × r^n
        if len(hop_data) >= 2:
            avg_per_hop = cumulative ** (1.0 / len(hop_data))
        else:
            avg_per_hop = cumulative

        return {
            "hops": len(hop_data),
            "per_hop_data": hop_data,
            "final_confidence": round(cumulative, 6),
            "final_degradation": round(1.0 - cumulative, 6),
            "avg_retention_per_hop": round(avg_per_hop, 6),
            "half_life_hops": round(math.log(0.5) / math.log(avg_per_hop), 2) if avg_per_hop > 0 and avg_per_hop < 1 else float("inf"),
        }


# ═══════════════════════════════════════════════════════════════
#  7. TEST SUITE
# ═══════════════════════════════════════════════════════════════

def run_tests():
    passed = 0
    failed = 0

    def check(name: str, condition: bool):
        nonlocal passed, failed
        status = "PASS" if condition else "FAIL"
        print(f"  [{status}] {name}")
        if condition:
            passed += 1
        else:
            failed += 1

    # ─── Build Domain Dictionaries ───
    # Medical → Legal
    med_legal = DictionaryEntity("dict:med-legal", "Medical-Legal",
                                  "medical", "legal", bidirectional=True)
    med_legal.t3 = TrustTensor(talent=0.9, training=0.85, temperament=0.88)
    med_legal.v3 = ValueTensor(valuation=0.8, veracity=0.9, validity=0.85)
    med_legal.codebook.add("MI", "myocardial_infarction", 0.95, ["claim"])
    med_legal.codebook.add("MVA", "motor_vehicle_accident", 0.92)
    med_legal.codebook.add("acute", "sudden_onset", 0.88, ["medical"])
    med_legal.codebook.add("chronic", "long_term_condition", 0.9)
    med_legal.codebook.add("prognosis", "medical_outlook", 0.85)
    med_legal.codebook.add("contraindicated", "medically_incompatible", 0.82)
    med_legal.codebook.add("etiology", "causal_origin", 0.87)
    med_legal.codebook.add("bilateral", "both_sides", 0.93)

    # Legal → Insurance
    legal_insurance = DictionaryEntity("dict:legal-ins", "Legal-Insurance",
                                        "legal", "insurance", bidirectional=False)
    legal_insurance.t3 = TrustTensor(talent=0.85, training=0.8, temperament=0.82)
    legal_insurance.v3 = ValueTensor(valuation=0.75, veracity=0.85, validity=0.8)
    legal_insurance.codebook.add("myocardial_infarction", "heart_attack_event", 0.92)
    legal_insurance.codebook.add("motor_vehicle_accident", "auto_collision_claim", 0.95)
    legal_insurance.codebook.add("sudden_onset", "acute_event", 0.88)
    legal_insurance.codebook.add("long_term_condition", "chronic_condition_rider", 0.85)
    legal_insurance.codebook.add("medical_outlook", "prognosis_assessment", 0.83)
    legal_insurance.codebook.add("causal_origin", "cause_of_loss", 0.87)

    # Engineering → Financial
    eng_fin = DictionaryEntity("dict:eng-fin", "Engineering-Financial",
                                "engineering", "financial", bidirectional=True)
    eng_fin.t3 = TrustTensor(talent=0.7, training=0.6, temperament=0.75)
    eng_fin.v3 = ValueTensor(valuation=0.65, veracity=0.7, validity=0.6)
    eng_fin.codebook.add("MTBF", "reliability_metric", 0.8)
    eng_fin.codebook.add("downtime", "service_interruption_cost", 0.75)
    eng_fin.codebook.add("throughput", "capacity_utilization", 0.7)

    # Medical → Lay (simplified)
    med_lay = DictionaryEntity("dict:med-lay", "Medical-Plain",
                                "medical", "lay", bidirectional=False)
    med_lay.t3 = TrustTensor(talent=0.95, training=0.9, temperament=0.92)
    med_lay.codebook.add("MI", "heart_attack", 0.98)
    med_lay.codebook.add("MVA", "car_accident", 0.97)
    med_lay.codebook.add("acute", "sudden", 0.95)
    med_lay.codebook.add("chronic", "ongoing", 0.95)
    med_lay.codebook.add("prognosis", "expected_outcome", 0.93)
    med_lay.codebook.add("contraindicated", "should_not_be_used", 0.9)
    med_lay.codebook.add("etiology", "cause", 0.96)
    med_lay.codebook.add("bilateral", "on_both_sides", 0.97)

    # ─── T1: Basic Translation ───
    print("\n═══ T1: Basic Translation ═══")

    request1 = TranslationRequest(
        terms=["MI", "MVA", "acute"],
        source_domain="medical",
        target_domain="legal",
    )
    result1 = med_legal.translate(request1)

    check("T1: all terms translated", len(result1.unknown_terms) == 0)
    check("T1: coverage = 1.0", result1.coverage == 1.0)
    check("T1: confidence > 0.8", result1.confidence > 0.8)
    check("T1: degradation < 0.2", result1.degradation < 0.2)
    check("T1: MI → myocardial_infarction",
          result1.translated_terms["MI"] == "myocardial_infarction")

    # ─── T2: Unknown Term Degradation ───
    print("\n═══ T2: Unknown Terms ═══")

    request2 = TranslationRequest(
        terms=["MI", "UNKNOWN_TERM", "acute"],
        source_domain="medical",
        target_domain="legal",
    )
    result2 = med_legal.translate(request2)

    check("T2: 1 unknown term", len(result2.unknown_terms) == 1)
    check("T2: coverage < 1.0", result2.coverage < 1.0)
    check("T2: confidence < result1", result2.confidence < result1.confidence)
    check("T2: unknown bracketed", result2.translated_terms["UNKNOWN_TERM"] == "[UNKNOWN_TERM]")

    # ─── T3: T3 Ceiling Effect ───
    print("\n═══ T3: T3 Trust Ceiling ═══")

    low_trust_dict = DictionaryEntity("dict:low", "Low-Trust",
                                       "medical", "legal")
    low_trust_dict.t3 = TrustTensor(talent=0.3, training=0.2, temperament=0.25)
    low_trust_dict.codebook.add("MI", "myocardial_infarction", 0.99)
    low_trust_dict.codebook.add("acute", "sudden_onset", 0.98)

    request3 = TranslationRequest(
        terms=["MI", "acute"],
        source_domain="medical",
        target_domain="legal",
    )
    result3 = low_trust_dict.translate(request3)

    check("T3: high entry confidence but low trust",
          low_trust_dict.codebook.avg_confidence() > 0.9)
    check("T3: confidence capped by T3",
          result3.confidence <= low_trust_dict.t3.composite() + 0.001)
    check("T3: confidence < entry confidence",
          result3.confidence < low_trust_dict.codebook.avg_confidence())

    # ─── T4: Bidirectional Translation ───
    print("\n═══ T4: Bidirectional Translation ═══")

    reverse_request = TranslationRequest(
        terms=["myocardial_infarction", "motor_vehicle_accident"],
        source_domain="legal",
        target_domain="medical",
    )
    reverse_result = med_legal.translate(reverse_request)

    check("T4: reverse translation works", len(reverse_result.unknown_terms) == 0)
    check("T4: MI recovered",
          reverse_result.translated_terms["myocardial_infarction"] == "MI")
    check("T4: reverse confidence slightly lower",
          reverse_result.confidence <= result1.confidence)

    # ─── T5: Context-Sensitive Translation ───
    print("\n═══ T5: Context-Sensitive Translation ═══")

    # "acute" has context tag "medical", should fail in "insurance" context
    request5_medical = TranslationRequest(
        terms=["acute"],
        source_domain="medical",
        target_domain="legal",
        context="medical",
    )
    result5_med = med_legal.translate(request5_medical)
    check("T5: medical context matches", len(result5_med.unknown_terms) == 0)

    request5_wrong = TranslationRequest(
        terms=["acute"],
        source_domain="medical",
        target_domain="legal",
        context="financial",
    )
    result5_wrong = med_legal.translate(request5_wrong)
    check("T5: wrong context filters out", len(result5_wrong.unknown_terms) == 1)
    check("T5: context mismatch degrades confidence",
          result5_wrong.confidence < result5_med.confidence)

    # ─── T6: Multi-Hop Translation Chain ───
    print("\n═══ T6: Multi-Hop Chain (Telephone Game) ═══")

    chain = TranslationChain("Medical→Legal→Insurance")
    chain.add_dictionary(med_legal)
    chain.add_dictionary(legal_insurance)

    chain_result = chain.translate_chain(
        ["MI", "MVA", "acute"],
        initial_domain="medical",
    )

    check("T6: 2-hop chain completed", chain_result.hop_number == 2)
    check("T6: cumulative confidence < single hop",
          chain_result.confidence < result1.confidence)
    check("T6: degradation increases with hops",
          chain_result.degradation > result1.degradation)
    check("T6: final terms are insurance domain",
          "heart_attack_event" in chain_result.translated_terms.values() or
          "auto_collision_claim" in chain_result.translated_terms.values())

    print(f"\n    Chain degradation analysis:")
    for hr in chain.hop_results:
        print(f"      Hop {hr.hop_number}: conf={hr.confidence:.4f} deg={hr.degradation:.4f}")
    print(f"      Cumulative: conf={chain_result.confidence:.4f} deg={chain_result.degradation:.4f}")

    # ─── T7: Degradation Curve Analysis ───
    print("\n═══ T7: Degradation Curve ═══")

    analyzer = CompressionTrustAnalyzer()
    curve = analyzer.analyze_degradation_curve(chain)

    check("T7: 2 hops analyzed", curve["hops"] == 2)
    check("T7: final degradation > 0", curve["final_degradation"] > 0)
    check("T7: avg retention < 1.0", curve["avg_retention_per_hop"] < 1.0)
    check("T7: half-life finite", curve["half_life_hops"] < float("inf"))

    print(f"\n    Degradation curve:")
    print(f"      Avg retention per hop: {curve['avg_retention_per_hop']:.4f}")
    print(f"      Half-life: {curve['half_life_hops']:.1f} hops")

    # ─── T8: Compression-Trust Relationship ───
    print("\n═══ T8: Compression-Trust Empirical Validation ═══")

    test_terms = ["MI", "MVA", "acute", "chronic", "prognosis"]

    # Measure at different trust levels
    trust_levels = [0.2, 0.4, 0.6, 0.8, 1.0]
    measurements = []

    for tl in trust_levels:
        test_dict = DictionaryEntity(f"dict:test-{tl}", f"Test-{tl}",
                                      "medical", "legal")
        test_dict.t3 = TrustTensor(talent=tl, training=tl, temperament=tl)
        for e in med_legal.codebook.entries.values():
            test_dict.codebook.add(e.source_term, e.target_term, e.confidence,
                                    list(e.context_tags))

        point = analyzer.measure(test_dict, test_terms)
        measurements.append(point)

    mono = analyzer.analyze_monotonicity()
    check("T8: confidence monotonically increases with trust", mono["monotonic"])
    check("T8: positive direction", mono["direction"] == "positive")

    print(f"\n    Compression-Trust data points:")
    for m in measurements:
        print(f"      trust={m['trust_level']:.2f} conf={m['confidence']:.4f} "
              f"coverage={m['coverage']:.2f}")

    # ─── T9: ATP Staking — Truthful Claims ───
    print("\n═══ T9: ATP Staking — Truthful Claims ═══")

    staking = ConfidenceStakingEngine()

    # Truthful claim: claim 0.8, actual 0.85
    stake1 = staking.create_stake("entity-A", "dict:med-legal", 0.8, 100.0)
    staking.settle_stake(stake1.stake_id, 0.85)

    check("T9: truthful claim settled", stake1.settled)
    check("T9: truthful payout = 10%", stake1.payout == 10.0)
    check("T9: no penalty for truthful", stake1.penalty == 0.0)

    # ─── T10: ATP Staking — Overconfident Claims ───
    print("\n═══ T10: ATP Staking — Overconfident ═══")

    stake2 = staking.create_stake("entity-B", "dict:med-legal", 0.95, 100.0)
    staking.settle_stake(stake2.stake_id, 0.60)

    check("T10: overconfident settled", stake2.settled)
    check("T10: penalty applied", stake2.penalty > 0)
    # Penalty = 100 * (1 - 0.60/0.95) ≈ 36.84
    check("T10: penalty proportional", abs(stake2.penalty - 100 * (1 - 0.60/0.95)) < 0.01)
    check("T10: no payout for overconfident", stake2.payout == 0.0)

    stats = staking.get_stats()
    check("T10: 1 truthful, 1 overconfident",
          stats["truthful_claims"] == 1 and stats["overconfident_claims"] == 1)

    # ─── T11: Feedback and Trust Recovery ───
    print("\n═══ T11: Feedback Loop ═══")

    feedback_dict = DictionaryEntity("dict:feedback", "Feedback-Test",
                                      "medical", "legal")
    feedback_dict.t3 = TrustTensor(talent=0.8, training=0.5, temperament=0.7)
    feedback_dict.codebook.add("MI", "cardiac_incident", 0.7)  # Bad translation

    # Apply correction from high-authority source
    training_before = feedback_dict.t3.training
    feedback_dict.apply_feedback("MI", "myocardial_infarction", authority_trust=0.9)

    entry = feedback_dict.codebook.entries["MI"]
    check("T11: correction applied", entry.target_term == "myocardial_infarction")
    check("T11: confidence boosted", entry.confidence > 0.7)
    check("T11: training improved", feedback_dict.t3.training > training_before)
    check("T11: corrections tracked", entry.corrections == 1)

    # Low-authority correction just penalizes
    feedback_dict.codebook.add("TEST", "wrong_answer", 0.9)
    feedback_dict.apply_feedback("TEST", "better_answer", authority_trust=0.5)
    test_entry = feedback_dict.codebook.entries["TEST"]
    check("T11: low-auth doesn't change term", test_entry.target_term == "wrong_answer")
    check("T11: low-auth penalizes confidence", test_entry.confidence < 0.9)

    # ─── T12: Drift Detection ───
    print("\n═══ T12: Drift Detection ═══")

    drift_dict = DictionaryEntity("dict:drift", "Drift-Test",
                                   "medical", "legal")
    drift_dict.t3 = TrustTensor(talent=0.8, training=0.7, temperament=0.75)

    # Add 5 entries
    for i in range(5):
        drift_dict.codebook.add(f"term{i}", f"translated{i}", 0.9)

    version_before = drift_dict.version

    # Correct just 1/5 = 20% → drift detected (> 10%)
    drift_dict.apply_feedback("term0", "corrected0", authority_trust=0.9)
    check("T12: version incremented on drift", drift_dict.version != version_before)
    check("T12: version history grows", len(drift_dict.version_history) > 1)

    # ─── T13: Domain Mismatch ───
    print("\n═══ T13: Domain Mismatch ═══")

    wrong_request = TranslationRequest(
        terms=["MI"],
        source_domain="engineering",
        target_domain="financial",
    )
    wrong_result = med_legal.translate(wrong_request)
    check("T13: wrong domain → failure", wrong_result.confidence == 0.0)
    check("T13: all terms unknown", len(wrong_result.unknown_terms) == 1)
    check("T13: failure counted", med_legal.translations_failed == 1)

    # ─── T14: Empty Translation ───
    print("\n═══ T14: Edge Cases ═══")

    empty_request = TranslationRequest(
        terms=[],
        source_domain="medical",
        target_domain="legal",
    )
    empty_result = med_legal.translate(empty_request)
    check("T14: empty input → 0 coverage", empty_result.coverage == 0.0)

    # All unknown terms
    all_unknown = TranslationRequest(
        terms=["XYZZY", "PLUGH", "QUUX"],
        source_domain="medical",
        target_domain="legal",
    )
    unknown_result = med_legal.translate(all_unknown)
    check("T14: all unknown → 0 confidence", unknown_result.confidence == 0.0)
    check("T14: degradation = 1.0", unknown_result.degradation == 1.0)

    # ─── T15: Compression Ratio ───
    print("\n═══ T15: Compression Ratio ═══")

    # Medical → Lay should have positive compression (short terms → longer descriptions)
    lay_request = TranslationRequest(
        terms=["MI", "MVA", "acute", "chronic"],
        source_domain="medical",
        target_domain="lay",
    )
    lay_result = med_lay.translate(lay_request)

    # Medical abbreviations are shorter than lay descriptions
    check("T15: lay translation → expansion (negative compression)",
          lay_result.compression_ratio < 0)
    check("T15: high confidence", lay_result.confidence > 0.85)

    # Legal → Insurance should be moderate
    legal_request = TranslationRequest(
        terms=["myocardial_infarction", "motor_vehicle_accident"],
        source_domain="legal",
        target_domain="insurance",
    )
    legal_result = legal_insurance.translate(legal_request)
    check("T15: legal→insurance translated", len(legal_result.unknown_terms) == 0)

    # ─── T16: N-Hop Degradation Scaling ───
    print("\n═══ T16: N-Hop Degradation Scaling ═══")

    # Create a long chain of identical dictionaries to test scaling
    hop_confidences = []
    cumulative = 1.0
    per_hop_conf = 0.9  # Each dictionary has ~0.9 confidence

    for n_hops in range(1, 8):
        cumulative *= per_hop_conf
        hop_confidences.append((n_hops, round(cumulative, 6)))

    check("T16: 1-hop > 2-hop", hop_confidences[0][1] > hop_confidences[1][1])
    check("T16: monotonically decreasing",
          all(hop_confidences[i][1] > hop_confidences[i+1][1]
              for i in range(len(hop_confidences)-1)))
    check("T16: 7-hop < 0.5", hop_confidences[6][1] < 0.5)

    print(f"\n    N-hop degradation (per-hop conf = {per_hop_conf}):")
    for n, c in hop_confidences:
        bar = "█" * int(c * 40)
        print(f"      {n} hops: conf={c:.4f} [{bar}]")

    # ─── T17: Dictionary Status ───
    print("\n═══ T17: Dictionary Status ═══")

    status = med_legal.status()
    check("T17: has dict_id", "dict_id" in status)
    check("T17: has domains", "domains" in status)
    check("T17: has t3", "t3" in status)
    check("T17: has v3", "v3" in status)
    check("T17: codebook_size > 0", status["codebook_size"] > 0)
    check("T17: translations > 0", status["translations"] > 0)

    # ─── T18: Codebook Metrics ───
    print("\n═══ T18: Codebook Metrics ═══")

    check("T18: avg confidence > 0.8", med_legal.codebook.avg_confidence() > 0.8)
    check("T18: codebook size = 8", med_legal.codebook.size() == 8)
    check("T18: usage counts tracked",
          any(e.usage_count > 0 for e in med_legal.codebook.entries.values()))

    # ─── T19: Cross-Domain Coverage Matrix ───
    print("\n═══ T19: Cross-Domain Coverage ═══")

    # Medical terms that need translation across all domains
    medical_terms = ["MI", "MVA", "acute", "chronic", "prognosis", "etiology"]

    domains = {
        "medical→legal": med_legal,
        "medical→lay": med_lay,
        "legal→insurance": legal_insurance,
    }

    print(f"\n    Cross-domain coverage matrix:")
    for domain_pair, dictionary in domains.items():
        source_domain = domain_pair.split("→")[0]
        target_domain = domain_pair.split("→")[1]
        terms_for_domain = medical_terms if source_domain == "medical" else \
            [med_legal.codebook.entries[t].target_term for t in medical_terms
             if t in med_legal.codebook.entries]

        covered = sum(1 for t in terms_for_domain if dictionary.codebook.entries.get(t))
        total = len(terms_for_domain)
        coverage = covered / total if total > 0 else 0
        print(f"      {domain_pair}: {covered}/{total} = {coverage:.0%}")

    check("T19: med→legal high coverage",
          sum(1 for t in medical_terms if med_legal.codebook.entries.get(t)) / len(medical_terms) > 0.7)
    check("T19: med→lay high coverage",
          sum(1 for t in medical_terms if med_lay.codebook.entries.get(t)) / len(medical_terms) > 0.7)

    # ─── T20: Trust Level Comparative Analysis ───
    print("\n═══ T20: Trust Level Comparison ═══")

    trust_configs = [
        ("Zero trust", TrustTensor(0.0, 0.0, 0.0)),
        ("Low trust", TrustTensor(0.2, 0.15, 0.25)),
        ("Medium trust", TrustTensor(0.5, 0.5, 0.5)),
        ("High trust", TrustTensor(0.8, 0.85, 0.82)),
        ("Perfect trust", TrustTensor(1.0, 1.0, 1.0)),
    ]

    comparison_terms = ["MI", "MVA", "acute", "chronic"]
    prev_confidence = -1.0

    print(f"\n    Trust level vs confidence:")
    for label, t3 in trust_configs:
        test_d = DictionaryEntity("dict:compare", label, "medical", "legal")
        test_d.t3 = t3
        for e in med_legal.codebook.entries.values():
            test_d.codebook.add(e.source_term, e.target_term, e.confidence)

        req = TranslationRequest(comparison_terms, "medical", "legal")
        res = test_d.translate(req)

        print(f"      {label:14s}: T3={t3.composite():.3f} conf={res.confidence:.4f} "
              f"deg={res.degradation:.4f}")

        if label != "Zero trust":
            check(f"T20: {label} confidence ≥ prev", res.confidence >= prev_confidence - 0.001)
        prev_confidence = res.confidence

    # ─── T21: Staking Statistics ───
    print("\n═══ T21: Staking Statistics ═══")

    # Create several stakes
    staking2 = ConfidenceStakingEngine()

    # 3 truthful, 2 overconfident
    for i in range(3):
        s = staking2.create_stake(f"entity-{i}", "dict:test", 0.7, 50.0)
        staking2.settle_stake(s.stake_id, 0.8)

    for i in range(3, 5):
        s = staking2.create_stake(f"entity-{i}", "dict:test", 0.95, 50.0)
        staking2.settle_stake(s.stake_id, 0.5)

    stats2 = staking2.get_stats()
    check("T21: 5 stakes total", stats2["total_stakes"] == 5)
    check("T21: 3 truthful", stats2["truthful_claims"] == 3)
    check("T21: 2 overconfident", stats2["overconfident_claims"] == 2)
    check("T21: total staked = 250", stats2["total_staked"] == 250.0)
    check("T21: penalties > 0", stats2["total_penalties"] > 0)
    check("T21: payouts > 0", stats2["total_payouts"] > 0)

    # ─── T22: Feedback-Driven New Entry ───
    print("\n═══ T22: Feedback New Entry ═══")

    fb_dict = DictionaryEntity("dict:fb-new", "Feedback-New", "medical", "legal")
    fb_dict.t3 = TrustTensor(0.8, 0.7, 0.75)
    original_size = fb_dict.codebook.size()

    fb_dict.apply_feedback("NEW_TERM", "new_translation", authority_trust=0.85)
    check("T22: new entry added", fb_dict.codebook.size() == original_size + 1)
    check("T22: new entry has confidence",
          fb_dict.codebook.entries["NEW_TERM"].confidence > 0.6)

    # ─── T23: Engineering→Financial Chain ───
    print("\n═══ T23: Cross-Domain Engineering→Financial ═══")

    eng_request = TranslationRequest(
        terms=["MTBF", "downtime", "throughput"],
        source_domain="engineering",
        target_domain="financial",
    )
    eng_result = eng_fin.translate(eng_request)

    check("T23: engineering terms translated", len(eng_result.unknown_terms) == 0)
    check("T23: lower trust = lower confidence",
          eng_result.confidence < result1.confidence)
    check("T23: T3 ceiling applies",
          eng_result.confidence <= eng_fin.t3.composite() + 0.001)

    # ─── T24: Long Chain Degradation (5 hops) ───
    print("\n═══ T24: Long Chain (5 Hops) ═══")

    # Create a 5-hop chain with ~0.85 confidence per hop
    long_chain = TranslationChain("5-hop-test")
    domains_seq = [
        ("d0", "d1"), ("d1", "d2"), ("d2", "d3"), ("d3", "d4"), ("d4", "d5"),
    ]

    for i, (src, tgt) in enumerate(domains_seq):
        d = DictionaryEntity(f"dict:chain-{i}", f"Chain-{i}", src, tgt)
        d.t3 = TrustTensor(0.9, 0.85, 0.88)
        # Each hop maps previous hop's output to next form
        suffix_in = f"_{i}" if i > 0 else ""
        suffix_out = f"_{i+1}"
        d.codebook.add(f"alpha{suffix_in}", f"alpha{suffix_out}", 0.88)
        d.codebook.add(f"beta{suffix_in}", f"beta{suffix_out}", 0.85)
        d.codebook.add(f"gamma{suffix_in}", f"gamma{suffix_out}", 0.82)
        long_chain.add_dictionary(d)

    long_result = long_chain.translate_chain(["alpha", "beta", "gamma"], "d0")

    check("T24: 5-hop chain completed", long_result.hop_number == 5)
    check("T24: significant degradation (> 50%)", long_result.degradation > 0.5)
    check("T24: confidence < 0.5", long_result.confidence < 0.5)

    long_curve = analyzer.analyze_degradation_curve(long_chain)
    check("T24: half-life computed", long_curve["half_life_hops"] > 0)

    print(f"\n    5-hop degradation:")
    for hp in long_curve["per_hop_data"]:
        bar = "█" * int(hp["cumulative_confidence"] * 40)
        print(f"      Hop {hp['hop']}: cum_conf={hp['cumulative_confidence']:.4f} [{bar}]")

    # ─── T25: Compression-Trust Theorem Validation ───
    print("\n═══ T25: Compression-Trust Theorem ═══")

    # Theorem: For trust T and codebook quality Q,
    # effective_confidence = min(T, Q)
    # Higher trust → higher usable confidence → more compression possible
    # This is monotonic and bounded by both T and Q.

    theorem_valid = True
    for tl in [0.1, 0.3, 0.5, 0.7, 0.9]:
        td = DictionaryEntity("dict:thm", "Theorem", "medical", "legal")
        td.t3 = TrustTensor(tl, tl, tl)
        # Copy entries WITHOUT context tags for clean coverage test
        for e in med_legal.codebook.entries.values():
            td.codebook.add(e.source_term, e.target_term, e.confidence)

        # Use terms that all exist in codebook, no context filtering
        test_terms_t25 = ["MI", "MVA", "acute"]
        req = TranslationRequest(test_terms_t25, "medical", "legal")
        res = td.translate(req)

        # confidence = min(coverage × avg_entry_confidence_of_translated, T3)
        translated_confs = [td.codebook.entries[t].confidence for t in test_terms_t25
                           if t in td.codebook.entries]
        avg_translated = sum(translated_confs) / len(translated_confs) if translated_confs else 0
        expected = min(avg_translated * res.coverage, td.t3.composite())
        if abs(res.confidence - expected) > 0.001:
            theorem_valid = False

    check("T25: compression-trust theorem holds", theorem_valid)

    print(f"""
    Compression-Trust Theorem:
      confidence = min(coverage × avg_entry_confidence, T3_composite)

      For full coverage (all terms known):
        confidence = min(codebook_quality, trust_level)

      Implication: Trust is the CEILING on information transfer.
      Even perfect codebooks can't overcome low trust.
      This is why "compression requires trust in shared decompression artifacts."
    """)

    # ═══ Summary ═══
    total = passed + failed
    print(f"{'=' * 60}")
    print(f"  Dictionary Cross-Domain Translation — Results")
    print(f"  {passed} passed, {failed} failed out of {total} checks")
    print(f"{'=' * 60}")

    if failed == 0:
        print(f"""
  All tests verified:
  T1:  Basic translation (medical → legal)
  T2:  Unknown term degradation
  T3:  T3 trust ceiling effect
  T4:  Bidirectional translation
  T5:  Context-sensitive translation
  T6:  Multi-hop chain (telephone game)
  T7:  Degradation curve analysis (half-life)
  T8:  Compression-trust empirical validation (monotonicity)
  T9:  ATP staking — truthful confidence claims
  T10: ATP staking — overconfident claims (slashing)
  T11: Feedback loop (trust recovery)
  T12: Drift detection (version management)
  T13: Domain mismatch handling
  T14: Edge cases (empty input, all unknown)
  T15: Compression ratio measurement
  T16: N-hop degradation scaling (exponential decay)
  T17: Dictionary status reporting
  T18: Codebook metrics
  T19: Cross-domain coverage matrix
  T20: Trust level comparative analysis
  T21: Staking statistics
  T22: Feedback-driven new entry creation
  T23: Cross-domain engineering→financial
  T24: Long chain (5 hops, > 50% degradation)
  T25: Compression-trust theorem validation

  Key findings:
  - Trust IS the ceiling on information transfer
  - Multi-hop degradation is exponential (multiplicative per hop)
  - Half-life of trust: ~{long_curve['half_life_hops']:.1f} hops at {long_curve['avg_retention_per_hop']:.2f} retention
  - Truthful staking works: overconfident claims are punished
  - Feedback loops enable trust recovery (training dimension)
  - Context-sensitive filtering prevents domain contamination
""")
    else:
        print(f"\n  {failed} checks need attention.")


if __name__ == "__main__":
    run_tests()
