"""
Dictionary Entity Evolution & Schema Negotiation
=================================================

Builds on dictionary_entities_protocol.py to add:
1. DictionaryVersion — Semantic versioning for dictionaries
2. EvolutionFSM — STABLE→DRAFT→REVIEW→PUBLISHED→DEPRECATED lifecycle
3. TermMigration — How terms evolve: addition, modification, deprecation, removal
4. SchemaNegotion — Client-server version compatibility negotiation
5. ConfidenceDegradation — Old mappings degrade over time
6. MigrationProtocol — Upgrade path from old to new dictionary version
7. EvolutionAuditTrail — Hash-chained record of all changes
8. CrossDomainEvolution — Coordinated evolution across interconnected dictionaries

Gap closed: Static dictionaries don't evolve; real semantic bridges change over time.
"""

from __future__ import annotations
import hashlib
import time
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Set, Tuple
from collections import defaultdict


# ─── Enums ────────────────────────────────────────────────────────────────────

class DictPhase(Enum):
    DRAFT = auto()       # Being prepared, not yet usable
    REVIEW = auto()      # Under community review
    PUBLISHED = auto()   # Active, production-ready
    DEPRECATED = auto()  # Still usable but scheduled for removal
    RETIRED = auto()     # No longer usable


class ChangeType(Enum):
    ADDITION = auto()      # New term added
    MODIFICATION = auto()  # Existing term meaning changed
    DEPRECATION = auto()   # Term marked for future removal
    REMOVAL = auto()       # Term permanently removed
    ALIAS = auto()         # New alias for existing term
    SPLIT = auto()         # One term split into multiple
    MERGE = auto()         # Multiple terms merged into one


class CompatMode(Enum):
    FULL = auto()          # 100% backward compatible
    PARTIAL = auto()       # Some features work, some don't
    BREAKING = auto()      # Not backward compatible
    NONE = auto()           # Incompatible


class NegotiationResult(Enum):
    EXACT_MATCH = auto()   # Client and server on same version
    COMPATIBLE = auto()    # Different versions, fully compatible
    DEGRADED = auto()      # Works with reduced functionality
    REJECTED = auto()      # Incompatible, cannot proceed


# ─── Data Structures ─────────────────────────────────────────────────────────

@dataclass
class SemanticVersion:
    """Semantic versioning for dictionaries."""
    major: int = 1
    minor: int = 0
    patch: int = 0

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"

    def __lt__(self, other: SemanticVersion) -> bool:
        return (self.major, self.minor, self.patch) < (other.major, other.minor, other.patch)

    def __le__(self, other: SemanticVersion) -> bool:
        return (self.major, self.minor, self.patch) <= (other.major, other.minor, other.patch)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SemanticVersion):
            return NotImplemented
        return (self.major, self.minor, self.patch) == (other.major, other.minor, other.patch)

    def __hash__(self) -> int:
        return hash((self.major, self.minor, self.patch))

    def is_compatible_with(self, other: SemanticVersion) -> CompatMode:
        """Check compatibility between two versions."""
        if self == other:
            return CompatMode.FULL
        if self.major != other.major:
            return CompatMode.BREAKING
        if self.minor != other.minor:
            return CompatMode.PARTIAL  # Minor = additive changes
        return CompatMode.FULL  # Patch = bug fixes only


@dataclass
class TermEntry:
    """A term in a dictionary."""
    term_id: str
    source_term: str
    target_term: str
    domain: str
    confidence: float = 0.9
    deprecated: bool = False
    deprecated_at: float = 0.0
    replacement_id: str = ""  # What to use instead
    added_in: str = "1.0.0"   # Version when added
    modified_in: str = ""     # Last version it was modified
    aliases: List[str] = field(default_factory=list)

    @property
    def effective_confidence(self) -> float:
        """Confidence degrades for deprecated terms."""
        if not self.deprecated:
            return self.confidence
        # Degrade over time: halve confidence per 30 days
        age_days = (time.time() - self.deprecated_at) / 86400.0
        decay = 0.5 ** (age_days / 30.0)
        return self.confidence * decay


@dataclass
class DictionaryChange:
    """A single change to a dictionary."""
    change_id: str
    change_type: ChangeType
    term_id: str
    description: str
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    timestamp: float = field(default_factory=time.time)
    author: str = ""
    change_hash: str = ""
    prev_hash: str = ""

    def __post_init__(self):
        if not self.change_hash:
            content = f"{self.change_id}:{self.change_type.name}:{self.term_id}:{self.timestamp}:{self.prev_hash}"
            self.change_hash = hashlib.sha256(content.encode()).hexdigest()


@dataclass
class DictionaryVersion:
    """A versioned dictionary."""
    dict_id: str
    name: str
    version: SemanticVersion
    phase: DictPhase = DictPhase.DRAFT
    terms: Dict[str, TermEntry] = field(default_factory=dict)
    changes: List[DictionaryChange] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    published_at: float = 0.0
    deprecated_at: float = 0.0
    parent_version: Optional[str] = None  # Previous version string
    source_domain: str = ""
    target_domain: str = ""

    @property
    def term_count(self) -> int:
        return len([t for t in self.terms.values() if not t.deprecated])

    @property
    def deprecated_count(self) -> int:
        return len([t for t in self.terms.values() if t.deprecated])

    def version_hash(self) -> str:
        """Content-based hash of the dictionary version."""
        content = f"{self.dict_id}:{self.version}:{self.phase.name}"
        for tid in sorted(self.terms.keys()):
            t = self.terms[tid]
            content += f":{tid}={t.source_term}>{t.target_term}:{t.confidence}"
        return hashlib.sha256(content.encode()).hexdigest()


