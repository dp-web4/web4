# Web4 Repository Cleanup Plan

**Date**: 2026-02-05
**Status**: Analysis Complete, Ready for Execution

---

## Summary of Issues

### Issue 1: `hardbound/` Directory in Public Repo

**Problem**: Enterprise-specific code exists in the public web4 repository.

**Location**: `/home/dp/ai-workspace/web4/hardbound/`

**Contents** (112+ files):
| File | Size | Description |
|------|------|-------------|
| `federation.py` | 131KB | Core federation logic |
| `attack_simulations.py` | 1.7MB | Security testing simulations |
| `economic_federation.py` | 27KB | Economic federation models |
| `federation_binding.py` | 26KB | Federation entity binding |
| `federation_discovery.py` | 40KB | Federation node discovery |
| `federation_health.py` | 26KB | Health monitoring |
| `federation_recovery.py` | 27KB | Recovery protocols |
| `cascading_failure.py` | 30KB | Failure cascade analysis |
| `cross_federation_audit.py` | 24KB | Cross-fed auditing |
| `governance_*.py` | ~42KB | Governance systems |
| `admin_binding.py` | 13KB | Admin binding |
| `heartbeat_ledger.py` | 39KB | Heartbeat tracking |
| `creative_reasoning_eval.py` | 20KB | Reasoning evaluation |
| + ~100 more files | | |

**Risk**: Enterprise code in public repo. Should be in private `hardbound` repo.

**CRITICAL FINDING**: The private `hardbound/` repo has a **different structure**:
- Private hardbound repo: **Rust-based** (Cargo.toml, hardbound-core/, hardbound-cli/)
- web4/hardbound/: **Python-based** (112+ .py files for federation simulation)

These are NOT the same codebase. The Python federation/attack simulation code in web4/hardbound/ appears to be:
- Active development (126 attack scenarios documented)
- Recent activity (Feb 5, 2026 on attack_simulations.py)
- Needs to be MOVED to private repo, not just deleted

