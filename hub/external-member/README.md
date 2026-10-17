# External message member — G1 foundation

Read [the PRD](../docs/PRD_EXTERNAL_MESSAGE_MEMBER.md). This is an inert Python
library, not a listening service, MCP adapter, signer, or usable Hub connection.
It has no network implementation and never reads fleet credentials.

Run isolated tests: `python3 -m unittest discover -s hub/external-member -v`.

`Binding` must come from the future authenticated host, never tool arguments.
Each store is pinned to one member/consumer/peer scope. Store only sealed opaque
bodies; the future wire adapter authenticates and validates the actual ciphertext.
The library does not implement cryptography or certify opaque strings as encrypted.
The service deployment must protect the directory and minimal metadata.

The proposed `hub-mailbox-receipt-v2` contract intentionally refuses current Hub's
legacy drain. Web4 #867 must land with real composed tests before an adapter can
claim it. Fakes in tests prove local state-machine behavior only. A matching
constant is NOT protocol negotiation or cryptographic authentication.

There is no pruning yet. Capacity counts acknowledged tombstones and accepted
outbox entries too: refuse new ingestion without ACK rather than silently dropping
history. Retention, compaction, multi-consumer routing, wire cryptography, OAuth,
remote MCP, admission and deployment remain PRD G2–G5 work.
