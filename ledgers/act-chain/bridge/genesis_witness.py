#!/usr/bin/env python3
"""
Genesis Witness System
Web4-compliant witness attestation framework
Implements bidirectional witness marks for trust verification
"""

import json
import random
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from genesis_crypto import GenesisCrypto

# === Configuration ===
WITNESS_HOME = Path.home() / ".genesis_witness"
ATTESTATIONS_FILE = WITNESS_HOME / "attestations.json"
WITNESS_POOL_FILE = WITNESS_HOME / "witness_pool.json"

# === Witness Roles ===
WITNESS_ENTITIES = [
    "lct:web4:genesis:trust_validator",
    "lct:web4:genesis:pattern_recognition", 
    "lct:web4:genesis:synchronism_oracle",
    "lct:web4:genesis:federation_bridge"
]

class GenesisWitnessSystem:
    """Manage witness attestations for Genesis Federation."""
    
    def __init__(self):
        self.crypto = GenesisCrypto()
        self.init_system()
        self.load_state()
        
    def init_system(self):
        """Initialize witness directories."""
        WITNESS_HOME.mkdir(parents=True, exist_ok=True)
        
        if not ATTESTATIONS_FILE.exists():
            initial_attestations = {
                'attestations': [],
                'version': '1.0.0'
            }
            with open(ATTESTATIONS_FILE, 'w') as f:
                json.dump(initial_attestations, f, indent=2)
                
        if not WITNESS_POOL_FILE.exists():
            initial_pool = {
                'witness_entities': WITNESS_ENTITIES,
                'active_witnesses': [],
                'witness_stats': {}
            }
            with open(WITNESS_POOL_FILE, 'w') as f:
                json.dump(initial_pool, f, indent=2)
                
    def load_state(self):
        """Load witness state."""
        with open(ATTESTATIONS_FILE, 'r') as f:
            self.attestations_data = json.load(f)
            
        with open(WITNESS_POOL_FILE, 'r') as f:
            self.witness_pool = json.load(f)
            
    def save_state(self):
        """Save witness state."""
        with open(ATTESTATIONS_FILE, 'w') as f:
            json.dump(self.attestations_data, f, indent=2)
            
        with open(WITNESS_POOL_FILE, 'w') as f:
            json.dump(self.witness_pool, f, indent=2)
            
    def select_witnesses(self, event_type: str, count: int = 2) -> List[str]:
        """
        Select witnesses for an event.
        Web4: Random selection from witness pool.
        """
        available = self.witness_pool['witness_entities']
        
        # Filter out busy witnesses
        available = [w for w in available 
                    if w not in self.witness_pool['active_witnesses']]
        
        if len(available) < count:
            # Use all available witnesses
            selected = available
        else:
            # Random selection
            selected = random.sample(available, count)
            
        # Mark as active
        self.witness_pool['active_witnesses'].extend(selected)
        self.save_state()
        
        return selected
        
    def create_attestation(self, witness_lct: str, event: Dict, 
                          claim: str = "witnessed") -> Dict:
        """
        Create a witness attestation for an event.
        Web4 compliant bidirectional witness mark.
        """
        # Generate event hash
        event_hash = self.crypto.hash_event(event)
        
        # Create attestation structure
        attestation = {
            'id': f"attest_{datetime.now().timestamp()}",
            'witness': witness_lct,
            'subject': event.get('subject_lct', event.get('from_lct')),
            'event_hash': event_hash,
            'event_type': event.get('type'),
            'claim': claim,
            'timestamp': datetime.now().isoformat(),
            'signature': None
        }
        
        # Sign attestation
        try:
            attestation['signature'] = self.crypto.sign_data(
                witness_lct, 
                {k: v for k, v in attestation.items() if k != 'signature'}
            )
        except:
            # If no keypair exists for witness, create one
            self.crypto.generate_keypair(witness_lct)
            attestation['signature'] = self.crypto.sign_data(
                witness_lct,
                {k: v for k, v in attestation.items() if k != 'signature'}
            )
            
        return attestation
        
    def verify_attestation(self, attestation: Dict) -> bool:
        """Verify a witness attestation signature."""
        if 'signature' not in attestation:
            return False
            
        # Extract data for verification
        attestation_data = {k: v for k, v in attestation.items() 
                           if k != 'signature'}
        
        return self.crypto.verify_signature(
            attestation['witness'],
            attestation_data,
            attestation['signature']
        )
        
    def witness_transaction(self, transaction: Dict, witness_count: int = 2) -> Dict:
        """
        Add witness attestations to a transaction.
        Returns transaction with witness marks.
        """
        # Select witnesses
        witnesses = self.select_witnesses(
            transaction.get('type', 'transaction'),
            witness_count
        )
        
        # Create attestations
        attestations = []
        for witness in witnesses:
            attestation = self.create_attestation(
                witness,
                transaction,
                f"Witnessed {transaction.get('type', 'transaction')}"
            )
            attestations.append(attestation)
            
            # Store attestation
            self.attestations_data['attestations'].append(attestation)
            
        # Add attestations to transaction
        witnessed_tx = transaction.copy()
        witnessed_tx['witness_attestations'] = attestations
        witnessed_tx['witness_count'] = len(attestations)
        
        # Release witnesses
        for witness in witnesses:
            if witness in self.witness_pool['active_witnesses']:
                self.witness_pool['active_witnesses'].remove(witness)
                
        # Update witness stats
        for witness in witnesses:
            if witness not in self.witness_pool['witness_stats']:
                self.witness_pool['witness_stats'][witness] = {
                    'total_attestations': 0,
                    'verified': 0,
                    'disputed': 0
                }
            self.witness_pool['witness_stats'][witness]['total_attestations'] += 1
            
        self.save_state()
        
        return witnessed_tx
        
    def verify_witnessed_transaction(self, transaction: Dict) -> Tuple[bool, List[str]]:
        """
        Verify all witness attestations on a transaction.
        Returns (all_valid, list_of_invalid_witnesses).
        """
        if 'witness_attestations' not in transaction:
            return False, ['No witness attestations']
            
        invalid_witnesses = []
        
        for attestation in transaction['witness_attestations']:
            if not self.verify_attestation(attestation):
                invalid_witnesses.append(attestation['witness'])
                
        all_valid = len(invalid_witnesses) == 0
        
        return all_valid, invalid_witnesses
        
    def get_attestation_history(self, lct_id: str = None, 
                               event_hash: str = None) -> List[Dict]:
        """Get attestation history for an entity or event."""
        attestations = self.attestations_data['attestations']
        
        if lct_id:
            # Filter by witness or subject
            attestations = [a for a in attestations 
                          if a['witness'] == lct_id or a['subject'] == lct_id]
                          
        if event_hash:
            # Filter by event
            attestations = [a for a in attestations 
                          if a['event_hash'] == event_hash]
                          
        return attestations
        
    def get_witness_reputation(self, witness_lct: str) -> Dict:
        """Get reputation score for a witness."""
        stats = self.witness_pool['witness_stats'].get(witness_lct, {
            'total_attestations': 0,
            'verified': 0,
            'disputed': 0
        })
        
        if stats['total_attestations'] == 0:
            reputation = 1.0  # Default reputation
        else:
            # Calculate reputation based on verified vs disputed
            reputation = (stats['verified'] - stats['disputed']) / stats['total_attestations']
            reputation = max(0.0, min(1.0, reputation))  # Clamp to [0, 1]
            
        return {
            'witness': witness_lct,
            'reputation': reputation,
            'stats': stats
        }
        
    def create_mrh_witness_binding(self, witness_lct: str, 
                                   subject_lct: str) -> Dict:
        """
        Create MRH witnessing relationship.
        Establishes witness in subject's Markov Relevancy Horizon.
        """
        binding = self.crypto.create_mrh_binding(
            witness_lct,
            subject_lct,
            'witnessing'
        )
        
        return binding
        
    def display_witness_pool(self):
        """Display current witness pool status."""
        print("\n" + "="*60)
        print("👁️  GENESIS WITNESS POOL")
        print("="*60)
        
        print("\n📋 Available Witnesses:")
        for witness in self.witness_pool['witness_entities']:
            active = witness in self.witness_pool['active_witnesses']
            status = "🔴 BUSY" if active else "🟢 AVAILABLE"
            
            rep = self.get_witness_reputation(witness)
            name = witness.split(':')[-1].replace('_', ' ').title()
            
            print(f"   {name:25} {status:12} Rep: {rep['reputation']:.2f}")
            
        print("\n📊 Witness Statistics:")
        total_attestations = sum(
            stats['total_attestations'] 
            for stats in self.witness_pool['witness_stats'].values()
        )
        print(f"   Total Attestations: {total_attestations}")
        print(f"   Active Witnesses: {len(self.witness_pool['active_witnesses'])}")
        
        print("="*60)

# === Integration with ATP/ADP ===
class WitnessedTransactionManager:
    """Integrate witness system with ATP/ADP transactions."""
    
    def __init__(self):
        self.witness_system = GenesisWitnessSystem()
        
    def create_witnessed_discharge(self, lct_id: str, amount: int, 
                                  operation_id: str, reason: str) -> Dict:
        """Create ATP discharge with witness attestations."""
        # Create base transaction
        transaction = {
            'type': 'discharge',
            'from_lct': lct_id,
            'amount': amount,
            'operation_id': operation_id,
            'reason': reason,
            'timestamp': datetime.now().isoformat()
        }
        
        # Add witnesses
        witnessed = self.witness_system.witness_transaction(transaction)
        
        return witnessed
        
    def create_witnessed_recharge(self, lct_id: str, amount: int,
                                 value_proof: Dict, reason: str) -> Dict:
        """Create ADP recharge with witness attestations."""
        # Create base transaction
        transaction = {
            'type': 'recharge',
            'to_lct': lct_id,
            'amount': amount,
            'value_proof': value_proof,
            'reason': reason,
            'timestamp': datetime.now().isoformat()
        }
        
        # Add witnesses (more witnesses for value creation)
        witnessed = self.witness_system.witness_transaction(transaction, witness_count=3)
        
        return witnessed

