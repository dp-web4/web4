# Proposal: Add R6 Action Framework to Part 2

## Proposer
- LCT: human-dennis
- Date: 2025-08-19
- Status: Under Review

## Summary
Add a new section 2.5 "The R6 Action Framework" that formalizes how all actions in Web4 emerge from the composition of Rules, Role, Request, Reference, Resource → Result.

## Rationale
Currently, the whitepaper describes the components (LCTs, entities, roles, MRH) but doesn't explain how these components interact to produce actions. The R6 framework fills this gap by providing a formal structure for all Web4 interactions.

## Key Contributions
1. **Makes intent explicit** - The Request component captures what is desired
2. **Acknowledges uncertainty** - Result may differ from Request  
3. **Creates feedback loops** - Request-Result alignment drives trust evolution
4. **Natural governance** - Constraints emerge from the R6 components themselves

## Proposed Changes

### Location
Insert as new Section 2.5, after current Section 2.4 (MRH). Renumber MRH to 2.6.

### Content Structure
- 2.5 The R6 Action Framework
  - 2.5.1 Components of R6 Actions
  - 2.5.2 Confidence Thresholds and Action Initiation
  - 2.5.3 Request-Result Alignment and Trust Impact
  - 2.5.4 R6 Actions and LCT Integration
  - 2.5.5 Composability and Hierarchical Actions
  - 2.5.6 Governance Through R6 Constraints
  - 2.5.7 Synthesis: Actions as Living Intentions

### Integration Points
- Links to LCTs (actions recorded in entity footprints)
- Links to Roles (determine permissions within actions)
- Links to MRH (defines relevant Reference scope)
- Links to ATP/ADP (Resources consumed/generated)
- Links to T3/V3 (trust impact from Request-Result alignment)

## Implementation Notes
The text should maintain the manifesto energy of the current Part 2 while introducing this technical framework. Focus on the vision: actions that carry intent, learn from outcomes, and create natural governance.

## Risk Assessment
Low risk - This addition enhances understanding without modifying existing concepts. It provides the missing "how" that connects the "what" of Web4's components.