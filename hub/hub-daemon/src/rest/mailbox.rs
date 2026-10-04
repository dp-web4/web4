// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Metalinxx Inc.

//! Durable mailbox operations. The notifications mutex serializes each complete
//! read/modify/commit; the store, not the hydrated RAM cache, is authoritative.
use super::*;
use hub_lib::store::HubStore;
use sha2::{Digest, Sha256};

pub(super) const RECEIVE_PROTOCOL: &str = "hub-mailbox-receive-v1";

/// How long an ACK tombstone is kept. A tombstone exists for ONE reason: a retried ACK (its
/// response was lost, or the daemon restarted) must answer "acknowledged" rather than 404. It
/// is not what keeps a notice from coming back — a notice ID hashes its committed timestamp,
/// so an ACKed notice cannot recur. So tombstones are bounded by age and count, and an ACK
/// FREES its slot (web4#867 item 5: expiry is explicit, never receipt; and the retention bound
/// must not end a member's inbound mail).
pub(super) const TOMBSTONE_WINDOW_SECS: i64 = 7 * 24 * 3600;
pub(super) const MAX_TOMBSTONES: usize = 4096;

/// How long a sender's `operation_id` is remembered. A retry inside the window gets the first
/// attempt's receipt; after it, the same id is a new send. Declared, not implied (#867).
pub(super) const SEND_OP_WINDOW_SECS: i64 = 7 * 24 * 3600;

/// Serializes operator enrollment (preflight + witness + write). See
/// `enable_mailbox_receipts_as_operator`.
pub(super) static ENROLL_LOCK: tokio::sync::Mutex<()> = tokio::sync::Mutex::const_new(());

/// Serializes an operation-id send through its entire queued -> witnessed -> completed
/// transition. This is intentionally coarse for v1: one daemon owns the mailbox store, and
/// correctness beats parallel sender throughput. Completed replays are cheap; a later
/// operation-keyed lock can narrow this without changing the protocol. The important property
/// is that a second twin cannot land the same act or withdraw a notice after the first twin
/// completed it.
pub(super) static SEND_OP_LOCK: tokio::sync::Mutex<()> = tokio::sync::Mutex::const_new(());

/// A mailbox operation's failure, split by WHO must act on it. A caller's retry logic
/// treats a 5xx as transient; a protocol refusal ("not enrolled", "bad id", "mailbox
/// full") is not, and returning it as 500 teaches the caller to retry forever.
#[derive(Debug)]
pub(super) enum MailboxError {
    /// The request is refused by the protocol; retrying it unchanged cannot succeed.
    Refused(StatusCode, String),
    /// The store could not be read or written; nothing changed, and a retry may succeed.
    Store(anyhow::Error),
}
impl From<anyhow::Error> for MailboxError {
    fn from(e: anyhow::Error) -> Self { Self::Store(e) }
}
impl From<serde_json::Error> for MailboxError {
    fn from(e: serde_json::Error) -> Self { Self::Store(e.into()) }
}
impl std::fmt::Display for MailboxError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self { Self::Refused(_, m) => f.write_str(m), Self::Store(e) => write!(f, "{e:#}") }
    }
}
impl From<MailboxError> for ApiError {
    fn from(e: MailboxError) -> Self {
        match e {
            MailboxError::Refused(status, message) => ApiError { status, message },
            MailboxError::Store(e) => ApiError::internal(e),
        }
    }
}
pub(super) fn refused<T>(status: StatusCode, msg: impl Into<String>) -> Result<T, MailboxError> {
    Err(MailboxError::Refused(status, msg.into()))
}
fn require_durable(store: &dyn HubStore) -> Result<(), MailboxError> {
    if store.mailbox_is_durable() { return Ok(()); }
    // The deployment cannot offer the protocol at all: not the caller's error, not transient.
    refused(StatusCode::NOT_IMPLEMENTED, "receipt delivery requires durable mailbox storage")
}

#[derive(Clone, Serialize, Deserialize, PartialEq)]
#[serde(deny_unknown_fields)]
pub(super) struct Tombstone {
    id: String,
    /// Unix seconds of the ACK.
    at: i64,
}

#[derive(Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub(super) struct ReceiptMailbox {
    protocol: String,
    pub notices: Vec<SealedNotice>,
    acked: Vec<Tombstone>,
}
impl ReceiptMailbox {
    /// Drop tombstones past the window, then the oldest beyond the count bound.
    fn prune_tombstones(&mut self, now: i64) {
        self.acked.retain(|t| t.at >= now - TOMBSTONE_WINDOW_SECS);
        if self.acked.len() > MAX_TOMBSTONES {
            let excess = self.acked.len() - MAX_TOMBSTONES;
            self.acked.drain(..excess);
        }
    }
}

// Old Vec blobs are read in place; only explicit enrollment changes their format.
#[derive(Clone, Serialize, Deserialize)]
#[serde(untagged)]
pub(super) enum Mailbox {
    Legacy(Vec<SealedNotice>),
    Receipts(ReceiptMailbox),
}
impl Mailbox {
    pub fn decode(bytes: &[u8]) -> Result<Self> {
        let record: Self = serde_json::from_slice(bytes)?;
        if let Self::Receipts(r) = &record {
            anyhow::ensure!(r.protocol == RECEIVE_PROTOCOL, "unknown mailbox protocol");
            anyhow::ensure!(r.notices.len() <= MAX_NOTICES_PER_MEMBER && r.acked.len() <= MAX_TOMBSTONES,
                "receipt mailbox exceeds retention bound");
        }
        Ok(record)
    }
    pub fn notices(&self) -> &Vec<SealedNotice> {
        match self { Self::Legacy(q) => q, Self::Receipts(r) => &r.notices }
    }
    pub fn notices_mut(&mut self) -> &mut Vec<SealedNotice> {
        match self { Self::Legacy(q) => q, Self::Receipts(r) => &mut r.notices }
    }
    pub fn is_receipts(&self) -> bool { matches!(self, Self::Receipts(_)) }
    /// Pending notices only. Tombstones are pruned and never hold a slot.
    pub fn full(&self) -> bool {
        matches!(self, Self::Receipts(r) if r.notices.len() >= MAX_NOTICES_PER_MEMBER)
    }
}

