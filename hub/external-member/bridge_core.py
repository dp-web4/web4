"""Inert external-member bridge foundation; no network or key custody.

The authenticated host supplies Binding; never construct it from tool arguments.
Only sealed opaque envelopes enter storage. Wire/auth adapters are separate gates.
SPDX-License-Identifier: AGPL-3.0-or-later
"""
from dataclasses import dataclass
import hashlib
import json
import sqlite3
from typing import Protocol

CONTRACT = 'hub-mailbox-receipt-v2'  # Proposed contract, NOT shipped Hub API.
MAX_ENVELOPE_BYTES = 65536


class Refused(ValueError):
    pass


@dataclass(frozen=True)
class Binding:
    member: str
    consumer: str
    peers: frozenset[str]


class Transport(Protocol):
    """Trusted adapter must authenticate and validate this capability remotely.

    send must deduplicate (member, operation_id); fetch must not consume.
    ACK and acceptance are durable/idempotent. Legacy Hub cannot implement this.
    """
    contract: str
    def fetch(self, member: str, limit: int) -> list[dict]: ...
    def ack(self, member: str, message_id: str) -> None: ...
    def send(self, member: str, operation_id: str, envelope: dict) -> dict: ...


def encoded(envelope: dict) -> str:
    if not isinstance(envelope, dict) or set(envelope) != {'id', 'from', 'to', 'sealed'}:
        raise Refused('exact envelope fields required')
    if any(not isinstance(v, str) or not v for v in envelope.values()):
        raise Refused('nonempty string envelope fields required')
    if any(len(envelope[k]) > 256 for k in ('id', 'from', 'to')):
        raise Refused('identity too long')
    body = json.dumps(envelope, sort_keys=True, separators=(',', ':'))
    if len(body.encode()) > MAX_ENVELOPE_BYTES:
        raise Refused('envelope too large')
    return body


