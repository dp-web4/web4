"""Generic JSON-LD deserialization dispatcher for web4 documents.

Reads the ``@type`` field from any web4 JSON-LD document and dispatches
to the correct class's ``from_jsonld()`` method.  Supports both prefixed
(``web4:LinkedContextToken``) and bare (``LinkedContextToken``) type values.

Usage::

    import json, web4

    doc = json.load(open("entity.jsonld"))
    obj = web4.from_jsonld(doc)  # -> LCT, T3, R7Action, ...
"""

from __future__ import annotations

import json
from typing import Any, Callable, Dict, List, Optional


class UnknownTypeError(Exception):
    """Raised when a JSON-LD document has an unrecognized ``@type``."""

    def __init__(self, type_value: str) -> None:
        self.type_value = type_value
        super().__init__(
            f"Unknown @type: {type_value!r}. "
            f"Use supported_types() to list recognized types."
        )


# ---------------------------------------------------------------------------
# Lazy registry -- built on first use to avoid circular imports
# ---------------------------------------------------------------------------

_registry: Optional[Dict[str, Callable[..., Any]]] = None


def _build_registry() -> Dict[str, Callable[..., Any]]:
    """Build the @type -> deserializer mapping."""
    from .acp import AgentPlan, Decision, ExecutionRecord, Intent
    from .atp import ATPAccount, TransferResult
    from .attestation import AttestationEnvelope
    from .capability import (
        LevelRequirement,
        capability_assessment_from_jsonld,
        capability_framework_from_jsonld,
    )
    from .dictionary import (
        DictionaryEntity,
        DictionarySpec,
        TranslationChain,
        TranslationResult,
    )
    from .entity import EntityTypeInfo, entity_registry_from_jsonld
    from .lct import LCT
    from .r6 import ActionChain, R7Action, ReputationDelta
    from .trust import T3, V3, TrustQuery

    registry: Dict[str, Callable[..., Any]] = {}

    # Class-based: @type -> cls.from_jsonld
    _class_types: Dict[str, Any] = {
        "LinkedContextToken": LCT,
        "AttestationEnvelope": AttestationEnvelope,
        "T3Tensor": T3,
        "V3Tensor": V3,
        "TrustQuery": TrustQuery,
        "ATPAccount": ATPAccount,
        "TransferResult": TransferResult,
        "AgentPlan": AgentPlan,
        "Intent": Intent,
        "Decision": Decision,
        "ExecutionRecord": ExecutionRecord,
        "EntityTypeInfo": EntityTypeInfo,
        "LevelRequirement": LevelRequirement,
        "DictionarySpec": DictionarySpec,
        "TranslationResult": TranslationResult,
        "TranslationChain": TranslationChain,
        "DictionaryEntity": DictionaryEntity,
        "R7Action": R7Action,
        "ReputationDelta": ReputationDelta,
        "ActionChain": ActionChain,
    }

    # Function-based: @type -> module-level from_jsonld function
    _func_types: Dict[str, Callable[..., Any]] = {
        "EntityTypeRegistry": entity_registry_from_jsonld,
        "CapabilityAssessment": capability_assessment_from_jsonld,
        "CapabilityFramework": capability_framework_from_jsonld,
    }

    for type_name, cls in _class_types.items():
        fn: Callable[..., Any] = cls.from_jsonld
        registry[type_name] = fn
        registry[f"web4:{type_name}"] = fn

    for type_name, func in _func_types.items():
        registry[type_name] = func
        registry[f"web4:{type_name}"] = func

    return registry


def _get_registry() -> Dict[str, Callable[..., Any]]:
    """Return the registry, building it on first access."""
    global _registry  # noqa: PLW0603
    if _registry is None:
        _registry = _build_registry()
    return _registry


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def from_jsonld(doc: Dict[str, Any]) -> Any:
    """Deserialize any web4 JSON-LD document to the appropriate Python object.

    Reads the ``@type`` field and dispatches to the correct class's
    ``from_jsonld()`` method or module-level deserializer.

    Args:
        doc: A JSON-LD document dict with an ``@type`` field.

    Returns:
        The deserialized web4 object (LCT, T3, V3, R7Action, etc.).

    Raises:
        UnknownTypeError: If the ``@type`` is not recognized.
        ValueError: If the document has no ``@type`` field or ``@type``
            is not a string or list.
        TypeError: If *doc* is not a dict.
    """
    if not isinstance(doc, dict):
        raise TypeError(f"Expected dict, got {type(doc).__name__}")

    type_val = doc.get("@type")
    if type_val is None:
        raise ValueError("Document has no @type field")

    registry = _get_registry()

    # Single string @type
    if isinstance(type_val, str):
        deserializer = registry.get(type_val)
        if deserializer is not None:
            return deserializer(doc)
        raise UnknownTypeError(type_val)

    # List @type -- try each value in order
    if isinstance(type_val, list):
        for t in type_val:
            if isinstance(t, str):
                deserializer = registry.get(t)
                if deserializer is not None:
                    return deserializer(doc)
        raise UnknownTypeError(str(type_val))

    raise ValueError(
        f"@type must be a string or list, got {type(type_val).__name__}"
    )


def from_jsonld_string(s: str) -> Any:
    """Deserialize a JSON-LD string to the appropriate web4 object.

    Convenience wrapper that parses JSON then calls :func:`from_jsonld`.

    Args:
        s: A JSON string containing a web4 JSON-LD document.

    Returns:
        The deserialized web4 object.

    Raises:
        json.JSONDecodeError: If the string is not valid JSON.
        UnknownTypeError: If the ``@type`` is not recognized.
        ValueError: If the document has no ``@type`` field.
    """
    doc: Dict[str, Any] = json.loads(s)
    return from_jsonld(doc)


def supported_types() -> List[str]:
    """Return the list of supported ``@type`` values (bare names only).

    Returns:
        Sorted list of type names without the ``web4:`` prefix,
        e.g. ``["ActionChain", "AgentPlan", ...]``.
    """
    registry = _get_registry()
    return sorted(k for k in registry if not k.startswith("web4:"))


__all__ = [
    "UnknownTypeError",
    "from_jsonld",
    "from_jsonld_string",
    "supported_types",
]
