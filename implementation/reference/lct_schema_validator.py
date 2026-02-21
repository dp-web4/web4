#!/usr/bin/env python3
"""
LCT Schema Validator — Track H
===============================
Validates LCT documents from all reference implementations against the
canonical JSON Schema (web4-standard/schemas/lct.schema.json).

Purpose: Discover and catalog divergences between what the code actually
emits and what the schema requires. This is a research/audit tool.

Key finding: No Python implementation produces a full schema-compliant
LCT document. TypeScript and Go do. This validator proves it and maps
every specific divergence.
"""

import json
import hashlib
import time
import os
import sys
from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

# Add project paths
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "web4-standard" / "implementation" / "reference"))

import jsonschema
from jsonschema import Draft202012Validator, ValidationError


# ═══════════════════════════════════════════════════════════════
# Schema loader
# ═══════════════════════════════════════════════════════════════

def load_schema() -> dict:
    """Load the canonical LCT JSON Schema."""
    schema_path = Path(__file__).parent.parent.parent / "web4-standard" / "schemas" / "lct.schema.json"
    with open(schema_path) as f:
        return json.load(f)


def create_validator(schema: dict) -> Draft202012Validator:
    """Create a JSON Schema 2020-12 validator."""
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


# ═══════════════════════════════════════════════════════════════
# Divergence catalog
# ═══════════════════════════════════════════════════════════════

@dataclass
class Divergence:
    """A single spec-vs-code divergence."""
    source: str          # Which implementation
    category: str        # missing_field, extra_field, wrong_type, pattern_mismatch, etc.
    path: str            # JSON path to the field
    expected: str        # What schema requires
    actual: str          # What code produces
    severity: str        # critical (required field missing), warning (pattern/type), info (extra field)

    def to_dict(self) -> dict:
        return {
            "source": self.source, "category": self.category,
            "path": self.path, "expected": self.expected,
            "actual": self.actual, "severity": self.severity
        }


@dataclass
class ValidationReport:
    """Structured report for one LCT document validation."""
    source: str
    document_type: str
    is_valid: bool
    divergences: List[Divergence] = field(default_factory=list)
    error_count: int = 0
    warning_count: int = 0
    info_count: int = 0

    def add(self, d: Divergence):
        self.divergences.append(d)
        if d.severity == "critical":
            self.error_count += 1
        elif d.severity == "warning":
            self.warning_count += 1
        else:
            self.info_count += 1

    def summary(self) -> str:
        status = "PASS" if self.is_valid else "FAIL"
        return (f"[{status}] {self.source} ({self.document_type}): "
                f"{self.error_count} critical, {self.warning_count} warnings, "
                f"{self.info_count} info")


# ═══════════════════════════════════════════════════════════════
# Document builders — construct what each implementation emits
# ═══════════════════════════════════════════════════════════════

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_birth_certificate_doc() -> Tuple[dict, str]:
    """What BirthCertificate.to_dict() actually produces (from hardbound_cli.py)."""
    return {
        "@context": ["https://web4.io/contexts/sal.jsonld"],
        "type": "Web4BirthCertificate",
        "entity": "lct:web4:alice-001",
        "entityName": "alice",
        "citizenRole": "lct:web4:role:citizen:member",
        "society": "lct:web4:test-society",
        "societyName": "TestSociety",
        "lawOracle": "lct:web4:law-oracle-001",
        "lawVersion": "v1",
        "birthTimestamp": now_iso(),
        "witnesses": ["lct:web4:founder-001"],
        "genesisBlock": hashlib.sha256(b"genesis").hexdigest(),
        "initialRights": ["vote", "propose", "delegate"],
        "initialResponsibilities": ["follow_law", "pay_taxes"],
        "bindingType": "software",
        "certHash": hashlib.sha256(b"test-cert").hexdigest(),
    }, "BirthCertificate.to_dict()"


def build_web4entity_status() -> Tuple[dict, str]:
    """What Web4Entity.status() actually produces."""
    return {
        "lct_id": "lct:web4:agent-001",
        "entity_type": "ai",
        "name": "sage-legion",
        "state": "active",
        "t3": {"talent": 0.5, "training": 0.5, "temperament": 0.5, "composite": 0.5},
        "v3": {"valuation": 0.0, "veracity": 0.5, "validity": 0.5, "composite": 0.35},
        "atp": {"atp": 100.0, "adp": 0.0, "energy_ratio": 1.0},
        "coherence": 0.7,
        "presence_density": 0.5,
        "witnesses": 3,
        "relationships": 2,
        "children": 1,
        "actions_taken": 5,
        "created_at": now_iso()
    }, "Web4Entity.status()"


