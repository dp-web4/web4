#!/usr/bin/env python3
"""
Genesis Cryptographic Layer
Web4-compliant cryptographic operations for LCTs and attestations
Implements Ed25519 for signatures (partial W4-BASE-1 compliance)
"""

import json
import base64
import hashlib
from pathlib import Path
from typing import Dict, Tuple, Optional
from datetime import datetime

# Try to use cryptography library, fallback to nacl
try:
    from cryptography.hazmat.primitives.asymmetric import ed25519
    from cryptography.hazmat.primitives import serialization
    from cryptography.exceptions import InvalidSignature
    CRYPTO_LIB = "cryptography"
except ImportError:
    try:
        import nacl.signing
        import nacl.encoding
        CRYPTO_LIB = "nacl"
    except ImportError:
        print("Warning: No cryptographic library available. Install cryptography or PyNaCl.")
        CRYPTO_LIB = None

# === Configuration ===
KEYS_HOME = Path.home() / ".genesis_keys"
KEYS_FILE = KEYS_HOME / "keypairs.json"

class GenesisCrypto:
    """Cryptographic operations for Genesis Federation."""
    
    def __init__(self):
        self.init_system()
        self.load_keys()
        
    def init_system(self):
        """Initialize keys directory."""
        KEYS_HOME.mkdir(parents=True, exist_ok=True)
        
        if not KEYS_FILE.exists():
            initial_keys = {
                'keypairs': {},
                'version': '1.0.0'
            }
            with open(KEYS_FILE, 'w') as f:
                json.dump(initial_keys, f, indent=2)
                
    def load_keys(self):
        """Load existing keypairs."""
        with open(KEYS_FILE, 'r') as f:
            self.keys_data = json.load(f)
            
    def save_keys(self):
        """Save keypairs to file."""
        with open(KEYS_FILE, 'w') as f:
            json.dump(self.keys_data, f, indent=2)
            
    def generate_keypair(self, lct_id: str) -> Tuple[str, str]:
        """
        Generate Ed25519 keypair for an LCT.
        Returns (private_key_b64, public_key_b64)
        """
        if CRYPTO_LIB == "cryptography":
            # Use cryptography library
            private_key = ed25519.Ed25519PrivateKey.generate()
            public_key = private_key.public_key()
            
            # Serialize to PEM format
            private_pem = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )
            public_pem = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
            
            # Encode to base64 for storage
            private_b64 = base64.b64encode(private_pem).decode('utf-8')
            public_b64 = base64.b64encode(public_pem).decode('utf-8')
            
        elif CRYPTO_LIB == "nacl":
            # Use PyNaCl library
            signing_key = nacl.signing.SigningKey.generate()
            verify_key = signing_key.verify_key
            
            private_b64 = base64.b64encode(bytes(signing_key)).decode('utf-8')
            public_b64 = base64.b64encode(bytes(verify_key)).decode('utf-8')
            
        else:
            # Fallback: generate placeholder keys
            print("Warning: Using placeholder keys (not secure)")
            private_b64 = base64.b64encode(f"private_key_{lct_id}".encode()).decode('utf-8')
            public_b64 = base64.b64encode(f"public_key_{lct_id}".encode()).decode('utf-8')
            
        # Store keypair
        self.keys_data['keypairs'][lct_id] = {
            'private_key': private_b64,
            'public_key': public_b64,
            'algorithm': 'Ed25519',
            'created_at': datetime.now().isoformat()
        }
        self.save_keys()
        
        return private_b64, public_b64
        
    def sign_data(self, lct_id: str, data: Dict) -> str:
        """
        Sign data with entity's private key.
        Returns base64-encoded signature.
        """
        if lct_id not in self.keys_data['keypairs']:
            raise ValueError(f"No keypair found for {lct_id}")
            
        keypair = self.keys_data['keypairs'][lct_id]
        private_b64 = keypair['private_key']
        
        # Canonicalize data to JSON
        data_bytes = json.dumps(data, sort_keys=True).encode('utf-8')
        
        if CRYPTO_LIB == "cryptography":
            # Decode private key
            private_pem = base64.b64decode(private_b64)
            private_key = serialization.load_pem_private_key(private_pem, password=None)
            
            # Sign data
            signature = private_key.sign(data_bytes)
            
        elif CRYPTO_LIB == "nacl":
            # Decode private key
            private_bytes = base64.b64decode(private_b64)
            signing_key = nacl.signing.SigningKey(private_bytes)
            
            # Sign data
            signed = signing_key.sign(data_bytes)
            signature = signed.signature
            
        else:
            # Fallback: create hash-based "signature"
            signature = hashlib.sha256(private_b64.encode() + data_bytes).digest()
            
        return base64.b64encode(signature).decode('utf-8')
        
    def verify_signature(self, lct_id: str, data: Dict, signature_b64: str) -> bool:
        """
        Verify signature with entity's public key.
        Returns True if valid, False otherwise.
        """
        if lct_id not in self.keys_data['keypairs']:
            return False
            
        keypair = self.keys_data['keypairs'][lct_id]
        public_b64 = keypair['public_key']
        
        # Canonicalize data
        data_bytes = json.dumps(data, sort_keys=True).encode('utf-8')
        signature = base64.b64decode(signature_b64)
        
        try:
            if CRYPTO_LIB == "cryptography":
                # Decode public key
                public_pem = base64.b64decode(public_b64)
                public_key = serialization.load_pem_public_key(public_pem)
                
                # Verify signature
                public_key.verify(signature, data_bytes)
                return True
                
            elif CRYPTO_LIB == "nacl":
                # Decode public key
                public_bytes = base64.b64decode(public_b64)
                verify_key = nacl.signing.VerifyKey(public_bytes)
                
                # Verify signature
                verify_key.verify(data_bytes, signature)
                return True
                
            else:
                # Fallback: compare hashes
                expected = hashlib.sha256(
                    self.keys_data['keypairs'][lct_id]['private_key'].encode() + data_bytes
                ).digest()
                return signature == expected
                
        except (InvalidSignature, nacl.exceptions.BadSignatureError):
            return False
        except Exception as e:
            print(f"Verification error: {e}")
            return False
            
    def create_witness_attestation(self, witness_lct: str, subject_lct: str, 
                                  event: Dict, claim: str) -> Dict:
        """
        Create a witness attestation for an event.
        Web4 compliant witness mark.
        """
        attestation = {
            'witness': witness_lct,
            'subject': subject_lct,
            'event_hash': self.hash_event(event),
            'claim': claim,
            'timestamp': datetime.now().isoformat(),
            'signature': None
        }
        
        # Sign attestation
        attestation['signature'] = self.sign_data(witness_lct, attestation)
        
        return attestation
        
    def verify_attestation(self, attestation: Dict) -> bool:
        """Verify a witness attestation."""
        # Extract signature
        signature = attestation.get('signature')
        if not signature:
            return False
            
        # Create copy without signature for verification
        attestation_copy = attestation.copy()
        attestation_copy['signature'] = None
        
        # Verify with witness's public key
        return self.verify_signature(
            attestation['witness'],
            attestation_copy,
            signature
        )
        
    def hash_event(self, event: Dict) -> str:
        """Create deterministic hash of an event."""
        event_json = json.dumps(event, sort_keys=True)
        event_hash = hashlib.sha256(event_json.encode()).hexdigest()
        return event_hash
        
    def create_mrh_binding(self, lct_id: str, bound_lct: str, 
                          binding_type: str) -> Dict:
        """
        Create MRH (Markov Relevancy Horizon) binding.
        Links entities in contextual zones.
        """
        binding = {
            'from': lct_id,
            'to': bound_lct,
            'type': binding_type,  # 'bound', 'paired', 'witnessing'
            'timestamp': datetime.now().isoformat(),
            'signature': None
        }
        
        # Sign binding
        binding['signature'] = self.sign_data(lct_id, binding)
        
        return binding
        
    def get_public_key(self, lct_id: str) -> Optional[str]:
        """Get public key for an LCT."""
        if lct_id in self.keys_data['keypairs']:
            return self.keys_data['keypairs'][lct_id]['public_key']
        return None
        
    def list_entities(self) -> list:
        """List all entities with keypairs."""
        return list(self.keys_data['keypairs'].keys())
        
    def export_public_keys(self) -> Dict:
        """Export all public keys for sharing."""
        public_keys = {}
        for lct_id, keypair in self.keys_data['keypairs'].items():
            public_keys[lct_id] = {
                'public_key': keypair['public_key'],
                'algorithm': keypair['algorithm']
            }
        return public_keys

