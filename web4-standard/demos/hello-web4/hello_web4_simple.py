#!/usr/bin/env python3
"""
Hello-Web4 Demo (No External Dependencies)
Demonstrates core Web4 concepts using only Python standard library
"""

import json
import base64
import time
import hashlib
import hmac
from typing import Dict, Any

def b64(b: bytes) -> str:
    """Base64URL encode without padding"""
    return base64.urlsafe_b64encode(b).decode().rstrip("=")

def generate_mock_keypair(seed: str) -> Dict[str, str]:
    """Generate deterministic mock keypair from seed (for demo only!)"""
    # This is NOT cryptographically secure - just for demonstration
    private = hashlib.sha256(f"private:{seed}".encode()).digest()
    public = hashlib.sha256(f"public:{seed}".encode()).digest()
    return {
        "private": b64(private),
        "public": b64(public)
    }

def mock_sign(message: str, private_key: str) -> str:
    """Mock signature using HMAC (for demo only!)"""
    # This is NOT a real signature - just for demonstration
    key = base64.urlsafe_b64decode(private_key + "===")
    sig = hmac.new(key, message.encode(), hashlib.sha256).digest()
    return b64(sig)

def mock_verify(message: str, signature: str, public_key: str) -> bool:
    """Mock signature verification (for demo only!)"""
    # In real implementation, this would use proper crypto
    # For demo, we just check that signature is non-empty
    return len(signature) > 0 and len(public_key) > 0

def generate_lct_id(entity_type: str, pubkey: str) -> str:
    """Generate deterministic LCT ID"""
    h = hashlib.sha256(f"{entity_type}:{pubkey}".encode()).digest()
    return f"lct:web4:{b64(h[:16])}"