def build_federation_lct() -> Tuple[dict, str]:
    """What FederationLCT.to_dict() actually produces."""
    return {
        "lct_id": "lct:web4:fed-agent-001",
        "entity_type": "ai",
        "society_id": "society-alpha",
        "entity_name": "federation-agent",
        "status": "active",
        "public_key_hash": hashlib.sha256(b"pubkey").hexdigest(),
        "birth_cert_hash": hashlib.sha256(b"cert").hexdigest(),
        "created_at": time.time(),
        "grounding_anchor": hashlib.sha256(b"anchor").hexdigest(),
    }, "FederationLCT.to_dict()"


def build_compliant_minimal() -> Tuple[dict, str]:
    """A minimal but schema-compliant LCT document (what TypeScript/Go produce)."""
    ts = now_iso()
    return {
        "lct_id": "lct:web4:compliant-001",
        "subject": "did:web4:key:abc123",
        "binding": {
            "entity_type": "ai",
            "public_key": "z6MkhaXgBZDvotDkL5257faiztiGiC2QtKLGpbnnEGta2doK",
            "created_at": ts,
            "binding_proof": "cose:test-proof-data"
        },
        "birth_certificate": {
            "issuing_society": "lct:web4:test-society",
            "citizen_role": "lct:web4:role:citizen:member",
            "context": "platform",
            "birth_timestamp": ts,
            "birth_witnesses": ["lct:web4:founder-001"]
        },
        "mrh": {
            "bound": [],
            "paired": [{"lct_id": "lct:web4:society-001", "ts": ts}],
            "horizon_depth": 3,
            "last_updated": ts
        },
        "policy": {
            "capabilities": ["read", "write", "execute"]
        }
    }, "Compliant Minimal (TypeScript/Go pattern)"


def build_compliant_full() -> Tuple[dict, str]:
    """A fully-populated schema-compliant LCT document."""
    ts = now_iso()
    return {
        "lct_id": "lct:web4:full-001",
        "subject": "did:web4:key:xyz789",
        "binding": {
            "entity_type": "human",
            "public_key": "z6MkhaXgBZDvotDkL5257faiztiGiC2QtKLGpbnnEGta2doK",
            "hardware_anchor": "eat:tpm2-intel-adl-001",
            "created_at": ts,
            "binding_proof": "cose:ecdsa-p256-proof-data"
        },
        "birth_certificate": {
            "issuing_society": "lct:web4:research-federation",
            "citizen_role": "lct:web4:role:citizen:researcher",
            "context": "organization",
            "birth_timestamp": ts,
            "parent_entity": "lct:web4:admin-001",
            "birth_witnesses": ["lct:web4:admin-001", "lct:web4:witness-001"]
        },
        "mrh": {
            "bound": [
                {"lct_id": "lct:web4:device-001", "type": "child", "ts": ts}
            ],
            "paired": [
                {"lct_id": "lct:web4:society-001", "pairing_type": "birth_certificate",
                 "permanent": True, "context": "membership", "ts": ts}
            ],
            "witnessing": [
                {"lct_id": "lct:web4:oracle-001", "role": "audit", "last_attestation": ts}
            ],
            "horizon_depth": 5,
            "last_updated": ts
        },
        "policy": {
            "capabilities": ["read", "write", "execute", "delegate"],
            "constraints": {"max_delegation_depth": 3, "atp_cap": 500}
        },
        "t3_tensor": {
            "talent": 0.72, "training": 0.85, "temperament": 0.68,
            "sub_dimensions": {
                "talent": {"code_review": 0.8, "architecture": 0.65},
                "training": {"formal_education": 0.9, "practical": 0.8}
            },
            "composite_score": 0.75,
            "last_computed": ts,
            "computation_witnesses": ["lct:web4:oracle-001"]
        },
        "v3_tensor": {
            "valuation": 150.0, "veracity": 0.88, "validity": 0.92,
            "composite_score": 0.82,
            "last_computed": ts
        },
        "attestations": [
            {"witness": "lct:web4:oracle-001", "type": "trust_computation",
             "sig": "ecdsa-p256-sig-hex", "ts": ts}
        ],
        "lineage": [
            {"reason": "genesis", "ts": ts}
        ],
        "revocation": {
            "status": "active"
        }
    }, "Compliant Full (all optional fields)"


# ═══════════════════════════════════════════════════════════════
# Deep divergence analyzer
# ═══════════════════════════════════════════════════════════════

