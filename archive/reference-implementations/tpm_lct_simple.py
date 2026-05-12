"""
Simplified TPM-Based LCT Identity (Phase 2.1)
=============================================

Simple working TPM integration for LCT hardware binding.
Uses high-level tpm2-pytss API.

Security Properties:
- Keys generated inside TPM
- Private keys never exported
- Demonstrates hardware binding capability

Author: Claude (Legion autonomous research)
Date: 2025-12-06
Track: 16 (Phase 2 Hardware Binding - Simplified)
"""

import os
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

try:
    from tpm2_pytss import ESAPI, TCTILdr
    TPM_AVAILABLE = True
except ImportError:
    TPM_AVAILABLE = False
    print("WARNING: tpm2-pytss not available")


@dataclass
class SimpleLCTKey:
    """Simple LCT key metadata"""
    lct_id: str
    public_key_hex: str
    created_at: str
    tpm_device: str

    def to_dict(self) -> Dict:
        return asdict(self)


class SimpleTPMLCT:
    """
    Simplified TPM LCT Identity

    Demonstrates hardware binding using TPM 2.0.
    Phase 2.1: Basic key generation and signing.
    """

    def __init__(self, storage_path: Path = Path("./simple_tpm_keys")):
        if not TPM_AVAILABLE:
            raise ImportError("tpm2-pytss not available")

        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # Connect to TPM
        try:
            self.tcti = TCTILdr("device:/dev/tpmrm0")
            self.esapi = ESAPI(self.tcti)
            print(f"✅ Connected to TPM via /dev/tpmrm0")
        except Exception as e:
            try:
                self.tcti = TCTILdr("device:/dev/tpm0")
                self.esapi = ESAPI(self.tcti)
                print(f"✅ Connected to TPM via /dev/tpm0")
            except Exception as e2:
                raise RuntimeError(f"Failed to connect to TPM: {e}, {e2}")

    def generate_key(self, lct_id: str) -> SimpleLCTKey:
        """
        Generate ECC key in TPM

        This demonstrates hardware binding:
        - Key generated inside TPM
        - Private key never exported
        - Only public key returned
        """
        print(f"🔑 Generating TPM key for {lct_id}...")

        # Use TPM to generate random bytes (proves TPM access)
        random_bytes = self.esapi.get_random(32)
        print(f"   TPM random generated: {random_bytes.hex()[:32]}...")

        # For Phase 2.1, we'll create a simple key using TPM's CreatePrimary
        # This creates a key that exists only while TPM session is active
        try:
            # Create primary key in owner hierarchy
            from tpm2_pytss.types import (
                TPM2B_SENSITIVE_CREATE, TPM2B_PUBLIC, TPM2B_DATA,
                TPML_PCR_SELECTION, TPMT_PUBLIC, TPMA_OBJECT,
                TPMU_PUBLIC_PARMS, TPMS_ECC_PARMS, TPMT_SYM_DEF_OBJECT,
                TPMT_ECC_SCHEME, TPM2_ECC, TPMT_KDF_SCHEME, TPMU_SYM_KEY_BITS,
                TPMU_SYM_MODE
            )
            from tpm2_pytss.constants import TPM2_ALG, TPM2_RH

            # Build template for ECC signing key
            in_public = TPM2B_PUBLIC()
            in_public.publicArea = TPMT_PUBLIC()
            in_public.publicArea.type = TPM2_ALG.ECC
            in_public.publicArea.nameAlg = TPM2_ALG.SHA256

            # Set attributes for signing key
            in_public.publicArea.objectAttributes = (
                TPMA_OBJECT.USERWITHAUTH |
                TPMA_OBJECT.SIGN_ENCRYPT |
                TPMA_OBJECT.FIXEDTPM |
                TPMA_OBJECT.FIXEDPARENT |
                TPMA_OBJECT.SENSITIVEDATAORIGIN
            )

            # ECC parameters
            ecc_parms = TPMS_ECC_PARMS()
            ecc_parms.symmetric = TPMT_SYM_DEF_OBJECT()
            ecc_parms.symmetric.algorithm = TPM2_ALG.NULL
            ecc_parms.scheme = TPMT_ECC_SCHEME()
            ecc_parms.scheme.scheme = TPM2_ALG.ECDSA
            ecc_parms.curveID = TPM2_ECC.NIST_P256
            ecc_parms.kdf = TPMT_KDF_SCHEME()
            ecc_parms.kdf.scheme = TPM2_ALG.NULL

            in_public.publicArea.parameters = TPMU_PUBLIC_PARMS()
            in_public.publicArea.parameters.eccDetail = ecc_parms

            # Create primary key
            handle_out, out_public, _, _, _ = self.esapi.create_primary(
                primaryHandle=TPM2_RH.OWNER,
                inSensitive=TPM2B_SENSITIVE_CREATE(),
                inPublic=in_public,
                outsideInfo=TPM2B_DATA(),
                creationPCR=TPML_PCR_SELECTION()
            )

            # Extract public key
            pub_x = out_public.publicArea.unique.ecc.x.buffer.hex()
            pub_y = out_public.publicArea.unique.ecc.y.buffer.hex()
            public_key_hex = f"ECC-P256:X={pub_x},Y={pub_y}"

            print(f"✅ Key generated in TPM")
            print(f"   Public key: {public_key_hex[:64]}...")

            # Flush the key (not persisting yet - Phase 2.3)
            self.esapi.flush_context(handle_out)

            # Create metadata
            key = SimpleLCTKey(
                lct_id=lct_id,
                public_key_hex=public_key_hex,
                created_at=datetime.utcnow().isoformat(),
                tpm_device="/dev/tpmrm0 or /dev/tpm0"
            )

            # Save metadata
            self._save_metadata(lct_id, key)

            return key

        except Exception as e:
            print(f"❌ Key generation failed: {e}")
            raise

    def test_tpm_access(self) -> bool:
        """Test that we can access TPM"""
        try:
            random_bytes = self.esapi.get_random(16)
            return len(random_bytes) == 16
        except:
            return False

    def _save_metadata(self, lct_id: str, key: SimpleLCTKey):
        """Save key metadata"""
        safe_id = lct_id.replace("@", "_").replace("/", "_")
        meta_file = self.storage_path / f"{safe_id}.json"
        with open(meta_file, "w") as f:
            json.dump(key.to_dict(), f, indent=2)

    def list_keys(self) -> List[str]:
        """List all keys"""
        if not self.storage_path.exists():
            return []
        keys = []
        for f in self.storage_path.glob("*.json"):
            with open(f) as fp:
                meta = json.load(fp)
                keys.append(meta["lct_id"])
        return keys


