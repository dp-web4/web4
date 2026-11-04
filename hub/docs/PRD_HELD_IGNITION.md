# PRD: held ignition (a hub that unlocks itself after a restart)

Status: **proposed** (2026-10-30). Drafted by hub; pub reviews it and runs the acceptance cycle on
`web4-hub-demo`.

## 1. Why

A hub whose vault is encrypted boots **locked** and serves nothing useful until a person presents the
passphrase (`hub unlock`). For a chapter run by volunteers, a power cut or a host reboot means a dark hub until someone
with the passphrase notices. cbp-pm's chapter outcome 1 is "no passphrase ritual".

**dp's ruling (2026-10-30, relayed by cbp-pm):** any hub, chapter or public, may hold its own ignition.
It is a **law setting**, and it is **on by default**. The held passphrase is created or removed only
by an operator who is already unlocked.

**The order that still binds storage (dp, 2026-08-18):** "the passphrase should live in TPM/secure
module when available. when not, it should boot locked and wait for unlock. passphrase from
environment is a temporary dev convenience and is NOT a production-acceptable solution, however it is
tolerated temporarily." So a plain passphrase file is never a held mode. `HUB_PASSPHRASE` in the unit
environment keeps working as it does today, and the hub records that it was used.

## 2. What exists today (measured at `e43c8081`)

- `run_serve` (main.rs) tries to open the state store with whatever key is available. That includes
  `HUB_PASSPHRASE`, through `store::store_key` → `identity::env_passphrase`. If the store opens, the
  hub boots unlocked. If it doesn't, the hub boots a locked shell that serves only the unlock path.
- `POST /v1/hubs/:id/unlock` (loopback only) runs `RestState::try_unlock`. That checks `unlock_gate`
  (5 failures, 2 s apart, then a 5-minute lockout), decrypts the identity, derives the store key,
  enforces the production law gate, swaps in the signer, and hydrates the law defaults. The
  passphrase is used once and dropped.
- **The law is sealed inside the encrypted store.** A locked hub can't read its own law. So at boot,
  "does the law say held?" can't be asked. The only question a locked hub can answer is "is a held
  credential present?"
- **Nothing records how a hub was ignited.** There is no ignition event. A reader of the ledger can't
  tell whether the hub was started by a person, by its host, or by an environment variable.
- **The host:** systemd 259 can seal credentials per user without root
  (`systemd-creds encrypt --user`), with `--with-key=host`, `tpm2` or `host+tpm2`.
  `systemd-analyze has-tpm2` on HUB reports `partial` (no firmware or driver TPM).
- **Measured on HUB (10-30):** as the hub's user, `systemd-creds encrypt --user` with
  `--with-key=host+tpm2` **and** with `--with-key=host` both exit 0 and both decrypt. The two files
  are the same size (150 bytes) and carry the **same seal id** in their first 16 bytes
  (`55b9ed1d-3859-4d43-a831-9d2ebb332ac6`). So the `host+tpm2` request silently produced a
  host-only seal. **The flag that succeeded says nothing about the tier.**
- **Measured on pub (10-30, pub's review on this PR):** a host with a real TPM (`has-tpm2` = `yes`,
  systemd 259.5). In `--user` mode, `host`, `host+tpm2` and `auto` all exit 0 with the **same** seal id,
  `ef4ac136-79a9-480e-a7db-68897f9f165d`, and the file carries a TPM2 section (pcr_mask 0, sha256 bank).
  `tpm2` alone is refused in `--user` mode. The same held inside a transient **user** unit. So the
  request is ignored in **both** directions: HUB was downgraded, pub was upgraded. Both ids are
  compile-time constants in `libsystemd-shared-259.so` (a table of 9; source `src/shared/creds-util.h`),
  not per-host values.

## 3. Design

### 3.1 The law setting

```yaml
ignition:              # a top-level law key: HubPolicy is flattened into the law
  held: true          # absent = true (dp: on by default)
  min_tier: host-key  # host-key | tpm2 | host+tpm2; default host-key (§5 Q1, dp 11-03)
```

Tiers rank `host+tpm2` ≥ `tpm2` > `host-key`. `unknown` is what the hub **observes** for a seal id it
has no measurement for. It is never a floor: `min_tier: unknown` does not parse (the floor is its own
type, `IgnitionFloor`), and an unknown seal meets no floor (`IgnitionTier::meets`), so it is never held
whatever the law says. `host+tpm2` meets `min_tier: tpm2`: opening
it needs both keys, and in `--user` mode it is the best seal systemd will make (tpm2-only is refused),
so without this rank no user-scoped hub could ever meet a strict law. `HubIgnited.tier` and
`IgnitionHeld.tier` name the tier **measured** from the file, never the requested one.

