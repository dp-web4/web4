"""
LCT Binding Chain Validation

Track BM: Validates hierarchical LCT binding as described in Web4 architecture.

Key concepts from Web4:
1. **Binding**: Permanent identity attachment (hardware to LCT)
2. **Witnessing**: Each level witnesses the level below, creating unforgeable presence chain
3. **Hierarchy**: API-Bridge → App → Pack Controller → Battery Module (example)

This module provides:
- Binding chain creation and validation
- Witness relationship tracking
- Chain integrity verification
- Presence proof accumulation

A binding chain is valid if:
- Each node has a valid LCT
- Each node witnesses the node below it
- Parent nodes have higher trust than children
- No circular dependencies exist
"""

import hashlib
import json
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Set, Tuple
from pathlib import Path
from enum import Enum


class BindingType(Enum):
    """Types of entity binding."""
    HARDWARE = "hardware"      # Physical device binding
    SOFTWARE = "software"      # Software-only binding
    DERIVED = "derived"        # Derived from parent binding
    WITNESSED = "witnessed"    # Established through witnessing


@dataclass
class LCTNode:
    """
    A node in the LCT binding chain.

    Represents an entity with an LCT that participates in the hierarchy.
    """
    lct_id: str
    entity_type: str          # "hardware", "software", "team", "federation"
    binding_type: BindingType
    parent_lct: Optional[str] = None  # Parent in binding chain
    trust_level: float = 0.5
    created_at: str = ""
    witnessed_by: List[str] = field(default_factory=list)  # LCTs that have witnessed this
    witnesses_for: List[str] = field(default_factory=list)  # LCTs this witnesses
    metadata: Dict = field(default_factory=dict)

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()


@dataclass
class WitnessRelationship:
    """
    A witnessing relationship between two LCT nodes.

    Witnessing creates a bidirectional MRH (Markov Relevancy Horizon) link.
    """
    witness_lct: str          # The witness
    subject_lct: str          # The witnessed
    established_at: str
    trust_contribution: float = 0.05  # How much trust this witnessing adds
    active: bool = True
    witness_count: int = 1    # How many times witnessed