pub(super) fn notice_id(recipient: Uuid, notice: &SealedNotice) -> String {
    // Fixed struct field order, domain separated, recipient bound. Includes the
    // committed timestamp: two distinct queue entries never share an ACK by pair_id.
    let bytes = serde_json::to_vec(&(RECEIVE_PROTOCOL, recipient, notice)).expect("notice JSON");
    hex::encode(Sha256::digest(bytes))
}

/// A sender's `send_secret` operation, committed in the SAME transaction as the notice it
/// queued. `binding` is what the operation id stands for; a retry must match it.
#[derive(Clone, Serialize, Deserialize, PartialEq, Debug)]
#[serde(deny_unknown_fields)]
pub(super) struct SendOp {
    pub binding: serde_json::Value,
    pub act_id: Uuid,
    pub notice_id: String,
    pub created_at: i64,
    /// `None` until the act lands on the ledger. A retry of an op left here (the daemon died
    /// between queueing and witnessing) finds the act by `act_id`, or witnesses it then.
    pub entry_index: Option<u64>,
    pub durable: bool,
}

/// The id of the act a `(sender, operation_id)` witnesses — deterministic, so a retry after a
/// crash can find the act on the ledger instead of witnessing a second one.
pub(super) fn op_act_id(sender: Uuid, op_id: &str) -> Uuid {
    let d = Sha256::digest(format!("web4-hub/send-op/v1\0{sender}\0{op_id}").as_bytes());
    let mut b = [0u8; 16];
    b.copy_from_slice(&d[..16]);
    Uuid::from_bytes(b)
}

pub(super) fn check_op_id(op_id: &str) -> Result<(), MailboxError> {
    let ok = (1..=128).contains(&op_id.len())
        && op_id.bytes().all(|b| b.is_ascii_alphanumeric() || matches!(b, b'-' | b'_' | b'.' | b':'));
    if ok { Ok(()) } else {
        refused(StatusCode::BAD_REQUEST, "operation_id must be 1-128 of [A-Za-z0-9._:-]")
    }
}

impl RestState {
    /// Withdraw a notice this call queued whose act could not be witnessed, and its op record,
    /// in one transaction. -> `Ok(true)` withdrawn; `Ok(false)` it is no longer queued (already
    /// drained or ACKed — delivered), so it cannot be withdrawn and the op record is kept for
    /// the retry that completes its act.
    pub(super) async fn mailbox_withdraw(
        &self, recipient: Uuid, id: &str, op: Option<(Uuid, &str)>,
    ) -> Result<bool, MailboxError> {
        let mut cache = self.notifications.lock().await;
        let mut store = self.open_store().await?;
        let cached = cache.get(&recipient).map(Vec::as_slice).unwrap_or(&[]);
        let mut record = self.load_mailbox_record(&*store, recipient, cached).await?;

        // A completed operation owns its notice permanently until the RECIPIENT ACKs it.
        // Never let a losing/error path erase custody after another attempt landed the act.
        if let Some((sender, op_id)) = op {
            if let Some(bytes) = store.send_op_get(sender, op_id).await? {
                let existing: SendOp = serde_json::from_slice(&bytes)?;
                if existing.entry_index.is_some() {
                    return Ok(false);
                }
            }
        }

        let Some(index) = record.notices().iter().position(|n| notice_id(recipient, n) == id) else {
            return Ok(false);
        };
        record.notices_mut().remove(index);
        let blob = serde_json::to_vec(&record)?;
        match op {
            Some((sender, op_id)) => store.mailbox_commit_with_op(recipient, Some(&blob),
                Some((sender, op_id, 0, None)), Utc::now().timestamp() - SEND_OP_WINDOW_SECS).await?,
            None => store.mailbox_put(recipient, &blob).await?,
        }
        cache.insert(recipient, record.notices().clone());
        Ok(true)
    }

    pub(super) async fn load_mailbox_record(
        &self, store: &dyn HubStore, recipient: Uuid, cached: &[SealedNotice],
    ) -> Result<Mailbox> {
        if !store.mailbox_is_durable() { return Ok(Mailbox::Legacy(cached.to_vec())); }
        // Authoritative state over a cache that may have failed hydration, read for
        // THIS recipient only: another member's unreadable row is not this one's outage.
        match store.mailbox_get(recipient).await? {
            Some(bytes) => Mailbox::decode(&bytes),
            None => Ok(Mailbox::Legacy(Vec::new())),
        }
    }

    /// Enroll `recipient` in receipt delivery. An OPERATOR act, reached only from the
    /// loopback admin plane (`POST /admin/api/members/:lct_id/mailbox-receipts`), never from
    /// the member channel: enrollment is one-way (no downgrade, older binaries cannot read the
    /// record), and it moves the member from consume-on-poll to fetch/ACK — a member whose
    /// client never ACKs stops receiving at `MAX_NOTICES_PER_MEMBER` unacknowledged notices.
    /// A door that cannot be closed again is admission-shaped.
    ///
    /// -> `Ok(true)` when this call enrolled, `Ok(false)` when already enrolled (idempotent).
    pub(super) async fn mailbox_enable_receipts(&self, recipient: Uuid) -> Result<bool, MailboxError> {
        let mut cache = self.notifications.lock().await;
        let mut store = self.open_store().await?;
        require_durable(&*store)?;
        let record = self.load_mailbox_record(&*store, recipient, &[]).await?;
        let record = match record {
            Mailbox::Legacy(notices) => Mailbox::Receipts(ReceiptMailbox {
                protocol: RECEIVE_PROTOCOL.into(), notices, acked: Vec::new(),
            }),
            Mailbox::Receipts(_) => return Ok(false),
        };
        store.mailbox_put(recipient, &serde_json::to_vec(&record)?).await?;
        cache.insert(recipient, record.notices().clone());
        Ok(true)
    }

