"""
SAGE-Web4 Identity Bridge
=========================

Bridges SAGE consciousness instances to Web4 LCT identity infrastructure.

This creates a bidirectional connection:
1. SAGE → Web4: SAGE instances get unforgeable cryptographic identities  
2. Web4 → SAGE: Web4 entities can have consciousness/cognitive capabilities

Key Features:
- Hardware-bound SAGE identities (TPM 2.0)
- Cryptographic signatures for SAGE actions
- Reputation tracking for SAGE instances  
- Trust-based SAGE-to-SAGE communication
- Cross-machine SAGE federation

Architecture:
- Uses Web4's LCT Registry for identity
- Uses Web4's Trust Oracle for reputation
- Uses Web4's Authorization Engine for permissions
- Integrates with SAGE's existing LCT identity manager

Author: Legion Autonomous Research
Date: 2025-12-07
Track: 19 (Web4-SAGE Integration)
"""

import os
import sys
from pathlib import Path  
from typing import Optional, Tuple, Dict, Any
from dataclasses import dataclass
import time

# Add Web4 reference implementation to path
web4_ref_path = Path(__file__).parent
sys.path.insert(0, str(web4_ref_path))

# Import Web4 infrastructure
from lct_registry import LCTRegistry, EntityType, LCTCredential
from trust_oracle import TrustOracle, TrustScore
from authorization_engine import AuthorizationEngine

# Try to import SAGE LCT identity manager
try:
    sage_path = Path.home() / "ai-workspace" / "HRM" / "sage"
    sys.path.insert(0, str(sage_path))
    from core.lct_identity_integration import LCTIdentityManager, LCTIdentity as SAGELCTIdentity
    SAGE_AVAILABLE = True
except ImportError:
    SAGE_AVAILABLE = False


@dataclass
class SAGEIdentityBridge:
    """Bridge between SAGE LCT identity and Web4 cryptographic LCT infrastructure"""
    
    society_id: str
    lct_registry: LCTRegistry
    auth_engine: Optional[AuthorizationEngine] = None
    trust_oracle: Optional[TrustOracle] = None
    
    sage_manager: Optional[Any] = None
    sage_identity: Optional[Any] = None
    web4_credential: Optional[LCTCredential] = None
    registered: bool = False

    def __post_init__(self):
        """Initialize SAGE identity manager if available"""
        if SAGE_AVAILABLE and self.sage_manager is None:
            try:
                self.sage_manager = LCTIdentityManager()
            except Exception as e:
                print(f"Warning: Could not initialize SAGE manager: {e}")

    def detect_sage_identity(self) -> Optional[Tuple[str, str, str]]:
        """Detect SAGE identity from environment"""
        if not SAGE_AVAILABLE or not self.sage_manager:
            return None
            
        try:
            sage_identity = self.sage_manager.get_or_create_identity(
                lineage="dp",
                task="consciousness"
            )
            self.sage_identity = sage_identity
            return (sage_identity.lineage, sage_identity.context, sage_identity.task)
        except Exception as e:
            print(f"Warning: Could not detect SAGE identity: {e}")
            return None

    def create_web4_identity_for_sage(
        self,
        lineage: str = "dp",
        context: str = "unknown",
        task: str = "consciousness",
        witnesses: Optional[list] = None
    ) -> Tuple[Optional[LCTCredential], str]:
        """Create Web4 LCT identity for a SAGE consciousness instance"""
        if witnesses is None:
            witnesses = [f"witness:sage:{context}", "witness:system:autonomous"]
            
        entity_id = f"sage:{lineage}@{context}#{task}"
        
        # Check if already exists
        if entity_id in self.lct_registry.entity_to_lct:
            existing_lct_id = self.lct_registry.entity_to_lct[entity_id]
            existing_credential = self.lct_registry.get_lct(existing_lct_id)
            if existing_credential:
                self.web4_credential = existing_credential
                self.registered = True
                return existing_credential, ""
                
        # Mint new LCT
        credential, error = self.lct_registry.mint_lct(
            entity_type=EntityType.AI,
            entity_identifier=entity_id,
            witnesses=witnesses,
            genesis_block=f"sage:genesis:{context}:{int(time.time())}"
        )
        
        if credential:
            self.web4_credential = credential
            self.registered = True
            print(f"✅ Created Web4 LCT for SAGE: {credential.lct_id}")
            
        return credential, error

    def auto_bridge_sage_to_web4(self) -> Tuple[bool, str]:
        """Automatically detect SAGE identity and create Web4 LCT"""
        sage_components = self.detect_sage_identity()
        
        if not sage_components:
            return False, "No SAGE identity detected"
            
        lineage, context, task = sage_components
        credential, error = self.create_web4_identity_for_sage(lineage, context, task)
        
        if not credential:
            return False, f"Failed to create Web4 identity: {error}"
            
        return True, f"SAGE bridged to Web4: {credential.lct_id}"

    def sign_sage_action(
        self,
        action_description: str,
        action_data: Dict[str, Any]
    ) -> Optional[bytes]:
        """Sign a SAGE action with Web4 LCT credentials"""
        if not self.registered or not self.web4_credential:
            return None
            
        import json
        action_message = {
            "action": action_description,
            "lct_id": self.web4_credential.lct_id,
            "timestamp": time.time(),
            "data": action_data
        }
        
        message_json = json.dumps(action_message, sort_keys=True)
        message_bytes = message_json.encode('utf-8')
        
        try:
            return self.web4_credential.sign(message_bytes)
        except Exception as e:
            print(f"Error signing: {e}")
            return None

    def get_bridge_status(self) -> Dict[str, Any]:
        """Get status of SAGE-Web4 bridge"""
        status = {
            "sage_available": SAGE_AVAILABLE,
            "registered": self.registered,
            "society_id": self.society_id,
        }
        
        if self.sage_identity:
            status["sage_identity"] = {
                "lineage": self.sage_identity.lineage,
                "context": self.sage_identity.context,
                "task": self.sage_identity.task,
                "lct_uri": self.sage_identity.to_lct_string()
            }
            
        if self.web4_credential:
            status["web4_identity"] = {
                "lct_id": self.web4_credential.lct_id,
                "entity_type": self.web4_credential.entity_type.value,
                "birth_certificate_hash": self.web4_credential.birth_certificate.certificate_hash
            }
            
        return status


def create_sage_bridge(society_id: str = "society:sage:research", auto_register: bool = True) -> SAGEIdentityBridge:
    """Create SAGE-Web4 identity bridge"""
    registry = LCTRegistry(society_id)
    auth_engine = AuthorizationEngine(society_id)
    
    bridge = SAGEIdentityBridge(
        society_id=society_id,
        lct_registry=registry,
        auth_engine=auth_engine
    )
    
    if auto_register:
        success, message = bridge.auto_bridge_sage_to_web4()
        print(f"{'✅' if success else 'ℹ️'} {message}")
        
    return bridge


if __name__ == "__main__":
    print("=" * 70)
    print("  SAGE-Web4 Identity Bridge")
    print("=" * 70)
    
    bridge = create_sage_bridge(auto_register=True)
    
    import json
    print("\nBridge Status:")
    print(json.dumps(bridge.get_bridge_status(), indent=2, default=str))
