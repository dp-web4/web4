"""
web4_reference_client.py
Toy end-to-end handshake + ATP/ADP roundtrip using crypto stubs.
"""
import json, time
from implementation.reference import web4_crypto_stub as crypto

def demo():
    # Key generation
    alice = crypto.ed25519_generate("alice-key")
    bob = crypto.ed25519_generate("bob-key")

    # --- Handshake (toy) ---
    clienthello = {"type":"ClientHello","suites":["W4-BASE-1"],"nonce":"n1"}
    serverhello = {"type":"ServerHello","suite":"W4-BASE-1","nonce":"n2"}

    transcript = json.dumps([clienthello,serverhello],sort_keys=True)
    auth_msg = {"type":"HandshakeAuth","ts":time.time()}
    signed = crypto.cose_sign(auth_msg, alice)

    assert crypto.cose_verify(signed, alice)

    # --- ATP/ADP flow ---
    grant = {"type":"CreditGrant","grant_id":"atp-123","ceil":{"total":1000,"unit":"J"}}
    token = crypto.jws_sign(grant, bob)
    assert crypto.jws_verify(token, bob)

    usage = {"type":"UsageReport","grant_id":"atp-123","seq":1,"usage":[{"scope":"compute:infer","amount":42,"unit":"J"}]}
    usage_env = crypto.cose_sign(usage, alice)
    assert crypto.cose_verify(usage_env, alice)

    print("Handshake transcript:", transcript)
    print("Auth envelope:", json.dumps(signed, indent=2))
    print("Grant JWS:", token)
    print("Usage envelope:", json.dumps(usage_env, indent=2))

if __name__ == "__main__":
    demo()
