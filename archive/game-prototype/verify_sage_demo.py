#!/usr/bin/env python3
"""
Quick verification that SAGE demo worked
Checks database for evidence of SAGE's activity
"""

import psycopg2
from psycopg2.extras import RealDictCursor

def verify_sage_activity():
    """Check database for SAGE's activity"""

    conn = psycopg2.connect(
        dbname='web4_test',
        user='postgres',
        host='localhost',
        cursor_factory=RealDictCursor
    )
    cursor = conn.cursor()

    print("=" * 70)
    print("  SAGE Activity Verification")
    print("=" * 70)

    # Check SAGE exists in database
    cursor.execute("""
        SELECT lct_id, entity_type, created_at
        FROM lct_identities
        WHERE lct_id = 'lct:sage:legion:1763906585'
    """)
    sage = cursor.fetchone()

    if sage:
        print(f"\n✅ SAGE Identity Found:")
        print(f"   LCT: {sage['lct_id']}")
        print(f"   Type: {sage['entity_type']}")
        print(f"   Created: {sage['created_at']}")
    else:
        print(f"\n❌ SAGE identity not found")
        return

    # Check SAGE reputation
    cursor.execute("""
        SELECT talent_score, training_score, temperament_score,
               total_actions, last_updated
        FROM reputation_scores
        WHERE lct_id = 'lct:sage:legion:1763906585'
    """)
    rep = cursor.fetchone()

    if rep:
        t3 = (float(rep['talent_score']) + float(rep['training_score']) +
              float(rep['temperament_score'])) / 3.0
        print(f"\n✅ SAGE Reputation:")
        print(f"   T3 Composite: {t3:.3f}")
        print(f"   Talent: {rep['talent_score']:.3f}")
        print(f"   Training: {rep['training_score']:.3f}")
        print(f"   Temperament: {rep['temperament_score']:.3f}")
        print(f"   Total Actions: {rep['total_actions']}")
        print(f"   Last Updated: {rep['last_updated']}")

    # Check trust history for SAGE
    cursor.execute("""
        SELECT event_type, t3_delta, event_description, recorded_at
        FROM trust_history
        WHERE lct_id = 'lct:sage:legion:1763906585'
        ORDER BY recorded_at DESC
        LIMIT 5
    """)
    history = cursor.fetchall()

    if history:
        print(f"\n✅ SAGE Trust History ({len(history)} recent events):")
        for h in history:
            print(f"   [{h['recorded_at']}] {h['event_type']}: {h['t3_delta']:+.3f}")
            print(f"      {h['event_description'][:60]}...")

    # Check failure attributions (Bob's fraud)
    cursor.execute("""
        SELECT attributed_to_lct, failure_type, confidence_score,
               detected_at, penalty_applied
        FROM failure_attributions
        WHERE failure_type = 'sabotage'
        ORDER BY detected_at DESC
        LIMIT 5
    """)
    attributions = cursor.fetchall()

    if attributions:
        print(f"\n✅ Failure Attributions ({len(attributions)} found):")
        for attr in attributions:
            print(f"   Target: {attr['attributed_to_lct'][:40]}")
            print(f"   Type: {attr['failure_type']}")
            print(f"   Confidence: {attr['confidence_score']:.2f}")
            print(f"   Penalty: {'Yes' if attr['penalty_applied'] else 'No'}")
            print(f"   Detected: {attr['detected_at']}")
            print()

    # Check all reputation scores in game org
    cursor.execute("""
        SELECT lct_id, talent_score, training_score, temperament_score
        FROM reputation_scores
        WHERE organization_id = 'org:web4:game'
        ORDER BY lct_id
    """)
    all_reps = cursor.fetchall()

    if all_reps:
        print(f"\n✅ All Game Organization Reputation Scores:")
        for r in all_reps:
            t3 = (float(r['talent_score']) + float(r['training_score']) +
                  float(r['temperament_score'])) / 3.0
            print(f"   {r['lct_id'][:50]:50} T3: {t3:.3f}")

    print("\n" + "=" * 70)

    cursor.close()
    conn.close()

if __name__ == "__main__":
    verify_sage_activity()
