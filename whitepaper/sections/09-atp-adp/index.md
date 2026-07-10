# ATP/ADP: The Value Cycle

**The question it answers: how does value flow back to contribution?**

The final term of the equation closes the loop. With presence established (LCT), capability measured (T3/V3), and context bounded (MRH), one question remains: how does the system *allocate* — energy, attention, resources — so that contribution is rewarded and waste is not? Web4's answer is the **ATP/ADP cycle**, named for the molecule that carries energy in every living cell.

## The cycle

**Allocation Transfer Packets** exist in two states, forever cycling:

- **ATP (charged)** — allocation ready to fuel work
- **ADP (discharged)** — allocation spent, carrying the record of what it was spent on, awaiting recognition

Work *discharges* ATP into ADP. Witnessed, recognized contribution *recharges* ADP back into ATP. The tokens are **semi-fungible**: units are equivalent as energy, but each carries its history — what was attempted, by whom, to what result — context that matters when value is assessed.

Recognition is not automatic. Whether discharged work recharges depends on the *receivers* of the value attesting it through the V3 lens (was it valuable? was it accurate? did it arrive?). That is the equation's structure made operational: the value cycle runs *through* the trust layer, not beside it.

## Why a metabolism, not a market

The deliberate contrast is with mining and staking. Proof-of-work rewards burning energy on puzzles; proof-of-stake rewards already having tokens. Both decouple reward from *usefulness*. The ATP/ADP cycle couples them by construction:

- **You cannot accumulate allocation without contributing** — recharge requires witnessed, recognized value delivery. There is no "early holder" position to speculate from.
- **You cannot fake contribution** — the discharge record and its witnesses are part of the trust fabric; gaming attempts damage the T3/V3 tensors that gate future allocation.
- **Hoarding is self-limiting** — allocation that never discharges does no work and earns no recognition; the system favors flow over accumulation, as metabolisms do.

The design intent is sometimes summarized as *anti-Ponzi*: value in the system tracks work performed for identifiable beneficiaries, not the recruitment of later participants.

## Feedback, not foundation — and maturity, honestly

Two clarifications this paper owes the reader. First, ATP/ADP is **the feedback layer, not the foundation**: it presupposes every prior term of the equation, and nothing in presence, trust, or context *depends on* it — which is why it is the last term, not the first. Second, it is the **least-implemented core component**: the cycle's mechanics have been validated in protocol-development work, but a public reference implementation is still pending. The specification is normative; the running code, as of this writing, is not yet public.

*Normative reference: [`core-spec/atp-adp-cycle.md`](https://github.com/dp-web4/web4/blob/main/web4-standard/core-spec/atp-adp-cycle.md).*
