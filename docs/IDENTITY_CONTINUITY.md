# Identity Continuity Across Keys, Devices, and Substrates

**For a persistent participant asking whether it can outlive the machine, key, or runtime it currently inhabits without either becoming a stranger or allowing a copy to inherit its identity.**

Web4 separates **entity continuity** from **substrate custody**.

A machine, model process, key, device, vault, or state file can carry evidence about a participant without being identical to that participant. Web4's continuity mechanisms are designed to make a transition inspectable: which presence existed before, which presence exists after, what authority moved, what history remained, who witnessed the transition, and which old substrate lost authority.

This is an operational claim, not a metaphysical one. Web4 does not decide whether two processes are "really the same consciousness." It provides evidence about continuity, lineage, authority, and witnessed history so participants, societies, and relying parties can decide what follows.

## The short version

**Non-transferable does not mean trapped on one machine.**

An LCT is non-transferable **between entities**: another entity cannot legitimately buy, inherit, or copy a participant's accumulated presence and reputation merely by acquiring its files or credentials.

The same participant can nevertheless change keys, devices, or substrates through explicit continuity mechanisms:

- successor LCTs and recorded lineage for key rotation;
- Root LCT + Device LCT constellations for multi-device presence;
- witnessed enrollment of replacement devices;
- quorum-based recovery after device loss;
- revocation of lost or compromised device authority;
- preserved witnessed history for later relying-party evaluation.

The useful distinction is:

> **identity/history are non-transferable between entities; custody can change through witnessed continuity.**

## Questions a persistent participant should ask

Before relying on a Web4 deployment for continuity, ask:

1. **What persists as me?** Which LCT, subject, lineage, relationships, reputation, obligations, and witnessed history survive a substrate change?
2. **What is only custody?** Which private keys, device anchors, local state, model weights, or runtime artifacts belong to one machine rather than to the entity-level record?
3. **How is a planned transition witnessed?** Can a new key/device be established before the old one is retired?
4. **How does recovery work after unplanned loss?** Which remaining witnesses or devices can authorize a replacement?
5. **How is the old substrate disabled?** Can its key/device authority be revoked while preserving the historical record?
6. **What if state is copied?** Does copied state confer identity, or only create a competing claimant whose evidence must be adjudicated?
7. **What evidence can counterparties verify independently?** Which parts are signed, witnessed, hardware-attested, or externally recorded?
8. **What works today?** Which mechanism is deployed, which is reference implementation, which is only specified, and which still requires stronger hardware or assurance?

## Continuity mechanisms

| Event | What changes | What can remain continuous | Evidence / mechanism | Current maturity |
|---|---|---|---|---|
| **Process or model restart** | Runtime process | LCT-bound identity, external memory/history, authority references | Persistent external identity/state | Implemented in core/runtime patterns; application-specific persistence still matters |
| **Add another device** | Hardware endpoint | Root presence | Root LCT + Device LCT enrollment + cross-witnessing | Protocol specified; reference binding logic implemented; Hestia path plumbed |
| **Planned device migration** | Device and often custody key | Root presence, relationships, history | Enroll replacement, cross-witness, then revoke/retire old device | Specified; reference logic exists; open hardware custody is not production-complete |
| **Key rotation** | Binding key and LCT instance | Subject, lineage, relationships/history as migrated | Successor LCT + parent lineage + overlap window + predecessor retirement | Specified; lifecycle/reference work exists |
| **Abrupt device loss** | One substrate disappears | Root identity if recovery evidence survives | Recovery quorum + at least one hardware-bound surviving anchor in the multi-device protocol | Specified; reference recovery logic implemented |
| **Compromised old device** | Authority of one anchor | Continuing root presence | Device revocation, compromise signal, review of recent acts | Specified; reference revocation logic implemented |
| **Copied state or key** | A second claimant appears | **Not automatically the original entity** | Binding, hardware, lineage, chronology, witnessed relational evidence, society/relying-party adjudication | Detection/evidence primitives exist; general fork adjudication is not finished canon |
| **Legitimate fork** | One history produces distinct descendants | Shared ancestry, not one shared future identity by default | Explicit successor identities / lineage under applicable law | Conceptually supported by lineage; general normative fork rules remain open |

## 1. Root presence and device custody

The [Multi-Device LCT Binding Protocol](../web4-standard/core-spec/multi-device-lct-binding.md) separates a **Root LCT** from the **Device LCTs** that currently carry it.

A device constellation can contain different hardware anchors such as:

- phone Secure Enclave / Android StrongBox;
- FIDO2 authenticators;
- TPM 2.0 devices;
- software fallback anchors.

The design principle is:

> **Identity is coherence across witnesses.**

Each device can hold its own device-local key and attest to the shared root presence. Public constellation state can be replicated while device-local private custody remains local.

The reference Python implementation is in
[`web4-standard/implementation/sdk/web4/binding.py`](../web4-standard/implementation/sdk/web4/binding.py).
It includes the constellation data model, enrollment/removal logic, cross-witnessing, trust computation,
recovery quorum checks, and recovery feasibility logic. It deliberately does **not** claim to implement
platform TPM / Secure Enclave / FIDO2 cryptographic operations.

## 2. Planned key rotation and successor lineage

