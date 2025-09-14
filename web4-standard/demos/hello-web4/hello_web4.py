#!/usr/bin/env python3
"""
Hello-Web4 Demo: A minimal implementation showing core Web4 concepts
- Birth certificates (citizen role assignment)
- W4ID exchange (pairing)
- LCT signing and verification
- MRH updates
- Role-contextual trust (no global scores)
"""

import json
import base64
import time
import hashlib
from typing import Dict, Any, Optional

try:
    from nacl import signing
    from nacl.encoding import RawEncoder
except ImportError:
    print("Please install PyNaCl: pip install pynacl")
    exit(1)

def b64(b: bytes) -> str:
    """Base64URL encode without padding"""
    return base64.urlsafe_b64encode(b).decode().rstrip("=")

def b64_decode(s: str) -> bytes:
    """Base64URL decode with padding restoration"""
    padding = "=" * ((4 - len(s) % 4) % 4)
    return base64.urlsafe_b64decode(s + padding)

def generate_lct_id(entity_type: str, pubkey: bytes) -> str:
    """Generate deterministic LCT ID from entity type and public key"""
    h = hashlib.sha256(entity_type.encode() + pubkey).digest()
    return f"lct:web4:{b64(h[:16])}"

def create_birth_certificate(entity: Dict, context: str = "platform") -> Dict:
    """Create birth certificate with citizen role pairing"""
    citizen_role_id = f"lct:web4:role:citizen:{context}"
    birth_cert = {
        "entity_lct": entity["lct_id"],
        "citizen_role": citizen_role_id,
        "context": f"web4://{context}",
        "birth_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "parent_entity": "lct:web4:platform:genesis",
        "birth_witnesses": [
            "lct:web4:witness:time",
            "lct:web4:witness:platform"
        ],
        "initial_rights": ["exist", "interact", "accumulate_reputation"]
    }
    
    # Add citizen role to entity's MRH paired list (permanent pairing)
    entity["mrh"]["paired"].insert(0, {
        "lct_id": citizen_role_id,
        "pairing_type": "birth_certificate",
        "permanent": True,
        "ts": birth_cert["birth_timestamp"]
    })
    
    return birth_cert

def gen_w4id(name: str, entity_type: str = "human") -> Dict:
    """Generate a W4ID with associated keypair and LCT"""
    sk = signing.SigningKey.generate()
    pk = sk.verify_key
    pk_bytes = bytes(pk)
    
    lct_id = generate_lct_id(entity_type, pk_bytes)
    
    return {
        "name": name,
        "lct_id": lct_id,
        "w4id": f"did:web4:key:{b64(pk_bytes)}",
        "entity_type": entity_type,
        "binding": {
            "entity_type": entity_type,
            "public_key": b64(pk_bytes),
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        },
        "mrh": {
            "bound": [],
            "paired": [],  # Citizen role will be added by birth certificate
            "witnessing": [],
            "horizon_depth": 3
        },
        "keys": {"ed25519": b64(pk_bytes)},
        "_sk": sk  # Keep locally, not in real docs
    }

def sign_lct(issuer: Dict, subject: Dict, context: Dict, role: str = "data-provider") -> Dict:
    """Sign an LCT with role-contextual trust"""
    header = {
        "alg": "Ed25519",
        "typ": "LCT-JSON",
        "kid": issuer["w4id"]
    }
    
    # Include role-specific trust scores (T3)
    trust_in_role = {
        "role": role,
        "talent": 0.75,     # Role-specific capability
        "training": 0.80,   # Role-specific expertise
        "temperament": 0.85 # Role-specific reliability
    }
    
    payload = {
        "iss": issuer["w4id"],
        "iss_lct": issuer["lct_id"],
        "sub": subject["w4id"],
        "sub_lct": subject["lct_id"],
        "ctx": context,
        "role": role,
        "t3_in_role": trust_in_role,  # Role-contextual trust
        "mrh": {
            "horizon": 2,
            "depth": 1,
            "relationship_type": "pairing"
        },
        "iat": int(time.time()),
        "exp": int(time.time()) + 3600
    }
    
    # Canonical JSON serialization for signing
    canonical_header = json.dumps(header, separators=(",", ":"), sort_keys=True)
    canonical_payload = json.dumps(payload, separators=(",", ":"), sort_keys=True)
    message = (canonical_header + "." + canonical_payload).encode()
    
    sig = issuer["_sk"].sign(message, encoder=RawEncoder).signature
    
    return {
        "protected": header,
        "payload": payload,
        "sig": b64(sig)
    }

