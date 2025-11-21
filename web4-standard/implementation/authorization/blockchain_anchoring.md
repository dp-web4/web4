# Blockchain Anchoring for Trust Database
**Session #56 Extension**: Unforgeable trust through witnessed presence

## Problem Statement

Current implementation vulnerability:
```
Database → Trust Scores → No cryptographic proof
                        ↓
            Administrator can alter history
            Sybil attacks undetectable
            Replay attacks possible
            No audit trail
```

Web4 principle violated: **"Presence exists only through witnessing"**

## Solution: Minimal On-Chain Witnessing

Not full data on-chain (expensive, slow), but enough to:
1. **Deter** tampering - knowing it will be detected
2. **Detect** tampering - verify database against chain
3. **Prove** authenticity - cryptographic trust history

## Architecture

### Three-Layer Design

```
Layer 1: Off-Chain (Database)
├── Full trust update details
├── Individual action records
├── Real-time score computations
└── High-frequency updates (60x batched)

Layer 2: Merkle Tree (Memory)
├── Hash of each trust update batch
├── Merkle root computed per flush
├── Combines 100+ updates into single hash
└── Enables efficient proof-of-inclusion

Layer 3: On-Chain (Blockchain)
├── Merkle roots (one per flush)
├── LCT birth certificates
├── Critical delegations
└── Periodic trust checkpoints
```

### What Goes On-Chain (Minimal)

**1. Trust Update Merkle Roots** (every flush)
```solidity
struct TrustBatchAnchor {
    bytes32 merkleRoot;          // Root of all updates in batch
    uint256 timestamp;           // Block timestamp
    uint256 batchSize;           // Number of updates
    bytes32 previousRoot;        // Chain previous batches
    bytes signature;             // Batcher signature
}
```

**Cost**: ~200 gas per flush (60 seconds) = ~3.3 gas/second
**Frequency**: Every 60 seconds or 100 updates (whichever first)

**2. LCT Birth Certificates** (once per identity)
```solidity
struct LCTBirthCertificate {
    string lct_id;               // LCT identity
    bytes32 publicKeyHash;       // Public key hash
    bytes32 hardwareBinding;     // Hardware TPM hash (optional)
    uint256 birthTimestamp;      // Creation time
    bytes signature;             // Creator signature
}
```

**Cost**: ~500 gas per identity creation
**Frequency**: Rare (new entities only)

**3. Delegation Anchors** (critical delegations only)
```solidity
struct DelegationAnchor {
    string delegatorLCT;         // Who delegates
    string delegateeLCT;         // To whom
    bytes32 permissionsHash;     // Hash of permissions
    uint256 expiresAt;           // Expiration timestamp
    bytes signature;             // Delegator signature
}
```

**Cost**: ~300 gas per critical delegation
**Frequency**: Occasional (admin delegations, etc.)

**4. Trust Checkpoints** (periodic snapshots)
```solidity
struct TrustCheckpoint {
    bytes32 databaseStateRoot;   // Merkle root of entire DB state
    uint256 totalEntities;       // Entity count
    uint256 totalUpdates;        // Update count
    uint256 checkpointNumber;    // Sequential checkpoint ID
    bytes signature;             // Validator signature
}
```

**Cost**: ~400 gas per checkpoint
**Frequency**: Daily or weekly

## Implementation

### Merkle Tree for Trust Updates

