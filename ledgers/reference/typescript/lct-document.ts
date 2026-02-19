/**
 * Web4 LCT (Linked Context Token) Document Library
 *
 * Full LCT document model matching lct.schema.json.
 * Complements lct-parser.ts (URI format) with the document format
 * (T3/V3 tensors, MRH, binding, birth certificate, attestations).
 *
 * @version 1.0.0
 * @see web4-standard/schemas/lct.schema.json
 * @see web4-standard/core-spec/LCT-linked-context-token.md
 */

// ═══════════════════════════════════════════════════════════════
// Entity Types — 15 canonical types per entity-types.md (Feb 2026)
// ═══════════════════════════════════════════════════════════════

export type EntityType =
  | 'human'
  | 'ai'
  | 'society'
  | 'organization'
  | 'role'
  | 'task'
  | 'resource'
  | 'device'
  | 'service'
  | 'oracle'
  | 'accumulator'
  | 'dictionary'
  | 'hybrid'
  | 'policy'
  | 'infrastructure';

// ═══════════════════════════════════════════════════════════════
// T3 Trust Tensor — Canonical 3-root dimensions
// ═══════════════════════════════════════════════════════════════

/**
 * Trust Tensor with 3 canonical root dimensions.
 * Each root is an aggregate of an open-ended RDF sub-dimension graph
 * linked via web4:subDimensionOf.
 */
export interface T3Tensor {
  /** Role-specific capability (0.0-1.0) */
  talent: number;
  /** Role-specific expertise / learning quality (0.0-1.0) */
  training: number;
  /** Behavioral stability / reliability (0.0-1.0) */
  temperament: number;
  /** Optional domain-specific refinements */
  sub_dimensions?: Record<string, Record<string, number>>;
  /** Weighted composite score (0.0-1.0) */
  composite_score?: number;
  /** When tensors were last computed */
  last_computed?: string;
  /** LCT IDs of entities that computed these scores */
  computation_witnesses?: string[];
}

// ═══════════════════════════════════════════════════════════════
// V3 Value Tensor — Canonical 3-root dimensions
// ═══════════════════════════════════════════════════════════════

/**
 * Value Tensor with 3 canonical root dimensions.
 * Follows same fractal sub-dimension pattern as T3.
 */
export interface V3Tensor {
  /** Subjective worth / economic value (0.0+, can exceed 1.0) */
  valuation: number;
  /** Truthfulness / accuracy of claims (0.0-1.0) */
  veracity: number;
  /** Soundness of reasoning / confirmed value delivery (0.0-1.0) */
  validity: number;
  /** Optional domain-specific refinements */
  sub_dimensions?: Record<string, Record<string, number>>;
  /** Weighted composite score (0.0-1.0) */
  composite_score?: number;
  /** When tensors were last computed */
  last_computed?: string;
  /** LCT IDs of entities that computed these scores */
  computation_witnesses?: string[];
}

// ═══════════════════════════════════════════════════════════════
// Binding — Cryptographic anchor
// ═══════════════════════════════════════════════════════════════

export interface LCTBinding {
  /** What kind of entity this LCT represents */
  entity_type: EntityType;
  /** Multibase-encoded public key */
  public_key: string;
  /** Optional EAT hardware attestation token */
  hardware_anchor?: string;
  /** ISO 8601 creation timestamp */
  created_at: string;
  /** COSE_Sign1 binding proof */
  binding_proof: string;
}

// ═══════════════════════════════════════════════════════════════
// Birth Certificate — Society-issued identity
// ═══════════════════════════════════════════════════════════════

export type BirthContext = 'nation' | 'platform' | 'network' | 'organization' | 'ecosystem';

export interface BirthCertificate {
  /** LCT of the society issuing this certificate */
  issuing_society: string;
  /** Citizen role LCT */
  citizen_role: string;
  /** Birth context */
  context: BirthContext;
  /** ISO 8601 birth timestamp */
  birth_timestamp: string;
  /** Parent entity LCT (if any) */
  parent_entity?: string;
  /** Witness LCTs (minimum 1, recommended 3+) */
  birth_witnesses: string[];
}

// ═══════════════════════════════════════════════════════════════
// MRH — Markov Relevancy Horizon
// ═══════════════════════════════════════════════════════════════

export type BoundType = 'parent' | 'child' | 'sibling';
export type PairingType = 'birth_certificate' | 'role' | 'operational';
export type WitnessRole = 'time' | 'audit' | 'oracle' | 'peer' | 'existence' | 'action' | 'state' | 'quality';

