# Web4 Community Hub — Chapter Law

The chapter's **charter** is the constitutional document the Sovereign signs at chapter founding. It's plain-text-with-structure (JSON in MVP) and lives at `<chapter-dir>/charter.json`. Its sha256 hash is stored in `society.json`'s `charter_hash` field, so any tampering with the charter invalidates the society state's link to it.

## What's in the default charter

`hub init` writes a minimal default:

```json
{
  "schema_version": "0.1",
  "chapter_name": "Your Chapter Name",
  "founded_at": "2026-06-07T17:36:21.939166474Z",
  "founding_sovereign_lct_id": "...",
  "preamble": "This is the founding charter of...",
  "rules": [],
  "amendments": []
}
```

The default `preamble` says the chapter is constituted as a Web4 society, operates by chapter law, and amends via the witnessed process the law itself defines. That's enough to legitimately operate but doesn't say much about how *your* chapter actually wants to work.

## What chapter law should cover (suggested topics)

The Web4 spec leaves chapter law unspecified by design — each chapter is sovereign. A practical starter set of topics:

### Member admission

- Who can become a Citizen? (open, invite-only, vetted, etc.)
- What's the process? (self-application, sponsor-required, vote, etc.)
- What information is shared on admission? (skill declarations? affiliations?)

### Member departure + removal

- Voluntary departure: what triggers `MemberRemoved`? (formal request? inactivity threshold?)
- Involuntary removal: under what conditions? Who decides? (Sovereign? Policy Entity? majority of other members?)
- What happens to T3 / skill declarations on departure?

### Role rotation

- How often are roles rotated? (annually? on request? never?)
- Who can nominate a role-filler? Who confirms? (Sovereign? existing role-holder?)
- What's the consent step? (assignee LCT signs acceptance — already enforced by `hub assign-role`)

### Treasury policy

- What gets reified as ATP? (sweat-equity hours? sponsor inflow? attendance?)
- Who can authorize ATP allocations? (Treasurer alone? Treasurer + Sovereign?)
- What's the conservation invariant in practice? (just the technical sum-preservation, or also "no chapter ATP leaves without recorded justification")

### Events

- What counts as a recordable chapter event? (only chapter-organized? affiliated meetups too?)
- Who's authorized to record events? (Administrator? Anyone with Citizen?)
- What attendance attestation is acceptable? (self-report? door-check? RSVP confirmed?)

### Amendments

- How does the charter get amended? (Sovereign-only? Sovereign + chapter vote? consensus of N role-holders?)
- What's the proposal-and-review window? (immediate? 7 days? 30 days?)
- How are amendments recorded? (Already enforced: each amendment is a `CharterAmended` ledger entry; the new `charter_hash` replaces the old one in `society.json`.)

### Federation

- What's the chapter's posture toward federation with other chapters? (open / curated / closed)
- Who can negotiate inter-society protocols? (Sovereign? Witness?)
- How are imported reputation tensors weighted? (Full trust? Capped? Per-source override?) — V2 feature; this column will matter when the inter-society protocol is exercised.

## How to amend the charter

1. **Edit `<chapter-dir>/charter.json`** directly. Add rules to the `rules` array, modify the preamble, etc. (V2 will provide a structured CLI for this; MVP is hand-edit.)
2. **Compute the new hash** — when you run any `hub` command that touches the chapter, it'll catch a hash mismatch on read. The official path:
   ```bash
   # Hand-compute would be:
   #   python3 -c "import json,hashlib; c=json.load(open('charter.json')); print('sha256:'+hashlib.sha256(json.dumps(c,separators=(',',':')).encode()).hexdigest())"
   # But MVP doesn't have a `hub amend-charter` command yet — V2.
   ```
3. **Record a `CharterAmended` event in the ledger** with the new hash. **MVP gap**: there's no CLI for this yet (would be `hub amend-charter <chapter-dir> --diff-summary "..."` or similar). For now the recommended flow is to leave the charter at its default and document chapter law externally (e.g. in a markdown doc in the chapter dir alongside the charter) until V2 ships the amendment flow.

## What chapter law is NOT

- Not a binding legal document outside the chapter's own membership.
- Not a substitute for actual law (employment, finance, etc. as applicable to the chapter's operations).
- Not consulted by the Hardbound policy engine in MVP (that's V2 — once Hardbound's canonical Web4 alignment debt is resolved, the Policy Entity role can mechanically enforce machine-readable rules from the charter).

For MVP, chapter law is **social infrastructure** — the agreed-upon way the chapter operates, witnessed and tamper-evident via the ledger but enforced by chapter members' good faith.

## Template

A starter charter for a community chapter might look like:

```
Preamble: This is the founding charter of <Chapter Name>. The chapter is
constituted as a Web4 society for the purpose of advancing AI literacy,
community engagement, and humans-in-the-loop AI development at the
<location/scope>. Members hold portable identity (LCT) and accrue
reputation (T3/V3) by attested contribution.

Rules:
  1. Membership is open to anyone who attends a chapter event in good
     standing and requests admission.
  2. The chapter holds at least one public event per month.
  3. Event attendance is recorded as a witnessed ledger entry by the
     Administrator role within 7 days.
  4. Charter amendments require the Sovereign's signature and a 14-day
     notice period to current Citizens.
  5. The chapter federates with other community chapters per the Central
     overlay protocol (when Central is established).

Treasury policy:
  - 1 ATP = 1 hour of attested chapter work (event organizing, mentorship,
    code contribution to chapter projects).
  - Sponsor inflow is reified at par with the sponsor's stated value.
  - ATP allocations require Treasurer signature.

Amendment process:
  - Sovereign proposes amendments.
  - 14-day notice via chapter Slack + email.
  - Sovereign signs to ratify; CharterAmended event recorded.
```

Adapt to your chapter's needs. The hub's job is to witness whatever you decide; the deciding is yours.
