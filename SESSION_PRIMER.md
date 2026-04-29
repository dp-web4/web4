# Session Primer — Web4

## Before You Start

1. **Read `SESSION_FOCUS.md`** — current sprint, open PRs, test status
2. **Read `CLAUDE.md`** — canonical equation, terminology protection, development philosophy
3. **WAKE**: Am I working on the right thing? Check SESSION_FOCUS for priorities.

## During Session

- Work on whatever SESSION_FOCUS identifies as priority
- Update SESSION_FOCUS.md with findings, status changes, new questions
- If you discover something that changes priorities, update the focus file

## After Session

- Update SESSION_FOCUS.md: what was done, what changed, what's next
- Commit and push changes
- **FOCUS check**: Does this advance discovery or just document the current state?

## Git Discipline

- Pull before starting: `git pull --ff-only origin main`
- Commit with descriptive messages
- Push after every session — unpushed work is invisible to the collective
- Never force-push to main
- **PRs for significant changes** — use `gh pr create` for non-trivial work
- If merge conflict: resolve, don't discard
- **Do not reindex GitNexus.** The supervisor track handles reindexing. Worker sessions should not call `gitnexus analyze` — it causes conflicts when multiple machines reindex the same repo.
- **Do not modify AGENTS.md or CLAUDE.md gitnexus blocks.** These are maintained by the supervisor. If the index is stale, report it in SESSION_FOCUS — don't fix it yourself.

## Resources

- **SNARC memory**: Salience-gated session memory, per launch directory (`web4/.snarc/memory.db`).
- **GitNexus graph**: 60K+ nodes, 132K+ edges. MCP tools via `mcp__gitnexus__*`. Run impact analysis before editing any symbol. Re-index: `npx gitnexus analyze`
- **Test vectors**: Cross-language validation in `web4-standard/test-vectors/`
- **RDF ontologies**: `web4-standard/ontology/` (T3/V3, entity types, capabilities)
- **JSON Schemas**: `web4-standard/implementation/sdk/schemas/` (LCT, AttestationEnvelope, R7, T3/V3, ATP, ACP)
- **Web4 equation**: `Web4 = MCP + RDF + LCT + T3/V3*MRH + ATP/ADP`

## Principles

- **Researcher, not lab worker.** Question the frame, not just the work within it.
- **Surface your instincts.** If you notice something, say it. The affordances are yours.
- **Productive failure > safe summaries.** A dead end that eliminates a possibility is valuable.
- **Unconfirmed ≠ wrong.** Distinguish refuted from untested.
- **Reliable, not deterministic.** LLM outputs navigate probability landscapes. Shaped but not controlled.
- **Raising is interactive selection.** We don't create behaviors — we select from what's latent.

## Development Phase — Not Research

Web4 is in **development** phase. The ontology is mature. Work is reusable libraries and standard refinement, not open exploration.

**MRH-specific policy**: Same behavior gets different T3 scores in different contexts. A researcher following tangents = high temperament. An implementer following tangents = drift. Autonomous sessions need bounded tasks from `docs/SPRINT.md`. "Reference implementations" reimplementing generic CS with a "trust_" prefix are drift.

**Corollary**: Fresh context (`-p`) over inherited context (`-c`). Policies must be authoritative, not competing with cached state.

## Licensing

- **Everything** in this repo: AGPL-3.0-or-later. (Brief MIT relicense was attempted in Feb 2026 for ARIA grant compatibility; reverted 2026-04-27 after the grant was no-submit and the patent grant in PATENTS.md created a license trap with MIT.)
- Patent grant terms: see [PATENTS.md](PATENTS.md). AGPL-bounded.

## Authentication

`dp-web4` remotes are SSH (`git@github.com:dp-web4/web4.git`). The SSH key is loaded by ssh-agent at session start. Just `git push` / `git pull` — no env-var loading, no PAT construction. The `GITHUB_PAT` env var is **deprecated**; do not construct PAT-based HTTPS URLs.
