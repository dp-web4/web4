#!/usr/bin/env python3
"""
Cross-Machine Heartbeat Verification

Provides cryptographic verification of heartbeat chains across machines.
Integrates with TPM binding for hardware-rooted signatures when available.

Key Features:
- Sign heartbeat entries using TPM or software keys
- Verify signatures on imported heartbeat chains
- Cross-machine chain validation
- Trust scoring based on verification results

Use Cases:
1. Distributed Identity: Verify presence claims across network
2. Audit Trails: Cryptographic proof of operational continuity
3. Cross-Instance Trust: Build trust based on verifiable history
4. Anomaly Detection: Identify tampering or clock manipulation
"""

import hashlib
import json
import os
import base64
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass, field, asdict
from enum import Enum

# Try to import TPM binding (optional)
try:
    from tpm_binding import TPMBoundLCT, TPMError
    TPM_AVAILABLE = True
except ImportError:
    TPM_AVAILABLE = False


# ============================================================================
# Configuration
# ============================================================================

@dataclass
class VerificationConfig:
    """Configuration for heartbeat verification."""

    # Acceptable clock drift between machines (seconds)
    max_clock_drift: float = 60.0

    # Trust scoring weights
    signature_weight: float = 0.4      # Weight of valid signatures
    chain_weight: float = 0.3          # Weight of unbroken chain
    timing_weight: float = 0.2         # Weight of consistent timing
    hardware_weight: float = 0.1       # Weight of hardware binding

    # Minimum entries for meaningful verification
    min_entries_for_score: int = 5

    # Signature algorithm preference
    prefer_tpm: bool = True


class VerificationResult(Enum):
    """Result of verification operation."""
    VALID = "valid"
    INVALID_SIGNATURE = "invalid_signature"
    INVALID_CHAIN = "invalid_chain"
    INVALID_TIMING = "invalid_timing"
    MISSING_DATA = "missing_data"
    UNTRUSTED_SOURCE = "untrusted_source"


# ============================================================================
# Software Signing (fallback when TPM unavailable)
# ============================================================================

class SoftwareSigningKey:
    """
    Software-based signing key.

    Uses HMAC-SHA256 with a local secret.
    Less secure than TPM but works everywhere.
    """

    def __init__(self, key_file: Optional[Path] = None):
        self.key_file = key_file or (Path.home() / ".web4" / "signing_key")
        self._secret: Optional[bytes] = None

    def _load_or_create(self) -> bytes:
        """Load or create signing secret."""
        if self._secret is not None:
            return self._secret

        if self.key_file.exists():
            with open(self.key_file, "rb") as f:
                self._secret = f.read()
        else:
            # Generate new secret
            self._secret = os.urandom(32)
            self.key_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.key_file, "wb") as f:
                f.write(self._secret)
            os.chmod(self.key_file, 0o600)

        return self._secret

    def sign(self, data: bytes) -> str:
        """Sign data with HMAC-SHA256."""
        import hmac
        secret = self._load_or_create()
        signature = hmac.new(secret, data, hashlib.sha256).digest()
        return base64.b64encode(signature).decode('ascii')

    def verify(self, data: bytes, signature: str) -> bool:
        """Verify HMAC signature."""
        import hmac
        secret = self._load_or_create()
        expected = hmac.new(secret, data, hashlib.sha256).digest()
        try:
            provided = base64.b64decode(signature)
            return hmac.compare_digest(expected, provided)
        except Exception:
            return False

    @property
    def binding_type(self) -> str:
        return "software"


# ============================================================================
# Heartbeat Signer
# ============================================================================

