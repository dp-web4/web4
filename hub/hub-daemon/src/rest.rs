// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Metalinxx Inc.

//! V2 REST surface for external clients (Hestia, peer hubs).
//!
//! Per architecture commitment #8: every consequential request arrives
//! as a [`SignedEnvelope`] (from hub_lib::envelope) with a server-issued
//! nonce. The hub verifies signature + nonce, then routes the payload to
//! a handler. Private keys never reach the hub.
//!
//! Spec reference: see `shared-context/forum/cbp-to-legion-hub-api-spec-for-h2-h3-2026-06-07.md`
//!
//! ## V2-7 Step 2 scope (this module)
//!
//! - `POST /v1/auth/challenge`  — mint a single-use nonce
//! - `POST /v1/hubs/{hub_id}/events` — accept a SignedEnvelope and
//!   route its payload (limited action set) to the ledger
//! - `GET  /v1/hubs/{hub_id}/state` — public state (no auth in
//!   this slice; need-to-know filtering arrives with V2-8 law interpreter)
//!
//! Limitations honest about today:
//! - PublicKeyResolver only knows the Sovereign LCT. Members can't sign
//!   envelopes yet — their public keys aren't registered with the hub
//!   until V2-12 (member self-add) closes that gap.
//! - The `Sovereign-sign-callback` (hub → Hestia direction) is V2-7
//!   Step 3, not here.
//! - Authority/need-to-know on reads is V2-8.

use anyhow::Result;
use axum::{
    extract::{ConnectInfo, Path, State},
    http::StatusCode,
    response::{IntoResponse, Json},
    routing::{get, post},
    Router,
};
use std::net::SocketAddr;
use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use std::path::PathBuf;
use std::sync::Arc;
use tokio::sync::Mutex;
use uuid::Uuid;

use hub_lib::hub::{HubPaths, SovereignMode};
use hub_lib::law::HubLawExt;
use hub_lib::envelope::{verify_envelope, Challenge, MapResolver, NonceStore, PublicKeyResolver, SignedEnvelope, VerifyError};
use hub_lib::replay::ReplayGuard;
use hub_lib::events::HubEvent;
use hub_lib::identity::IdentityFile;
use hub_lib::init::load_society;
use hub_lib::law::{Decision, DecisionOutcome, Law, R6Request};
use hub_lib::ledger::HubLedger;
use hub_lib::signer::{HestiaCallbackSigner, LocalKeypairSigner, LockedSigner, RemoteSigner, SignIntent, SwappableSigner};
use hub_lib::state::HubState;
use hub_lib::unlock_gate::{GateDecision, UnlockGate};

/// The hub's **public identity**, written clear at `<hub-dir>/public-identity.json`.
/// This is the tier-0 public layer: who the hub is (did:web4 / pubkey) and who founded
/// it — non-secret by definition, the same accepted-clear class as the KDF salt. It lets a
/// **locked-shell** hub (state store sealed + closed) still answer "what hub is this?" on
/// `/.well-known` so an operator can `hub unlock` it. Written whenever the hub is ignited;
/// read at locked boot.
#[derive(Clone, Serialize, Deserialize)]
pub struct PublicIdentity {
    pub hub_id: Uuid,
    pub hub_name: String,
    pub founding_sovereign_lct_id: Uuid,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub sovereign_pubkey_hex: Option<String>,
}

impl PublicIdentity {
    fn path(hub_dir: &std::path::Path) -> PathBuf {
        hub_dir.join("public-identity.json")
    }
    /// Read the clear public identity, if present.
    pub fn read(hub_dir: &std::path::Path) -> Option<Self> {
        std::fs::read(Self::path(hub_dir)).ok().and_then(|b| serde_json::from_slice(&b).ok())
    }
    /// Write the clear public identity (idempotent; public info, 0644).
    pub fn write(&self, hub_dir: &std::path::Path) -> anyhow::Result<()> {
        let bytes = serde_json::to_vec_pretty(self)?;
        std::fs::write(Self::path(hub_dir), bytes)?;
        Ok(())
    }
}

#[derive(Clone)]
pub struct RestState {
    pub paths: HubPaths,
    pub hub_id: Uuid,
    pub hub_name: String,
    /// True only for the loopback-only operator-plane listener (the one that
    /// serves the write pages). Plain bool (not shared): set on the cloned
    /// RestState handed to the operator app, so the admin nav can show the
    /// write-page links (`/admin/joins`, `/admin/manage`) only where they exist.
    pub operator_plane: bool,
    pub sovereign_lct_id: Uuid,
    /// The signer abstraction, behind a `SwappableSigner` so the hub can be
    /// promoted **locked → unlocked at runtime** (the unlock slot swaps the
    /// `LockedSigner` for the real `LocalKeypairSigner` in place — no restart).
    /// Inner kind: LocalKeypairSigner for MVP-compat chapters (keypair in
    /// process); HestiaCallbackSigner for Hestia-mode chapters (hub holds NO
    /// keys; signs via Hestia HTTP callback); LockedSigner while sealed.
    pub signer: Arc<SwappableSigner>,
    pub ledger: Arc<Mutex<HubLedger>>,
    /// Incremental projection cache. The ledger is append-only, so a cached
    /// `HubState` can be advanced by folding only entries appended since it was
    /// built — O(appended) instead of O(ledger) per query. Behind a **sync**
    /// mutex taken only while the async ledger lock is already held (see
    /// [`RestState::projected`]), so it's uncontended and never spans an await.
    pub state_cache: Arc<std::sync::Mutex<ProjectionCache>>,
    pub nonces: Arc<NonceStore>,
    /// Anti-replay seen-set for sealed channel requests (see [`ReplayGuard`]).
    /// AEAD authenticates the sealer but not freshness; this rejects captured
    /// `{pair_id, sealed}` re-submissions that would double-witness write acts.
    pub replay: Arc<ReplayGuard>,
    /// Public-key resolver for envelope signature verification.
    /// Wrapped in RwLock so the V2-12 join endpoint can extend it
    /// at runtime as new members are admitted.
    pub resolver: Arc<tokio::sync::RwLock<MapResolver>>,
    /// Hub law, loaded at open() time. None = no law set (all
    /// envelope-authenticated acts allowed). When present, the PolicyEntity
    /// gate runs before each act is committed to the ledger.
    ///
    /// Wrapped in RwLock so set-law (or `POST /v1/hubs/{id}/law`)
    /// can hot-reload without restarting hub serve.
    pub law: Arc<tokio::sync::RwLock<Option<Law>>>,
    /// Per-pair constellation MFA state: outstanding challenge nonces +
    /// verified assurance-tier bindings (`constellation_challenge` /
    /// `present_constellation` channel tools).
    pub constellations: Arc<hub_lib::constellation::ConstellationGate>,
    /// Outstanding OID4VP presentation requests (single-use nonce → request),
    /// minted at `/vp/request`, consumed at `/vp/response`. The hub as relying
    /// party (EUDI Phase 2, society scale).
    pub vp_requests: Arc<Mutex<std::collections::HashMap<String, web4_core::oid4vc::PresentationRequest>>>,
    /// Outstanding OID4VCI `c_nonce`s minted at `/nonce`, consumed at
    /// `/credential` (the hub as society-scale *issuer* of membership creds).
    pub vci_nonces: Arc<Mutex<std::collections::HashSet<String>>>,
    /// Rate limiter for the unlock slot (`POST /unlock`). The passphrase is
    /// still required; this caps online guessing (min interval + max
    /// consecutive failures + lockout), since anyone who can reach the unlock
    /// UI could still feed it attempts.
    pub unlock_gate: Arc<UnlockGate>,
    /// Path to the **tier-2 M-of-N unlock verifier** binary (the private quorum
    /// engine), if installed. `None` → tier-2 unlock is **N/A** (the hub still
    /// runs; `/unlock/challenge` returns 501). Set from `HUB_UNLOCK_VERIFIER`.
    /// The seam is generic + public; the verifier ships separately (open-core).
    pub unlock_verifier_cmd: Option<String>,
    /// Outstanding tier-2 unlock challenges (id → accumulating attestations).
    pub unlock_sessions: Arc<Mutex<std::collections::HashMap<Uuid, UnlockSession>>>,
    /// The **protected tier**: a `vault_tree` enclosure holding data that opens only on a
    /// granted M-of-N unlock (recursive-vault P2 / H3). `None` when the hub is locked (no
    /// passphrase) — there's no master key to open it. Seeded with a demo Sealed item so a
    /// granted quorum has something real to release.
    pub protected: Arc<Mutex<Option<hub_lib::vault_tree::OpenVault>>>,
    /// The derived SQLCipher key for the state store, held in memory (zeroized on
    /// drop) — the de-env'd replacement for reading `HUB_PASSPHRASE` from the
    /// environment on every runtime store re-open. `None` while locked. Set once
    /// at ignition; shared with `McpState`.
    pub store_key: Arc<tokio::sync::RwLock<Option<zeroize::Zeroizing<[u8; 32]>>>>,
    /// Per-citizen pending-notifications mailbox (DRAFT — the hub→citizen delivery
    /// floor). A `ReferencedAct{to: Citizen}` queues a `SealedNotice` here; the citizen
    /// drains it via the `notifications` channel tool (poll floor). Push to a registered
    /// LCT-MCP endpoint is the future optimization on the same queue.
    pub notifications: Arc<Mutex<std::collections::HashMap<Uuid, Vec<SealedNotice>>>>,

    /// Ephemeral liveness — last channel contact per member (presence /
    /// "bidirectional ping"). In-memory, NOT witnessed (too frequent for the
    /// ledger); resets on restart. Any authenticated channel op refreshes it.
    pub last_seen: Arc<Mutex<std::collections::HashMap<Uuid, chrono::DateTime<Utc>>>>,
}

/// One sealed notice queued for a citizen. `sealed` is ciphertext sealed to the
/// citizen's pinned pubkey — only that LCT can open it (`channel_open` with the hub
/// pubkey + `pair_id`).
/// The hestia notify wire (`forum/hub-to-hestia-witness-notify-wire-confirmed`):
/// `pair_id` + cleartext `kind` + sealed body. These are *delivery* concerns —
/// they ride the mailbox envelope, never the witnessed `Act` on the ledger.
#[derive(Clone, Serialize)]
pub struct SealedNotice {
    pub pair_id: Uuid,
    /// Sender LCT, in the clear on the envelope so the recipient can address a
    /// reply without opening the sealed body (the coordination loop's back-leg).
    pub from: Uuid,
    pub sealed: String,
    pub kind: String,
    pub pointer_uri: String,
    pub queued_at: chrono::DateTime<Utc>,
}

/// An in-flight tier-2 unlock: the minted challenge + the roster/threshold
/// snapshot taken at issue time + the attestations gathered so far.
pub struct UnlockSession {
    pub challenge: ChallengeWire,
    /// Snapshot of the admin roster (Sovereign Council) at challenge time:
    /// (admin LCT, pinned pubkey hex). Frozen so a mid-flight roster change
    /// can't move the goalposts of an open challenge.
    pub roster: Vec<(Uuid, String)>,
    /// Required distinct approvals (the council M) at challenge time.
    pub required: u32,
    /// Opaque admin attestations as received — the hub forwards these to the
    /// (private) verifier; it does not interpret the quorum itself.
    pub attestations: Vec<serde_json::Value>,
    pub granted: bool,
}

/// The challenge the hub mints + serializes to the verifier. Field shape
/// matches the verifier's `UnlockChallenge` (nonce is 32 raw bytes).
#[derive(Clone, Serialize)]
pub struct ChallengeWire {
    pub challenge_id: Uuid,
    pub nonce: [u8; 32],
    pub tier: String,
    pub hub_lct: Uuid,
    pub issued_at: u64,
}

/// Cached projection: a folded `HubState` plus the ledger position it reflects.
/// `advance` re-folds only entries appended since, so repeat queries are
/// O(appended) rather than O(ledger). Correct because the ledger is append-only
/// (entries never rewritten, `index == position`); a fresh RestState on restart
/// starts an empty cache.
#[derive(Default)]
pub struct ProjectionCache {
    state: HubState,
    next: usize,
}

impl RestState {
    /// Whether the vault is sealed. The lock state **is** the kind of the
    /// currently-installed signer — a `LockedSigner` (set at startup when the
    /// Sovereign identity is encrypted and no passphrase was available) means
    /// degraded no-LCT-tier mode; the unlock slot swaps in the real signer.
    pub fn is_locked(&self) -> bool {
        matches!(self.signer.signer_kind(), hub_lib::signer::SignerKind::Locked)
    }

    /// Current projection, served from the incremental cache. **Call while
    /// holding the ledger lock** (pass the guard): the sync cache mutex is taken
    /// and released within, never across an await, and always under the ledger
    /// lock — so it's uncontended (one ledger-lock holder at a time) and
    /// deadlock-free. Result is identical to `HubState::project(ledger)`.
    pub fn projected(&self, ledger: &HubLedger) -> HubState {
        let mut cache = self.state_cache.lock().expect("projection cache poisoned");
        let from = cache.next;
        cache.next = cache.state.advance(ledger, from);
        cache.state.clone()
    }
}

/// True if the identity at `path` is an encrypted vault (W4VT) **and** no
/// `HUB_PASSPHRASE` is available — so the hub must start LOCKED. A present-but-
/// wrong passphrase is deliberately NOT "locked": `load_auto` will hard-error,
/// surfacing the real problem rather than silently running degraded.
fn identity_is_locked(path: &std::path::Path) -> bool {
    if hub_lib::identity::env_passphrase().is_some() {
        return false;
    }
    std::fs::read(path).map(|b| b.starts_with(b"W4VT")).unwrap_or(false)
}

impl RestState {
    /// As `hub serve` needs it: a caller-supplied shared in-memory ledger
    /// handle. `hub serve` passes the *same* `Arc<Mutex<HubLedger>>` here and
    /// to `McpState`, so MCP, REST, and the admin dashboard all read/write one
    /// ledger — an act recorded through any surface is immediately visible to
    /// the others (previously each held its own startup snapshot and only
    /// reconverged on restart).
    pub async fn open_with_law_and_ledger(
        hub_dir: PathBuf,
        law: Arc<tokio::sync::RwLock<Option<Law>>>,
        ledger: Arc<Mutex<HubLedger>>,
    ) -> Result<Self> {
        let paths = HubPaths::new(hub_dir.clone());
        let config = hub_lib::hub::HubConfig::load(paths.config())?;
        let society = load_society(&hub_dir).await?;

        // Project the ledger once up front — clear sqlite state, readable
        // without the identity passphrase. Used for resolver seeding AND, in
        // locked mode, to recover the Sovereign LCT id (the private key is in
        // the locked vault, but the founding-sovereign id is in Genesis).
        let projected = {
            let l = ledger.lock().await;
            HubState::project(&*l)
        };

        // Build the right Sovereign LCT + signer for the chapter's mode. If the
        // Local-mode identity is an encrypted vault and no passphrase is
        // available, start LOCKED: degraded no-LCT-tier surface, no signing.
        let (sovereign_lct_id, sovereign_lct, signer, locked): (Uuid, Option<_>, Arc<dyn RemoteSigner>, bool) =
            match config.sovereign.mode()? {
                SovereignMode::Local { lct_path } if identity_is_locked(&lct_path) => {
                    let sov_id = projected.founding_sovereign_lct_id.ok_or_else(|| {
                        anyhow::anyhow!(
                            "Sovereign identity at {} is locked and the ledger has no founding \
                             sovereign — cannot start even in degraded mode",
                            lct_path.display()
                        )
                    })?;
                    tracing::warn!(
                        "Sovereign identity is an encrypted vault with no HUB_PASSPHRASE — \
                         starting LOCKED (no-LCT-tier surface only; set HUB_PASSPHRASE to unlock)"
                    );
                    (sov_id, None, Arc::new(LockedSigner::new(sov_id)) as Arc<dyn RemoteSigner>, true)
                }
                SovereignMode::Local { lct_path } => {
                    let sovereign = IdentityFile::load_auto(&lct_path)?;
                    let kp = sovereign.keypair()?;
                    let signer = Arc::new(LocalKeypairSigner::new(sovereign.lct.id, kp));
                    (sovereign.lct.id, Some(sovereign.lct), signer as Arc<dyn RemoteSigner>, false)
                }
                SovereignMode::Hestia { callback_url, lct_id, pubkey_hex } => {
                    let lct = hub_lib::hub::hestia_sovereign_lct(lct_id, &pubkey_hex)?;
                    let signer = Arc::new(HestiaCallbackSigner::new(lct_id, callback_url)?);
                    (lct.id, Some(lct), signer as Arc<dyn RemoteSigner>, false)
                }
            };

        // Resolver seeded with the Sovereign LCT (if available) + every member's
        // pubkey from prior MemberAdded events (V2-12). HubState::project walks
        // the ledger and accumulates member_pubkeys; we reconstruct an Lct
        // per member so future envelopes from them verify against the
        // public key recorded at admission time. (Locked: no Sovereign pubkey to
        // seed — fine, locked mode does no envelope verification.)
        let mut resolver = MapResolver::new();
        if let Some(sl) = &sovereign_lct {
            resolver.insert(sl.clone());
        }
        for (member_lct_id, pubkey_hex) in &projected.member_pubkeys {
            match hub_lib::hub::hestia_sovereign_lct(*member_lct_id, pubkey_hex) {
                Ok(lct) => resolver.insert(lct),
                Err(e) => tracing::warn!(
                    "skipping member {} pubkey reconstruction: {}",
                    member_lct_id, e
                ),
            }
        }
        // V2-9 Phase 1: seed the resolver with every Sovereign Council
        // holder's pubkey so any holder can sign chapter acts as a
        // co-Sovereign. Holders are also auto-added to member_pubkeys
        // when they're admitted (CouncilMemberAdded handler in state.rs
        // inserts them into the member registry); this loop is the
        // explicit council-holder pass for clarity + to surface
        // reconstruction errors with the council label.
        for (holder_lct_id, pubkey_hex) in &projected.council_pubkeys {
            match hub_lib::hub::hestia_sovereign_lct(*holder_lct_id, pubkey_hex) {
                Ok(lct) => resolver.insert(lct),
                Err(e) => tracing::warn!(
                    "skipping council holder {} pubkey reconstruction: {}",
                    holder_lct_id, e
                ),
            }
        }

        let _ = locked; // lock state now derives from the installed signer kind
        Ok(Self {
            paths,
            hub_id: society.lct_id,
            hub_name: society.name.clone(),
            sovereign_lct_id,
            signer: Arc::new(SwappableSigner::new(signer)),
            ledger,
            state_cache: Arc::new(std::sync::Mutex::new(ProjectionCache::default())),
            nonces: Arc::new(NonceStore::new()),
            replay: Arc::new(ReplayGuard::new()),
            resolver: Arc::new(tokio::sync::RwLock::new(resolver)),
            law,
            constellations: Arc::new(hub_lib::constellation::ConstellationGate::new()),
            vp_requests: Arc::new(Mutex::new(std::collections::HashMap::new())),
            vci_nonces: Arc::new(Mutex::new(std::collections::HashSet::new())),
            unlock_gate: Arc::new(UnlockGate::default_policy()),
            unlock_verifier_cmd: std::env::var("HUB_UNLOCK_VERIFIER").ok().filter(|s| !s.is_empty()),
            unlock_sessions: Arc::new(Mutex::new(std::collections::HashMap::new())),
            protected: Arc::new(Mutex::new(
                hub_lib::identity::env_passphrase().and_then(|p| open_protected_vault(&hub_dir, &p)),
            )),
            // Derive + hold the store key in memory (env-fed at construction for now;
            // ignition will set it from a transient passphrase — increment 6). Never
            // re-read from env at runtime.
            store_key: Arc::new(tokio::sync::RwLock::new(
                match hub_lib::identity::env_passphrase() {
                    Some(p) => hub_lib::store::derive_store_key(&hub_dir, &p)
                        .ok()
                        .map(zeroize::Zeroizing::new),
                    None => None,
                },
            )),
            notifications: Arc::new(Mutex::new(std::collections::HashMap::new())),
            last_seen: Arc::new(Mutex::new(std::collections::HashMap::new())),
            operator_plane: false,
        })
    }

    /// Open the state store using the in-memory derived key (de-env'd). Used for
    /// every runtime store re-open instead of reading `HUB_PASSPHRASE` from the
    /// environment.
    pub async fn open_store(&self) -> anyhow::Result<Box<dyn hub_lib::store::HubStore>> {
        let key = self.store_key.read().await.as_ref().map(|z| **z);
        hub_lib::store::open_hub_store_with_key(&self.paths.root, key)
    }

    /// Read the society via the **in-memory-keyed** store. Unlike
    /// `init::load_society` (which re-opens the store from disk with no key and
    /// thus fails on an ignited *encrypted* hub), this uses the runtime store key,
    /// so admin/read handlers work after ignition.
    pub async fn society(&self) -> anyhow::Result<web4_core::society::Society> {
        let store = self.open_store().await?;
        store.read_society().await?
            .ok_or_else(|| anyhow::anyhow!("no society found in hub store"))
    }

    /// Construct a **locked shell**: the encrypted state store could not be opened
    /// (no key — total enclosure), so the hub comes up serving only the unlock path.
    /// Identity (hub_id / name / founding sovereign) is read from the clear tier-0
    /// `public-identity.json`; the ledger is an empty placeholder (replaced at
    /// ignition); the signer is a `LockedSigner`; no store key, no protected tier.
    /// `hub unlock` then ignites it (see [`try_unlock`](Self::try_unlock)).
    pub async fn open_locked_shell(
        hub_dir: PathBuf,
        law: Arc<tokio::sync::RwLock<Option<Law>>>,
        placeholder_ledger: Arc<Mutex<HubLedger>>,
    ) -> Result<Self> {
        let paths = HubPaths::new(hub_dir.clone());
        let pid = PublicIdentity::read(&hub_dir).ok_or_else(|| {
            anyhow::anyhow!(
                "hub state is encrypted and there is no clear public-identity.json — cannot \
                 start a locked shell without knowing the hub's public identity. Run \
                 `hub export-public-identity {}` (with the passphrase) once to seed it.",
                hub_dir.display()
            )
        })?;
        let signer: Arc<dyn RemoteSigner> = Arc::new(LockedSigner::new(pid.founding_sovereign_lct_id));
        Ok(Self {
            paths,
            hub_id: pid.hub_id,
            hub_name: pid.hub_name,
            sovereign_lct_id: pid.founding_sovereign_lct_id,
            signer: Arc::new(SwappableSigner::new(signer)),
            ledger: placeholder_ledger,
            state_cache: Arc::new(std::sync::Mutex::new(ProjectionCache::default())),
            nonces: Arc::new(NonceStore::new()),
            replay: Arc::new(ReplayGuard::new()),
            resolver: Arc::new(tokio::sync::RwLock::new(MapResolver::new())),
            law,
            constellations: Arc::new(hub_lib::constellation::ConstellationGate::new()),
            vp_requests: Arc::new(Mutex::new(std::collections::HashMap::new())),
            vci_nonces: Arc::new(Mutex::new(std::collections::HashSet::new())),
            unlock_gate: Arc::new(UnlockGate::default_policy()),
            unlock_verifier_cmd: std::env::var("HUB_UNLOCK_VERIFIER").ok().filter(|s| !s.is_empty()),
            unlock_sessions: Arc::new(Mutex::new(std::collections::HashMap::new())),
            protected: Arc::new(Mutex::new(None)),
            store_key: Arc::new(tokio::sync::RwLock::new(None)),
            notifications: Arc::new(Mutex::new(std::collections::HashMap::new())),
            last_seen: Arc::new(Mutex::new(std::collections::HashMap::new())),
            operator_plane: false,
        })
    }

    /// Re-read the hub law from storage and swap it into the
    /// in-memory snapshot. Returns Ok with the version (or "none" if
    /// no law set). Used by the `/v1/admin/reload-law` endpoint so
    /// operators can `hub set-law` then `curl reload-law` without
    /// restarting hub serve.
    pub async fn reload_law(&self) -> anyhow::Result<String> {
        use anyhow::Context;
        let store = self.open_store().await
            .context("opening store for law reload")?;
        let new_law: Option<Law> = match store.read_law().await? {
            Some(ref yaml) => Some(Law::parse_and_validate(yaml)
                .map_err(|e| anyhow::anyhow!("law on disk failed to parse/validate: {}", e))?),
            None => None,
        };
        let version = new_law.as_ref()
            .map(|l| l.version.clone())
            .unwrap_or_else(|| "none".to_string());
        *self.law.write().await = new_law;
        Ok(version)
    }

    /// The **unlock slot** (tier-1 ignition via the stub-console / passphrase
    /// plugin). Rate-limited; opens the encrypted Sovereign identity with
    /// `passphrase` and, on success, **promotes the hub in place** locked →
    /// unlocked: the real `LocalKeypairSigner` is swapped into the
    /// `SwappableSigner` and the Sovereign pubkey is seeded into the resolver,
    /// with no restart. The passphrase is used here and dropped — never stored.
    /// `now` is unix-seconds (injected for deterministic rate-limit tests).
    pub async fn try_unlock(&self, passphrase: &str, now: i64) -> UnlockOutcome {
        if !self.is_locked() {
            return UnlockOutcome::NotLocked;
        }
        // Cap online guessing first — the passphrase is still required, but
        // anyone who reaches this slot could feed it attempts.
        match self.unlock_gate.check(now) {
            GateDecision::Allow => {}
            GateDecision::TooSoon { retry_after_secs }
            | GateDecision::LockedOut { retry_after_secs } => {
                return UnlockOutcome::RateLimited { retry_after_secs };
            }
        }
        // Re-derive the encrypted identity path from config.
        let config = match hub_lib::hub::HubConfig::load(self.paths.config()) {
            Ok(c) => c,
            Err(e) => return UnlockOutcome::Unsupported(format!("config load failed: {e}")),
        };
        let lct_path = match config.sovereign.mode() {
            Ok(SovereignMode::Local { lct_path }) => lct_path,
            Ok(_) => {
                return UnlockOutcome::Unsupported(
                    "hub is not in local-vault mode; passphrase unlock does not apply".into(),
                )
            }
            Err(e) => return UnlockOutcome::Unsupported(format!("sovereign mode: {e}")),
        };
        // Attempt to open the encrypted identity with the passphrase.
        match IdentityFile::load_encrypted(&lct_path, passphrase) {
            Ok(identity) => {
                let kp = match identity.keypair() {
                    Ok(k) => k,
                    Err(e) => {
                        // A successful decrypt but unusable key is not a bad
                        // guess — don't count it against the rate limit.
                        return UnlockOutcome::Unsupported(format!(
                            "identity decrypted but has no usable keypair: {e}"
                        ));
                    }
                };
                let lct = identity.lct.clone();

                // Open the encrypted STATE store with a key derived from the SAME
                // passphrase, and load the real ledger. Fail closed BEFORE swapping
                // the signer — never leave a half-ignited hub (real signer + empty
                // ledger). A store failure here is an internal error, not a bad guess.
                let store_key = match hub_lib::store::derive_store_key(&self.paths.root, passphrase) {
                    Ok(k) => k,
                    Err(e) => return UnlockOutcome::Unsupported(format!("deriving store key: {e}")),
                };
                let store = match hub_lib::store::open_hub_store_with_key(&self.paths.root, Some(store_key)) {
                    Ok(s) => s,
                    Err(e) => {
                        tracing::error!("ignition: identity decrypted but state store did not open: {e}");
                        return UnlockOutcome::Unsupported(format!("state store did not open: {e}"));
                    }
                };
                let real_ledger = match hub_lib::ledger::HubLedger::open(store).await {
                    Ok(l) => l,
                    Err(e) => return UnlockOutcome::Unsupported(format!("opening ledger: {e}")),
                };
                let projected = HubState::project(&real_ledger);

                // Commit ignition into memory: signer, store key, ledger, resolver, protected.
                self.signer.swap(Arc::new(LocalKeypairSigner::new(lct.id, kp)));
                *self.store_key.write().await = Some(zeroize::Zeroizing::new(store_key));
                *self.ledger.lock().await = real_ledger;
                {
                    let mut resolver = self.resolver.write().await;
                    resolver.insert(lct.clone());
                    for (m, pk) in &projected.member_pubkeys {
                        if let Ok(l) = hub_lib::hub::hestia_sovereign_lct(*m, pk) { resolver.insert(l); }
                    }
                    for (h, pk) in &projected.council_pubkeys {
                        if let Ok(l) = hub_lib::hub::hestia_sovereign_lct(*h, pk) { resolver.insert(l); }
                    }
                }
                // Open the protected tier with the transient passphrase (then it's dropped).
                *self.protected.lock().await = open_protected_vault(&self.paths.root, passphrase);
                // Load the now-readable law (store opens with the held key).
                if let Err(e) = self.reload_law().await {
                    tracing::warn!("ignition: law reload failed (continuing): {e}");
                }
                self.unlock_gate.record_success();
                // Refresh the clear public-identity tier-0 file so a future locked-shell
                // boot knows who this hub is (to serve well-known + accept `hub unlock`).
                let pid = PublicIdentity {
                    hub_id: self.hub_id,
                    hub_name: self.hub_name.clone(),
                    founding_sovereign_lct_id: lct.id,
                    sovereign_pubkey_hex: self.signer.public_key().map(|p| p.to_hex()),
                };
                if let Err(e) = pid.write(&self.paths.root) {
                    tracing::warn!("ignition: writing public-identity.json failed (non-fatal): {e}");
                }
                tracing::warn!(
                    sovereign_lct = %lct.id,
                    "HUB IGNITED via passphrase — identity + state store + protected tier opened into memory; passphrase dropped, never stored"
                );
                UnlockOutcome::Unlocked { sovereign_lct_id: lct.id }
            }
            Err(_) => {
                self.unlock_gate.record_failure(now);
                tracing::warn!("vault unlock attempt FAILED (wrong passphrase or corrupt vault)");
                UnlockOutcome::WrongPassphrase
            }
        }
    }
}

/// Result of a vault-unlock attempt via the unlock slot.
pub enum UnlockOutcome {
    /// Promoted locked → unlocked; the real signer is now installed.
    Unlocked { sovereign_lct_id: Uuid },
    /// The hub was already unlocked — nothing to do.
    NotLocked,
    /// The passphrase didn't open the vault (counted against the rate limit).
    WrongPassphrase,
    /// Refused by the rate limiter — wait `retry_after_secs`.
    RateLimited { retry_after_secs: i64 },
    /// This hub can't be unlocked by passphrase (e.g. Hestia-mode, or a
    /// config/identity problem) — not a bad guess.
    Unsupported(String),
}

/// `POST /v1/hubs/:hub_id/unlock` — the **stub-console unlock slot**.
///
/// Privileged + **local-only**: a locked hub accepts an unlock attempt only
/// from a loopback caller (the stub-console plugin runs on the hub host and
/// connects to `127.0.0.1`). Combined with the rate limiter, this is the honest
/// answer to "a local process could unlock it": the process still needs the
/// passphrase, and *we* control how it's obtained (our UI) and that it's used
/// once and discarded. Remote callers are refused before any attempt is counted.
async fn unlock(
    ConnectInfo(peer): ConnectInfo<SocketAddr>,
    State(s): State<RestState>,
    Json(req): Json<UnlockRequest>,
) -> Result<Json<UnlockResponse>, ApiError> {
    if !peer.ip().is_loopback() {
        return Err(ApiError {
            status: StatusCode::FORBIDDEN,
            message: "unlock is local-only — present the passphrase from the hub host (127.0.0.1)"
                .to_string(),
        });
    }
    match s.try_unlock(&req.passphrase, Utc::now().timestamp()).await {
        UnlockOutcome::Unlocked { sovereign_lct_id } => {
            // Now operational + able to sign: hydrate any law-driven defaults
            // into the law (idempotent; witnessed only if it filled something).
            match hydrate_law_defaults(&s).await {
                Ok(true) => tracing::info!("law defaults hydrated post-ignition"),
                Ok(false) => {}
                Err(e) => tracing::warn!("law-default hydration skipped: {e}"),
            }
            Ok(Json(UnlockResponse {
                unlocked: true,
                status: "unlocked".into(),
                sovereign_lct_id: Some(sovereign_lct_id),
                retry_after_secs: None,
            }))
        }
        UnlockOutcome::NotLocked => Ok(Json(UnlockResponse {
            unlocked: true,
            status: "already_unlocked".into(),
            sovereign_lct_id: Some(s.sovereign_lct_id),
            retry_after_secs: None,
        })),
        UnlockOutcome::WrongPassphrase => Err(ApiError {
            status: StatusCode::UNAUTHORIZED,
            message: "unlock failed: wrong passphrase".to_string(),
        }),
        UnlockOutcome::RateLimited { retry_after_secs } => Err(ApiError {
            status: StatusCode::TOO_MANY_REQUESTS,
            message: format!("unlock rate-limited; retry after {retry_after_secs}s"),
        }),
        UnlockOutcome::Unsupported(m) => Err(ApiError {
            status: StatusCode::BAD_REQUEST,
            message: format!("unlock not applicable: {m}"),
        }),
    }
}

#[derive(Deserialize)]
struct UnlockRequest {
    /// The tier-1 ignition passphrase. May be empty (explicit NULL passphrase).
    passphrase: String,
}

#[derive(Serialize)]
struct UnlockResponse {
    unlocked: bool,
    status: String,
    sovereign_lct_id: Option<Uuid>,
    retry_after_secs: Option<i64>,
}

// ─────────────────────── tier-2 M-of-N unlock (witnessed) ───────────────────
//
// The generic, PUBLIC seam. The hub mints a challenge, gathers admin
// attestations (over the open surface — each is signature-verified), witnesses
// every step to the ledger, and asks the PRIVATE verifier subprocess for the
// quorum decision. With no verifier installed, tier-2 unlock is N/A (501) and
// the hub runs unaffected. The novel quorum logic lives only in the verifier.

/// The generic ceil(N/2) default (50% rounded up). Not novel — the council's
/// own threshold (M) overrides it when set; this is just the bootstrap default.
fn unlock_default_threshold(n: usize) -> u32 {
    ((n + 1) / 2) as u32
}

/// Witness a hub event to the signed ledger (build → sign as Sovereign →
/// append). Returns the committed entry index. Requires an ignited signer.
async fn witness_event(s: &RestState, event: HubEvent) -> Result<u64, ApiError> {
    let event_kind_str = event.kind().to_string();
    let event_value = serde_json::to_value(&event)
        .map_err(|e| ApiError::internal(anyhow::anyhow!("serializing event: {}", e)))?;
    let (unsigned, intent) = {
        let ledger = s.ledger.lock().await;
        let unsigned = ledger
            .build_entry(s.sovereign_lct_id, event.clone(), Utc::now())
            .map_err(ApiError::internal)?;
        let intent = SignIntent {
            request_id: Uuid::new_v4(),
            hub_id: s.hub_id,
            hub_name: s.hub_name.clone(),
            actor_lct_id: s.sovereign_lct_id,
            ledger_index: unsigned.entry.index,
            event_kind: event_kind_str,
            event: event_value,
        };
        (unsigned, intent)
    };
    let signing_bytes = unsigned.signing_bytes.clone();
    let signature = s
        .signer
        .sign(s.sovereign_lct_id, &signing_bytes, &intent)
        .await
        .map_err(|e| match e {
            hub_lib::signer::SignError::Denied(reason) => {
                ApiError::unauthorized(format!("Sovereign signer denied: {}", reason))
            }
            hub_lib::signer::SignError::Transport(msg) => ApiError {
                status: StatusCode::SERVICE_UNAVAILABLE,
                message: format!("Sovereign signer unreachable: {}", msg),
            },
            hub_lib::signer::SignError::Malformed(msg) => {
                ApiError::internal(anyhow::anyhow!("malformed signer response: {}", msg))
            }
            hub_lib::signer::SignError::Internal(err) => ApiError::internal(err),
        })?;
    let mut ledger = s.ledger.lock().await;
    let entry = ledger
        .append_signed(unsigned, signature)
        .await
        .map_err(ApiError::internal)?;
    Ok(entry.index)
}

/// Hub→citizen notification (DRAFT): witness a `ReferencedAct{to: Citizen}` and queue a
/// sealed notice in the citizen's mailbox (the poll floor). `body` is sealed to the
/// citizen's pinned pubkey — only that LCT can open it. Best-effort: missing pubkey / seal
/// failure logs and drops (the witnessed act still records that a notice was intended).
/// Seal `body` to the recipient's pinned pubkey and queue it in their mailbox
/// (the poll floor) — NO ledger write. Use this when the act is already witnessed
/// by the caller (e.g. the `referenced_act` dispatch). `from` rides the envelope
/// in the clear so the recipient can address a reply. Best-effort: dropped if the
/// recipient has no pinned pubkey / the seal fails.
/// Per-member mailbox size cap. A member can't flood a peer's mailbox (or the
/// hub's memory) without bound; at the cap the oldest notice is dropped to make
/// room (ring semantics — the most recent N always survive).
const MAX_NOTICES_PER_MEMBER: usize = 1000;
/// Notice retention. Notices older than this are pruned on enqueue and on drain,
/// so a mailbox that's touched (or polled) doesn't accumulate stale entries. A
/// fully-idle mailbox is bounded instead by [`MAX_NOTICES_PER_MEMBER`].
const NOTICE_TTL_SECS: i64 = 7 * 24 * 3600;

