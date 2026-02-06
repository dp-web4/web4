"""
Game-Database Integration Bridge
Session #66: Connect Web4 game simulation to production PostgreSQL database

This module bridges the in-memory game simulation with the production
authorization database, allowing:
1. Game agents to have real LCT identities from database
2. ATP operations to be tracked in action_sequences
3. Reputation changes to update reputation_scores
4. Treasury events to trigger failure_attributions
5. Audit requests to create database records

Architecture:
- Game simulation generates events (treasury_spend, audit_request, etc.)
- Bridge translates events to database operations
- Database state influences game behavior (reputation gates, ATP limits)
- Microblocks store references to database transactions

Integration with Session #65:
- SAGE (lct:sage:legion:1763906585) can be a game agent
- Greedy treasurer scenario triggers ATP drain mitigation
- Audit requests create real database audit records
- Role revocations update agent_delegations status
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Dict, List, Optional, Any
import json
import hashlib

class GameDatabaseBridge:
    """Bridge between game simulation and production database"""

    def __init__(self, db_config: Dict[str, str]):
        """
        Initialize bridge with database connection

        Args:
            db_config: PostgreSQL connection parameters
                {
                    'dbname': 'web4_test',
                    'user': 'postgres',
                    'host': 'localhost'
                }
        """
        self.db_config = db_config
        self.conn = None
        self.org_id = "org:web4:game"  # Game simulation organization

    def connect(self):
        """Establish database connection"""
        self.conn = psycopg2.connect(**self.db_config, cursor_factory=RealDictCursor)
        # Ensure game organization exists
        self._ensure_game_organization()

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            self.conn = None

    def _ensure_game_organization(self):
        """Create game organization if it doesn't exist"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO organizations (organization_id, organization_name)
            VALUES (%s, 'Web4 Game Simulation')
            ON CONFLICT (organization_id) DO NOTHING
        """, (self.org_id,))
        self.conn.commit()
        cursor.close()

    def sync_agent_to_db(self, agent_lct: str, agent_data: Dict[str, Any]) -> bool:
        """
        Sync game agent to database

        Creates or updates:
        - lct_identities entry
        - reputation_scores entry

        Args:
            agent_lct: Agent's LCT identifier
            agent_data: Agent dictionary from game
                {
                    'name': str,
                    'trust_axes': {'T3': {'talent', 'training', 'temperament'}},
                    'resources': {'ATP': float},
                    'capabilities': {...},
                    'memberships': [...],
                    'roles': [...]
                }

        Returns:
            True if sync successful
        """
        cursor = self.conn.cursor()

        try:
            # Create LCT identity if doesn't exist
            cursor.execute("""
                INSERT INTO lct_identities (
                    lct_id, entity_type, birth_certificate_hash, public_key
                ) VALUES (%s, 'ai', %s, %s)
                ON CONFLICT (lct_id) DO NOTHING
            """, (
                agent_lct,
                hashlib.sha256(f"{agent_lct}:game".encode()).hexdigest(),
                f"game_pubkey:{agent_lct}"
            ))

            # Get T3 scores from agent data
            t3 = agent_data.get('trust_axes', {}).get('T3', {})
            talent = float(t3.get('talent', 0.5))
            training = float(t3.get('training', 0.5))
            temperament = float(t3.get('temperament', 0.5))

            # Create or update reputation
            cursor.execute("""
                INSERT INTO reputation_scores (
                    lct_id, organization_id,
                    talent_score, training_score, temperament_score
                ) VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (lct_id, organization_id) DO UPDATE SET
                    talent_score = EXCLUDED.talent_score,
                    training_score = EXCLUDED.training_score,
                    temperament_score = EXCLUDED.temperament_score,
                    last_updated = CURRENT_TIMESTAMP
            """, (agent_lct, self.org_id, talent, training, temperament))

            self.conn.commit()
            cursor.close()
            return True

        except Exception as e:
            print(f"Error syncing agent {agent_lct}: {e}")
            self.conn.rollback()
            cursor.close()
            return False

    def record_treasury_spend(self, event: Dict[str, Any]) -> Optional[str]:
        """
        Record treasury spend event in database

        Creates:
        - failure_attribution if suspicious
        - trust_history entry

        Args:
            event: Treasury spend event from game
                {
                    'type': 'treasury_spend',
                    'society_lct': str,
                    'treasury_lct': str,
                    'initiator_lct': str,
                    'amount': float,
                    'reason': str,
                    'world_tick': int
                }

        Returns:
            attribution_id if failure attributed, None otherwise
        """
        cursor = self.conn.cursor()

        try:
            # Check if this looks suspicious
            is_suspicious = 'suspicious' in event.get('reason', '').lower()

            if is_suspicious:
                # Record failure attribution
                evidence = {
                    'treasury_event': event,
                    'pattern': 'repeated_self_allocation',
                    'amount': event['amount']
                }
                evidence_hash = hashlib.sha256(
                    json.dumps(evidence, sort_keys=True).encode()
                ).hexdigest()

                # Use the record_failure_attribution function which automatically
                # applies penalties for high-confidence sabotage
                cursor.execute("""
                    SELECT record_failure_attribution(
                        NULL,  -- sequence_id (NULL for game events)
                        %s,    -- iteration_number (world_tick)
                        'sabotage',
                        %s,    -- attributed_to_lct
                        %s,    -- evidence_hash
                        %s     -- confidence_score
                    ) as result
                """, (
                    event['world_tick'],
                    event['initiator_lct'],
                    evidence_hash,
                    0.85  # High confidence for blatant self-allocation
                ))

                result = cursor.fetchone()
                if result and result['result']:
                    result_data = result['result']
                    attribution_id = result_data.get('attribution_id')
                    penalty_applied = result_data.get('penalty_applied', False)
                else:
                    attribution_id = None

                self.conn.commit()
                cursor.close()
                return attribution_id

            cursor.close()
            return None

        except Exception as e:
            print(f"Error recording treasury spend: {e}")
            self.conn.rollback()
            cursor.close()
            return None

    def record_audit_request(self, event: Dict[str, Any]) -> bool:
        """
        Record audit request in database

        Could create:
        - audit_requests table entry (future)
        - trust_history entry for auditor

        Args:
            event: Audit request event from game
                {
                    'type': 'audit_request',
                    'auditor_lct': str,
                    'target_lct': str,
                    'scope': {...},
                    'reason': str,
                    'atp_allocation': float,
                    'world_tick': int
                }

        Returns:
            True if recorded successfully
        """
        cursor = self.conn.cursor()

        try:
            # Record in trust history (auditor performed audit)
            cursor.execute("""
                INSERT INTO trust_history (
                    lct_id, organization_id, t3_delta,
                    event_type, event_description
                ) VALUES (
                    %s, %s, %s, 'audit_performed', %s
                )
            """, (
                event['auditor_lct'],
                self.org_id,
                0.02,  # Small reputation boost for performing audit
                f"Audited {event['target_lct']}: {event['reason']}"
            ))

            self.conn.commit()
            cursor.close()
            return True

        except Exception as e:
            print(f"Error recording audit request: {e}")
            self.conn.rollback()
            cursor.close()
            return False

    def record_role_revocation(self, event: Dict[str, Any]) -> bool:
        """
        Record role revocation in database

        Updates:
        - agent_delegations status (if exists)
        - trust_history

        Args:
            event: Role revocation event from game
                {
                    'type': 'role_revocation',
                    'society_lct': str,
                    'role_lct': str,
                    'subject_lct': str,
                    'reason': str,
                    'world_tick': int
                }

        Returns:
            True if recorded successfully
        """
        cursor = self.conn.cursor()

        try:
            # Update any matching delegations to revoked status
            cursor.execute("""
                UPDATE agent_delegations
                SET status = 'revoked'
                WHERE delegatee_lct = %s
                  AND role_lct = %s
                  AND status = 'active'
            """, (event['subject_lct'], event['role_lct']))

            # Record in trust history (role revoked)
            cursor.execute("""
                INSERT INTO trust_history (
                    lct_id, organization_id, t3_delta,
                    event_type, event_description
                ) VALUES (
                    %s, %s, %s, 'role_revoked', %s
                )
            """, (
                event['subject_lct'],
                self.org_id,
                -0.10,  # Significant penalty for role revocation
                f"Role revoked: {event['reason']}"
                ))

            self.conn.commit()
            cursor.close()
            return True

        except Exception as e:
            print(f"Error recording role revocation: {e}")
            self.conn.rollback()
            cursor.close()
            return False

    def get_agent_reputation(self, agent_lct: str) -> Optional[Dict[str, float]]:
        """
        Get agent's current reputation from database

        Args:
            agent_lct: Agent's LCT identifier

        Returns:
            {
                'talent': float,
                'training': float,
                'temperament': float,
                't3_composite': float
            } or None if not found
        """
        cursor = self.conn.cursor()

        cursor.execute("""
            SELECT talent_score, training_score, temperament_score
            FROM reputation_scores
            WHERE lct_id = %s AND organization_id = %s
        """, (agent_lct, self.org_id))

        result = cursor.fetchone()
        cursor.close()

        if result:
            t3 = (float(result['talent_score']) + float(result['training_score']) +
                  float(result['temperament_score'])) / 3.0
            return {
                'talent': float(result['talent_score']),
                'training': float(result['training_score']),
                'temperament': float(result['temperament_score']),
                't3_composite': t3
            }
        return None

    def process_game_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a game event and sync to database

        Routes event to appropriate handler based on type.

        Args:
            event: Game event dictionary

        Returns:
            Processing result with status and any IDs created
        """
        event_type = event.get('type')

        handlers = {
            'treasury_spend': self.record_treasury_spend,
            'audit_request': self.record_audit_request,
            'role_revocation': self.record_role_revocation,
        }

        handler = handlers.get(event_type)
        if handler:
            result = handler(event)
            return {
                'event_type': event_type,
                'processed': result is not None,
                'result': result
            }

        return {
            'event_type': event_type,
            'processed': False,
            'reason': 'no_handler'
        }


def create_bridge(db_config: Optional[Dict[str, str]] = None) -> GameDatabaseBridge:
    """
    Create and connect a game-database bridge

    Args:
        db_config: Database configuration, defaults to web4_test

    Returns:
        Connected GameDatabaseBridge instance
    """
    if db_config is None:
        db_config = {
            'dbname': 'web4_test',
            'user': 'postgres',
            'host': 'localhost'
        }

    bridge = GameDatabaseBridge(db_config)
    bridge.connect()
    return bridge


# Example usage
if __name__ == "__main__":
    # Create bridge
    bridge = create_bridge()

    # Example: Sync a game agent
    agent_data = {
        'name': 'Alice',
        'trust_axes': {
            'T3': {
                'talent': 0.8,
                'training': 0.75,
                'temperament': 0.9
            }
        },
        'resources': {'ATP': 100.0},
        'roles': ['role:web4:auditor']
    }

    success = bridge.sync_agent_to_db('lct:web4:agent:alice', agent_data)
    print(f"Agent sync: {'✅' if success else '❌'}")

    # Get reputation back
    rep = bridge.get_agent_reputation('lct:web4:agent:alice')
    if rep:
        print(f"Agent reputation: T3={rep['t3_composite']:.2f}")

    bridge.close()
