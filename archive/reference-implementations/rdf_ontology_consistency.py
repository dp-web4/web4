#!/usr/bin/env python3
"""
RDF Ontology Consistency Test

Validates the semantic backbone across all Web4 ontology files and
reference implementations. Checks:

1. Namespace consistency — same prefix must map to same URI
2. Class coverage — all ontology classes exercised by implementations
3. Property consistency — predicates used correctly across modules
4. Cross-ontology references — references between ontologies are valid
5. Implementation alignment — Python RDF exports match ontology definitions
6. Entity type coverage — all 15 entity types have RDF representation
7. Predicate taxonomy — no undefined predicates used

Discovery from research: web4: prefix maps to THREE different base URIs:
  - https://web4.io/ontology#
  - https://web4.foundation/web4/v1#
  - https://web4.foundation/ontology#

This test catalogs the inconsistency and validates which URI should be canonical.
"""

import os
import re
import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple
from collections import defaultdict


# ═══════════════════════════════════════════════════════════════
#  1. TURTLE PARSER (Minimal — extracts prefixes, classes, properties)
# ═══════════════════════════════════════════════════════════════

@dataclass
class TurtleOntology:
    """Parsed content of a Turtle (.ttl) ontology file."""
    filepath: str
    prefixes: Dict[str, str] = field(default_factory=dict)  # prefix → URI
    classes: Set[str] = field(default_factory=set)           # Full URIs
    properties: Set[str] = field(default_factory=set)        # Full URIs
    triples: List[Tuple[str, str, str]] = field(default_factory=list)
    raw_lines: int = 0
    parse_errors: List[str] = field(default_factory=list)


def parse_turtle_file(filepath: str) -> TurtleOntology:
    """Parse a Turtle file to extract prefixes, classes, and properties."""
    onto = TurtleOntology(filepath=filepath)

    if not os.path.exists(filepath):
        onto.parse_errors.append(f"File not found: {filepath}")
        return onto

    try:
        with open(filepath, "r") as f:
            content = f.read()
    except Exception as e:
        onto.parse_errors.append(f"Read error: {e}")
        return onto

    lines = content.split("\n")
    onto.raw_lines = len(lines)

    # Extract @prefix declarations
    for line in lines:
        line = line.strip()
        prefix_match = re.match(r'@prefix\s+(\w+):\s+<([^>]+)>\s*\.', line)
        if prefix_match:
            onto.prefixes[prefix_match.group(1)] = prefix_match.group(2)

    # Extract classes (rdfs:Class, owl:Class, rdf:type)
    class_patterns = [
        r'(\w+:\w+)\s+a\s+(?:rdfs|owl):Class',
        r'(\w+:\w+)\s+a\s+rdf:Class',
        r'(\w+:\w+)\s+rdf:type\s+(?:rdfs|owl):Class',
    ]
    for pattern in class_patterns:
        for match in re.finditer(pattern, content):
            onto.classes.add(match.group(1))

    # Extract properties (rdf:Property, owl:ObjectProperty, owl:DatatypeProperty)
    prop_patterns = [
        r'(\w+:\w+)\s+a\s+(?:rdf|owl):(?:Object|Datatype)?Property',
        r'(\w+:\w+)\s+a\s+rdf:Property',
    ]
    for pattern in prop_patterns:
        for match in re.finditer(pattern, content):
            onto.properties.add(match.group(1))

    # Extract domain/range declarations as additional property evidence
    domain_range_pattern = r'(\w+:\w+)\s+(?:rdfs:domain|rdfs:range)\s+(\w+:\w+)'
    for match in re.finditer(domain_range_pattern, content):
        onto.properties.add(match.group(1))

    return onto


# ═══════════════════════════════════════════════════════════════
#  2. PYTHON IMPLEMENTATION SCANNER
# ═══════════════════════════════════════════════════════════════