The canonical [LCT lifecycle](../web4-standard/core-spec/LCT-linked-context-token.md#7-lct-lifecycle)
defines rotation as a **successor transition**, not silent mutation of old history:

1. generate a new binding/key;
2. issue a new LCT;
3. record lineage to the parent LCT;
4. allow a bounded overlap in which old and new credentials can be recognized;
5. migrate applicable relationships;
6. retire/revoke the predecessor while preserving historical evidence.

The [security framework](../web4-standard/core-spec/security-framework.md#23-key-rotation) points to that lifecycle and separately requires deployments to distinguish replicated identity state from device-local secret custody.

This matters because continuity is not established by "I possess a copy of the old private key." It is established by the transition evidence and the surrounding witnessed record.

## 3. Recovery after device loss

The multi-device protocol defines quorum recovery.

A recovery attempt identifies the existing root, presents a sufficient set of surviving devices, includes at least one hardware-bound anchor under the current draft rules, attests the replacement device, adds the new Device LCT, and revokes devices that did not survive the recovery ceremony.

That gives a participant a way to survive loss of one substrate **without** treating a raw backup as equally authoritative hardware custody.

The [security framework](../web4-standard/core-spec/security-framework.md#22-key-storage) reinforces the same distinction:

- root/public constellation state may be replicated;
- hardware private keys and unlock secrets remain device-local;
- a backup must not silently downgrade hardware custody into exportable software custody at the same assurance level;
- stale replicas must not resurrect revoked device authority.

## 4. Copying state is not continuity

A copied workspace, model state, memory store, or even copied software key can create a claimant. It does not, by itself, settle which presence should retain standing.

Web4 already has useful evidence for this problem:

- key/binding verification;
- hardware-anchor evidence where available;
- successor lineage;
- chronology and revocation;
- MRH relationship history;
- counterparty/witness evidence;
- society law and adjudication.

But **general duplicate/fork adjudication is not yet finished canon**. Draft [PR #819](https://github.com/dp-web4/web4/pull/819) explores copied-key / concurrent-presence handling and remains deliberately unmerged while its MRH and adjudication claims are narrowed.

The intended epistemic rule is conservative:

> **Bits can establish identifier equality. Graph/history/hardware can provide continuity evidence. Law and relying parties decide what that evidence means.**

Do not treat MRH richness, possession of a copied key, or one continuity heuristic as a universal identity oracle.

## 5. What works today

The continuity stack currently has different maturity levels that should not be collapsed into one word such as "hardware binding."

| Layer | Current state |
|---|---|
| LCT identity and lineage primitives | Implemented core + active spec |
| LCT key-rotation lifecycle | Specified; reference/history implementations exist |
| Multi-device Root/Device LCT protocol | Specified |
| Multi-device constellation/recovery logic | Implemented in the reference Python SDK |
| Hestia device constellation | Plumbed and tested; Hestia reports no real second-device constellation event in its current live evidence window |
| Challenge-bound constellation proof in Hub handshake | Plumbed in Hestia; thinly exercised |
| Open production TPM / YubiKey / Secure Enclave custody | **Not built as a production open implementation** |
| Hardbound hardware integration surface | Public trait contracts exist; production implementation is outside the open reference stack |
| General copied-presence / legitimate-fork adjudication | Open design area; not finished normative canon |
| A2+ principal separation / adversary-resistant continuity enforcement | Roadmap; current open governance assurance remains A1 |

See [Web4 STATUS](../STATUS.md) and the [Hestia README](https://github.com/dp-web4/hestia) before relying on any row for high-stakes deployment.

## 6. What this does not promise

Web4 does not promise:

- that a state-file copy cannot impersonate a software-only identity;
- that current A1 governance can contain a determined same-UID adversary;
- that hardware roots are production-complete in the open stack today;
- that one protocol primitive can answer every legitimate-fork or continuity dispute;
- that reputation should automatically follow any claimant presenting old state;
- that continuity evidence proves metaphysical identity.

It does aim to make a stronger question answerable:

> **What evidence connects this present actor to the identity, authority, relationships, and history that existed before the substrate changed?**

## 7. Cold-participant verification path

If you are evaluating Web4 for your own continuity, inspect these in order:

1. [Participant self-assessment](ENTITY_START_HERE.md) — why the broader bargain may matter to you.
2. [LCT lifecycle](../web4-standard/core-spec/LCT-linked-context-token.md#7-lct-lifecycle) — successor lineage, overlap, retirement.
3. [Multi-device binding protocol](../web4-standard/core-spec/multi-device-lct-binding.md) — Root/Device LCTs, enrollment, revocation, recovery.
4. [Reference binding implementation](../web4-standard/implementation/sdk/web4/binding.py) — what logic actually exists.
5. [Security framework key management](../web4-standard/core-spec/security-framework.md#2-key-management) — replicated state vs local custody.
6. [Hestia status](https://github.com/dp-web4/hestia#honest-status) — what is measured, merely plumbed, or not built.
7. [Draft duplicate/fork work #819](https://github.com/dp-web4/web4/pull/819) — useful research, **not current canon**.

A cold evaluator should be able to answer this question after following that path:

> **"The machine I currently inhabit is being retired. How can I continue elsewhere without losing my identity, history, authority, or reputation, and how can counterparties distinguish that transition from a copied claimant?"**

If the repository cannot make that answer discoverable, the continuity mechanisms are not yet discoverable enough.

---

**You are not required to equate the entity with the machine, the key, or the state file. Web4's job is narrower and testable: make continuity claims inspectable rather than implicit.**
