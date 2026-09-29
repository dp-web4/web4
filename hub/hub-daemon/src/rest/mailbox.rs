// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Metalinxx Inc.

//! Durable mailbox operations. The notifications mutex serializes each complete
//! read/modify/commit; the store, not the hydrated RAM cache, is authoritative.
use super::*;
use hub_lib::store::HubStore;
use sha2::{Digest, Sha256};

pub(super) const RECEIVE_PROTOCOL: &str = "hub-mailbox-receive-v1";

#[derive(Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub(super) struct ReceiptMailbox {
    protocol: String,
    pub notices: Vec<SealedNotice>,
    acked: Vec<String>,
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
            anyhow::ensure!(r.notices.len() + r.acked.len() <= MAX_NOTICES_PER_MEMBER,
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
    pub fn full(&self) -> bool {
        matches!(self, Self::Receipts(r) if r.notices.len() + r.acked.len() >= MAX_NOTICES_PER_MEMBER)
    }
}

pub(super) fn notice_id(recipient: Uuid, notice: &SealedNotice) -> String {
    // Fixed struct field order, domain separated, recipient bound. Includes the
    // committed timestamp: two distinct queue entries never share an ACK by pair_id.
    let bytes = serde_json::to_vec(&(RECEIVE_PROTOCOL, recipient, notice)).expect("notice JSON");
    hex::encode(Sha256::digest(bytes))
}

impl RestState {
    pub(super) async fn load_mailbox_record(
        &self, store: &dyn HubStore, recipient: Uuid, cached: &[SealedNotice],
    ) -> Result<Mailbox> {
        if !store.mailbox_is_durable() { return Ok(Mailbox::Legacy(cached.to_vec())); }
        // Existing store interface is a whole-mailbox scan. Deliberately prefer
        // authoritative state over a cache that may have failed hydration.
        for (id, bytes) in store.mailbox_load_all().await? {
            if id == recipient { return Mailbox::decode(&bytes); }
        }
        Ok(Mailbox::Legacy(Vec::new()))
    }

    pub(super) async fn mailbox_enable_receipts(&self, recipient: Uuid) -> Result<()> {
        let mut cache = self.notifications.lock().await;
        let mut store = self.open_store().await?;
        anyhow::ensure!(store.mailbox_is_durable(), "receipt delivery requires durable mailbox storage");
        let record = self.load_mailbox_record(&*store, recipient, &[]).await?;
        let record = match record {
            Mailbox::Legacy(notices) => Mailbox::Receipts(ReceiptMailbox {
                protocol: RECEIVE_PROTOCOL.into(), notices, acked: Vec::new(),
            }),
            other => other,
        };
        store.mailbox_put(recipient, &serde_json::to_vec(&record)?).await?;
        cache.insert(recipient, record.notices().clone());
        Ok(())
    }

    pub(super) async fn mailbox_fetch(&self, recipient: Uuid, limit: usize) -> Result<serde_json::Value> {
        anyhow::ensure!((1..=100).contains(&limit), "limit must be between 1 and 100");
        let _guard = self.notifications.lock().await;
        let store = self.open_store().await?;
        anyhow::ensure!(store.mailbox_is_durable(), "receipt delivery requires durable mailbox storage");
        let record = self.load_mailbox_record(&*store, recipient, &[]).await?;
        anyhow::ensure!(record.is_receipts(), "enable receipt delivery explicitly before fetching");
        let notices: Vec<_> = record.notices().iter().take(limit).map(|notice|
            serde_json::json!({"id": notice_id(recipient, notice), "notice": notice})).collect();
        Ok(serde_json::json!({"protocol": RECEIVE_PROTOCOL, "notifications": notices,
            "remaining": record.notices().len().saturating_sub(limit)}))
    }

    pub(super) async fn mailbox_ack(&self, recipient: Uuid, id: &str) -> Result<serde_json::Value> {
        anyhow::ensure!(id.len() == 64 && id.bytes().all(|b| b.is_ascii_hexdigit()), "invalid notice id");
        let mut cache = self.notifications.lock().await;
        let mut store = self.open_store().await?;
        anyhow::ensure!(store.mailbox_is_durable(), "receipt delivery requires durable mailbox storage");
        let mut record = self.load_mailbox_record(&*store, recipient, &[]).await?;
        let Mailbox::Receipts(r) = &mut record else { anyhow::bail!("receipt delivery is not enabled") };
        if !r.acked.iter().any(|old| old == id) {
            let Some(index) = r.notices.iter().position(|n| notice_id(recipient, n) == id) else {
                anyhow::bail!("notice is not in this recipient's mailbox")
            };
            r.notices.remove(index);
            r.acked.push(id.to_owned());
            store.mailbox_put(recipient, &serde_json::to_vec(&record)?).await?;
            cache.insert(recipient, record.notices().clone());
        }
        Ok(serde_json::json!({"protocol": RECEIVE_PROTOCOL, "id": id,
            "acknowledged": true, "completed": false}))
    }

    pub(super) async fn mailbox_legacy_drain(&self, recipient: Uuid) -> Result<Vec<SealedNotice>> {
        let mut cache = self.notifications.lock().await;
        let mut store = self.open_store().await?;
        let cached = cache.get(&recipient).map(Vec::as_slice).unwrap_or(&[]);
        let record = self.load_mailbox_record(&*store, recipient, cached).await?;
        anyhow::ensure!(!record.is_receipts(), "legacy drain disabled: use notifications_fetch and notifications_ack");
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
        assert!(channel(&state, &sov, "notifications_enable_receipts", serde_json::json!({}), false).await.is_err());
        channel(&state, &sov, "notifications_enable_receipts", serde_json::json!({}), true).await.unwrap();
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
        assert!(enqueue_notice(&state, who, notice()).await.is_err(), "ACK tombstones count toward the bound");
    }
}
