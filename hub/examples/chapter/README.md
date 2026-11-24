# Chapter kit

Everything needed to stand up a chapter hub that does what the chapter asked for:
- every email to the chapter gets an owner and a backup;
- every event gets an owner, a backup and a checklist;
- silence goes to the backup, then the leads;
- everyone can see who does what.

Product spec: [`../../docs/PRD_CHAPTER_PRODUCT.md`](../../docs/PRD_CHAPTER_PRODUCT.md).

## Pieces

| Process | What it does | Needs |
|---|---|---|
| `hub serve` | The chapter's pages and record. Public plane on 127.0.0.1:8780 behind a tunnel; operator plane on 127.0.0.1:8782, never exposed. | `HUB_PUBLIC_BASE_URL=https://<hostname>`, `HUB_CHAPTER_UTC_OFFSET=-08:00` |
| `hub-nudge --every 300` | Sends nudges and chapter notices (welcome, "you're on this event", recaps) by SMTP. Reports each send to the hub. | `nudge.json` + a 0600 netrc with the sender's app password |
| `hub-intake --every 120` | Reads new mail from the chapter's intake mailbox over IMAP and hands each message to the hub. | `intake.json` + a 0600 netrc with the mailbox login |

## Stand it up (synthetic chapter first)

1. Genesis on the production profile (see `../../DEPLOY-CLOUD.md`, and pub's rehearsal record): `hub up <dir> --profile public-tunnel --domain <hostname>`, then `init` with `--storage sqlite`, then `set-law`, `export-public-identity`, `serve`, `unlock`.
2. Seed the made-up chapter, sending every email to one inbox you read:
   ```
   python3 seed.py --chapter synthetic-chapter.json --admin http://127.0.0.1:8782 \
     --token-file <dir>/operator.token --inbox you@example.org --links
   ```
3. Start `hub-nudge`. The welcome emails go out on its first pass. Each one carries that person's chapter page.
4. Point `hub-intake` at the intake mailbox. Send it an email, and within two minutes the inbox committee's first person gets "Email: <subject>: you're named as the owner".

## `nudge.json`

```json
{
  "hub_admin_url": "http://127.0.0.1:8782",
  "smtp_url": "smtps://smtp.gmail.com:465",
  "from": "Chapter <chapter@example.org>",
  "operator_address": "operator@example.org",
  "netrc_file": "/home/<user>/.config/chapter-hub/smtp.netrc",
  "state_file": "/home/<user>/.local/state/chapter-hub/nudge-state.json"
}
```

## `intake.json`

```json
{
  "hub_admin_url": "http://127.0.0.1:8782",
  "imap_url": "imaps://imap.gmail.com:993/INBOX",
  "netrc_file": "/home/<user>/.config/chapter-hub/imap.netrc",
  "state_file": "/home/<user>/.local/state/chapter-hub/intake-state.json",
  "ignore_from": ["chapter@example.org"],
  "backfill_days": 1
}
```

A netrc file looks like `machine smtp.gmail.com login chapter@example.org password <app password>`. Keep it 0600, and never commit it.

## The demo, in the chapter's own words

1. **"Inbound emails get missed."** Send an email to the chapter address. The person on inbox duty gets one email with a link. The page shows the message, a **Reply from your email** button, and **Pass to Partnerships**. Press it: Partnerships' lead and backup are emailed, and the record shows who passed it where.
2. **"Each event is owned by one person, with no backup."** A lead opens their chapter page, plans "December social" (name, date, owner, backup), and the checklist appears. The owner and backup get one email each.
3. **"Nothing happens when nobody acts."** On a job page, the owner presses **I'm stuck**, and the backup's phone gets an email at once. A job nobody answers moves on its own when its window runs out.
4. **"Who do I ask?"** Any chapter page shows every committee, its leads, and who owns each open job.
5. **After the event,** the owner presses **close it**, and the committee gets the recap.

At no point does anyone log in, install anything, or leave email.
