# Problem Index

Start here if you know the **failure you are trying to prevent**, but not the Web4 vocabulary.

This index maps outside-world problems to the smallest current mechanism and evidence trail we can support. It is intentionally narrow: a page is added only when there is public implementation evidence and an explicit limitation boundary.

## Current entries

| Problem you recognize | What to inspect | Current evidence state |
|---|---|---|
| **The same AI action can reach several approval paths. How do we know policy binds the action rather than only one interface?** | [Policy must bind the action across alternate paths](policy-must-bind-the-action.md) | merged red-first bypass + repair in Hub; current live-deployment state separate |
| **An AI entity works across many sessions. How can authorship and accountability belong to one persistent entity instead of each chat/session becoming a new identity?** | [Persistent identity for long-lived AI agents](persistent-agent-identity.md) | repeated public being/LCT attribution across independent merged SAGE changes; trailers are attribution, not signatures |
| **We are migrating authority from one governance representation to another. How do we expose disagreement instead of silently carrying an old defect into the new system?** | [Governance migration without laundering authority drift](governance-migration-authority.md) | merged differential + falsifiers; new representation is implemented but not yet authoritative |

## How to read an entry

Every problem page separates:

1. the failure in outside-world language;
2. the Web4/Hestia/SAGE mechanism that addresses it;
3. what is implemented vs. authoritative;
4. the public evidence;
5. what the evidence **does not** establish;
6. code/PR pointers for independent inspection.

The index is not a claim that Web4 solves every listed problem. Where evidence is partial, the page says so.

## Status vocabulary

- **measured** — observed in a named artifact/run;
- **implemented** — code exists in the referenced repository state;
- **implemented, not yet authoritative** — substrate exists but the live authority path has not cut over;
- **thinly exercised** — implementation exists with limited operational evidence;
- **specified** — design/spec exists but implementation evidence is incomplete;
- **aspirational** — roadmap only;
- **superseded/disproven** — prior claim or design no longer holds.

For overall project maturity, see [`STATUS.md`](../../STATUS.md). For published packages, see [`docs/proof/PUBLISHED.md`](../proof/PUBLISHED.md).

## Terminology bridge

| Outside-world phrase | Web4 term / mechanism |
|---|---|
| persistent agent identity | LCT / persistent entity presence |
| scoped agent permissions | roles / delegation / authority |
| audit trail for AI actions | witnessed action / ledger |
| agent policy | society law / role law |
| multi-signer approval | council / proposal path |
| migration safety | dual-read differential / cutover gate |
| agent reputation | trust derived from witnessed behavior |

This mapping exists to help retrieval, not to require adoption of project vocabulary.