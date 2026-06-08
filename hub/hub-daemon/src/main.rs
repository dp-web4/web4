// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Metalinxx Inc.

//! Web4 Community Hub daemon — single-binary entrypoint.
//!
//! Sprint 1+2+3 surface: `hub init` + `hub gen-lct` + `hub verify-ledger`
//! + `hub serve` (MCP HTTP server). Subsequent sprints add CLI parity for
//! act-recording commands (sprint 4), Docker entrypoint (sprint 5), and docs/
//! polish (sprint 6).

mod admin;
mod mcp;
mod rest;

use anyhow::{Context, Result};
use clap::{Parser, Subcommand};
use std::net::SocketAddr;
use std::path::PathBuf;

use hub_lib::hub::HubConfig;
use hub_lib::identity::IdentityFile;
use hub_lib::init::{init_chapter, verify_chapter, InitArgs, InitResult};
use hub_lib::session::HubSession;
use uuid::Uuid;
use web4_core::lct::EntityType;
use web4_core::role::SocietyRole;

use crate::mcp::{router as mcp_router, McpState};
use crate::rest::{router as rest_router, RestState};

/// Web4 Community Hub — minimum-viable Web4 society for a community chapter.
#[derive(Parser, Debug)]
#[command(name = "hub", version = hub_lib::VERSION, about, long_about = None)]
struct Cli {
    #[command(subcommand)]
    command: Option<Command>,
}

#[derive(Subcommand, Debug)]
enum Command {
    /// Initialize a new chapter society in the given directory.
    ///
    /// Two modes:
    /// - **Local mode** (MVP-compatible): pass `--sovereign-lct PATH` to a
    ///   local IdentityFile. The hub loads the keypair from the file.
    /// - **Hestia mode** (V2-7+, recommended): pass
    ///   `--sovereign-hestia URL --sovereign-lct-id ID --sovereign-pubkey HEX`.
    ///   The hub holds NO keypair; Genesis is signed by Hestia via the
    ///   callback URL.
    Init {
        /// Human-readable chapter name (e.g. "Lisbon Chapter").
        name: String,

        /// **Local mode**: path to the Sovereign IdentityFile (LCT + keypair).
        /// Generate one with `hub gen-lct` if you don't have one yet.
        /// Mutually exclusive with --sovereign-hestia.
        #[arg(long, conflicts_with = "sovereign_hestia")]
        sovereign_lct: Option<PathBuf>,

        /// **Hestia mode**: URL of the Sovereign's Hestia sign-request callback.
        /// Requires --sovereign-lct-id and --sovereign-pubkey.
        #[arg(long, requires_all = ["sovereign_lct_id", "sovereign_pubkey"])]
        sovereign_hestia: Option<String>,

        /// **Hestia mode**: the Sovereign's LCT id (uuid).
        #[arg(long)]
        sovereign_lct_id: Option<Uuid>,

        /// **Hestia mode**: the Sovereign's public key (hex-encoded 32 bytes).
        #[arg(long)]
        sovereign_pubkey: Option<String>,

        /// Directory to create the hub in. Defaults to ./<name-slug>.
        /// (Accepts deprecated alias --chapter-dir for back-compat with
        /// scripts pre-dating the chapter→hub rename.)
        #[arg(long, alias = "chapter-dir")]
        hub_dir: Option<PathBuf>,

        /// Storage backend for chapter state. Defaults to `file` (MVP-
        /// compatible JSON/JSONL). `sqlite` uses a single chapter.db file
        /// for better query performance + simpler ops.
        #[arg(long, default_value = "file")]
        storage: String,
    },

    /// Generate a fresh LCT + keypair, save to a JSON file.
    ///
    /// Use this to create a Sovereign identity for `hub init`, or any
    /// other entity (member, role-filler) that needs an LCT.
    GenLct {
        /// Output file path (will be created or overwritten).
        output: PathBuf,

        /// Entity type. Default: human (chapter organizers are humans).
        #[arg(long, value_enum, default_value = "human")]
        entity_type: CliEntityType,
    },