export interface MRHBound {
  lct_id: string;
  type: BoundType;
  ts: string;
}

export interface MRHPaired {
  lct_id: string;
  pairing_type?: PairingType;
  permanent?: boolean;
  context?: string;
  session_id?: string;
  ts: string;
}

export interface MRHWitnessing {
  lct_id: string;
  role: WitnessRole;
  last_attestation: string;
}

export interface MRH {
  /** Permanent hierarchical attachments */
  bound: MRHBound[];
  /** Authorized operational relationships (minimum 1) */
  paired: MRHPaired[];
  /** Witness relationships */
  witnessing?: MRHWitnessing[];
  /** Context boundary depth (1-10, default 3) */
  horizon_depth: number;
  /** ISO 8601 last update timestamp */
  last_updated: string;
}

// ═══════════════════════════════════════════════════════════════
// Policy — Capabilities and constraints
// ═══════════════════════════════════════════════════════════════

export interface LCTPolicy {
  /** List of capability strings */
  capabilities: string[];
  /** Optional constraint object */
  constraints?: Record<string, unknown>;
}

// ═══════════════════════════════════════════════════════════════
// Attestation — Witness observations
// ═══════════════════════════════════════════════════════════════

export interface Attestation {
  /** Witness DID or LCT */
  witness: string;
  /** Attestation type */
  type: string;
  /** Signature */
  sig: string;
  /** ISO 8601 timestamp */
  ts: string;
  /** Optional claims */
  claims?: Record<string, unknown>;
}

// ═══════════════════════════════════════════════════════════════
// Lineage — Evolution history
// ═══════════════════════════════════════════════════════════════

export type LineageReason = 'genesis' | 'rotation' | 'fork' | 'upgrade';

export interface LineageEntry {
  /** Parent LCT ID */
  parent?: string;
  /** Reason for lineage event */
  reason: LineageReason;
  /** ISO 8601 timestamp */
  ts: string;
}

// ═══════════════════════════════════════════════════════════════
// Revocation — Termination record
// ═══════════════════════════════════════════════════════════════

export type RevocationStatus = 'active' | 'revoked';
export type RevocationReason = 'compromise' | 'superseded' | 'expired';

export interface Revocation {
  status: RevocationStatus;
  ts?: string;
  reason?: RevocationReason;
}

// ═══════════════════════════════════════════════════════════════
// LCT Document — Complete Linked Context Token
// ═══════════════════════════════════════════════════════════════

/**
 * Complete LCT document structure per lct.schema.json.
 *
 * Required: lct_id, subject, binding, birth_certificate, mrh, policy
 * Optional: t3_tensor, v3_tensor, attestations, lineage, revocation
 */
export interface LCTDocument {
  /** Globally unique LCT identifier (format: lct:web4:{type}:{hash}) */
  lct_id: string;
  /** DID of the entity (format: did:web4:{method}:{id}) */
  subject: string;
  /** Cryptographic binding */
  binding: LCTBinding;
  /** Society-issued birth certificate */
  birth_certificate: BirthCertificate;
  /** Markov Relevancy Horizon */
  mrh: MRH;
  /** Capabilities and constraints */
  policy: LCTPolicy;
  /** Trust tensor (3 canonical root dimensions) */
  t3_tensor?: T3Tensor;
  /** Value tensor (3 canonical root dimensions) */
  v3_tensor?: V3Tensor;
  /** Witness attestations */
  attestations?: Attestation[];
  /** Evolution history */
  lineage?: LineageEntry[];
  /** Termination record */
  revocation?: Revocation;
}

// ═══════════════════════════════════════════════════════════════
// Tensor Operations
// ═══════════════════════════════════════════════════════════════

/**
 * Compute T3 composite score (weighted average of root dimensions).
 */
export function computeT3Composite(t3: T3Tensor): number {
  return t3.talent * 0.4 + t3.training * 0.3 + t3.temperament * 0.3;
}

/**
 * Compute V3 composite score.
 */
export function computeV3Composite(v3: V3Tensor): number {
  return v3.valuation * 0.3 + v3.veracity * 0.35 + v3.validity * 0.35;
}

/**
 * Create default T3 tensor (neutral starting point).
 */
export function defaultT3(): T3Tensor {
  return {
    talent: 0.5,
    training: 0.5,
    temperament: 0.5,
    composite_score: 0.5,
    last_computed: new Date().toISOString(),
  };
}

