# ATP/ADP: The Value Cycle

**The question it answers: how does value flow back to contribution?**

The final term of the equation closes the loop. With presence established (LCT), capability measured (T3/V3), and context bounded (MRH), one question remains: how does the system *allocate* — energy, attention, compute, resources — so that contribution is rewarded and waste is not? Web4's answer is the **ATP/ADP cycle**, named for the molecule that carries energy in every living cell.

## The cycle

**Allocation Transfer Packets** exist in two states, forever cycling:

- **ATP (charged)** — allocation ready to fuel work
- **ADP (Allocation Discharge Packet)** — allocation spent, carrying the record of what it was spent on, awaiting recognition

Work *discharges* ATP into ADP. Witnessed, recognized contribution *recharges* ADP back into ATP. The tokens are **semi-fungible**: units are equivalent as allocation, but each carries its history — what was attempted, by whom, to what result — context that matters when value is assessed.

The mechanics are deliberately conservative. Societies **mint** the supply (in the discharged ADP state) and hold it in governed pools; the cycle obeys a strict **conservation invariant** — total supply always equals charged plus discharged, and every transfer balances to the unit, fees recycled to the pool rather than destroyed. The one sanctioned exception is **slashing**: witnessed, evidence-backed destruction for violations — the economic analogue of the tensor's asymmetric accrual, and equally deliberate.

Two rules weld the cycle into everything that came before it. First, **discharge happens only through the R6 action grammar**: spending allocation *is* transacting — every R6 Request carries an `atpStake`, locked in escrow at validation and settled atomically with the action's costs, so allocation can never move without a governed, witnessed act attached. Second, **recharge requires proof**: charging ADP back to ATP demands producer authorization under society law plus a cryptographic value proof — recognition is not automatic. Whether discharged work recharges depends on the *receivers* of the value attesting it through the V3 lens (was it valuable? was it accurate? did it arrive?). That is the equation's structure made operational: the value cycle runs *through* the trust layer, not beside it.

And the weld runs both directions: every ATP event feeds the tensors — recognized charging raises Training and Valuation; slashing cuts Temperament and Veracity. An entity's economic record and its trust record are one record, viewed through two terms of the equation. (An LCT may even surface its allocation position as an `energy_balance` sub-dimension of V3 Valuation — capability level 3 expects it — so "does this entity do recognized work?" is a graph query, not an audit.)

## Why a metabolism, not a market

The deliberate contrast is with mining and staking. Proof-of-work rewards burning energy on puzzles; proof-of-stake rewards already having tokens. Both decouple reward from *usefulness*. The ATP/ADP cycle couples them by construction:

- **You cannot accumulate allocation without contributing** — recharge requires witnessed, recognized value delivery. There is no "early holder" position to speculate from.
- **You cannot fake contribution** — the discharge record and its witnesses are part of the trust fabric; gaming attempts damage the T3/V3 tensors that gate future allocation.
- **Hoarding is self-limiting** — allocation that never discharges does no work and earns no recognition, and societies may levy **demurrage**: a maintenance discharge on idle charge, so dormant allocation slowly returns to the pool. The system favors flow over accumulation, as metabolisms do.

The design intent is sometimes summarized as *anti-Ponzi*: value in the system tracks work performed for identifiable beneficiaries, not the recruitment of later participants.

## Feedback, not foundation — and maturity, honestly

Two clarifications this paper owes the reader. First, ATP/ADP is **the feedback layer, not the foundation**: it presupposes every prior term of the equation, and nothing in presence, trust, or context *depends on* it — which is why it is the last term, not the first. Second, its maturity is honestly mixed. The *mechanism* now ships in public: the account model and conservation invariants are implemented in the published `web4-core` crate and the Python SDK, validated against the standard's test vectors. What does not yet exist is a *live economy* — no deployment circulates real allocation at scale, and large-scale economic attack modeling remains open research. The accounting runs; the metabolism it is meant to govern is still ahead.

*Normative reference: [`core-spec/atp-adp-cycle.md`](https://github.com/dp-web4/web4/blob/main/web4-standard/core-spec/atp-adp-cycle.md), with the discharge weld in [`core-spec/r6-framework.md`](https://github.com/dp-web4/web4/blob/main/web4-standard/core-spec/r6-framework.md).*