    /// V2-7 helper: build + print a SignedEnvelope for a given payload.
    ///
    /// Reads a keypair from an IdentityFile, signs (signer_lct_id ||
    /// nonce || canonical(payload)) per the envelope spec, and prints
    /// the SignedEnvelope JSON to stdout. Pair with `curl` to drive
    /// REST endpoints from the shell. Real Hestia replaces this — but
    /// it's a useful smoke + reference today.
    EnvelopeSign {
        /// Path to the signer's IdentityFile (LCT + keypair).
        #[arg(long)]
        identity: PathBuf,

        /// Challenge nonce previously obtained from `POST /v1/auth/challenge`.
        #[arg(long)]
        nonce: String,

        /// Payload as inline JSON.
        #[arg(long)]
        payload: String,
    },

    /// Verify the integrity of a chapter's ledger end-to-end.
    ///
    /// Checks: every entry's signature against the actor LCT, every
    /// entry's hash matches recomputation, prev-hash chain is unbroken,
    /// indices are sequential. Errors loudly if any entry is tampered.
    VerifyLedger {
        /// Path to the chapter directory.
        hub_dir: PathBuf,
    },

    /// Migrate a chapter's storage backend (e.g. file → sqlite).
    ///
    /// Auto-detects the current backend, copies charter + society +
    /// ledger entries (byte-for-byte; no re-signing) to the target
    /// backend, then renames source artifacts to `.pre-migration`
    /// suffixes so they remain recoverable. Runs verify-ledger on the
    /// migrated chapter before returning success.
    Migrate {
        /// Path to the chapter directory.
        hub_dir: PathBuf,

        /// Target backend: `file` or `sqlite`.
        #[arg(long)]
        to: String,
    },

    /// Run the MCP HTTP server for a chapter. Daemon loads the Sovereign
    /// keypair from config.toml and signs ledger entries on behalf of
    /// authenticated clients (MVP: localhost only; per-client signed
    /// envelopes are V2).
    Serve {
        /// Chapter directory.
        hub_dir: PathBuf,

        /// Override the port from config.toml.
        #[arg(long)]
        port: Option<u16>,

        /// Bind address (default 127.0.0.1 — local-only).
        #[arg(long, default_value = "127.0.0.1")]
        bind: String,
    },

    /// Print chapter status (name, members, ledger length, head hash, port).
    Status {
        hub_dir: PathBuf,
    },

    /// Add a member to the chapter.
    AddMember {
        hub_dir: PathBuf,
        /// Member's LCT id (uuid).
        member_lct_id: Uuid,
        /// Optional display name.
        #[arg(long)]
        name: Option<String>,
    },

    /// Remove a member from the chapter.
    RemoveMember {
        hub_dir: PathBuf,
        member_lct_id: Uuid,
        #[arg(long)]
        reason: Option<String>,
    },

    /// Assign a role to a member.
    AssignRole {
        hub_dir: PathBuf,
        /// One of: sovereign | law_oracle | policy_entity | treasurer
        /// | administrator | archivist | citizen | witness | auditor.
        role: String,
        /// The role LCT id (taken from `hub init` output or `hub status`).
        role_lct_id: Uuid,
        /// The member LCT id.
        member_lct_id: Uuid,
    },

    /// Record a chapter event (demo night, workshop, etc.).
    RecordEvent {
        hub_dir: PathBuf,
        /// Short event kind (e.g. "demo_night", "workshop").
        event_kind: String,
        /// Event title.
        title: String,
        /// Attendee LCT ids (comma-separated). Optional.
        #[arg(long, value_delimiter = ',')]
        attended_by: Vec<Uuid>,
    },

    /// Declare a skill for a member.
    DeclareSkill {
        hub_dir: PathBuf,
        member_lct_id: Uuid,
        skill: String,
    },

