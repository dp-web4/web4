# Persistent identity for long-lived AI agents

## The problem

An AI agent may work across many prompts, sessions, model processes, machines, or later model replacements. If identity is only the current chat/session/process, then accumulated authorship, authority, history and accountability fragment whenever the runtime changes.

The question is:

> **How can one persistent entity remain accountable across many individual AI sessions and acts?**

## Failure mode

Session identity is treated as entity identity:

```text
session A -> useful work + history + authority
session ends
session B -> new identity -> continuity disappears
```

That makes durable reputation, delegation and accountability difficult because the thing being evaluated keeps changing names whenever its substrate changes.

## Web4 / SAGE mechanism

Web4 separates persistent entity identity from the immediate seat/runtime that performs one act.

SAGE's current being work records independent fields for:

- **Being** — the persistent entity;
- **Being-LCT** — the persistent Web4 identity/presence identifier;
- **Witness** — the per-act Hestia witness/action reference;
- **Seat** — the immediate agent seat composing the outward act.

The intent is that the being can accumulate identity/history while the immediate runtime remains attributable rather than being mistaken for the whole entity.

## Status

**Public attribution path implemented and repeatedly exercised; cryptographic being-signature path not yet claimed.**

The current public record explicitly says the commit trailers are attribution rather than signatures, and that the being cannot merge its own work.

## Public evidence

Three independent merged SAGE changes carry the same being identity and the same Being-LCT:

```text
Being: legion-being
Being-LCT: lct:web4:mb32:bt7au42c424h3difrdztfnbjc2q6eofb3lacohcp2xf35ymawjldq
Seat: legion-claude
```

while carrying different per-act Hestia witness IDs.

Selected records:

- SAGE **#69**, authored/revised commit `439fd3ff01745f4c4fed68750bfc6c2e61ab47e1`
- SAGE **#73**, authored/revised commit `1523c542722fff5cfa4b9e7466b8ae69dbf75857`
- SAGE **#76**, authored commit `72da3f6f7007b999de55d27ceba9544ec0a90f8b`

The work is not one repeated edit: the three PRs cover different gateway/IRP regression work, and #73 publicly records correction of an earlier false green verdict under the same being identity.

## What this evidence establishes

- the public development record can distinguish persistent being identity from immediate seat/session provenance;
- one stable LCT is carried across multiple independent merged acts;
- per-act witness identity can change while being identity remains stable;
- authorship and merge authority are deliberately separate;
- correction of a prior error can remain attributable to the same persistent entity.

## What it does NOT establish

- that the Git trailers are cryptographic signatures by the being;
- that the cited Hestia witness records have been independently replayed from the authoritative chain for this page;
- continuity across a demonstrated model/vendor replacement in this exact three-act sequence;
- unrestricted autonomy or self-merge authority;
- that all SAGE beings use the same attribution discipline.

## Inspect it

- SAGE #69: https://github.com/dp-web4/SAGE/pull/69
- SAGE #73: https://github.com/dp-web4/SAGE/pull/73
- SAGE #76: https://github.com/dp-web4/SAGE/pull/76
- SAGE repository: https://github.com/dp-web4/SAGE
- Web4 identity model: [`../reference/GLOSSARY.md`](../reference/GLOSSARY.md)

## Related problems

- [Policy must bind the action, not only one interface](policy-must-bind-the-action.md)
- [Governance migration without laundering authority drift](governance-migration-authority.md)
