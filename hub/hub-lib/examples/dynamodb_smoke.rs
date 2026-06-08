// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Metalinxx Inc.
//
// Manual smoke for the DynamoDB backend. Driven by
// `web4/hub/examples/dynamodb_local_smoke.sh` against DynamoDB Local
// (or a real AWS account if you set the env vars accordingly).
//
// Run:
//   HUB_ID=<uuid> TABLE=<name> ENDPOINT=http://127.0.0.1:8765 \
//     cargo run -p hub-lib --features dynamodb --example dynamodb_smoke
//
// What it exercises:
//   1. write_charter / read_charter round-trip
//   2. write_society / read_society round-trip
//   3. write_law / read_law round-trip
//   4. ledger_append (idx=0, idx=1) + ledger_load_all returns both in order
//   5. ledger_append at an existing idx → ConditionalCheckFailed (atomicity)
//   6. write_proposal / read_proposal / list_proposals / delete_proposal

#[cfg(not(feature = "dynamodb"))]
fn main() {
    eprintln!("This example requires --features dynamodb");
    std::process::exit(1);
}

#[cfg(feature = "dynamodb")]
#[tokio::main]
async fn main() -> anyhow::Result<()> {
    use hub_lib::charter::Charter;
    use hub_lib::dynamodb_store::{DynamoDbBackend, ensure_table};
    use hub_lib::events::HubEvent;
    use hub_lib::ledger::LedgerEntry;
    use hub_lib::proposal::CouncilProposal;
    use hub_lib::store::HubStore;
    use uuid::Uuid;
    use web4_core::society::Society;
    use chrono::Utc;

    let hub_id: Uuid = std::env::var("HUB_ID")?.parse()?;
    let table = std::env::var("TABLE")?;
    let endpoint = std::env::var("ENDPOINT").ok();

    // Build an SDK config that respects the optional ENDPOINT override
    // (DynamoDB Local listens on http://127.0.0.1:8765 by default).
    let mut loader = aws_config::defaults(aws_config::BehaviorVersion::latest());
    if let Some(ep) = endpoint.as_deref() {
        loader = loader.endpoint_url(ep);
    }
    let cfg = loader.load().await;
    let client = aws_sdk_dynamodb::Client::new(&cfg);

    // Ensure table exists (no-op against pre-provisioned tables; useful
    // for DynamoDB Local where the test script creates it but a real
    // operator might want this idempotent path).
    ensure_table(&client, &table).await?;

    let mut store = DynamoDbBackend::open(client, &table, hub_id);

    println!("--- 1. charter round-trip ---");
    let charter = Charter::found("Dynamo Smoke".into(), hub_id);
    store.write_charter(&charter).await?;
    let back = store.read_charter().await?.expect("charter present");
    assert_eq!(back.hub_name, charter.hub_name);
    println!("OK charter hub_name={}", back.hub_name);

    println!("--- 2. society round-trip ---");
    let (society, _) = Society::bootstrap("Dynamo Smoke".into(), "h".repeat(64), hub_id);
    store.write_society(&society).await?;
    let back = store.read_society().await?.expect("society present");
    assert_eq!(back.lct_id, society.lct_id);
    println!("OK society lct_id={}", back.lct_id);

    println!("--- 3. law round-trip ---");
    let yaml = "version: \"1.0.0\"\nnorms: []\n";
    store.write_law(yaml).await?;
    assert_eq!(store.read_law().await?.unwrap(), yaml);
    println!("OK law round-tripped");

    println!("--- 4. ledger append + load ---");
    let mk_entry = |idx: u64, name: &str| LedgerEntry {
        index: idx,
        timestamp: Utc::now(),
        prev_hash: "0".repeat(64),
        actor_lct_id: hub_id,
        event: HubEvent::MemberAdded {
            member_lct_id: Uuid::new_v4(),
            added_by: hub_id,
            member_name: Some(name.into()),
            member_pubkey_hex: None,
        },
        signature: "deadbeef".into(),
        entry_hash: format!("h{}", idx),
        proposal_ref: None,
    };
    store.ledger_append(&mk_entry(0, "Alice")).await?;
    store.ledger_append(&mk_entry(1, "Bob")).await?;
    let loaded = store.ledger_load_all().await?;
    assert_eq!(loaded.len(), 2, "expected 2 entries, got {}", loaded.len());
    assert_eq!(loaded[0].index, 0);
    assert_eq!(loaded[1].index, 1);
    println!("OK ledger has 2 entries in order");

    println!("--- 5. ledger append at existing idx must fail (atomicity) ---");
    let dup = mk_entry(1, "Bob-duplicate");
    match store.ledger_append(&dup).await {
        Ok(_) => panic!("FAIL: dup append must have errored"),
        Err(e) => println!("OK rejected: {}", e),
    }

    println!("--- 6. proposal CRUD ---");
    let mut proposal = CouncilProposal::new(
        HubEvent::MemberAdded {
            member_lct_id: Uuid::new_v4(),
            added_by: hub_id,
            member_name: Some("Carol".into()),
            member_pubkey_hex: None,
        },
        hub_id,
        Utc::now(),
    );
    let pid = proposal.id;
    store.write_proposal(&proposal).await?;
    let back = store.read_proposal(pid).await?.expect("proposal present");
    assert_eq!(back.id, pid);
    let list = store.list_proposals().await?;
    assert_eq!(list.len(), 1);
    proposal.status = hub_lib::proposal::ProposalStatus::Committed {
        entry_index: 42, committed_at: Utc::now(),
    };
    store.write_proposal(&proposal).await?;
    let back = store.read_proposal(pid).await?.unwrap();
    assert!(matches!(back.status, hub_lib::proposal::ProposalStatus::Committed { entry_index: 42, .. }));
    store.delete_proposal(pid).await?;
    assert!(store.read_proposal(pid).await?.is_none(), "delete didn't take");
    println!("OK proposal CRUD");

    println!();
    println!("=== DynamoDB backend smoke OK ===");
    Ok(())
}
