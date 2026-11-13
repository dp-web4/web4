# Hub public website — first implementation slice

Companion to [member website PRD](../docs/PRD_MEMBER_WEBSITE_FIRST_USER_2026-11-11.md) and Web4 #990/#991.

## What this is
A static, responsive, accessible **public visitor shell**, located in the canonical `web4/hub` tree. It shows the intended member-facing information architecture without fabricating membership, admissions, profiles or witnessed outcomes. It runs without Hestia or private credentials.

Preview locally: from this directory, `python3 -m http.server 8000`, then visit `http://localhost:8000`. This is **not** a production deployment and is not yet served by the Hub daemon.

## Next binding slice (blocking release)
- Render site name, purpose, public charter and governing disclosure from a server-side **public projection**; do not accept browser-supplied law or identity.
- Keep `/admin/*`, operator keys and member-only tools completely outside the public-site bundle and public plane. No browser direct calls to loopback operator APIs.
- Treat locked, maintenance and unavailable states explicitly; never turn an unavailable read into a clean/empty membership claim.
- Add explicit admission choices only after API-level consent, CSRF/replay protection, authentication and authorization tests exist.
- Cross-browser privacy tests: no member-only or self-only profile fields in HTML, preload, cache, logs, or public JSON.
- Add read-only committees/ownership/events backed by governed projections, followed by real officer workflow and channel coexistence.
- Verify reverse-proxy HTTPS, CSP, no unsafe inline scripts, keyboard navigation and mobile before claiming public deployment.

## Acceptance
1. Visitor sees purpose and preview limitations without logging in.
2. No fake join, no member listing, no invented action receipts.
3. No JavaScript or access token is required to render the page.
4. The future live endpoint must pass a fresh-user path on a real chapter, not merely this static preview.
