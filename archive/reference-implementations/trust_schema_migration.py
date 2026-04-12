"""
Trust Schema Migration for Web4
Session 34, Track 5

Schema evolution for Web4 trust data structures:
- Schema versioning and compatibility matrix
- Backward-compatible (additive) changes
- Breaking changes with explicit migration paths
- Schema registry tracking all versions
- Migration scripts: transform old records to new format
- Canary testing for migrations
- Rollback support
- Compatibility checking (can_read, can_write)

Design principles:
  - Every schema change gets a version bump
  - Additive changes (new optional fields) are backward-compatible
  - Removing/renaming fields requires a migration script
  - The registry knows which version pairs can be migrated
  - Canary: run migration on a sample, check invariants, then proceed
  - Rollback: keep the original schema and a reverse migration
"""

import copy
import json
import hashlib
import time
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Set, Tuple


# ─── Schema Types ────────────────────────────────────────────────

class FieldType(Enum):
    STRING = "string"
    FLOAT = "float"
    INT = "int"
    BOOL = "bool"
    LIST = "list"
    DICT = "dict"
    OPTIONAL_FLOAT = "optional_float"
    OPTIONAL_STRING = "optional_string"


class ChangeType(Enum):
    ADDITIVE = "additive"          # New optional field — backward compatible
    RENAME = "rename"              # Field renamed — breaking
    REMOVE = "remove"              # Field removed — breaking
    TYPE_CHANGE = "type_change"    # Field type changed — breaking
    RESTRUCTURE = "restructure"    # Multiple field reorganization — breaking
    DEPRECATE = "deprecate"        # Field marked deprecated — non-breaking


@dataclass
class SchemaField:
    name: str
    field_type: FieldType
    required: bool = True
    default: Any = None
    deprecated: bool = False
    description: str = ""

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "type": self.field_type.value,
            "required": self.required,
            "default": self.default,
            "deprecated": self.deprecated,
        }


@dataclass
class TrustSchema:
    """A versioned schema for trust records."""
    name: str
    version: str         # semver: "1.0.0", "1.1.0", "2.0.0"
    fields: List[SchemaField]
    description: str = ""
    created_at: float = field(default_factory=time.time)

    def field_names(self) -> Set[str]:
        return {f.name for f in self.fields}

    def required_fields(self) -> Set[str]:
        return {f.name for f in self.fields if f.required}

    def optional_fields(self) -> Set[str]:
        return {f.name for f in self.fields if not f.required}

    def get_field(self, name: str) -> Optional[SchemaField]:
        for f in self.fields:
            if f.name == name:
                return f
        return None

    def fingerprint(self) -> str:
        """Hash of required field names + types for quick compatibility check."""
        sig = sorted(f"{f.name}:{f.field_type.value}" for f in self.fields if f.required)
        return hashlib.sha256("|".join(sig).encode()).hexdigest()[:16]

    def validate(self, record: dict) -> Tuple[bool, List[str]]:
        """Validate a record against this schema."""
        errors = []
        for f in self.fields:
            if f.required and f.name not in record:
                errors.append(f"Missing required field: {f.name}")
            if f.name in record:
                val = record[f.name]
                # Optional fields may be None
                if val is None and not f.required:
                    continue
                if f.field_type == FieldType.FLOAT and not isinstance(val, (int, float)):
                    errors.append(f"Field {f.name}: expected float, got {type(val).__name__}")
                elif f.field_type == FieldType.STRING and not isinstance(val, str):
                    errors.append(f"Field {f.name}: expected str, got {type(val).__name__}")
                elif f.field_type == FieldType.BOOL and not isinstance(val, bool):
                    errors.append(f"Field {f.name}: expected bool, got {type(val).__name__}")
        return len(errors) == 0, errors

    def version_tuple(self) -> Tuple[int, int, int]:
        parts = self.version.split(".")
        return tuple(int(p) for p in parts)  # type: ignore


# ─── Schema Compatibility ─────────────────────────────────────────

class CompatibilityLevel(Enum):
    FULL = "full"               # Reader can read all writer records
    BACKWARD = "backward"       # New schema can read old records
    FORWARD = "forward"         # Old schema can read new records
    NONE = "none"               # No compatibility


