# Conclusion

> **Status (2026-04-29)**: Web4 is a research-stage project. Some primitives are shipped (`web4-core` 0.1.1 + `web4-trust-core` 0.1.1 on crates.io and PyPI; AttestationEnvelope; agent-commerce-delegation demo with 166 passing tests). Many more are operational in the Hardbound CLI as protocol-validation work but not yet in public packages. Some remain specification. The Executive Summary draws the explicit lines.

## What this whitepaper has covered

The architecture of Web4 as proposed:

- **Linked Context Tokens (LCTs)** — non-transferable presence primitives, cryptographically anchored, with multi-device binding and parent/child lineage
- **T3 / V3 Tensors** — multi-dimensional capability and contribution records, fractally extensible via RDF sub-graphs, bound to entity-role pairs
- **ATP / ADP cycle** — value-creation accounting modeled on biological energy metabolism, with formal Sybil-resistance proofs and game-theoretic cooperation guarantees in the Hardbound implementation
- **Markov Relevancy Horizon (MRH)** — contextual scoping as a typed RDF graph with trust-propagation through path products
- **R6 / R7 Action Framework** — the grammar of every Web4 action (Rules / Role / Request / Reference / Resource → Result, plus Reputation as first-class output)
- **Coherence framework** — `C × S × Φ × R` as a measurable property of stable identity
- **Dictionary entities** — living semantic bridges with forward/reverse translation, ATP-staked confidence, drift detection
- **Heterogeneous identity / constellation pattern** — multi-factor witnessing as the structural answer to vendor-gating concerns; full design note at [`docs/specs/heterogeneous-identity.md`](https://github.com/dp-web4/web4/blob/main/docs/specs/heterogeneous-identity.md)
- **AttestationEnvelope** — unified hardware-trust primitive with TPM2 / FIDO2 / Secure Enclave / software anchors

The architecture's load-bearing claim: trust can be a first-class primitive of the protocol layer — earned through witnessed contribution, expressed through a typed RDF ontology, anchored cryptographically — and this provides a useful substrate for human–AI collaboration that current architectures don't.

Whether that claim holds will be answered by what gets built on top of these primitives, by whom, and in what time horizon. The first implementations exist; sociotechnical-scale validation requires real adoption.

## What's actually different from prior framings

Some specific positions Web4 takes that distinguish it from adjacent work:

- **Identity is a constellation, not a credential.** Web4 entities don't have *an* LCT — they have a graph of mutually-witnessing factors (host LCT + hardware key + session token + software identity + peer attestations + ledger anchor). No single factor is necessary or sufficient. Resilience scales with constellation size and diversity. This is the structural answer to "what stops a hardware vendor from gating LCT access?" — you don't depend on one factor.
- **ATP comes from measurement, not creation.** First ATP at the bottom of the chain is reified from observation of resources that already exist (compute, network, storage, attention). Not minted from nothing; not granted by an outside authority. Existence is witnessed; ATP follows from witnessed existence.
- **Trust as routing primitive.** Trust scores in Web4 don't just describe — they actively shape attention allocation, ATP distribution, role binding, and graph traversal in the codebase. The earlier framing of "trust as gravity" was decorative; the routing is real.
- **Witness ≠ vouch. Signature ≠ vouch.** A witness statement says "I observed X at time T." A signature says "this observation claim is intact." Neither asserts endorsement. Multi-factor identity rides on the *consistency* between independent witnesses, not on any one endorsing the others.
- **Salience-aware everything.** Fingerprints, publishing decisions, audit alarms — all should hash over what's *salient* per kind, not over whatever the source happens to expose. The principle generalizes from identity into how the protocol records and propagates state.

## What we're asking for

This whitepaper is a research artifact, not a sales document. Useful engagement at any of these depths:

1. **Run the published packages.** `cargo add web4-core` or `pip install web4-core`. The first README example runs in 60 seconds.
2. **Try the demo.** Clone [`dp-web4/web4`](https://github.com/dp-web4/web4), open `/demo`, run the agent authorization tests. 166 of them should pass.
3. **Read the spec corpus.** [`web4-standard/core-spec/`](https://github.com/dp-web4/web4/tree/main/web4-standard/core-spec) is the canonical specification. R6 / R7, AttestationEnvelope, MRH tensors, T3/V3 ontology — all formalized.
4. **Challenge the design.** What are we getting wrong? Where does the framing carve at the wrong joint? Where is an existing standard (DIDs, VCs, MCP authorization, OAuth, OpenID Connect) already solving the same problem better?
5. **Build something.** Implement a piece. Validate or refute a specification claim. Open a PR or an issue.

## What we're being honest about

The whitepaper has been around since 2024 in various forms. Earlier versions of it framed Web4 as a "revolution" and "the future of the internet." The work itself is more grounded than that framing suggested. As of 2026-04-29, the implementation reality:

- Working code exists for the foundational primitives and a non-trivial commerce demo
- The cosmology around the engineering ("trust as gravity," "memory as living tissue") was rhetoric. The engineering doesn't depend on it
- Many vision components remain specification, not deployed code. The Executive Summary names which is which
- Adoption is unproven. There is no production deployment. There are no enterprise users. There are no other implementations of the spec at this time

The strongest single signal of how the work approaches its own claims is [STATUS.md](https://github.com/dp-web4/web4/blob/main/STATUS.md) — read it before judging this whitepaper's claims. The strongest signal of the development cadence is the v0.1.0 → v0.1.1 same-day catch-and-fix narrative in [`docs/proof/PUBLISHED.md`](https://github.com/dp-web4/web4/blob/main/docs/proof/PUBLISHED.md): a publish defect was caught by clean-install verification, the package was yanked, the fix shipped, and the discipline rule that would have prevented it pre-publish was preserved as cross-machine fleet memory — all on the same calendar day. That loop — detection → correction → preserved learning — is the asset.

## Contact

[dp@metalinxx.io](mailto:dp@metalinxx.io). Issues and pull requests at [github.com/dp-web4/web4](https://github.com/dp-web4/web4).