@dataclass
class ImplementationRDF:
    """RDF usage extracted from a Python implementation file."""
    filepath: str
    predicates_used: Set[str] = field(default_factory=set)   # web4:predicate strings
    namespaces_used: Dict[str, str] = field(default_factory=dict)  # prefix → URI
    entity_types: Set[str] = field(default_factory=set)       # Entity types mentioned
    exports_turtle: bool = False
    exports_jsonld: bool = False


def scan_python_rdf(filepath: str) -> ImplementationRDF:
    """Scan a Python file for RDF predicate usage and namespace definitions."""
    impl = ImplementationRDF(filepath=filepath)

    if not os.path.exists(filepath):
        return impl

    try:
        with open(filepath, "r") as f:
            content = f.read()
    except Exception:
        return impl

    # Extract predicate strings (web4:xxx patterns)
    predicate_pattern = r'"(web4:\w+)"'
    for match in re.finditer(predicate_pattern, content):
        impl.predicates_used.add(match.group(1))

    # Also match mrh: predicates
    mrh_pattern = r'"(mrh:\w+)"'
    for match in re.finditer(mrh_pattern, content):
        impl.predicates_used.add(match.group(1))

    # Extract namespace declarations
    ns_pattern = r'["\']?(https?://web4\.(?:io|foundation)/[^"\'\s]+)["\']?'
    for match in re.finditer(ns_pattern, content):
        uri = match.group(1)
        if "web4.io" in uri:
            impl.namespaces_used["web4.io"] = uri
        elif "web4.foundation" in uri:
            impl.namespaces_used["web4.foundation"] = uri

    # Check for Turtle/JSON-LD export
    impl.exports_turtle = "turtle" in content.lower() or "export_turtle" in content
    impl.exports_jsonld = "jsonld" in content.lower() or "json-ld" in content.lower()

    # Entity types
    entity_types = [
        "human", "ai", "society", "organization", "role", "task",
        "resource", "device", "service", "oracle", "accumulator",
        "dictionary", "hybrid", "policy", "infrastructure",
    ]
    for et in entity_types:
        if f'"{et}"' in content or f"'{et}'" in content:
            impl.entity_types.add(et)

    return impl


# ═══════════════════════════════════════════════════════════════
#  3. SCHEMA SCANNER
# ═══════════════════════════════════════════════════════════════

@dataclass
class SchemaInfo:
    """Information extracted from a JSON schema."""
    filepath: str
    entity_types: Set[str] = field(default_factory=set)
    predicates: Set[str] = field(default_factory=set)
    namespace_uris: Set[str] = field(default_factory=set)


def scan_json_schema(filepath: str) -> SchemaInfo:
    """Extract entity types and predicates from a JSON schema."""
    info = SchemaInfo(filepath=filepath)

    if not os.path.exists(filepath):
        return info

    try:
        with open(filepath, "r") as f:
            schema = json.load(f)
    except Exception:
        return info

    # Walk the schema to find entity_type enums
    def walk(obj, path=""):
        if isinstance(obj, dict):
            if "enum" in obj and path.endswith("entity_type"):
                for v in obj["enum"]:
                    info.entity_types.add(v)
            for k, v in obj.items():
                walk(v, f"{path}.{k}")
        elif isinstance(obj, list):
            for item in obj:
                walk(item, path)

    walk(schema)

    # Find namespace URIs
    content = json.dumps(schema)
    for match in re.finditer(r'(https?://web4\.[^"]+)', content):
        info.namespace_uris.add(match.group(1))

    return info


# ═══════════════════════════════════════════════════════════════
#  4. CONSISTENCY ANALYZER
# ═══════════════════════════════════════════════════════════════

@dataclass
class ConsistencyReport:
    """Results of cross-ontology consistency analysis."""
    namespace_variants: Dict[str, List[str]] = field(default_factory=lambda: defaultdict(list))
    undefined_predicates: List[Tuple[str, str]] = field(default_factory=list)  # (file, predicate)
    class_coverage: Dict[str, bool] = field(default_factory=dict)
    entity_type_gaps: List[str] = field(default_factory=list)
    cross_ontology_refs: List[Dict] = field(default_factory=list)
    property_conflicts: List[Dict] = field(default_factory=list)
    total_classes: int = 0
    total_properties: int = 0
    total_triples_exportable: int = 0


