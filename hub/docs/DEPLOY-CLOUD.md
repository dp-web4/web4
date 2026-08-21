# Deploying a chapter hub to a managed host

**Audience**: chapter organizer who wants the hub reachable by members without running a machine.
**Profile**: `public-managed` — a platform terminates TLS and restarts your container when it feels
like it. Fly.io is the worked example because the `public-managed` archetype names it; the shape
applies to any container platform with a persistent volume and a secret store.

**Status of this document**: the configuration and the reasoning are derived from the hub's own
source and are marked where they are. The end-to-end deploy has **not** been run by the author —
every step that has not been executed is marked *(unverified)* rather than presented as tested.
Corrections from the first real deploy should land here as a PR.

---

## What you are deploying

Two planes, and the distinction decides the whole configuration
(`web4-standard/core-spec/interface-planes.md`):

| plane | what it serves | exposure | binding |
|---|---|---|---|
| **public** | tier-0 identity, the fleet page, member queries | public / member | `0.0.0.0:8770`, TLS by the platform |
| **operator** | law, roles, members, admission, manage | **operator** | `127.0.0.1:8772`, **never published** |

The operator plane is loopback **by construction**, not by configuration: `plane_addrs()` in
`hub-daemon/src/main.rs` builds it from `Ipv4Addr::LOCALHOST` regardless of what `--bind` says. You
cannot accidentally publish it, and you should not try to. You reach it by proxying into the machine.

## Key custody and restart survival — read this before you deploy

A sealed hub **boots locked**: the lock-gate refuses every request at 503 except a small **tier-0
allowlist**, and `hub unlock` ignites it. The allowlist is five paths, not one — it is
`locked_tier0_allows` in `hub-daemon/src/rest.rs`, and it is worth knowing exactly which, because one
of them decides how you monitor this deployment:

| tier-0 path (served while locked) | why |
|---|---|
| `/.well-known/web4-hub.json` | discovery — how an operator finds the hub id that ignition needs |
| **`/`** | the landing page renders the 🔒 from `is_locked()` + the in-memory law; it never touches the store |
| `/v1/hubs/{id}/unlock` | ignition itself |
| `/v1/hubs/{id}/law` | the signed law, from the clear in-memory projection |
| `/v1/hubs/{id}/.well-known/openid-credential-issuer` | public OID4VCI issuer metadata |

**`/` is on that list, so a locked hub answers `200` on `/`.** A human who opens it sees the lock; an
HTTP status check does not. Everything below that talks about proving ignition uses a *non-tier-0*
path for that reason. Where the vault key lives is the decision this profile turns on.

**Ruling (dp, 2026-08-18), in priority order:**

| tier | posture | status today |
|---|---|---|
| **1** | The passphrase lives in a **TPM or secure module** where one is available | **not implemented anywhere in the stack** |
| **2** | No secure module → **boot locked and wait for unlock** | **shipped — this is the hub's default behaviour** |
| **3** | Passphrase from the environment (`HUB_PASSPHRASE`) | works; a **temporary dev convenience**, tolerated for now, and **not a production-acceptable solution** |

Hardware binding is aspirational throughout the codebase, not available: `web4-core/src/crypto.rs:10`
says keys are *"designed to be hardware-bindable (TPM/SE) in production"*, `lct.rs:16` says the same
of LCTs, and `hub-lib/src/constellation.rs:104` refers to *"a future `hardware_evidence` layer"*.
Canon defines hardware as LCT capability level 5 (`lct-capability-levels.md`); no code binds a key to
it. So tier 1 is the target, not an option you can select today.

**Therefore, on a managed host today: tier 2. The hub boots locked and waits for you to ignite it.**

Say plainly what that costs, because it is the deciding property of this profile: a platform restart
at 3am leaves your chapter's hub answering 503 until a human ignites it through the proxy (§5). On a
free tier, where restarts are routine and unattended, that will happen. Mitigate it — do not paper
over it:

- set `auto_stop_machines = false` and `min_machines_running = 1` (already in the example config) so
  the platform is not restarting you for idleness;