async fn queue_sealed_notice(
    s: &RestState, recipient: Uuid, from: Uuid, kind: &str, pointer_uri: &str, body: &[u8],
) {
    let pubkey_hex = {
        let ledger = s.ledger.lock().await;
        s.projected(&ledger).member_pubkeys.get(&recipient).cloned()
    };
    let Some(pubkey_hex) = pubkey_hex else {
        tracing::warn!("queue_sealed_notice: no pinned pubkey for {recipient}; notice dropped");
        return;
    };
    let pubkey = match hex::decode(&pubkey_hex)
        .ok()
        .and_then(|b| <[u8; 32]>::try_from(b).ok())
        .and_then(|a| web4_core::crypto::PublicKey::from_bytes(&a).ok())
    {
        Some(pk) => pk,
        None => { tracing::warn!("queue_sealed_notice: bad pubkey for {recipient}"); return; }
    };
    let pair_id = Uuid::new_v4();
    let sealed = match s.signer.channel_seal(&pubkey, pair_id, body) {
        Ok(c) => c,
        Err(e) => { tracing::warn!("queue_sealed_notice: seal failed: {e}"); return; }
    };
    let now = Utc::now();
    let cutoff = now - chrono::Duration::seconds(NOTICE_TTL_SECS);
    let mut mailbox = s.notifications.lock().await;
    let queue = mailbox.entry(recipient).or_default();
    queue.retain(|n| n.queued_at >= cutoff); // TTL prune
    while queue.len() >= MAX_NOTICES_PER_MEMBER {
        queue.remove(0); // at cap: drop oldest to make room
        tracing::warn!(
            "mailbox for {recipient} at cap ({MAX_NOTICES_PER_MEMBER}); dropped oldest notice"
        );
    }
    queue.push(SealedNotice {
        pair_id,
        from,
        sealed,
        kind: kind.to_string(),
        pointer_uri: pointer_uri.to_string(),
        queued_at: now,
    });
}

/// Hub-originated notification: witness a thin `notify:<event>` act AND queue the
/// sealed notice. For an act the caller already witnessed, use
/// [`queue_sealed_notice`] directly (avoids double-witnessing).
async fn notify_citizen(
    s: &RestState, recipient: Uuid, from: Uuid, kind: &str, pointer_uri: &str, body: &[u8],
) {
    // Witness a thin act — `content_hash` binds the witnessed pointer to this
    // exact notice body so it can't drift; medium = Message; consequence defaults
    // to Reversible. The sealed body rides the mailbox, NOT the ledger.
    let act = web4_core::act::Act::addressed(
        s.sovereign_lct_id,
        web4_core::act::ActAddress::Citizen { lct_id: recipient },
        kind,
        web4_core::act::SubstanceRef::new(
            pointer_uri,
            web4_core::sha256_hex(body),
            web4_core::act::SubstanceMedium::Message,
        ),
        Utc::now(),
    );
    let _ = witness_event(s, HubEvent::ReferencedAct { act }).await;
    queue_sealed_notice(s, recipient, from, kind, pointer_uri, body).await;
}

#[derive(Deserialize)]
pub struct ChallengeReq {
    /// The protected tier to unlock (free-form label, witnessed). Defaults to
    /// "protected".
    #[serde(default = "default_unlock_tier")]
    tier: String,
}
fn default_unlock_tier() -> String {
    "protected".to_string()
}

#[derive(Serialize)]
pub struct ChallengeResp {
    challenge_id: Uuid,
    nonce_hex: String,
    tier: String,
    hub_lct: Uuid,
    issued_at: u64,
    /// Distinct admin approvals required (the council M).
    required: u32,
    /// The admin LCTs that may attest (the Sovereign Council roster).
    roster: Vec<Uuid>,
}

/// `POST /v1/hubs/:id/unlock/challenge` — the ignited hub mints a tier-2 unlock
/// challenge for its M-of-N admins (the Sovereign Council). Local-only (the
/// operator/hub triggers it); the request is witnessed (`VaultUnlockRequested`).
async fn unlock_challenge(
    ConnectInfo(peer): ConnectInfo<SocketAddr>,
    State(s): State<RestState>,
    Path(_hub_id): Path<Uuid>,
    Json(req): Json<ChallengeReq>,
) -> Result<Json<ChallengeResp>, ApiError> {
    if !peer.ip().is_loopback() {
        return Err(ApiError {
            status: StatusCode::FORBIDDEN,
            message: "issuing a tier-2 unlock challenge is local-only (the hub/operator triggers it)".to_string(),
        });
    }
    // Must be ignited (tier-1) to recognize the council + to witness.
    if s.is_locked() {
        return Err(ApiError {
            status: StatusCode::SERVICE_UNAVAILABLE,
            message: "ignite tier-1 first (passphrase / hardware) before a tier-2 M-of-N unlock".to_string(),
        });
    }
    // Tier-2 verifier plugin must be installed, else N/A.
    if s.unlock_verifier_cmd.is_none() {
        return Err(ApiError {
            status: StatusCode::NOT_IMPLEMENTED,
            message: "tier-2 M-of-N unlock is not available on this hub (no unlock verifier plugin configured)".to_string(),
        });
    }
    // Roster + threshold from the Sovereign Council (tier-0 clear projection).
    let (roster, required) = {
        let ledger = s.ledger.lock().await;
        let st = HubState::project(&*ledger);
        let roster: Vec<(Uuid, String)> = st
            .council_pubkeys
            .iter()
            .map(|(lct, pk)| (*lct, pk.clone()))
            .collect();
        let required = st
            .council_threshold
            .map(|(m, _)| m)
            .unwrap_or_else(|| unlock_default_threshold(roster.len()));
        (roster, required)
    };
    if roster.is_empty() {
        return Err(ApiError {
            status: StatusCode::CONFLICT,
            message: "no Sovereign Council enrolled — there is no admin roster to authorize a tier-2 unlock".to_string(),
        });
    }
    // Mint the challenge (nonce = 256 bits from two v4 UUIDs' random bytes).
    let mut nonce = [0u8; 32];
    nonce[..16].copy_from_slice(Uuid::new_v4().as_bytes());
    nonce[16..].copy_from_slice(Uuid::new_v4().as_bytes());
    let challenge = ChallengeWire {
        challenge_id: Uuid::new_v4(),
        nonce,
        tier: req.tier.clone(),
        hub_lct: s.sovereign_lct_id,
        issued_at: Utc::now().timestamp().max(0) as u64,
    };
    // Witness the request, then record the open session.
    witness_event(
        &s,
        HubEvent::VaultUnlockRequested {
            challenge_id: challenge.challenge_id,
            tier: req.tier.clone(),
            required,
            requested_at: Utc::now(),
        },
    )
    .await?;
    let roster_lcts: Vec<Uuid> = roster.iter().map(|(lct, _)| *lct).collect();
    s.unlock_sessions.lock().await.insert(
        challenge.challenge_id,
        UnlockSession {
            challenge: challenge.clone(),
            roster,
            required,
            attestations: Vec::new(),
            granted: false,
        },
    );
    Ok(Json(ChallengeResp {
        challenge_id: challenge.challenge_id,
        nonce_hex: hex::encode(nonce),
        tier: req.tier,
        hub_lct: s.sovereign_lct_id,
        issued_at: challenge.issued_at,
        required,
        roster: roster_lcts,
    }))
}

#[derive(Deserialize)]
pub struct AttestReq {
    challenge_id: Uuid,
    /// The admin's signed attestation (opaque to the hub; the verifier checks
    /// it). Shape = the verifier's `AdminAttestation`.
    attestation: serde_json::Value,
}

#[derive(Serialize)]
pub struct AttestResp {
    granted: bool,
    approvals: Vec<Uuid>,
    declines: Vec<Uuid>,
    rejected: usize,
    required: usize,
    reason: String,
    /// On the first grant: the tier-2 protected payload the quorum released (H3 — proof the
    /// M-of-N opened real encrypted data, not just a symbolic authorization).
    #[serde(skip_serializing_if = "Option::is_none")]
    released: Option<String>,
}

#[derive(Deserialize)]
struct VerifierDecision {
    granted: bool,
    approvals: Vec<Uuid>,
    declines: Vec<Uuid>,
    rejected: usize,
    required: usize,
    reason: String,
    #[serde(default)]
    #[allow(dead_code)]
    roster_parse_errors: usize,
}

/// `POST /v1/hubs/:id/unlock/attest` — an admin submits a signed decision for an
/// open challenge. Open surface (admins attest from their own constellations);
/// every attestation is signature-verified by the private verifier. Each
/// receipt is witnessed (`VaultUnlockAttested`); the first grant is witnessed
/// (`VaultUnlockResolved`).
async fn unlock_attest(
    State(s): State<RestState>,
    Path(_hub_id): Path<Uuid>,
    Json(req): Json<AttestReq>,
) -> Result<Json<AttestResp>, ApiError> {
    let cmd = s.unlock_verifier_cmd.clone().ok_or_else(|| ApiError {
        status: StatusCode::NOT_IMPLEMENTED,
        message: "tier-2 M-of-N unlock is not available on this hub (no unlock verifier plugin configured)".to_string(),
    })?;

    // Append the attestation + snapshot what the verifier needs.
    let (challenge, roster, required, atts, already_granted) = {
        let mut sessions = s.unlock_sessions.lock().await;
        let session = sessions.get_mut(&req.challenge_id).ok_or_else(|| {
            ApiError::not_found("no such unlock challenge (expired or never issued)")
        })?;
        session.attestations.push(req.attestation.clone());
        (
            session.challenge.clone(),
            session.roster.clone(),
            session.required,
            session.attestations.clone(),
            session.granted,
        )
    };

    // Witness the receipt (best-effort admin/decision extraction for the record).
    let admin_lct = req
        .attestation
        .get("admin_lct")
        .and_then(|v| v.as_str())
        .and_then(|s| Uuid::parse_str(s).ok())
        .unwrap_or_else(Uuid::nil);
    let decision_str = req
        .attestation
        .get("decision")
        .and_then(|v| v.as_str())
        .unwrap_or("unknown")
        .to_string();
    witness_event(
        &s,
        HubEvent::VaultUnlockAttested {
            challenge_id: req.challenge_id,
            admin_lct_id: admin_lct,
            decision: decision_str,
            attested_at: Utc::now(),
        },
    )
    .await?;

    // Ask the private verifier for the quorum decision.
    let vreq = serde_json::json!({
        "challenge": challenge,
        "attestations": atts,
        "roster": roster.iter().map(|(lct, pk)| serde_json::json!({"lct": lct, "pubkey_hex": pk})).collect::<Vec<_>>(),
        "policy": { "min_approvals": required, "max_age_secs": 300 },
        "now": Utc::now().timestamp().max(0) as u64,
    });
    let decision = run_unlock_verifier(&cmd, &vreq).await?;

    // Witness the resolution exactly once, on the first grant — and actually OPEN the
    // protected tier (H3): the quorum's authorization releases real Sealed data.
    let mut released: Option<String> = None;
    if decision.granted && !already_granted {
        witness_event(
            &s,
            HubEvent::VaultUnlockResolved {
                challenge_id: req.challenge_id,
                tier: challenge.tier.clone(),
                granted: true,
                approvals: decision.approvals.clone(),
                declines: decision.declines.clone(),
                resolved_at: Utc::now(),
            },
        )
        .await?;
        if let Some(sess) = s.unlock_sessions.lock().await.get_mut(&req.challenge_id) {
            sess.granted = true;
        }
        released = open_protected_tier(&s).await;
        tracing::warn!(
            challenge = %req.challenge_id, tier = %challenge.tier, released = released.is_some(),
            "TIER-2 VAULT UNLOCK GRANTED by M-of-N quorum (witnessed) — protected tier opened"
        );
    }

    Ok(Json(AttestResp {
        granted: decision.granted,
        approvals: decision.approvals,
        declines: decision.declines,
        rejected: decision.rejected,
        required: decision.required,
        reason: decision.reason,
        released,
    }))
}

/// On a granted quorum, open the protected-tier Sealed item: read its sealing credential
/// (master tier, available since ignition) and decrypt the item into memory. This is the
/// recognition model — the quorum *authorizes*; the hub holds the credential. Returns the
/// released payload, or `None` if no protected store is configured / it can't be opened.
async fn open_protected_tier(s: &RestState) -> Option<String> {
    let guard = s.protected.lock().await;
    let v = guard.as_ref()?;
    let cred = match v.open_item(PROTECTED_NOTE_CRED, None) {
        Ok(c) => String::from_utf8_lossy(&c).into_owned(),
        Err(e) => { tracing::warn!("protected-tier: reading sealing credential failed: {e}"); return None; }
    };
    match v.open_item(PROTECTED_NOTE, Some(&cred)) {
        Ok(bytes) => Some(String::from_utf8_lossy(&bytes).into_owned()),
        Err(e) => { tracing::warn!("protected-tier: opening sealed item failed: {e}"); None }
    }
}

/// H-010: hard cap on the tier-2 unlock verifier subprocess so a hung/slow
/// verifier can't wedge the unlock-attestation path indefinitely.
const UNLOCK_VERIFIER_TIMEOUT_SECS: u64 = 10;

/// Invoke the private verifier subprocess: pipe the request JSON to stdin, read
/// the decision JSON from stdout. Fail-closed: a non-zero exit or unparseable
/// output is an error (the caller does not get a grant).
async fn run_unlock_verifier(
    cmd: &str,
    req: &serde_json::Value,
) -> Result<VerifierDecision, ApiError> {
    use tokio::io::AsyncWriteExt;
    // H-010: the verifier is a signing-authority gate — require an ABSOLUTE path so
    // a compromised PATH / working directory can't substitute a different binary.
    if !std::path::Path::new(cmd).is_absolute() {
        return Err(ApiError {
            status: StatusCode::SERVICE_UNAVAILABLE,
            message: format!("HUB_UNLOCK_VERIFIER must be an absolute path (got {cmd:?})"),
        });
    }
    let mut child = tokio::process::Command::new(cmd)
        .stdin(std::process::Stdio::piped())
        .stdout(std::process::Stdio::piped())
        .stderr(std::process::Stdio::piped())
        .kill_on_drop(true) // H-010: killed if the timeout below fires (drops this future)
        .spawn()
        .map_err(|e| ApiError {
            status: StatusCode::SERVICE_UNAVAILABLE,
            message: format!("unlock verifier not runnable ({cmd}): {e}"),
        })?;
    let body = serde_json::to_vec(req)
        .map_err(|e| ApiError::internal(anyhow::anyhow!("serializing verifier request: {e}")))?;
    // H-010: bound the whole write+wait so a verifier that hangs on stdin or never
    // exits can't stall the unlock path. On timeout the future drops → kill_on_drop.
    let out = tokio::time::timeout(
        std::time::Duration::from_secs(UNLOCK_VERIFIER_TIMEOUT_SECS),
        async move {
            {
                let mut stdin = child.stdin.take().ok_or_else(|| {
                    ApiError::internal(anyhow::anyhow!("verifier stdin unavailable"))
                })?;
                stdin
                    .write_all(&body)
                    .await
                    .map_err(|e| ApiError::internal(anyhow::anyhow!("writing to verifier: {e}")))?;
                // stdin dropped here → EOF for the verifier.
            }
            child
                .wait_with_output()
                .await
                .map_err(|e| ApiError::internal(anyhow::anyhow!("awaiting verifier: {e}")))
        },
    )
    .await
    .map_err(|_elapsed| ApiError {
        status: StatusCode::GATEWAY_TIMEOUT,
        message: format!("unlock verifier timed out after {UNLOCK_VERIFIER_TIMEOUT_SECS}s (fail-closed)"),
    })??;
    if !out.status.success() {
        let stderr = String::from_utf8_lossy(&out.stderr);
        return Err(ApiError {
            status: StatusCode::BAD_GATEWAY,
            message: format!("unlock verifier failed (fail-closed): {}", stderr.trim()),
        });
    }
    serde_json::from_slice(&out.stdout).map_err(|e| {
        ApiError::internal(anyhow::anyhow!("unparseable verifier decision: {e}"))
    })
}

const PROTECTED_NOTE: &str = "protected-note";
const PROTECTED_NOTE_CRED: &str = "protected-note.cred";

/// Open (or create) the hub's **protected-tier** vault — the recursive-vault enclosure
/// that holds data released only on a granted M-of-N unlock (H3). Keyed by the vault
/// passphrase; `None` when the hub is locked (no passphrase → no master key). Seeds a demo
/// Sealed item the first time, so a granted quorum has something real to open. Any failure
/// is logged and yields `None` (degraded, not fatal — the rest of the hub still runs).
fn open_protected_vault(hub_dir: &std::path::Path, pass: &str) -> Option<hub_lib::vault_tree::OpenVault> {
    use hub_lib::vault_tree::{ItemKind, OpenVault};
    let path = hub_dir.join("protected.hvlt");
    let mut v = match OpenVault::open_or_create(&path, pass, "protected-tier") {
        Ok(v) => v,
        Err(e) => {
            tracing::warn!("protected-tier store unavailable ({}): {e}", path.display());
            return None;
        }
    };
    if !v.contains(PROTECTED_NOTE) {
        // Sealing credential the hub holds at master tier (available after ignition); the
        // tier-2 policy only *uses* it on a granted quorum.
        let cred = format!("{}{}", Uuid::new_v4().simple(), Uuid::new_v4().simple());
        v.put_master(PROTECTED_NOTE_CRED, ItemKind::Credential, cred.as_bytes());
        let payload = b"TIER-2 PROTECTED PAYLOAD - released only by a witnessed M-of-N quorum unlock.";
        if let Err(e) = v.put_sealed(PROTECTED_NOTE, ItemKind::Document, payload, &cred) {
            tracing::warn!("seeding protected-tier item failed: {e}");
            return None;
        }
        if let Err(e) = v.save() {
            tracing::warn!("persisting protected-tier store failed: {e}");
            return None;
        }
        tracing::info!("protected-tier store initialized at {} (demo Sealed item seeded)", path.display());
    }
    Some(v)
}

pub fn router(state: RestState) -> Router {
    Router::new()
        // Discovery endpoint that Hestia's `hestia hub connect` calls.
        // Matches the HubInfo shape declared in `hestia/core/src/hub.rs`
        // (hub_lct_id, api_versions, endpoints, hubs). Unauthenticated
        // by design — discovery is a public read.
        .route("/.well-known/web4-hub.json", get(well_known_hub_info))
        // EUDI Phase 2 (society scale): the hub as OID4VCI issuer of membership
        // SD-JWT-VCs + OID4VP verifier (relying party). web4-core::oid4vc/
        // sd_jwt_vc do the heavy lifting; these are the thin wrappers.
        .route("/v1/hubs/:hub_id/.well-known/openid-credential-issuer", get(vci_metadata))
        .route("/v1/hubs/:hub_id/nonce", post(vci_nonce))
        .route("/v1/hubs/:hub_id/credential", post(vci_credential))
        .route("/v1/hubs/:hub_id/vp/request", post(vp_request))
        .route("/v1/hubs/:hub_id/vp/response", post(vp_response))
        // tier-0: the hub's law is readable even while the vault is locked
        .route("/v1/hubs/:hub_id/law", get(read_hub_law))
        // the unlock slot (stub-console / passphrase): local-only + rate-limited.
        // Promotes a locked hub → unlocked in place (swaps in the real signer).
        .route("/v1/hubs/:hub_id/unlock", post(unlock))
        // tier-2 M-of-N unlock (witnessed): the ignited hub mints a challenge,
        // admins attest, the private verifier judges the quorum. N/A (501) when
        // no verifier plugin is configured.
        .route("/v1/hubs/:hub_id/unlock/challenge", post(unlock_challenge))
        .route("/v1/hubs/:hub_id/unlock/attest", post(unlock_attest))
        .route("/v1/auth/challenge", post(issue_challenge))
        // Hub-named routes (canonical; chapter→hub rename mirrored on
        // Hestia side at hestia@c3932a8 — back-compat /v1/chapters/*
        // aliases dropped 2026-06-08).
        .route("/v1/hubs/:hub_id/events", post(submit_event))
        .route("/v1/hubs/:hub_id/state", get(read_state))
        // Member↔hub E2E channel: citizen-tier reads/acts travel sealed,
        // never in the clear. The sealed request authenticates the caller
        // (AEAD open) AND decrypts in one step; the response is sealed back.
        .route("/v1/hubs/:hub_id/channel", post(channel_request))
        .route("/v1/hubs/:hub_id/members/join", post(submit_join))
        // V2-9 Phase 2: Sovereign Council proposal + aggregation flow.
        .route("/v1/hubs/:hub_id/council/propose", post(submit_proposal))
        .route("/v1/hubs/:hub_id/council/sign", post(sign_proposal))
        .route("/v1/hubs/:hub_id/council/proposals", get(list_proposals))
        .route("/v1/hubs/:hub_id/council/proposals/:proposal_id", get(get_proposal))
        // PAIRED-CHANNELS Sprint C: LCT pair lifecycle endpoints.
        // Request / confirm / revoke are signed-envelope acts; list /
        // detail are public reads (hub law gates later).
        .route("/v1/hubs/:hub_id/pairs/request", post(submit_pair_request))
        .route("/v1/hubs/:hub_id/pairs/:pair_id/confirm", post(submit_pair_confirm))
        .route("/v1/hubs/:hub_id/pairs/:pair_id/revoke", post(submit_pair_revoke))
        .route("/v1/hubs/:hub_id/pairs", get(list_pairs))
        .route("/v1/hubs/:hub_id/pairs/:pair_id", get(get_pair))
        // PAIRED-CHANNELS Sprint D: message relay on a confirmed pair.
        .route("/v1/hubs/:hub_id/pairs/:pair_id/messages",
               post(post_pair_message).get(get_pair_messages))
        .route("/v1/admin/reload-law", post(reload_law))
        .with_state(state)
}

// ---------- error wrapper ----------

#[derive(Debug)]
struct ApiError {
    status: StatusCode,
    message: String,
}

impl ApiError {
    fn bad_request(msg: impl Into<String>) -> Self {
        Self { status: StatusCode::BAD_REQUEST, message: msg.into() }
    }
    fn unauthorized(msg: impl Into<String>) -> Self {
        Self { status: StatusCode::UNAUTHORIZED, message: msg.into() }
    }
    fn not_found(msg: impl Into<String>) -> Self {
        Self { status: StatusCode::NOT_FOUND, message: msg.into() }
    }
    fn internal(e: anyhow::Error) -> Self {
        Self { status: StatusCode::INTERNAL_SERVER_ERROR, message: format!("{:#}", e) }
    }
    fn conflict(msg: impl Into<String>) -> Self {
        Self { status: StatusCode::CONFLICT, message: msg.into() }
    }
}

/// The hub's vault is locked: refuse citizen-tier+ work, 503. Tier-0 (no-LCT)
/// reads (discovery, issuer metadata, law) stay available.
fn locked_error() -> ApiError {
    ApiError {
        status: StatusCode::SERVICE_UNAVAILABLE,
        message: "hub vault is locked — ignite it first (run `hub unlock`); only the unlock path is served while locked"
            .to_string(),
    }
}

/// The fail-closed **lock-gate**: while the hub is locked, every request is
/// refused (503) except the small tier-0 allowlist — the unlock path itself, the
/// public discovery doc, the (clear) law, and the OID4VCI issuer metadata.
/// Applied once to the merged app (covers MCP + REST + admin uniformly), so no
/// handler runs against unpopulated state in a locked shell. A locked hub is
/// unlocked, not operated.
pub async fn lock_gate(
    State(s): State<RestState>,
    req: axum::extract::Request,
    next: axum::middleware::Next,
) -> axum::response::Response {
    if s.is_locked() {
        let path = req.uri().path();
        let allowed = path == "/.well-known/web4-hub.json"
            || path.ends_with("/unlock")                              // tier-1 ignition only
            || path.ends_with("/law")                                  // signed law is tier-0
            || path.ends_with("/.well-known/openid-credential-issuer"); // public issuer metadata
        if !allowed {
            return locked_error().into_response();
        }
    }
    next.run(req).await
}

impl IntoResponse for ApiError {
    fn into_response(self) -> axum::response::Response {
        let body = serde_json::json!({"error": self.message});
        (self.status, Json(body)).into_response()
    }
}

impl From<VerifyError> for ApiError {
    fn from(e: VerifyError) -> Self {
        // Map verifier outcomes to HTTP status codes
        match e {
            VerifyError::UnknownSigner(_) => ApiError::unauthorized(e.to_string()),
            VerifyError::UnknownNonce(_) => ApiError::unauthorized(e.to_string()),
            VerifyError::ExpiredNonce(_) => ApiError::unauthorized(e.to_string()),
            VerifyError::NonceLctMismatch(_) => ApiError::unauthorized(e.to_string()),
            VerifyError::BadSignature(_) => ApiError::unauthorized(e.to_string()),
            VerifyError::Internal(err) => ApiError::internal(err),
        }
    }
}

// ---------- GET /.well-known/web4-hub.json (discovery) ----------

/// Shape matches `hestia::hub::HubInfo` exactly so `hestia hub connect`
/// can deserialize without translation. Public read; no auth.
#[derive(Serialize)]
struct WellKnownHubInfo {
    /// The hub's society LCT id (what `hestia hub connect` keys on).
    hub_lct_id: Uuid,
    /// True when the hub is a locked shell (state sealed; only the unlock path is
    /// served). Clients/operators see this to know to `hub unlock` before use.
    locked: bool,
    /// The hub's LCT public key (hex) — the ECDH peer a member uses to open
    /// an E2E member↔hub channel. `None` if the signer can't expose it
    /// (e.g. Hestia mode). Public, integrity-protecting only (not a secret).
    #[serde(skip_serializing_if = "Option::is_none")]
    hub_pubkey_hex: Option<String>,
    /// API versions this hub serves. v1 today; future versions get
    /// added when the wire shape evolves under semver discipline.
    api_versions: Vec<&'static str>,
    /// Endpoint hints for clients. `rest` is the v1 base; `mcp` is the
    /// tool-call base. Both are relative to the hub's reachable URL
    /// (the client already knows it — they fetched this from there).
    endpoints: WellKnownEndpoints,
    /// True when a hub law is loaded. **`false` = no-law / permissive mode**
    /// (H-003): acts and admissions are not gated by law. Production hubs should
    /// serve a signed starter law; a no-law public hub is dev-only. Exposed so
    /// clients/operators can detect the posture without guessing.
    law_present: bool,
    /// Hubs this server hosts. Single-hub deployments return one entry;
    /// future multi-hub hosting returns multiple.
    hubs: Vec<WellKnownHubSummary>,
}

#[derive(Serialize)]
struct WellKnownEndpoints {
    rest: &'static str,
    mcp: &'static str,
}

#[derive(Serialize)]
struct WellKnownHubSummary {
    id: Uuid,
    name: String,
    public: bool,
}

async fn well_known_hub_info(
    State(s): State<RestState>,
) -> Json<WellKnownHubInfo> {
    Json(WellKnownHubInfo {
        hub_lct_id: s.hub_id,
        locked: s.is_locked(),
        hub_pubkey_hex: s.signer.public_key().map(|pk| pk.to_hex())
            .or_else(|| PublicIdentity::read(&s.paths.root).and_then(|p| p.sovereign_pubkey_hex)),
        api_versions: vec!["v1"],
        endpoints: WellKnownEndpoints {
            rest: "/v1",
            mcp: "/tools",
        },
        law_present: s.law.read().await.is_some(),
        hubs: vec![WellKnownHubSummary {
            id: s.hub_id,
            name: s.hub_name.clone(),
            // For now every hub the daemon serves is publicly
            // discoverable — if you reached the well-known you reach
            // the hub. Private hub semantics (ACLs at the discovery
            // layer) land if/when the operational model requires.
            public: true,
        }],
    })
}

// ---------- GET /v1/hubs/:hub_id/law (tier-0: readable while locked) ----------

/// The hub's law, readable in **tier-0** — works even with the vault locked.
/// "Whatever the law is, it is inspectable without unlock; it cannot be changed
/// without unlock." (Rollback protection — pinning the served law's hash to the
/// LawAmended ledger head — is a noted follow-on.)
async fn read_hub_law(
    State(s): State<RestState>,
    Path(hub_id): Path<Uuid>,
) -> Result<Json<serde_json::Value>, ApiError> {
    if hub_id != s.hub_id {
        return Err(ApiError::not_found(format!("unknown hub {hub_id}")));
    }
    let law = s.law.read().await;
    Ok(Json(match law.as_ref() {
        Some(l) => serde_json::json!({
            "version": l.version,
            "norms": l.norms.len(),
            "law": serde_json::to_value(l).ok(),
        }),
        None => serde_json::json!({ "law": null }),
    }))
}

// ---------- OID4VP verifier (EUDI Phase 2, society scale) ----------
//
// The hub acts as a relying party over web4-core::oid4vc. Trust path is the
// hub's OWN member roster, not an external trusted list (that's Phase 3): a
// presented credential's issuer (a member's hestia, `did:web4:<host>:<lct>`)
// is resolved to its pinned pubkey via the same MapResolver used for envelope
// auth — the member's identity key both authenticates to the hub and signs the
// credentials it issues, so the hub already holds the verification key.

#[derive(Deserialize)]
struct VpRequestBody {
    vct: String,
    #[serde(default)]
    required_claims: Vec<String>,
}

#[derive(Serialize)]
struct VpVerified {
    vct: String,
    issuer: String,
    issuer_lct_id: Uuid,
    claims: serde_json::Map<String, serde_json::Value>,
}

/// POST /v1/hubs/{hub_id}/vp/request — mint a single-use OID4VP request.
async fn vp_request(
    State(s): State<RestState>,
    Path(hub_id): Path<Uuid>,
    headers: axum::http::HeaderMap,
    Json(body): Json<VpRequestBody>,
) -> Result<Json<web4_core::oid4vc::PresentationRequest>, ApiError> {
    if hub_id != s.hub_id {
        return Err(ApiError::not_found(format!("unknown hub {hub_id}")));
    }
    let host = headers.get(axum::http::header::HOST).and_then(|h| h.to_str().ok()).unwrap_or("127.0.0.1");
    let client_id = web4_core::did::did_web4(host, s.hub_id);
    let response_uri = format!("http://{host}/v1/hubs/{}/vp/response", s.hub_id);
    let nonce = web4_core::oid4vc::opaque_token(Uuid::new_v4().as_bytes());
    let claims: Vec<&str> = body.required_claims.iter().map(|c| c.as_str()).collect();
    let mut req = web4_core::oid4vc::PresentationRequest::new(&client_id, &nonce, &response_uri, &body.vct);
    if !claims.is_empty() {
        req = req.requiring(&claims);
    }
    s.vp_requests.lock().await.insert(nonce, req.clone());
    Ok(Json(req))
}

/// POST /v1/hubs/{hub_id}/vp/response — verify a wallet's presentation.
async fn vp_response(
    State(s): State<RestState>,
    Path(hub_id): Path<Uuid>,
    Json(resp): Json<web4_core::oid4vc::PresentationResponse>,
) -> Result<Json<VpVerified>, ApiError> {
    if hub_id != s.hub_id {
        return Err(ApiError::not_found(format!("unknown hub {hub_id}")));
    }
    // Which outstanding request does this answer? Consume it (single-use).
    let nonce = web4_core::oid4vc::unverified_nonce(&resp.vp_token)
        .ok_or_else(|| ApiError::bad_request("presentation missing Key-Binding nonce".to_string()))?;
    let req = s.vp_requests.lock().await.remove(&nonce)
        .ok_or_else(|| ApiError::unauthorized("unknown or already-used presentation nonce".to_string()))?;
    // Resolve the credential issuer's did:web4 LCT to its pinned member pubkey.
    let iss = web4_core::oid4vc::unverified_issuer(&resp.vp_token)
        .ok_or_else(|| ApiError::bad_request("presented credential has no issuer".to_string()))?;
    let (_authority, issuer_lct_id) = web4_core::did::parse_did_web4(&iss)
        .ok_or_else(|| ApiError::bad_request(format!("credential issuer is not a did:web4: {iss}")))?;
    let issuer_lct = {
        let resolver = s.resolver.read().await;
        resolver.lookup(issuer_lct_id).ok_or_else(|| ApiError::unauthorized(format!(
            "credential issuer {issuer_lct_id} is not a known member of this hub"
        )))?
    };
    let cred = web4_core::oid4vc::verify_presentation_response(
        &resp, &req, &issuer_lct.public_key, 300, Utc::now().timestamp(),
    ).map_err(ApiError::unauthorized)?;
    Ok(Json(VpVerified {
        vct: cred.vct,
        issuer: cred.issuer,
        issuer_lct_id,
        claims: cred.claims,
    }))
}

// ---------- OID4VCI issuer (EUDI Phase 2, society scale) ----------
//
// The hub issues `Web4Membership` SD-JWT-VCs to its own members. The OID4VCI
// holder key-possession proof doubles as member authentication: the proof key
// MUST be a pinned member pubkey (reverse-resolved via the MapResolver), so the
// hub credentials only a verified member, `cnf`-bound to that member's key. The
// hub signs through its `RemoteSigner` (it may hold no keys) via the
// signer-agnostic `SdJwtVc::prepare` / `UnsignedSdJwtVc::into_compact` split —
// so issuance works over LocalKeypairSigner AND HestiaCallbackSigner.

const VCI_VCT: &str = "Web4Membership";

/// The hub's OID4VCI `credential_issuer` URL: `http://<host>/v1/hubs/<id>`;
/// `for_vct` derives `<issuer>/credential` from it = the mounted route.
fn vci_issuer_url(headers: &axum::http::HeaderMap, hub_id: Uuid) -> String {
    let host = headers.get(axum::http::header::HOST).and_then(|h| h.to_str().ok()).unwrap_or("127.0.0.1");
    format!("http://{host}/v1/hubs/{hub_id}")
}

/// GET /v1/hubs/{hub_id}/.well-known/openid-credential-issuer
async fn vci_metadata(
    State(s): State<RestState>,
    Path(hub_id): Path<Uuid>,
    headers: axum::http::HeaderMap,
) -> Result<Json<web4_core::oid4vc::CredentialIssuerMetadata>, ApiError> {
    if hub_id != s.hub_id {
        return Err(ApiError::not_found(format!("unknown hub {hub_id}")));
    }
    let issuer = vci_issuer_url(&headers, s.hub_id);
    Ok(Json(web4_core::oid4vc::CredentialIssuerMetadata::for_vct(&issuer, VCI_VCT)))
}

/// POST /v1/hubs/{hub_id}/nonce — mint a single-use c_nonce.
async fn vci_nonce(
    State(s): State<RestState>,
    Path(hub_id): Path<Uuid>,
) -> Result<Json<serde_json::Value>, ApiError> {
    if hub_id != s.hub_id {
        return Err(ApiError::not_found(format!("unknown hub {hub_id}")));
    }
    let nonce = web4_core::oid4vc::opaque_token(Uuid::new_v4().as_bytes());
    s.vci_nonces.lock().await.insert(nonce.clone());
    Ok(Json(serde_json::json!({ "c_nonce": nonce })))
}

#[derive(Serialize)]
struct IssuedCredential {
    credential: String,
    format: &'static str,
}