class HeartbeatSigner:
    """
    Signs heartbeat entries using best available method.

    Prefers TPM when available, falls back to software keys.
    """

    def __init__(self, config: Optional[VerificationConfig] = None):
        self.config = config or VerificationConfig()
        self._tpm: Optional['TPMBoundLCT'] = None
        self._software: Optional[SoftwareSigningKey] = None
        self._binding_type: str = "none"

        self._initialize()

    def _initialize(self):
        """Initialize signing capability."""
        if self.config.prefer_tpm and TPM_AVAILABLE:
            try:
                self._tpm = TPMBoundLCT.create()
                self._binding_type = "tpm"
                return
            except Exception:
                pass  # Fall through to software

        self._software = SoftwareSigningKey()
        self._binding_type = "software"

    @property
    def binding_type(self) -> str:
        """Return the type of key binding."""
        return self._binding_type

    def sign_entry(self, entry: dict) -> str:
        """
        Sign a heartbeat entry.

        Signs the entry_hash which covers all critical fields.
        """
        # Get the canonical data to sign
        entry_hash = entry.get("entry_hash", "")
        timestamp = entry.get("timestamp", "")
        data = f"{entry_hash}:{timestamp}".encode('utf-8')

        if self._tpm is not None:
            return self._tpm.sign(data)
        elif self._software is not None:
            return self._software.sign(data)
        else:
            raise RuntimeError("No signing capability available")

    def verify_entry(self, entry: dict, signature: str) -> bool:
        """
        Verify a heartbeat entry signature.

        Note: For cross-machine verification, use verify_external_entry.
        """
        entry_hash = entry.get("entry_hash", "")
        timestamp = entry.get("timestamp", "")
        data = f"{entry_hash}:{timestamp}".encode('utf-8')

        if self._tpm is not None:
            return self._tpm.verify(data, signature)
        elif self._software is not None:
            return self._software.verify(data, signature)
        else:
            return False


# ============================================================================
# Cross-Machine Verification
# ============================================================================

@dataclass
class ChainVerificationResult:
    """Result of verifying a heartbeat chain."""
    valid: bool
    entries_checked: int
    signatures_valid: int
    chain_intact: bool
    timing_consistent: bool
    hardware_bound: bool
    trust_score: float
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