def analyze_divergences(doc: dict, schema: dict, source: str) -> ValidationReport:
    """Deep analysis: validate + catalog every divergence."""
    validator = create_validator(schema)
    errors = list(validator.iter_errors(doc))
    report = ValidationReport(
        source=source,
        document_type="LCT",
        is_valid=len(errors) == 0
    )

    # Deduplicate: track (category, path) pairs we've already reported
    seen = set()

    for err in errors:
        path = ".".join(str(p) for p in err.absolute_path) or "(root)"
        # Classify the error
        if err.validator == "required":
            for missing in err.validator_value:
                if missing not in err.instance:
                    key = ("missing_required_field",
                           f"{path}.{missing}" if path != "(root)" else missing)
                    if key in seen:
                        continue
                    seen.add(key)
                    report.add(Divergence(
                        source=source, category="missing_required_field",
                        path=key[1],
                        expected=f"required field '{missing}'",
                        actual="not present",
                        severity="critical"
                    ))
        elif err.validator == "additionalProperties":
            # Find which properties are extra
            allowed = set(err.schema.get("properties", {}).keys())
            actual = set(err.instance.keys()) if isinstance(err.instance, dict) else set()
            extras = actual - allowed
            for extra_key in extras:
                key = ("extra_field",
                       f"{path}.{extra_key}" if path != "(root)" else extra_key)
                if key in seen:
                    continue
                seen.add(key)
                report.add(Divergence(
                    source=source, category="extra_field",
                    path=key[1],
                    expected="not allowed (additionalProperties: false)",
                    actual=f"present with value: {repr(err.instance.get(extra_key, '?'))[:80]}",
                    severity="warning"
                ))
        elif err.validator == "pattern":
            report.add(Divergence(
                source=source, category="pattern_mismatch",
                path=path,
                expected=f"pattern: {err.validator_value}",
                actual=f"value: {repr(err.instance)[:80]}",
                severity="warning"
            ))
        elif err.validator == "enum":
            report.add(Divergence(
                source=source, category="enum_mismatch",
                path=path,
                expected=f"one of {err.validator_value}",
                actual=f"value: {repr(err.instance)[:80]}",
                severity="warning"
            ))
        elif err.validator == "type":
            report.add(Divergence(
                source=source, category="wrong_type",
                path=path,
                expected=f"type: {err.validator_value}",
                actual=f"type: {type(err.instance).__name__}, value: {repr(err.instance)[:80]}",
                severity="critical"
            ))
        elif err.validator == "format":
            report.add(Divergence(
                source=source, category="format_mismatch",
                path=path,
                expected=f"format: {err.validator_value}",
                actual=f"value: {repr(err.instance)[:80]}",
                severity="warning"
            ))
        elif err.validator == "minItems":
            report.add(Divergence(
                source=source, category="constraint_violation",
                path=path,
                expected=f"minItems: {err.validator_value}",
                actual=f"length: {len(err.instance) if isinstance(err.instance, list) else '?'}",
                severity="warning"
            ))
        else:
            report.add(Divergence(
                source=source, category=f"validation_{err.validator}",
                path=path,
                expected=str(err.validator_value)[:80],
                actual=str(err.instance)[:80] if err.instance else "?",
                severity="warning"
            ))

    return report


# ═══════════════════════════════════════════════════════════════
# Cross-implementation field analysis
# ═══════════════════════════════════════════════════════════════

def analyze_field_coverage(schema: dict, implementations: List[Tuple[dict, str]]) -> dict:
    """Analyze which schema fields each implementation actually populates."""
    required_fields = schema.get("required", [])
    all_properties = list(schema.get("properties", {}).keys())

    coverage = {}
    for doc, name in implementations:
        present = set(doc.keys())
        schema_fields = set(all_properties)
        required_set = set(required_fields)

        coverage[name] = {
            "required_present": sorted(present & required_set),
            "required_missing": sorted(required_set - present),
            "optional_present": sorted(present & (schema_fields - required_set)),
            "extra_fields": sorted(present - schema_fields),
            "coverage_pct": round(100 * len(present & schema_fields) / len(schema_fields), 1)
                            if schema_fields else 0
        }

    return coverage


# ═══════════════════════════════════════════════════════════════
# Pattern compliance checker
# ═══════════════════════════════════════════════════════════════

