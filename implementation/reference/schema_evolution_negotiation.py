#!/usr/bin/env python3
"""
Schema Evolution & Version Negotiation — Session 20, Track 2

How Web4 handles schema changes across heterogeneous deployments:
- Schema versioning with semantic version tracking
- Forward/backward compatibility classification
- Automatic migration engine (up/down migrations)
- Field rename/add/remove/type-change detection
- Version negotiation between peers
- Graceful degradation for unknown fields
- Federation consensus on schema versions
- Breaking change detection and alerts
- Migration rollback with safety checks
- Schema diff and merge operations
- Performance at scale

Reference: LCT_UNIFIED_PERMISSION_STANDARD.md, wire protocol versions
"""

from __future__ import annotations
import hashlib
import json
import copy
import math
import time
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Set, Tuple


# ─── Constants ────────────────────────────────────────────────────────────────

class FieldType(Enum):
    STRING = "string"
    INT = "int"
    FLOAT = "float"
    BOOL = "bool"
    BYTES = "bytes"
    LIST = "list"
    MAP = "map"
    ENUM = "enum"


class CompatLevel(Enum):
    FULL = "full"                  # Both directions work
    BACKWARD = "backward"          # New can read old
    FORWARD = "forward"            # Old can read new
    BREAKING = "breaking"          # Neither direction works
    NONE = "none"                  # No data to compare


class ChangeType(Enum):
    FIELD_ADDED = "field_added"
    FIELD_REMOVED = "field_removed"
    FIELD_RENAMED = "field_renamed"
    TYPE_CHANGED = "type_changed"
    DEFAULT_CHANGED = "default_changed"
    REQUIRED_CHANGED = "required_changed"
    CONSTRAINT_CHANGED = "constraint_changed"


# ─── Data Structures ─────────────────────────────────────────────────────────

@dataclass
class SemVer:
    """Semantic version."""
    major: int
    minor: int
    patch: int

    def __str__(self):
        return f"{self.major}.{self.minor}.{self.patch}"

    def __lt__(self, other):
        return (self.major, self.minor, self.patch) < (other.major, other.minor, other.patch)

    def __eq__(self, other):
        return (self.major, self.minor, self.patch) == (other.major, other.minor, other.patch)

    def __le__(self, other):
        return self == other or self < other

    def __hash__(self):
        return hash((self.major, self.minor, self.patch))

    def compatible_with(self, other: "SemVer") -> bool:
        """Same major version = API compatible."""
        return self.major == other.major

    @staticmethod
    def parse(s: str) -> "SemVer":
        parts = s.split(".")
        return SemVer(int(parts[0]), int(parts[1]), int(parts[2]))


@dataclass
class FieldDef:
    """Schema field definition."""
    name: str
    field_type: FieldType
    required: bool = True
    default: Any = None
    constraints: Dict[str, Any] = field(default_factory=dict)
    description: str = ""


@dataclass
class SchemaVersion:
    """A versioned schema definition."""
    name: str
    version: SemVer
    fields: Dict[str, FieldDef]
    metadata: Dict[str, str] = field(default_factory=dict)

    def field_names(self) -> Set[str]:
        return set(self.fields.keys())

    def required_fields(self) -> Set[str]:
        return {n for n, f in self.fields.items() if f.required}

    def fingerprint(self) -> str:
        """Content-based schema fingerprint."""
        parts = sorted(f"{n}:{f.field_type.value}:{f.required}" for n, f in self.fields.items())
        return hashlib.sha256("|".join(parts).encode()).hexdigest()[:16]


@dataclass
class SchemaChange:
    """A detected change between schema versions."""
    change_type: ChangeType
    field_name: str
    old_value: Any = None
    new_value: Any = None
    breaking: bool = False


@dataclass
class Migration:
    """A migration between two schema versions."""
    from_version: SemVer
    to_version: SemVer
    up_transforms: List[Callable] = field(default_factory=list)
    down_transforms: List[Callable] = field(default_factory=list)
    description: str = ""


# ─── S1: Schema Versioning ──────────────────────────────────────────────────

class SchemaRegistry:
    """Registry of schema versions with evolution tracking."""

    def __init__(self):
        self.schemas: Dict[str, Dict[str, SchemaVersion]] = {}  # name → {version_str → schema}
        self.migrations: Dict[str, List[Migration]] = {}  # name → migrations

    def register(self, schema: SchemaVersion):
        """Register a schema version."""
        name = schema.name
        if name not in self.schemas:
            self.schemas[name] = {}
            self.migrations[name] = []
        self.schemas[name][str(schema.version)] = schema

    def get(self, name: str, version: str) -> Optional[SchemaVersion]:
        return self.schemas.get(name, {}).get(version)

    def latest(self, name: str) -> Optional[SchemaVersion]:
        """Get the latest version of a schema."""
        versions = self.schemas.get(name, {})
        if not versions:
            return None
        latest_ver = max(versions.keys(), key=lambda v: SemVer.parse(v))
        return versions[latest_ver]

    def versions(self, name: str) -> List[SemVer]:
        """Get all versions of a schema, sorted."""
        versions = self.schemas.get(name, {})
        return sorted(SemVer.parse(v) for v in versions.keys())

    def add_migration(self, name: str, migration: Migration):
        if name not in self.migrations:
            self.migrations[name] = []
        self.migrations[name].append(migration)


# ─── S2: Compatibility Classification ───────────────────────────────────────

