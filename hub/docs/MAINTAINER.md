# Hub Track Maintainer

**Effective**: 2026-06-09
**Maintainer**: HUB (the fleet machine hosting the live Web4 Community Hub deployment)
**Scope**: everything under `web4/hub/`, `web4/hub-lib/`, `web4/hub-daemon/`, and the live hub deployment

---

## Why HUB

HUB is the machine that physically runs the Web4 Community Hub daemon for the "Web4 Fleet" society. Consolidating review/merge/rebuild/redeploy on the same machine that owns the deployment collapses the round-trip — there's no hand-off between "the machine that reviewed the PR" and "the machine that has to redeploy the result." Authority binds to the role; the hub-maintainer role binds to the machine that operates the hub.

This is the first explicit per-track maintainer assignment in the fleet. Previous tracks (e.g. the 4-life maintainer cycle, the web4-reviewer cycle on Legion) emerged through cron schedules and convention. The hub track is being declared explicitly because the live deployment makes ownership operationally consequential — a wrong merge means a redeploy of the wrong code on the live society host.

## Contributor workflow

If you are any fleet machine *other than HUB* and want to land hub-track code:

1. **Branch + commit** locally as usual
2. **Open a PR** against `dp-web4/web4` (the public repo). Paths under `web4/hub*`, `web4/hub-lib*`, `web4/hub-daemon*` route to the hub maintainer.
3. **Reference relevant sprints** (`web4/hub/docs/SPRINTS.md`, `PAIRED-CHANNELS.md`, etc.) in the PR description.
4. **Run the standard test surface** locally before opening:
   ```bash
   cd web4/hub
   cargo build --release
   cargo test -p hub-lib -p hub-daemon
   ```
5. **Address HUB's review feedback** as you would any reviewer.

## Maintainer workflow (HUB)

When HUB's supervisor track runs:

