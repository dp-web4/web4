"""
Web4 schema validation — validate JSON-LD documents against Web4 JSON Schemas.

Provides programmatic validation of JSON-LD documents produced by SDK
``to_jsonld()`` methods (or received from external systems) against the
canonical JSON Schemas shipped with the package.

Schemas are resolved in order:

1. ``WEB4_SCHEMA_DIR`` environment variable (explicit override)
2. ``importlib.resources`` (works for wheel/pip installs)
3. Filesystem walk from module location (editable installs, repo checkouts)

The ``jsonschema`` package is an **optional** dependency. If not installed,
:func:`validate` raises :class:`SchemaValidationUnavailable` with
installation instructions.

Usage::

    from web4.validation import validate, list_schemas, get_schema

    # Validate an LCT document
    doc = lct.to_jsonld()
    result = validate(doc, "lct")
    assert result.valid

    # List available schemas
    for name in list_schemas():
        print(name)

    # Get raw schema dict
    schema = get_schema("attestation-envelope")
"""

from __future__ import annotations

import importlib.resources
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

__all__ = [
    "ValidationResult",
    "ValidationError",
    "SchemaValidationUnavailable",
    "SchemaNotFound",
    "validate",
    "list_schemas",
    "get_schema",
    "get_schema_dir",
]

# ── Schema directory resolution ─────────────────────────────────

# Schema name -> filename mapping.  Covers both JSON-LD schemas and
# standalone schemas shipped in web4-standard/schemas/.
_SCHEMA_FILES: Dict[str, str] = {
    "lct": "lct-jsonld.schema.json",
    "attestation-envelope": "attestation-envelope-jsonld.schema.json",
    "t3v3": "t3v3-jsonld.schema.json",
    "atp": "atp-jsonld.schema.json",
    "acp": "acp-jsonld.schema.json",
    "entity": "entity-jsonld.schema.json",
    "capability": "capability-jsonld.schema.json",
    "dictionary": "dictionary-jsonld.schema.json",
    "r7-action": "r7-action-jsonld.schema.json",
    # Non-JSON-LD schemas
    "lct-raw": "lct.schema.json",
    "t3v3-raw": "t3v3.schema.json",
    "trust-query": "trust-query.schema.json",
}


def _find_schema_dir_package() -> Optional[Path]:
    """Locate schemas bundled as package data via ``importlib.resources``.

    Works for wheel installs, sdist installs, and editable installs where
    ``web4/schemas/`` is a proper sub-package.
    Returns *None* if the package data cannot be found.
    """
    try:
        # Python 3.9+ API
        ref = importlib.resources.files("web4.schemas")
        # Resolve to a concrete filesystem path
        schema_path = Path(str(ref))
        if schema_path.is_dir() and (schema_path / "lct-jsonld.schema.json").exists():
            return schema_path
    except (ModuleNotFoundError, TypeError, FileNotFoundError):
        pass
    return None


def _find_schema_dir_repo() -> Optional[Path]:
    """Locate ``web4-standard/schemas/`` by walking up the repository tree.

    Fallback for editable installs and direct repo checkouts where schemas
    may live in the standard's ``schemas/`` directory rather than inside
    the package.  Returns *None* if the directory cannot be found.
    """
    current = Path(__file__).resolve().parent  # web4/
    for _ in range(6):  # max 6 levels up
        candidate = current / "schemas"
        if candidate.is_dir() and (candidate / "lct-jsonld.schema.json").exists():
            return candidate
        sibling = current / "web4-standard" / "schemas"
        if sibling.is_dir() and (sibling / "lct-jsonld.schema.json").exists():
            return sibling
        current = current.parent
    return None


def get_schema_dir() -> Path:
    """Return the resolved path to the schema directory.

    Checks (in order):
    1. ``WEB4_SCHEMA_DIR`` environment variable (explicit override)
    2. ``importlib.resources`` — package-bundled schemas (wheel/pip installs)
    3. Repository-relative filesystem walk (editable installs, repo checkouts)

    Raises:
        SchemaNotFound: If the schema directory cannot be located.
    """
    import os

    env_dir = os.environ.get("WEB4_SCHEMA_DIR")
    if env_dir:
        p = Path(env_dir)
        if p.is_dir():
            return p
        raise SchemaNotFound(
            f"WEB4_SCHEMA_DIR={env_dir!r} does not exist or is not a directory"
        )

    # Try package-bundled schemas first (works in wheel installs)
    found = _find_schema_dir_package()
    if found is not None:
        return found

    # Fallback: walk up repo tree (editable installs, repo checkouts)
    found = _find_schema_dir_repo()
    if found is not None:
        return found

    raise SchemaNotFound(
        "Cannot locate Web4 JSON Schemas. "
        "Install the web4 package (pip install web4) or "
        "set WEB4_SCHEMA_DIR to the schema directory path."
    )