def classify_compatibility(old: SchemaVersion, new: SchemaVersion) -> CompatLevel:
    """
    Classify compatibility between two schema versions.

    FULL: All old fields exist in new, no type changes, new fields have defaults.
    BACKWARD: New can read old (new fields have defaults, old required fields present).
    FORWARD: Old can read new (no required fields removed).
    BREAKING: Required field removed or type changed.
    """
    old_fields = old.field_names()
    new_fields = new.field_names()

    added = new_fields - old_fields
    removed = old_fields - new_fields

    # Check for type changes in common fields
    type_changes = False
    for fname in old_fields & new_fields:
        if old.fields[fname].field_type != new.fields[fname].field_type:
            type_changes = True
            break

    # Required field removed → breaking
    for fname in removed:
        if old.fields[fname].required:
            return CompatLevel.BREAKING

    # Type change → breaking
    if type_changes:
        return CompatLevel.BREAKING

    # New required field without default → breaking
    for fname in added:
        f = new.fields[fname]
        if f.required and f.default is None:
            return CompatLevel.BREAKING

    # All added fields have defaults → backward compatible
    # No fields removed → forward compatible
    if not removed:
        return CompatLevel.FULL  # Both directions

    # Fields removed but none were required → backward only
    return CompatLevel.BACKWARD


# ─── S3: Change Detection ───────────────────────────────────────────────────

def detect_changes(old: SchemaVersion, new: SchemaVersion) -> List[SchemaChange]:
    """Detect all changes between two schema versions."""
    changes = []
    old_fields = old.field_names()
    new_fields = new.field_names()

    # Added fields
    for fname in new_fields - old_fields:
        f = new.fields[fname]
        changes.append(SchemaChange(
            change_type=ChangeType.FIELD_ADDED,
            field_name=fname,
            new_value=f.field_type.value,
            breaking=f.required and f.default is None,
        ))

    # Removed fields
    for fname in old_fields - new_fields:
        f = old.fields[fname]
        changes.append(SchemaChange(
            change_type=ChangeType.FIELD_REMOVED,
            field_name=fname,
            old_value=f.field_type.value,
            breaking=f.required,
        ))

    # Modified fields
    for fname in old_fields & new_fields:
        of = old.fields[fname]
        nf = new.fields[fname]

        if of.field_type != nf.field_type:
            changes.append(SchemaChange(
                change_type=ChangeType.TYPE_CHANGED,
                field_name=fname,
                old_value=of.field_type.value,
                new_value=nf.field_type.value,
                breaking=True,
            ))

        if of.default != nf.default:
            changes.append(SchemaChange(
                change_type=ChangeType.DEFAULT_CHANGED,
                field_name=fname,
                old_value=of.default,
                new_value=nf.default,
                breaking=False,
            ))

        if of.required != nf.required:
            changes.append(SchemaChange(
                change_type=ChangeType.REQUIRED_CHANGED,
                field_name=fname,
                old_value=of.required,
                new_value=nf.required,
                breaking=not of.required and nf.required and nf.default is None,
            ))

    return changes


def has_breaking_changes(changes: List[SchemaChange]) -> bool:
    return any(c.breaking for c in changes)


# ─── S4: Migration Engine ───────────────────────────────────────────────────

class MigrationEngine:
    """Execute schema migrations on data documents."""

    def __init__(self, registry: SchemaRegistry):
        self.registry = registry

    def migrate(
        self,
        data: Dict[str, Any],
        schema_name: str,
        from_version: SemVer,
        to_version: SemVer,
    ) -> Tuple[Dict[str, Any], List[str]]:
        """
        Migrate data from one version to another.
        Returns (migrated_data, list_of_applied_migrations).
        """
        result = copy.deepcopy(data)
        applied = []

        if from_version == to_version:
            return result, []

        # Find migration path
        migrations = self.registry.migrations.get(schema_name, [])
        forward = from_version < to_version

        if forward:
            # Apply up transforms in order
            path = self._find_path(migrations, from_version, to_version, "up")
        else:
            # Apply down transforms: start at from_version (high), step down to to_version (low)
            path = self._find_path(migrations, from_version, to_version, "down")

        for migration, direction in path:
            transforms = migration.up_transforms if direction == "up" else migration.down_transforms
            for transform in transforms:
                result = transform(result)
            applied.append(f"{migration.from_version}→{migration.to_version} ({direction})")

        # Auto-migration: fill defaults for new fields
        target_schema = self.registry.get(schema_name, str(to_version))
        if target_schema:
            for fname, fdef in target_schema.fields.items():
                if fname not in result and fdef.default is not None:
                    result[fname] = fdef.default

        return result, applied

    def _find_path(
        self,
        migrations: List[Migration],
        start: SemVer,
        end: SemVer,
        direction: str,
    ) -> List[Tuple[Migration, str]]:
        """Find migration path from start to end."""
        path = []
        current = start
        visited = set()

        while current != end:
            found = False
            for m in migrations:
                key = (str(m.from_version), str(m.to_version))
                if key in visited:
                    continue
                if direction == "up" and m.from_version == current and m.to_version <= end:
                    path.append((m, "up"))
                    visited.add(key)
                    current = m.to_version
                    found = True
                    break
                elif direction == "down" and m.to_version == current and m.from_version >= end:
                    path.append((m, "down"))
                    visited.add(key)
                    current = m.from_version
                    found = True
                    break
            if not found:
                break

        return path

    def can_migrate(self, schema_name: str, from_v: SemVer, to_v: SemVer) -> bool:
        """Check if a migration path exists."""
        migrations = self.registry.migrations.get(schema_name, [])
        forward = from_v < to_v
        if forward:
            path = self._find_path(migrations, from_v, to_v, "up")
        else:
            path = self._find_path(migrations, to_v, from_v, "down")
        # Check if we reached the target
        current = from_v if forward else to_v
        for m, d in path:
            current = m.to_version if d == "up" else m.from_version
        return current == (to_v if forward else from_v)


