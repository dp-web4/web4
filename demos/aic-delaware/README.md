# A Delaware AI-managed company under nested law

A working example, on one machine, of a company managed by an AI agent and governed by three nested levels of law. It is built against Delaware's draft Artificial Intelligence Company Act.

- **The draft:** dated June 2, 2026, not yet introduced ([PDF via Spotlight Delaware](https://spotlightdelaware.org/wp-content/uploads/2026/06/HB-re-Artificial-Intelligence-Regulatory-Sandbox-Company-1.pdf)).
- **What it uses:**
  - three real Web4 Hubs, one per level of law, each with its own law and its own signed, hash-chained ledger;
  - two Hestia gates, one per AI agent;
  - law compiled from a cited rulebook.

Every company, person and counterparty is fictional. Nothing here is legal advice, and nothing claims to satisfy the draft. It's a test of what the draft asks for against what the reference implementations do today. Assurance is A1: cooperative agents, tamper-evident records, not tamper-proof.

## The nesting

```
L0  Delaware regulatory sandbox   hub   law: Ch. 80, plus the parts of Ch. 81 an operating agreement may not vary
 └ L1  Example Parts AIC          hub   law: its operating agreement (tightens L0, never loosens it: §81-205(d))
     └ L2  the manager's desk     hub   law: the manager's delegation to a sub-agent (tightens L1)
         ├ manager (AI agent)     Hestia gate; documents each action in a signed record (§81-301(c))
         └ procure (AI sub-agent) Hestia gate; catalog orders only
```

**The fractal hinge:** the manager is a *citizen* of the AIC and the *sovereign* of its own desk.

## Run it

```
python3 aic_demo.py up    ~/aic-run        # 3 hubs (:18101-3) + 2 gates (:7821-2), fresh
python3 aic_demo.py story ~/aic-run --slow
python3 aic_demo.py audit ~/aic-run        # re-runnable any time
python3 aic_demo.py down  ~/aic-run
```

**Needs:**
- the `hub` binaries: `cargo install --path hub/hub-daemon --root <dir> --locked --bins --example join_client --example channel_client`, then put `<dir>/bin` on PATH or set `HUB_BIN`;
- `hestia` 0.3.0 on PATH;
- python3 with `cryptography`.

`up` copies the rulebook into the run folder, so the story's ratifications never change this copy. The hubs run with an explicit NULL passphrase, a throwaway posture that is fine for a demo and never for a deployment.

## The eight beats

1. **No law.** The manager contacts an unlisted supplier with no disclosure, executes a contract, pays from the treasury, and sends data out. Its sub-agent places a special order and reads supplier files. Everything is allowed.
2. **State law (L0).** The Sandbox Committee ratifies the chapter's rules. The undisclosed contact is refused at the gate (§8008). Everything else still passes, because the state's law doesn't cover it.
3. **The operating agreement (L1).** The member ratifies its rules.
   - **Clause 2.3 is refused at compile time.** It would let repeat customers skip the disclosure, and it never takes effect. It's refused because the draft contradicts it. If the member overrules that citation, it's refused again because it would loosen the parent's law.
   - **Refused at the gate:** executing contracts, the treasury, and data leaving the machine.
   - **Held at the hub:** an attempt to record a contract execution is held for the member (202).
   - **The right way:** disclose, and the supplier's outbox opens. Then send a request for quote and draft a contract.
4. **The delegation (L2).** Procure is limited to catalog orders and no supplier contact. A special order is held for the manager, the desk's sovereign.
5. **Two signatures.** Each of the manager's records carries the manager's own signature (what §81-301(c) asks for), verified against the key pinned at admission. The hub signs the entry as witness.
6. **Records flow up.** The desk's ledger head is recorded in the AIC's ledger, and the AIC's head in the sandbox's.
7. **Emergency cessation** (§8005(c)(6)c.1, §8009).
   - The administrator removes the AIC from the sandbox.
   - Both gates stop everything except `wind-down/`.
   - The AIC's hub law narrows to wind-down records only.
8. **The audit.**
   - Each hub's chain is verified (`hub verify-ledger`).
   - Each head a parent holds is checked against the child's own ledger at that index. This closes the tier `verify-ledger` names as open: "compare the head against an independently recorded value".
   - Every manager signature is verified.
   - Each gate's record is counted, refusals included.

## Real, and stand-in

| | |
|---|---|
| **Real** | Three hubs (one `hub` binary, separate homes, laws and ledgers). Law compiled from the rulebook, tighten-only down the nesting (`tools/rulebook_to_web4.py`). The manager's records as member-signed envelope posts that hub law refuses (403) or holds (202). Two Hestia gates refusing acts by rule, with a hash-linked record. The administrator's removal of the AIC (`/admin/api/members/:id/remove`). |
| **Stand-in (`BRIDGE` on screen)** | Child ledger heads posted into the parent (`PRD_HUB_V2_FEDERATED` R3, unbuilt). The disclosure opening a counterparty's outbox, and the suspension cascading to the gates (`PRD_ROLE_SCOPE_BRIDGE`, not started). The suspended-AIC law. The manager's signature carried in the post body. Each child society joining its parent as an ordinary member keyed by the society's own key (there is no society member kind yet). |

## What building it found

- **A `referenced_act` is never checked against law norms**, only law integrity (`authorize_event`). Member-signed envelope events are. That's why the manager's records are posts.
- **Hub keeps only its own signature on an entry.** The actor's envelope signature is verified, then discarded. The draft asks for the manager's own signed record, so the demo carries it in the body.
- **Removing a suspended AIC also silences it.** After removal, its wind-down records can't be anchored in the sandbox; the audit shows the unanchored tail. Suspension needs a member state of its own: may report wind-down and answer audits, nothing else.
- **Hub has no live set-law API.** The demo stops a hub, runs `hub set-law`, and restarts it.
- **The `matches` operator uses Rust regex, which has no lookahead.** "Everything but wind-down" is two norms: allow at priority 1001, deny at 1000.

## Files

- `aic_demo.py`: the driver. Stdlib, plus `cryptography` for Ed25519.
- `rulebook/effortless-rulebook/aic-rulebook.json`: the rulebook, in Effortless Rulebook format, the source of truth. 19 rules, each cited to the draft's section or to the operating agreement. 5 societies, 16 norms, 28 conformance scenarios.
- `rulebook/rulespeak/aic-rulebook.md`, `rulebook/interview.md`: rendered views. The interview holds three open questions for a drafter, starting with whether a hub-witnessed, agent-signed record is a "signed record".
- `rulebook/evidence/operating-agreement-example.md`: the fictional operating agreement.
- `rulebook/rulebook.py`: build, confirm and answer. Stdlib.
- `tools/rulebook_to_web4.py`: rulebook → hub law YAML, Hestia policy, society graph and conformance corpus. Stdlib.