class Bridge:
    """One database per explicitly configured external presence/consumer.

    Opening with a different binding refuses; scope updates need a reviewed
    migration. live() is a trusted host revocation check, called on every act.
    No default live callback, path, identity or transport exists.
    """
    def __init__(self, path: str, binding: Binding, transport: Transport, live,
                 capacity: int = 10000):
        if not binding.member or not binding.consumer or capacity <= 0:
            raise Refused('explicit binding and capacity required')
        self.binding, self.transport, self.live = binding, transport, live
        self.capacity = capacity
        self.db = sqlite3.connect(path)
        self.db.row_factory = sqlite3.Row
        self.db.execute('PRAGMA synchronous=FULL')
        self.db.executescript('''
            CREATE TABLE IF NOT EXISTS binding (singleton INTEGER PRIMARY KEY CHECK(singleton=1), value TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS inbox (id TEXT PRIMARY KEY, body TEXT NOT NULL, presented INTEGER NOT NULL DEFAULT 0, acked INTEGER NOT NULL DEFAULT 0);
            CREATE TABLE IF NOT EXISTS outbox (id TEXT PRIMARY KEY, body TEXT NOT NULL, receipt TEXT);
        ''')
        value = json.dumps([binding.member, binding.consumer, sorted(binding.peers)])
        with self.db:
            self.db.execute('INSERT OR IGNORE INTO binding VALUES (1, ?)', (value,))
        if self.db.execute('SELECT value FROM binding').fetchone()[0] != value:
            self.db.close()
            raise Refused('database belongs to a different binding/scope')

    def close(self):
        self.db.close()

    def guard(self):
        if self.live(self.binding) is not True:
            raise Refused('binding revoked or unavailable')

    def wire_guard(self):
        self.guard()
        if self.transport.contract != CONTRACT:
            raise Refused('durable receipt transport unavailable; no legacy drain fallback')

    def sync(self, limit: int = 100) -> int:
        self.wire_guard()
        if type(limit) is not int or not 1 <= limit <= 100:
            raise Refused('limit must be 1..100')
        rows = self.transport.fetch(self.binding.member, limit)
        if not isinstance(rows, list) or len(rows) > limit:
            raise Refused('invalid upstream batch')
        self.guard()
        # Validate/commit the complete batch before ANY upstream ACK.
        with self.db:
            for row in rows:
                body = encoded(row)
                if row['to'] != self.binding.member or row['from'] not in self.binding.peers:
                    raise Refused('envelope outside binding scope')
                old = self.db.execute('SELECT body FROM inbox WHERE id=?', (row['id'],)).fetchone()
                if old is not None:
                    if old[0] != body:
                        raise Refused('message ID/content conflict')
                    continue
                if self.db.execute('SELECT COUNT(*) FROM inbox').fetchone()[0] >= self.capacity:
                    raise Refused('capacity reached; upstream messages retained')
                self.db.execute('INSERT INTO inbox(id,body) VALUES (?,?)', (row['id'], body))
        for row in rows:
            self.wire_guard()
            self.transport.ack(self.binding.member, row['id'])
        return len(rows)

    def inbox(self, limit: int = 100) -> list[dict]:
        self.guard()
        if type(limit) is not int or not 1 <= limit <= 100:
            raise Refused('limit must be 1..100')
        with self.db:
            rows = self.db.execute('SELECT id,body FROM inbox WHERE acked=0 ORDER BY rowid LIMIT ?', (limit,)).fetchall()
            self.db.executemany('UPDATE inbox SET presented=1 WHERE id=?', [(r['id'],) for r in rows])
        # This records presentation attempt, not proof a response reached a chat.
        # Lost responses leave rows unacked and readable again.
        return [json.loads(r['body']) for r in rows]

    def ack(self, message_id: str):
        self.guard()
        with self.db:
            row = self.db.execute('SELECT presented FROM inbox WHERE id=?', (message_id,)).fetchone()
            if row is None or not row[0]:
                raise Refused('message was not presented to this bound consumer')
            self.db.execute('UPDATE inbox SET acked=1 WHERE id=?', (message_id,))
        return {'message_id': message_id, 'state': 'received', 'completed': False}

    def enqueue(self, envelope: dict):
        self.guard()
        body = encoded(envelope)
        if envelope['from'] != self.binding.member or envelope['to'] not in self.binding.peers:
            raise Refused('sender/recipient outside binding')
        with self.db:
            old = self.db.execute('SELECT body FROM outbox WHERE id=?', (envelope['id'],)).fetchone()
            if old is not None and old[0] != body:
                raise Refused('operation ID/content conflict')
            if old is None:
                if self.db.execute('SELECT COUNT(*) FROM outbox').fetchone()[0] >= self.capacity:
                    raise Refused('outbox capacity reached')
                self.db.execute('INSERT INTO outbox(id,body) VALUES (?,?)', (envelope['id'], body))
        return self.status(envelope['id'])

    def flush(self, operation_id: str):
        self.wire_guard()
        row = self.db.execute('SELECT body,receipt FROM outbox WHERE id=?', (operation_id,)).fetchone()
        if row is None:
            raise Refused('unknown operation')
        if row['receipt'] is not None:
            return self.status(operation_id)
        receipt = self.transport.send(self.binding.member, operation_id, json.loads(row['body']))
        digest = hashlib.sha256(row['body'].encode()).hexdigest()
        if (not isinstance(receipt, dict) or receipt.get('state') != 'durably_accepted'
                or receipt.get('operation_id') != operation_id
                or receipt.get('member') != self.binding.member
                or receipt.get('content_sha256') != digest
                or not isinstance(receipt.get('receipt_id'), str) or not receipt['receipt_id']):
            raise Refused('invalid durable acceptance receipt; outcome remains unknown')
        self.guard()
        with self.db:
            self.db.execute('UPDATE outbox SET receipt=? WHERE id=?', (json.dumps(receipt), operation_id))
        return self.status(operation_id)

    def status(self, operation_id: str):
        self.guard()
        row = self.db.execute('SELECT receipt FROM outbox WHERE id=?', (operation_id,)).fetchone()
        if row is None:
            raise Refused('unknown operation')
        return {'operation_id': operation_id,
                'state': 'durably_accepted' if row[0] else 'pending_or_unknown',
                'receipt': json.loads(row[0]) if row[0] else None}
