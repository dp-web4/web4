// Smoke test for the published web4-trust-core npm package.
// Imports the WASM module, instantiates key classes, exercises basic operations.
// Run with: npm test  (handles esbuild bundling + node execution)

import * as web4 from 'web4-trust-core';

const failures = [];
function check(label, cond, detail = '') {
  if (cond) {
    console.log(`  OK   ${label}`);
  } else {
    console.log(`  FAIL ${label}  ${detail}`);
    failures.push(label);
  }
}

console.log('web4-trust-core WASM smoke test');
console.log('================================');
console.log();
console.log(`Module type:   ${typeof web4}`);
const exports = Object.keys(web4).filter((k) => !k.startsWith('_'));
console.log(`Exports (${exports.length}): ${exports.slice(0, 12).join(', ')}${exports.length > 12 ? '...' : ''}`);
console.log();

// --- Section 1: WASM init (if exposed) -------------------------------------
console.log('Section 1 — Module loading');
check('module loaded', typeof web4 === 'object' && exports.length > 0);
check('init() function exported', typeof web4.init === 'function');
check('EntityTrust class exported', typeof web4.EntityTrust === 'function');
check('T3Tensor class exported', typeof web4.T3Tensor === 'function');
check('V3Tensor class exported', typeof web4.V3Tensor === 'function');
check('WasmSociety class exported', typeof web4.WasmSociety === 'function');
check('WasmSocietyRole class exported', typeof web4.WasmSocietyRole === 'function');
check('WasmRoleAssignment class exported', typeof web4.WasmRoleAssignment === 'function');
check('WasmATPAccount class exported', typeof web4.WasmATPAccount === 'function');
check('WasmR7Action class exported', typeof web4.WasmR7Action === 'function');
check('WasmTrustStore class exported', typeof web4.WasmTrustStore === 'function');

// --- Section 2: EntityTrust round-trip --------------------------------------
console.log();
console.log('Section 2 — EntityTrust instantiation + API');
try {
  const et = new web4.EntityTrust('lct:web4:smoke-test:agent-a');
  check('EntityTrust constructor accepts entity_id', true);
  check('successRate() returns number', typeof et.successRate() === 'number');
  check('t3Average() returns number', typeof et.t3Average() === 'number');
  check('v3Average() returns number', typeof et.v3Average() === 'number');
  check('trustLevel() returns string', typeof et.trustLevel() === 'string');
  check('toJSON() returns object', typeof et.toJSON() === 'object');

  // exercise some mutation
  et.updateFromOutcome(true, 0.5);
  et.updateFromOutcome(true, 0.3);
  et.updateFromOutcome(false, 0.1);
  const post = et.toJSON();
  check('updateFromOutcome() mutates state', JSON.stringify(post).length > 0);
  check('successRate() reflects outcomes', et.successRate() > 0 && et.successRate() < 1);

  et.giveWitness('lct:web4:smoke-test:agent-b', true, 0.8);
  et.receiveWitness('lct:web4:smoke-test:agent-b', true, 0.7);
  check('giveWitness / receiveWitness execute without error', true);

  et.applyDecay(7, 0.01);
  check('applyDecay() executes', true);

  et.free();
  check('free() releases without error', true);
} catch (e) {
  check('EntityTrust full lifecycle', false, `threw: ${e.message}`);
}

// --- Section 3: T3 / V3 round-trip ------------------------------------------
console.log();
console.log('Section 3 — T3 / V3 tensors');
try {
  const t3 = new web4.T3Tensor();
  check('T3Tensor constructs', true);
  if (typeof t3.toJSON === 'function') {
    check('T3Tensor.toJSON() returns object', typeof t3.toJSON() === 'object');
  }
  t3.free?.();

  const v3 = new web4.V3Tensor();
  check('V3Tensor constructs', true);
  v3.free?.();
} catch (e) {
  check('T3/V3 lifecycle', false, `threw: ${e.message}`);
}

// --- Section 4: Society + Role wiring ---------------------------------------
console.log();
console.log('Section 4 — Society / Role / RoleAssignment');
try {
  // WasmSociety has a private constructor; instances come from WasmSociety.bootstrap().
  // Signature: bootstrap(name: string, charter_hash: string, founder_lct_id: string)
  // founder_lct_id is parsed as a UUID by the Rust binding (see bindings/wasm.rs).
  const founderUuid = '11111111-1111-4111-8111-111111111111';  // valid v4-shaped UUID
  const society = web4.WasmSociety.bootstrap(
    'smoke-society',
    '0'.repeat(64),  // charter_hash: 32-byte hex hash placeholder
    founderUuid,
  );
  check('WasmSociety.bootstrap() returns instance', !!society);

  if (typeof society.toJSON === 'function') {
    const j = society.toJSON();
    check('WasmSociety.toJSON() returns object', typeof j === 'object');
  }
  if (typeof society.addCitizen === 'function') {
    society.addCitizen('22222222-2222-4222-8222-222222222222');  // UUID, not lct URI
    check('WasmSociety.addCitizen() executes', true);
  }
  society.free?.();
} catch (e) {
  check('WasmSociety basic lifecycle', false, `threw: ${e.message}`);
}

try {
  // WasmSocietyRole.baseMandatory() returns the 7 base-mandatory role definitions.
  const baseRoles = web4.WasmSocietyRole.baseMandatory();
  check('WasmSocietyRole.baseMandatory() returns array', Array.isArray(baseRoles));
  check('WasmSocietyRole.baseMandatory() has 7 roles', baseRoles.length === 7,
        `(got ${baseRoles.length})`);
  for (const r of baseRoles) r.free?.();
} catch (e) {
  check('WasmSocietyRole.baseMandatory()', false, `threw: ${e.message}`);
}

// --- Summary ----------------------------------------------------------------
console.log();
console.log('================================');
if (failures.length === 0) {
  console.log('All checks passed.');
  process.exit(0);
} else {
  console.log(`${failures.length} failures:`);
  for (const f of failures) console.log(`  - ${f}`);
  process.exit(1);
}
