# Hub environment

Every knob the hub daemon reads from the environment, in one place.

This file exists because the knobs were not *undocumented* — twelve of the
twenty-two were documented **in Rust module docstrings**, which is the right place
for someone reading `rate_limit.rs` and the wrong place for someone deciding how to
run the daemon. Four of the twelve switch off a safety check. A safety override that
only a source reader can find is the kind of flag that ends up set in a deployment
nobody remembers configuring.

Defaults below were read from the source, not remembered. Where the source states no
default, this file says so rather than inventing one.

## Safety overrides — read this section before setting anything in it

Each of these **disables a check that is on by default**. They exist for development,
forensics, or a deployment whose second factor lives outside the hub. None should be
set in an ordinary deployment, and each should be set deliberately, with a reason
someone else can read.

| Variable | Effect when set to `1` |
|---|---|
| `HUB_ALLOW_NO_LAW` | Serves **without a signed law**. This switches off the law gate itself — the check that everything else is measured against. The intended path is `hub set-law`. |
| `HUB_ALLOW_INSECURE_ORIGIN` | Accepts requests whose origin cannot be derived from the `Host` header — i.e. plain `http` for development. |
| `HUB_ALLOW_LOOPBACK_OPERATOR` | Accepts a loopback caller as the operator, on the theory that **host access (SSH) is the second factor**. That is a real argument, and it is only true where host access is actually restricted. |
| `HUB_ALLOW_CHAIN_ROLLBACK` | Permits the ledger chain to move backwards. Intended for **forensics**, not for running. |

Reachability is not authority — the hub's own posture. `HUB_ALLOW_LOOPBACK_OPERATOR`
is the one place that trade is made explicitly, which is exactly why it should be
visible here rather than only at its call site.

## Identity and operator access

| Variable | Default | Meaning |
|---|---|---|
| `HUB_ID` | source states none | Hub identity. |
| `HUB_PASSPHRASE` | none | Unlocks the hub's key material. **Never** commit it, put it in a unit file, or pass it on a command line that lands in shell history. |
| `HUB_OPERATOR_AUTH` | see `hub/README.md` | Operator authentication configuration. |
| `HUB_OPERATOR_TOKEN_TTL_SECONDS` | source states none | Lifetime of an operator token. The TTL check **fail-closes on a missing creation timestamp**, so it can be enabled later without locking out an existing operator. |
| `HUB_UNLOCK_VERIFIER` | see `hub/README.md` | Unlock verification. |
| `HUB_PROFILE` | see `hub/README.md` | Deployment profile. |
| `HUB_PUBLIC_BASE_URL` | see `hub/README.md` | Public base URL, when the hub is reached through a proxy or a name it cannot derive. |
| `HUB_RATIFIED_MANIFEST` | source states none | Ratified manifest to enforce. |

## Rate limiting and request size

Defaults from `hub/hub-daemon/src/rate_limit.rs`. Rate limiting is **on by default**.

| Variable | Default | Meaning |
|---|---|---|
| `HUB_RATE_LIMIT_ENABLED` | `1` (on) | Set to `0` to disable entirely. |
| `HUB_RATE_LIMIT_RPS` | `10` | Sustained requests per second, per IP. |
| `HUB_RATE_LIMIT_BURST` | `30` | Burst capacity, per IP. |
| `HUB_RATE_LIMIT_LOOPBACK_MULT` | `10` | Multiplier applied to the rate for loopback callers. |
| `HUB_MAX_BODY_SIZE` | 1 MiB | `Content-Length` cap, in bytes. |

## Paths

The hub does not search for its neighbours and does not enumerate known layouts. A
path it needs is either passed explicitly or derived from something on the machine
actually running.

| Variable | Meaning |
|---|---|
| `HUB_EXEC_PATH` | Explicit path to the hub executable, where a caller must name it rather than resolve it. |
| `CARGO_MANIFEST_DIR` | Set by Cargo during build and test. Not something to set by hand at runtime. |

Two notes that are easy to get wrong:

- **A wrong path does not fail loudly.** A spawn against a path that does not exist
  is `ENOENT`, and a caller that treats an absent component as "nothing to run"
  proceeds with the component silently disabled. Prefer an explicit value that is
  verified at startup over one discovered late.
- **Do not substitute an unrendered placeholder for a baked path.** A placeholder
  that never gets rendered fails exactly the same silent way as a stale absolute
  path. Render at install time, from a value the installing machine resolved.

## Setting them

The daemon's environment is whatever its supervisor gives it — **not** your shell.
Exporting a variable in a terminal does not reach a service the init system started.

- **systemd unit:** `Environment=HUB_RATE_LIMIT_RPS=25`, then
  `systemctl daemon-reload && systemctl restart <unit>`.
- **container:** the image's env / compose `environment:` block.
- **foreground, for development:** `HUB_ALLOW_INSECURE_ORIGIN=1 cargo run -p hub-daemon`.

Secrets (`HUB_PASSPHRASE`) belong in a secret store or a mode-600 file the unit reads
at start — not in the unit text, not in an image layer, not in Git.

## Verifying

Read the environment of the **running process**, not the unit file. A unit edited
after start is a real and silent divergence:

```
systemctl show <unit> -p Environment --value
```

If an override is set that you did not intend, treat it as a live finding rather
than a note: every variable in the first section above turns a check off.
