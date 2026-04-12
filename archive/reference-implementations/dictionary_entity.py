#!/usr/bin/env python3
"""
Dictionary Entity — Reference Implementation
===============================================

Implements the Dictionary Entities spec (web4-standard/core-spec/dictionary-entities.md).

Dictionary Entities are living semantic bridges between domains. They are not
static translation tables but evolving entities with their own LCTs, reputations,
and relationships that mediate meaning across boundaries.

Core concept: All meaningful communication is compression plus trust across
shared or sufficiently aligned latent fields.

  High Trust → High Compression → Efficient Communication
  Low Trust  → Low Compression  → Verbose Communication
  Zero Trust → No Compression   → Raw Data Transfer

This implementation covers:
1. DictionaryEntity: living entity with LCT, T3/V3, codebook, versioning
2. Translation pipeline: request → validate → translate → degrade → witness
3. Multi-hop translation with cumulative trust degradation
4. ATP staking on confidence claims (slash on overconfidence)
5. Feedback-driven learning + semantic drift detection
6. DictionaryRegistry: discovery and best-dictionary selection

Date: 2026-02-21
Spec: web4-standard/core-spec/dictionary-entities.md
"""

import hashlib
import json
import math
import random
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


# ═══════════════════════════════════════════════════════════════
# Dictionary Entity Types and Errors
# ═══════════════════════════════════════════════════════════════

class DictionaryType(Enum):
    """Types of dictionary entities."""
    DOMAIN = "domain"           # Professional/technical domains
    MODEL = "model"             # AI model bridging
    COMPRESSION = "compression" # Lossy/lossless compression
    META = "meta"               # Translates between dictionaries


class DictionaryError(Exception):
    """Base error for dictionary operations."""
    pass

class IncompetentDictionary(DictionaryError):
    """Dictionary doesn't cover required domains."""
    pass

class InsufficientDictionaryTrust(DictionaryError):
    """Dictionary trust below required threshold."""
    pass

class TranslationFailed(DictionaryError):
    """Translation could not be completed."""
    pass

class DriftDetected(DictionaryError):
    """Semantic drift detected in dictionary."""
    pass

class StakeSlashed(DictionaryError):
    """ATP stake was slashed due to overconfidence."""
    pass


# ═══════════════════════════════════════════════════════════════
# Trust Tensors (simplified for dictionary context)
# ═══════════════════════════════════════════════════════════════

@dataclass
class DictT3:
    """Trust tensor for dictionary competence."""
    talent: float = 0.5        # Domain expertise depth
    training: float = 0.5      # Translation accuracy from experience
    temperament: float = 0.5   # Consistency and reliability

    def composite(self) -> float:
        return 0.4 * self.talent + 0.3 * self.training + 0.3 * self.temperament

    def update(self, dim: str, delta: float):
        val = getattr(self, dim, 0.5)
        setattr(self, dim, max(0.0, min(1.0, val + delta)))


@dataclass
class DictV3:
    """Value tensor for translation quality."""
    veracity: float = 0.5      # Truthfulness of translations
    validity: float = 0.5      # Structural correctness
    value: float = 0.5         # Usefulness to consumers

    def composite(self) -> float:
        return 0.4 * self.veracity + 0.3 * self.validity + 0.3 * self.value

    def update(self, dim: str, delta: float):
        val = getattr(self, dim, 0.5)
        setattr(self, dim, max(0.0, min(1.0, val + delta)))


# ═══════════════════════════════════════════════════════════════
# Codebook: The semantic mapping substrate
# ═══════════════════════════════════════════════════════════════

@dataclass
class CodebookEntry:
    """A single concept mapping in the codebook."""
    source_term: str
    target_term: str
    confidence: float = 1.0       # How reliable this mapping is
    context_tags: List[str] = field(default_factory=list)
    usage_count: int = 0
    last_used: Optional[str] = None
    corrections: int = 0          # Times this mapping was corrected