# === Transaction Signing ===
class TransactionSigner:
    """Sign ATP/ADP transactions for blockchain submission."""
    
    def __init__(self, crypto: GenesisCrypto):
        self.crypto = crypto
        
    def sign_transaction(self, transaction: Dict, signer_lct: str) -> Dict:
        """
        Sign a transaction for blockchain submission.
        Adds Web4-compliant signature fields.
        """
        # Create canonical transaction for signing
        tx_to_sign = {
            'type': transaction.get('type'),
            'from_lct': transaction.get('from_lct'),
            'to_lct': transaction.get('to_lct'),
            'amount': transaction.get('amount'),
            'timestamp': transaction.get('timestamp'),
            'nonce': self.generate_nonce()
        }
        
        # Sign transaction
        signature = self.crypto.sign_data(signer_lct, tx_to_sign)
        
        # Add signature to transaction
        signed_tx = transaction.copy()
        signed_tx['signature'] = signature
        signed_tx['signer'] = signer_lct
        signed_tx['nonce'] = tx_to_sign['nonce']
        
        return signed_tx
        
    def verify_transaction(self, transaction: Dict) -> bool:
        """Verify a signed transaction."""
        if 'signature' not in transaction or 'signer' not in transaction:
            return False
            
        # Extract fields for verification
        tx_to_verify = {
            'type': transaction.get('type'),
            'from_lct': transaction.get('from_lct'),
            'to_lct': transaction.get('to_lct'),
            'amount': transaction.get('amount'),
            'timestamp': transaction.get('timestamp'),
            'nonce': transaction.get('nonce')
        }
        
        return self.crypto.verify_signature(
            transaction['signer'],
            tx_to_verify,
            transaction['signature']
        )
        
    def generate_nonce(self) -> str:
        """Generate unique nonce for transaction."""
        return hashlib.sha256(
            f"{datetime.now().timestamp()}".encode()
        ).hexdigest()[:16]

