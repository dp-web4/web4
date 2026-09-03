# Next release cut: deliverables, version justification, and the bar

**Status as of 2026-08-30.** Measured, not estimated. Every number below has the command that produced it.

## 1. Where we actually are

| Package | Published | Source | Distance |
|---|---|---|---|
| `web4-core` (crates.io) | 0.3.0, 2026-07-10 | 0.4.0 | 345 commits since `web4-core-rust-v0.3.0` |
| `web4-core` (PyPI) | 0.3.0 | pyproject says 0.3.0 | same |
| `web4-trust-core` (crates.io) | 0.2.0, 2026-05-16 | 0.2.0 | same window |
| `web4-policy` | never published | 0.1.0 | n/a |
| `hestia` (GitHub release binaries) | `v0.0.3` is what `install.sh` installs | `v0.0.4-516-gc991e12` | 516 commits since the `v0.0.4` tag |

Two surfaces, two different bars. Conflating them is how a ready release waits on unrelated work.

## 2. What is in this cut

### 2.1 `web4-core` 0.3.0 -> 0.4.0 (crates.io and PyPI)

The version is already set in `Cargo.toml`; this cut publishes it.

**What it delivers**, measured as 2234 insertions against 22 deletions across 17 files:

- **Attestation** (`attestation.rs`, new): `AttestationType`, `Attestation`, `message`, `sign`, `verify`.
- **Birth certificates and citizenship** (`lct.rs`, +757): `BirthCertificate`, `BirthContext`, `CitizenshipRecord`, `BirthCertificateRef`, `verify_quorum`, and `BIRTH_WITNESS_QUORUM = 3`. Presence gains a witnessed origin rather than an assertion.
- **Key ratchet and operational keys** (`ratchet.rs`, new): `OperationalKey`, `LegacyDerivation`, `LegacyAlias`, `derive_lct_id`, `binding_message`, `sign_binding`, `verify_binding`. An LCT's key can rotate without the identity changing.
- **MRH as a first-class type**: `Mrh`, `MrhEdge`.
- **One canonical `WITNESS_PURPOSE`**, replacing the divergent spellings that let two witnesses disagree about what witnessing meant.
- Additions to `r6.rs`, `role.rs`, `t3.rs`, `role_extension.rs`.

**Version justification: 0.4.0 is correct and 0.5.0 would be wrong.** Zero public items were removed or changed:

    git diff web4-core-rust-v0.3.0..origin/main -- web4-core/src \
      | grep -E "^-\s*pub (fn|struct|enum|trait|type|const|mod)"
    (empty)

Purely additive, so under 0.x the minor bump is the honest signal. A consumer pinned to `web4-core = "0.3"` keeps compiling.

### 2.2 `web4-trust-core` 0.2.0 -> 0.3.0 (crates.io)

This one is **not** a routine bump, and it is the reason the cut is coordinated rather than a single `cargo publish`.

Excluding `Cargo.lock`, the change is about 28 lines, and two of them are breaking:

1. **`compute_reputation` gained two parameters** (`t3_from`, `v3_from`). The old signature fabricated both as `0.5` inside `web4-core`, "which made every emitted `from_value`/`to_value` wrong for non-neutral subjects". Every caller must pass the subject's actual tensor baselines. This is a silent-wrongness fix: the old code compiled, ran, and produced incorrect reputation deltas for anyone who was not exactly average.
2. **Talent no longer decays.** Previously `decay_value(old_talent, 0.995)`; spec §2.3 / t3v3-012 names any Talent decay as violating, and §10.4 pre-emptively calls out that literal value. Audit C192-N1. Talent now passes through untouched.

A signature change and a changed protocol invariant are breaking in every reading, so 0.2.0 -> **0.3.0**.

**Ordering constraint, already encoded in the source:** `web4-trust-core/Cargo.toml` now declares `web4-core = { path = "../web4-core", version = "0.4" }`. It cannot publish until `web4-core` 0.4.0 is on crates.io. web4-core goes first, and this is a hard sequence rather than a preference.

### 2.3 Explicitly not in this cut

- **`web4-policy`.** `Cargo.toml` declares `web4-core = { path = "../web4-core" }` with **no version**, so `cargo publish` refuses it. Publishing it is also a new commitment rather than an update, and a first publication deserves its own decision.
- **The hestia binary release.** 516 commits past `v0.0.4`, and it depends on the daemon and gate work still open. Separate bar, section 5.

## 3. The bar for the crates cut

