# Hub mesh migration — ownership and staged conformance

Status: **staged, not deployed**. Parent: [Web4 #894](https://github.com/dp-web4/web4/issues/894).
This directory is the destination for **portable** host-side mesh contracts, not a
copy of one fleet's installed watcher. The live private-context scripts remain in
place until the public replacement passes independent review and controlled rollout.

## Work packages

| Public work | Private incident/source issues | Portable deliverable | Retain privately |
|---|---|---|---|
| [#981](https://github.com/dp-web4/web4/issues/981) | private-context #48, #50, #51, #56, #86 | Host-independent discovery, primer/runtime version pinning, Linux system+user and Darwin adapters; no gated `/proc` dependency | Machine-specific unit names, paths, service incidents and logs |
| [#982](https://github.com/dp-web4/web4/issues/982) | #49, #52, #53, #82 | Actor/router separation, authenticated reply targets, self-send refusal, polled-receiver truth and distinct seat attribution | Fleet identities, peer maps, credentials, local send evidence |
| [#983](https://github.com/dp-web4/web4/issues/983) | #54, #55, #84 | Durable notification custody and retry lifecycle, post-claim crash recovery, provenance-bound content digest and same-thread accounting | Local queue contents, real receipts, machine state, secrets |

## First migrated contract: authored reply target

`reply_target.py` separates a Hub **router member** (the transport `from`)
from the **canonical being/child author** (authenticated `from_lct`). A
present canonical author wins; a missing author retains legacy router routing.
A *malformed* author must not degrade to the router. This is a pure selection
function, **not an authentication layer and not yet installed in the sender**.

The caller MUST first verify the Hub notice, including provenance/binding of
`from_lct`; then resolve recipient status under Hub law. An unpolled identity
must not be represented as successfully delivered. Do not invoke this function
on user-supplied notice JSON without that authorization. No private keys,
endpoint URLs, machine names, aliases, or local fleet paths belong here.

Run the offline fixture with:

```sh
python3 -m unittest discover -s hub/mesh -p 'test_*.py'
```

The canonical-id shape is the current key-derived `lct:web4:mb32:b...`;
the helper refuses other shapes rather than treating legacy aliases as proven
canonical LCT presence. This does not replace the registry's full identity
resolver or assert that a resolved identity has a consumer.

## Promotion/retirement gates

1. **Read old implementations and tests; classify ownership.** Preserve incident
   facts in private-context and port only reusable code/tests.
2. **Land a bounded public implementation.** Test positive/negative controls on
   canonical and legacy notices, independent author/router identity, and
   malformed metadata. Bind to existing Web4 Hub API instead of introducing a
   parallel permission channel.
3. **Integrate send, receive, and engagement.** For the #84 case, a locally
   `.taken` notice with no committed dispatch outcome is **retryable** after
   crash; the ACK alone does not certify execution. Check replay idempotency,
   durable receipt fsync, and distinct terminal outcomes.
4. **Test installed hosts** on Linux and macOS with current gate posture. Include
   no system-manager bus, no `/proc` grant, old primer/new watcher skew,
   legacy/no-`from_lct` senders, and lease/ACK crashes.
5. **Cutover with receipts.** Keep old scripts until equivalence is demonstrated,
   then retire duplicate executable behavior from private-context with a pointer
   to public commit. Do not close private issues until their exact acceptance
   tests and a deployed version are cited.

No Hestia changes, scope grants, Hub dispatch, or remote deployment are
authorized by this document.