```python
# trust_merkle_tree.py

import hashlib
from typing import List, Tuple
from dataclasses import dataclass

@dataclass
class TrustUpdateLeaf:
    """Single trust update in Merkle tree"""
    lct_id: str
    org_id: str
    talent_delta: Decimal
    training_delta: Decimal
    temperament_delta: Decimal
    veracity_delta: Decimal
    validity_delta: Decimal
    valuation_delta: Decimal
    timestamp: datetime

    def hash(self) -> bytes:
        """Hash this update for Merkle tree"""
        data = f"{self.lct_id}:{self.org_id}:"
        data += f"{self.talent_delta}:{self.training_delta}:{self.temperament_delta}:"
        data += f"{self.veracity_delta}:{self.validity_delta}:{self.valuation_delta}:"
        data += f"{self.timestamp.isoformat()}"

        return hashlib.sha256(data.encode('utf-8')).digest()


class TrustMerkleTree:
    """
    Merkle tree for trust update batches.

    Enables:
    - Single on-chain hash representing 100+ updates
    - Proof-of-inclusion for any update
    - Tamper detection
    """

    def __init__(self, updates: List[TrustUpdateLeaf]):
        """Build Merkle tree from trust updates"""
        self.leaves = updates
        self.tree = self._build_tree()
        self.root = self.tree[-1][0] if self.tree else None

    def _build_tree(self) -> List[List[bytes]]:
        """Build complete Merkle tree"""
        if not self.leaves:
            return []

        # Leaf level
        current_level = [leaf.hash() for leaf in self.leaves]
        tree = [current_level]

        # Build up to root
        while len(current_level) > 1:
            next_level = []
            for i in range(0, len(current_level), 2):
                left = current_level[i]
                right = current_level[i + 1] if i + 1 < len(current_level) else left

                # Hash pair
                parent = hashlib.sha256(left + right).digest()
                next_level.append(parent)

            tree.append(next_level)
            current_level = next_level

        return tree

    def get_root(self) -> bytes:
        """Get Merkle root"""
        return self.root

    def get_proof(self, index: int) -> List[Tuple[bytes, str]]:
        """
        Get Merkle proof for update at index.

        Returns list of (hash, position) where position is 'left' or 'right'
        """
        if index >= len(self.leaves):
            raise IndexError(f"Index {index} out of range")

        proof = []
        current_index = index

        for level in self.tree[:-1]:  # Exclude root level
            # Find sibling
            if current_index % 2 == 0:
                # Left node, sibling is right
                sibling_index = current_index + 1
                position = 'right'
            else:
                # Right node, sibling is left
                sibling_index = current_index - 1
                position = 'left'

            if sibling_index < len(level):
                proof.append((level[sibling_index], position))

            # Move to parent
            current_index //= 2

        return proof

    @staticmethod
    def verify_proof(leaf_hash: bytes, proof: List[Tuple[bytes, str]], root: bytes) -> bool:
        """
        Verify Merkle proof.

        Args:
            leaf_hash: Hash of the leaf to verify
            proof: List of (sibling_hash, position)
            root: Expected Merkle root

        Returns:
            True if proof is valid
        """
        current = leaf_hash

        for sibling, position in proof:
            if position == 'left':
                current = hashlib.sha256(sibling + current).digest()
            else:
                current = hashlib.sha256(current + sibling).digest()

        return current == root


# Example usage
if __name__ == "__main__":
    from decimal import Decimal
    from datetime import datetime

    # Create some test updates
    updates = [
        TrustUpdateLeaf(
            lct_id="lct:ai:test:001",
            org_id="org:test:001",
            talent_delta=Decimal('0.001'),
            training_delta=Decimal('0.002'),
            temperament_delta=Decimal('0.001'),
            veracity_delta=Decimal('0.0'),
            validity_delta=Decimal('0.0'),
            valuation_delta=Decimal('0.0'),
            timestamp=datetime.utcnow()
        )
        for i in range(10)
    ]

    # Build Merkle tree
    tree = TrustMerkleTree(updates)
    root = tree.get_root()

    print(f"Merkle root: {root.hex()[:16]}...")

    # Get proof for update 5
    proof = tree.get_proof(5)
    print(f"Proof length: {len(proof)} hashes")

    # Verify proof
    leaf_hash = updates[5].hash()
    valid = TrustMerkleTree.verify_proof(leaf_hash, proof, root)
    print(f"Proof valid: {valid}")
```

### Modified Trust Update Batcher

