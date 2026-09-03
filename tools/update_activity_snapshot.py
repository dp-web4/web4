#!/usr/bin/env python3
"""Generate a cache-resistant plain-text repository activity snapshot.

Derive activity from Git history and write ordinary Markdown. Automated GitHub
readers can cache or mis-render GitHub's UI counters; committed text remains
inspectable, diffable, and attributable to a specific snapshot time.

Example from sibling full-history checkouts:
  python3 tools/update_activity_snapshot.py \
      --repo Web4=. \
      --repo Hestia=../hestia \
      --target ACTIVITY.md

The generator prefers each checkout's remote default branch (origin/HEAD) when
available, so a feature branch does not get counted as default-branch activity.
"""

from __future__ import annotations

import argparse
import datetime as dt
import pathlib
import subprocess
from dataclasses import dataclass

BEGIN = "<!-- activity-snapshot:begin -->"
END = "<!-- activity-snapshot:end -->"


@dataclass(frozen=True)
class RepoStats:
    label: str
    path: pathlib.Path
    ref: str
    head: str
    committed_at: str
    total: int
    last_7d: int
    last_30d: int


def git(path: pathlib.Path, *args: str) -> str:
    return subprocess.check_output(
        ["git", "-C", str(path), *args], text=True, stderr=subprocess.STDOUT
    ).strip()


def default_ref(path: pathlib.Path) -> str:
    try:
        return git(path, "symbolic-ref", "--quiet", "--short", "refs/remotes/origin/HEAD")
    except subprocess.CalledProcessError:
        return "HEAD"


def stats(label: str, path: pathlib.Path) -> RepoStats:
    path = path.resolve()
    ref = default_ref(path)
    head = git(path, "rev-parse", ref)
    committed_at = git(path, "show", "-s", "--format=%cI", head)
    total = int(git(path, "rev-list", "--count", head))
    last_7d = int(git(path, "rev-list", "--count", "--since=7.days", head))
    last_30d = int(git(path, "rev-list", "--count", "--since=30.days", head))
    return RepoStats(label, path, ref, head, committed_at, total, last_7d, last_30d)


def render(rows: list[RepoStats]) -> str:
    now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
    combined = sum(r.total for r in rows)
    lines = [
        BEGIN,
        "## Generated repository activity snapshot",
        "",
        f"**Generated:** {now}",
        "",
        "| Repository | Default-branch HEAD | HEAD commit time | Reachable commits | Last 7 days | Last 30 days |",
        "|---|---|---|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            f"| **{row.label}** | `{row.head[:12]}` | `{row.committed_at}` | "
            f"{row.total:,} | {row.last_7d:,} | {row.last_30d:,} |"
        )
    lines.extend(
        [
            "",
            f"**Combined reachable default-branch history ({' + '.join(r.label for r in rows)}): {combined:,} commits.**",
            "",
            "Method: `git rev-list --count <default-branch>` for lifetime history and the same command with `--since` for recent windows. "
            "The HEAD SHA and commit time make the snapshot independently checkable. Counts are evidence of repository activity, not a quality metric.",
            "",
            "`dp-web4/4-hub` is intentionally excluded from the combined count because it is a filtered mirror of `dp-web4/web4`; adding it would double-count upstream work.",
            END,
        ]
    )
    return "\n".join(lines)


def replace_block(text: str, block: str) -> str:
    if BEGIN in text and END in text:
        before, rest = text.split(BEGIN, 1)
        _, after = rest.split(END, 1)
        return before.rstrip() + "\n\n" + block + after
    return text.rstrip() + "\n\n" + block + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--repo",
        action="append",
        required=True,
        metavar="LABEL=PATH",
        help="repository checkout to measure; repeat for a cross-project snapshot",
    )
    parser.add_argument(
        "--target",
        action="append",
        required=True,
        metavar="PATH",
        help="Markdown file whose activity-snapshot block is replaced; repeat as needed",
    )
    args = parser.parse_args()

    rows: list[RepoStats] = []
    for item in args.repo:
        if "=" not in item:
            parser.error(f"--repo must be LABEL=PATH, got {item!r}")
        label, raw_path = item.split("=", 1)
        rows.append(stats(label.strip(), pathlib.Path(raw_path)))

    block = render(rows)
    for raw_target in args.target:
        target = pathlib.Path(raw_target)
        old = target.read_text(encoding="utf-8") if target.exists() else ""
        new = replace_block(old, block)
        target.write_text(new, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