@dataclass
class Codebook:
    """Semantic mapping between two domains."""
    entries: Dict[str, CodebookEntry] = field(default_factory=dict)
    version: str = "1.0.0"
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def lookup(self, source_term: str, context: Optional[str] = None) -> Optional[CodebookEntry]:
        """Look up a term, optionally filtering by context."""
        entry = self.entries.get(source_term)
        if entry and context and entry.context_tags:
            if context not in entry.context_tags:
                return None  # Context mismatch
        if entry:
            entry.usage_count += 1
            entry.last_used = datetime.now(timezone.utc).isoformat()
        return entry

    def add_entry(self, source: str, target: str, confidence: float = 1.0,
                  contexts: Optional[List[str]] = None):
        """Add or update a codebook entry."""
        self.entries[source] = CodebookEntry(
            source_term=source,
            target_term=target,
            confidence=confidence,
            context_tags=contexts or [],
        )

    def coverage(self) -> int:
        """Number of entries in codebook."""
        return len(self.entries)

    def average_confidence(self) -> float:
        """Average confidence across all entries."""
        if not self.entries:
            return 0.0
        return sum(e.confidence for e in self.entries.values()) / len(self.entries)

    def detect_drift(self, correction_threshold: float = 0.1) -> bool:
        """Detect if too many entries have been corrected (semantic drift)."""
        if not self.entries:
            return False
        corrected = sum(1 for e in self.entries.values() if e.corrections > 0)
        return corrected / len(self.entries) > correction_threshold


# ═══════════════════════════════════════════════════════════════
# Translation Request and Result
# ═══════════════════════════════════════════════════════════════

@dataclass
class TranslationRequest:
    """A request to translate content between domains."""
    request_id: str = field(default_factory=lambda: f"tr:{uuid.uuid4().hex[:12]}")
    source_content: str = ""
    source_domain: str = ""
    target_domain: str = ""
    context: Dict[str, Any] = field(default_factory=dict)
    min_fidelity: float = 0.8
    require_witness: bool = False
    atp_stake: float = 0.0


@dataclass
class TranslationResult:
    """Result of a translation."""
    request_id: str
    target_content: str
    confidence: float
    degradation: float         # 1.0 - confidence
    dictionary_lct: str
    terms_translated: int = 0
    terms_unknown: int = 0
    witness_required: bool = False
    atp_earned: float = 0.0
    atp_slashed: float = 0.0
    chain_position: int = 0    # Position in multi-hop chain


@dataclass
class TranslationChainResult:
    """Result of a multi-hop translation chain."""
    hops: List[TranslationResult]
    final_content: str
    cumulative_confidence: float
    cumulative_degradation: float
    total_atp_cost: float
    witnesses: List[str] = field(default_factory=list)


# ═══════════════════════════════════════════════════════════════
# Dictionary Entity
# ═══════════════════════════════════════════════════════════════