    /// Set (or amend) the chapter's law from a YAML file (V2-8).
    /// Validates the YAML against the chapter-law schema, writes it
    /// to the chapter store, and appends a LawAmended event to the
    /// ledger for audit.
    SetLaw {
        hub_dir: PathBuf,
        /// Path to a YAML file matching the chapter-law schema (see
        /// web4-standard/core-spec/chapter-law-schema.md).
        yaml: PathBuf,
        /// Optional one-line summary of what changed.
        #[arg(long)]
        diff_summary: Option<String>,
    },

    /// Print the current chapter law YAML (or report none is set).
    GetLaw {
        hub_dir: PathBuf,
    },

    /// Write the starter chapter-law template to a file the operator
    /// can review + edit, then apply via `hub set-law`. Doesn't touch
    /// any chapter directly.
    InitLaw {
        /// Where to write the starter YAML (e.g. ./hub-law.yaml).
        #[arg(default_value = "./hub-law.yaml")]
        output: PathBuf,
        /// Overwrite if the file already exists.
        #[arg(long)]
        force: bool,
    },

    /// Query chapter state (members, skills, etc.).
    Query {
        #[command(subcommand)]
        subcommand: QueryCommand,
    },
}

#[derive(Subcommand, Debug)]
enum QueryCommand {
    /// List all current chapter members.
    Members { hub_dir: PathBuf },
    /// Find members by skill (case-insensitive substring).
    Skill {
        hub_dir: PathBuf,
        query: String,
    },
    /// Print chapter identity + role-fill snapshot.
    Chapter { hub_dir: PathBuf },
}

/// Subset of web4_core::EntityType exposed via CLI. (clap can't derive
/// ValueEnum on the upstream enum because it's not annotated; mirror here.)
#[derive(Copy, Clone, Debug, clap::ValueEnum)]
enum CliEntityType {
    Human,
    AiSoftware,
    AiEmbodied,
    Organization,
    Role,
    Task,
    Resource,
    Hybrid,
}

impl From<CliEntityType> for EntityType {
    fn from(c: CliEntityType) -> Self {
        match c {
            CliEntityType::Human => EntityType::Human,
            CliEntityType::AiSoftware => EntityType::AiSoftware,
            CliEntityType::AiEmbodied => EntityType::AiEmbodied,
            CliEntityType::Organization => EntityType::Organization,
            CliEntityType::Role => EntityType::Role,
            CliEntityType::Task => EntityType::Task,
            CliEntityType::Resource => EntityType::Resource,
            CliEntityType::Hybrid => EntityType::Hybrid,
        }
    }
}

#[tokio::main]
async fn main() -> Result<()> {
    let filter = tracing_subscriber::EnvFilter::try_from_default_env()
        .unwrap_or_else(|_| tracing_subscriber::EnvFilter::new("info"));
    tracing_subscriber::fmt().with_env_filter(filter).init();

    let cli = Cli::parse();

    match cli.command {
        None => {
            // No subcommand — print short usage hint and exit 0.
            println!("hub {} — Web4 Community Hub", hub_lib::VERSION);
            println!("Run `hub --help` for available commands.");
            Ok(())
        }
        Some(Command::Init {
            name, sovereign_lct, sovereign_hestia, sovereign_lct_id, sovereign_pubkey,
            hub_dir, storage,
        }) => {
            run_init(name, sovereign_lct, sovereign_hestia, sovereign_lct_id,
                     sovereign_pubkey, hub_dir, storage).await
        }
        Some(Command::GenLct { output, entity_type }) => {
            run_gen_lct(output, entity_type.into())
        }
        Some(Command::EnvelopeSign { identity, nonce, payload }) => {
            run_envelope_sign(identity, nonce, payload)
        }
        Some(Command::VerifyLedger { hub_dir }) => {
            run_verify_ledger(hub_dir)
        }
        Some(Command::Migrate { hub_dir, to }) => {
            run_migrate(hub_dir, to)
        }
        Some(Command::Serve { hub_dir, port, bind }) => {
            run_serve(hub_dir, port, bind).await
        }
        Some(Command::Status { hub_dir }) => run_status(hub_dir),
        Some(Command::AddMember { hub_dir, member_lct_id, name }) => {
            run_add_member(hub_dir, member_lct_id, name)
        }
        Some(Command::RemoveMember { hub_dir, member_lct_id, reason }) => {
            run_remove_member(hub_dir, member_lct_id, reason)
        }
        Some(Command::AssignRole { hub_dir, role, role_lct_id, member_lct_id }) => {
            run_assign_role(hub_dir, role, role_lct_id, member_lct_id)
        }
        Some(Command::RecordEvent { hub_dir, event_kind, title, attended_by }) => {
            run_record_event(hub_dir, event_kind, title, attended_by)
        }
        Some(Command::DeclareSkill { hub_dir, member_lct_id, skill }) => {
            run_declare_skill(hub_dir, member_lct_id, skill)
        }
        Some(Command::SetLaw { hub_dir, yaml, diff_summary }) => {
            run_set_law(hub_dir, yaml, diff_summary)
        }
        Some(Command::GetLaw { hub_dir }) => run_get_law(hub_dir),
        Some(Command::InitLaw { output, force }) => run_init_law(output, force),
        Some(Command::Query { subcommand }) => run_query(subcommand),
    }
}

