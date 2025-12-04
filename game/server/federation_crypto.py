"""
Federation Cryptography - Ed25519 Signing and Verification

Provides cryptographic signing and verification for SAGE federation tasks and proofs.
Uses Ed25519 for high-performance signature generation and verification.

Author: Legion Autonomous Session #55
Date: 2025-12-03
References: MULTI_MACHINE_SAGE_FEDERATION_DESIGN.md
"""

from typing import Tuple, Optional
import json
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization


class FederationCrypto:
    """
    Cryptographic operations for SAGE consciousness federation

    Provides Ed25519 signing and verification for:
    - Federation tasks (delegation requests)
    - Execution proofs (results)
    - Platform identity verification
    """

    @staticmethod
    def generate_keypair() -> Tuple[ed25519.Ed25519PrivateKey, ed25519.Ed25519PublicKey]:
        """
        Generate new Ed25519 keypair

        Returns:
        --------
        Tuple[Ed25519PrivateKey, Ed25519PublicKey]
            Private and public key pair
        """
        private_key = ed25519.Ed25519PrivateKey.generate()
        public_key = private_key.public_key()
        return private_key, public_key

    @staticmethod
    def save_keypair(
        private_key: ed25519.Ed25519PrivateKey,
        key_path: Path
    ):
        """
        Save private key to file

        Parameters:
        -----------
        private_key : Ed25519PrivateKey
            Private key to save
        key_path : Path
            Path to save key file
        """
        # Serialize private key
        private_bytes = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )

        # Ensure directory exists
        key_path.parent.mkdir(parents=True, exist_ok=True)

        # Write to file
        key_path.write_bytes(private_bytes)

        # Set restrictive permissions (600)
        key_path.chmod(0o600)

    @staticmethod
    def load_private_key(key_path: Path) -> ed25519.Ed25519PrivateKey:
        """
        Load private key from file

        Parameters:
        -----------
        key_path : Path
            Path to key file

        Returns:
        --------
        Ed25519PrivateKey
            Loaded private key
        """
        private_bytes = key_path.read_bytes()
        private_key = serialization.load_pem_private_key(
            private_bytes,
            password=None
        )
        return private_key

    @staticmethod
    def save_public_key(
        public_key: ed25519.Ed25519PublicKey,
        key_path: Path
    ):
        """
        Save public key to file

        Parameters:
        -----------
        public_key : Ed25519PublicKey
            Public key to save
        key_path : Path
            Path to save key file
        """
        # Serialize public key
        public_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )

        # Ensure directory exists
        key_path.parent.mkdir(parents=True, exist_ok=True)

        # Write to file
        key_path.write_bytes(public_bytes)

    @staticmethod
    def load_public_key(key_path: Path) -> ed25519.Ed25519PublicKey:
        """
        Load public key from file

        Parameters:
        -----------
        key_path : Path
            Path to key file

        Returns:
        --------
        Ed25519PublicKey
            Loaded public key
        """
        public_bytes = key_path.read_bytes()
        public_key = serialization.load_pem_public_key(public_bytes)
        return public_key

    @staticmethod
    def sign_task(
        task_dict: dict,
        private_key: ed25519.Ed25519PrivateKey
    ) -> bytes:
        """
        Sign federation task with Ed25519

        Parameters:
        -----------
        task_dict : dict
            Task dictionary (from FederationTask.to_signable_dict())
        private_key : Ed25519PrivateKey
            Private key for signing

        Returns:
        --------
        bytes
            Signature bytes (64 bytes)
        """
        # Canonical JSON representation
        task_json = json.dumps(task_dict, sort_keys=True)
        task_bytes = task_json.encode('utf-8')

        # Sign with Ed25519
        signature = private_key.sign(task_bytes)

        return signature

    @staticmethod
    def verify_task(
        task_dict: dict,
        signature: bytes,
        public_key: ed25519.Ed25519PublicKey
    ) -> bool:
        """
        Verify federation task signature

        Parameters:
        -----------
        task_dict : dict
            Task dictionary (from FederationTask.to_signable_dict())
        signature : bytes
            Signature to verify
        public_key : Ed25519PublicKey
            Public key for verification

        Returns:
        --------
        bool
            True if signature valid, False otherwise
        """
        try:
            # Canonical JSON representation
            task_json = json.dumps(task_dict, sort_keys=True)
            task_bytes = task_json.encode('utf-8')

            # Verify signature (throws exception if invalid)
            public_key.verify(signature, task_bytes)
            return True

        except Exception:
            return False

    @staticmethod
    def sign_proof(
        proof_dict: dict,
        private_key: ed25519.Ed25519PrivateKey
    ) -> bytes:
        """
        Sign execution proof with Ed25519

        Parameters:
        -----------
        proof_dict : dict
            Proof dictionary (from ExecutionProof.to_signable_dict())
        private_key : Ed25519PrivateKey
            Private key for signing

        Returns:
        --------
        bytes
            Signature bytes (64 bytes)
        """
        # Canonical JSON representation
        proof_json = json.dumps(proof_dict, sort_keys=True)
        proof_bytes = proof_json.encode('utf-8')

        # Sign with Ed25519
        signature = private_key.sign(proof_bytes)

        return signature

    @staticmethod
    def verify_proof(
        proof_dict: dict,
        signature: bytes,
        public_key: ed25519.Ed25519PublicKey
    ) -> bool:
        """
        Verify execution proof signature

        Parameters:
        -----------
        proof_dict : dict
            Proof dictionary (from ExecutionProof.to_signable_dict())
        signature : bytes
            Signature to verify
        public_key : Ed25519PublicKey
            Public key for verification

        Returns:
        --------
        bool
            True if signature valid, False otherwise
        """
        try:
            # Canonical JSON representation
            proof_json = json.dumps(proof_dict, sort_keys=True)
            proof_bytes = proof_json.encode('utf-8')

            # Verify signature (throws exception if invalid)
            public_key.verify(signature, proof_bytes)
            return True

        except Exception:
            return False