Add Merkle tree generation to flush:

```python
# In trust_update_batcher.py

from trust_merkle_tree import TrustMerkleTree, TrustUpdateLeaf

class TrustUpdateBatcher:
    # ... existing code ...

    def __init__(self, ..., blockchain_client=None):
        # ... existing init ...
        self.blockchain_client = blockchain_client
        self.merkle_roots = []  # Track all roots

    def flush(self):
        """
        Flush pending updates to database AND anchor to blockchain.
        """
        # Get pending updates
        with self.lock:
            if not self.pending:
                return

            updates_to_flush = self.pending.copy()
            self.pending.clear()

        # Build Merkle tree
        leaves = []
        for key, delta in updates_to_flush.items():
            leaf = TrustUpdateLeaf(
                lct_id=delta.lct_id,
                org_id=delta.org_id,
                talent_delta=delta.talent_delta,
                training_delta=delta.training_delta,
                temperament_delta=delta.temperament_delta,
                veracity_delta=delta.veracity_delta,
                validity_delta=delta.validity_delta,
                valuation_delta=delta.valuation_delta,
                timestamp=delta.last_update
            )
            leaves.append(leaf)

        merkle_tree = TrustMerkleTree(leaves)
        merkle_root = merkle_tree.get_root()

        # Database flush (existing code)
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()

            try:
                # BEGIN TRANSACTION

                # Store Merkle root in database
                cursor.execute("""
                    INSERT INTO trust_merkle_roots
                    (root_hash, batch_size, previous_root, created_at)
                    VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
                    RETURNING root_id
                """, (
                    merkle_root.hex(),
                    len(updates_to_flush),
                    self.merkle_roots[-1].hex() if self.merkle_roots else None
                ))

                root_id = cursor.fetchone()[0]

                # Store Merkle proofs for each update
                for i, (key, delta) in enumerate(updates_to_flush.items()):
                    proof = merkle_tree.get_proof(i)
                    proof_json = json.dumps([
                        {'hash': h.hex(), 'position': p}
                        for h, p in proof
                    ])

                    cursor.execute("""
                        INSERT INTO trust_update_proofs
                        (root_id, lct_id, org_id, merkle_proof, update_index)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (
                        root_id,
                        delta.lct_id,
                        delta.org_id,
                        proof_json,
                        i
                    ))

                # Update trust scores (existing flush logic)
                # ... existing code ...

                # COMMIT TRANSACTION
                conn.commit()

                # Anchor to blockchain (async, non-blocking)
                if self.blockchain_client:
                    self._anchor_to_blockchain(merkle_root, len(updates_to_flush))

                # Track root
                self.merkle_roots.append(merkle_root)

            except Exception as e:
                conn.rollback()
                # ... error handling ...

        finally:
            cursor.close()
            conn.close()

    def _anchor_to_blockchain(self, merkle_root: bytes, batch_size: int):
        """
        Anchor Merkle root to blockchain (async).

        Non-blocking - queues anchor request.
        """
        try:
            previous_root = self.merkle_roots[-2].hex() if len(self.merkle_roots) >= 2 else "0x0"

            self.blockchain_client.anchor_trust_batch(
                merkle_root=merkle_root.hex(),
                batch_size=batch_size,
                previous_root=previous_root,
                timestamp=datetime.utcnow().isoformat()
            )
        except Exception as e:
            print(f"Blockchain anchor error (non-fatal): {e}")
            # Log but don't fail flush
```

### Database Schema Addition

