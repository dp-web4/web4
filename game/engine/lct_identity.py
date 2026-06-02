# lct_identity.py
try:
    from nacl.signing import SigningKey, VerifyKey
    CRYPTO_BACKEND = "pynacl"
except ImportError:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import (
        Ed25519PrivateKey,
        Ed25519PublicKey
    )
    CRYPTO_BACKEND = "cryptography"

def sign_identity_creator(identity: LCTIdentity, signing_func):
    # Use faster backend when available
    content = identity.signable_content_creator()
    if CRYPTO_BACKEND == "pynacl":
        return sign_with_pynacl(content, signing_func)
    else:
        return sign_with_cryptography(content, signing_func)
