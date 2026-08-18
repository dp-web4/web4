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

## Restart survival — read this before you deploy

A sealed hub **boots locked**: every endpoint returns 503 except the unlock path, and `hub unlock`
ignites it. That is the right default for a laptop and the wrong one for a managed host, where the
platform restarts your container unattended and nobody is awake to re-ignite it.

**Ruling (dp, 2026-08-18): on a managed host, set `HUB_PASSPHRASE` from the platform's secret
store.** The daemon then opens the vault at boot and never reaches the locked shell
(`main.rs:1471-1486` — the env'd entry point is `open_hub_store_async` → `store::store_key` →
`identity::env_passphrase`).

Be clear about what that trades. The source names the cost: it "parks the passphrase at rest beside
the ciphertext it protects," which is why the planned de-env'ing ("increment 6") exists. On a managed
platform the trade is better than the same choice on a VPS, because the secret and the volume have
**different compromise paths** — an attacker who obtains the volume snapshot does not thereby obtain
the key. An attacker who obtains a shell in the running container obtains both. Judge accordingly,
and prefer a platform whose secrets are encrypted at rest and injected at process start rather than
written into the image.

If you would rather not make that trade, run without the secret and ignite manually after every
restart via the proxy in §5 — and expect a 3am restart to leave the hub answering 503 until someone
notices.

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
fly secrets set HUB_PASSPHRASE='...'            # per the ruling above (unverified)
```

Use a generated passphrase you also store in a password manager. **If you lose it, the vault is
unrecoverable** — that is the point of a vault.

## 4. One-time chapter genesis

The image's entrypoint is the `hub` binary, so any subcommand can be run in place of `serve`. Genesis
must happen once, against the mounted volume, before the daemon can serve anything:

```bash
fly deploy                                       # builds and starts (will boot un-ignited)  (unverified)
fly ssh console -C "hub init /chapter/data"      # founding charter + sovereign identity     (unverified)
```

`hub init` resolves the passphrase from `HUB_PASSPHRASE` (already in the environment from §3) and
seals the identity under it. Genesis currently mints all seven base-mandatory role LCTs and the hub
discards five of them (`hub-lib/src/init.rs:46`, pending a `web4-core` bootstrap parameter) — this is
known, harmless, and cosmetic in the ledger.

A hub with no law **refuses to serve** under `HUB_PROFILE=production`. Install a starter law:

```bash
fly ssh console -C "hub set-law /chapter/data /path/to/starter-law.yaml"   # (unverified)
```

`hub/examples/starter-law.yaml` is the worked example; `docs/HUB-LAW.md` explains the norms.

### Expect the first deploy to refuse to serve — that is the gate working

With `HUB_PASSPHRASE` set (§3) the hub boots **unlocked**, so the production law gate runs at boot
(`production_law_gate`, `main.rs:1291`). Until §4 has completed, the daemon refuses to serve with
*"refusing to serve with NO hub law (acts/admissions ungated)"*. That refusal is correct: a
production hub that would gate nothing does not start. Work through genesis and the law, and it comes
up.

**Do not set `HUB_ALLOW_NO_LAW=1` to get past it.** That waiver switches off the very gate the
production profile exists to provide, and its documented meaning is that the operator is *knowingly*
accepting an ungated hub. It is not a startup workaround.

One related trap, worth knowing before it costs you an afternoon: on `--storage sqlite` the law lives
inside the vault, so a **locked** hub reports "no law" no matter what `hub set-law` wrote
(`main.rs:1268`). If you ever run without the passphrase secret, "no law" on a locked hub means
*locked*, not *lawless* — check ignition first.

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
curl -sf https://your-chapter.fly.dev/ >/dev/null && echo "public plane up"
```

Then confirm the two things a green HTTP check does **not** prove:

1. **The hub is ignited, not merely running.** A locked hub answers 503, so a 200 on `/` means the
   vault opened. If you see 503 after a restart, the secret is not reaching the process.
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

- **No hub release exists.** The only published tag is `web4 v0.2.0` (2026-05-16), which predates most
  of the hub, so this path builds from source. A tagged release with a published image would remove
  the build step entirely and is the single biggest reduction in friction available.
- **The end-to-end deploy is unverified** (marked throughout). The configuration follows from the
  source; the platform interactions have not been executed.
- **Memory sizing is a guess.** `512mb` is chosen for headroom, not measured. Trim only after
  watching a real deploy.
- **Backup and restore of the chapter volume has no runbook.** For a volunteer-run chapter whose
  ledger *is* the meeting record, this matters more than most of the above.