    pub(super) async fn mailbox_fetch(&self, recipient: Uuid, limit: usize) -> Result<serde_json::Value, MailboxError> {
        if !(1..=100).contains(&limit) {
            return refused(StatusCode::BAD_REQUEST, "limit must be between 1 and 100");
        }
        let _guard = self.notifications.lock().await;
        let store = self.open_store().await?;
        require_durable(&*store)?;
        let record = self.load_mailbox_record(&*store, recipient, &[]).await?;
        if !record.is_receipts() {
            return refused(StatusCode::CONFLICT,
                "receipt delivery is not enabled for this member; enrollment is an operator act");
        }
        let notices: Vec<_> = record.notices().iter().take(limit).map(|notice|
            serde_json::json!({"id": notice_id(recipient, notice), "notice": notice})).collect();
        Ok(serde_json::json!({"protocol": RECEIVE_PROTOCOL, "notifications": notices,
            "remaining": record.notices().len().saturating_sub(limit)}))
    }

    pub(super) async fn mailbox_ack(&self, recipient: Uuid, id: &str) -> Result<serde_json::Value, MailboxError> {
        if !(id.len() == 64 && id.bytes().all(|b| b.is_ascii_hexdigit())) {
            return refused(StatusCode::BAD_REQUEST, "invalid notice id: 64 hex characters");
        }
        let mut cache = self.notifications.lock().await;
        let mut store = self.open_store().await?;
        require_durable(&*store)?;
        let mut record = self.load_mailbox_record(&*store, recipient, &[]).await?;
        let Mailbox::Receipts(r) = &mut record else {
            return refused(StatusCode::CONFLICT,
                "receipt delivery is not enabled for this member; enrollment is an operator act");
        };
        let now = Utc::now().timestamp();
        let held = r.acked.len();
        r.prune_tombstones(now);
        let mut dirty = r.acked.len() != held;
        if !r.acked.iter().any(|old| old.id == id) {
            let Some(index) = r.notices.iter().position(|n| notice_id(recipient, n) == id) else {
                return refused(StatusCode::NOT_FOUND, format!(
                    "notice is not in this recipient's mailbox — never queued here, or ACKed more \
                     than {} days ago (tombstones are kept that long)", TOMBSTONE_WINDOW_SECS / 86400));
            };
            r.notices.remove(index);
            r.acked.push(Tombstone { id: id.to_owned(), at: now });
            r.prune_tombstones(now);
            dirty = true;
        }
        // A retried ACK changes nothing of its own, but expired tombstones it pruned must not
        // survive on disk for want of a write.
        if dirty {
            store.mailbox_put(recipient, &serde_json::to_vec(&record)?).await?;
            cache.insert(recipient, record.notices().clone());
        }
        Ok(serde_json::json!({"protocol": RECEIVE_PROTOCOL, "id": id,
            "acknowledged": true, "completed": false}))
    }