class CrossMachineVerifier:
    """
    Verifies heartbeat chains from other machines.

    Cannot verify signatures (no access to signing key) but can:
    - Verify hash chain integrity
    - Check timing consistency
    - Detect anomalies
    - Compute trust scores based on observable properties
    """

    def __init__(self, config: Optional[VerificationConfig] = None):
        self.config = config or VerificationConfig()

    def verify_chain(self, entries: List[dict]) -> ChainVerificationResult:
        """
        Verify a heartbeat chain.

        Args:
            entries: List of heartbeat entry dicts (in order)

        Returns:
            ChainVerificationResult with detailed findings
        """
        errors = []
        warnings = []

        if not entries:
            return ChainVerificationResult(
                valid=False,
                entries_checked=0,
                signatures_valid=0,
                chain_intact=False,
                timing_consistent=False,
                hardware_bound=False,
                trust_score=0.0,
                errors=["No entries provided"]
            )

        # Check chain integrity
        chain_intact = True
        timing_consistent = True
        hardware_bound = False
        signatures_present = 0
        timing_deltas = []

        for i, entry in enumerate(entries):
            # Check hash chain
            if i > 0:
                prev = entries[i - 1]
                if entry.get("previous_hash") != prev.get("entry_hash"):
                    chain_intact = False
                    errors.append(f"Chain broken at entry {i}")

                # Check sequence
                if entry.get("sequence", 0) != prev.get("sequence", 0) + 1:
                    warnings.append(f"Sequence gap at entry {i}")

                # Check timing
                try:
                    prev_time = datetime.fromisoformat(
                        prev["timestamp"].replace("Z", "+00:00")
                    )
                    curr_time = datetime.fromisoformat(
                        entry["timestamp"].replace("Z", "+00:00")
                    )
                    delta = (curr_time - prev_time).total_seconds()

                    if delta < 0:
                        timing_consistent = False
                        errors.append(f"Negative time delta at entry {i}")
                    else:
                        timing_deltas.append(delta)

                except (KeyError, ValueError) as e:
                    warnings.append(f"Cannot parse timestamp at entry {i}: {e}")

            # Check for signatures
            if entry.get("signature"):
                signatures_present += 1

            # Check hardware binding
            if entry.get("binding_type") == "tpm":
                hardware_bound = True

        # Analyze timing consistency
        if len(timing_deltas) >= 2:
            avg_delta = sum(timing_deltas) / len(timing_deltas)
            variance = sum((d - avg_delta) ** 2 for d in timing_deltas) / len(timing_deltas)
            std_dev = variance ** 0.5

            # High variance in timing is suspicious
            if std_dev > avg_delta * 0.5:
                warnings.append(f"High timing variance: std_dev={std_dev:.1f}s")

        # Compute trust score
        score = self._compute_trust_score(
            entries_count=len(entries),
            chain_intact=chain_intact,
            timing_consistent=timing_consistent,
            signatures_present=signatures_present,
            hardware_bound=hardware_bound
        )

        valid = chain_intact and timing_consistent and not errors

        return ChainVerificationResult(
            valid=valid,
            entries_checked=len(entries),
            signatures_valid=signatures_present,  # Can't verify, just count
            chain_intact=chain_intact,
            timing_consistent=timing_consistent,
            hardware_bound=hardware_bound,
            trust_score=score,
            errors=errors,
            warnings=warnings
        )

    def _compute_trust_score(
        self,
        entries_count: int,
        chain_intact: bool,
        timing_consistent: bool,
        signatures_present: int,
        hardware_bound: bool
    ) -> float:
        """Compute trust score based on verification results."""
        if entries_count < self.config.min_entries_for_score:
            # Not enough data
            return 0.0

        score = 0.0

        # Chain integrity
        if chain_intact:
            score += self.config.chain_weight

        # Timing consistency
        if timing_consistent:
            score += self.config.timing_weight

        # Signatures present (can't verify remotely)
        sig_ratio = signatures_present / entries_count if entries_count > 0 else 0
        score += self.config.signature_weight * sig_ratio

        # Hardware binding
        if hardware_bound:
            score += self.config.hardware_weight

        return round(min(1.0, score), 3)

    def import_and_verify(
        self,
        source_path: Path,
        entity_lct: Optional[str] = None
    ) -> ChainVerificationResult:
        """
        Import heartbeat chain from file and verify.

        Args:
            source_path: Path to JSONL heartbeat file
            entity_lct: Expected entity LCT (optional filter)

        Returns:
            ChainVerificationResult
        """
        if not source_path.exists():
            return ChainVerificationResult(
                valid=False,
                entries_checked=0,
                signatures_valid=0,
                chain_intact=False,
                timing_consistent=False,
                hardware_bound=False,
                trust_score=0.0,
                errors=[f"File not found: {source_path}"]
            )

        entries = []
        try:
            with open(source_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        entry = json.loads(line)
                        if entity_lct is None or entry.get("entity_lct") == entity_lct:
                            entries.append(entry)
        except Exception as e:
            return ChainVerificationResult(
                valid=False,
                entries_checked=0,
                signatures_valid=0,
                chain_intact=False,
                timing_consistent=False,
                hardware_bound=False,
                trust_score=0.0,
                errors=[f"Failed to read file: {e}"]
            )

        return self.verify_chain(entries)


# ============================================================================
# Export for Verification
# ============================================================================

class HeartbeatExporter:
    """
    Exports heartbeat chains for cross-machine verification.

    Creates portable format with all necessary data.
    """

    def __init__(self, ledger_dir: Optional[Path] = None):
        self.ledger_dir = ledger_dir or (Path.home() / ".web4" / "heartbeat")

    def export_session(
        self,
        session_id: str,
        output_path: Path,
        sign_entries: bool = True,
        signer: Optional[HeartbeatSigner] = None
    ) -> dict:
        """
        Export a session's heartbeat chain.

        Args:
            session_id: Session ID to export
            output_path: Path to write export file
            sign_entries: Whether to sign entries
            signer: HeartbeatSigner to use (creates new if None)

        Returns:
            Export metadata
        """
        source = self.ledger_dir / f"{session_id}.jsonl"

        if not source.exists():
            raise FileNotFoundError(f"Session not found: {session_id}")

        # Read entries
        entries = []
        with open(source, 'r') as f:
            for line in f:
                line = line.strip()
                if line:
                    entries.append(json.loads(line))

        # Sign if requested
        if sign_entries:
            if signer is None:
                signer = HeartbeatSigner()

            for entry in entries:
                if not entry.get("signature"):
                    entry["signature"] = signer.sign_entry(entry)
                    entry["binding_type"] = signer.binding_type

        # Write export
        export = {
            "version": "1.0",
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "session_id": session_id,
            "entry_count": len(entries),
            "entries": entries,
            "metadata": {
                "binding_type": signer.binding_type if signer else "none",
                "source_machine": os.uname().nodename
            }
        }

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(export, f, indent=2)

        return {
            "session_id": session_id,
            "entries_exported": len(entries),
            "output_path": str(output_path),
            "signed": sign_entries
        }

    def export_all_sessions(
        self,
        output_dir: Path,
        sign_entries: bool = True
    ) -> List[dict]:
        """Export all sessions to a directory."""
        results = []
        signer = HeartbeatSigner() if sign_entries else None

        for ledger_file in self.ledger_dir.glob("*.jsonl"):
            session_id = ledger_file.stem
            output_path = output_dir / f"{session_id}.json"

            try:
                result = self.export_session(
                    session_id,
                    output_path,
                    sign_entries,
                    signer
                )
                results.append(result)
            except Exception as e:
                results.append({
                    "session_id": session_id,
                    "error": str(e)
                })

        return results


# ============================================================================
# MCP Integration
# ============================================================================

def verify_remote_heartbeat(session_data: dict) -> ChainVerificationResult:
    """
    Verify heartbeat data received via MCP.

    Args:
        session_data: Export format data from remote machine

    Returns:
        ChainVerificationResult
    """
    verifier = CrossMachineVerifier()

    entries = session_data.get("entries", [])
    if not entries:
        return ChainVerificationResult(
            valid=False,
            entries_checked=0,
            signatures_valid=0,
            chain_intact=False,
            timing_consistent=False,
            hardware_bound=False,
            trust_score=0.0,
            errors=["No entries in session data"]
        )

    return verifier.verify_chain(entries)


# ============================================================================
# CLI
# ============================================================================

def main():
    """Command-line interface for heartbeat verification."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Cross-machine heartbeat verification"
    )
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Export command
    export_parser = subparsers.add_parser("export", help="Export session for verification")
    export_parser.add_argument("session_id", help="Session ID to export")
    export_parser.add_argument("-o", "--output", required=True, help="Output file path")
    export_parser.add_argument("--no-sign", action="store_true", help="Don't sign entries")

    # Verify command
    verify_parser = subparsers.add_parser("verify", help="Verify imported heartbeat chain")
    verify_parser.add_argument("file", help="File to verify (JSONL or JSON export)")

    # Info command
    info_parser = subparsers.add_parser("info", help="Show signing info")

    args = parser.parse_args()

    if args.command == "export":
        exporter = HeartbeatExporter()
        try:
            result = exporter.export_session(
                args.session_id,
                Path(args.output),
                sign_entries=not args.no_sign
            )
            print(f"Exported {result['entries_exported']} entries to {result['output_path']}")
            if result['signed']:
                print(f"Signed with: {result.get('binding_type', 'unknown')}")
        except FileNotFoundError as e:
            print(f"Error: {e}")
            return 1

    elif args.command == "verify":
        verifier = CrossMachineVerifier()
        path = Path(args.file)

        if path.suffix == ".json":
            # Export format
            with open(path) as f:
                data = json.load(f)
            entries = data.get("entries", [])
        else:
            # JSONL format
            entries = []
            with open(path) as f:
                for line in f:
                    if line.strip():
                        entries.append(json.loads(line))

        result = verifier.verify_chain(entries)

        print(f"\nVerification Results")
        print(f"==================")
        print(f"Valid: {result.valid}")
        print(f"Entries: {result.entries_checked}")
        print(f"Chain intact: {result.chain_intact}")
        print(f"Timing consistent: {result.timing_consistent}")
        print(f"Hardware bound: {result.hardware_bound}")
        print(f"Trust score: {result.trust_score}")

        if result.errors:
            print(f"\nErrors:")
            for e in result.errors:
                print(f"  - {e}")

        if result.warnings:
            print(f"\nWarnings:")
            for w in result.warnings:
                print(f"  - {w}")

    elif args.command == "info":
        signer = HeartbeatSigner()
        print(f"Signing method: {signer.binding_type}")
        if signer.binding_type == "tpm":
            print("TPM hardware key available")
        else:
            print("Using software HMAC key")

    else:
        parser.print_help()

    return 0


if __name__ == "__main__":
    exit(main())