// ---------- Sprint 4 CLI handlers ----------

fn parse_role(s: &str) -> Result<SocietyRole> {
    use SocietyRole::*;
    Ok(match s.to_lowercase().replace('-', "_").as_str() {
        "sovereign" => Sovereign,
        "law_oracle" | "laworacle" => LawOracle,
        "policy_entity" | "policyentity" => PolicyEntity,
        "treasurer" => Treasurer,
        "administrator" => Administrator,
        "archivist" => Archivist,
        "citizen" => Citizen,
        "witness" => Witness,
        "auditor" => Auditor,
        other => return Err(anyhow::anyhow!(
            "unknown role '{}'. Expected one of: sovereign, law_oracle, \
             policy_entity, treasurer, administrator, archivist, citizen, \
             witness, auditor", other
        )),
    })
}

fn run_status(hub_dir: PathBuf) -> Result<()> {
    let session = HubSession::open(&hub_dir)?;
    let st = session.status();
    println!("Chapter status:");
    println!("  Chapter dir:     {}", st.hub_dir.display());
    println!("  Chapter name:    {}", st.hub_name);
    println!("  Members:         {}", st.member_count);
    println!("  Ledger entries:  {}", st.ledger_entries);
    println!("  Head hash:       {}", st.head_hash);
    println!("  MCP port:        {} (config; not necessarily running)", st.mcp_port);
    Ok(())
}

fn run_add_member(hub_dir: PathBuf, member_lct_id: Uuid, name: Option<String>) -> Result<()> {
    let mut session = HubSession::open(&hub_dir)?;
    let entry = session.add_member(member_lct_id, name.clone())?;
    println!("Member added.");
    println!("  Member LCT:   {}", member_lct_id);
    if let Some(n) = name { println!("  Name:         {}", n); }
    println!("  Entry index:  {}", entry.index);
    println!("  Entry hash:   {}", entry.entry_hash);
    Ok(())
}

fn run_remove_member(hub_dir: PathBuf, member_lct_id: Uuid, reason: Option<String>) -> Result<()> {
    let mut session = HubSession::open(&hub_dir)?;
    let entry = session.remove_member(member_lct_id, reason)?;
    println!("Member removed.");
    println!("  Member LCT:   {}", member_lct_id);
    println!("  Entry index:  {}", entry.index);
    println!("  Entry hash:   {}", entry.entry_hash);
    Ok(())
}

fn run_assign_role(
    hub_dir: PathBuf,
    role: String,
    role_lct_id: Uuid,
    member_lct_id: Uuid,
) -> Result<()> {
    let parsed = parse_role(&role)?;
    let mut session = HubSession::open(&hub_dir)?;
    let entry = session.assign_role(parsed.clone(), role_lct_id, member_lct_id)?;
    println!("Role assigned.");
    println!("  Role:         {:?}", parsed);
    println!("  Role LCT:     {}", role_lct_id);
    println!("  Member LCT:   {}", member_lct_id);
    println!("  Entry index:  {}", entry.index);
    println!("  Entry hash:   {}", entry.entry_hash);
    Ok(())
}

