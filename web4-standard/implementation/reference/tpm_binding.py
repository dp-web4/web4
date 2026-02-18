#!/usr/bin/env python3
"""
TPM-Bound Linked Context Token (LCT) Implementation

Provides hardware-rooted identity by binding LCTs to TPM 2.0 signing keys.
This creates verifiable digital presence - the private key NEVER leaves the TPM.

Key Concepts:
- **TPM Binding**: LCT identity is tied to a TPM-resident signing key
- **Hardware Attestation**: Signatures prove possession of physical hardware
- **Non-exportable Keys**: Private key material cannot be extracted
- **Persistent Handles**: Keys survive reboots at fixed addresses

Architecture:
    +------------------+
    |   Application    |
    +--------+---------+
             |
    +--------v---------+
    |  TPMBoundLCT     |  <- This module
    |  - create_key()  |
    |  - sign()        |
    |  - verify()      |
    +--------+---------+
             |
    +--------v---------+
    |   tpm2-tools     |  <- Shell commands (requires sudo)
    +--------+---------+
             |
    +--------v---------+
    |   /dev/tpmrm0    |  <- TPM Resource Manager
    +------------------+

Security Properties:
1. Key generation happens IN the TPM (not imported)
2. Private key is `fixedtpm` - cannot be duplicated
3. Signing requires physical access to the TPM
4. Public key hash becomes the LCT identifier

Requirements:
- TPM 2.0 hardware (/dev/tpm0 or /dev/tpmrm0)
- tpm2-tools package installed
- User in 'tss' group OR sudo access
"""

import hashlib
import json
import subprocess
import tempfile
import base64
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple, Dict
from dataclasses import dataclass, asdict
import os


# ============================================================================
# Configuration
# ============================================================================

@dataclass
class TPMConfig:
    """TPM binding configuration"""
    # Persistent handle range for LCT keys (0x81010000 - 0x8101FFFF)
    base_handle: int = 0x81010000

    # Key algorithm
    key_algorithm: str = "ecc"  # ECC is faster and smaller than RSA
    curve: str = "ecc:ecdsa"    # NIST P-256 with ECDSA
    hash_algorithm: str = "sha256"

    # Storage for key metadata
    key_store: Path = Path.home() / ".web4" / "tpm"

    # Use sudo for TPM access (set False if user has direct access)
    use_sudo: bool = True

    def __post_init__(self):
        self.key_store = Path(self.key_store)
        self.key_store.mkdir(parents=True, exist_ok=True)


# ============================================================================
# TPM Command Execution
# ============================================================================

def run_tpm_command(
    cmd: list,
    config: TPMConfig,
    input_data: Optional[bytes] = None
) -> Tuple[bool, str, str]:
    """
    Execute a tpm2-tools command

    Args:
        cmd: Command and arguments (e.g., ["tpm2_getrandom", "8"])
        config: TPM configuration
        input_data: Optional data to pipe to stdin

    Returns:
        (success, stdout, stderr)
    """
    if config.use_sudo:
        cmd = ["sudo"] + cmd

    try:
        result = subprocess.run(
            cmd,
            input=input_data,
            capture_output=True,
            timeout=30
        )
        return (
            result.returncode == 0,
            result.stdout.decode('utf-8', errors='replace'),
            result.stderr.decode('utf-8', errors='replace')
        )
    except subprocess.TimeoutExpired:
        return (False, "", "Command timed out")
    except Exception as e:
        return (False, "", str(e))


def check_tpm_available(config: TPMConfig) -> Tuple[bool, str]:
    """
    Check if TPM is available and accessible

    Returns:
        (available, message)
    """
    # Check device exists
    if not Path("/dev/tpm0").exists() and not Path("/dev/tpmrm0").exists():
        return (False, "No TPM device found (/dev/tpm0 or /dev/tpmrm0)")

    # Try to get random bytes
    success, stdout, stderr = run_tpm_command(
        ["tpm2_getrandom", "8", "--hex"],
        config
    )

    if success:
        return (True, f"TPM available, random: {stdout.strip()}")
    else:
        return (False, f"TPM access failed: {stderr}")


