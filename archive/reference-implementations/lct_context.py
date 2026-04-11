from __future__ import annotations

"""Lightweight LCT context graph helper.

This module provides an in-process, MRH-aware context graph for Linked
Context Tokens (LCTs). It follows the logical model described in
WEB4_MRH_LCT_CONTEXT_SPEC.md without prescribing any particular storage
backend.

The design is intentionally minimal and JSON-friendly so it can be wired
into existing demos and tests without introducing external dependencies.
"""

from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Iterable, Any


MRHProfile = Dict[str, str]


@dataclass
class ContextTriple:
    """A single context triple linking LCTs with optional MRH profile."""

    subject: str
    predicate: str
    object: str
    mrh: Optional[MRHProfile] = None

    def to_dict(self) -> Dict[str, Any]:
        d = {
            "subject": self.subject,
            "predicate": self.predicate,
            "object": self.object,
        }
        if self.mrh is not None:
            d["mrh"] = self.mrh
        return d


class LCTContextGraph:
    """In-memory context graph for LCTs.

    This is intentionally simple: it stores triples in lists keyed by
    subject and object for quick neighborhood lookups.
    """

    def __init__(self) -> None:
        self._by_subject: Dict[str, List[ContextTriple]] = {}
        self._by_object: Dict[str, List[ContextTriple]] = {}

    # ------------------------------------------------------------------
    # Mutation
    # ------------------------------------------------------------------

    def add_link(
        self,
        subject: str,
        predicate: str,
        object: str,
        mrh: Optional[MRHProfile] = None,
    ) -> None:
        """Add a context triple to the graph.

        Duplicate triples are allowed but callers may choose to coalesce
        them if needed.
        """

        triple = ContextTriple(subject=subject, predicate=predicate, object=object, mrh=mrh)
        self._by_subject.setdefault(subject, []).append(triple)
        self._by_object.setdefault(object, []).append(triple)

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def neighbors(
        self,
        lct: str,
        *,
        predicate: Optional[str] = None,
        within_mrh: Optional[MRHProfile] = None,
        direction: str = "both",
    ) -> List[Dict[str, Any]]:
        """Return triples in the neighborhood of `lct`.

        Args:
            lct: The LCT URI whose neighborhood to query.
            predicate: Optional predicate filter.
            within_mrh: Optional MRH profile filter (coarse, dict-equality
                or subset-based depending on the provided keys).
            direction: "out", "in", or "both".
        """

        triples: List[ContextTriple] = []
        if direction in ("out", "both"):
            triples.extend(self._by_subject.get(lct, []))
        if direction in ("in", "both"):
            triples.extend(self._by_object.get(lct, []))

        def _mrh_matches(triple_mrh: Optional[MRHProfile]) -> bool:
            if within_mrh is None:
                return True
            if triple_mrh is None:
                return False
            # Simple subset match: all keys in within_mrh must match.
            for k, v in within_mrh.items():
                if triple_mrh.get(k) != v:
                    return False
            return True

        results: List[Dict[str, Any]] = []
        for t in triples:
            if predicate is not None and t.predicate != predicate:
                continue
            if not _mrh_matches(t.mrh):
                continue
            results.append(t.to_dict())
        return results

    def all_triples(self) -> List[Dict[str, Any]]:
        """Return all triples as dictionaries (for inspection or export)."""

        # Use a set of ids to avoid returning duplicates if a triple is
        # present in both subject and object indices.
        seen: set[int] = set()
        out: List[Dict[str, Any]] = []
        for triples in self._by_subject.values():
            for t in triples:
                tid = id(t)
                if tid in seen:
                    continue
                seen.add(tid)
                out.append(t.to_dict())
        return out


# A default global graph instance that demos can import and use without
# explicit dependency injection. More advanced applications may choose
# to manage their own graph instances instead.
GLOBAL_CONTEXT_GRAPH = LCTContextGraph()
