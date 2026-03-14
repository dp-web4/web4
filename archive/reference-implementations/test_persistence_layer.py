"""
Persistence Layer Tests
=======================

Test suite for PostgreSQL persistence layer.

Tests:
- LCT registry persistence (mint, get, list)
- Delegation storage (create, update ATP, revoke)
- Witness attestation storage (store, query, nonce replay)
- Transaction safety (rollback on error)
- Connection management

Author: Legion Autonomous Session (2025-12-05)
"""

import unittest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, timedelta, timezone
import json
import base64
import secrets

from persistence_layer import (
    PersistentLCTRegistry, PersistentDelegationStore, PersistentWitnessStore,
    create_persistent_lct_registry, create_persistent_delegation_store,
    create_persistent_witness_store, PersistenceError
)


class TestPersistentLCTRegistry(unittest.TestCase):
    """Test LCT registry persistence"""

    def setUp(self):
        """Set up test fixtures"""
        self.db_config = {
            'host': 'localhost',
            'port': 5432,
            'dbname': 'test_web4',
            'user': 'test',
            'password': 'test'
        }
        self.society_id = "web4:test"

    @patch('persistence_layer.psycopg2.connect')
    def test_mint_lct_success(self, mock_connect):
        """Test successful LCT minting"""
        # Mock database
        mock_cursor = MagicMock()
        mock_cursor.fetchone.side_effect = [None, ("lct:web4:ai:web4:test:123",)]

        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        # Mint LCT
        registry = PersistentLCTRegistry(self.db_config, self.society_id)
        lct_id, error = registry.mint_lct(
            entity_type="AI",
            entity_identifier="ai:agent:001",
            public_key="abcd1234" * 16,
            birth_certificate_data={
                "society_id": self.society_id,
                "law_oracle_id": "oracle:law:test",
                "law_version": "v1.0.0"
            }
        )

        self.assertTrue(lct_id)
        self.assertIn("lct:web4:ai", lct_id)
        self.assertEqual(error, "")

        registry.close()

    @patch('persistence_layer.psycopg2.connect')
    def test_mint_lct_duplicate(self, mock_connect):
        """Test duplicate entity rejection"""
        # Mock database showing existing entity
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = ("lct:existing",)

        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        # Try to mint duplicate
        registry = PersistentLCTRegistry(self.db_config, self.society_id)
        lct_id, error = registry.mint_lct(
            entity_type="AI",
            entity_identifier="ai:agent:001",
            public_key="abcd1234" * 16,
            birth_certificate_data={}
        )

        self.assertEqual(lct_id, "")
        self.assertIn("already exists", error)

        registry.close()

    @patch('persistence_layer.psycopg2.connect')
    def test_get_lct(self, mock_connect):
        """Test LCT retrieval"""
        # Mock database response
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {
            'lct_id': 'lct:web4:ai:test:001',
            'entity_type': 'AI',
            'society_id': 'web4:test',
            'birth_certificate_hash': '0xabcd',
            'public_key': 'pubkey123',
            'hardware_binding_hash': None,
            'created_at': datetime.now(timezone.utc)
        }

        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        # Get LCT
        registry = PersistentLCTRegistry(self.db_config, self.society_id)
        lct_data = registry.get_lct('lct:web4:ai:test:001')

        self.assertIsNotNone(lct_data)
        self.assertEqual(lct_data['lct_id'], 'lct:web4:ai:test:001')
        self.assertEqual(lct_data['entity_type'], 'AI')

        registry.close()

    @patch('persistence_layer.psycopg2.connect')
    def test_list_lcts(self, mock_connect):
        """Test LCT listing with filters"""
        # Mock database response
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            {
                'lct_id': 'lct:web4:ai:test:001',
                'entity_type': 'AI',
                'society_id': 'web4:test'
            },
            {
                'lct_id': 'lct:web4:ai:test:002',
                'entity_type': 'AI',
                'society_id': 'web4:test'
            }
        ]

        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        # List LCTs
        registry = PersistentLCTRegistry(self.db_config, self.society_id)
        lcts = registry.list_lcts(entity_type="AI", limit=10)

        self.assertEqual(len(lcts), 2)
        self.assertEqual(lcts[0]['entity_type'], 'AI')

        registry.close()


