# Cross-Repo Import Target Analysis

**Date**: 2026-04-19
**Authorized by**: Issue #166 candidate (a)-3
**Sprint**: 43 T2
**Scope**: Identify which web4 module(s) hardbound and/or 4-life would benefit from
importing but currently don't. Analysis only — no code changes.

---

## 1. Current State: What Web4 Ships Cross-Language

The web4 repository contains three layers of cross-language artifacts:

### A. JSON Schemas (language-neutral)

12 JSON Schema files in `web4-standard/schemas/`:

| Schema | Validates |
|--------|-----------|
| `lct.schema.json` | LCT core structure |
| `lct-jsonld.schema.json` | LCT JSON-LD documents |
| `t3v3.schema.json` | T3/V3 tensor structure |
| `t3v3-jsonld.schema.json` | T3/V3 JSON-LD documents |
| `atp-jsonld.schema.json` | ATP/ADP JSON-LD |
| `acp-jsonld.schema.json` | ACP JSON-LD |
| `entity-jsonld.schema.json` | Entity JSON-LD |
| `capability-jsonld.schema.json` | Capability JSON-LD |
| `dictionary-jsonld.schema.json` | Dictionary JSON-LD |
| `r7-action-jsonld.schema.json` | R7 Action JSON-LD |
| `attestation-envelope-jsonld.schema.json` | Attestation Envelope JSON-LD |
| `trust-query.schema.json` | Trust Query structure |

These are also bundled as `schema_registry.json` inside the Python SDK package.

### B. JSON-LD Context Files (language-neutral)

10 context files in `web4-standard/schemas/contexts/` defining the `https://web4.io/ns/`
namespace for all core types (LCT, T3, V3, ATP, ACP, Entity, Capability, Dictionary,
R7 Action, Attestation Envelope).

### C. Ontology (language-neutral)

2 Turtle files in `web4-standard/ontology/`:
- `web4-core-ontology.ttl` — core classes and predicates
- `t3v3-ontology.ttl` — trust/value tensor dimension hierarchy

### D. Rust Crates (multi-target)

Two Rust crates provide compiled bindings:

**`web4-core/`** — Core types library
- Types: LCT, T3, V3, Coherence, crypto primitives
- Features: `python` (PyO3 bindings)
- Status: v0.1.0, linked by hardbound via optional feature flag

**`web4-trust-core/`** — Runtime trust engine
- Types: EntityTrust, T3Tensor, V3Tensor, TrustStore, witnessing, decay
- Features: `python` (PyO3), `wasm` (wasm-bindgen), `file-store`, `sled-store`
- Status: v0.1.0, WASM output (66KB) is deployed in 4-life
- Builds to: native library, Python extension, WASM module

### E. Python SDK (Python-only)

`web4` package (v0.26.0): 22 modules, 364 exports, 2613 tests. Behavioral functions
(`evaluate_trust_query`, `resolve_trust`, `process_action_outcome`), MCP server,
CLI, JSON-LD serialization/deserialization, schema validation.

---

## 2. Consumer Analysis

### 4-life (Public — Next.js/TypeScript)

**Relationship to web4**: Interactive explainer, browser-deployed.

**What it currently imports from web4**:
- `web4-trust-core` WASM binary (`web4_trust_core_bg.wasm`, 66KB) providing
  EntityTrust, T3Tensor, V3Tensor, and WasmTrustStore for browser-side trust
  calculations. Loaded via `src/lib/web4-trust.ts` wrapper.

**What it re-implements independently**:
- Single-agent simulation engine (633 lines TS) — ATP budget, trust dynamics,
  karma carry-forward, epistemic proprioception, coherence index
- Multi-agent society engine (1,575 lines TS) — game-theoretic interactions,
  coalition formation, reputation weighting, 6 agent strategies
- Federation market simulator — ATP supply/demand pricing
- Narrative generation — event detection, story generation, export
- Type definitions — AgentState, ActionRecord, LifeCycle, SimulationResult
- Glossary terms (235 lines of hardcoded definitions)

**What it does NOT import but could**:
1. **JSON Schemas** — 4-life generates trust/entity documents but never validates
   them against the canonical schemas. No npm package exists to import.
2. **JSON-LD context files** — 4-life references web4 concepts but doesn't use
   the canonical `@context` documents for semantic precision.
3. **TypeScript type definitions** — 4-life defines its own TS types for T3/V3/ATP/LCT
   that are structurally similar but not schema-derived.