/**
 * Create default V3 tensor.
 */
export function defaultV3(): V3Tensor {
  return {
    valuation: 0.0,
    veracity: 0.5,
    validity: 0.5,
    composite_score: 0.35,
    last_computed: new Date().toISOString(),
  };
}

/**
 * Migrate legacy 6-dim T3 to canonical 3-dim.
 * Migration path from web4-trust-core/src/tensor/t3.rs::from_legacy_6d()
 */
export function migrateT3FromLegacy6d(
  competence: number,
  reliability: number,
  consistency: number,
  witnesses: number,
  lineage: number,
  alignment: number,
): T3Tensor {
  const talent = competence;
  const training = (reliability + consistency + lineage) / 3.0;
  const temperament = (witnesses + alignment) / 2.0;
  return {
    talent: clamp01(talent),
    training: clamp01(training),
    temperament: clamp01(temperament),
    composite_score: computeT3Composite({ talent, training, temperament }),
    last_computed: new Date().toISOString(),
  };
}

/**
 * Migrate legacy 6-dim V3 to canonical 3-dim.
 */
export function migrateV3FromLegacy6d(
  energy: number,
  contribution: number,
  stewardship: number,
  network: number,
  reputation: number,
  temporal: number,
): V3Tensor {
  const valuation = (energy + contribution) / 2.0;
  const veracity = reputation;
  const validity = (stewardship + network + temporal) / 3.0;
  return {
    valuation: clamp01(valuation),
    veracity: clamp01(veracity),
    validity: clamp01(validity),
    composite_score: computeV3Composite({ valuation, veracity, validity }),
    last_computed: new Date().toISOString(),
  };
}

function clamp01(v: number): number {
  return Math.max(0, Math.min(1, v));
}

// ═══════════════════════════════════════════════════════════════
// Validation
// ═══════════════════════════════════════════════════════════════

export interface ValidationResult {
  valid: boolean;
  errors: string[];
  warnings: string[];
}

const LCT_ID_PATTERN = /^lct:web4:[A-Za-z0-9_:-]+$/;
const SUBJECT_PATTERN = /^did:web4:(key|method):[A-Za-z0-9_-]+$/;
const VALID_ENTITY_TYPES: EntityType[] = [
  'human', 'ai', 'society', 'organization', 'role', 'task',
  'resource', 'device', 'service', 'oracle', 'accumulator',
  'dictionary', 'hybrid', 'policy', 'infrastructure',
];

/**
 * Validate an LCT document against the schema rules.
 */
