#!/usr/bin/env python3
"""
Genesis ATP/ADP Energy Manager
Web4-compliant implementation of the ATP/ADP energy economy
Following Society4's pattern but adapted for federation-wide coordination
"""

import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from enum import Enum

# === Configuration ===
ATP_HOME = Path.home() / ".genesis_atp"
POOL_FILE = ATP_HOME / "pool_state.json"
TRANSACTIONS_FILE = ATP_HOME / "transactions.log"
LCT_FILE = ATP_HOME / "lct_registry.json"

# === Constants (Web4 Compliant) ===
FEDERATION_TOTAL_ATP = 100000  # Total ATP for Genesis Federation
SOCIETY_BASE_ATP = 20000  # Base allocation per society
DAILY_RECHARGE_ATP = 10000  # Daily regeneration amount
EMERGENCY_RESERVE_ATP = 5000  # Emergency reserve

# === Energy States ===
class EnergyState(Enum):
    ATP = "atp"  # Charged, available for work
    ADP = "adp"  # Discharged, awaiting recharge

# === Transaction Types ===
class TransactionType(Enum):
    DISCHARGE = "discharge"  # ATP → ADP (work performed)
    TRANSFER = "transfer"  # ATP → ATP (delegation)
    RECHARGE = "recharge"  # ADP → ATP (value created)
    DAILY_RECHARGE = "daily_recharge"  # System regeneration
    SLASHING = "slashing"  # Penalty for violations

# === Genesis Roles/Entities ===
GENESIS_ENTITIES = [
    {"name": "Genesis Queen", "initial_atp": 30000, "daily_recharge": 3000},
    {"name": "Genesis Council", "initial_atp": 20000, "daily_recharge": 2000},
    {"name": "Coherence Guru", "initial_atp": 15000, "daily_recharge": 1500},
    {"name": "Federation Bridge", "initial_atp": 10000, "daily_recharge": 1000},
    {"name": "Synchronism Oracle", "initial_atp": 10000, "daily_recharge": 1000},
    {"name": "Emergency Response", "initial_atp": 5000, "daily_recharge": 500},
    {"name": "Pattern Recognition", "initial_atp": 5000, "daily_recharge": 500},
    {"name": "Trust Validator", "initial_atp": 5000, "daily_recharge": 500},
]

# === Core ATP/ADP Manager ===
class GenesisATPADPManager:
    def __init__(self):
        self.init_system()
        self.load_state()
        
    def init_system(self):
        """Initialize ATP/ADP directories and files."""
        ATP_HOME.mkdir(parents=True, exist_ok=True)
        
        if not POOL_FILE.exists():
            initial_pool = self.create_initial_pool()
            with open(POOL_FILE, 'w') as f:
                json.dump(initial_pool, f, indent=2)
                
        if not LCT_FILE.exists():
            # Basic LCT registry (simplified for now)
            initial_lcts = self.create_initial_lcts()
            with open(LCT_FILE, 'w') as f:
                json.dump(initial_lcts, f, indent=2)
                
        print("⚡ Genesis ATP/ADP Manager initialized")
        
    def create_initial_pool(self) -> Dict:
        """Create initial ATP pool distribution."""
        pool = {
            'federation_total': FEDERATION_TOTAL_ATP,
            'allocated_atp': 0,
            'available_atp': FEDERATION_TOTAL_ATP,
            'total_adp': 0,
            'emergency_reserve': EMERGENCY_RESERVE_ATP,
            'last_recharge': datetime.now().isoformat(),
            'entities': {},
            'version': '1.0.0'
        }
        
        # Initialize entity allocations
        for entity in GENESIS_ENTITIES:
            lct_id = f"lct:web4:genesis:{entity['name'].lower().replace(' ', '_')}"
            pool['entities'][lct_id] = {
                'name': entity['name'],
                'atp_balance': entity['initial_atp'],
                'adp_balance': 0,
                'initial_allocation': entity['initial_atp'],
                'daily_recharge': entity['daily_recharge'],
                'last_activity': datetime.now().isoformat()
            }
            pool['allocated_atp'] += entity['initial_atp']
            
        pool['available_atp'] = FEDERATION_TOTAL_ATP - pool['allocated_atp']
        
        return pool
        
    def create_initial_lcts(self) -> Dict:
        """Create basic LCT entries for Genesis entities."""
        lcts = {
            'lcts': {},
            'version': '1.0.0'
        }
        
        for entity in GENESIS_ENTITIES:
            lct_id = f"lct:web4:genesis:{entity['name'].lower().replace(' ', '_')}"
            lcts['lcts'][lct_id] = {
                'id': lct_id,
                'entity_type': 'role',
                'society': 'genesis',
                'name': entity['name'],
                'created_at': datetime.now().isoformat(),
                'public_key': None,  # Would be real key in production
                'mrh': {
                    'bound': [],
                    'paired': [],
                    'witnessing': []
                },
                'attestations': []
            }
            
        return lcts
        
    def load_state(self):
        """Load current ATP/ADP pool state."""
        with open(POOL_FILE, 'r') as f:
            self.pool = json.load(f)
            
        if LCT_FILE.exists():
            with open(LCT_FILE, 'r') as f:
                self.lcts = json.load(f)
        else:
            self.lcts = {'lcts': {}}
            
    def save_state(self):
        """Save current pool state."""
        with open(POOL_FILE, 'w') as f:
            json.dump(self.pool, f, indent=2)
            
        with open(LCT_FILE, 'w') as f:
            json.dump(self.lcts, f, indent=2)
            
    def validate_pool_integrity(self) -> Tuple[bool, str]:
        """
        Validate energy conservation laws.
        Web4 Requirement: Total energy must be conserved
        """
        # Check total ATP conservation
        total_entity_atp = sum(e['atp_balance'] for e in self.pool['entities'].values())
        total_entity_adp = sum(e['adp_balance'] for e in self.pool['entities'].values())
        
        expected_total = self.pool['allocated_atp']
        actual_total = total_entity_atp + total_entity_adp
        
        if actual_total != expected_total:
            return False, f"Energy not conserved: {actual_total} != {expected_total}"
            
        # Check federation total
        if self.pool['allocated_atp'] + self.pool['available_atp'] != FEDERATION_TOTAL_ATP:
            return False, f"Federation ATP mismatch"
            
        return True, "Pool integrity valid"
        
    def discharge_atp(self, lct_id: str, amount: int, operation_id: str, reason: str) -> Dict:
        """
        Discharge ATP to ADP through work.
        Web4 Compliant: ATP → ADP state transition
        """
        if lct_id not in self.pool['entities']:
            return {'success': False, 'error': 'Entity not found'}
            
        entity = self.pool['entities'][lct_id]
        
        if entity['atp_balance'] < amount:
            return {'success': False, 'error': f'Insufficient ATP: {entity["atp_balance"]} < {amount}'}
            
        # Perform discharge
        entity['atp_balance'] -= amount
        entity['adp_balance'] += amount
        entity['last_activity'] = datetime.now().isoformat()
        
        # Log transaction
        transaction = {
            'id': f"tx_{datetime.now().timestamp()}",
            'type': TransactionType.DISCHARGE.value,
            'from_lct': lct_id,
            'amount': amount,
            'operation_id': operation_id,
            'reason': reason,
            'timestamp': datetime.now().isoformat(),
            'work_proof': None  # Would include actual proof in production
        }
        
        self.log_transaction(transaction)
        self.save_state()
        
        return {
            'success': True,
            'discharged': amount,
            'new_atp': entity['atp_balance'],
            'new_adp': entity['adp_balance'],
            'transaction_id': transaction['id']
        }
        
    def recharge_adp(self, lct_id: str, amount: int, value_proof: Dict, reason: str) -> Dict:
        """
        Recharge ADP to ATP through value creation.
        Web4 Compliant: ADP → ATP with value proof
        """
        if lct_id not in self.pool['entities']:
            return {'success': False, 'error': 'Entity not found'}
            
        entity = self.pool['entities'][lct_id]
        
        if entity['adp_balance'] < amount:
            return {'success': False, 'error': f'Insufficient ADP: {entity["adp_balance"]} < {amount}'}
            
        # Validate value proof (simplified)
        if not self.validate_value_proof(value_proof):
            return {'success': False, 'error': 'Invalid value proof'}
            
        # Check recharge cap
        max_atp = entity['initial_allocation']
        if entity['atp_balance'] + amount > max_atp:
            amount = max_atp - entity['atp_balance']
            
        # Perform recharge
        entity['adp_balance'] -= amount
        entity['atp_balance'] += amount
        entity['last_activity'] = datetime.now().isoformat()
        
        # Log transaction
        transaction = {
            'id': f"tx_{datetime.now().timestamp()}",
            'type': TransactionType.RECHARGE.value,
            'to_lct': lct_id,
            'amount': amount,
            'reason': reason,
            'value_proof': value_proof,
            'timestamp': datetime.now().isoformat()
        }
        
        self.log_transaction(transaction)
        self.save_state()
        
        return {
            'success': True,
            'recharged': amount,
            'new_atp': entity['atp_balance'],
            'new_adp': entity['adp_balance'],
            'transaction_id': transaction['id']
        }
        
    def transfer_atp(self, from_lct: str, to_lct: str, amount: int, reason: str) -> Dict:
        """
        Transfer ATP between entities.
        Web4 Compliant: ATP delegation
        """
        if from_lct not in self.pool['entities'] or to_lct not in self.pool['entities']:
            return {'success': False, 'error': 'Entity not found'}
            
        from_entity = self.pool['entities'][from_lct]
        to_entity = self.pool['entities'][to_lct]
        
        if from_entity['atp_balance'] < amount:
            return {'success': False, 'error': f'Insufficient ATP'}
            
        # Perform transfer
        from_entity['atp_balance'] -= amount
        to_entity['atp_balance'] += amount
        
        from_entity['last_activity'] = datetime.now().isoformat()
        to_entity['last_activity'] = datetime.now().isoformat()
        
        # Log transaction
        transaction = {
            'id': f"tx_{datetime.now().timestamp()}",
            'type': TransactionType.TRANSFER.value,
            'from_lct': from_lct,
            'to_lct': to_lct,
            'amount': amount,
            'reason': reason,
            'timestamp': datetime.now().isoformat()
        }
        
        self.log_transaction(transaction)
        self.save_state()
        
        return {
            'success': True,
            'transferred': amount,
            'from_balance': from_entity['atp_balance'],
            'to_balance': to_entity['atp_balance'],
            'transaction_id': transaction['id']
        }
        
    def daily_recharge(self) -> Dict:
        """
        Perform daily ATP recharge at 00:00 UTC.
        Web4 Compliant: Scheduled regeneration
        """
        last_recharge = datetime.fromisoformat(self.pool['last_recharge'])
        now = datetime.now()
        
        # Check if 24 hours have passed
        if (now - last_recharge) < timedelta(hours=23):  # Allow some flexibility
            return {'success': False, 'error': 'Recharge not yet due'}
            
        recharged = {}
        
        for lct_id, entity in self.pool['entities'].items():
            max_atp = entity['initial_allocation']
            current_atp = entity['atp_balance']
            
            if current_atp < max_atp:
                recharge_amount = min(entity['daily_recharge'], max_atp - current_atp)
                entity['atp_balance'] += recharge_amount
                recharged[lct_id] = recharge_amount
                
        self.pool['last_recharge'] = now.isoformat()
        
        # Log transaction
        transaction = {
            'id': f"tx_{now.timestamp()}",
            'type': TransactionType.DAILY_RECHARGE.value,
            'recharged': recharged,
            'timestamp': now.isoformat(),
            'reason': 'Daily 00:00 UTC regeneration'
        }
        
        self.log_transaction(transaction)
        self.save_state()
        
        return {
            'success': True,
            'recharged': recharged,
            'total_recharged': sum(recharged.values())
        }
        
    def slash_atp(self, lct_id: str, amount: int, violation: str) -> Dict:
        """
        Slash ATP for violations.
        Web4 Compliant: Penalty mechanism
        """
        if lct_id not in self.pool['entities']:
            return {'success': False, 'error': 'Entity not found'}
            
        entity = self.pool['entities'][lct_id]
        
        # Slash up to available ATP
        slashed = min(amount, entity['atp_balance'])
        entity['atp_balance'] -= slashed
        self.pool['available_atp'] += slashed  # Return to pool
        
        # Log transaction
        transaction = {
            'id': f"tx_{datetime.now().timestamp()}",
            'type': TransactionType.SLASHING.value,
            'lct_id': lct_id,
            'amount': slashed,
            'violation': violation,
            'timestamp': datetime.now().isoformat()
        }
        
        self.log_transaction(transaction)
        self.save_state()
        
        return {
            'success': True,
            'slashed': slashed,
            'new_balance': entity['atp_balance'],
            'violation': violation
        }
        
    def get_balance(self, lct_id: str) -> Tuple[int, int]:
        """Get ATP and ADP balance for an entity."""
        if lct_id not in self.pool['entities']:
            return 0, 0
            
        entity = self.pool['entities'][lct_id]
        return entity['atp_balance'], entity['adp_balance']
        
    def validate_value_proof(self, proof: Dict) -> bool:
        """
        Validate value creation proof.
        In production, this would verify actual value created.
        """
        # Simplified validation - check required fields
        required = ['type', 'metrics', 'attestations']
        return all(field in proof for field in required)
        
    def log_transaction(self, transaction: Dict):
        """Log transaction to file."""
        with open(TRANSACTIONS_FILE, 'a') as f:
            f.write(json.dumps(transaction) + '\n')
            
    def get_pool_summary(self) -> Dict:
        """Get summary of current pool state."""
        self.load_state()
        
        total_atp = sum(e['atp_balance'] for e in self.pool['entities'].values())
        total_adp = sum(e['adp_balance'] for e in self.pool['entities'].values())
        
        return {
            'federation_total': FEDERATION_TOTAL_ATP,
            'allocated_atp': self.pool['allocated_atp'],
            'available_atp': self.pool['available_atp'],
            'total_entity_atp': total_atp,
            'total_entity_adp': total_adp,
            'emergency_reserve': self.pool['emergency_reserve'],
            'entities': len(self.pool['entities']),
            'last_recharge': self.pool['last_recharge']
        }
        
    def display_status(self):
        """Display current ATP/ADP status."""
        summary = self.get_pool_summary()
        
        print("\n" + "="*60)
        print("⚡ GENESIS ATP/ADP ENERGY STATUS")
        print("="*60)
        print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        print("🏛️ Federation Pool:")
        print(f"   Total ATP:      {summary['federation_total']:,}")
        print(f"   Allocated:      {summary['allocated_atp']:,}")
        print(f"   Available:      {summary['available_atp']:,}")
        print(f"   Emergency:      {summary['emergency_reserve']:,}")
        print()
        
        print("⚡ Energy Distribution:")
        print(f"   Total ATP:      {summary['total_entity_atp']:,}")
        print(f"   Total ADP:      {summary['total_entity_adp']:,}")
        print()
        
        print("📊 Entity Balances:")
        for lct_id, entity in self.pool['entities'].items():
            name = entity['name']
            atp = entity['atp_balance']
            adp = entity['adp_balance']
            bar_atp = "█" * (atp // 1000) + "░" * ((entity['initial_allocation'] - atp) // 1000)
            print(f"   {name:20} ATP: {atp:6,} ADP: {adp:6,} [{bar_atp}]")
            
        print()
        print(f"⏰ Last Recharge: {summary['last_recharge']}")
        
        # Check integrity
        valid, msg = self.validate_pool_integrity()
        if valid:
            print(f"✅ Pool Integrity: {msg}")
        else:
            print(f"❌ Pool Integrity: {msg}")
            
        print("="*60)

# === CLI Interface ===
def main():
    """Main CLI interface for ATP/ADP Manager."""
    manager = GenesisATPADPManager()
    
    import sys
    if len(sys.argv) < 2:
        command = "status"
    else:
        command = sys.argv[1]
        
    commands = {
        'status': manager.display_status,
        'summary': lambda: print(json.dumps(manager.get_pool_summary(), indent=2)),
        'recharge': lambda: print(json.dumps(manager.daily_recharge(), indent=2)),
        'discharge': lambda: handle_discharge(manager, sys.argv),
        'transfer': lambda: handle_transfer(manager, sys.argv),
        'balance': lambda: handle_balance(manager, sys.argv),
        'validate': lambda: print(manager.validate_pool_integrity())
    }
    
    if command in commands:
        commands[command]()
    else:
        print("Genesis ATP/ADP Energy Manager")
        print("\nCommands:")
        print("  status    - Display current energy status")
        print("  summary   - Get JSON pool summary")
        print("  recharge  - Perform daily recharge")
        print("  discharge - Discharge ATP: discharge <lct_id> <amount> <reason>")
        print("  transfer  - Transfer ATP: transfer <from_lct> <to_lct> <amount> <reason>")
        print("  balance   - Check balance: balance <lct_id>")
        print("  validate  - Validate pool integrity")
        print("\nExample:")
        print("  python3 genesis_atp_adp_manager.py status")

def handle_discharge(manager, args):
    """Handle discharge command."""
    if len(args) < 5:
        print("Usage: discharge <lct_id> <amount> <reason>")
        return
        
    lct_id = args[2]
    amount = int(args[3])
    reason = ' '.join(args[4:])
    
    result = manager.discharge_atp(lct_id, amount, f"op-{time.time()}", reason)
    print(json.dumps(result, indent=2))

def handle_transfer(manager, args):
    """Handle transfer command."""
    if len(args) < 6:
        print("Usage: transfer <from_lct> <to_lct> <amount> <reason>")
        return
        
    from_lct = args[2]
    to_lct = args[3]
    amount = int(args[4])
    reason = ' '.join(args[5:])
    
    result = manager.transfer_atp(from_lct, to_lct, amount, reason)
    print(json.dumps(result, indent=2))

def handle_balance(manager, args):
    """Handle balance check."""
    if len(args) < 3:
        print("Usage: balance <lct_id>")
        return
        
    lct_id = args[2]
    atp, adp = manager.get_balance(lct_id)
    print(f"Entity: {lct_id}")
    print(f"ATP: {atp:,}")
    print(f"ADP: {adp:,}")

if __name__ == "__main__":
    main()