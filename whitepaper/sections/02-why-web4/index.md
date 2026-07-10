# Why Web4

AI agents now make purchases, execute code, and take decisions on behalf of the humans and organizations they serve. The internet they operate on has no native way to answer the two questions this raises:

1. **How do I know an agent will act appropriately in a given context, *before* it acts?** Today's answers: trust the platform that hosts it (Web2), or trust whoever holds the keys (Web3). Neither says anything about behavioral capability or contextual fit.
2. **How do I prove what an agent actually did, *after* the fact, without depending on a single trusted intermediary?** Today's answers: platform logs (revocable, manipulable) or blockchain records (limited expressivity, largely blind to off-chain action).

These are not future problems. They are the current, unsolved problems of agent delegation, agent-tool authorization, and any system where multiple agents — human or AI — must coordinate without a single referee.

The web arrived in layers, each solving the problem the previous one left open. **Web1** gave us access. **Web2** gave us participation, at the price of platform monopoly. **Web3** gave us ownership, at the price of token speculation. The problem now open is **trust between diverse intelligences** — and Web4's wager is that solving it requires trust to be a **first-class primitive of the protocol layer**: earned through witnessed interaction, expressed as verifiable structure, and inspectable by anyone. Not granted by a platform. Not purchased with a token.

The mechanism for that wager is **verifiable presence**. If every participating entity — human, AI, organization, role, task, or device — has a cryptographically anchored, non-transferable footprint that accumulates witnessed history, then trust can be *computed from the record* rather than *declared by an authority*. Everything in Web4 builds from that single move.

This paper is a technical introduction to the Web4 standard. It is deliberately scoped: it explains the **concepts** — what each mechanism is, why it exists, and how the pieces fit — and leaves specifications, schemas, and code to the [normative standard](https://github.com/dp-web4/web4/tree/main/web4-standard) it describes. The entire architecture can be stated in one line, and that line is where we begin.