```sql
-- trust_merkle_roots table
CREATE TABLE trust_merkle_roots (
    root_id SERIAL PRIMARY KEY,
    root_hash VARCHAR(64) NOT NULL UNIQUE,  -- Merkle root (hex)
    batch_size INTEGER NOT NULL,            -- Number of updates
    previous_root VARCHAR(64),              -- Previous root (chain)
    blockchain_tx VARCHAR(66),              -- On-chain tx hash (when anchored)
    blockchain_confirmed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    anchored_at TIMESTAMP                   -- When anchored to chain
);

-- trust_update_proofs table
CREATE TABLE trust_update_proofs (
    proof_id SERIAL PRIMARY KEY,
    root_id INTEGER REFERENCES trust_merkle_roots(root_id),
    lct_id VARCHAR(255) NOT NULL,
    org_id VARCHAR(255) NOT NULL,
    merkle_proof JSONB NOT NULL,           -- Proof path (JSON)
    update_index INTEGER NOT NULL,          -- Index in batch
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_merkle_roots_hash ON trust_merkle_roots(root_hash);
CREATE INDEX idx_merkle_roots_created ON trust_merkle_roots(created_at DESC);
CREATE INDEX idx_update_proofs_lct ON trust_update_proofs(lct_id, org_id);
CREATE INDEX idx_update_proofs_root ON trust_update_proofs(root_id);

-- LCT birth certificates table
CREATE TABLE lct_birth_certificates (
    lct_id VARCHAR(255) PRIMARY KEY,
    public_key_hash VARCHAR(66) NOT NULL,
    hardware_binding_hash VARCHAR(66),
    birth_timestamp TIMESTAMP NOT NULL,
    blockchain_tx VARCHAR(66),              -- On-chain tx hash
    blockchain_confirmed BOOLEAN DEFAULT FALSE,
    signature TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Verification API

```python
# trust_verification.py

class TrustVerifier:
    """Verify trust database integrity against blockchain"""

    def __init__(self, db_config: dict, blockchain_client):
        self.db_config = db_config
        self.blockchain = blockchain_client

    def verify_update(self, lct_id: str, org_id: str, root_id: int) -> bool:
        """
        Verify a specific trust update against blockchain.

        Returns True if update is cryptographically proven.
        """
        conn = psycopg2.connect(**self.db_config)
        cursor = conn.cursor()

        try:
            # Get Merkle proof from database
            cursor.execute("""
                SELECT p.merkle_proof, r.root_hash, r.blockchain_tx
                FROM trust_update_proofs p
                JOIN trust_merkle_roots r ON p.root_id = r.root_id
                WHERE p.lct_id = %s AND p.org_id = %s AND p.root_id = %s
            """, (lct_id, org_id, root_id))

            row = cursor.fetchone()
            if not row:
                return False

            proof_json, root_hash, blockchain_tx = row

            # Get update leaf hash
            cursor.execute("""
                SELECT talent_delta, training_delta, temperament_delta,
                       veracity_delta, validity_delta, valuation_delta,
                       last_updated
                FROM reputation_scores
                WHERE lct_id = %s AND organization_id = %s
            """, (lct_id, org_id))

            update_row = cursor.fetchone()
            if not update_row:
                return False

            # Reconstruct leaf
            leaf = TrustUpdateLeaf(
                lct_id=lct_id,
                org_id=org_id,
                talent_delta=update_row[0],
                training_delta=update_row[1],
                temperament_delta=update_row[2],
                veracity_delta=update_row[3],
                validity_delta=update_row[4],
                valuation_delta=update_row[5],
                timestamp=update_row[6]
            )

            # Verify Merkle proof
            proof = [(bytes.fromhex(p['hash']), p['position'])
                     for p in json.loads(proof_json)]

            root_valid = TrustMerkleTree.verify_proof(
                leaf.hash(),
                proof,
                bytes.fromhex(root_hash)
            )

            if not root_valid:
                return False

            # Verify blockchain anchor (if confirmed)
            if blockchain_tx:
                chain_root = self.blockchain.get_merkle_root(blockchain_tx)
                if chain_root != root_hash:
                    return False

            return True

        finally:
            cursor.close()
            conn.close()

    def verify_database_state(self) -> dict:
        """
        Verify entire database state against blockchain.

        Returns:
            {
                'valid': bool,
                'total_roots': int,
                'verified_roots': int,
                'failed_roots': [],
                'unanchored_roots': int
            }
        """
        conn = psycopg2.connect(**self.db_config)
        cursor = conn.cursor()

        try:
            # Get all Merkle roots
            cursor.execute("""
                SELECT root_id, root_hash, blockchain_tx, blockchain_confirmed
                FROM trust_merkle_roots
                ORDER BY created_at ASC
            """)

            roots = cursor.fetchall()
            verified = 0
            failed = []
            unanchored = 0

            for root_id, root_hash, blockchain_tx, confirmed in roots:
                if not blockchain_tx:
                    unanchored += 1
                    continue

                # Verify against blockchain
                try:
                    chain_root = self.blockchain.get_merkle_root(blockchain_tx)
                    if chain_root == root_hash:
                        verified += 1
                    else:
                        failed.append({
                            'root_id': root_id,
                            'expected': root_hash,
                            'actual': chain_root
                        })
                except Exception as e:
                    failed.append({
                        'root_id': root_id,
                        'error': str(e)
                    })

            return {
                'valid': len(failed) == 0,
                'total_roots': len(roots),
                'verified_roots': verified,
                'failed_roots': failed,
                'unanchored_roots': unanchored
            }

        finally:
            cursor.close()
            conn.close()