def check_compatibility(reader: TrustSchema, writer: TrustSchema) -> CompatibilityLevel:
    """
    Determine compatibility between reader and writer schemas.

    Full compatibility: same required fields, same types.
    Backward: reader has new optional fields only (reader is newer).
    Forward: reader is missing some optional writer fields (writer is newer).
    None: required field removed, renamed, or type changed.
    """
    r_required = reader.required_fields()
    w_required = writer.required_fields()

    # Check required fields match in name
    missing_from_reader = w_required - r_required
    extra_in_reader = r_required - w_required

    if missing_from_reader:
        # Reader is missing required fields that writer produces — cannot read
        return CompatibilityLevel.NONE

    if extra_in_reader:
        # Reader requires fields writer doesn't produce
        # This means old readers break on new records — NONE
        return CompatibilityLevel.NONE

    # Check type compatibility for shared fields
    for fname in r_required & w_required:
        rf = reader.get_field(fname)
        wf = writer.get_field(fname)
        if rf and wf and rf.field_type != wf.field_type:
            return CompatibilityLevel.NONE

    # All required fields match — check optional
    r_optional = reader.optional_fields()
    w_optional = writer.optional_fields()

    if r_required == w_required:
        if r_optional == w_optional:
            return CompatibilityLevel.FULL
        elif w_optional.issubset(r_optional):
            # Reader has additional optional fields — backward compatible
            return CompatibilityLevel.BACKWARD
        elif r_optional.issubset(w_optional):
            # Writer has additional optional fields — forward compatible
            return CompatibilityLevel.FORWARD
        else:
            # Mixed optional differences
            return CompatibilityLevel.BACKWARD

    return CompatibilityLevel.FULL


# ─── Migration Scripts ────────────────────────────────────────────

MigrationFn = Callable[[dict], dict]


@dataclass
class Migration:
    """A migration transforms records from source_version to target_version."""
    name: str
    source_version: str
    target_version: str
    change_type: ChangeType
    migrate: MigrationFn
    rollback: Optional[MigrationFn] = None
    description: str = ""

    def apply(self, record: dict) -> dict:
        return self.migrate(copy.deepcopy(record))

    def reverse(self, record: dict) -> Optional[dict]:
        if self.rollback:
            return self.rollback(copy.deepcopy(record))
        return None

    def is_reversible(self) -> bool:
        return self.rollback is not None


# ─── Schema Registry ──────────────────────────────────────────────

class SchemaRegistry:
    """
    Central registry for all trust schema versions and migration paths.
    Tracks: schemas, migrations, compatibility matrix.
    """

    def __init__(self):
        self.schemas: Dict[str, TrustSchema] = {}           # version -> schema
        self.migrations: List[Migration] = []
        self._compat_cache: Dict[Tuple[str, str], CompatibilityLevel] = {}

    def register_schema(self, schema: TrustSchema):
        self.schemas[schema.version] = schema
        # Invalidate cache
        self._compat_cache.clear()

    def register_migration(self, migration: Migration):
        self.migrations.append(migration)

    def get_schema(self, version: str) -> Optional[TrustSchema]:
        return self.schemas.get(version)

    def all_versions(self) -> List[str]:
        """Return all registered versions, sorted semantically."""
        def ver_key(v: str):
            return tuple(int(x) for x in v.split("."))
        return sorted(self.schemas.keys(), key=ver_key)

    def latest_version(self) -> Optional[str]:
        versions = self.all_versions()
        return versions[-1] if versions else None

    def find_migration_path(self, source: str, target: str) -> Optional[List[Migration]]:
        """
        BFS to find a migration path from source to target version.
        Returns ordered list of migrations to apply.
        """
        if source == target:
            return []
        # Build adjacency from migrations
        graph: Dict[str, List[Migration]] = {}
        for m in self.migrations:
            graph.setdefault(m.source_version, []).append(m)

        # BFS
        from collections import deque
        queue = deque([(source, [])])
        visited = {source}
        while queue:
            current, path = queue.popleft()
            for m in graph.get(current, []):
                if m.target_version == target:
                    return path + [m]
                if m.target_version not in visited:
                    visited.add(m.target_version)
                    queue.append((m.target_version, path + [m]))
        return None  # No path found

    def migrate_record(self, record: dict, source: str, target: str) -> Tuple[Optional[dict], str]:
        """
        Migrate a record from source version to target version.
        Returns (migrated_record, status_message).
        """
        path = self.find_migration_path(source, target)
        if path is None:
            return None, f"no_migration_path_{source}_to_{target}"
        result = copy.deepcopy(record)
        for migration in path:
            result = migration.apply(result)
        return result, "ok"

    def rollback_record(self, record: dict, from_version: str, to_version: str) -> Tuple[Optional[dict], str]:
        """
        Rollback a record from from_version back to to_version.
        Traverses migrations in reverse.
        """
        # Find forward path (to_version -> from_version) then reverse it
        path = self.find_migration_path(to_version, from_version)
        if path is None:
            return None, "no_forward_path_for_rollback"
        # Reverse the path and apply rollbacks
        result = copy.deepcopy(record)
        for migration in reversed(path):
            rolled = migration.reverse(result)
            if rolled is None:
                return None, f"migration_{migration.name}_not_reversible"
            result = rolled
        return result, "ok"

    def compatibility_matrix(self) -> Dict[Tuple[str, str], CompatibilityLevel]:
        """Build compatibility matrix for all registered schema pairs."""
        versions = self.all_versions()
        matrix = {}
        for r_ver in versions:
            for w_ver in versions:
                key = (r_ver, w_ver)
                if key not in self._compat_cache:
                    r_schema = self.schemas[r_ver]
                    w_schema = self.schemas[w_ver]
                    self._compat_cache[key] = check_compatibility(r_schema, w_schema)
                matrix[key] = self._compat_cache[key]
        return matrix

    def schema_count(self) -> int:
        return len(self.schemas)

    def migration_count(self) -> int:
        return len(self.migrations)


