// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Metalinxx Inc.

//! V2-Sprint2: AWS DynamoDB backend for [`crate::store::HubStore`].
//!
//! **Status:** Untested against real AWS in this commit. The code
//! compiles, types align with `aws-sdk-dynamodb` v1, and the logic is
//! cleanly transliterated from the file/sqlite impls. Run the manual
//! smoke at `web4/hub/examples/dynamodb_local_smoke.sh` (against
//! DynamoDB Local) or your AWS account before relying on it for any
//! production chapter.
//!
//! ## Single-table design
//!
//! Operator picks one DynamoDB table; many chapters share it. Per
//! chapter, the layout is:
//!
//! | PK              | SK                 | item                  |
//! |-----------------|--------------------|-----------------------|
//! | `HUB#<hub_id>`  | `CHARTER`          | charter JSON bytes    |
//! | `HUB#<hub_id>`  | `SOCIETY`          | society JSON bytes    |
//! | `HUB#<hub_id>`  | `LAW`              | law YAML bytes        |
//! | `HUB#<hub_id>`  | `LEDGER#<idx20>`   | ledger entry JSON     |
//! | `HUB#<hub_id>`  | `PROPOSAL#<uuid>`  | proposal JSON         |
//! | `HUB#<hub_id>`  | `PAIRMSG#<pair>#<seq20>` | pair message JSON |
//!
//! `<idx20>` / `<seq20>` are the 20-digit zero-padded entry index and
//! per-pair message seq, so DynamoDB's lexicographic Sort Key ordering
//! matches numeric ledger / seq order.
//!
//! ## Atomic ledger append
//!
//! `PutItem` with `ConditionExpression: attribute_not_exists(SK)`
//! gives the same primitive sqlite gets from its `INTEGER PRIMARY KEY`
//! constraint: two appenders racing at the same index → exactly one
//! commits, the other gets `ConditionalCheckFailedException` which
//! maps to a Rust error and surfaces as the existing
//! "ledger advanced between build_entry and append_signed" stale-
//! detection (the next build_entry sees the committed entry's index
//! and uses index+1).
//!
//! ## Why single-table-design
//!
//! AWS best practice for DynamoDB. One table holds all item types for
//! a given access pattern, distinguished by composite key. Cheaper
//! than table-per-concern (no fixed per-table cost; pay only for
//! actual reads/writes), and `Query` on PK with `SK begins_with`
//! filter is the idiomatic way to fetch related items (e.g., all
//! ledger entries for a hub).
//!
//! ## What this MVP does NOT do
//!
//! - **TransactWriteItems for cross-item atomicity.** Not needed by
//!   the current trait surface — every method writes one item.
//! - **DynamoDB Streams.** Useful for cross-region replication or
//!   audit; out of scope here.
//! - **GSIs.** Single-table-design here keeps a single access pattern
//!   (PK by hub_id). Cross-hub indexing (e.g. "find all chapters
//!   declaring skill X") would need a GSI.
//! - **Multi-region Global Tables.** Configured at table level, not
//!   in the backend code. Operator provisions the table; the backend
//!   just talks to one region.

use anyhow::{Context, Result};
use aws_sdk_dynamodb::types::AttributeValue;
use aws_sdk_dynamodb::Client;
use std::collections::HashMap;
use uuid::Uuid;

use crate::charter::Charter;
use crate::ledger::LedgerEntry;
use crate::proposal::CouncilProposal;
use crate::store::{BackendKind, HubStore};
use web4_core::society::Society;

/// AWS DynamoDB backend. Constructed via [`Self::open`] given an
/// already-configured `aws_sdk_dynamodb::Client`, a table name, and
/// the hub id this backend serves (single-table-design partitions
/// items by hub).
pub struct DynamoDbBackend {
    client: Client,
    table: String,
    hub_id: Uuid,
}

impl std::fmt::Debug for DynamoDbBackend {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("DynamoDbBackend")
            .field("table", &self.table)
            .field("hub_id", &self.hub_id)
            .finish()
    }
}

