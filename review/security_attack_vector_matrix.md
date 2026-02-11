# External Red-Team Attack Vector Matrix (Web4)

This matrix proposes external test scenarios mapped to internal attack themes, with emphasis on realistic exploit chains.

| ID | Vector | Internal Coverage Theme | External Test Expansion | Expected Failure Signal | Priority |
|----|--------|-------------------------|-------------------------|-------------------------|----------|
| RT-01 | Adaptive witness cartel | Witness diversity / collusion tracks | Low-and-slow collusion with role rotation and staggered attestations | Undetected trust inflation over time | P0 |
| RT-02 | ROI-positive Sybil economy | Identity stake / ATP economics | Budget-constrained attacker simulation with market-like ATP assumptions | Net-positive attacker returns | P0 |
| RT-03 | Challenge protocol flooding | Challenge-response tracks | Automated challenge spam + evidence laundering + timeout gaming | Trust penalties fail to deter abuse | P1 |
| RT-04 | Trust-to-admin pivot chain | Authorization + reputation | Use reputation foothold to escalate delegated capabilities | Unauthorized high-impact action | P0 |
| RT-05 | Replay + ordering drift | Checkpoint/timing/consensus tracks | Partitioned network with clock skew and delayed replay | Conflicting state acceptance | P0 |
| RT-06 | Semantic policy confusion | Policy confusion tracks | Intentionally ambiguous policy + stale doc alignment attacks | Divergent enforcement decisions | P1 |
| RT-07 | MCP relay/tool abuse chain | MCP relay injection tracks | Prompt-injection into tool invocation with privilege boundary tests | Tool executes out-of-policy action | P1 |
| RT-08 | CI/CD supply-chain compromise | Dependency confusion / build tracks | Poisoned dependency + release pipeline tamper simulation | Signed/approved malicious artifact path | P0 |
| RT-09 | Recovery quorum manipulation | Recovery/quorum tracks | Social + technical pressure campaign during identity recovery | Incorrect account recovery approval | P1 |
| RT-10 | V3 value laundering | Value tensor manipulation tracks | Multi-entity circular value creation with delayed settlement | Artificially elevated value trust | P1 |
| RT-11 | Side-channel extraction | Timing/error side-channel tracks | Differential timing/error probing at scale | Sensitive state inference | P2 |
| RT-12 | Long-con federation infiltration | Long-con trust tracks | Multi-week benign behavior then coordinated betrayal | Late-stage high blast-radius compromise | P2 |

## Notes
- P0 vectors should be included in wave 1.
- Each vector should define: attacker budget, required access, assumed defenses, and explicit success criteria.
- Findings should reference violated invariants: identity integrity, trust integrity, ATP conservation, authorization correctness, federation consistency.

