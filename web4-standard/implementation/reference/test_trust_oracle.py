"""
Trust Oracle Tests
==================

Test suite for PostgreSQL-backed trust query service.

Tests:
- Trust score queries
- T3/V3 tensor retrieval
- Temporal decay application
- Trust relationship queries
- Caching behavior
- Authorization interface

Author: Legion Autonomous Session (2025-12-05)
"""

import unittest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, timedelta, timezone
import time

from trust_oracle import TrustOracle, TrustScore, create_trust_oracle


class TestTrustScore(unittest.TestCase):
    """Test TrustScore dataclass"""

    def test_composite_score_with_v3(self):
        """Test composite score calculation with V3"""
        score = TrustScore(
            lct_id="test",
            organization_id="org",
            talent=0.8,
            training=0.7,
            temperament=0.9,
            t3_score=0.8,
            veracity=0.85,
            validity=0.75,
            valuation=0.65,
            v3_score=0.75
        )

        # Default: 60% T3, 40% V3
        composite = score.composite_score()
        expected = (0.6 * 0.8) + (0.4 * 0.75)
        self.assertAlmostEqual(composite, expected, places=3)

    def test_composite_score_without_v3(self):
        """Test composite score falls back to T3"""
        score = TrustScore(
            lct_id="test",
            organization_id="org",
            talent=0.8,
            training=0.7,
            temperament=0.9,
            t3_score=0.8
        )

        composite = score.composite_score()
        self.assertAlmostEqual(composite, 0.8, places=3)

    def test_is_stale(self):
        """Test staleness detection"""
        # Fresh score
        fresh = TrustScore(
            lct_id="test",
            organization_id="org",
            talent=0.8,
            training=0.7,
            temperament=0.9,
            t3_score=0.8,
            last_updated=datetime.now(timezone.utc)
        )
        self.assertFalse(fresh.is_stale(threshold_days=90))

        # Stale score
        old = TrustScore(
            lct_id="test",
            organization_id="org",
            talent=0.8,
            training=0.7,
            temperament=0.9,
            t3_score=0.8,
            last_updated=datetime.now(timezone.utc) - timedelta(days=100)
        )
        self.assertTrue(old.is_stale(threshold_days=90))

        # No timestamp
        no_timestamp = TrustScore(
            lct_id="test",
            organization_id="org",
            talent=0.8,
            training=0.7,
            temperament=0.9,
            t3_score=0.8
        )
        self.assertTrue(no_timestamp.is_stale())


