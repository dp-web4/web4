# Web4 Game Simulations - MOVED

**⚠️ CANONICAL LOCATION: `4-life/lib/game/`**

The game simulation scripts have been moved to the **4-life repository** as of 2026-01-16.

## Why the Move?

**4-life is the interactive platform** - it's the user-facing web application that runs these simulations. Making 4-life the canonical location means:

1. **Self-contained deployment**: 4-life can be deployed to Vercel without depending on sibling repositories
2. **Clear ownership**: The interactive platform owns the simulation code it uses
3. **Easier maintenance**: Code changes happen where they're consumed

## Where Things Are Now

| What | Old Location | New Location |
|------|-------------|--------------|
| **Game scripts (CANONICAL)** | `web4/game/*.py` | **`4-life/lib/game/*.py`** |
| **API endpoints** | N/A | `4-life/src/app/api/` |
| **Interactive UI** | N/A | `4-life/src/app/` |

## Making Changes

**✅ DO**: Make code changes in `4-life/lib/game/`

**❌ DON'T**: Edit files in `web4/game/` - they may be stale or removed

## This Directory

The `web4/game/` directory may:
- Contain archived copies for reference
- Contain experimental scripts not yet moved to 4-life
- Be removed entirely in future cleanup

**When in doubt, check `4-life/lib/game/` first.**

---

## Migration Details

**Date**: 2026-01-16
**Reason**: Prepare 4-life for Vercel deployment (requires self-contained repo)
**Files moved**: 84 Python scripts
**Status**: ✅ Complete

**See**: `4-life/lib/game/` for the canonical simulation code.
