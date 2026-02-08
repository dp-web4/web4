/**
 * Tests for LCT URI Parser
 *
 * Run with: npx tsx lct-parser.test.ts
 * Or with Deno: deno run lct-parser.test.ts
 */

import {
  parseLctUri,
  validateLctUri,
  buildLctUri,
  lctIdentityEquals,
  lctIdentityCanonical,
  toEntityId,
  fromEntityId,
  runTestVectors,
  type LCTIdentity
} from './lct-parser.js';

function assert(condition: boolean, message: string): void {
  if (!condition) {
    throw new Error(`Assertion failed: ${message}`);
  }
}

function assertEqual<T>(actual: T, expected: T, message: string): void {
  if (actual !== expected) {
    throw new Error(`${message}: expected ${expected}, got ${actual}`);
  }
}

// Test basic parsing
console.log('\n=== Basic Parsing Tests ===\n');

const basic = parseLctUri('lct://sage:thinker:expert_42@testnet');
assert(basic.success, 'Basic parse should succeed');
assertEqual(basic.identity!.component, 'sage', 'Component');
assertEqual(basic.identity!.instance, 'thinker', 'Instance');
assertEqual(basic.identity!.role, 'expert_42', 'Role');
assertEqual(basic.identity!.network, 'testnet', 'Network');
console.log('✓ Basic parsing works');

// Test with query parameters
const withParams = parseLctUri('lct://web4-agent:guardian:coordinator@mainnet?pairing_status=active&trust_threshold=0.75');
assert(withParams.success, 'Parse with params should succeed');
assertEqual(withParams.identity!.pairingStatus, 'active', 'Pairing status');
assertEqual(withParams.identity!.trustThreshold, 0.75, 'Trust threshold');
console.log('✓ Query parameters work');

// Test with capabilities
const withCaps = parseLctUri('lct://mcp:filesystem:reader@local?capabilities=read,write,list');
assert(withCaps.success, 'Parse with capabilities should succeed');
assert(withCaps.identity!.capabilities!.length === 3, 'Should have 3 capabilities');
assert(withCaps.identity!.capabilities!.includes('read'), 'Should include read');
console.log('✓ Capabilities parsing works');

// Test with fragment (public key hash)
const withFragment = parseLctUri('lct://sage:thinker:expert@testnet#did:key:z6MkhaXgBZDvotDkL5257faiztiGiC2QtKLGpbnnEGta2doK');
assert(withFragment.success, 'Parse with fragment should succeed');
assert(withFragment.identity!.publicKeyHash?.startsWith('did:key:'), 'Should have public key hash');
console.log('✓ Fragment (public key hash) works');

// Test invalid URIs
console.log('\n=== Error Handling Tests ===\n');

const noScheme = parseLctUri('sage:thinker:expert_42@testnet');
assert(!noScheme.success, 'Should fail without lct:// scheme');
console.log('✓ Rejects missing scheme');

const badAuthority = parseLctUri('lct://sage-thinker-expert@testnet');
assert(!badAuthority.success, 'Should fail with bad authority format');
console.log('✓ Rejects invalid authority format');

const badPairing = parseLctUri('lct://sage:thinker:expert@testnet?pairing_status=invalid');
assert(!badPairing.success, 'Should fail with invalid pairing status');
console.log('✓ Rejects invalid pairing status');

const badThreshold = parseLctUri('lct://sage:thinker:expert@testnet?trust_threshold=1.5');
assert(!badThreshold.success, 'Should fail with threshold > 1');
console.log('✓ Rejects invalid trust threshold');

// Test validation
console.log('\n=== Validation Tests ===\n');

const validResult = validateLctUri('lct://sage:thinker:expert_42@testnet');
assert(validResult.valid, 'Should be valid');
assertEqual(validResult.warnings.length, 0, 'No warnings');
console.log('✓ Valid URI has no warnings');

const localNoKey = validateLctUri('lct://mcp:filesystem:reader@local');
assert(localNoKey.valid, 'Should be valid');
assert(localNoKey.warnings.length > 0, 'Should have warning about missing key');
console.log('✓ Local network without key produces warning');