impl DynamoDbBackend {
    /// Construct a backend handle. Caller supplies a ready DynamoDB
    /// `Client` (from `aws_config::load_defaults` or similar) and
    /// the table name + hub_id. Does not touch the network until
    /// the first HubStore method is called.
    pub fn open(client: Client, table: impl Into<String>, hub_id: Uuid) -> Self {
        Self { client, table: table.into(), hub_id }
    }

    fn pk(&self) -> String {
        format!("HUB#{}", self.hub_id)
    }

    fn ledger_sk(index: u64) -> String {
        // 20-digit zero-pad keeps lexicographic order == numeric order
        // up to u64::MAX (20 digits = ~1.8e19 which exceeds 2^64).
        format!("LEDGER#{:020}", index)
    }

    fn proposal_sk(id: Uuid) -> String {
        format!("PROPOSAL#{}", id)
    }

    /// Sort key for one message in a pair's sidecar log. Same
    /// 20-digit zero-pad trick as the ledger so lexicographic SK
    /// order == numeric seq order, and every message for a pair
    /// shares the [`Self::pair_msg_sk_prefix`] prefix.
    fn pair_msg_sk(pair_id: Uuid, seq: u64) -> String {
        format!("PAIRMSG#{}#{:020}", pair_id, seq)
    }

    fn pair_msg_sk_prefix(pair_id: Uuid) -> String {
        format!("PAIRMSG#{}#", pair_id)
    }

    fn key_for(&self, sk: &str) -> HashMap<String, AttributeValue> {
        let mut m = HashMap::new();
        m.insert("PK".into(), AttributeValue::S(self.pk()));
        m.insert("SK".into(), AttributeValue::S(sk.to_string()));
        m
    }

    fn item(&self, sk: &str, body: &str) -> HashMap<String, AttributeValue> {
        let mut item = self.key_for(sk);
        item.insert("body".into(), AttributeValue::S(body.into()));
        item
    }

    async fn get_body(&self, sk: &str) -> Result<Option<String>> {
        let out = self.client.get_item()
            .table_name(&self.table)
            .set_key(Some(self.key_for(sk)))
            .send().await
            .with_context(|| format!("dynamodb get_item PK={} SK={}", self.pk(), sk))?;
        Ok(out.item
            .and_then(|m| m.get("body").cloned())
            .and_then(|av| av.as_s().ok().cloned()))
    }

    async fn put_body(&self, sk: &str, body: &str) -> Result<()> {
        self.client.put_item()
            .table_name(&self.table)
            .set_item(Some(self.item(sk, body)))
            .send().await
            .with_context(|| format!("dynamodb put_item PK={} SK={}", self.pk(), sk))?;
        Ok(())
    }

    /// Query all items with this PK and SK prefix, returning the
    /// `body` of each in SK-sorted ascending order. Handles pagination
    /// transparently.
    async fn query_by_sk_prefix(&self, sk_prefix: &str) -> Result<Vec<String>> {
        let mut out = Vec::new();
        let mut last_evaluated_key: Option<HashMap<String, AttributeValue>> = None;
        loop {
            let mut req = self.client.query()
                .table_name(&self.table)
                .key_condition_expression("#pk = :pk AND begins_with(#sk, :skp)")
                .expression_attribute_names("#pk", "PK")
                .expression_attribute_names("#sk", "SK")
                .expression_attribute_values(":pk", AttributeValue::S(self.pk()))
                .expression_attribute_values(":skp", AttributeValue::S(sk_prefix.to_string()))
                .scan_index_forward(true); // ascending
            if let Some(ek) = last_evaluated_key.take() {
                req = req.set_exclusive_start_key(Some(ek));
            }
            let resp = req.send().await
                .with_context(|| format!("dynamodb query PK={} SK~{}", self.pk(), sk_prefix))?;
            if let Some(items) = resp.items {
                for item in items {
                    if let Some(av) = item.get("body") {
                        if let Ok(s) = av.as_s() {
                            out.push(s.clone());
                        }
                    }
                }
            }
            last_evaluated_key = resp.last_evaluated_key;
            if last_evaluated_key.is_none() { break; }
        }
        Ok(out)
    }
}

#[async_trait::async_trait]
impl HubStore for DynamoDbBackend {
    fn backend_kind(&self) -> BackendKind { BackendKind::Dynamodb }

