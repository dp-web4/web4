# Web4 and Standard Credentials

### How Web4 interoperates with eIDAS/EUDI, W3C Verifiable Credentials, and OpenID — and what it adds that they don't have

**Version 1.0 — June 2026**
**Metalinxx Inc. / the Web4 project** — https://github.com/dp-web4/web4

---

## Executive summary

A frequent and fair question about Web4: *the world already has X.509, OpenID, W3C Verifiable Credentials, and now the EU Digital Identity Wallet — why another identity system, and does Web4 fight them or work with them?*

The short answer is both simpler and more interesting than "another identity system":

1. **Web4 speaks the standards.** A Web4 entity can issue and verify W3C-style Verifiable Credentials in the formats the EUDI wallet ecosystem consumes (SD-JWT-VC over OpenID4VCI/VP). This is implemented and running today: a live Web4 community hub issues selectively-disclosable membership credentials to standard wallet flows, signed by an Ed25519 key any standards-based verifier can check.

2. **Web4 is not, at its core, a credential system.** Credentials are *point-in-time assertions* — "issuer I said claim C about subject S at time T." Web4 models something credentials structurally cannot: **accumulated, witnessed, contextual relationships** — presence that builds over time, trust that is earned per-context rather than asserted globally, and accountability that has an economic cost. A credential is a *photograph*; Web4 maintains the *living subject*. The bridge between them is deliberate and lossy in one direction only: Web4 can always flatten its rich state into a standard credential; a credential cannot be inflated into relationship history.

3. **The two compose.** The right deployment is not either/or. Web4 communities use credentials as their *interface to the existing world* — membership in your phone's wallet, attestations any verifier can check — while keeping the *living trust fabric* native. Conversely, standard credentials plug into Web4 as recognized evidence: an accredited institution's credential is an anchor a Web4 community can ground its admission policy on.

This paper walks through the existing credential stack, shows precisely where Web4 plugs into it (with the implementation status of each touchpoint), and then details the capabilities Web4 adds that have no equivalent in the standards — with honest notes on what is built, what is planned, and what is hard.

---

## 1. The credential stack today

Four generations of identity infrastructure are in active use, each solving a real problem and each inheriting a structural ceiling.

### 1.1 X.509 / PKI (1988–)
The root of it all: a certificate authority signs a binding between a name and a public key. It secures the web (TLS) and code signing.
**Ceiling:** trust is *hierarchical and binary*. You trust the CA or you don't; the certificate is valid or it isn't. There is no notion of *what for*, *how much*, or *based on what history*. Revocation remains operationally painful (CRLs, OCSP). The subject is passive — certificates say nothing the CA didn't put there.

### 1.2 OAuth / OpenID Connect (2007–)
Federated login: "sign in with Google." An identity provider vouches for you in real time, per session.
**Ceiling:** the identity provider is *in the loop for every transaction* — it sees where you log in, can deny you, and is a single point of failure and surveillance. Your "identity" is an account in someone's database; you possess none of it.

### 1.3 W3C Verifiable Credentials + DIDs (2019–)
A genuine architectural advance: the **issuer–holder–verifier triangle**. The issuer signs a credential; the *holder* stores it and presents it; the verifier checks the issuer's signature without calling the issuer. Decentralized Identifiers (DIDs) let subjects control their identifiers. Selective disclosure (notably **SD-JWT**, where individual claims are salted-hashed so the holder reveals only chosen ones) adds privacy.
**Ceiling:** the trust model is still *issuer-reputation, point-in-time*. A VC is exactly as good as your out-of-band trust in its issuer, frozen at issuance. Nothing in the format accumulates, contextualizes, or prices trust. Revocation and freshness remain bolt-ons. And the ecosystem's hard problem — *which issuers should anyone trust?* — is delegated to "trusted lists" maintained by governance processes outside the technology.

### 1.4 eIDAS 2.0 / the EUDI Wallet (2024–)
The EU regulation operationalizes the VC triangle at state scale: every member state must offer citizens a digital identity wallet; specified formats (SD-JWT-VC, mDoc) and protocols (**OpenID4VCI** for issuance, **OpenID4VP** for presentation) make wallets, issuers, and verifiers interoperable; state-anchored trusted lists answer the "which issuers" question by fiat.
**Ceiling:** the same VC ceiling, plus the trust list is *political infrastructure* — superbly credible for government-anchored claims (legal identity, diplomas, licenses), and structurally silent about everything underneath: communities, collaborations, working relationships, earned reputation, machine agents. The EUDI wallet can prove you are a licensed physician; it has no vocabulary for *"this person has been a reliable contributor to this community for two years, as witnessed by its members."*

