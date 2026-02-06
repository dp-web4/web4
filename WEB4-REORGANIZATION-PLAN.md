# Web4 Repository Reorganization Plan

**Created**: 2026-02-05
**Status**: DRAFT - Awaiting Review

---

## Executive Summary

The web4 repository has accumulated 137 root files and 80+ docs files from active R&D. Following HRM's successful cleanup (73 → 7 root files), this plan proposes a phased reorganization to:

1. Clean root to ~15 essential files
2. Fix terminology inconsistencies (ATP/ADP definitions)
3. Address broken links and overclaims
4. Reorganize docs by audience (why/what/how/history pattern)
5. Improve first-visitor navigation

---

## Phase 1: Terminology Fixes (Critical)

**Time estimate**: 30 minutes
**Risk**: Low
**Blocking**: Should be done first to establish baseline

### Issues Found

| File | Term | Current (Wrong) | Should Be |
|------|------|-----------------|-----------|
| `docs/GLOSSARY.md` | ATP | "Adaptive Trust Points" | "Allocation Transfer Packet" |
| `docs/GLOSSARY.md` | ADP | "Adaptive Development Points" | "Allocation Discharge Packet" |
| `game/engine/atp_metering.py` | ATP | "Attention Token Pool" | "Allocation Transfer Packet" |
| `whitepaper/WHITEPAPER_DISCREPANCIES.md` | ATP | "Alignment Transfer Protocol" | "Allocation Transfer Packet" |

### Actions

1. Update `docs/GLOSSARY.md` lines 42-47
2. Update `game/engine/atp_metering.py` line 3 comment
3. Update `whitepaper/WHITEPAPER_DISCREPANCIES.md` line 24
4. Add note to `docs/design/ATP-ADP-TERMINOLOGY-EVOLUTION.md` about fixes

---

## Phase 2: Fix Broken Links & Overclaims (Critical)

**Time estimate**: 1-2 hours
**Risk**: Medium (may require creating missing docs or softening claims)

### Broken Links

| Source File | Broken Link | Status |
|-------------|-------------|--------|
| `docs/LCT_DOCUMENTATION_INDEX.md` | `LCT_UNIFIED_PERMISSION_STANDARD.md` | File moved to `docs/specs/` |
| `docs/LCT_DOCUMENTATION_INDEX.md` | `LCT_IDENTITY_PHASE2_COMPLETE.md` | File moved to `docs/specs/` |
| `docs/LCT_DOCUMENTATION_INDEX.md` | `LCT_IDENTITY_PHASE3_COMPLETE.md` | File moved to `docs/specs/` |
| `docs/LCT_DOCUMENTATION_INDEX.md` | `LCT_E2E_INTEGRATION_COMPLETE.md` | File moved to `docs/specs/` |
| `README.md` line 91, 215, 342 | `THREAT_MODEL.md` | File at `docs/security/THREAT_MODEL.md` |

### Overclaims to Address

| File | Claim | Reality | Fix |
|------|-------|---------|-----|
| `README.md` line 117 | "LCT identity system (4 phases complete)" | Only Phase 1 documented | Change to "Phase 1 complete; phases 2-4 in progress" |
| `game/README.md` | "Scripts moved to 4-life repo" | Files still exist in web4/game | Clarify: "Reference implementation here; deployment copy in 4-life" |
| `docs/IMPLEMENTATION_STATUS.md` | "Last Updated: 2025-11-18" | 2.5 months stale | Update or mark as archived |
| `proposals/WEB4-001-production-readiness.md` | "implementation-complete" | Hardware binding pending | Clarify: "Software complete; hardware pending" |

### Date Inconsistencies

| File | Date Claimed | Action |
|------|--------------|--------|
| `README.md` | 2026-01-13 | Keep (most recent) |
| `STATUS.md` | 2025-12-17 | Update to current |
| `docs/IMPLEMENTATION_STATUS.md` | 2025-11-18 | Update or archive |

---

## Phase 3: Clean Root Directory (Major)

**Time estimate**: 2-3 hours
**Risk**: Low (moving files, not deleting)

### Current State: 137 files at root

```
79 session*.py files (research scripts)
17 test_session*.py files
36 session artifacts (.json, .log, .txt)
7 essential .md files
5 misc .py files (prototypes, hw providers)
Various other files
```

### Target State: ~15 files at root

**Keep at root**:
```
README.md
CLAUDE.md
STATUS.md
SESSION_MAP.md (or move to sessions/)
SECURITY.md
PATENTS.md
LICENSE
CITATION.cff
.gitignore
.private-context.md
```