def verify_lct(issuer_pubkey_b64: str, lct: Dict) -> bool:
    """Verify LCT signature and validity"""
    # Reconstruct canonical message
    header = json.dumps(lct["protected"], separators=(",", ":"), sort_keys=True)
    payload = json.dumps(lct["payload"], separators=(",", ":"), sort_keys=True)
    message = (header + "." + payload).encode()
    
    # Verify signature
    sig = b64_decode(lct["sig"])
    vk = signing.VerifyKey(b64_decode(issuer_pubkey_b64))
    
    try:
        vk.verify(message, sig)
    except Exception as e:
        print(f"Signature verification failed: {e}")
        return False
    
    # Check temporal validity
    now = int(time.time())
    if not (lct["payload"]["iat"] <= now <= lct["payload"]["exp"]):
        print("LCT expired or not yet valid")
        return False
    
    return True

def update_mrh(entity: Dict, peer_lct: Dict) -> None:
    """Update entity's MRH with new relationship"""
    mrh_entry = {
        "lct_id": peer_lct["payload"]["iss_lct"],
        "w4id": peer_lct["payload"]["iss"],
        "relationship_type": peer_lct["payload"]["mrh"]["relationship_type"],
        "role": peer_lct["payload"]["role"],
        "context": peer_lct["payload"]["ctx"],
        "t3_scores": peer_lct["payload"]["t3_in_role"],
        "witnessed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }
    
    # Add to paired relationships (after citizen role)
    entity["mrh"]["paired"].append(mrh_entry)
    
    # Also add as witness
    entity["mrh"]["witnessing"].append({
        "lct_id": peer_lct["payload"]["iss_lct"],
        "role": "peer",
        "last_attestation": mrh_entry["witnessed_at"]
    })

def display_trust_context(lct: Dict) -> None:
    """Display role-contextual trust scores"""
    t3 = lct["payload"]["t3_in_role"]
    role = lct["payload"]["role"]
    print(f"\n[TRUST] Role-contextual scores for '{role}':")
    print(f"  Talent:      {t3['talent']:.2f} (capability in role)")
    print(f"  Training:    {t3['training']:.2f} (expertise in role)")
    print(f"  Temperament: {t3['temperament']:.2f} (reliability in role)")
    print(f"  Note: These scores apply ONLY to the '{role}' role")
    print(f"        No global trust score exists!")

def main():
    print("[INIT] Creating entities with birth certificates...")
    
    # 1) Create entities
    alice = gen_w4id("Alice", "human")
    bob = gen_w4id("Bob", "ai")
    
    # 2) Generate birth certificates (citizen role assignment)
    alice_birth = create_birth_certificate(alice, "platform")
    print("[BIRTH] Alice citizen role established    ✅")
    
    bob_birth = create_birth_certificate(bob, "platform")
    print("[BIRTH] Bob citizen role established      ✅")
    
    # 3) Pairing: exchange W4IDs (after birth certificates)
    # In real implementation, this would involve network exchange
    print("[PAIR] Alice↔Bob W4IDs exchanged         ✅")
    
    # 4) Alice issues an LCT to Bob in specific role context
    context = {
        "purpose": "demo-hello-web4",
        "scope": "data-exchange",
        "claim": "greeting-protocol"
    }
    lct = sign_lct(alice, bob, context, role="data-provider")
    print("[SIGN] Alice issued LCT                  ✅")
    
    # 5) Bob verifies Alice's signature
    verified = verify_lct(alice["keys"]["ed25519"], lct)
    if verified:
        print("[VERIFY] Bob verified LCT sig            ✅")
    else:
        print("[VERIFY] Bob verification failed          ❌")
        return
    
    # 6) Bob updates MRH with witnessed relationship
    update_mrh(bob, lct)
    print("[MRH] Bob updated relationship            ✅")
    
    # 7) Display role-contextual trust (no global scores!)
    display_trust_context(lct)
    print("[TRUST] Role-contextual trust verified   ✅")
    
    # Save artifacts for inspection
    def clean_entity(entity: Dict) -> Dict:
        """Remove private key before saving"""
        return {k: v for k, v in entity.items() if k != "_sk"}
    
    with open("sample_w4id_alice.json", "w") as f:
        json.dump(clean_entity(alice), f, indent=2)
    
    with open("sample_w4id_bob.json", "w") as f:
        json.dump(clean_entity(bob), f, indent=2)
    
    with open("sample_lct.json", "w") as f:
        json.dump(lct, f, indent=2)
    
    with open("sample_birth_cert_alice.json", "w") as f:
        json.dump(alice_birth, f, indent=2)
    
    with open("sample_birth_cert_bob.json", "w") as f:
        json.dump(bob_birth, f, indent=2)
    
    print("\n✨ Hello-Web4 demo complete!")
    print("📁 Check the JSON files for detailed inspection")

if __name__ == "__main__":
    main()