- put a health check on **`/tools`** — not `/` — somewhere that notifies **you**, so the 503 reaches a
  person rather than waiting to be noticed by a member. `/` is tier-0 and answers 200 while locked, so
  a check pointed there reports healthy through exactly the outage you are trying to be paged for;
  `/tools` is public-plane and non-tier-0, so the lock-gate refuses it (pinned by
  `the_other_operator_pages_stay_refused_while_locked` in `hub-daemon/src/main.rs`);
- treat ignition as a two-minute operational task with a written procedure (§5), not an emergency.

### On `HUB_PASSPHRASE` (tier 3)

The daemon **will** self-ignite if `HUB_PASSPHRASE` is present in its environment — the env'd entry
point is `open_hub_store_async` → `store::store_key` → `identity::env_passphrase`
(`main.rs:1471-1486`), and such a hub never reaches the locked shell. It is documented here so you
recognise the behaviour, **not** as the recommended configuration.

The source names the cost: it *"parks the passphrase at rest beside the ciphertext it protects,"*
which is the whole reason the planned de-env'ing ("increment 6") exists. Per the ruling above this is
a **dev convenience**, tolerated temporarily, and **not production-acceptable** — do not ship a real
chapter on it merely because it is more convenient than being paged. If you use it while developing,
use a throwaway passphrase and a throwaway chapter.

## 1. Prerequisites

- The `web4` repo checked out (the image needs sibling crates `web4-core`, `web4-trust-core`,
  `web4-policy` — the Dockerfile copies all three).
- A platform account and CLI. Free allowances change; check your platform's current limits rather
  than trusting any number written here.

## 2. Configuration

```bash
cd web4                       # repo ROOT — the Docker build context
cp hub/fly.toml.example ./fly.toml
$EDITOR fly.toml              # set `app` and `primary_region`
```

`fly.toml` must sit at the repo root. The Dockerfile's build context has to include the sibling
crates, and the platform uses the config file's directory as the context.

## 3. Volume and secrets

```bash
fly apps create your-chapter
fly volumes create chapter_data --size 1        # durable chapter dir  (unverified)
```

**No passphrase secret is set** — that is tier 3, and this deployment is tier 2 (see *Key custody*).
The passphrase is presented interactively at genesis and at each ignition, and is never stored on the
host.

Use a generated passphrase you keep in a password manager. **If you lose it, the vault is
unrecoverable** — that is the point of a vault.

## 4. One-time chapter genesis

The image's entrypoint is the `hub` binary, so any subcommand can be run in place of `serve`. Genesis
must happen once, against the mounted volume, before the daemon can serve anything:

```bash
fly deploy                                       # builds and starts (will boot un-ignited)  (unverified)
fly ssh console -C "hub init /chapter/data"      # founding charter + sovereign identity     (unverified)
```

`hub init` resolves the passphrase from a TTY prompt (`HUB_PASSPHRASE` would also satisfy it, but
this deployment sets none) and seals the identity under it. `fly ssh console` gives you a terminal so
the prompt works; an empty value is allowed but must be explicit, and on a real chapter must not be
empty. Genesis currently mints all seven base-mandatory role LCTs and the hub
discards five of them (`hub-lib/src/init.rs:46`, pending a `web4-core` bootstrap parameter) — this is
known, harmless, and cosmetic in the ledger.

A hub with no law **refuses to serve** under `HUB_PROFILE=production`. Install a starter law:

```bash
fly ssh console -C "hub set-law /chapter/data /path/to/starter-law.yaml"   # (unverified)
```

`hub/examples/starter-law.yaml` is the worked example; `docs/HUB-LAW.md` explains the norms.

### Expect the first deploy to refuse to serve — that is the gate working

The production law gate (`production_law_gate`, `main.rs:1291`) is checked at the two moments its
answer is real: an **unlocked boot**, or **ignition** on a locked boot — where it fails closed
*before* the signer swap, so a lawless production hub never reaches a serving state. On this tier-2
deployment the check happens **at ignition**, which means:

- before genesis and law, the hub sits locked and refuses every non-tier-0 request at 503 — expected;
- with no law installed, `hub unlock` **refuses to ignite**: *"refusing to serve with NO hub law
  (acts/admissions ungated)"*. That refusal is correct — a production hub that would gate nothing
  does not start.

**Do not set `HUB_ALLOW_NO_LAW=1` to get past it.** That waiver switches off the very gate the
production profile exists to provide, and its documented meaning is that the operator is *knowingly*
accepting an ungated hub. It is not a startup workaround.

One related trap, worth knowing before it costs you an afternoon: on `--storage sqlite` the law lives
inside the vault, so a **locked** hub reports "no law" no matter what `hub set-law` wrote
(`main.rs:1268`). Because this deployment boots locked by design, that is the **normal**
pre-ignition state: "no law" on a locked hub means *locked*, not *lawless*. Check ignition before you
go looking for a law problem.

## 5. Reaching the operator plane

```bash
fly proxy 8772:8772 -a your-chapter     # (unverified)
# then open http://127.0.0.1:8772/admin
```

You are tunnelling to a loopback listener inside the machine. Nothing is published by doing this, and
closing the proxy closes the access. In production the operator plane also requires an operator token
(`public-managed` sets `operator_auth: "token"`), so the tunnel alone is not authority — which is the
point: reachability is evidence, never authority.

## 6. Verify

```bash
# The process is up and serving. This is ALL this proves — `/` is tier-0 and a
# locked, un-ignited hub answers it 200 as well.
curl -sf https://your-chapter.fly.dev/ >/dev/null && echo "public plane up"

# Ignition. `/tools` is public-plane and non-tier-0, so the lock-gate refuses it
# at 503 until the vault is open. 200 here is the thing you actually wanted to know.
curl -s -o /dev/null -w '%{http_code}\n' https://your-chapter.fly.dev/tools
```

Then confirm the two things a green check on `/` does **not** prove:

1. **The hub is ignited, not merely running.** `/` cannot answer this — it is served while locked.
   Use `/tools`: **503 means locked**, 200 means the vault opened. **A 503 after a restart is expected
   on this tier** — the machine came back and is waiting for you to ignite it (§5). It does not mean
   anything is broken.
2. **The law is loaded.** `/admin` (through the proxy) shows law version and norm count. A production
   hub that serves at all has a law, but check the version is the one you installed.

## 7. Upgrades

Deploy a new image and let the platform roll it. The chapter directory is on the volume and is not
touched by a redeploy. Two cautions:

- **Never let an older image roll over a newer one.** State formats move forward; an older binary
  against newer state fails at open. Pin the image you deploy.
- **Back up the volume before an upgrade** that crosses a storage or ledger change. The ledger is
  append-only and hash-chained, so a restore is coherent, but only if you have one.

## 8. What is not solved yet

Recorded here rather than left for the first operator to discover:

- **Semantic discovery needs a sidecar this path does not provision.** `find_members` reaches the
  membot sidecar at `WEB4_MEMBOX_URL` (default `http://127.0.0.1:8771`; a non-loopback value is
  refused unless `WEB4_MEMBOX_ALLOW_REMOTE=1`). A single container has no sidecar, so a hosted
  chapter would advertise discovery it cannot serve. Tracked as **#749**, with two acceptable
  postures: provision and health-check it, or advertise discovery as degraded. Do not ship a
  chapter on this path without picking one.
- **No hub release exists.** The only published tag is `web4 v0.2.0` (2026-05-16), which predates most
  of the hub, so this path builds from source. A tagged release with a published image would remove
  the build step entirely and is the single biggest reduction in friction available.
- **The end-to-end deploy is unverified** (marked throughout). The configuration follows from the
  source; the platform interactions have not been executed.
- **Memory sizing is a guess.** `512mb` is chosen for headroom, not measured. Trim only after
  watching a real deploy.
- **Backup and restore of the chapter volume has no runbook.** For a volunteer-run chapter whose
  ledger *is* the meeting record, this matters more than most of the above.
