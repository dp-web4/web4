# Web4 Extension Registry
Status: Draft / experimental — pre-IANA template • Last-Updated: 2026-06-18

## Registry Name
Web4 Protocol Extensions

## Registration Procedure
Specification Required (RFC 8126)

## Reference
[Web4 Standard, protocols/web4-handshake.md §5 (Capability & Suite Negotiation)](../protocols/web4-handshake.md)

## Registry Contents

| Extension ID | Name | Description | Reference |
|--------------|------|-------------|-----------|
| 0x0001 | MRH_RDF | RDF-based Markov Relevancy Horizons | [Web4-MRH-RDF] |
| 0x0002 | WITNESS_EXTENDED | Extended witness attestation | [Web4-Witness] |
| 0x0003 | MCP_BRIDGE | Model Context Protocol bridge | [Web4-MCP] |
| 0x0004 | R6_TENSOR | R6 tensor calculations | [Web4-R6] |
| 0x0005 | T3_V3 | Trust and value tensor extensions | [Web4-T3V3] |
| 0x0006 | BLOCKCHAIN_BRIDGE | Blockchain integration | [Web4-Blockchain] |
| 0x0007 | QUANTUM_READY | Post-quantum cryptography | [Web4-PQC] |

## Extension Negotiation

Extensions are negotiated during the Web4 handshake protocol:

1. Client offers supported extensions in ClientHello
2. Server selects mutually supported extensions
3. Extensions modify protocol behavior as specified

## Notes

- Extensions MUST NOT change core protocol semantics
- Extensions MUST be backwards compatible
- Private use: 0xF000-0xFFFE
- Reserved: 0x0000, 0xFFFF