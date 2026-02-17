# Society-Authority-Law (SAL) Integration Summary

## Overview

The Society-Authority-Law (SAL) layer has been integrated into the Web4 standard, providing a complete trust accountability layer for entity lifecycle, authority delegation, and transparent rule compliance.

## Key Concepts Added

### 1. Society as First-Class Entity
- **Definition**: Delegative entity with authority to issue citizenship and bind law
- **Capabilities**: Issues birth certificates, maintains Law Oracle, operates immutable ledger
- **Fractal**: Societies can be citizens of other societies (team → org → network → ecosystem)

### 2. Enhanced Birth Certificate
Every entity is now born into a society with:
- Society context and Law Oracle reference
- Witness quorum requirements
- Immutable ledger proof
- Initial rights AND responsibilities
- Law version binding at birth

### 3. Law Oracle
Machine-readable law publication system:
- Versioned law datasets (norms, procedures, interpretations)
- Compliance query interface with proof transcripts
- R6 action grammar mapping
- Deterministic Q&A capability

### 4. Authority Delegation
Structured delegation mechanism:
- Scoped authority (finance, safety, membership)
- Sub-authority creation with limits
- Machine-readable scope publication
- Emergency powers if defined by law

### 5. Enhanced Witness Role
Beyond basic attestation:
- Co-signs ledger entries for SAL-critical events
- Maintains immutable record
- Participates in quorum requirements
- Provides availability proofs

### 6. Auditor Role
New role with adjustment powers:
- Traverses society's MRH graph
- Validates/adjusts T3/V3 tensors
- Evidence-based audit transcripts
- Rate-limited adjustments per law

## SAL-R6 Mapping

| R6 Component | SAL Source | Enforcement |
|--------------|------------|-------------|
| **Rules** | Law Oracle norms + procedures | Law hash pinned at action time |
| **Role** | Citizen (prereq), Authority/Oracle/Other | Role LCTs with scopes |
| **Request** | Actor's intent within society | Quorum check; caps/limits |
| **Reference** | MRH graph (precedents) | Graph queries + witnesses |
| **Resource** | ATP/compute caps from law | Metering + pricing oracles |
| **Result** | Outcome + attestations | T3/V3 updates; auditor adjustments |

## MRH Graph Extensions

New RDF triples for SAL:
```turtle
@prefix web4: <https://web4.io/ontology#> .

# Society membership
lct:entity web4:memberOf lct:society .

# Authority structure
lct:society web4:hasAuthority lct:authorityRole .
lct:society web4:hasLawOracle lct:lawOracle .

# Delegation chain
lct:authority web4:delegatesTo lct:subAuthority .

# Law publication
lct:lawOracle web4:publishes lct:lawDatasetV120 .
```

## Implementation Requirements

### Mandatory (MUST)
1. Every entity born into a society context
2. Birth certificate written to immutable ledger
3. Witness quorum for SAL-critical events
4. Law Oracle for every society
5. Ledger inclusion proofs

### Recommended (SHOULD)
1. Deterministic audit adjustments
2. Appeal paths for negative adjustments
3. Rate limits on adjustments
4. Law version caching

## Benefits of SAL Integration

1. **Complete Provenance**: Every entity has verifiable origin
2. **Clear Governance**: Machine-readable laws and authority
3. **Fractal Composition**: Societies nest naturally
4. **Audit Trail**: All critical events on immutable ledger
5. **Dispute Resolution**: Evidence-based adjustments with appeals

## Migration Path

For existing implementations:
1. Define root society for existing entities
2. Generate retroactive birth certificates
3. Deploy Law Oracle with initial ruleset
4. Establish witness quorum policies
5. Enable auditor role gradually

## Security Considerations

- Law downgrades prevented by version pinning
- Witness diversity requirements prevent collusion
- Rate limits prevent adjustment abuse
- Evidence requirements prevent arbitrary changes
- Immutable ledger provides non-repudiation

## Next Steps

1. Deploy reference Law Oracle implementation
2. Create society bootstrapping tools
3. Define standard law dataset schemas
4. Implement witness quorum protocols
5. Build auditor adjustment framework

## References

- [Web4 Society-Authority-Law Specification](core-spec/web4-society-authority-law.md)
- [SAL JSON-LD Context](../forum/nova/web4-sal-bundle/sal.jsonld)
- [SAL Ontology](../forum/nova/web4-sal-bundle/sal-ontology.ttl)
- [Conformance Tests](../forum/nova/web4-sal-bundle/web4-sal-conformance-and-ledger/)