# === CLI Interface ===
def main():
    """CLI for cryptographic operations."""
    crypto = GenesisCrypto()
    
    import sys
    if len(sys.argv) < 2:
        command = "help"
    else:
        command = sys.argv[1]
        
    if command == "generate":
        if len(sys.argv) < 3:
            print("Usage: generate <lct_id>")
            return
        lct_id = sys.argv[2]
        private_key, public_key = crypto.generate_keypair(lct_id)
        print(f"Generated keypair for {lct_id}")
        print(f"Public key: {public_key[:50]}...")
        
    elif command == "sign":
        if len(sys.argv) < 4:
            print("Usage: sign <lct_id> <data>")
            return
        lct_id = sys.argv[2]
        data = json.loads(sys.argv[3])
        signature = crypto.sign_data(lct_id, data)
        print(f"Signature: {signature}")
        
    elif command == "verify":
        if len(sys.argv) < 5:
            print("Usage: verify <lct_id> <data> <signature>")
            return
        lct_id = sys.argv[2]
        data = json.loads(sys.argv[3])
        signature = sys.argv[4]
        valid = crypto.verify_signature(lct_id, data, signature)
        print(f"Valid: {valid}")
        
    elif command == "list":
        entities = crypto.list_entities()
        print("Entities with keypairs:")
        for entity in entities:
            print(f"  - {entity}")
            
    elif command == "export":
        public_keys = crypto.export_public_keys()
        print(json.dumps(public_keys, indent=2))
        
    else:
        print("Genesis Cryptographic Layer")
        print("\nCommands:")
        print("  generate <lct_id>  - Generate keypair for entity")
        print("  sign <lct_id> <data>  - Sign data")
        print("  verify <lct_id> <data> <signature>  - Verify signature")
        print("  list  - List entities with keypairs")
        print("  export  - Export public keys")
        print("\nExample:")
        print('  python3 genesis_crypto.py generate "lct:web4:genesis:queen"')

if __name__ == "__main__":
    main()