# ── Exceptions ──────────────────────────────────────────────────


class SchemaValidationUnavailable(ImportError):
    """Raised when ``jsonschema`` is not installed."""

    def __init__(self) -> None:
        super().__init__(
            "Schema validation requires the 'jsonschema' package. "
            "Install it with: pip install 'web4[dev]'  or  pip install jsonschema"
        )


class SchemaNotFound(FileNotFoundError):
    """Raised when a schema file or directory cannot be found."""


class ValidationError(Exception):
    """Raised when validation fails and ``raise_on_error=True``."""

    def __init__(self, result: "ValidationResult") -> None:
        self.result = result
        super().__init__(f"{len(result.errors)} validation error(s)")


# ── Result type ─────────────────────────────────────────────────


@dataclass
class ValidationResult:
    """Result of validating a document against a JSON Schema.

    Attributes:
        valid: Whether the document passed validation.
        schema_name: The schema name used for validation.
        errors: List of human-readable error descriptions (empty if valid).
    """

    valid: bool
    schema_name: str
    errors: List[str] = field(default_factory=list)

    def __bool__(self) -> bool:
        return self.valid


# ── Schema cache ────────────────────────────────────────────────

_schema_cache: Dict[str, Dict[str, Any]] = {}


def _load_schema(name: str, schema_dir: Path) -> Dict[str, Any]:
    """Load and cache a schema by name."""
    if name in _schema_cache:
        return _schema_cache[name]

    filename = _SCHEMA_FILES.get(name)
    if filename is None:
        raise SchemaNotFound(
            f"Unknown schema {name!r}. Available: {', '.join(sorted(_SCHEMA_FILES))}"
        )

    path = schema_dir / filename
    if not path.exists():
        raise SchemaNotFound(f"Schema file not found: {path}")

    with open(path) as f:
        schema: Dict[str, Any] = json.load(f)

    _schema_cache[name] = schema
    return schema


# ── Public API ──────────────────────────────────────────────────


def list_schemas() -> List[str]:
    """Return sorted list of available schema names.

    Returns:
        List of schema name strings that can be passed to :func:`validate`
        or :func:`get_schema`.
    """
    return sorted(_SCHEMA_FILES.keys())


def get_schema(name: str, *, schema_dir: Optional[Path] = None) -> Dict[str, Any]:
    """Load and return a JSON Schema as a dictionary.

    Args:
        name: Schema name (e.g. ``"lct"``, ``"attestation-envelope"``).
        schema_dir: Override schema directory. If *None*, auto-detected.

    Returns:
        The parsed JSON Schema dictionary.

    Raises:
        SchemaNotFound: If the schema name is unknown or file is missing.
    """
    if schema_dir is None:
        schema_dir = get_schema_dir()
    return _load_schema(name, schema_dir)


def validate(
    document: Dict[str, Any],
    schema_name: str,
    *,
    schema_dir: Optional[Path] = None,
    raise_on_error: bool = False,
) -> ValidationResult:
    """Validate a JSON-LD document against a Web4 JSON Schema.

    Args:
        document: The JSON-LD document (typically from ``to_jsonld()``).
        schema_name: Schema to validate against (e.g. ``"lct"``).
        schema_dir: Override schema directory. If *None*, auto-detected.
        raise_on_error: If *True*, raise :class:`ValidationError` on failure.

    Returns:
        A :class:`ValidationResult` with ``valid``, ``schema_name``, and
        ``errors`` attributes.

    Raises:
        SchemaValidationUnavailable: If ``jsonschema`` is not installed.
        SchemaNotFound: If the schema name is unknown.
        ValidationError: If ``raise_on_error=True`` and validation fails.
    """
    try:
        from jsonschema import Draft202012Validator  # type: ignore[import-untyped]
    except ImportError:
        raise SchemaValidationUnavailable()

    schema = get_schema(schema_name, schema_dir=schema_dir)
    validator = Draft202012Validator(schema)
    raw_errors = list(validator.iter_errors(document))

    if not raw_errors:
        return ValidationResult(valid=True, schema_name=schema_name)

    error_messages = []
    for err in raw_errors:
        path = ".".join(str(p) for p in err.absolute_path) or "(root)"
        error_messages.append(f"{path}: {err.message}")

    result = ValidationResult(
        valid=False,
        schema_name=schema_name,
        errors=error_messages,
    )

    if raise_on_error:
        raise ValidationError(result)

    return result