class LCTBindingChain:
    """
    Manages hierarchical LCT binding chains.

    Track BM: Validates that binding chains follow Web4 principles:
    - Unidirectional witnessing (parent witnesses child)
    - Trust flows downward (children derive trust from parents)
    - Presence accumulates through witnessing
    """

    # Minimum trust for a node to witness others
    MIN_WITNESS_TRUST = 0.3

    # Trust contribution per witness
    TRUST_PER_WITNESS = 0.05

    # Maximum depth of binding chain
    MAX_CHAIN_DEPTH = 10

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize the binding chain manager.

        Args:
            db_path: Path to SQLite database (None for in-memory)
        """
        self._in_memory = db_path is None
        if db_path:
            self.db_path = Path(db_path)
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            self._conn = None  # Will create new connections
        else:
            # For in-memory, we need a persistent connection
            self.db_path = ":memory:"
            self._conn = sqlite3.connect(":memory:", check_same_thread=False)

        self._ensure_tables()

    def _get_conn(self):
        """Get a database connection."""
        if self._in_memory:
            return self._conn
        return sqlite3.connect(self.db_path)

    def _ensure_tables(self):
        """Create database tables."""
        conn = self._get_conn()
        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS lct_nodes (
                    lct_id TEXT PRIMARY KEY,
                    entity_type TEXT NOT NULL,
                    binding_type TEXT NOT NULL,
                    parent_lct TEXT,
                    trust_level REAL DEFAULT 0.5,
                    created_at TEXT NOT NULL,
                    metadata TEXT DEFAULT '{}'
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS witness_relationships (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    witness_lct TEXT NOT NULL,
                    subject_lct TEXT NOT NULL,
                    established_at TEXT NOT NULL,
                    trust_contribution REAL DEFAULT 0.05,
                    active INTEGER DEFAULT 1,
                    witness_count INTEGER DEFAULT 1,
                    UNIQUE(witness_lct, subject_lct)
                )
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_parent_lct
                ON lct_nodes(parent_lct)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_witness_relationships
                ON witness_relationships(subject_lct)
            """)
            conn.commit()
        finally:
            if not self._in_memory:
                conn.close()

    def create_root_node(
        self,
        lct_id: str,
        entity_type: str,
        binding_type: BindingType = BindingType.HARDWARE,
        initial_trust: float = 0.8,
        metadata: Dict = None,
    ) -> LCTNode:
        """
        Create a root node in the binding chain.

        Root nodes have no parent and typically represent hardware-bound identities.

        Args:
            lct_id: Unique LCT identifier
            entity_type: Type of entity (hardware, software, etc.)
            binding_type: How this LCT is bound
            initial_trust: Initial trust level
            metadata: Additional metadata

        Returns:
            LCTNode for the root
        """
        now = datetime.now(timezone.utc).isoformat()

        node = LCTNode(
            lct_id=lct_id,
            entity_type=entity_type,
            binding_type=binding_type,
            parent_lct=None,
            trust_level=initial_trust,
            created_at=now,
            metadata=metadata or {},
        )

        conn = self._get_conn()
        try:
            conn.execute("""
                INSERT INTO lct_nodes
                (lct_id, entity_type, binding_type, parent_lct, trust_level, created_at, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                node.lct_id,
                node.entity_type,
                node.binding_type.value,
                node.parent_lct,
                node.trust_level,
                node.created_at,
                json.dumps(node.metadata),
            ))
            conn.commit()
        finally:
            if not self._in_memory:
                conn.close()

        return node

    def bind_child(
        self,
        parent_lct: str,
        child_lct: str,
        entity_type: str,
        binding_type: BindingType = BindingType.DERIVED,
        metadata: Dict = None,
    ) -> LCTNode:
        """
        Bind a child node to a parent in the chain.

        The child's trust is derived from the parent's trust (slightly lower).
        The parent automatically witnesses the child.

        Args:
            parent_lct: LCT of the parent node
            child_lct: LCT of the new child node
            entity_type: Type of child entity
            binding_type: How the child is bound
            metadata: Additional metadata

        Returns:
            LCTNode for the child

        Raises:
            ValueError: If parent doesn't exist or chain would be too deep
        """
        parent = self.get_node(parent_lct)
        if not parent:
            raise ValueError(f"Parent node not found: {parent_lct}")

        # Check chain depth
        depth = self.get_chain_depth(parent_lct)
        if depth >= self.MAX_CHAIN_DEPTH:
            raise ValueError(f"Maximum chain depth ({self.MAX_CHAIN_DEPTH}) exceeded")

        # Child trust is derived from parent (slightly lower)
        child_trust = max(0.1, parent.trust_level - 0.1)

        now = datetime.now(timezone.utc).isoformat()

        child = LCTNode(
            lct_id=child_lct,
            entity_type=entity_type,
            binding_type=binding_type,
            parent_lct=parent_lct,
            trust_level=child_trust,
            created_at=now,
            metadata=metadata or {},
        )

        conn = self._get_conn()
        try:
            conn.execute("""
                INSERT INTO lct_nodes
                (lct_id, entity_type, binding_type, parent_lct, trust_level, created_at, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                child.lct_id,
                child.entity_type,
                child.binding_type.value,
                child.parent_lct,
                child.trust_level,
                child.created_at,
                json.dumps(child.metadata),
            ))
            conn.commit()
        finally:
            if not self._in_memory:
                conn.close()

        # Parent automatically witnesses child
        self.witness(parent_lct, child_lct)

        return child

    def get_node(self, lct_id: str) -> Optional[LCTNode]:
        """Get an LCT node by ID."""
        conn = self._get_conn()
        try:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM lct_nodes WHERE lct_id = ?",
                (lct_id,)
            ).fetchone()

            if not row:
                return None

            return LCTNode(
                lct_id=row["lct_id"],
                entity_type=row["entity_type"],
                binding_type=BindingType(row["binding_type"]),
                parent_lct=row["parent_lct"],
                trust_level=row["trust_level"],
                created_at=row["created_at"],
                metadata=json.loads(row["metadata"]) if row["metadata"] else {},
            )
        finally:
            if not self._in_memory:
                conn.close()

    def witness(
        self,
        witness_lct: str,
        subject_lct: str,
    ) -> WitnessRelationship:
        """
        Record a witnessing event.

        The witness observes the subject, contributing to its presence.

        Args:
            witness_lct: LCT of the witness
            subject_lct: LCT of the subject being witnessed

        Returns:
            WitnessRelationship record
        """
        witness = self.get_node(witness_lct)
        if not witness:
            raise ValueError(f"Witness node not found: {witness_lct}")

        if witness.trust_level < self.MIN_WITNESS_TRUST:
            raise ValueError(f"Witness trust too low: {witness.trust_level} < {self.MIN_WITNESS_TRUST}")

        now = datetime.now(timezone.utc).isoformat()

        conn = self._get_conn()
        try:
            # Try to update existing or insert new
            conn.execute("""
                INSERT INTO witness_relationships
                (witness_lct, subject_lct, established_at, trust_contribution, witness_count)
                VALUES (?, ?, ?, ?, 1)
                ON CONFLICT(witness_lct, subject_lct) DO UPDATE SET
                    witness_count = witness_count + 1
            """, (witness_lct, subject_lct, now, self.TRUST_PER_WITNESS))

            # Update subject's trust based on witnessing
            conn.execute("""
                UPDATE lct_nodes
                SET trust_level = MIN(1.0, trust_level + ?)
                WHERE lct_id = ?
            """, (self.TRUST_PER_WITNESS, subject_lct))
            conn.commit()
        finally:
            if not self._in_memory:
                conn.close()

        return WitnessRelationship(
            witness_lct=witness_lct,
            subject_lct=subject_lct,
            established_at=now,
            trust_contribution=self.TRUST_PER_WITNESS,
        )

    def get_chain_depth(self, lct_id: str) -> int:
        """Get the depth of a node in the binding chain."""
        depth = 0
        current = self.get_node(lct_id)

        while current and current.parent_lct and depth < self.MAX_CHAIN_DEPTH + 1:
            depth += 1
            current = self.get_node(current.parent_lct)

        return depth

    def get_ancestors(self, lct_id: str) -> List[LCTNode]:
        """Get all ancestors of a node (from parent to root)."""
        ancestors = []
        current = self.get_node(lct_id)

        while current and current.parent_lct:
            parent = self.get_node(current.parent_lct)
            if parent:
                ancestors.append(parent)
            current = parent

        return ancestors

    def get_descendants(self, lct_id: str) -> List[LCTNode]:
        """Get all descendants of a node (children, grandchildren, etc.)."""
        descendants = []

        conn = self._get_conn()
        try:
            conn.row_factory = sqlite3.Row

            # BFS to find all descendants
            queue = [lct_id]
            visited = {lct_id}

            while queue:
                current = queue.pop(0)
                children = conn.execute(
                    "SELECT * FROM lct_nodes WHERE parent_lct = ?",
                    (current,)
                ).fetchall()

                for row in children:
                    if row["lct_id"] not in visited:
                        visited.add(row["lct_id"])
                        queue.append(row["lct_id"])
                        descendants.append(LCTNode(
                            lct_id=row["lct_id"],
                            entity_type=row["entity_type"],
                            binding_type=BindingType(row["binding_type"]),
                            parent_lct=row["parent_lct"],
                            trust_level=row["trust_level"],
                            created_at=row["created_at"],
                            metadata=json.loads(row["metadata"]) if row["metadata"] else {},
                        ))
        finally:
            if not self._in_memory:
                conn.close()

        return descendants

    def validate_chain(self, lct_id: str) -> Dict:
        """
        Validate the binding chain for an LCT.

        Track BM: Comprehensive chain validation.

        Checks:
        1. All ancestors exist
        2. Trust decreases down the chain
        3. Each level has witness relationship with child
        4. No circular dependencies

        Returns:
            Dict with validation results
        """
        node = self.get_node(lct_id)
        if not node:
            return {"valid": False, "error": "Node not found"}

        issues = []
        ancestors = []

        # Check ancestor chain
        current = node
        visited = {lct_id}

        while current.parent_lct:
            if current.parent_lct in visited:
                issues.append(f"Circular dependency: {current.parent_lct}")
                break

            parent = self.get_node(current.parent_lct)
            if not parent:
                issues.append(f"Missing parent: {current.parent_lct}")
                break

            visited.add(current.parent_lct)
            ancestors.append(parent)

            # Check trust ordering (parent should have higher trust)
            if parent.trust_level < current.trust_level:
                issues.append(
                    f"Trust inversion: {parent.lct_id} ({parent.trust_level}) < {current.lct_id} ({current.trust_level})"
                )

            # Check witnessing relationship
            conn = self._get_conn()
            try:
                rel = conn.execute("""
                    SELECT * FROM witness_relationships
                    WHERE witness_lct = ? AND subject_lct = ?
                """, (parent.lct_id, current.lct_id)).fetchone()

                if not rel:
                    issues.append(f"Missing witness relationship: {parent.lct_id} -> {current.lct_id}")
            finally:
                if not self._in_memory:
                    conn.close()

            current = parent

        # Get witnesses for this node
        conn = self._get_conn()
        try:
            witnesses = conn.execute(
                "SELECT witness_lct, witness_count FROM witness_relationships WHERE subject_lct = ?",
                (lct_id,)
            ).fetchall()
        finally:
            if not self._in_memory:
                conn.close()

        return {
            "valid": len(issues) == 0,
            "lct_id": lct_id,
            "chain_depth": len(ancestors),
            "ancestors": [a.lct_id for a in ancestors],
            "root": ancestors[-1].lct_id if ancestors else lct_id,
            "trust_level": node.trust_level,
            "witness_count": len(witnesses),
            "witnesses": [w[0] for w in witnesses],
            "issues": issues,
        }

    def get_presence_proof(self, lct_id: str) -> Dict:
        """
        Generate a presence proof for an LCT.

        Presence is accumulated through witnessing. The more an entity
        is witnessed, the more "present" it becomes in the network.

        Returns:
            Dict with presence proof data
        """
        node = self.get_node(lct_id)
        if not node:
            return {"error": "Node not found"}

        # Get witness history
        conn = self._get_conn()
        try:
            conn.row_factory = sqlite3.Row
            witnesses = conn.execute("""
                SELECT witness_lct, witness_count, trust_contribution, established_at
                FROM witness_relationships
                WHERE subject_lct = ?
            """, (lct_id,)).fetchall()
        finally:
            if not self._in_memory:
                conn.close()

        total_witness_count = sum(w["witness_count"] for w in witnesses)
        accumulated_trust = sum(w["trust_contribution"] * w["witness_count"] for w in witnesses)

        # Get chain validation
        chain_validation = self.validate_chain(lct_id)

        return {
            "lct_id": lct_id,
            "entity_type": node.entity_type,
            "binding_type": node.binding_type.value,
            "trust_level": node.trust_level,
            "chain_valid": chain_validation["valid"],
            "chain_depth": chain_validation["chain_depth"],
            "root_lct": chain_validation["root"],
            "unique_witnesses": len(witnesses),
            "total_witness_events": total_witness_count,
            "accumulated_trust_contribution": accumulated_trust,
            "presence_score": min(1.0, 0.3 + (total_witness_count * 0.1)),  # Presence formula
            "witnesses": [
                {
                    "witness_lct": w["witness_lct"],
                    "count": w["witness_count"],
                    "contribution": w["trust_contribution"],
                }
                for w in witnesses
            ],
        }


