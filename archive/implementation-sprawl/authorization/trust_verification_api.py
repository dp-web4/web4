#!/usr/bin/env python3
"""
Trust Verification API
Session #57: REST API for Merkle proof verification and audit queries

Provides HTTP endpoints for:
- Verifying trust updates against Merkle roots
- Querying audit trails
- Checking database integrity
- Historical trust evolution

Architecture:
- Flask REST API
- PostgreSQL backend (merkle schema)
- JSON responses
- CORS enabled for Web UI integration
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from typing import Optional, Dict, List, Any

from trust_merkle_tree import TrustMerkleTree

app = Flask(__name__)
CORS(app)  # Enable CORS for web UI

# Database configuration
DB_CONFIG = {
    'dbname': 'web4',
    'user': 'postgres',
    'host': 'localhost'
}


def get_db_connection():
    """Get database connection"""
    return psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
        conn.close()
        return jsonify({'status': 'healthy', 'timestamp': datetime.utcnow().isoformat()})
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 500


@app.route('/api/v1/merkle/roots', methods=['GET'])
def get_merkle_roots():
    """
    Get recent Merkle roots.

    Query params:
        limit: Number of roots to return (default: 10)
        offset: Pagination offset (default: 0)

    Returns:
        List of Merkle roots with metadata
    """
    limit = int(request.args.get('limit', 10))
    offset = int(request.args.get('offset', 0))

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                root_id,
                merkle_root,
                previous_root,
                flush_timestamp,
                batch_size,
                leaf_count,
                total_actions,
                total_transactions,
                blockchain_tx_hash,
                anchored_at
            FROM merkle_roots
            ORDER BY flush_timestamp DESC
            LIMIT %s OFFSET %s
        """, (limit, offset))

        roots = cursor.fetchall()

        # Get total count
        cursor.execute("SELECT COUNT(*) as total FROM merkle_roots")
        total = cursor.fetchone()['total']

        cursor.close()
        conn.close()

        return jsonify({
            'roots': roots,
            'total': total,
            'limit': limit,
            'offset': offset
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/v1/merkle/root/<root_id>', methods=['GET'])
def get_merkle_root(root_id):
    """
    Get specific Merkle root details.

    Path params:
        root_id: Merkle root ID

    Returns:
        Root details with leaf list
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Get root details
        cursor.execute("""
            SELECT *
            FROM merkle_roots
            WHERE root_id = %s
        """, (root_id,))

        root = cursor.fetchone()

        if not root:
            cursor.close()
            conn.close()
            return jsonify({'error': 'Root not found'}), 404

        # Get leaves
        cursor.execute("""
            SELECT *
            FROM trust_update_leaves
            WHERE root_id = %s
            ORDER BY leaf_index
        """, (root_id,))

        leaves = cursor.fetchall()

        cursor.close()
        conn.close()

        return jsonify({
            'root': root,
            'leaves': leaves
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/v1/merkle/verify', methods=['POST'])
def verify_merkle_proof():
    """
    Verify a Merkle proof.

    Request body (JSON):
        {
            "leaf_hash": "abc123...",
            "proof": [["def456...", "right"], ["ghi789...", "left"], ...],
            "merkle_root": "root123..."
        }

    Returns:
        Verification result
    """
    try:
        data = request.get_json()

        leaf_hash = data.get('leaf_hash')
        proof = data.get('proof')
        merkle_root = data.get('merkle_root')

        if not all([leaf_hash, proof, merkle_root]):
            return jsonify({'error': 'Missing required fields'}), 400

        # Verify using static method
        is_valid = TrustMerkleTree.verify_proof_hex(leaf_hash, proof, merkle_root)

        return jsonify({
            'valid': is_valid,
            'leaf_hash': leaf_hash,
            'merkle_root': merkle_root,
            'proof_length': len(proof)
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/v1/trust/history/<lct_id>/<org_id>', methods=['GET'])
def get_trust_history(lct_id, org_id):
    """
    Get trust update history for an entity.

    Path params:
        lct_id: LCT identity
        org_id: Organization ID

    Query params:
        limit: Number of updates to return (default: 100)

    Returns:
        Trust update history with Merkle proofs
    """
    limit = int(request.args.get('limit', 100))

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM get_entity_trust_history(%s, %s, %s)
        """, (lct_id, org_id, limit))

        history = cursor.fetchall()

        cursor.close()
        conn.close()

        return jsonify({
            'lct_id': lct_id,
            'org_id': org_id,
            'history': history,
            'count': len(history)
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/v1/trust/audit', methods=['GET'])
def get_audit_trail():
    """
    Get complete audit trail.

    Query params:
        start_date: Start date (ISO format)
        end_date: End date (ISO format)
        limit: Number of records (default: 100)
        offset: Pagination offset (default: 0)

    Returns:
        Audit trail records
    """
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    limit = int(request.args.get('limit', 100))
    offset = int(request.args.get('offset', 0))

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        query = """
            SELECT *
            FROM trust_audit_trail
            WHERE 1=1
        """
        params = []

        if start_date:
            query += " AND update_timestamp >= %s"
            params.append(start_date)

        if end_date:
            query += " AND update_timestamp <= %s"
            params.append(end_date)

        query += " ORDER BY update_timestamp DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])

        cursor.execute(query, params)
        records = cursor.fetchall()

        # Get total count
        count_query = """
            SELECT COUNT(*) as total
            FROM trust_audit_trail
            WHERE 1=1
        """
        count_params = []

        if start_date:
            count_query += " AND update_timestamp >= %s"
            count_params.append(start_date)

        if end_date:
            count_query += " AND update_timestamp <= %s"
            count_params.append(end_date)

        cursor.execute(count_query, count_params)
        total = cursor.fetchone()['total']

        cursor.close()
        conn.close()

        return jsonify({
            'records': records,
            'total': total,
            'limit': limit,
            'offset': offset
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/v1/merkle/chain', methods=['GET'])
def get_merkle_chain():
    """
    Get Merkle root chain (linked via previous_root).

    Returns:
        Chain of roots showing lineage
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM merkle_chain
            ORDER BY depth
        """)

        chain = cursor.fetchall()

        cursor.close()
        conn.close()

        return jsonify({
            'chain': chain,
            'length': len(chain)
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/v1/trust/proof/<lct_id>/<org_id>', methods=['GET'])
def get_trust_proof(lct_id, org_id):
    """
    Get Merkle proof for entity's most recent update.

    Path params:
        lct_id: LCT identity
        org_id: Organization ID

    Returns:
        Merkle proof data
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Get most recent update for entity
        cursor.execute("""
            SELECT l.*, p.proof_path, r.merkle_root
            FROM trust_update_leaves l
            JOIN merkle_roots r ON l.root_id = r.root_id
            LEFT JOIN merkle_proofs p ON l.leaf_id = p.leaf_id
            WHERE l.lct_id = %s AND l.organization_id = %s
            ORDER BY l.update_timestamp DESC
            LIMIT 1
        """, (lct_id, org_id))

        result = cursor.fetchone()

        if not result:
            cursor.close()
            conn.close()
            return jsonify({'error': 'No updates found for entity'}), 404

        cursor.close()
        conn.close()

        # Convert proof_path from JSONB to list if available
        if result['proof_path']:
            proof = result['proof_path']
        else:
            proof = None

        return jsonify({
            'lct_id': lct_id,
            'org_id': org_id,
            'leaf_hash': result['leaf_hash'],
            'merkle_root': result['merkle_root'],
            'proof': proof,
            'timestamp': result['update_timestamp'].isoformat() if result['update_timestamp'] else None,
            'deltas': {
                'talent': float(result['talent_delta']) if result['talent_delta'] else 0,
                'training': float(result['training_delta']) if result['training_delta'] else 0,
                'temperament': float(result['temperament_delta']) if result['temperament_delta'] else 0,
                'veracity': float(result['veracity_delta']) if result['veracity_delta'] else 0,
                'validity': float(result['validity_delta']) if result['validity_delta'] else 0,
                'valuation': float(result['valuation_delta']) if result['valuation_delta'] else 0
            }
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/v1/integrity/check', methods=['GET'])
def check_integrity():
    """
    Check database integrity against Merkle roots.

    Returns:
        Integrity check results
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check root chain integrity
        cursor.execute("""
            SELECT COUNT(*) as broken_links
            FROM merkle_roots r1
            WHERE previous_root IS NOT NULL
            AND NOT EXISTS (
                SELECT 1 FROM merkle_roots r2
                WHERE r2.merkle_root = r1.previous_root
            )
        """)
        broken_links = cursor.fetchone()['broken_links']

        # Check for duplicate roots (should be impossible with UNIQUE constraint)
        cursor.execute("""
            SELECT merkle_root, COUNT(*) as count
            FROM merkle_roots
            GROUP BY merkle_root
            HAVING COUNT(*) > 1
        """)
        duplicates = cursor.fetchall()

        # Get total stats
        cursor.execute("""
            SELECT
                COUNT(*) as total_roots,
                SUM(batch_size) as total_updates,
                MIN(flush_timestamp) as first_flush,
                MAX(flush_timestamp) as last_flush
            FROM merkle_roots
        """)
        stats = cursor.fetchone()

        cursor.close()
        conn.close()

        return jsonify({
            'integrity': {
                'broken_chain_links': broken_links,
                'duplicate_roots': len(duplicates),
                'status': 'OK' if (broken_links == 0 and len(duplicates) == 0) else 'COMPROMISED'
            },
            'stats': stats
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    print("Trust Verification API")
    print("=" * 60)
    print(f"Database: {DB_CONFIG['dbname']}@{DB_CONFIG['host']}")
    print(f"Starting server on http://localhost:5000")
    print(f"\nEndpoints:")
    print(f"  GET  /health")
    print(f"  GET  /api/v1/merkle/roots")
    print(f"  GET  /api/v1/merkle/root/<root_id>")
    print(f"  POST /api/v1/merkle/verify")
    print(f"  GET  /api/v1/trust/history/<lct_id>/<org_id>")
    print(f"  GET  /api/v1/trust/audit")
    print(f"  GET  /api/v1/merkle/chain")
    print(f"  GET  /api/v1/trust/proof/<lct_id>/<org_id>")
    print(f"  GET  /api/v1/integrity/check")
    print("=" * 60)

    app.run(debug=True, host='0.0.0.0', port=5000)