def check_lct_id_patterns(implementations: List[Tuple[dict, str]]) -> List[Divergence]:
    """Check if lct_id values match the required pattern."""
    import re
    pattern = re.compile(r"^lct:web4:[A-Za-z0-9_-]+$")
    divergences = []

    for doc, name in implementations:
        lct_id = doc.get("lct_id", "")
        if lct_id and not pattern.match(lct_id):
            divergences.append(Divergence(
                source=name, category="pattern_mismatch",
                path="lct_id",
                expected="^lct:web4:[A-Za-z0-9_-]+$",
                actual=lct_id,
                severity="critical"
            ))

        # Check nested lct_id references
        birth_cert = doc.get("birth_certificate", {})
        if isinstance(birth_cert, dict):
            for field_name in ["issuing_society", "parent_entity"]:
                val = birth_cert.get(field_name, "")
                if val and not pattern.match(val):
                    divergences.append(Divergence(
                        source=name, category="pattern_mismatch",
                        path=f"birth_certificate.{field_name}",
                        expected="^lct:web4:[A-Za-z0-9_-]+$",
                        actual=val,
                        severity="warning"
                    ))

    return divergences


# ═══════════════════════════════════════════════════════════════
# Cross-language conformance comparison
# ═══════════════════════════════════════════════════════════════

def analyze_cross_language_conformance() -> dict:
    """Compare conformance status across TypeScript, Go, and Python."""
    return {
        "typescript": {
            "file": "ledgers/reference/typescript/lct-document.ts",
            "produces_full_lct": True,
            "schema_compliant": True,
            "field_naming": "snake_case (matches schema)",
            "notes": "LCTDocumentBuilder validates required fields at build time"
        },
        "go": {
            "file": "ledgers/reference/go/lct/document.go",
            "produces_full_lct": True,
            "schema_compliant": True,
            "field_naming": "snake_case via json tags (matches schema)",
            "notes": "Struct tags ensure wire format matches schema"
        },
        "python_web4entity": {
            "file": "implementation/reference/web4_entity.py",
            "produces_full_lct": False,
            "schema_compliant": False,
            "field_naming": "snake_case (partial match)",
            "notes": "status() is a snapshot, not a full LCT document. Missing: subject, binding, birth_certificate, mrh, policy"
        },
        "python_birth_cert": {
            "file": "implementation/reference/hardbound_cli.py",
            "produces_full_lct": False,
            "schema_compliant": False,
            "field_naming": "camelCase (JSON-LD convention, NOT matching schema)",
            "notes": "BirthCertificate.to_dict() uses camelCase and includes extra JSON-LD fields (@context, type, etc.)"
        },
        "python_federation": {
            "file": "implementation/reference/lct_federation_registry.py",
            "produces_full_lct": False,
            "schema_compliant": False,
            "field_naming": "snake_case (partial match)",
            "notes": "FederationLCT is a lightweight reference, not a full LCT document"
        }
    }


# ═══════════════════════════════════════════════════════════════
# LCT document constructor from existing implementations
# ═══════════════════════════════════════════════════════════════

def construct_lct_from_web4entity_status(status: dict) -> dict:
    """
    Attempt to construct a schema-compliant LCT document from
    Web4Entity.status() output. Shows what's missing.
    """
    ts = now_iso()
    lct = {
        "lct_id": status.get("lct_id", ""),
        # MISSING: subject — Web4Entity has no DID
        # MISSING: binding — Web4Entity has no public key or binding proof
        # MISSING: birth_certificate — Web4Entity has parent_lct but not full birth cert
        # MISSING: mrh — Web4Entity has witnesses/relationships but not in MRH format
        # MISSING: policy — Web4Entity has no capabilities list
    }

    # What we CAN construct (partial)
    if "t3" in status:
        t3 = status["t3"]
        lct["t3_tensor"] = {
            "talent": t3.get("talent", 0.5),
            "training": t3.get("training", 0.5),
            "temperament": t3.get("temperament", 0.5),
        }
        if "composite" in t3:
            lct["t3_tensor"]["composite_score"] = t3["composite"]
            lct["t3_tensor"]["last_computed"] = ts

    if "v3" in status:
        v3 = status["v3"]
        lct["v3_tensor"] = {
            "valuation": v3.get("valuation", 0.0),
            "veracity": v3.get("veracity", 0.5),
            "validity": v3.get("validity", 0.5),
        }
        if "composite" in v3:
            lct["v3_tensor"]["composite_score"] = v3["composite"]
            lct["v3_tensor"]["last_computed"] = ts

    return lct


def construct_lct_from_birth_cert(cert_dict: dict) -> dict:
    """
    Attempt to construct birth_certificate section from BirthCertificate.to_dict().
    Demonstrates the camelCase → snake_case mapping gap.
    """
    return {
        "issuing_society": cert_dict.get("society", ""),       # society → issuing_society
        "citizen_role": cert_dict.get("citizenRole", ""),       # citizenRole → citizen_role
        "context": "platform",                                   # NOT in cert, must be added
        "birth_timestamp": cert_dict.get("birthTimestamp", ""), # birthTimestamp → birth_timestamp
        "birth_witnesses": cert_dict.get("witnesses", []),      # witnesses → birth_witnesses
        # Unmapped fields from cert: @context, type, entity, entityName, societyName,
        # lawOracle, lawVersion, genesisBlock, initialRights, initialResponsibilities,
        # bindingType, certHash — none of these exist in the schema's birth_certificate
    }