# ─── Evolution FSM ────────────────────────────────────────────────────────────

class EvolutionFSM:
    """Manages dictionary lifecycle transitions."""

    VALID_TRANSITIONS = {
        DictPhase.DRAFT: {DictPhase.REVIEW},
        DictPhase.REVIEW: {DictPhase.PUBLISHED, DictPhase.DRAFT},  # Reject → back to draft
        DictPhase.PUBLISHED: {DictPhase.DEPRECATED},
        DictPhase.DEPRECATED: {DictPhase.RETIRED, DictPhase.PUBLISHED},  # Un-deprecate
        DictPhase.RETIRED: set(),  # Terminal state
    }

    def __init__(self):
        self.transition_log: List[Dict] = []

    def can_transition(self, current: DictPhase, target: DictPhase) -> bool:
        return target in self.VALID_TRANSITIONS.get(current, set())

    def transition(self, dictionary: DictionaryVersion,
                   target: DictPhase, reason: str = "") -> bool:
        """Transition a dictionary to a new phase."""
        if not self.can_transition(dictionary.phase, target):
            return False

        old_phase = dictionary.phase
        dictionary.phase = target

        if target == DictPhase.PUBLISHED:
            dictionary.published_at = time.time()
        elif target == DictPhase.DEPRECATED:
            dictionary.deprecated_at = time.time()

        self.transition_log.append({
            "dict_id": dictionary.dict_id,
            "version": str(dictionary.version),
            "from": old_phase.name,
            "to": target.name,
            "reason": reason,
            "timestamp": time.time(),
        })
        return True


# ─── Term Migration ──────────────────────────────────────────────────────────

class TermMigrator:
    """Manages term-level changes within dictionaries."""

    def __init__(self):
        self.change_chain: List[DictionaryChange] = []

    def _append_change(self, change: DictionaryChange):
        prev_hash = self.change_chain[-1].change_hash if self.change_chain else "genesis"
        change.prev_hash = prev_hash
        # Recompute hash with prev_hash
        content = f"{change.change_id}:{change.change_type.name}:{change.term_id}:{change.timestamp}:{change.prev_hash}"
        change.change_hash = hashlib.sha256(content.encode()).hexdigest()
        self.change_chain.append(change)

    def add_term(self, dictionary: DictionaryVersion,
                 term: TermEntry) -> DictionaryChange:
        """Add a new term to the dictionary."""
        term.added_in = str(dictionary.version)
        dictionary.terms[term.term_id] = term

        change = DictionaryChange(
            change_id=f"add_{term.term_id}_{time.time()}",
            change_type=ChangeType.ADDITION,
            term_id=term.term_id,
            description=f"Added term: {term.source_term} → {term.target_term}",
            new_value=term.target_term,
        )
        self._append_change(change)
        dictionary.changes.append(change)
        return change

    def modify_term(self, dictionary: DictionaryVersion,
                    term_id: str, new_target: str,
                    new_confidence: float = None) -> Optional[DictionaryChange]:
        """Modify an existing term."""
        term = dictionary.terms.get(term_id)
        if not term:
            return None

        old_value = term.target_term
        term.target_term = new_target
        term.modified_in = str(dictionary.version)
        if new_confidence is not None:
            term.confidence = new_confidence

        change = DictionaryChange(
            change_id=f"mod_{term_id}_{time.time()}",
            change_type=ChangeType.MODIFICATION,
            term_id=term_id,
            description=f"Modified: {old_value} → {new_target}",
            old_value=old_value,
            new_value=new_target,
        )
        self._append_change(change)
        dictionary.changes.append(change)
        return change

    def deprecate_term(self, dictionary: DictionaryVersion,
                       term_id: str, replacement_id: str = "") -> Optional[DictionaryChange]:
        """Deprecate a term with optional replacement."""
        term = dictionary.terms.get(term_id)
        if not term:
            return None

        term.deprecated = True
        term.deprecated_at = time.time()
        term.replacement_id = replacement_id

        change = DictionaryChange(
            change_id=f"dep_{term_id}_{time.time()}",
            change_type=ChangeType.DEPRECATION,
            term_id=term_id,
            description=f"Deprecated: {term.source_term}" + (
                f" → use {replacement_id}" if replacement_id else ""),
            old_value=term.target_term,
        )
        self._append_change(change)
        dictionary.changes.append(change)
        return change

    def remove_term(self, dictionary: DictionaryVersion,
                    term_id: str) -> Optional[DictionaryChange]:
        """Remove a term (must be deprecated first)."""
        term = dictionary.terms.get(term_id)
        if not term or not term.deprecated:
            return None

        change = DictionaryChange(
            change_id=f"rem_{term_id}_{time.time()}",
            change_type=ChangeType.REMOVAL,
            term_id=term_id,
            description=f"Removed: {term.source_term}",
            old_value=term.target_term,
        )
        self._append_change(change)
        dictionary.changes.append(change)
        del dictionary.terms[term_id]
        return change

    def add_alias(self, dictionary: DictionaryVersion,
                  term_id: str, alias: str) -> Optional[DictionaryChange]:
        """Add an alias for an existing term."""
        term = dictionary.terms.get(term_id)
        if not term:
            return None

        term.aliases.append(alias)

        change = DictionaryChange(
            change_id=f"alias_{term_id}_{time.time()}",
            change_type=ChangeType.ALIAS,
            term_id=term_id,
            description=f"Alias added: {alias} → {term.source_term}",
            new_value=alias,
        )
        self._append_change(change)
        dictionary.changes.append(change)
        return change

    def verify_chain(self) -> Tuple[bool, List[int]]:
        """Verify the change chain integrity."""
        broken = []
        for i, change in enumerate(self.change_chain):
            expected_prev = self.change_chain[i - 1].change_hash if i > 0 else "genesis"
            if change.prev_hash != expected_prev:
                broken.append(i)

            expected_hash = hashlib.sha256(
                f"{change.change_id}:{change.change_type.name}:{change.term_id}:{change.timestamp}:{change.prev_hash}".encode()
            ).hexdigest()
            if change.change_hash != expected_hash:
                broken.append(i)

        return len(broken) == 0, broken