export function validateLCT(doc: LCTDocument): ValidationResult {
  const errors: string[] = [];
  const warnings: string[] = [];

  // Required fields
  if (!doc.lct_id) errors.push('Missing required field: lct_id');
  if (!doc.subject) errors.push('Missing required field: subject');
  if (!doc.binding) errors.push('Missing required field: binding');
  if (!doc.birth_certificate) errors.push('Missing required field: birth_certificate');
  if (!doc.mrh) errors.push('Missing required field: mrh');
  if (!doc.policy) errors.push('Missing required field: policy');

  if (errors.length > 0) return { valid: false, errors, warnings };

  // LCT ID format
  if (!LCT_ID_PATTERN.test(doc.lct_id)) {
    errors.push(`Invalid lct_id format: "${doc.lct_id}"`);
  }

  // Subject format
  if (!SUBJECT_PATTERN.test(doc.subject)) {
    errors.push(`Invalid subject format: "${doc.subject}"`);
  }

  // Binding validation
  if (!VALID_ENTITY_TYPES.includes(doc.binding.entity_type)) {
    errors.push(`Invalid entity_type: "${doc.binding.entity_type}"`);
  }
  if (!doc.binding.public_key) errors.push('Missing binding.public_key');
  if (!doc.binding.created_at) errors.push('Missing binding.created_at');
  if (!doc.binding.binding_proof) errors.push('Missing binding.binding_proof');

  // Birth certificate validation
  const bc = doc.birth_certificate;
  if (!bc.issuing_society) errors.push('Missing birth_certificate.issuing_society');
  if (!bc.citizen_role) errors.push('Missing birth_certificate.citizen_role');
  if (!bc.context) errors.push('Missing birth_certificate.context');
  if (!bc.birth_timestamp) errors.push('Missing birth_certificate.birth_timestamp');
  if (!bc.birth_witnesses || bc.birth_witnesses.length === 0) {
    errors.push('birth_certificate.birth_witnesses must have at least 1 entry');
  }
  if (bc.birth_witnesses && bc.birth_witnesses.length < 3) {
    warnings.push('birth_certificate.birth_witnesses should have at least 3 entries per spec');
  }

  // MRH validation
  if (!doc.mrh.paired || doc.mrh.paired.length === 0) {
    errors.push('mrh.paired must have at least 1 entry');
  }
  if (doc.mrh.horizon_depth < 1 || doc.mrh.horizon_depth > 10) {
    errors.push(`mrh.horizon_depth must be 1-10, got ${doc.mrh.horizon_depth}`);
  }

  // Check for permanent citizen pairing
  const citizenPairing = doc.mrh.paired?.find(p => p.pairing_type === 'birth_certificate' && p.permanent);
  if (!citizenPairing) {
    warnings.push('No permanent birth_certificate pairing found in mrh.paired');
  }

  // Policy validation
  if (!doc.policy.capabilities) errors.push('Missing policy.capabilities');

  // T3 tensor validation
  if (doc.t3_tensor) {
    if (doc.t3_tensor.talent < 0 || doc.t3_tensor.talent > 1)
      errors.push('t3_tensor.talent must be 0.0-1.0');
    if (doc.t3_tensor.training < 0 || doc.t3_tensor.training > 1)
      errors.push('t3_tensor.training must be 0.0-1.0');
    if (doc.t3_tensor.temperament < 0 || doc.t3_tensor.temperament > 1)
      errors.push('t3_tensor.temperament must be 0.0-1.0');
  }

  // V3 tensor validation
  if (doc.v3_tensor) {
    if (doc.v3_tensor.valuation < 0)
      errors.push('v3_tensor.valuation must be >= 0');
    if (doc.v3_tensor.veracity < 0 || doc.v3_tensor.veracity > 1)
      errors.push('v3_tensor.veracity must be 0.0-1.0');
    if (doc.v3_tensor.validity < 0 || doc.v3_tensor.validity > 1)
      errors.push('v3_tensor.validity must be 0.0-1.0');
  }

  // Revocation validation
  if (doc.revocation && doc.revocation.status === 'revoked') {
    if (!doc.revocation.ts) warnings.push('Revoked LCT should have revocation timestamp');
    if (!doc.revocation.reason) warnings.push('Revoked LCT should have revocation reason');
  }

  return { valid: errors.length === 0, errors, warnings };
}

// ═══════════════════════════════════════════════════════════════
// Builder — Fluent LCT construction
// ═══════════════════════════════════════════════════════════════

/**
 * Fluent builder for LCT documents.
 *
 * @example
 * const lct = new LCTBuilder('ai', 'sage-legion')
 *   .withBirthCertificate('lct:web4:society:federation', 'lct:web4:role:citizen:ai')
 *   .withT3({ talent: 0.8, training: 0.7, temperament: 0.9 })
 *   .addCapability('witness:attest')
 *   .build();
 */
export class LCTBuilder {
  private doc: Partial<LCTDocument>;
  private entityType: EntityType;

  constructor(entityType: EntityType, name: string) {
    this.entityType = entityType;
    const hash = simpleHash(`${entityType}:${name}:${Date.now()}`);
    const now = new Date().toISOString();

    this.doc = {
      lct_id: `lct:web4:${entityType}:${hash}`,
      subject: `did:web4:key:${hash}`,
      binding: {
        entity_type: entityType,
        public_key: '',
        created_at: now,
        binding_proof: '',
      },
      mrh: {
        bound: [],
        paired: [],
        witnessing: [],
        horizon_depth: 3,
        last_updated: now,
      },
      policy: {
        capabilities: [],
      },
      revocation: {
        status: 'active',
      },
    };
  }

  /** Set the public key and binding proof. */
  withBinding(publicKey: string, bindingProof: string, hardwareAnchor?: string): this {
    this.doc.binding!.public_key = publicKey;
    this.doc.binding!.binding_proof = bindingProof;
    if (hardwareAnchor) this.doc.binding!.hardware_anchor = hardwareAnchor;
    return this;
  }

