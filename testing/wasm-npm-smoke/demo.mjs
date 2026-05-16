// What you can actually DO with web4-trust-core: a worked example.
// Scenario: three agents collaborating; one earns trust through outcomes
// and witnessed events; one's reputation decays from inactivity; one
// fails a high-stakes action and pays reputational cost.
//
// Run: node --experimental-wasm-modules --no-warnings=ExperimentalWarning /tmp/web4-demo.mjs
//      (from a directory where web4-trust-core is installed)

import {
  EntityTrust, T3Tensor, V3Tensor,
  WasmATPAccount, WasmSociety, WasmSocietyRole,
} from 'web4-trust-core';

console.log('\n=== Web4 trust-core demo: a small federation in action ===\n');

// ---------------------------------------------------------------------------
// 1. Three agents enter the world with neutral trust.
// ---------------------------------------------------------------------------
const alice = new EntityTrust('alice');
const bob   = new EntityTrust('bob');
const carol = new EntityTrust('carol');

const report = (a, name) =>
  console.log(`  ${name.padEnd(6)}: t3=${a.t3Average().toFixed(3)}  v3=${a.v3Average().toFixed(3)}  success=${a.successRate().toFixed(2)}  level=${a.trustLevel()}`);

console.log('Start: everyone neutral.');
[[alice,'alice'],[bob,'bob'],[carol,'carol']].forEach(([a,n])=>report(a,n));

// ---------------------------------------------------------------------------
// 2. Time passes. Outcomes accumulate. Each successful action with a high
//    magnitude increases T3; failures decrease it. This is the *behavioral*
//    layer of trust — what an entity *does* shapes what others can rely on.
// ---------------------------------------------------------------------------
console.log('\nWeek 1: Alice ships 5 small wins, Bob ships 2 medium wins, Carol mixed.');
for (let i = 0; i < 5; i++) alice.updateFromOutcome(true, 0.4);
for (let i = 0; i < 2; i++) bob.updateFromOutcome(true, 0.7);
carol.updateFromOutcome(true,  0.5);
carol.updateFromOutcome(false, 0.4);
carol.updateFromOutcome(true,  0.3);
[[alice,'alice'],[bob,'bob'],[carol,'carol']].forEach(([a,n])=>report(a,n));

// ---------------------------------------------------------------------------
// 3. Witness events. When Bob witnesses Alice succeeding, both reputations
//    move: Alice's "received witness" record grows, Bob's "given witness"
//    record grows. This is the *social* layer — who vouches for whom.
// ---------------------------------------------------------------------------
console.log('\nWeek 2: Bob publicly witnesses 3 of Alice\'s wins. Carol witnesses 1.');
bob.giveWitness('alice', true, 0.6); alice.receiveWitness('bob', true, 0.6);
bob.giveWitness('alice', true, 0.6); alice.receiveWitness('bob', true, 0.6);
bob.giveWitness('alice', true, 0.7); alice.receiveWitness('bob', true, 0.7);
carol.giveWitness('alice', true, 0.5); alice.receiveWitness('carol', true, 0.5);
[[alice,'alice'],[bob,'bob'],[carol,'carol']].forEach(([a,n])=>report(a,n));

// ---------------------------------------------------------------------------
// 4. Time-based decay. Trust that isn't refreshed degrades. Reputation has
//    to be *maintained* — it's not a permanent attribute.
// ---------------------------------------------------------------------------
console.log('\nWeek 3-6: Carol goes silent for 30 days. Decay applies.');
carol.applyDecay(30, 0.005);  // 30 days at half-life ~140 days
[[alice,'alice'],[bob,'bob'],[carol,'carol']].forEach(([a,n])=>report(a,n));

// ---------------------------------------------------------------------------
// 5. T3 tensor directly. T3 = Talent / Training / Temperament; these are
//    the three sub-dimensions of trust in the Web4 ontology. You can
//    instantiate them with explicit values when you have signal about
//    *which* dimension is strong, vs. updating from behavior alone.
// ---------------------------------------------------------------------------
console.log('\nDavid joins (a new hire with strong portfolio but no on-the-job history).');
const davidT3 = new T3Tensor(0.85, 0.40, 0.65);  // high talent, low training, moderate temperament
console.log(`  David T3: talent=${davidT3.talent} training=${davidT3.training} temperament=${davidT3.temperament}  avg=${davidT3.average().toFixed(3)}  level=${davidT3.level()}`);

// V3 = Valuation / Veracity / Validity — the value-side counterpart to T3.
const projectV3 = new V3Tensor(0.7, 0.9, 0.8);
console.log(`  Project V3: valuation=${projectV3.valuation} veracity=${projectV3.veracity} validity=${projectV3.validity}  avg=${projectV3.average().toFixed(3)}`);

// ---------------------------------------------------------------------------
// 6. ATP accounting. Actions cost energy. Lock-on-attempt + commit-on-success
//    + rollback-on-failure is the bio-inspired ATP/ADP cycle.
// ---------------------------------------------------------------------------
console.log('\nAlice attempts a 25-ATP action. Lock now, commit if it works.');
const aliceWallet = new WasmATPAccount(100);  // starts with 100 ATP
console.log(`  Wallet starts: energyRatio=${aliceWallet.energyRatio().toFixed(2)}`);
aliceWallet.lock(25);
console.log(`  After lock(25): some ATP is escrowed; if action fails, rollback restores it.`);
const committed = aliceWallet.commit(25);
console.log(`  After commit(25): ${committed} ATP discharged to ADP. Action paid for.`);
const recharged = aliceWallet.recharge(0.3, 2.0);
console.log(`  recharge(rate=0.3, max=2.0x): ${recharged.toFixed(2)} ATP regenerated from ADP.`);

// ---------------------------------------------------------------------------
// 7. Society + roles. Entities aren't just floating reputation scores —
//    they hold roles inside a society. The 7 base-mandatory roles
//    (Sovereign, Law Oracle, Policy-Entity, Treasurer, Administrator,
//    Archivist, Citizen) are the same regardless of which society you
//    bootstrap — the structural taxonomy is part of the Web4 spec.
// ---------------------------------------------------------------------------
console.log('\nBootstrap a small society. Inspect the 7 base-mandatory roles.');
const roles = WasmSocietyRole.baseMandatory();
console.log(`  Base-mandatory roles (${roles.length}):`);
for (const r of roles) {
  if (typeof r.toJSON === 'function') {
    const j = r.toJSON();
    console.log(`    - ${j.name || j.role || JSON.stringify(j).slice(0,50)}`);
  }
  r.free?.();
}

const founderUuid = '11111111-1111-4111-8111-111111111111';
const charterHash = '0'.repeat(64);
const society = WasmSociety.bootstrap('demo-federation', charterHash, founderUuid);
society.addCitizen('22222222-2222-4222-8222-222222222222');
society.addCitizen('33333333-3333-4333-8333-333333333333');
console.log(`  Society bootstrapped with founder + 2 citizens added.`);

// Cleanup
[alice, bob, carol, davidT3, projectV3, aliceWallet, society].forEach(o => o.free?.());

console.log('\n=== Done. ===');
console.log(`
This is one library doing four jobs:
  1. EntityTrust  — track reputation evolution from observed behavior + witnesses
  2. T3/V3        — typed multi-dimensional trust/value scores with semantic axes
  3. ATP/ADP      — energy-coupled cost accounting for consequential actions
  4. Society+Role — formal social structure with the 7-role base taxonomy

What it's good for: any app where agents (human, AI, service) interact and
you need a principled — not ad-hoc — way to track reputations that evolve.
`);