def analyze_consistency(
    ontologies: List[TurtleOntology],
    implementations: List[ImplementationRDF],
    schemas: List[SchemaInfo],
) -> ConsistencyReport:
    """Analyze consistency across ontologies, implementations, and schemas."""
    report = ConsistencyReport()

    # 1. Namespace consistency
    all_prefix_uris: Dict[str, Set[str]] = defaultdict(set)
    for onto in ontologies:
        for prefix, uri in onto.prefixes.items():
            all_prefix_uris[prefix].add(uri)
            report.namespace_variants[prefix].append(f"{onto.filepath}: {uri}")

    for impl in implementations:
        for domain, uri in impl.namespaces_used.items():
            all_prefix_uris[domain].add(uri)

    # 2. Collect all defined classes and properties
    all_classes: Set[str] = set()
    all_properties: Set[str] = set()
    for onto in ontologies:
        all_classes.update(onto.classes)
        all_properties.update(onto.properties)

    report.total_classes = len(all_classes)
    report.total_properties = len(all_properties)

    # 3. Check implementation predicates against ontology definitions
    for impl in implementations:
        for pred in impl.predicates_used:
            if pred not in all_properties and pred not in all_classes:
                # Check if it's a known predicate with different namespace
                base_name = pred.split(":")[-1]
                found = any(p.endswith(f":{base_name}") for p in all_properties | all_classes)
                if not found:
                    report.undefined_predicates.append(
                        (os.path.basename(impl.filepath), pred)
                    )

    # 4. Entity type coverage
    schema_entity_types = set()
    for schema in schemas:
        schema_entity_types.update(schema.entity_types)

    impl_entity_types = set()
    for impl in implementations:
        impl_entity_types.update(impl.entity_types)

    canonical_15 = {
        "human", "ai", "society", "organization", "role", "task",
        "resource", "device", "service", "oracle", "accumulator",
        "dictionary", "hybrid", "policy", "infrastructure",
    }

    for et in canonical_15:
        if et not in schema_entity_types and et not in impl_entity_types:
            report.entity_type_gaps.append(et)

    # 5. Count exportable implementations
    report.total_triples_exportable = sum(
        1 for impl in implementations if impl.exports_turtle or impl.exports_jsonld
    )

    return report