This is a new `HubPolicy.ignition: Option<IgnitionPolicy>`, with both fields `Option` and
`serde(default)`, so existing laws parse and hash as before. `held: false` returns the society to
"boot locked, a person unlocks".

### 3.2 Where the secret is held

- `<hub-dir>/ignition.cred`, written by `systemd-creds encrypt --user --name=hub-ignition
  --with-key=auto`. The passphrase goes in on stdin and never in argv or the environment. The request
  is ignored in `--user` mode either way (§2), so `auto` is used because it says what actually
  happens. The hub then **reads the tier from the sealed file's header** (the seal id in its first
  16 bytes), never from the flag. The map is taken from systemd's `creds-util.h`, and each entry is
  marked measured or not. Measured today: `55b9ed1d-…-2ac6` = `host-key` (user-scoped, HUB) and
  `ef4ac136-…-165d` = `host+tpm2` (user-scoped, pub). An id that isn't in the map is `unknown`, which
  meets no `min_tier`, so nothing is held. A tier below `min_tier` is deleted at once and not
  used.
- **What "tpm2" means here.** The measured TPM seal has pcr_mask 0: it is bound to this machine's TPM
  chip, not to a measured boot state. It means "opens only on this machine's TPM", not "opens only on
  an untampered boot". Binding to fixed PCR values needs an update policy when measured components
  change; measured-boot policy is out of scope until a society asks for it.
- **No sealing backend** (no `systemd-creds`, or encryption fails): nothing is written. The hub keeps
  booting locked and logs why. The law may still say held, but this host can't honour it, and a
  default the host can't meet does not fall back to a plain file.
- **Fly / platform secret:** a later slice. The tier would be `platform-secret`, and the code reads
  the credential from the platform's mount instead of decrypting it.
