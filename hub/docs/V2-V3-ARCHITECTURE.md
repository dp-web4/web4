# Web4 Community Hub — V2-V3 Architecture

**Status:** Working document. Captures the outer-landscape MRH from the 2026-06-07 conversation. Evolves as fractal subsets get worked through.
**Companion to:** `PRD.md` (MVP), `SPRINTS.md` (sprints 0-6 history), `README.md` (current state)
**Date initiated:** 2026-06-07
**Maintained by:** dp + the building entities

---

## Vocabulary note: acts (not mutations)

Hub operations split into **reads** and **acts** — not reads and "mutations." The ledger is append-only; nothing in it ever mutates. Each act is a signed event being witnessed into the chapter's history. Acts append; the derived state (members, role assignments) re-projects from the new ledger tail.

| Surface | Reads | Acts |
|---|---|---|
| CLI | `query`, `status`, `verify-ledger` | `add-member`, `remove-member`, `assign-role`, `record-event`, `declare-skill` |
| REST | `GET /v1/hubs/{id}/state` | `POST /v1/hubs/{id}/events` |
| MCP | `query_chapter`, `list_members`, `find_skill` | `add_member`, `assign_role`, `record_event`, `declare_skill` |

Acts in Hestia mode require an async HTTP roundtrip to the vault — that's what makes "sync CLI acts on Hestia chapters" an open design question, while sync CLI reads remain trivial.

The word "mutation" carries baggage (GraphQL convention, FP anti-pattern connotation) and is technically wrong for an append-only system. "Act" is Web4-native — presence accumulates as witnessed acts.

---

## What this is

The MVP (sprints 0-6) shipped a single-binary chapter-hub that one operator can run end-to-end. This document scopes what V2-V3 turn that into: **open-source community infrastructure that can host millions of members across thousands of chapters, with most operations delegated to AI agents bound by signed hub law, and humans escalated only for key decisions.**

What we're delivering at the long horizon:
- **Building blocks** — primitives others compose with
- **Infrastructure** — deployable substrate that scales
- **Tools** — operator-facing CLIs, UIs, scripts
- **Guidance** — documented patterns + sample hub laws
- **MVP foundation** — a working starting point a community can adopt and evolve

The hub is **generic open-source infrastructure**. Any community willing to operate as a Web4 society can adopt it. Enterprise can license hardbound as an upgrade for hardware-bound identity + production policy enforcement.

The hub is **a law interpreter**, not a policy holder. The Web4 community evolves both the hub itself and the law patterns it interprets, per their needs.

---

## MRH (what this document scopes vs. what's deferred)

### In scope here (outer landscape)
- Load-bearing architectural commitments (the constitutional principles)
- Track structure (where work happens: web4/hub, hestia/, web4-core upstream, community)
- Proposed sprint sequence
- Open design decisions still needing resolution

### Deferred to focused sub-conversations (fractal subsets)
- Individual sprint detail (what gets built in each sprint, week by week)
- Law schema bikeshed (RDF vs YAML vs hybrid)
- Cloud-vendor-specific deployment patterns (one is "platform-agnostic" already — pick a starting target later)
- Reference AI role-filler implementations (community-led, not hub-internal)
- Federation protocol specifics (relevant when 2+ chapters are running)