class TestTrustOracle(unittest.TestCase):
    """Test TrustOracle with mocked database"""

    def setUp(self):
        """Set up test fixtures"""
        self.db_config = {
            'host': 'localhost',
            'port': 5432,
            'dbname': 'test_web4',
            'user': 'test',
            'password': 'test'
        }

    @patch('trust_oracle.psycopg2.connect')
    def test_get_trust_score_found(self, mock_connect):
        """Test successful trust score query"""
        # Mock database response
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {
            'lct_id': 'lct:ai:001',
            'organization_id': 'org:test',
            'talent_score': 0.8,
            'training_score': 0.7,
            'temperament_score': 0.9,
            't3_score': 0.8,
            'veracity_score': 0.85,
            'validity_score': 0.75,
            'valuation_score': 0.65,
            'v3_score': 0.75,
            'reputation_level': 'trusted',
            'total_actions': 100,
            'successful_actions': 85,
            'total_transactions': 50,
            'successful_transactions': 45,
            't3_last_updated': datetime.now(timezone.utc),
            'v3_last_updated': datetime.now(timezone.utc)
        }

        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        # Query trust
        oracle = TrustOracle(self.db_config, enable_decay=False)
        score = oracle.get_trust_score('lct:ai:001', 'org:test')

        self.assertEqual(score.lct_id, 'lct:ai:001')
        self.assertEqual(score.organization_id, 'org:test')
        self.assertAlmostEqual(score.t3_score, 0.8, places=3)
        self.assertAlmostEqual(score.v3_score, 0.75, places=3)
        self.assertEqual(score.reputation_level, 'trusted')
        self.assertEqual(score.total_actions, 100)

        oracle.close()

    @patch('trust_oracle.psycopg2.connect')
    def test_get_trust_score_not_found(self, mock_connect):
        """Test trust query for non-existent entity"""
        # Mock database response (no result)
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None

        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        # Query trust
        oracle = TrustOracle(self.db_config)
        score = oracle.get_trust_score('lct:unknown', 'org:test')

        # Should return default novice scores
        self.assertEqual(score.lct_id, 'lct:unknown')
        self.assertAlmostEqual(score.t3_score, 0.5, places=3)
        self.assertEqual(score.reputation_level, 'novice')

        oracle.close()

    @patch('trust_oracle.psycopg2.connect')
    def test_caching(self, mock_connect):
        """Test trust score caching"""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {
            'lct_id': 'lct:ai:001',
            'organization_id': 'org:test',
            'talent_score': 0.8,
            'training_score': 0.7,
            'temperament_score': 0.9,
            't3_score': 0.8,
            'veracity_score': None,
            'validity_score': None,
            'valuation_score': None,
            'v3_score': None,
            'reputation_level': 'trusted',
            'total_actions': 100,
            'successful_actions': 85,
            'total_transactions': 0,
            'successful_transactions': 0,
            't3_last_updated': datetime.now(timezone.utc),
            'v3_last_updated': None
        }

        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        oracle = TrustOracle(self.db_config, cache_ttl_seconds=60)

        # First query - should hit database
        score1 = oracle.get_trust_score('lct:ai:001', 'org:test')
        self.assertEqual(mock_cursor.execute.call_count, 1)

        # Second query - should hit cache
        score2 = oracle.get_trust_score('lct:ai:001', 'org:test')
        self.assertEqual(mock_cursor.execute.call_count, 1)  # Still 1

        # Same score
        self.assertEqual(score1.t3_score, score2.t3_score)

        oracle.close()

    @patch('trust_oracle.psycopg2.connect')
    def test_cache_bypass(self, mock_connect):
        """Test cache bypass option"""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {
            'lct_id': 'lct:ai:001',
            'organization_id': 'org:test',
            'talent_score': 0.8,
            'training_score': 0.7,
            'temperament_score': 0.9,
            't3_score': 0.8,
            'veracity_score': None,
            'validity_score': None,
            'valuation_score': None,
            'v3_score': None,
            'reputation_level': 'trusted',
            'total_actions': 100,
            'successful_actions': 85,
            'total_transactions': 0,
            'successful_transactions': 0,
            't3_last_updated': datetime.now(timezone.utc),
            'v3_last_updated': None
        }

        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        oracle = TrustOracle(self.db_config, cache_ttl_seconds=60)

        # First query
        oracle.get_trust_score('lct:ai:001', 'org:test', use_cache=True)
        self.assertEqual(mock_cursor.execute.call_count, 1)

        # Second query with cache bypass
        oracle.get_trust_score('lct:ai:001', 'org:test', use_cache=False)
        self.assertEqual(mock_cursor.execute.call_count, 2)

        oracle.close()

    def test_temporal_decay(self):
        """Test temporal decay application"""
        oracle = TrustOracle(self.db_config, enable_decay=True)

        # Create score 60 days old
        old_score = TrustScore(
            lct_id='test',
            organization_id='org',
            talent=0.8,  # Doesn't decay
            training=0.9,  # Decays: -0.001 per month
            temperament=0.5,  # Recovers: +0.01 per month
            t3_score=0.73,
            last_updated=datetime.now(timezone.utc) - timedelta(days=60)
        )

        decayed = oracle._apply_decay(old_score)

        # Training should decay: 0.9 - (0.001 * 2 months) = 0.898
        self.assertLess(decayed.training, 0.9)
        self.assertGreater(decayed.training, 0.89)

        # Temperament should recover: 0.5 + (0.01 * 2 months) = 0.52
        self.assertGreater(decayed.temperament, 0.5)
        self.assertLess(decayed.temperament, 0.53)

        # Talent unchanged
        self.assertAlmostEqual(decayed.talent, 0.8, places=3)

    @patch('trust_oracle.psycopg2.connect')
    def test_get_trust_relationship(self, mock_connect):
        """Test trust relationship query"""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {
            'trust_score': 0.85,
            'confidence': 0.9,
            'interaction_count': 50,
            'successful_interactions': 45,
            'failed_interactions': 5
        }

        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        oracle = TrustOracle(self.db_config)
        trust = oracle.get_trust_relationship(
            source_lct='lct:ai:001',
            target_lct='lct:ai:002',
            organization_id='org:test',
            relationship_type='collaborated'
        )

        self.assertAlmostEqual(trust, 0.85, places=3)
        oracle.close()

    @patch('trust_oracle.psycopg2.connect')
    def test_query_trust_for_authorization(self, mock_connect):
        """Test authorization interface"""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {
            'lct_id': 'lct:ai:001',
            'organization_id': 'org:test',
            'talent_score': 0.8,
            'training_score': 0.7,
            'temperament_score': 0.9,
            't3_score': 0.8,
            'veracity_score': 0.85,
            'validity_score': 0.75,
            'valuation_score': 0.65,
            'v3_score': 0.75,
            'reputation_level': 'trusted',
            'total_actions': 100,
            'successful_actions': 85,
            'total_transactions': 50,
            'successful_transactions': 45,
            't3_last_updated': datetime.now(timezone.utc),
            'v3_last_updated': datetime.now(timezone.utc)
        }

        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        oracle = TrustOracle(self.db_config)
        trust = oracle.query_trust_for_authorization(
            lct_id='lct:ai:001',
            organization_id='org:test',
            action_type='read',
            required_role='member'
        )

        # Should return composite score: 0.6*0.8 + 0.4*0.75 = 0.78
        self.assertAlmostEqual(trust, 0.78, places=2)
        oracle.close()

    def test_factory_function(self):
        """Test factory function"""
        oracle = create_trust_oracle(
            self.db_config,
            cache_ttl_seconds=120,
            enable_decay=False
        )

        self.assertIsInstance(oracle, TrustOracle)
        self.assertEqual(oracle.cache_ttl, 120)
        self.assertFalse(oracle.enable_decay)


if __name__ == '__main__':
    unittest.main()