# ─── Canary Testing ───────────────────────────────────────────────

@dataclass
class CanaryResult:
    total_records: int
    migrated: int
    validated: int
    failed: int
    invariants_held: int
    invariants_violated: int
    success_rate: float
    proceed_recommended: bool
    failure_examples: List[str]


class CanaryMigrationTester:
    """
    Tests a migration on a sample of records before full deployment.
    Runs invariant checks on migrated records to catch silent failures.
    """

    def __init__(self, registry: SchemaRegistry):
        self.registry = registry

    def run_canary(self,
                   records: List[dict],
                   source_version: str,
                   target_version: str,
                   invariants: List[Callable[[dict], bool]],
                   sample_size: Optional[int] = None,
                   success_threshold: float = 0.99) -> CanaryResult:
        """
        Run migration on `sample_size` records (or all if None).
        Check each migrated record against all invariants.
        Recommend proceed if success_rate >= success_threshold.
        """
        target_schema = self.registry.get_schema(target_version)
        sample = records[:sample_size] if sample_size else records

        migrated_count = 0
        validated_count = 0
        failed_count = 0
        inv_held = 0
        inv_violated = 0
        failures = []

        for record in sample:
            migrated, status = self.registry.migrate_record(record, source_version, target_version)
            if migrated is None or status != "ok":
                failed_count += 1
                failures.append(f"migration_failed: {status}")
                continue
            migrated_count += 1

            # Schema validation
            if target_schema:
                valid, errors = target_schema.validate(migrated)
                if valid:
                    validated_count += 1
                else:
                    failed_count += 1
                    failures.append(f"schema_invalid: {errors[0] if errors else 'unknown'}")
                    continue
            else:
                validated_count += 1  # No schema to check

            # Invariant checks
            all_inv_ok = True
            for inv in invariants:
                try:
                    if inv(migrated):
                        inv_held += 1
                    else:
                        inv_violated += 1
                        all_inv_ok = False
                        failures.append("invariant_violated")
                except Exception as e:
                    inv_violated += 1
                    all_inv_ok = False
                    failures.append(f"invariant_exception: {e}")

        total_checks = migrated_count + failed_count
        success_rate = validated_count / total_checks if total_checks > 0 else 0.0

        return CanaryResult(
            total_records=len(sample),
            migrated=migrated_count,
            validated=validated_count,
            failed=failed_count,
            invariants_held=inv_held,
            invariants_violated=inv_violated,
            success_rate=success_rate,
            proceed_recommended=success_rate >= success_threshold,
            failure_examples=failures[:5],  # First 5 failures
        )


# ─── Concrete Trust Schema Versions ──────────────────────────────

