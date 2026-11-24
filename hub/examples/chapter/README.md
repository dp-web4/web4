# Chapter kit

A chapter hub does what a volunteer chapter asked for:
- every email to the chapter gets an owner and a backup;
- every event gets owners and backups along the chapter's own pipeline;
- silence goes to the backup, then the leads;
- everyone can see who does what.

Nobody logs in or installs anything, and the chapter keeps its email and Slack.

Product spec: [`../../docs/PRD_CHAPTER_PRODUCT.md`](../../docs/PRD_CHAPTER_PRODUCT.md).

## Pieces

| Process | What it does | Needs |
|---|---|---|
| `hub serve` | The chapter's pages and record. Public plane on 127.0.0.1:8780 behind a tunnel; operator plane on 127.0.0.1:8782, never exposed. | `HUB_PUBLIC_BASE_URL=https://<hostname>`, `HUB_CHAPTER_UTC_OFFSET=-08:00` |
| `hub-nudge --every 300` | Sends nudges and chapter notices (welcome, "your part of this event", recaps) by SMTP, and reports each send to the hub. | `nudge.json` + a 0600 netrc with the sender's app password |
| `hub-intake --every 120` | Reads new mail from the mailbox the chapter's address forwards to, over IMAP, and hands each message to the hub. | `intake.json` + a 0600 netrc with the mailbox login |

## Setting up a chapter

1. **Genesis** on the production profile (see `../../DEPLOY-CLOUD.md`):
   - `hub up <dir> --profile public-tunnel --domain <hostname>`
   - `init "<the chapter's name>"` with `--storage sqlite`
   - `set-law`, `export-public-identity`, `serve`, `unlock`
2. **The starting structure**, from what the chapter already told you: committees, the leads you know, the people you know.
   - Keep that file outside this repository, because it holds real addresses. `example-chapter.json` shows the format.
   - A committee with no known lead starts with the chapter leads as its leads. They hand it on from their page.
   ```
   python3 seed.py --chapter <chapter.json> --admin http://127.0.0.1:8782 \
     --token-file <dir>/operator.token --invite <chapter-lead-tags>
   ```
3. **Start `hub-nudge`.** Only the invited chapter leads get a welcome, with their own chapter page. From there they:
   - fix anything wrong (move people, make someone a lead, start a committee);
   - add people;
   - press **Send the welcome** when they want the rest of the team in.

   Nobody hears from the tool before a chapter lead has decided they should.
4. **Start `hub-intake`** against the mailbox the chapter's address forwards to. From then on, every email to the chapter becomes a job for the committee that answers it.

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

A netrc file looks like `machine smtp.gmail.com login chapter@example.org password <app password>`. Keep it 0600 and never commit it.

## What changes for the chapter

1. **"Inbound emails get missed."**
   - Each email to the chapter goes to one person, with a backup, as a single email with a link.
   - The page shows the message, a **Reply from your email** button, and **I've answered it**.
   - If it isn't theirs, one tap passes it to the right committee.
2. **"Each event is owned by one person, with no backup."**
   - A lead plans an event with one form.
   - The chapter's pipeline becomes the checklist:
     - the prospectus, for the two people running it;
     - venue and sponsors, for Partnerships;
     - the marketing plan and Luma page, for Marketing;
     - speakers and the day-of.
   - Each person gets one email listing their part.
3. **"Nothing happens when nobody acts."** A step whose date passes with nobody on it goes to its backup, then to the committee leads. An unanswered email does the same after a day.
4. **"Who do I ask?"** Every chapter page shows each committee, its leads, and who owns each open job.
5. **After an event,** closing it sends the committee a plain-language recap.