# ─── Schema Negotiation ──────────────────────────────────────────────────────

class SchemaNegotiator:
    """Negotiates dictionary version compatibility between parties."""

    def __init__(self):
        self.available_versions: Dict[str, List[DictionaryVersion]] = defaultdict(list)

    def register_version(self, dictionary: DictionaryVersion):
        """Register an available dictionary version."""
        self.available_versions[dictionary.dict_id].append(dictionary)

    def negotiate(self, dict_id: str,
                  client_version: SemanticVersion,
                  server_versions: List[SemanticVersion] = None
                  ) -> Tuple[NegotiationResult, Optional[SemanticVersion]]:
        """Negotiate a compatible version between client and server."""
        if server_versions is None:
            server_versions = [
                d.version for d in self.available_versions.get(dict_id, [])
                if d.phase in (DictPhase.PUBLISHED, DictPhase.DEPRECATED)
            ]

        if not server_versions:
            return NegotiationResult.REJECTED, None

        # Exact match
        if client_version in server_versions:
            return NegotiationResult.EXACT_MATCH, client_version

        # Find best compatible version
        compatible = []
        for sv in server_versions:
            compat = client_version.is_compatible_with(sv)
            if compat == CompatMode.FULL:
                compatible.append((sv, NegotiationResult.COMPATIBLE))
            elif compat == CompatMode.PARTIAL:
                compatible.append((sv, NegotiationResult.DEGRADED))

        if compatible:
            # Prefer COMPATIBLE over DEGRADED, then highest version
            compatible.sort(key=lambda x: (x[1] == NegotiationResult.COMPATIBLE,
                                            x[0].minor, x[0].patch), reverse=True)
            return compatible[0][1], compatible[0][0]

        return NegotiationResult.REJECTED, None

    def build_compatibility_matrix(self, dict_id: str) -> Dict[str, Dict[str, str]]:
        """Build a compatibility matrix for all versions of a dictionary."""
        versions = [d.version for d in self.available_versions.get(dict_id, [])
                    if d.phase in (DictPhase.PUBLISHED, DictPhase.DEPRECATED)]

        matrix = {}
        for v1 in versions:
            row = {}
            for v2 in versions:
                row[str(v2)] = v1.is_compatible_with(v2).name
            matrix[str(v1)] = row

        return matrix


# ─── Confidence Degradation ──────────────────────────────────────────────────

class ConfidenceDegradation:
    """Models how confidence degrades for stale or deprecated mappings."""

    def __init__(self, freshness_half_life_days: float = 90.0,
                 min_confidence: float = 0.1):
        self.half_life = freshness_half_life_days * 86400.0  # Convert to seconds
        self.min_confidence = min_confidence

    def degrade(self, original_confidence: float,
                age_seconds: float,
                is_deprecated: bool = False) -> float:
        """Calculate degraded confidence."""
        if age_seconds <= 0:
            return original_confidence

        effective_half_life = self.half_life / 2.0 if is_deprecated else self.half_life
        decay = 0.5 ** (age_seconds / effective_half_life)
        return max(self.min_confidence, original_confidence * decay)

    def time_to_threshold(self, original_confidence: float,
                          threshold: float,
                          is_deprecated: bool = False) -> float:
        """Calculate time until confidence drops below threshold."""
        if original_confidence <= threshold:
            return 0.0
        if threshold <= self.min_confidence:
            return float('inf')

        ratio = threshold / original_confidence
        effective_half_life = self.half_life / 2.0 if is_deprecated else self.half_life
        import math
        return -effective_half_life * math.log2(ratio)


# ─── Migration Protocol ──────────────────────────────────────────────────────