### Create New Directories

```
sessions/
├── README.md              # Index of all sessions
├── active/                # Current work (session_200+)
├── archive/               # Completed research phases
│   ├── session_001_100/
│   ├── session_101_150/
│   └── session_151_200/
├── outputs/               # .json, .log, .txt results
└── prototypes/            # prototype_*.py files

tests/
├── sessions/              # test_session_*.py
├── fixtures/              # Test data
└── conftest.py

implementation/
├── hardware/              # sprout_hw_provider.py, thor_hw_provider.py
└── (existing content)
```

### Move Commands Summary

```bash
# Session files
git mv session*.py sessions/active/
git mv session*.json session*.log session*.txt sessions/outputs/
git mv prototype_*.py sessions/prototypes/

# Test files
git mv test_session*.py tests/sessions/

# Hardware providers
git mv *_hw_provider.py implementation/hardware/

# Misc cleanup
git mv act-federation-smoke.zip archive/
git mv WEB4_*.txt archive/
git mv *.png archive/ (if any)
```

---

## Phase 4: Reorganize docs/ Directory (Major)

**Time estimate**: 3-4 hours
**Risk**: Medium (many files, many potential broken links)

### Current State: 80+ files, topic-based

```
docs/
├── specs/           (15 files)
├── security/        (3 files)
├── design/          (10 files)
├── guides/          (4 files)
├── strategic/       (3 files)
├── articles/        (1 dir)
├── audits/          (1 file)
├── whitepaper-web/  (generated)
└── [27 loose files at root]
```

### Target State: Audience-based (HRM pattern)

```
docs/
├── README.md              # Navigation hub
├── START_HERE.md          # Quick orientation
│
├── why/                   # Vision, motivation
│   ├── README.md
│   ├── problem_statement.md
│   ├── web4_vs_web3.md
│   └── (from strategic/)
│
├── what/                  # Concepts, architecture
│   ├── README.md
│   ├── core_concepts/
│   │   ├── lct.md
│   │   ├── trust_tensors.md
│   │   ├── entities_roles.md
│   │   └── mrh.md
│   └── specifications/
│       └── (from specs/)
│
├── how/                   # Implementation guides
│   ├── README.md
│   ├── quickstart.md
│   ├── developer_guide.md
│   ├── agent_integration.md
│   └── (from guides/)
│
├── history/               # Evolution, decisions
│   ├── README.md
│   ├── design_decisions/
│   ├── research_notes/
│   └── (from design/)
│
├── reference/             # Technical details
│   ├── security/
│   ├── audits/
│   ├── protocols/
│   └── schemas/
│
├── GLOSSARY.md            # Central terminology
└── whitepaper-web/        # Keep as-is
```

### Migration Map

| From | To |
|------|-----|
| `docs/strategic/*` | `docs/why/` |
| `docs/specs/*` | `docs/what/specifications/` |
| `docs/design/*` | `docs/history/design_decisions/` |
| `docs/guides/*` | `docs/how/` |
| `docs/security/*` | `docs/reference/security/` |
| `docs/audits/*` | `docs/reference/audits/` |
| Loose concept files | `docs/what/core_concepts/` |

---

## Phase 5: Improve Navigation (New Content)

**Time estimate**: 4-6 hours
**Risk**: Low (adding, not changing)

### New Files to Create

#### 1. `docs/START_HERE.md`
Quick orientation for first visitors:
- 30-second explanation of Web4
- Audience routing table
- Key links by role

#### 2. `CONTRIBUTING.md` (at root)
- How to run tests
- PR workflow
- Terminology protection rules
- Where to find issues

#### 3. `docs/HOW/AGENT_INTEGRATION.md`
For AI agents:
- LCT acquisition
- Society membership
- ATP budget management
- Example workflows

#### 4. `docs/ENTERPRISE_READINESS.md`
For evaluators:
- Maturity by component
- Security status
- Timeline estimates
- Known gaps

### README.md Updates

Add audience routing table after status snapshot:

```markdown
## Quick Navigation

| You Are... | Your Goal | Start Here |
|------------|-----------|------------|
| New to Web4 | Understand the vision | [docs/START_HERE.md](docs/START_HERE.md) |
| Developer | Implement locally | [demo/](demo/) → [game/README.md](game/README.md) |
| Researcher | Study the theory | [STATUS.md](STATUS.md) → [whitepaper/](whitepaper/) |
| Enterprise | Assess readiness | [docs/ENTERPRISE_READINESS.md](docs/ENTERPRISE_READINESS.md) |
| AI Agent | Integrate | [docs/HOW/AGENT_INTEGRATION.md](docs/HOW/AGENT_INTEGRATION.md) |
| Contributor | Help the project | [CONTRIBUTING.md](CONTRIBUTING.md) |
```

