/**
 * Web4 LCT (Linked Context Token) URI Parser
 *
 * Parses and validates LCT URIs in the format:
 *   lct://{component}:{instance}:{role}@{network}?{query}#{fragment}
 *
 * Example URIs:
 *   lct://sage:thinker:expert_42@testnet
 *   lct://web4-agent:guardian:coordinator@mainnet?pairing_status=active&trust_threshold=0.75
 *   lct://mcp:filesystem:reader@local#did:key:z6Mk...
 *
 * @version 1.0.0
 * @see docs/what/specifications/LCT_UNIFIED_IDENTITY_SPECIFICATION.md
 */

/**
 * Pairing status for LCT relationships
 */
export type PairingStatus = 'pending' | 'active' | 'suspended' | 'revoked';

/**
 * Parsed LCT identity structure
 */
export interface LCTIdentity {
  /** System or domain (e.g., "sage", "web4-agent", "mcp") */
  component: string;

  /** Instance within component (e.g., "thinker", "guardian", "filesystem") */
  instance: string;

  /** Role or capability (e.g., "expert_42", "coordinator", "reader") */
  role: string;

  /** Network identifier (e.g., "testnet", "mainnet", "local") */
  network: string;

  /** Version (defaults to "1.0.0") */
  version: string;

  /** Current pairing status */
  pairingStatus?: PairingStatus;

  /** Trust threshold for operations (0.0-1.0) */
  trustThreshold?: number;

  /** List of capabilities */
  capabilities?: string[];

  /** Public key hash or DID (from URI fragment) */
  publicKeyHash?: string;

  /** Raw URI string for reference */
  rawUri: string;
}

/**
 * Result of LCT parsing with validation errors if any
 */
export interface LCTParseResult {
  success: boolean;
  identity?: LCTIdentity;
  errors: string[];
}

/**
 * Validation result for LCT URIs
 */
export interface LCTValidationResult {
  valid: boolean;
  errors: string[];
  warnings: string[];
}

// Authority pattern: component:instance:role@network
const AUTHORITY_PATTERN = /^([a-z0-9][a-z0-9-]*):([a-z0-9][a-z0-9_-]*):([a-z0-9][a-z0-9_-]*)@([a-z0-9][a-z0-9-]*)$/i;

// Component name validation (lowercase alphanumeric with hyphens)
const COMPONENT_PATTERN = /^[a-z0-9][a-z0-9-]*$/;

// Instance/role name validation (alphanumeric with underscores and hyphens)
const NAME_PATTERN = /^[a-z0-9][a-z0-9_-]*$/i;

// Network name validation
const NETWORK_PATTERN = /^[a-z0-9][a-z0-9-]*$/;

/**
 * Parse an LCT URI into a structured identity object.
 *
 * @param uri - The LCT URI string to parse
 * @returns LCTParseResult with identity or errors
 *
 * @example
 * const result = parseLctUri("lct://sage:thinker:expert_42@testnet");
 * if (result.success) {
 *   console.log(result.identity.component); // "sage"
 *   console.log(result.identity.role);      // "expert_42"
 * }
 */