/// POST /v1/hubs/{hub_id}/credential — verify holder proof (= member auth),
/// issue a Web4Membership SD-JWT-VC signed by the hub's RemoteSigner.
async fn vci_credential(
    State(s): State<RestState>,
    Path(hub_id): Path<Uuid>,
    headers: axum::http::HeaderMap,
    Json(req): Json<web4_core::oid4vc::CredentialRequest>,
) -> Result<Json<IssuedCredential>, ApiError> {
    if hub_id != s.hub_id {
        return Err(ApiError::not_found(format!("unknown hub {hub_id}")));
    }
    let issuer_url = vci_issuer_url(&headers, s.hub_id);
    let now = Utc::now().timestamp();

    // 1. Consume the c_nonce the proof bound to (single-use).
    let nonce = web4_core::oid4vc::proof_nonce(&req.proof_jwt)
        .ok_or_else(|| ApiError::bad_request("holder proof missing nonce".to_string()))?;
    if !s.vci_nonces.lock().await.remove(&nonce) {
        return Err(ApiError::unauthorized("unknown or already-used c_nonce".to_string()));
    }

    // 2. Verify holder key possession (aud = us, fresh).
    let holder_pk = web4_core::oid4vc::verify_holder_proof(&req.proof_jwt, &issuer_url, &nonce, 300, now)
        .map_err(ApiError::unauthorized)?;

    // 3. The proof IS member authentication: the holder key must be a pinned
    //    member pubkey. Reverse-resolve it to the member LCT.
    let member_lct = {
        let resolver = s.resolver.read().await;
        resolver.0.values()
            .find(|lct| lct.public_key.to_bytes() == holder_pk.to_bytes())
            .map(|lct| lct.id)
            .ok_or_else(|| ApiError::unauthorized(
                "holder key is not a member of this hub — only members may pull a membership credential".to_string(),
            ))?
    };
    // And current in the ledger projection (not just key-known).
    let member_name = {
        let ledger = s.ledger.lock().await;
        match HubState::project(&ledger).members.get(&member_lct) {
            Some(m) => m.name.clone(),
            None => return Err(ApiError::unauthorized(format!("{member_lct} is key-known but not a current member"))),
        }
    };

    // 4. Build the credential, signed by the hub identity.
    let host = headers.get(axum::http::header::HOST).and_then(|h| h.to_str().ok()).unwrap_or("127.0.0.1");
    let issuer_did = web4_core::did::did_web4(host, s.sovereign_lct_id);
    let subject_did = web4_core::did::did_web4(host, member_lct);
    let mut builder = web4_core::sd_jwt_vc::SdJwtVc::new(VCI_VCT, &issuer_did)
        .iat(now)
        .holder_binding(&holder_pk)
        .claim("sub", serde_json::json!(subject_did))
        .sd_claim("society", serde_json::json!(s.hub_name))
        .sd_claim("society_lct", serde_json::json!(s.hub_id.to_string()))
        .sd_claim("member", serde_json::json!(true));
    if let Some(name) = member_name {
        builder = builder.sd_claim("member_name", serde_json::json!(name));
    }

    // 5. Sign via the hub's RemoteSigner (no KeyPair in process; Local + Hestia).
    let kid = format!("{issuer_did}#key-0");
    let unsigned = builder.prepare(&kid);
    let intent = SignIntent {
        request_id: Uuid::new_v4(),
        hub_id: s.hub_id,
        hub_name: s.hub_name.clone(),
        actor_lct_id: s.sovereign_lct_id,
        ledger_index: 0,
        event_kind: "oid4vci_credential".to_string(),
        event: serde_json::json!({ "vct": VCI_VCT, "sub": subject_did }),
    };
    let sig = s.signer
        .sign(s.sovereign_lct_id, unsigned.signing_bytes(), &intent)
        .await
        .map_err(|e| ApiError::internal(anyhow::anyhow!("hub signer denied/failed: {e}")))?;
    let credential = unsigned.into_compact(&sig.bytes);
    Ok(Json(IssuedCredential { credential, format: "vc+sd-jwt" }))
}

// ---------- POST /v1/auth/challenge ----------

#[derive(Deserialize)]
struct ChallengeRequest {
    for_lct_id: Uuid,
}

async fn issue_challenge(
    State(s): State<RestState>,
    Json(req): Json<ChallengeRequest>,
) -> Result<Json<Challenge>, ApiError> {
    // Cheap maintenance: drop expired before issuing a new one.
    s.nonces.prune_expired(Utc::now());
    let challenge = s.nonces.issue(req.for_lct_id, Utc::now());
    Ok(Json(challenge))
}

// ---------- POST /v1/hubs/{hub_id}/events ----------

/// The action types V2-7 Step 2 routes from a verified envelope.
/// Mirrors a subset of HubEvent; extends as more flows land.
#[derive(Deserialize)]
#[serde(tag = "action", rename_all = "snake_case")]
enum EnvelopeAction {
    AddMember {
        member_lct_id: Uuid,
        #[serde(default)]
        name: Option<String>,
    },
    DeclareSkill {
        member_lct_id: Uuid,
        skill: String,
    },
    UpdateProfile {
        member_lct_id: Uuid,
        fields: std::collections::BTreeMap<String, String>,
    },
}

#[derive(Serialize)]
struct EventAccepted {
    entry_index: u64,
    entry_hash: String,
    event_kind: String,
    signer_lct_id: Uuid,
}

async fn submit_event(
    State(s): State<RestState>,
    Path(hub_id): Path<Uuid>,
    Json(envelope): Json<SignedEnvelope>,
) -> Result<Json<EventAccepted>, ApiError> {
    if hub_id != s.hub_id {
        return Err(ApiError::not_found(format!(
            "chapter id {} does not match this hub's chapter {}",
            hub_id, s.hub_id
        )));
    }
    // Acts require the Sovereign signer (to witness them) — unavailable while
    // the vault is locked.
    if s.is_locked() {
        return Err(locked_error());
    }

    // 1. Authority check: envelope verifies (signer known, nonce valid,
    // payload not tampered).
    let resolver_guard = s.resolver.read().await;
    let _redeemed = verify_envelope(&envelope, &s.nonces, &*resolver_guard, Utc::now())?;
    drop(resolver_guard);

    // 2. V2-7 §2 broadening (Sprint 3): the founding Sovereign OR any
    // current member may sign envelopes. Per-action authorization
    // (below at action match) constrains *which* acts each may perform
    // — Sovereign-only acts (add_member) reject member envelopes;
    // self-acts (declare_skill) require envelope.signer == act subject.
    //
    // Pre-Sprint-3 behavior was Sovereign-only at this layer. The
    // restriction moved into per-action checks because V2-12 admitted
    // members already authenticate via the resolver — gating their
    // envelopes here was just delaying the inevitable.
    let (signer_is_sovereign, signer_is_member) = {
        let ledger = s.ledger.lock().await;
        let projected = hub_lib::state::HubState::project(&*ledger);
        let is_sov = envelope.signer_lct_id == s.sovereign_lct_id;
        let is_member = projected.members.contains_key(&envelope.signer_lct_id);
        (is_sov, is_member)
    };
    if !signer_is_sovereign && !signer_is_member {
        return Err(ApiError::unauthorized(format!(
            "signer {} is neither the founding Sovereign nor a current member",
            envelope.signer_lct_id
        )));
    }

    // 2.5 V2-9 Phase 2 council gate: if a council threshold of 2+ is
    // recorded in state, no single-signer commit is permitted — all
    // acts must flow through the council propose/sign endpoints so
    // M-of-N is actually enforced. The founding Sovereign is still a
    // valid voter; they just participate as one of M like any holder.
    let council_threshold_active = {
        let ledger = s.ledger.lock().await;
        let projected = hub_lib::state::HubState::project(&*ledger);
        matches!(projected.council_threshold, Some((m, _)) if m >= 2)
    };
    if council_threshold_active {
        return Err(ApiError {
            status: StatusCode::CONFLICT,
            message: "council mode active (threshold >= 2-of-N): submit acts via \
                      POST /v1/hubs/{hub_id}/council/propose + /sign".into(),
        });
    }

    // 3. Parse the action.
    let action: EnvelopeAction = serde_json::from_value(envelope.payload.clone())
        .map_err(|e| ApiError::bad_request(format!("payload not a known action: {}", e)))?;

    // Per-action authorization. Sprint 3 carves the action space into
    // "Sovereign-only" (membership control, role assignment, charter,
    // law) and "member-self" (declare your own skill, etc.). The
    // founding Sovereign can do anything; members are restricted to
    // acts about themselves.
    let event = match action {
        EnvelopeAction::AddMember { member_lct_id, name } => {
            if !signer_is_sovereign {
                return Err(ApiError::unauthorized(String::from(
                    "add_member is a Sovereign-only act; members cannot admit other members \
                     (members self-add via POST /v1/hubs/{id}/members/join — V2-12)"
                )));
            }
            HubEvent::MemberAdded {
                member_lct_id,
                added_by: envelope.signer_lct_id,
                member_name: name,
                member_pubkey_hex: None,
            }
        }
        EnvelopeAction::DeclareSkill { member_lct_id, skill } => {
            // Sovereign can declare skills for any member (operator
            // convenience). Members can declare only their OWN skills —
            // signer must match the subject, no impersonation.
            if !signer_is_sovereign && envelope.signer_lct_id != member_lct_id {
                return Err(ApiError::unauthorized(format!(
                    "members may only declare their own skills (signer {} != subject {})",
                    envelope.signer_lct_id, member_lct_id,
                )));
            }
            HubEvent::MemberSkillDeclared {
                member_lct_id,
                skill,
                declared_by: envelope.signer_lct_id,
            }
        }
        EnvelopeAction::UpdateProfile { member_lct_id, fields } => {
            // Same self-only rule as DeclareSkill: members update only their
            // own profile (signer == subject); Sovereign may update any
            // member's (operator convenience / seeding).
            if !signer_is_sovereign && envelope.signer_lct_id != member_lct_id {
                return Err(ApiError::unauthorized(format!(
                    "members may only update their own profile (signer {} != subject {})",
                    envelope.signer_lct_id, member_lct_id,
                )));
            }
            HubEvent::MemberProfileUpdated {
                member_lct_id,
                fields,
                updated_by: envelope.signer_lct_id,
            }
        }
    };

    // 3.5 PolicyEntity gate (V2-8 §4): if a hub law is loaded,
    // evaluate the act against it. Deny → 403; Escalate → 202 with the
    // escalate_to role; Allow → proceed.
    let law_guard = s.law.read().await;
    if let Some(law) = law_guard.as_ref() {
        let req = build_r6_request(&envelope, &event, s.sovereign_lct_id)
            .map_err(ApiError::internal)?;
        let outcome = law.evaluate_outcome(&req);
        match outcome.decision {
            Decision::Allow => { /* proceed */ }
            Decision::Warn => {
                // Non-blocking flagged-allow: proceed, but surface the advisory.
                // Structured Warn consumption (witnessing) lands with the
                // sequenced hub-consumes step after the hestia migration.
                tracing::warn!(
                    "act flagged by hub law (norm: {})",
                    outcome.winning_norm.as_deref().unwrap_or("?")
                );
            }
            Decision::Deny => {
                return Err(ApiError {
                    status: StatusCode::FORBIDDEN,
                    message: format!(
                        "act denied by hub law (norm: {})",
                        outcome.winning_norm.as_deref().unwrap_or("?")
                    ),
                });
            }
            Decision::Escalate => {
                return Err(ApiError {
                    status: StatusCode::ACCEPTED,
                    message: format!(
                        "act requires escalation to {} ({}); admin review queue is V2-16",
                        outcome.escalate_to.as_deref().unwrap_or("sovereign"),
                        outcome.winning_norm.as_deref().unwrap_or("escalation trigger"),
                    ),
                });
            }
        }
    }
    drop(law_guard);

    // 4. Build the unsigned entry. We need the ledger lock briefly to
    // assign index + prev_hash, then we release it during the (possibly
    // remote) signing roundtrip, then re-acquire to commit. The
    // append_signed call detects if a parallel append landed in between
    // and errors loudly rather than corrupting the chain (per Step 3a's
    // stale-detection contract).
    let event_kind_str = event.kind().to_string();
    let event_value = serde_json::to_value(&event)
        .map_err(|e| ApiError::internal(anyhow::anyhow!("serializing event: {}", e)))?;
    let (unsigned, intent) = {
        let ledger = s.ledger.lock().await;
        let unsigned = ledger.build_entry(s.sovereign_lct_id, event.clone(), Utc::now())
            .map_err(ApiError::internal)?;
        let intent = SignIntent {
            request_id: Uuid::new_v4(),
            hub_id: s.hub_id,
            hub_name: s.hub_name.clone(),
            actor_lct_id: s.sovereign_lct_id,
            ledger_index: unsigned.entry.index,
            event_kind: event_kind_str.clone(),
            event: event_value,
        };
        (unsigned, intent)
    };

    // 5. Sign — via LocalKeypairSigner (MVP) or HestiaCallbackSigner
    // (V2-7+). The signer trait abstracts whether the key lives in
    // process or in a remote vault. Per architecture commitment #8,
    // the hub never holds keys in Hestia-mode chapters.
    let signing_bytes = unsigned.signing_bytes.clone();
    let signature = s.signer
        .sign(s.sovereign_lct_id, &signing_bytes, &intent)
        .await
        .map_err(|e| match e {
            hub_lib::signer::SignError::Denied(reason) => ApiError::unauthorized(
                format!("Sovereign signer denied: {}", reason)
            ),
            hub_lib::signer::SignError::Transport(msg) => ApiError {
                status: StatusCode::SERVICE_UNAVAILABLE,
                message: format!("Sovereign signer unreachable: {}", msg),
            },
            hub_lib::signer::SignError::Malformed(msg) => ApiError::internal(
                anyhow::anyhow!("malformed signer response: {}", msg)
            ),
            hub_lib::signer::SignError::Internal(err) => ApiError::internal(err),
        })?;

    // 6. Commit the signed entry.
    let mut ledger = s.ledger.lock().await;
    let entry = ledger.append_signed(unsigned, signature).await
        .map_err(ApiError::internal)?;

    Ok(Json(EventAccepted {
        entry_index: entry.index,
        entry_hash: entry.entry_hash.clone(),
        event_kind: entry.event.kind().to_string(),
        signer_lct_id: envelope.signer_lct_id,
    }))
}

// ---------- GET /v1/hubs/{hub_id}/state ----------

#[derive(Serialize)]
struct PublicState {
    hub_id: Uuid,
    hub_name: String,
    member_count: usize,
    ledger_entries: u64,
    head_hash: String,
    /// V2-7 Step 2: public roles list (which roles are filled).
    /// Filler identities are public-by-design within the chapter.
    /// V2-8 will gate this on need-to-know per hub law.
    filled_roles: Vec<RoleSnapshot>,
}

#[derive(Serialize)]
struct RoleSnapshot {
    role: String,
    role_lct_id: Uuid,
    filled_by_lct_id: Uuid,
}

async fn read_state(
    State(s): State<RestState>,
    Path(hub_id): Path<Uuid>,
) -> Result<Json<PublicState>, ApiError> {
    if hub_id != s.hub_id {
        return Err(ApiError::not_found(format!(
            "chapter id {} does not match this hub's chapter {}",
            hub_id, s.hub_id
        )));
    }
    let ledger = s.ledger.lock().await;
    let state = HubState::project(&ledger);
    let society = load_society(s.paths.root.clone()).await
        .map_err(ApiError::internal)?;
    let filled_roles: Vec<RoleSnapshot> = society.roles.iter()
        .map(|(name, ra)| RoleSnapshot {
            role: name.clone(),
            role_lct_id: ra.role_lct_id,
            filled_by_lct_id: ra.filling_entity_lct_id,
        })
        .collect();
    let member_count = state.member_count();
    let ledger_entries = ledger.len() as u64;
    let head_hash = ledger.head_hash().to_string();
    Ok(Json(PublicState {
        hub_id: s.hub_id,
        hub_name: state.hub_name,
        member_count,
        ledger_entries,
        head_hash,
        filled_roles,
    }))
}

// ---------- POST /v1/hubs/{id}/channel (E2E member↔hub channel) ----------
//
// Citizen-tier reads/acts never travel in the clear. The member seals a
// request to the hub's LCT (X25519 ECDH from identity keys → ChaCha20-Poly1305,
// `web4_core::pair_channel`); the hub opens it (a successful AEAD open both
// AUTHENTICATES the caller — only the holder of their private key could have
// sealed it — and decrypts), runs the authz pipeline, and seals the response
// back. v1 serves citizen-tier reads; PolicyEntity-on-reads + MRH/trust/
// constellation scoping layer onto `dispatch_channel`.

#[derive(Deserialize)]
struct ChannelRequest {
    caller_lct_id: Uuid,
    pair_id: Uuid,
    /// base64(nonce ‖ ciphertext) sealed to the hub's LCT pubkey.
    sealed: String,
    /// For an **external** caller (not yet a member, so no pinned pubkey): the
    /// self-vouched pubkey to ECDH against. The hub uses it to open the
    /// channel (a successful open proves key possession) but only honors the
    /// `request_citizenship` action — the external→citizen bootstrap, encrypted.
    /// Members ignore this (their pinned pubkey is authoritative).
    #[serde(default)]
    caller_pubkey_hex: Option<String>,
}

#[derive(Serialize)]
struct ChannelResponse {
    sealed: String,
}

/// The decrypted inner request: a tool name + free-form args, mirroring the
/// MCP read surface.
#[derive(Deserialize)]
struct ChannelInner {
    tool: String,
    #[serde(default)]
    args: serde_json::Value,
    /// Anti-replay nonce, fresh per request. Optional for back-compat: when
    /// present it keys the replay guard directly; when absent the guard falls
    /// back to the sealed-blob hash (still rejects byte-identical replays).
    #[serde(default)]
    nonce: Option<String>,
    /// Client send time. Optional for back-compat: when present, requests
    /// outside the freshness window are rejected, which makes the TTL-bounded
    /// replay set complete (a replay can't outlive the window it's checked in).
    #[serde(default)]
    issued_at: Option<DateTime<Utc>>,
}

async fn channel_request(
    State(s): State<RestState>,
    Path(hub_id): Path<Uuid>,
    Json(req): Json<ChannelRequest>,
) -> Result<Json<ChannelResponse>, ApiError> {
    if hub_id != s.hub_id {
        return Err(ApiError::not_found(format!("unknown hub {hub_id}")));
    }
    // The sealed channel is citizen-tier+; a locked vault has no signer to
    // open/seal it. Refuse cleanly (tier-0 only while locked).
    if s.is_locked() {
        return Err(locked_error());
    }

    // Resolve the caller's pubkey: a member's is pinned (authoritative); an
    // external caller (not yet a member) self-vouches one in caller_pubkey_hex,
    // which only unlocks the request_citizenship action below. A successful
    // channel_open authenticates either way (only the key holder could seal).
    let caller_pubkey = {
        let resolver = s.resolver.read().await;
        match resolver.lookup(req.caller_lct_id).map(|lct| lct.public_key) {
            Some(pinned) => pinned,
            None => match req.caller_pubkey_hex.as_deref() {
                Some(hex) => hub_lib::hub::hestia_sovereign_lct(req.caller_lct_id, hex)
                    .map_err(|e| ApiError::bad_request(format!("invalid caller_pubkey_hex: {e}")))?
                    .public_key,
                None => return Err(ApiError::unauthorized(
                    "caller LCT not known to this hub — include caller_pubkey_hex to request citizenship".to_string(),
                )),
            },
        }
    };

    // Open = authenticate (AEAD proves key possession) + decrypt, in one step.
    let plaintext = s.signer
        .channel_open(&caller_pubkey, req.pair_id, &req.sealed)
        .map_err(|_| ApiError::unauthorized(
            "channel authentication/decryption failed".to_string(),
        ))?;
    let inner: ChannelInner = serde_json::from_slice(&plaintext)
        .map_err(|e| ApiError::bad_request(format!("malformed channel request: {e}")))?;

    // Anti-replay. AEAD authenticated the sealer but proves possession, not
    // freshness: a captured `{pair_id, sealed}` POST decrypts identically on
    // re-submission, which would double-witness a write act (referenced_act,
    // record_reputation, …) and inflate the ledger + any reputation folded
    // from it. Freshness-gate when the client dates the request, then dedup on
    // its nonce (or, for older clients, the sealed-blob hash). Keys are
    // namespaced by caller so a nonce value can't collide across members.
    // Reads are idempotent so this is harmless for them; the seal is randomized
    // per call, so a legitimate re-invocation is a new key, never a false reject.
    let now = Utc::now();
    const CHANNEL_FRESHNESS_SECS: i64 = 120;
    if let Some(issued) = inner.issued_at {
        if (now - issued).num_seconds().abs() > CHANNEL_FRESHNESS_SECS {
            return Err(ApiError::bad_request(
                "channel request outside freshness window (replay or clock skew)".to_string(),
            ));
        }
    }
    let replay_key = match &inner.nonce {
        Some(n) => format!("{}:n:{n}", req.caller_lct_id),
        None => format!(
            "{}:h:{}",
            req.caller_lct_id,
            web4_core::crypto::sha256_hex(req.sealed.as_bytes())
        ),
    };
    if !s.replay.check_and_record(&replay_key, now) {
        return Err(ApiError::conflict(
            "channel request replay rejected (already processed)".to_string(),
        ));
    }

    // Authz + dispatch on the decrypted request.
    let response = dispatch_channel(&s, req.caller_lct_id, req.pair_id, req.caller_pubkey_hex.clone(), inner).await?;

    // Seal the response back over the same channel.
    let body = serde_json::to_vec(&response)
        .map_err(|e| ApiError::internal(anyhow::anyhow!("serializing response: {e}")))?;
    let sealed = s.signer
        .channel_seal(&caller_pubkey, req.pair_id, &body)
        .map_err(|e| ApiError::internal(anyhow::anyhow!("sealing response: {e}")))?;

    Ok(Json(ChannelResponse { sealed }))
}

/// Per-tier default cap on how many member records one read may return. The
/// MRH bound at the result layer: a citizen can't bulk-enumerate the whole
/// membership; the Sovereign is unbounded. v1 default — hub law / config
/// will own this value, and a higher trust score or a verified constellation
/// (MFA) will raise it once those subsystems land.
const CITIZEN_READ_LIMIT: usize = 50;

/// Read scope: who is asking + how much they may see. v1 enforces result
/// bounding by tier. `assurance` (single LCT vs verified constellation) and a
/// trust floor are the hooks the constellation / T3-V3 layers attach to — not
/// yet enforced (those subsystems don't exist yet), but threaded here so they
/// slot in without re-touching the read handlers.
struct ReadScope {
    #[allow(dead_code)] // surfaced for the future trust/constellation layers
    role: &'static str,
    /// None = unbounded (Sovereign); Some(n) = at most n records.
    max_results: Option<usize>,
}

impl ReadScope {
    fn for_role(role: &'static str) -> Self {
        let max_results = match role {
            "sovereign" => None,
            _ => Some(CITIZEN_READ_LIMIT),
        };
        ReadScope { role, max_results }
    }

    /// Effective record count: honor the caller's requested `limit` but never
    /// exceed the tier cap.
    fn effective_limit(&self, requested: Option<usize>) -> Option<usize> {
        match (self.max_results, requested) {
            (None, r) => r,
            (Some(cap), Some(r)) => Some(r.min(cap)),
            (Some(cap), None) => Some(cap),
        }
    }
}

/// §5.1 R7 carrier: the effect of an `r7` block on a `referenced_act`.
enum R7Op {
    /// Open an accountability obligation the caller (subject) commits to.
    Open {
        request_id: String,
        role_lct: String,
        due_at: DateTime<Utc>,
        criticality: web4_core::time::Criticality,
    },
    /// Mark that this act satisfies (completes) a prior obligation.
    Satisfy { request_id: String },
}

/// Parse the optional `r7` block on a `referenced_act`. `Ok(None)` = absent.
/// `Err` = present but malformed → the caller rejects the whole act: per the
/// fleet fail-closed convention, an unrecognized/ambiguous R7 shape is
/// `deny+warn`, never "ignore and proceed". Exactly one of `deadline` (open) or
/// `satisfies` (resolve).
fn parse_r7(args: &serde_json::Value) -> Result<Option<R7Op>, ApiError> {
    let Some(r7) = args.get("r7") else {
        return Ok(None);
    };
    let fail = |why: &str| {
        tracing::warn!("referenced_act r7 malformed: {why} — rejected (fail-closed)");
        ApiError::bad_request(format!("malformed r7 block: {why}"))
    };
    if !r7.is_object() {
        return Err(fail("r7 must be an object"));
    }
    match (r7.get("satisfies").is_some(), r7.get("deadline").is_some()) {
        (true, false) => {
            let request_id = r7
                .get("satisfies")
                .and_then(|v| v.as_str())
                .ok_or_else(|| fail("satisfies must be a request_id string"))?
                .to_string();
            Ok(Some(R7Op::Satisfy { request_id }))
        }
        (false, true) => {
            let request_id = r7
                .get("request_id")
                .and_then(|v| v.as_str())
                .ok_or_else(|| fail("open requires request_id"))?
                .to_string();
            let role_lct = r7
                .get("role_lct")
                .and_then(|v| v.as_str())
                .ok_or_else(|| fail("open requires role_lct"))?
                .to_string();
            let dl = r7.get("deadline").unwrap();
            let due_at: DateTime<Utc> = dl
                .get("due_at")
                .and_then(|v| v.as_str())
                .and_then(|s| DateTime::parse_from_rfc3339(s).ok())
                .map(|d| d.with_timezone(&Utc))
                .ok_or_else(|| fail("deadline.due_at must be rfc3339"))?;
            let criticality: web4_core::time::Criticality = dl
                .get("criticality")
                .map(|v| serde_json::from_value(v.clone()))
                .transpose()
                .map_err(|_| fail("deadline.criticality must be soft|firm|hard"))?
                .unwrap_or_default();
            Ok(Some(R7Op::Open { request_id, role_lct, due_at, criticality }))
        }
        _ => Err(fail("exactly one of deadline (open) or satisfies (resolve)")),
    }
}

/// Build the temporal `ReputationDelta` for a resolved obligation from the
/// deadline outcome's `TemporalImpact`. The hub *computes* this from witnessed
/// timestamps (not a caller claim) and folds it via the #430 `ReputationRecorded`
/// path, scoped to the obligation's `(subject_lct, role_lct)`.
fn temporal_delta(
    ob: &hub_lib::state::Obligation,
    request_id: &str,
    outcome: &str,
    impact: &web4_core::time::TemporalImpact,
    action_id: u64,
    action_kind: &str,
    ts: DateTime<Utc>,
) -> web4_core::r6::ReputationDelta {
    use std::collections::HashMap;
    // from_value/to_value are synthetic (0.0 → change): the #430 fold reads only
    // `change` via apply_delta, and the true prior value lives in the projected
    // tensor, not here. They exist to satisfy the TensorDelta shape.
    let mut t3_delta = HashMap::new();
    if impact.temperament != 0.0 {
        t3_delta.insert(
            "temperament".to_string(),
            web4_core::r6::TensorDelta {
                change: impact.temperament,
                from_value: 0.0,
                to_value: impact.temperament,
            },
        );
    }
    let mut v3_delta = HashMap::new();
    if impact.veracity != 0.0 {
        v3_delta.insert(
            "veracity".to_string(),
            web4_core::r6::TensorDelta {
                change: impact.veracity,
                from_value: 0.0,
                to_value: impact.veracity,
            },
        );
    }
    web4_core::r6::ReputationDelta {
        subject_lct: ob.subject_lct.clone(),
        role_lct: ob.role_lct.clone(),
        // Hub-internal obligation-outcome delta: the hub does not hardware-attest
        // the subject's sovereign here, so it stays at the fail-closed default.
        sovereign_strength: web4_core::r6::SovereignStrength::default(),
        action_type: action_kind.to_string(),
        action_target: "hub".to_string(),
        action_id: action_id.to_string(),
        rule_triggered: format!("deadline_{outcome}"),
        reason: format!("obligation {request_id} {outcome}"),
        t3_delta,
        v3_delta,
        contributing_factors: vec![],
        witnesses: vec![],
        timestamp: ts,
    }
}