    async fn read_charter(&self) -> Result<Option<Charter>> {
        match self.get_body("CHARTER").await? {
            None => Ok(None),
            Some(json) => Ok(Some(serde_json::from_str(&json)
                .context("parsing charter from dynamodb")?)),
        }
    }

    async fn write_charter(&mut self, charter: &Charter) -> Result<()> {
        let json = serde_json::to_string(charter).context("serializing charter")?;
        self.put_body("CHARTER", &json).await
    }

    async fn read_society(&self) -> Result<Option<Society>> {
        match self.get_body("SOCIETY").await? {
            None => Ok(None),
            Some(json) => Ok(Some(serde_json::from_str(&json)
                .context("parsing society from dynamodb")?)),
        }
    }

    async fn write_society(&mut self, society: &Society) -> Result<()> {
        let json = serde_json::to_string(society).context("serializing society")?;
        self.put_body("SOCIETY", &json).await
    }

    async fn ledger_load_all(&self) -> Result<Vec<LedgerEntry>> {
        let bodies = self.query_by_sk_prefix("LEDGER#").await?;
        let mut entries = Vec::with_capacity(bodies.len());
        for body in bodies {
            let entry: LedgerEntry = serde_json::from_str(&body)
                .context("parsing ledger entry from dynamodb")?;
            entries.push(entry);
        }
        Ok(entries)
    }

    async fn ledger_append(&mut self, entry: &LedgerEntry) -> Result<()> {
        let json = serde_json::to_string(entry).context("serializing ledger entry")?;
        let sk = Self::ledger_sk(entry.index);
        // Conditional put: fail if an entry already exists at this
        // index. This is the atomic-append primitive that protects
        // the hash chain from concurrent appenders. The error maps
        // to the same "ledger advanced" surface the sqlite PRIMARY
        // KEY constraint produces.
        let result = self.client.put_item()
            .table_name(&self.table)
            .set_item(Some(self.item(&sk, &json)))
            .condition_expression("attribute_not_exists(SK)")
            .send().await;
        match result {
            Ok(_) => Ok(()),
            Err(e) => {
                // Distinguish ConditionalCheckFailed (concurrent append)
                // from transport errors so callers can react appropriately.
                let svc_err = e.as_service_error();
                if let Some(svc) = svc_err {
                    if svc.is_conditional_check_failed_exception() {
                        return Err(anyhow::anyhow!(
                            "dynamodb ledger_append: entry at idx={} already exists \
                             (concurrent append — caller should rebuild and retry)",
                            entry.index
                        ));
                    }
                }
                Err(anyhow::anyhow!("dynamodb put_item failed: {}", e))
            }
        }
    }

    async fn read_law(&self) -> Result<Option<String>> {
        self.get_body("LAW").await
    }

    async fn write_law(&mut self, yaml: &str) -> Result<()> {
        self.put_body("LAW", yaml).await
    }

    async fn write_proposal(&mut self, proposal: &CouncilProposal) -> Result<()> {
        let json = serde_json::to_string(proposal).context("serializing proposal")?;
        self.put_body(&Self::proposal_sk(proposal.id), &json).await
    }

    async fn read_proposal(&self, id: Uuid) -> Result<Option<CouncilProposal>> {
        match self.get_body(&Self::proposal_sk(id)).await? {
            None => Ok(None),
            Some(json) => Ok(Some(serde_json::from_str(&json)
                .context("parsing proposal from dynamodb")?)),
        }
    }

    async fn list_proposals(&self) -> Result<Vec<CouncilProposal>> {
        let bodies = self.query_by_sk_prefix("PROPOSAL#").await?;
        let mut out = Vec::with_capacity(bodies.len());
        for body in bodies {
            match serde_json::from_str::<CouncilProposal>(&body) {
                Ok(p) => out.push(p),
                Err(e) => tracing::warn!("skipping unparseable proposal from dynamodb: {}", e),
            }
        }
        // Sort newest-first to match FileBackend's behavior.
        out.sort_by(|a, b| b.proposed_at.cmp(&a.proposed_at));
        Ok(out)
    }

