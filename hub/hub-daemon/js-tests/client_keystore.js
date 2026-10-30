// /client's key store, run in node: real WebCrypto, a minimal in-memory IndexedDB.
// Usage: node client_keystore.js <a file holding KEYSTORE_JS then CLIENT_JS>. Run by the daemon test
// the_client_moves_an_old_key_once_and_keeps_every_key_non_extractable.
'use strict';
const fs = require('fs'), vm = require('vm');
const src = fs.readFileSync(process.argv[2], 'utf8');
const assert = require('assert');

function makeIdb(failPut) {
  const dbs = {};
  return {
    open(name) {
      const req = {};
      setTimeout(() => {
        const fresh = !dbs[name];
        const stores = dbs[name] || (dbs[name] = {});
        const db = {
          createObjectStore(n) { stores[n] = new Map(); },
          close() {},
          transaction(n, mode) {
            const tx = {};
            const store = {
              get(k) { const r = { result: stores[n].get(k) }; return r; },
              put(v, k) { if (failPut) { setTimeout(() => tx.onabort && tx.onabort()); return {}; }
                          stores[n].set(k, v); return { result: k }; },
              delete(k) { stores[n].delete(k); return { result: undefined }; },
            };
            tx.objectStore = () => store;
            tx.error = new Error('quota');
            setTimeout(() => { if (!failPut || mode === 'readonly') tx.oncomplete && tx.oncomplete(); });
            return tx;
          },
        };
        req.result = db;
        if (fresh && req.onupgradeneeded) req.onupgradeneeded();
        req.onsuccess();
      });
      return req;
    },
    dbs,
  };
}

function makeEnv(failPut) {
  const ls = new Map();
  const el = () => ({ innerHTML: '', textContent: '', className: '', value: '', href: '',
    classList: { add() {}, remove() {} } });
  const els = {};
  const ctx = {
    crypto: globalThis.crypto, TextEncoder, Uint8Array, JSON, Promise, String, Object, Array, Error, setTimeout,
    console,
    indexedDB: makeIdb(failPut),
    localStorage: { getItem: k => (ls.has(k) ? ls.get(k) : null), setItem: (k, v) => ls.set(k, String(v)), removeItem: k => ls.delete(k) },
    navigator: { storage: { persist: () => Promise.resolve(true) } },
    document: { querySelector: s => (els[s] || (els[s] = el())), addEventListener() {} },
    fetch: () => Promise.reject(new Error('offline')),
  };
  vm.createContext(ctx);
  vm.runInContext(src, ctx);
  return { ctx, ls };
}

const hex = b => [...new Uint8Array(b)].map(x => x.toString(16).padStart(2, '0')).join('');
const run = (ctx, code) => vm.runInContext(code, ctx);

(async () => {
  // 1. An old page's extractable JWK moves once, as the same key, and the JWK is deleted.
  const kp = await crypto.subtle.generateKey({ name: 'Ed25519' }, true, ['sign', 'verify']);
  const pubHex = hex(await crypto.subtle.exportKey('raw', kp.publicKey));
  const privJwk = await crypto.subtle.exportKey('jwk', kp.privateKey);
  const old = { lct_id: 'lct-1', pubHex, privJwk };
  const { ctx, ls } = makeEnv(false);
  ls.set('hestia_hub_id', JSON.stringify(old));
  const id = await run(ctx, 'loadID()');
  assert.strictEqual(id.lct_id, 'lct-1'); assert.strictEqual(id.pubHex, pubHex);
  assert.strictEqual(id.priv.extractable, false, 'migrated key must be non-extractable');
  await assert.rejects(crypto.subtle.exportKey('jwk', id.priv), 'exporting a migrated key must fail');
  const msg = new TextEncoder().encode('nonce{"a":1}');
  const sig = await crypto.subtle.sign('Ed25519', id.priv, msg);
  assert.ok(await crypto.subtle.verify('Ed25519', kp.publicKey, sig, msg), 'same key signs');
  assert.strictEqual(ls.has('hestia_hub_id'), false, 'the JWK is deleted after the move');
  const again = await run(ctx, 'loadID()');
  assert.strictEqual(again.lct_id, 'lct-1', 'the second load comes from IndexedDB');
  console.log('ok 1 migration: same key, non-extractable, JWK deleted, reload from IndexedDB');

  // 2. A failed store keeps the JWK: nothing is lost if IndexedDB refuses.
  const f = makeEnv(true);
  f.ls.set('hestia_hub_id', JSON.stringify(old));
  await assert.rejects(run(f.ctx, 'loadID()'));
  assert.strictEqual(f.ls.has('hestia_hub_id'), true, 'JWK kept when the store fails');
  console.log('ok 2 a failed store leaves the old JWK in place');

  // 3. A fresh identity is non-extractable, stored in IndexedDB, and never in localStorage.
  const g = makeEnv(false);
  await run(g.ctx, 'genID()');
  const gid = await run(g.ctx, 'loadID()');
  assert.ok(gid && gid.priv.extractable === false && /^[0-9a-f]{64}$/.test(gid.pubHex));
  assert.strictEqual(g.ls.size, 0, 'nothing written to localStorage');
  console.log('ok 3 a new identity is non-extractable and lives only in IndexedDB');

  // 4. Forget removes both stores.
  g.ls.set('hestia_hub_id', JSON.stringify(old));
  await run(g.ctx, 'forget()');
  assert.strictEqual(await run(g.ctx, 'idbGet()'), undefined);
  assert.strictEqual(g.ls.size, 0);
  console.log('ok 4 forget clears IndexedDB and any old JWK');

  // 5. esc escapes quotes, so a topic id cannot break out of a data attribute.
  assert.strictEqual(run(g.ctx, 'esc(`a"b\'c<d>`)'), 'a&quot;b&#39;c&lt;d&gt;');
  console.log('ok 5 esc covers quotes');

  // 6. A corrupt old key is named as such and left in place, every time it is loaded.
  for (const bad of ['{not json', JSON.stringify({ lct_id: 'lct-1', pubHex, privJwk: { kty: 'OKP' } })]) {
    const c = makeEnv(false);
    c.ls.set('hestia_hub_id', bad);
    for (let i = 0; i < 2; i++) {
      await assert.rejects(run(c.ctx, 'loadID()'), { message: 'LEGACY_UNREADABLE' });
    }
    assert.strictEqual(c.ls.get('hestia_hub_id'), bad, 'the unreadable key is kept');
    assert.strictEqual(await run(c.ctx, 'idbGet()'), undefined, 'and nothing half-moved');
  }
  console.log('ok 6 a corrupt old key is named and kept');
})().catch(e => { console.error('FAIL', e); process.exit(1); });
