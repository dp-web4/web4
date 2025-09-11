# IETF Submission Guide for Web4

## Overview

This guide provides step-by-step instructions for submitting the Web4 specification as an Internet-Draft to the IETF.

## Current Status

- **Draft Name**: draft-web4-core-00
- **Status**: Ready for initial submission
- **Target**: Standards Track
- **Working Group**: Independent Submission (initially)

## Prerequisites

### 1. IETF Datatracker Account
Create an account at: https://datatracker.ietf.org/accounts/create/

### 2. XML2RFC Tools
Install the tools for validating and converting the draft:
```bash
pip install xml2rfc
```

### 3. Validate the Draft
```bash
cd web4-standard/submission
xml2rfc --text --html draft-web4-core-00.xml
```

## Submission Process

### Step 1: Initial Submission

1. Go to: https://datatracker.ietf.org/submit/
2. Upload `draft-web4-core-00.xml`
3. Fill in metadata:
   - Title: Web4: The Witnessed Internet Protocol Suite
   - Abstract: (copy from XML)
   - Intended Status: Standards Track
   - Areas: Internet Area

### Step 2: Find a Sponsor

For Standards Track, we need an Area Director sponsor:
- Target: Security Area or Internet Area
- Potential contacts:
  - Security ADs for cryptographic protocols
  - Internet ADs for new protocol suites

### Step 3: Community Review

1. Announce on relevant mailing lists:
   - secdispatch@ietf.org (Security Dispatch)
   - dispatch@ietf.org (General Dispatch)
   - saag@ietf.org (Security Area Advisory Group)

2. Present at IETF meeting:
   - Submit for dispatch workshop
   - Prepare 10-minute presentation
   - Focus on unique value proposition

### Step 4: Form Working Group (Optional)

If there's sufficient interest:
1. Write a charter
2. Find co-chairs
3. Get AD sponsorship
4. Hold BoF (Birds of a Feather) session

## Document Structure

The submission includes multiple documents that should be submitted as a suite:

### Core Documents (Phase 1)
1. `draft-web4-core-00` - Main architecture and overview
2. `draft-web4-binding-00` - Binding protocol specification
3. `draft-web4-handshake-00` - HPKE handshake protocol
4. `draft-web4-metering-00` - ATP/ADP metering protocol

### Extension Documents (Phase 2)
1. `draft-web4-privacy-00` - Privacy considerations
2. `draft-web4-iot-00` - IoT profile
3. `draft-web4-blockchain-00` - Blockchain integration

## Timeline

### Month 1: Initial Submission
- Submit draft-web4-core-00
- Announce on mailing lists
- Gather initial feedback

### Month 2-3: Revision
- Incorporate feedback
- Submit -01 version
- Find AD sponsor

### Month 4-6: Community Building
- Present at IETF meeting
- Build implementation community
- Demonstrate interoperability

### Month 7-12: Standardization
- Form working group (if applicable)
- Multiple draft iterations
- Last Call preparation

## Key Messages for IETF Community

### Unique Value Proposition
"Web4 introduces witnessed presence as a fundamental internet primitive, enabling unforgeable digital identity through cryptographic witnessing rather than central authorities."

### Technical Merit
- Built on proven primitives (HPKE, X25519, Ed25519)
- Privacy-preserving by design (pairwise identifiers)
- Scalable (no global consensus required)
- Implementable (reference code available)

### Use Cases
- IoT device identity (75B devices by 2025)
- AI agent reputation systems
- Decentralized energy markets
- Privacy-preserving authentication

### Implementation Status
- Reference implementation in Python
- Production implementation in modbatt-CAN
- Test vectors available
- Multiple conformance profiles

## Review Checklist

Before submission, ensure:

- [ ] XML validates without errors
- [ ] All normative references are stable RFCs
- [ ] Security considerations are comprehensive
- [ ] IANA considerations are complete
- [ ] IPR disclosure completed
- [ ] Co-authors agree on submission
- [ ] Abstract is under 200 words
- [ ] Examples compile and run

## Support Materials

### Presentation Template
```
Slide 1: Problem Statement
- Digital identity is forgeable
- No systematic trust building
- Privacy vs identity conflict

Slide 2: Web4 Solution
- Witnessed presence
- Four mechanisms
- Modern cryptography

Slide 3: Technical Approach
- HPKE handshake
- Pairwise identifiers
- MRH tensors

Slide 4: Implementation
- Reference code
- Real deployment
- Test suite

Slide 5: Call to Action
- Review the draft
- Join implementation
- Support WG formation
```

### FAQ Responses

**Q: How is this different from DID?**
A: DIDs provide identity; Web4 provides witnessed presence. DIDs can be created arbitrarily; Web4 entities exist only through witnessing.

**Q: Why not use existing protocols?**
A: Existing protocols lack the binding/pairing/witnessing/broadcast distinction and don't provide witness-based trust accumulation.

**Q: What about blockchain?**
A: Web4 can anchor to blockchains but doesn't require global consensus for every operation, making it more scalable.

## Contacts

### Draft Authors
- Web4 Working Group: standards@web4.dev
- GitHub: https://github.com/dp-web4/web4

### IETF Resources
- Datatracker: https://datatracker.ietf.org/
- Tools: https://tools.ietf.org/
- Mailing lists: https://www.ietf.org/mailman/listinfo

## Next Steps

1. **Immediate**: Validate XML and generate text/HTML versions
2. **Week 1**: Create datatracker account and submit draft
3. **Week 2**: Announce on security and dispatch lists
4. **Month 1**: Identify potential AD sponsor
5. **Ongoing**: Build community and implementations

## Success Metrics

- Initial submission accepted
- Positive mailing list feedback
- AD sponsor identified
- Working group formed
- Multiple implementations
- Interoperability demonstrated

---

*Remember: The IETF runs on "rough consensus and running code". We have the running code; now we need to build consensus.*