# ─── S5: Version Negotiation ────────────────────────────────────────────────

@dataclass
class VersionCapability:
    """A peer's schema version capabilities."""
    peer_id: str
    supported_versions: List[SemVer]
    preferred_version: SemVer


def negotiate_version(
    local: VersionCapability,
    remote: VersionCapability,
) -> Optional[SemVer]:
    """
    Negotiate the best common schema version.
    Prefers highest mutually supported version.
    """
    local_set = set(str(v) for v in local.supported_versions)
    remote_set = set(str(v) for v in remote.supported_versions)
    common = local_set & remote_set

    if not common:
        return None

    # Highest common version
    return max(SemVer.parse(v) for v in common)


def negotiate_with_fallback(
    local: VersionCapability,
    remote: VersionCapability,
    engine: MigrationEngine,
    schema_name: str,
) -> Tuple[Optional[SemVer], str]:
    """
    Negotiate version with migration fallback.
    Returns (negotiated_version, strategy).
    """
    # Try direct negotiation first
    direct = negotiate_version(local, remote)
    if direct:
        return direct, "direct"

    # Try migration: can either side migrate to the other's version?
    for local_v in sorted(local.supported_versions, reverse=True):
        for remote_v in sorted(remote.supported_versions, reverse=True):
            if engine.can_migrate(schema_name, local_v, remote_v):
                return remote_v, "local_migrates"
            if engine.can_migrate(schema_name, remote_v, local_v):
                return local_v, "remote_migrates"

    return None, "incompatible"


# ─── S6: Graceful Degradation ───────────────────────────────────────────────

def strip_unknown_fields(data: Dict[str, Any], schema: SchemaVersion) -> Dict[str, Any]:
    """Remove fields not in schema (forward compatibility)."""
    return {k: v for k, v in data.items() if k in schema.fields}


def fill_missing_defaults(data: Dict[str, Any], schema: SchemaVersion) -> Dict[str, Any]:
    """Fill missing fields with defaults (backward compatibility)."""
    result = dict(data)
    for fname, fdef in schema.fields.items():
        if fname not in result:
            if fdef.default is not None:
                result[fname] = fdef.default
            elif not fdef.required:
                result[fname] = None
    return result


def validate_document(data: Dict[str, Any], schema: SchemaVersion) -> List[str]:
    """Validate a document against a schema. Returns list of errors."""
    errors = []
    for fname, fdef in schema.fields.items():
        if fname not in data:
            if fdef.required:
                errors.append(f"Missing required field: {fname}")
            continue
        # Type check (simplified)
        value = data[fname]
        expected = fdef.field_type
        if expected == FieldType.STRING and not isinstance(value, str):
            errors.append(f"Field {fname}: expected string, got {type(value).__name__}")
        elif expected == FieldType.INT and not isinstance(value, int):
            errors.append(f"Field {fname}: expected int, got {type(value).__name__}")
        elif expected == FieldType.FLOAT and not isinstance(value, (int, float)):
            errors.append(f"Field {fname}: expected float, got {type(value).__name__}")
        elif expected == FieldType.BOOL and not isinstance(value, bool):
            errors.append(f"Field {fname}: expected bool, got {type(value).__name__}")

    # Extra fields (warn but don't error)
    for key in data:
        if key not in schema.fields:
            errors.append(f"Unknown field: {key} (ignored)")

    return errors


# ─── S7: Federation Schema Consensus ────────────────────────────────────────

@dataclass
class SchemaVote:
    """A federation member's vote on schema version."""
    voter_id: str
    schema_name: str
    version: SemVer
    timestamp: float


class FederationSchemaConsensus:
    """Achieve consensus on schema versions across federation."""

    def __init__(self, quorum_fraction: float = 0.67):
        self.votes: Dict[str, List[SchemaVote]] = {}  # schema_name → votes
        self.quorum_fraction = quorum_fraction
        self.members: Set[str] = set()

    def add_member(self, member_id: str):
        self.members.add(member_id)

    def vote(self, schema_vote: SchemaVote):
        name = schema_vote.schema_name
        if name not in self.votes:
            self.votes[name] = []
        # Replace existing vote from same voter
        self.votes[name] = [
            v for v in self.votes[name] if v.voter_id != schema_vote.voter_id
        ]
        self.votes[name].append(schema_vote)

    def consensus_version(self, schema_name: str) -> Optional[SemVer]:
        """
        Return the version that has quorum, or None.
        """
        votes = self.votes.get(schema_name, [])
        if not votes or not self.members:
            return None

        quorum_needed = math.ceil(len(self.members) * self.quorum_fraction)
        version_counts: Dict[str, int] = {}
        for v in votes:
            key = str(v.version)
            version_counts[key] = version_counts.get(key, 0) + 1

        for ver_str, count in version_counts.items():
            if count >= quorum_needed:
                return SemVer.parse(ver_str)

        return None

    def adoption_rate(self, schema_name: str, version: SemVer) -> float:
        """Fraction of members using a specific version."""
        votes = self.votes.get(schema_name, [])
        if not self.members:
            return 0.0
        matching = sum(1 for v in votes if v.version == version)
        return matching / len(self.members)


