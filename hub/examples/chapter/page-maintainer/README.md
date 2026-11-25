# Page maintainer: templates

The chapter's front page (`/`) is kept by a **page maintainer**: a role a chapter co-lead fills with their own AI assistant. The spec is [`../../../docs/PRD_CHAPTER_FRONT_PAGE.md`](../../../docs/PRD_CHAPTER_FRONT_PAGE.md).

| File | What it is |
|---|---|
| [`brief.md`](brief.md) | **The role's context.** The default brief every chapter starts with (`{chapter}` becomes the chapter's name). The co-leads own it; their assistant rewrites it with them. It's compiled into the hub as the default. |
| [`law.yaml`](law.yaml) | **The role's law.** The norm that decides what a maintainer may do (allow, escalate or deny), with the R6 fields the hub evaluates. Already in `../../starter-law.yaml`. |
| [`page.example.json`](page.example.json) | **The page's shape**, filled with example content. The hub's tests check it validates. |

## How a co-lead uses it

1. Open your chapter page (the link in your welcome email). Under **Front page**, type what you call your assistant and press **Give my assistant the page**.
2. Copy the message the hub shows you into a conversation with your assistant. It holds the assistant's private link.
3. The assistant reads its instructions at that link: who it acts for, what the chapter's rules allow, the brief, and the page as it is now. Then it asks you what to say.
4. It publishes (or proposes, if the chapter's law says changes wait for a co-lead). You and the other co-leads see each change on your chapter pages, and can undo it or stop the assistant.

## Changing the rules

- **To make every assistant change wait for a co-lead:** in the hub law, change `CHAPTER-PAGE-MAINTAINER`'s `decision` from `allow` to `escalate`, then `hub set-law`.
- **To change the voice, audience or rules:** have your assistant rewrite the brief with you (`POST /a/:token/brief`). That's recorded like a page change.
