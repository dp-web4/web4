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
  min_tier: host-key  # unknown | host-key | tpm2 | host+tpm2; see §5 Q1
```

Tiers rank `host+tpm2` ≥ `tpm2` > `host-key` > `unknown`. `host+tpm2` meets `min_tier: tpm2`: opening
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
  ranks below every `min_tier`, so nothing is held. A tier below `min_tier` is deleted at once and not
  used.
- **What "tpm2" means here.** The measured TPM seal has pcr_mask 0: it is bound to this machine's TPM
  chip, not to a measured boot state. It means "opens only on this machine's TPM", not "opens only on
  an untampered boot". PCR binding would break the seal at every firmware or kernel update; it is
  out of scope until a society asks for it.
- **No sealing backend** (no `systemd-creds`, or encryption fails): nothing is written. The hub keeps
  booting locked and logs why. The law may still say held, but this host can't honour it, and a
  default the host can't meet does not fall back to a plain file.
- **Fly / platform secret:** a later slice. The tier would be `platform-secret`, and the code reads
  the credential from the platform's mount instead of decrypting it.
- **What sealing protects, said plainly.** A host-key or TPM credential can't be opened on another
  machine, from a disk copy, or from a backup. It does **not** protect against a process running on
  the same host as the hub's own user: that process can call `systemd-creds decrypt --user` too. This
  is equally true of `LoadCredentialEncrypted=` in the unit, whose plaintext lands in a directory
  readable by that same user. **The hub's user account is the trust boundary.** A public hub should
  run as a dedicated service user that nothing else runs as. The runbook says so; the code can't
  enforce it.

### 3.3 When the secret is created: at a person's unlock

A running hub doesn't hold the passphrase. `try_unlock` drops it after deriving the keys. So the only
moment the hub can seal the passphrase is when a person presents it:

1. A person unlocks (`hub unlock`), as today.
2. After the signer swap and the law hydration, if the law says `held` (or says nothing), no
   `ignition.cred` exists, and a backend at or above `min_tier` is available, the hub seals the
   passphrase it is holding at that moment, then drops it.
3. The hub witnesses `IgnitionHeld { tier, by: <sovereign> }`.
4. **The person is told, at that moment.** The unlock response carries `held_ignition: { tier }` and
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
the held copy, and why (`law_off`, or `below_min_tier` from the file's own seal id).

- **An amendment the daemon witnesses** (`witness_law_amendment`, which every in-daemon law change
  goes through) asks that check right after the `LawAmended` append, and deletes a rejected copy with
  `IgnitionReleased { reason }`. If the delete fails, it logs an error and the amendment still stands.
  The ledger then says "off" while the disk still holds the secret, which is exactly the state §3.5
  repairs on the next boot. (No in-daemon route edits `ignition` today; offline `set-law` does. The
  check sits in the shared path so a future route can't skip it.)
- **Offline `hub set-law`** asks the same check after witnessing the amendment, then deletes the
  copy and witnesses `IgnitionReleased` through `HubSession`. The delete comes first, so a law that
  says "don't hold" never leaves a copy for the next boot, even if the record then fails.
- **`hub rotate-passphrase`** (offline, hub stopped) deletes `ignition.cred` before re-keying,
  because a copy sealed to the old passphrase would fail at the next boot and cost an attempt. It
  can't witness: it runs mid-rekey, with no signer. The next person's unlock re-seals the copy and
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
  they come to fix it. A held attempt does count as one failure in `unlock_gate`.
- **A failed held unlock leaves the hub up and locked,** never stopped, so the human path still works.
- **Check the effect, not the exit code.** `/tools` answers 200 only when unlocked; `/` answers 200
  even when locked. pub's acceptance test reads `/tools`.
- **What a reader sees.** `/.well-known/web4-hub.json` gains `held_ignition: "none" | "ok" |
  "failed"`, a state with no reason text. The reason goes only to the log, because the well-known
  document is public.

### 3.6 The record: how the hub was ignited

A new event, `HubIgnited { via: held | human | env, tier: Option<host+tpm2 | tpm2 | host-key | platform-secret> }`,
is witnessed at every ignition that reaches a signer:

- `held`, carrying the tier.
- `human`, through `/unlock`.
- `env`: the store opened at boot with `HUB_PASSPHRASE` set. That is 08-18's tolerated dev tier, and
  now it shows on the ledger.

A boot that opens a plaintext or NULL-keyed store records `env` only if `HUB_PASSPHRASE` was set.
Otherwise it records nothing, because there was no ignition.

The tier is the evidence that issue 729 asks for. A hub's LCT capability level can then be **derived**
from the newest `HubIgnited` and never claimed. That derivation is a follow-up, and this design only
makes the evidence exist.

Each new event kind needs a `BODY_EXEMPT` entry and a HUB-LAW.md row, both in the same commit.

### 3.7 The restart alert

A held unlock can fail too: the passphrase was rotated, the host was rebuilt, or the TPM was
cleared. A failed one leaves the hub dark in the same way a locked boot does. So
`held_ignition: "failed"` (and `locked: true` with no held credential, while the law says held) is
what a health check pages a person on. Wiring that check is the deployment's job (hub-watch on HUB,
pub's checklist on the public hub). This design only makes the state readable.

## 4. Slices

| Slice | What | Tests that must bite |
|---|---|---|
| **I1** | `IgnitionPolicy` in the law; the `HubIgnited` event (`human` and `env` only); `held_ignition` in well-known (always `"none"`). No sealing yet. | An old law parses and hashes the same; `/unlock` witnesses `human`; an env boot witnesses `env`; a plaintext boot witnesses nothing. |
| **I2** | The sealing backend behind a trait (`systemd-creds --user`, and a test double); seal at a person's unlock; boot unlock from `ignition.cred`; one attempt; failed → locked; law-off at boot → delete. | Double: seal → restart → held unlock → `/tools` 200; a corrupt cred → up and locked, `unlock_gate` charged exactly 1; law off + cred present → deleted after unlock; `min_tier: tpm2` on a host-key backend → nothing written; a `host+tpm2` header meets `min_tier: tpm2`; an unknown id → nothing held; a cred below `min_tier` at boot → used once, deleted, `below_min_tier` witnessed; the unlock response names the tier. |
| **I3** | Every law change asks `release_under`: a daemon amendment and offline `set-law` delete a copy the new law rejects (`held: false`, or a seal below a raised `min_tier`) and witness `IgnitionReleased`; `rotate-passphrase` deletes it before re-keying. No `hold`/`release` commands (§3.3, §3.4). | The check itself (none held, default, off, below, at the floor); a daemon amendment raising `min_tier` releases and one at the floor doesn't; offline `set-law` with `held: false` deletes and records `law_off`. `rotate-passphrase` is interactive (TTY) and untested. |
| **Acceptance** | pub, on `web4-hub-demo`, with its other self-unlock mechanism switched off so a 200 can come only from held ignition: restart → held unlock → `/tools` 200, and the seal id read from the file. | pub expects `ef4ac136` (`host+tpm2`); HUB's seat covers `host-key` (`55b9ed1d`). A system unit with `User=` (HUB's shape) stays unmeasured until HUB runs it, and the PR says so. |

## 5. Open questions

- **Q1, for dp: is `host-key` acceptable as held?** A fact for this, from pub: on a host with a TPM,
  the default seal is TPM-bound with no operator choice, so the strict reading only changes hosts
  without one. The 08-18 order says "TPM/secure module when
  available; when not, boot locked." Read strictly, a host without a TPM (HUB,
  most VPS and fly machines) never holds, and dp's 10-30 default of "held" would almost never apply.
  **Proposed:** `min_tier` defaults to `host-key`. 10-30 is the later ruling and is about exactly
  this, the tier is on the ledger, and capability is derived from it, so a host-key hub never claims
  hardware binding. A society that wants the strict reading sets `min_tier: tpm2`. If dp reads 08-18
  as still binding here, the default becomes `tpm2`, and the design is otherwise unchanged.
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
R: pass [construct: the cred opens only on this host for this user; reachability is not the basis]
W: pass [construct: sealing needs a person's successful unlock, and the law (signed, ledgered) decides held]
O: pass [construct: boot decrypt -> try_unlock, the same preflight as a person; a failure leaves the hub locked]
A: pass [construct: HubIgnited{via,tier} witnessed at each ignition; IgnitionHeld/Released at each change]
V: present [construct: law held:false; min_tier:tpm2 for a strict society; release_under on every law change deletes a rejected copy]
verdict: PASS, conditional on Q1 (dp)
```