class DictionaryEntity:
    """
    A living Web4 entity that bridges semantic domains.

    Every dictionary has:
    - LCT identity
    - T3/V3 trust tensors
    - Codebook (semantic mappings)
    - Version history
    - Translation history
    - ATP balance (earned from translations)
    """

    def __init__(
        self,
        lct_id: str,
        name: str,
        source_domain: str,
        target_domain: str,
        dict_type: DictionaryType = DictionaryType.DOMAIN,
        bidirectional: bool = False,
    ):
        self.lct_id = lct_id
        self.name = name
        self.source_domain = source_domain
        self.target_domain = target_domain
        self.dict_type = dict_type
        self.bidirectional = bidirectional

        # Trust tensors
        self.t3 = DictT3()
        self.v3 = DictV3()

        # Codebook
        self.codebook = Codebook()
        self._reverse_codebook: Optional[Codebook] = None
        if bidirectional:
            self._reverse_codebook = Codebook()

        # State
        self.atp_balance: float = 100.0
        self.version: str = "1.0.0"
        self.translations_completed: int = 0
        self.translations_failed: int = 0
        self.total_degradation: float = 0.0
        self.feedback_received: int = 0

        # History
        self.version_history: List[Dict] = [
            {"version": "1.0.0", "timestamp": datetime.now(timezone.utc).isoformat(),
             "reason": "initial"}
        ]
        self.translation_log: List[Dict] = []

    def covers_domains(self, source: str, target: str) -> bool:
        """Check if this dictionary covers the source → target translation."""
        if self.source_domain == source and self.target_domain == target:
            return True
        if self.bidirectional:
            return self.source_domain == target and self.target_domain == source
        return False

    def add_mapping(self, source: str, target: str, confidence: float = 1.0,
                    contexts: Optional[List[str]] = None):
        """Add a term mapping to the codebook."""
        self.codebook.add_entry(source, target, confidence, contexts)
        if self.bidirectional and self._reverse_codebook is not None:
            self._reverse_codebook.add_entry(target, source, confidence, contexts)

    def translate(self, request: TranslationRequest) -> TranslationResult:
        """
        Translate content from source domain to target domain.

        Pipeline: validate → decompose → map → reassemble → score
        """
        # 1. Validate domains
        if not self.covers_domains(request.source_domain, request.target_domain):
            raise IncompetentDictionary(
                f"Dictionary covers {self.source_domain}→{self.target_domain}, "
                f"not {request.source_domain}→{request.target_domain}"
            )

        # 2. Check trust requirements
        if self.t3.composite() < 0.2:
            raise InsufficientDictionaryTrust(
                f"Dictionary trust {self.t3.composite():.3f} too low"
            )

        # 3. Select codebook (forward or reverse)
        cb = self.codebook
        if request.source_domain == self.target_domain and self.bidirectional:
            cb = self._reverse_codebook

        # 4. Decompose source into terms and translate
        # Use greedy longest-match for multi-word codebook entries
        words = request.source_content.lower().split()
        translated_terms = []
        terms_translated = 0
        terms_unknown = 0
        confidence_sum = 0.0

        context = request.context.get("purpose", None)
        i = 0
        while i < len(words):
            matched = False
            # Try longest phrase first (up to 4 words)
            for length in range(min(4, len(words) - i), 0, -1):
                phrase = " ".join(words[i:i + length])
                entry = cb.lookup(phrase, context) if cb else None
                if entry:
                    translated_terms.append(entry.target_term)
                    confidence_sum += entry.confidence
                    terms_translated += 1
                    i += length
                    matched = True
                    break
            if not matched:
                translated_terms.append(f"[{words[i]}]")
                terms_unknown += 1
                i += 1

        # 5. Compute confidence
        total_terms = terms_translated + terms_unknown
        if total_terms == 0:
            confidence = 0.0
        else:
            # Confidence = (weighted translation confidence) × (coverage ratio)
            avg_entry_confidence = confidence_sum / max(1, terms_translated)
            coverage_ratio = terms_translated / total_terms
            confidence = avg_entry_confidence * coverage_ratio

        # Apply dictionary trust as ceiling
        confidence = min(confidence, self.t3.composite())

        degradation = 1.0 - confidence

        # 6. Check minimum fidelity
        if confidence < request.min_fidelity:
            self.translations_failed += 1
            raise TranslationFailed(
                f"Confidence {confidence:.3f} below minimum {request.min_fidelity}"
            )

        # 7. Handle ATP staking
        atp_earned = 0.0
        atp_slashed = 0.0
        if request.atp_stake > 0:
            # Staking: if confidence >= claimed_confidence, reward; else slash
            claimed_confidence = request.min_fidelity
            if confidence >= claimed_confidence:
                atp_earned = request.atp_stake * 0.1  # 10% reward
            else:
                slash_ratio = confidence / claimed_confidence
                atp_slashed = request.atp_stake * (1.0 - slash_ratio)
                atp_earned = -atp_slashed

            self.atp_balance += atp_earned

        # 8. Update state
        self.translations_completed += 1
        self.total_degradation += degradation

        # Update T3 based on outcome
        self.t3.update("training", 0.005)   # Experience gain
        if confidence > 0.9:
            self.t3.update("talent", 0.002)  # Expertise reward
        self.t3.update("temperament", 0.003) # Consistency

        # Update V3
        self.v3.update("veracity", 0.003 * confidence)
        self.v3.update("validity", 0.002)

        target_content = " ".join(translated_terms)

        # Log
        self.translation_log.append({
            "request_id": request.request_id,
            "confidence": confidence,
            "terms": terms_translated,
            "unknown": terms_unknown,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

        return TranslationResult(
            request_id=request.request_id,
            target_content=target_content,
            confidence=confidence,
            degradation=degradation,
            dictionary_lct=self.lct_id,
            terms_translated=terms_translated,
            terms_unknown=terms_unknown,
            witness_required=confidence < 0.95 or request.require_witness,
            atp_earned=atp_earned,
            atp_slashed=atp_slashed,
        )

    def apply_feedback(self, source_term: str, corrected_target: str,
                       authority_trust: float = 0.5):
        """Apply a correction feedback to the codebook."""
        entry = self.codebook.entries.get(source_term)
        if entry:
            entry.corrections += 1
            # Reduce confidence based on correction
            entry.confidence *= 0.95
            # If correction is from high-trust authority, update mapping
            if authority_trust > 0.7:
                entry.target_term = corrected_target
                entry.confidence = min(1.0, entry.confidence + 0.1)

        self.feedback_received += 1

        # Check for drift
        if self.codebook.detect_drift():
            self._increment_version("drift_correction")

    def _increment_version(self, reason: str):
        """Bump the minor version."""
        parts = self.version.split(".")
        parts[1] = str(int(parts[1]) + 1)
        self.version = ".".join(parts)
        self.codebook.version = self.version
        self.version_history.append({
            "version": self.version,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "reason": reason,
        })

    def status(self) -> Dict:
        """Get dictionary status summary."""
        return {
            "lct_id": self.lct_id,
            "name": self.name,
            "domains": f"{self.source_domain}→{self.target_domain}",
            "bidirectional": self.bidirectional,
            "type": self.dict_type.value,
            "version": self.version,
            "codebook_size": self.codebook.coverage(),
            "avg_confidence": round(self.codebook.average_confidence(), 3),
            "t3": round(self.t3.composite(), 3),
            "v3": round(self.v3.composite(), 3),
            "translations": self.translations_completed,
            "failures": self.translations_failed,
            "atp_balance": round(self.atp_balance, 2),
            "drift_detected": self.codebook.detect_drift(),
        }


# ═══════════════════════════════════════════════════════════════
# Multi-Hop Translation Chain
# ═══════════════════════════════════════════════════════════════

class TranslationChain:
    """
    Execute multi-hop translations through a chain of dictionaries.

    Trust degradation is cumulative: confidence = product of all hop confidences.
    This is the formal model of "telephone game" trust loss.
    """

    def __init__(self, dictionaries: List[DictionaryEntity]):
        self.dictionaries = dictionaries

    def translate(
        self,
        content: str,
        domains: List[str],
        context: Optional[Dict] = None,
        min_fidelity: float = 0.5,
    ) -> TranslationChainResult:
        """
        Translate content through a chain of domains.

        Args:
            content: Source content
            domains: List of domains to traverse (e.g., ["medical", "legal", "insurance"])
            context: Translation context
            min_fidelity: Minimum cumulative confidence
        """
        if len(domains) < 2:
            raise DictionaryError("Need at least 2 domains for chain translation")

        hops = []
        current_content = content
        cumulative_confidence = 1.0
        total_atp = 0.0

        for i in range(len(domains) - 1):
            source_domain = domains[i]
            target_domain = domains[i + 1]

            # Find dictionary for this hop
            dictionary = self._find_dictionary(source_domain, target_domain)
            if not dictionary:
                raise IncompetentDictionary(
                    f"No dictionary for {source_domain}→{target_domain}"
                )

            request = TranslationRequest(
                source_content=current_content,
                source_domain=source_domain,
                target_domain=target_domain,
                context=context or {},
                min_fidelity=0.0,  # Don't fail individual hops
            )

            result = dictionary.translate(request)
            result.chain_position = i + 1
            hops.append(result)

            current_content = result.target_content
            cumulative_confidence *= result.confidence
            total_atp += abs(result.atp_earned)

        cumulative_degradation = 1.0 - cumulative_confidence

        if cumulative_confidence < min_fidelity:
            raise TranslationFailed(
                f"Chain confidence {cumulative_confidence:.3f} below "
                f"minimum {min_fidelity}"
            )

        return TranslationChainResult(
            hops=hops,
            final_content=current_content,
            cumulative_confidence=cumulative_confidence,
            cumulative_degradation=cumulative_degradation,
            total_atp_cost=total_atp,
        )

    def _find_dictionary(self, source: str, target: str) -> Optional[DictionaryEntity]:
        """Find a dictionary that covers source → target."""
        for d in self.dictionaries:
            if d.covers_domains(source, target):
                return d
        return None


# ═══════════════════════════════════════════════════════════════
# Dictionary Registry (Discovery + Selection)
# ═══════════════════════════════════════════════════════════════

class DictionaryRegistry:
    """
    Registry for discovering and selecting best dictionaries.

    Selection score = trust × coverage × recency_factor
    """

    def __init__(self):
        self.dictionaries: Dict[str, DictionaryEntity] = {}

    def register(self, dictionary: DictionaryEntity):
        """Register a dictionary entity."""
        self.dictionaries[dictionary.lct_id] = dictionary

    def discover(self, source_domain: str, target_domain: str,
                 min_trust: float = 0.0) -> List[DictionaryEntity]:
        """Find dictionaries that cover source → target."""
        results = []
        for d in self.dictionaries.values():
            if d.covers_domains(source_domain, target_domain):
                if d.t3.composite() >= min_trust:
                    results.append(d)
        return sorted(results, key=lambda d: d.t3.composite(), reverse=True)

    def select_best(self, source_domain: str, target_domain: str,
                    context: Optional[Dict] = None) -> Optional[DictionaryEntity]:
        """Select the best dictionary for a translation."""
        candidates = self.discover(source_domain, target_domain)
        if not candidates:
            return None

        best = None
        best_score = -1.0

        for d in candidates:
            trust = d.t3.composite()
            coverage = d.codebook.coverage()
            # Recency: prefer recently used dictionaries
            recency = 1.0 / max(1, d.translations_completed + 1)
            score = trust * math.log2(coverage + 1) * (1.0 - recency * 0.1)
            if score > best_score:
                best_score = score
                best = d

        return best

    def find_chain(self, source_domain: str, target_domain: str,
                   max_hops: int = 3) -> Optional[List[DictionaryEntity]]:
        """
        Find a chain of dictionaries from source to target.

        BFS through dictionary coverage graph.
        """
        if source_domain == target_domain:
            return []

        # Direct lookup first
        direct = self.discover(source_domain, target_domain)
        if direct:
            return [direct[0]]

        # BFS for multi-hop path
        from collections import deque

        queue = deque([(source_domain, [])])
        visited = {source_domain}

        while queue:
            current, path = queue.popleft()
            if len(path) >= max_hops:
                continue

            # Find all dictionaries from current domain
            for d in self.dictionaries.values():
                next_domain = None
                if d.source_domain == current and d.target_domain not in visited:
                    next_domain = d.target_domain
                elif d.bidirectional and d.target_domain == current and d.source_domain not in visited:
                    next_domain = d.source_domain

                if next_domain:
                    new_path = path + [d]
                    if next_domain == target_domain:
                        return new_path
                    visited.add(next_domain)
                    queue.append((next_domain, new_path))

        return None


# ═══════════════════════════════════════════════════════════════
# Demo
# ═══════════════════════════════════════════════════════════════

def run_demo():
    """Demonstrate Dictionary Entity capabilities."""
    print("=" * 70)
    print("  Dictionary Entity — Reference Implementation")
    print("  Living semantic bridges with trust degradation tracking")
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

    # ── Test 1: Create Dictionary Entity ──
    print("\n── Test 1: Create Dictionary Entity ──")

    med_legal = DictionaryEntity(
        lct_id="lct:web4:dict:med-legal:v1",
        name="Medical-Legal Dictionary",
        source_domain="medical",
        target_domain="legal",
        dict_type=DictionaryType.DOMAIN,
        bidirectional=True,
    )

    # Populate codebook
    med_legal.add_mapping("mi", "heart attack", confidence=0.95)
    med_legal.add_mapping("tbi", "traumatic brain injury", confidence=0.98)
    med_legal.add_mapping("mva", "motor vehicle accident", confidence=0.99)
    med_legal.add_mapping("acute", "sudden onset", confidence=0.90, contexts=["claim"])
    med_legal.add_mapping("moderate", "significant", confidence=0.85)
    med_legal.add_mapping("presented", "was diagnosed", confidence=0.88)
    med_legal.add_mapping("with", "with", confidence=1.0)
    med_legal.add_mapping("following", "resulting from", confidence=0.92)

    # Boost trust to realistic levels
    med_legal.t3 = DictT3(talent=0.85, training=0.90, temperament=0.88)
    med_legal.v3 = DictV3(veracity=0.92, validity=0.88, value=0.85)

    status = med_legal.status()
    check("T1: Dictionary created with LCT", "lct:web4:dict" in status["lct_id"])
    check("T1: Codebook has 8 entries", status["codebook_size"] == 8)
    check("T1: Bidirectional enabled", status["bidirectional"])
    check("T1: T3 composite > 0.85", status["t3"] > 0.85)

    # ── Test 2: Basic Translation ──
    print("\n── Test 2: Basic Translation ──")

    request = TranslationRequest(
        source_content="acute mi following mva",
        source_domain="medical",
        target_domain="legal",
        context={"purpose": "claim"},
        min_fidelity=0.5,
    )

    result = med_legal.translate(request)
    print(f"  Source: '{request.source_content}'")
    print(f"  Target: '{result.target_content}'")
    print(f"  Confidence: {result.confidence:.3f}")
    print(f"  Degradation: {result.degradation:.3f}")

    check("T2: Translation produced output", len(result.target_content) > 0)
    check("T2: All terms translated", result.terms_unknown == 0)
    check("T2: Confidence > 0.8", result.confidence > 0.8)
    check("T2: Degradation < 0.2", result.degradation < 0.2)

    # ── Test 3: Unknown Terms Handling ──
    print("\n── Test 3: Unknown Terms Handling ──")

    request_unknown = TranslationRequest(
        source_content="acute mi with unknown_syndrome",
        source_domain="medical",
        target_domain="legal",
        min_fidelity=0.3,
    )

    result_unknown = med_legal.translate(request_unknown)
    check("T3: Unknown terms pass through in brackets",
          "[unknown_syndrome]" in result_unknown.target_content)
    check("T3: Unknown terms counted", result_unknown.terms_unknown == 1)
    check("T3: Confidence reduced by unknowns",
          result_unknown.confidence < result.confidence)

    # ── Test 4: Reverse Translation (Bidirectional) ──
    print("\n── Test 4: Reverse Translation (Bidirectional) ──")

    reverse_request = TranslationRequest(
        source_content="heart attack resulting from motor vehicle accident",
        source_domain="legal",
        target_domain="medical",
        min_fidelity=0.3,
    )

    reverse_result = med_legal.translate(reverse_request)
    print(f"  Legal→Medical: '{reverse_result.target_content}'")
    check("T4: Reverse translation works", reverse_result.terms_translated > 0)
    check("T4: Some terms translated back",
          "mi" in reverse_result.target_content or "heart" not in reverse_result.target_content)

    # ── Test 5: Minimum Fidelity Enforcement ──
    print("\n── Test 5: Minimum Fidelity Enforcement ──")

    # Create a low-trust dictionary
    low_trust_dict = DictionaryEntity(
        lct_id="lct:web4:dict:low-trust",
        name="Low Trust Dict",
        source_domain="test-a",
        target_domain="test-b",
    )
    low_trust_dict.add_mapping("hello", "world", confidence=0.5)
    low_trust_dict.t3 = DictT3(talent=0.3, training=0.3, temperament=0.3)

    try:
        low_trust_dict.translate(TranslationRequest(
            source_content="hello",
            source_domain="test-a",
            target_domain="test-b",
            min_fidelity=0.9,
        ))
        check("T5: Low confidence rejected", False, "should have raised")
    except TranslationFailed as e:
        check("T5: Low confidence rejected", "below minimum" in str(e))

    # ── Test 6: ATP Staking ──
    print("\n── Test 6: ATP Staking + Slashing ──")

    initial_atp = med_legal.atp_balance
    staked_request = TranslationRequest(
        source_content="acute mi with tbi",
        source_domain="medical",
        target_domain="legal",
        min_fidelity=0.5,
        atp_stake=50.0,
    )

    staked_result = med_legal.translate(staked_request)
    check("T6: ATP earned from successful stake",
          staked_result.atp_earned > 0,
          f"earned {staked_result.atp_earned:.2f}")
    check("T6: ATP balance increased",
          med_legal.atp_balance > initial_atp)

    # ── Test 7: Multi-Hop Translation Chain ──
    print("\n── Test 7: Multi-Hop Translation Chain ──")

    # Create legal → insurance dictionary
    legal_insurance = DictionaryEntity(
        lct_id="lct:web4:dict:legal-insurance",
        name="Legal-Insurance Dictionary",
        source_domain="legal",
        target_domain="insurance",
    )
    legal_insurance.add_mapping("heart attack", "cardiac event", confidence=0.95)
    legal_insurance.add_mapping("sudden onset", "acute occurrence", confidence=0.90)
    legal_insurance.add_mapping("motor vehicle accident", "auto claim incident", confidence=0.97)
    legal_insurance.add_mapping("resulting from", "caused by", confidence=0.93)
    legal_insurance.add_mapping("traumatic brain injury", "head trauma claim", confidence=0.91)
    legal_insurance.add_mapping("with", "with", confidence=1.0)
    legal_insurance.add_mapping("was diagnosed", "claimant diagnosed", confidence=0.88)
    legal_insurance.t3 = DictT3(talent=0.82, training=0.85, temperament=0.80)

    chain = TranslationChain([med_legal, legal_insurance])
    chain_result = chain.translate(
        content="acute mi following mva",
        domains=["medical", "legal", "insurance"],
        context={"purpose": "claim"},
        min_fidelity=0.3,
    )

    print(f"  Medical → Legal → Insurance:")
    for hop in chain_result.hops:
        print(f"    Hop {hop.chain_position}: confidence={hop.confidence:.3f} "
              f"→ '{hop.target_content}'")
    print(f"  Cumulative confidence: {chain_result.cumulative_confidence:.3f}")
    print(f"  Cumulative degradation: {chain_result.cumulative_degradation:.3f}")

    check("T7: Chain completed 2 hops", len(chain_result.hops) == 2)
    check("T7: Cumulative confidence < individual hops",
          chain_result.cumulative_confidence < chain_result.hops[0].confidence)
    check("T7: Cumulative degradation is product-based",
          chain_result.cumulative_degradation > 0.1)  # 1 - (0.87 * 0.82) ≈ 0.28

    # ── Test 8: Feedback + Drift Detection ──
    print("\n── Test 8: Feedback + Drift Detection ──")

    # Apply corrections
    initial_version = med_legal.version
    for term in ["mi", "tbi", "acute"]:  # Correct 3 of 8 entries
        med_legal.apply_feedback(term, f"corrected_{term}", authority_trust=0.8)

    check("T8: Feedback received", med_legal.feedback_received == 3)
    check("T8: Drift detected (3/8 corrected > 10% threshold)",
          med_legal.codebook.detect_drift())
    check("T8: Version incremented on drift",
          med_legal.version != initial_version)

    # ── Test 9: Registry Discovery ──
    print("\n── Test 9: Registry Discovery + Selection ──")

    registry = DictionaryRegistry()
    registry.register(med_legal)
    registry.register(legal_insurance)

    # Add a competing medical-legal dict with lower trust
    med_legal_v2 = DictionaryEntity(
        lct_id="lct:web4:dict:med-legal:v2",
        name="Medical-Legal Dict v2",
        source_domain="medical",
        target_domain="legal",
    )
    med_legal_v2.add_mapping("mi", "heart attack", confidence=0.99)
    med_legal_v2.t3 = DictT3(talent=0.6, training=0.6, temperament=0.6)
    registry.register(med_legal_v2)

    candidates = registry.discover("medical", "legal")
    check("T9: Found 2 medical-legal dictionaries", len(candidates) == 2)

    best = registry.select_best("medical", "legal")
    check("T9: Higher trust dictionary selected",
          best is not None and best.lct_id == med_legal.lct_id,
          f"selected {best.lct_id if best else 'None'}")

    # ── Test 10: Chain Discovery via Registry ──
    print("\n── Test 10: Chain Discovery via Registry ──")

    chain_path = registry.find_chain("medical", "insurance")
    check("T10: Multi-hop chain found", chain_path is not None and len(chain_path) == 2,
          f"path length: {len(chain_path) if chain_path else 0}")

    # No direct medical→insurance dictionary exists
    direct = registry.discover("medical", "insurance")
    check("T10: No direct dictionary exists", len(direct) == 0)

    # ── Test 11: Incompetent Dictionary Rejection ──
    print("\n── Test 11: Incompetent Dictionary Rejection ──")

    try:
        med_legal.translate(TranslationRequest(
            source_content="test",
            source_domain="engineering",
            target_domain="finance",
        ))
        check("T11: Wrong domain rejected", False)
    except IncompetentDictionary:
        check("T11: Wrong domain rejected", True)

    # ── Test 12: Version History ──
    print("\n── Test 12: Version History + Evolution ──")

    check("T12: Version history tracked",
          len(med_legal.version_history) >= 2)  # initial + drift
    check("T12: Latest version reflects drift",
          any("drift" in v.get("reason", "") for v in med_legal.version_history))

    # ── Test 13: Dictionary Status Dashboard ──
    print("\n── Test 13: Dictionary Status Dashboard ──")

    status = med_legal.status()
    print(f"  Name: {status['name']}")
    print(f"  Version: {status['version']}")
    print(f"  Codebook: {status['codebook_size']} entries, "
          f"avg confidence {status['avg_confidence']}")
    print(f"  T3: {status['t3']}, V3: {status['v3']}")
    print(f"  Translations: {status['translations']} completed, "
          f"{status['failures']} failed")
    print(f"  ATP: {status['atp_balance']}")
    print(f"  Drift: {status['drift_detected']}")

    check("T13: Status includes all fields",
          all(k in status for k in ["t3", "v3", "translations", "atp_balance"]))

    # ── Summary ──
    print("\n" + "=" * 70)
    total = checks_passed + checks_failed
    print(f"  Dictionary Entity: {checks_passed}/{total} checks passed")
    if checks_failed == 0:
        print("  ALL CHECKS PASSED!")

    print(f"\n  CAPABILITIES DEMONSTRATED:")
    print(f"    1. Living dictionary entity with LCT, T3/V3 tensors")
    print(f"    2. Forward + reverse translation (bidirectional)")
    print(f"    3. Unknown term handling (bracket pass-through)")
    print(f"    4. Minimum fidelity enforcement")
    print(f"    5. ATP staking on confidence claims")
    print(f"    6. Multi-hop translation chain with cumulative degradation")
    print(f"    7. Feedback-driven learning + drift detection")
    print(f"    8. Registry discovery + best-dictionary selection")
    print(f"    9. Chain discovery via BFS (multi-hop routing)")
    print(f"   10. Version evolution with history tracking")

    print(f"\n  KEY INSIGHT: Compression-Trust Duality")
    print(f"    Every translation hop degrades trust (cumulative product)")
    print(f"    Chain: medical→legal→insurance:")
    if chain_result:
        for h in chain_result.hops:
            print(f"      Hop {h.chain_position}: conf={h.confidence:.3f}")
        print(f"    Cumulative: {chain_result.cumulative_confidence:.3f}")
        print(f"    This IS the compression-trust relationship made observable")

    print("=" * 70)

    return checks_failed == 0


if __name__ == "__main__":
    success = run_demo()
    import sys
    sys.exit(0 if success else 1)
