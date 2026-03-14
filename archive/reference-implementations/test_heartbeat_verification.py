#!/usr/bin/env python3
"""Test cross-machine heartbeat verification."""

import json
import tempfile
import uuid
from pathlib import Path
from datetime import datetime, timezone, timedelta

from heartbeat_verification import (
    HeartbeatSigner,
    CrossMachineVerifier,
    HeartbeatExporter,
    SoftwareSigningKey,
    verify_remote_heartbeat,
    ChainVerificationResult,
)


def create_test_chain(count: int = 10) -> list:
    """Create a valid test heartbeat chain."""
    entries = []
    prev_hash = ""
    base_time = datetime.now(timezone.utc)

    for i in range(count):
        timestamp = (base_time + timedelta(seconds=60 * i)).isoformat()
        if timestamp.endswith("+00:00"):
            timestamp = timestamp[:-6] + "Z"

        # Compute hash
        import hashlib
        hash_input = f"test-entity:{timestamp}:{prev_hash}:{i + 1}"
        entry_hash = hashlib.sha256(hash_input.encode()).hexdigest()[:32]

        entry = {
            "sequence": i + 1,
            "timestamp": timestamp,
            "status": "on_time" if i > 0 else "initial",
            "delta_seconds": 60.0 if i > 0 else 0.0,
            "action": f"action_{i}",
            "action_index": i,
            "previous_hash": prev_hash,
            "entry_hash": entry_hash,
        }

        entries.append(entry)
        prev_hash = entry_hash

    return entries


def test_software_signing():
    """Test software signing key."""
    print("Testing software signing...")

    with tempfile.TemporaryDirectory() as tmpdir:
        key_file = Path(tmpdir) / "test_key"
        signer = SoftwareSigningKey(key_file)

        # Sign
        data = b"test data"
        sig = signer.sign(data)
        assert sig, "Signature should not be empty"
        print(f"  Signature: {sig[:32]}...")

        # Verify
        valid = signer.verify(data, sig)
        assert valid, "Signature should verify"

        # Wrong data should fail
        valid = signer.verify(b"wrong data", sig)
        assert not valid, "Wrong data should not verify"

        print("  Software signing: OK")


def test_heartbeat_signer():
    """Test heartbeat entry signing."""
    print("\nTesting heartbeat signer...")

    signer = HeartbeatSigner()
    print(f"  Binding type: {signer.binding_type}")

    entries = create_test_chain(3)

    # Sign entries
    for entry in entries:
        sig = signer.sign_entry(entry)
        entry["signature"] = sig
        assert sig, "Signature should not be empty"

    print(f"  Signed {len(entries)} entries")

    # Verify entries
    for entry in entries:
        valid = signer.verify_entry(entry, entry["signature"])
        assert valid, f"Entry {entry['sequence']} should verify"

    print("  Verification: OK")


def test_chain_verification():
    """Test cross-machine chain verification."""
    print("\nTesting chain verification...")

    verifier = CrossMachineVerifier()

    # Valid chain
    entries = create_test_chain(10)
    result = verifier.verify_chain(entries)

    print(f"  Valid chain: {result.valid}")
    print(f"  Chain intact: {result.chain_intact}")
    print(f"  Timing consistent: {result.timing_consistent}")
    print(f"  Trust score: {result.trust_score}")

    assert result.valid, "Valid chain should verify"
    assert result.chain_intact, "Chain should be intact"
    assert result.timing_consistent, "Timing should be consistent"
    assert len(result.errors) == 0, "Should have no errors"


def test_broken_chain():
    """Test detection of broken chain."""
    print("\nTesting broken chain detection...")

    verifier = CrossMachineVerifier()
    entries = create_test_chain(5)

    # Break the chain
    entries[2]["previous_hash"] = "broken"

    result = verifier.verify_chain(entries)

    print(f"  Valid: {result.valid}")
    print(f"  Chain intact: {result.chain_intact}")
    print(f"  Errors: {result.errors}")

    assert not result.valid, "Broken chain should not verify"
    assert not result.chain_intact, "Chain should not be intact"
    assert len(result.errors) > 0, "Should have errors"


def test_timing_anomaly():
    """Test detection of timing anomalies."""
    print("\nTesting timing anomaly detection...")

    verifier = CrossMachineVerifier()
    entries = create_test_chain(5)

    # Reverse timestamps (time going backwards)
    entries[3]["timestamp"] = entries[1]["timestamp"]

    result = verifier.verify_chain(entries)

    print(f"  Valid: {result.valid}")
    print(f"  Timing consistent: {result.timing_consistent}")
    print(f"  Errors: {result.errors}")

    assert not result.valid, "Timing anomaly should fail"
    assert not result.timing_consistent, "Timing should not be consistent"


def test_export_import():
    """Test export and import cycle."""
    print("\nTesting export/import cycle...")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Create test session
        session_id = f"test_{uuid.uuid4().hex[:8]}"
        heartbeat_dir = tmpdir / "heartbeat"
        heartbeat_dir.mkdir(parents=True)

        # Write test entries
        entries = create_test_chain(5)
        ledger_file = heartbeat_dir / f"{session_id}.jsonl"
        with open(ledger_file, "w") as f:
            for entry in entries:
                f.write(json.dumps(entry) + "\n")

        # Export
        exporter = HeartbeatExporter(heartbeat_dir)
        export_path = tmpdir / "export.json"
        result = exporter.export_session(session_id, export_path)

        print(f"  Exported: {result['entries_exported']} entries")
        assert export_path.exists(), "Export file should exist"

        # Verify exported data
        with open(export_path) as f:
            export_data = json.load(f)

        assert export_data["session_id"] == session_id
        assert len(export_data["entries"]) == 5
        assert export_data["entries"][0].get("signature"), "Should be signed"

        # Verify via MCP-style call
        verify_result = verify_remote_heartbeat(export_data)
        print(f"  Remote verify: valid={verify_result.valid}, score={verify_result.trust_score}")

        assert verify_result.valid, "Exported chain should verify"


def test_empty_chain():
    """Test handling of empty chain."""
    print("\nTesting empty chain...")

    verifier = CrossMachineVerifier()
    result = verifier.verify_chain([])

    assert not result.valid
    assert result.entries_checked == 0
    assert len(result.errors) > 0


def test_signed_chain_trust():
    """Test that signed chains have higher trust."""
    print("\nTesting signed vs unsigned trust scores...")

    verifier = CrossMachineVerifier()
    signer = HeartbeatSigner()

    # Unsigned chain
    unsigned = create_test_chain(10)
    unsigned_result = verifier.verify_chain(unsigned)

    # Signed chain
    signed = create_test_chain(10)
    for entry in signed:
        entry["signature"] = signer.sign_entry(entry)
        entry["binding_type"] = signer.binding_type

    signed_result = verifier.verify_chain(signed)

    print(f"  Unsigned trust: {unsigned_result.trust_score}")
    print(f"  Signed trust: {signed_result.trust_score}")

    # Signed should have higher trust
    assert signed_result.trust_score > unsigned_result.trust_score, \
        "Signed chain should have higher trust"


def main():
    print("=" * 60)
    print("Cross-Machine Heartbeat Verification Tests")
    print("=" * 60)

    test_software_signing()
    test_heartbeat_signer()
    test_chain_verification()
    test_broken_chain()
    test_timing_anomaly()
    test_export_import()
    test_empty_chain()
    test_signed_chain_trust()

    print("\n" + "=" * 60)
    print("All tests passed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