class MigrationProtocol:
    """Manages migration from one dictionary version to another."""

    def __init__(self):
        self.migration_plans: List[Dict] = []

    def plan_migration(self, source: DictionaryVersion,
                       target: DictionaryVersion) -> Dict:
        """Plan a migration from source to target version."""
        compat = source.version.is_compatible_with(target.version)

        additions = set(target.terms.keys()) - set(source.terms.keys())
        removals = set(source.terms.keys()) - set(target.terms.keys())
        common = set(source.terms.keys()) & set(target.terms.keys())

        modifications = []
        for tid in common:
            s_term = source.terms[tid]
            t_term = target.terms[tid]
            if s_term.target_term != t_term.target_term:
                modifications.append(tid)
            elif s_term.confidence != t_term.confidence:
                modifications.append(tid)
            elif s_term.deprecated != t_term.deprecated:
                modifications.append(tid)

        plan = {
            "source_version": str(source.version),
            "target_version": str(target.version),
            "compatibility": compat.name,
            "additions": len(additions),
            "removals": len(removals),
            "modifications": len(modifications),
            "unchanged": len(common) - len(modifications),
            "total_changes": len(additions) + len(removals) + len(modifications),
            "added_terms": list(additions),
            "removed_terms": list(removals),
            "modified_terms": modifications,
            "migration_risk": self._assess_risk(compat, len(removals), len(modifications)),
        }

        self.migration_plans.append(plan)
        return plan

    def execute_migration(self, source: DictionaryVersion,
                          target: DictionaryVersion) -> Dict:
        """Execute the migration, creating a mapping from source terms to target terms."""
        plan = self.plan_migration(source, target)

        # Build term mapping
        mapping = {}
        for tid in source.terms:
            if tid in target.terms:
                t_term = target.terms[tid]
                if t_term.deprecated and t_term.replacement_id:
                    mapping[tid] = t_term.replacement_id
                else:
                    mapping[tid] = tid
            else:
                mapping[tid] = None  # Removed, no mapping

        return {
            "plan": plan,
            "mapping": mapping,
            "unmapped_count": sum(1 for v in mapping.values() if v is None),
            "mapped_count": sum(1 for v in mapping.values() if v is not None),
        }

    def _assess_risk(self, compat: CompatMode,
                     removals: int, modifications: int) -> str:
        if compat == CompatMode.BREAKING:
            return "high"
        if removals > 5 or modifications > 10:
            return "medium"
        if removals > 0 or modifications > 3:
            return "low"
        return "minimal"


# ─── Cross-Domain Evolution ──────────────────────────────────────────────────

class CrossDomainEvolution:
    """Coordinates evolution across interconnected dictionaries."""

    def __init__(self):
        self.dictionaries: Dict[str, DictionaryVersion] = {}
        self.dependencies: Dict[str, Set[str]] = defaultdict(set)  # dict_id → depends_on

    def register(self, dictionary: DictionaryVersion):
        self.dictionaries[dictionary.dict_id] = dictionary

    def add_dependency(self, dict_id: str, depends_on: str):
        """Record that dict_id depends on depends_on."""
        self.dependencies[dict_id].add(depends_on)

    def impact_analysis(self, changed_dict_id: str,
                        change_type: ChangeType) -> Dict:
        """Analyze the impact of changing a dictionary on its dependents."""
        affected = set()
        self._find_dependents(changed_dict_id, affected)

        severity = "low"
        if change_type in (ChangeType.REMOVAL, ChangeType.MODIFICATION):
            severity = "high" if len(affected) > 2 else "medium"
        elif change_type == ChangeType.DEPRECATION:
            severity = "medium"

        return {
            "changed_dict": changed_dict_id,
            "change_type": change_type.name,
            "affected_dictionaries": list(affected),
            "affected_count": len(affected),
            "severity": severity,
            "requires_coordinated_update": len(affected) > 0 and severity != "low",
        }

    def _find_dependents(self, dict_id: str, result: Set[str]):
        """Recursively find all dictionaries that depend on dict_id."""
        for dep_id, deps in self.dependencies.items():
            if dict_id in deps and dep_id not in result:
                result.add(dep_id)
                self._find_dependents(dep_id, result)


# ═══════════════════════════════════════════════════════════════════════════════
# TESTS
# ═══════════════════════════════════════════════════════════════════════════════

def _make_term(tid: str, source: str, target: str,
               domain: str = "medical", confidence: float = 0.9) -> TermEntry:
    return TermEntry(term_id=tid, source_term=source, target_term=target,
                     domain=domain, confidence=confidence)


def _make_dict(dict_id: str, name: str,
               major: int = 1, minor: int = 0, patch: int = 0,
               phase: DictPhase = DictPhase.DRAFT) -> DictionaryVersion:
    return DictionaryVersion(
        dict_id=dict_id, name=name,
        version=SemanticVersion(major, minor, patch),
        phase=phase,
        source_domain="medical", target_domain="regulatory",
    )