### The common ceiling, stated once

Every layer of the stack shares one shape: **a trusted third party asserts a static claim, and verification means checking that assertion's signature.** What none of them model:

- **History** — relationships that accumulate evidence over time
- **Context** — trust that differs by domain ("trusted as a surgeon, unknown as a driver")
- **Reciprocity** — both sides of a relationship witnessing it
- **Cost** — nothing economically prevents bulk assertion, spam, or reputation farming
- **Liveness** — whether the subject is *present and participating now*, vs. was credentialed once

These are not flaws to fix in the formats. They are scope decisions — credentials are *portable assertions*, optimized for exactly that. The gap is what Web4 exists to fill.

---

## 2. How Web4 interoperates — concretely, today

Web4's foundation is the **LCT (Linked Context Token)**: a cryptographic presence token bound to an entity (person, AI agent, organization, device, role), holding an Ed25519 keypair, accumulating witnessed relationships. Everything below maps LCT-world onto credential-world.

| Standards concept | Web4 equivalent | Bridge (status) |
|---|---|---|
| DID (decentralized identifier) | LCT identity | `did:web4` / `did:web` face over an LCT (**built**) |
| VC issuer | Any LCT — typically a *society* (community hub) or a person | Hub + hestia issuance (**built, live**) |
| SD-JWT-VC credential | A signed, flattened *projection* of Web4 attestation state | `web4-core::sd_jwt_vc` (**built**, IETF SD-JWT/SD-JWT-VC drafts) |
| OpenID4VCI (issuance protocol) | Wallet pulls a credential from a hub/person | `web4-core::oid4vc` + live hub endpoint (**built, live**) |
| OpenID4VP (presentation) | Verifier requests + checks a presentation | Protocol core (**built**); hub-as-verifier wiring (planned) |
| Holder binding (`cnf`) | The member's own key, proven at issuance | (**built, live**) |
| Trusted list | Anchors a community's law recognizes | Policy-layer design (planned); EU-list conformance (governance track) |

### 2.1 A worked example, running now

A live Web4 community hub (a "society" — it has members, roles, a signed charter, an append-only witnessed ledger, and machine-readable law) issues membership credentials:

1. A member — over an end-to-end-encrypted, authenticated channel to their hub — requests a credential offer. The hub mints a single-use, short-lived pre-authorized code bound to that member's LCT.
2. The member's wallet redeems the code at the hub's standard OID4VCI endpoint (`/.well-known/openid-credential-issuer` advertises it), supplying a **holder-key proof** so the credential is bound to the wallet's key.
3. The hub issues an **SD-JWT-VC** (`vct: web4:hub:membership`), signed by the society's sovereign key: membership claims in clear; name and skills as **selectively-disclosable** claims. The member can prove membership while revealing nothing else — or reveal their skill profile when that's the point.
4. Any standards-based verifier checks the issuer signature against the hub's published key and the holder binding against the presenter — *no Web4 software required.*

The issuance is **lossy by design**. Inside the hub, that membership is a living thing: ledger-witnessed admission, skill declarations, role assignments, channel activity, multi-device assurance. The credential is a faithful snapshot of selected facts at issuance — the *projection* of rich state into a portable, standards-readable artifact. That is the correct direction of flow: project out freely, never pretend a snapshot is the living state.

### 2.2 Personal-scale issuance

The same machinery runs at person scale: an individual's Web4 agent (the *hestia* daemon — a personal vault + identity service) mounts the same issuance endpoints, so a **person** can issue credentials about their own context: "this AI agent is authorized to act for me in scope S," "this device is part of my constellation." This matters because the EUDI world makes issuers institutional almost by definition; Web4 makes *every entity* a first-class potential issuer, with the same formats.

### 2.3 Multi-device assurance, exported

Web4 members can register a **constellation** — multiple devices, each with its own key, co-signing as one identity. The hub verifies co-signatures and *derives* (never takes on faith) an assurance tier: single-device, multi-device, and upward. That tier is exactly the kind of claim worth exporting: a credential carrying `assurance_level: multi_device` tells a standards-world verifier something the VC stack itself has no way to establish — that the subject's identity is anchored in more than one piece of hardware. (The EUDI wallet's own "high assurance" levels are issuer-asserted from enrollment ceremony; Web4's are continuously re-derivable from live key behavior.)

### 2.4 What flows the other way

