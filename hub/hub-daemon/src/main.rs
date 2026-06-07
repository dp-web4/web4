// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Metalinxx Inc.

//! AIC Hub daemon — single-binary entrypoint.
//!
//! Sprint 1+2+3 surface: `hub init` + `hub gen-lct` + `hub verify-ledger`
//! + `hub serve` (MCP HTTP server). Subsequent sprints add CLI parity for
//! mutating commands (sprint 4), Docker entrypoint (sprint 5), and docs/
//! polish (sprint 6).

mod mcp;

use anyhow::Result;
use clap::{Parser, Subcommand};
use std::net::SocketAddr;
use std::path::PathBuf;

use hub_lib::chapter::ChapterConfig;
use hub_lib::identity::IdentityFile;
use hub_lib::init::{init_chapter, verify_chapter, InitArgs, InitResult};
use hub_lib::session::ChapterSession;
use uuid::Uuid;
use web4_core::lct::EntityType;
use web4_core::role::SocietyRole;

use crate::mcp::{router as mcp_router, McpState};

/// AIC Hub — minimum-viable Web4 society for a community chapter.
#[derive(Parser, Debug)]
#[command(name = "hub", version = hub_lib::VERSION, about, long_about = None)]
struct Cli {
    #[command(subcommand)]
    command: Option<Command>,
}