def create_entity(name: str, entity_type: str = "human") -> Dict:
    """Create a Web4 entity with birth certificate"""
    keys = generate_mock_keypair(name)
    lct_id = generate_lct_id(entity_type, keys["public"])
    
    entity = {
        "name": name,
        "lct_id": lct_id,
        "w4id": f"did:web4:key:{keys['public']}",
        "entity_type": entity_type,
        "binding": {
            "entity_type": entity_type,
            "public_key": keys["public"],
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        },
        "birth_certificate": {
            "citizen_role": "lct:web4:role:citizen:platform",
            "context": "platform",
            "birth_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "parent_entity": "lct:web4:platform:genesis",
            "birth_witnesses": ["lct:web4:witness:time", "lct:web4:witness:platform"],
            "initial_rights": ["exist", "interact", "accumulate_reputation"]
        },
        "mrh": {
            "bound": [],
            "paired": [
                {
                    "lct_id": "lct:web4:role:citizen:platform",
                    "pairing_type": "birth_certificate",
                    "permanent": True,
                    "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                }
            ],
            "witnessing": [],
            "horizon_depth": 3
        },
        "keys": keys
    }
    
    return entity

def create_lct(issuer: Dict, subject: Dict, role: str = "data-provider") -> Dict:
    """Create a signed LCT with role-contextual trust"""
    
    # Role-specific trust scores (NOT global!)
    trust_in_role = {
        "role": role,
        "talent": 0.75,     # Capability in THIS role
        "training": 0.80,   # Expertise in THIS role  
        "temperament": 0.85 # Reliability in THIS role
    }
    
    payload = {
        "iss": issuer["w4id"],
        "iss_lct": issuer["lct_id"],
        "sub": subject["w4id"],
        "sub_lct": subject["lct_id"],
        "context": {
            "purpose": "demo-hello-web4",
            "scope": "data-exchange",
            "claim": "greeting-protocol"
        },
        "role": role,
        "t3_in_role": trust_in_role,
        "mrh": {
            "horizon": 2,
            "depth": 1,
            "relationship_type": "pairing"
        },
        "iat": int(time.time()),
        "exp": int(time.time()) + 3600
    }
    
    # Create signature (mock for demo)
    message = json.dumps(payload, separators=(",", ":"), sort_keys=True)
    signature = mock_sign(message, issuer["keys"]["private"])
    
    return {
        "protected": {
            "alg": "MockEd25519",
            "typ": "LCT-JSON",
            "kid": issuer["w4id"]
        },
        "payload": payload,
        "sig": signature
    }

def update_mrh(entity: Dict, lct: Dict) -> None:
    """Update entity's MRH with new relationship"""
    mrh_entry = {
        "lct_id": lct["payload"]["iss_lct"],
        "w4id": lct["payload"]["iss"],
        "relationship_type": lct["payload"]["mrh"]["relationship_type"],
        "role": lct["payload"]["role"],
        "context": lct["payload"]["context"],
        "t3_scores": lct["payload"]["t3_in_role"],
        "witnessed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }
    
    entity["mrh"]["paired"].append(mrh_entry)
    entity["mrh"]["witnessing"].append({
        "lct_id": lct["payload"]["iss_lct"],
        "role": "peer",
        "last_attestation": mrh_entry["witnessed_at"]
    })

def main():
    print("=" * 60)
    print("Hello-Web4 Demo - Core Concepts Demonstration")
    print("=" * 60)
    print()
    
    # Step 1: Create entities with birth certificates
    print("📝 Creating entities with birth certificates...")
    alice = create_entity("Alice", "human")
    bob = create_entity("Bob", "ai")
    
    print(f"  ✅ Alice created (LCT: {alice['lct_id'][:20]}...)")
    print(f"     Citizen role: {alice['birth_certificate']['citizen_role']}")
    print(f"  ✅ Bob created (LCT: {bob['lct_id'][:20]}...)")
    print(f"     Citizen role: {bob['birth_certificate']['citizen_role']}")
    print()
    
    # Step 2: Show initial MRH state
    print("🔗 Initial MRH state (birth certificates only):")
    print(f"  Alice has {len(alice['mrh']['paired'])} pairing(s)")
    print(f"    - Citizen role (permanent): ✅")
    print(f"  Bob has {len(bob['mrh']['paired'])} pairing(s)")
    print(f"    - Citizen role (permanent): ✅")
    print()
    
    # Step 3: Create and exchange LCT
    print("📨 Alice issues LCT to Bob...")
    lct = create_lct(alice, bob, role="data-provider")
    
    # Mock verification
    verified = mock_verify(
        json.dumps(lct["payload"], separators=(",", ":"), sort_keys=True),
        lct["sig"],
        alice["keys"]["public"]
    )
    
    if verified:
        print("  ✅ LCT created and signed")
        print("  ✅ Bob verified Alice's signature")
    print()
    
    # Step 4: Show role-contextual trust
    print("🎯 Role-Contextual Trust (NO global scores!):")
    t3 = lct["payload"]["t3_in_role"]
    role = lct["payload"]["role"]
    print(f"  Alice's trust as '{role}':")
    print(f"    Talent:      {t3['talent']:.2f} (capability in role)")
    print(f"    Training:    {t3['training']:.2f} (expertise in role)")
    print(f"    Temperament: {t3['temperament']:.2f} (reliability in role)")
    print()
    print("  ⚠️  These scores apply ONLY to the 'data-provider' role!")
    print("  ⚠️  Alice might have different trust scores as 'surgeon' or 'mechanic'")
    print("  ⚠️  Web4 has NO global trust scores - trust is always contextual!")
    print()
    
    # Step 5: Update MRH
    print("🔄 Bob updates MRH with new relationship...")
    update_mrh(bob, lct)
    print(f"  Bob now has {len(bob['mrh']['paired'])} pairing(s)")
    print(f"  Bob now has {len(bob['mrh']['witnessing'])} witness relationship(s)")
    print()
    
    # Step 6: Save artifacts
    print("💾 Saving demonstration artifacts...")
    
    # Clean private keys before saving
    alice_clean = {k: v for k, v in alice.items() if k != "keys"}
    alice_clean["public_key"] = alice["keys"]["public"]
    
    bob_clean = {k: v for k, v in bob.items() if k != "keys"}
    bob_clean["public_key"] = bob["keys"]["public"]
    
    with open("demo_alice.json", "w") as f:
        json.dump(alice_clean, f, indent=2)
    
    with open("demo_bob.json", "w") as f:
        json.dump(bob_clean, f, indent=2)
    
    with open("demo_lct.json", "w") as f:
        json.dump(lct, f, indent=2)
    
    print("  ✅ demo_alice.json")
    print("  ✅ demo_bob.json")
    print("  ✅ demo_lct.json")
    print()
    
    print("=" * 60)
    print("✨ Hello-Web4 demo complete!")
    print("=" * 60)
    print()
    print("Key concepts demonstrated:")
    print("  1. Birth certificates (citizen role) for all entities")
    print("  2. Role-contextual trust (no global scores)")
    print("  3. MRH relationship tracking")
    print("  4. LCT as signed context unit")
    print("  5. W4ID/DID-style identifiers")
    print()
    print("Note: This demo uses mock crypto for simplicity.")
    print("Real implementations must use proper Ed25519/X25519!")

if __name__ == "__main__":
    main()