Interop is bidirectional. A standard credential presented *to* a Web4 community becomes **evidence its law can act on**: "admit applicants who present a valid credential from issuer X" — where X might be another Web4 hub (cross-community membership portability) or a conventional institution (an accredited university, a state registry). The credential's issuer functions as an **anchor**: an entity the community already trusts, letting trust extend to strangers who carry its signature. Web4 does not need to re-invent the institutional trust the credential world already encodes; it consumes it as one input among several.

---

## 3. What Web4 adds that credentials don't have

Each capability below has no structural equivalent in X.509/OIDC/VC/EUDI — not because those systems are badly designed, but because their scope ends at portable assertion.

### 3.1 Presence, not just assertion
An LCT is not an identifier *about* an entity; it is the entity's accumulating footprint: relationships formed, actions witnessed, roles inhabited. Identity grows from participation. In credential terms: imagine if your diploma got *more verifiable* every time you practiced your profession, because practice itself left cryptographic witnesses. That inversion — **evidence accumulates instead of decaying** — is Web4's root primitive. A credential's evidentiary value is maximal the moment it's signed and decays as the world drifts from the snapshot; witnessed presence moves the other way.

### 3.2 Contextual, graded trust (T3/V3 × MRH)
Web4 trust is a **tensor, not a bit**. The T3 tensor scores capability dimensions (talent, training, temperament); V3 scores value delivered (valuation, veracity, validity) — and critically, every score is **contextualized** by the MRH (Markov Relevancy Horizon): the bounded context in which it was earned. "Trusted 0.9 for ML evaluation within this research community" is a different fact from "trusted 0.3 for production deployment," and both attach to the same entity without contradiction. The credential stack's validity model — `valid | expired | revoked` — cannot express either the gradation or the context-dependence. Verifiers in Web4 don't ask "is this credential valid?"; they ask "what is this entity's earned standing *for this purpose*?"

### 3.3 Witnessing: verification by relationship
In the VC triangle, verification is signature-checking against one issuer. In Web4, attestations are **witnessed** — observed and counter-signed by other entities whose own standing is on the line — and witnessing accumulates into a web of cross-referenced evidence. Trust derives from *the structure of accumulated relationships* rather than from any single authority's say-so. The practical consequence: compromising one signer forges one signature, but it cannot retroactively manufacture a witnessed history, because that history lives in *other entities'* ledgers too.

### 3.4 Societies: governance attached to the trust fabric
A Web4 community is a **society** — it has a charter, machine-readable **law** (evaluated by a policy engine over every consequential action: who may join, what each role may read, what requires escalation to a human sovereign), an append-only witnessed **ledger**, and accountable **roles**. Compare the credential-world issuer: an opaque organization whose internal policy is invisible and unenforceable. A Web4 hub's issuance policy *is inspectable law*; its issuance acts *are ledger-witnessed events*. When a hub signs a membership credential, the receiving verifier can know not just *that* the hub signed, but *under what standing rules*, with the rule evaluation itself on the record. Issuers stop being black boxes.

### 3.5 Confidential, consent-first relationships
Web4 member↔community traffic runs over end-to-end encrypted channels (X25519/ChaCha20-Poly1305, keys bound to the LCTs themselves) — membership interaction is never in the clear, and a member's queries are between member and hub. Member↔member connection is **double-consent**: discovery returns candidates, but a connection forms only when both parties agree, at which point the hub hands each side the other's key and steps out of the path. Contrast OIDC (the provider sees every login) and even wallet presentations (the verifier learns whatever the credential reveals, and presentations are typically unilateral). Web4's default is that *relationships are formed by mutual consent and conducted privately* — the infrastructure broker provably cannot read what it brokers.

### 3.6 Accountability economics (ATP/ADP)
Web4 prices action. Consequential acts dischargeable energy tokens (ATP→ADP, a bio-inspired cycle), recharged through delivered value. The effect is structural spam- and Sybil-resistance: asserting, witnessing, and querying at scale *costs something*, and the cost is tied to standing rather than to capital alone. The credential stack has no native answer to bulk-issuance abuse or reputation farming — issuance is free, so defense lives entirely in the trusted-list gate. Web4's defense is metabolic: an entity that only extracts and never delivers runs out of capacity to act.

### 3.7 AI agents as first-class citizens
The credential stack assumes human subjects with legal identities; agent identity is an afterthought (API keys, OAuth service accounts — i.e., the password era). Web4 was designed agent-native from the start: an AI agent holds an LCT, earns contextual trust the same way a person does, operates under delegation chains that are themselves witnessed ("agent A acts for person P in scope S"), and can be governed by society law. As agentic systems multiply, *this* — not human login — is where the identity gap is widest, and it is precisely where point-in-time credentials are weakest: an agent's trustworthiness is almost entirely a question of *track record in context*, the thing Web4 measures and credentials cannot.