export function parseLctUri(uri: string): LCTParseResult {
  const errors: string[] = [];

  // Validate scheme
  if (!uri.startsWith('lct://')) {
    return {
      success: false,
      errors: [`Invalid LCT URI scheme: must start with "lct://", got "${uri.substring(0, 10)}..."`]
    };
  }

  // Remove scheme
  const withoutScheme = uri.substring(6);

  // Split off fragment (public key hash)
  const [uriWithoutFragment, fragment] = withoutScheme.split('#', 2);
  const publicKeyHash = fragment || undefined;

  // Split off query string
  const [authority, queryString] = uriWithoutFragment.split('?', 2);

  // Parse authority (component:instance:role@network)
  const authorityMatch = authority.match(AUTHORITY_PATTERN);
  if (!authorityMatch) {
    return {
      success: false,
      errors: [`Invalid LCT authority format: expected "component:instance:role@network", got "${authority}"`]
    };
  }

  const [, component, instance, role, network] = authorityMatch;

  // Validate individual parts
  if (!COMPONENT_PATTERN.test(component)) {
    errors.push(`Invalid component name: "${component}" - must be lowercase alphanumeric with hyphens`);
  }
  if (!NAME_PATTERN.test(instance)) {
    errors.push(`Invalid instance name: "${instance}" - must be alphanumeric with underscores/hyphens`);
  }
  if (!NAME_PATTERN.test(role)) {
    errors.push(`Invalid role name: "${role}" - must be alphanumeric with underscores/hyphens`);
  }
  if (!NETWORK_PATTERN.test(network)) {
    errors.push(`Invalid network name: "${network}" - must be lowercase alphanumeric with hyphens`);
  }

  if (errors.length > 0) {
    return { success: false, errors };
  }

  // Parse query parameters
  let version = '1.0.0';
  let pairingStatus: PairingStatus | undefined;
  let trustThreshold: number | undefined;
  let capabilities: string[] | undefined;

  if (queryString) {
    const params = new URLSearchParams(queryString);

    // Version
    const versionParam = params.get('version');
    if (versionParam) {
      version = versionParam;
    }

    // Pairing status
    const statusParam = params.get('pairing_status');
    if (statusParam) {
      if (['pending', 'active', 'suspended', 'revoked'].includes(statusParam)) {
        pairingStatus = statusParam as PairingStatus;
      } else {
        errors.push(`Invalid pairing_status: "${statusParam}" - must be pending|active|suspended|revoked`);
      }
    }

    // Trust threshold
    const thresholdParam = params.get('trust_threshold');
    if (thresholdParam) {
      const threshold = parseFloat(thresholdParam);
      if (isNaN(threshold) || threshold < 0 || threshold > 1) {
        errors.push(`Invalid trust_threshold: "${thresholdParam}" - must be a number between 0 and 1`);
      } else {
        trustThreshold = threshold;
      }
    }

    // Capabilities
    const capabilitiesParam = params.get('capabilities');
    if (capabilitiesParam) {
      capabilities = capabilitiesParam.split(',').map(c => c.trim()).filter(c => c.length > 0);
    }
  }

  if (errors.length > 0) {
    return { success: false, errors };
  }

  return {
    success: true,
    identity: {
      component,
      instance,
      role,
      network,
      version,
      pairingStatus,
      trustThreshold,
      capabilities,
      publicKeyHash,
      rawUri: uri
    },
    errors: []
  };
}

/**
 * Validate an LCT URI format without fully parsing it.
 * Returns validation result with errors and warnings.
 *
 * @param uri - The LCT URI string to validate
 * @returns LCTValidationResult with validity status and messages
 */
export function validateLctUri(uri: string): LCTValidationResult {
  const errors: string[] = [];
  const warnings: string[] = [];

  const result = parseLctUri(uri);
  if (!result.success) {
    return { valid: false, errors: result.errors, warnings: [] };
  }

  const identity = result.identity!;

  // Warnings for non-standard but valid URIs
  if (identity.network === 'local' && !identity.publicKeyHash) {
    warnings.push('Local network LCTs should include public key hash for verification');
  }

  if (identity.trustThreshold !== undefined && identity.trustThreshold < 0.5) {
    warnings.push(`Low trust threshold (${identity.trustThreshold}) may allow untrusted operations`);
  }

  if (identity.version !== '1.0.0') {
    warnings.push(`Non-standard version: ${identity.version}`);
  }

  return { valid: true, errors, warnings };
}

/**
 * Construct an LCT URI from an identity object.
 *
 * @param identity - Partial identity object with required fields
 * @returns The constructed LCT URI string
 * @throws Error if required fields are missing
 */
export function buildLctUri(identity: Partial<LCTIdentity> & Pick<LCTIdentity, 'component' | 'instance' | 'role' | 'network'>): string {
  const { component, instance, role, network, version, pairingStatus, trustThreshold, capabilities, publicKeyHash } = identity;

  // Build base URI
  let uri = `lct://${component}:${instance}:${role}@${network}`;

  // Build query string
  const params: string[] = [];

  if (version && version !== '1.0.0') {
    params.push(`version=${encodeURIComponent(version)}`);
  }

  if (pairingStatus) {
    params.push(`pairing_status=${encodeURIComponent(pairingStatus)}`);
  }

  if (trustThreshold !== undefined) {
    params.push(`trust_threshold=${trustThreshold}`);
  }

  if (capabilities && capabilities.length > 0) {
    params.push(`capabilities=${encodeURIComponent(capabilities.join(','))}`);
  }

  if (params.length > 0) {
    uri += `?${params.join('&')}`;
  }

  // Add fragment
  if (publicKeyHash) {
    uri += `#${publicKeyHash}`;
  }

  return uri;
}