**What it SHOULD NOT import**:
- The Python SDK (wrong language, server-side only)
- Simulation engines (4-life's simulations are explainer-specific, not generic)

### Hardbound (Private — TypeScript + Rust)

**Relationship to web4**: Enterprise product, deploys web4 ontology in production.

**What it currently imports from web4**:
- `web4-core` Rust crate via optional feature flag with path dependency.
  Interop layer provides bidirectional type conversion (TrustTensor/T3,
  EntityType mapping, CoherenceMetrics/Coherence).

**What it re-implements independently**:
- TypeScript ports of reference implementations (trust computation, LCT
  authorization, RDF ontology validation, ATP accounting, sybil resistance)
- Independent T3/V3 tensor implementations in both TypeScript and Rust
- Full audit, ledger, policy, and governance infrastructure

**What it does NOT import but could**:
1. **JSON Schemas for validation** — hardbound implements its own validation
   rather than using the canonical schemas as a shared contract.
2. **TypeScript types from schemas** — hardbound's TypeScript types are hand-written
   ports. Generated types from the canonical JSON Schemas would ensure alignment.

**What it SHOULD NOT import**:
- The Python SDK (wrong runtime)
- web4-trust-core WASM (hardbound has native Rust access; WASM adds overhead)

---

## 3. Gap Analysis: Why Consumers Don't Import More

### The language barrier

The web4 Python SDK (v0.26.0) is the most complete artifact — 22 modules, 364
exports, behavioral functions, MCP server. But its consumers are TypeScript (both
4-life and hardbound) and Rust (hardbound). A Python package can't be `import`-ed
from TypeScript or `use`-d from Rust.

### What's already bridged

The Rust crates (`web4-core`, `web4-trust-core`) successfully bridge the language
gap for **type-level** concerns. 4-life uses the WASM output; hardbound uses the
native Rust library. This is a working pattern.

### What's NOT bridged: the schema layer

The 12 JSON Schemas and 10 JSON-LD context files are language-neutral by design —
they're JSON documents that any language can consume. But they're not **packaged**
for consumption:

- No **npm package** publishes the schemas for TypeScript/JavaScript consumers
- No **TypeScript type definitions** are generated from the schemas
- No **crate** exposes the schemas for Rust consumers (though `web4-core` provides
  hand-written Rust types that align with them)
- The schemas sit in `web4-standard/schemas/` and are copied manually or referenced
  by file path when needed

Both consumers work around this by writing their own types and validation. This
produces **drift risk**: when the schema evolves, consumers may not notice.

---

## 4. Recommendation: Highest-Value Import Target

### Publish JSON Schemas as an npm package

**What**: Create `@web4/schemas` (or similar) npm package containing:
1. All 12 JSON Schema files as importable JSON modules
2. All 10 JSON-LD context files
3. Generated TypeScript type definitions from the schemas (via `json-schema-to-typescript` or equivalent)
4. A simple `validate(type, document)` function wrapping `ajv` or similar

**Why this is the highest-value target**:
1. **Both consumers are TypeScript** — an npm package is directly importable by
   both 4-life and hardbound's TypeScript layers
2. **Schemas already exist** — no new specification work needed, only packaging
3. **Eliminates drift** — consumers validate against the same schemas the Python
   SDK uses, ensuring cross-language document compatibility
4. **Generated types > hand-written types** — TypeScript types derived from the
   canonical schemas are guaranteed to match; hand-written ports can diverge
5. **Low risk** — schemas are the most stable layer (they define the wire format
   that all implementations must agree on)

**Why NOT the alternatives**:
- *Publishing web4-trust-core to crates.io/npm*: Already works via WASM for 4-life
  and path dependency for hardbound. Publishing would help third parties but doesn't
  solve the current cross-repo gap.
- *Porting behavioral functions to TypeScript*: High effort, duplicates the Python
  SDK's most complex logic, and behavioral functions are less stable than schemas.
- *Publishing the Python SDK to PyPI*: Only helps Python consumers (which both
  consumers are not for their primary codepaths).

### Concrete next step

A single bounded sprint task:

1. Create `web4-standard/packages/schemas/` with `package.json`
2. Copy (or symlink) the 12 JSON Schema files and 10 context files
3. Run `json-schema-to-typescript` to generate `.d.ts` files
4. Add a minimal `validate.ts` wrapping `ajv`
5. Publish to npm as `@web4/schemas` (or use as path dependency initially)

Estimated scope: 1 session, ≤5 new files, zero changes to existing code.

---

## 5. Success Story: web4-trust-core WASM

It's worth noting that the `web4-trust-core` → WASM → 4-life pipeline is already
a working cross-repo import. The pattern demonstrates that web4 CAN produce
cross-language artifacts that consumers actually use. The WASM module provides
real protocol math (T3/V3 tensors, decay, witnessing) running in the browser at
near-native speed.

The gap is at the **schema/type layer**, not the **runtime layer**. The Rust crates
handle runtime; what's missing is the declarative contract layer that lets consumers
validate documents and generate types without manual porting.

---

## 6. Summary Table

| Artifact | 4-life imports? | Hardbound imports? | Gap |
|----------|----------------|-------------------|-----|
| Python SDK | No (wrong language) | No (wrong language) | Structural — not fixable |
| web4-core (Rust) | No (not needed) | Yes (optional feature) | None |
| web4-trust-core (WASM) | Yes (66KB binary) | No (uses native Rust) | None |
| JSON Schemas | No (not packaged) | No (not packaged) | **Packaging gap** |
| JSON-LD contexts | No (not packaged) | No (not packaged) | **Packaging gap** |
| TypeScript types | No (hand-written) | No (hand-written) | **Generation gap** |
| Behavioral functions | No (Python-only) | No (Python-only) | Low priority |

**Bottom line**: The highest-value cross-repo import target is the JSON Schema +
TypeScript type layer. Both consumers need it, neither has it, and it requires
packaging existing artifacts — not writing new ones.