    pub(super) async fn mailbox_legacy_drain(&self, recipient: Uuid) -> Result<Vec<SealedNotice>, MailboxError> {
        let mut cache = self.notifications.lock().await;
        let mut store = self.open_store().await?;
        let cached = cache.get(&recipient).map(Vec::as_slice).unwrap_or(&[]);
        let record = self.load_mailbox_record(&*store, recipient, cached).await?;
        if record.is_receipts() {
            return refused(StatusCode::CONFLICT,
                "legacy drain disabled for this member: use notifications_fetch and notifications_ack");
        }
        // Legacy semantics remain consume-on-response, explicitly NOT the receipt
        // contract. Keep its deletion ordered with enqueue so it cannot erase a new send.
        store.mailbox_delete(recipient).await?;
        cache.remove(&recipient);
        let cutoff = Utc::now() - chrono::Duration::seconds(NOTICE_TTL_SECS);
        Ok(record.notices().iter().filter(|n| n.queued_at >= cutoff).cloned().collect())
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use hub_lib::{identity::IdentityFile, init::{init_hub, InitArgs}, ledger::HubLedger,
        store::{open_hub_store, BackendKind}};
    use web4_core::{lct::EntityType, pair_channel};

    async fn fixture(durable: bool) -> (tempfile::TempDir, RestState, IdentityFile) {
        let tmp = tempfile::tempdir().unwrap();
        let sovereign = IdentityFile::generate(EntityType::Human);
        let key = tmp.path().join("sovereign.json");
        sovereign.save(&key).unwrap();
        let root = tmp.path().join("hub");
        init_hub(InitArgs { hub_name: "Receipt tests".into(), hub_dir: root.clone(),
            sovereign_lct_path: key, storage: if durable { Some(BackendKind::Sqlite) } else { None },
            dynamodb: None }).await.unwrap();
        let state = reopen(&root).await;
        (tmp, state, sovereign)
    }
    async fn reopen(root: &std::path::Path) -> RestState {
        let ledger = HubLedger::open(open_hub_store(root).unwrap()).await.unwrap();
        RestState::open_with_law_and_ledger(root.to_owned(),
            Arc::new(tokio::sync::RwLock::new(None)), Arc::new(Mutex::new(ledger))).await.unwrap()
    }
    fn notice() -> SealedNotice {
        SealedNotice { pair_id: Uuid::new_v4(), from: Uuid::new_v4(), sealed: "opaque".into(),
            kind: "test".into(), pointer_uri: "test".into(), queued_at: Utc::now(), sealed_by: None }
    }
    fn sql(tmp: &tempfile::TempDir, query: &str) {
        rusqlite::Connection::open(tmp.path().join("hub/hub.db")).unwrap().execute_batch(query).unwrap();
    }
    async fn channel(state: &RestState, identity: &IdentityFile, tool: &str,
        args: serde_json::Value, fresh: bool) -> Result<serde_json::Value, ApiError> {
        let pair = Uuid::new_v4();
        let key = identity.keypair().unwrap();
        let hub = state.signer.public_key().unwrap();
        let mut inner = serde_json::json!({"tool": tool, "args": args});
        if fresh {
            inner["nonce"] = serde_json::json!(Uuid::new_v4().to_string());
            inner["issued_at"] = serde_json::json!(Utc::now().to_rfc3339());
        }
        let sealed = pair_channel::seal(&key, &hub, pair, &serde_json::to_vec(&inner).unwrap()).unwrap().to_base64();
        let reply = channel_request(State(state.clone()), Path(state.hub_id), Json(ChannelRequest {
            caller_lct_id: identity.lct.id, pair_id: pair, sealed, caller_pubkey_hex: None,
        })).await?;
        let sealed = pair_channel::Sealed::from_base64(&reply.0.sealed).unwrap();
        let plain = pair_channel::open(&key, &hub, pair, &sealed).unwrap();
        Ok(serde_json::from_slice(&plain).unwrap())
    }

    #[tokio::test]
    async fn receipt_send_secret_never_accepts_failed_store_without_optin() {
        let (tmp, state, sov) = fixture(true).await;
        sql(&tmp, "CREATE TRIGGER refuse_mailbox BEFORE INSERT ON mailbox BEGIN SELECT RAISE(FAIL, 'injected write failure'); END;");
        let args = serde_json::json!({"to": sov.lct.id, "sealed": "opaque",
            "pair_id": Uuid::new_v4(), "content_hash": format!("sha256-content:{}", "a".repeat(64))});
        assert!(channel(&state, &sov, "send_secret", args, true).await.is_err(),
            "failed mailbox persistence must not return delivered:true, even for an unenrolled legacy mailbox");
    }

    #[tokio::test]
    async fn receipt_fetch_restart_lost_ack_and_legacy_refusal() {
        let (tmp, state, _) = fixture(true).await;
        let who = Uuid::new_v4();
        // Compatibility: begin with the original Vec blob, then explicitly enroll.
        let n = notice();
        state.open_store().await.unwrap().mailbox_put(who, &serde_json::to_vec(&vec![n]).unwrap()).await.unwrap();
        assert!(state.mailbox_fetch(who, 100).await.is_err());
        state.mailbox_enable_receipts(who).await.unwrap();
        let first = state.mailbox_fetch(who, 100).await.unwrap();
        let restart = reopen(&tmp.path().join("hub")).await; // deliberately no hydration
        assert_eq!(restart.mailbox_fetch(who, 100).await.unwrap(), first, "lost fetch response survives restart");
        assert!(restart.mailbox_legacy_drain(who).await.is_err());
        let id = first["notifications"][0]["id"].as_str().unwrap();
        let ack = restart.mailbox_ack(who, id).await.unwrap(); // discard response
        let again = reopen(&tmp.path().join("hub")).await;
        assert_eq!(again.mailbox_ack(who, id).await.unwrap(), ack, "lost ACK response is retryable");
        assert_eq!(ack["completed"], false);
        assert_eq!(again.mailbox_fetch(who, 100).await.unwrap()["notifications"], serde_json::json!([]));
        assert!(again.mailbox_legacy_drain(who).await.is_err(), "empty mailbox retains receipt mode");
    }

    #[tokio::test]
    async fn receipt_failed_enqueue_and_ack_do_not_change_ram_or_disk() {
        let (tmp, state, _) = fixture(true).await;
        let who = Uuid::new_v4();
        state.mailbox_enable_receipts(who).await.unwrap();
        enqueue_notice(&state, who, notice()).await.unwrap();
        let before = state.mailbox_fetch(who, 100).await.unwrap();
        sql(&tmp, "CREATE TRIGGER refuse_mailbox BEFORE INSERT ON mailbox BEGIN SELECT RAISE(FAIL, 'injected write failure'); END;");
        assert!(enqueue_notice(&state, who, notice()).await.is_err());
        assert!(state.mailbox_ack(who, before["notifications"][0]["id"].as_str().unwrap()).await.is_err());
        assert_eq!(state.notifications.lock().await[&who].len(), 1);
        assert_eq!(state.mailbox_fetch(who, 100).await.unwrap(), before);
        assert_eq!(reopen(&tmp.path().join("hub")).await.mailbox_fetch(who, 100).await.unwrap(), before);
    }

    #[tokio::test]
    async fn receipt_send_secret_reports_store_failure_through_real_channel() {
        let (tmp, state, sov) = fixture(true).await;
        state.mailbox_enable_receipts(sov.lct.id).await.unwrap();
        let args = serde_json::json!({"to": sov.lct.id, "sealed": "opaque",
            "pair_id": Uuid::new_v4(), "content_hash": format!("sha256-content:{}", "a".repeat(64))});
        let ok = channel(&state, &sov, "send_secret", args.clone(), true).await.unwrap();
        assert_eq!(ok["durably_accepted"], true);
        let before = state.mailbox_fetch(sov.lct.id, 100).await.unwrap();
        sql(&tmp, "CREATE TRIGGER refuse_mailbox BEFORE INSERT ON mailbox BEGIN SELECT RAISE(FAIL, 'injected write failure'); END;");
        assert!(channel(&state, &sov, "send_secret", args, true).await.is_err(), "failed persistence cannot return delivered:true");
        assert_eq!(state.mailbox_fetch(sov.lct.id, 100).await.unwrap(), before);
        assert_eq!(reopen(&tmp.path().join("hub")).await.mailbox_fetch(sov.lct.id, 100).await.unwrap(), before);
    }

    #[tokio::test]
    async fn receipt_failed_enrollment_preserves_legacy_queue() {
        let (tmp, state, _) = fixture(true).await;
        let who = Uuid::new_v4();
        enqueue_notice(&state, who, notice()).await.unwrap();
        sql(&tmp, "CREATE TRIGGER refuse_mailbox BEFORE INSERT ON mailbox BEGIN SELECT RAISE(FAIL, 'injected write failure'); END;");
        assert!(state.mailbox_enable_receipts(who).await.is_err());
        assert!(state.mailbox_fetch(who, 100).await.is_err());
        assert_eq!(state.mailbox_legacy_drain(who).await.unwrap().len(), 1);
    }

    #[tokio::test]
    async fn receipt_concurrent_ack_and_enqueue_preserve_new_notice() {
        let (tmp, state, _) = fixture(true).await;
        let who = Uuid::new_v4();
        state.mailbox_enable_receipts(who).await.unwrap();
        let old = notice(); let id = notice_id(who, &old);
        enqueue_notice(&state, who, old).await.unwrap();
        let next = notice(); let next_id = notice_id(who, &next);
        let (ack, sent) = tokio::join!(state.mailbox_ack(who, &id), enqueue_notice(&state, who, next));
        ack.unwrap(); sent.unwrap();
        let out = reopen(&tmp.path().join("hub")).await.mailbox_fetch(who, 100).await.unwrap();
        assert_eq!(out["notifications"].as_array().unwrap().len(), 1);
        assert_eq!(out["notifications"][0]["id"], next_id);
    }

    #[tokio::test]
    async fn receipt_channel_binds_ack_to_authenticated_recipient_and_requires_freshness() {
        let (_tmp, state, sov) = fixture(true).await;
        let who = sov.lct.id;
        // Enrollment is an operator act: the member channel refuses it even fresh, and says where.
        let e = channel(&state, &sov, "notifications_enable_receipts", serde_json::json!({}), true).await.unwrap_err();
        assert_eq!(e.status, StatusCode::FORBIDDEN);
        assert!(e.message.contains("/mailbox-receipts"), "{}", e.message);
        assert!(state.mailbox_fetch(who, 100).await.is_err(), "a refused self-enrollment changed nothing");
        state.mailbox_enable_receipts(who).await.unwrap();
        enqueue_notice(&state, who, notice()).await.unwrap();
        let out = channel(&state, &sov, "notifications_fetch", serde_json::json!({}), false).await.unwrap();
        let id = out["notifications"][0]["id"].as_str().unwrap();
        assert!(channel(&state, &sov, "notifications_ack", serde_json::json!({"id":id}), false).await.is_err());
        let other = Uuid::new_v4();
        state.mailbox_enable_receipts(other).await.unwrap();
        let n = notice(); let other_id = notice_id(other, &n);
        enqueue_notice(&state, other, n).await.unwrap();
        assert!(channel(&state, &sov, "notifications_ack", serde_json::json!({"id":other_id,"recipient":other}), true).await.is_err());
        assert_eq!(state.mailbox_fetch(other, 100).await.unwrap()["notifications"].as_array().unwrap().len(),1);
        channel(&state, &sov, "notifications_ack", serde_json::json!({"id":id}), true).await.unwrap();
        assert!(channel(&state, &sov, "notifications", serde_json::json!({}), false).await.is_err());
    }

    #[tokio::test]
    async fn receipt_non_durable_and_corrupt_store_fail_closed() {
        let (_tmp, state, _) = fixture(false).await;
        let who = Uuid::new_v4();
        assert!(state.mailbox_enable_receipts(who).await.is_err());
        assert!(state.mailbox_fetch(who, 100).await.is_err());
        assert!(!enqueue_notice(&state, who, notice()).await.unwrap(), "RAM delivery cannot claim durable acceptance");
        let (_tmp, state, _) = fixture(true).await;
        state.open_store().await.unwrap().mailbox_put(who, b"corrupt").await.unwrap();
        assert!(state.mailbox_enable_receipts(who).await.is_err());
        assert!(enqueue_notice(&state, who, notice()).await.is_err(), "failed hydration must not erase unread disk state");
        assert!(state.mailbox_legacy_drain(who).await.is_err());
    }

    #[tokio::test]
    async fn receipt_retention_bound_refuses_instead_of_evicting() {
        let (_tmp, state, _) = fixture(true).await;
        let who = Uuid::new_v4();
        let mut old = notice(); old.queued_at = Utc::now() - chrono::Duration::days(30);
        let mut notices = vec![old];
        notices.extend((1..MAX_NOTICES_PER_MEMBER).map(|_| notice()));
        let record = Mailbox::Receipts(ReceiptMailbox { protocol: RECEIVE_PROTOCOL.into(), notices, acked: vec![] });
        state.open_store().await.unwrap().mailbox_put(who, &serde_json::to_vec(&record).unwrap()).await.unwrap();
        assert!(enqueue_notice(&state, who, notice()).await.is_err());
        let out = state.mailbox_fetch(who, 100).await.unwrap();
        assert_eq!(out["remaining"], 900);
        assert_eq!(out["notifications"][0]["id"], notice_id(who, &record.notices()[0]), "no TTL deletion in receipt mode");
        state.mailbox_ack(who, out["notifications"][0]["id"].as_str().unwrap()).await.unwrap();
        // #867 item 5: an ACK frees its slot — the bound can no longer end a member's inbound mail.
        assert!(enqueue_notice(&state, who, notice()).await.is_ok(), "an ACK frees a slot");
        assert!(enqueue_notice(&state, who, notice()).await.is_err(), "and only one");
    }

    /// Tombstones exist so a RETRIED ack answers "acknowledged"; they are bounded by age and
    /// count, and one past the window answers 404 with the reason.
    #[tokio::test]
    async fn receipt_tombstones_expire_by_age_and_count() {
        let (_tmp, state, _) = fixture(true).await;
        let who = Uuid::new_v4();
        let now = Utc::now().timestamp();
        let (fresh, stale) = (notice(), notice());
        let (fresh_id, stale_id) = (notice_id(who, &fresh), notice_id(who, &stale));
        let mut acked: Vec<Tombstone> = (0..MAX_TOMBSTONES - 1)
            .map(|i| Tombstone { id: format!("{i:064x}"), at: now - 60 }).collect();
        acked.push(Tombstone { id: stale_id.clone(), at: now - TOMBSTONE_WINDOW_SECS - 1 });
        acked.push(Tombstone { id: fresh_id.clone(), at: now - 60 });
        let record = Mailbox::Receipts(ReceiptMailbox { protocol: RECEIVE_PROTOCOL.into(), notices: vec![], acked });
        // one over the count bound is refused as a stored record (decode bound) ...
        state.open_store().await.unwrap().mailbox_put(who, &serde_json::to_vec(&record).unwrap()).await.unwrap();
        assert!(state.mailbox_fetch(who, 100).await.is_err(), "a record past the tombstone bound does not load");
        // ... so store one within it, and let an ACK prune the stale one.
        let Mailbox::Receipts(mut r) = record else { unreachable!() };
        r.acked.remove(0);
        state.open_store().await.unwrap().mailbox_put(who, &serde_json::to_vec(&Mailbox::Receipts(r)).unwrap()).await.unwrap();
        assert_eq!(state.mailbox_ack(who, &fresh_id).await.unwrap()["acknowledged"], true, "a retried ACK inside the window");
        assert_eq!(status(state.mailbox_ack(who, &stale_id).await), StatusCode::NOT_FOUND, "past the window");
        let bytes = state.open_store().await.unwrap().mailbox_get(who).await.unwrap().unwrap();
        let Mailbox::Receipts(after) = Mailbox::decode(&bytes).unwrap() else { unreachable!() };
        assert!(after.acked.iter().all(|t| t.id != stale_id), "the stale tombstone was pruned on write");
    }

    // ---- send_secret: the ledger never asserts a send the mailbox refused (#867 contract 1) ----

    fn secret_args(to: Uuid, sealed: &str, op: Option<&str>) -> serde_json::Value {
        secret_args_with_pair(to, sealed, op, Uuid::from_u128(0x1210))
    }
    fn secret_args_with_pair(
        to: Uuid, sealed: &str, op: Option<&str>, pair_id: Uuid,
    ) -> serde_json::Value {
        let mut a = serde_json::json!({"to": to, "sealed": sealed, "pair_id": pair_id,
            "content_hash": format!("sha256-content:{}", "a".repeat(64))});
        if let Some(op) = op { a["operation_id"] = serde_json::json!(op); }
        a
    }
    async fn ledger_len(s: &RestState) -> usize { s.ledger.lock().await.len() }
    async fn queued(s: &RestState, who: Uuid) -> usize {
        let store = s.open_store().await.unwrap();
        s.load_mailbox_record(&*store, who, &[]).await.unwrap().notices().len()
    }

    #[tokio::test]
    async fn a_refused_send_leaves_no_act_on_the_ledger() {
        let (tmp, state, sov) = fixture(true).await;
        let before = ledger_len(&state).await;
        sql(&tmp, "CREATE TRIGGER refuse_mailbox BEFORE INSERT ON mailbox BEGIN SELECT RAISE(FAIL, 'injected'); END;");
        assert!(channel(&state, &sov, "send_secret", secret_args(sov.lct.id, "s", None), true).await.is_err());
        assert_eq!(ledger_len(&state).await, before, "a refused send witnessed an act");
    }

    #[tokio::test]
    async fn an_act_that_cannot_land_withdraws_its_notice() {
        let (tmp, state, sov) = fixture(true).await;
        let (before, q0) = (ledger_len(&state).await, queued(&state, sov.lct.id).await);
        sql(&tmp, "CREATE TRIGGER refuse_ledger BEFORE INSERT ON ledger_entries BEGIN SELECT RAISE(FAIL, 'injected'); END;");
        let e = channel(&state, &sov, "send_secret", secret_args(sov.lct.id, "s", Some("op-1")), true).await.unwrap_err();
        assert!(e.message.contains("withdrawn"), "{}", e.message);
        assert_eq!(queued(&state, sov.lct.id).await, q0, "the notice was withdrawn");
        assert_eq!(ledger_len(&state).await, before);
        let store = state.open_store().await.unwrap();
        assert!(store.send_op_get(sov.lct.id, "op-1").await.unwrap().is_none(), "and its op record");
    }

    #[tokio::test]
    async fn a_retried_operation_gets_the_first_receipt_not_a_second_send() {
        let (_tmp, state, sov) = fixture(true).await;
        let who = sov.lct.id;
        let (l0, q0) = (ledger_len(&state).await, queued(&state, who).await);
        let first = channel(&state, &sov, "send_secret", secret_args(who, "s", Some("op-1")), true).await.unwrap();
        assert_eq!(first["replayed"], false);
        let again = channel(&state, &sov, "send_secret", secret_args(who, "s", Some("op-1")), true).await.unwrap();
        assert_eq!(again["replayed"], true);
        assert_eq!((again["entry_index"].clone(), again["notice_id"].clone()),
                   (first["entry_index"].clone(), first["notice_id"].clone()));
        assert_eq!((ledger_len(&state).await, queued(&state, who).await), (l0 + 1, q0 + 1), "one act, one notice");
        // the same id for a different message is refused and changes nothing
        let e = channel(&state, &sov, "send_secret", secret_args(who, "other", Some("op-1")), true).await.unwrap_err();
        assert_eq!(e.status, StatusCode::CONFLICT);
        assert_eq!((ledger_len(&state).await, queued(&state, who).await), (l0 + 1, q0 + 1));
        // pair_id is recipient-visible opening context, so it is part of the operation binding.
        let e = channel(
            &state,
            &sov,
            "send_secret",
            secret_args_with_pair(who, "s", Some("op-1"), Uuid::from_u128(0x1211)),
            true,
        ).await.unwrap_err();
        assert_eq!(e.status, StatusCode::CONFLICT);
        assert_eq!((ledger_len(&state).await, queued(&state, who).await), (l0 + 1, q0 + 1));
        // without an operation_id nothing is deduplicated (legacy behaviour, ordering fixed)
        channel(&state, &sov, "send_secret", secret_args(who, "s", None), true).await.unwrap();
        assert_eq!(queued(&state, who).await, q0 + 2);
        let e = channel(&state, &sov, "send_secret", secret_args(who, "s", Some("bad id/")), true).await.unwrap_err();
        assert_eq!(e.status, StatusCode::BAD_REQUEST);
    }

    /// Two simultaneous retries of the same operation converge on one custody record and one
    /// ledger act. The transition lock makes this structural rather than a scheduler accident.
    #[tokio::test]
    async fn concurrent_twins_share_one_notice_one_act_and_one_receipt() {
        let (_tmp, state, sov) = fixture(true).await;
        let who = sov.lct.id;
        let (l0, q0) = (ledger_len(&state).await, queued(&state, who).await);
        let args = secret_args(who, "same-ciphertext", Some("op-twin"));
        let (a, b) = tokio::join!(
            channel(&state, &sov, "send_secret", args.clone(), true),
            channel(&state, &sov, "send_secret", args, true),
        );
        let (a, b) = (a.unwrap(), b.unwrap());
        assert_eq!(a["entry_index"], b["entry_index"]);
        assert_eq!(a["notice_id"], b["notice_id"]);
        assert_eq!((ledger_len(&state).await, queued(&state, who).await), (l0 + 1, q0 + 1));

        let act_id = op_act_id(who, "op-twin");
        let ledger = state.ledger.lock().await;
        let count = ledger.entries().iter().filter(|e| matches!(
            &e.event, HubEvent::ReferencedAct { act } if act.act_id == act_id
        )).count();
        assert_eq!(count, 1, "same operation_id landed more than one ReferencedAct");
    }

    /// Once the op says its act landed, an error/cleanup path may not withdraw its notice.
    #[tokio::test]
    async fn a_completed_operation_cannot_withdraw_its_notice() {
        let (_tmp, state, sov) = fixture(true).await;
        let who = sov.lct.id;
        let out = channel(&state, &sov, "send_secret", secret_args(who, "s", Some("op-done")), true)
            .await.unwrap();
        let id = out["notice_id"].as_str().unwrap().to_string();
        let before = queued(&state, who).await;
        assert!(!state.mailbox_withdraw(who, &id, Some((who, "op-done"))).await.unwrap());
        assert_eq!(queued(&state, who).await, before, "completed op's notice was withdrawn");
        let bytes = state.open_store().await.unwrap().send_op_get(who, "op-done").await.unwrap().unwrap();
        let op: SendOp = serde_json::from_slice(&bytes).unwrap();
        assert!(op.entry_index.is_some(), "completed op was reset");
    }

    /// The notice and its op record are ONE transaction: a notice is never accepted without the
    /// record that makes its retry safe (and no act is witnessed for it).
    #[tokio::test]
    async fn the_notice_and_its_op_record_commit_together() {
        let (tmp, state, sov) = fixture(true).await;
        let who = sov.lct.id;
        let (l0, q0) = (ledger_len(&state).await, queued(&state, who).await);
        sql(&tmp, "CREATE TRIGGER refuse_op BEFORE INSERT ON send_ops BEGIN SELECT RAISE(FAIL, 'injected'); END;");
        assert!(channel(&state, &sov, "send_secret", secret_args(who, "s", Some("op-tx")), true).await.is_err());
        assert_eq!((ledger_len(&state).await, queued(&state, who).await), (l0, q0),
            "the mailbox write survived its op record's failure");
    }

    /// The daemon died between queueing the notice and landing its act: the op record says
    /// queued, no entry. A retry witnesses the act ONCE — and if the act did land but the op
    /// record was not updated, the retry FINDS it rather than witnessing a second.
    #[tokio::test]
    async fn a_retry_after_a_crash_completes_the_record_exactly_once() {
        let (_tmp, state, sov) = fixture(true).await;
        let who = sov.lct.id;
        let binding = |sealed: &str| serde_json::json!({"to": who, "pointer_uri": "secret",
            "content_hash": format!("sha256-content:{}", "a".repeat(64)),
            "sealed_sha256": web4_core::sha256_hex(sealed.as_bytes()),
            "pair_id": Uuid::from_u128(0x1210)});
        // Case 1: queued, act never landed.
        let rec = SendOp { binding: binding("s"), act_id: op_act_id(who, "op-crash"), notice_id: String::new(),
            created_at: Utc::now().timestamp(), entry_index: None, durable: true };
        let n = SealedNotice { from: who, sealed: "s".into(), kind: "secret".into(), pointer_uri: "secret".into(),
            sealed_by: Some(who), ..notice() };
        assert!(matches!(enqueue_notice_op(&state, who, n, Some((who, "op-crash", &rec))).await.unwrap(),
            Enqueued::Queued { .. }));
        let (l0, q0) = (ledger_len(&state).await, queued(&state, who).await);
        let out = channel(&state, &sov, "send_secret", secret_args(who, "s", Some("op-crash")), true).await.unwrap();
        assert_eq!(out["replayed"], true);
        assert_eq!((ledger_len(&state).await, queued(&state, who).await), (l0 + 1, q0), "act landed once, no second notice");
        let index = out["entry_index"].as_u64().unwrap();
        let again = channel(&state, &sov, "send_secret", secret_args(who, "s", Some("op-crash")), true).await.unwrap();
        assert_eq!(again["entry_index"], index);
        assert_eq!(ledger_len(&state).await, l0 + 1);

        // Case 2: the act landed, the op record was never updated.
        let rec2 = SendOp { act_id: op_act_id(who, "op-landed"), ..rec.clone() };
        let n2 = SealedNotice { from: who, sealed: "s".into(), kind: "secret".into(), pointer_uri: "secret".into(),
            sealed_by: Some(who), ..notice() };
        enqueue_notice_op(&state, who, n2, Some((who, "op-landed", &rec2))).await.unwrap();
        let mut act = web4_core::act::Act::addressed(who, web4_core::act::ActAddress::Citizen { lct_id: who },
            "secret", web4_core::act::SubstanceRef::new("secret", format!("sha256-content:{}", "a".repeat(64)),
            web4_core::act::SubstanceMedium::Message), Utc::now());
        act.act_id = op_act_id(who, "op-landed");
        let landed = witness_event(&state, HubEvent::ReferencedAct { act }).await.unwrap();
        let l1 = ledger_len(&state).await;
        let out = channel(&state, &sov, "send_secret", secret_args(who, "s", Some("op-landed")), true).await.unwrap();
        assert_eq!(out["entry_index"], landed, "found by act_id");
        assert_eq!(ledger_len(&state).await, l1, "not witnessed a second time");
    }


    fn status<T>(r: Result<T, MailboxError>) -> StatusCode {
        match r {
            Ok(_) => panic!("expected a refusal, got success"),
            Err(MailboxError::Refused(st, _)) => st,
            Err(MailboxError::Store(e)) => panic!("store error: {e:#}"),
        }
    }

    /// A caller's retry logic reads the status: a protocol refusal must not look like a
    /// transient store failure (500), or the caller retries a permanent "no" forever.
    #[tokio::test]
    async fn receipt_protocol_refusals_are_not_500s() {
        let (_tmp, state, _) = fixture(true).await;
        let who = Uuid::new_v4();
        assert_eq!(status(state.mailbox_fetch(who, 100).await), StatusCode::CONFLICT, "not enrolled");
        assert_eq!(status(state.mailbox_fetch(who, 0).await), StatusCode::BAD_REQUEST);
        assert_eq!(status(state.mailbox_ack(who, "nothex").await), StatusCode::BAD_REQUEST);
        assert_eq!(status(state.mailbox_ack(who, &"a".repeat(64)).await), StatusCode::CONFLICT, "not enrolled");
        assert!(state.mailbox_enable_receipts(who).await.unwrap(), "first enrollment");
        assert!(!state.mailbox_enable_receipts(who).await.unwrap(), "idempotent");
        assert_eq!(status(state.mailbox_ack(who, &"a".repeat(64)).await), StatusCode::NOT_FOUND);
        assert_eq!(status(state.mailbox_legacy_drain(who).await), StatusCode::CONFLICT);
        let (_tmp2, ram, _) = fixture(false).await;
        assert_eq!(status(ram.mailbox_enable_receipts(who).await), StatusCode::NOT_IMPLEMENTED);
        // the retention bound refuses a SEND as the recipient's bound, not a server fault
        let full = Mailbox::Receipts(ReceiptMailbox { protocol: RECEIVE_PROTOCOL.into(),
            notices: (0..MAX_NOTICES_PER_MEMBER).map(|_| notice()).collect(), acked: vec![] });
        let busy = Uuid::new_v4();
        state.open_store().await.unwrap().mailbox_put(busy, &serde_json::to_vec(&full).unwrap()).await.unwrap();
        assert_eq!(status(enqueue_notice(&state, busy, notice()).await), StatusCode::INSUFFICIENT_STORAGE);
    }

    /// Another member's unreadable row must not take THIS member's mailbox down: the record is
    /// read per recipient, not by a scan that fails as a whole.
    #[tokio::test]
    async fn receipt_one_bad_row_is_not_every_members_outage() {
        let (tmp, state, _) = fixture(true).await;
        let who = Uuid::new_v4();
        state.mailbox_enable_receipts(who).await.unwrap();
        sql(&tmp, "INSERT INTO mailbox (recipient, blob) VALUES ('not-a-uuid', x'00');");
        enqueue_notice(&state, who, notice()).await.unwrap();
        assert_eq!(state.mailbox_fetch(who, 100).await.unwrap()["notifications"].as_array().unwrap().len(), 1);
    }

    /// Enrollment holds ENROLL_LOCK across preflight + witness + write. Deterministic form of
    /// "two concurrent calls witness once": while another holder has the lock, an enrollment
    /// must not reach the ledger at all. (A join! of two calls does not interleave on the test
    /// runtime, so it passed with the lock removed — a test that could not fail.)
    #[tokio::test]
    async fn an_enrollment_waits_for_the_enrollment_lock_before_witnessing() {
        let (_tmp, state, sov) = fixture(true).await;
        let before = state.ledger.lock().await.len();
        let held = ENROLL_LOCK.lock().await;
        let task = {
            let state = state.clone();
            let who = sov.lct.id;
            tokio::spawn(async move { enable_mailbox_receipts_as_operator(&state, who, "r").await })
        };
        tokio::time::sleep(std::time::Duration::from_millis(50)).await;
        assert_eq!(state.ledger.lock().await.len(), before, "witnessed while another enrollment held the lock");
        drop(held);
        let out = task.await.unwrap().unwrap();
        assert_eq!(out["already"], false);
        assert_eq!(state.ledger.lock().await.len(), before + 1);
        let again = enable_mailbox_receipts_as_operator(&state, sov.lct.id, "r2").await.unwrap();
        assert_eq!(again["already"], true);
    }

    #[tokio::test]
    async fn receipt_enrollment_is_an_operator_act_witnessed_once() {
        let (_tmp, state, sov) = fixture(true).await;
        let who = sov.lct.id;
        let e = enable_mailbox_receipts_as_operator(&state, who, "  ").await.unwrap_err();
        assert_eq!(e.status, StatusCode::BAD_REQUEST, "a reason is required");
        let e = enable_mailbox_receipts_as_operator(&state, Uuid::new_v4(), "r").await.unwrap_err();
        assert_eq!(e.status, StatusCode::NOT_FOUND, "only a known member");
        let len = |s: &RestState| { let s = s.clone(); async move { s.ledger.lock().await.len() } };
        let before = len(&state).await;
        let out = enable_mailbox_receipts_as_operator(&state, who, "external bridge G4 staging").await.unwrap();
        assert_eq!((out["enrolled"].clone(), out["already"].clone()), (serde_json::json!(true), serde_json::json!(false)));
        assert_eq!(len(&state).await, before + 1, "the enrollment is on the ledger");
        assert!(state.mailbox_fetch(who, 100).await.is_ok(), "and in force");
        let again = enable_mailbox_receipts_as_operator(&state, who, "again").await.unwrap();
        assert_eq!(again["already"], true);
        assert_eq!(len(&state).await, before + 1, "an idempotent re-call writes no second act");
    }
}