  /** Set birth certificate. */
  withBirthCertificate(
    issuingSociety: string,
    citizenRole: string,
    context: BirthContext = 'platform',
    witnesses: string[] = [],
  ): this {
    const now = new Date().toISOString();
    this.doc.birth_certificate = {
      issuing_society: issuingSociety,
      citizen_role: citizenRole,
      context,
      birth_timestamp: now,
      birth_witnesses: witnesses,
    };
    // Add permanent citizen pairing to MRH
    this.doc.mrh!.paired!.push({
      lct_id: citizenRole,
      pairing_type: 'birth_certificate',
      permanent: true,
      ts: now,
    });
    return this;
  }

  /** Set T3 trust tensor. */
  withT3(t3: Partial<T3Tensor>): this {
    const full: T3Tensor = {
      talent: t3.talent ?? 0.5,
      training: t3.training ?? 0.5,
      temperament: t3.temperament ?? 0.5,
      last_computed: new Date().toISOString(),
      ...t3,
    };
    full.composite_score = computeT3Composite(full);
    this.doc.t3_tensor = full;
    return this;
  }

  /** Set V3 value tensor. */
  withV3(v3: Partial<V3Tensor>): this {
    const full: V3Tensor = {
      valuation: v3.valuation ?? 0.0,
      veracity: v3.veracity ?? 0.5,
      validity: v3.validity ?? 0.5,
      last_computed: new Date().toISOString(),
      ...v3,
    };
    full.composite_score = computeV3Composite(full);
    this.doc.v3_tensor = full;
    return this;
  }

  /** Add a capability. */
  addCapability(capability: string): this {
    this.doc.policy!.capabilities.push(capability);
    return this;
  }

  /** Add a bound relationship (permanent hierarchical). */
  addBound(lctId: string, type: BoundType): this {
    this.doc.mrh!.bound!.push({ lct_id: lctId, type, ts: new Date().toISOString() });
    return this;
  }

  /** Add a pairing relationship. */
  addPairing(lctId: string, type: PairingType = 'operational', permanent = false): this {
    this.doc.mrh!.paired!.push({
      lct_id: lctId,
      pairing_type: type,
      permanent,
      ts: new Date().toISOString(),
    });
    return this;
  }

  /** Add a witness. */
  addWitness(lctId: string, role: WitnessRole): this {
    if (!this.doc.mrh!.witnessing) this.doc.mrh!.witnessing = [];
    this.doc.mrh!.witnessing!.push({
      lct_id: lctId,
      role,
      last_attestation: new Date().toISOString(),
    });
    return this;
  }

  /** Add a lineage entry. */
  addLineage(reason: LineageReason, parent?: string): this {
    if (!this.doc.lineage) this.doc.lineage = [];
    this.doc.lineage.push({ reason, parent, ts: new Date().toISOString() });
    return this;
  }

  /** Set policy constraints. */
  withConstraints(constraints: Record<string, unknown>): this {
    this.doc.policy!.constraints = constraints;
    return this;
  }

  /** Build and validate the LCT document. */
  build(): LCTDocument {
    const doc = this.doc as LCTDocument;
    const result = validateLCT(doc);
    if (!result.valid) {
      throw new Error(`Invalid LCT: ${result.errors.join('; ')}`);
    }
    return doc;
  }

  /** Build without validation (for testing or partial documents). */
  buildUnsafe(): LCTDocument {
    return this.doc as LCTDocument;
  }
}

// ═══════════════════════════════════════════════════════════════
// Bridge to URI Parser
// ═══════════════════════════════════════════════════════════════

/**
 * Convert an LCT document to an LCT URI for network addressing.
 * Uses binding.entity_type as component, lct_id hash as instance.
 */
export function documentToUri(doc: LCTDocument, network = 'local', role = 'default'): string {
  const hash = doc.lct_id.split(':').pop() || 'unknown';
  return `lct://${doc.binding.entity_type}:${hash}:${role}@${network}`;
}

// ═══════════════════════════════════════════════════════════════
// Utilities
// ═══════════════════════════════════════════════════════════════

function simpleHash(input: string): string {
  let hash = 0;
  for (let i = 0; i < input.length; i++) {
    const char = input.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash = hash & hash; // Convert to 32-bit integer
  }
  return Math.abs(hash).toString(16).padStart(16, '0').slice(0, 16);
}

// ═══════════════════════════════════════════════════════════════
// Test Vectors
// ═══════════════════════════════════════════════════════════════

