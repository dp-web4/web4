# Web4 Repository: Quick Reference Guide

**Analysis Date**: December 24, 2025  
**Repository Status**: HEALTHY RESEARCH CODEBASE  
**Health Score**: 8.5/10

## At a Glance

```
Repository: web4 (active AI trust-native distributed intelligence research)
Size: ~25 MB tracked, ~50 MB with git history
Files: 512 Python, 371 Markdown, 30+ JSON/YAML
Code: ~47,000 lines of active research
Tests: 218 test files with integration suite
Last Commit: Dec 22, 2025 (Session 84)
```

---

## Quick Navigation

### For Developers
**Start Here**: `/docs/GLOSSARY.md` → `/docs/LCT_DOCUMENTATION_INDEX.md` → `/game/README.md`

### For Reviewers
**Latest Work**: `/implementation/` (Session 84) → `/web4-standard/` → `/game/`

### For Contributors
1. Read `README.md` (vision + learning path)
2. Choose a track: `/game/` (simulation), `/web4-standard/` (spec), or `/implementation/` (research)
3. Follow session pattern: implement → test → document → commit

### For Adding Features
1. Check `/STATUS.md` for current gaps
2. Create session-numbered branch
3. Add to appropriate subsystem (game/ vs web4-standard/ vs implementation/)
4. Include tests + results.json
5. Commit with session label

---

## Repository Structure Map

### TIER 1: Active Primary Code (Last: Dec 22)
| Directory | Size | Focus | Status |
|-----------|------|-------|--------|
| `/web4-standard/` | 12 MB | RFC-style specification | VERY ACTIVE |
| `/implementation/` | 1.5 MB | Research session code | VERY ACTIVE |
| `/game/` | 2.8 MB | Society simulation engine | ACTIVE |

### TIER 2: Active Documentation (Last: Dec 17-19)
| Directory | Size | Focus | Status |
|-----------|------|-------|--------|
| `/whitepaper/` | 1.4 MB | Technical specification | MAINTAINED |
| `/docs/` | 852 KB | Current reference docs | MAINTAINED |
| `/proposals/` | 112 KB | RFC development | ACTIVE |

### TIER 3: Reference & Design (Last: Nov 20 - Dec 5)
| Directory | Size | Focus | Status |
|-----------|------|-------|--------|
| `/reference/` | 276 KB | Original concepts | LEGACY |
| `/forum/` | 1.4 MB | Design discussions | SEMI-ACTIVE |
| `/demo/` | 224 KB | Working UI prototype | REFERENCE |

### TIER 4: Archive & Build (Properly Ignored)
| Directory | Size | Focus | Status |
|-----------|------|-------|--------|
| `/archive/` | 136 KB | Old content | LABELED |
| `__pycache__/` | N/A | Bytecode (ignored) | IGNORED ✓ |
| `.pytest_cache/` | N/A | Test cache (ignored) | IGNORED ✓ |

---

## Four Development Tracks

### Track 1: Game Simulation (Tier 1)
**Location**: `/game/`  
**Purpose**: 4-Life society simulation for validating Web4 primitives  
**Key Files**: 
- `engine/` (25,557 lines of core simulation)
- 50+ `run_*.py` demo/test scripts
- `sage_empirical_data.json` research findings

### Track 2: Web4 Standard (Tier 1)
**Location**: `/web4-standard/`  
**Purpose**: RFC-style formal specification with reference implementation  
**Key Files**:
- `implementation/act_deployment/` (ATP protocol)
- `implementation/authorization/` (Trust permissions)
- `implementation/integration_tests/` (E2E validation)
- `testing/` (Test vectors, conformance)

### Track 3: Session-Based Research (Tier 1)
**Location**: `/implementation/`  
**Purpose**: Latest autonomous research session implementations  
**Pattern**: `sessionNN_trackM_*.py` + `sessionNN_trackM_results.json`  
**Latest**: Session 84 (Dec 22) - Attack vector analysis

### Track 4: Documentation (Tier 2-3)
**Location**: `/whitepaper/`, `/docs/`, `/reference/`  
**Purpose**: Technical foundation + specifications + historical context  
**Key Docs**: LCT identity spec, binding protocols, SAGE integration

---

## Activity Heat Map

```
VERY HOT (Dec 22):    web4-standard/, implementation/
HOT (Dec 17):         game/, docs/, whitepaper/, demo/
WARM (Dec 13-19):     CLAUDE.md, proposals/, STATUS.md
COOL (Dec 5):         reference/, most root docs
COLD (Nov 29):        competitive-landscape/ (stalled)
```