    async fn delete_proposal(&mut self, id: Uuid) -> Result<()> {
        self.client.delete_item()
            .table_name(&self.table)
            .set_key(Some(self.key_for(&Self::proposal_sk(id))))
            .send().await
            .with_context(|| format!("dynamodb delete_item PK={} SK=PROPOSAL#{}", self.pk(), id))?;
        Ok(())
    }

    // ----- PAIRED-CHANNELS Sprint D: pair message sidecar -----

    async fn append_pair_message(
        &mut self,
        msg: &crate::pair_message::PairMessage,
    ) -> Result<()> {
        let json = serde_json::to_string(msg).context("serializing pair message")?;
        let sk = Self::pair_msg_sk(msg.pair_id, msg.seq);
        // Conditional put, same primitive as ledger_append: two
        // appenders racing on the same seq must not silently clobber
        // each other — the trait contract calls that a chain-integrity
        // bug, so surface it instead of losing a message.
        let result = self.client.put_item()
            .table_name(&self.table)
            .set_item(Some(self.item(&sk, &json)))
            .condition_expression("attribute_not_exists(SK)")
            .send().await;
        match result {
            Ok(_) => Ok(()),
            Err(e) => {
                if let Some(svc) = e.as_service_error() {
                    if svc.is_conditional_check_failed_exception() {
                        return Err(anyhow::anyhow!(
                            "dynamodb append_pair_message: message at pair={} seq={} \
                             already exists (concurrent append — caller should re-read \
                             message_count and retry)",
                            msg.pair_id, msg.seq
                        ));
                    }
                }
                Err(anyhow::Error::new(e).context(format!(
                    "dynamodb put_item PK={} SK={}", self.pk(), sk)))
            }
        }
    }

    async fn list_pair_messages(
        &self,
        pair_id: Uuid,
        since_seq: Option<u64>,
    ) -> Result<Vec<crate::pair_message::PairMessage>> {
        // Query returns SK-ascending == seq-ascending by construction
        // of pair_msg_sk, which is the order the trait requires.
        let bodies = self.query_by_sk_prefix(&Self::pair_msg_sk_prefix(pair_id)).await?;
        let mut out = Vec::with_capacity(bodies.len());
        for body in bodies {
            let msg: crate::pair_message::PairMessage = serde_json::from_str(&body)
                .with_context(|| format!("parsing pair message for pair {}", pair_id))?;
            // Filter on the read path to match FileBackend. A pair's
            // log is small, so the wasted read is cheaper than the
            // extra key-condition complexity.
            if let Some(s) = since_seq {
                if msg.seq <= s { continue; }
            }
            out.push(msg);
        }
        Ok(out)
    }
}

/// Convenience constructor: load AWS config from the environment
/// (region / credentials per the AWS SDK default chain) and open
/// a backend handle. Operators with custom auth flows should
/// construct `Client` themselves and call [`DynamoDbBackend::open`].
pub async fn open_default(table: impl Into<String>, hub_id: Uuid) -> Result<DynamoDbBackend> {
    let cfg = aws_config::defaults(aws_config::BehaviorVersion::latest())
        .load().await;
    let client = Client::new(&cfg);
    Ok(DynamoDbBackend::open(client, table, hub_id))
}