# ─── S8: Breaking Change Detection ──────────────────────────────────────────

@dataclass
class BreakingChangeAlert:
    """Alert for a detected breaking change."""
    schema_name: str
    from_version: SemVer
    to_version: SemVer
    changes: List[SchemaChange]
    severity: str  # "warning", "error", "critical"
    message: str


def analyze_breaking_changes(
    registry: SchemaRegistry,
    schema_name: str,
) -> List[BreakingChangeAlert]:
    """Analyze all version transitions for breaking changes."""
    alerts = []
    versions = registry.versions(schema_name)

    for i in range(len(versions) - 1):
        old = registry.get(schema_name, str(versions[i]))
        new = registry.get(schema_name, str(versions[i + 1]))
        if not old or not new:
            continue

        changes = detect_changes(old, new)
        breaking = [c for c in changes if c.breaking]

        if breaking:
            severity = "critical" if any(
                c.change_type == ChangeType.TYPE_CHANGED for c in breaking
            ) else "error"

            alerts.append(BreakingChangeAlert(
                schema_name=schema_name,
                from_version=versions[i],
                to_version=versions[i + 1],
                changes=breaking,
                severity=severity,
                message=f"{len(breaking)} breaking changes in {versions[i]}→{versions[i+1]}",
            ))

    return alerts


# ─── S9: Schema Diff & Merge ────────────────────────────────────────────────

@dataclass
class SchemaDiff:
    """Diff between two schema versions."""
    added: List[str]
    removed: List[str]
    modified: List[Tuple[str, str]]  # (field_name, description)
    compat: CompatLevel


def diff_schemas(old: SchemaVersion, new: SchemaVersion) -> SchemaDiff:
    """Compute diff between two schemas."""
    old_names = old.field_names()
    new_names = new.field_names()

    added = sorted(new_names - old_names)
    removed = sorted(old_names - new_names)

    modified = []
    for fname in sorted(old_names & new_names):
        of = old.fields[fname]
        nf = new.fields[fname]
        diffs = []
        if of.field_type != nf.field_type:
            diffs.append(f"type: {of.field_type.value}→{nf.field_type.value}")
        if of.required != nf.required:
            diffs.append(f"required: {of.required}→{nf.required}")
        if of.default != nf.default:
            diffs.append(f"default: {of.default}→{nf.default}")
        if diffs:
            modified.append((fname, "; ".join(diffs)))

    compat = classify_compatibility(old, new)
    return SchemaDiff(added=added, removed=removed, modified=modified, compat=compat)


def merge_schemas(base: SchemaVersion, a: SchemaVersion, b: SchemaVersion) -> Tuple[SchemaVersion, List[str]]:
    """
    Three-way merge of schema changes.
    Returns (merged_schema, conflict_messages).
    """
    conflicts = []
    merged_fields = dict(base.fields)

    # Changes from a
    a_added = a.field_names() - base.field_names()
    a_removed = base.field_names() - a.field_names()

    # Changes from b
    b_added = b.field_names() - base.field_names()
    b_removed = base.field_names() - b.field_names()

    # Apply additions (both sides)
    for fname in a_added:
        merged_fields[fname] = a.fields[fname]
    for fname in b_added:
        if fname in a_added:
            # Both added same field — conflict if different
            if a.fields[fname].field_type != b.fields[fname].field_type:
                conflicts.append(f"Conflict: {fname} added by both with different types")
            # Use a's version by default
        else:
            merged_fields[fname] = b.fields[fname]

    # Apply removals
    for fname in a_removed | b_removed:
        if fname in a_removed and fname in b_removed:
            merged_fields.pop(fname, None)
        elif fname in a_removed and fname not in b_added:
            merged_fields.pop(fname, None)
        elif fname in b_removed and fname not in a_added:
            merged_fields.pop(fname, None)
        else:
            conflicts.append(f"Conflict: {fname} removed by one side, kept by other")

    # Check for type conflicts on common fields
    for fname in (a.field_names() & b.field_names()) - a_added - b_added:
        if fname in a.fields and fname in b.fields:
            if a.fields[fname].field_type != b.fields[fname].field_type:
                conflicts.append(f"Conflict: {fname} has different types in branches")

    merged = SchemaVersion(
        name=base.name,
        version=SemVer(base.version.major, base.version.minor + 1, 0),
        fields=merged_fields,
    )
    return merged, conflicts


# ─── S10: Migration Rollback ────────────────────────────────────────────────

@dataclass
class MigrationCheckpoint:
    """Snapshot before migration for rollback."""
    data: Dict[str, Any]
    version: SemVer
    timestamp: float
    checksum: str