---

## What's Working Well ✓

- **Session-based development**: Clear naming, version progression
- **Test coverage**: 218 test files, integration suite
- **Documentation**: 371 markdown files, current specs
- **Git hygiene**: Proper .gitignore, clean history
- **Organization**: Clear tiers (active/reference/archive)
- **Modular structure**: Independent subsystems

## What Could Be Better

- **Architecture documentation**: Need `ARCHITECTURE.md` showing 4 tracks
- **Onboarding docs**: Need `MAINTENANCE.md` for session workflow
- **Directory deprecation**: `/reference/` needs notice "See /docs/ for current"
- **Archive consolidation**: Move `/competitive-landscape/` to archive
- **PDF organization**: Move forum PDFs to archive, keep nova/

---

## Deprecation Status

### No Danger
- ✅ Archive directory is small (136 KB) and well-labeled
- ✅ Reference directory is legacy but intentionally maintained
- ✅ All overlaps are intentional domain separation

### Consider Moving
- 📦 `/competitive-landscape/` (1.5 MB, incomplete, Nov 29)
- 📦 `/forum/*.pdf` (280 KB, design history, move to archive)

### Monitor
- 🔄 `/reference/` - Add deprecation notice pointing to `/docs/`
- 🔄 `/demo/` - Add notice "Maintained as reference implementation"

---

## Key Documents to Read

| Document | When | What You'll Learn |
|----------|------|------------------|
| `README.md` | First | Vision, learning path, why Web4 matters |
| `STATUS.md` | Planning | What exists, what works, what's missing |
| `SECURITY.md` | Before coding | Known vulnerabilities, threat model |
| `docs/GLOSSARY.md` | Learning | Term definitions (LCT, ATP, T3, MRH, etc.) |
| `docs/LCT_DOCUMENTATION_INDEX.md` | Deep dive | All identity-related documentation |
| `game/README.md` | Research | How simulation works, running demos |
| `THREAT_MODEL.md` | Security review | Attack vectors and mitigations |

---

## File Quality Metrics

| Metric | Score | Notes |
|--------|-------|-------|
| Organization | 8.5/10 | Clear structure, minor consolidation possible |
| Activity | 9/10 | Very active, well-documented |
| Documentation | 8/10 | Current where needed, manageable overlap |
| Code Quality | 7.5/10 | Research-grade, good tests |
| Git Hygiene | 9.5/10 | Excellent, no bloat or secrets |
| Deprecation Risk | 9/10 | Minimal dead code |
| Maintainability | 7.5/10 | Session-based, needs workflow docs |
| Onboarding | 7/10 | Good README, needs architecture diagram |

---

## Next Steps (Priority Order)

### This Week
- [ ] Move `/competitive-landscape/` to archive
- [ ] Add deprecation notice to `/reference/README.md`

### Next Sprint
- [ ] Create root-level `ARCHITECTURE.md`
- [ ] Create `MAINTENANCE.md` (session workflow)
- [ ] Move forum PDFs to archive/

### Quarterly
- [ ] Consolidate `/reference/` and `/docs/`
- [ ] Formalize test suite structure
- [ ] Add performance benchmarks

---

## For New Contributors

1. **Read first**: `README.md` + `STATUS.md`
2. **Pick a focus**: Game simulation? RFC spec? Security research?
3. **Check existing**: Browse `/implementation/` recent sessions
4. **Follow pattern**: Session-numbered branch, tests, results.json
5. **Test thoroughly**: All tests must pass
6. **Document**: Add session notes + commit message

---

## Clone & Setup

```bash
# Clone
git clone https://github.com/dp-web4/web4.git
cd web4

# Setup
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt  # if exists

# Explore
cat README.md
cat STATUS.md
cat docs/GLOSSARY.md
```

**Estimated clone time**: 2-3 minutes (50 MB)  
**Onboarding time**: 2-4 hours with docs

---

## Questions?

- **"Where's the main code?"** → `/game/engine/` or `/web4-standard/implementation/`
- **"What's being worked on?"** → Check `/implementation/sessionNN_*`
- **"Is this production-ready?"** → See `STATUS.md` - it's a research prototype
- **"How do I contribute?"** → Create session-numbered branch, follow patterns
- **"What's deprecated?"** → `/reference/` is legacy, see `/docs/` for current

---

**Last Updated**: December 24, 2025  
**Repository**: Active research, excellent health  
**Status**: Ready for collaborative development