**Recommended Action**: Move web4/hardbound/*.py to private hardbound repo before removing from public web4.

---

### Issue 2: Claude-Code Plugin Divergence

**Problem**: Two copies of the web4-governance plugin exist, with web4 being newer.

#### Location A: web4/claude-code-plugin/ (MORE RECENT)
- **Last commit**: Jan 31, 2026
- **Files**: 85 files
- **Key commits**:
  ```
  63aeed6 Jan 31 - Add git push divergence check to pre-tool-use hook
  d582e3e Jan 31 - Consolidate PR/issue docs into concise versions
  1a4b3d1 Jan 30 - feat(claude-code-plugin): Tier 1.5 features + PolicyEntity
  808545c Jan 30 - feat(governance): Add presence tracking - silence as signal
  ```

#### Location B: claude-code/plugins/web4-governance/ (OLDER)
- **Last commit**: Jan 28, 2026
- **Files**: ~80 files (missing some)
- **Key commits**:
  ```
  04cb5e2 Jan 28 - feat(governance): add PolicyEntity as first-class trust network
  19cca2f Jan 28 - docs: add Tier 1.5 features to README
  356a544 Jan 28 - Add Tier 1.5 features: presets, rate limiting, audit query
  ```

#### Differences Identified

| Component | web4 (A) | claude-code fork (B) |
|-----------|----------|---------------------|
| `governance/presence.py` | EXISTS (279 lines) | MISSING |
| `hooks/pre_tool_use.py` | 23632 bytes (+160 lines) | 19426 bytes |
| Git push divergence check | YES | NO |
| Command patterns matching | YES | NO |
| `hooks/heartbeat.py` | Newer version | Older |
| `hooks/session_start.py` | Newer version | Older |

**Conclusion**: web4 is the upstream, claude-code fork needs sync.

---

## Cleanup Plan

### Step 1: Move `hardbound/` to private repo (PRIORITY: HIGH)

**Important**: The Python code must be preserved before removal.

```bash
# Step 1a: Copy Python federation code to private hardbound repo
cp -r /home/dp/ai-workspace/web4/hardbound /home/dp/ai-workspace/hardbound/federation-python

# Step 1b: Commit in private repo
cd /home/dp/ai-workspace/hardbound
git add federation-python/
git commit -m "feat: import Python federation simulation code from web4

126 attack scenarios, federation registry, and economic models.
Moved from public web4 repo to keep enterprise code private."
git push

# Step 1c: Remove from public web4 repo
cd /home/dp/ai-workspace/web4
git rm -r hardbound/
git commit -m "chore: move enterprise code to private hardbound repo

Python federation simulation code (126 attack scenarios) moved to
private hardbound/federation-python directory."
git push
```

**REQUIRES USER DECISION**: The private hardbound repo is Rust-based. Where should the Python code live?
- Option A: `hardbound/federation-python/` (new directory in private repo)
- Option B: Separate private repo for Python federation code
- Option C: Keep in web4 but add to .gitignore (not recommended)

---

### Step 2: Sync claude-code fork with web4 plugin (PRIORITY: MEDIUM)

Two options:

#### Option A: Copy from web4 to claude-code (Recommended)
```bash
cd /home/dp/ai-workspace/claude-code

# Backup current
cp -r plugins/web4-governance plugins/web4-governance.backup

# Copy from upstream
cp -r /home/dp/ai-workspace/web4/claude-code-plugin/* plugins/web4-governance/

# Review and commit
git diff plugins/web4-governance/
git add plugins/web4-governance/
git commit -m "feat(web4-governance): sync with upstream web4 repo

Includes:
- presence.py (silence as signal tracking)
- git push divergence check
- command_patterns matching for advanced governance"

git push
```

#### Option B: Establish proper upstream relationship
Create a script or workflow that keeps these in sync. Consider:
- Making claude-code-plugin a git submodule pointing to web4
- Or establishing web4 as the single source of truth with periodic sync

---

### Step 3: Clean up __pycache__ directories (PRIORITY: LOW)

```bash
cd /home/dp/ai-workspace/web4
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null

# Add to .gitignore if not present
echo "__pycache__/" >> .gitignore
echo "*.pyc" >> .gitignore
```

---

## Verification Steps

After cleanup:

1. **hardbound removal**:
   ```bash
   ls -la /home/dp/ai-workspace/web4/hardbound  # Should not exist
   git log --oneline -5  # Should show removal commit
   ```

2. **plugin sync**:
   ```bash
   diff -rq /home/dp/ai-workspace/web4/claude-code-plugin/governance \
            /home/dp/ai-workspace/claude-code/plugins/web4-governance/governance \
            2>/dev/null | grep -v __pycache__
   # Should show no differences (or only intentional ones)
   ```

---

## Repository Relationship Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                         REPOS                                │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  web4 (PUBLIC)               hardbound (PRIVATE)            │
│  ├── whitepaper/            ├── federation.py               │
│  ├── web4-standard/         ├── attack_simulations.py       │
│  ├── claude-code-plugin/ ←──┤── economic_federation.py      │
│  │   └── (upstream)         └── ... (enterprise code)       │
│  └── ...                                                     │
│                                                              │
│         ↓ sync                                               │
│                                                              │
│  claude-code (FORK)                                          │
│  └── plugins/                                                │
│      └── web4-governance/ ← Needs sync from web4             │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Decision Points for User

1. **hardbound verification**: Before removal, confirm that `/home/dp/ai-workspace/hardbound/` contains all the code being removed from web4.

2. **Plugin sync strategy**:
   - One-time copy (Option A) - simpler
   - Establish ongoing sync mechanism (Option B) - more maintainable

3. **Remove claude-code-plugin from web4 after sync?**
   - Keep it as upstream development location
   - Or consolidate to single location in claude-code fork

---

## Execution Status

- [ ] **Step 1**: Move hardbound/ to private repo - **NEEDS USER DECISION** (see options above)
- [x] **Step 2**: Sync plugin to claude-code fork - **COMPLETED** (Feb 5, 2026)
  - Synced 16 files including presence.py, git push divergence check, command_patterns
  - Resolved merge conflict in presets.py (combined time_window + command_patterns)
  - Pushed to `add-web4-governance-plugin` branch
- [ ] **Step 3**: Clean __pycache__ - Minor, can do anytime