```

## Attack Vector Mitigation

### Before Blockchain Anchoring
| Attack | Status |
|--------|--------|
| Database tampering | ⚠️ VULNERABLE |
| Batch replay | ⚠️ VULNERABLE |
| Sybil attacks | ⚠️ PARTIAL |
| Reputation washing | ⚠️ PARTIAL |
| History falsification | ⚠️ VULNERABLE |

### After Blockchain Anchoring
| Attack | Status |
|--------|--------|
| Database tampering | ✅ DETECTED - Merkle proof fails |
| Batch replay | ✅ PREVENTED - On-chain sequence |
| Sybil attacks | ✅ MITIGATED - Birth certs on-chain |
| Reputation washing | ✅ AUDITABLE - Full history chain |
| History falsification | ✅ IMPOSSIBLE - Exponentially harder with witnesses |

## Cost Analysis

**Per hour operation** (60 flushes):
- Trust batch anchors: 60 × 200 gas = 12,000 gas
- At $2000 ETH, 20 gwei gas: ~$0.0005/hour = **$0.36/month**

**Per entity** (one-time):
- Birth certificate: 500 gas = ~$0.02
- For 10,000 entities: **$200 one-time**

**Total operational cost**: < $1/month for typical usage

**Value**: Cryptographic unforgeability of entire trust system

## Implementation Priority

**Phase 1**: Merkle tree generation + database storage
- Modify TrustUpdateBatcher to build trees
- Add merkle_roots and update_proofs tables
- No blockchain dependency yet

**Phase 2**: Blockchain anchoring (async)
- Integrate with Web4 blockchain
- Anchor roots every 60s
- Non-blocking, queued anchoring

**Phase 3**: Verification API
- Trust verification endpoints
- Database audit tools
- Continuous integrity checking

**Phase 4**: LCT birth certificates
- On-chain identity anchoring
- Sybil resistance enforcement
- Hardware binding verification

## Key Insight

**Web4's "trust through witnessing" realized**:
- Database = working memory (fast, mutable)
- Merkle trees = compression (efficient proofs)
- Blockchain = witnesses (unforgeable history)

Same principle as LCTs for identity, now applied to trust evolution. An entity's trust score is real to the extent it's been witnessed and recorded on-chain.

**"Presence accumulation makes falsifying history exponentially harder"** - now applies to trust itself.

---

**Next Steps**:
1. Implement Merkle tree generation in TrustUpdateBatcher
2. Add database schema for roots and proofs
3. Create verification API
4. Integrate with Web4 blockchain client (when ready)
5. Update attack vectors document with mitigation status