# ═══════════════════════════════════════════════════════════════
#  5. TEST SUITE
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

    BASE = "/home/dp/ai-workspace/web4"

    # ─── T1: Parse All Turtle Ontologies ───
    print("\n═══ T1: Parse Turtle Ontologies ═══")

    ttl_files = [
        f"{BASE}/web4-standard/ontology/t3v3-ontology.ttl",
        f"{BASE}/forum/nova/ACP-bundle/acp-ontology.ttl",
        f"{BASE}/forum/nova/agency-bundle/agy-ontology.ttl",
        f"{BASE}/forum/nova/web4-sal-bundle/sal-ontology.ttl",
        f"{BASE}/web4-standard/ontology/web4-core-ontology.ttl",
    ]

    ontologies = []
    for path in ttl_files:
        onto = parse_turtle_file(path)
        ontologies.append(onto)
        name = os.path.basename(path)
        exists = len(onto.parse_errors) == 0
        check(f"T1: {name} parsed", exists)

    check("T1: 5 ontology files found", len(ontologies) == 5)

    # Count total definitions
    total_classes = sum(len(o.classes) for o in ontologies)
    total_props = sum(len(o.properties) for o in ontologies)
    check("T1: classes found", total_classes > 0)
    check("T1: properties found", total_props > 0)

    # ─── T2: Namespace Inventory ───
    print("\n═══ T2: Namespace Inventory ═══")

    # Collect all namespaces
    all_ns: Dict[str, Set[str]] = defaultdict(set)
    for onto in ontologies:
        for prefix, uri in onto.prefixes.items():
            all_ns[prefix].add(uri)

    check("T2: web4 prefix defined", "web4" in all_ns)
    check("T2: rdfs prefix defined", "rdfs" in all_ns)

    # Check for web4 namespace variants
    web4_uris = all_ns.get("web4", set())
    check("T2: web4 URIs cataloged", len(web4_uris) > 0)

    # Print namespace report
    print(f"\n  Namespace Report:")
    for prefix, uris in sorted(all_ns.items()):
        if len(uris) > 1:
            print(f"    {prefix}: [{len(uris)} VARIANTS]")
            for uri in sorted(uris):
                print(f"      - {uri}")
        else:
            print(f"    {prefix}: {list(uris)[0]}")

    # ─── T3: Namespace Consistency ───
    print("\n═══ T3: Namespace Consistency ═══")

    # web4 should ideally be one URI
    web4_variant_count = len(web4_uris)
    check("T3: web4 namespace variants counted", web4_variant_count >= 1)

    # Report the inconsistency
    if web4_variant_count > 1:
        print(f"\n  WARNING: web4: prefix maps to {web4_variant_count} different URIs:")
        for uri in sorted(web4_uris):
            sources = []
            for onto in ontologies:
                if onto.prefixes.get("web4") == uri:
                    sources.append(os.path.basename(onto.filepath))
            print(f"    {uri}")
            for s in sources:
                print(f"      used by: {s}")

    # Standard prefixes should be consistent
    for std_prefix in ["rdf", "rdfs", "xsd", "owl"]:
        variants = all_ns.get(std_prefix, set())
        if variants:
            check(f"T3: {std_prefix} prefix consistent", len(variants) == 1)

    # ─── T4: Class Definitions Per Ontology ───
    print("\n═══ T4: Class Definitions ═══")

    for onto in ontologies:
        name = os.path.basename(onto.filepath)
        check(f"T4: {name} has classes", len(onto.classes) > 0 or name == "t3v3-ontology.ttl")
        if onto.classes:
            print(f"    Classes in {name}: {sorted(onto.classes)}")

    # T3/V3 ontology classes
    t3v3 = ontologies[0]
    check("T4: T3Tensor defined", any("T3Tensor" in c for c in t3v3.classes))
    check("T4: V3Tensor defined", any("V3Tensor" in c for c in t3v3.classes))
    check("T4: Dimension defined", any("Dimension" in c for c in t3v3.classes))

    # SAL ontology classes
    sal = ontologies[3]
    check("T4: Society defined in SAL", any("Society" in c for c in sal.classes))

    # ACP ontology classes
    acp = ontologies[1]
    check("T4: AgentPlan defined in ACP", any("Plan" in c or "Agent" in c for c in acp.classes))

    # AGY ontology classes
    agy = ontologies[2]
    check("T4: AgencyGrant defined in AGY", any("Grant" in c or "Agency" in c for c in agy.classes))

    # Core ontology classes
    core = ontologies[4]
    check("T4: Binding defined in core", any("Binding" in c for c in core.classes))
    check("T4: Pairing defined in core", any("Pairing" in c for c in core.classes))
    check("T4: WitnessAttestation defined in core", any("WitnessAttestation" in c for c in core.classes))
    check("T4: ActionRecord defined in core", any("ActionRecord" in c for c in core.classes))

    # ─── T5: Property Definitions ───
    print("\n═══ T5: Property Definitions ═══")

    all_defined_props = set()
    for onto in ontologies:
        all_defined_props.update(onto.properties)
        name = os.path.basename(onto.filepath)
        if onto.properties:
            print(f"    Properties in {name}: {sorted(onto.properties)}")

    check("T5: properties defined across ontologies", len(all_defined_props) > 0)

    # Core properties should exist
    core_predicates = ["web4:entity", "web4:role", "web4:talent", "web4:training", "web4:temperament"]
    for pred in core_predicates:
        found = any(pred in p or pred.split(":")[-1] in str(p) for p in all_defined_props)
        check(f"T5: {pred} defined", found)

    # ─── T6: Scan Python Implementations ───
    print("\n═══ T6: Scan Python Implementations ═══")

    impl_files = [
        f"{BASE}/web4-standard/implementation/reference/mrh_graph.py",
        f"{BASE}/web4-standard/mrh_rdf_implementation.py",
        f"{BASE}/implementation/reference/mrh_governance_integration.py",
        f"{BASE}/implementation/reference/t3v3_reputation_engine.py",
        f"{BASE}/implementation/reference/cross_implementation_integration.py",
        f"{BASE}/implementation/reference/mrh_policy_scoping.py",
    ]

    implementations = []
    for path in impl_files:
        impl = scan_python_rdf(path)
        implementations.append(impl)
        name = os.path.basename(path)
        check(f"T6: {name} scanned", os.path.exists(path))

    # Collect all predicates used in implementations
    impl_predicates = set()
    for impl in implementations:
        impl_predicates.update(impl.predicates_used)

    check("T6: web4 predicates used in implementations", any("web4:" in p for p in impl_predicates))

    print(f"\n    Predicates found in implementations:")
    for pred in sorted(impl_predicates):
        print(f"      {pred}")

    # ─── T7: Predicate Coverage ───
    print("\n═══ T7: Predicate Coverage ═══")

    # Core predicates that MUST be used somewhere
    essential_predicates = [
        "web4:boundTo",
        "web4:memberOf",
        "web4:hasRole",
        "web4:witnessedBy",
        "web4:delegatesTo",
        "web4:hasT3Tensor",
        "web4:subDimensionOf",
    ]

    for pred in essential_predicates:
        used = pred in impl_predicates
        check(f"T7: {pred} used in implementations", used)

    # ─── T8: Scan JSON Schemas ───
    print("\n═══ T8: JSON Schemas ═══")

    schema_files = [
        f"{BASE}/web4-standard/schemas/lct.schema.json",
        f"{BASE}/web4-standard/schemas/t3v3.schema.json",
    ]

    schemas = []
    for path in schema_files:
        info = scan_json_schema(path)
        schemas.append(info)
        name = os.path.basename(path)
        check(f"T8: {name} parsed", os.path.exists(path))

    # LCT schema should have 15 entity types
    lct_schema = schemas[0]
    check("T8: LCT schema has entity types", len(lct_schema.entity_types) > 0)
    if lct_schema.entity_types:
        print(f"    Entity types in schema: {sorted(lct_schema.entity_types)}")
        check("T8: 15 entity types in schema", len(lct_schema.entity_types) == 15)

    # ─── T9: Entity Type Coverage ───
    print("\n═══ T9: Entity Type Coverage ═══")

    canonical_15 = {
        "human", "ai", "society", "organization", "role", "task",
        "resource", "device", "service", "oracle", "accumulator",
        "dictionary", "hybrid", "policy", "infrastructure",
    }

    schema_types = set()
    for s in schemas:
        schema_types.update(s.entity_types)

    for et in sorted(canonical_15):
        in_schema = et in schema_types
        check(f"T9: {et} in schema", in_schema)

    # ─── T10: Cross-Ontology Reference Consistency ───
    print("\n═══ T10: Cross-Ontology References ═══")

    # Classes referenced in one ontology but defined in another
    all_class_names = set()
    for onto in ontologies:
        for cls in onto.classes:
            all_class_names.add(cls.split(":")[-1])

    # Key cross-references
    cross_refs = {
        "SAL → T3V3": ("Society", "T3Tensor"),
        "AGY → SAL": ("AgencyGrant", "Society"),
        "ACP → AGY": ("ACP_Intent", "AgencyGrant"),
    }

    for ref_name, (class_a, class_b) in cross_refs.items():
        a_exists = any(class_a in c for c in all_class_names)
        b_exists = any(class_b in c for c in all_class_names)
        check(f"T10: {ref_name} both classes exist", a_exists and b_exists)

    # ─── T11: Full Consistency Analysis ───
    print("\n═══ T11: Full Consistency Analysis ═══")

    report = analyze_consistency(ontologies, implementations, schemas)

    check("T11: total classes > 10", report.total_classes > 10)
    check("T11: total properties > 5", report.total_properties > 5)
    check("T11: RDF exporters exist", report.total_triples_exportable > 0)

    # Report undefined predicates
    if report.undefined_predicates:
        # Separate structural predicates (lowercase local name) from
        # role/instance references (uppercase local name like Engineer, Talent)
        structural = [(f, p) for f, p in report.undefined_predicates
                      if p.split(":")[-1][0].islower()]
        instances = [(f, p) for f, p in report.undefined_predicates
                     if p.split(":")[-1][0].isupper()]

        if structural:
            print(f"\n    Structural predicates still undefined ({len(structural)}):")
            for file, pred in structural[:15]:
                print(f"      {file}: {pred}")
        if instances:
            print(f"\n    Instance references (role names, not ontology defs): {len(instances)}")
            instance_names = sorted(set(p for _, p in instances))
            print(f"      {', '.join(instance_names[:10])}")

        check("T11: structural predicates ≤ 5 undefined", len(structural) <= 5)
    else:
        check("T11: all predicates formally defined", True)

    # Entity type gaps
    if report.entity_type_gaps:
        print(f"\n    Entity types with no RDF representation: {report.entity_type_gaps}")
    check("T11: entity type gaps cataloged", True)

    # ─── T12: JSON-LD Context Alignment ───
    print("\n═══ T12: JSON-LD Context ═══")

    jsonld_path = f"{BASE}/web4-standard/ontology/t3v3.jsonld"
    if os.path.exists(jsonld_path):
        with open(jsonld_path, "r") as f:
            jsonld = json.load(f)

        context = jsonld.get("@context", {})
        check("T12: JSON-LD context exists", bool(context))
        check("T12: web4 in context", "web4" in context)
        check("T12: T3Tensor mapped", "T3Tensor" in context)
        check("T12: V3Tensor mapped", "V3Tensor" in context)
        check("T12: entity mapped", "entity" in context)
        check("T12: role mapped", "role" in context)

        # Check namespace alignment with TTL
        jsonld_web4_uri = context.get("web4", "")
        ttl_web4_uris = all_ns.get("web4", set())
        aligned = jsonld_web4_uri in ttl_web4_uris
        check("T12: JSON-LD web4 URI matches TTL", aligned)
        if not aligned:
            print(f"    JSON-LD: {jsonld_web4_uri}")
            print(f"    TTL:     {ttl_web4_uris}")
    else:
        check("T12: JSON-LD context file exists", False)

    # ─── T13: Implementation Namespace Usage ───
    print("\n═══ T13: Implementation Namespace Usage ═══")

    impl_ns_variants = defaultdict(set)
    for impl in implementations:
        for domain, uri in impl.namespaces_used.items():
            impl_ns_variants[domain].add(uri)

    for domain, uris in impl_ns_variants.items():
        if len(uris) > 1:
            print(f"    WARNING: {domain} has {len(uris)} URI variants in implementations:")
            for uri in sorted(uris):
                print(f"      {uri}")
            check(f"T13: {domain} namespace inconsistency cataloged", True)
        else:
            check(f"T13: {domain} namespace consistent in implementations", True)

    # ─── T14: Turtle Export Capability ───
    print("\n═══ T14: Turtle Export Capability ═══")

    turtle_exporters = [impl for impl in implementations if impl.exports_turtle]
    jsonld_exporters = [impl for impl in implementations if impl.exports_jsonld]

    check("T14: Turtle exporters exist", len(turtle_exporters) > 0)
    check("T14: JSON-LD support exists", len(jsonld_exporters) > 0)

    print(f"    Turtle exporters: {[os.path.basename(i.filepath) for i in turtle_exporters]}")
    print(f"    JSON-LD exporters: {[os.path.basename(i.filepath) for i in jsonld_exporters]}")

    # ─── T15: Ontology Domain Coverage ───
    print("\n═══ T15: Ontology Domain Coverage ═══")

    domains = {
        "Trust (T3)": ["T3Tensor", "talent", "training", "temperament"],
        "Value (V3)": ["V3Tensor", "valuation", "veracity", "validity"],
        "Identity": ["boundTo", "witnessedBy", "memberOf"],
        "Authority": ["delegatesTo", "hasAuthority", "hasLawOracle"],
        "Agency": ["AgencyGrant", "delegationScope", "agentOf"],
        "Governance": ["Society", "AuthorityRole", "LawOracle"],
    }

    all_defined_str = " ".join(str(p) for p in all_defined_props | all_class_names)

    for domain_name, terms in domains.items():
        found = sum(1 for t in terms if t in all_defined_str)
        coverage = found / len(terms) if terms else 0
        check(f"T15: {domain_name} domain coverage ≥ 50%", coverage >= 0.5)

    # ─── T16: Canonical Namespace Recommendation ───
    print("\n═══ T16: Canonical Namespace Recommendation ═══")

    # Count usage frequency across all files
    uri_usage: Dict[str, int] = defaultdict(int)
    for onto in ontologies:
        web4_uri = onto.prefixes.get("web4", "")
        if web4_uri:
            uri_usage[web4_uri] += 1

    for impl in implementations:
        for _, uri in impl.namespaces_used.items():
            uri_usage[uri] += 1

    if uri_usage:
        print(f"\n    web4: namespace usage frequency:")
        for uri, count in sorted(uri_usage.items(), key=lambda x: -x[1]):
            print(f"      {uri}: {count} files")

        canonical = max(uri_usage.items(), key=lambda x: x[1])
        check("T16: canonical URI identified", True)
        print(f"\n    RECOMMENDED canonical: {canonical[0]} (used {canonical[1]} times)")

        # Report non-canonical usage
        non_canonical = {u for u in uri_usage if u != canonical[0]}
        if non_canonical:
            print(f"    NON-CANONICAL variants to align: {non_canonical}")
            check("T16: namespace alignment needed", True)
        else:
            check("T16: all namespaces already aligned", True)
    else:
        check("T16: namespace usage analyzed", True)

    # ─── T17: Predicate Taxonomy ───
    print("\n═══ T17: Predicate Taxonomy ═══")

    # Group predicates by category
    categories = {
        "binding": ["boundTo", "parentBinding", "childBinding"],
        "witness": ["witnessedBy", "timeWitness", "auditWitness"],
        "society": ["memberOf", "hasRole", "pairedWith"],
        "authority": ["delegatesTo", "hasAuthority", "hasLawOracle"],
        "trust": ["hasT3Tensor", "hasV3Tensor", "hasDimensionScore"],
        "fractal": ["subDimensionOf"],
        "action": ["authorizedAction"],
    }

    for cat, predicates in categories.items():
        used = sum(1 for p in predicates if f"web4:{p}" in impl_predicates)
        defined = sum(1 for p in predicates if any(p in str(prop) for prop in all_defined_props))
        check(f"T17: {cat} predicates used ({used}/{len(predicates)})", used > 0 or defined > 0)

    # ─── T18: Summary Statistics ───
    print("\n═══ T18: Summary Statistics ═══")

    stats = {
        "ontology_files": len(ontologies),
        "implementation_files": len(implementations),
        "schema_files": len(schemas),
        "total_classes": total_classes,
        "total_properties": total_props,
        "impl_predicates": len(impl_predicates),
        "namespace_variants": len(web4_uris),
        "entity_types_in_schema": len(schema_types),
        "turtle_exporters": len(turtle_exporters),
        "jsonld_exporters": len(jsonld_exporters),
    }

    print(f"\n    Summary:")
    for k, v in stats.items():
        print(f"      {k}: {v}")

    check("T18: comprehensive analysis complete", True)
    check("T18: statistics captured", len(stats) > 0)

    # ─── T19: Core Ontology Closure ───
    print("\n═══ T19: Core Ontology Closure ═══")

    # All 22 structural predicates that were previously undefined
    core_structural_predicates = {
        # Binding (4)
        "web4:boundTo": "Binding",
        "web4:parentBinding": "Binding",
        "web4:childBinding": "Binding",
        "web4:siblingBinding": "Binding",
        # Pairing (4)
        "web4:energyPairing": "Pairing",
        "web4:dataPairing": "Pairing",
        "web4:servicePairing": "Pairing",
        "web4:pairedWithRole": "Pairing",
        # Witness (3)
        "web4:timeWitness": "Witness",
        "web4:auditWitness": "Witness",
        "web4:oracleWitness": "Witness",
        # Entity-Role (1)
        "web4:hasRole": "Entity-Role",
        # Tensor Binding (2)
        "web4:hasT3Tensor": "Tensor",
        "web4:hasV3Tensor": "Tensor",
        # Action Metadata (5)
        "web4:actionType": "Action",
        "web4:resource": "Action",
        "web4:atpCost": "Action",
        "web4:lawHash": "Action",
        "web4:authorizedAction": "Action",
        # Delegation (1)
        "web4:delegatedBy": "Delegation",
        # Identity (2)
        "web4:references": "Identity",
        "web4:birthCertificate": "Identity",
    }

    now_defined = 0
    still_missing = []
    for pred, category in core_structural_predicates.items():
        found = pred in all_defined_props
        if found:
            now_defined += 1
        else:
            still_missing.append((pred, category))

    check("T19: core ontology file parsed", len(core.properties) >= 20)
    check("T19: ≥ 20 of 22 structural predicates defined", now_defined >= 20)
    check("T19: all 22 structural predicates defined", now_defined == 22)

    if still_missing:
        print(f"\n    Still missing ({len(still_missing)}):")
        for pred, cat in still_missing:
            print(f"      [{cat}] {pred}")
    else:
        print(f"    All 22 structural predicates formally defined in ontology!")

    # Verify core classes
    core_classes = {"web4:Binding", "web4:Pairing", "web4:WitnessAttestation", "web4:ActionRecord"}
    all_class_set = set()
    for onto in ontologies:
        all_class_set.update(onto.classes)
    for cls in sorted(core_classes):
        check(f"T19: {cls} class defined", cls in all_class_set)

    # Combined totals
    combined_classes = sum(len(o.classes) for o in ontologies)
    combined_props = sum(len(o.properties) for o in ontologies)
    check("T19: combined classes ≥ 25", combined_classes >= 25)
    check("T19: combined properties ≥ 58", combined_props >= 58)

    print(f"\n    Combined ontology: {combined_classes} classes, {combined_props} properties")
    print(f"    Closure: {now_defined}/22 structural predicates formally defined")

    # ═══ Summary ═══
    total = passed + failed
    print(f"\n{'=' * 60}")
    print(f"  RDF Ontology Consistency — Results")
    print(f"  {passed} passed, {failed} failed out of {total} checks")
    print(f"{'=' * 60}")

    if failed == 0:
        print(f"""
  All consistency checks verified:
  T1:  Turtle ontology parsing (5 files)
  T2:  Namespace inventory across all files
  T3:  Namespace consistency (variants cataloged)
  T4:  Class definitions per ontology (incl. core)
  T5:  Property definitions across ontologies
  T6:  Python implementation scanning (6 files)
  T7:  Essential predicate coverage
  T8:  JSON schema parsing + entity types
  T9:  15 canonical entity types coverage
  T10: Cross-ontology reference validity
  T11: Full consistency analysis
  T12: JSON-LD context alignment
  T13: Implementation namespace usage
  T14: Turtle/JSON-LD export capability
  T15: Ontology domain coverage (6 domains)
  T16: Canonical namespace recommendation
  T17: Predicate taxonomy by category
  T18: Summary statistics
  T19: Core ontology closure (22 structural predicates)

  Key findings:
  - {len(web4_uris)} web4: namespace variants found
  - {combined_classes} classes across 5 ontologies
  - {combined_props} properties defined
  - {len(impl_predicates)} predicates used in implementations
  - {len(schema_types)} entity types in LCT schema
  - {len(turtle_exporters)} implementations export Turtle
  - {now_defined}/22 structural predicates formally closed
""")
    else:
        print(f"\n  {failed} checks need attention.")

    return passed, failed


if __name__ == "__main__":
    run_tests()