export const DOCUMENT_TEST_VECTORS = {
  /** Minimal valid LCT document */
  minimal: (): LCTDocument => ({
    lct_id: 'lct:web4:ai:test0000deadbeef',
    subject: 'did:web4:key:z6Mk1234567890',
    binding: {
      entity_type: 'ai',
      public_key: 'mb64testkey',
      created_at: '2026-02-19T00:00:00Z',
      binding_proof: 'cose:test_proof',
    },
    birth_certificate: {
      issuing_society: 'lct:web4:society:genesis',
      citizen_role: 'lct:web4:role:citizen:ai',
      context: 'platform',
      birth_timestamp: '2026-02-19T00:00:00Z',
      birth_witnesses: ['lct:web4:witness:w1', 'lct:web4:witness:w2', 'lct:web4:witness:w3'],
    },
    mrh: {
      bound: [],
      paired: [{
        lct_id: 'lct:web4:role:citizen:ai',
        pairing_type: 'birth_certificate',
        permanent: true,
        ts: '2026-02-19T00:00:00Z',
      }],
      witnessing: [],
      horizon_depth: 3,
      last_updated: '2026-02-19T00:00:00Z',
    },
    policy: {
      capabilities: ['witness:attest'],
    },
    t3_tensor: {
      talent: 0.5,
      training: 0.5,
      temperament: 0.5,
      composite_score: 0.5,
    },
    v3_tensor: {
      valuation: 0.0,
      veracity: 0.5,
      validity: 0.5,
      composite_score: 0.35,
    },
    revocation: { status: 'active' },
  }),
};

/**
 * Run document validation tests.
 */
export function runDocumentTests(): { passed: number; failed: number; details: string[] } {
  let passed = 0;
  let failed = 0;
  const details: string[] = [];

  // Test 1: Minimal valid document
  const minimal = DOCUMENT_TEST_VECTORS.minimal();
  const result1 = validateLCT(minimal);
  if (result1.valid) {
    passed++;
    details.push('PASS: Minimal valid document validates');
  } else {
    failed++;
    details.push(`FAIL: Minimal valid document: ${result1.errors.join(', ')}`);
  }

  // Test 2: T3 composite computation
  const t3: T3Tensor = { talent: 0.8, training: 0.6, temperament: 0.9 };
  const composite = computeT3Composite(t3);
  const expected = 0.8 * 0.4 + 0.6 * 0.3 + 0.9 * 0.3; // 0.77
  if (Math.abs(composite - expected) < 0.001) {
    passed++;
    details.push(`PASS: T3 composite = ${composite.toFixed(3)} (expected ${expected.toFixed(3)})`);
  } else {
    failed++;
    details.push(`FAIL: T3 composite = ${composite}, expected ${expected}`);
  }

  // Test 3: Builder creates valid document
  try {
    const built = new LCTBuilder('ai', 'test-agent')
      .withBinding('mb64testkey', 'cose:test')
      .withBirthCertificate(
        'lct:web4:society:test',
        'lct:web4:role:citizen:ai',
        'platform',
        ['lct:web4:witness:w1', 'lct:web4:witness:w2', 'lct:web4:witness:w3'],
      )
      .withT3({ talent: 0.7, training: 0.8, temperament: 0.6 })
      .addCapability('write:lct')
      .build();
    const result3 = validateLCT(built);
    if (result3.valid) {
      passed++;
      details.push('PASS: Builder creates valid document');
    } else {
      failed++;
      details.push(`FAIL: Builder document invalid: ${result3.errors.join(', ')}`);
    }
  } catch (e) {
    failed++;
    details.push(`FAIL: Builder threw: ${e}`);
  }

  // Test 4: Invalid document caught
  const invalid: LCTDocument = { ...minimal, lct_id: 'bad-id' };
  const result4 = validateLCT(invalid);
  if (!result4.valid) {
    passed++;
    details.push('PASS: Invalid lct_id correctly caught');
  } else {
    failed++;
    details.push('FAIL: Invalid lct_id not caught');
  }

  // Test 5: Legacy migration
  const migrated = migrateT3FromLegacy6d(0.8, 0.7, 0.6, 0.9, 0.5, 0.8);
  if (migrated.talent === 0.8 && Math.abs(migrated.training - 0.6) < 0.01) {
    passed++;
    details.push(`PASS: Legacy T3 migration: talent=${migrated.talent}, training=${migrated.training.toFixed(2)}, temperament=${migrated.temperament.toFixed(2)}`);
  } else {
    failed++;
    details.push(`FAIL: Legacy migration unexpected values`);
  }

  return { passed, failed, details };
}
