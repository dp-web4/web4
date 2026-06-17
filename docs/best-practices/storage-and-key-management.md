# Best Practice: Storage & Key Management — Full Enclosure

**Status:** Recommendation (strong). Not part of the core standard.
**Applies to:** any Web4 implementation that persists identity, credentials, trust state,
or governance state (hubs, identity wallets, enterprise deployments).

> A Web4 system is trust infrastructure. If its *own* state — member rosters, pinned keys,
> trust tensors, ledgers, the signing key itself — sits in plaintext on disk, then a single
> read of that disk dissolves the accountability the standard exists to provide. The
> recommendation below, **full enclosure**, closes that gap. It is how an implementation
> earns the trust the standard lets it claim.

## The recommendation, in one line

**Persist nothing in the clear except the minimum crypto-bootstrap metadata. Decrypt only
into memory. Fail closed.**

## The three invariants

A robust implementation should aim for all three:

1. **Total enclosure.** Every setting, identity, credential, and piece of state persists
   *only* inside an encrypted container. There should be **no plaintext config / state /
   identity files** on disk — the on-disk artifacts are encrypted blobs plus the small set
   of crypto-bootstrap metadata called out below. (This generalizes the common "encrypt
   secrets" rule to "encrypt *everything*" — in trust infrastructure, the non-secret state
   like the member roster is itself sensitive.)

2. **Tiered protection.** Opening the outer container should yield only the basics (config,
   metadata, and an *index* of what exists) — not automatically every item's plaintext.
   Implementations are encouraged to let individual items carry their own, stronger
   protection (an independent credential, a hardware key, and/or a freshness/liveness
   requirement) so that the most sensitive material requires an additional factor beyond the
   outer unlock. *(How a given product implements per-item gating is an implementation
   concern and lives in that product's own documentation.)*

3. **Memory-only unlock.** Decryption should happen *into process memory only, never onto
   disk*. No temp plaintext, no decrypted cache, no "unpack to a directory." While open,
   data lives in RAM; persistence always re-encrypts; on lock/exit, keys and plaintext are
   zeroized. If a consumer needs a file path, decrypt to a RAM-backed location and remove it
   after load — never leave decrypted bytes on persistent storage.

## Fail closed

- An encrypted store opened without the key must **refuse to open** — never silently fall
  back to plaintext, and never start in a degraded mode that serves state it can't actually
  decrypt. A locked system is meant to be *unlocked first, not operated*.
- A wrong key must be rejected (authenticated encryption — AEAD — makes this automatic).
- An explicit "no passphrase / NULL" choice (encrypt under an empty-derived key) may be
  *allowed* but must be **explicit and never the default** — defaulting to plaintext lets
  insecurity propagate silently and undermines the trust foundation.

## Don't duplicate sensitive data into derived caches

Search indexes, embeddings, denormalized views, and similar derived artifacts are a common
back door: the primary store is encrypted, but a derived cache re-exposes the same data in
the clear. Prefer to **hold sensitive data once**, in the enclosed store, and keep derived
artifacts to the minimum non-sensitive projection needed (e.g. an opaque id + a vector
index, with the human-readable fields re-attached from the enclosed store at query time).

## What may stay in the clear (accepted threat model)

Application-level (file) encryption protects **content**, not **shape**. After enclosure, an
attacker with disk read access but not the key still sees a small, well-understood residue.
The ruling on each:

| In the clear | Why it's acceptable |
|---|---|
| **KDF salts** | A salt is a public per-container randomizer; security rests on passphrase/key entropy × KDF cost. It is needed *before* the key exists (chicken-and-egg), so it must be clear. Zero security cost. |
| **AEAD nonces** | Modern AEAD ciphers (e.g. ChaCha20-Poly1305) are designed for public nonces. Must be clear. Zero cost. |
| **Format magic / version** | Enables corruption and version detection; obscurity here buys nothing. |
| **File existence, sizes, counts, mtimes** | A metadata/*shape* leak (a store exists, roughly how much state, rough activity timing). Inherent to file-level encryption — see the FDE note below. |

## Two complementary layers: app-level encryption + FDE

The residual leak above is *shape*, and the attacker who can exploit shape is the
**offline/physical** one (a stolen powered-off disk, a forensic image). That is the job of
**full-disk encryption (LUKS/dm-crypt/BitLocker)**, not the application vault. The two layers
are complementary by threat model:

- **Application-level enclosure** defends *content* against a **running-system** attacker —
  other processes/users, a store file copied off-box, an accidental commit to version
  control, a backup tarball. Content is plaintext only in the daemon's RAM while unlocked.
- **Full-disk encryption** defends *everything, including metadata and the salts*, against an
  **offline** attacker — but provides nothing once the system is booted and unlocked, which
  is exactly where the application vault earns its keep.

**Recommendation:** use both. FDE for at-rest metadata/shape; application-level enclosure for
content confidentiality on a running system. A public salt does not weaken this model, and
the shape the vault can't hide is covered by FDE.

## The crown jewel

The security ultimately rests on the **unlock secret** — a passphrase (portable, but
guessable if weak) or a **device/hardware key** (TPM/FIDO2-bound, which removes the
guessing attack entirely). Treat its entropy and custody as the primary control; everything
else is mechanism.

## Checklist

- [ ] No plaintext config/state/identity files on disk (only encrypted blobs + salts/nonces).
- [ ] Private keys encrypted at rest; never a raw key file.
- [ ] Decryption into memory only; no decrypted temp files; zeroize on drop.
- [ ] Fail closed on missing/wrong key; no silent plaintext fallback; NULL passphrase explicit-only.
- [ ] Derived caches/indexes carry no sensitive content (hold data once, in the enclosed store).
- [ ] Full-disk encryption enabled on the host (covers metadata/shape + the salts).
- [ ] 0600 on the store and its salt; restrictive perms on the data directory.