fn run_record_event(
    hub_dir: PathBuf,
    event_kind: String,
    title: String,
    attended_by: Vec<Uuid>,
) -> Result<()> {
    let mut session = HubSession::open(&hub_dir)?;
    let entry = session.record_event(event_kind.clone(), title.clone(), attended_by.clone(), None)?;
    println!("Event recorded.");
    println!("  Kind:         {}", event_kind);
    println!("  Title:        {}", title);
    println!("  Attendees:    {}", attended_by.len());
    println!("  Entry index:  {}", entry.index);
    println!("  Entry hash:   {}", entry.entry_hash);
    Ok(())
}

fn run_set_law(hub_dir: PathBuf, yaml_path: PathBuf, diff_summary: Option<String>) -> Result<()> {
    let yaml = std::fs::read_to_string(&yaml_path)
        .with_context(|| format!("reading law YAML from {}", yaml_path.display()))?;
    // Parse + validate at the operator boundary so errors land clearly.
    let law = hub_lib::law::Law::parse_and_validate(&yaml)
        .context("parsing/validating law YAML")?;
    let version = law.version.clone();

    let mut session = HubSession::open(&hub_dir)?;
    let entry = session.set_law(&yaml, version.clone(), diff_summary.clone())?;

    println!("Law set.");
    println!("  Chapter dir:  {}", hub_dir.display());
    println!("  Version:      {}", version);
    println!("  Norms:        {}", law.norms.len());
    println!("  Procedures:   {}", law.procedures.len());
    println!("  Entry index:  {}", entry.index);
    println!("  Entry hash:   {}", entry.entry_hash);
    if let Some(s) = diff_summary {
        println!("  Diff summary: {}", s);
    }
    Ok(())
}

fn run_get_law(hub_dir: PathBuf) -> Result<()> {
    let session = HubSession::open(&hub_dir)?;
    match session.get_law()? {
        Some(yaml) => print!("{}", yaml),
        None => println!("No chapter law set."),
    }
    Ok(())
}

/// Starter chapter-law template — embedded at compile time so the
/// binary ships with it. Source: `web4/hub/examples/starter-law.yaml`.
const STARTER_LAW_YAML: &str = include_str!("../../examples/starter-law.yaml");

fn run_init_law(output: PathBuf, force: bool) -> Result<()> {
    if output.exists() && !force {
        anyhow::bail!(
            "{} already exists. Pass --force to overwrite, or pick a different --output path.",
            output.display()
        );
    }
    // Sanity-check that the embedded template still parses + validates.
    // If this fires, the starter template has drifted from the schema —
    // catch at write time, not at the operator's `set-law` boundary.
    hub_lib::law::Law::parse_and_validate(STARTER_LAW_YAML)
        .context("embedded starter-law.yaml failed to parse/validate (bug in the binary, not the operator)")?;

    if let Some(parent) = output.parent() {
        if !parent.as_os_str().is_empty() {
            std::fs::create_dir_all(parent)
                .with_context(|| format!("creating parent dir {}", parent.display()))?;
        }
    }
    std::fs::write(&output, STARTER_LAW_YAML)
        .with_context(|| format!("writing starter law to {}", output.display()))?;

    println!("Starter chapter-law written to {}.", output.display());
    println!();
    println!("Next steps:");
    println!("  1. Edit {} — adjust norms, admission, atp_issuance, etc.", output.display());
    println!("  2. Apply to a chapter:  hub set-law <chapter-dir> {}", output.display());
    println!("  3. If serve is running: curl -X POST http://<host>/v1/admin/reload-law");
    Ok(())
}

fn run_declare_skill(hub_dir: PathBuf, member_lct_id: Uuid, skill: String) -> Result<()> {
    let mut session = HubSession::open(&hub_dir)?;
    let entry = session.declare_skill(member_lct_id, skill.clone())?;
    println!("Skill declared.");
    println!("  Member LCT:   {}", member_lct_id);
    println!("  Skill:        {}", skill);
    println!("  Entry index:  {}", entry.index);
    println!("  Entry hash:   {}", entry.entry_hash);
    Ok(())
}

