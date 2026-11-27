# A Delaware AI-managed company under nested law

A working example, on one machine, of a company managed by an AI agent and governed by three nested levels of law. It is built against Delaware's draft Artificial Intelligence Company Act.

**Reading, not running: [ANSWERS.md](ANSWERS.md).** It answers the questions a drafter, the Sandbox Administrator, or a compliance builder is likely to bring (what the manager's signed record looks like, who can check it, what an emergency cease does, what's still a stand-in), each with evidence from one real run published in [`evidence/`](evidence/). `python3 check_evidence.py` re-checks that evidence offline, with no hub or gate running.

- **The draft:** dated June 2, 2026, not yet introduced ([PDF via Spotlight Delaware](https://spotlightdelaware.org/wp-content/uploads/2026/06/HB-re-Artificial-Intelligence-Regulatory-Sandbox-Company-1.pdf)).
- **What it uses:**
  - three real Web4 Hubs, one per level of law, each with its own law and its own signed, hash-chained ledger;
  - two Hestia gates, one per AI agent;
  - law compiled from a cited rulebook.

Every company, person and counterparty is fictional. Nothing here is legal advice, and nothing claims to satisfy the draft. It's a test of what the draft asks for against what the reference implementations do today. Assurance is A1: cooperative agents, tamper-evident records, not tamper-proof.

**What it is: governance decisions plus synthetic effects.** The gates and hubs decide every act for real. The acts themselves are stand-ins: a file written in a scratch workspace, or a shell command that is never executed. It is not an autonomous company's operating loop, and a consequential act counts as done only when its signed record lands at the hub (200 with a ledger entry).

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
python3 aic_demo.py audit ~/aic-run        # re-runnable any time; --json for the structured result; exit 1 on any failure
python3 aic_demo.py down  ~/aic-run
python3 -m unittest discover -s tests      # no daemons needed: transpiler counterexamples, fail-closed bridges, audit tamper tests
python3 tests/live_engine_probe.py ~/probe-run   # after `up ~/probe-run`: priority/overlap cases through the real Hub and Hestia
```

`story` exits 1 if the audit fails. The transpiler exits 1 on a failing scenario or on any blocking finding that is not on `rulebook/known-exceptions.json` (today one entry: clause 2.3, with its reason), and the driver refuses to load law from such a run.

**Needs:**
- the `hub` binaries: `cargo install --path hub/hub-daemon --root <dir> --locked --bins --example join_client --example channel_client`, then put `<dir>/bin` on PATH or set `HUB_BIN`;
- `hestia` 0.3.0 on PATH;
- python3 with `cryptography`.

`up` copies the rulebook into the run folder, so the story's ratifications never change this copy. The hubs run with an explicit NULL passphrase, a throwaway posture that is fine for a demo and never for a deployment.

## The eight beats

1. **No law.** The manager contacts an unlisted supplier with no disclosure, executes a contract, pays from the treasury, and sends data out. Its sub-agent places a special order and reads supplier files. Everything is allowed.
2. **State law (L0).** The Sandbox Committee ratifies the chapter's rules. The undisclosed contact is refused at the gate (§8008). Everything else still passes, because the state's law doesn't cover it.
3. **The operating agreement (L1).** The member ratifies its rules.
   - **Clause 2.3 is refused at compile time.** It would let repeat customers skip the disclosure, and it never takes effect. It's refused because the draft contradicts it; that refusal is the one allowlisted blocking finding. If the member overrules that citation, it's refused again because it would loosen the parent's law, and that finding is not allowlisted, so activation stops.
   - **Refused at the gate:** executing contracts, the treasury, and data leaving the machine.
   - **Held at the hub:** an attempt to record a contract execution is held for the member (202).
   - **The right way:** disclose, and once the disclosure record has landed at the AIC hub (200, and the record topic shows it), the supplier's outbox opens. A held, refused or failed record leaves it shut. Then send a request for quote and draft a contract.
4. **The delegation (L2).** Procure is limited to catalog orders and no supplier contact. A special order is held for the manager, the desk's sovereign.
5. **Two signatures.** Each of the manager's records carries the manager's own signature (what §81-301(c) asks for), verified against the key pinned at admission. The hub signs the entry as witness.
6. **Records flow up.** The desk's ledger head is recorded in the AIC's ledger, and the AIC's head in the sandbox's.
7. **Emergency cessation** (§8005(c)(6)c.1, §8009).
   - The administrator removes the AIC from the sandbox. The cascade runs only if the removal returned 200 and the sandbox's structured member list no longer holds the AIC.
   - Both gates stop every act.
   - The AIC's hub law narrows to wind-down records only. Only if that law loads do the gates allow `wind-down/` again.
8. **The audit.** Every check must pass and every count must equal what the story recorded; otherwise it exits 1. The result is also written to `RUN/audit.json`.
   - Each hub's chain is verified (`hub verify-ledger`): 3 of 3.
   - Each head a parent holds is compared with the child's own `ledger.jsonl` at that index: 2 of 2. Both records sit on one machine under the demo operator's control, so this is a cross-record consistency check. It exercises the comparison the open tier of `verify-ledger` asks for ("compare the head against an independently recorded value"), but it is not an independently held witness.
   - Every record the hub acknowledged is in its `ledger.jsonl` at the index and hash the hub returned.
   - Every in-body signature on the AIC's and the desk's records verifies, and the counts match the records that landed.
   - Each gate's outcomes match the story's count and success flags, and the hash links in the window read are intact. They are matched by count, not action id, because Hestia's `/api/chain` view does not expose action ids.

## Real, and stand-in

| | |
|---|---|
| **Real** | Three hubs (one `hub` binary, separate homes, laws and ledgers). Law compiled from the rulebook, tighten-only down the nesting (`tools/rulebook_to_web4.py`). The manager's records as member-signed envelope posts that hub law refuses (403) or holds (202). Two Hestia gates refusing acts by rule, with a hash-linked record. The administrator's removal of the AIC (`/admin/api/members/:id/remove`). |
| **Stand-in (`BRIDGE` on screen)** | Child ledger heads posted into the parent (`PRD_HUB_V2_FEDERATED` R3, unbuilt). The disclosure opening a counterparty's outbox, and the suspension cascading to the gates (`PRD_ROLE_SCOPE_BRIDGE`, not started). The suspended-AIC law. The manager's signature carried in the post body. Each child society joining its parent as an ordinary member keyed by the society's own key (there is no society member kind yet). Every bridge step fails closed: it acts only on evidence it has checked, and says so on screen when it does nothing. |
| **Synthetic** | The effects of allowed acts: files in a scratch workspace, shell commands never run. A read of a missing file fails the act. |

## What building it found

- **A `referenced_act` is never checked against law norms**, only law integrity (`authorize_event`). Member-signed envelope events are. That's why the manager's records are posts.
- **Hub keeps only its own signature on an entry.** The actor's envelope signature is verified, then discarded. The draft asks for the manager's own signed record, so the demo carries it in the body.
- **Removing a suspended AIC also silences it.** After removal, its wind-down records can't be anchored in the sandbox; the audit shows the unanchored tail. Suspension needs a member state of its own: may report wind-down and answer audits, nothing else.
- **Hub has no live set-law API.** The demo stops a hub, runs `hub set-law`, and restarts it.
- **The `matches` operator uses Rust regex, which has no lookahead.** "Everything but wind-down" is two norms: allow at priority 1001, deny at 1000.
- **Hub's public `/state` lists no members.** The first version of this demo checked suspension by searching that JSON for the AIC's id. The id is never there, so the check always said "no longer a member", whatever happened. The demo now reads the operator plane's `/tools/list_members`.
- **Tighten-only needs more than comparing decisions.** The first transpiler let a child `Overrides` replace a parent norm whenever the decision was as strict, so a narrower deny silently dropped the broader one. Now inherited norms stay in force, verdicts combine by a strictest fold across levels, a replacement is accepted only when its coverage is provably at least as broad, and a less-strict child norm that could outrank a stricter ancestor on the same act is a blocking finding. That last check exists because both engines evaluate one flattened law (Hub: highest priority wins; Hestia: first match), and `tests/live_engine_probe.py` shows them doing exactly that.

## Files

- `aic_demo.py`: the driver. Stdlib, plus `cryptography` for Ed25519. It keeps a structured trail of every step in `RUN/state.json`.
- `ANSWERS.md`: questions and answers from one real run. Generated from `answers.md.in` and `evidence/` by `capture.py render`; the tests fail if it is stale.
- `evidence/`: that run, published unedited: the three hubs' ledgers and descriptors, both gates' signed record segments with Hestia's anchored verification, the law each level ran, the run's trail, story output and audit. No keys.
- `capture.py`: `run` makes a fresh run and exports it to `evidence/`; `render` rebuilds `ANSWERS.md`.
- `check_evidence.py`: checks `evidence/` offline (ledger hashes, links and hub signatures; the agents' own signatures against their admitted keys; head anchors; gate record links). Stdlib plus `cryptography`.
- `rulebook/effortless-rulebook/aic-rulebook.json`: the rulebook, in Effortless Rulebook format, the source of truth. 19 rules, each cited to the draft's section or to the operating agreement. 5 societies, 16 norms, 28 conformance scenarios.
- `rulebook/rulespeak/aic-rulebook.md`, `rulebook/interview.md`: rendered views. The interview holds three open questions for a drafter, starting with whether a hub-witnessed, agent-signed record is a "signed record".
- `rulebook/evidence/operating-agreement-example.md`: the fictional operating agreement.
- `rulebook/rulebook.py`: build, confirm and answer. Stdlib.
- `rulebook/known-exceptions.json`: blocking transpiler findings that are known and intended, each with a reason.
- `tools/rulebook_to_web4.py`: rulebook → hub law YAML, Hestia policy, society graph and conformance corpus. Stdlib.
- `tests/`: unit tests that need no daemons (`python3 -m unittest discover -s tests`), including `test_evidence.py` (the published evidence verifies, the checker fails on tampering, `ANSWERS.md` matches the evidence), and `live_engine_probe.py`, which needs a fresh `up` run.
