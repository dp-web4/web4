# Open-issue review — 2026-11-03

Scope: all 36 open Web4 issues, oldest first. Every issue was triaged from its body, activity and linked work. Closure/update candidates were checked against acceptance text, PR evidence and, where useful, current source. Cross-repository issue-number mentions and evidence-only PRs were not treated as implementations. No issue was closed for age alone.

## Actions

- Reopened #709 after independent review. #792 landed the Hub defence-in-depth half, but Hestia #481 and #716 do not explicitly prove the issue's induced-write refusal and escalation criterion for the Hub deploy closure. That acceptance remains open; the earlier closure was incorrect.
- Deploy closure: #709 remains open for gate-enforced refusal and escalation of systemd/ExecStart, deploy-script, staged-artifact and ratification-manifest writes.
- Closed #817 as moved. The Hub route is intentionally operator-only on the public plane; the remaining client defect now lives in Hestia #1493, which requires sealed-channel roster resolution and joined-vs-connected error semantics.
- Narrowed #818 to the two remaining defects: optional join names and no governed post-admit member-profile amendment.
- Narrowed #867 to the remaining mailbox work after #869: consumer/sender dedupe, retention/compaction and legacy migration. Durable acceptance and authenticated fetch/ACK are no longer presented as unimplemented.
- Narrowed #904 to Hub Phase 3. The crates and Hestia v0.3.0 are released; #971 remains the release-path dependency.

## Remaining open work

- Deferred design record: #458. Its own activation condition has not occurred; it is not presented as an implementation blocker.
- Sponsor/discovery/product delivery: #707, #749, #798, #799, #800, #814, #820, #918, #921.
- Custody and assurance: #729, #730, #858, #859, #919. These retain concrete missing evidence carriers, law-enforcement or containment work.
- Implementation and architecture: #795, #816, #831, #862, #874, #875, #879, #881, #884, #894, #932.
- Repository Plane: #886, #887, #888, #889. #890/#891 are bootstrap/discovery documents, not the adapter, Gitea parity matrix, one-gate mapping or sovereign seed lifecycle.
- Rights/provenance: #901. A conclusion affecting grants still requires rights-holder/counsel review.
- Release: #904, narrowed as above.

## Evidence notes

- #816 remains reproduced in source: `web4-trust-core/Cargo.toml` still declares `crate-type = ["cdylib", "rlib"]`, the hashless-artifact collision described by the issue.
- #818's message carrier is implemented, but `JoinPayload.name` remains optional and no post-admit profile amendment path was found.
- #867's #869 implementation is substantial but explicitly partial; it was not used as grounds to close the larger consumer-durability contract.
- #874/#875 have merged identity/spec slices but still have staged resolver, lifecycle and convergence work.
- #904's Hub release PR #971 is open, so the ecosystem plan is not complete.