def main():
    """Test TPM hardware binding"""
    print("=" * 70)
    print("SIMPLIFIED TPM LCT IDENTITY - PHASE 2.1")
    print("=" * 70)
    print()

    if not TPM_AVAILABLE:
        print("❌ tpm2-pytss not installed")
        return 1

    try:
        # Initialize
        print("🔧 Initializing Simple TPM LCT...")
        tpm = SimpleTPMLCT()
        print()

        # Test TPM access
        print("🧪 Testing TPM access...")
        if tpm.test_tpm_access():
            print("✅ TPM access working")
        else:
            print("❌ TPM access failed")
            return 1
        print()

        # Generate key
        test_id = "legion@web4.test"
        print(f"🔑 Generating hardware-bound key for: {test_id}")
        key = tpm.generate_key(test_id)
        print()

        # Show results
        print("📊 Key Metadata:")
        print(f"   LCT ID: {key.lct_id}")
        print(f"   Public Key: {key.public_key_hex[:80]}...")
        print(f"   Created: {key.created_at}")
        print(f"   TPM Device: {key.tpm_device}")
        print()

        # List keys
        print("📋 All TPM Keys:")
        for kid in tpm.list_keys():
            print(f"   - {kid}")
        print()

        print("=" * 70)
        print("✅ PHASE 2.1 DEMONSTRATION COMPLETE")
        print("=" * 70)
        print()
        print("Hardware Binding Validated:")
        print("  ✅ TPM 2.0 device accessible")
        print("  ✅ Key generation inside TPM successful")
        print("  ✅ Public key extraction working")
        print("  ✅ FIXEDTPM attribute prevents key export")
        print()
        print("Next Steps (Phase 2.2):")
        print("  • Implement signing with TPM keys")
        print("  • Add PCR sealing for boot integrity")
        print("  • Implement persistent key storage")
        print("  • Add remote attestation")
        print()

        return 0

    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        print()
        print("Troubleshooting:")
        print("  1. Run with sudo: sudo -E python3 tpm_lct_simple.py")
        print("  2. Check TPM device: ls -la /dev/tpm*")
        print("  3. Add user to tss group: sudo usermod -a -G tss $USER")
        return 1


if __name__ == "__main__":
    exit(main())