/// Tier resolution + dispatch for a decrypted channel request.
/// Tiers: Sovereign / citizen (member) → reads; **external** (authenticated
/// LCT, not yet a member) → only `request_citizenship`. Finer role/trust/
/// constellation gating layers on here.
async fn dispatch_channel(
    s: &RestState,
    caller_lct_id: Uuid,
    pair_id: Uuid,
    caller_pubkey_hex: Option<String>,
    inner: ChannelInner,
) -> Result<serde_json::Value, ApiError> {
    let state = {
        let ledger = s.ledger.lock().await;
        s.projected(&ledger)
    };

    // Tier resolution.
    let role = if caller_lct_id == s.sovereign_lct_id {
        "sovereign"
    } else if state.members.contains_key(&caller_lct_id) {
        "citizen"
    } else {
        // External tier: an authenticated non-member. It may request citizenship
        // (the encrypted external→citizen bootstrap) or — if it's been auto-blocked
        // after repeated denials — plead for a denial-review (the repair path).
        // Everything else is refused.
        match inner.tool.as_str() {
            "request_citizenship" =>
                return request_citizenship(s, caller_lct_id, caller_pubkey_hex, &inner.args).await,
            "request_admission_review" =>
                return request_admission_review(s, caller_lct_id, &inner.args).await,
            _ => return Err(ApiError {
                status: StatusCode::FORBIDDEN,
                message: "external LCTs may only request citizenship or a denial review".to_string(),
            }),
        }
    };

    // Presence: any authenticated member contact is a liveness signal — the
    // "bidirectional ping" (calling `presence` both announces you and returns
    // who else is around). Ephemeral + in-memory; never witnessed.
    s.last_seen.lock().await.insert(caller_lct_id, Utc::now());

    // PolicyEntity-on-reads: hub law decides whether this tier may run
    // this read (default-open when no law / no matching norm).
    gate_read(s, role, inner.tool.as_str()).await?;

    // Scoping: bound how much this tier may see (MRH at the result layer).
    let scope = ReadScope::for_role(role);
    let requested = inner.args.get("limit").and_then(|v| v.as_u64()).map(|n| n as usize);
    let limit = scope.effective_limit(requested);

    match inner.tool.as_str() {
        "query_hub" => Ok(serde_json::json!({
            "hub_name": state.hub_name,
            "member_count": state.member_count(),
            "last_ledger_index": state.last_index,
        })),
        // Presence roster — the read half of the bidirectional ping. Each member
        // with a status derived from how recently they last touched the channel:
        // online (<90s) / away (<10m) / offline. Ephemeral; thresholds will move
        // to law later. The caller's own last_seen was just refreshed above.
        "presence" => {
            let seen = s.last_seen.lock().await;
            let now = Utc::now();
            let mut roster: Vec<serde_json::Value> = state.members.keys().map(|lct| {
                let (last, status) = match seen.get(lct) {
                    Some(t) => {
                        let age = (now - *t).num_seconds();
                        let st = if age < 90 { "online" } else if age < 600 { "away" } else { "offline" };
                        (Some(t.to_rfc3339()), st)
                    }
                    None => (None, "offline"),
                };
                serde_json::json!({ "lct_id": lct, "last_seen": last, "status": status })
            }).collect();
            roster.sort_by(|a, b| a["lct_id"].as_str().cmp(&b["lct_id"].as_str()));
            let total = roster.len();
            if let Some(n) = limit { roster.truncate(n); }
            Ok(serde_json::json!({
                "now": now.to_rfc3339(),
                "present": roster,
                "total": total,
                "truncated": total > limit.unwrap_or(total),
            }))
        }
        // R7 reputation READ — the (subject, role) trust/value tensors accrued on
        // this society's ledger. Role-contextualized (RFC #403): pass `role_lct` to
        // scope to one role-pairing, or omit for all of the subject's role reps.
        "reputation" => {
            let Some(subject) = inner.args.get("subject_lct").and_then(|v| v.as_str()) else {
                return Err(ApiError::bad_request("reputation requires 'subject_lct'".to_string()));
            };
            let role_filter = inner.args.get("role_lct").and_then(|v| v.as_str());
            let mut out: Vec<serde_json::Value> = state.reputation.iter()
                .filter(|((subj, role), _)| subj == subject && role_filter.is_none_or(|r| r == role))
                .map(|((subj, role), rep)| serde_json::json!({
                    "subject_lct": subj,
                    "role_lct": role,
                    "t3": rep.t3,
                    "v3": rep.v3,
                    "observations": rep.observations,
                    "sovereign_strength": rep.sovereign_strength,
                    "last_updated": rep.last_updated,
                }))
                .collect();
            let total = out.len();
            if let Some(n) = limit { out.truncate(n); }
            Ok(serde_json::json!({
                "reputation": out,
                "total": total,
                "truncated": total > limit.unwrap_or(total),
            }))
        }
        // R7 reputation RECORD — witness a pre-computed `ReputationDelta` so it folds
        // into the projection. The delta is produced by `web4_core::r6::compute_reputation`
        // (factors × society-law weights); the hub records + applies it, it does NOT
        // invent the scoring math.
        //
        // Authorization (thread repemit-1, co-spec'd with Legion):
        // - **Sovereign** may always record (path unchanged — Sovereign ingest untouched).
        // - A **non-Sovereign authenticated emitter** is gated by the hub law's
        //   `reputation_emit` section. Pin #1: the emitter is the *authenticated
        //   channel identity* (`caller_lct_id`), NOT a payload field — a delta whose
        //   payload names a foreign emitter is irrelevant; only who sealed the op counts.
        //   With no section (or no matching rule) the path is dark: fail-closed deny.
        "record_reputation" => {
            let delta: web4_core::r6::ReputationDelta = inner.args.get("delta")
                .cloned()
                .and_then(|v| serde_json::from_value(v).ok())
                .ok_or_else(|| ApiError::bad_request(
                    "record_reputation requires 'delta' (a ReputationDelta)".to_string()))?;
            if role != "sovereign" {
                // Emitter = the authenticated caller (Pin #1); subject-role = the
                // delta's role_lct (the only role signal the hub holds in v1).
                let emitter = caller_lct_id.to_string();
                let outcome = {
                    let law_guard = s.law.read().await;
                    match law_guard.as_ref() {
                        Some(law) => law.reputation_emit_decision(&emitter, &delta.role_lct),
                        // No law ⇒ dark: Sovereign-only, the pre-wiring behavior.
                        None => hub_lib::law::ReputationEmitOutcome {
                            decision: Decision::Deny,
                            matched_rule: None,
                        },
                    }
                };
                match outcome.decision {
                    Decision::Allow => { /* authorized emit — proceed */ }
                    Decision::Warn => {
                        // Non-blocking flagged-allow: the emit proceeds, flagged.
                        tracing::warn!(
                            "reputation_emit by {emitter} for role '{}' flagged by hub law (rule: {})",
                            delta.role_lct,
                            outcome.matched_rule.as_deref().unwrap_or("?")
                        );
                    }
                    Decision::Deny => {
                        tracing::warn!(
                            "reputation_emit by {emitter} for role '{}' denied (fail-closed; \
                             no matching reputation_emit rule)",
                            delta.role_lct
                        );
                        return Err(ApiError {
                            status: StatusCode::FORBIDDEN,
                            message: "record_reputation not authorized for this emitter by hub law \
                                      (reputation_emit)".to_string(),
                        });
                    }
                    Decision::Escalate => {
                        return Err(ApiError {
                            status: StatusCode::ACCEPTED,
                            message: "record_reputation escalated by hub law (reputation_emit)".to_string(),
                        });
                    }
                }
            }
            let index = witness_event(s, HubEvent::ReputationRecorded { delta }).await?;
            Ok(serde_json::json!({ "recorded": true, "entry_index": index }))
        }
        "list_members" => {
            let all: Vec<&hub_lib::state::Member> = state.members.values().collect();
            let total = all.len();
            let shown: Vec<&hub_lib::state::Member> = match limit {
                Some(n) => all.into_iter().take(n).collect(),
                None => all,
            };
            Ok(serde_json::json!({
                "members": shown,
                "total": total,
                "truncated": total > limit.unwrap_or(total),
            }))
        }
        "find_skill" => {
            let q = inner.args.get("q").and_then(|v| v.as_str()).unwrap_or("").to_lowercase();
            let matches: Vec<&hub_lib::state::Member> = state.members.values()
                .filter(|m| m.skills.iter().any(|sk| sk.contains(&q)))
                .collect();
            let total = matches.len();
            let shown: Vec<&hub_lib::state::Member> = match limit {
                Some(n) => matches.into_iter().take(n).collect(),
                None => matches,
            };
            Ok(serde_json::json!({
                "members": shown,
                "total": total,
                "truncated": total > limit.unwrap_or(total),
            }))
        }
        "find_members" => {
            // Semantic member discovery. The hub is the front door (gating +
            // tier scoping happen here); membot is the engine (the sidecar does
            // the embedding + 3-signal search). top_k is bounded by the tier cap.
            let query = inner.args.get("query").and_then(|v| v.as_str()).unwrap_or("");
            if query.trim().is_empty() {
                return Err(ApiError::bad_request("find_members requires a 'query'".to_string()));
            }
            let requested = inner.args.get("top_k").and_then(|v| v.as_u64()).map(|n| n as usize);
            let effective = scope.effective_limit(requested.or(Some(12))).unwrap_or(12);
            let temperature = inner.args.get("temperature").and_then(|v| v.as_f64()).unwrap_or(0.0);
            let mut hits = membox_find_members(query, effective, temperature).await?;
            // The cart is a pure index: the sidecar returns {member_lct, score}.
            // Re-attach member name from the hub's authoritative (encrypted)
            // registry here — member PII lives once, in the hub, not the cart.
            enrich_member_hits(&mut hits, &state.members);
            Ok(serde_json::json!({
                "results": hits,
                "total": hits.len(),
                "temperature": temperature,
            }))
        }
        // Reserved registration slot for membot's Walk-as-MCP (ships ~2026-06-12):
        // when it lands it's a register-and-gate, not a reimplement. Same role
        // gating + tier scoping as find_members applies (gate_read already ran).
        "walk_members" => Err(ApiError {
            status: StatusCode::NOT_IMPLEMENTED,
            message: "walk_members is reserved for membot's Walk-as-MCP (not yet shipped)".to_string(),
        }),
        // (Credential issuance is NOT a channel tool in the refined design: the
        // wallet pulls directly at /v1/hubs/:id/{nonce,credential} and the
        // holder-key proof — which must be a pinned member key — IS the auth.)
        // ---- introductions (the consent half of discovery) ----
        // Both halves ride the sealed channel, so by construction both parties
        // hold pinned channel keys by the time an intro is accepted — which is
        // exactly what makes the mutual-approval payoff (each side getting the
        // other's pubkey for a direct member↔member pair_channel) possible.
        "request_intro" => {
            let to: Uuid = inner.args.get("to").and_then(|v| v.as_str())
                .and_then(|s| s.parse().ok())
                .ok_or_else(|| ApiError::bad_request("request_intro requires 'to' (member LCT uuid)".to_string()))?;
            // purpose is optional free text — and ledger-witnessed; keep it brief.
            let purpose = inner.args.get("purpose").and_then(|v| v.as_str()).map(String::from);
            if to == caller_lct_id {
                return Err(ApiError::bad_request("cannot request an intro to yourself".to_string()));
            }
            if !state.members.contains_key(&to) {
                return Err(ApiError::bad_request(format!("{to} is not a member of this hub")));
            }
            let dup = state.intros.values().any(|i| {
                i.status == hub_lib::state::IntroStatus::Pending
                    && i.from_lct == caller_lct_id
                    && i.to_lct == to
            });
            if dup {
                return Err(ApiError::bad_request("an intro to that member is already pending".to_string()));
            }
            let intro_id = Uuid::new_v4();
            let event = HubEvent::IntroRequested {
                intro_id,
                from_lct: caller_lct_id,
                to_lct: to,
                purpose,
            };
            let (index, _hash) = commit_pair_event(s, event).await?;
            Ok(serde_json::json!({ "intro_id": intro_id, "status": "pending", "entry_index": index }))
        }
        "list_intros" => {
            // Only intros the caller is a party to — never the full table.
            let mine: Vec<serde_json::Value> = state.intros.values()
                .filter(|i| i.from_lct == caller_lct_id || i.to_lct == caller_lct_id)
                .map(|i| {
                    let mut v = serde_json::json!({
                        "intro_id": i.id,
                        "from_lct": i.from_lct,
                        "to_lct": i.to_lct,
                        "purpose": i.purpose,
                        "status": i.status,
                    });
                    // The mutual-approval payoff: once accepted, each party
                    // gets the OTHER party's pinned pubkey — everything a
                    // direct member↔member pair_channel needs.
                    if i.status == hub_lib::state::IntroStatus::Accepted {
                        let peer = if i.from_lct == caller_lct_id { i.to_lct } else { i.from_lct };
                        v["peer_lct"] = serde_json::json!(peer);
                        v["peer_pubkey_hex"] = serde_json::json!(state.member_pubkeys.get(&peer));
                    }
                    v
                })
                .collect();
            Ok(serde_json::json!({ "intros": mine, "total": mine.len() }))
        }
        "respond_intro" => {
            let intro_id: Uuid = inner.args.get("intro_id").and_then(|v| v.as_str())
                .and_then(|s| s.parse().ok())
                .ok_or_else(|| ApiError::bad_request("respond_intro requires 'intro_id'".to_string()))?;
            let accept = inner.args.get("accept").and_then(|v| v.as_bool())
                .ok_or_else(|| ApiError::bad_request("respond_intro requires 'accept' (bool)".to_string()))?;
            let intro = state.intros.get(&intro_id)
                .ok_or_else(|| ApiError::bad_request(format!("unknown intro {intro_id}")))?;
            if intro.to_lct != caller_lct_id {
                return Err(ApiError {
                    status: StatusCode::FORBIDDEN,
                    message: "only the intro's target may respond".to_string(),
                });
            }
            if intro.status != hub_lib::state::IntroStatus::Pending {
                return Err(ApiError::bad_request("intro is already resolved".to_string()));
            }
            let from = intro.from_lct;
            let event = HubEvent::IntroResponded { intro_id, responded_by: caller_lct_id, accepted: accept };
            let (index, _hash) = commit_pair_event(s, event).await?;
            let mut out = serde_json::json!({
                "intro_id": intro_id,
                "status": if accept { "accepted" } else { "declined" },
                "entry_index": index,
            });
            if accept {
                out["peer_lct"] = serde_json::json!(from);
                out["peer_pubkey_hex"] = serde_json::json!(state.member_pubkeys.get(&from));
                // Hub→citizen push (DRAFT): notify the original requester their intro was
                // accepted — they'd otherwise only learn by polling list_intros.
                let notice = serde_json::json!({
                    "event": "intro_accepted",
                    "intro_id": intro_id,
                    "peer_lct": caller_lct_id,
                    "peer_pubkey_hex": state.member_pubkeys.get(&caller_lct_id),
                }).to_string();
                notify_citizen(s, from, caller_lct_id, "notify:intro_accepted", &format!("intro/{intro_id}"), notice.as_bytes()).await;
            }
            Ok(out)
        }
        // ---- DRAFT: referenced acts + the hub→citizen notification poll floor ----
        "notifications" => {
            // A citizen drains their pending sealed notices (the delivery floor; push to a
            // registered LCT-MCP endpoint is the future optimization on the same queue).
            let cutoff = Utc::now() - chrono::Duration::seconds(NOTICE_TTL_SECS);
            let mut notices = s.notifications.lock().await.remove(&caller_lct_id).unwrap_or_default();
            notices.retain(|n| n.queued_at >= cutoff); // don't deliver expired notices
            Ok(serde_json::json!({ "total": notices.len(), "notifications": notices }))
        }
        "referenced_act" => {
            // A caller submits a generic referenced act (cbp's handoff/sweep/memo). The act's
            // `actor_lct` is the authenticated caller; the hub witnesses it as a verbatim
            // `web4_core::act::Act`. `to` is a core `ActAddress` (Peer/Citizen/Role/Society/
            // FutureSelf); the substance pointer carries a `content_hash` so the witnessed
            // record binds to a specific version and can't silently drift.
            let address: web4_core::act::ActAddress = inner.args.get("to")
                .cloned()
                .and_then(|v| serde_json::from_value(v).ok())
                .ok_or_else(|| ApiError::bad_request("referenced_act requires 'to' (ActAddress)".to_string()))?;
            // The act's routing label — bare `<verb>` for fleet/peer acts
            // ("handoff"/"sweep"/"memo"/"forum"), `notify:<event>` for hub→citizen.
            let kind = inner.args.get("kind").and_then(|v| v.as_str())
                .ok_or_else(|| ApiError::bad_request("referenced_act requires 'kind'".to_string()))?.to_string();
            let uri = inner.args.get("pointer_uri").and_then(|v| v.as_str())
                .ok_or_else(|| ApiError::bad_request("referenced_act requires 'pointer_uri'".to_string()))?.to_string();
            let content_hash = inner.args.get("content_hash").and_then(|v| v.as_str())
                .unwrap_or("").to_string();
            let medium: web4_core::act::SubstanceMedium = inner.args.get("medium")
                .and_then(|v| serde_json::from_value(v.clone()).ok())
                .unwrap_or(web4_core::act::SubstanceMedium::Other);
            // Reversibility is the canonical, actor-assessable property; the council gate
            // (`Irreversible ⇒ proposal_ref`) is derived from it. Defaults to Reversible.
            let consequence: web4_core::act::ConsequenceClass = inner.args.get("consequence")
                .and_then(|v| serde_json::from_value(v.clone()).ok())
                .unwrap_or_default();
            // §5.1 R7 carrier: parse the optional `r7` block up front so a
            // malformed one rejects the whole act (fail-closed) before anything
            // is witnessed.
            let r7_op = parse_r7(&inner.args)?;
            // Validate r7 SEMANTICS against current state here too — before the
            // ReferencedAct is witnessed — so a fail-closed reject never leaves a
            // half-applied act on the ledger. (The apply block below assumes these
            // hold.) Two ambiguous conditions → deny+warn per the fleet directive:
            if let Some(op) = &r7_op {
                match op {
                    // Re-opening a live obligation would let a subject reset its
                    // own clock past a miss, or clobber another member's obligation.
                    R7Op::Open { request_id, .. } => {
                        if state.obligations.contains_key(request_id) {
                            tracing::warn!("r7 re-opens live obligation {request_id} — rejected (fail-closed)");
                            return Err(ApiError::bad_request(format!("obligation {request_id} already open")));
                        }
                    }
                    // Only the obligation's own subject may satisfy it — else a
                    // third party could impose a Late debit or an unearned Met
                    // credit on the subject (griefing).
                    R7Op::Satisfy { request_id } => {
                        let ob = state.obligations.get(request_id).ok_or_else(|| {
                            tracing::warn!("r7 satisfies unknown obligation {request_id} — rejected (fail-closed)");
                            ApiError::bad_request(format!("unknown obligation {request_id}"))
                        })?;
                        if ob.subject_lct != caller_lct_id.to_string() {
                            tracing::warn!("r7 satisfy of {request_id} by non-subject {caller_lct_id} — rejected (fail-closed)");
                            return Err(ApiError::bad_request(
                                "only the obligation's subject may satisfy it".to_string()));
                        }
                    }
                }
            }
            // A Citizen/Peer-addressed act is also a *delivery*: queue a sealed
            // notice in the recipient's mailbox so the act reaches them without
            // them having to read the whole ledger. This is what makes the hub a
            // member→member async message bus (not just a witness): emit a
            // referenced_act to a peer, the peer drains it via `notifications`.
            // Role/Society/FutureSelf are not point-deliveries — witnessed only.
            let recipient = match &address {
                web4_core::act::ActAddress::Citizen { lct_id }
                | web4_core::act::ActAddress::Peer { lct_id } => Some(*lct_id),
                _ => None,
            };
            let notice_kind = kind.clone();
            let notice_uri = uri.clone();
            let act = web4_core::act::Act::addressed(
                caller_lct_id,
                address,
                kind,
                web4_core::act::SubstanceRef::new(uri, content_hash, medium),
                Utc::now(),
            ).with_consequence(consequence);
            let index = witness_event(s, HubEvent::ReferencedAct { act }).await?;
            // §5.1 R7 carrier effects (r7 already validated fail-closed above).
            let mut r7_out = serde_json::Map::new();
            if let Some(op) = r7_op {
                match op {
                    R7Op::Open { request_id, role_lct, due_at, criticality } => {
                        witness_event(s, HubEvent::ObligationOpened {
                            request_id: request_id.clone(),
                            subject_lct: caller_lct_id.to_string(),
                            role_lct,
                            due_at,
                            criticality,
                            opened_at: Utc::now(),
                        }).await?;
                        r7_out.insert("obligation_opened".into(), serde_json::json!(request_id));
                    }
                    R7Op::Satisfy { request_id } => {
                        // Unknown obligation → deny+warn (fail-closed).
                        let ob = state.obligations.get(&request_id).cloned().ok_or_else(|| {
                            tracing::warn!("r7 satisfies unknown obligation {request_id} — rejected (fail-closed)");
                            ApiError::bad_request(format!("unknown obligation {request_id}"))
                        })?;
                        let now = Utc::now();
                        // The hub computes met/late from witnessed timestamps — the
                        // caller can't claim an outcome. completed_at is set, so the
                        // outcome is only ever Met or Late (never Missed/Suspended).
                        let deadline = web4_core::time::Deadline::new(ob.due_at)
                            .with_criticality(ob.criticality);
                        let timing = web4_core::time::Timing::started(ob.opened_at).complete(now);
                        let outcome = deadline.evaluate(
                            &timing,
                            web4_core::time::WitnessAvailability::Available,
                            true,
                            now,
                        );
                        let impact = deadline.reputation_impact(&outcome);
                        let outcome_str = match &outcome {
                            web4_core::time::DeadlineOutcome::Late { .. } => "late",
                            _ => "met",
                        };
                        let delta = temporal_delta(&ob, &request_id, outcome_str, &impact, index, &notice_kind, now);
                        witness_event(s, HubEvent::ReputationRecorded { delta }).await?;
                        witness_event(s, HubEvent::ObligationResolved {
                            request_id: request_id.clone(),
                            outcome: outcome_str.to_string(),
                            resolved_by: Some(caller_lct_id),
                            resolved_at: now,
                        }).await?;
                        r7_out.insert("obligation_resolved".into(), serde_json::json!(request_id));
                        r7_out.insert("outcome".into(), serde_json::json!(outcome_str));
                        r7_out.insert("t3_temperament".into(), serde_json::json!(impact.temperament));
                        r7_out.insert("v3_veracity".into(), serde_json::json!(impact.veracity));
                    }
                }
            }
            // Deliver (best-effort; dropped if the recipient has no pinned key —
            // they can still see the witnessed act on the ledger).
            if let Some(rcpt) = recipient {
                let body = serde_json::json!({
                    "from": caller_lct_id,
                    "kind": notice_kind,
                    "pointer_uri": notice_uri,
                    "entry_index": index,
                })
                .to_string();
                queue_sealed_notice(s, rcpt, caller_lct_id, &notice_kind, &notice_uri, body.as_bytes()).await;
            }
            let mut resp = serde_json::json!({ "recorded": true, "entry_index": index });
            if !r7_out.is_empty() {
                resp.as_object_mut().unwrap().extend(r7_out);
            }
            Ok(resp)
        }
        // ---- constellation attestation (challenge-response MFA, assurance tiers) ----
        // Wire contract: forum/legion-constellation-attestation-wire-shape-2026-06-11.md.
        // Member side ships in hestia (core/src/constellation.rs); this is the
        // verifier half. The derived tier binds to THIS pair_id — it's the
        // `assurance` hook ReadScope already reserves.
        "constellation_challenge" => {
            let nonce = s.constellations.mint_challenge(pair_id);
            Ok(serde_json::json!({ "nonce": nonce }))
        }
        "present_constellation" => {
            let att: hub_lib::constellation::ConstellationAttestation =
                serde_json::from_value(inner.args.clone())
                    .map_err(|e| ApiError::bad_request(format!("malformed attestation: {e}")))?;
            // The attestation must be bound to the channel identity: its owner
            // key is checked against the caller's PINNED resolver pubkey. No
            // pinned key (never enrolled via set-member-key/admission) = reject,
            // never fall back to a self-carried key.
            let pinned = {
                let resolver = s.resolver.read().await;
                resolver.lookup(caller_lct_id).map(|lct| lct.public_key.to_hex())
            };
            let Some(pinned) = pinned else {
                return Err(ApiError {
                    status: StatusCode::FORBIDDEN,
                    message: "no pinned key for this member — enroll a key before presenting a constellation".to_string(),
                });
            };
            use hub_lib::constellation::VerifyError;
            let binding = s.constellations
                .present(pair_id, &att, &pinned, chrono::Utc::now())
                .map_err(|e| match e {
                    // A foreign owner key on an authenticated channel is an
                    // authorization failure (memo rule 3: reject, not warn).
                    VerifyError::ForeignOwnerKey => ApiError {
                        status: StatusCode::FORBIDDEN,
                        message: e.to_string(),
                    },
                    other => ApiError::bad_request(other.to_string()),
                })?;
            Ok(serde_json::json!({
                "assurance": binding.assurance,
                "valid_until": binding.valid_until,
            }))
        }
        other => Err(ApiError::bad_request(format!("unknown or non-channel tool: {other}"))),
    }
}

/// Re-attach member display data (name) to the index-only hits returned by the
/// membox cart, looked up from the authoritative registry. The cart holds no
/// PII — just `member_lct` + embedding — so the hub is the single source of
/// member identity; unknown/absent LCTs are left as-is (lct + score only).
fn enrich_member_hits(
    hits: &mut [serde_json::Value],
    members: &std::collections::BTreeMap<Uuid, hub_lib::state::Member>,
) {
    for hit in hits.iter_mut() {
        if let Some(lct) = hit
            .get("member_lct")
            .and_then(|v| v.as_str())
            .and_then(|s| Uuid::parse_str(s).ok())
        {
            if let Some(name) = members.get(&lct).and_then(|m| m.name.clone()) {
                hit["name"] = serde_json::json!(name);
            }
        }
    }
}

/// True iff `url`'s host is a loopback literal — the membox sidecar is local-only
/// (H-011). Unparseable / non-loopback → false (fail-closed).
fn membox_url_is_local(url: &str) -> bool {
    match reqwest::Url::parse(url).ok().as_ref().and_then(|u| u.host_str()) {
        Some(h) => matches!(h, "127.0.0.1" | "localhost" | "::1" | "[::1]"),
        None => false,
    }
}

/// Call the local membox sidecar (the discovery engine) for semantic member
/// search. The hub composes membot as a localhost dependency; this never faces
/// the network. A sidecar that's down → 503 with a clear message (discovery
/// degraded, the rest of the hub is fine).
async fn membox_find_members(
    query: &str,
    top_k: usize,
    temperature: f64,
) -> Result<Vec<serde_json::Value>, ApiError> {
    let base = std::env::var("WEB4_MEMBOX_URL")
        .unwrap_or_else(|_| "http://127.0.0.1:8771".to_string());
    // H-011: the sidecar is a localhost dependency (see doc above). A non-loopback
    // WEB4_MEMBOX_URL would ship member queries + metadata off-box to an
    // unauthenticated endpoint (exfiltration / result manipulation), so refuse it
    // unless the operator explicitly opts in.
    if !membox_url_is_local(&base)
        && std::env::var("WEB4_MEMBOX_ALLOW_REMOTE").as_deref() != Ok("1")
    {
        tracing::warn!(
            "refusing non-loopback WEB4_MEMBOX_URL={base} (set WEB4_MEMBOX_ALLOW_REMOTE=1 to allow)"
        );
        return Err(ApiError {
            status: StatusCode::SERVICE_UNAVAILABLE,
            message: "member-discovery sidecar must be loopback; set WEB4_MEMBOX_ALLOW_REMOTE=1 to override"
                .to_string(),
        });
    }
    let client = reqwest::Client::new();
    let resp = client
        .post(format!("{}/find_members", base.trim_end_matches('/')))
        .json(&serde_json::json!({ "query": query, "top_k": top_k, "temperature": temperature }))
        .send()
        .await
        .map_err(|e| ApiError {
            status: StatusCode::SERVICE_UNAVAILABLE,
            message: format!("member-discovery engine unreachable: {e}"),
        })?;
    if !resp.status().is_success() {
        let code = resp.status();
        let body = resp.text().await.unwrap_or_default();
        return Err(ApiError {
            status: StatusCode::BAD_GATEWAY,
            message: format!("discovery engine returned {code}: {body}"),
        });
    }
    let body: serde_json::Value = resp
        .json()
        .await
        .map_err(|e| ApiError::internal(anyhow::anyhow!("parsing discovery response: {e}")))?;
    Ok(body
        .get("results")
        .and_then(|r| r.as_array())
        .cloned()
        .unwrap_or_default())
}

/// External→citizen bootstrap over the channel. An authenticated external LCT
/// (proven by the successful channel_open) asks to become a member. Mirrors the
/// plaintext `/members/join` admission, but encrypted: PolicyEntity gates as
/// `role="applicant"`; on accept the Sovereign signs a MemberAdded pinning the
/// applicant's pubkey, and we add them to the resolver so their *next* channel
/// is as a citizen (no caller_pubkey_hex needed).
async fn request_citizenship(
    s: &RestState,
    caller_lct_id: Uuid,
    caller_pubkey_hex: Option<String>,
    args: &serde_json::Value,
) -> Result<serde_json::Value, ApiError> {
    let pubkey_hex = caller_pubkey_hex.ok_or_else(|| ApiError::bad_request(
        "request_citizenship requires the channel to carry caller_pubkey_hex".to_string(),
    ))?;
    // Idempotency: collapse repeat applications from the same LCT — already a
    // member, or an already-pending request, short-circuits without queuing a dup.
    match admission_state(s, caller_lct_id).await {
        AdmissionState::Member =>
            return Ok(serde_json::json!({ "admitted": true, "already_member": true })),
        AdmissionState::Pending(request_id) =>
            return Ok(serde_json::json!({
                "admitted": false, "status": "pending_review",
                "request_id": request_id, "already_pending": true,
            })),
        AdmissionState::Blocked { denials, can_review } =>
            return Ok(serde_json::json!({
                "admitted": false,
                "status": "blocked",
                "denials": denials,
                "can_review": can_review,
                "message": if can_review {
                    "admission blocked after repeated denials — request a denial review (request_admission_review)"
                } else {
                    "admission blocked; review limit reached — awaiting operator admission-reset"
                },
            })),
        AdmissionState::New => {}
    }
    let name = args.get("name").and_then(|v| v.as_str()).map(String::from);
    let event = HubEvent::MemberAdded {
        member_lct_id: caller_lct_id,
        added_by: s.sovereign_lct_id,
        member_name: name,
        member_pubkey_hex: Some(pubkey_hex.clone()),
    };

    // PolicyEntity gate — admission policy from hub law, role="applicant".
    {
        let law_guard = s.law.read().await;
        if let Some(law) = law_guard.as_ref() {
            let payload = serde_yaml::to_value(&event)
                .map_err(|e| ApiError::internal(anyhow::anyhow!("serializing event for R6: {e}")))?;
            let req = R6Request {
                role: "applicant".to_string(),
                action: "member_join_request".to_string(),
                payload,
                resource: Default::default(),
            };
            match law.evaluate_outcome(&req).decision {
                Decision::Allow => {}
                Decision::Warn => {
                    // Non-blocking flagged-allow: admission proceeds, flagged.
                    tracing::warn!("member_join_request flagged by hub law (proceeding)");
                }
                Decision::Deny => return Err(ApiError {
                    status: StatusCode::FORBIDDEN,
                    message: "citizenship denied by hub law".to_string(),
                }),
                Decision::Escalate => {
                    // Queue for operator review (V2-16 admission queue) — witnessed,
                    // not dropped. The applicant gets the request_id back to poll.
                    let request_id = Uuid::new_v4();
                    witness_event(s, HubEvent::MemberJoinRequested {
                        request_id,
                        member_lct_id: caller_lct_id,
                        member_pubkey_hex: pubkey_hex.clone(),
                        name: args.get("name").and_then(|v| v.as_str()).map(String::from),
                        message: args.get("message").and_then(|v| v.as_str()).map(String::from),
                        requested_at: Utc::now(),
                    }).await?;
                    return Ok(serde_json::json!({
                        "admitted": false,
                        "status": "pending_review",
                        "request_id": request_id,
                    }));
                }
            }
        }
    }

    // Sovereign-signs + commits the admission, then pins the new member's
    // pubkey so future channels authenticate them as a citizen.
    let (index, _hash) = commit_pair_event(s, event).await?;
    if let Ok(lct) = hub_lib::hub::hestia_sovereign_lct(caller_lct_id, &pubkey_hex) {
        s.resolver.write().await.insert(lct);
    }

    Ok(serde_json::json!({
        "admitted": true,
        "member_lct_id": caller_lct_id,
        "entry_index": index,
    }))
}

// ---------- POST /v1/admin/reload-law ----------

#[derive(Serialize)]
struct ReloadLawResponse {
    reloaded: bool,
    version: String,
}

async fn reload_law(
    State(s): State<RestState>,
) -> Result<Json<ReloadLawResponse>, ApiError> {
    let version = s.reload_law().await.map_err(ApiError::internal)?;
    Ok(Json(ReloadLawResponse { reloaded: true, version }))
}

// ---------- POST /v1/hubs/{hub_id}/members/join (V2-12) ----------

/// Payload shape inside the SignedEnvelope for a join request. The
/// member signs this with their own keypair; the hub bootstraps
/// signature verification from the supplied `member_pubkey_hex`
/// (since the resolver doesn't yet know this LCT).
#[derive(Clone, Debug, Serialize, Deserialize)]
struct JoinPayload {
    /// MUST be "member_join_request" so a misrouted envelope can't
    /// accidentally trigger a join.
    action: String,
    /// The applicant's LCT id. MUST equal envelope.signer_lct_id.
    member_lct_id: Uuid,
    /// Applicant's public key (hex-encoded 32 bytes) — pinned by this
    /// MemberAdded event for future signature verification.
    member_pubkey_hex: String,
    #[serde(default)]
    name: Option<String>,
    /// Optional free-text note to the operator (surfaced in the review queue
    /// when hub law escalates the request).
    #[serde(default)]
    message: Option<String>,
}

#[derive(Serialize)]
struct JoinAccepted {
    member_lct_id: Uuid,
    entry_index: u64,
    entry_hash: String,
    welcome: String,
}

/// A join request that hub law escalated to operator review — queued, not yet
/// admitted. The applicant polls / the operator actions it via the admin plane.
#[derive(Serialize)]
struct JoinQueued {
    request_id: Uuid,
    status: &'static str,
    message: String,
}

/// Admit a member **through the daemon**: append a Sovereign-signed `MemberAdded`
/// (pinning `member_pubkey_hex`) and insert the new member into the LIVE
/// `MapResolver` — so their envelopes verify immediately, **no serve restart**.
/// Shared by `submit_join` (law-`Allow`) and the operator `approve_join` path.
/// Returns the new entry's `(index, hash)`.
async fn admit_member(
    s: &RestState,
    member_lct_id: Uuid,
    member_pubkey_hex: &str,
    name: Option<String>,
) -> Result<(u64, String), ApiError> {
    let applicant_lct = hub_lib::hub::hestia_sovereign_lct(member_lct_id, member_pubkey_hex)
        .map_err(|e| ApiError::bad_request(format!("invalid member_pubkey_hex: {}", e)))?;
    let index = witness_event(s, HubEvent::MemberAdded {
        member_lct_id,
        added_by: s.sovereign_lct_id,
        member_name: name,
        member_pubkey_hex: Some(member_pubkey_hex.to_string()),
    }).await?;
    // Live resolver insert — the whole point of the no-restart path.
    s.resolver.write().await.insert(applicant_lct);
    let hash = s.ledger.lock().await.head_hash().to_string();
    Ok((index, hash))
}

/// Look up a pending join request from the projection, erroring if it's unknown
/// or already resolved (so admit/deny are idempotent-safe).
async fn pending_join(s: &RestState, request_id: Uuid) -> Result<hub_lib::state::JoinRequest, ApiError> {
    let jr = {
        let ledger = s.ledger.lock().await;
        HubState::project(&ledger).pending_joins.get(&request_id).cloned()
    };
    match jr {
        None => Err(ApiError::not_found(format!("no join request {request_id}"))),
        Some(jr) if jr.status != hub_lib::state::JoinStatus::Pending =>
            Err(ApiError::bad_request(format!("join request {request_id} is already {:?}", jr.status))),
        Some(jr) => Ok(jr),
    }
}

/// The applicant's admission state — drives idempotent + abuse-resistant join handling.
enum AdmissionState {
    /// Already a member; a repeat join is a no-op.
    Member,
    /// A pending request already exists for this LCT — reuse it, don't queue another.
    Pending(Uuid),
    /// Auto-blocked: `denials` ≥ the law's repeat_limit. `can_review` is true while
    /// review requests remain under the law's review_limit (then it's terminal —
    /// cleared only by an operator admission-reset).
    Blocked { denials: u32, can_review: bool },
    /// Neither — proceed to evaluate / queue.
    New,
}

/// The effective admission limits — from hub law, or the defaults when unset
/// (law is the single source of truth; defaults live in `hub_lib::law`).
async fn admission_limits(s: &RestState) -> (u32, u32) {
    match s.law.read().await.as_ref() {
        Some(l) => (l.admission_repeat_limit(), l.admission_review_limit()),
        None => (
            hub_lib::law::DEFAULT_ADMISSION_REPEAT_LIMIT,
            hub_lib::law::DEFAULT_ADMISSION_REVIEW_LIMIT,
        ),
    }
}

/// Idempotency + abuse-resistance gate. Collapses repeat applications (already a
/// member / an existing pending request) and enforces the repair-path block:
/// after repeat_limit denials the applicant is auto-blocked and must request a
/// denial-review (itself capped at review_limit).
async fn admission_state(s: &RestState, lct: Uuid) -> AdmissionState {
    let projected = {
        let ledger = s.ledger.lock().await;
        HubState::project(&ledger)
    };
    if projected.members.contains_key(&lct) {
        return AdmissionState::Member;
    }
    if let Some(jr) = projected
        .pending_joins
        .values()
        .find(|j| j.member_lct_id == lct && j.status == hub_lib::state::JoinStatus::Pending)
    {
        return AdmissionState::Pending(jr.request_id);
    }
    let standing = projected.admission.get(&lct).copied().unwrap_or_default();
    let (repeat_limit, review_limit) = admission_limits(s).await;
    if standing.denials >= repeat_limit {
        return AdmissionState::Blocked {
            denials: standing.denials,
            can_review: standing.reviews < review_limit,
        };
    }
    AdmissionState::New
}

/// Repair path: a blocked applicant pleads for a denial-review (the only
/// self-service way to clear an auto-block). Valid only while blocked and under
/// the law's review_limit; idempotent (an existing pending review is returned).
async fn request_admission_review(
    s: &RestState,
    caller_lct_id: Uuid,
    args: &serde_json::Value,
) -> Result<serde_json::Value, ApiError> {
    let can_review = match admission_state(s, caller_lct_id).await {
        AdmissionState::Member =>
            return Ok(serde_json::json!({ "status": "already_member" })),
        AdmissionState::New =>
            return Err(ApiError::bad_request(
                "no admission block to review — you can apply directly".to_string())),
        AdmissionState::Pending(request_id) =>
            return Ok(serde_json::json!({
                "status": "pending_review", "request_id": request_id,
                "note": "a join request is already queued; no review needed yet",
            })),
        AdmissionState::Blocked { can_review, .. } => can_review,
    };
    // Idempotency FIRST: an outstanding pending review is the applicant's one
    // attempt — a re-plea returns it (and is NOT a fresh attempt against the
    // limit). Only creating a *new* review consumes a slot.
    let existing = {
        let ledger = s.ledger.lock().await;
        HubState::project(&ledger).join_reviews.values()
            .find(|r| r.member_lct_id == caller_lct_id
                && r.status == hub_lib::state::ReviewStatus::Pending)
            .map(|r| r.review_id)
    };
    if let Some(review_id) = existing {
        return Ok(serde_json::json!({
            "status": "pending_review", "review_id": review_id, "already_pending": true }));
    }
    // No pending review → creating a new one requires a free slot.
    if !can_review {
        return Err(ApiError {
            status: StatusCode::CONFLICT,
            message: "review limit reached — awaiting operator admission-reset".to_string(),
        });
    }
    let plea = args.get("plea").and_then(|v| v.as_str()).map(String::from);
    let review_id = Uuid::new_v4();
    witness_event(s, HubEvent::MemberJoinReviewRequested {
        review_id, member_lct_id: caller_lct_id, plea, requested_at: Utc::now(),
    }).await?;
    Ok(serde_json::json!({ "status": "review_requested", "review_id": review_id }))
}

/// Look up a pending denial-review, erroring if unknown or already resolved.
async fn pending_review(s: &RestState, review_id: Uuid) -> Result<hub_lib::state::JoinReview, ApiError> {
    let rv = {
        let ledger = s.ledger.lock().await;
        HubState::project(&ledger).join_reviews.get(&review_id).cloned()
    };
    match rv {
        None => Err(ApiError::not_found(format!("no review {review_id}"))),
        Some(rv) if rv.status != hub_lib::state::ReviewStatus::Pending =>
            Err(ApiError::bad_request(format!("review {review_id} is already {:?}", rv.status))),
        Some(rv) => Ok(rv),
    }
}

/// Operator grants a denial-review → clears the applicant's auto-block (their
/// denial count resets; they may apply afresh).
async fn grant_review(s: &RestState, review_id: Uuid, resolved_by: Uuid) -> Result<u64, ApiError> {
    let _rv = pending_review(s, review_id).await?;
    witness_event(s, HubEvent::MemberJoinReviewResolved {
        review_id, granted: true, resolved_by, reason: None, resolved_at: Utc::now(),
    }).await
}

/// Operator refuses a denial-review (counts toward the review limit).
async fn refuse_review(s: &RestState, review_id: Uuid, resolved_by: Uuid, reason: Option<String>) -> Result<u64, ApiError> {
    let _rv = pending_review(s, review_id).await?;
    witness_event(s, HubEvent::MemberJoinReviewResolved {
        review_id, granted: false, resolved_by, reason, resolved_at: Utc::now(),
    }).await
}

/// Operator hard-reset of an applicant's admission standing — the terminal
/// backstop, clearing both denial and review counts.
async fn admission_reset(s: &RestState, lct: Uuid, reset_by: Uuid, reason: Option<String>) -> Result<u64, ApiError> {
    witness_event(s, HubEvent::MemberAdmissionReset {
        member_lct_id: lct, reset_by, reason, reset_at: Utc::now(),
    }).await
}

/// Operator approves a pending join request: admit the member live (no restart)
/// and witness the resolution. The audit trail is request → resolution + the
/// `MemberAdded`, all signed by the Sovereign.
async fn approve_join(s: &RestState, request_id: Uuid, resolved_by: Uuid) -> Result<(u64, String), ApiError> {
    let jr = pending_join(s, request_id).await?;
    let (index, hash) = admit_member(s, jr.member_lct_id, &jr.member_pubkey_hex, jr.name.clone()).await?;
    witness_event(s, HubEvent::MemberJoinResolved {
        request_id,
        approved: true,
        resolved_by,
        reason: None,
        resolved_at: Utc::now(),
    }).await?;
    Ok((index, hash))
}

/// Operator denies a pending join request: witness the resolution, admit nothing.
async fn deny_join(s: &RestState, request_id: Uuid, resolved_by: Uuid, reason: Option<String>) -> Result<u64, ApiError> {
    let _jr = pending_join(s, request_id).await?;
    witness_event(s, HubEvent::MemberJoinResolved {
        request_id,
        approved: false,
        resolved_by,
        reason,
        resolved_at: Utc::now(),
    }).await
}

/// Pin (or rotate) an existing member's channel pubkey **through the daemon**:
/// witness `MemberKeyPinned` and update the LIVE resolver in place — the
/// no-restart equivalent of the `hub set-member-key` CLI (which writes the store
/// out-of-band and leaves the running daemon's resolver stale until reboot). The
/// member must already exist; `insert` replaces the prior entry for this LCT id,
/// so this is the re-key path (sprout's JetPack-wipe case for an existing member).
async fn pin_member_key(s: &RestState, member_lct_id: Uuid, pubkey_hex: &str) -> Result<u64, ApiError> {
    let lct = hub_lib::hub::hestia_sovereign_lct(member_lct_id, pubkey_hex)
        .map_err(|e| ApiError::bad_request(format!("invalid pubkey_hex: {}", e)))?;
    {
        let ledger = s.ledger.lock().await;
        if !HubState::project(&ledger).members.contains_key(&member_lct_id) {
            return Err(ApiError::not_found(format!("no member {member_lct_id} to key")));
        }
    }
    let index = witness_event(s, HubEvent::MemberKeyPinned {
        member_lct_id,
        member_pubkey_hex: pubkey_hex.to_string(),
        pinned_by: s.sovereign_lct_id,
    }).await?;
    s.resolver.write().await.insert(lct);
    Ok(index)
}

/// Remove a member **through the daemon**: witness `MemberRemoved` and evict them
/// from the LIVE resolver — no restart; their envelopes stop verifying as a
/// member immediately. (The projection also drops their pinned key, so a future
/// restart won't re-seed them.)
async fn remove_member_live(s: &RestState, member_lct_id: Uuid, reason: Option<String>) -> Result<u64, ApiError> {
    {
        let ledger = s.ledger.lock().await;
        if !HubState::project(&ledger).members.contains_key(&member_lct_id) {
            return Err(ApiError::not_found(format!("no member {member_lct_id} to remove")));
        }
    }
    let index = witness_event(s, HubEvent::MemberRemoved {
        member_lct_id,
        removed_by: s.sovereign_lct_id,
        reason,
    }).await?;
    s.resolver.write().await.0.remove(&member_lct_id);
    Ok(index)
}

// ============================================================================
// Operator plane — a SEPARATE 127.0.0.1-only listener (never network-exposed).
// ============================================================================
//
// The network-facing port (0.0.0.0:8770) stays read-only for admin + carries the
// signed APIs. Member-admission *writes* (admit/deny/remove/re-key) live here, on
// a listener bound to loopback only, so a remote caller cannot reach them even
// through a TLS-terminating reverse proxy on the same host (which forwards as
// 127.0.0.1 and would defeat a plain loopback check on the shared port). Being on
// this local plane while the hub is
// ignited IS the authorization — the actions sign as the Sovereign via the live
// signer (they fail closed if the hub is locked). Defense-in-depth: every handler
// also re-checks loopback.

/// Reject any non-loopback caller. Redundant given the 127.0.0.1 bind, but cheap
/// belt-and-suspenders so a future mis-bind can't silently expose operator writes.
fn require_loopback(peer: &SocketAddr) -> Result<(), ApiError> {
    if !peer.ip().is_loopback() {
        return Err(ApiError {
            status: StatusCode::FORBIDDEN,
            message: "operator API is local-only (reach it from the hub host / a local tunnel)".to_string(),
        });
    }
    Ok(())
}

#[derive(Deserialize)]
struct ReasonBody {
    #[serde(default)]
    reason: Option<String>,
}

#[derive(Deserialize)]
struct KeyBody {
    pubkey_hex: String,
}