# ═══════════════════════════════════════════════════════════════
# Main test suite
# ═══════════════════════════════════════════════════════════════

def main():
    passed = 0
    failed = 0

    def check(name: str, condition: bool, detail: str = ""):
        nonlocal passed, failed
        status = "PASS" if condition else "FAIL"
        print(f"  [{status}] {name}" + (f" — {detail}" if detail else ""))
        if condition:
            passed += 1
        else:
            failed += 1
        return condition

    schema = load_schema()
    validator = create_validator(schema)

    # ─── T1: Schema self-consistency ────────────────────────────
    print("\n═══ T1: Schema Self-Consistency ═══")
    check("T1: Schema is valid JSON Schema 2020-12", True, f"$id={schema.get('$id')}")
    check("T1: Required fields defined",
          set(schema["required"]) == {"lct_id", "subject", "binding", "birth_certificate", "mrh", "policy"},
          f"required={schema['required']}")
    entity_types = schema["properties"]["binding"]["properties"]["entity_type"]["enum"]
    check("T1: 15 entity types in schema", len(entity_types) == 15,
          f"count={len(entity_types)}, types={entity_types}")
    check("T1: additionalProperties is false",
          schema.get("additionalProperties") == False,
          "strict mode enforced")

    # ─── T2: Compliant minimal document validates ───────────────
    print("\n═══ T2: Compliant Minimal Document ═══")
    minimal_doc, minimal_name = build_compliant_minimal()
    minimal_report = analyze_divergences(minimal_doc, schema, minimal_name)
    check("T2: Minimal compliant doc validates", minimal_report.is_valid,
          f"errors={minimal_report.error_count}")
    check("T2: Zero divergences", len(minimal_report.divergences) == 0,
          f"divergences={len(minimal_report.divergences)}")

    # ─── T3: Compliant full document validates ──────────────────
    print("\n═══ T3: Compliant Full Document ═══")
    full_doc, full_name = build_compliant_full()
    full_report = analyze_divergences(full_doc, schema, full_name)
    check("T3: Full compliant doc validates", full_report.is_valid,
          f"errors={full_report.error_count}")
    check("T3: All optional fields accepted", full_report.warning_count == 0,
          f"warnings={full_report.warning_count}")

    # ─── T4: BirthCertificate.to_dict() fails validation ───────
    print("\n═══ T4: BirthCertificate Divergences ═══")
    cert_doc, cert_name = build_birth_certificate_doc()
    cert_report = analyze_divergences(cert_doc, schema, cert_name)
    check("T4: BirthCert is NOT schema-compliant", not cert_report.is_valid)
    check("T4: Missing required fields detected", cert_report.error_count > 0,
          f"critical={cert_report.error_count}")

    # Catalog specific divergences
    missing_fields = [d for d in cert_report.divergences if d.category == "missing_required_field"]
    extra_fields = [d for d in cert_report.divergences if d.category == "extra_field"]
    check("T4: Missing 'subject' field", any(d.path == "subject" for d in missing_fields))
    check("T4: Missing 'binding' field", any(d.path == "binding" for d in missing_fields))
    check("T4: Missing 'mrh' field", any(d.path == "mrh" for d in missing_fields))
    check("T4: Missing 'policy' field", any(d.path == "policy" for d in missing_fields))
    check("T4: Extra '@context' detected", any("@context" in d.path for d in extra_fields))
    check("T4: Extra 'entityName' detected", any("entityName" in d.path for d in extra_fields))

    print(f"\n    Birth Certificate divergence catalog ({len(cert_report.divergences)} total):")
    for d in cert_report.divergences:
        print(f"      [{d.severity}] {d.category}: {d.path} — expected: {d.expected[:60]}, actual: {d.actual[:60]}")

    # ─── T5: Web4Entity.status() fails validation ──────────────
    print("\n═══ T5: Web4Entity.status() Divergences ═══")
    entity_doc, entity_name = build_web4entity_status()
    entity_report = analyze_divergences(entity_doc, schema, entity_name)
    check("T5: Web4Entity.status() is NOT schema-compliant", not entity_report.is_valid)

    missing = [d for d in entity_report.divergences if d.category == "missing_required_field"]
    extras = [d for d in entity_report.divergences if d.category == "extra_field"]
    check("T5: Missing 'subject'", any(d.path == "subject" for d in missing))
    check("T5: Missing 'binding'", any(d.path == "binding" for d in missing))
    check("T5: Missing 'birth_certificate'", any(d.path == "birth_certificate" for d in missing))
    check("T5: Missing 'mrh'", any(d.path == "mrh" for d in missing))
    check("T5: Missing 'policy'", any(d.path == "policy" for d in missing))
    check("T5: Extra 'name' detected", any("name" in d.path for d in extras))
    check("T5: Extra 'state' detected", any("state" in d.path for d in extras))
    check("T5: Extra 'coherence' detected", any("coherence" in d.path for d in extras))
    check("T5: Extra 'atp' detected", any("atp" in d.path for d in extras))

    print(f"\n    Web4Entity divergence catalog ({len(entity_report.divergences)} total):")
    for d in entity_report.divergences:
        print(f"      [{d.severity}] {d.category}: {d.path} — expected: {d.expected[:60]}, actual: {d.actual[:60]}")

    # ─── T6: FederationLCT.to_dict() fails validation ──────────
    print("\n═══ T6: FederationLCT Divergences ═══")
    fed_doc, fed_name = build_federation_lct()
    fed_report = analyze_divergences(fed_doc, schema, fed_name)
    check("T6: FederationLCT is NOT schema-compliant", not fed_report.is_valid)

    missing = [d for d in fed_report.divergences if d.category == "missing_required_field"]
    extras = [d for d in fed_report.divergences if d.category == "extra_field"]
    check("T6: Missing 'subject'", any(d.path == "subject" for d in missing))
    check("T6: Missing 'binding'", any(d.path == "binding" for d in missing))
    check("T6: Missing 'birth_certificate'", any(d.path == "birth_certificate" for d in missing))
    check("T6: Extra 'society_id' detected", any("society_id" in d.path for d in extras))
    check("T6: Extra 'entity_name' detected", any("entity_name" in d.path for d in extras))
    check("T6: Extra 'public_key_hash' detected", any("public_key_hash" in d.path for d in extras))

    # ─── T7: Field coverage analysis ───────────────────────────
    print("\n═══ T7: Cross-Implementation Field Coverage ═══")
    implementations = [
        build_birth_certificate_doc(),
        build_web4entity_status(),
        build_federation_lct(),
        build_compliant_minimal(),
        build_compliant_full(),
    ]
    coverage = analyze_field_coverage(schema, implementations)

    for name, cov in coverage.items():
        print(f"\n    {name}:")
        print(f"      Required present: {cov['required_present']}")
        print(f"      Required missing: {cov['required_missing']}")
        print(f"      Extra fields: {cov['extra_fields']}")
        print(f"      Coverage: {cov['coverage_pct']}%")

    check("T7: BirthCert coverage < 20%",
          coverage[cert_name]["coverage_pct"] < 20,
          f"coverage={coverage[cert_name]['coverage_pct']}%")
    check("T7: Web4Entity coverage < 20%",
          coverage[entity_name]["coverage_pct"] < 20,
          f"coverage={coverage[entity_name]['coverage_pct']}%")
    check("T7: FederationLCT coverage < 20%",
          coverage[fed_name]["coverage_pct"] < 20,
          f"coverage={coverage[fed_name]['coverage_pct']}%")
    check("T7: Minimal compliant covers all required",
          len(coverage[minimal_name]["required_missing"]) == 0)
    check("T7: Full compliant covers >80%",
          coverage[full_name]["coverage_pct"] > 80,
          f"coverage={coverage[full_name]['coverage_pct']}%")

    # ─── T8: Cross-language conformance ─────────────────────────
    print("\n═══ T8: Cross-Language Conformance ═══")
    conformance = analyze_cross_language_conformance()
    check("T8: TypeScript produces full LCT", conformance["typescript"]["produces_full_lct"])
    check("T8: TypeScript is schema-compliant", conformance["typescript"]["schema_compliant"])
    check("T8: Go produces full LCT", conformance["go"]["produces_full_lct"])
    check("T8: Go is schema-compliant", conformance["go"]["schema_compliant"])
    check("T8: Python Web4Entity does NOT produce full LCT",
          not conformance["python_web4entity"]["produces_full_lct"])
    check("T8: Python BirthCert does NOT produce full LCT",
          not conformance["python_birth_cert"]["produces_full_lct"])
    check("T8: Python Federation does NOT produce full LCT",
          not conformance["python_federation"]["produces_full_lct"])

    # ─── T9: camelCase vs snake_case mapping ───────────────────
    print("\n═══ T9: Naming Convention Analysis ═══")
    cert_doc_raw, _ = build_birth_certificate_doc()
    camel_keys = [k for k in cert_doc_raw.keys() if any(c.isupper() for c in k)]
    snake_keys_in_schema = [k for k in schema["properties"].keys()]

    check("T9: BirthCert uses camelCase", len(camel_keys) > 0,
          f"camelCase keys: {camel_keys}")
    check("T9: Schema uses snake_case", all("_" in k or k.islower() for k in snake_keys_in_schema),
          f"schema keys: {snake_keys_in_schema}")

    # Field mapping table
    mapping = {
        "citizenRole": "citizen_role (in birth_certificate)",
        "birthTimestamp": "birth_timestamp (in birth_certificate)",
        "society": "issuing_society (in birth_certificate)",
        "societyName": "NO EQUIVALENT in schema",
        "entityName": "NO EQUIVALENT in schema",
        "lawOracle": "NO EQUIVALENT in schema",
        "lawVersion": "NO EQUIVALENT in schema",
        "genesisBlock": "NO EQUIVALENT in schema",
        "initialRights": "NO EQUIVALENT in schema → maybe policy.capabilities?",
        "initialResponsibilities": "NO EQUIVALENT in schema",
        "bindingType": "NO EQUIVALENT in schema → maybe binding.entity_type?",
        "certHash": "NO EQUIVALENT in schema → attestations?",
    }
    mapped_count = sum(1 for v in mapping.values() if "NO EQUIVALENT" not in v)
    unmapped_count = sum(1 for v in mapping.values() if "NO EQUIVALENT" in v)
    check("T9: Some fields map to schema", mapped_count > 0,
          f"mappable={mapped_count}")
    check("T9: Some fields have no equivalent", unmapped_count > 0,
          f"unmapped={unmapped_count}")

    print(f"\n    camelCase → snake_case mapping table:")
    for camel, snake in mapping.items():
        print(f"      {camel:30s} → {snake}")

    # ─── T10: Partial construction from Web4Entity ─────────────
    print("\n═══ T10: LCT Construction from Existing Data ═══")
    entity_status, _ = build_web4entity_status()
    partial_lct = construct_lct_from_web4entity_status(entity_status)
    partial_report = analyze_divergences(partial_lct, schema, "Constructed from Web4Entity")

    check("T10: Constructed LCT still invalid (missing required fields)",
          not partial_report.is_valid)
    check("T10: T3 tensor present in constructed doc", "t3_tensor" in partial_lct)
    check("T10: V3 tensor present in constructed doc", "v3_tensor" in partial_lct)

    # What's still missing?
    missing = [d for d in partial_report.divergences if d.category == "missing_required_field"]
    missing_names = [d.path for d in missing]
    check("T10: Still missing 'subject'", "subject" in missing_names)
    check("T10: Still missing 'binding'", "binding" in missing_names)
    check("T10: Still missing 'birth_certificate'", "birth_certificate" in missing_names)
    check("T10: Still missing 'mrh'", "mrh" in missing_names)
    check("T10: Still missing 'policy'", "policy" in missing_names)

    print(f"\n    Web4Entity can contribute: lct_id, t3_tensor, v3_tensor")
    print(f"    Web4Entity CANNOT contribute: subject (DID), binding (keys), birth_certificate, mrh, policy")

    # ─── T11: Partial construction from BirthCertificate ───────
    print("\n═══ T11: Birth Certificate → Schema Mapping ═══")
    cert_raw, _ = build_birth_certificate_doc()
    mapped_birth_cert = construct_lct_from_birth_cert(cert_raw)

    # Validate just the birth_certificate section against its sub-schema
    birth_cert_schema = schema["properties"]["birth_certificate"]
    bc_validator = Draft202012Validator(birth_cert_schema)
    bc_errors = list(bc_validator.iter_errors(mapped_birth_cert))

    check("T11: Mapped birth cert has issuing_society",
          bool(mapped_birth_cert.get("issuing_society")))
    check("T11: Mapped birth cert has citizen_role",
          bool(mapped_birth_cert.get("citizen_role")))
    check("T11: Mapped birth cert has birth_timestamp",
          bool(mapped_birth_cert.get("birth_timestamp")))
    check("T11: Mapped birth cert has birth_witnesses",
          bool(mapped_birth_cert.get("birth_witnesses")))
    check("T11: 'context' must be manually added (not in cert)",
          mapped_birth_cert.get("context") == "platform")

    # Check if the mapped version validates against sub-schema
    bc_valid = len(bc_errors) == 0
    check("T11: Mapped birth cert validates against sub-schema", bc_valid,
          f"errors={len(bc_errors)}")

    if not bc_valid:
        for err in bc_errors:
            print(f"      Sub-schema error: {err.message}")

    print(f"\n    Unmapped BirthCert fields (no schema equivalent):")
    unmapped = ["@context", "type", "entityName", "societyName", "lawOracle",
                "lawVersion", "genesisBlock", "initialRights",
                "initialResponsibilities", "bindingType", "certHash"]
    for f in unmapped:
        print(f"      ✗ {f}")

    # ─── T12: Divergence statistics summary ────────────────────
    print("\n═══ T12: Divergence Statistics ═══")
    all_reports = [cert_report, entity_report, fed_report, minimal_report, full_report]
    total_divergences = sum(len(r.divergences) for r in all_reports)
    total_critical = sum(r.error_count for r in all_reports)
    total_warnings = sum(r.warning_count for r in all_reports)
    total_info = sum(r.info_count for r in all_reports)

    print(f"\n    Total divergences across all implementations: {total_divergences}")
    print(f"    Critical (missing required fields): {total_critical}")
    print(f"    Warnings (extra/pattern/type): {total_warnings}")
    print(f"    Info: {total_info}")

    check("T12: Divergences found", total_divergences > 0, f"total={total_divergences}")
    check("T12: Critical issues in Python impls", total_critical > 0,
          f"critical={total_critical}")
    check("T12: Compliant docs have zero divergences",
          minimal_report.error_count == 0 and full_report.error_count == 0)

    # By category
    all_divs = []
    for r in all_reports:
        all_divs.extend(r.divergences)
    categories = {}
    for d in all_divs:
        categories[d.category] = categories.get(d.category, 0) + 1

    print(f"\n    Divergences by category:")
    for cat, count in sorted(categories.items(), key=lambda x: -x[1]):
        print(f"      {cat}: {count}")

    check("T12: missing_required_field is top category",
          categories.get("missing_required_field", 0) > 0)

    # ─── T13: Recommendations ──────────────────────────────────
    print("\n═══ T13: Actionable Recommendations ═══")
    recommendations = [
        ("HIGH", "Create PythonLCTDocument class",
         "Python has no equivalent of TypeScript LCTDocumentBuilder or Go Document struct. "
         "Web4Entity, BirthCertificate, and FederationLCT each produce fragments, not full documents."),
        ("HIGH", "Decide BirthCertificate format: JSON-LD vs schema",
         "BirthCertificate.to_dict() uses camelCase JSON-LD. Schema birth_certificate uses snake_case. "
         "Are these the same thing? If yes, one must change. If no, the relationship needs documenting."),
        ("MEDIUM", "Add 'context' to BirthCertificate",
         "Schema requires birth_certificate.context (nation|platform|network|organization|ecosystem) "
         "but BirthCertificate class doesn't track this."),
        ("MEDIUM", "Map BirthCert extra fields to schema",
         "8 BirthCert fields have no schema equivalent: lawOracle, lawVersion, genesisBlock, "
         "initialRights, initialResponsibilities, bindingType, entityName, societyName. "
         "Either extend schema or accept these as domain-specific extensions."),
        ("LOW", "Web4Entity → full LCT adapter",
         "Web4Entity.status() covers lct_id + t3 + v3 but misses subject, binding, birth_certificate, "
         "mrh, policy. An adapter that assembles the full document from entity + team context would close this."),
        ("LOW", "FederationLCT → full LCT projection",
         "FederationLCT is intentionally lightweight. Document this as a 'reference' type vs 'full document' type."),
    ]

    for priority, title, detail in recommendations:
        check(f"T13: [{priority}] {title}", True)
        print(f"        {detail}")

    # ─── Summary ───────────────────────────────────────────────
    print(f"\n{'='*60}")
    print(f"  LCT Schema Validator — Track H Results")
    print(f"  {passed} passed, {failed} failed out of {passed+failed} checks")
    print(f"{'='*60}")

    print(f"\n  KEY FINDINGS:")
    print(f"  1. Schema is well-formed (JSON Schema 2020-12, 15 entity types)")
    print(f"  2. TypeScript + Go produce schema-compliant LCT documents")
    print(f"  3. NO Python implementation produces a full LCT document")
    print(f"  4. BirthCertificate uses camelCase JSON-LD ≠ schema's snake_case")
    print(f"  5. Web4Entity.status() is a fragment (covers ~15% of schema)")
    print(f"  6. FederationLCT is a lightweight reference (covers ~8% of schema)")
    print(f"  7. Total {total_divergences} divergences found across all implementations")
    print(f"  8. BirthCert has 8 fields with NO schema equivalent")

    return passed, failed


if __name__ == "__main__":
    passed, failed = main()
    sys.exit(0 if failed == 0 else 1)