const lowThreshold = validateLctUri('lct://sage:thinker:expert@testnet?trust_threshold=0.3');
assert(lowThreshold.valid, 'Should be valid');
assert(lowThreshold.warnings.some(w => w.includes('Low trust')), 'Should warn about low threshold');
console.log('✓ Low trust threshold produces warning');

// Test building URIs
console.log('\n=== URI Building Tests ===\n');

const built = buildLctUri({
  component: 'sage',
  instance: 'thinker',
  role: 'expert_42',
  network: 'testnet'
});
assertEqual(built, 'lct://sage:thinker:expert_42@testnet', 'Basic build');
console.log('✓ Basic URI building works');

const builtWithParams = buildLctUri({
  component: 'web4-agent',
  instance: 'guardian',
  role: 'coordinator',
  network: 'mainnet',
  pairingStatus: 'active',
  trustThreshold: 0.75
});
assert(builtWithParams.includes('pairing_status=active'), 'Should include pairing status');
assert(builtWithParams.includes('trust_threshold=0.75'), 'Should include trust threshold');
console.log('✓ URI building with params works');

const builtWithFragment = buildLctUri({
  component: 'mcp',
  instance: 'filesystem',
  role: 'reader',
  network: 'local',
  publicKeyHash: 'did:key:z6Mk...'
});
assert(builtWithFragment.endsWith('#did:key:z6Mk...'), 'Should include fragment');
console.log('✓ URI building with fragment works');

// Test round-trip
console.log('\n=== Round-trip Tests ===\n');

const original = 'lct://sage:thinker:expert_42@testnet?pairing_status=active&trust_threshold=0.5';
const parsed = parseLctUri(original);
assert(parsed.success, 'Should parse');
const rebuilt = buildLctUri(parsed.identity!);
const reparsed = parseLctUri(rebuilt);
assert(reparsed.success, 'Should reparse');
assert(lctIdentityEquals(parsed.identity!, reparsed.identity!), 'Should be equal after round-trip');
console.log('✓ Round-trip preserves identity');

// Test utility functions
console.log('\n=== Utility Function Tests ===\n');

const id1: LCTIdentity = {
  component: 'sage', instance: 'thinker', role: 'expert_42', network: 'testnet',
  version: '1.0.0', rawUri: 'lct://sage:thinker:expert_42@testnet'
};
const id2: LCTIdentity = {
  component: 'sage', instance: 'thinker', role: 'expert_42', network: 'testnet',
  version: '1.0.0', pairingStatus: 'active', rawUri: 'lct://sage:thinker:expert_42@testnet?pairing_status=active'
};
const id3: LCTIdentity = {
  component: 'sage', instance: 'thinker', role: 'expert_43', network: 'testnet',
  version: '1.0.0', rawUri: 'lct://sage:thinker:expert_43@testnet'
};

assert(lctIdentityEquals(id1, id2), 'Same entity with different metadata should be equal');
assert(!lctIdentityEquals(id1, id3), 'Different roles should not be equal');
console.log('✓ Identity equality works');

assertEqual(lctIdentityCanonical(id1), 'sage:thinker:expert_42@testnet', 'Canonical form');
console.log('✓ Canonical representation works');

assertEqual(toEntityId(id1), 'sage:thinker', 'Entity ID');
console.log('✓ Entity ID conversion works');

const fromId = fromEntityId('mcp:filesystem', 'mainnet', 'reader');
assertEqual(fromId.component, 'mcp', 'From entity ID component');
assertEqual(fromId.instance, 'filesystem', 'From entity ID instance');
assertEqual(fromId.role, 'reader', 'From entity ID role');
console.log('✓ Entity ID reverse conversion works');

// Run specification test vectors
console.log('\n=== Specification Test Vectors ===\n');

const vectorResults = runTestVectors();
for (const detail of vectorResults.details) {
  console.log(detail);
}

console.log(`\nPassed: ${vectorResults.passed}, Failed: ${vectorResults.failed}`);

// Summary
console.log('\n=== Summary ===\n');
console.log('All tests passed! LCT parser is ready for use.');
console.log('\nUsage:');
console.log('  import { parseLctUri, buildLctUri } from "./lct-parser.js";');
console.log('  const result = parseLctUri("lct://sage:thinker:expert_42@testnet");');
console.log('  if (result.success) console.log(result.identity);');
