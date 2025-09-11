# Minimal COSE/JWS signing stubs for Web4 reference client
# WARNING: Illustrative only, not for production.

from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric.utils import Prehashed

def cose_sign_ed25519(payload: bytes, sk: bytes) -> bytes:
    sk_obj = ed25519.Ed25519PrivateKey.from_private_bytes(sk)
    return sk_obj.sign(payload)

def jws_sign_es256(payload: bytes, sk_pem: bytes) -> bytes:
    from cryptography.hazmat.primitives.asymmetric import ec
    sk = serialization.load_pem_private_key(sk_pem, password=None)
    return sk.sign(payload, ec.ECDSA(hashes.SHA256()))