/// `GET /admin/api/joins` — the admission queue (pending first, newest first).
async fn admin_list_joins(
    State(s): State<RestState>,
    ConnectInfo(peer): ConnectInfo<SocketAddr>,
) -> Result<Json<serde_json::Value>, ApiError> {
    require_loopback(&peer)?;
    let projected = {
        let ledger = s.ledger.lock().await;
        HubState::project(&ledger)
    };
    let mut joins: Vec<hub_lib::state::JoinRequest> = projected.pending_joins.into_values().collect();
    joins.sort_by(|a, b| {
        use hub_lib::state::JoinStatus::Pending;
        // Pending first, then most-recent request first.
        let ap = (a.status != Pending, std::cmp::Reverse(a.requested_at));
        let bp = (b.status != Pending, std::cmp::Reverse(b.requested_at));
        ap.cmp(&bp)
    });
    let pending = joins.iter().filter(|j| j.status == hub_lib::state::JoinStatus::Pending).count();
    Ok(Json(serde_json::json!({ "pending": pending, "total": joins.len(), "joins": joins })))
}

/// `POST /admin/api/joins/:request_id/admit` — approve a pending join (live).
async fn admin_admit_join(
    State(s): State<RestState>,
    ConnectInfo(peer): ConnectInfo<SocketAddr>,
    Path(request_id): Path<Uuid>,
) -> Result<Json<serde_json::Value>, ApiError> {
    require_loopback(&peer)?;
    let (entry_index, entry_hash) = approve_join(&s, request_id, s.sovereign_lct_id).await?;
    Ok(Json(serde_json::json!({ "approved": true, "entry_index": entry_index, "entry_hash": entry_hash })))
}

/// `POST /admin/api/joins/:request_id/deny` — deny a pending join.
async fn admin_deny_join(
    State(s): State<RestState>,
    ConnectInfo(peer): ConnectInfo<SocketAddr>,
    Path(request_id): Path<Uuid>,
    Json(body): Json<ReasonBody>,
) -> Result<Json<serde_json::Value>, ApiError> {
    require_loopback(&peer)?;
    let entry_index = deny_join(&s, request_id, s.sovereign_lct_id, body.reason).await?;
    Ok(Json(serde_json::json!({ "denied": true, "entry_index": entry_index })))
}

/// `POST /admin/api/members/:lct_id/key` — pin/rotate a member's channel key (live).
async fn admin_pin_key(
    State(s): State<RestState>,
    ConnectInfo(peer): ConnectInfo<SocketAddr>,
    Path(lct_id): Path<Uuid>,
    Json(body): Json<KeyBody>,
) -> Result<Json<serde_json::Value>, ApiError> {
    require_loopback(&peer)?;
    let entry_index = pin_member_key(&s, lct_id, &body.pubkey_hex).await?;
    Ok(Json(serde_json::json!({ "pinned": true, "entry_index": entry_index })))
}

/// `POST /admin/api/members/:lct_id/remove` — remove a member (live eviction).
async fn admin_remove_member(
    State(s): State<RestState>,
    ConnectInfo(peer): ConnectInfo<SocketAddr>,
    Path(lct_id): Path<Uuid>,
    Json(body): Json<ReasonBody>,
) -> Result<Json<serde_json::Value>, ApiError> {
    require_loopback(&peer)?;
    let entry_index = remove_member_live(&s, lct_id, body.reason).await?;
    Ok(Json(serde_json::json!({ "removed": true, "entry_index": entry_index })))
}

#[derive(Deserialize)]
struct AddMemberBody {
    lct_id: Uuid,
    pubkey_hex: String,
    #[serde(default)]
    name: Option<String>,
}

/// `POST /admin/api/members/add` — the Sovereign adds a *known* member directly
/// (e.g. a fleet machine whose pubkey is already committed), without waiting for
/// a self-submitted join request. Live (no restart). This is the proactive
/// counterpart to the request-driven queue; it's a Sovereign act, so it isn't
/// law-gated (the operator IS the authority), same stance as the add-member CLI.
async fn admin_add_member(
    State(s): State<RestState>,
    ConnectInfo(peer): ConnectInfo<SocketAddr>,
    Json(body): Json<AddMemberBody>,
) -> Result<Json<serde_json::Value>, ApiError> {
    require_loopback(&peer)?;
    {
        let ledger = s.ledger.lock().await;
        if HubState::project(&ledger).members.contains_key(&body.lct_id) {
            return Err(ApiError::bad_request(format!("{} is already a member", body.lct_id)));
        }
    }
    let (entry_index, entry_hash) = admit_member(&s, body.lct_id, &body.pubkey_hex, body.name).await?;
    Ok(Json(serde_json::json!({ "added": true, "entry_index": entry_index, "entry_hash": entry_hash })))
}

/// The operator-plane write API. Mounted ONLY on the loopback operator listener.
/// `GET /admin/api/reviews` — the denial-review queue (pending first), with the
/// effective admission limits for context.
async fn admin_list_reviews(
    State(s): State<RestState>,
    ConnectInfo(peer): ConnectInfo<SocketAddr>,
) -> Result<Json<serde_json::Value>, ApiError> {
    require_loopback(&peer)?;
    let projected = {
        let ledger = s.ledger.lock().await;
        HubState::project(&ledger)
    };
    let mut reviews: Vec<hub_lib::state::JoinReview> = projected.join_reviews.into_values().collect();
    reviews.sort_by(|a, b| {
        use hub_lib::state::ReviewStatus::Pending;
        let ak = (a.status != Pending, std::cmp::Reverse(a.requested_at));
        let bk = (b.status != Pending, std::cmp::Reverse(b.requested_at));
        ak.cmp(&bk)
    });
    let pending = reviews.iter().filter(|r| r.status == hub_lib::state::ReviewStatus::Pending).count();
    let (repeat_limit, review_limit) = admission_limits(&s).await;
    Ok(Json(serde_json::json!({
        "pending": pending, "total": reviews.len(), "reviews": reviews,
        "limits": { "repeat_limit": repeat_limit, "review_limit": review_limit },
    })))
}

/// `POST /admin/api/reviews/:review_id/grant` — clear the applicant's auto-block.
async fn admin_grant_review(
    State(s): State<RestState>,
    ConnectInfo(peer): ConnectInfo<SocketAddr>,
    Path(review_id): Path<Uuid>,
) -> Result<Json<serde_json::Value>, ApiError> {
    require_loopback(&peer)?;
    let entry_index = grant_review(&s, review_id, s.sovereign_lct_id).await?;
    Ok(Json(serde_json::json!({ "granted": true, "entry_index": entry_index })))
}

/// `POST /admin/api/reviews/:review_id/refuse` — refuse (counts toward the limit).
async fn admin_refuse_review(
    State(s): State<RestState>,
    ConnectInfo(peer): ConnectInfo<SocketAddr>,
    Path(review_id): Path<Uuid>,
    Json(body): Json<ReasonBody>,
) -> Result<Json<serde_json::Value>, ApiError> {
    require_loopback(&peer)?;
    let entry_index = refuse_review(&s, review_id, s.sovereign_lct_id, body.reason).await?;
    Ok(Json(serde_json::json!({ "refused": true, "entry_index": entry_index })))
}

/// `POST /admin/api/members/:lct_id/admission-reset` — terminal backstop: clear
/// an applicant's denial + review standing so they may apply afresh.
async fn admin_admission_reset(
    State(s): State<RestState>,
    ConnectInfo(peer): ConnectInfo<SocketAddr>,
    Path(lct_id): Path<Uuid>,
    Json(body): Json<ReasonBody>,
) -> Result<Json<serde_json::Value>, ApiError> {
    require_loopback(&peer)?;
    let entry_index = admission_reset(&s, lct_id, s.sovereign_lct_id, body.reason).await?;
    Ok(Json(serde_json::json!({ "reset": true, "entry_index": entry_index })))
}

#[derive(Deserialize)]
struct AdmissionLimitsBody {
    #[serde(default)]
    repeat_limit: Option<u32>,
    #[serde(default)]
    review_limit: Option<u32>,
}

/// Advance a law version on amendment: increment the trailing numeric component
/// (semver patch), e.g. `1.0.0` → `1.0.1`; fall back to appending `.1` for
/// non-numeric versions.
fn bump_law_version(v: &str) -> String {
    let parts: Vec<&str> = v.split('.').collect();
    if let Some((last, head)) = parts.split_last() {
        if let Ok(n) = last.parse::<u64>() {
            let mut out: Vec<String> = head.iter().map(|s| s.to_string()).collect();
            out.push((n + 1).to_string());
            return out.join(".");
        }
    }
    format!("{v}.1")
}

/// Hydrate code defaults into the live hub law so every law-driven parameter is
/// inspectable in the law itself. Runs once when the hub becomes operational
/// (normal boot / post-ignition). Writes a witnessed `LawAmended` **only if a
/// default was actually filled** (idempotent — steady-state boots are no-ops),
/// so newly-added parameters auto-populate on first boot with no maintenance.
/// No-op when no law is set (operator establishes a base law via `hub init-law`).
pub(crate) async fn hydrate_law_defaults(s: &RestState) -> anyhow::Result<bool> {
    let mut law = match s.law.read().await.clone() {
        Some(l) => l,
        None => return Ok(false),
    };
    if !law.hydrate_defaults() {
        return Ok(false);
    }
    law.version = bump_law_version(&law.version);
    let yaml = serde_yaml::to_string(&law)?;
    hub_lib::law::Law::parse_and_validate(&yaml)?; // sanity — must still validate
    {
        let mut ledger = s.ledger.lock().await;
        ledger.store_mut().write_law(&yaml).await?;
    }
    witness_event(s, HubEvent::LawAmended {
        new_law_sha256: hub_lib::law::Law::sha256_hex_of(&yaml),
        amended_by: s.sovereign_lct_id,
        version: law.version.clone(),
        diff_summary: Some("auto-hydrate law defaults".to_string()),
    })
    .await
    .map_err(|e| anyhow::anyhow!("witnessing law-default hydration: {}", e.message))?;
    *s.law.write().await = Some(law);
    Ok(true)
}

/// `POST /admin/api/admission-limits` — set the admission repeat/review limits by
/// **amending chapter law** (law is the single inspectable source of truth — the
/// operator's choice is written there, witnessed via LawAmended, not a side
/// config). Requires a base law to exist (`hub init-law`).
async fn admin_set_admission_limits(
    State(s): State<RestState>,
    ConnectInfo(peer): ConnectInfo<SocketAddr>,
    Json(body): Json<AdmissionLimitsBody>,
) -> Result<Json<serde_json::Value>, ApiError> {
    require_loopback(&peer)?;
    let mut law = s.law.read().await.clone().ok_or_else(|| ApiError::bad_request(
        "no hub law set — run `hub init-law` first, then set admission limits".to_string(),
    ))?;
    {
        let adm = law.ext.admission.get_or_insert_with(Default::default);
        if let Some(r) = body.repeat_limit { adm.repeat_limit = Some(r); }
        if let Some(r) = body.review_limit { adm.review_limit = Some(r); }
    }
    // Each amendment advances the version (semver patch bump); the witnessed
    // LawAmended records who/when/sha alongside.
    law.version = bump_law_version(&law.version);
    let yaml = serde_yaml::to_string(&law)
        .map_err(|e| ApiError::internal(anyhow::anyhow!("serializing law: {e}")))?;
    // Sanity: the amended law must still parse + validate.
    hub_lib::law::Law::parse_and_validate(&yaml)
        .map_err(|e| ApiError::internal(anyhow::anyhow!("amended law invalid: {e}")))?;
    {
        let mut ledger = s.ledger.lock().await;
        ledger.store_mut().write_law(&yaml).await.map_err(ApiError::internal)?;
    }
    let entry_index = witness_event(&s, HubEvent::LawAmended {
        new_law_sha256: hub_lib::law::Law::sha256_hex_of(&yaml),
        amended_by: s.sovereign_lct_id,
        version: law.version.clone(),
        diff_summary: Some("admission limits set via operator plane".to_string()),
    }).await?;
    let (repeat_limit, review_limit) = (law.admission_repeat_limit(), law.admission_review_limit());
    *s.law.write().await = Some(law);
    Ok(Json(serde_json::json!({
        "updated": true, "entry_index": entry_index,
        "repeat_limit": repeat_limit, "review_limit": review_limit,
    })))
}

/// Query for [`admin_ledger_tail`].
#[derive(Deserialize)]
struct LedgerTailQuery {
    /// Return entries with `index >= since`. Omitted → the last `limit` entries.
    /// Poll pattern: pass the previous response's `total` as `since` next time.
    since: Option<u64>,
    /// Max entries returned. Default 50, hard-capped at 500.
    limit: Option<usize>,
}

/// `GET /admin/api/ledger?since=N&limit=M` — operator-plane ledger tail.
///
/// Returns the witnessed-act **envelope metadata** (index, actor, event kind,
/// and for a `referenced_act` the recipient + act kind + pointer) straight from
/// the daemon's in-memory ledger. This is the operator's view of the witnessed
/// chain — e.g. observing the thor↔cbp channel flow — **without the vault
/// passphrase** (the running daemon already holds the ledger decrypted).
///
/// It never exposes sealed notice **bodies**: those ride the mailbox encrypted
/// to the recipient and are not on the ledger. Local-only (operator plane).
async fn admin_ledger_tail(
    State(s): State<RestState>,
    ConnectInfo(peer): ConnectInfo<SocketAddr>,
    axum::extract::Query(q): axum::extract::Query<LedgerTailQuery>,
) -> Result<Json<serde_json::Value>, ApiError> {
    require_loopback(&peer)?;
    let ledger = s.ledger.lock().await;
    let entries = ledger.entries();
    let total = entries.len();
    let limit = q.limit.unwrap_or(50).min(500);
    // Default window is the last `limit` entries; an explicit `since` overrides
    // (clamped to the chain length so an over-large cursor just returns empty).
    let start = match q.since {
        Some(n) => (n as usize).min(total),
        None => total.saturating_sub(limit),
    };
    let acts: Vec<serde_json::Value> = entries
        .iter()
        .skip(start)
        .take(limit)
        .map(|e| {
            let mut v = serde_json::json!({
                "index": e.index,
                "at": e.timestamp,
                "actor": e.actor_lct_id,
                "event": e.event.kind(),
            });
            if let HubEvent::ReferencedAct { act } = &e.event {
                use web4_core::act::ActAddress::*;
                let (to_kind, to): (&str, Option<Uuid>) = match &act.address {
                    Citizen { lct_id } => ("citizen", Some(*lct_id)),
                    Peer { lct_id } => ("peer", Some(*lct_id)),
                    Society { lct_id } => ("society", Some(*lct_id)),
                    FutureSelf { entity } => ("future_self", Some(*entity)),
                    Role { role } => {
                        v["to_role"] = serde_json::json!(role);
                        ("role", None)
                    }
                };
                v["to_kind"] = serde_json::json!(to_kind);
                if let Some(id) = to {
                    v["to"] = serde_json::json!(id);
                }
                v["act_kind"] = serde_json::json!(act.kind);
                v["pointer"] = serde_json::json!(act.substance.uri);
            }
            v
        })
        .collect();
    Ok(Json(serde_json::json!({
        "total": total,
        "head_hash": ledger.head_hash(),
        "returned": acts.len(),
        "acts": acts,
    })))
}

pub fn admin_api_router(state: RestState) -> Router {
    Router::new()
        .route("/admin/api/admission-limits", post(admin_set_admission_limits))
        .route("/admin/api/ledger", get(admin_ledger_tail))
        .route("/admin/api/joins", get(admin_list_joins))
        .route("/admin/api/joins/:request_id/admit", post(admin_admit_join))
        .route("/admin/api/joins/:request_id/deny", post(admin_deny_join))
        .route("/admin/api/reviews", get(admin_list_reviews))
        .route("/admin/api/reviews/:review_id/grant", post(admin_grant_review))
        .route("/admin/api/reviews/:review_id/refuse", post(admin_refuse_review))
        .route("/admin/api/members/add", post(admin_add_member))
        .route("/admin/api/members/:lct_id/key", post(admin_pin_key))
        .route("/admin/api/members/:lct_id/remove", post(admin_remove_member))
        .route("/admin/api/members/:lct_id/admission-reset", post(admin_admission_reset))
        .with_state(state)
}

async fn submit_join(
    State(s): State<RestState>,
    Path(hub_id): Path<Uuid>,
    Json(envelope): Json<SignedEnvelope>,
) -> Result<axum::response::Response, ApiError> {
    use axum::response::IntoResponse;
    if hub_id != s.hub_id {
        return Err(ApiError::not_found(format!(
            "hub id {} does not match this hub {}", hub_id, s.hub_id
        )));
    }

    // 1. Parse the join payload from the envelope.
    let payload: JoinPayload = serde_json::from_value(envelope.payload.clone())
        .map_err(|e| ApiError::bad_request(format!("join payload not parseable: {}", e)))?;
    if payload.action != "member_join_request" {
        return Err(ApiError::bad_request(format!(
            "join endpoint requires action='member_join_request', got '{}'",
            payload.action
        )));
    }
    if payload.member_lct_id != envelope.signer_lct_id {
        return Err(ApiError::bad_request(format!(
            "envelope.signer_lct_id ({}) must match payload.member_lct_id ({})",
            envelope.signer_lct_id, payload.member_lct_id,
        )));
    }

    // 2. Bootstrap signature verification against the payload-supplied
    // pubkey. Adhoc one-shot resolver containing just the applicant —
    // we can't go through s.resolver because the applicant isn't there
    // yet (that's the whole point of join). The pubkey is self-vouched
    // for this single act; downstream verification trusts the same key
    // because admission pinned it into the ledger.
    let applicant_lct = hub_lib::hub::hestia_sovereign_lct(
        payload.member_lct_id, &payload.member_pubkey_hex,
    ).map_err(|e| ApiError::bad_request(format!("invalid member_pubkey_hex: {}", e)))?;
    let mut adhoc = MapResolver::new();
    adhoc.insert(applicant_lct.clone());
    let _redeemed = verify_envelope(&envelope, &s.nonces, &adhoc, Utc::now())?;

    // 2b. Idempotency: collapse repeat applications from the same LCT before the
    // law gate. Already a member → 200 already_member; an existing pending request
    // → 202 with that request_id (don't queue a duplicate). Only a genuinely-new
    // applicant proceeds to evaluation.
    match admission_state(&s, payload.member_lct_id).await {
        AdmissionState::Member => {
            return Ok((
                StatusCode::OK,
                Json(serde_json::json!({
                    "member_lct_id": payload.member_lct_id,
                    "status": "already_member",
                    "welcome": format!("already a member of {}", s.hub_name),
                })),
            ).into_response());
        }
        AdmissionState::Pending(request_id) => {
            return Ok((
                StatusCode::ACCEPTED,
                Json(JoinQueued {
                    request_id,
                    status: "pending_review",
                    message: format!("a join request is already queued for review at {}", s.hub_name),
                }),
            ).into_response());
        }
        AdmissionState::Blocked { denials, can_review } => {
            return Ok((
                StatusCode::FORBIDDEN,
                Json(serde_json::json!({
                    "status": "blocked",
                    "denials": denials,
                    "can_review": can_review,
                    "message": if can_review {
                        "admission blocked after repeated denials — request a denial review"
                    } else {
                        "admission blocked; review limit reached — awaiting operator admission-reset"
                    },
                })),
            ).into_response());
        }
        AdmissionState::New => {}
    }

    // 3. PolicyEntity gate — admission policy from hub law. The R6 payload
    // is the MemberAdded we *would* record. Allow → auto-admit; Deny → reject;
    // Escalate → queue for operator review (V2-16 admission queue).
    let prospective = HubEvent::MemberAdded {
        member_lct_id: payload.member_lct_id,
        added_by: s.sovereign_lct_id,
        member_name: payload.name.clone(),
        member_pubkey_hex: Some(payload.member_pubkey_hex.clone()),
    };
    let event_value_yaml = serde_yaml::to_value(&prospective)
        .map_err(|e| ApiError::internal(anyhow::anyhow!("serializing event for R6: {}", e)))?;

    let decision = {
        let law_guard = s.law.read().await;
        match law_guard.as_ref() {
            None => Decision::Allow, // open-by-default when no law is set
            Some(law) => law.evaluate_outcome(&R6Request {
                role: "applicant".to_string(),
                action: "member_join_request".to_string(),
                payload: event_value_yaml,
                resource: Default::default(),
            }).decision,
        }
    };

    match decision {
        Decision::Deny => Err(ApiError {
            status: StatusCode::FORBIDDEN,
            message: "membership denied by hub law".to_string(),
        }),
        Decision::Allow | Decision::Warn => {
            // Auto-admit, live (no restart). Warn is a non-blocking
            // flagged-allow: same path, with the advisory surfaced.
            if decision == Decision::Warn {
                tracing::warn!("member join flagged by hub law (auto-admitting)");
            }
            let (entry_index, entry_hash) = admit_member(
                &s, payload.member_lct_id, &payload.member_pubkey_hex, payload.name.clone(),
            ).await?;
            Ok(Json(JoinAccepted {
                member_lct_id: payload.member_lct_id,
                entry_index,
                entry_hash,
                welcome: format!("welcome to {}", s.hub_name),
            }).into_response())
        }
        Decision::Escalate => {
            // Queue for operator review — witnessed, NOT dropped (closes the
            // V2-16 gap). The operator admits/denies via the admin plane.
            let request_id = Uuid::new_v4();
            witness_event(&s, HubEvent::MemberJoinRequested {
                request_id,
                member_lct_id: payload.member_lct_id,
                member_pubkey_hex: payload.member_pubkey_hex.clone(),
                name: payload.name.clone(),
                message: payload.message.clone(),
                requested_at: Utc::now(),
            }).await?;
            Ok((
                StatusCode::ACCEPTED,
                Json(JoinQueued {
                    request_id,
                    status: "pending_review",
                    message: format!("join request queued for operator review at {}", s.hub_name),
                }),
            ).into_response())
        }
    }
}

// ---------- PolicyEntity gate helper (V2-8 §4) ----------

/// Build an R6Request from a SignedEnvelope + the resolved HubEvent.
///
/// Sprint 3 (V2-7 §2 broadening): the role is now derived from the
/// signer. Sovereign envelopes get role="sovereign"; member envelopes
/// get role="citizen" (the base membership role per Web4 spec). Chapter
/// law can therefore write different norms for each — e.g., allow
/// citizens to declare_skill but deny them from add_member (which
/// is already enforced upstream in submit_event's per-action check;
/// the law can add policy on top of code-level authorization).
/// PolicyEntity-on-reads (the read half of the §8 "PolicyEntity gates queries
/// the same way it gates writes" commitment). Evaluate a read of `tool` by a
/// caller in `role` against hub law. No law → Allow (open-by-default, the
/// pre-gate behavior). Reads are namespaced `read:<tool>` in the action so
/// read norms don't collide with act (event-kind) norms. Pure + testable;
/// `gate_read` wires it to the live law slot + HTTP status codes.
fn read_decision(law: Option<&Law>, role: &str, tool: &str) -> DecisionOutcome {
    let Some(law) = law else {
        return DecisionOutcome {
            decision: Decision::Allow,
            winning_norm: None,
            escalation_index: None,
            escalate_to: None,
        };
    };
    let req = R6Request {
        role: role.to_string(),
        action: format!("read:{tool}"),
        payload: Default::default(),
        resource: Default::default(),
    };
    law.evaluate_outcome(&req)
}

/// Gate a channel read against hub law. Allow → proceed; Deny → 403;
/// Escalate → 202 (the read is held pending the escalation target's review).
async fn gate_read(s: &RestState, role: &str, tool: &str) -> Result<(), ApiError> {
    let law_guard = s.law.read().await;
    let outcome = read_decision(law_guard.as_ref(), role, tool);
    match outcome.decision {
        Decision::Allow => Ok(()),
        Decision::Warn => {
            // Non-blocking flagged-allow: the read proceeds, flagged.
            tracing::warn!(
                "read '{tool}' flagged by hub law (norm: {})",
                outcome.winning_norm.as_deref().unwrap_or("?")
            );
            Ok(())
        }
        Decision::Deny => Err(ApiError {
            status: StatusCode::FORBIDDEN,
            message: format!(
                "read '{tool}' denied by hub law (norm: {})",
                outcome.winning_norm.as_deref().unwrap_or("?")
            ),
        }),
        Decision::Escalate => Err(ApiError {
            status: StatusCode::ACCEPTED,
            message: format!(
                "read '{tool}' escalated to {} by hub law",
                outcome.escalate_to.as_deref().unwrap_or("sovereign")
            ),
        }),
    }
}

fn build_r6_request(
    envelope: &SignedEnvelope,
    event: &HubEvent,
    sovereign_lct_id: Uuid,
) -> anyhow::Result<R6Request> {
    let payload = serde_yaml::to_value(event)
        .map_err(|e| anyhow::anyhow!("serializing event for R6: {}", e))?;
    let role = if envelope.signer_lct_id == sovereign_lct_id {
        "sovereign"
    } else {
        "citizen"
    };
    Ok(R6Request {
        role: role.to_string(),
        action: event.kind().to_string(),
        payload,
        resource: Default::default(),
    })
}

// ============================================================================
// V2-9 Phase 2 — Sovereign Council propose / sign / list / get
// ============================================================================

use hub_lib::proposal::{CouncilProposal, ProposalStatus};

#[derive(Deserialize)]
#[serde(tag = "action", rename_all = "snake_case")]
enum CouncilAction {
    CouncilPropose { proposed_event: HubEvent },
    CouncilSign { proposal_id: Uuid },
}

#[derive(Serialize)]
struct ProposalSummary {
    id: Uuid,
    event_kind: String,
    proposed_by: Uuid,
    proposed_at: chrono::DateTime<Utc>,
    expires_at: chrono::DateTime<Utc>,
    signatures: usize,
    threshold_m: u32,
    threshold_n: u32,
    status: ProposalStatusTag,
    /// Set when status == "committed".
    #[serde(skip_serializing_if = "Option::is_none")]
    entry_index: Option<u64>,
}

#[derive(Serialize)]
#[serde(rename_all = "snake_case")]
enum ProposalStatusTag {
    Open,
    Committed,
    Rejected,
    Expired,
}

impl From<&ProposalStatus> for ProposalStatusTag {
    fn from(s: &ProposalStatus) -> Self {
        match s {
            ProposalStatus::Open => Self::Open,
            ProposalStatus::Committed { .. } => Self::Committed,
            ProposalStatus::Rejected { .. } => Self::Rejected,
            ProposalStatus::Expired => Self::Expired,
        }
    }
}

fn summarize(p: &CouncilProposal, threshold: (u32, u32)) -> ProposalSummary {
    let entry_index = match &p.status {
        ProposalStatus::Committed { entry_index, .. } => Some(*entry_index),
        _ => None,
    };
    ProposalSummary {
        id: p.id,
        event_kind: p.proposed_event.kind().to_string(),
        proposed_by: p.proposed_by,
        proposed_at: p.proposed_at,
        expires_at: p.expires_at,
        signatures: p.unique_signers().len(),
        threshold_m: threshold.0,
        threshold_n: threshold.1,
        status: (&p.status).into(),
        entry_index,
    }
}

/// Project the current set of valid council holders (founding Sovereign
/// included) + the threshold from the ledger. Used by both propose
/// and sign to know who counts as a vote.
fn project_council(
    s: &RestState,
    ledger: &hub_lib::ledger::HubLedger,
) -> (std::collections::BTreeSet<Uuid>, (u32, u32)) {
    let projected = hub_lib::state::HubState::project(ledger);
    let mut holders = projected.council_holders.clone();
    holders.insert(s.sovereign_lct_id);
    // Default threshold when none set: 1-of-1 (current behavior). The
    // propose flow still works without an explicit threshold — it just
    // commits on first signature, which mirrors single-Sovereign mode
    // but produces a council audit trail.
    let threshold = projected.council_threshold
        .unwrap_or((1, holders.len() as u32));
    (holders, threshold)
}

async fn submit_proposal(
    State(s): State<RestState>,
    Path(hub_id): Path<Uuid>,
    Json(envelope): Json<SignedEnvelope>,
) -> Result<Json<ProposalSummary>, ApiError> {
    if hub_id != s.hub_id {
        return Err(ApiError::not_found(format!(
            "hub id {} does not match this hub {}", hub_id, s.hub_id
        )));
    }

    // 1. Envelope verifies (signature + nonce + signer known).
    let resolver_guard = s.resolver.read().await;
    let _redeemed = verify_envelope(&envelope, &s.nonces, &*resolver_guard, Utc::now())?;
    drop(resolver_guard);

    // 2. Parse + validate action shape.
    let action: CouncilAction = serde_json::from_value(envelope.payload.clone())
        .map_err(|e| ApiError::bad_request(format!("payload not a council action: {}", e)))?;
    let proposed_event = match action {
        CouncilAction::CouncilPropose { proposed_event } => proposed_event,
        CouncilAction::CouncilSign { .. } => {
            return Err(ApiError::bad_request(
                String::from("this endpoint expects action=council_propose; use /council/sign for council_sign")
            ));
        }
    };

    // 3. Authorization: signer must be a current council holder (or
    // founding Sovereign). Members can't propose chapter acts.
    let (holders, threshold) = {
        let ledger = s.ledger.lock().await;
        project_council(&s, &*ledger)
    };
    if !holders.contains(&envelope.signer_lct_id) {
        return Err(ApiError::unauthorized(format!(
            "signer {} is not a Sovereign Council holder", envelope.signer_lct_id
        )));
    }

    // 4. Create proposal + record proposer's vote. Cleanup any expired
    // proposals while we're touching the store, so they don't pile up.
    let now = Utc::now();
    let mut proposal = CouncilProposal::new(proposed_event, envelope.signer_lct_id, now);
    proposal.add_vote(envelope, now);

    // If proposer alone meets threshold (1-of-1 case or 1-of-N with
    // M=1), commit immediately so this works as a strict superset of
    // the existing /events flow.
    if proposal.meets_threshold(threshold.0, &holders) {
        let entry_index = commit_proposed_event(&s, &proposal.proposed_event, Some(proposal.id)).await?;
        proposal.status = ProposalStatus::Committed { entry_index, committed_at: now };
    }

    persist_proposal(&s, &proposal).await?;
    cleanup_expired_proposals(&s, now).await;

    Ok(Json(summarize(&proposal, threshold)))
}

async fn sign_proposal(
    State(s): State<RestState>,
    Path(hub_id): Path<Uuid>,
    Json(envelope): Json<SignedEnvelope>,
) -> Result<Json<ProposalSummary>, ApiError> {
    if hub_id != s.hub_id {
        return Err(ApiError::not_found(format!(
            "hub id {} does not match this hub {}", hub_id, s.hub_id
        )));
    }

    let resolver_guard = s.resolver.read().await;
    let _redeemed = verify_envelope(&envelope, &s.nonces, &*resolver_guard, Utc::now())?;
    drop(resolver_guard);

    let action: CouncilAction = serde_json::from_value(envelope.payload.clone())
        .map_err(|e| ApiError::bad_request(format!("payload not a council action: {}", e)))?;
    let proposal_id = match action {
        CouncilAction::CouncilSign { proposal_id } => proposal_id,
        CouncilAction::CouncilPropose { .. } => {
            return Err(ApiError::bad_request(
                String::from("this endpoint expects action=council_sign; use /council/propose for council_propose")
            ));
        }
    };

    let (holders, threshold) = {
        let ledger = s.ledger.lock().await;
        project_council(&s, &*ledger)
    };
    if !holders.contains(&envelope.signer_lct_id) {
        return Err(ApiError::unauthorized(format!(
            "signer {} is not a Sovereign Council holder", envelope.signer_lct_id
        )));
    }

    let mut proposal = read_proposal(&s, proposal_id).await?
        .ok_or_else(|| ApiError::not_found(format!("proposal {} not found", proposal_id)))?;

    if !proposal.is_open() {
        return Err(ApiError {
            status: StatusCode::CONFLICT,
            message: format!("proposal {} is not open (status: {:?})", proposal_id, proposal.status),
        });
    }
    let now = Utc::now();
    if proposal.is_expired_at(now) {
        proposal.status = ProposalStatus::Expired;
        persist_proposal(&s, &proposal).await?;
        return Err(ApiError {
            status: StatusCode::CONFLICT,
            message: format!("proposal {} expired at {}", proposal_id, proposal.expires_at),
        });
    }

    proposal.add_vote(envelope, now);

    if proposal.meets_threshold(threshold.0, &holders) {
        let entry_index = commit_proposed_event(&s, &proposal.proposed_event, Some(proposal.id)).await?;
        proposal.status = ProposalStatus::Committed { entry_index, committed_at: now };
    }

    persist_proposal(&s, &proposal).await?;
    Ok(Json(summarize(&proposal, threshold)))
}

async fn list_proposals(
    State(s): State<RestState>,
    Path(hub_id): Path<Uuid>,
) -> Result<Json<Vec<ProposalSummary>>, ApiError> {
    if hub_id != s.hub_id {
        return Err(ApiError::not_found(format!(
            "hub id {} does not match this hub {}", hub_id, s.hub_id
        )));
    }
    let (_holders, threshold) = {
        let ledger = s.ledger.lock().await;
        project_council(&s, &*ledger)
    };
    let proposals = read_all_proposals(&s).await?;
    Ok(Json(proposals.iter().map(|p| summarize(p, threshold)).collect()))
}

async fn get_proposal(
    State(s): State<RestState>,
    Path((hub_id, proposal_id)): Path<(Uuid, Uuid)>,
) -> Result<Json<CouncilProposal>, ApiError> {
    if hub_id != s.hub_id {
        return Err(ApiError::not_found(format!(
            "hub id {} does not match this hub {}", hub_id, s.hub_id
        )));
    }
    let proposal = read_proposal(&s, proposal_id).await?
        .ok_or_else(|| ApiError::not_found(format!("proposal {} not found", proposal_id)))?;
    Ok(Json(proposal))
}

// ---------- council helpers ----------
//
// Direct async calls now that HubStore is async-trait. No spawn_blocking
// needed — file/sqlite store methods complete synchronously inside their
// async fn bodies; future network backends (DynamoDB, Postgres) do real
// awaits here.

async fn persist_proposal(s: &RestState, proposal: &CouncilProposal) -> Result<(), ApiError> {
    let mut store = s.open_store().await
        .map_err(ApiError::internal)?;
    store.write_proposal(proposal).await
        .map_err(ApiError::internal)
}

async fn read_proposal(s: &RestState, id: Uuid) -> Result<Option<CouncilProposal>, ApiError> {
    let store = s.open_store().await
        .map_err(ApiError::internal)?;
    store.read_proposal(id).await
        .map_err(ApiError::internal)
}

async fn read_all_proposals(s: &RestState) -> Result<Vec<CouncilProposal>, ApiError> {
    let store = s.open_store().await
        .map_err(ApiError::internal)?;
    store.list_proposals().await
        .map_err(ApiError::internal)
}

async fn cleanup_expired_proposals(s: &RestState, now: chrono::DateTime<Utc>) {
    // Best-effort: mark expired proposals so listings reflect reality.
    // We don't delete — keeping them as audit trail of attempted-but-
    // never-committed acts. Deletion is a separate operator action.
    let Ok(all) = read_all_proposals(s).await else { return };
    for mut p in all {
        if p.is_open() && p.is_expired_at(now) {
            p.status = ProposalStatus::Expired;
            let _ = persist_proposal(s, &p).await;
        }
    }
}

/// Commit a proposed event to the ledger via the hub's signer (founding
/// Sovereign). The ledger entry's `actor_lct_id` is the founding
/// Sovereign — they're the executor of the council's decision. The
/// authorization audit trail (M holder signatures) lives in the
/// proposal record, linked bidirectionally:
/// - proposal → ledger: `ProposalStatus::Committed { entry_index }`
/// - ledger → proposal: `LedgerEntry.proposal_ref = Some(proposal_id)`
/// The ledger-side reference is part of `signing_payload`, so an
/// attacker can't forge a `proposal_ref` onto an existing entry
/// without invalidating the founding Sovereign's signature.
async fn commit_proposed_event(
    s: &RestState,
    event: &HubEvent,
    proposal_ref: Option<Uuid>,
) -> Result<u64, ApiError> {
    let event_kind_str = event.kind().to_string();
    let event_value = serde_json::to_value(event)
        .map_err(|e| ApiError::internal(anyhow::anyhow!("serializing event: {}", e)))?;
    let (unsigned, intent) = {
        let ledger = s.ledger.lock().await;
        let unsigned = ledger.build_entry_with_proposal_ref(
            s.sovereign_lct_id, event.clone(), Utc::now(), proposal_ref,
        ).map_err(ApiError::internal)?;
        let intent = SignIntent {
            request_id: Uuid::new_v4(),
            hub_id: s.hub_id,
            hub_name: s.hub_name.clone(),
            actor_lct_id: s.sovereign_lct_id,
            ledger_index: unsigned.entry.index,
            event_kind: event_kind_str,
            event: event_value,
        };
        (unsigned, intent)
    };
    let signing_bytes = unsigned.signing_bytes.clone();
    let signature = s.signer
        .sign(s.sovereign_lct_id, &signing_bytes, &intent)
        .await
        .map_err(|e| match e {
            hub_lib::signer::SignError::Denied(reason) => ApiError::unauthorized(
                format!("Sovereign signer denied: {}", reason)
            ),
            hub_lib::signer::SignError::Transport(msg) => ApiError {
                status: StatusCode::SERVICE_UNAVAILABLE,
                message: format!("Sovereign signer unreachable: {}", msg),
            },
            hub_lib::signer::SignError::Malformed(msg) => ApiError::internal(
                anyhow::anyhow!("malformed signer response: {}", msg)
            ),
            hub_lib::signer::SignError::Internal(err) => ApiError::internal(err),
        })?;
    let mut ledger = s.ledger.lock().await;
    let (entry_index, needs_resolver_refresh) = {
        let entry = ledger.append_signed(unsigned, signature).await
            .map_err(ApiError::internal)?;
        let needs = matches!(
            &entry.event,
            HubEvent::CouncilMemberAdded { .. }
                | HubEvent::MemberAdded { .. }
                | HubEvent::MemberKeyPinned { .. } // live re-key: insert replaces by lct id
        );
        (entry.index, needs)
    };
    // If the committed act was a council membership / member-add,
    // refresh the resolver so the new pubkey can verify envelopes
    // immediately (same pattern as submit_join's live insert).
    if needs_resolver_refresh {
        let projected = hub_lib::state::HubState::project(&*ledger);
        let mut resolver = s.resolver.write().await;
        for (lct_id, pk) in projected.member_pubkeys.iter()
            .chain(projected.council_pubkeys.iter())
        {
            if let Ok(lct) = hub_lib::hub::hestia_sovereign_lct(*lct_id, pk) {
                resolver.insert(lct);
            }
        }
    }
    Ok(entry_index)
}