### Out of scope entirely
- Community-specific governance choices (those go in a chapter's law file, not in hub code)
- Hardbound integration deep-dive (separate licensable layer)
- V4+ (we'll set its MRH when V3 is real and we know what it didn't address)

---

## Load-bearing architectural commitments

These survive every sub-conversation. Every implementation decision is checked against them.

### 1. Law is always signed and auditable, never hardcoded

**Everything in this document follows from this.**

Hub law is a signed structured file (schema TBD — see open questions). The Sovereign Council signs it. The LawOracle role publishes it. The PolicyEntity role evaluates every consequential request against it. The hub binary's job is to **interpret the law**, not to encode policy.

Implications:
- Escalation thresholds: in law, not in code
- Member admission rules: in law, not in code
- AI role delegation rules: in law, not in code
- Role-fill procedures: in law, not in code
- ATP issuance policy: in law, not in code
- Treasury thresholds: in law, not in code

The hub ships with **no default policy**. It ships with **sample law templates** the chapter can adopt by signing. Adopting a template is a Sovereign act, not a configuration default.

This is a constitutional discipline. Transparency is foundational to accountability — every behavior of the chapter traces back to a signed law document any member can read.

### 2. Hestia is the universal Web4 presence (humans + AI)

Hestia is ONE shape: a vault + identity + multi-hub connector + plugin host. It works for:
- **Human users** — vault holds the human's private keys; human signs requests via Hestia
- **AI agents** — vault holds the AI's private keys (when AI is autonomous) OR the AI's signing authority is a *delegation* from a human's Hestia (when AI acts as proxy for a human)

Human → AI delegation is a first-class operation in Hestia: "I authorize agent X to act on my behalf in role Y, with these scope limits, revocable at any time." This makes AI delegation safe AND traceable — every AI action ultimately roots to a human Hestia (or to a chapter-owned AI Hestia, when chapters mature to fully autonomous AI agents).

### 3. The hub is an interpreter, not a policy holder

The hub binary contains:
- Web4 primitives (via web4-core / web4-trust-core)
- Storage backend abstraction + implementations
- Law parsing + validation + interpretation
- Event recording + ledger chain integrity
- MCP HTTP surface + admin UI surface
- AI role-filler runtime (process supervision, ATP accounting, T3 scoring)

The hub binary does NOT contain:
- Any chapter-specific policy
- Any hardcoded escalation thresholds
- Any built-in admission rules
- Any default member behaviors
- Anything that should be a chapter-sovereign choice

### 4. Storage is backend-abstracted from V2 day one

**SHIPPED.** Not retrofitted. The `HubStore`/`ChapterStore` trait + implementations are live:
- `InMemoryBackend` — tests + ephemeral
- `FileBackend` — the MVP file ledger, now one backend behind the trait
- `SqliteBackend` — single-machine production; **SQLCipher-encrypted at rest by default**
- `DynamoDB` backend — opt-in via the `dynamodb` feature
- `PostgresBackend` / `S3CompatibleColdStorage` — multi-tenant + cold-archive tiers still on the roadmap

File-based `ledger.jsonl` from MVP is now one backend among many, and the migration tool (`hub migrate`) to convert MVP chapters to another backend has shipped.

The Ledger trait pattern web4-core already uses for LCT anchoring is the model. Hub's chapter event ledger gets the same shape.

### 5. Multi-Sovereign Council from the start (no single-founder pattern)

**SHIPPED.** Single-Sovereign is a special case of M-of-N where M=N=1. The architecture handles M-of-N natively, and the Sovereign Council data model + propose/sign/threshold flow is live:
- Sovereigns are admitted, retire, get ejected, are member-elected per hub law
- Consequential Sovereign actions require N-of-M signatures (propose → sign → threshold enforcement, with `proposal_ref` linking committed acts back to the proposal for single-pane audit)
- Election as constitutional escape valve when Council fails

The threshold-signing semantics landed in the hub directly (data model + management + admin UI + M-of-N enforcement).

### 6. AI is a first-class role-filler

The Web4 ontology already supports this via `EntityType::AiSoftware` and `EntityType::AiEmbodied`. What V3 adds:
- Operational runtime: hub spawns + supervises AI agents per role
- ATP accounting per AI action (compute costs paid from treasury)
- T3 scoring of AI role performance (decisions appealed, escalation rate, throughput)
- Escalation routing (AI raises, human resolves, recorded in ledger)
- Reference AI role-fillers as separate community-led projects (PolicyEntity, Archivist, Witness, Auditor)

Default human-vs-AI mapping per role:
- **Sovereign**: human-only (constitutional)
- **Law Oracle**: human-authored laws / AI-assisted interpretation
- **Policy Entity**: AI-default, escalation per law
- **Treasurer**: hybrid, threshold in law
- **Administrator**: AI-default, sensitive ops escalate
- **Archivist**: AI-default
- **Citizen**: either (humans AND AI agents can be members)
- **Witness / Auditor**: AI-default

Hub law specifies which roles are AI-filled and on what terms.

### 7. Open-source community infrastructure (no single owner)

AGPL-3.0-or-later. Patent grant per web4 root PATENTS.md. Any community can fork and adopt; no community owns the codebase. Enterprise can license hardbound (private) for hardware-bound identity + production policy enforcement; that's an upgrade path, not a fork.

The community evolves the hub. We ship the foundation; communities adapt + extend + contribute back.

### 8. Secrets in the vault only; access on verified authority + need-to-know; ZKP preferred

> **SHIPPED (hub-native enclosure):** the original framing put all secrets in an *external* Hestia vault and called the hub's plaintext identity JSON an anti-pattern to be deprecated. The hub now carries its own fail-closed encrypt-at-rest enclosure: the Sovereign identity is **encrypted at rest** (with `hub seal-identity` to migrate a plaintext identity in place), the hub boots **unlock-first** into a degraded **locked shell** (tier-0 surface) with **no stored passphrase**, ignites at runtime via an unlock seam (incl. a tier-2 M-of-N witnessed unlock grant), and supports `rotate-passphrase` (operator-chosen secret). SQLCipher-encrypted state + encrypted ledger complete the enclosure. The external-Hestia path remains valid; the hub no longer *requires* it to protect its own keys.

Three rules, in order of specificity:

**A. Vault is the exclusive home of secrets.** Private keys, API credentials, sealing material, any secret the system needs — all live in Hestia's vault. The hub never stores secrets. The hub's databases, ledgers, society state, charters, role assignments — all of it is public-by-design within the chapter (signed for integrity, not encrypted for confidentiality of the data itself). If something needs to be secret, it belongs in a vault, not in chapter storage.

**B. Access is gated on verified authority + need-to-know — both, not either.** A caller asking for a secret (or even for a signature using a secret) must prove (i) they hold the authority to act, AND (ii) the action under that authority requires that specific secret right now. Authority alone is not enough. Need-to-know alone is not enough. Same gate applies to derived queries: even non-secret state should be returned at minimum granularity for the caller's role and current action.

**C. Zero-knowledge proofs preferred over disclosure when possible.** Whenever the hub or another verifier needs to confirm a fact — "this caller is authorized," "this caller is a member," "this caller's trust score exceeds threshold," "this caller holds a current delegation for role X" — prefer a ZKP that confirms the fact without revealing the underlying secret, identity, or threshold value. Standard signatures remain correct where the signer's identity must be public (audit trail of consequential acts, council votes). ZKPs are the preferred shape for everywhere else.

Implications across tracks:
- **Track H (Hestia)**: vault interface design must support ZKP-producing operations, not just "give me the credential" or "sign this payload." The vault is the privacy-preserving prover. The vault enforces the authority+need-to-know gate at access time. See addendum to Track H delegation post.
- **Track U (web4-core)**: signature primitives may need ZKP-variant additions (predicate proofs over membership, threshold proofs over T3/V3 scores, range proofs for ATP balances). Likely a U5 sprint once Hestia's ZKP requirements crystallize.
- **Track B (hub)**: storage is secrets-free **by design** — the trait surface never includes secret material. The MVP plaintext-identity-file anti-pattern has been **resolved hub-side**: the Sovereign identity is now encrypted at rest behind the fail-closed vault (see the SHIPPED note above), so the bootstrap convenience no longer leaves a key in plaintext. Query handlers enforce need-to-know via the law — **PolicyEntity gates reads the same way it gates writes (shipped).**

This is constitutional alongside #1 (law) and #2 (Hestia). Privacy and authority discipline is foundational to the whole stack; bolting it on later means redesigning every interface.

---

## Track structure

Work splits across four tracks. Sync points named where tracks meet.

### Track H — Hestia (hestia repo, parallel to hub)

Hestia evolves from "Claude Code safety hook" into universal Web4 presence.

- **H1**: Vault — encrypted-at-rest credential store. Passphrase-first (PBKDF2 → AES-GCM, or libsqlcipher). Hardware backing (TPM 2.0, Secure Enclave, YubiKey) **optional**, not required. Stores: Web4 LCT private keys, AI tool API credentials (OpenAI, Anthropic, etc.), other secrets a user needs.
- **H2**: Member CLI — `hestia init`, `hestia connect-hub`, `hestia sign-request`, `hestia list-hubs`, `hestia revoke-delegation`.
- **H3**: Multi-hub connector — manage N hub connections, route signing requests to correct hub.
- **H4**: Delegation primitives — `hestia delegate-to-agent <agent-id> --role X --scope ...` (creates DelegatedAuthority); `hestia revoke <delegation-id>`.
- **H5**: AI variant — same Hestia code, AI-owned vault. For autonomous AI agents that own their own keys (vs. human-delegated agents). Pattern: identical to human Hestia; ownership differs.
- **H6**: Plugin extensibility — formal spec for agent-tool plugins (Claude Code, Cursor, ChatGPT desktop, custom). Each plugin: declare what it does, request signing via Hestia, log actions.
- **H7**: TUI / GUI — later, V3.

**Sync points to hub**: H2-H3 → hub uses Hestia LCTs as Sovereign (Track B item B2). H4 → hub recognizes delegation envelopes from member Hestias when AI agents act (Track B item B-AI).

### Track U — Web4-core (upstream PRs)

PRs go to dp-web4/web4. Decided per PR whether this or another session handles each.

- **U1**: Multi-fill `RoleAssignment` with threshold semantics. Or new `MultiFillRoleAssignment` type alongside the existing one. Spec for M-of-N signing validity.
- **U2**: `DelegatedAuthority` primitive — binds delegator LCT → agent LCT → scope (roles, actions, expiration). Validation: agent's signature is valid IF a current DelegatedAuthority covers the action.
- **U3**: Law schema — RDF-based per Web4's "RDF is the ontological backbone" commitment. Law document = RDF graph of typed law statements (rules, escalations, thresholds, role assignments, delegations). Schema defines the predicates.
- **U4**: AI entity type refinements — `EntityType::AiSoftware` exists; may need extensions for hardware-bound AI (`AiHardwareBound`), AI-with-delegation (`AiDelegated`), etc. Or stay as-is and let delegation envelopes carry the nuance.

### Track B — Hub (web4/hub, this repo)

Application infrastructure built on Hestia, web4-core, ACT.

- **B1**: Member-role refactor — Citizen-default; non-Sovereign roles unfilled at genesis. Founder fills Sovereign + Citizen only. **SHIPPED (V2-1).**
- **B2**: Hestia-LCT-as-Sovereign integration — `hub init` accepts existing Hestia LCT; deprecate anonymous-Sovereign pattern. **SHIPPED (V2-7):** `hub init --sovereign-hestia` + RemoteSigner/HestiaCallbackSigner; MCP + REST acts work on Hestia chapters.
- **B3**: Sovereign Council mechanics — multi-fill at the role level; admit/retire/eject/elect event types; M-of-N signature validation. **SHIPPED (V2-9):** Council data model + propose/aggregate flow + M-of-N enforcement + admin UI.
- **B4**: Law parser + interpreter — read signed law file; validate signatures; evaluate requests against rules. PolicyEntity role calls into this. **SHIPPED (V2-8):** YAML law parser/validator, signed law storage (`LawAmended`), evaluator (Law × R6 → Allow/Deny/Escalate), PolicyEntity gate wired into REST + MCP act handlers *and reads*, hot-reload, `hub set-law`/`get-law`/`init-law`.
- **B5**: Storage backend abstraction — Trait + SqliteBackend + PostgresBackend impls; migration tool from file-based MVP. **SHIPPED (V2-2):** `ChapterStore`/`HubStore` trait + FileBackend + SqliteBackend (SQLCipher-encrypted) + DynamoDB backend + `hub migrate`. Postgres still on the roadmap.
- **B6**: Multi-tenant deployment — schema-per-chapter (default) or tenant-id-column (high-density) within one Postgres deployment; one-chapter-per-process for max isolation. *Needs B5. (Still future.)*
- **B7**: Member self-add request flow — `MemberJoinRequested` event; admin review surface; hub-law-policy hook. **SHIPPED:** V2-12 member self-add via signed envelope, plus a member **admission queue + operator GUI** (no-restart admit/deny/re-key/remove).
- **B8**: AI role-filler runtime — process supervision (spawning + monitoring AI agents per role); ATP accounting per AI action; T3 scoring; escalation event routing. *Needs U2+U4 and B4. (Still future.)*
- **B9**: Admin web UI — askama server-rendered HTML; member view + admin view + Sovereign Council interface + escalation review queue. **SHIPPED (V2-16):** read-only `/admin` dashboard + write-capable operator plane (admissions + member management) on the admin port `127.0.0.1:8772`.
- **B10**: HTTPS + caddy convention — reverse-proxy pattern; well-known URI for discovery. **PARTLY SHIPPED:** the `GET /.well-known/web4-hub.json` discovery endpoint ships; the HTTPS/reverse-proxy convention is still future.
- **B11**: Cloud deployment artifacts — helm chart for k8s + terraform modules for AWS/GCP/Azure. Platform-agnostic via clean storage + reverse-proxy abstractions. *Needs B5+B10. (Still future.)*

### Track L — Law primitives (shared between hub + community)

Lives partly in web4-core (schema in U3), partly in hub (interpreter in B4), partly in standalone repos (templates + validators).

- **L1**: Law schema as RDF (U3)
- **L2**: Law interpreter (B4)
- **L3**: Sample law templates — community-chapter starter, enterprise-compliance starter, etc. Open-source. Each template is a SIGNED EXAMPLE; chapters adopt by re-signing with their Sovereign.
- **L4**: Law validator CLI — `web4-law-check <law-file>` validates schema + signatures + internal consistency.

### Track C — Reference AI role-fillers (community-led)

These are SEPARATE projects that consume hub's role-filler API. NOT in web4/hub.

- **C1**: Reference PolicyEntity — open-source, built on commodity LLMs (Claude, GPT, local models via Ollama). Reads law, evaluates requests, returns approve/deny/escalate with reasoning.
- **C2**: Reference Archivist — automated ledger maintenance + retention.
- **C3**: Reference Witness — independent attestation across chapters.
- **C4**: Reference Auditor — T3/V3 validation, trust math checks.

These are demonstrations + starter implementations. Communities can swap any for their preferred AI provider or build their own. The hub provides the API; the community provides the role-fillers.

---

## Proposed V2 sprint sequence

Dependency-driven order, not calendar-driven. Each sprint produces a verifiable milestone.

| Sprint | Track | Focus | Depends on | Status |
|---|---|---|---|---|
| V2-1 | B | B1 — Member-role refactor (Citizen-default, others unfilled) | — | **SHIPPED** |
| V2-2 | B | B5 — Storage backend abstraction + SQLite impl + migration tool | — | **SHIPPED** (file/SQLite/DynamoDB + `hub migrate`) |
| V2-3 | H | H1 — Hestia vault (passphrase-first; hardware optional) | — | Hestia track |
| V2-4 | H | H2-H3 — Hestia member CLI + multi-hub connector | H1 | Hestia track |
| V2-5 | U | U1+U2 — web4-core PRs: multi-fill RoleAssignment + DelegatedAuthority | — | web4-core track |
| V2-6 | U | U3 — Law schema PR upstream | — | web4-core track |
| V2-7 | B | B2 — Hestia-LCT-as-Sovereign integration | H2 + U3 | **SHIPPED** |
| V2-8 | B | B4 — Law interpreter; PolicyEntity uses it | U3 + B5 | **SHIPPED** (gates writes *and* reads) |
| V2-9 | B | B3 — Sovereign Council mechanics | U1+U2 + B2 | **SHIPPED** (M-of-N propose/sign/threshold) |
| V2-10 | H | H4 — Hestia delegation primitives | U2 | Hestia track |
| V2-11 | H | H5 — AI-variant Hestia | H1+H4 | Hestia track |
| V2-12 | B | B7 — Member self-add flow | H3 + B4 + B5 | **SHIPPED** (+ admission queue/operator GUI) |
| V2-13 | B | B8 — AI role-filler runtime | U2+U4 + B4 + H5 | future |
| V2-14 | C | C1-C4 — Reference AI role-fillers (parallel, community-led) | B8 (API) | future (community-led) |
| V2-15 | B | B6 — Multi-tenant deployment | B5 | future |
| V2-16 | B | B9 — Admin web UI | B7 + B8 | **SHIPPED** (`/admin` + operator plane) |
| V2-17 | B | B10 — HTTPS + discovery | B9 | partly (`.well-known` shipped) |
| V2-18 | B | B11 — Cloud deployment artifacts | B5 + B10 | future |

V2 done when V2-18 ships. That's the "deployable as production community infrastructure" target. V3 is whatever V2 didn't address — likely federation specifics, advanced AI role coordination, performance work at >1M scale.

This is **not** a calendar plan. It's a dependency-graph order. Pace is set by how fast each piece can be done well, not by a roadmap.

---

## Shipped beyond the original plan

Several subsystems were not in the original track structure above but have since shipped. Recorded here so the architecture stays honest about current state.

- **Hub encrypt-at-rest enclosure.** The hub now protects its own keys without requiring an external Hestia: Sovereign identity encrypted at rest, `hub seal-identity` (migrate a plaintext identity in place), unlock-first boot into a degraded **locked shell** (tier-0 surface, no stored passphrase), runtime ignition via an unlock seam (incl. a tier-2 **M-of-N witnessed** unlock grant) and `rotate-passphrase`. SQLCipher-encrypted state + encrypted ledger complete it. (Updates Commitment #8.)
- **Sealed channels + discovery.** Sealed member↔hub E2E channel; paired member↔member channels (ECDH + ChaCha20-Poly1305, forward secrecy via ephemeral session keys); `find_members` (hub gates, membot engine); `request_intro`/`list_intros`/`respond_intro` (the consent half of discovery); external→citizen bootstrap (`request_citizenship`) over the channel. PolicyEntity gates channel reads with MRH-style result bounding.
- **EUDI / `did:web4`.** OID4VCI issuer (membership SD-JWT-VCs) + OID4VP verifier, with a RemoteSigner issuer, and `did:web4` identifiers. Society-scale verifiable credentials.
- **Constellation attestation.** Hub-side verify + challenge/present channel tools.
- **Member admission queue + operator plane.** Self-add via signed envelope plus a no-restart operator GUI (admit/deny/re-key/remove) on the operator plane (`127.0.0.1:8772`). (Realizes B7 + B9.)
- **ReferencedAct + hub→citizen notifications.** Acts can reference prior acts; the hub notifies citizens. (Phase-0 Gap A.)
- **Open-core plugin seam.** The generic `hub-plugin` seam — canonical `gate → handle → scope` dispatch path — is promoted to open core (public). Advanced role-fillers can plug in behind it.

---

## Open design questions (need resolution before / during respective sprints)

### Law schema (gates V2-6 and V2-8)
- RDF graph (per Web4 commitment to RDF as ontological backbone) or YAML (human-readable, simpler)?
- Recommendation: **RDF as canonical, YAML as ergonomic surface** that compiles to RDF. Chapters edit YAML; hub stores + signs the RDF. Validators check both.
- Predicates needed: `chapter:hasRule`, `chapter:escalationTrigger`, `chapter:admissionPolicy`, `chapter:atpIssuancePolicy`, etc. Spec inside U3.

### Multi-tenancy strategy (gates V2-15)
- Schema-per-chapter in one Postgres? Tenant-id-column in shared tables? One Postgres per chapter (heavy)?
- Recommendation: **schema-per-chapter** as the default — strong isolation, reasonable density (1000s of chapters per database server before scaling out). Tenant-id-column option for ultra-high-density deployments later.

### Discovery (later sprints)
- Well-known URI (`https://hub.<chapter>.example.com/.well-known/web4-hub.json`) — definitely.
- Centralized registry overlay (e.g. a deployment's central server aggregating well-known queries across chapters) — optional, deployment-specific.

### AI vault crypto (gates V2-11)
- Same passphrase-derived crypto as humans?
- Or hardware-bound by default for AI keys (TPM, Secure Enclave, KMS-backed in cloud deployments)?
- Recommendation: **same as humans** by default (simplicity); deployment can choose hardware backing as configuration. Aligns with "hardbound optional, not required."

### Sovereign Council formation (gates V2-9)
- M-of-N defaults? (1-of-1 at founding, then upgradeable to 2-of-3, 3-of-5, etc.?)
- Threshold change procedure? (Sovereign Council votes? Member vote? Both?)
- Recommendation: **hub law specifies** (per Commitment #1). Hub provides the mechanism; chapter sovereign-signs the policy.

---

## Implications for MVP — what to revisit before V2 starts

> **RESOLVED.** All three MVP conflicts below have been addressed.

Three MVP artifacts conflicted with the new commitments and were flagged for cleanup:

1. **`hub gen-lct ./sovereign.json`** — generated an anonymous chapter-specific LCT. **RESOLVED:** Hestia-as-Sovereign (`hub init --sovereign-hestia`) shipped (V2-7), and the Sovereign identity is now encrypted at rest behind the fail-closed vault rather than sitting in a plaintext JSON file.
2. **`Society::bootstrap` filling all 7 roles with founder** — **RESOLVED (V2-1):** founder fills Sovereign + Citizen only; other roles unfilled until law specifies otherwise.
3. **Daemon hardcodes Sovereign-signs-everything** — **RESOLVED (V2-8):** the PolicyEntity, reading the signed law, decides whether a request is authorized (Allow/Deny/Escalate) before any signing happens — on writes *and* reads.

These were clean migration points, not breaking changes. MVP chapters can still run as-is; V2 chapters use the new flow.

---

## Next MRH (focused sub-conversation candidates)

Once this outer landscape is committed, we partition. Next focused sub-conversations could be:

- **Sprint V2-1**: member-role refactor. Smallest scope; gets us into V2 cleanly. Independent.
- **Sprint V2-5/V2-6**: web4-core PRs. Upstream work; bigger reach (any web4 user benefits). Independent.
- **Track H bootstrap**: Hestia vault + member CLI. Lives in the other repo; can run in parallel by another session/track.
- **Law schema design**: deeper conversation on RDF predicates + YAML ergonomics. Gates V2-6+V2-8.
- **LCT paired channels** (see [`PAIRED-CHANNELS.md`](PAIRED-CHANNELS.md)) — hub-mediated, E2E-encrypted, ledger-witnessed pairs as the operational manifestation of pairing-as-relationship-substrate. Activates the trust-medium claim of the Web4 equation. Sprint A is an ECDH primitive in web4-core; later sprints land hub-side lifecycle, messaging, FS, V3 accrual.

We pick one. Iterate. Set MRH for the next sub-conversation when that one closes.

---

## Document evolution

This file is a working artifact. Update when:
- A sprint ships and we learn something that updates the architecture
- An open design question gets resolved
- A new constraint emerges (like this conversation surfaced AI role delegation as load-bearing)
- We partition into a focused sub-conversation and want to record the MRH transition

Don't try to keep it perfect or final. The goal is **enough alignment to act**, not full specification before acting. MRH management is the work.

---

*— dp + Claude, 2026-06-07, scoping outer landscape*