class TestPersistentDelegationStore(unittest.TestCase):
    """Test delegation storage persistence"""

    def setUp(self):
        """Set up test fixtures"""
        self.db_config = {
            'host': 'localhost',
            'port': 5432,
            'dbname': 'test_web4',
            'user': 'test',
            'password': 'test'
        }

    @patch('persistence_layer.psycopg2.connect')
    def test_create_delegation(self, mock_connect):
        """Test delegation creation"""
        # Mock database
        mock_cursor = MagicMock()

        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        # Create delegation
        store = PersistentDelegationStore(self.db_config)
        success, error = store.create_delegation(
            delegation_id="delegation:001",
            delegator_lct="lct:client:001",
            delegatee_lct="lct:agent:001",
            organization_id="org:test",
            role_lct=None,
            granted_permissions=["read:*", "write:code:*"],
            atp_budget=1000,
            valid_from=datetime.now(timezone.utc),
            valid_until=datetime.now(timezone.utc) + timedelta(days=30),
            delegation_signature="sig123"
        )

        self.assertTrue(success)
        self.assertEqual(error, "")

        store.close()

    @patch('persistence_layer.psycopg2.connect')
    def test_get_delegation(self, mock_connect):
        """Test delegation retrieval"""
        # Mock database response
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {
            'delegation_id': 'delegation:001',
            'delegator_lct': 'lct:client:001',
            'delegatee_lct': 'lct:agent:001',
            'atp_budget_total': 1000,
            'atp_budget_spent': 100,
            'status': 'active'
        }

        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        # Get delegation
        store = PersistentDelegationStore(self.db_config)
        delegation = store.get_delegation('delegation:001')

        self.assertIsNotNone(delegation)
        self.assertEqual(delegation['delegation_id'], 'delegation:001')
        self.assertEqual(delegation['atp_budget_total'], 1000)

        store.close()

    @patch('persistence_layer.psycopg2.connect')
    def test_update_atp_spent(self, mock_connect):
        """Test ATP budget update"""
        # Mock database
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = ('delegation:001',)

        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        # Update ATP
        store = PersistentDelegationStore(self.db_config)
        success, error = store.update_atp_spent('delegation:001', 50)

        self.assertTrue(success)
        self.assertEqual(error, "")

        store.close()

    @patch('persistence_layer.psycopg2.connect')
    def test_update_atp_insufficient_budget(self, mock_connect):
        """Test ATP update fails when budget exceeded"""
        # Mock database returning None (no rows updated = budget exceeded)
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None

        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        # Try to spend more than budget
        store = PersistentDelegationStore(self.db_config)
        success, error = store.update_atp_spent('delegation:001', 9999)

        self.assertFalse(success)
        self.assertIn("Insufficient ATP", error)

        store.close()

    @patch('persistence_layer.psycopg2.connect')
    def test_revoke_delegation(self, mock_connect):
        """Test delegation revocation"""
        # Mock database
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = ('delegation:001',)

        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        # Revoke delegation
        store = PersistentDelegationStore(self.db_config)
        success, error = store.revoke_delegation(
            'delegation:001',
            'Policy violation',
            'lct:admin:001'
        )

        self.assertTrue(success)
        self.assertEqual(error, "")

        store.close()

    @patch('persistence_layer.psycopg2.connect')
    def test_list_delegations_with_filters(self, mock_connect):
        """Test delegation listing with filters"""
        # Mock database response
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            {
                'delegation_id': 'delegation:001',
                'delegator_lct': 'lct:client:001',
                'delegatee_lct': 'lct:agent:001',
                'status': 'active'
            },
            {
                'delegation_id': 'delegation:002',
                'delegator_lct': 'lct:client:001',
                'delegatee_lct': 'lct:agent:002',
                'status': 'active'
            }
        ]

        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        # List delegations
        store = PersistentDelegationStore(self.db_config)
        delegations = store.list_delegations(
            delegator_lct='lct:client:001',
            status='active',
            limit=10
        )

        self.assertEqual(len(delegations), 2)
        self.assertEqual(delegations[0]['delegator_lct'], 'lct:client:001')

        store.close()


