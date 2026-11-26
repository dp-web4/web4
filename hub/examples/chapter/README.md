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
| `hub-page-agent --every 5` | **The chapter's own assistant.** Wakes when a co-lead asks for a page change, runs Claude with no tools under the operator's own login, and hands the answer to the hub, which keeps it as a draft for a co-lead to publish. Optional: without it, the ask box says the assistant is offline. | `page-agent.json` + a logged-in `claude` CLI |

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

## The front page

`/` is the chapter's own front page once a committee answers its address. It says what the chapter is, what's next, what happened lately, and how to get involved. It never names a person.

It's kept by a **page maintainer**: a co-lead's own AI assistant, appointed from the co-lead's chapter page. The role's law is a norm in the hub law. Its context is a brief the co-leads own. Every change is a governed, recorded act, and any co-lead can undo it. Templates and how-to: [`page-maintainer/`](page-maintainer/). Spec: [`../../docs/PRD_CHAPTER_FRONT_PAGE.md`](../../docs/PRD_CHAPTER_FRONT_PAGE.md).

Co-leads who don't have an assistant of their own, or don't want to paste a link into one, can **ask the chapter's assistant** from their chapter page instead. They type what they want, and they get a draft to look at, publish or ask again about. That's the hub filling the same role with its own agent, run by `hub-page-agent`. Its law is the `CHAPTER-PAGE-AGENT` norm: by default every change it writes waits for a co-lead. Spec: [`../../docs/PRD_CHAPTER_PAGE_AGENT.md`](../../docs/PRD_CHAPTER_PAGE_AGENT.md).

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

## `page-agent.json`

```json
{
  "hub_admin_url": "http://127.0.0.1:8782",
  "claude": "/home/<user>/.local/bin/claude",
  "model": "opus",
  "timeout_secs": 240,
  "max_runs_per_hour": 30,
  "host_label": "pub"
}
```

The runner uses the Claude login of the user it runs as. For a service that shouldn't depend on an interactive login, run `claude setup-token` once and point `oauth_token_file` at a 0600 file holding the token. On a hub run with `HUB_OPERATOR_AUTH=token`, add `"operator_token_file": "<hub dir>/operator.token"`.

What the runner can and can't do:
- It reaches only the hub's job routes. The hub validates each answer against the page's rules and the chapter's law before storing anything.
- The model runs with no tools, MCP servers, settings or hooks, and saves no session. Its only effect is the text it returns.

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
