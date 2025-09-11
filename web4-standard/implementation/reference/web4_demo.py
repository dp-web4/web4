"""
web4_demo.py
Tiny, single-file demo that exercises:
  1) Handshake (ClientHello/ServerHello + HandshakeAuth)
  2) Session key derivation (toy HKDF)
  3) ATP/ADP metering (CreditGrant -> UsageReport -> Settle)
using the toy crypto facade in web4_crypto_stub.py.

Run:
  python web4_demo.py

Note: This is illustrative only. Do not use in production.
"""
import json, os, time, hashlib, hmac
from typing import Dict, Any, Tuple
from web4_crypto_stub import ed25519_generate, cose_sign, cose_verify, KeyPair

def jcs(obj: Dict[str, Any]) -> bytes:
    return json.dumps(obj, separators=(",", ":"), sort_keys=True).encode("utf-8")

def hkdf_sha256(secret: bytes, info: bytes, L: int) -> bytes:
    # Minimal HKDF-Expand for demo (assumes Extract already done).
    out = b""
    T = b""
    counter = 1
    while len(out) < L:
        T = hmac.new(secret, T + info + bytes([counter]), hashlib.sha256).digest()
        out += T
        counter += 1
    return out[:L]

def base32_nopad(b: bytes) -> str:
    import base64
    return base64.b32encode(b).decode().rstrip("=")

def derive_w4idp(sk_master: bytes, peer_salt: bytes) -> str:
    prk = hmac.new(peer_salt, sk_master, hashlib.sha256).digest()
    w = hkdf_sha256(prk, b"W4IDp:v1", 16)
    return "w4idp-" + base32_nopad(w)

def transcript_hash(*msgs: Dict[str, Any]) -> bytes:
    h = hashlib.sha256()
    for m in msgs:
        h.update(jcs(m))
    return h.digest()

def aead_key_from_exporter(exporter: bytes, tag: str, length=32) -> bytes:
    return hkdf_sha256(exporter, tag.encode(), length)

def demo():
    # --- Keys & identities (toy) ---
    I_sig: KeyPair = ed25519_generate("init-sign")
    R_sig: KeyPair = ed25519_generate("resp-sign")
    I_master = os.urandom(32)
    R_master = os.urandom(32)
    I_peer_salt = os.urandom(16)
    R_peer_salt = os.urandom(16)
    I_w4idp = derive_w4idp(I_master, R_peer_salt)
    R_w4idp = derive_w4idp(R_master, I_peer_salt)

    # --- ClientHello ---
    ch = {
        "type": "ClientHello",
        "ver": "w4/1",
        "w4idp_hint": I_w4idp,
        "suites": ["W4-BASE-1", "W4-FIPS-1", "W4-GREASE-93f07f2a"],
        "media": ["application/web4+cbor", "application/web4+json"],
        "ext": ["w4_ext_sdjwt_vp@1", "w4_ext_93f07f2a@0"],
        "nonce": base32_nopad(os.urandom(12).ljust(12,b'\x00')),
        "ts": "2025-09-11T15:00:00Z",
        "kex_epk": "X25519:ephemeral-pub-ABCD"   # placeholder
    }

    # --- ServerHello ---
    sh = {
        "type": "ServerHello",
        "ver": "w4/1",
        "w4idp": R_w4idp,
        "suite": "W4-BASE-1",
        "media": "application/web4+cbor",
        "ext_ack": ["w4_ext_sdjwt_vp@1"],
        "nonce": base32_nopad(os.urandom(12).ljust(12,b'\x00')),
        "ts": "2025-09-11T15:00:01Z",
        "kex_epk": "X25519:ephemeral-pub-DCBA"   # placeholder
    }

    TH = transcript_hash(ch, sh)
    exporter = hashlib.sha256(TH + b"exporter").digest()
    kI = aead_key_from_exporter(exporter, "W4-SessionKeys:I->R")
    kR = aead_key_from_exporter(exporter, "W4-SessionKeys:R->I")

    # --- HandshakeAuth (I -> R) ---
    auth_I = {
        "type": "HandshakeAuth",
        "suite": "W4-BASE-1",
        "kid": I_sig.kid,
        "alg": "Ed25519-toy",
        "cap": {"scopes": ["read:lct", "write:lct"]},
        "th": TH.hex(),
        "ts": "2025-09-11T15:00:02Z"
    }
    env_I = cose_sign(auth_I, I_sig)
    assert cose_verify(env_I, I_sig), "Self-verify failed (I)"

    # Receiver verifies
    assert cose_verify(env_I, I_sig), "Responder failed to verify Initiator"

    # --- HandshakeAuth (R -> I) ---
    auth_R = {
        "type": "HandshakeAuth",
        "suite": "W4-BASE-1",
        "kid": R_sig.kid,
        "alg": "Ed25519-toy",
        "cap": {"scopes": ["read:lct"]},
        "th": TH.hex(),
        "ts": "2025-09-11T15:00:02Z"
    }
    env_R = cose_sign(auth_R, R_sig)
    assert cose_verify(env_R, R_sig), "Self-verify failed (R)"
    assert cose_verify(env_R, R_sig), "Initiator failed to verify Responder"

    # --- Metering: CreditGrant (R->I) ---
    grant = {
        "type": "CreditGrant",
        "ver": "w4/1",
        "grant_id": "atp-DEMO-123",
        "scopes": ["compute:infer","net:egress"],
        "ceil": {"total": 10000, "unit": "joule-equivalent"},
        "rate": {"max_per_min": 5000},
        "window": {"size_s": 60, "burst": 1},
        "not_before": "2025-09-11T15:00:00Z",
        "not_after": "2025-09-11T16:00:00Z",
    }
    grant_env = cose_sign(grant, R_sig)
    assert cose_verify(grant_env, R_sig), "Grant verify failed at Initiator"

    # --- UsageReport (I->R) ---
    report = {
        "type": "UsageReport",
        "ver": "w4/1",
        "grant_id": "atp-DEMO-123",
        "seq": 1,
        "window": "2025-09-11T15:00:00Z/2025-09-11T15:01:00Z",
        "usage": [
            {"scope":"compute:infer","amount":420,"unit":"joule-equivalent"}
        ]
    }
    report_env = cose_sign(report, I_sig)
    assert cose_verify(report_env, I_sig), "Report verify failed at Responder"

    # --- Settle (R->I) ---
    settle = {
        "type":"Settle",
        "ver":"w4/1",
        "grant_id":"atp-DEMO-123",
        "up_to_seq":1,
        "balance":{"remaining":9600,"unit":"joule-equivalent"},
        "receipt":"rcpt-DEMO-1"
    }
    settle_env = cose_sign(settle, R_sig)
    assert cose_verify(settle_env, R_sig), "Settle verify failed at Initiator"

    # --- Output summary ---
    bundle = {
        "ClientHello": ch,
        "ServerHello": sh,
        "HandshakeAuth_I": env_I,
        "HandshakeAuth_R": env_R,
        "CreditGrant": grant_env,
        "UsageReport": report_env,
        "Settle": settle_env,
        "SessionKeys": {"I_to_R": kI.hex()[:32]+"...", "R_to_I": kR.hex()[:32]+"..."}
    }
    print(json.dumps(bundle, indent=2))

if __name__ == "__main__":
    demo()