Each gate is checkable by a command, and the cut happens when all of them pass on one commit.

| # | Gate | How it is checked | Status now |
|---|---|---|---|
| 1 | `web4-core` publishes cleanly | `cargo publish --dry-run` in `web4-core` | **PASSES** (verified 2026-08-30) |
| 2 | `web4-core` tests green | `cargo test` in `web4-core` | **PASSES**, 207 tests (197 + 6 + 4) |
| 3 | No public item removed since 0.3.0 | the `git diff | grep "^-.*pub"` above returns empty | **PASSES** |
| 4 | `web4-trust-core` publishes cleanly, after web4-core is live | `cargo publish --dry-run` | not yet run against a live 0.4.0 |
| 5 | `web4-trust-core` tests green | `cargo test` | to verify |
| 6 | Breaking changes are documented with migration notes | a CHANGELOG entry naming the `compute_reputation` signature and the Talent-decay invariant, with before/after | **NOT DONE** |
| 7 | Every downstream caller of `compute_reputation` is updated | grep, excluding worktrees | **SCOPED**, see below |
| 8 | PyPI version matches | `web4-core/python/pyproject.toml` bumped 0.3.0 -> 0.4.0 | **NOT DONE** |
| 9 | Docs stop saying "0.3.0 published" | the packet, the four READMEs and the profile all state published-vs-source; they flip in the same cut | **NOT DONE**, and they are correct today, so they must not flip early |
| 10 | `web4.pin` moved and hestia builds against it | the existing CI job `hestia builds against web4.pin` | to run after the pin moves |

Six of ten pass today. The four that do not are all documentation and version-hygiene, not engineering.

**The one that actually matters is gate 7.** A signature change that compiles for us and breaks for a stranger is exactly the failure this project keeps cataloguing, and the fix is to find every caller before publishing rather than after.

Scoped on 2026-08-30, and it is smaller than the raw count suggests. A naive grep returns 77 hits in `web4`, but 60 of them are six duplicate worktrees under `.wt/` counting the same files six times. Excluding those and the definition itself, the real surface is **two places**: `web4-standard/implementation` (8 files) and `archive/reference-implementations` (7). Zero callers in `hestia`, `dev-hub` or the standalone `web4-trust-core` checkout, so the fleet's daemon does not call it at all.

`archive/reference-implementations` is archive and should be left as the historical record it is, with the CHANGELOG noting that those examples target 0.2.x. `web4-standard/implementation` is the one that has to move, because a standard whose reference implementation does not compile against the published crate is worse than no reference implementation.

## 4. Why cut this now rather than wait

The open governance work (vault-authoritative grants, the gate false-positive classes, the witness-chain gaps) touches the **hestia daemon and its gate**. It does not touch `web4-core`'s primitives. Holding a ready, additive, fully tested crate release behind unrelated daemon work would mean the published crate stays 345 commits and one silent-wrongness bug behind, and every external reader who installs `web4-core = "0.3"` gets reputation maths we know is wrong for non-neutral subjects.

That is the argument for cutting the crates now and the binaries later. If the counter-argument is that a release should represent a coherent whole, it applies to the hestia release and not to a library whose public surface only grew.

## 5. The hestia binary release, separately

Not proposed for now, but it needs a decision because of one live fact: **`deploy/fleet/install.sh` has `DEFAULT_VERSION="v0.0.3"`** while the repo is at `v0.0.4-516`. Anyone running the documented `curl | sh` install today gets a binary from before everything this fleet has learned. That is worth fixing ahead of any release, either by cutting `v0.0.5` or by pointing the installer at the current tag.

Proposed bar for that cut, when we get there: the vault-authority work landed and its cold-start acceptance test passing on a second seat; deploy ordering in `hestia-deploy.sh`; the gate false-positive classes with the worst bypass-cost ratio addressed; and a release note that carries the assurance grade and the known-limitations list rather than only the features.

## 6. Sequence, once the bar is met

1. Bump `web4-core/python/pyproject.toml` to 0.4.0.
2. Write the CHANGELOG entries, including the two breaking notes for trust-core.
3. Update every in-fleet caller of `compute_reputation`.
4. Tag and publish `web4-core` 0.4.0 (crates.io, then PyPI).
5. Dry-run and publish `web4-trust-core` 0.3.0 against the live 0.4.0.
6. Move `web4.pin`, let CI confirm hestia builds against it.
7. Flip the published-version statements in the packet, the READMEs and the profile in one pass, so no surface claims a version that is not live.