fn run_query(sub: QueryCommand) -> Result<()> {
    match sub {
        QueryCommand::Members { hub_dir } => {
            let session = HubSession::open(&hub_dir)?;
            let members = session.list_members();
            println!("Members ({}):", members.len());
            for m in members {
                let skills = if m.skills.is_empty() {
                    "(none)".to_string()
                } else {
                    m.skills.iter().cloned().collect::<Vec<_>>().join(", ")
                };
                println!("  - {:36}  {}  [{}]",
                    m.lct_id,
                    m.name.as_deref().unwrap_or("(unnamed)"),
                    skills);
            }
            Ok(())
        }
        QueryCommand::Skill { hub_dir, query } => {
            let session = HubSession::open(&hub_dir)?;
            let matches = session.find_skill(&query);
            println!("Skill search '{}' — {} match(es):", query, matches.len());
            for m in matches {
                println!("  - {} ({}): {}",
                    m.name.as_deref().unwrap_or("(unnamed)"),
                    m.lct_id,
                    m.skills.iter().cloned().collect::<Vec<_>>().join(", "));
            }
            Ok(())
        }
        QueryCommand::Chapter { hub_dir } => {
            let session = HubSession::open(&hub_dir)?;
            let society = session.society()?;
            let state = session.state();
            let unfilled = session.unfilled_base_roles()?;
            println!("Chapter:");
            println!("  Name:        {}", society.name);
            println!("  Society LCT: {}", society.lct_id);
            println!("  State:       {:?}", society.state);
            println!("  Founder:     {}", society.founder_lct_id);
            println!("  Members:     {}", state.member_count());
            println!("  Charter:     {}", society.charter_hash);
            println!("  Roles filled ({}):", society.roles.len());
            let mut roles: Vec<_> = society.roles.iter().collect();
            roles.sort_by(|a, b| a.0.cmp(b.0));
            for (role_key, assignment) in roles {
                println!("    {:18} role_lct={}  filled_by={}",
                    role_key, assignment.role_lct_id, assignment.filling_entity_lct_id);
            }
            if !unfilled.is_empty() {
                println!("  Roles unfilled ({}):", unfilled.len());
                for role in &unfilled {
                    println!("    {:?}", role);
                }
                println!("    (assign via `hub assign-role <chapter-dir> <role> <role-lct-id> <member-lct-id>` per chapter law)");
            }
            Ok(())
        }
    }
}

async fn run_serve(hub_dir: PathBuf, port_override: Option<u16>, bind: String) -> Result<()> {
    let config = HubConfig::load(hub_lib::hub::HubPaths::new(&hub_dir).config())?;
    let port = port_override.unwrap_or(config.daemon.mcp_port);
    let addr: SocketAddr = format!("{}:{}", bind, port).parse()?;

    // Both MCP and REST route through the signer abstraction (V2-7 §4
    // for MCP); both work for Local + Hestia mode chapters.
    // Construct a shared Law slot so both MCP + REST evaluate against
    // the same in-memory snapshot, and so the REST reload-law endpoint
    // refreshes both surfaces in one call.
    let initial_law = {
        let store = hub_lib::store::open_chapter_store(&hub_dir)?;
        match store.read_law()? {
            Some(yaml) => Some(hub_lib::law::Law::parse_and_validate(&yaml)?),
            None => None,
        }
    };
    let shared_law = std::sync::Arc::new(tokio::sync::RwLock::new(initial_law));
    let mcp_state = McpState::open_with_law(hub_dir.clone(), shared_law.clone())?;
    let rest_state = RestState::open_with_law(hub_dir.clone(), shared_law)?;
    // Admin UI reuses RestState (read-only; shares ledger + law snapshot).
    let admin_state = rest_state.clone();
    let app = mcp_router(mcp_state)
        .merge(rest_router(rest_state))
        .merge(admin::router(admin_state));

    tracing::info!(
        hub = %config.hub.name,
        hub_dir = %hub_dir.display(),
        bind = %addr,
        "HTTP server starting"
    );
    println!("hub serve — {} listening on http://{}", config.hub.name, addr);
    println!("  MCP tools:    http://{}/tools", addr);
    println!("  REST v1:      http://{}/v1/", addr);
    println!("  Admin UI:     http://{}/admin", addr);
    println!("  Stop:         Ctrl-C");

    let listener = tokio::net::TcpListener::bind(addr).await?;
    axum::serve(listener, app)
        .with_graceful_shutdown(shutdown_signal())
        .await?;

    println!("hub serve — shut down cleanly");
    Ok(())
}