def build_trust_schema_registry() -> SchemaRegistry:
    """
    Build a realistic trust schema registry with versions v1 through v3.

    v1.0.0: Initial trust record
    v1.1.0: Added optional 'metadata' field (additive, backward compatible)
    v2.0.0: Renamed 'trust' -> 'trust_score', added 'dimensions' dict (breaking)
    v2.1.0: Added optional 'audit_log' list (additive)
    v3.0.0: Restructured — flattened dimensions into top-level fields (breaking)
    """
    registry = SchemaRegistry()

    # ── v1.0.0 ────────────────────────────────────────────────────
    v1 = TrustSchema(
        name="TrustRecord",
        version="1.0.0",
        description="Initial trust record schema",
        fields=[
            SchemaField("entity_id", FieldType.STRING, required=True),
            SchemaField("trust", FieldType.FLOAT, required=True),
            SchemaField("attested_by", FieldType.STRING, required=True),
            SchemaField("timestamp", FieldType.FLOAT, required=True),
        ]
    )
    registry.register_schema(v1)

    # ── v1.1.0 — additive: add optional 'metadata' ────────────────
    v1_1 = TrustSchema(
        name="TrustRecord",
        version="1.1.0",
        description="Added optional metadata field",
        fields=[
            SchemaField("entity_id", FieldType.STRING, required=True),
            SchemaField("trust", FieldType.FLOAT, required=True),
            SchemaField("attested_by", FieldType.STRING, required=True),
            SchemaField("timestamp", FieldType.FLOAT, required=True),
            SchemaField("metadata", FieldType.DICT, required=False, default=None),
        ]
    )
    registry.register_schema(v1_1)

    # ── v2.0.0 — breaking: rename 'trust' -> 'trust_score' ───────
    v2 = TrustSchema(
        name="TrustRecord",
        version="2.0.0",
        description="Renamed trust field, added dimensions",
        fields=[
            SchemaField("entity_id", FieldType.STRING, required=True),
            SchemaField("trust_score", FieldType.FLOAT, required=True),
            SchemaField("attested_by", FieldType.STRING, required=True),
            SchemaField("timestamp", FieldType.FLOAT, required=True),
            SchemaField("dimensions", FieldType.DICT, required=False, default=None,
                        description="T3 dimensions: talent, training, temperament"),
        ]
    )
    registry.register_schema(v2)

    # ── v2.1.0 — additive: add optional 'audit_log' ───────────────
    v2_1 = TrustSchema(
        name="TrustRecord",
        version="2.1.0",
        description="Added optional audit_log",
        fields=[
            SchemaField("entity_id", FieldType.STRING, required=True),
            SchemaField("trust_score", FieldType.FLOAT, required=True),
            SchemaField("attested_by", FieldType.STRING, required=True),
            SchemaField("timestamp", FieldType.FLOAT, required=True),
            SchemaField("dimensions", FieldType.DICT, required=False, default=None),
            SchemaField("audit_log", FieldType.LIST, required=False, default=None),
        ]
    )
    registry.register_schema(v2_1)

    # ── v3.0.0 — breaking: flatten dimensions to top-level ────────
    v3 = TrustSchema(
        name="TrustRecord",
        version="3.0.0",
        description="Flattened T3 dimensions to top-level fields",
        fields=[
            SchemaField("entity_id", FieldType.STRING, required=True),
            SchemaField("trust_score", FieldType.FLOAT, required=True),
            SchemaField("attested_by", FieldType.STRING, required=True),
            SchemaField("timestamp", FieldType.FLOAT, required=True),
            SchemaField("talent", FieldType.FLOAT, required=False, default=None),
            SchemaField("training", FieldType.FLOAT, required=False, default=None),
            SchemaField("temperament", FieldType.FLOAT, required=False, default=None),
            SchemaField("audit_log", FieldType.LIST, required=False, default=None),
        ]
    )
    registry.register_schema(v3)

    # ── Migrations ─────────────────────────────────────────────────

    def migrate_v1_to_v1_1(r: dict) -> dict:
        r.setdefault("metadata", None)
        return r

    def rollback_v1_1_to_v1(r: dict) -> dict:
        r.pop("metadata", None)
        return r

    registry.register_migration(Migration(
        name="add_metadata",
        source_version="1.0.0",
        target_version="1.1.0",
        change_type=ChangeType.ADDITIVE,
        migrate=migrate_v1_to_v1_1,
        rollback=rollback_v1_1_to_v1,
        description="Add optional metadata field",
    ))

    def migrate_v1_1_to_v2(r: dict) -> dict:
        r["trust_score"] = r.pop("trust", r.get("trust", 0.5))
        r.pop("metadata", None)
        r.setdefault("dimensions", None)
        return r

    def rollback_v2_to_v1_1(r: dict) -> dict:
        r["trust"] = r.pop("trust_score", 0.5)
        r.pop("dimensions", None)
        r.setdefault("metadata", None)
        return r

    registry.register_migration(Migration(
        name="rename_trust_to_trust_score",
        source_version="1.1.0",
        target_version="2.0.0",
        change_type=ChangeType.RENAME,
        migrate=migrate_v1_1_to_v2,
        rollback=rollback_v2_to_v1_1,
        description="Rename 'trust' to 'trust_score', add dimensions",
    ))

    def migrate_v2_to_v2_1(r: dict) -> dict:
        r.setdefault("audit_log", None)
        return r

    def rollback_v2_1_to_v2(r: dict) -> dict:
        r.pop("audit_log", None)
        return r

    registry.register_migration(Migration(
        name="add_audit_log",
        source_version="2.0.0",
        target_version="2.1.0",
        change_type=ChangeType.ADDITIVE,
        migrate=migrate_v2_to_v2_1,
        rollback=rollback_v2_1_to_v2,
        description="Add optional audit_log field",
    ))

    def migrate_v2_1_to_v3(r: dict) -> dict:
        dims = r.pop("dimensions", None) or {}
        r["talent"] = dims.get("talent", None)
        r["training"] = dims.get("training", None)
        r["temperament"] = dims.get("temperament", None)
        return r

    def rollback_v3_to_v2_1(r: dict) -> dict:
        dims = {}
        talent = r.pop("talent", None)
        training = r.pop("training", None)
        temperament = r.pop("temperament", None)
        if talent is not None:
            dims["talent"] = talent
        if training is not None:
            dims["training"] = training
        if temperament is not None:
            dims["temperament"] = temperament
        r["dimensions"] = dims if dims else None
        return r

    registry.register_migration(Migration(
        name="flatten_dimensions",
        source_version="2.1.0",
        target_version="3.0.0",
        change_type=ChangeType.RESTRUCTURE,
        migrate=migrate_v2_1_to_v3,
        rollback=rollback_v3_to_v2_1,
        description="Flatten T3 dimensions dict to top-level fields",
    ))

    return registry


