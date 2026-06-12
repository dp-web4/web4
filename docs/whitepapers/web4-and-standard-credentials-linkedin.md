# Your credentials are photographs. Your trust is alive.

*(LinkedIn article version of the whitepaper "Web4 and Standard Credentials" — full paper in the repo, link at the end.)*

---

Europe just made digital identity real. Under eIDAS 2.0, every EU member state is rolling out a Digital Identity Wallet — your diploma, your driver's license, your professional registration, cryptographically signed, in your phone, verifiable by anyone in seconds.

This is genuinely good infrastructure. And it shares one quiet assumption with every identity system we've built since the 1980s — an assumption worth examining, because the next decade is going to break it.

**Every credential is a photograph.**

An issuer looked at you once, signed a statement — "this person graduated," "this person is licensed" — and handed you the snapshot. Verification means checking the signature on the photo. X.509 certificates work this way. "Sign in with Google" works this way. W3C Verifiable Credentials and the EUDI wallet work this way, with real improvements: *you* hold the photo now, and you can show just a corner of it instead of the whole thing (selective disclosure — a real privacy win).

But notice what no photograph can tell you:

- Whether the subject is **still** who the photo says — not revoked-or-not, but *actively present, participating, accountable*
- What they're trusted **for** — a credential is valid or invalid; it can't say "excellent at evaluation methodology, untested in production systems"
- What **happened since** — relationships formed, work delivered, trust earned or burned
- What it **costs to lie at scale** — issuing assertions is free, so the only defense is gatekeeping who may issue

These aren't design flaws. Credentials are *optimized* to be portable snapshots, and they're excellent at it. The gap is everything a snapshot structurally cannot hold — and that gap is exactly where the most important trust questions now live. Ask anyone trying to answer: *should this AI agent be allowed to act on my behalf?* A photograph of an agent tells you almost nothing. Its **track record in context** tells you almost everything.

**That's the layer we've been building.** We call it Web4.

The core inversion is simple to state: identity shouldn't be something asserted about you once — it should be something that **accumulates** as you participate. In Web4, every entity (person, organization, AI agent, device) holds a cryptographic presence token whose value grows from *witnessed relationships*: actions observed and counter-signed by other entities whose own reputations are on the line. Trust isn't a bit, it's a **graded tensor, scoped to context** — trusted *this much*, *for this*, *based on that history*. Communities run as "societies" with machine-readable law: who may join, what each role may do, what needs a human's sign-off — and the rules are inspectable, with every consequential act witnessed on an append-only ledger. Acting at scale has a metabolic cost, so spam and reputation-farming aren't free. And AI agents are first-class citizens: they earn standing the same way people do, under delegation chains that are themselves witnessed.

A photograph decays from the moment it's taken. Witnessed presence appreciates.

**Now — does this compete with the credential world? No. It feeds it.**

Here's the part I'm most pleased about, because it's not a roadmap slide. It runs today.

A Web4 community hub — a small Rust daemon any community can operate — maintains the living layer: consent-gated membership, encrypted member channels, skill discovery, mutual-approval introductions, multi-device identity assurance. And when a member needs to prove something to the *outside* world, the hub **projects the living state into a standard credential**: a selectively-disclosable SD-JWT-VC, delivered over OpenID4VCI — the exact formats and protocols the EUDI wallet ecosystem speaks. Any standards-based verifier can check it. No Web4 software required on their side.

We call this the **lossy bridge**, and the loss runs in only one safe direction. Rich, living state can always be flattened into a portable snapshot — freshly, on demand. A snapshot can never be inflated back into a history. So you never choose between interoperability and depth: you export interoperability and keep depth.

It composes the other way too. When someone presents a conventional credential *to* a Web4 community — a university degree, a state license, membership in a partner community — that credential becomes an **anchor**: institutional trust the community's own law can build on. We didn't reinvent the trust the credential world already encodes. We consume it, and we add the layer it never had.

**Honest status, because trust content should model what it preaches:** the formats verify with standard tooling today, and a live pilot community issues real membership credentials as I write this. What's *not* done: Web4 issuers aren't on official EU trust registries (that's a governance process, not a code problem), the verifier-side wiring is the next build, and the deepest layer — trust tensors feeding back into discovery and policy in a closed loop — is active development, not a finished claim.

The one-line summary I keep coming back to:

**Credentials carry the declaration. Web4 carries the relating. Each is better with the other.**

If you're building communities, agent systems, or anything where "is this credential valid?" is no longer the question you actually need answered — the full whitepaper goes deeper on all of this, including the architecture and the limits: **github.com/dp-web4/web4** (`docs/whitepapers/web4-and-standard-credentials.md`).

And if you're working on EUDI wallets, verifiable credentials, or agent identity and any of this resonates (or provokes) — my inbox is open. Trust accrues by relating, not by declaration. That goes for ideas too.

---

*#DigitalIdentity #VerifiableCredentials #eIDAS #EUDI #SSI #AIAgents #Web4 #Trust*