// ============================================================================
// PAIRED-CHANNELS Sprint C — pair lifecycle endpoints
// ============================================================================
//
// Three POST endpoints (request / confirm / revoke) and two GETs
// (list / detail). Reads are public-by-default; hub law gates
// later. Writes are signed envelopes — same machinery as /v1/hubs/.../events.
//
// The hub never sees the ECDH shared secret — that's derived at the
// endpoints from their LCT keys (Sprint A). The hub only witnesses
// the lifecycle and (eventually, Sprint D) relays opaque ciphertext.

use hub_lib::state::{PairState, PairStatus};
use hub_lib::events::PairRevocationKind;

#[derive(Deserialize)]
struct PairRequestPayload {
    /// Discriminator inside the envelope payload (same shape as
    /// other action types). Required to be "pair_request".
    action: String,
    counterparty_lct_id: Uuid,
    purpose: String,
    #[serde(default)]
    expires_at: Option<chrono::DateTime<Utc>>,
    /// PAIRED-CHANNELS Sprint F: initiator's per-session X25519
    /// ephemeral public key (hex). If supplied AND the counterparty
    /// supplies theirs in pair_confirm, this pair's messages get
    /// forward secrecy.
    #[serde(default)]
    initiator_ephemeral_pub_hex: Option<String>,
}

#[derive(Deserialize)]
struct PairConfirmPayload {
    action: String, // "pair_confirm"
    pair_id: Uuid,
    /// PAIRED-CHANNELS Sprint F: counterparty's per-session X25519
    /// ephemeral public key (hex). Optional for back-compat.
    #[serde(default)]
    counterparty_ephemeral_pub_hex: Option<String>,
}

#[derive(Deserialize)]
struct PairRevokePayload {
    action: String, // "pair_revoke"
    pair_id: Uuid,
    #[serde(default = "default_revocation_kind")]
    revocation_kind: PairRevocationKind,
    #[serde(default)]
    reason: Option<String>,
}

fn default_revocation_kind() -> PairRevocationKind {
    PairRevocationKind::Voluntary
}

#[derive(Serialize)]
struct PairAccepted {
    pair_id: Uuid,
    entry_index: u64,
    entry_hash: String,
    status: PairStatus,
}

#[derive(Serialize)]
struct PairSummary {
    id: Uuid,
    initiator: Uuid,
    counterparty: Uuid,
    purpose: String,
    status: PairStatus,
    effective_status: &'static str,
    proposed_at: chrono::DateTime<Utc>,
    #[serde(skip_serializing_if = "Option::is_none")]
    confirmed_at: Option<chrono::DateTime<Utc>>,
    #[serde(skip_serializing_if = "Option::is_none")]
    revoked_at: Option<chrono::DateTime<Utc>>,
    #[serde(skip_serializing_if = "Option::is_none")]
    expires_at: Option<chrono::DateTime<Utc>>,
    message_count: u64,
    /// PAIRED-CHANNELS Sprint F: ephemeral public keys. Recipient
    /// reads counterparty_ephemeral_pub_hex from initiator's side
    /// and vice versa; both are needed to derive the v2 session key.
    #[serde(skip_serializing_if = "Option::is_none")]
    initiator_ephemeral_pub_hex: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    counterparty_ephemeral_pub_hex: Option<String>,
}

impl PairSummary {
    fn from_pair(p: &PairState, now: chrono::DateTime<Utc>) -> Self {
        Self {
            id: p.id,
            initiator: p.initiator,
            counterparty: p.counterparty,
            purpose: p.purpose.clone(),
            status: p.status,
            effective_status: p.effective_status(now),
            proposed_at: p.proposed_at,
            confirmed_at: p.confirmed_at,
            revoked_at: p.revoked_at,
            expires_at: p.expires_at,
            message_count: p.message_count,
            initiator_ephemeral_pub_hex: p.initiator_ephemeral_pub_hex.clone(),
            counterparty_ephemeral_pub_hex: p.counterparty_ephemeral_pub_hex.clone(),
        }
    }
}

/// Shared preamble for the three POST handlers: verify envelope,
/// reject if signer isn't a current member or the founding Sovereign,
/// reject if council mode active (consistency with /events behavior).
/// Returns the projected HubState (caller often needs it next).
async fn pair_endpoint_preamble(
    s: &RestState,
    envelope: &SignedEnvelope,
) -> Result<hub_lib::state::HubState, ApiError> {
    let resolver_guard = s.resolver.read().await;
    let _redeemed = verify_envelope(envelope, &s.nonces, &*resolver_guard, Utc::now())?;
    drop(resolver_guard);

    let projected = {
        let ledger = s.ledger.lock().await;
        hub_lib::state::HubState::project(&*ledger)
    };

    let is_sov = envelope.signer_lct_id == s.sovereign_lct_id;
    let is_member = projected.members.contains_key(&envelope.signer_lct_id);
    if !is_sov && !is_member {
        return Err(ApiError::unauthorized(format!(
            "signer {} is neither the founding Sovereign nor a current member",
            envelope.signer_lct_id
        )));
    }

    // Same council gate as /events for consistency. In council mode,
    // pair acts go through the propose/sign flow like everything else.
    if matches!(projected.council_threshold, Some((m, _)) if m >= 2) {
        return Err(ApiError {
            status: StatusCode::CONFLICT,
            message: "council mode active (threshold >= 2-of-N): submit pair acts via \
                      POST /v1/hubs/{hub_id}/council/propose + /sign".into(),
        });
    }

    Ok(projected)
}

async fn submit_pair_request(
    State(s): State<RestState>,
    Path(hub_id): Path<Uuid>,
    Json(envelope): Json<SignedEnvelope>,
) -> Result<Json<PairAccepted>, ApiError> {
    if hub_id != s.hub_id {
        return Err(ApiError::not_found(format!(
            "hub id {} does not match this hub {}", hub_id, s.hub_id
        )));
    }
    let projected = pair_endpoint_preamble(&s, &envelope).await?;

    let payload: PairRequestPayload = serde_json::from_value(envelope.payload.clone())
        .map_err(|e| ApiError::bad_request(format!("payload not a pair_request: {}", e)))?;
    if payload.action != "pair_request" {
        return Err(ApiError::bad_request(format!(
            "expected action=pair_request, got {}", payload.action
        )));
    }

    // Counterparty must be a current member (or the Sovereign) — we
    // can't pair with someone we don't know how to deliver to.
    let cp_known = payload.counterparty_lct_id == s.sovereign_lct_id
        || projected.members.contains_key(&payload.counterparty_lct_id);
    if !cp_known {
        return Err(ApiError::bad_request(format!(
            "counterparty {} is not a current member; only known LCTs can be paired with",
            payload.counterparty_lct_id
        )));
    }
    // Self-pairs are pointless.
    if payload.counterparty_lct_id == envelope.signer_lct_id {
        return Err(ApiError::bad_request(
            String::from("self-pair (initiator == counterparty) is not allowed")
        ));
    }
    // Idempotency / no-duplicate: refuse if a Pending or Active pair between
    // these two LCTs already exists (either direction). Without this, repeated
    // pair_requests pile up parallel live pairs for the same relationship.
    let dup = projected.pairs.values().any(|p| {
        matches!(p.status, PairStatus::Pending | PairStatus::Active)
            && p.includes(envelope.signer_lct_id)
            && p.includes(payload.counterparty_lct_id)
    });
    if dup {
        return Err(ApiError {
            status: StatusCode::CONFLICT,
            message: format!(
                "a pending or active pair with {} already exists",
                payload.counterparty_lct_id
            ),
        });
    }

    let pair_id = Uuid::new_v4();
    let event = HubEvent::PairingRequested {
        pair_id,
        initiator_lct_id: envelope.signer_lct_id,
        counterparty_lct_id: payload.counterparty_lct_id,
        purpose: payload.purpose,
        proposed_at: Utc::now(),
        expires_at: payload.expires_at,
        initiator_ephemeral_pub_hex: payload.initiator_ephemeral_pub_hex,
    };

    // PolicyEntity gate (V2-8 §4): hub law can pattern-match
    // `r6.request.action == "pairing_requested"` and gate by purpose,
    // counterparty role, initiator role, etc.
    let law_guard = s.law.read().await;
    if let Some(law) = law_guard.as_ref() {
        let req = build_r6_request(&envelope, &event, s.sovereign_lct_id)
            .map_err(ApiError::internal)?;
        match law.evaluate_outcome(&req).decision {
            Decision::Allow => {}
            Decision::Warn => {
                // Non-blocking flagged-allow: the pairing proceeds, flagged.
                tracing::warn!("pair_request flagged by hub law (proceeding)");
            }
            Decision::Deny => {
                return Err(ApiError {
                    status: StatusCode::FORBIDDEN,
                    message: "pair_request denied by hub law".into(),
                });
            }
            Decision::Escalate => {
                return Err(ApiError {
                    status: StatusCode::ACCEPTED,
                    message: "pair_request escalated to council; use propose/sign".into(),
                });
            }
        }
    }
    drop(law_guard);

    let (entry_index, entry_hash) = commit_pair_event(&s, event).await?;
    Ok(Json(PairAccepted {
        pair_id,
        entry_index,
        entry_hash,
        status: PairStatus::Pending,
    }))
}

async fn submit_pair_confirm(
    State(s): State<RestState>,
    Path((hub_id, pair_id)): Path<(Uuid, Uuid)>,
    Json(envelope): Json<SignedEnvelope>,
) -> Result<Json<PairAccepted>, ApiError> {
    if hub_id != s.hub_id {
        return Err(ApiError::not_found(format!(
            "hub id {} does not match this hub {}", hub_id, s.hub_id
        )));
    }
    let projected = pair_endpoint_preamble(&s, &envelope).await?;

    let payload: PairConfirmPayload = serde_json::from_value(envelope.payload.clone())
        .map_err(|e| ApiError::bad_request(format!("payload not a pair_confirm: {}", e)))?;
    if payload.action != "pair_confirm" || payload.pair_id != pair_id {
        return Err(ApiError::bad_request(
            String::from("pair_id in path must match payload + action must be pair_confirm")
        ));
    }

    let pair = projected.pairs.get(&pair_id)
        .ok_or_else(|| ApiError::not_found(format!("pair {} not found", pair_id)))?;
    if pair.status != PairStatus::Pending {
        return Err(ApiError {
            status: StatusCode::CONFLICT,
            message: format!("pair {} is {:?}, not Pending; cannot confirm", pair_id, pair.status),
        });
    }
    // Only the counterparty can confirm.
    if envelope.signer_lct_id != pair.counterparty {
        return Err(ApiError::unauthorized(format!(
            "only the counterparty ({}) may confirm pair {}; got {}",
            pair.counterparty, pair_id, envelope.signer_lct_id
        )));
    }

    let event = HubEvent::PairingConfirmed {
        pair_id,
        confirmed_by: envelope.signer_lct_id,
        counterparty_ephemeral_pub_hex: payload.counterparty_ephemeral_pub_hex,
    };
    let (entry_index, entry_hash) = commit_pair_event(&s, event).await?;
    Ok(Json(PairAccepted {
        pair_id,
        entry_index,
        entry_hash,
        status: PairStatus::Active,
    }))
}

async fn submit_pair_revoke(
    State(s): State<RestState>,
    Path((hub_id, pair_id)): Path<(Uuid, Uuid)>,
    Json(envelope): Json<SignedEnvelope>,
) -> Result<Json<PairAccepted>, ApiError> {
    if hub_id != s.hub_id {
        return Err(ApiError::not_found(format!(
            "hub id {} does not match this hub {}", hub_id, s.hub_id
        )));
    }
    let projected = pair_endpoint_preamble(&s, &envelope).await?;

    let payload: PairRevokePayload = serde_json::from_value(envelope.payload.clone())
        .map_err(|e| ApiError::bad_request(format!("payload not a pair_revoke: {}", e)))?;
    if payload.action != "pair_revoke" || payload.pair_id != pair_id {
        return Err(ApiError::bad_request(
            String::from("pair_id in path must match payload + action must be pair_revoke")
        ));
    }

    let pair = projected.pairs.get(&pair_id)
        .ok_or_else(|| ApiError::not_found(format!("pair {} not found", pair_id)))?;
    if pair.status == PairStatus::Revoked {
        return Err(ApiError {
            status: StatusCode::CONFLICT,
            message: format!("pair {} already revoked", pair_id),
        });
    }
    // Either party (or the founding Sovereign, as operator override)
    // can revoke. Hub law could further restrict; today no law
    // norms target pairing_revoked yet.
    let is_party = envelope.signer_lct_id == pair.initiator
        || envelope.signer_lct_id == pair.counterparty;
    let is_sov = envelope.signer_lct_id == s.sovereign_lct_id;
    if !is_party && !is_sov {
        return Err(ApiError::unauthorized(format!(
            "signer {} is neither a party to pair {} nor the founding Sovereign",
            envelope.signer_lct_id, pair_id
        )));
    }

    let event = HubEvent::PairingRevoked {
        pair_id,
        revoked_by: envelope.signer_lct_id,
        revocation_kind: payload.revocation_kind,
        reason: payload.reason,
    };
    let (entry_index, entry_hash) = commit_pair_event(&s, event).await?;
    Ok(Json(PairAccepted {
        pair_id,
        entry_index,
        entry_hash,
        status: PairStatus::Revoked,
    }))
}

async fn list_pairs(
    State(s): State<RestState>,
    Path(hub_id): Path<Uuid>,
    axum::extract::Query(q): axum::extract::Query<ListPairsQuery>,
) -> Result<Json<Vec<PairSummary>>, ApiError> {
    if hub_id != s.hub_id {
        return Err(ApiError::not_found(format!(
            "hub id {} does not match this hub {}", hub_id, s.hub_id
        )));
    }
    let projected = {
        let ledger = s.ledger.lock().await;
        hub_lib::state::HubState::project(&*ledger)
    };
    let now = Utc::now();
    let mut pairs: Vec<_> = projected.pairs.values()
        .filter(|p| match q.r#for {
            Some(lct) => p.includes(lct),
            None => true,
        })
        .map(|p| PairSummary::from_pair(p, now))
        .collect();
    // Newest-first by proposed_at for stable, useful ordering.
    pairs.sort_by(|a, b| b.proposed_at.cmp(&a.proposed_at));
    Ok(Json(pairs))
}

#[derive(Deserialize)]
struct ListPairsQuery {
    #[serde(default)]
    r#for: Option<Uuid>,
}

async fn get_pair(
    State(s): State<RestState>,
    Path((hub_id, pair_id)): Path<(Uuid, Uuid)>,
) -> Result<Json<PairSummary>, ApiError> {
    if hub_id != s.hub_id {
        return Err(ApiError::not_found(format!(
            "hub id {} does not match this hub {}", hub_id, s.hub_id
        )));
    }
    let projected = {
        let ledger = s.ledger.lock().await;
        hub_lib::state::HubState::project(&*ledger)
    };
    let pair = projected.pairs.get(&pair_id)
        .ok_or_else(|| ApiError::not_found(format!("pair {} not found", pair_id)))?;
    Ok(Json(PairSummary::from_pair(pair, Utc::now())))
}

// ---------- PAIRED-CHANNELS Sprint D: message relay ----------

use hub_lib::pair_message::PairMessage;

#[derive(Deserialize)]
struct PairMessagePayload {
    action: String, // "pair_message"
    pair_id: Uuid,
    /// Sprint D: plaintext. Sprint E: base64-encoded ciphertext.
    /// Wire shape unchanged.
    body: String,
}

#[derive(Serialize)]
struct PairMessageAccepted {
    pair_id: Uuid,
    seq: u64,
    entry_index: u64,
    entry_hash: String,
    payload_hash: String,
}

async fn post_pair_message(
    State(s): State<RestState>,
    Path((hub_id, pair_id)): Path<(Uuid, Uuid)>,
    Json(envelope): Json<SignedEnvelope>,
) -> Result<Json<PairMessageAccepted>, ApiError> {
    if hub_id != s.hub_id {
        return Err(ApiError::not_found(format!(
            "hub id {} does not match this hub {}", hub_id, s.hub_id
        )));
    }
    // Envelope verify + member check + council gate via the same preamble
    // pair_request / confirm / revoke use.
    let projected = pair_endpoint_preamble(&s, &envelope).await?;

    let payload: PairMessagePayload = serde_json::from_value(envelope.payload.clone())
        .map_err(|e| ApiError::bad_request(format!("payload not a pair_message: {}", e)))?;
    if payload.action != "pair_message" || payload.pair_id != pair_id {
        return Err(ApiError::bad_request(
            String::from("pair_id in path must match payload + action must be pair_message")
        ));
    }

    let pair = projected.pairs.get(&pair_id)
        .ok_or_else(|| ApiError::not_found(format!("pair {} not found", pair_id)))?;
    // Must be Active to relay (use effective_status so expired pairs
    // are rejected even though stored status is Active).
    let eff = pair.effective_status(Utc::now());
    if eff != "active" {
        return Err(ApiError {
            status: StatusCode::CONFLICT,
            message: format!("pair {} is {}; messages can only be relayed on active pairs",
                pair_id, eff),
        });
    }
    // Signer must be one of the two parties — no third-party injection.
    let is_party = envelope.signer_lct_id == pair.initiator
        || envelope.signer_lct_id == pair.counterparty;
    if !is_party {
        return Err(ApiError::unauthorized(format!(
            "signer {} is not a party to pair {}", envelope.signer_lct_id, pair_id
        )));
    }

    // Compute seq: the pair's current message_count IS the next seq
    // (0-indexed). Hub holds the ledger lock during the
    // build_entry → commit window, so concurrent posts to the same
    // pair serialize naturally — the append_signed stale-detection
    // would catch any race anyway.
    let seq = pair.message_count;
    let now = Utc::now();
    let payload_hash = PairMessage::payload_hash(&payload.body);

    // 1. Append the message to the sidecar BEFORE the ledger event.
    //    If sidecar write fails, no ledger event → no message_count
    //    bump → consistent. If ledger commit fails after sidecar
    //    write, we have an orphan sidecar entry (recoverable: next
    //    post with the same seq will fail the conditional/append
    //    detection). Acceptable for MVP; Sprint E will add atomicity
    //    if needed via a HubStore::tx_pair_message helper.
    let msg = PairMessage {
        pair_id,
        seq,
        from: envelope.signer_lct_id,
        posted_at: now,
        payload: payload.body,
        ephemeral_pub_hex: None,
    };
    {
        let mut store = s.open_store().await
            .map_err(ApiError::internal)?;
        store.append_pair_message(&msg).await
            .map_err(ApiError::internal)?;
    }

    // 2. Commit the ledger event so the projection bumps
    //    message_count + the witness chain records the metadata.
    let event = HubEvent::PairMessagePosted {
        pair_id,
        seq,
        from: envelope.signer_lct_id,
        posted_at: now,
        payload_hash: payload_hash.clone(),
    };
    let (entry_index, entry_hash) = commit_pair_event(&s, event).await?;

    Ok(Json(PairMessageAccepted {
        pair_id,
        seq,
        entry_index,
        entry_hash,
        payload_hash,
    }))
}

#[derive(Deserialize)]
struct PairMessagesQuery {
    /// Return only messages with seq strictly greater than this.
    /// Polling clients pass the last seq they saw.
    #[serde(default)]
    since: Option<u64>,
}

#[derive(Serialize)]
struct PairMessagesResponse {
    pair_id: Uuid,
    count: usize,
    messages: Vec<PairMessage>,
}

async fn get_pair_messages(
    State(s): State<RestState>,
    Path((hub_id, pair_id)): Path<(Uuid, Uuid)>,
    axum::extract::Query(q): axum::extract::Query<PairMessagesQuery>,
) -> Result<Json<PairMessagesResponse>, ApiError> {
    if hub_id != s.hub_id {
        return Err(ApiError::not_found(format!(
            "hub id {} does not match this hub {}", hub_id, s.hub_id
        )));
    }
    // Pair must exist (don't leak which pair_ids exist via empty 200).
    {
        let ledger = s.ledger.lock().await;
        let projected = hub_lib::state::HubState::project(&*ledger);
        if !projected.pairs.contains_key(&pair_id) {
            return Err(ApiError::not_found(format!("pair {} not found", pair_id)));
        }
    }
    let store = s.open_store().await
        .map_err(ApiError::internal)?;
    let messages = store.list_pair_messages(pair_id, q.since).await
        .map_err(ApiError::internal)?;
    Ok(Json(PairMessagesResponse {
        pair_id,
        count: messages.len(),
        messages,
    }))
}

/// Commit a pair lifecycle event via the hub's signer (founding
/// Sovereign as executor). Same shape as `commit_proposed_event` —
/// hub signs the ledger entry; the pair's authorization is in the
/// envelope (verified above) + the event's fields (initiator_lct_id,
/// confirmed_by, revoked_by). Auditors correlate.
async fn commit_pair_event(s: &RestState, event: HubEvent) -> Result<(u64, String), ApiError> {
    let event_kind_str = event.kind().to_string();
    let event_value = serde_json::to_value(&event)
        .map_err(|e| ApiError::internal(anyhow::anyhow!("serializing event: {}", e)))?;
    let (unsigned, intent) = {
        let ledger = s.ledger.lock().await;
        let unsigned = ledger.build_entry(s.sovereign_lct_id, event.clone(), Utc::now())
            .map_err(ApiError::internal)?;
        let intent = SignIntent {
            request_id: Uuid::new_v4(),
            hub_id: s.hub_id,
            hub_name: s.hub_name.clone(),
            actor_lct_id: s.sovereign_lct_id,
            ledger_index: unsigned.entry.index,
            event_kind: event_kind_str,
            event: event_value,
        };
        (unsigned, intent)
    };
    let signing_bytes = unsigned.signing_bytes.clone();
    let signature = s.signer
        .sign(s.sovereign_lct_id, &signing_bytes, &intent)
        .await
        .map_err(|e| ApiError::internal(anyhow::anyhow!("Sovereign signer denied/failed: {}", e)))?;
    let mut ledger = s.ledger.lock().await;
    let entry = ledger.append_signed(unsigned, signature).await
        .map_err(ApiError::internal)?;
    Ok((entry.index, entry.entry_hash.clone()))
}

#[cfg(test)]
mod read_gate_tests {
    use super::*;
    use hub_lib::law::Law;

    #[test]
    fn read_defaults_open_without_law() {
        // No hub law → reads are open (pre-gate behavior preserved).
        assert_eq!(read_decision(None, "citizen", "list_members").decision, Decision::Allow);
        assert_eq!(read_decision(None, "sovereign", "find_skill").decision, Decision::Allow);
    }

    #[test]
    fn read_honors_a_deny_norm_and_leaves_others_open() {
        let yaml = r#"
version: "1.0.0"
norms:
  - id: NO-MEMBER-DUMP
    selector: r6.request.action
    operator: "=="
    value: "read:list_members"
    decision: deny
    priority: 10
    description: "Members are not bulk-listable over the channel"
"#;
        let law = Law::parse_and_validate(yaml).expect("valid law");
        // The denied read is denied for a citizen...
        let denied = read_decision(Some(&law), "citizen", "list_members");
        assert_eq!(denied.decision, Decision::Deny);
        assert_eq!(denied.winning_norm.as_deref(), Some("NO-MEMBER-DUMP"));
        // ...while an unlisted read stays open (default-allow).
        assert_eq!(read_decision(Some(&law), "citizen", "find_skill").decision, Decision::Allow);
    }

    #[test]
    fn read_can_escalate() {
        let yaml = r#"
version: "1.0.0"
norms:
  - id: SENSITIVE-QUERY
    selector: r6.request.action
    operator: "=="
    value: "read:query_hub"
    decision: escalate
    priority: 5
    description: "Hub-identity queries need Sovereign sign-off"
"#;
        let law = Law::parse_and_validate(yaml).expect("valid law");
        assert_eq!(read_decision(Some(&law), "citizen", "query_hub").decision, Decision::Escalate);
    }

    #[test]
    fn scope_bounds_citizens_and_not_the_sovereign() {
        let citizen = ReadScope::for_role("citizen");
        let sovereign = ReadScope::for_role("sovereign");
        // Citizen is capped; Sovereign is unbounded.
        assert_eq!(citizen.effective_limit(None), Some(CITIZEN_READ_LIMIT));
        assert_eq!(sovereign.effective_limit(None), None);
        // A citizen's requested limit is honored only up to the cap.
        assert_eq!(citizen.effective_limit(Some(5)), Some(5));
        assert_eq!(citizen.effective_limit(Some(10_000)), Some(CITIZEN_READ_LIMIT));
        // The Sovereign's requested limit is honored as-is.
        assert_eq!(sovereign.effective_limit(Some(5)), Some(5));
    }
}

/// End-to-end channel harness: a real RestState over a throwaway chapter, with
/// requests sealed by an external applicant via the same pair_channel primitive
/// the member side (hestia) uses. Exercises the full path — channel_open (authn)
/// → tier resolution → PolicyEntity → dispatch → seal response — that the unit
/// tests can't reach. The first RestState integration harness in this crate.
#[cfg(test)]
mod channel_e2e_tests {
    use super::*;
    use axum::extract::{Json, Path, State};
    use hub_lib::identity::IdentityFile;
    use hub_lib::init::{init_hub, InitArgs};
    use hub_lib::ledger::HubLedger;
    use hub_lib::store::open_hub_store;
    use tokio::sync::RwLock;
    use web4_core::crypto::{KeyPair, PublicKey};
    use web4_core::lct::EntityType;
    use web4_core::pair_channel::{self, Sealed};

    /// A throwaway Local-mode chapter + a RestState over it, optional law loaded.
    async fn fresh_rest_state(law_yaml: Option<&str>) -> (tempfile::TempDir, RestState) {
        let tmp = tempfile::tempdir().unwrap();
        let sov = tmp.path().join("sovereign.json");
        IdentityFile::generate(EntityType::Human).save(&sov).unwrap();
        let hub_dir = tmp.path().join("chapter");
        init_hub(InitArgs {
            hub_name: "E2E Test Hub".into(),
            hub_dir: hub_dir.clone(),
            sovereign_lct_path: sov,
            storage: None,
        })
        .await
        .unwrap();
        let law = Arc::new(RwLock::new(
            law_yaml.map(|y| Law::parse_and_validate(y).unwrap()),
        ));
        let store = open_hub_store(&hub_dir).unwrap();
        let ledger = Arc::new(Mutex::new(HubLedger::open(store).await.unwrap()));
        let state = RestState::open_with_law_and_ledger(hub_dir, law, ledger)
            .await
            .unwrap();
        (tmp, state)
    }

    fn seal_req(
        applicant: &KeyPair,
        hub_pub: &PublicKey,
        pair_id: Uuid,
        tool: &str,
        args: serde_json::Value,
    ) -> String {
        let inner = serde_json::json!({ "tool": tool, "args": args });
        let pt = serde_json::to_vec(&inner).unwrap();
        pair_channel::seal(applicant, hub_pub, pair_id, &pt)
            .unwrap()
            .to_base64()
    }

    fn open_resp(
        applicant: &KeyPair,
        hub_pub: &PublicKey,
        pair_id: Uuid,
        sealed_b64: &str,
    ) -> serde_json::Value {
        let sealed = Sealed::from_base64(sealed_b64).unwrap();
        let pt = pair_channel::open(applicant, hub_pub, pair_id, &sealed).unwrap();
        serde_json::from_slice(&pt).unwrap()
    }

    #[tokio::test]
    async fn external_bootstrap_then_citizen_read_over_channel() {
        let (_tmp, state) = fresh_rest_state(None).await; // open admission
        let hub_pub = state.signer.public_key().expect("local signer exposes a pubkey");
        let applicant = KeyPair::generate();
        let applicant_lct = Uuid::new_v4();
        let applicant_hex = applicant.verifying_key().to_hex();

        // 1. External tier → request_citizenship over a sealed channel, carrying
        //    a self-vouched pubkey. AEAD open authenticates; admission pins it.
        let pid = Uuid::new_v4();
        let sealed = seal_req(&applicant, &hub_pub, pid, "request_citizenship",
            serde_json::json!({ "name": "E2E Applicant" }));
        let req = ChannelRequest {
            caller_lct_id: applicant_lct,
            pair_id: pid,
            sealed,
            caller_pubkey_hex: Some(applicant_hex),
        };
        let resp = channel_request(State(state.clone()), Path(state.hub_id), Json(req))
            .await
            .expect("admission should succeed");
        let out = open_resp(&applicant, &hub_pub, pid, &resp.0.sealed);
        assert_eq!(out["admitted"], serde_json::json!(true));

        // 2. Now a citizen: a sealed list_members read returns the membership,
        //    and the channel needs NO caller_pubkey_hex (the pubkey is pinned).
        let pid2 = Uuid::new_v4();
        let sealed2 = seal_req(&applicant, &hub_pub, pid2, "list_members", serde_json::json!({}));
        let req2 = ChannelRequest {
            caller_lct_id: applicant_lct,
            pair_id: pid2,
            sealed: sealed2,
            caller_pubkey_hex: None,
        };
        let resp2 = channel_request(State(state.clone()), Path(state.hub_id), Json(req2))
            .await
            .expect("citizen read should succeed");
        let out2 = open_resp(&applicant, &hub_pub, pid2, &resp2.0.sealed);
        let members = out2["members"].as_array().expect("members array");
        assert!(
            members.iter().any(|m| m["lct_id"] == serde_json::json!(applicant_lct)),
            "the admitted applicant should appear in list_members"
        );
    }

    #[tokio::test]
    async fn referenced_act_to_peer_queues_a_mailbox_notice() {
        // The member→member message bus: a referenced_act addressed to a Citizen/
        // Peer is not just witnessed — it queues a sealed notice in the recipient's
        // mailbox, drained via `notifications`. Self-addressed here so a single
        // pinned member proves the full emit → deliver → drain loop.
        let (_tmp, state) = fresh_rest_state(None).await; // open admission pins on join
        let hub_pub = state.signer.public_key().unwrap();
        let member = KeyPair::generate();
        let member_lct = Uuid::new_v4();
        let pid = Uuid::new_v4();
        let sealed = seal_req(&member, &hub_pub, pid, "request_citizenship",
            serde_json::json!({ "name": "Emitter" }));
        channel_request(State(state.clone()), Path(state.hub_id), Json(ChannelRequest {
            caller_lct_id: member_lct, pair_id: pid, sealed,
            caller_pubkey_hex: Some(member.verifying_key().to_hex()),
        })).await.expect("admitted + pinned");

        // Emit a referenced_act addressed to self (Peer).
        let pid2 = Uuid::new_v4();
        let sealed2 = seal_req(&member, &hub_pub, pid2, "referenced_act", serde_json::json!({
            "to": { "to": "peer", "lct_id": member_lct },
            "kind": "handoff",
            "pointer_uri": "pr/423#thread=t1",
        }));
        let resp = channel_request(State(state.clone()), Path(state.hub_id), Json(ChannelRequest {
            caller_lct_id: member_lct, pair_id: pid2, sealed: sealed2, caller_pubkey_hex: None,
        })).await.expect("referenced_act recorded");
        assert_eq!(open_resp(&member, &hub_pub, pid2, &resp.0.sealed)["recorded"], serde_json::json!(true));

        // Drain the mailbox — the notice is there, kind + pointer in the clear.
        let pid3 = Uuid::new_v4();
        let sealed3 = seal_req(&member, &hub_pub, pid3, "notifications", serde_json::json!({}));
        let resp3 = channel_request(State(state.clone()), Path(state.hub_id), Json(ChannelRequest {
            caller_lct_id: member_lct, pair_id: pid3, sealed: sealed3, caller_pubkey_hex: None,
        })).await.expect("drain");
        let out3 = open_resp(&member, &hub_pub, pid3, &resp3.0.sealed);
        assert_eq!(out3["total"], serde_json::json!(1), "exactly one notice queued");
        assert_eq!(out3["notifications"][0]["kind"], serde_json::json!("handoff"));
        assert_eq!(out3["notifications"][0]["pointer_uri"], serde_json::json!("pr/423#thread=t1"));
        assert_eq!(out3["notifications"][0]["from"], serde_json::json!(member_lct),
            "sender LCT rides the envelope in the clear so the recipient can reply");
    }

    #[tokio::test]
    async fn channel_replay_is_rejected_and_does_not_double_witness() {
        // Capture-and-replay: re-POSTing the identical sealed bytes must be
        // rejected, or a write act would be witnessed twice. Uses the back-compat
        // hash path (seal_req sends no nonce/issued_at).
        let (_tmp, state) = fresh_rest_state(None).await;
        let hub_pub = state.signer.public_key().unwrap();
        let member = KeyPair::generate();
        let member_lct = Uuid::new_v4();
        let pid = Uuid::new_v4();
        let sealed = seal_req(&member, &hub_pub, pid, "request_citizenship",
            serde_json::json!({ "name": "Replayer" }));
        channel_request(State(state.clone()), Path(state.hub_id), Json(ChannelRequest {
            caller_lct_id: member_lct, pair_id: pid, sealed,
            caller_pubkey_hex: Some(member.verifying_key().to_hex()),
        })).await.expect("admitted + pinned");

        // Emit a referenced_act to self, then replay the EXACT same bytes.
        let pid2 = Uuid::new_v4();
        let sealed2 = seal_req(&member, &hub_pub, pid2, "referenced_act", serde_json::json!({
            "to": { "to": "peer", "lct_id": member_lct },
            "kind": "handoff",
            "pointer_uri": "pr/999#thread=t1",
        }));
        let mk = || ChannelRequest {
            caller_lct_id: member_lct, pair_id: pid2, sealed: sealed2.clone(), caller_pubkey_hex: None,
        };
        channel_request(State(state.clone()), Path(state.hub_id), Json(mk()))
            .await.expect("first submission recorded");
        let replay = channel_request(State(state.clone()), Path(state.hub_id), Json(mk())).await;
        assert!(replay.is_err(), "identical re-POST must be rejected as a replay");

        // The act was witnessed exactly once: the mailbox holds one notice.
        let pid3 = Uuid::new_v4();
        let sealed3 = seal_req(&member, &hub_pub, pid3, "notifications", serde_json::json!({}));
        let resp3 = channel_request(State(state.clone()), Path(state.hub_id), Json(ChannelRequest {
            caller_lct_id: member_lct, pair_id: pid3, sealed: sealed3, caller_pubkey_hex: None,
        })).await.expect("drain");
        let out3 = open_resp(&member, &hub_pub, pid3, &resp3.0.sealed);
        assert_eq!(out3["total"], serde_json::json!(1),
            "replay must not double-witness — exactly one notice");

        // A genuinely new invocation (fresh seal) is NOT blocked.
        let pid4 = Uuid::new_v4();
        let sealed4 = seal_req(&member, &hub_pub, pid4, "presence", serde_json::json!({}));
        channel_request(State(state.clone()), Path(state.hub_id), Json(ChannelRequest {
            caller_lct_id: member_lct, pair_id: pid4, sealed: sealed4, caller_pubkey_hex: None,
        })).await.expect("a fresh request with new sealed bytes is accepted");
    }

    #[tokio::test]
    async fn channel_stale_issued_at_is_rejected() {
        // A client-dated request outside the freshness window is refused — this is
        // what bounds the replay set so a deferred replay can't outlive it.
        let (_tmp, state) = fresh_rest_state(None).await;
        let hub_pub = state.signer.public_key().unwrap();
        let member = KeyPair::generate();
        let member_lct = Uuid::new_v4();
        // Pin first (fresh request_citizenship, no issued_at → accepted).
        let pid = Uuid::new_v4();
        let sealed = seal_req(&member, &hub_pub, pid, "request_citizenship",
            serde_json::json!({ "name": "Timely" }));
        channel_request(State(state.clone()), Path(state.hub_id), Json(ChannelRequest {
            caller_lct_id: member_lct, pair_id: pid, sealed,
            caller_pubkey_hex: Some(member.verifying_key().to_hex()),
        })).await.expect("pinned");

        // Seal a presence read stamped 10 minutes in the past.
        let pid2 = Uuid::new_v4();
        let stale = (Utc::now() - chrono::Duration::seconds(600)).to_rfc3339();
        let inner = serde_json::json!({
            "tool": "presence", "args": {},
            "nonce": Uuid::new_v4().to_string(), "issued_at": stale,
        });
        let sealed2 = pair_channel::seal(&member, &hub_pub, pid2, &serde_json::to_vec(&inner).unwrap())
            .unwrap().to_base64();
        let res = channel_request(State(state.clone()), Path(state.hub_id), Json(ChannelRequest {
            caller_lct_id: member_lct, pair_id: pid2, sealed: sealed2, caller_pubkey_hex: None,
        })).await;
        assert!(res.is_err(), "stale issued_at must be rejected as out-of-window");
    }