# ─── Sample Records ───────────────────────────────────────────────

def make_v1_records(n: int = 10) -> List[dict]:
    records = []
    for i in range(n):
        records.append({
            "entity_id": f"entity_{i}",
            "trust": round(0.3 + (i % 7) * 0.1, 2),
            "attested_by": f"attester_{i % 3}",
            "timestamp": 1700000000.0 + i * 100,
        })
    return records


def make_v2_records(n: int = 10) -> List[dict]:
    records = []
    for i in range(n):
        records.append({
            "entity_id": f"entity_{i}",
            "trust_score": round(0.3 + (i % 7) * 0.1, 2),
            "attested_by": f"attester_{i % 3}",
            "timestamp": 1700000000.0 + i * 100,
            "dimensions": {
                "talent": round(0.4 + i * 0.05, 2),
                "training": round(0.5 + i * 0.04, 2),
                "temperament": round(0.6 + i * 0.03, 2),
            },
            "audit_log": [f"event_{j}" for j in range(i % 3)],
        })
    return records


# ═══════════════════════════════════════════════════════════════
#  CHECKS
# ═══════════════════════════════════════════════════════════════

def run_checks():
    passed = 0
    failed = 0

    def check(name, condition, detail=""):
        nonlocal passed, failed
        if condition:
            passed += 1
        else:
            failed += 1
            print(f"  FAIL: {name}" + (f" — {detail}" if detail else ""))

    print("=" * 70)
    print("Trust Schema Migration for Web4")
    print("Session 34, Track 5")
    print("=" * 70)

    # ── §1 Schema Construction ────────────────────────────────────
    print("\n§1 Schema Construction\n")

    v1_fields = [
        SchemaField("entity_id", FieldType.STRING, required=True),
        SchemaField("trust", FieldType.FLOAT, required=True),
        SchemaField("timestamp", FieldType.FLOAT, required=True),
    ]
    s = TrustSchema("TrustRecord", "1.0.0", v1_fields)

    check("schema_name", s.name == "TrustRecord")
    check("schema_version", s.version == "1.0.0")
    check("field_names", s.field_names() == {"entity_id", "trust", "timestamp"})
    check("required_fields", s.required_fields() == {"entity_id", "trust", "timestamp"})
    check("optional_fields_empty", s.optional_fields() == set())
    check("version_tuple", s.version_tuple() == (1, 0, 0))

    fp = s.fingerprint()
    check("fingerprint_is_string", isinstance(fp, str))
    check("fingerprint_length_16", len(fp) == 16)

    # Validation
    valid_record = {"entity_id": "e1", "trust": 0.7, "timestamp": 1700000000.0}
    ok, errs = s.validate(valid_record)
    check("valid_record_passes", ok, str(errs))

    missing_record = {"entity_id": "e1", "timestamp": 1700000000.0}
    ok2, errs2 = s.validate(missing_record)
    check("missing_required_field_fails", not ok2)
    check("error_mentions_trust", any("trust" in e for e in errs2))

    wrong_type = {"entity_id": "e1", "trust": "high", "timestamp": 1700000000.0}
    ok3, errs3 = s.validate(wrong_type)
    check("wrong_type_fails", not ok3)

    # ── §2 Compatibility Checking ─────────────────────────────────
    print("\n§2 Compatibility Checking\n")

    # Same schema — full compatibility
    s2 = TrustSchema("TrustRecord", "1.0.0", copy.deepcopy(v1_fields))
    compat = check_compatibility(s, s2)
    check("same_schema_full_compat", compat == CompatibilityLevel.FULL,
          f"compat={compat}")

    # Reader adds optional field — backward compat (reader is newer)
    v1_1_fields = copy.deepcopy(v1_fields) + [
        SchemaField("metadata", FieldType.DICT, required=False)
    ]
    s1_1 = TrustSchema("TrustRecord", "1.1.0", v1_1_fields)
    compat_bw = check_compatibility(s1_1, s)  # reader=1.1.0, writer=1.0.0
    check("additive_change_backward_compat",
          compat_bw in (CompatibilityLevel.BACKWARD, CompatibilityLevel.FULL),
          f"compat={compat_bw}")

    # Breaking: rename required field
    v2_fields_renamed = [
        SchemaField("entity_id", FieldType.STRING, required=True),
        SchemaField("trust_score", FieldType.FLOAT, required=True),  # renamed
        SchemaField("timestamp", FieldType.FLOAT, required=True),
    ]
    s2_renamed = TrustSchema("TrustRecord", "2.0.0", v2_fields_renamed)
    compat_break = check_compatibility(s, s2_renamed)  # old reader, new writer
    check("renamed_field_breaks_compat", compat_break == CompatibilityLevel.NONE,
          f"compat={compat_break}")

    # Type change breaks compatibility
    v_type_change = [
        SchemaField("entity_id", FieldType.STRING, required=True),
        SchemaField("trust", FieldType.INT, required=True),  # int not float
        SchemaField("timestamp", FieldType.FLOAT, required=True),
    ]
    s_type = TrustSchema("TrustRecord", "1.5.0", v_type_change)
    compat_type = check_compatibility(s, s_type)
    check("type_change_breaks_compat", compat_type == CompatibilityLevel.NONE,
          f"compat={compat_type}")

    # ── §3 Schema Registry ────────────────────────────────────────
    print("\n§3 Schema Registry\n")

    registry = build_trust_schema_registry()
    check("registry_has_5_schemas", registry.schema_count() == 5,
          f"count={registry.schema_count()}")
    check("registry_has_4_migrations", registry.migration_count() == 4,
          f"count={registry.migration_count()}")

    versions = registry.all_versions()
    check("versions_sorted", versions == ["1.0.0", "1.1.0", "2.0.0", "2.1.0", "3.0.0"],
          f"versions={versions}")
    check("latest_version_is_3", registry.latest_version() == "3.0.0")

    schema_v2 = registry.get_schema("2.0.0")
    check("get_schema_works", schema_v2 is not None)
    check("v2_has_trust_score", schema_v2 and "trust_score" in schema_v2.field_names())

    schema_none = registry.get_schema("99.0.0")
    check("get_nonexistent_returns_none", schema_none is None)

    # ── §4 Migration Path Finding ─────────────────────────────────
    print("\n§4 Migration Path Finding\n")

    path = registry.find_migration_path("1.0.0", "3.0.0")
    check("migration_path_found", path is not None)
    check("migration_path_length_4", len(path) == 4 if path else False,
          f"len={len(path) if path else None}")

    # Direct path (adjacent)
    direct = registry.find_migration_path("1.0.0", "1.1.0")
    check("direct_migration_path", direct is not None and len(direct) == 1,
          f"len={len(direct) if direct else None}")

    # No path (backwards migration not directly supported without rollback API)
    # Same version = empty path
    same = registry.find_migration_path("2.0.0", "2.0.0")
    check("same_version_empty_path", same == [])

    no_path = registry.find_migration_path("3.0.0", "1.0.0")
    # Forward migrations only registered; no reverse path
    check("no_reverse_path_without_rollback", no_path is None)

    # ── §5 Record Migration ───────────────────────────────────────
    print("\n§5 Record Migration\n")

    v1_records = make_v1_records(5)
    sample = v1_records[0]

    # v1 -> v1.1
    migrated_1_1, status = registry.migrate_record(sample, "1.0.0", "1.1.0")
    check("v1_to_v1_1_ok", status == "ok" and migrated_1_1 is not None, status)
    check("v1_1_has_metadata_key", migrated_1_1 and "metadata" in migrated_1_1)
    check("v1_1_preserves_entity_id",
          migrated_1_1 and migrated_1_1["entity_id"] == sample["entity_id"])

    # v1 -> v2 (multi-hop via registry path)
    migrated_v2, status2 = registry.migrate_record(sample, "1.0.0", "2.0.0")
    check("v1_to_v2_ok", status2 == "ok" and migrated_v2 is not None, status2)
    check("v2_has_trust_score", migrated_v2 and "trust_score" in migrated_v2)
    check("v2_no_trust_field", migrated_v2 and "trust" not in migrated_v2)
    check("v2_trust_score_value_preserved",
          migrated_v2 and abs(migrated_v2["trust_score"] - sample["trust"]) < 1e-6)

    # v1 -> v3 (full chain)
    migrated_v3, status3 = registry.migrate_record(sample, "1.0.0", "3.0.0")
    check("v1_to_v3_ok", status3 == "ok" and migrated_v3 is not None, status3)
    check("v3_has_talent_field", migrated_v3 and "talent" in migrated_v3)
    check("v3_has_training_field", migrated_v3 and "training" in migrated_v3)
    check("v3_has_temperament_field", migrated_v3 and "temperament" in migrated_v3)
    check("v3_no_dimensions_dict", migrated_v3 and "dimensions" not in migrated_v3)

    # Validate migrated record against target schema
    v3_schema = registry.get_schema("3.0.0")
    if v3_schema and migrated_v3:
        v3_valid, v3_errs = v3_schema.validate(migrated_v3)
        check("migrated_v3_validates_against_schema", v3_valid, str(v3_errs))

    # ── §6 Rollback ───────────────────────────────────────────────
    print("\n§6 Rollback\n")

    # Migrate forward then roll back
    original = v1_records[2]
    migrated_fwd, _ = registry.migrate_record(original, "1.0.0", "1.1.0")
    rolled_back, rb_status = registry.rollback_record(migrated_fwd, "1.1.0", "1.0.0")
    check("rollback_status_ok", rb_status == "ok", rb_status)
    check("rollback_restores_entity_id",
          rolled_back and rolled_back["entity_id"] == original["entity_id"])
    check("rollback_removes_metadata", rolled_back and "metadata" not in rolled_back)
    check("rollback_preserves_trust_value",
          rolled_back and abs(rolled_back["trust"] - original["trust"]) < 1e-6)

    # Multi-hop rollback
    fwd_v2_1, _ = registry.migrate_record(original, "1.0.0", "2.1.0")
    rb_to_v1_1, rb_status2 = registry.rollback_record(fwd_v2_1, "2.1.0", "1.1.0")
    check("multi_hop_rollback_ok", rb_status2 == "ok", rb_status2)
    check("multi_hop_rollback_has_trust_field",
          rb_to_v1_1 and "trust" in rb_to_v1_1)

    # ── §7 Canary Testing ─────────────────────────────────────────
    print("\n§7 Canary Testing\n")

    records = make_v1_records(20)
    tester = CanaryMigrationTester(registry)

    # Invariants for migrated v3 records
    def trust_score_in_range(r: dict) -> bool:
        return 0.0 <= r.get("trust_score", -1) <= 1.0

    def entity_id_present(r: dict) -> bool:
        return isinstance(r.get("entity_id"), str) and len(r["entity_id"]) > 0

    def timestamp_positive(r: dict) -> bool:
        return r.get("timestamp", -1) > 0

    invariants = [trust_score_in_range, entity_id_present, timestamp_positive]

    canary = tester.run_canary(
        records=records,
        source_version="1.0.0",
        target_version="3.0.0",
        invariants=invariants,
        sample_size=10,
        success_threshold=0.95,
    )
    check("canary_total_records_10", canary.total_records == 10,
          f"total={canary.total_records}")
    check("canary_all_migrated", canary.migrated == 10,
          f"migrated={canary.migrated}")
    check("canary_no_failures", canary.failed == 0,
          f"failed={canary.failed}")
    check("canary_invariants_held",
          canary.invariants_held == 10 * len(invariants),
          f"held={canary.invariants_held}")
    check("canary_success_rate_high",
          canary.success_rate >= 0.99,
          f"rate={canary.success_rate}")
    check("canary_proceed_recommended", canary.proceed_recommended)

    # Canary on already-valid records
    v2_records = make_v2_records(5)
    canary2 = tester.run_canary(
        records=v2_records,
        source_version="2.1.0",
        target_version="3.0.0",
        invariants=[trust_score_in_range, entity_id_present],
        sample_size=5,
    )
    check("canary_v2_to_v3_succeeds", canary2.proceed_recommended,
          f"rate={canary2.success_rate}")

    # ── §8 Compatibility Matrix ───────────────────────────────────
    print("\n§8 Compatibility Matrix\n")

    matrix = registry.compatibility_matrix()
    check("matrix_has_25_entries", len(matrix) == 25,
          f"len={len(matrix)}")

    # v1.0.0 -> v1.0.0: full
    check("self_compat_full",
          matrix[("1.0.0", "1.0.0")] == CompatibilityLevel.FULL)

    # v1.1.0 reading v1.0.0: backward compatible (reader has extra optional)
    v1_1_reads_v1_0 = matrix[("1.1.0", "1.0.0")]
    check("v1_1_can_read_v1_0",
          v1_1_reads_v1_0 in (CompatibilityLevel.BACKWARD, CompatibilityLevel.FULL),
          f"compat={v1_1_reads_v1_0}")

    # v1.0.0 reading v2.0.0: none (required field renamed)
    v1_reads_v2 = matrix[("1.0.0", "2.0.0")]
    check("v1_cannot_read_v2", v1_reads_v2 == CompatibilityLevel.NONE,
          f"compat={v1_reads_v2}")

    # v2.0.0 reading v2.1.0: forward compatible (writer has extra optional)
    v2_reads_v2_1 = matrix[("2.0.0", "2.1.0")]
    check("v2_reads_v2_1_forward_or_full",
          v2_reads_v2_1 in (CompatibilityLevel.FORWARD, CompatibilityLevel.FULL),
          f"compat={v2_reads_v2_1}")

    # v3.0.0 reading v1.0.0: none (required field mismatch)
    v3_reads_v1 = matrix[("3.0.0", "1.0.0")]
    check("v3_cannot_read_v1", v3_reads_v1 == CompatibilityLevel.NONE,
          f"compat={v3_reads_v1}")

    # Summary
    total = passed + failed
    print(f"\n{'=' * 70}")
    print(f"Trust Schema Migration: {passed}/{total} checks passed")
    if failed > 0:
        print(f"  {failed} checks FAILED")
    else:
        print(f"  All {total} checks passed")
    return passed, failed


if __name__ == "__main__":
    passed, failed = run_checks()
    exit(0 if failed == 0 else 1)