class PlatformKeyManager:
    """
    Manages Ed25519 keypairs for federation platforms

    Handles:
    - Key generation
    - Key loading/saving
    - Public key distribution
    - Key rotation
    """

    def __init__(self, platform_name: str, keys_dir: Optional[Path] = None):
        """
        Initialize platform key manager

        Parameters:
        -----------
        platform_name : str
            Platform identifier (e.g., "Legion", "Thor", "Sprout")
        keys_dir : Optional[Path]
            Directory for key storage (default: ~/.web4/federation/keys/)
        """
        self.platform_name = platform_name

        if keys_dir is None:
            keys_dir = Path.home() / ".web4" / "federation" / "keys"

        self.keys_dir = keys_dir
        self.private_key_path = keys_dir / f"{platform_name}_ed25519_private.pem"
        self.public_key_path = keys_dir / f"{platform_name}_ed25519_public.pem"

        self.private_key: Optional[ed25519.Ed25519PrivateKey] = None
        self.public_key: Optional[ed25519.Ed25519PublicKey] = None

    def generate_and_save_keys(self) -> Tuple[ed25519.Ed25519PrivateKey, ed25519.Ed25519PublicKey]:
        """
        Generate new keypair and save to disk

        Returns:
        --------
        Tuple[Ed25519PrivateKey, Ed25519PublicKey]
            Generated keypair
        """
        # Generate keypair
        private_key, public_key = FederationCrypto.generate_keypair()

        # Save to disk
        FederationCrypto.save_keypair(private_key, self.private_key_path)
        FederationCrypto.save_public_key(public_key, self.public_key_path)

        # Cache in memory
        self.private_key = private_key
        self.public_key = public_key

        print(f"Generated keypair for {self.platform_name}")
        print(f"  Private key: {self.private_key_path}")
        print(f"  Public key: {self.public_key_path}")

        return private_key, public_key

    def load_or_generate_keys(self) -> Tuple[ed25519.Ed25519PrivateKey, ed25519.Ed25519PublicKey]:
        """
        Load existing keys or generate new ones if not found

        Returns:
        --------
        Tuple[Ed25519PrivateKey, Ed25519PublicKey]
            Loaded or generated keypair
        """
        if self.private_key_path.exists():
            # Load existing keys
            self.private_key = FederationCrypto.load_private_key(self.private_key_path)
            self.public_key = FederationCrypto.load_public_key(self.public_key_path)
            print(f"Loaded existing keypair for {self.platform_name}")
        else:
            # Generate new keys
            self.private_key, self.public_key = self.generate_and_save_keys()

        return self.private_key, self.public_key

    def get_public_key_bytes(self) -> bytes:
        """
        Get public key as raw bytes for distribution

        Returns:
        --------
        bytes
            Public key bytes (32 bytes for Ed25519)
        """
        if self.public_key is None:
            self.load_or_generate_keys()

        return self.public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )
