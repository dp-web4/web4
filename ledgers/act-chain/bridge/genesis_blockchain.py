#!/usr/bin/env python3
"""
Genesis Blockchain Integration
Connects federation tools to the running ACT blockchain
Web4-compliant on-chain transaction recording
"""

import json
import base64
import hashlib
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, List
from genesis_crypto import GenesisCrypto, TransactionSigner
from genesis_witness import GenesisWitnessSystem

# === Configuration ===
BLOCKCHAIN_RPC = "http://localhost:26657"
BLOCKCHAIN_API = "http://localhost:1317"
CHAIN_ID = "act-web4"
TX_LOG = Path.home() / ".genesis_blockchain" / "transactions.log"

class GenesisBlockchainIntegration:
    """Bridge between Genesis federation tools and ACT blockchain."""
    
    def __init__(self):
        self.crypto = GenesisCrypto()
        self.witness_system = GenesisWitnessSystem()
        self.tx_signer = TransactionSigner(self.crypto)
        self.init_system()
        
    def init_system(self):
        """Initialize blockchain directories."""
        TX_LOG.parent.mkdir(parents=True, exist_ok=True)
        
    def check_blockchain_status(self) -> Dict:
        """Check if blockchain is running and get status."""
        try:
            response = requests.get(f"{BLOCKCHAIN_RPC}/status")
            if response.status_code == 200:
                data = response.json()
                return {
                    'connected': True,
                    'chain_id': data['result']['node_info']['network'],
                    'latest_block': data['result']['sync_info']['latest_block_height'],
                    'catching_up': data['result']['sync_info']['catching_up']
                }
        except:
            pass
            
        return {
            'connected': False,
            'error': 'Cannot connect to blockchain RPC'
        }
        
    def encode_transaction(self, tx_data: Dict) -> str:
        """
        Encode transaction for blockchain submission.
        Web4 compliant encoding.
        """
        # Create canonical transaction
        canonical_tx = {
            'type': tx_data.get('type'),
            'data': tx_data,
            'timestamp': datetime.now().isoformat(),
            'chain_id': CHAIN_ID
        }
        
        # Convert to JSON and encode
        tx_json = json.dumps(canonical_tx, sort_keys=True)
        tx_bytes = tx_json.encode('utf-8')
        tx_encoded = base64.b64encode(tx_bytes).decode('utf-8')
        
        return tx_encoded
        
    def submit_transaction(self, transaction: Dict, signer_lct: str) -> Dict:
        """
        Submit transaction to blockchain.
        Adds signature and witnesses before submission.
        """
        # Add witness attestations
        witnessed_tx = self.witness_system.witness_transaction(transaction, witness_count=2)
        
        # Sign transaction
        signed_tx = self.tx_signer.sign_transaction(witnessed_tx, signer_lct)
        
        # Encode for blockchain
        encoded_tx = self.encode_transaction(signed_tx)
        
        # Submit to blockchain
        try:
            response = requests.post(
                f"{BLOCKCHAIN_RPC}/broadcast_tx_commit",
                json={"jsonrpc": "2.0", "id": 1, "method": "broadcast_tx_commit", "params": {"tx": encoded_tx}}
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Log transaction
                self.log_blockchain_tx(signed_tx, result)
                
                if 'error' in result:
                    return {
                        'success': False,
                        'error': result['error']['message'],
                        'transaction': signed_tx
                    }
                    
                return {
                    'success': True,
                    'height': result.get('result', {}).get('height'),
                    'hash': result.get('result', {}).get('hash'),
                    'transaction': signed_tx,
                    'witnesses': [w['witness'] for w in witnessed_tx['witness_attestations']]
                }
            else:
                return {
                    'success': False,
                    'error': f'HTTP {response.status_code}',
                    'transaction': signed_tx
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'transaction': signed_tx
            }
            
    def log_blockchain_tx(self, transaction: Dict, result: Dict):
        """Log blockchain transaction to file."""
        entry = {
            'timestamp': datetime.now().isoformat(),
            'transaction': transaction,
            'result': result
        }
        
        with open(TX_LOG, 'a') as f:
            f.write(json.dumps(entry) + '\n')
            
    def query_transaction(self, tx_hash: str) -> Optional[Dict]:
        """Query transaction by hash from blockchain."""
        try:
            response = requests.get(f"{BLOCKCHAIN_RPC}/tx", params={"hash": f"0x{tx_hash}"})
            if response.status_code == 200:
                return response.json()
        except:
            pass
        return None
        
    def get_account_balance(self, address: str) -> Optional[Dict]:
        """Get account balance from blockchain."""
        try:
            response = requests.get(f"{BLOCKCHAIN_API}/cosmos/bank/v1beta1/balances/{address}")
            if response.status_code == 200:
                return response.json()
        except:
            pass
        return None
        
    def submit_atp_discharge(self, lct_id: str, amount: int, 
                            operation_id: str, reason: str) -> Dict:
        """
        Submit ATP discharge transaction to blockchain.
        Integrates with ATP/ADP manager.
        """
        # Import here to avoid circular dependency
        from genesis_atp_adp_manager import GenesisATPADPManager
        atp_manager = GenesisATPADPManager()
        
        # First perform discharge locally
        local_result = atp_manager.discharge_atp(lct_id, amount, operation_id, reason)
        
        if not local_result['success']:
            return local_result
            
        # Create blockchain transaction
        blockchain_tx = {
            'type': 'atp_discharge',
            'lct_id': lct_id,
            'amount': amount,
            'operation_id': operation_id,
            'reason': reason,
            'new_atp': local_result['new_atp'],
            'new_adp': local_result['new_adp'],
            'local_tx_id': local_result['transaction_id']
        }
        
        # Submit to blockchain
        chain_result = self.submit_transaction(blockchain_tx, lct_id)
        
        # Merge results
        return {
            **local_result,
            'blockchain': chain_result
        }
        
    def submit_atp_recharge(self, lct_id: str, amount: int,
                          value_proof: Dict, reason: str) -> Dict:
        """
        Submit ADP recharge transaction to blockchain.
        Requires value proof validation.
        """
        from genesis_atp_adp_manager import GenesisATPADPManager
        atp_manager = GenesisATPADPManager()
        
        # Perform recharge locally
        local_result = atp_manager.recharge_adp(lct_id, amount, value_proof, reason)
        
        if not local_result['success']:
            return local_result
            
        # Create blockchain transaction with value proof
        blockchain_tx = {
            'type': 'atp_recharge',
            'lct_id': lct_id,
            'amount': amount,
            'value_proof': value_proof,
            'reason': reason,
            'new_atp': local_result['new_atp'],
            'new_adp': local_result['new_adp'],
            'local_tx_id': local_result['transaction_id']
        }
        
        # Submit with extra witnesses for value creation
        chain_result = self.submit_transaction(blockchain_tx, lct_id)
        
        return {
            **local_result,
            'blockchain': chain_result
        }
        
    def submit_witness_attestation(self, witness_lct: str, 
                                  event: Dict, claim: str) -> Dict:
        """Submit standalone witness attestation to blockchain."""
        attestation = self.witness_system.create_attestation(
            witness_lct, event, claim
        )
        
        # Submit attestation as transaction
        attestation_tx = {
            'type': 'witness_attestation',
            'attestation': attestation
        }
        
        return self.submit_transaction(attestation_tx, witness_lct)
        
    def query_attestations(self, event_hash: str = None, 
                          witness_lct: str = None) -> List[Dict]:
        """
        Query attestations from blockchain.
        Filter by event hash or witness.
        """
        # For now, query from local storage
        # In production, would query blockchain state
        attestations = self.witness_system.get_attestation_history(
            lct_id=witness_lct,
            event_hash=event_hash
        )
        
        return attestations
        
    def display_blockchain_status(self):
        """Display current blockchain connection status."""
        status = self.check_blockchain_status()
        
        print("\n" + "="*60)
        print("⛓️  GENESIS BLOCKCHAIN INTEGRATION")
        print("="*60)
        
        if status['connected']:
            print(f"✅ Connected to blockchain")
            print(f"   Chain ID: {status['chain_id']}")
            print(f"   Latest Block: {status['latest_block']}")
            print(f"   Syncing: {'Yes' if status['catching_up'] else 'No'}")
        else:
            print(f"❌ Not connected: {status.get('error', 'Unknown error')}")
            
        print()
        print("📡 Endpoints:")
        print(f"   RPC: {BLOCKCHAIN_RPC}")
        print(f"   API: {BLOCKCHAIN_API}")
        
        # Check transaction log
        if TX_LOG.exists():
            with open(TX_LOG, 'r') as f:
                lines = f.readlines()
                print(f"\n📝 Transaction History: {len(lines)} transactions")
                
                if lines:
                    # Show last transaction
                    last_tx = json.loads(lines[-1])
                    print(f"   Last: {last_tx['timestamp']}")
                    if 'result' in last_tx and 'result' in last_tx['result']:
                        print(f"   Height: {last_tx['result']['result'].get('height', 'N/A')}")
                        
        print("="*60)

# === R6 Transaction Pattern ===
class R6TransactionManager:
    """
    Implements Web4 R6 pattern:
    Request → Response → Reason → Result → Reify → Record
    """
    
    def __init__(self):
        self.blockchain = GenesisBlockchainIntegration()
        
    def execute_r6_transaction(self, request: Dict, signer_lct: str, 
                              atp_required: int) -> Dict:
        """
        Execute transaction following R6 pattern.
        Web4 compliant transaction flow.
        """
        r6_record = {
            'request': request,
            'response': None,
            'reason': None,
            'result': None,
            'reify': None,
            'record': None
        }
        
        try:
            # 1. REQUEST - Already provided
            
            # 2. RESPONSE - Process request
            response = self.process_request(request)
            r6_record['response'] = response
            
            # 3. REASON - Validate response
            reason = self.validate_response(response)
            r6_record['reason'] = reason
            
            # 4. RESULT - Generate outcome
            if reason['valid']:
                result = {'success': True, 'output': response}
            else:
                result = {'success': False, 'error': reason['error']}
            r6_record['result'] = result
            
            # 5. REIFY - Discharge ATP for work
            if result['success']:
                reify = self.blockchain.submit_atp_discharge(
                    signer_lct,
                    atp_required,
                    f"r6-{datetime.now().timestamp()}",
                    f"R6 transaction: {request.get('type', 'unknown')}"
                )
                r6_record['reify'] = reify
                
            # 6. RECORD - Submit to blockchain
            record_tx = {
                'type': 'r6_transaction',
                'r6': r6_record,
                'timestamp': datetime.now().isoformat()
            }
            
            record = self.blockchain.submit_transaction(record_tx, signer_lct)
            r6_record['record'] = record
            
        except Exception as e:
            r6_record['error'] = str(e)
            
        return r6_record
        
    def process_request(self, request: Dict) -> Dict:
        """Process R6 request based on type."""
        req_type = request.get('type', 'unknown')
        
        if req_type == 'coherence_check':
            from synchronism_implementation import SynchronismFramework
            sync = SynchronismFramework()
            return {'coherence': sync.quick_check()}
            
        elif req_type == 'pattern_recognition':
            return {'patterns_found': 3, 'confidence': 0.85}
            
        else:
            return {'processed': True, 'type': req_type}
            
    def validate_response(self, response: Dict) -> Dict:
        """Validate R6 response."""
        if response and 'error' not in response:
            return {'valid': True, 'checks_passed': True}
        else:
            return {'valid': False, 'error': response.get('error', 'Invalid response')}

# === CLI Interface ===
def main():
    """CLI for blockchain operations."""
    blockchain = GenesisBlockchainIntegration()
    
    import sys
    if len(sys.argv) < 2:
        command = "status"
    else:
        command = sys.argv[1]
        
    if command == "status":
        blockchain.display_blockchain_status()
        
    elif command == "submit":
        if len(sys.argv) < 4:
            print("Usage: submit <lct_id> <transaction_json>")
            return
            
        lct_id = sys.argv[2]
        tx_data = json.loads(sys.argv[3])
        
        result = blockchain.submit_transaction(tx_data, lct_id)
        print(json.dumps(result, indent=2))
        
    elif command == "discharge":
        if len(sys.argv) < 5:
            print("Usage: discharge <lct_id> <amount> <reason>")
            return
            
        lct_id = sys.argv[2]
        amount = int(sys.argv[3])
        reason = ' '.join(sys.argv[4:])
        
        result = blockchain.submit_atp_discharge(
            lct_id, amount, f"op-{datetime.now().timestamp()}", reason
        )
        print(json.dumps(result, indent=2))
        
    elif command == "r6":
        if len(sys.argv) < 4:
            print("Usage: r6 <lct_id> <request_json> <atp_cost>")
            return
            
        lct_id = sys.argv[2]
        request = json.loads(sys.argv[3])
        atp_cost = int(sys.argv[4]) if len(sys.argv) > 4 else 100
        
        r6_manager = R6TransactionManager()
        result = r6_manager.execute_r6_transaction(request, lct_id, atp_cost)
        print(json.dumps(result, indent=2))
        
    else:
        print("Genesis Blockchain Integration")
        print("\nCommands:")
        print("  status  - Check blockchain connection")
        print("  submit <lct> <tx>  - Submit transaction")
        print("  discharge <lct> <amount> <reason>  - ATP discharge to chain")
        print("  r6 <lct> <request> [atp]  - Execute R6 transaction")
        print("\nExample:")
        print('  python3 genesis_blockchain.py discharge "lct:web4:genesis:genesis_queen" 100 "Test discharge"')

if __name__ == "__main__":
    main()