class SafeMigration:
    """Migration with checkpoint and rollback support."""

    def __init__(self, engine: MigrationEngine):
        self.engine = engine
        self.checkpoints: List[MigrationCheckpoint] = []

    def checkpoint(self, data: Dict[str, Any], version: SemVer):
        """Save checkpoint before migration."""
        checksum = hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()[:16]
        self.checkpoints.append(MigrationCheckpoint(
            data=copy.deepcopy(data),
            version=version,
            timestamp=time.time(),
            checksum=checksum,
        ))

    def migrate_safe(
        self,
        data: Dict[str, Any],
        schema_name: str,
        from_v: SemVer,
        to_v: SemVer,
    ) -> Tuple[Dict[str, Any], bool, List[str]]:
        """
        Migrate with automatic checkpoint.
        Returns (result, success, messages).
        """
        self.checkpoint(data, from_v)

        try:
            result, applied = self.engine.migrate(data, schema_name, from_v, to_v)

            # Verify result against target schema
            target = self.engine.registry.get(schema_name, str(to_v))
            if target:
                errors = validate_document(result, target)
                # Only count missing required fields and type mismatches as failures
                real_errors = [e for e in errors if not e.startswith("Unknown field")]
                if real_errors:
                    return data, False, ["Validation failed: " + "; ".join(real_errors)]

            return result, True, applied

        except Exception as e:
            return data, False, [f"Migration error: {str(e)}"]

    def rollback(self) -> Optional[Tuple[Dict[str, Any], SemVer]]:
        """Rollback to last checkpoint."""
        if not self.checkpoints:
            return None
        cp = self.checkpoints.pop()
        return cp.data, cp.version

    def rollback_to(self, version: SemVer) -> Optional[Dict[str, Any]]:
        """Rollback to a specific version checkpoint."""
        for i in range(len(self.checkpoints) - 1, -1, -1):
            if self.checkpoints[i].version == version:
                cp = self.checkpoints[i]
                self.checkpoints = self.checkpoints[:i]
                return cp.data
        return None


# ─── S11: Performance ───────────────────────────────────────────────────────

# Included in checks


# ══════════════════════════════════════════════════════════════════════════════
#  CHECKS
# ══════════════════════════════════════════════════════════════════════════════