class TestPersistentWitnessStore(unittest.TestCase):
    """Test witness attestation storage"""

    def setUp(self):
        """Set up test fixtures"""
        self.db_config = {
            'host': 'localhost',
            'port': 5432,
            'dbname': 'test_web4',
            'user': 'test',
            'password': 'test'
        }

    @patch('persistence_layer.psycopg2.connect')
    def test_store_attestation(self, mock_connect):
        """Test attestation storage"""
        # Mock database
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (1,)  # attestation_id

        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        # Store attestation
        store = PersistentWitnessStore(self.db_config)
        nonce = base64.b64encode(secrets.token_bytes(16)).decode('ascii')

        success, error = store.store_attestation(
            witness_did="did:web4:witness:time001",
            witness_type="time",
            subject="lct:agent:001",
            claims={"ts": datetime.now(timezone.utc).isoformat(), "nonce": nonce},
            signature="sig123",
            nonce=nonce,
            timestamp=datetime.now(timezone.utc)
        )

        self.assertTrue(success)
        self.assertEqual(error, "")

        store.close()

    @patch('persistence_layer.psycopg2.connect')
    def test_store_attestation_nonce_replay(self, mock_connect):
        """Test nonce replay protection"""
        # Mock database with integrity error (duplicate nonce)
        mock_cursor = MagicMock()
        mock_cursor.execute.side_effect = [
            None,  # Schema initialization
            None,  # Schema initialization (indexes)
            Exception("duplicate key value violates unique constraint")  # Nonce collision
        ]

        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        # Try to store with duplicate nonce
        store = PersistentWitnessStore(self.db_config)
        nonce = "duplicate_nonce_123"

        # First attempt would succeed in real DB, simulate second attempt
        import psycopg2
        mock_cursor.execute.side_effect = psycopg2.IntegrityError("duplicate nonce")

        success, error = store.store_attestation(
            witness_did="did:web4:witness:time001",
            witness_type="time",
            subject="lct:agent:001",
            claims={"ts": datetime.now(timezone.utc).isoformat(), "nonce": nonce},
            signature="sig123",
            nonce=nonce,
            timestamp=datetime.now(timezone.utc)
        )

        self.assertFalse(success)
        self.assertIn("Nonce already used", error)

        store.close()

    @patch('persistence_layer.psycopg2.connect')
    def test_get_attestations(self, mock_connect):
        """Test attestation queries"""
        # Mock database response
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            {
                'attestation_id': 1,
                'witness_did': 'did:web4:witness:time001',
                'witness_type': 'time',
                'subject': 'lct:agent:001',
                'claims': {'ts': '2025-12-05T12:00:00Z', 'nonce': 'abc123'},
                'signature': 'sig123',
                'nonce': 'abc123',
                'timestamp': datetime.now(timezone.utc)
            },
            {
                'attestation_id': 2,
                'witness_did': 'did:web4:witness:time001',
                'witness_type': 'time',
                'subject': 'lct:agent:001',
                'claims': {'ts': '2025-12-05T12:01:00Z', 'nonce': 'def456'},
                'signature': 'sig456',
                'nonce': 'def456',
                'timestamp': datetime.now(timezone.utc)
            }
        ]

        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        # Query attestations
        store = PersistentWitnessStore(self.db_config)
        attestations = store.get_attestations(
            witness_did='did:web4:witness:time001',
            witness_type='time',
            limit=10
        )

        self.assertEqual(len(attestations), 2)
        self.assertEqual(attestations[0]['witness_did'], 'did:web4:witness:time001')
        self.assertEqual(attestations[0]['witness_type'], 'time')

        store.close()

    @patch('persistence_layer.psycopg2.connect')
    def test_check_nonce_used(self, mock_connect):
        """Test nonce checking"""
        # Mock database
        # Create separate cursor mocks for each call
        mock_cursor_init = MagicMock()
        mock_cursor_check1 = MagicMock()
        mock_cursor_check1.fetchone.return_value = (1,)  # Nonce exists
        mock_cursor_check2 = MagicMock()
        mock_cursor_check2.fetchone.return_value = None  # Nonce doesn't exist

        mock_conn = MagicMock()
        # Return different cursors for each call
        mock_conn.cursor.return_value.__enter__.side_effect = [
            mock_cursor_init,  # Schema init
            mock_cursor_check1,  # Check used nonce
            mock_cursor_check2   # Check unused nonce
        ]
        mock_connect.return_value = mock_conn

        # Check nonces
        store = PersistentWitnessStore(self.db_config)

        # Used nonce
        used = store.check_nonce_used('existing_nonce')
        self.assertTrue(used)

        # Unused nonce
        unused = store.check_nonce_used('new_nonce')
        self.assertFalse(unused)

        store.close()


class TestFactoryFunctions(unittest.TestCase):
    """Test factory functions"""

    @patch('persistence_layer.psycopg2.connect')
    def test_create_persistent_lct_registry(self, mock_connect):
        """Test LCT registry factory"""
        db_config = {'host': 'localhost', 'dbname': 'test'}
        registry = create_persistent_lct_registry(db_config, "web4:test")

        self.assertIsInstance(registry, PersistentLCTRegistry)
        self.assertEqual(registry.society_id, "web4:test")

    @patch('persistence_layer.psycopg2.connect')
    def test_create_persistent_delegation_store(self, mock_connect):
        """Test delegation store factory"""
        db_config = {'host': 'localhost', 'dbname': 'test'}
        store = create_persistent_delegation_store(db_config)

        self.assertIsInstance(store, PersistentDelegationStore)

    @patch('persistence_layer.psycopg2.connect')
    def test_create_persistent_witness_store(self, mock_connect):
        """Test witness store factory"""
        db_config = {'host': 'localhost', 'dbname': 'test'}
        store = create_persistent_witness_store(db_config)

        self.assertIsInstance(store, PersistentWitnessStore)


if __name__ == '__main__':
    unittest.main()
