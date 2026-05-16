# web4-trust-core npm smoke test

End-to-end verification that the `web4-trust-core` package on npm is consumable: installs from the public registry, bundles for Node via esbuild, exercises the WASM API, prints pass/fail.

Use this:
- After any new release of the npm package, to validate the publish worked end-to-end
- On any fleet machine, to verify the package installs and runs in that environment
- As a starting template for downstream consumers integrating the package

## Run

Any machine with **Node 20+** and **npm**:

```bash
cd web4/testing/wasm-npm-smoke
npm install
npm test
```

That's it. Expected output ends with `All checks passed.` and exit code 0 (25 checks across 4 sections).

The default `npm test` script runs Node directly with `--experimental-wasm-modules` (needed for the bundler-target WASM that the published package ships). An alternative bundled flow `npm run test:bundled` is included for documenting the esbuild path — but it currently fails because esbuild's `--loader:.wasm=copy` doesn't propagate the wasm-bindgen internal-imports correctly. Real-world bundler consumers (vite, webpack) handle this natively. The direct-Node path with `--experimental-wasm-modules` is what works without a real bundler.

## What it does

1. `npm install` pulls `web4-trust-core@^0.2.0` from npm (this is the published package, not a local path).
2. `npm test` runs `esbuild` to bundle `smoke.mjs` plus the WASM into a single executable bundle at `dist/smoke.bundle.mjs`, then runs that bundle with `node`.
3. The smoke test:
   - confirms the module loads
   - lists exported classes (EntityTrust, T3Tensor, V3Tensor, WasmSociety, WasmSocietyRole, WasmRoleAssignment, WasmATPAccount, WasmR7Action, WasmTrustStore)
   - instantiates `EntityTrust` and exercises its full lifecycle (constructor, updateFromOutcome, giveWitness, receiveWitness, applyDecay, free)
   - probes T3Tensor and V3Tensor construction + serialization
   - probes WasmSociety basic instantiation

## Why bundler-target (and what this means for direct Node usage)

The published `web4-trust-core` was built with `wasm-pack build --target bundler` (matches the 0.1.x build). That means:
- **Web app consumers** (vite, webpack, rollup, esbuild, parcel, etc.) — just `npm install web4-trust-core`, import it, the bundler handles the WASM. Standard usage.
- **Raw Node `require()` or `import()`** — does NOT work directly because the bundler-target output uses module-relative `.wasm` references that Node can't resolve without bundler help.

This smoke test handles that by using esbuild to bundle (which is what every real Node-side consumer would do anyway). If a use case ever demands direct Node-loadable WASM without a bundler step, we'd need to publish a parallel package (e.g., `web4-trust-core-nodejs`) built with `wasm-pack build --target nodejs`.

## When the wasm feature was missed

For the record (and so the next rebuild doesn't trip the same way): `web4-trust-core/Cargo.toml` gates the WASM bindings behind an **optional `wasm` feature**. A bare `wasm-pack build` produces an essentially-empty 1.4 KB module. The correct invocation is:

```bash
cd web4-trust-core
wasm-pack build --target bundler --release -- --features wasm
```

The `--` separates wasm-pack args from forwarded cargo args. Output size sanity check: the `web4_trust_core_bg.wasm` file in `pkg/` should be ~330 KB; if it's < 10 KB, the feature flag was missed.

## Fleet-wide deployment

The published npm package is publicly available. Fleet machines that want to use it from a JS context just install it as a dep:

```bash
npm install web4-trust-core
```

There is **no fleet-wide "global install"** needed and none recommended — npm packages are scoped per-project. The smoke test in this directory is the canonical example of how to integrate it.

If a specific fleet machine ends up doing heavy npm-based development (e.g., a SAGE web UI), `npm install -g esbuild` may be a useful one-time setup for fast bundle iteration.