async fn shutdown_signal() {
    let _ = tokio::signal::ctrl_c().await;
    tracing::info!("ctrl-c received — shutting down");
}

fn run_verify_ledger(hub_dir: PathBuf) -> Result<()> {
    let result = verify_chapter(&hub_dir)?;
    println!("Ledger verified.");
    println!("  Chapter dir:    {}", result.hub_dir.display());
    println!("  Chapter name:   {}", result.hub_name);
    println!("  Entries:        {}", result.entries);
    println!("  Head hash:      {}", result.head_hash);
    Ok(())
}

fn run_migrate(hub_dir: PathBuf, to: String) -> Result<()> {
    use std::str::FromStr;
    let target = hub_lib::store::BackendKind::from_str(&to)
        .context("parsing --to")?;
    println!("Migrating {} → {}", hub_dir.display(), target.as_str());
    let result = hub_lib::store::migrate_chapter(&hub_dir, target)
        .context("migrating chapter")?;
    if result.source_backend == result.target_backend {
        println!("Source backend is already {}; nothing to do.", target.as_str());
        return Ok(());
    }
    println!("  Source backend:  {}", result.source_backend.as_str());
    println!("  Target backend:  {}", result.target_backend.as_str());
    println!("  Charter copied:  {}", result.charter_copied);
    println!("  Society copied:  {}", result.society_copied);
    println!("  Ledger entries:  {}", result.ledger_entries_copied);
    println!("  Preserved (rollback-recoverable):");
    for p in &result.preserved_artifacts {
        println!("    {}", p.display());
    }
    println!();
    println!("Verifying migrated chapter end-to-end ...");
    let verify = verify_chapter(&hub_dir)
        .context("post-migration ledger verification failed")?;
    println!("Ledger verified on {} backend.", target.as_str());
    println!("  Entries:        {}", verify.entries);
    println!("  Head hash:      {}", verify.head_hash);
    Ok(())
}

