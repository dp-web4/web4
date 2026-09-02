# Unattended judge demo

This is the shortest honest external demo path. A judge needs only a current
browser and the public `/client` URL. No Hestia install, wallet, account, or
operator approval is required.

## What the judge does

1. Open `/client`.
2. Generate a Web4 identity. The private key stays in browser storage.
3. Request membership. The demo law auto-admits the signed identity.
4. Open a topic or reply to one.
5. Follow **published law** to inspect the rules that admitted the act.
6. See the resulting ledger index beside the discussion entry.

This demonstrates real signing, law evaluation, admission, and ledger writes.
It is not a static simulation. The ledger is local, signed, hash-linked, and
verifiable; it is not externally anchored.

## Operator cutover

Apply the demo-specific law to the chapter before publishing the link:

```bash
hub set-law <chapter-dir> ./examples/judge-demo-law.yaml \
  --diff-summary "time-bounded unattended hackathon judging"
```

If the daemon is already running, reload the law through the existing operator
path and require both `reloaded: true` and `law_integrity: ok` in the response.
Then verify these from a clean browser profile:

- `/.well-known/web4-hub.json` reports the intended hub, unlocked and governed;
- `/client` loads without external assets;
- a new identity is admitted immediately;
- creating a topic returns a ledger entry and `/discuss` renders it;
- `hub verify-ledger <chapter-dir>` succeeds.

After judging, restore the ordinary starter law (closed admission) with another
witnessed `hub set-law`. Do not leave judge mode as the production default.