/// CloudFormation-equivalent CreateTable invocation for the
/// single-table layout. Operators with infra-as-code skip this and
/// provision via Terraform / CDK / CloudFormation. Provided as a
/// convenience for first-time setup + the smoke against DynamoDB
/// Local. Idempotent: if the table already exists, returns Ok.
pub async fn ensure_table(client: &Client, table: &str) -> Result<()> {
    use aws_sdk_dynamodb::types::{AttributeDefinition, BillingMode, KeySchemaElement, KeyType, ScalarAttributeType};

    // Probe — describe-table returns ResourceNotFoundException if absent.
    match client.describe_table().table_name(table).send().await {
        Ok(_) => return Ok(()),
        Err(e) => {
            let svc = e.as_service_error();
            let is_not_found = svc.map(|s| s.is_resource_not_found_exception()).unwrap_or(false);
            if !is_not_found {
                return Err(anyhow::anyhow!("describe_table failed: {}", e));
            }
        }
    }
    client.create_table()
        .table_name(table)
        .billing_mode(BillingMode::PayPerRequest)
        .attribute_definitions(AttributeDefinition::builder()
            .attribute_name("PK").attribute_type(ScalarAttributeType::S).build()
            .map_err(|e| anyhow::anyhow!("PK attr def: {}", e))?)
        .attribute_definitions(AttributeDefinition::builder()
            .attribute_name("SK").attribute_type(ScalarAttributeType::S).build()
            .map_err(|e| anyhow::anyhow!("SK attr def: {}", e))?)
        .key_schema(KeySchemaElement::builder()
            .attribute_name("PK").key_type(KeyType::Hash).build()
            .map_err(|e| anyhow::anyhow!("PK key schema: {}", e))?)
        .key_schema(KeySchemaElement::builder()
            .attribute_name("SK").key_type(KeyType::Range).build()
            .map_err(|e| anyhow::anyhow!("SK key schema: {}", e))?)
        .send().await
        .with_context(|| format!("creating dynamodb table {}", table))?;
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    /// SK encoding must be lexicographically stable across u64 indices.
    #[test]
    fn ledger_sk_lexicographic_order() {
        assert!(DynamoDbBackend::ledger_sk(0) < DynamoDbBackend::ledger_sk(1));
        assert!(DynamoDbBackend::ledger_sk(9) < DynamoDbBackend::ledger_sk(10));
        assert!(DynamoDbBackend::ledger_sk(99) < DynamoDbBackend::ledger_sk(100));
        assert!(DynamoDbBackend::ledger_sk(u64::MAX - 1) < DynamoDbBackend::ledger_sk(u64::MAX));
    }

    /// 20 digits accommodates u64::MAX (~1.8e19).
    #[test]
    fn ledger_sk_format() {
        assert_eq!(DynamoDbBackend::ledger_sk(0), "LEDGER#00000000000000000000");
        assert_eq!(DynamoDbBackend::ledger_sk(42), "LEDGER#00000000000000000042");
    }

    #[test]
    fn proposal_sk_uses_full_uuid() {
        let id = uuid::Uuid::parse_str("550e8400-e29b-41d4-a716-446655440000").unwrap();
        assert_eq!(
            DynamoDbBackend::proposal_sk(id),
            "PROPOSAL#550e8400-e29b-41d4-a716-446655440000"
        );
    }

    /// Sidecar SKs must sort by seq within a pair, and every SK for a
    /// pair must sit under the prefix `list_pair_messages` queries on
    /// — otherwise a drain silently returns nothing.
    #[test]
    fn pair_msg_sk_orders_by_seq_under_prefix() {
        let pair = uuid::Uuid::parse_str("6907b489-2372-485c-a91b-2ec05139104c").unwrap();
        assert!(DynamoDbBackend::pair_msg_sk(pair, 9) < DynamoDbBackend::pair_msg_sk(pair, 10));
        assert!(DynamoDbBackend::pair_msg_sk(pair, u64::MAX - 1)
            < DynamoDbBackend::pair_msg_sk(pair, u64::MAX));
        let prefix = DynamoDbBackend::pair_msg_sk_prefix(pair);
        assert!(DynamoDbBackend::pair_msg_sk(pair, 0).starts_with(&prefix));
        assert_eq!(
            DynamoDbBackend::pair_msg_sk(pair, 1),
            "PAIRMSG#6907b489-2372-485c-a91b-2ec05139104c#00000000000000000001"
        );
    }

    /// A prefix query for one pair must not pick up another pair's
    /// messages — the `#` terminator is what makes that true.
    #[test]
    fn pair_msg_prefix_does_not_straddle_pairs() {
        let a = uuid::Uuid::parse_str("6907b489-2372-485c-a91b-2ec05139104c").unwrap();
        let b = uuid::Uuid::parse_str("6907b489-2372-485c-a91b-2ec05139104d").unwrap();
        assert!(!DynamoDbBackend::pair_msg_sk(b, 0)
            .starts_with(&DynamoDbBackend::pair_msg_sk_prefix(a)));
    }
}
