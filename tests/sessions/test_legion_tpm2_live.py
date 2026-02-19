#!/usr/bin/env python3
"""
Live TPM2 Hardware Binding Validation - Legion
===============================================

Tests the full hardware binding flow on Legion's Intel TPM 2.0:
1. Create primary key in owner hierarchy
2. Create ECC-P256 signing key (non-extractable)
3. Make key persistent
4. Sign data with TPM
5. Verify signature with Python cryptography
6. Read PCR values (boot integrity)
7. Generate attestation quote

This resolves the TCTI blocker from December 2025 by confirming
end-to-end hardware signing works via tpm2-tools CLI.

Date: 2026-02-19
Machine: Legion Pro 7 (Intel Core i9-13900HX, TPM 2.0 INTC/ADL)
"""

import os
import sys
import subprocess
import tempfile
import hashlib
import base64
import json
from pathlib import Path
from datetime import datetime, timezone


def run_tpm2(cmd, check=True):
    """Run a tpm2-tools command."""
    result = subprocess.run(cmd, capture_output=True, timeout=30)
    if check and result.returncode != 0:
        error = result.stderr.decode('utf-8', errors='replace')
        raise RuntimeError(f"{cmd[0]} failed: {error}")
    return result


def tpm_sig_to_der(tpm_sig):
    """Convert TPM TPMT_SIGNATURE to DER format."""
    offset = 4  # Skip sigAlg + hashAlg
    r_size = int.from_bytes(tpm_sig[offset:offset+2], 'big')
    offset += 2
    r = tpm_sig[offset:offset+r_size]
    offset += r_size
    s_size = int.from_bytes(tpm_sig[offset:offset+2], 'big')
    offset += 2
    s = tpm_sig[offset:offset+s_size]

    def encode_int(value):
        if value[0] & 0x80:
            value = b'\x00' + value
        return bytes([0x02, len(value)]) + value

    r_der = encode_int(r)
    s_der = encode_int(s)
    content = r_der + s_der
    return bytes([0x30, len(content)]) + content