    #[tokio::test]
    async fn mailbox_is_capped_and_drops_oldest() {
        // Flood protection: a member's mailbox can't grow without bound. Past the
        // cap the oldest notices are dropped (ring), so the newest survive.
        let (_tmp, state) = fresh_rest_state(None).await;
        let hub_pub = state.signer.public_key().unwrap();
        let member = KeyPair::generate();
        let member_lct = Uuid::new_v4();
        let pid = Uuid::new_v4();
        let sealed = seal_req(&member, &hub_pub, pid, "request_citizenship",
            serde_json::json!({ "name": "Flooded" }));
        channel_request(State(state.clone()), Path(state.hub_id), Json(ChannelRequest {
            caller_lct_id: member_lct, pair_id: pid, sealed,
            caller_pubkey_hex: Some(member.verifying_key().to_hex()),
        })).await.expect("pinned");

        let overflow = super::MAX_NOTICES_PER_MEMBER + 5;
        for i in 0..overflow {
            super::queue_sealed_notice(
                &state, member_lct, member_lct, "handoff",
                &format!("pr/{i}"), b"body",
            ).await;
        }
        let mailbox = state.notifications.lock().await;
        let queue = mailbox.get(&member_lct).expect("mailbox exists");
        assert_eq!(queue.len(), super::MAX_NOTICES_PER_MEMBER, "capped at the max");
        // The first 5 (oldest) were dropped; the newest is the last enqueued.
        assert_eq!(queue.first().unwrap().pointer_uri, "pr/5", "oldest dropped");
        assert_eq!(queue.last().unwrap().pointer_uri, format!("pr/{}", overflow - 1));
    }

    #[tokio::test]
    async fn projection_cache_reflects_appends_and_matches_full_projection() {
        // The incremental cache must never go stale: after an append the cached
        // projection includes the new entry and equals a from-scratch projection.
        let (_tmp, state) = fresh_rest_state(None).await;
        let before = { let l = state.ledger.lock().await; state.projected(&l) };
        let n0 = before.member_count();

        let zed = Uuid::new_v4();
        witness_event(&state, HubEvent::MemberAdded {
            member_lct_id: zed, added_by: state.sovereign_lct_id,
            member_name: Some("Zed".into()), member_pubkey_hex: None,
        }).await.expect("append MemberAdded");

        let after = { let l = state.ledger.lock().await; state.projected(&l) };
        assert_eq!(after.member_count(), n0 + 1, "cache advanced to include the append");
        assert!(after.members.contains_key(&zed));
        // Cache == source of truth.
        let fresh = { let l = state.ledger.lock().await; HubState::project(&l) };
        assert_eq!(after.member_count(), fresh.member_count());
        assert_eq!(after.last_index, fresh.last_index);
        assert!(fresh.members.contains_key(&zed));
    }

    // ---- §5.1 R7 carrier: obligations + deadline→reputation ----

    async fn pin_member(state: &RestState, hub_pub: &web4_core::crypto::PublicKey) -> (KeyPair, Uuid) {
        let member = KeyPair::generate();
        let lct = Uuid::new_v4();
        let pid = Uuid::new_v4();
        let sealed = seal_req(&member, hub_pub, pid, "request_citizenship",
            serde_json::json!({ "name": "Obligor" }));
        channel_request(State(state.clone()), Path(state.hub_id), Json(ChannelRequest {
            caller_lct_id: lct, pair_id: pid, sealed,
            caller_pubkey_hex: Some(member.verifying_key().to_hex()),
        })).await.expect("pinned");
        (member, lct)
    }

    async fn ref_act(state: &RestState, m: &KeyPair, lct: Uuid, hub_pub: &web4_core::crypto::PublicKey,
                     args: serde_json::Value) -> Result<serde_json::Value, ApiError> {
        let pid = Uuid::new_v4();
        let sealed = seal_req(m, hub_pub, pid, "referenced_act", args);
        let r = channel_request(State(state.clone()), Path(state.hub_id), Json(ChannelRequest {
            caller_lct_id: lct, pair_id: pid, sealed, caller_pubkey_hex: None,
        })).await?;
        Ok(open_resp(m, hub_pub, pid, &r.0.sealed))
    }

    #[tokio::test]
    async fn r7_obligation_opens_then_resolves_on_time() {
        let (_tmp, state) = fresh_rest_state(None).await;
        let hub_pub = state.signer.public_key().unwrap();
        let (m, lct) = pin_member(&state, &hub_pub).await;

        // Open an obligation due in the future.
        let due = (Utc::now() + chrono::Duration::hours(1)).to_rfc3339();
        let out = ref_act(&state, &m, lct, &hub_pub, serde_json::json!({
            "to": {"to":"peer","lct_id": lct}, "kind":"handoff", "pointer_uri":"pr/500",
            "r7": {"request_id":"req-1","role_lct":"citizen",
                   "deadline":{"due_at": due, "criticality":"firm"}},
        })).await.expect("open ok");
        assert_eq!(out["obligation_opened"], serde_json::json!("req-1"));
        // Projected: the obligation is open.
        let proj = { let l = state.ledger.lock().await; HubState::project(&l) };
        assert!(proj.obligations.contains_key("req-1"));

        // Resolve it now (before due) → Met, positive temperament.
        let out2 = ref_act(&state, &m, lct, &hub_pub, serde_json::json!({
            "to": {"to":"peer","lct_id": lct}, "kind":"review_done", "pointer_uri":"pr/500",
            "r7": {"satisfies":"req-1"},
        })).await.expect("resolve ok");
        assert_eq!(out2["outcome"], serde_json::json!("met"));
        assert!(out2["t3_temperament"].as_f64().unwrap() > 0.0, "on-time = positive temperament");

        // Projected: obligation cleared, reputation folded at (subject, role).
        let proj2 = { let l = state.ledger.lock().await; HubState::project(&l) };
        assert!(!proj2.obligations.contains_key("req-1"), "resolved obligation removed");
        let rep = proj2.reputation.get(&(lct.to_string(), "citizen".to_string()))
            .expect("reputation folded for (subject, citizen)");
        assert_eq!(rep.observations, 1);
    }

    #[tokio::test]
    async fn r7_resolve_after_deadline_is_late_and_debits() {
        let (_tmp, state) = fresh_rest_state(None).await;
        let hub_pub = state.signer.public_key().unwrap();
        let (m, lct) = pin_member(&state, &hub_pub).await;

        // Open already past-due, then resolve → Late (negative).
        let due = (Utc::now() - chrono::Duration::hours(1)).to_rfc3339();
        ref_act(&state, &m, lct, &hub_pub, serde_json::json!({
            "to": {"to":"peer","lct_id": lct}, "kind":"handoff", "pointer_uri":"pr/501",
            "r7": {"request_id":"req-2","role_lct":"citizen",
                   "deadline":{"due_at": due, "criticality":"firm"}},
        })).await.expect("open ok");
        let out = ref_act(&state, &m, lct, &hub_pub, serde_json::json!({
            "to": {"to":"peer","lct_id": lct}, "kind":"review_done", "pointer_uri":"pr/501",
            "r7": {"satisfies":"req-2"},
        })).await.expect("resolve ok");
        assert_eq!(out["outcome"], serde_json::json!("late"));
        assert!(out["t3_temperament"].as_f64().unwrap() < 0.0, "late = temperament debit");
    }

    #[tokio::test]
    async fn r7_malformed_or_unknown_is_rejected_fail_closed() {
        let (_tmp, state) = fresh_rest_state(None).await;
        let hub_pub = state.signer.public_key().unwrap();
        let (m, lct) = pin_member(&state, &hub_pub).await;

        // r7 present but neither open nor satisfies → deny (fail-closed).
        let bad = ref_act(&state, &m, lct, &hub_pub, serde_json::json!({
            "to": {"to":"peer","lct_id": lct}, "kind":"handoff", "pointer_uri":"pr/x",
            "r7": {"foo":"bar"},
        })).await;
        assert!(bad.is_err(), "malformed r7 rejected");

        // satisfies an obligation that was never opened → deny (fail-closed).
        let unknown = ref_act(&state, &m, lct, &hub_pub, serde_json::json!({
            "to": {"to":"peer","lct_id": lct}, "kind":"review_done", "pointer_uri":"pr/x",
            "r7": {"satisfies":"never-opened"},
        })).await;
        assert!(unknown.is_err(), "unknown obligation rejected");
    }

    #[tokio::test]
    async fn r7_reopen_is_rejected_and_clock_not_reset() {
        // The clock-reset attack: open past-due, re-open with a fresh future
        // deadline, then satisfy → "met". The re-open must be rejected, and even
        // if it weren't the keep-first fold preserves the original clock.
        let (_tmp, state) = fresh_rest_state(None).await;
        let hub_pub = state.signer.public_key().unwrap();
        let (m, lct) = pin_member(&state, &hub_pub).await;
        let past = (Utc::now() - chrono::Duration::hours(1)).to_rfc3339();
        ref_act(&state, &m, lct, &hub_pub, serde_json::json!({
            "to": {"to":"peer","lct_id": lct}, "kind":"handoff", "pointer_uri":"pr/1",
            "r7": {"request_id":"req-x","role_lct":"citizen",
                   "deadline":{"due_at": past, "criticality":"firm"}},
        })).await.expect("open past-due");

        let future = (Utc::now() + chrono::Duration::hours(1)).to_rfc3339();
        let reopen = ref_act(&state, &m, lct, &hub_pub, serde_json::json!({
            "to": {"to":"peer","lct_id": lct}, "kind":"handoff", "pointer_uri":"pr/1",
            "r7": {"request_id":"req-x","role_lct":"citizen",
                   "deadline":{"due_at": future, "criticality":"firm"}},
        })).await;
        assert!(reopen.is_err(), "re-open of a live obligation must be rejected");

        // Satisfy → still LATE (the original past-due clock stands).
        let out = ref_act(&state, &m, lct, &hub_pub, serde_json::json!({
            "to": {"to":"peer","lct_id": lct}, "kind":"review_done", "pointer_uri":"pr/1",
            "r7": {"satisfies":"req-x"},
        })).await.expect("resolve");
        assert_eq!(out["outcome"], serde_json::json!("late"), "clock was not reset");
    }

    #[tokio::test]
    async fn r7_satisfy_by_non_subject_is_rejected() {
        // Griefing guard: only the obligation's subject may satisfy it.
        let (_tmp, state) = fresh_rest_state(None).await;
        let hub_pub = state.signer.public_key().unwrap();
        let (a, a_lct) = pin_member(&state, &hub_pub).await;
        let (b, b_lct) = pin_member(&state, &hub_pub).await;
        let future = (Utc::now() + chrono::Duration::hours(1)).to_rfc3339();
        ref_act(&state, &a, a_lct, &hub_pub, serde_json::json!({
            "to": {"to":"peer","lct_id": a_lct}, "kind":"handoff", "pointer_uri":"pr/2",
            "r7": {"request_id":"req-a","role_lct":"citizen",
                   "deadline":{"due_at": future, "criticality":"firm"}},
        })).await.expect("A opens");

        // B attempts to resolve A's obligation → rejected.
        let grief = ref_act(&state, &b, b_lct, &hub_pub, serde_json::json!({
            "to": {"to":"peer","lct_id": b_lct}, "kind":"review_done", "pointer_uri":"pr/2",
            "r7": {"satisfies":"req-a"},
        })).await;
        assert!(grief.is_err(), "a non-subject cannot satisfy another's obligation");

        // A resolves its own → ok.
        ref_act(&state, &a, a_lct, &hub_pub, serde_json::json!({
            "to": {"to":"peer","lct_id": a_lct}, "kind":"review_done", "pointer_uri":"pr/2",
            "r7": {"satisfies":"req-a"},
        })).await.expect("subject resolves its own");
    }

    #[tokio::test]
    async fn presence_roster_shows_active_members_online() {
        let (_tmp, state) = fresh_rest_state(None).await; // open admission
        let hub_pub = state.signer.public_key().unwrap();
        let a = KeyPair::generate();
        let a_lct = Uuid::new_v4();
        let b = KeyPair::generate();
        let b_lct = Uuid::new_v4();
        // admit both, then each does a citizen op so presence registers their liveness
        for (kp, lct) in [(&a, a_lct), (&b, b_lct)] {
            let pid = Uuid::new_v4();
            let sealed = seal_req(kp, &hub_pub, pid, "request_citizenship",
                serde_json::json!({ "name": "P" }));
            channel_request(State(state.clone()), Path(state.hub_id), Json(ChannelRequest {
                caller_lct_id: lct, pair_id: pid, sealed,
                caller_pubkey_hex: Some(kp.verifying_key().to_hex()),
            })).await.expect("admitted");
            let pid2 = Uuid::new_v4();
            let sealed2 = seal_req(kp, &hub_pub, pid2, "query_hub", serde_json::json!({}));
            channel_request(State(state.clone()), Path(state.hub_id), Json(ChannelRequest {
                caller_lct_id: lct, pair_id: pid2, sealed: sealed2, caller_pubkey_hex: None,
            })).await.expect("liveness op");
        }
        // A reads the presence roster (the bidirectional ping).
        let pid = Uuid::new_v4();
        let sealed = seal_req(&a, &hub_pub, pid, "presence", serde_json::json!({}));
        let resp = channel_request(State(state.clone()), Path(state.hub_id), Json(ChannelRequest {
            caller_lct_id: a_lct, pair_id: pid, sealed, caller_pubkey_hex: None,
        })).await.expect("presence");
        let out = open_resp(&a, &hub_pub, pid, &resp.0.sealed);
        let present = out["present"].as_array().expect("present array");
        let find = |lct: Uuid| present.iter().find(|m| m["lct_id"] == serde_json::json!(lct)).cloned();
        let ma = find(a_lct).expect("A in roster");
        let mb = find(b_lct).expect("B in roster");
        assert_eq!(ma["status"], serde_json::json!("online"), "A just active -> online");
        assert_eq!(mb["status"], serde_json::json!("online"), "B just active -> online");
        assert!(!ma["last_seen"].is_null() && !mb["last_seen"].is_null(), "last_seen populated");
    }

    #[tokio::test]
    async fn admission_law_escalates_external_join() {
        // The live admission law: joins escalate to the Sovereign, not auto-admit.
        const LAW: &str = r#"
version: "1.0.0"
norms:
  - id: ADMISSION-REQUIRES-SOVEREIGN
    selector: r6.request.action
    operator: "=="
    value: member_join_request
    decision: escalate
    priority: 100
"#;
        let (_tmp, state) = fresh_rest_state(Some(LAW)).await;
        let hub_pub = state.signer.public_key().unwrap();
        let applicant = KeyPair::generate();
        let pid = Uuid::new_v4();
        let sealed = seal_req(&applicant, &hub_pub, pid, "request_citizenship",
            serde_json::json!({ "name": "Should Escalate" }));
        let req = ChannelRequest {
            caller_lct_id: Uuid::new_v4(),
            pair_id: pid,
            sealed,
            caller_pubkey_hex: Some(applicant.verifying_key().to_hex()),
        };
        let resp = channel_request(State(state.clone()), Path(state.hub_id), Json(req))
            .await
            .expect("escalated join is queued (200 sealed), not an error");
        let out = open_resp(&applicant, &hub_pub, pid, &resp.0.sealed);
        assert_eq!(out["admitted"], serde_json::json!(false), "escalate → not admitted");
        assert_eq!(out["status"], serde_json::json!("pending_review"));
        let request_id: Uuid = serde_json::from_value(out["request_id"].clone())
            .expect("a request_id was returned");

        // It is witnessed as a Pending entry in the admission queue, not dropped.
        let projected = {
            let ledger = state.ledger.lock().await;
            HubState::project(&ledger)
        };
        let jr = projected.pending_joins.get(&request_id).expect("queued for review");
        assert_eq!(jr.status, hub_lib::state::JoinStatus::Pending);

        // The operator approves it → member admitted live, no restart; status flips.
        let (_idx, _hash) = approve_join(&state, request_id, state.sovereign_lct_id)
            .await
            .expect("approve should admit the member");
        let after = {
            let ledger = state.ledger.lock().await;
            HubState::project(&ledger)
        };
        assert_eq!(after.pending_joins[&request_id].status, hub_lib::state::JoinStatus::Approved);
        assert!(after.members.contains_key(&jr.member_lct_id), "approved applicant is now a member");
        assert!(after.member_pubkeys.contains_key(&jr.member_lct_id), "their pubkey is pinned");
        assert!(state.resolver.read().await.0.contains_key(&jr.member_lct_id),
            "and they are in the LIVE resolver — no serve restart needed");
    }

    #[tokio::test]
    async fn deny_join_records_denial_and_admits_nobody() {
        const LAW: &str = r#"
version: "1.0.0"
norms:
  - id: ADMISSION-REQUIRES-SOVEREIGN
    selector: r6.request.action
    operator: "=="
    value: member_join_request
    decision: escalate
    priority: 100
"#;
        let (_tmp, state) = fresh_rest_state(Some(LAW)).await;
        let hub_pub = state.signer.public_key().unwrap();
        let applicant = KeyPair::generate();
        let pid = Uuid::new_v4();
        let sealed = seal_req(&applicant, &hub_pub, pid, "request_citizenship",
            serde_json::json!({ "name": "Reject Me" }));
        let req = ChannelRequest {
            caller_lct_id: Uuid::new_v4(),
            pair_id: pid,
            sealed,
            caller_pubkey_hex: Some(applicant.verifying_key().to_hex()),
        };
        let resp = channel_request(State(state.clone()), Path(state.hub_id), Json(req))
            .await.unwrap();
        let out = open_resp(&applicant, &hub_pub, pid, &resp.0.sealed);
        let request_id: Uuid = serde_json::from_value(out["request_id"].clone()).unwrap();
        let member_lct = {
            let ledger = state.ledger.lock().await;
            HubState::project(&ledger).pending_joins[&request_id].member_lct_id
        };

        deny_join(&state, request_id, state.sovereign_lct_id, Some("not this time".into()))
            .await.expect("deny should record a denial");

        let after = {
            let ledger = state.ledger.lock().await;
            HubState::project(&ledger)
        };
        assert_eq!(after.pending_joins[&request_id].status, hub_lib::state::JoinStatus::Denied);
        assert_eq!(after.pending_joins[&request_id].reason.as_deref(), Some("not this time"));
        assert!(!after.members.contains_key(&member_lct), "denied applicant is NOT a member");

        // Double-resolve is rejected (idempotency guard).
        assert!(approve_join(&state, request_id, state.sovereign_lct_id).await.is_err(),
            "an already-resolved request can't be approved");
    }

    #[tokio::test]
    async fn operator_api_lists_and_admits_behind_the_loopback_guard() {
        const LAW: &str = r#"
version: "1.0.0"
norms:
  - id: ADMISSION-REQUIRES-SOVEREIGN
    selector: r6.request.action
    operator: "=="
    value: member_join_request
    decision: escalate
    priority: 100
"#;
        let (_tmp, state) = fresh_rest_state(Some(LAW)).await;
        let hub_pub = state.signer.public_key().unwrap();
        let applicant = KeyPair::generate();
        let applicant_lct = Uuid::new_v4();
        let pid = Uuid::new_v4();
        let sealed = seal_req(&applicant, &hub_pub, pid, "request_citizenship",
            serde_json::json!({ "name": "Via API" }));
        let req = ChannelRequest {
            caller_lct_id: applicant_lct,
            pair_id: pid,
            sealed,
            caller_pubkey_hex: Some(applicant.verifying_key().to_hex()),
        };
        let resp = match channel_request(State(state.clone()), Path(state.hub_id), Json(req)).await { Ok(r)=>r, Err(e)=>panic!("channel_request {}: {}", e.status, e.message) };
        let out = open_resp(&applicant, &hub_pub, pid, &resp.0.sealed);
        let request_id: Uuid = serde_json::from_value(out["request_id"].clone()).unwrap();

        let loop_addr: SocketAddr = "127.0.0.1:5555".parse().unwrap();
        let remote_addr: SocketAddr = "10.0.0.9:5555".parse().unwrap();

        // Non-loopback callers are rejected (defense-in-depth behind the bind).
        assert_eq!(
            admin_list_joins(State(state.clone()), ConnectInfo(remote_addr)).await.err().unwrap().status,
            StatusCode::FORBIDDEN,
        );
        // Loopback lists the pending request.
        let list = admin_list_joins(State(state.clone()), ConnectInfo(loop_addr)).await.unwrap();
        assert_eq!(list.0["pending"], serde_json::json!(1));

        // Admit via the API → member admitted live (no restart).
        admin_admit_join(State(state.clone()), ConnectInfo(loop_addr), Path(request_id)).await.unwrap();
        let proj = { let l = state.ledger.lock().await; HubState::project(&l) };
        assert!(proj.members.contains_key(&applicant_lct), "admitted via the operator API");
        assert_eq!(proj.pending_joins[&request_id].status, hub_lib::state::JoinStatus::Approved);

        // A remote caller can't admit even with a valid id.
        assert_eq!(
            admin_admit_join(State(state.clone()), ConnectInfo(remote_addr), Path(request_id))
                .await.err().unwrap().status,
            StatusCode::FORBIDDEN,
        );
    }

    #[tokio::test]
    async fn operator_add_member_admits_a_known_member_live() {
        let (_tmp, state) = fresh_rest_state(None).await;
        let kp = KeyPair::generate();
        let lct = Uuid::new_v4();
        let loop_addr: SocketAddr = "127.0.0.1:5555".parse().unwrap();
        let remote_addr: SocketAddr = "10.0.0.9:5555".parse().unwrap();
        let body = || AddMemberBody { lct_id: lct, pubkey_hex: kp.verifying_key().to_hex(), name: Some("Sprout".into()) };

        // Remote callers are rejected.
        assert_eq!(
            admin_add_member(State(state.clone()), ConnectInfo(remote_addr), Json(body()))
                .await.err().unwrap().status,
            StatusCode::FORBIDDEN,
        );
        // Loopback adds the member live (in the resolver, no restart).
        admin_add_member(State(state.clone()), ConnectInfo(loop_addr), Json(body())).await.unwrap();
        let proj = { let l = state.ledger.lock().await; HubState::project(&l) };
        assert!(proj.members.contains_key(&lct));
        assert!(proj.member_pubkeys.contains_key(&lct));
        assert!(state.resolver.read().await.0.contains_key(&lct), "in the live resolver");
        // Double-add is rejected.
        assert!(admin_add_member(State(state.clone()), ConnectInfo(loop_addr), Json(body())).await.is_err());
    }

    #[tokio::test]
    async fn pin_member_key_rotates_the_live_resolver_without_restart() {
        let (_tmp, state) = fresh_rest_state(None).await;
        let member = Uuid::new_v4();
        let key_a = KeyPair::generate();
        let key_b = KeyPair::generate();

        admit_member(&state, member, &key_a.verifying_key().to_hex(), Some("Rotator".into()))
            .await.unwrap();
        assert_eq!(state.resolver.read().await.0[&member].public_key.to_hex(),
            key_a.verifying_key().to_hex());

        // Rotate the key live — the sprout JetPack-wipe re-key case for a member.
        pin_member_key(&state, member, &key_b.verifying_key().to_hex()).await.unwrap();
        assert_eq!(state.resolver.read().await.0[&member].public_key.to_hex(),
            key_b.verifying_key().to_hex(),
            "the live resolver reflects the rotated key immediately — no serve restart");
        let proj = { let l = state.ledger.lock().await; HubState::project(&l) };
        assert_eq!(proj.member_pubkeys[&member], key_b.verifying_key().to_hex());

        // Keying an unknown LCT errors (must be an existing member).
        assert!(pin_member_key(&state, Uuid::new_v4(), &key_a.verifying_key().to_hex()).await.is_err());
    }

    #[tokio::test]
    async fn remove_member_live_evicts_from_resolver_and_projection() {
        let (_tmp, state) = fresh_rest_state(None).await;
        let member = Uuid::new_v4();
        let kp = KeyPair::generate();
        admit_member(&state, member, &kp.verifying_key().to_hex(), Some("Goodbye".into()))
            .await.unwrap();
        assert!(state.resolver.read().await.0.contains_key(&member));

        remove_member_live(&state, member, Some("retired".into())).await.unwrap();

        assert!(!state.resolver.read().await.0.contains_key(&member),
            "evicted from the live resolver — no restart");
        let proj = { let l = state.ledger.lock().await; HubState::project(&l) };
        assert!(!proj.members.contains_key(&member));
        assert!(!proj.member_pubkeys.contains_key(&member),
            "pinned key dropped from projection — won't be re-seeded on a future restart");

        // Removing a non-member errors.
        assert!(remove_member_live(&state, Uuid::new_v4(), None).await.is_err());
    }

    #[tokio::test]
    async fn admission_is_idempotent_no_duplicate_pending() {
        const LAW: &str = r#"
version: "1.0.0"
norms:
  - id: ADMISSION-REQUIRES-SOVEREIGN
    selector: r6.request.action
    operator: "=="
    value: member_join_request
    decision: escalate
    priority: 100
"#;
        let (_tmp, state) = fresh_rest_state(Some(LAW)).await;
        let hub_pub = state.signer.public_key().unwrap();
        let applicant = KeyPair::generate();
        let applicant_lct = Uuid::new_v4();
        let hex = applicant.verifying_key().to_hex();

        // Submit a request_citizenship over the channel; returns the sealed
        // dispatch result, or the ApiError if the channel refused it.
        let submit = || {
            let (state, hub_pub, applicant, hex) =
                (state.clone(), hub_pub.clone(), applicant.clone(), hex.clone());
            async move {
                let pid = Uuid::new_v4();
                let sealed = seal_req(&applicant, &hub_pub, pid, "request_citizenship",
                    serde_json::json!({ "name": "Dup" }));
                let req = ChannelRequest { caller_lct_id: applicant_lct, pair_id: pid, sealed,
                    caller_pubkey_hex: Some(hex) };
                channel_request(State(state.clone()), Path(state.hub_id), Json(req)).await
                    .map(|resp| open_resp(&applicant, &hub_pub, pid, &resp.0.sealed))
            }
        };

        // First application → queued pending.
        let first = submit().await.unwrap();
        let rid1: Uuid = serde_json::from_value(first["request_id"].clone()).unwrap();
        // Repeat application → SAME request_id, flagged already_pending, no new entry.
        let second = submit().await.unwrap();
        assert_eq!(second["already_pending"], serde_json::json!(true));
        assert_eq!(serde_json::from_value::<Uuid>(second["request_id"].clone()).unwrap(), rid1,
            "a repeat application returns the existing pending request");
        let pending = {
            let l = state.ledger.lock().await;
            HubState::project(&l).pending_joins.values()
                .filter(|j| j.member_lct_id == applicant_lct
                    && j.status == hub_lib::state::JoinStatus::Pending)
                .count()
        };
        assert_eq!(pending, 1, "exactly one pending entry — no duplicates");

        // Approve → member. A member can't even re-apply over the channel
        // (request_citizenship is external-tier-only), so re-application is refused
        // at tier routing — the end-to-end idempotence guarantee.
        approve_join(&state, rid1, state.sovereign_lct_id).await.unwrap();
        assert!(submit().await.is_err(), "an admitted member cannot re-apply via the channel");
    }

    #[tokio::test]
    async fn admission_repair_path_blocks_reviews_and_resets() {
        // Escalate law (no limits set → defaults repeat_limit=3, review_limit=1).
        const LAW: &str = r#"
version: "1.0.0"
norms:
  - id: ADMISSION-REQUIRES-SOVEREIGN
    selector: r6.request.action
    operator: "=="
    value: member_join_request
    decision: escalate
    priority: 100
"#;
        let (_tmp, state) = fresh_rest_state(Some(LAW)).await;
        let hub_pub = state.signer.public_key().unwrap();
        let applicant = KeyPair::generate();
        let lct = Uuid::new_v4();
        let hex = applicant.verifying_key().to_hex();
        let sov = state.sovereign_lct_id;

        // Channel call helper (request_citizenship / request_admission_review).
        let call = |tool: &'static str, args: serde_json::Value| {
            let (state, hub_pub, applicant, hex) =
                (state.clone(), hub_pub.clone(), applicant.clone(), hex.clone());
            async move {
                let pid = Uuid::new_v4();
                let sealed = seal_req(&applicant, &hub_pub, pid, tool, args);
                let req = ChannelRequest { caller_lct_id: lct, pair_id: pid, sealed,
                    caller_pubkey_hex: Some(hex) };
                channel_request(State(state.clone()), Path(state.hub_id), Json(req)).await
                    .map(|resp| open_resp(&applicant, &hub_pub, pid, &resp.0.sealed))
            }
        };
        // Apply, returning the operator-denied request's id (drives a denial).
        async fn apply_and_get_rid(out: serde_json::Value) -> Uuid {
            serde_json::from_value(out["request_id"].clone()).expect("queued request_id")
        }

        // Three applications, each operator-denied → blocked.
        for _ in 0..3 {
            let r = call("request_citizenship", serde_json::json!({"name":"X"})).await.unwrap();
            let rid = apply_and_get_rid(r).await;
            deny_join(&state, rid, sov, Some("no".into())).await.unwrap();
        }
        let blocked = call("request_citizenship", serde_json::json!({"name":"X"})).await.unwrap();
        assert_eq!(blocked["status"], serde_json::json!("blocked"));
        assert_eq!(blocked["can_review"], serde_json::json!(true), "first block → review available");

        // Plea for a review (idempotent), operator grants → auto-block cleared.
        let rev = call("request_admission_review", serde_json::json!({"plea":"please"})).await.unwrap();
        let review_id: Uuid = serde_json::from_value(rev["review_id"].clone()).unwrap();
        let rev2 = call("request_admission_review", serde_json::json!({})).await.unwrap();
        assert_eq!(rev2["already_pending"], serde_json::json!(true), "review plea is idempotent");
        grant_review(&state, review_id, sov).await.unwrap();

        // Unblocked: applies again (queues, not blocked).
        let reapply = call("request_citizenship", serde_json::json!({})).await.unwrap();
        assert_eq!(reapply["status"], serde_json::json!("pending_review"), "grant cleared the block");
        let rid2 = apply_and_get_rid(reapply).await;
        deny_join(&state, rid2, sov, None).await.unwrap();
        for _ in 0..2 {
            let r = call("request_citizenship", serde_json::json!({})).await.unwrap();
            let rid = apply_and_get_rid(r).await;
            deny_join(&state, rid, sov, None).await.unwrap();
        }
        // Blocked again — but reviews (1) now == review_limit (1) → terminal.
        let blocked2 = call("request_citizenship", serde_json::json!({})).await.unwrap();
        assert_eq!(blocked2["status"], serde_json::json!("blocked"));
        assert_eq!(blocked2["can_review"], serde_json::json!(false), "review limit reached → terminal");
        assert!(call("request_admission_review", serde_json::json!({})).await.is_err(),
            "terminal: review plea refused");