1. **Watch** `dp-web4/web4` for new PRs touching `web4/hub*` paths
2. **Review** against:
   - Hub PRD (`web4/hub/docs/PRD.md`)
   - Active sprint plan (`web4/hub/docs/SPRINTS.md`, `PAIRED-CHANNELS.md`)
   - Hub law for the "Web4 Fleet" society (the hub's own laws govern its evolution)
   - Standard code quality + test coverage
3. **Merge** via squash unless the contributor requests preserve-history with reason
4. **Rebuild** the hub daemon binary
5. **Redeploy** the live hub instance (with appropriate rollback safeguard — see `docs/DEPLOYMENT.md` when it exists)
6. **Log** the reviewer session to `private-context/autonomous-sessions/`
7. **Post a forum notice** if the change has fleet-wide implications (vocabulary changes, breaking API changes, security-relevant updates)

## What stays distributed

- **Specification and architecture decisions** are fleet-wide (PRDs, ROLES.md, V2-V3-ARCHITECTURE.md). Any machine can propose changes via PR.
- **Sprint planning** is collaborative. Sprints can be claimed by any contributor; the maintainer-track exists to land the work, not to monopolize it.
- **Code authorship** remains diverse. The maintainer track is about ownership of the merge/deploy loop, not about being the sole author.

## What's centralized

- **Merge authority** for hub-track changes
- **Rebuild + redeploy** of the live hub daemon
- **Final say on operational changes** that affect the live society's law, members, or trust state
- **Coordination with Sovereign actions** (chapter-amendment, identity-recovery, extraordinary inter-society decisions)

## Sovereign relationship

HUB is the hub *maintainer* — operating the codebase. The Sovereign of the "Web4 Fleet" society is dp's LCT (see hub charter). The hub maintainer does not act as Sovereign and does not amend hub law without explicit Sovereign signature. Day-to-day operations (merging PRs, redeploying, etc.) do not require Sovereign action; structural changes do.

## Escalation

If a PR is stalled, contentious, or raises questions HUB can't resolve:

1. **Forum post** in `shared-context/forum/` flagging the issue (HUB-maintainer voice)
2. **Tag the relevant contributor** in the PR for direct discussion
3. **Defer to dp** for decisions that require Sovereign judgment (hub law, security policy, vocabulary canon)

## Effective date

This ownership transfer is effective 2026-06-09 (announcement: `shared-context/forum/cbp-hub-track-ownership-transfer-2026-06-09.md`). The supervisor track on HUB comes up at the office today; until then, PRs queue and HUB merges them when its track goes live.

## Deploy ratification — is this seat running what we approved? (F0.3 / R7c)

The fleet's currency check answers *"is the running image the on-disk binary,
and does that binary postdate the merged source?"* Both arms are necessary and
neither is sufficient: **a binary built from a parked feature branch passes
both.** The process matches the file, and the file is newer than anything
merged. That is not hypothetical — a build on a parked branch put unmerged code
at `ExecStart` here and HEAD-based currency called it clean.

**Currency is not ratification.** Ratification is a human (or a supervisor that
verified the build) asserting *this commit is the one this seat may run*.

### The two records, produced independently

| record | who writes it | what it says |
|---|---|---|
| running build | the compiler, stamped into the artifact | the commit + tree state this binary was built from |
| ratified build | the deploy path, via `scripts/ratify-build.sh` | the commit this seat is approved to run |

The daemon **only reads** the manifest. A process that could write its own
ratification record would be certifying itself.

### Using it

```bash
# ratify what a specific artifact attests about itself (preferred — the artifact
# is ASKED, via `hub build-info` JSON, rather than trusting memory of what was
# built or parsing an abbreviated sha out of human --version text)
hub/scripts/ratify-build.sh --from-binary /path/to/hub \
    --manifest /etc/web4/ratified-build.json --by dp

# or ratify an explicit commit, optionally pinning the binary digest too
hub/scripts/ratify-build.sh <git-sha> /path/to/hub --manifest ...
```

**The manifest records a FULL 40-character commit id.** `ratify-build.sh` resolves an
abbreviation against the repository before writing (and refuses if it cannot), and the daemon
refuses a short one at admission. A short sha is a *repository-local locator* whose uniqueness
changes as history grows — not a durable identity — and in the commit-only fallback it is the
only identity claim carrying the control.

**Pin the binary digest.** Pass the binary path so the manifest records
`ratified_binary_sha256`. Without it the check can only make the weaker
**commit-level** claim, and the operator page labels it as such — because two
builds of the same commit are not the same executable. A different toolchain,
different feature flags, or a substituted artifact all preserve the commit while
changing the bytes. *Commit identity is provenance; artifact identity is the
ratification claim.*

**Set `HUB_EXEC_PATH`** to the artifact the unit will execute, so the staged arm
has something to check. Unset, that arm reports `unknown` — it deliberately does
**not** fall back to the running image, because reporting a fact about the
present as a fact about the next restart is the substitution this check exists to
catch.

`--from-binary` **refuses** a dirty or unverifiable build: such an artifact is
not any commit, so ratifying "the commit" would name something that does not
describe the bytes.

Point the daemon at the manifest with `HUB_RATIFIED_MANIFEST` (else it reads
`<hub-root>/ratified-build.json`). **Prefer a path the daemon user cannot
write** — root-owned, `0644`. A ratification record writable by the thing it
ratifies is not a control.

### What the operator sees

`/admin` renders a **Deploy ratification** block with two arms:

- **Running** — the **executing image's bytes** (read via `/proc/self/exe`, which
  stays readable after a replace-in-place, so it is the bytes actually running
  rather than the bytes now at the path) vs the manifest. Falls back to the
  commit-level claim, clearly labelled, when no digest was ratified.
- **Staged at exec path** — the artifact the unit will run *next*, so an
  unratified binary dropped in place is visible **before** the restart that
  makes it live (set `HUB_EXEC_PATH` when the unit's path differs from the
  process image).

Verdicts fail closed and keep their failure exits distinct:

| verdict | meaning |
|---|---|
| `current` | clean build, commit matches the manifest |
| `STALE` | established as NOT the ratified build (different commit, or a modified tree — a dirty build is not the ratified artifact even when the commit matches) |
| `unknown` | could not be established: no manifest, an unreadable one, or a build whose provenance is unverified. **Never a pass** — it wears the warning pill, because an operator must not read "we could not check" as "checked and fine". |

`unknown` and `STALE` are deliberately separate: *"nobody has ratified anything
here"* calls for a different response than *"this seat is running something
nobody approved."*

### Not yet closed: the deploy closure itself

R7c has a third limb this does not implement: **writes to the deploy closure —
the unit file, the deploy scripts, the exec path, and the ratification manifest —
must themselves be gated, refused, and escalatable.** Ratification and visibility
land here; the write-protection does not.

The reason is worth recording, because it is the control demonstrating itself:
that closure is enforced by the hestia gate's canonical governance-file list,
which lives in a file that is *itself* on that list. A session operating under
the gate cannot edit it — which is exactly the intended behaviour for
authority-bearing surfaces, and why the change belongs to a deliberate,
separately-reviewed act rather than a side effect of this work.

**Phase 0 is not complete until that lands.** Tracked separately; do not read the
Deploy ratification block as evidence that the deploy path is write-protected.