---

## Phase 6: Cleanup & Verification

**Time estimate**: 1-2 hours
**Risk**: Low

### Actions

1. Run link checker across all .md files
2. Update CLAUDE.md with new directory structure
3. Create `MIGRATION_LOG.md` documenting what moved where
4. Update `.gitignore` for new directories
5. Clean `__pycache__`, `.pytest_cache` directories
6. Final commit with comprehensive message

### Verification Checklist

- [ ] Root has ≤15 files
- [ ] All internal links work
- [ ] Terminology is consistent (grep for old ATP/ADP definitions)
- [ ] README audience routing works
- [ ] docs/ has README.md at each level
- [ ] No orphaned files in archive/
- [ ] Tests still run

---

## Summary: Files Moved

| Category | Count | From | To |
|----------|-------|------|-----|
| Session scripts | 79 | root | sessions/active/ or sessions/archive/ |
| Session tests | 17 | root | tests/sessions/ |
| Session outputs | 36 | root | sessions/outputs/ |
| Prototypes | 2 | root | sessions/prototypes/ |
| Hardware providers | 2 | root | implementation/hardware/ |
| Misc files | 5+ | root | archive/ |
| **Total moved from root** | **~141** | | |
| Game directory | 65+ | game/ | archive/game-prototype/ |

| Category | Count | From | To |
|----------|------|------|-----|
| Strategic docs | 3 | docs/strategic/ | docs/WHY/ |
| Spec docs | 15 | docs/specs/ | docs/WHAT/specifications/ |
| Design docs | 10 | docs/design/ | docs/HISTORY/ |
| Guide docs | 4 | docs/guides/ | docs/HOW/ |
| Security docs | 3 | docs/security/ | docs/REFERENCE/security/ |
| Loose docs | ~27 | docs/ | sorted by topic |
| **Total docs reorganized** | **~62** | | |

---

## Execution Order

1. **Phase 1**: Terminology fixes (30 min) — immediate, no dependencies
2. **Phase 2**: Broken links & overclaims (1-2 hr) — immediate
3. **Phase 3**: Clean root (2-3 hr) — after phases 1-2 committed
4. **Phase 4**: Reorganize docs (3-4 hr) — after phase 3
5. **Phase 5**: New navigation content (4-6 hr) — after phase 4
6. **Phase 6**: Verification (1-2 hr) — final pass

**Total estimated time**: 12-18 hours

---

## Decisions Made

1. **SESSION_MAP.md**: Keep at root — shows scope of research
2. **Session organization**: Create `/research/` directory for current sessions (defer to later phase)
3. **docs/ naming**: Use lowercase (`why/`, `what/`, `how/`, `history/`)
4. **New content priority**: By relevance to "new social contract" governance mission
5. **game/ directory**: Archive — 4-life is now standalone. Document as "prototype that became 4-life"

### Additional Phase: Archive game/

Add to Phase 3:
```bash
# Archive game/ with documentation
echo "# Game Directory (Archived)

This directory contains the original prototype that evolved into the 4-life project.

**Status**: Archived as of 2026-02-05
**Active Development**: https://github.com/dp-web4/4-life

The game simulation demonstrated Web4 concepts (LCT, ATP, trust tensors) in a
playable format. The successful prototype led to 4-life as a standalone project.

See: archive/game-to-4life-evolution.md for the full history.
" > game/ARCHIVED.md

git mv game archive/game-prototype
```

---

## Appendix: Agent Analysis Summaries

### Terminology Agent Findings
- 4 files with wrong ATP/ADP definitions
- LCT, MRH, T3, V3, R6 all consistent
- Terminology evolution documented in docs/design/

### Overclaims Agent Findings
- 5 broken internal links
- 4 status contradictions
- 1 stale document (27 days old)
- "4 phases complete" claim not supported

### Directory Agent Findings
- 137 files at root (should be ~15)
- 80+ docs files need organization
- HRM pattern (why/what/how/history) recommended
- Session files should have lifecycle-based structure

### Navigation Agent Findings
- No explicit audience routing
- 30-second comprehension fails (too much scrolling)
- Glossary hard to find
- Missing: CONTRIBUTING.md, AGENT_INTEGRATION.md, ENTERPRISE_READINESS.md
- HRM outperforms web4 on navigation in 9/11 categories