# === CLI Interface ===
def main():
    """CLI for witness operations."""
    witness_system = GenesisWitnessSystem()
    
    import sys
    if len(sys.argv) < 2:
        command = "status"
    else:
        command = sys.argv[1]
        
    if command == "status":
        witness_system.display_witness_pool()
        
    elif command == "witness":
        if len(sys.argv) < 3:
            print("Usage: witness <transaction_json>")
            return
            
        tx_data = json.loads(sys.argv[2])
        witnessed = witness_system.witness_transaction(tx_data)
        print(json.dumps(witnessed, indent=2))
        
    elif command == "verify":
        if len(sys.argv) < 3:
            print("Usage: verify <witnessed_transaction_json>")
            return
            
        tx_data = json.loads(sys.argv[2])
        valid, invalid = witness_system.verify_witnessed_transaction(tx_data)
        
        if valid:
            print("✅ All witness attestations valid")
        else:
            print(f"❌ Invalid witnesses: {invalid}")
            
    elif command == "history":
        if len(sys.argv) < 3:
            attestations = witness_system.get_attestation_history()
        else:
            lct_id = sys.argv[2]
            attestations = witness_system.get_attestation_history(lct_id=lct_id)
            
        print(f"Found {len(attestations)} attestations")
        for att in attestations[-5:]:  # Show last 5
            print(f"  {att['timestamp']}: {att['witness']} -> {att['claim']}")
            
    else:
        print("Genesis Witness System")
        print("\nCommands:")
        print("  status  - Display witness pool status")
        print("  witness <tx>  - Add witnesses to transaction")
        print("  verify <tx>  - Verify witnessed transaction")
        print("  history [lct]  - Show attestation history")
        print("\nExample:")
        print('  python3 genesis_witness.py witness \'{"type":"transfer","amount":100}\'')

if __name__ == "__main__":
    main()