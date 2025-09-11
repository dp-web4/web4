"""
web4_crypto_stub.py
NON-PRODUCTION cryptographic facade for the Web4 reference client.
This file only provides interfaces + toy implementations to exercise the protocol.
Replace with real COSE/JWS libraries (e.g., python-cose, jwcrypto) in production.
"""
from dataclasses import dataclass
from typing import Tuple, Dict, Any
import hmac, hashlib, json, os, time

@dataclass
class KeyPair:
    kid: str
    sk: bytes
    pk: bytes

def _jcs(obj: Dict[str, Any]) -> bytes:
    """JCS-like canonical JSON (deterministic keys, no whitespace)."""
    return json.dumps(obj, separators=(",", ":"), sort_keys=True).encode("utf-8")

def ed25519_generate(kid: str = None) -> KeyPair:
    # Toy: derive keys from os.urandom; not actual Ed25519.
    kid = kid or f"kid-{int(time.time())}"
    sk = os.urandom(32)
    pk = hashlib.sha256(sk).digest()
    return KeyPair(kid=kid, sk=sk, pk=pk)

def cose_sign(payload: Dict[str, Any], key: KeyPair) -> Dict[str, Any]:
    """Toy COSE-like: place MAC in 'sig' over canonical payload."""
    body = _jcs(payload)
    mac = hmac.new(key.sk, body, hashlib.sha256).digest()
    return {"protected": {"alg": "Ed25519-toy", "kid": key.kid},
            "payload": payload,
            "sig": mac.hex()}

def cose_verify(envelope: Dict[str, Any], key: KeyPair) -> bool:
    body = _jcs(envelope["payload"])
    mac = hmac.new(key.sk, body, hashlib.sha256).digest().hex()
    return hmac.compare_digest(mac, envelope["sig"])

def jws_sign(payload: Dict[str, Any], key: KeyPair) -> str:
    """Toy JWS compact: b64(header).b64(payload).b64(sig)"""
    header = {"alg": "ES256-toy", "kid": key.kid}
    enc = lambda b: base64url(b)
    signing_input = enc(_jcs(header)) + b"." + enc(_jcs(payload))
    sig = hmac.new(key.sk, signing_input, hashlib.sha256).digest()
    return (enc(_jcs(header)) + b"." + enc(_jcs(payload)) + b"." + enc(sig)).decode()

def jws_verify(token: str, key: KeyPair) -> bool:
    try:
        header_b64, payload_b64, sig_b64 = token.split(".")
        signing_input = (header_b64 + "." + payload_b64).encode()
        sig = base64url_decode(sig_b64.encode())
        exp = hmac.new(key.sk, signing_input, hashlib.sha256).digest()
        return hmac.compare_digest(sig, exp)
    except Exception:
        return False

def base64url(b: bytes) -> bytes:
    import base64
    return base64.urlsafe_b64encode(b).rstrip(b"=")

def base64url_decode(b: bytes) -> bytes:
    import base64
    padding = b"=" * ((4 - len(b) % 4) % 4)
    return base64.urlsafe_b64decode(b + padding)
