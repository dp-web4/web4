"""Hermetic state-machine tests. No production transport or credentials."""
import hashlib
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

from bridge_core import Binding, Bridge, CONTRACT, Refused, encoded


class FakeWire:
    contract = CONTRACT

    def __init__(self):
        self.rows = []
        self.acks = []
        self.sent = {}
        self.lose_ack = False
        self.lose_send = False
        self.bad_receipt = False

    def fetch(self, member, limit):
        return self.rows[:limit]

    def ack(self, member, message_id):
        self.acks.append((member, message_id))
        if self.lose_ack:
            raise TimeoutError('ACK reply lost')
        self.rows = [r for r in self.rows if r['id'] != message_id]

    def send(self, member, operation_id, envelope):
        body = encoded(envelope)
        previous = self.sent.setdefault((member, operation_id), body)
        if previous != body:
            raise Refused('upstream dedup conflict')
        if self.lose_send:
            raise TimeoutError('send reply lost after commit')
        if self.bad_receipt:
            return {'delivered': True}
        return {'state': 'durably_accepted', 'operation_id': operation_id,
                'member': member, 'receipt_id': 'receipt-1',
                'content_sha256': hashlib.sha256(body.encode()).hexdigest()}


class BridgeTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = str(Path(self.temp.name) / 'inbox.sqlite')
        self.binding = Binding('external', 'one-consumer', frozenset({'thor'}))
        self.wire = FakeWire()
        self.active = True
        self.bridge = self.open()
        self.incoming = {'id': 'm1', 'from': 'thor', 'to': 'external', 'sealed': 'opaque-test-ciphertext'}
        self.outgoing = {'id': 'op1', 'from': 'external', 'to': 'thor', 'sealed': 'opaque-test-ciphertext'}

    def open(self, **kw):
        return Bridge(self.path, self.binding, self.wire, lambda _: self.active, **kw)

    def tearDown(self):
        self.bridge.close()
        self.temp.cleanup()

    def restart(self, **kw):
        self.bridge.close()
        self.bridge = self.open(**kw)

    def test_restart_after_upstream_ack_before_chat_read(self):
        self.wire.rows = [self.incoming]
        self.bridge.sync()
        self.assertEqual(self.wire.rows, [])
        self.restart()
        self.assertEqual(self.bridge.inbox(), [self.incoming])
        self.assertEqual(self.bridge.inbox(), [self.incoming])
        self.assertFalse(self.bridge.ack('m1')['completed'])
        self.restart()
        self.assertEqual(self.bridge.inbox(), [])

    def test_lost_ack_response_redelivers_one_row(self):
        self.wire.rows = [self.incoming]
        self.wire.lose_ack = True
        with self.assertRaises(TimeoutError):
            self.bridge.sync()
        self.restart()
        self.wire.lose_ack = False
        self.bridge.sync()
        self.assertEqual(self.bridge.inbox(), [self.incoming])
        self.assertEqual(len(self.wire.acks), 2)

    def test_tombstone_prevents_reappearance(self):
        self.wire.rows = [self.incoming]
        self.bridge.sync()
        self.bridge.inbox()
        self.bridge.ack('m1')
        self.restart()
        self.wire.rows = [self.incoming]
        self.bridge.sync()
        self.assertEqual(self.bridge.inbox(), [])

    def test_storage_failure_no_upstream_ack(self):
        self.bridge.db.execute("CREATE TRIGGER fail_write BEFORE INSERT ON inbox BEGIN SELECT RAISE(ABORT, 'disk fault'); END")
        self.wire.rows = [self.incoming]
        with self.assertRaises(sqlite3.DatabaseError):
            self.bridge.sync()
        self.assertEqual(self.wire.acks, [])
        self.assertEqual(self.wire.rows, [self.incoming])

    def test_bad_batch_is_atomic(self):
        self.wire.rows = [self.incoming, dict(self.incoming, id='m2', to='other')]
        with self.assertRaises(Refused):
            self.bridge.sync()
        self.assertEqual(self.bridge.inbox(), [])
        self.assertEqual(self.wire.acks, [])

    def test_message_id_conflict_not_acked(self):
        self.wire.rows = [self.incoming]
        self.bridge.sync()
        self.wire.rows = [dict(self.incoming, sealed='changed')]
        with self.assertRaises(Refused):
            self.bridge.sync()
        self.assertEqual(len(self.wire.acks), 1)
        self.assertEqual(self.bridge.inbox(), [self.incoming])

    def test_binding_and_consumer_cannot_be_switched(self):
        for b in [Binding('other', 'one-consumer', self.binding.peers),
                  Binding('external', 'other-chat', self.binding.peers),
                  Binding('external', 'one-consumer', frozenset({'other'}))]:
            with self.assertRaises(Refused):
                Bridge(self.path, b, self.wire, lambda _: True)

    def test_unpresented_ack_refused(self):
        self.wire.rows = [self.incoming]
        self.bridge.sync()
        with self.assertRaises(Refused):
            self.bridge.ack('m1')
        with self.assertRaises(Refused):
            self.bridge.ack('unknown')

    def test_revocation_blocks_all_public_acts(self):
        self.active = False
        for act in [self.bridge.sync, self.bridge.inbox,
                    lambda: self.bridge.ack('m1'),
                    lambda: self.bridge.enqueue(self.outgoing),
                    lambda: self.bridge.flush('op1'),
                    lambda: self.bridge.status('op1')]:
            with self.assertRaises(Refused):
                act()
        self.assertEqual(self.wire.acks, [])
        self.assertEqual(self.wire.sent, {})

    def test_revocation_during_fetch_prevents_commit_and_ack(self):
        def fetch(member, limit):
            self.active = False
            return [self.incoming]
        self.wire.fetch = fetch
        with self.assertRaises(Refused):
            self.bridge.sync()
        self.active = True
        self.assertEqual(self.bridge.inbox(), [])
        self.assertEqual(self.wire.acks, [])

    def test_legacy_transport_is_refused_without_fetch(self):
        self.wire.contract = 'legacy-drain'
        self.wire.fetch = lambda *_: self.fail('legacy endpoint called')
        with self.assertRaises(Refused):
            self.bridge.sync()

    def test_capacity_preserves_upstream_queue(self):
        self.restart(capacity=1)
        self.wire.rows = [self.incoming]
        self.bridge.sync()
        self.wire.rows = [dict(self.incoming, id='m2')]
        with self.assertRaises(Refused):
            self.bridge.sync()
        self.assertEqual(len(self.wire.acks), 1)
        self.assertEqual(self.wire.rows[0]['id'], 'm2')

    def test_outbox_restart_and_lost_response_same_operation(self):
        self.assertEqual(self.bridge.enqueue(self.outgoing)['state'], 'pending_or_unknown')
        self.wire.lose_send = True
        with self.assertRaises(TimeoutError):
            self.bridge.flush('op1')
        self.restart()
        self.assertEqual(self.bridge.status('op1')['state'], 'pending_or_unknown')
        self.wire.lose_send = False
        self.assertEqual(self.bridge.flush('op1')['state'], 'durably_accepted')
        self.assertEqual(len(self.wire.sent), 1)
        self.restart()
        self.assertEqual(self.bridge.flush('op1')['state'], 'durably_accepted')

    def test_outbox_spoof_and_reuse_conflict(self):
        with self.assertRaises(Refused):
            self.bridge.enqueue(dict(self.outgoing, **{'from': 'codex'}))
        with self.assertRaises(Refused):
            self.bridge.enqueue(dict(self.outgoing, to='unapproved'))
        self.bridge.enqueue(self.outgoing)
        with self.assertRaises(Refused):
            self.bridge.enqueue(dict(self.outgoing, sealed='changed'))

    def test_no_outer_success_is_a_receipt(self):
        self.bridge.enqueue(self.outgoing)
        self.wire.bad_receipt = True
        with self.assertRaises(Refused):
            self.bridge.flush('op1')
        self.assertEqual(self.bridge.status('op1')['state'], 'pending_or_unknown')

    def test_receipt_must_bind_member_operation_and_content(self):
        self.bridge.enqueue(self.outgoing)
        send = self.wire.send
        good = send('external', 'op1', self.outgoing)
        for field in ('member', 'operation_id', 'content_sha256', 'receipt_id', 'state'):
            self.wire.send = lambda *_, field=field: dict(good, **{field: ''})
            with self.assertRaises(Refused):
                self.bridge.flush('op1')
        self.assertEqual(self.bridge.status('op1')['state'], 'pending_or_unknown')

    def test_payload_bounds_and_unknown_fields(self):
        for row in [dict(self.outgoing, sealed='x' * 65536),
                    dict(self.outgoing, role='sovereign')]:
            with self.assertRaises(Refused):
                self.bridge.enqueue(row)
        for limit in [0, 101, True, '1']:
            with self.assertRaises(Refused):
                self.bridge.inbox(limit)


if __name__ == '__main__':
    unittest.main()