def run_tests():
    results = []

    def check(name, condition, detail=""):
        results.append((name, condition, detail))

    # ─── S1: Semantic Version ─────────────────────────────────────────

    v1 = SemanticVersion(1, 0, 0)
    v1_1 = SemanticVersion(1, 1, 0)
    v1_0_1 = SemanticVersion(1, 0, 1)
    v2 = SemanticVersion(2, 0, 0)

    check("s1_version_str", str(v1) == "1.0.0")
    check("s1_lt", v1 < v1_1)
    check("s1_lt_patch", v1 < v1_0_1)
    check("s1_lt_major", v1 < v2)
    check("s1_eq", v1 == SemanticVersion(1, 0, 0))
    check("s1_le", v1 <= v1)

    # Compatibility
    check("s1_compat_same", v1.is_compatible_with(v1) == CompatMode.FULL)
    check("s1_compat_patch", v1.is_compatible_with(v1_0_1) == CompatMode.FULL)
    check("s1_compat_minor", v1.is_compatible_with(v1_1) == CompatMode.PARTIAL)
    check("s1_compat_major", v1.is_compatible_with(v2) == CompatMode.BREAKING)

    # ─── S2: Dictionary Version ───────────────────────────────────────

    d = _make_dict("dict_med", "Medical Terms")
    check("s2_initial_phase", d.phase == DictPhase.DRAFT)
    check("s2_no_terms", d.term_count == 0)

    # Add terms
    d.terms["t1"] = _make_term("t1", "hypertension", "high blood pressure")
    d.terms["t2"] = _make_term("t2", "tachycardia", "fast heart rate")
    check("s2_term_count", d.term_count == 2)
    check("s2_version_hash", len(d.version_hash()) == 64)

    # Deprecated term
    d.terms["t2"].deprecated = True
    check("s2_deprecated_count", d.deprecated_count == 1)
    check("s2_active_count", d.term_count == 1)

    # ─── S3: Evolution FSM ────────────────────────────────────────────

    fsm = EvolutionFSM()
    d3 = _make_dict("dict_fsm", "FSM Test")

    check("s3_can_draft_review", fsm.can_transition(DictPhase.DRAFT, DictPhase.REVIEW))
    check("s3_cannot_draft_publish",
          not fsm.can_transition(DictPhase.DRAFT, DictPhase.PUBLISHED))

    # DRAFT → REVIEW
    check("s3_to_review", fsm.transition(d3, DictPhase.REVIEW, "ready"))
    check("s3_is_review", d3.phase == DictPhase.REVIEW)

    # REVIEW → PUBLISHED
    check("s3_to_published", fsm.transition(d3, DictPhase.PUBLISHED, "approved"))
    check("s3_is_published", d3.phase == DictPhase.PUBLISHED)
    check("s3_published_at", d3.published_at > 0)

    # PUBLISHED → DEPRECATED
    check("s3_to_deprecated", fsm.transition(d3, DictPhase.DEPRECATED, "v2 released"))
    check("s3_is_deprecated", d3.phase == DictPhase.DEPRECATED)

    # DEPRECATED → RETIRED
    check("s3_to_retired", fsm.transition(d3, DictPhase.RETIRED, "end of life"))
    check("s3_is_retired", d3.phase == DictPhase.RETIRED)

    # RETIRED is terminal
    check("s3_retired_terminal",
          not fsm.transition(d3, DictPhase.PUBLISHED, "nope"))

    # REVIEW → DRAFT (rejection)
    d3b = _make_dict("dict_fsm2", "FSM Test 2")
    fsm.transition(d3b, DictPhase.REVIEW)
    check("s3_reject_to_draft", fsm.transition(d3b, DictPhase.DRAFT, "needs work"))
    check("s3_back_to_draft", d3b.phase == DictPhase.DRAFT)

    # DEPRECATED → PUBLISHED (un-deprecate)
    d3c = _make_dict("dict_fsm3", "FSM Test 3")
    fsm.transition(d3c, DictPhase.REVIEW)
    fsm.transition(d3c, DictPhase.PUBLISHED)
    fsm.transition(d3c, DictPhase.DEPRECATED)
    check("s3_undeprecate", fsm.transition(d3c, DictPhase.PUBLISHED, "still needed"))

    # Transition log
    check("s3_log_count", len(fsm.transition_log) > 5)

    # ─── S4: Term Migration ───────────────────────────────────────────

    migrator = TermMigrator()
    d4 = _make_dict("dict_mig", "Migration Test", phase=DictPhase.PUBLISHED)

    # Add terms
    t1 = _make_term("med_001", "aspirin", "acetylsalicylic acid")
    t2 = _make_term("med_002", "ibuprofen", "NSAID analgesic")
    c1 = migrator.add_term(d4, t1)
    c2 = migrator.add_term(d4, t2)
    check("s4_add_term", c1.change_type == ChangeType.ADDITION)
    check("s4_two_terms", d4.term_count == 2)
    check("s4_added_in", t1.added_in == "1.0.0")

    # Modify term
    c3 = migrator.modify_term(d4, "med_002", "non-steroidal anti-inflammatory", 0.95)
    check("s4_modify", c3 is not None)
    check("s4_modified_value", d4.terms["med_002"].target_term == "non-steroidal anti-inflammatory")
    check("s4_old_value", c3.old_value == "NSAID analgesic")

    # Modify nonexistent
    check("s4_modify_none", migrator.modify_term(d4, "none", "x") is None)

    # Deprecate term
    c4 = migrator.deprecate_term(d4, "med_001", replacement_id="med_003")
    check("s4_deprecated", c4 is not None)
    check("s4_is_deprecated", d4.terms["med_001"].deprecated)
    check("s4_replacement", d4.terms["med_001"].replacement_id == "med_003")

    # Add alias
    c5 = migrator.add_alias(d4, "med_002", "ibu")
    check("s4_alias", c5 is not None)
    check("s4_alias_stored", "ibu" in d4.terms["med_002"].aliases)

    # Remove deprecated term
    c6 = migrator.remove_term(d4, "med_001")
    check("s4_remove", c6 is not None)
    check("s4_removed", "med_001" not in d4.terms)

    # Cannot remove non-deprecated term
    check("s4_remove_non_dep", migrator.remove_term(d4, "med_002") is None)

    # Chain integrity
    valid, broken = migrator.verify_chain()
    check("s4_chain_valid", valid, f"broken={broken}")
    check("s4_chain_length", len(migrator.change_chain) == 6)

    # ─── S5: Schema Negotiation ───────────────────────────────────────

    negotiator = SchemaNegotiator()

    d_1_0 = _make_dict("dict_neg", "Negotiation", 1, 0, 0, DictPhase.PUBLISHED)
    d_1_1 = _make_dict("dict_neg", "Negotiation", 1, 1, 0, DictPhase.PUBLISHED)
    d_1_2 = _make_dict("dict_neg", "Negotiation", 1, 2, 0, DictPhase.PUBLISHED)
    d_2_0 = _make_dict("dict_neg", "Negotiation", 2, 0, 0, DictPhase.PUBLISHED)
    d_0_9 = _make_dict("dict_neg", "Negotiation", 1, 0, 0, DictPhase.DEPRECATED)

    for d in [d_1_0, d_1_1, d_1_2, d_2_0, d_0_9]:
        negotiator.register_version(d)

    # Exact match
    result, ver = negotiator.negotiate("dict_neg", SemanticVersion(1, 1, 0))
    check("s5_exact_match", result == NegotiationResult.EXACT_MATCH)
    check("s5_exact_version", ver == SemanticVersion(1, 1, 0))

    # Compatible (same major, different minor)
    result2, ver2 = negotiator.negotiate("dict_neg", SemanticVersion(1, 3, 0))
    check("s5_compatible", result2 == NegotiationResult.DEGRADED,
          f"result={result2.name}")

    # Incompatible (different major, no match)
    result3, ver3 = negotiator.negotiate("dict_neg", SemanticVersion(3, 0, 0))
    check("s5_rejected", result3 == NegotiationResult.REJECTED)

    # No available versions
    result4, ver4 = negotiator.negotiate("nonexistent", SemanticVersion(1, 0, 0))
    check("s5_no_versions", result4 == NegotiationResult.REJECTED)

    # Compatibility matrix
    matrix = negotiator.build_compatibility_matrix("dict_neg")
    check("s5_matrix_size", len(matrix) > 0)
    check("s5_self_full", matrix["1.0.0"]["1.0.0"] == "FULL")

    # ─── S6: Confidence Degradation ───────────────────────────────────

    degradation = ConfidenceDegradation(freshness_half_life_days=90.0)

    # No age → no degradation
    check("s6_no_age", degradation.degrade(0.9, 0.0) == 0.9)

    # After 90 days → half confidence
    d90 = 90 * 86400.0
    degraded = degradation.degrade(0.9, d90)
    check("s6_half_life", abs(degraded - 0.45) < 0.01,
          f"degraded={degraded:.3f}")

    # After 180 days → quarter confidence
    degraded180 = degradation.degrade(0.9, d90 * 2)
    check("s6_two_halflives", abs(degraded180 - 0.225) < 0.01,
          f"degraded={degraded180:.3f}")

    # Deprecated degrades faster (half the half-life)
    dep_degraded = degradation.degrade(0.9, d90, is_deprecated=True)
    check("s6_deprecated_faster", dep_degraded < degraded,
          f"dep={dep_degraded:.3f} vs normal={degraded:.3f}")

    # Floor at min_confidence
    very_old = degradation.degrade(0.9, d90 * 100)
    check("s6_min_floor", very_old >= 0.1,
          f"floor={very_old:.3f}")

    # Time to threshold
    ttl = degradation.time_to_threshold(0.9, 0.45)
    check("s6_ttl", abs(ttl - d90) < 86400,  # Within 1 day of 90 days
          f"ttl_days={ttl/86400:.1f}")

    # Already below threshold
    check("s6_already_below", degradation.time_to_threshold(0.3, 0.5) == 0.0)

    # ─── S7: Migration Protocol ───────────────────────────────────────

    migration = MigrationProtocol()

    # Source v1
    src = _make_dict("dict_mig_test", "Migration", 1, 0, 0, DictPhase.PUBLISHED)
    src.terms["t1"] = _make_term("t1", "old_term_1", "meaning_1")
    src.terms["t2"] = _make_term("t2", "old_term_2", "meaning_2")
    src.terms["t3"] = _make_term("t3", "old_term_3", "meaning_3")

    # Target v2 — t1 unchanged, t2 modified, t3 removed, t4 added
    tgt = _make_dict("dict_mig_test", "Migration", 2, 0, 0, DictPhase.PUBLISHED)
    tgt.terms["t1"] = _make_term("t1", "old_term_1", "meaning_1")
    tgt.terms["t2"] = _make_term("t2", "old_term_2", "new_meaning_2", confidence=0.95)
    tgt.terms["t4"] = _make_term("t4", "new_term_4", "meaning_4")

    plan = migration.plan_migration(src, tgt)
    check("s7_additions", plan["additions"] == 1)
    check("s7_removals", plan["removals"] == 1)
    check("s7_modifications", plan["modifications"] == 1)
    check("s7_unchanged", plan["unchanged"] == 1)
    check("s7_total_changes", plan["total_changes"] == 3)
    check("s7_breaking", plan["compatibility"] == "BREAKING")
    check("s7_risk_high", plan["migration_risk"] == "high")

    # Execute migration
    exec_result = migration.execute_migration(src, tgt)
    check("s7_mapped", exec_result["mapped_count"] == 2)  # t1→t1, t2→t2
    check("s7_unmapped", exec_result["unmapped_count"] == 1)  # t3 removed

    # Low-risk migration (patch change, no removals)
    src2 = _make_dict("dict_patch", "Patch", 1, 0, 0, DictPhase.PUBLISHED)
    src2.terms["p1"] = _make_term("p1", "a", "b")
    tgt2 = _make_dict("dict_patch", "Patch", 1, 0, 1, DictPhase.PUBLISHED)
    tgt2.terms["p1"] = _make_term("p1", "a", "b")
    plan2 = migration.plan_migration(src2, tgt2)
    check("s7_minimal_risk", plan2["migration_risk"] == "minimal")

    # ─── S8: Cross-Domain Evolution ───────────────────────────────────

    cross = CrossDomainEvolution()

    d_base = _make_dict("base", "Base Terms")
    d_med = _make_dict("medical", "Medical Terms")
    d_reg = _make_dict("regulatory", "Regulatory Terms")
    d_report = _make_dict("reporting", "Reporting Terms")

    cross.register(d_base)
    cross.register(d_med)
    cross.register(d_reg)
    cross.register(d_report)

    # medical depends on base
    # regulatory depends on base and medical
    # reporting depends on regulatory
    cross.add_dependency("medical", "base")
    cross.add_dependency("regulatory", "base")
    cross.add_dependency("regulatory", "medical")
    cross.add_dependency("reporting", "regulatory")

    # Impact of changing base
    impact_base = cross.impact_analysis("base", ChangeType.REMOVAL)
    check("s8_base_impact", impact_base["affected_count"] == 3,
          f"affected={impact_base['affected_count']}")
    check("s8_base_severity", impact_base["severity"] == "high")
    check("s8_base_coordinated", impact_base["requires_coordinated_update"])

    # Impact of changing regulatory (only reporting affected)
    impact_reg = cross.impact_analysis("regulatory", ChangeType.ADDITION)
    check("s8_reg_impact", impact_reg["affected_count"] == 1)
    check("s8_reg_severity", impact_reg["severity"] == "low")

    # Impact of changing reporting (no dependents)
    impact_rep = cross.impact_analysis("reporting", ChangeType.MODIFICATION)
    check("s8_report_impact", impact_rep["affected_count"] == 0)
    check("s8_report_no_coord", not impact_rep["requires_coordinated_update"])

    # ─── S9: Term effective confidence ────────────────────────────────

    # Active term
    active_term = _make_term("active", "a", "b", confidence=0.9)
    check("s9_active_full", abs(active_term.effective_confidence - 0.9) < 0.001)

    # Deprecated term (recently)
    dep_term = _make_term("dep", "c", "d", confidence=0.9)
    dep_term.deprecated = True
    dep_term.deprecated_at = time.time() - 1  # Just deprecated
    check("s9_dep_recent", dep_term.effective_confidence > 0.8,
          f"conf={dep_term.effective_confidence:.3f}")

    # Deprecated long ago
    old_dep = _make_term("old_dep", "e", "f", confidence=0.9)
    old_dep.deprecated = True
    old_dep.deprecated_at = time.time() - (60 * 86400)  # 60 days ago
    check("s9_dep_old", old_dep.effective_confidence < 0.5,
          f"conf={old_dep.effective_confidence:.3f}")

    # ─── S10: Full lifecycle E2E ──────────────────────────────────────

    fsm_e2e = EvolutionFSM()
    mig_e2e = TermMigrator()
    neg_e2e = SchemaNegotiator()

    # v1.0.0: Create and publish
    v1_dict = _make_dict("lifecycle", "Lifecycle Test", 1, 0, 0)
    mig_e2e.add_term(v1_dict, _make_term("lc_001", "fever", "pyrexia"))
    mig_e2e.add_term(v1_dict, _make_term("lc_002", "cough", "tussis"))
    mig_e2e.add_term(v1_dict, _make_term("lc_003", "headache", "cephalalgia"))
    fsm_e2e.transition(v1_dict, DictPhase.REVIEW, "v1 ready")
    fsm_e2e.transition(v1_dict, DictPhase.PUBLISHED, "approved")
    neg_e2e.register_version(v1_dict)

    check("s10_v1_published", v1_dict.phase == DictPhase.PUBLISHED)
    check("s10_v1_3_terms", v1_dict.term_count == 3)

    # v1.1.0: Add term, modify term (minor version)
    v1_1_dict = _make_dict("lifecycle", "Lifecycle Test", 1, 1, 0)
    # Copy existing terms
    for tid, t in v1_dict.terms.items():
        v1_1_dict.terms[tid] = TermEntry(
            term_id=t.term_id, source_term=t.source_term,
            target_term=t.target_term, domain=t.domain,
            confidence=t.confidence, added_in=t.added_in,
        )
    mig_e2e.add_term(v1_1_dict, _make_term("lc_004", "nausea", "emesis"))
    mig_e2e.modify_term(v1_1_dict, "lc_003", "cephalgia", 0.95)  # Fix spelling
    fsm_e2e.transition(v1_1_dict, DictPhase.REVIEW)
    fsm_e2e.transition(v1_1_dict, DictPhase.PUBLISHED)
    neg_e2e.register_version(v1_1_dict)

    check("s10_v1_1_4_terms", v1_1_dict.term_count == 4)

    # v2.0.0: Breaking change — deprecate old term, add new
    v2_dict = _make_dict("lifecycle", "Lifecycle Test", 2, 0, 0)
    for tid, t in v1_1_dict.terms.items():
        v2_dict.terms[tid] = TermEntry(
            term_id=t.term_id, source_term=t.source_term,
            target_term=t.target_term, domain=t.domain,
            confidence=t.confidence, added_in=t.added_in,
        )
    mig_e2e.deprecate_term(v2_dict, "lc_002", replacement_id="lc_005")
    mig_e2e.add_term(v2_dict, _make_term("lc_005", "cough", "pertussis-like cough"))
    fsm_e2e.transition(v2_dict, DictPhase.REVIEW)
    fsm_e2e.transition(v2_dict, DictPhase.PUBLISHED)
    neg_e2e.register_version(v2_dict)

    # Deprecate v1.0
    fsm_e2e.transition(v1_dict, DictPhase.DEPRECATED, "v1.1+ available")

    # Negotiate: client at v1.0 → should get degraded (v1.1 or v1.2)
    neg_result, neg_ver = neg_e2e.negotiate("lifecycle", SemanticVersion(1, 0, 0))
    check("s10_negotiate_v1", neg_result in (NegotiationResult.EXACT_MATCH,
                                              NegotiationResult.COMPATIBLE,
                                              NegotiationResult.DEGRADED),
          f"result={neg_result.name}, ver={neg_ver}")

    # Client at v2.0 → exact match
    neg_result2, neg_ver2 = neg_e2e.negotiate("lifecycle", SemanticVersion(2, 0, 0))
    check("s10_negotiate_v2", neg_result2 == NegotiationResult.EXACT_MATCH)

    # Migration plan v1→v2
    mig_protocol = MigrationProtocol()
    mig_plan = mig_protocol.plan_migration(v1_dict, v2_dict)
    check("s10_migration_has_changes", mig_plan["total_changes"] > 0)
    check("s10_migration_breaking", mig_plan["compatibility"] == "BREAKING")

    # Chain integrity across all operations
    valid, broken = mig_e2e.verify_chain()
    check("s10_chain_valid", valid, f"broken={broken}")

    # ─── S11: Edge cases ──────────────────────────────────────────────

    # Empty dictionary
    empty = _make_dict("empty", "Empty")
    check("s11_empty_terms", empty.term_count == 0)
    check("s11_empty_hash", len(empty.version_hash()) == 64)

    # Version comparison edge cases
    v0 = SemanticVersion(0, 0, 0)
    check("s11_zero_version", str(v0) == "0.0.0")
    check("s11_zero_lt", v0 < v1)
    check("s11_hash_equal", hash(v1) == hash(SemanticVersion(1, 0, 0)))

    # Deprecation of nonexistent term
    check("s11_dep_none", migrator.deprecate_term(d4, "nonexistent") is None)

    # Alias of nonexistent term
    check("s11_alias_none", migrator.add_alias(d4, "nonexistent", "x") is None)

    # Remove non-deprecated term
    non_dep_dict = _make_dict("nd", "ND")
    non_dep_dict.terms["nd1"] = _make_term("nd1", "x", "y")
    check("s11_remove_non_dep", migrator.remove_term(non_dep_dict, "nd1") is None)

    # ─── Print Results ────────────────────────────────────────────────

    passed = sum(1 for _, ok, _ in results if ok)
    failed = sum(1 for _, ok, _ in results if not ok)

    print(f"\n{'='*70}")
    print(f"Dictionary Entity Evolution & Schema Negotiation")
    print(f"{'='*70}")

    for name, ok, detail in results:
        status = "PASS" if ok else "FAIL"
        det = f" [{detail}]" if detail else ""
        if not ok:
            print(f"  {status}: {name}{det}")

    print(f"\n  Total: {passed + failed} | Passed: {passed} | Failed: {failed}")
    print(f"{'='*70}")

    if failed > 0:
        print("\nFAILED TESTS:")
        for name, ok, detail in results:
            if not ok:
                print(f"  FAIL: {name} [{detail}]")

    return passed, failed


if __name__ == "__main__":
    run_tests()
