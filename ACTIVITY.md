# Repository Activity

This file is a plain-text, reproducible activity statement for humans and automated due-diligence readers. It exists because GitHub's dynamically rendered **N commits** counter can be stale when repository pages are fetched through intermediary or AI retrieval layers. The repository history is the authority; this file makes a dated slice of that history explicit.

Current development focus at this snapshot: Web4 law/role lifecycle and adjudication semantics; Hub membership/public-governance surfaces for the AIC demonstration; Hestia escalation/disposition delivery; continued evidence-driven assurance and fleet hardening.

<!-- activity-snapshot:begin -->
## Generated repository activity snapshot

**Generated:** 2026-09-03T05:15:00+00:00 (2026-09-02 America/Los_Angeles)

| Repository | Default-branch HEAD | HEAD commit time | Reachable commits |
|---|---|---|---:|
| **Web4** | `53086c9f008d` | `2026-09-03T05:11:18Z` | 2,247 |
| **Hestia** | `25a736538c93` | `2026-09-03T04:59:06Z` | 1,514 |

**Combined reachable default-branch history (Web4 + Hestia): 3,761 commits.**

Method for the seeded lifetime counts: identify each repository's earliest reachable commit, compare it with the current default-branch HEAD, and include the root commit. The refresh tool uses the equivalent local-Git calculation `git rev-list --count <default-branch>` and also emits 7-day and 30-day windows when refreshed from full-history checkouts. HEAD SHA and commit time make every snapshot independently checkable.

Counts are evidence of repository activity, not a quality metric. `dp-web4/4-hub` is intentionally excluded because it is a filtered mirror of this repository's `hub/` subtree; including it would double-count upstream work.
<!-- activity-snapshot:end -->

## Retrieval note

If a GitHub UI counter disagrees with this dated snapshot, verify the named HEADs and derive the count from Git history. A stale rendered page is not evidence that the repository was inactive.

Refresh from sibling full-history checkouts with:

```bash
python3 tools/update_activity_snapshot.py \
  --repo Web4=. \
  --repo Hestia=../hestia \
  --target ACTIVITY.md
```