async fn run_init(
    name: String,
    sovereign_lct: Option<PathBuf>,
    sovereign_hestia: Option<String>,
    sovereign_lct_id: Option<Uuid>,
    sovereign_pubkey: Option<String>,
    hub_dir: Option<PathBuf>,
    storage: String,
) -> Result<()> {
    use std::str::FromStr;
    let hub_dir = hub_dir.unwrap_or_else(|| PathBuf::from(slugify(&name)));
    let backend = hub_lib::store::BackendKind::from_str(&storage)
        .context("parsing --storage")?;

    let result = match (sovereign_lct, sovereign_hestia) {
        (Some(path), None) => {
            // Local mode
            init_chapter(InitArgs {
                hub_name: name,
                hub_dir,
                sovereign_lct_path: path,
                storage: Some(backend),
            })?
        }
        (None, Some(callback_url)) => {
            // Hestia mode — clap's `requires_all` guarantees lct_id + pubkey are present
            let lct_id = sovereign_lct_id.expect("clap requires_all");
            let pubkey_hex = sovereign_pubkey.expect("clap requires_all");
            println!("hub init: Hestia mode — Genesis will be signed by {}", callback_url);
            hub_lib::init::init_chapter_hestia(hub_lib::init::HestiaInitArgs {
                hub_name: name,
                hub_dir,
                sovereign_lct_id: lct_id,
                sovereign_pubkey_hex: pubkey_hex,
                hestia_callback_url: callback_url,
                storage: Some(backend),
            }).await?
        }
        (None, None) => {
            anyhow::bail!(
                "hub init requires one of: --sovereign-lct PATH (Local mode) \
                 OR --sovereign-hestia URL --sovereign-lct-id ID --sovereign-pubkey HEX (Hestia mode)"
            );
        }
        (Some(_), Some(_)) => unreachable!("clap conflicts_with should catch this"),
    };

    match result {
        InitResult::Initialized { society_lct_id, hub_dir, role_lcts } => {
            println!("Chapter initialized.");
            println!("  Chapter dir:     {}", hub_dir.display());
            println!("  Society LCT id:  {}", society_lct_id);
            println!("  Roles wired:     {}", role_lcts.len());
            for (role, role_lct_id) in &role_lcts {
                println!("    {:?}: {}", role, role_lct_id);
            }
            println!();
            println!("Next: in sprint 2 this is where you'd start recording events.");
            println!("      For now, inspect the chapter dir or run `hub init {} ...` again",
                     "<same-name>");
            println!("      to verify idempotency.");
        }
        InitResult::AlreadyInitialized { society_lct_id, hub_dir, hub_name } => {
            println!("Chapter already initialized — no changes made.");
            println!("  Chapter dir:     {}", hub_dir.display());
            println!("  Chapter name:    {}", hub_name);
            println!("  Society LCT id:  {}", society_lct_id);
        }
    }

    Ok(())
}

fn run_gen_lct(output: PathBuf, entity_type: EntityType) -> Result<()> {
    let identity = IdentityFile::generate(entity_type);
    identity.save(&output)?;
    println!("Identity generated.");
    println!("  File:          {}", output.display());
    println!("  LCT id:        {}", identity.lct.id);
    println!("  Entity type:   {:?}", identity.lct.entity_type);
    println!();
    println!("This file contains private key material. Protect it (chmod 600 recommended).");
    Ok(())
}

fn run_envelope_sign(identity_path: PathBuf, nonce: String, payload_json: String) -> Result<()> {
    use chrono::Utc;
    use hub_lib::envelope::{build_envelope, Challenge};

    let identity = IdentityFile::load(&identity_path)
        .with_context(|| format!("loading identity from {}", identity_path.display()))?;
    let kp = identity.keypair().context("reconstructing keypair")?;
    let payload: serde_json::Value = serde_json::from_str(&payload_json)
        .context("parsing --payload as JSON")?;

    // Build a Challenge-shaped struct from the user-supplied nonce. The
    // server checks LCT match + expiry on its own copy of the challenge;
    // build_envelope only needs the nonce string from this side.
    let now = Utc::now();
    let stub_challenge = Challenge {
        nonce,
        for_lct_id: identity.lct.id,
        issued_at: now,
        expires_at: now,
    };

    let envelope = build_envelope(identity.lct.id, &kp, &stub_challenge, payload)?;
    let json = serde_json::to_string_pretty(&envelope).context("serializing envelope")?;
    println!("{}", json);
    Ok(())
}

/// Slugify a chapter name into a filesystem-safe default dir name.
/// "Lisbon Chapter" → "lisbon-chapter".
fn slugify(name: &str) -> String {
    name.to_lowercase()
        .chars()
        .map(|c| if c.is_alphanumeric() { c } else { '-' })
        .collect::<String>()
        .split('-')
        .filter(|s| !s.is_empty())
        .collect::<Vec<_>>()
        .join("-")
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn slugify_handles_common_cases() {
        assert_eq!(slugify("Lisbon Chapter"), "lisbon-chapter");
        assert_eq!(slugify("NYC Chapter #1"), "nyc-chapter-1");
        // Unicode letters survive via char::is_alphanumeric — fine for chapter dirs.
        assert_eq!(slugify("São Paulo"), "são-paulo");
        assert_eq!(slugify("東京"), "東京");
        assert_eq!(slugify("   spaces   "), "spaces");
        assert_eq!(slugify(""), "");
    }
}