# ============================================================================
# TPM Key Management
# ============================================================================

@dataclass
class TPMKeyInfo:
    """Information about a TPM-resident key"""
    handle: int              # Persistent handle (e.g., 0x81010001)
    public_key_x: str        # ECC X coordinate (hex)
    public_key_y: str        # ECC Y coordinate (hex)
    lct_id: str              # LCT identifier (hash of public key)
    created_at: str          # ISO8601 timestamp
    machine_id: str          # Machine identifier (from /etc/machine-id)
    key_name: str            # TPM key name (hex)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> 'TPMKeyInfo':
        return cls(**data)

    def save(self, config: TPMConfig) -> None:
        """Save key info to disk"""
        path = config.key_store / f"{self.lct_id}.json"
        with open(path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, lct_id: str, config: TPMConfig) -> Optional['TPMKeyInfo']:
        """Load key info from disk"""
        path = config.key_store / f"{lct_id}.json"
        if not path.exists():
            return None
        with open(path, 'r') as f:
            return cls.from_dict(json.load(f))


def get_machine_id() -> str:
    """Get unique machine identifier"""
    try:
        with open("/etc/machine-id", "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        # Fallback to hostname hash
        import socket
        return hashlib.sha256(socket.gethostname().encode()).hexdigest()[:32]


def find_available_handle(config: TPMConfig) -> int:
    """Find an available persistent handle"""
    # Check existing keys
    existing = list(config.key_store.glob("*.json"))
    used_handles = set()

    for key_file in existing:
        try:
            with open(key_file) as f:
                data = json.load(f)
                used_handles.add(data.get('handle', 0))
        except:
            pass

    # Find first available in range
    for i in range(256):
        handle = config.base_handle + i
        if handle not in used_handles:
            return handle

    raise RuntimeError("No available persistent handles")


def create_tpm_key(
    config: Optional[TPMConfig] = None
) -> Tuple[bool, Optional[TPMKeyInfo], str]:
    """
    Create a new TPM-resident signing key

    Steps:
    1. Create primary key in owner hierarchy
    2. Create signing key under primary
    3. Make signing key persistent
    4. Extract public key and compute LCT ID

    Returns:
        (success, key_info, message)
    """
    config = config or TPMConfig()

    # Check TPM available
    available, msg = check_tpm_available(config)
    if not available:
        return (False, None, msg)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        primary_ctx = tmpdir / "primary.ctx"
        key_pub = tmpdir / "key.pub"
        key_priv = tmpdir / "key.priv"
        key_ctx = tmpdir / "key.ctx"

        # 1. Create primary key
        success, stdout, stderr = run_tpm_command([
            "tpm2_createprimary",
            "-C", "o",  # Owner hierarchy
            "-g", config.hash_algorithm,
            "-G", config.key_algorithm,
            "-c", str(primary_ctx)
        ], config)

        if not success:
            return (False, None, f"Failed to create primary: {stderr}")

        # 2. Create signing key
        success, stdout, stderr = run_tpm_command([
            "tpm2_create",
            "-C", str(primary_ctx),
            "-g", config.hash_algorithm,
            "-G", config.curve,
            "-u", str(key_pub),
            "-r", str(key_priv)
        ], config)

        if not success:
            return (False, None, f"Failed to create key: {stderr}")

        # Parse public key coordinates from output
        x_coord = ""
        y_coord = ""
        for line in stdout.split('\n'):
            if line.startswith('x:'):
                x_coord = line.split(':')[1].strip()
            elif line.startswith('y:'):
                y_coord = line.split(':')[1].strip()

        # 3. Load the key
        success, stdout, stderr = run_tpm_command([
            "tpm2_load",
            "-C", str(primary_ctx),
            "-u", str(key_pub),
            "-r", str(key_priv),
            "-c", str(key_ctx)
        ], config)

        if not success:
            return (False, None, f"Failed to load key: {stderr}")

        # Parse key name
        key_name = ""
        for line in stdout.split('\n'):
            if line.startswith('name:'):
                key_name = line.split(':')[1].strip()

        # 4. Make key persistent
        handle = find_available_handle(config)

        success, stdout, stderr = run_tpm_command([
            "tpm2_evictcontrol",
            "-C", "o",
            "-c", str(key_ctx),
            hex(handle)
        ], config)

        if not success:
            return (False, None, f"Failed to persist key: {stderr}")

        # 5. Compute LCT ID from public key
        pub_key_bytes = bytes.fromhex(x_coord + y_coord)
        lct_id = "lct:" + hashlib.sha256(pub_key_bytes).hexdigest()[:32]

        # Create key info
        key_info = TPMKeyInfo(
            handle=handle,
            public_key_x=x_coord,
            public_key_y=y_coord,
            lct_id=lct_id,
            created_at=datetime.now().isoformat(),
            machine_id=get_machine_id(),
            key_name=key_name
        )

        # Save to disk
        key_info.save(config)

        return (True, key_info, f"Created key with LCT ID: {lct_id}")


def list_tpm_keys(config: Optional[TPMConfig] = None) -> list[TPMKeyInfo]:
    """List all TPM keys for this machine"""
    config = config or TPMConfig()
    keys = []

    for key_file in config.key_store.glob("*.json"):
        try:
            with open(key_file) as f:
                data = json.load(f)
                if data.get('machine_id') == get_machine_id():
                    keys.append(TPMKeyInfo.from_dict(data))
        except:
            pass

    return keys


def delete_tpm_key(
    lct_id: str,
    config: Optional[TPMConfig] = None
) -> Tuple[bool, str]:
    """
    Delete a TPM key

    Args:
        lct_id: LCT identifier of key to delete

    Returns:
        (success, message)
    """
    config = config or TPMConfig()

    key_info = TPMKeyInfo.load(lct_id, config)
    if not key_info:
        return (False, f"Key not found: {lct_id}")

    # Remove from TPM
    success, stdout, stderr = run_tpm_command([
        "tpm2_evictcontrol",
        "-C", "o",
        "-c", hex(key_info.handle)
    ], config)

    if not success:
        return (False, f"Failed to evict key: {stderr}")

    # Remove metadata file
    key_file = config.key_store / f"{lct_id}.json"
    if key_file.exists():
        key_file.unlink()

    return (True, f"Deleted key: {lct_id}")


# ============================================================================
# Signing and Verification
# ============================================================================

def tpm_sign(
    data: bytes,
    lct_id: str,
    config: Optional[TPMConfig] = None
) -> Tuple[bool, Optional[str], str]:
    """
    Sign data using TPM-resident key

    Args:
        data: Data to sign
        lct_id: LCT identifier of signing key

    Returns:
        (success, signature_base64, message)
    """
    config = config or TPMConfig()

    key_info = TPMKeyInfo.load(lct_id, config)
    if not key_info:
        return (False, None, f"Key not found: {lct_id}")

    # Use /tmp with predictable path for sudo compatibility
    sig_path = f"/tmp/tpm_sig_{os.getpid()}.bin"

    try:
        # Sign data from stdin, output to file (TPMT_SIGNATURE format for TPM verification)
        success, stdout, stderr = run_tpm_command([
            "tpm2_sign",
            "-c", hex(key_info.handle),
            "-g", config.hash_algorithm,
            "-o", sig_path
        ], config, input_data=data)

        if not success:
            return (False, None, f"Signing failed: {stderr}")

        # Read signature (may need sudo if created by root)
        if config.use_sudo:
            result = subprocess.run(
                ["sudo", "cat", sig_path],
                capture_output=True
            )
            signature = result.stdout
        else:
            with open(sig_path, 'rb') as f:
                signature = f.read()

        if not signature:
            return (False, None, "Empty signature returned")

        sig_b64 = base64.b64encode(signature).decode('ascii')
        return (True, sig_b64, "Signed successfully")

    finally:
        # Cleanup with sudo if needed
        if os.path.exists(sig_path):
            if config.use_sudo:
                subprocess.run(["sudo", "rm", "-f", sig_path], capture_output=True)
            else:
                os.unlink(sig_path)


def tpm_verify(
    data: bytes,
    signature_b64: str,
    lct_id: str,
    config: Optional[TPMConfig] = None
) -> Tuple[bool, str]:
    """
    Verify signature using TPM

    Note: Verification can also be done without TPM using the public key,
    but using TPM ensures the signature format is correct.

    Args:
        data: Original data
        signature_b64: Base64-encoded signature
        lct_id: LCT identifier of signing key

    Returns:
        (valid, message)
    """
    config = config or TPMConfig()

    key_info = TPMKeyInfo.load(lct_id, config)
    if not key_info:
        return (False, f"Key not found: {lct_id}")

    # Use fixed paths for sudo compatibility
    sig_path = f"/tmp/tpm_verify_sig_{os.getpid()}.bin"
    data_path = f"/tmp/tpm_verify_data_{os.getpid()}.bin"

    try:
        # Write files
        with open(sig_path, 'wb') as f:
            f.write(base64.b64decode(signature_b64))
        with open(data_path, 'wb') as f:
            f.write(data)

        success, stdout, stderr = run_tpm_command([
            "tpm2_verifysignature",
            "-c", hex(key_info.handle),
            "-g", config.hash_algorithm,
            "-s", sig_path,
            "-m", data_path
        ], config)

        if success:
            return (True, "Signature valid")
        else:
            return (False, f"Signature invalid: {stderr}")

    finally:
        for path in [sig_path, data_path]:
            if os.path.exists(path):
                try:
                    os.unlink(path)
                except:
                    pass


# ============================================================================
# TPM-Bound LCT
# ============================================================================

@dataclass
class TPMBoundLCT:
    """
    Hardware-bound Linked Context Token

    Represents an identity that is cryptographically tied to a specific
    TPM chip. The private key never leaves the TPM, making this identity
    unforgeable without physical access to the hardware.
    """
    lct_id: str              # LCT identifier (hash of public key)
    public_key_x: str        # ECC X coordinate
    public_key_y: str        # ECC Y coordinate
    machine_id: str          # Machine this LCT is bound to
    created_at: str          # When the binding was created
    tpm_handle: int          # TPM persistent handle

    _config: TPMConfig = None

    @classmethod
    def create(cls, config: Optional[TPMConfig] = None) -> 'TPMBoundLCT':
        """Create a new TPM-bound LCT"""
        config = config or TPMConfig()

        success, key_info, msg = create_tpm_key(config)
        if not success:
            raise RuntimeError(f"Failed to create TPM key: {msg}")

        lct = cls(
            lct_id=key_info.lct_id,
            public_key_x=key_info.public_key_x,
            public_key_y=key_info.public_key_y,
            machine_id=key_info.machine_id,
            created_at=key_info.created_at,
            tpm_handle=key_info.handle
        )
        lct._config = config
        return lct

    @classmethod
    def load(cls, lct_id: str, config: Optional[TPMConfig] = None) -> Optional['TPMBoundLCT']:
        """Load existing TPM-bound LCT"""
        config = config or TPMConfig()

        key_info = TPMKeyInfo.load(lct_id, config)
        if not key_info:
            return None

        lct = cls(
            lct_id=key_info.lct_id,
            public_key_x=key_info.public_key_x,
            public_key_y=key_info.public_key_y,
            machine_id=key_info.machine_id,
            created_at=key_info.created_at,
            tpm_handle=key_info.handle
        )
        lct._config = config
        return lct

    def sign(self, data: bytes) -> str:
        """
        Sign data with this LCT's TPM-resident key

        Args:
            data: Data to sign

        Returns:
            Base64-encoded signature

        Raises:
            RuntimeError if signing fails
        """
        success, sig, msg = tpm_sign(data, self.lct_id, self._config)
        if not success:
            raise RuntimeError(f"Signing failed: {msg}")
        return sig

    def verify(self, data: bytes, signature: str) -> bool:
        """
        Verify a signature against this LCT

        Args:
            data: Original data
            signature: Base64-encoded signature

        Returns:
            True if signature is valid
        """
        valid, msg = tpm_verify(data, signature, self.lct_id, self._config)
        return valid

    def sign_grounding(self, grounding_data: dict) -> dict:
        """
        Sign a grounding announcement with hardware attestation

        Args:
            grounding_data: Grounding data to sign

        Returns:
            Signed grounding with signature and attestation
        """
        # Canonical serialization
        canonical = json.dumps(grounding_data, sort_keys=True, separators=(',', ':'))
        data_bytes = canonical.encode('utf-8')

        # Sign
        signature = self.sign(data_bytes)

        return {
            **grounding_data,
            'lct_id': self.lct_id,
            'signature': signature,
            'attestation': {
                'type': 'tpm2_ecdsa',
                'machine_id': self.machine_id,
                'public_key': {
                    'curve': 'P-256',
                    'x': self.public_key_x,
                    'y': self.public_key_y
                }
            }
        }

    def to_dict(self) -> dict:
        """Export LCT metadata (not the private key!)"""
        return {
            'lct_id': self.lct_id,
            'public_key_x': self.public_key_x,
            'public_key_y': self.public_key_y,
            'machine_id': self.machine_id,
            'created_at': self.created_at,
            'bound_to_tpm': True
        }


# ============================================================================
# Demo
# ============================================================================

def demo_tpm_binding():
    """Demonstrate TPM binding functionality"""

    print("=" * 60)
    print("TPM BINDING DEMO - Hardware-Rooted LCT")
    print("=" * 60)

    config = TPMConfig()

    # Check TPM
    print("\n1. Checking TPM Availability")
    print("-" * 40)
    available, msg = check_tpm_available(config)
    print(f"  Available: {available}")
    print(f"  Message: {msg}")

    if not available:
        print("\nTPM not available. Cannot proceed with demo.")
        return

    # List existing keys
    print("\n2. Existing TPM Keys")
    print("-" * 40)
    keys = list_tpm_keys(config)
    if keys:
        for key in keys:
            print(f"  - {key.lct_id} (handle: {hex(key.handle)})")
    else:
        print("  No existing keys")

    # Create or load LCT
    print("\n3. TPM-Bound LCT")
    print("-" * 40)

    if keys:
        lct = TPMBoundLCT.load(keys[0].lct_id, config)
        print(f"  Loaded existing LCT: {lct.lct_id}")
    else:
        print("  Creating new LCT...")
        lct = TPMBoundLCT.create(config)
        print(f"  Created: {lct.lct_id}")

    print(f"  Machine ID: {lct.machine_id}")
    print(f"  TPM Handle: {hex(lct.tpm_handle)}")

    # Sign test data
    print("\n4. Signing Test Data")
    print("-" * 40)
    test_data = b"Hello from TPM-bound identity!"
    signature = lct.sign(test_data)
    print(f"  Data: {test_data.decode()}")
    print(f"  Signature: {signature[:40]}...")

    # Verify
    print("\n5. Verifying Signature")
    print("-" * 40)
    valid = lct.verify(test_data, signature)
    print(f"  Valid: {valid}")

    # Tampered data
    tampered = b"Hello from TPM-bound identity?"
    valid_tampered = lct.verify(tampered, signature)
    print(f"  Tampered valid: {valid_tampered}")

    # Sign grounding
    print("\n6. Signed Grounding Announcement")
    print("-" * 40)
    grounding = {
        'entity': lct.lct_id,
        'timestamp': datetime.now().isoformat(),
        'location': 'geo:45.5231,-122.6765',
        'hardware_class': 'server'
    }
    signed = lct.sign_grounding(grounding)
    print(f"  Grounding signed with TPM attestation")
    print(f"  Attestation type: {signed['attestation']['type']}")

    print("\n" + "=" * 60)
    print("TPM Binding Demo Complete!")
    print("=" * 60)


if __name__ == "__main__":
    demo_tpm_binding()
