# Constellation Enrollment Registry — closing the network self-authentication hole

**Status:** design + Phase 1 (2026-07-21) · **Repos:** web4 (hub), hestia (driver)
**Origin:** GPT security report `shared-context/forum/gpt/hestia_constellation_assurance_bug_analysis.md`

## The defect (network half)

`hub-lib/src/constellation.rs::ConstellationAttestation::verify` derives the assurance
tier from device facts **carried in the presented attestation**: it checks each device
signature against `ds.pubkey_hex` (line ~160) and reads `HardwareBacked`/`MultiDevice`
from `ds.device_type` (line ~171). An actor holding the owner key can mint fresh software
keypairs, label them `Hardware`, sign the challenge, and obtain an inflated tier over the
network — no real second device, no hardware key. The hub authenticates the *owner* but
not the *constellation*. (The hestia local verifier was fixed 2026-07-20, daa18a7:
`verify_against_store` resolves device facts from the vault store.)

**Invariant:** an attestation proves current possession of keys whose association, class,
and status were established **before** the challenge and are resolved from authoritative
state **independent of the presented attestation**. The presenter identifies a device and
proves possession; it is never authoritative for that device's key or class.

## The fix: an owner-committed enrollment registry the hub resolves against

The hub holds `enrolled_devices: BTreeMap<(owner_lct, device_lct), EnrolledDevice>`,
populated by **owner-signed** `DeviceEnrolled` / `DeviceRevoked` ledger events (pre-
challenge). The verifier resolves each device's pubkey + class + status from that record;
the presented `pubkey_hex`/`device_type` are ignored. Only `Active` enrolled devices count.

```
EnrolledDevice { owner_lct_id, device_lct_id, pubkey_hex, device_class, status, enrolled_at, enrollment_version }
DeviceStatus   { Active, Suspended, Revoked }      // revoked keys count for NOTHING
DeviceClass    { Desktop, Mobile, Server, Agent, Hardware }   // Hardware here = owner committed it pre-challenge
```

`HardwareBacked` from an enrolled `Hardware` class is *owner-committed, pre-challenge* —
strictly stronger than presenter-labeled, and it closes the forge-at-challenge attack. A
future layer (`hardware_evidence`: TPM EK/AK, Secure-Enclave attestation + proof-of-
possession) upgrades the tier to *verified* hardware; out of scope here, noted.

## Phased delivery (bounded, non-breaking)

- **Phase 1 (this PR) — hub-lib, purely additive, zero blast radius.**
  `EnrolledDevice`/`DeviceStatus`/`DeviceClass`/`EnrolledDeviceSet` + a NEW
  `verify_enrolled(pinned_owner_pubkey, enrolled, max_age, future_skew, now)` that resolves
  from the registry. The old `verify` is untouched (daemon still calls it), so nothing
  breaks. Tests: every GPT exploit scenario (forged hardware, unenrolled device, revoked
  device, foreign key, duplicate sig, wrong owner, future-dated) now fails. Also fixes the
  future-dated `issued_at` gap (GPT #5).
- **Phase 2 — hub-daemon.** `DeviceEnrolled`/`DeviceRevoked` events + `enrolled_devices`
  projection + `POST /v1/hubs/:id/constellation/enroll` (owner-signed) +
  `GET .../constellation/:owner/devices`. Switch `ConstellationGate::present` to
  `verify_enrolled` against the projected set.
- **Phase 3 — hestia driver.** `hestia constellation enroll <device>` (owner-signs +
  submits) + retire the old presented-key `verify` once both sides resolve from enrollment.

## RWOA (surface: verify_enrolled — the assurance-tier verifier)
act: derive an assurance tier a relying party scales trust to
S: high/irreversible-ish [construct: verify_enrolled] — an inflated tier over-grants; the point is inspectable evidence
R: n/a — not reachability; the caller supplies pinned owner key + registry
W: pass [construct: owner sig vs pinned key; device sigs vs ENROLLED key; class/status from the enrolled record]
O: pass [construct: pure function; resolves before deriving; no side effects]
A: n/a here (verifier); the enrollment events (Phase 2) are the witnessed authoritative record
V: present [construct: fail-closed on unenrolled/revoked/foreign/stale/future — presented facts never authoritative]
verdict: PASS