def run_checks():
    checks = []

    # Build test schemas
    v1_fields = {
        "entity_id": FieldDef("entity_id", FieldType.STRING, required=True),
        "trust_score": FieldDef("trust_score", FieldType.FLOAT, required=True),
        "name": FieldDef("name", FieldType.STRING, required=False, default="unknown"),
    }
    v1 = SchemaVersion("entity", SemVer(1, 0, 0), v1_fields)

    v2_fields = {
        "entity_id": FieldDef("entity_id", FieldType.STRING, required=True),
        "trust_score": FieldDef("trust_score", FieldType.FLOAT, required=True),
        "name": FieldDef("name", FieldType.STRING, required=False, default="unknown"),
        "federation_id": FieldDef("federation_id", FieldType.STRING, required=False, default="default"),
    }
    v2 = SchemaVersion("entity", SemVer(1, 1, 0), v2_fields)

    v3_fields = {
        "entity_id": FieldDef("entity_id", FieldType.STRING, required=True),
        "trust_score": FieldDef("trust_score", FieldType.FLOAT, required=True),
        "federation_id": FieldDef("federation_id", FieldType.STRING, required=True),
        "role": FieldDef("role", FieldType.STRING, required=False, default="member"),
    }
    v3 = SchemaVersion("entity", SemVer(2, 0, 0), v3_fields)

    # ── S1: Schema Versioning ────────────────────────────────────────────

    registry = SchemaRegistry()
    registry.register(v1)
    registry.register(v2)
    registry.register(v3)

    # S1.1: Get specific version
    checks.append(("s1_get_version", registry.get("entity", "1.0.0") is not None))

    # S1.2: Latest version
    latest = registry.latest("entity")
    checks.append(("s1_latest", latest is not None and latest.version == SemVer(2, 0, 0)))

    # S1.3: All versions sorted
    versions = registry.versions("entity")
    checks.append(("s1_versions_sorted", versions == [SemVer(1, 0, 0), SemVer(1, 1, 0), SemVer(2, 0, 0)]))

    # S1.4: Missing schema returns None
    checks.append(("s1_missing_none", registry.get("nonexistent", "1.0.0") is None))

    # S1.5: Fingerprint is deterministic
    fp1 = v1.fingerprint()
    fp2 = v1.fingerprint()
    checks.append(("s1_fingerprint_deterministic", fp1 == fp2))

    # S1.6: Different schemas have different fingerprints
    checks.append(("s1_fingerprint_different", v1.fingerprint() != v2.fingerprint()))

    # S1.7: SemVer comparison
    checks.append(("s1_semver_order", SemVer(1, 0, 0) < SemVer(1, 1, 0) < SemVer(2, 0, 0)))

    # S1.8: SemVer compatibility
    checks.append(("s1_semver_compat", SemVer(1, 0, 0).compatible_with(SemVer(1, 1, 0))))
    checks.append(("s1_semver_incompat", not SemVer(1, 0, 0).compatible_with(SemVer(2, 0, 0))))

    # ── S2: Compatibility Classification ─────────────────────────────────

    # S2.1: v1→v2 is FULL (added optional field with default)
    compat = classify_compatibility(v1, v2)
    checks.append(("s2_v1_v2_full", compat == CompatLevel.FULL))

    # S2.2: v1→v3 is BREAKING (removed "name", made federation_id required)
    compat = classify_compatibility(v1, v3)
    checks.append(("s2_v1_v3_breaking", compat == CompatLevel.BREAKING))

    # S2.3: Identical schemas are FULL
    compat = classify_compatibility(v1, v1)
    checks.append(("s2_identical_full", compat == CompatLevel.FULL))

    # S2.4: Adding required field without default is BREAKING
    v_breaking = SchemaVersion("test", SemVer(1, 1, 0), {
        **v1_fields,
        "new_req": FieldDef("new_req", FieldType.STRING, required=True),
    })
    compat = classify_compatibility(v1, v_breaking)
    checks.append(("s2_required_no_default_breaking", compat == CompatLevel.BREAKING))

    # S2.5: Removing optional field is BACKWARD
    v_removed = SchemaVersion("test", SemVer(1, 1, 0), {
        "entity_id": v1_fields["entity_id"],
        "trust_score": v1_fields["trust_score"],
    })
    compat = classify_compatibility(v1, v_removed)
    checks.append(("s2_remove_optional_backward", compat == CompatLevel.BACKWARD))

    # ── S3: Change Detection ─────────────────────────────────────────────

    # S3.1: Detect field addition
    changes = detect_changes(v1, v2)
    added = [c for c in changes if c.change_type == ChangeType.FIELD_ADDED]
    checks.append(("s3_detect_added", len(added) == 1 and added[0].field_name == "federation_id"))

    # S3.2: Detect field removal
    changes = detect_changes(v2, v3)
    removed = [c for c in changes if c.change_type == ChangeType.FIELD_REMOVED]
    checks.append(("s3_detect_removed", any(c.field_name == "name" for c in removed)))

    # S3.3: Detect type change
    v_type = SchemaVersion("test", SemVer(1, 1, 0), {
        "entity_id": FieldDef("entity_id", FieldType.INT, required=True),  # STRING→INT
        "trust_score": v1_fields["trust_score"],
        "name": v1_fields["name"],
    })
    changes = detect_changes(v1, v_type)
    type_changes = [c for c in changes if c.change_type == ChangeType.TYPE_CHANGED]
    checks.append(("s3_detect_type_change", len(type_changes) == 1))

    # S3.4: Breaking changes detected
    checks.append(("s3_breaking_flag", has_breaking_changes(detect_changes(v1, v3))))
    checks.append(("s3_no_breaking", not has_breaking_changes(detect_changes(v1, v2))))

    # S3.5: Default change detected
    v_default = SchemaVersion("test", SemVer(1, 0, 1), {
        "entity_id": v1_fields["entity_id"],
        "trust_score": v1_fields["trust_score"],
        "name": FieldDef("name", FieldType.STRING, required=False, default="renamed"),
    })
    changes = detect_changes(v1, v_default)
    default_changes = [c for c in changes if c.change_type == ChangeType.DEFAULT_CHANGED]
    checks.append(("s3_detect_default_change", len(default_changes) == 1))

    # ── S4: Migration Engine ─────────────────────────────────────────────

    # Set up migrations
    def add_federation_id(data):
        data["federation_id"] = data.get("federation_id", "default")
        return data

    def remove_federation_id(data):
        data.pop("federation_id", None)
        return data

    m1_2 = Migration(
        SemVer(1, 0, 0), SemVer(1, 1, 0),
        up_transforms=[add_federation_id],
        down_transforms=[remove_federation_id],
    )
    registry.add_migration("entity", m1_2)

    engine = MigrationEngine(registry)

    # S4.1: Migrate v1 → v2
    data_v1 = {"entity_id": "alice", "trust_score": 0.8, "name": "Alice"}
    result, applied = engine.migrate(data_v1, "entity", SemVer(1, 0, 0), SemVer(1, 1, 0))
    checks.append(("s4_migrate_up", result.get("federation_id") == "default"))

    # S4.2: Migrate v2 → v1 (downgrade)
    data_v2 = {"entity_id": "bob", "trust_score": 0.7, "name": "Bob", "federation_id": "fed1"}
    result, applied = engine.migrate(data_v2, "entity", SemVer(1, 1, 0), SemVer(1, 0, 0))
    checks.append(("s4_migrate_down", "federation_id" not in result))

    # S4.3: No-op migration
    result, applied = engine.migrate(data_v1, "entity", SemVer(1, 0, 0), SemVer(1, 0, 0))
    checks.append(("s4_noop", len(applied) == 0 and result == data_v1))

    # S4.4: Can migrate check
    checks.append(("s4_can_migrate_yes", engine.can_migrate("entity", SemVer(1, 0, 0), SemVer(1, 1, 0))))

    # S4.5: Original data unchanged
    checks.append(("s4_immutable_original", "federation_id" not in data_v1))

    # ── S5: Version Negotiation ──────────────────────────────────────────

    local = VersionCapability(
        "local", [SemVer(1, 0, 0), SemVer(1, 1, 0)], SemVer(1, 1, 0),
    )
    remote = VersionCapability(
        "remote", [SemVer(1, 0, 0), SemVer(1, 1, 0), SemVer(2, 0, 0)], SemVer(2, 0, 0),
    )

    # S5.1: Negotiate highest common
    negotiated = negotiate_version(local, remote)
    checks.append(("s5_highest_common", negotiated == SemVer(1, 1, 0)))

    # S5.2: No common versions
    incompatible = VersionCapability("other", [SemVer(3, 0, 0)], SemVer(3, 0, 0))
    checks.append(("s5_no_common", negotiate_version(local, incompatible) is None))

    # S5.3: Negotiate with fallback
    ver, strategy = negotiate_with_fallback(local, remote, engine, "entity")
    checks.append(("s5_fallback_direct", strategy == "direct"))

    # S5.4: Fallback to migration
    local_v2_only = VersionCapability("l", [SemVer(1, 1, 0)], SemVer(1, 1, 0))
    remote_v1_only = VersionCapability("r", [SemVer(1, 0, 0)], SemVer(1, 0, 0))
    ver, strategy = negotiate_with_fallback(local_v2_only, remote_v1_only, engine, "entity")
    checks.append(("s5_fallback_migrates", strategy in ("local_migrates", "remote_migrates")))

    # ── S6: Graceful Degradation ─────────────────────────────────────────

    # S6.1: Strip unknown fields
    extra_data = {"entity_id": "alice", "trust_score": 0.8, "name": "Alice", "unknown_field": 42}
    stripped = strip_unknown_fields(extra_data, v1)
    checks.append(("s6_strip_unknown", "unknown_field" not in stripped and "entity_id" in stripped))

    # S6.2: Fill missing defaults
    partial = {"entity_id": "bob", "trust_score": 0.7}
    filled = fill_missing_defaults(partial, v1)
    checks.append(("s6_fill_defaults", filled.get("name") == "unknown"))

    # S6.3: Validate valid document
    valid_doc = {"entity_id": "alice", "trust_score": 0.8, "name": "Alice"}
    errors = validate_document(valid_doc, v1)
    checks.append(("s6_valid_no_errors", not any(
        e for e in errors if not e.startswith("Unknown")
    )))

    # S6.4: Validate missing required
    invalid_doc = {"name": "Bob"}
    errors = validate_document(invalid_doc, v1)
    checks.append(("s6_missing_required", any("Missing required" in e for e in errors)))

    # S6.5: Validate type mismatch
    type_error_doc = {"entity_id": 123, "trust_score": 0.8, "name": "Alice"}
    errors = validate_document(type_error_doc, v1)
    checks.append(("s6_type_mismatch", any("expected string" in e for e in errors)))

    # S6.6: Extra fields reported
    errors = validate_document(extra_data, v1)
    checks.append(("s6_extra_reported", any("Unknown field" in e for e in errors)))

    # ── S7: Federation Schema Consensus ──────────────────────────────────

    consensus = FederationSchemaConsensus(quorum_fraction=0.67)
    for i in range(5):
        consensus.add_member(f"node{i}")

    # S7.1: No votes → no consensus
    checks.append(("s7_no_votes", consensus.consensus_version("entity") is None))

    # S7.2: Below quorum → no consensus
    consensus.vote(SchemaVote("node0", "entity", SemVer(1, 0, 0), time.time()))
    consensus.vote(SchemaVote("node1", "entity", SemVer(1, 0, 0), time.time()))
    checks.append(("s7_below_quorum", consensus.consensus_version("entity") is None))

    # S7.3: At quorum → consensus reached
    consensus.vote(SchemaVote("node2", "entity", SemVer(1, 0, 0), time.time()))
    consensus.vote(SchemaVote("node3", "entity", SemVer(1, 0, 0), time.time()))
    checks.append(("s7_at_quorum", consensus.consensus_version("entity") == SemVer(1, 0, 0)))

    # S7.4: Split votes → no consensus
    split_consensus = FederationSchemaConsensus(quorum_fraction=0.67)
    for i in range(4):
        split_consensus.add_member(f"s{i}")
    split_consensus.vote(SchemaVote("s0", "entity", SemVer(1, 0, 0), time.time()))
    split_consensus.vote(SchemaVote("s1", "entity", SemVer(1, 0, 0), time.time()))
    split_consensus.vote(SchemaVote("s2", "entity", SemVer(2, 0, 0), time.time()))
    split_consensus.vote(SchemaVote("s3", "entity", SemVer(2, 0, 0), time.time()))
    checks.append(("s7_split_no_consensus", split_consensus.consensus_version("entity") is None))

    # S7.5: Adoption rate
    rate = consensus.adoption_rate("entity", SemVer(1, 0, 0))
    checks.append(("s7_adoption_rate", abs(rate - 0.8) < 0.01))

    # S7.6: Vote replacement (same voter updates)
    consensus.vote(SchemaVote("node0", "entity", SemVer(2, 0, 0), time.time()))
    rate_v1 = consensus.adoption_rate("entity", SemVer(1, 0, 0))
    checks.append(("s7_vote_replacement", abs(rate_v1 - 0.6) < 0.01))

    # ── S8: Breaking Change Detection ────────────────────────────────────

    # S8.1: Detect breaking changes in registry
    alerts = analyze_breaking_changes(registry, "entity")
    checks.append(("s8_breaking_alerts", len(alerts) > 0))

    # S8.2: v1→v2 not in alerts (non-breaking)
    v1_v2_alerts = [a for a in alerts if a.from_version == SemVer(1, 0, 0) and a.to_version == SemVer(1, 1, 0)]
    checks.append(("s8_v1_v2_no_alert", len(v1_v2_alerts) == 0))

    # S8.3: v2→v3 has alert
    v2_v3_alerts = [a for a in alerts if a.from_version == SemVer(1, 1, 0)]
    checks.append(("s8_v2_v3_alert", len(v2_v3_alerts) > 0))

    # S8.4: Severity classification
    if v2_v3_alerts:
        checks.append(("s8_severity", v2_v3_alerts[0].severity in ("error", "critical")))
    else:
        checks.append(("s8_severity", False))

    # ── S9: Schema Diff & Merge ──────────────────────────────────────────

    # S9.1: Diff v1→v2
    diff = diff_schemas(v1, v2)
    checks.append(("s9_diff_added", "federation_id" in diff.added))
    checks.append(("s9_diff_no_removed", len(diff.removed) == 0))

    # S9.2: Diff compatibility
    checks.append(("s9_diff_compat", diff.compat == CompatLevel.FULL))

    # S9.3: Three-way merge — no conflicts
    branch_a = SchemaVersion("entity", SemVer(1, 1, 0), {
        **v1_fields,
        "new_a": FieldDef("new_a", FieldType.STRING, required=False, default="a"),
    })
    branch_b = SchemaVersion("entity", SemVer(1, 1, 0), {
        **v1_fields,
        "new_b": FieldDef("new_b", FieldType.INT, required=False, default=0),
    })
    merged, conflicts = merge_schemas(v1, branch_a, branch_b)
    checks.append(("s9_merge_no_conflicts", len(conflicts) == 0))
    checks.append(("s9_merge_has_both", "new_a" in merged.fields and "new_b" in merged.fields))

    # S9.4: Merge with conflict
    branch_c = SchemaVersion("entity", SemVer(1, 1, 0), {
        **v1_fields,
        "shared": FieldDef("shared", FieldType.STRING),
    })
    branch_d = SchemaVersion("entity", SemVer(1, 1, 0), {
        **v1_fields,
        "shared": FieldDef("shared", FieldType.INT),
    })
    _, conflicts = merge_schemas(v1, branch_c, branch_d)
    checks.append(("s9_merge_conflict", len(conflicts) > 0))

    # ── S10: Migration Rollback ──────────────────────────────────────────

    safe = SafeMigration(engine)

    # S10.1: Safe migration succeeds
    data = {"entity_id": "test", "trust_score": 0.5, "name": "Test"}
    result, success, msgs = safe.migrate_safe(data, "entity", SemVer(1, 0, 0), SemVer(1, 1, 0))
    checks.append(("s10_safe_success", success and "federation_id" in result))

    # S10.2: Rollback restores data
    rollback = safe.rollback()
    checks.append(("s10_rollback", rollback is not None and rollback[1] == SemVer(1, 0, 0)))

    # S10.3: Rollback data matches original
    checks.append(("s10_rollback_data", rollback is not None and rollback[0] == data))

    # S10.4: No checkpoints → rollback returns None
    checks.append(("s10_empty_rollback", safe.rollback() is None))

    # S10.5: Multiple checkpoints
    safe.checkpoint({"a": 1}, SemVer(1, 0, 0))
    safe.checkpoint({"b": 2}, SemVer(1, 1, 0))
    safe.checkpoint({"c": 3}, SemVer(2, 0, 0))
    rb = safe.rollback_to(SemVer(1, 0, 0))
    checks.append(("s10_rollback_to_version", rb is not None and rb.get("a") == 1))

    # ── S11: Performance ─────────────────────────────────────────────────

    import random
    rng = random.Random(42)

    # S11.1: Register 100 schema versions
    t0 = time.time()
    perf_registry = SchemaRegistry()
    for i in range(100):
        fields = {
            f"field_{j}": FieldDef(f"field_{j}", FieldType.STRING, default=f"val_{j}")
            for j in range(rng.randint(5, 20))
        }
        perf_registry.register(SchemaVersion(
            "perf_schema", SemVer(1, i, 0), fields,
        ))
    elapsed = time.time() - t0
    checks.append(("s11_register_100", elapsed < 1.0))

    # S11.2: Change detection at scale
    t0 = time.time()
    big_v1 = SchemaVersion("big", SemVer(1, 0, 0), {
        f"f_{i}": FieldDef(f"f_{i}", FieldType.STRING, default=f"d_{i}")
        for i in range(200)
    })
    big_v2 = SchemaVersion("big", SemVer(2, 0, 0), {
        f"f_{i}": FieldDef(f"f_{i}", FieldType.STRING if i % 2 == 0 else FieldType.INT, default=f"d_{i}")
        for i in range(200)
    })
    changes = detect_changes(big_v1, big_v2)
    elapsed = time.time() - t0
    checks.append(("s11_change_detect_200", len(changes) > 0 and elapsed < 1.0))

    # S11.3: Validate 1000 documents
    t0 = time.time()
    for i in range(1000):
        doc = {"entity_id": f"e{i}", "trust_score": rng.random(), "name": f"name_{i}"}
        validate_document(doc, v1)
    elapsed = time.time() - t0
    checks.append(("s11_validate_1000", elapsed < 1.0))

    # S11.4: Federation consensus with 100 members
    t0 = time.time()
    big_consensus = FederationSchemaConsensus()
    for i in range(100):
        big_consensus.add_member(f"m{i}")
        ver = SemVer(1, rng.randint(0, 2), 0)
        big_consensus.vote(SchemaVote(f"m{i}", "entity", ver, time.time()))
    result = big_consensus.consensus_version("entity")
    elapsed = time.time() - t0
    checks.append(("s11_consensus_100", elapsed < 1.0))

    # S11.5: Schema diff at scale
    t0 = time.time()
    for _ in range(100):
        diff_schemas(big_v1, big_v2)
    elapsed = time.time() - t0
    checks.append(("s11_diff_100x", elapsed < 1.0))

    # ── Print Results ────────────────────────────────────────────────────
    passed = sum(1 for _, ok in checks if ok)
    total = len(checks)
    print(f"\n{'='*60}")
    print(f"  Schema Evolution & Version Negotiation — {passed}/{total} checks passed")
    print(f"{'='*60}")

    for name, ok in checks:
        status = "PASS" if ok else "FAIL"
        print(f"  [{status}] {name}")

    if passed < total:
        print(f"\n  FAILURES:")
        for name, ok in checks:
            if not ok:
                print(f"    ✗ {name}")

    print()
    return passed, total


if __name__ == "__main__":
    run_checks()