def main():
    results = {}
    handle = '0x81010099'  # Test handle

    print("=" * 60)
    print("LIVE TPM2 HARDWARE BINDING TEST - LEGION")
    print(f"Date: {datetime.now(timezone.utc).isoformat()}")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        primary_ctx = tmpdir / "primary.ctx"
        key_pub = tmpdir / "key.pub"
        key_priv = tmpdir / "key.priv"
        key_ctx = tmpdir / "key.ctx"
        key_pem = tmpdir / "key.pem"

        # Step 1: Create primary key
        print("\n[1] Creating primary key (owner hierarchy, ECC-P256)...")
        try:
            run_tpm2([
                "tpm2_createprimary", "-C", "o",
                "-g", "sha256", "-G", "ecc256",
                "-c", str(primary_ctx)
            ])
            print("    OK: Primary key created")
            results["primary_key"] = True
        except Exception as e:
            print(f"    FAIL: {e}")
            results["primary_key"] = False
            return results

        # Step 2: Create signing key (non-extractable)
        print("[2] Creating signing key (fixedtpm|fixedparent|sensitivedataorigin)...")
        try:
            run_tpm2([
                "tpm2_create", "-C", str(primary_ctx),
                "-g", "sha256", "-G", "ecc256",
                "-u", str(key_pub), "-r", str(key_priv),
                "-a", "sign|fixedtpm|fixedparent|sensitivedataorigin|userwithauth"
            ])
            print("    OK: Signing key created (non-extractable)")
            results["signing_key"] = True
        except Exception as e:
            print(f"    FAIL: {e}")
            results["signing_key"] = False
            return results

        # Step 3: Load key
        print("[3] Loading key into TPM context...")
        try:
            run_tpm2([
                "tpm2_load", "-C", str(primary_ctx),
                "-u", str(key_pub), "-r", str(key_priv),
                "-c", str(key_ctx)
            ])
            print("    OK: Key loaded")
            results["key_load"] = True
        except Exception as e:
            print(f"    FAIL: {e}")
            results["key_load"] = False
            return results

        # Step 4: Make persistent
        print(f"[4] Making key persistent at {handle}...")
        try:
            # Evict existing (ignore errors)
            subprocess.run(
                ["tpm2_evictcontrol", "-C", "o", "-c", handle],
                capture_output=True
            )
            run_tpm2([
                "tpm2_evictcontrol", "-C", "o",
                "-c", str(key_ctx), handle
            ])
            print(f"    OK: Key persisted at {handle}")
            results["persistent"] = True
        except Exception as e:
            print(f"    FAIL: {e}")
            results["persistent"] = False
            return results

        # Step 5: Read public key
        print("[5] Reading public key (PEM format)...")
        try:
            run_tpm2([
                "tpm2_readpublic", "-c", handle,
                "-f", "pem", "-o", str(key_pem)
            ])
            with open(key_pem, 'r') as f:
                public_key_pem = f.read()
            print(f"    OK: Public key ({len(public_key_pem)} bytes)")
            for line in public_key_pem.strip().split('\n'):
                print(f"    {line}")
            results["public_key"] = True
        except Exception as e:
            print(f"    FAIL: {e}")
            results["public_key"] = False
            return results

        # Step 6: Sign data
        print("[6] Signing test data with TPM...")
        test_data = (
            b"Web4 Hardware Binding Validation - Legion - "
            + datetime.now(timezone.utc).isoformat().encode()
        )
        data_hash = hashlib.sha256(test_data).digest()

        data_file = tmpdir / "sign_data.bin"
        sig_file = tmpdir / "signature.bin"

        with open(data_file, 'wb') as f:
            f.write(data_hash)

        try:
            run_tpm2([
                "tpm2_sign", "-c", handle,
                "-g", "sha256", "-s", "ecdsa",
                "-d", str(data_file),
                "-o", str(sig_file)
            ])
            with open(sig_file, 'rb') as f:
                tpm_signature = f.read()
            sig_b64 = base64.b64encode(tpm_signature).decode()
            print(f"    OK: Signature ({len(tpm_signature)} bytes)")
            print(f"    Raw (b64): {sig_b64[:60]}...")
            results["signing"] = True
        except Exception as e:
            print(f"    FAIL: {e}")
            results["signing"] = False
            return results

        # Step 7: Verify signature
        print("[7] Verifying signature (Python cryptography library)...")
        try:
            der_signature = tpm_sig_to_der(tpm_signature)
            from cryptography.hazmat.primitives import hashes, serialization
            from cryptography.hazmat.primitives.asymmetric import ec

            pub_key = serialization.load_pem_public_key(public_key_pem.encode())
            pub_key.verify(der_signature, test_data, ec.ECDSA(hashes.SHA256()))
            print("    OK: SIGNATURE VERIFIED SUCCESSFULLY")
            results["verification"] = True
        except Exception as e:
            print(f"    FAIL: {e}")
            results["verification"] = False

        # Step 8: Read PCR values
        print("[8] Reading PCR values (boot integrity)...")
        try:
            pcr_result = run_tpm2([
                "tpm2_pcrread", "sha256:0,1,2,3,4,5,6,7"
            ])
            pcr_output = pcr_result.stdout.decode()
            for line in pcr_output.strip().split('\n')[:8]:
                print(f"    {line.strip()}")
            results["pcr_read"] = True
        except Exception as e:
            print(f"    FAIL: {e}")
            results["pcr_read"] = False

        # Step 9: Attestation quote
        print("[9] Generating TPM attestation quote...")
        try:
            quote_file = tmpdir / "quote.bin"
            quote_sig_file = tmpdir / "quote_sig.bin"
            nonce = os.urandom(32)
            nonce_file = tmpdir / "nonce.bin"
            with open(nonce_file, 'wb') as f:
                f.write(nonce)

            run_tpm2([
                "tpm2_quote", "-c", handle,
                "-l", "sha256:0,1,2,3,4,5,6,7",
                "-q", str(nonce_file),
                "-m", str(quote_file),
                "-s", str(quote_sig_file)
            ])
            with open(quote_file, 'rb') as f:
                quote_data = f.read()
            with open(quote_sig_file, 'rb') as f:
                quote_sig_data = f.read()

            print(f"    OK: Quote ({len(quote_data)} bytes), Sig ({len(quote_sig_data)} bytes)")
            print(f"    Nonce: {nonce.hex()[:32]}...")
            results["attestation"] = True
        except Exception as e:
            print(f"    FAIL: {e}")
            results["attestation"] = False

        # Step 10: Clean up
        print("[10] Cleaning up test key...")
        subprocess.run(
            ["tpm2_evictcontrol", "-C", "o", "-c", handle],
            capture_output=True
        )
        print("    OK: Test key evicted")

    # Summary
    print()
    print("=" * 60)
    print("RESULTS SUMMARY")
    print("=" * 60)

    # Get TPM info
    try:
        cap_result = subprocess.run(
            ["tpm2_getcap", "properties-fixed"],
            capture_output=True, timeout=5
        )
        cap_text = cap_result.stdout.decode()
        manufacturer = "Unknown"
        for line in cap_text.split('\n'):
            if 'TPM2_PT_MANUFACTURER' in line and 'value' in line:
                manufacturer = line.split('"')[1]
    except Exception:
        manufacturer = "Unknown"

    print(f"TPM Manufacturer:     {manufacturer}")
    print(f"TPM Version:          2.0")
    print(f"Key Algorithm:        ECC-P256 (NIST)")
    print(f"Key Attributes:       fixedtpm|fixedparent|sensitivedataorigin")
    print(f"Signature Algorithm:  ECDSA-SHA256")
    print()

    all_pass = True
    for step, passed in results.items():
        status = "PASS" if passed else "FAIL"
        if not passed:
            all_pass = False
        print(f"  {step:20s}: {status}")

    print()
    if all_pass:
        print(">>> ALL TESTS PASSED <<<")
        print(">>> HARDWARE BINDING FULLY OPERATIONAL ON LEGION <<<")
        print(">>> Level 5 LCT capability CONFIRMED <<<")
    else:
        failed = [k for k, v in results.items() if not v]
        print(f">>> PARTIAL: {len(results) - len(failed)}/{len(results)} passed <<<")
        print(f">>> Failed: {', '.join(failed)} <<<")

    print("=" * 60)

    # Save results
    output = {
        "test": "TPM2 Hardware Binding Validation",
        "date": datetime.now(timezone.utc).isoformat(),
        "machine": "Legion Pro 7 (dp-Legion-Pro-7-16IRX8H)",
        "tpm_manufacturer": manufacturer,
        "results": results,
        "all_pass": all_pass,
        "conclusion": "Level 5 hardware binding operational" if all_pass else "Partial success"
    }

    output_file = Path(__file__).parent.parent / "outputs" / "tpm2_live_validation_2026-02-19.json"
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)
    print(f"\nResults saved to: {output_file}")

    return results


if __name__ == "__main__":
    main()