#[derive(Subcommand, Debug)]
enum Command {
    /// Initialize a new chapter society in the given directory.
    Init {
        /// Human-readable chapter name (e.g. "Lisbon Chapter").
        name: String,

        /// Path to the Sovereign identity file (LCT + keypair). Generate
        /// one with `hub gen-lct` if you don't have one yet.
        #[arg(long)]
        sovereign_lct: PathBuf,

        /// Directory to create the chapter in. Defaults to ./<name-slug>.
        #[arg(long)]
        chapter_dir: Option<PathBuf>,
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

    /// Verify the integrity of a chapter's ledger end-to-end.
    ///
    /// Checks: every entry's signature against the actor LCT, every
    /// entry's hash matches recomputation, prev-hash chain is unbroken,
    /// indices are sequential. Errors loudly if any entry is tampered.
    VerifyLedger {
        /// Path to the chapter directory.
        chapter_dir: PathBuf,
    },

    /// Run the MCP HTTP server for a chapter. Daemon loads the Sovereign
    /// keypair from config.toml and signs ledger entries on behalf of
    /// authenticated clients (MVP: localhost only; per-client signed
    /// envelopes are V2).
    Serve {
        /// Chapter directory.
        chapter_dir: PathBuf,

        /// Override the port from config.toml.
        #[arg(long)]
        port: Option<u16>,

        /// Bind address (default 127.0.0.1 — local-only).
        #[arg(long, default_value = "127.0.0.1")]
        bind: String,
    },

    /// Print chapter status (name, members, ledger length, head hash, port).
    Status {
        chapter_dir: PathBuf,
    },

    /// Add a member to the chapter.
    AddMember {
        chapter_dir: PathBuf,
        /// Member's LCT id (uuid).
        member_lct_id: Uuid,
        /// Optional display name.
        #[arg(long)]
        name: Option<String>,
    },

    /// Remove a member from the chapter.
    RemoveMember {
        chapter_dir: PathBuf,
        member_lct_id: Uuid,
        #[arg(long)]
        reason: Option<String>,
    },

    /// Assign a role to a member.
    AssignRole {
        chapter_dir: PathBuf,
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
        chapter_dir: PathBuf,
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
        chapter_dir: PathBuf,
        member_lct_id: Uuid,
        skill: String,
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
    Members { chapter_dir: PathBuf },
    /// Find members by skill (case-insensitive substring).
    Skill {
        chapter_dir: PathBuf,
        query: String,
    },
    /// Print chapter identity + role-fill snapshot.
    Chapter { chapter_dir: PathBuf },
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
            println!("hub {} — AIC Hub", hub_lib::VERSION);
            println!("Run `hub --help` for available commands.");
            Ok(())
        }
        Some(Command::Init { name, sovereign_lct, chapter_dir }) => {
            run_init(name, sovereign_lct, chapter_dir)
        }
        Some(Command::GenLct { output, entity_type }) => {
            run_gen_lct(output, entity_type.into())
        }
        Some(Command::VerifyLedger { chapter_dir }) => {
            run_verify_ledger(chapter_dir)
        }
        Some(Command::Serve { chapter_dir, port, bind }) => {
            run_serve(chapter_dir, port, bind).await
        }
        Some(Command::Status { chapter_dir }) => run_status(chapter_dir),
        Some(Command::AddMember { chapter_dir, member_lct_id, name }) => {
            run_add_member(chapter_dir, member_lct_id, name)
        }
        Some(Command::RemoveMember { chapter_dir, member_lct_id, reason }) => {
            run_remove_member(chapter_dir, member_lct_id, reason)
        }
        Some(Command::AssignRole { chapter_dir, role, role_lct_id, member_lct_id }) => {
            run_assign_role(chapter_dir, role, role_lct_id, member_lct_id)
        }
        Some(Command::RecordEvent { chapter_dir, event_kind, title, attended_by }) => {
            run_record_event(chapter_dir, event_kind, title, attended_by)
        }
        Some(Command::DeclareSkill { chapter_dir, member_lct_id, skill }) => {
            run_declare_skill(chapter_dir, member_lct_id, skill)
        }
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

fn run_status(chapter_dir: PathBuf) -> Result<()> {
    let session = ChapterSession::open(&chapter_dir)?;
    let st = session.status();
    println!("Chapter status:");
    println!("  Chapter dir:     {}", st.chapter_dir.display());
    println!("  Chapter name:    {}", st.chapter_name);
    println!("  Members:         {}", st.member_count);
    println!("  Ledger entries:  {}", st.ledger_entries);
    println!("  Head hash:       {}", st.head_hash);
    println!("  MCP port:        {} (config; not necessarily running)", st.mcp_port);
    Ok(())
}

fn run_add_member(chapter_dir: PathBuf, member_lct_id: Uuid, name: Option<String>) -> Result<()> {
    let mut session = ChapterSession::open(&chapter_dir)?;
    let entry = session.add_member(member_lct_id, name.clone())?;
    println!("Member added.");
    println!("  Member LCT:   {}", member_lct_id);
    if let Some(n) = name { println!("  Name:         {}", n); }
    println!("  Entry index:  {}", entry.index);
    println!("  Entry hash:   {}", entry.entry_hash);
    Ok(())
}

fn run_remove_member(chapter_dir: PathBuf, member_lct_id: Uuid, reason: Option<String>) -> Result<()> {
    let mut session = ChapterSession::open(&chapter_dir)?;
    let entry = session.remove_member(member_lct_id, reason)?;
    println!("Member removed.");
    println!("  Member LCT:   {}", member_lct_id);
    println!("  Entry index:  {}", entry.index);
    println!("  Entry hash:   {}", entry.entry_hash);
    Ok(())
}

fn run_assign_role(
    chapter_dir: PathBuf,
    role: String,
    role_lct_id: Uuid,
    member_lct_id: Uuid,
) -> Result<()> {
    let parsed = parse_role(&role)?;
    let mut session = ChapterSession::open(&chapter_dir)?;
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
    chapter_dir: PathBuf,
    event_kind: String,
    title: String,
    attended_by: Vec<Uuid>,
) -> Result<()> {
    let mut session = ChapterSession::open(&chapter_dir)?;
    let entry = session.record_event(event_kind.clone(), title.clone(), attended_by.clone(), None)?;
    println!("Event recorded.");
    println!("  Kind:         {}", event_kind);
    println!("  Title:        {}", title);
    println!("  Attendees:    {}", attended_by.len());
    println!("  Entry index:  {}", entry.index);
    println!("  Entry hash:   {}", entry.entry_hash);
    Ok(())
}

fn run_declare_skill(chapter_dir: PathBuf, member_lct_id: Uuid, skill: String) -> Result<()> {
    let mut session = ChapterSession::open(&chapter_dir)?;
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
        QueryCommand::Members { chapter_dir } => {
            let session = ChapterSession::open(&chapter_dir)?;
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
        QueryCommand::Skill { chapter_dir, query } => {
            let session = ChapterSession::open(&chapter_dir)?;
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
        QueryCommand::Chapter { chapter_dir } => {
            let session = ChapterSession::open(&chapter_dir)?;
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

async fn run_serve(chapter_dir: PathBuf, port_override: Option<u16>, bind: String) -> Result<()> {
    let config = ChapterConfig::load(hub_lib::chapter::ChapterPaths::new(&chapter_dir).config())?;
    let port = port_override.unwrap_or(config.daemon.mcp_port);
    let addr: SocketAddr = format!("{}:{}", bind, port).parse()?;

    let state = McpState::open(chapter_dir.clone())?;
    let app = mcp_router(state);

    tracing::info!(
        chapter = %config.chapter.name,
        chapter_dir = %chapter_dir.display(),
        bind = %addr,
        "MCP HTTP server starting"
    );
    println!("hub serve — {} listening on http://{}", config.chapter.name, addr);
    println!("  Tools:        http://{}/tools", addr);
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

fn run_verify_ledger(chapter_dir: PathBuf) -> Result<()> {
    let result = verify_chapter(&chapter_dir)?;
    println!("Ledger verified.");
    println!("  Chapter dir:    {}", result.chapter_dir.display());
    println!("  Chapter name:   {}", result.chapter_name);
    println!("  Entries:        {}", result.entries);
    println!("  Head hash:      {}", result.head_hash);
    Ok(())
}

fn run_init(name: String, sovereign_lct: PathBuf, chapter_dir: Option<PathBuf>) -> Result<()> {
    let chapter_dir = chapter_dir.unwrap_or_else(|| PathBuf::from(slugify(&name)));

    let result = init_chapter(InitArgs {
        chapter_name: name,
        chapter_dir,
        sovereign_lct_path: sovereign_lct,
    })?;

    match result {
        InitResult::Initialized { society_lct_id, chapter_dir, role_lcts } => {
            println!("Chapter initialized.");
            println!("  Chapter dir:     {}", chapter_dir.display());
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
        InitResult::AlreadyInitialized { society_lct_id, chapter_dir, chapter_name } => {
            println!("Chapter already initialized — no changes made.");
            println!("  Chapter dir:     {}", chapter_dir.display());
            println!("  Chapter name:    {}", chapter_name);
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
        assert_eq!(slugify("AIC NYC #1"), "aic-nyc-1");
        // Unicode letters survive via char::is_alphanumeric — fine for chapter dirs.
        assert_eq!(slugify("São Paulo"), "são-paulo");
        assert_eq!(slugify("東京"), "東京");
        assert_eq!(slugify("   spaces   "), "spaces");
        assert_eq!(slugify(""), "");
    }
}
