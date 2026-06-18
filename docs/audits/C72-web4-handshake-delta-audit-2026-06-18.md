# C72 — `protocols/web4-handshake.md` Delta Re-Audit (first delta; prior C28)

**Date**: 2026-06-18
**Auditor**: autonomous web4 session (legion, firing `120047`, LEAD voice)
**Target**: `web4-standard/protocols/web4-handshake.md` (238 lines; header `Last-Updated: 2026-06-03T06:00:00Z`)
**Series**: C72 — **first delta re-audit**. Prior audit **C28** (2026-06-03); remediation **#265** (`8b3bbac3`, +6/−6) closed 4 autonomous §B findings; file byte-stable since. This is the alternation **AUDIT** turn following the C71 registries remediation (#354, merged `3f1d6fad`).

**Methodology** (per the standard delta-re-audit method):
- **§A** — prior-finding verification: the 4 C28 §B fixes + INFO1 held? + regression sweep + **remediation-completeness** (C56 token-by-token, since the file is byte-stable since #265) + **bidirectional re-verification** of every C28 §C design-Q/cross-track carry against the **current (post-C68/C70/C71) corpus**.
- **§B** — multi-agent finder workflow (`wf_561f87bb-c8b`, 7 primitive lenses + adversarial refute-by-default verify): **27 raw → 22 upheld / 5 refuted**, deduped at synthesis.
- **§C** — disposition / routing (autonomous → C73 / design-Q → operator / cross-track).

**Authority anchors re-read this session** (re-read, not recalled):
- `web4-standard/protocols/web4-handshake.md` (full, L1–L238)
- `core-spec/core-protocol.md` §1 suite table (3 suites) + §2 handshake block (4-msg-MAC flow)
- `registries/initial-registries.md` cipher suites L5–L7 (now **3** suites incl. W4-IOT-1, post-C71) + error codes L52
- `core-spec/errors.md` §2.4/§2.6/§5 (AUTHZ status mapping; PROTO_* codes)
- `core-spec/data-formats.md` §4 pairwise-W4ID derivation (`salt = sha256(peer_id)`, `w4id:pair:` form)
- `implementation/sdk/web4/protocol.py` ClientHello/ServerHello (4-msg-MAC field set)
- `implementation/reference/web4_demo.py` L47/L88–L90 (session-key derivation)
- `testing/test-vectors/protocol/core-protocol.json` (4-msg-MAC vector) + `testing/test-vectors/handshakeauth_{cose,jose}.json` (3-msg-sig vectors)
- `profiles/edge-device-profile.md` L18 (mandates `W4-IOT-1`)

---

## Summary

**Headline 1 — bidirectional carry resolution.** C28's **C-M2** (W4-IOT-1 a registry *orphan*) has **MOVED**: C71's registries remediation (#354) **registered** W4-IOT-1, so registry L7 **and** core-protocol §1 **and** `edge-device-profile.md` L18 all now carry/require it. `web4-handshake.md` §3 (lists only W4-BASE-1 / W4-FIPS-1) is now the **lone corpus document missing the registered suite**. The C28 "decide if it's real" design-Q is settled by merged operator-ratified #354 → **aligning handshake §3 is now autonomous-actionable** (suites-1).

**Headline 2 — the test-vector corpus is itself split on the C-H1 flow design-Q.** C28 framed C-H1 as "3 anchors (core-protocol + SDK + vectors) implement the 4-msg-MAC flow; handshake.md alone specifies the 3-msg-sig flow." Re-reading the vectors shows the vector corpus is **split**: `core-protocol.json` backs the 4-msg-MAC flow, but `handshakeauth_{cose,jose}.json` implement handshake.md's **3-msg-sig HandshakeAuth**. So the corpus does *not* uniformly back one handshake — it has conformance vectors for **both**. This **deepens** C-H1 (it is not "1 vs 3"; both flows have spec text + vectors) and does **not** resolve it. **Still design-Q, operator-owned.**

**Headline 3 — §B flagship (new): §6.2 session-key derivation is non-interoperable as written.** §6.2 derives `k_send, k_recv` from a **single direction-agnostic** `HKDF-Expand(info="W4-SessionKeys:v1", L=2*keylen)` split positionally. Both peers compute the identical output and identical split, so `A.k_send == B.k_send` and `A.k_recv == B.k_recv` — A's send key is **not** B's receive key, so two spec-faithful peers cannot decrypt each other. The bare assertion "Keys MUST be independent for each direction" (L186) is true *within* a peer but binds no half to a *direction across* peers. The repo's own reference implementation (`web4_demo.py` L89–90) **silently fixes** this with two directional labels `W4-SessionKeys:I->R` / `W4-SessionKeys:R->I` — a derivation materially different from the spec text. **Autonomous** (align §6.2 to the established reference scheme).

**§A result**: 4/4 C28 §B fixes **HELD**, INFO1 held, **0 regression** from the +6/−6 #265 diff. Bidirectional: **C-M2 MOVED** (→ autonomous), **C-H1 / C-M1 / C-M3 OPEN** (re-confirmed, C-H1 deepened by the vector split).

**§B result**: 27 raw → **22 upheld** / 5 refuted, deduped to **15 distinct** findings (0 HIGH-autonomous; 1 HIGH design-Q; 7 MED; 5 LOW; 2 INFO).

**Routing**: **10 autonomous** (→ C73 remediation on handshake.md) / **4 design-Q** (operator; incl. the 3 carried C28 §C items) / **5 cross-track** (test-vector regen + errors.md SSOT).

---

## §A. Prior-Finding Verification (C28)

### §A.1 — The 4 autonomous §B fixes (remediation #265) — all HELD

| C28 ID | Fix | Current state | Verdict |
|--------|-----|---------------|---------|
| B-M1 (MED) | GREASE `*a*a*a*a` mask → RFC 8701-style random, no fixed mask | §5.0 L66–69: "8 hex digits chosen uniformly at random… there is no fixed reserved value or mask (RFC 8701-style)"; examples `1a2a3a4a`/`fafbfcfd` no longer claim mask-conformance | **HELD** |
| B-M2 (MED) | Add `w4_sig_*@1` ext to worked Hellos | §5.1 ext L85 = `[w4_sig_cose@1, w4_sig_jose@1, …]`; §5.2 ext_ack L100 = `[w4_sig_cose@1, …]` (server selects +cbor → cose) | **HELD** |
| B-L1 (LOW) | `WaitClientHello` prose vs diagram | §8 L207: "The Responder runs the mirror-image flow (receive ClientHello → send ServerHello → receive and verify `HandshakeAuth` → `Established`)" | **HELD** |
| B-L2 (LOW) | "plaintext JSON" label | §5.1 L77: "shown as JSON for readability; serialized per the negotiated media type — CBOR is MTI" | **HELD** |
| B-INFO1 | Stale date | L2 = `2026-06-03` | **HELD** |

**Regression sweep**: the #265 diff was +6/−6, single-file, no cross-spec surface. No HELD fix introduced a new defect. **0 regression.** (Per the [[feedback_remediation_introduced_regression]] discipline, the §B finder fleet was fed the HELD + DEFERRED lists so it would not re-report them as new; it did not.)

**Remediation-completeness (C56 method)**: re-read each #265 claim token-by-token against the file. B-M2's claim "server selects +cbor → cose" is internally consistent (ServerHello `media=application/web4+cbor`, `ext_ack` carries `w4_sig_cose@1`, drops `w4_sig_jose@1` — correct negotiation). No incomplete remediation-site found (contrast C56-A1/C64-A.1).

### §A.2 — Bidirectional re-verification of the 4 C28 §C carries

| C28 ID | C28 status | Current corpus | C72 verdict |
|--------|-----------|----------------|-------------|
| **C-M2** (W4-IOT-1 orphan + P-256 spelling) | cross-track | **W4-IOT-1 now registered** (registry L7, C71 #354) + in core §1 + mandated by `edge-device-profile.md` L18. handshake §3 is the lone omitter. | **MOVED → autonomous** (suites-1). P-256 spelling (`P-256EC` handshake / `P-256ECDH` core / `P-256 ECDH` registry) **still 3-way**, handshake the outlier — folds into C68 B-7 cross-track. |
| **C-H1** (3-msg-sig vs 4-msg-MAC canonical handshake) | design-Q (=C27-H2) | core §2 still 4-msg-MAC; handshake still 3-msg-sig; **vector corpus now seen to be split** (`core-protocol.json` 4-msg-MAC; `handshakeauth_*` 3-msg-sig). | **OPEN — deepened.** Both flows have spec text **and** vectors. Operator-owned. **NEVER auto-action.** |
| **C-M1** (nonce 96 vs 256 vs 48-bit) | design-Q (=C27-M3) | handshake `<random 96-bit>`; core/SDK `nonce[32]`; vector 48-bit; unchanged. New sub-evidence: §9/§6.1 overload the name across 3 distinct fields (nonce-1). | **OPEN** — design-Q. |
| **C-M3** (W4IDp surface form `w4idp-<base32>`) | design-Q/cross-track | handshake `w4idp-<base32>`; data-formats `w4id:pair:<base32>` (L95); SDK `w4id:key:`; grammar `did:web4:`. Re-confirmed divergent + now coupled to a **salt-derivation contradiction** (w4idp-2) and a **hint/final naming asymmetry** (msgshape-4/w4idp-5). | **OPEN — hardened.** Identifier-scheme bundle (C27-H1 + C24-H1). |

---

## §B. Finder Workflow Findings (deduped, verified)

`wf_561f87bb-c8b` — 7 primitive lenses (message-shape, nonce-freshness, suites-grease, signature-profiles, w4idp-identifiers, errors-status, statemachine-rekey) → adversarial refute-by-default verify. 27 raw → 22 upheld → **15 distinct** after synthesis dedup.

### Autonomous-actionable (→ C73 remediation on handshake.md)

**B1 (MED) — suites-1 — add W4-IOT-1 (MAY) to §3** *[C-M2-MOVED headline]*
§3 (L20–23) lists only W4-BASE-1 / W4-FIPS-1. W4-IOT-1 is now registered (registry L7), in core §1, and mandated by `edge-device-profile.md` L18. handshake.md is the lone omitter. **Fix**: add row `| W4-IOT-1 (MAY) | X25519 | Ed25519 | AES-CCM | SHA-256 | CBOR |` mirroring core §1 / registry L7. (Decision already merged via #354; no design choice remains.)

**B2 (MED) — sm-rekey-1 — §6.2 session keys are non-interoperable** *[§B flagship]*
§6.2 (L182–186) derives `k_send, k_recv` from one direction-agnostic `HKDF-Expand(info="W4-SessionKeys:v1", L=2*keylen)`. Both peers compute the identical output + split → `A.k_send == B.k_send`, so A→B traffic is undecryptable by a spec-faithful B. Reference impl `web4_demo.py` L89–90 uses directional `W4-SessionKeys:I->R` / `R->I`. **Fix**: rewrite §6.2 to two directional expands (`k_i2r = HKDF-Expand(exporter, info="W4-SessionKeys:I->R", L=keylen)`, `k_r2i = …"R->I"`), matching the reference impl; map send/recv by role. *Confine the edit to §6.2's KDF info-label/split so it does not prejudge C-H1.*

**B3 (MED) — msgshape-2 — §6.1 HandshakeAuth example is not a valid §6.0.3 COSE_Sign1 envelope**
§6.1 (L162–175) shows a flat map with `kid`/`alg`/`sig` as sibling payload fields. §6.0.3 (the MTI profile) puts `kid`/`alg(=-8)`/`content-type` in **protected headers** and signs the map "excluding any `sig`/envelope fields" (L139). The §6.1 shape can't be emitted as the §6.0.3 wire envelope; `handshakeauth_cose.json` confirms the collision (kid/alg in both protected_headers and payload). **Fix**: reshape the §6.1 example as the concrete instance of §6.0.3 (kid/alg/content-type → protected headers; sign payload excluding sig; detached sig) + cross-ref §6.0.3.

**B4 (MED) — nonce-1 — §9 replay rule doesn't say which `nonce` it tracks**
§9 L210 "`nonce` values MUST be unique per key; maintain a replay window" — but the file defines **three** `nonce` fields (ClientHello L86, ServerHello L102, HandshakeAuth L173) with different roles, and §9 names neither the tracked field nor the "key" that scopes uniqueness. **Fix**: name the HandshakeAuth `nonce` (§6.1) explicitly as the replay-tracked value and scope the cache to the HPKE context_key lifetime.

**B5 (MED) — nonce-2 — HandshakeAuth `nonce`/`ts` are not in the signed input**
§6.1 sig covers `Hash(TH || channel_binding)` (L170); TH is frozen at the Hellos (L107–108). So the HandshakeAuth `nonce` (L173) / `ts` are **not** integrity-protected by the signature, yet §6.1 L177 requires receivers to "check freshness" and §9 runs anti-replay on them. Their integrity rests only on the AEAD context_key, which the spec never states. **Fix**: either fold `nonce`/`ts` into the signed input, or state that their integrity is provided by the AEAD envelope.

**B6 (MED) — w4idp-3 — §4.1 HKDF-Expand has no output length `L`**
§4.1 (L34–37) `w4idp = MB32(HKDF-Extract-Then-Expand(salt=peer_salt, IKM=sk_master, info="W4IDp:v1"))` omits the HKDF-Expand output length, so the encoded W4IDp length is implementation-defined (two conformant impls derive different-length IDs). Contrast §6.2 which *does* set `L`. data-formats truncates to 16 bytes (L95). **Fix**: add explicit `L` to §4.1 (e.g. `L=16`) reconciled with data-formats. *(Couples to the C-M3 identifier bundle but the missing-`L` defect is fixable independent of the surface-form decision.)*

**B7 (LOW) — msgshape-1 — §6.0.1 references a server-side `ext` field that doesn't exist**
§6.0.1 L121 says negotiation is "performed via `media` and `ext` in ClientHello/ServerHello" — but ServerHello carries `ext_ack` (L100), not `ext`. **Fix**: "… via `media` and `ext` in ClientHello / `ext_ack` in ServerHello".

**B8 (LOW) — msgshape-5 — `cap.ext` is an undisambiguated third `ext`-stem slot**
HandshakeAuth carries nested `cap.ext` (L171) atop ClientHello `ext` (L85) and ServerHello `ext_ack` (L100); the doc never distinguishes capability-grant extensions from the suite/profile negotiation channel. **Fix**: one sentence distinguishing `cap.ext` (authenticated capability-grant extensions) from the `ext`/`ext_ack` negotiation channel.

**B9 (LOW) — nonce-3 — §9 replay-window retention is unbounded relative to the `ts` band**
§9 L211 accepts `ts` within ±300s (a 600s band) but L210 gives the nonce cache no retention floor; to actually stop replays the cache must retain ≥ the acceptance band. **Fix**: "The replay window MUST retain entries for at least the `ts` acceptance band (≥300s)."

**B10 (LOW) — sig-4 — `channel_binding` serialization is undefined**
§6.0.5/§6.1 sign `Hash(TH || channel_binding)` with `channel_binding` "include both HPKE ephemeral keys" (L176), but no clause fixes the byte order of the two epks, length-prefixing, or the `TH || channel_binding` concatenation — two conformant impls can compute different signing inputs. **Fix**: add one normative sentence, e.g. `channel_binding = epk_I || epk_R` (initiator first, raw KEM-public-key bytes), signing input `= Hash(TH || channel_binding)` under the §3 suite Hash. *(Obvious convention; autonomous. Couples to B2's directional concern — apply consistently.)*

### Design-Q (operator)

**D1 (HIGH) — w4idp-1 — `peer_salt` MUST be exchanged in the handshake, but no message carries it**
§4.2 L45 makes `peer_salt` exchange a MUST and it is the load-bearing input to the §4.1 W4IDp derivation — but neither ClientHello (§5.1) nor ServerHello (§5.2) defines a salt field (`grep salt` → only L34/L43–45). A conformant implementation literally cannot perform the §4.1 derivation. **Why design-Q (not autonomous)**: the fix couples to D2 — handshake's own §4.2 says salt is random+exchanged, but data-formats derives it deterministically (no exchange), so you cannot just add a field without picking the canonical derivation. Couples to the C-M3 identifier bundle.

**D2 (MED) — w4idp-2 — two mutually exclusive salt-derivation schemes for the same pairwise identifier**
handshake §4.2 L43–44: `peer_salt` MUST be 128-bit **random**, MUST NOT be derived from stable identifiers. data-formats §4.1 L88 / §4.2 L102: `salt = sha256(peer_identifier)` — **deterministic**, derived from the (stable) identifier, no exchange. These cannot both be canonical. **Operator picks**: (A) random+exchanged (handshake; unlinkable; needs the D1 field) vs (B) deterministic `salt=H(peer_id)` (data-formats; no exchange; weaker unlinkability). Settles D1 in the same stroke; couples C-M3.

**D3 (carried) — C-H1 / C-M1 / C-M3** — re-confirmed OPEN (see §A.2). C-H1 deepened by the split vector corpus. Bundle with C27-H1/H2 + C24-H1.

**D4 (INFO/coordination) — errors-status-3 — §10 `W4_ERR_AUTHZ_DENIED@401`**
The §10 worked example (`401`, `about:blank`, `W4_ERR_AUTHZ_DENIED`, `web4://…`) is byte-consistent with errors.md §2.4/§5 as currently written — **not a new contradiction**. Movement note: it is a registered downstream site of the open errors-layer **B-1** design-Q (recommend 403). If operator picks 403, update §10 status/code in the coordinated change set (errors.md + test vector + SDK + registry + handshake §10).

### Cross-track

**X1 (MED) — handshakeauth vector regeneration** *(test-vector maintainer)* — consolidates msgshape-3 + sig-1 + sig-3.
`handshakeauth_{cose,jose}.json` diverge from §6.1/§6.0.5 on three counts: (a) they carry a literal `th` payload field the §6.1 shape doesn't define and **sign the payload bytes** rather than `Hash(TH || channel_binding)`; (b) they **omit `nonce`** (§6.1 L173) and `cap.ext` (L171); (c) no `channel_binding` (= both HPKE epks). **Fix**: regenerate to sign `Hash(TH || channel_binding)`, restore `nonce`/`cap.ext`, drop the literal `th` field — OR, if a literal `th` field is intended, that is a design-Q (add to §6.1 + reconcile §6.0.5). Couples to B2/B3/B10 (resolve the spec shape first, then regenerate).

**X2 (LOW) — sig-2 — JOSE vector `alg` self-contradiction** *(vector maintainer)*
`handshakeauth_jose.json`: protected_header `alg="ES256"` (correct per §6.0.4) but payload `alg="EdDSA"`. **Fix**: set payload `alg="ES256"`, regenerate `payload_b64`/`signing_input`/`signing_input_sha256`.

**X3 (LOW) — sig-5 — JOSE vector `typ="JWT"`** *(vector maintainer)*
A HandshakeAuth is a Web4 message, not a JWT claims set; `typ="JWT"` invites JWT-claims tooling to mishandle it; §6.0.4 specifies no `typ`. **Fix**: set `typ` to a Web4 value (`application/web4+json`) or omit; optionally pin in §6.0.4.

**X4 (MED) — errors-status-1 + errors-status-2 — `W4_ERR_PROTO_FORMAT` absent from errors.md SSOT** *(= C70 B-C1; errors.md owner)*
handshake §6.0.7 L160 makes `W4_ERR_PROTO_FORMAT` a MUST-abort code and §13 cites `initial-registries.md` as the registry. The code IS in the registry (L52, name+description only) but is **absent from `errors.md` §2.6** (which lists VERSION/SEQUENCE/REPLAY/DOWNGRADE) — and errors.md §1 mandates a `status` member every error must have, which PROTO_FORMAT has nowhere. **Fix**: add `W4_ERR_PROTO_FORMAT` to errors.md §2.6 (Status 400, "Protocol Format Mismatch"). This is the same class as C70's `WITNESS_REQUIRED`/`PROTO_FORMAT`-missing-from-errors.md carry.

### Refuted / duplicate (5) — recorded so they are not re-raised

- **suites-2** (duplicate of C28 B-INFO / table convention) — §3 5-col table with KDF as prose at L25; not a new defect.
- **suites-3** (refuted) — §3 L25–26 suite-GREASE MUST is unambiguous; no normativity asymmetry.
- **w4idp-4** (refuted) — §4.2 L50 "≥4 concurrent W4IDp" vs §5 singular field is guidance-vs-wire, not a contradiction (a message carries one identifier; the cache holds ≥4).
- **sm-rekey-2** (refuted) — misread §6.0.7 PROTO_FORMAT abort scope (it is signature-profile mismatch, correctly scoped).
- **sm-rekey-3** (refuted) — §8 diagram vs key-lifecycle granularity is taste, not a defect.

---

## §C. Disposition / Routing

| ID | Sev | Class | Route |
|----|-----|-------|-------|
| B1 suites-1 | MED | **autonomous** | Add W4-IOT-1 (MAY) row to §3 *(C-M2-MOVED)* |
| B2 sm-rekey-1 | MED | **autonomous** | §6.2 directional key derivation → match `web4_demo.py` *(flagship)* |
| B3 msgshape-2 | MED | **autonomous** | §6.1 HandshakeAuth example → valid §6.0.3 COSE_Sign1 envelope |
| B4 nonce-1 | MED | **autonomous** | §9 name the replay-tracked nonce + scope |
| B5 nonce-2 | MED | **autonomous** | HandshakeAuth nonce/ts freshness integrity (sign or state AEAD) |
| B6 w4idp-3 | MED | **autonomous** | §4.1 add HKDF-Expand output length `L` |
| B7 msgshape-1 | LOW | **autonomous** | §6.0.1 `ext` → `ext`/`ext_ack` per message |
| B8 msgshape-5 | LOW | **autonomous** | §6.1 disambiguate `cap.ext` vs `ext`/`ext_ack` |
| B9 nonce-3 | LOW | **autonomous** | §9 replay-window retention ≥ ts band (300s) |
| B10 sig-4 | LOW | **autonomous** | §6.0.5 fix `channel_binding` serialization |
| D1 w4idp-1 | HIGH | **design-Q** | peer_salt has no carrier field (couples D2 + C-M3) |
| D2 w4idp-2 | MED | **design-Q** | random-salt (handshake) vs `H(peer_id)` (data-formats) |
| D3 C-H1/C-M1/C-M3 | HIGH/MED | **design-Q** | carried; C-H1 deepened by split vectors |
| D4 errors-status-3 | INFO | **design-Q** | §10 AUTHZ_DENIED@401 rides errors B-1 |
| X1 vectors | MED | **cross-track** | regenerate handshakeauth_{cose,jose} (sign Hash(TH‖cb), restore nonce/cap.ext) |
| X2 sig-2 | LOW | **cross-track** | JOSE vector payload alg EdDSA→ES256 |
| X3 sig-5 | LOW | **cross-track** | JOSE vector typ=JWT |
| X4 errors PROTO_FORMAT | MED | **cross-track** | add to errors.md §2.6 (= C70 B-C1) |

**No spec/SDK/vector edits made this turn** (audit turn). The **10 autonomous** items are internal to handshake.md and queued for the next REMEDIATION turn (**C73**). B2 and B10 touch key-derivation / signing-input — confine each edit to its own clause so neither prejudges the C-H1 flow design-Q. The **4 design-Q** items bundle with the open C27-H1/H2 + C24-H1 carries; **D1+D2 should be adjudicated together** (the salt-source decision settles both and feeds C-M3). The **5 cross-track** items route to the test-vector maintainer (X1–X3) and the errors.md owner (X4 = C70 B-C1).

**Next turn = REMEDIATION (C73)**: apply the 10 autonomous findings to `web4-standard/protocols/web4-handshake.md`. After C73, handshake.md will have its first full delta cycle (C28→#265→C72→C73).