# Self-test
if __name__ == "__main__":
    print("=" * 60)
    print("LCT Binding Chain - Self Test")
    print("=" * 60)

    import tempfile

    db_path = Path(tempfile.mkdtemp()) / "binding_chain_test.db"
    chain = LCTBindingChain(db_path=db_path)

    # Create hierarchical binding chain (modbatt-CAN example)
    print("\n1. Creating binding hierarchy:")

    # Root: API Bridge (hardware bound)
    root = chain.create_root_node(
        "lct:api-bridge:001",
        "hardware",
        BindingType.HARDWARE,
        initial_trust=0.9,
        metadata={"device": "api-bridge", "serial": "AB001"}
    )
    print(f"   Root: {root.lct_id} (trust={root.trust_level})")

    # Level 1: App
    app = chain.bind_child(
        root.lct_id,
        "lct:app:001",
        "software",
        BindingType.DERIVED,
        metadata={"app": "modbatt-controller"}
    )
    print(f"   └── App: {app.lct_id} (trust={app.trust_level})")

    # Level 2: Pack Controller
    pack = chain.bind_child(
        app.lct_id,
        "lct:pack:001",
        "hardware",
        BindingType.DERIVED,
        metadata={"pack": "lithium-48v"}
    )
    print(f"       └── Pack: {pack.lct_id} (trust={pack.trust_level})")

    # Level 3: Battery Modules
    for i in range(3):
        module = chain.bind_child(
            pack.lct_id,
            f"lct:module:{i:03d}",
            "hardware",
            BindingType.DERIVED,
            metadata={"module_id": i}
        )
        print(f"           └── Module: {module.lct_id} (trust={module.trust_level})")

    # Validate chain
    print("\n2. Chain Validation:")
    for module_id in ["lct:module:000", "lct:module:001", "lct:module:002"]:
        validation = chain.validate_chain(module_id)
        status = "VALID" if validation["valid"] else "INVALID"
        print(f"   {module_id}: {status} (depth={validation['chain_depth']})")

    # Presence proof
    print("\n3. Presence Proof:")
    proof = chain.get_presence_proof("lct:module:000")
    print(f"   LCT: {proof['lct_id']}")
    print(f"   Chain valid: {proof['chain_valid']}")
    print(f"   Chain depth: {proof['chain_depth']}")
    print(f"   Root: {proof['root_lct']}")
    print(f"   Presence score: {proof['presence_score']:.2f}")

    # Additional witnessing
    print("\n4. Additional Witnessing:")
    # Peer modules witness each other
    chain.witness("lct:module:000", "lct:module:001")
    chain.witness("lct:module:001", "lct:module:002")
    chain.witness("lct:module:002", "lct:module:000")

    proof_after = chain.get_presence_proof("lct:module:000")
    print(f"   Module 0 witnesses after peer witnessing: {proof_after['total_witness_events']}")
    print(f"   New presence score: {proof_after['presence_score']:.2f}")

    print("\n" + "=" * 60)
    print("Self-test complete.")