/**
 * Check if two LCT identities refer to the same entity.
 * Compares component, instance, role, and network (ignoring metadata).
 *
 * @param a - First LCT identity
 * @param b - Second LCT identity
 * @returns true if identities match
 */
export function lctIdentityEquals(a: LCTIdentity, b: LCTIdentity): boolean {
  return a.component === b.component &&
         a.instance === b.instance &&
         a.role === b.role &&
         a.network === b.network;
}

/**
 * Generate a canonical string representation for an LCT identity.
 * Useful for hashing, caching, and comparison.
 *
 * @param identity - The LCT identity
 * @returns Canonical string representation
 */
export function lctIdentityCanonical(identity: LCTIdentity): string {
  return `${identity.component}:${identity.instance}:${identity.role}@${identity.network}`;
}

/**
 * Extract the simple entity ID format used by web4-trust-core WASM bindings.
 * Converts LCT identity to "type:name" format for EntityTrust compatibility.
 *
 * @param identity - The LCT identity
 * @returns Simple entity ID string (e.g., "mcp:filesystem")
 */
export function toEntityId(identity: LCTIdentity): string {
  return `${identity.component}:${identity.instance}`;
}

/**
 * Parse a simple entity ID and create a minimal LCT identity.
 * Inverse of toEntityId for basic compatibility.
 *
 * @param entityId - Simple entity ID in "type:name" format
 * @param network - Network to use (defaults to "local")
 * @param role - Role to use (defaults to "default")
 * @returns Partial LCT identity
 */
export function fromEntityId(entityId: string, network = 'local', role = 'default'): Partial<LCTIdentity> {
  const [component, instance] = entityId.split(':', 2);
  return {
    component: component || 'unknown',
    instance: instance || 'unknown',
    role,
    network,
    version: '1.0.0'
  };
}

// Test vectors from specification
export const TEST_VECTORS = [
  {
    uri: 'lct://sage:thinker:expert_42@testnet',
    expected: {
      component: 'sage',
      instance: 'thinker',
      role: 'expert_42',
      network: 'testnet'
    }
  },
  {
    uri: 'lct://web4-agent:guardian:coordinator@mainnet?pairing_status=active&trust_threshold=0.75',
    expected: {
      component: 'web4-agent',
      instance: 'guardian',
      role: 'coordinator',
      network: 'mainnet',
      pairingStatus: 'active',
      trustThreshold: 0.75
    }
  },
  {
    uri: 'lct://mcp:filesystem:reader@local?capabilities=read,list#did:key:z6MkhaXgBZDvotDkL5257faiztiGiC2QtKLGpbnnEGta2doK',
    expected: {
      component: 'mcp',
      instance: 'filesystem',
      role: 'reader',
      network: 'local',
      capabilities: ['read', 'list'],
      publicKeyHash: 'did:key:z6MkhaXgBZDvotDkL5257faiztiGiC2QtKLGpbnnEGta2doK'
    }
  }
];

/**
 * Run test vectors and return results.
 * Useful for validating parser implementation.
 */
export function runTestVectors(): { passed: number; failed: number; details: string[] } {
  let passed = 0;
  let failed = 0;
  const details: string[] = [];

  for (const vector of TEST_VECTORS) {
    const result = parseLctUri(vector.uri);

    if (!result.success) {
      failed++;
      details.push(`FAIL: ${vector.uri} - Parse failed: ${result.errors.join(', ')}`);
      continue;
    }

    const identity = result.identity!;
    let vectorPassed = true;

    for (const [key, expectedValue] of Object.entries(vector.expected)) {
      const actualValue = (identity as Record<string, unknown>)[key];

      if (Array.isArray(expectedValue)) {
        if (!Array.isArray(actualValue) ||
            expectedValue.length !== actualValue.length ||
            !expectedValue.every((v, i) => v === actualValue[i])) {
          vectorPassed = false;
          details.push(`FAIL: ${vector.uri} - ${key} mismatch: expected ${JSON.stringify(expectedValue)}, got ${JSON.stringify(actualValue)}`);
        }
      } else if (actualValue !== expectedValue) {
        vectorPassed = false;
        details.push(`FAIL: ${vector.uri} - ${key} mismatch: expected ${expectedValue}, got ${actualValue}`);
      }
    }

    if (vectorPassed) {
      passed++;
      details.push(`PASS: ${vector.uri}`);
    } else {
      failed++;
    }
  }

  return { passed, failed, details };
}