### 3.8 The lossy bridge as a feature
Because Web4 state strictly contains credential state, the bridge runs lossy in one safe direction: **project rich state out** into any standard format the world consumes, on demand, fresh each time. The reverse — treating a credential as if it were relationship history — is impossible by construction, and that asymmetry is correct. A Web4 deployment never has to choose between interoperability and depth: it exports interoperability and keeps depth.

---

## 4. Deployment patterns

**A community (the pilot case).** A community runs a hub. Members join through consent-gated admission, declare skills in their own words, discover each other semantically, and connect by mutual approval — all over encrypted channels, all under the community's own law. Each member's *membership card* is a standard SD-JWT-VC in any compliant wallet; partner organizations verify it with off-the-shelf tooling. The community gets living trust internally and standards compliance externally, from one substrate.

**A federation of communities.** Hubs recognize each other's credentials as admission anchors: membership in good standing at hub A becomes portable evidence at hub B, with B's law deciding what it grants. This is the trusted-list pattern — but bottom-up, peer-negotiated, and revocable per-relationship rather than fiat-administered.

**An enterprise.** An organization consumes standard credentials at its boundary (employee onboarding, partner verification — including EUDI-wallet credentials as those roll out) while running Web4-native authorization inside: roles as inhabited LCT relationships, delegation chains for both people and AI agents, policy as law, and hardware-anchored provenance on critical artifacts.

**A person.** An individual's wallet holds conventional credentials *and* their Web4 presence: their personal agent issues scoped authorizations to their AI tools, their devices form an assurance constellation, and their accumulated standing in the communities they belong to travels with them — exportable as a credential whenever a verifier needs the snapshot.

---

## 5. Honest limits and roadmap

- **EU trusted-list membership is governance, not code.** Web4 credentials are *formatically* conformant (parse, verify, selectively disclose with standard tooling) but Web4 issuers are not yet on official eIDAS trust registries — that's a legal/conformance track, deliberately separated from the technology track so neither blocks the other.
- **Hub-as-verifier (OID4VP) wiring is the next build step** — protocol core exists; the policy question (which anchors a community recognizes, expressed in its law) deserves design care, not haste.
- **Issuance signing currently requires the society's key locally**; remote-vault signing for issuance is a known follow-up with a clear path.
- **Trust-tensor accrual is the deepest layer and the least finished**: the T3/V3 schema exists, witnessed evidence accumulates today, but closed-loop trust computation feeding back into discovery and policy is active development. We say "measured trust" only where measurement actually closes the loop.
- **Format breadth**: SD-JWT-VC is implemented; mDoc/mDL (the other EUDI format) is not yet.

---

## 6. Summary table

| | X.509 / PKI | OIDC | W3C VC / EUDI | **Web4** |
|---|---|---|---|---|
| Trust model | CA hierarchy | provider session | issuer assertion | **witnessed relationships** |
| Trust value | binary | binary | binary + expiry | **graded tensor, per-context** |
| History | none | logs (provider's) | none | **native, append-only, witnessed** |
| Subject role | passive | account | holder of snapshots | **accumulating presence** |
| Issuer accountability | audits | terms of service | trusted list | **inspectable law + witnessed ledger** |
| Privacy of use | n/a | provider sees all | selective disclosure | **selective disclosure + E2E channels + double-consent** |
| Abuse economics | none | rate limits | none | **metabolic cost (ATP/ADP)** |
| AI agents | none | service accounts | out of scope | **first-class, delegated, trust-accruing** |
| Interop with the others | — | — | — | **speaks VC/OID4VC natively (live)** |

---

## 7. Pointers

- **Web4 standard + reference implementation:** https://github.com/dp-web4/web4 (`web4-standard/` for specs; `web4-core/` for the credential bridge: `sd_jwt_vc`, `oid4vc`; `hub/` for the reference community hub)
- **Formats/protocols implemented:** IETF SD-JWT + SD-JWT-VC (drafts), OpenID4VCI (pre-authorized code), OpenID4VP (protocol core), Ed25519/EdDSA JWS
- **The whitepaper series:** `whitepaper/` in the repo for Web4's full conceptual foundation (LCT, T3/V3, MRH, ATP/ADP, societies, witnessing)

*Trust accrues by relating, not by declaration. Credentials carry the declaration; Web4 carries the relating — and each is better with the other.*