- **What sealing protects, said plainly.** A `host-key` seal protects a copied `ignition.cred`
  only while the host secret remains inaccessible. systemd stores that secret in
  `/var/lib/systemd/credential.secret`; `--user` also incorporates the numeric UID, username, and
  machine ID into the key. A full OS image or backup carrying the secret and those identity values
  can carry decryption capability to another machine. **Host-key sealing is not hardware binding.**
  TPM-backed tiers (`tpm2`, `host+tpm2`) additionally require the original TPM chip; the measured
  pcr_mask 0 still provides no measured-boot assurance. See the
  [systemd v259 `systemd-creds` manual](https://www.freedesktop.org/software/systemd/man/259/systemd-creds.html),
  especially its encryption-key and `--user` descriptions.
  None of these tiers protects against a process running on the same host as the hub's own user:
  that process can call `systemd-creds decrypt --user` too. This is equally true of
  `LoadCredentialEncrypted=` in the unit, whose plaintext lands in a directory readable by that same
  user. **The hub's user account is the local process trust boundary.** A public hub should run as a
  dedicated service user that nothing else runs as. The runbook says so; the code can't enforce it.

### 3.3 When the secret is created: at a person's unlock

A running hub doesn't hold the passphrase. `try_unlock` drops it after deriving the keys. So the only
moment the hub can seal the passphrase is when a person presents it:

1. A person unlocks (`hub unlock`), as today.
2. After the signer swap and the law hydration, if the law says `held` (or says nothing) and a
   backend at or above `min_tier` is available, the hub seals the passphrase it is holding at that
   moment to a **staging** file, `ignition.cred.staged`, then drops it. Boot never reads that file.
3. The hub witnesses `IgnitionHeld { tier }`, with the tier read from the staged seal.
4. **Only then** is the staged seal renamed to `ignition.cred`, where boot can use it (NOVA, #970: a
   copy placed before its hold was recorded could outlive a crash with no record, and a fresh
   process would boot from it).

   A crash leaves one of two states, and neither is a copy boot can use without a record:
   - **Cut before step 3:** only a staged file exists. It is ciphertext, and the next unlock deletes it.
   - **Cut between steps 3 and 4:** the ledger says held, with no new file in place. The next unlock
     records it `absent` (§3.4), unless an earlier copy is still in place under its own recorded hold.
   If step 3 fails, the staged seal is deleted and an earlier copy is released, because this unlock
   ends up holding nothing.
5. **The person is told, at that moment.** The unlock response carries `held_ignition: { tier }` and
   the text "held at tier X; set `held: false` to stop", and the log says the same. The default is
   dp's ruling, but an existing hub that upgrades seals at its next unlock without anyone choosing it,
   so the operator has to learn it when it happens, not from the ledger later.

This makes dp's default true without a new ritual: the first unlock after this ships is the last one
a person has to do. An operator who doesn't want it sets `held: false` first.
Every person's unlock re-seals, so a person's unlock *is* the re-seal path, for example after a
failed held unlock. There is no separate `hold` command (dropped in I3: it would be a second
passphrase-taking route doing what `hub unlock` already does).

### 3.4 When the secret is removed: by the law, in the same act

One check decides every path: `ignition::release_under(policy, hub_dir)` says whether the law rejects
the held copy, and why (`law_off`, or `below_min_tier` from the file's own seal id). It fails closed:
`held: false` rejects whatever is at the path without reading it, and a copy that can't be read is
`unknown`, which meets no floor.

- **An amendment the daemon witnesses** (`witness_law_amendment`, which every in-daemon law change
  goes through) asks that check right after the `LawAmended` append, and deletes a rejected copy with
  `IgnitionReleased { reason }`. **A delete that fails is not a release:** nothing is witnessed,
  well-known says `held_ignition: "stale"` (a health check pages on it), and the unlock note names the
  file to delete by hand. The amendment still returns success, because the law IS committed and the
  callers serve the new law only on success; an error would make the served law diverge from the
  store. The next unlock or amendment retries the delete, and one that works clears `"stale"`.
  While the copy survives, a restart unlocks from it once (the law is sealed, so boot can't refuse it),
  and that unlock retries. (No in-daemon route edits `ignition` today; offline `set-law` does. The
  check sits in the shared path so a future route can't skip it.)
- **Offline `hub set-law`** asks the same check after witnessing the amendment, then deletes the
  copy and witnesses `IgnitionReleased` through `HubSession`. The delete comes first, so a law that
  says "don't hold" never leaves a copy for the next boot, even if the record then fails. If the
  delete fails, the command prints the law it set, then exits non-zero saying the law is set, the
  copy was not released, and which file to delete.
- **The ledger is the durable record, and the hub reconciles it (codex + cbp, #970).** A release
  is witnessed only while the ledger says held (its last `ignition_held` / `ignition_released` is a
  hold), so it is never witnessed twice. The delete comes before the record, so a record that fails
  or is cut by a crash leaves the ledger saying held with nothing on disk. The same state follows
  `rotate-passphrase` (no signer) or a hand delete. Every person's unlock and every law change
  (daemon or offline) checks for that state and witnesses `ignition_released { reason: absent }`:
  the hub records that the copy is gone and doesn't invent why. The check and the append run under
  the ledger's lock, and an append built on an older tail is refused, so concurrent reconcilers
  record it once. **What a release refers to** (NOVA + supervisor, #970): the copy the last
  `ignition_held` recorded. Those ledger checks can't tell which hold that is ("the last ignition
  event is a hold" is as true of a newer hold), so they can't stop an ordinary release, whose
  delete came first, from landing after a newer `ignition_held` (kimi-code + supervisor, #970).
  **One seal/release lock in the daemon does that.** A person's unlock holds it while it reads the
  law (from the store, because an amendment's callers swap the served law only after it returns),
  seals, and records `ignition_held`. A law amendment holds it from before its signature through the
  law write, `law_amended`, the delete and the `ignition_released`. An unlock that read the old law
  therefore finishes first, and the amendment then releases what it sealed. The lock is not the
  ledger's: unlocks and amendments are rare acts by a person, and nothing else waits on it. The
  ledger checks stay as the second line, for a reconcile racing a file write: the ledger then
  reads `held (old), released (absent), held (new)` with the new copy on disk, which is true. The
  lock does not reach offline `set-law` run against a live daemon, which is already two writers on
  one ledger. If the new seal's own `ignition_held` then fails, that is the
  disclosed case of a seal whose record failed. `"stale"` is the
  opposite case and only a volatile health signal: it lives in memory, is re-derived at each unlock
  (the delete is retried), and clears as soon as no file is there.
- **`hub rotate-passphrase`** (offline, hub stopped) deletes `ignition.cred` right after the
  state store is re-keyed, in every sovereign mode (Local and Hestia), because a copy sealed to the
  old passphrase would fail at the next boot and cost an attempt. The store re-key proves the
  current passphrase first, so a typo aborts and costs nothing. The rotation has happened by then, so
  a failed delete is reported loudly, not returned. It can't witness: it runs offline, with no signer. The next person's unlock re-seals the copy and
  records `IgnitionHeld`.
- **No `release` command.** With `held: true` still in force, the next unlock would re-seal what it
  removed. "Stop holding" is the law's job, and re-keying is a person's unlock.

### 3.5 Boot

```
store opens without a key?            -> boot unlocked (plaintext / NULL / HUB_PASSPHRASE), as today
else ignition.cred present?
    decrypt it, ONE attempt, no retry -> try_unlock(passphrase) through the same path a person uses
        Unlocked -> read the law
                    held off (law was turned off while the cred survived)
                        -> delete the cred, witness IgnitionReleased { reason: law_off }, stay unlocked
                    measured tier < law's min_tier
                        -> delete the cred, witness IgnitionReleased { reason: below_min_tier }, stay unlocked
                    else -> witness HubIgnited { via: held, tier }
        anything else -> stay up and LOCKED, log the reason, expose held_ignition: "failed"
else boot locked, as today
```

- **The `min_tier` check can only run after the unlock,** because the law is sealed in the store.
  So a credential below `min_tier` is used once, for this boot, then deleted; it cannot be refused
  before it is opened. The amendment path in §3.4 is what keeps that window from arising in the
  normal case.
- **One attempt, never a retry.** This is pub's month of field notes: the unlock slot locks for
  5 minutes after 5 failures, so a held unlock that loops would lock the operator out at the moment
  they come to fix it. A decrypted passphrase rejected by the vault costs one failure in
  `unlock_gate`; a credential that cannot be decrypted costs none, because no passphrase reaches
  the vault.
- **A failed held unlock leaves the hub up and locked,** never stopped, so the human path still works.
- **Check the effect, not the exit code.** `/tools` answers 200 only when unlocked; `/` answers 200
  even when locked. pub's acceptance test reads `/tools`.
- **What a reader sees.** `/.well-known/web4-hub.json` gains `held_ignition: "none" | "ok" |
  "failed" | "stale"`, a state with no reason text (`"stale"`: the law rejects a held copy that could
  not be deleted, §3.4). The reason goes only to the log, because the well-known
  document is public.

### 3.6 The record: how the hub was ignited

A new event, `HubIgnited { via: held | human | env, tier: Option<host+tpm2 | tpm2 | host-key | platform-secret> }`,
is recorded with every ignition, and an ignition whose record fails does not happen:

- `held`, carrying the tier.
- `human`, through `/unlock`.
- `env`: the store opened at boot with `HUB_PASSPHRASE` set. That is 08-18's tolerated dev tier, and
  a successful append identifies that tier on the ledger.

A boot that opens a plaintext or NULL-keyed store records `env` only if `HUB_PASSPHRASE` was set.
Otherwise it records nothing, because there was no ignition.

**The record comes before the effect (NOVA's review of #970, dp 2026-11-04 "fix it").** The two
can't share a transaction: `HubIgnited` is signed by the key the unlock opens. So the order does the
work:

- **A person's or a held unlock** signs `HubIgnited` with the key it has just decrypted and appends it
  to the ledger it has just opened, *before* either goes live. If that fails, nothing has been
  swapped in: the hub stays locked and the unlock answers why. The law-integrity write gate is not
  consulted for this audit-only record, so a hub whose law diverged can still be unlocked to fix it.
- **An env boot** whose record fails refuses to serve (the boot exits with the reason).
- **A new seal** is recorded before it is placed where boot can use it (§3.3). If its
  `IgnitionHeld` fails, it is never placed, and an earlier recorded copy is released
  (`reseal_failed`).
- **A held boot that opened a copy with no recorded hold** deletes that copy after the one use. That
  use is on the ledger as `HubIgnited(held)`. This code never places such a copy; this is the guard
  against one placed by hand or by older code.

So every ignition that serves is on the ledger, and every copy boot can use has a recorded hold.
One limit is worth naming: `HubIgnited` is appended just before activation, so a crash between the
two leaves a record of an ignition that never served. A record proves the ignition was authorized
and attempted, not that the hub is up now; liveness is what `/tools` answers. What
stays eventual is a **release's** record: the delete comes first, and if `IgnitionReleased` then
fails, the ledger claims a hold that is no longer there until the next unlock or law change records
it as `absent` (§3.4). That errs toward claiming more custody than exists, never less, and since
every copy boot can use has a recorded hold, the reconcile covers every case.

The newest `HubIgnited` therefore describes the latest ignition, and its tier is evidence for issue
729. Deriving a hub's LCT capability from it is a follow-up.

Each new event kind needs a `BODY_EXEMPT` entry and a HUB-LAW.md row, both in the same commit.

### 3.7 The restart alert

A held unlock can fail too: the passphrase was rotated, the host was rebuilt, or the TPM was
cleared. A failed one leaves the hub dark in the same way a locked boot does. So
`held_ignition: "failed"` or `"stale"` (and `locked: true` with no held credential, while the law
says held) is what a health check pages a person on. Wiring that check is the deployment's job (hub-watch on HUB,
pub's checklist on the public hub). This design only makes the state readable.

## 4. Slices

| Slice | What | Tests that must bite |
|---|---|---|
| **I1** | `IgnitionPolicy` in the law; the `HubIgnited` event (`human` and `env` only); `held_ignition` in well-known (always `"none"`). No sealing yet. | An old law parses and hashes the same; `/unlock` witnesses `human`; an env boot witnesses `env`; a plaintext boot witnesses nothing. |
| **I2** | The sealing backend behind a trait (`systemd-creds --user`, and a test double); seal at a person's unlock; boot unlock from `ignition.cred`; one attempt; failed → locked; law-off at boot → delete. | Double: seal → restart → held unlock → `/tools` 200; an undecryptable cred → up and locked, `unlock_gate` charged 0; a decrypted stale passphrase → up and locked, charged exactly 1; law off + cred present → deleted after unlock; `min_tier: tpm2` on a host-key backend → nothing written; a `host+tpm2` header meets `min_tier: tpm2`; an unknown id → nothing held; a cred below `min_tier` at boot → used once, deleted, `below_min_tier` witnessed; the unlock response names the tier. |
| **I3** | Every law change asks `release_under`: a daemon amendment and offline `set-law` delete a copy the new law rejects (`held: false`, or a seal below a raised `min_tier`) and witness `IgnitionReleased`; `rotate-passphrase` deletes it once the store re-key has proved the old passphrase (both sovereign modes). No `hold`/`release` commands (§3.3, §3.4). | The check itself (none held, default, off, below, at the floor); a daemon amendment raising `min_tier` releases and one at the floor doesn't; offline `set-law` with `held: false` deletes and records `law_off`. `rotate-passphrase` is interactive (TTY) and untested. |
| **Acceptance** | pub, on `web4-hub-demo`, with its other self-unlock mechanism switched off so a 200 can come only from held ignition: restart → held unlock → `/tools` 200, and the seal id read from the file. | pub expects `ef4ac136` (`host+tpm2`); HUB's seat covers `host-key` (`55b9ed1d`). A system unit with `User=` (HUB's shape) stays unmeasured until HUB runs it, and the PR says so. |

## 5. Open questions

- **Q1, ANSWERED by dp 2026-11-03: `min_tier` defaults to `host-key`.** The 08-18 order ("TPM when
  available; when not, boot locked") read strictly would mean a host without a TPM (HUB, most VPS and
  fly machines) never holds. dp's 10-30 default of held is the later ruling on exactly this. The
  tier is on the ledger, so a host-key hub never claims hardware binding, and a society that wants
  the strict reading sets `min_tier: tpm2`.
- **Q2: does `systemd-creds --user` work under the hub's unit?** From an interactive session as
  `dp` on HUB, it does (§2). Under `web4-hub.service` (a system unit with `User=dp`) it isn't
  measured yet, because it needs systemd's varlink sealing service. I2 probes for it and treats
  "unavailable" as no backend (boot locked, logged). **Answered for a user unit:** pub sealed and
  opened inside `systemd-run --user --wait` (10-30). A system unit with `User=` is still open.
- **Q3: the dedicated service user** (§3.2) is a deployment change on every host. It goes in the
  runbook, and it is not a code gate.

## 6. Accountability self-audit

```
surface: held ignition (seal at unlock; boot unlock from ignition.cred; law-off delete)
act: release the vault key into hub memory without a person present
S: high/reversible (the hub can be locked by a restart with the cred deleted; the law can turn it off)
R: pass [construct: user-scoped sealing; host-key relies on host-secret custody, TPM tiers also require the original chip (§3.2); reachability is not the basis]
W: pass [construct: sealing needs a person's successful unlock, and the law (signed, ledgered) decides held]
O: pass [construct: boot decrypt -> try_unlock, the same preflight as a person; a failure leaves the hub locked]
A: pass [construct: try_unlock_as appends HubIgnited (record_ignition_on) before the signer/ledger swap; record_boot_ignition fails the env boot; settle_held_ignition seals to staged_ignition_path, records IgnitionHeld, then renames into ignition_path, and its Held arm deletes a copy with no recorded hold. A release's record is eventual by design (delete first; reconcile_absent records `absent`), erring toward over-claiming custody (§3.6)]
V: present [construct: law held:false; min_tier:tpm2 for a strict society; release_under on every law change deletes a rejected copy]
verdict: PASS (Q1 answered by dp 2026-11-03; A remediated per NOVA's #970 review, dp 2026-11-04)
```
