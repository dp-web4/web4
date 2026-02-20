#!/usr/bin/env python3
"""
TPM2 Handle Cleanup Utility
============================

Standalone tool for managing TPM2 persistent handles in the Web4 namespace.

Fixes the known issue where `evict_orphaned_handles()` in TPM2Provider
silently swallows errors and misses handles created outside the provider's
metadata tracking (e.g., demos that create keys via HardwareWeb4Entity).

Usage:
    python tpm2_cleanup.py             # Show status (dry run)
    python tpm2_cleanup.py --evict     # Evict all orphaned handles
    python tpm2_cleanup.py --evict-all # Evict ALL Web4 handles (nuclear option)

Can also be imported:
    from core.lct_binding.tpm2_cleanup import TPM2Cleanup
    cleanup = TPM2Cleanup()
    status = cleanup.scan()
    cleanup.evict_orphaned()

Date: 2026-02-20
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import Optional


# Web4 TPM2 namespace
WEB4_HANDLE_BASE = 0x81010000
WEB4_HANDLE_END = 0x810100FF  # 256 slots

# System handles — NEVER touch
SYSTEM_HANDLE_RANGES = [
    (0x81800000, 0x81800FFF),  # Platform handles
]

# Default metadata storage
DEFAULT_METADATA_DIR = Path.home() / ".web4" / "identity" / "tpm2"


class TPM2Cleanup:
    """TPM2 persistent handle cleanup utility."""

    def __init__(self, metadata_dir: Optional[Path] = None, verbose: bool = True):
        self.metadata_dir = metadata_dir or DEFAULT_METADATA_DIR
        self.verbose = verbose

    def _run(self, cmd: list, check: bool = False) -> subprocess.CompletedProcess:
        """Run a TPM2 command with proper error handling."""
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=10,
            )
            if check and result.returncode != 0:
                stderr = result.stderr.decode().strip()
                raise RuntimeError(f"TPM2 command failed: {' '.join(cmd)}\n{stderr}")
            return result
        except subprocess.TimeoutExpired:
            raise RuntimeError(f"TPM2 command timed out: {' '.join(cmd)}")

    def _is_system_handle(self, handle: int) -> bool:
        """Check if a handle is in a system-reserved range."""
        for start, end in SYSTEM_HANDLE_RANGES:
            if start <= handle <= end:
                return True
        return False

    def _is_web4_handle(self, handle: int) -> bool:
        """Check if a handle is in the Web4 namespace."""
        return WEB4_HANDLE_BASE <= handle <= WEB4_HANDLE_END

    def _get_tracked_handles(self) -> dict:
        """Read metadata files to find handles with known ownership."""
        tracked = {}
        if not self.metadata_dir.exists():
            return tracked
        for meta_file in self.metadata_dir.glob("*.json"):
            try:
                data = json.loads(meta_file.read_text())
                handle_str = data.get("persistent_handle", "")
                key_id = data.get("key_id", meta_file.stem)
                if handle_str:
                    handle = int(handle_str, 16)
                    tracked[handle] = {
                        "key_id": key_id,
                        "file": str(meta_file),
                        "created_at": data.get("created_at", "?"),
                    }
            except (json.JSONDecodeError, ValueError, OSError) as e:
                if self.verbose:
                    print(f"  Warning: Could not read {meta_file.name}: {e}")
        return tracked

    def _get_persistent_handles(self) -> list:
        """Query TPM2 for all persistent handles."""
        result = self._run(["tpm2_getcap", "handles-persistent"])
        if result.returncode != 0:
            stderr = result.stderr.decode().strip()
            if "no connection" in stderr.lower() or "tcti" in stderr.lower():
                raise RuntimeError("Cannot connect to TPM2. Is tpm2-abrmd running?")
            return []

        handles = []
        for line in result.stdout.decode().split('\n'):
            line = line.strip()
            if line.startswith('- 0x'):
                try:
                    handle = int(line[2:], 16)
                    handles.append(handle)
                except ValueError:
                    if self.verbose:
                        print(f"  Warning: Could not parse handle: {line}")
        return sorted(handles)

    def scan(self) -> dict:
        """
        Scan TPM2 for all persistent handles and classify them.

        Returns dict with:
            - system: Handles in system-reserved ranges (never touch)
            - tracked: Web4 handles with metadata files
            - orphaned: Web4 handles WITHOUT metadata (safe to evict)
            - foreign: Handles outside all known ranges
            - total: Total handle count
        """
        handles = self._get_persistent_handles()
        tracked = self._get_tracked_handles()

        status = {
            "system": [],
            "tracked": [],
            "orphaned": [],
            "foreign": [],
            "total": len(handles),
        }

        for handle in handles:
            hex_handle = f"0x{handle:08x}"
            if self._is_system_handle(handle):
                status["system"].append(hex_handle)
            elif self._is_web4_handle(handle):
                if handle in tracked:
                    info = tracked[handle]
                    status["tracked"].append({
                        "handle": hex_handle,
                        "key_id": info["key_id"],
                        "created_at": info["created_at"],
                    })
                else:
                    status["orphaned"].append(hex_handle)
            else:
                status["foreign"].append(hex_handle)

        return status

    def evict_handle(self, handle_hex: str) -> bool:
        """Evict a single persistent handle."""
        result = self._run(["tpm2_evictcontrol", "-C", "o", "-c", handle_hex])
        if result.returncode != 0:
            stderr = result.stderr.decode().strip()
            if self.verbose:
                print(f"  Failed to evict {handle_hex}: {stderr}")
            return False
        return True

    def evict_orphaned(self) -> dict:
        """Evict all orphaned handles in the Web4 namespace."""
        status = self.scan()
        results = {"evicted": [], "failed": [], "skipped_system": len(status["system"])}

        for handle_hex in status["orphaned"]:
            if self.evict_handle(handle_hex):
                results["evicted"].append(handle_hex)
                if self.verbose:
                    print(f"  Evicted orphaned handle: {handle_hex}")
            else:
                results["failed"].append(handle_hex)

        return results

    def evict_all_web4(self) -> dict:
        """
        Nuclear option: evict ALL handles in the Web4 namespace,
        including tracked ones. Also removes metadata files.
        """
        status = self.scan()
        results = {"evicted": [], "failed": [], "metadata_removed": []}

        all_web4 = status["orphaned"] + [t["handle"] for t in status["tracked"]]
        for handle_hex in all_web4:
            if self.evict_handle(handle_hex):
                results["evicted"].append(handle_hex)
                if self.verbose:
                    print(f"  Evicted: {handle_hex}")
            else:
                results["failed"].append(handle_hex)

        # Clean up metadata files
        if self.metadata_dir.exists():
            for meta_file in self.metadata_dir.glob("*.json"):
                try:
                    meta_file.unlink()
                    results["metadata_removed"].append(str(meta_file))
                except OSError:
                    pass

        return results

    def print_status(self):
        """Print a human-readable status report."""
        status = self.scan()

        print("=" * 60)
        print("  TPM2 Handle Status Report")
        print("=" * 60)
        print(f"\n  Total persistent handles: {status['total']}")
        print(f"  System (protected):       {len(status['system'])}")
        print(f"  Web4 tracked:             {len(status['tracked'])}")
        print(f"  Web4 orphaned:            {len(status['orphaned'])}")
        print(f"  Foreign/unknown:          {len(status['foreign'])}")

        if status["system"]:
            print(f"\n  System handles (DO NOT TOUCH):")
            for h in status["system"]:
                print(f"    {h}")

        if status["tracked"]:
            print(f"\n  Tracked Web4 handles:")
            for t in status["tracked"]:
                print(f"    {t['handle']}  key={t['key_id'][:40]}  created={t['created_at'][:19]}")

        if status["orphaned"]:
            print(f"\n  Orphaned Web4 handles (safe to evict):")
            for h in status["orphaned"]:
                print(f"    {h}")

        if status["foreign"]:
            print(f"\n  Foreign handles (not Web4):")
            for h in status["foreign"]:
                print(f"    {h}")

        print(f"\n{'=' * 60}")
        return status


def demo_cleanup_hook(created_handles: list):
    """
    Call this in demo teardown to evict handles created during the demo.

    Usage in demos:
        handles_created = []
        # ... during demo: handles_created.append("0x81010042")
        # ... at end:
        demo_cleanup_hook(handles_created)
    """
    cleanup = TPM2Cleanup(verbose=True)
    print(f"\n  Demo cleanup: evicting {len(created_handles)} handles...")
    evicted = 0
    for handle_hex in created_handles:
        if cleanup.evict_handle(handle_hex):
            evicted += 1
    print(f"  Evicted {evicted}/{len(created_handles)} handles")
    return evicted


def main():
    import argparse
    parser = argparse.ArgumentParser(description="TPM2 handle cleanup for Web4")
    parser.add_argument("--evict", action="store_true",
                        help="Evict orphaned handles")
    parser.add_argument("--evict-all", action="store_true",
                        help="Evict ALL Web4 handles (nuclear option)")
    parser.add_argument("--quiet", action="store_true",
                        help="Minimal output")
    parser.add_argument("--json", action="store_true",
                        help="Output as JSON")
    args = parser.parse_args()

    cleanup = TPM2Cleanup(verbose=not args.quiet)

    try:
        if args.evict_all:
            if not args.quiet:
                print("Evicting ALL Web4 handles...")
            results = cleanup.evict_all_web4()
            if args.json:
                print(json.dumps(results, indent=2))
            else:
                print(f"\nEvicted: {len(results['evicted'])}, "
                      f"Failed: {len(results['failed'])}, "
                      f"Metadata removed: {len(results['metadata_removed'])}")

        elif args.evict:
            if not args.quiet:
                print("Evicting orphaned handles...")
            results = cleanup.evict_orphaned()
            if args.json:
                print(json.dumps(results, indent=2))
            else:
                print(f"\nEvicted: {len(results['evicted'])}, "
                      f"Failed: {len(results['failed'])}, "
                      f"System handles protected: {results['skipped_system']}")

        else:
            status = cleanup.print_status()
            if args.json:
                print(json.dumps(status, indent=2))

    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