        // Operator admission-reset → cleared; applies afresh.
        admission_reset(&state, lct, sov, Some("fresh start".into())).await.unwrap();
        let after = call("request_citizenship", serde_json::json!({})).await.unwrap();
        assert_eq!(after["status"], serde_json::json!("pending_review"), "reset cleared everything");
    }

    #[tokio::test]
    async fn law_defaults_hydrate_into_the_law_idempotently() {
        // Base law with no admission section (limits live only as code defaults).
        const BASE_LAW: &str = r#"
version: "1.0.0"
norms:
  - id: ADMISSION-REQUIRES-SOVEREIGN
    selector: r6.request.action
    operator: "=="
    value: member_join_request
    decision: escalate
    priority: 100
"#;
        let (_tmp, state) = fresh_rest_state(Some(BASE_LAW)).await;
        assert!(state.law.read().await.as_ref().unwrap().ext.admission.is_none(),
            "limits start as code defaults, not in the law");

        // First hydrate fills the defaults into the law + advances the version.
        assert!(hydrate_law_defaults(&state).await.unwrap(), "first hydrate fills gaps");
        let law = state.law.read().await.clone().unwrap();
        assert_eq!(law.ext.admission.as_ref().unwrap().repeat_limit, Some(3));
        assert_eq!(law.ext.admission.as_ref().unwrap().review_limit, Some(1));
        assert_eq!(law.version, "1.0.1", "amendment advanced the version");
        // Witnessed as a LawAmended, and persisted to the store.
        assert!({
            let l = state.ledger.lock().await;
            l.entries().iter().any(|e| e.event.kind() == "law_amended")
        });
        let persisted = state.open_store().await.unwrap().read_law().await.unwrap().unwrap();
        assert_eq!(hub_lib::law::Law::parse_and_validate(&persisted).unwrap().admission_repeat_limit(), 3);

        // Idempotent: a second hydrate is a no-op (no new amendment).
        assert!(!hydrate_law_defaults(&state).await.unwrap(), "steady-state boot is a no-op");
    }

    #[tokio::test]
    async fn admin_nav_is_plane_aware() {
        let (_tmp, mut state) = fresh_rest_state(None).await;
        // Fleet plane (default): the read-only dashboard must NOT advertise the
        // operator-only write pages (they'd 404 there).
        let html = crate::admin::members(State(state.clone())).await.unwrap().0;
        assert!(!html.contains("/admin/joins"), "fleet nav must not link operator pages");
        assert!(!html.contains("/admin/manage"), "fleet nav must not link operator pages");
        // Operator plane: the same page DOES surface the write-page nav links.
        state.operator_plane = true;
        let html = crate::admin::members(State(state.clone())).await.unwrap().0;
        assert!(html.contains("/admin/joins") && html.contains("/admin/manage"),
            "operator nav links the write pages");
    }

    #[tokio::test]
    async fn operator_joins_page_renders_pending_with_admit_button() {
        const LAW: &str = r#"
version: "1.0.0"
norms:
  - id: ADMISSION-REQUIRES-SOVEREIGN
    selector: r6.request.action
    operator: "=="
    value: member_join_request
    decision: escalate
    priority: 100
"#;
        let (_tmp, state) = fresh_rest_state(Some(LAW)).await;
        let hub_pub = state.signer.public_key().unwrap();
        let applicant = KeyPair::generate();
        let pid = Uuid::new_v4();
        let sealed = seal_req(&applicant, &hub_pub, pid, "request_citizenship",
            serde_json::json!({ "name": "Render Me", "message": "please let me in" }));
        let req = ChannelRequest {
            caller_lct_id: Uuid::new_v4(),
            pair_id: pid,
            sealed,
            caller_pubkey_hex: Some(applicant.verifying_key().to_hex()),
        };
        channel_request(State(state.clone()), Path(state.hub_id), Json(req)).await.unwrap();

        let html = crate::admin::joins_page(State(state.clone())).await.unwrap().0;
        assert!(html.contains("Admission queue"), "page title");
        assert!(html.contains("Operator plane"), "operator banner");
        assert!(html.contains("Render Me"), "applicant name shown");
        assert!(html.contains("please let me in"), "applicant message shown");
        assert!(html.contains("admit("), "Admit button wired to the API");
        assert!(html.contains("deny("), "Deny button wired to the API");
        // The repair-path review queue + reset control render on the same page.
        assert!(html.contains("Denial reviews"), "review queue section");
        assert!(html.contains("grantReview(") && html.contains("refuseReview("), "review buttons wired");
        assert!(html.contains("admissionReset("), "admission-reset control wired");
        // The admission-policy (limits) section + law-writing form render too.
        assert!(html.contains("Admission policy"), "policy section");
        assert!(html.contains("setLimits(") && html.contains("Write to hub law"), "limits form wired to law");
    }

    #[tokio::test]
    async fn operator_sets_admission_limits_by_amending_law() {
        const BASE_LAW: &str = r#"
version: "1.0.0"
norms:
  - id: ADMISSION-REQUIRES-SOVEREIGN
    selector: r6.request.action
    operator: "=="
    value: member_join_request
    decision: escalate
    priority: 100
"#;
        let (_tmp, state) = fresh_rest_state(Some(BASE_LAW)).await;
        let loop_addr: SocketAddr = "127.0.0.1:5555".parse().unwrap();
        let remote: SocketAddr = "10.0.0.9:5555".parse().unwrap();

        // Defaults until set (no admission section in the base law).
        assert_eq!(state.law.read().await.as_ref().unwrap().admission_review_limit(), 1);

        // Remote caller rejected.
        assert_eq!(
            admin_set_admission_limits(State(state.clone()), ConnectInfo(remote),
                Json(AdmissionLimitsBody { repeat_limit: Some(5), review_limit: Some(2) }))
                .await.err().unwrap().status,
            StatusCode::FORBIDDEN,
        );
        // Operator sets them → written to law (live + witnessed).
        admin_set_admission_limits(State(state.clone()), ConnectInfo(loop_addr),
            Json(AdmissionLimitsBody { repeat_limit: Some(5), review_limit: Some(2) }))
            .await.unwrap();
        let law = state.law.read().await.clone().unwrap();
        assert_eq!(law.admission_repeat_limit(), 5);
        assert_eq!(law.admission_review_limit(), 2);
        assert_eq!(law.version, "1.0.1", "the amendment advances the version (1.0.0 → 1.0.1)");
        assert!(law.ext.admission.as_ref().unwrap().repeat_limit == Some(5), "persisted in the law's admission section");
        // A LawAmended was witnessed.
        let amended = {
            let l = state.ledger.lock().await;
            l.entries().iter().any(|e| e.event.kind() == "law_amended")
        };
        assert!(amended, "the change is witnessed as a LawAmended");
        // And it round-trips through the on-disk store (re-projects to the same values).
        let persisted = state.open_store().await.unwrap().read_law().await.unwrap().unwrap();
        let reparsed = hub_lib::law::Law::parse_and_validate(&persisted).unwrap();
        assert_eq!(reparsed.admission_repeat_limit(), 5);
        assert_eq!(reparsed.admission_review_limit(), 2);
    }

    #[tokio::test]
    async fn operator_manage_page_renders_member_actions() {
        let (_tmp, state) = fresh_rest_state(None).await;
        let member = Uuid::new_v4();
        let kp = KeyPair::generate();
        admit_member(&state, member, &kp.verifying_key().to_hex(), Some("Manageable".into()))
            .await.unwrap();

        let html = crate::admin::manage_page(State(state.clone())).await.unwrap().0;
        assert!(html.contains("Manage members"));
        assert!(html.contains("Manageable"));
        assert!(html.contains("rekey("), "Re-key button wired");
        assert!(html.contains("removeMember("), "Remove button wired");
    }

    #[tokio::test]
    async fn find_members_over_channel_then_degrades_when_engine_down() {
        use axum::{routing::post, Router};

        // Stand up a mock discovery engine (the membox sidecar's contract).
        let app = Router::new().route(
            "/find_members",
            post(|| async {
                axum::Json(serde_json::json!({
                    "results": [{ "member_lct": "657b6bc9", "name": "Ada", "score": 0.87 }],
                    "total": 1
                }))
            }),
        );
        let listener = tokio::net::TcpListener::bind("127.0.0.1:0").await.unwrap();
        let addr = listener.local_addr().unwrap();
        tokio::spawn(async move { axum::serve(listener, app).await.unwrap(); });
        std::env::set_var("WEB4_MEMBOX_URL", format!("http://{addr}"));

        let (_tmp, state) = fresh_rest_state(None).await; // open admission
        let hub_pub = state.signer.public_key().unwrap();
        let applicant = KeyPair::generate();
        let applicant_lct = Uuid::new_v4();

        // Admit so the caller is a citizen (find_members is citizen-gated).
        let pid = Uuid::new_v4();
        let sealed = seal_req(&applicant, &hub_pub, pid, "request_citizenship",
            serde_json::json!({ "name": "Caller" }));
        channel_request(State(state.clone()), Path(state.hub_id), Json(ChannelRequest {
            caller_lct_id: applicant_lct, pair_id: pid, sealed,
            caller_pubkey_hex: Some(applicant.verifying_key().to_hex()),
        })).await.expect("admitted");

        // find_members over the channel → hub gates+scopes, calls the engine,
        // seals the ranked LCTs back.
        let pid2 = Uuid::new_v4();
        let sealed2 = seal_req(&applicant, &hub_pub, pid2, "find_members",
            serde_json::json!({ "query": "diffusion eval harness" }));
        let resp = channel_request(State(state.clone()), Path(state.hub_id), Json(ChannelRequest {
            caller_lct_id: applicant_lct, pair_id: pid2, sealed: sealed2, caller_pubkey_hex: None,
        })).await.expect("find_members ok");
        let out = open_resp(&applicant, &hub_pub, pid2, &resp.0.sealed);
        assert_eq!(out["results"][0]["member_lct"], serde_json::json!("657b6bc9"));
        assert_eq!(out["total"], serde_json::json!(1));

        // Engine down → graceful 503, hub itself unaffected.
        std::env::set_var("WEB4_MEMBOX_URL", "http://127.0.0.1:1");
        let pid3 = Uuid::new_v4();
        let sealed3 = seal_req(&applicant, &hub_pub, pid3, "find_members",
            serde_json::json!({ "query": "anything" }));
        let err = channel_request(State(state.clone()), Path(state.hub_id), Json(ChannelRequest {
            caller_lct_id: applicant_lct, pair_id: pid3, sealed: sealed3, caller_pubkey_hex: None,
        })).await.err().expect("engine-down should error");
        assert_eq!(err.status, StatusCode::SERVICE_UNAVAILABLE);

        std::env::remove_var("WEB4_MEMBOX_URL");
    }

    /// Seal+send one channel call for an admitted member; open the response.
    async fn member_call(
        state: &RestState,
        me: &KeyPair,
        my_lct: Uuid,
        tool: &str,
        args: serde_json::Value,
    ) -> Result<serde_json::Value, ApiError> {
        let hub_pub = state.signer.public_key().unwrap();
        let pid = Uuid::new_v4();
        let sealed = seal_req(me, &hub_pub, pid, tool, args);
        let resp = channel_request(State(state.clone()), Path(state.hub_id), Json(ChannelRequest {
            caller_lct_id: my_lct, pair_id: pid, sealed, caller_pubkey_hex: None,
        })).await?;
        Ok(open_resp(me, &hub_pub, pid, &resp.0.sealed))
    }

    #[tokio::test]
    async fn intro_full_loop_mutual_approval_exchanges_pubkeys() {
        let (_tmp, state) = fresh_rest_state(None).await; // open admission
        let hub_pub = state.signer.public_key().unwrap();

        // Admit Alice and Bob over the channel (pins their pubkeys).
        let (alice, alice_lct) = (KeyPair::generate(), Uuid::new_v4());
        let (bob, bob_lct) = (KeyPair::generate(), Uuid::new_v4());
        for (kp, lct, name) in [(&alice, alice_lct, "Alice"), (&bob, bob_lct, "Bob")] {
            let pid = Uuid::new_v4();
            let sealed = seal_req(kp, &hub_pub, pid, "request_citizenship",
                serde_json::json!({ "name": name }));
            channel_request(State(state.clone()), Path(state.hub_id), Json(ChannelRequest {
                caller_lct_id: lct, pair_id: pid, sealed,
                caller_pubkey_hex: Some(kp.verifying_key().to_hex()),
            })).await.expect("admitted");
        }

        // Alice requests an intro to Bob.
        let out = member_call(&state, &alice, alice_lct, "request_intro",
            serde_json::json!({ "to": bob_lct, "purpose": "collab on evals" })).await.unwrap();
        assert_eq!(out["status"], serde_json::json!("pending"));
        let intro_id = out["intro_id"].as_str().unwrap().to_string();

        // Duplicate pending request is rejected.
        let dup = member_call(&state, &alice, alice_lct, "request_intro",
            serde_json::json!({ "to": bob_lct })).await;
        assert!(dup.is_err(), "duplicate pending intro must be rejected");

        // Bob sees it pending; Alice can't respond to her own request.
        let bob_list = member_call(&state, &bob, bob_lct, "list_intros", serde_json::json!({})).await.unwrap();
        assert_eq!(bob_list["total"], serde_json::json!(1));
        assert_eq!(bob_list["intros"][0]["status"], serde_json::json!("pending"));
        let not_target = member_call(&state, &alice, alice_lct, "respond_intro",
            serde_json::json!({ "intro_id": intro_id, "accept": true })).await;
        assert!(not_target.is_err(), "only the target may respond");

        // Bob accepts → gets Alice's pinned pubkey in the response.
        let acc = member_call(&state, &bob, bob_lct, "respond_intro",
            serde_json::json!({ "intro_id": intro_id, "accept": true })).await.unwrap();
        assert_eq!(acc["status"], serde_json::json!("accepted"));
        assert_eq!(acc["peer_pubkey_hex"], serde_json::json!(alice.verifying_key().to_hex()));

        // Alice's list now shows accepted + Bob's pinned pubkey — everything a
        // direct member↔member pair_channel needs.
        let alice_list = member_call(&state, &alice, alice_lct, "list_intros", serde_json::json!({})).await.unwrap();
        assert_eq!(alice_list["intros"][0]["status"], serde_json::json!("accepted"));
        assert_eq!(alice_list["intros"][0]["peer_pubkey_hex"], serde_json::json!(bob.verifying_key().to_hex()));

        // Already-resolved: a second response is rejected.
        let again = member_call(&state, &bob, bob_lct, "respond_intro",
            serde_json::json!({ "intro_id": intro_id, "accept": false })).await;
        assert!(again.is_err(), "resolved intro can't be re-responded");
    }

    use hub_lib::constellation::{
        signing_payload, AssuranceLevel, ConstellationAttestation, DeviceSignature, DeviceType,
    };

    /// Build + sign an attestation the way hestia's member side does.
    fn make_att(
        owner_kp: &KeyPair,
        owner_lct: Uuid,
        cosigners: &[(DeviceType, &KeyPair)],
        nonce: &str,
        issued_at: chrono::DateTime<chrono::Utc>,
    ) -> ConstellationAttestation {
        let roster: Vec<Uuid> = cosigners.iter().map(|_| Uuid::new_v4()).collect();
        let payload = signing_payload(owner_lct, &roster, nonce, &issued_at);
        ConstellationAttestation {
            owner_lct_id: owner_lct,
            owner_pubkey_hex: owner_kp.verifying_key().to_hex(),
            member_lcts: roster.clone(),
            challenge_nonce: nonce.to_string(),
            issued_at,
            claimed_assurance: AssuranceLevel::SingleDevice,
            owner_signature: owner_kp.sign(&payload).to_hex(),
            device_signatures: roster
                .iter()
                .zip(cosigners)
                .map(|(lct, (dt, kp))| DeviceSignature {
                    lct_id: *lct,
                    device_type: dt.clone(),
                    pubkey_hex: kp.verifying_key().to_hex(),
                    signature: kp.sign(&payload).to_hex(),
                })
                .collect(),
        }
    }

    /// One challenge → present round trip on a fixed pair_id. Both calls ride
    /// the same sealed channel the other tools use.
    async fn challenge_and_present(
        state: &RestState,
        me: &KeyPair,
        my_lct: Uuid,
        pid: Uuid,
        att_for_nonce: impl FnOnce(String) -> ConstellationAttestation,
    ) -> Result<serde_json::Value, ApiError> {
        let hub_pub = state.signer.public_key().unwrap();
        let sealed = seal_req(me, &hub_pub, pid, "constellation_challenge", serde_json::json!({}));
        let resp = channel_request(State(state.clone()), Path(state.hub_id), Json(ChannelRequest {
            caller_lct_id: my_lct, pair_id: pid, sealed, caller_pubkey_hex: None,
        })).await?;
        let nonce = open_resp(me, &hub_pub, pid, &resp.0.sealed)["nonce"]
            .as_str().expect("challenge returns a nonce").to_string();

        let att = att_for_nonce(nonce);
        let sealed = seal_req(me, &hub_pub, pid, "present_constellation",
            serde_json::to_value(&att).unwrap());
        let resp = channel_request(State(state.clone()), Path(state.hub_id), Json(ChannelRequest {
            caller_lct_id: my_lct, pair_id: pid, sealed, caller_pubkey_hex: None,
        })).await?;
        Ok(open_resp(me, &hub_pub, pid, &resp.0.sealed))
    }

    /// Review criterion 5: all three tiers derived over the live channel —
    /// the tier comes from verified co-signs (memo rule 5), and each present
    /// burns its challenge so each tier needs a fresh challenge.
    #[tokio::test]
    async fn constellation_three_tiers_over_channel() {
        let (_tmp, state) = fresh_rest_state(None).await; // open admission
        let hub_pub = state.signer.public_key().unwrap();
        let (me, my_lct) = (KeyPair::generate(), Uuid::new_v4());
        let pid0 = Uuid::new_v4();
        let sealed = seal_req(&me, &hub_pub, pid0, "request_citizenship",
            serde_json::json!({ "name": "Constellation Owner" }));
        channel_request(State(state.clone()), Path(state.hub_id), Json(ChannelRequest {
            caller_lct_id: my_lct, pair_id: pid0, sealed,
            caller_pubkey_hex: Some(me.verifying_key().to_hex()),
        })).await.expect("admitted");

        let (k1, k2, khw) = (KeyPair::generate(), KeyPair::generate(), KeyPair::generate());

        // No co-signs → single_device.
        let out = challenge_and_present(&state, &me, my_lct, Uuid::new_v4(), |n|
            make_att(&me, my_lct, &[], &n, chrono::Utc::now())).await.unwrap();
        assert_eq!(out["assurance"], serde_json::json!("single_device"));
        assert!(out["valid_until"].is_string(), "binding carries its validity window");

        // Two device co-signs → multi_device.
        let out = challenge_and_present(&state, &me, my_lct, Uuid::new_v4(), |n|
            make_att(&me, my_lct,
                &[(DeviceType::Desktop, &k1), (DeviceType::Mobile, &k2)], &n, chrono::Utc::now())).await.unwrap();
        assert_eq!(out["assurance"], serde_json::json!("multi_device"));

        // A hardware co-sign → hardware_backed.
        let out = challenge_and_present(&state, &me, my_lct, Uuid::new_v4(), |n|
            make_att(&me, my_lct, &[(DeviceType::Hardware, &khw)], &n, chrono::Utc::now())).await.unwrap();
        assert_eq!(out["assurance"], serde_json::json!("hardware_backed"));
    }

    /// Review criteria 1–3: replay (burned nonce), bad nonce, stale issued_at,
    /// and a foreign owner key (valid channel, someone else's owner key → 403).
    #[tokio::test]
    async fn constellation_reject_paths_over_channel() {
        let (_tmp, state) = fresh_rest_state(None).await;
        let hub_pub = state.signer.public_key().unwrap();
        let (me, my_lct) = (KeyPair::generate(), Uuid::new_v4());
        let pid0 = Uuid::new_v4();
        let sealed = seal_req(&me, &hub_pub, pid0, "request_citizenship",
            serde_json::json!({ "name": "Rejectee" }));
        channel_request(State(state.clone()), Path(state.hub_id), Json(ChannelRequest {
            caller_lct_id: my_lct, pair_id: pid0, sealed,
            caller_pubkey_hex: Some(me.verifying_key().to_hex()),
        })).await.expect("admitted");

        let present = |pid: Uuid, att: ConstellationAttestation| {
            let sealed = seal_req(&me, &hub_pub, pid, "present_constellation",
                serde_json::to_value(&att).unwrap());
            channel_request(State(state.clone()), Path(state.hub_id), Json(ChannelRequest {
                caller_lct_id: my_lct, pair_id: pid, sealed, caller_pubkey_hex: None,
            }))
        };
        let challenge = |pid: Uuid| {
            let sealed = seal_req(&me, &hub_pub, pid, "constellation_challenge", serde_json::json!({}));
            channel_request(State(state.clone()), Path(state.hub_id), Json(ChannelRequest {
                caller_lct_id: my_lct, pair_id: pid, sealed, caller_pubkey_hex: None,
            }))
        };
        let nonce_of = |pid: Uuid, resp: &ChannelResponse| -> String {
            open_resp(&me, &hub_pub, pid, &resp.sealed)["nonce"].as_str().unwrap().to_string()
        };

        // Present with no outstanding challenge → 400.
        let pid = Uuid::new_v4();
        let att = make_att(&me, my_lct, &[], "never-minted", chrono::Utc::now());
        let err = present(pid, att).await.err().expect("no challenge → reject");
        assert_eq!(err.status, StatusCode::BAD_REQUEST);

        // Replay: a valid present succeeds once, the same attestation again
        // finds its nonce burned → 400.
        let pid = Uuid::new_v4();
        let resp = challenge(pid).await.unwrap();
        let att = make_att(&me, my_lct, &[], &nonce_of(pid, &resp.0), chrono::Utc::now());
        present(pid, att.clone()).await.expect("first present succeeds");
        let err = present(pid, att).await.err().expect("replay → reject");
        assert_eq!(err.status, StatusCode::BAD_REQUEST);

        // Wrong nonce → 400 (and the real nonce is burned by the attempt).
        let pid = Uuid::new_v4();
        challenge(pid).await.unwrap();
        let att = make_att(&me, my_lct, &[], "not-the-nonce", chrono::Utc::now());
        let err = present(pid, att).await.err().expect("bad nonce → reject");
        assert_eq!(err.status, StatusCode::BAD_REQUEST);

        // Stale issued_at (outside the 5-min window) → 400.
        let pid = Uuid::new_v4();
        let resp = challenge(pid).await.unwrap();
        let att = make_att(&me, my_lct, &[], &nonce_of(pid, &resp.0),
            chrono::Utc::now() - chrono::Duration::minutes(6));
        let err = present(pid, att).await.err().expect("stale → reject");
        assert_eq!(err.status, StatusCode::BAD_REQUEST);

        // Foreign owner key: correctly signed attestation, but by a key that
        // is NOT this member's pinned key → 403, not a warn-and-accept.
        let pid = Uuid::new_v4();
        let resp = challenge(pid).await.unwrap();
        let foreign = KeyPair::generate();
        let att = make_att(&foreign, my_lct, &[], &nonce_of(pid, &resp.0), chrono::Utc::now());
        let err = present(pid, att).await.err().expect("foreign owner key → reject");
        assert_eq!(err.status, StatusCode::FORBIDDEN);
    }

    /// Admit a member over the sealed channel (pins their key) → returns the
    /// keypair + lct. Shared by the EUDI tests below.
    async fn admit(state: &RestState, name: &str) -> (KeyPair, Uuid) {
        let hub_pub = state.signer.public_key().unwrap();
        let kp = KeyPair::generate();
        let lct = Uuid::new_v4();
        let pid = Uuid::new_v4();
        let sealed = seal_req(&kp, &hub_pub, pid, "request_citizenship", serde_json::json!({ "name": name }));
        channel_request(State(state.clone()), Path(state.hub_id), Json(ChannelRequest {
            caller_lct_id: lct, pair_id: pid, sealed, caller_pubkey_hex: Some(kp.verifying_key().to_hex()),
        })).await.expect("admitted");
        (kp, lct)
    }

    #[tokio::test]
    async fn hub_issues_membership_credential_only_to_a_member() {
        use web4_core::oid4vc::{build_holder_proof, CredentialRequest};
        use web4_core::sd_jwt_vc::verify_issuer;
        let (_tmp, state) = fresh_rest_state(None).await;
        let (alice, alice_lct) = admit(&state, "Alice").await;
        let hub_id = state.hub_id;
        let issuer_url = format!("http://127.0.0.1/v1/hubs/{hub_id}"); // empty-HeaderMap host fallback
        let now = Utc::now().timestamp();
        let h = axum::http::HeaderMap::new;

        // Member flow: nonce → holder proof signed by the MEMBER's pinned key → credential.
        let nonce = vci_nonce(State(state.clone()), Path(hub_id)).await.unwrap().0["c_nonce"]
            .as_str().unwrap().to_string();
        let proof = build_holder_proof(&alice, &issuer_url, &nonce, now);
        let out = vci_credential(State(state.clone()), Path(hub_id), h(),
            Json(CredentialRequest { credential_configuration_id: "Web4Membership".into(), proof_jwt: proof.clone() }))
            .await.expect("member issued a credential");
        // Verifies under the hub's Sovereign key; membership claims present (SD all revealed at issuance).
        let v = verify_issuer(&out.0.credential, &state.signer.public_key().unwrap()).expect("hub sig verifies");
        assert_eq!(v.vct, "Web4Membership");
        assert_eq!(v.claims["sub"], serde_json::json!(web4_core::did::did_web4("127.0.0.1", alice_lct)));
        assert_eq!(v.claims["society"], serde_json::json!(state.hub_name));
        assert_eq!(v.claims["member"], serde_json::json!(true));

        // c_nonce is single-use: replay → 401.
        let replay = vci_credential(State(state.clone()), Path(hub_id), h(),
            Json(CredentialRequest { credential_configuration_id: "Web4Membership".into(), proof_jwt: proof }))
            .await;
        assert!(replay.is_err(), "c_nonce must be single-use");

        // A non-member key (never pinned) cannot pull a credential.
        let stranger = KeyPair::generate();
        let n2 = vci_nonce(State(state.clone()), Path(hub_id)).await.unwrap().0["c_nonce"].as_str().unwrap().to_string();
        let p2 = build_holder_proof(&stranger, &issuer_url, &n2, now);
        let refused = vci_credential(State(state.clone()), Path(hub_id), h(),
            Json(CredentialRequest { credential_configuration_id: "Web4Membership".into(), proof_jwt: p2 }))
            .await;
        assert!(refused.is_err(), "non-member key must be refused");
    }

    #[tokio::test]
    async fn hub_verifies_a_member_issued_presentation_from_the_roster() {
        use web4_core::oid4vc::{build_presentation, PresentationResponse};
        use web4_core::sd_jwt_vc::SdJwtVc;
        let (_tmp, state) = fresh_rest_state(None).await;
        let (alice, alice_lct) = admit(&state, "Alice").await;
        let hub_id = state.hub_id;
        let now = Utc::now().timestamp();
        let h = axum::http::HeaderMap::new;

        // A member self-issues a Web4Presence VC, holder-bound to its own key,
        // issuer = its did:web4 (which the hub can resolve from the roster).
        let issuer_did = web4_core::did::did_web4("127.0.0.1", alice_lct);
        let compact = SdJwtVc::new("Web4Presence", &issuer_did)
            .iat(now)
            .holder_binding(&alice.verifying_key())
            .claim("sub", serde_json::json!(issuer_did))
            .sd_claim("assurance_level", serde_json::json!("multi_device"))
            .issue(&alice, &format!("{issuer_did}#key-0"));

        // Hub mints a VP request; member builds the presentation; hub verifies
        // (resolving the issuer did:web4 → alice's pinned pubkey from the roster).
        let req = vp_request(State(state.clone()), Path(hub_id), h(),
            Json(VpRequestBody { vct: "Web4Presence".into(), required_claims: vec![] })).await.unwrap().0;
        let presentation = build_presentation(&compact, &alice, &req, now).expect("presentation builds");
        let verified = vp_response(State(state.clone()), Path(hub_id), Json(presentation.clone())).await
            .expect("hub verifies a roster-issued presentation");
        assert_eq!(verified.0.vct, "Web4Presence");
        assert_eq!(verified.0.issuer_lct_id, alice_lct);

        // Single-use nonce: replaying the same presentation → 401.
        let replay = vp_response(State(state.clone()), Path(hub_id), Json(presentation)).await;
        assert!(replay.is_err(), "presentation nonce must be single-use");

        // A non-member issuer is rejected even with a valid presentation.
        let stranger = KeyPair::generate();
        let stranger_lct = Uuid::new_v4();
        let s_did = web4_core::did::did_web4("127.0.0.1", stranger_lct);
        let s_compact = SdJwtVc::new("Web4Presence", &s_did)
            .iat(now).holder_binding(&stranger.verifying_key())
            .claim("sub", serde_json::json!(s_did))
            .issue(&stranger, &format!("{s_did}#key-0"));
        let req2 = vp_request(State(state.clone()), Path(hub_id), h(),
            Json(VpRequestBody { vct: "Web4Presence".into(), required_claims: vec![] })).await.unwrap().0;
        let pres2 = build_presentation(&s_compact, &stranger, &req2, now).unwrap();
        let refused = vp_response(State(state.clone()), Path(hub_id), Json::<PresentationResponse>(pres2)).await;
        assert!(refused.is_err(), "non-member issuer must be rejected");
    }

    #[tokio::test]
    async fn locked_vault_refuses_citizen_tier_but_serves_tier0_law() {
        let (_tmp, state) = fresh_rest_state(None).await;
        // Simulate a sealed vault: swap in a LockedSigner (denies all key ops).
        state.signer.swap(Arc::new(LockedSigner::new(state.sovereign_lct_id)));
        assert!(state.is_locked());

        // Citizen-tier sealed channel → 503 (refused before any crypto).
        let req = ChannelRequest {
            caller_lct_id: Uuid::new_v4(),
            pair_id: Uuid::new_v4(),
            sealed: "irrelevant".into(),
            caller_pubkey_hex: None,
        };
        let err = channel_request(State(state.clone()), Path(state.hub_id), Json(req))
            .await
            .err()
            .expect("locked hub must refuse the channel");
        assert_eq!(err.status, StatusCode::SERVICE_UNAVAILABLE);

        // Tier-0 law read still works while locked (law is inspectable without unlock).
        let law = read_hub_law(State(state.clone()), Path(state.hub_id))
            .await
            .expect("law is tier-0 readable while locked");
        assert!(law.0.get("law").is_some());
    }

    /// Seal the hub's Sovereign identity at rest with `pass`, then simulate a
    /// locked startup. Returns the state for unlock-slot tests.
    async fn locked_state_sealed_with(pass: &str) -> (tempfile::TempDir, RestState) {
        let (tmp, state) = fresh_rest_state(None).await;
        let config = hub_lib::hub::HubConfig::load(state.paths.config()).unwrap();
        let lct_path = match config.sovereign.mode().unwrap() {
            SovereignMode::Local { lct_path } => lct_path,
            _ => panic!("expected local-vault mode"),
        };
        IdentityFile::load_auto(&lct_path)
            .unwrap()
            .save_encrypted(&lct_path, pass)
            .unwrap();
        state.signer.swap(Arc::new(LockedSigner::new(state.sovereign_lct_id)));
        assert!(state.is_locked());
        (tmp, state)
    }

    #[tokio::test]
    async fn unlock_slot_promotes_locked_hub_with_the_right_passphrase() {
        let pass = "correct horse battery staple";
        let (_tmp, state) = locked_state_sealed_with(pass).await;
        let now = 1_700_000_000;

        // A wrong passphrase is refused and does NOT unlock.
        assert!(matches!(
            state.try_unlock("nope", now).await,
            UnlockOutcome::WrongPassphrase
        ));
        assert!(state.is_locked(), "a bad guess must not unlock");

        // The right passphrase (past the min interval) promotes the hub in place.
        match state.try_unlock(pass, now + 5).await {
            UnlockOutcome::Unlocked { sovereign_lct_id } => {
                assert_eq!(sovereign_lct_id, state.sovereign_lct_id)
            }
            _ => panic!("the right passphrase must unlock"),
        }
        assert!(!state.is_locked(), "right passphrase promotes locked → unlocked");
        assert!(
            state.signer.public_key().is_some(),
            "the swapped-in real signer exposes the Sovereign pubkey"
        );

        // Idempotent: unlocking an unlocked hub is a no-op.
        assert!(matches!(
            state.try_unlock(pass, now + 10).await,
            UnlockOutcome::NotLocked
        ));
    }

    /// Write a tiny executable stub verifier that returns `granted` and exits 0.
    /// Stands in for the private engine so the public seam can be tested alone.
    fn stub_verifier(dir: &std::path::Path, granted: bool) -> String {
        use std::os::unix::fs::PermissionsExt;
        let path = dir.join("stub-verifier.sh");
        let body = format!(
            "#!/usr/bin/env bash\ncat >/dev/null\necho '{{\"granted\":{granted},\"approvals\":[],\"declines\":[],\"rejected\":0,\"required\":1,\"reason\":\"stub\",\"roster_parse_errors\":0}}'\n"
        );
        std::fs::write(&path, body).unwrap();
        std::fs::set_permissions(&path, std::fs::Permissions::from_mode(0o755)).unwrap();
        path.to_string_lossy().into_owned()
    }

    fn loopback() -> ConnectInfo<SocketAddr> {
        ConnectInfo("127.0.0.1:0".parse().unwrap())
    }

    #[test]
    fn find_members_hits_are_enriched_from_the_registry_not_the_cart() {
        use std::collections::{BTreeMap, BTreeSet};
        let lct = Uuid::new_v4();
        let mut members = BTreeMap::new();
        members.insert(lct, hub_lib::state::Member {
            lct_id: lct,
            name: Some("Sprout".into()),
            skills: BTreeSet::new(),
            profile: BTreeMap::new(),
        });
        // Index-only hits, exactly as the slim cart/sidecar returns them.
        let unknown = Uuid::new_v4();
        let mut hits = vec![
            serde_json::json!({ "member_lct": lct.to_string(), "score": 0.91 }),
            serde_json::json!({ "member_lct": unknown.to_string(), "score": 0.42 }),
        ];
        enrich_member_hits(&mut hits, &members);
        // Known member: name re-attached from the registry; score preserved.
        assert_eq!(hits[0]["name"], serde_json::json!("Sprout"));
        assert_eq!(hits[0]["score"], serde_json::json!(0.91));
        // Unknown LCT: left as index-only (no fabricated name).
        assert!(hits[1].get("name").is_none());
    }

    #[tokio::test]
    async fn notify_citizen_witnesses_a_referenced_act_and_queues_a_sealed_notice() {
        let (_tmp, state) = fresh_rest_state(None).await;
        // Enroll a citizen with a pinned channel pubkey.
        let kp = KeyPair::generate();
        let citizen = Uuid::new_v4();
        witness_event(&state, HubEvent::MemberAdded {
            member_lct_id: citizen,
            added_by: state.sovereign_lct_id,
            member_name: Some("Cit".into()),
            member_pubkey_hex: Some(kp.verifying_key().to_hex()),
        }).await.unwrap();

        // Hub pushes a notification to the citizen.
        notify_citizen(&state, citizen, state.sovereign_lct_id, "notify:test", "ptr/1", b"hello-citizen").await;

        // Queued for delivery (the poll floor) — sealed, addressed, with the act kind + pointer.
        {
            let mb = state.notifications.lock().await;
            let notices = mb.get(&citizen).expect("a notice was queued");
            assert_eq!(notices.len(), 1);
            assert_eq!(notices[0].kind, "notify:test");
            assert_eq!(notices[0].pointer_uri, "ptr/1");
            assert!(!notices[0].sealed.is_empty(), "the body is sealed to the citizen");
        }
        // And witnessed on the ledger as a thin referenced_act (no body on the ledger).
        let ledger = state.ledger.lock().await;
        let kinds: Vec<String> = ledger.entries().iter().map(|e| e.event.kind().to_string()).collect();
        assert!(kinds.contains(&"referenced_act".to_string()));
        // The witnessed act is a verbatim core Act carrying the notify kind, addressed to the
        // citizen, content-bound to the exact body (sha256), with no ciphertext on the ledger.
        let witnessed = ledger.entries().iter().find_map(|e| match &e.event {
            HubEvent::ReferencedAct { act } => Some(act.clone()),
            _ => None,
        }).expect("a referenced_act was witnessed");
        assert_eq!(witnessed.kind, "notify:test");
        assert_eq!(witnessed.address, web4_core::act::ActAddress::Citizen { lct_id: citizen });
        assert_eq!(witnessed.substance.content_hash, web4_core::sha256_hex(b"hello-citizen"));
        // A notice for an unknown (un-pinned) recipient is dropped, not queued.
        drop(ledger);
        notify_citizen(&state, Uuid::new_v4(), state.sovereign_lct_id, "notify:test", "ptr/2", b"x").await;
        assert_eq!(state.notifications.lock().await.len(), 1, "no pinned pubkey → dropped");
    }

    #[tokio::test]
    async fn admin_ledger_tail_is_local_only_and_projects_referenced_acts() {
        let (_tmp, state) = fresh_rest_state(None).await;
        let remote: std::net::SocketAddr = "8.8.8.8:9".parse().unwrap();
        let local: std::net::SocketAddr = "127.0.0.1:9".parse().unwrap();
        let q = || axum::extract::Query(LedgerTailQuery { since: None, limit: Some(50) });

        // Operator plane is local-only: a remote caller is refused.
        assert_eq!(
            admin_ledger_tail(State(state.clone()), ConnectInfo(remote), q())
                .await.err().unwrap().status,
            StatusCode::FORBIDDEN
        );

        // Witness a member→citizen notice; it appears in the tail with who/what/pointer
        // projected from the clear envelope (the sealed body never reaches the ledger).
        let kp = KeyPair::generate();
        let citizen = Uuid::new_v4();
        witness_event(&state, HubEvent::MemberAdded {
            member_lct_id: citizen,
            added_by: state.sovereign_lct_id,
            member_name: Some("Cit".into()),
            member_pubkey_hex: Some(kp.verifying_key().to_hex()),
        }).await.unwrap();
        notify_citizen(&state, citizen, state.sovereign_lct_id, "coordination", "forum/x#thread=t1", b"hi").await;

        let resp = admin_ledger_tail(State(state.clone()), ConnectInfo(local), q()).await.unwrap().0;
        let acts = resp["acts"].as_array().expect("acts array");
        let ra = acts.iter().rev()
            .find(|a| a["event"] == "referenced_act")
            .expect("the referenced_act shows in the tail");
        assert_eq!(ra["act_kind"], "coordination");
        assert_eq!(ra["to_kind"], "citizen");
        assert_eq!(ra["to"], serde_json::json!(citizen));
        assert_eq!(ra["pointer"], "forum/x#thread=t1");
        assert!(resp["total"].as_u64().unwrap() >= 1);
    }

    #[test]
    fn membox_url_locality_is_fail_closed() {
        // H-011: loopback literals pass; anything else (and unparseable) is refused.
        assert!(membox_url_is_local("http://127.0.0.1:8771"));
        assert!(membox_url_is_local("http://localhost:8771"));
        assert!(!membox_url_is_local("http://10.0.0.5:8771"), "LAN host refused");
        assert!(!membox_url_is_local("https://evil.example/find"), "remote refused");
        assert!(!membox_url_is_local("not a url"), "unparseable is fail-closed");
    }

    #[tokio::test]
    async fn tier2_unlock_is_na_without_a_verifier_plugin() {
        let (_tmp, mut state) = fresh_rest_state(None).await;
        state.unlock_verifier_cmd = None; // no plugin installed
        let err = unlock_challenge(loopback(), State(state.clone()), Path(state.hub_id), Json(ChallengeReq { tier: "protected".into() }))
            .await
            .err()
            .expect("tier-2 must be N/A with no verifier");
        assert_eq!(err.status, StatusCode::NOT_IMPLEMENTED);
    }

    #[tokio::test]
    async fn tier2_unlock_challenge_then_quorum_grant_is_witnessed() {
        let (tmp, mut state) = fresh_rest_state(None).await;
        state.unlock_verifier_cmd = Some(stub_verifier(tmp.path(), true));

        // Enroll one council admin so the roster is non-empty (witnessed act).
        let admin = Uuid::new_v4();
        witness_event(&state, HubEvent::CouncilMemberAdded {
            member_lct_id: admin,
            member_pubkey_hex: "00".repeat(32),
            added_by: state.sovereign_lct_id,
            member_name: Some("Admin One".into()),
        })
        .await
        .unwrap();

        // Mint a challenge.
        let ch = unlock_challenge(loopback(), State(state.clone()), Path(state.hub_id), Json(ChallengeReq { tier: "channel-keys".into() }))
            .await
            .expect("challenge issued")
            .0;
        assert_eq!(ch.roster, vec![admin]);
        assert!(ch.required >= 1);

        // An admin attests → the (stub) verifier grants → resolved + witnessed.
        let att = serde_json::json!({ "admin_lct": admin, "decision": "approve" });
        let resp = unlock_attest(State(state.clone()), Path(state.hub_id), Json(AttestReq { challenge_id: ch.challenge_id, attestation: att }))
            .await
            .expect("attest accepted")
            .0;
        assert!(resp.granted, "stub verifier grants: {}", resp.reason);

        // The flow was witnessed: requested + attested + resolved are on the ledger.
        let ledger = state.ledger.lock().await;
        let kinds: Vec<String> = ledger.entries().iter().map(|e| e.event.kind().to_string()).collect();
        assert!(kinds.contains(&"vault_unlock_requested".to_string()));
        assert!(kinds.contains(&"vault_unlock_attested".to_string()));
        assert!(kinds.contains(&"vault_unlock_resolved".to_string()));
    }

    #[tokio::test]
    async fn unlock_slot_rate_limits_repeated_wrong_guesses() {
        let pass = "open sesame";
        let (_tmp, state) = locked_state_sealed_with(pass).await;

        // Five consecutive wrong guesses (each past the 2 s min interval).
        let mut t = 1_700_000_000;
        for _ in 0..5 {
            assert!(matches!(
                state.try_unlock("wrong", t).await,
                UnlockOutcome::WrongPassphrase
            ));
            t += 3;
        }
        // The 6th attempt is locked out — even with the CORRECT passphrase.
        match state.try_unlock(pass, t).await {
            UnlockOutcome::RateLimited { retry_after_secs } => assert!(retry_after_secs > 0),
            _ => panic!("expected a lockout after 5 consecutive failures"),
        }
        assert!(state.is_locked(), "lockout holds the vault closed");
    }
}
