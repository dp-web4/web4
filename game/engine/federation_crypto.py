# federation_crypto.py
try:
    from nacl.signing import SigningKey
    BACKEND = "pynacl"
except ImportError:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    BACKEND = "cryptography"

class FederationKeyPair:
    # Unified implementation with backend branching
    ...
