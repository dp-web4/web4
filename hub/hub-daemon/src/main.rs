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
mod rate_limit;
mod rest;

use anyhow::{Context, Result};
use axum::Router;
use clap::{Parser, Subcommand};
use std::net::{Ipv4Addr, SocketAddr};
use std::path::PathBuf;

use hub_lib::hub::HubConfig;
use hub_lib::identity::IdentityFile;
use hub_lib::init::{init_hub, verify_hub, InitArgs, InitResult};
use hub_lib::session::HubSession;
use uuid::Uuid;
use web4_core::lct::EntityType;
use web4_core::role::SocietyRole;

use crate::mcp::{read_router as mcp_read_router, operator_read_router as mcp_operator_read_router, write_router as mcp_write_router, McpState};
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
    /// Initialize a new hub society in the given directory.
    ///
    /// Two modes:
    /// - **Local mode** (MVP-compatible): pass `--sovereign-lct PATH` to a
    ///   local IdentityFile. The hub loads the keypair from the file.
    /// - **Hestia mode** (V2-7+, recommended): pass
    ///   `--sovereign-hestia URL --sovereign-lct-id ID --sovereign-pubkey HEX`.
    ///   The hub holds NO keypair; Genesis is signed by Hestia via the
    ///   callback URL.
    Init {
        /// Human-readable hub name (e.g. "Lisbon Chapter").
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
        /// for better query performance + simpler ops. `dynamodb` stores
        /// state in a single DynamoDB table; requires --dynamodb-table.
        #[arg(long, default_value = "file")]
        storage: String,

        /// DynamoDB table name (required when --storage dynamodb).
        #[arg(long, required_if_eq("storage", "dynamodb"))]
        dynamodb_table: Option<String>,

        /// Optional AWS region for DynamoDB (default: SDK default chain).
        #[arg(long)]
        dynamodb_region: Option<String>,

        /// Optional DynamoDB endpoint override, e.g. http://localhost:8000.
        #[arg(long)]
        dynamodb_endpoint: Option<String>,
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

    /// Migrate a plaintext identity file to an encrypted vault in place (the
    /// vault doctrine). Reads via load_auto (plaintext OR already-encrypted),
    /// re-writes encrypted under the resolved passphrase (HUB_PASSPHRASE / TTY
    /// prompt; empty = a deliberate NULL choice). Idempotent — re-sealing an
    /// already-encrypted file just re-keys it. Back up the file first.
    SealIdentity {
        /// Path to the identity file to seal in place.
        path: PathBuf,
    },

    /// The **stub-console unlock plugin**: unlock a locked, running hub by
    /// presenting the tier-1 passphrase. Prompts for the passphrase (or reads
    /// `HUB_PASSPHRASE`), **uses it once and never stores it**, and POSTs it to
    /// the hub's local-only `/unlock` slot (127.0.0.1), promoting it locked →
    /// unlocked in place. Run this on the hub host. Empty (just Enter) = the
    /// explicit NULL-passphrase choice.
    Unlock {
        /// Port the hub is serving on (default 8770).
        #[arg(long, default_value = "8770")]
        port: u16,
    },

    /// Write the clear tier-0 `public-identity.json` (hub id, name, founding
    /// sovereign, pubkey) so a locked-shell hub can identify itself on
    /// `/.well-known` and accept `hub unlock`. Reads the encrypted store +
    /// identity with the passphrase (HUB_PASSPHRASE / prompt). Run once per hub.
    ExportPublicIdentity {
        /// The hub data directory.
        hub_dir: PathBuf,
    },

    /// Rotate the vault passphrase to one YOU choose (memorable, operator-picked —
    /// the hub never dictates it). Re-keys the Sovereign identity, the SQLCipher
    /// state store, and the protected tier from the current passphrase to a new
    /// one. Stop the hub first; ignite with the new phrase via `hub unlock` after.
    RotatePassphrase {
        /// The hub data directory.
        hub_dir: PathBuf,
    },

    /// Rotate the operator-plane bearer token. Generates a new 256-bit token,
    /// writes it to `<hub-dir>/operator.token` (0600), and prints the new
    /// fingerprint. The old token is invalidated immediately; any clients using
    /// it must be reconfigured. Requires `HUB_OPERATOR_AUTH=token`.
    RotateOperatorToken {
        /// The hub data directory.
        hub_dir: PathBuf,
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

    /// PAIRED-CHANNELS Sprint E/F: encrypt a pair-message body at the
    /// endpoint side. Uses the LCT identity file + peer's LCT pubkey
    /// + pair_id to derive the ECDH session key, then ChaCha20-Poly1305
    /// AEAD-encrypts the plaintext. Output: base64 of (nonce ‖ ct).
    ///
    /// **Forward secrecy (Sprint F):** if BOTH `--my-ephemeral-secret`
    /// and `--peer-ephemeral-pub` are supplied, the FS-mixing path is
    /// used (session key derived from static_ECDH || ephemeral_ECDH).
    /// Compromise of LCT keys after the fact does NOT decrypt past
    /// sessions that used FS. Without these flags, falls back to the
    /// Sprint E static-key-only derivation.
    PairEncrypt {
        /// Path to the sender's IdentityFile.
        #[arg(long)]
        identity: PathBuf,
        /// Peer's LCT public key (hex). Get from their identity file.
        #[arg(long)]
        peer_pubkey: String,
        /// Pair id this message is for (mixed into session-key HKDF).
        #[arg(long)]
        pair_id: Uuid,
        /// Plaintext body.
        #[arg(long)]
        plaintext: String,
        /// Sprint F: sender's per-session X25519 ephemeral SECRET (hex).
        /// Pair with --peer-ephemeral-pub.
        #[arg(long)]
        my_ephemeral_secret: Option<String>,
        /// Sprint F: peer's per-session X25519 ephemeral PUBLIC (hex).
        /// Read from pair detail's counterparty_ephemeral_pub_hex (if
        /// you are initiator) or initiator_ephemeral_pub_hex (if you
        /// are counterparty).
        #[arg(long)]
        peer_ephemeral_pub: Option<String>,
    },

    /// PAIRED-CHANNELS Sprint E/F: decrypt a pair-message body.
    /// Symmetric inverse of `pair-encrypt`. Errors if AEAD fails
    /// (wrong key, tampered, wrong pair_id, wrong ephemeral).
    PairDecrypt {
        #[arg(long)]
        identity: PathBuf,
        #[arg(long)]
        peer_pubkey: String,
        #[arg(long)]
        pair_id: Uuid,
        /// Base64-encoded sealed blob (output of pair-encrypt).
        #[arg(long)]
        ciphertext_b64: String,
        /// Sprint F: my per-session ephemeral SECRET (hex).
        #[arg(long)]
        my_ephemeral_secret: Option<String>,
        /// Sprint F: peer's per-session ephemeral PUBLIC (hex).
        #[arg(long)]
        peer_ephemeral_pub: Option<String>,
    },

    /// PAIRED-CHANNELS Sprint F: generate a fresh X25519 ephemeral
    /// keypair for a pair session. Output: JSON with `public_hex`
    /// (publish in pair_request / pair_confirm) and `secret_hex`
    /// (KEEP LOCAL — wipe when the pair ends to honor FS).
    PairGenerateEphemeral,

    /// Verify the integrity of a chapter's ledger end-to-end.
    ///
    /// Checks: every entry's signature against the actor LCT, every
    /// entry's hash matches recomputation, prev-hash chain is unbroken,
    /// indices are sequential. Errors loudly if any entry is tampered.
    VerifyLedger {
        /// Path to the hub directory.
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
        /// Path to the hub directory.
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

        /// Operator-plane port, always bound to 127.0.0.1 only (never exposed to
        /// the network). Serves the admit/deny/remove/re-key admin API + write GUI.
        /// Set to 0 to disable the operator plane entirely. (8771 is taken by the
        /// membox sidecar, so the default is 8772.)
        #[arg(long, default_value_t = 8772)]
        admin_port: u16,
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

    /// Assign a role to a member. The role LCT is society-managed (created
    /// on first fill, reused on rotation) — no role-lct-id argument needed.
    AssignRole {
        hub_dir: PathBuf,
        /// One of: sovereign | law_oracle | policy_entity | treasurer
        /// | administrator | archivist | citizen | witness | auditor.
        role: String,
        /// The member LCT id.
        member_lct_id: Uuid,
    },

    /// Record a hub event (demo night, workshop, etc.).
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

    /// Update a member's profile fields (for semantic discovery). Pass one or
    /// more `key=value` or `key@visibility=value` pairs, e.g.
    /// `skills="..." interests@public="..."`. Visibility is `self`, `members`,
    /// or `public`; omitted defaults to `members`. An empty value clears that
    /// field.
    SetProfile {
        hub_dir: PathBuf,
        member_lct_id: Uuid,
        /// `key=value` or `key@visibility=value` pairs (repeatable).
        #[arg(value_name = "KEY[@VISIBILITY]=VALUE", required = true)]
        fields: Vec<String>,
    },

    /// Set (or amend) the chapter's law from a YAML file (V2-8).
    /// Validates the YAML against the hub-law schema, writes it
    /// to the hub store, and appends a LawAmended event to the
    /// ledger for audit.
    SetLaw {
        hub_dir: PathBuf,
        /// Path to a YAML file matching the hub-law schema (see
        /// web4-standard/core-spec/hub-law-schema.md).
        yaml: PathBuf,
        /// Optional one-line summary of what changed.
        #[arg(long)]
        diff_summary: Option<String>,
    },

    /// Print the current hub law YAML (or report none is set).
    GetLaw {
        hub_dir: PathBuf,
    },

    /// Pin (or rotate) an existing member's channel public key — the member
    /// key-enrollment step. Members admitted without a pubkey cannot open the
    /// sealed channel; the member generates a keypair locally, shares the
    /// public half, and the Sovereign pins it here. Appends a MemberKeyPinned
    /// event; restart `hub serve` to re-seed the live resolver.
    SetMemberKey {
        hub_dir: PathBuf,
        /// The member's LCT id.
        member_lct_id: Uuid,
        /// Hex-encoded 32-byte Ed25519 public key (the member keeps the secret half).
        pubkey_hex: String,
    },

    /// Write the starter hub-law template to a file the operator
    /// can review + edit, then apply via `hub set-law`. Doesn't touch
    /// any hub directly.
    InitLaw {
        /// Where to write the starter YAML (e.g. ./hub-law.yaml).
        #[arg(default_value = "./hub-law.yaml")]
        output: PathBuf,
        /// Overwrite if the file already exists.
        #[arg(long)]
        force: bool,
    },

    /// V2-9 Phase 1: Sovereign Council management.
    ///
    /// Multi-Sovereign Council per architecture commitment #5. Phase 1
    /// ships data-model + management + admin UI; threshold is recorded
    /// but NOT yet enforced on `submit_event` (single-Sovereign signing
    /// still suffices). Phase 2 adds the proposal/aggregation flow that
    /// gates council-gated acts on M-of-N counter-signatures.
    Council {
        #[command(subcommand)]
        subcommand: CouncilCommand,
    },

    /// Query chapter state (members, skills, etc.).
    Query {
        #[command(subcommand)]
        subcommand: QueryCommand,
    },

    /// Turnkey setup for a deployment archetype (the `hub up` kit). Writes a
    /// fail-closed config profile (env + starter law + operator token) and prints
    /// the exact go-live runbook — one command for operators with no IT background.
    Up {
        /// Hub directory (society state lives here).
        #[arg(default_value = "./hub")]
        hub_dir: PathBuf,
        /// Deployment archetype: dev | private-vpn | public-managed |
        /// public-selfhost | public-tunnel. Omit to be prompted.
        #[arg(long)]
        profile: Option<String>,
        /// Public hostname for the public archetypes (e.g. hub.4-gov.org).
        #[arg(long)]
        domain: Option<String>,
        /// Don't prompt; error if a required value is missing (for scripts).
        #[arg(long)]
        yes: bool,
    },
}

#[derive(Subcommand, Debug)]
enum CouncilCommand {
    /// Admit a Sovereign Council holder. They become a co-Sovereign
    /// (in the resolver; can sign envelopes in Phase 2). Pubkey is
    /// pinned into the ledger so future verification needs no registry.
    Add {
        hub_dir: PathBuf,
        /// The new holder's LCT id (uuid).
        member_lct_id: Uuid,
        /// The new holder's public key (hex-encoded 32 bytes). Get
        /// from their identity file or `hub gen-lct`'s output.
        #[arg(long)]
        pubkey: String,
        /// Optional display name.
        #[arg(long)]
        name: Option<String>,
    },
    /// Remove a Sovereign Council holder.
    Remove {
        hub_dir: PathBuf,
        member_lct_id: Uuid,
        /// Removal kind for audit trail.
        #[arg(long, value_enum, default_value = "resigned")]
        kind: CliRoleEventKind,
        #[arg(long)]
        reason: Option<String>,
    },
    /// Set the council's M-of-N threshold. N is derived from
    /// holder count + 1 (the founding Sovereign) at apply time.
    /// Recorded but not yet enforced — Phase 2.
    SetThreshold {
        hub_dir: PathBuf,
        /// M — minimum number of signatures required.
        m: u32,
    },
    /// Show the current council state.
    Show {
        hub_dir: PathBuf,
    },
}

#[derive(Copy, Clone, Debug, clap::ValueEnum)]
enum CliRoleEventKind {
    Resigned,
    Ejected,
    Elected,
}

impl From<CliRoleEventKind> for web4_core::role::RoleEventKind {
    fn from(c: CliRoleEventKind) -> Self {
        use web4_core::role::RoleEventKind;
        match c {
            CliRoleEventKind::Resigned => RoleEventKind::FillerResigned,
            CliRoleEventKind::Ejected => RoleEventKind::FillerEjected,
            CliRoleEventKind::Elected => RoleEventKind::FillerElected,
        }
    }
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
            hub_dir, storage, dynamodb_table, dynamodb_region, dynamodb_endpoint,
        }) => {
            run_init(name, sovereign_lct, sovereign_hestia, sovereign_lct_id,
                     sovereign_pubkey, hub_dir, storage,
                     dynamodb_table, dynamodb_region, dynamodb_endpoint).await
        }
        Some(Command::GenLct { output, entity_type }) => {
            run_gen_lct(output, entity_type.into()).await
        }
        Some(Command::SealIdentity { path }) => run_seal_identity(path).await,
        Some(Command::Unlock { port }) => run_unlock(port).await,
        Some(Command::ExportPublicIdentity { hub_dir }) => run_export_public_identity(hub_dir).await,
        Some(Command::RotatePassphrase { hub_dir }) => run_rotate_passphrase(hub_dir).await,
        Some(Command::RotateOperatorToken { hub_dir }) => run_rotate_operator_token(hub_dir).await,
        Some(Command::EnvelopeSign { identity, nonce, payload }) => {
            run_envelope_sign(identity, nonce, payload).await
        }
        Some(Command::PairEncrypt {
            identity, peer_pubkey, pair_id, plaintext,
            my_ephemeral_secret, peer_ephemeral_pub,
        }) => {
            run_pair_encrypt(identity, peer_pubkey, pair_id, plaintext,
                my_ephemeral_secret, peer_ephemeral_pub).await
        }
        Some(Command::PairDecrypt {
            identity, peer_pubkey, pair_id, ciphertext_b64,
            my_ephemeral_secret, peer_ephemeral_pub,
        }) => {
            run_pair_decrypt(identity, peer_pubkey, pair_id, ciphertext_b64,
                my_ephemeral_secret, peer_ephemeral_pub).await
        }
        Some(Command::PairGenerateEphemeral) => {
            run_pair_generate_ephemeral().await
        }
        Some(Command::VerifyLedger { hub_dir }) => {
            run_verify_ledger(hub_dir).await
        }
        Some(Command::Migrate { hub_dir, to }) => {
            run_migrate(hub_dir, to).await
        }
        Some(Command::Serve { hub_dir, port, bind, admin_port }) => {
            run_serve(hub_dir, port, bind, admin_port).await
        }
        Some(Command::Status { hub_dir }) => run_status(hub_dir).await,
        Some(Command::AddMember { hub_dir, member_lct_id, name }) => {
            run_add_member(hub_dir, member_lct_id, name).await
        }
        Some(Command::RemoveMember { hub_dir, member_lct_id, reason }) => {
            run_remove_member(hub_dir, member_lct_id, reason).await
        }
        Some(Command::AssignRole { hub_dir, role, member_lct_id }) => {
            run_assign_role(hub_dir, role, member_lct_id).await
        }
        Some(Command::RecordEvent { hub_dir, event_kind, title, attended_by }) => {
            run_record_event(hub_dir, event_kind, title, attended_by).await
        }
        Some(Command::DeclareSkill { hub_dir, member_lct_id, skill }) => {
            run_declare_skill(hub_dir, member_lct_id, skill).await
        }
        Some(Command::SetProfile { hub_dir, member_lct_id, fields }) => {
            run_set_profile(hub_dir, member_lct_id, fields).await
        }
        Some(Command::SetLaw { hub_dir, yaml, diff_summary }) => {
            run_set_law(hub_dir, yaml, diff_summary).await
        }
        Some(Command::GetLaw { hub_dir }) => run_get_law(hub_dir).await,
        Some(Command::SetMemberKey { hub_dir, member_lct_id, pubkey_hex }) => {
            run_set_member_key(hub_dir, member_lct_id, pubkey_hex).await
        }
        Some(Command::InitLaw { output, force }) => run_init_law(output, force).await,
        Some(Command::Up { hub_dir, profile, domain, yes }) => run_up(hub_dir, profile, domain, yes).await,
        Some(Command::Council { subcommand }) => run_council(subcommand).await,
        Some(Command::Query { subcommand }) => run_query(subcommand).await,
    }
}

async fn run_council(sub: CouncilCommand) -> Result<()> {
    match sub {
        CouncilCommand::Add { hub_dir, member_lct_id, pubkey, name } => {
            // Validate pubkey hex shape early so the operator gets a clear
            // error at the CLI boundary rather than at envelope-verify time.
            let decoded = hex::decode(&pubkey)
                .context("decoding --pubkey as hex")?;
            if decoded.len() != 32 {
                anyhow::bail!("--pubkey must be 32 bytes (got {})", decoded.len());
            }
            let mut session = HubSession::open(&hub_dir).await?;
            // Idempotency: don't double-admit an existing holder (the projection
            // would absorb it as a set-insert, but the ledger would carry a
            // redundant CouncilMemberAdded).
            if session.state().council_holders.contains(&member_lct_id) {
                anyhow::bail!("{} is already a Sovereign Council holder", member_lct_id);
            }
            let entry = session.add_council_member(member_lct_id, pubkey, name.clone()).await?;
            println!("Council member added.");
            println!("  Member LCT:   {}", member_lct_id);
            if let Some(n) = name { println!("  Name:         {}", n); }
            println!("  Entry index:  {}", entry.index);
            println!("  Entry hash:   {}", entry.entry_hash);
            println!();
            println!("Note: V2-9 Phase 1 records council state + adds the holder to the");
            println!("resolver. Phase 2 will add the M-of-N proposal/aggregation flow.");
            Ok(())
        }
        CouncilCommand::Remove { hub_dir, member_lct_id, kind, reason } => {
            let mut session = HubSession::open(&hub_dir).await?;
            let entry = session.remove_council_member(member_lct_id, kind.into(), reason).await?;
            println!("Council member removed.");
            println!("  Member LCT:   {}", member_lct_id);
            println!("  Entry index:  {}", entry.index);
            println!("  Entry hash:   {}", entry.entry_hash);
            Ok(())
        }
        CouncilCommand::SetThreshold { hub_dir, m } => {
            let mut session = HubSession::open(&hub_dir).await?;
            let (entry_index, entry_hash) = {
                let entry = session.set_council_threshold(m).await?;
                (entry.index, entry.entry_hash.clone())
            };
            let state = session.state();
            let (eff_m, n) = state.council_threshold.unwrap_or((1, 1));
            println!("Council threshold set.");
            println!("  Requested M:  {}", m);
            println!("  Applied:      {}-of-{}", eff_m, n);
            println!("  Entry index:  {}", entry_index);
            println!("  Entry hash:   {}", entry_hash);
            if m != eff_m {
                println!("  Note:         requested M was clamped to applied (1..=N).");
            }
            println!();
            println!("Note: threshold is recorded but NOT yet enforced on submit_event.");
            println!("Phase 2 will gate council-gated acts on M-of-N counter-signatures.");
            Ok(())
        }
        CouncilCommand::Show { hub_dir } => {
            let session = HubSession::open(&hub_dir).await?;
            let state = session.state();
            let society = session.society().await?;
            println!("Sovereign Council:");
            println!("  Founding Sovereign: {}", society.founder_lct_id);
            println!("  Council holders: {}", state.council_holders.len());
            for holder in &state.council_holders {
                let name = state.members.get(holder)
                    .and_then(|m| m.name.clone())
                    .unwrap_or_else(|| "(unnamed)".into());
                println!("    - {} {}", holder, name);
            }
            match state.council_threshold {
                Some((m, n)) => println!("  Threshold: {}-of-{} (informational; not yet enforced)", m, n),
                None => println!("  Threshold: single-signer (none set)"),
            }
            Ok(())
        }
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

async fn run_status(hub_dir: PathBuf) -> Result<()> {
    let session = HubSession::open(&hub_dir).await?;
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

async fn run_add_member(hub_dir: PathBuf, member_lct_id: Uuid, name: Option<String>) -> Result<()> {
    let mut session = HubSession::open(&hub_dir).await?;
    let entry = session.add_member(member_lct_id, name.clone()).await?;
    println!("Member added.");
    println!("  Member LCT:   {}", member_lct_id);
    if let Some(n) = name { println!("  Name:         {}", n); }
    println!("  Entry index:  {}", entry.index);
    println!("  Entry hash:   {}", entry.entry_hash);
    Ok(())
}

async fn run_remove_member(hub_dir: PathBuf, member_lct_id: Uuid, reason: Option<String>) -> Result<()> {
    let mut session = HubSession::open(&hub_dir).await?;
    let entry = session.remove_member(member_lct_id, reason).await?;
    println!("Member removed.");
    println!("  Member LCT:   {}", member_lct_id);
    println!("  Entry index:  {}", entry.index);
    println!("  Entry hash:   {}", entry.entry_hash);
    Ok(())
}

async fn run_assign_role(
    hub_dir: PathBuf,
    role: String,
    member_lct_id: Uuid,
) -> Result<()> {
    let parsed = parse_role(&role)?;
    let mut session = HubSession::open(&hub_dir).await?;
    let entry = session.assign_role(parsed.clone(), member_lct_id).await?;
    println!("Role assigned.");
    println!("  Role:         {:?}", parsed);
    println!("  Member LCT:   {}", member_lct_id);
    println!("  Entry index:  {}", entry.index);
    println!("  Entry hash:   {}", entry.entry_hash);
    Ok(())
}

async fn run_record_event(
    hub_dir: PathBuf,
    event_kind: String,
    title: String,
    attended_by: Vec<Uuid>,
) -> Result<()> {
    let mut session = HubSession::open(&hub_dir).await?;
    let entry = session.record_event(event_kind.clone(), title.clone(), attended_by.clone(), None).await?;
    println!("Event recorded.");
    println!("  Kind:         {}", event_kind);
    println!("  Title:        {}", title);
    println!("  Attendees:    {}", attended_by.len());
    println!("  Entry index:  {}", entry.index);
    println!("  Entry hash:   {}", entry.entry_hash);
    Ok(())
}

async fn run_set_member_key(hub_dir: PathBuf, member_lct_id: Uuid, pubkey_hex: String) -> Result<()> {
    let mut session = HubSession::open(&hub_dir).await?;
    let entry = session.set_member_key(member_lct_id, pubkey_hex.clone()).await?;
    println!("Member key pinned.");
    println!("  Member LCT:   {member_lct_id}");
    println!("  Pubkey:       {pubkey_hex}");
    println!("  Entry index:  {}", entry.index);
    println!("  Entry hash:   {}", entry.entry_hash);
    println!("  NOTE: restart `hub serve` so the live resolver re-seeds from the ledger.");
    Ok(())
}

async fn run_set_law(hub_dir: PathBuf, yaml_path: PathBuf, diff_summary: Option<String>) -> Result<()> {
    let yaml = std::fs::read_to_string(&yaml_path)
        .with_context(|| format!("reading law YAML from {}", yaml_path.display()))?;
    // Parse + validate at the operator boundary so errors land clearly.
    let law = hub_lib::law::Law::parse_and_validate(&yaml)
        .context("parsing/validating law YAML")?;
    let version = law.version.clone();

    let mut session = HubSession::open(&hub_dir).await?;
    let entry = session.set_law(&yaml, version.clone(), diff_summary.clone()).await?;

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

async fn run_get_law(hub_dir: PathBuf) -> Result<()> {
    let session = HubSession::open(&hub_dir).await?;
    match session.get_law().await? {
        Some(yaml) => print!("{}", yaml),
        None => println!("No hub law set."),
    }
    Ok(())
}

/// Starter hub-law template — embedded at compile time so the
/// binary ships with it. Source: `web4/hub/examples/starter-law.yaml`.
const STARTER_LAW_YAML: &str = include_str!("../../examples/starter-law.yaml");

async fn run_init_law(output: PathBuf, force: bool) -> Result<()> {
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
    hub_lib::atomic_file::write_atomic(&output, STARTER_LAW_YAML)
        .with_context(|| format!("writing starter law to {}", output.display()))?;

    println!("Starter hub-law written to {}.", output.display());
    println!();
    println!("Next steps:");
    println!("  1. Edit {} — adjust norms, admission, atp_issuance, etc.", output.display());
    println!("  2. Apply to a chapter:  hub set-law <chapter-dir> {}", output.display());
    println!("  3. If serve is running: curl -X POST http://<host>/v1/admin/reload-law");
    Ok(())
}

// ---------- `hub up` — the turnkey deployment kit -----------------------------

/// A deployment archetype = a named, fail-closed posture (see the deployment map
/// in the hub README). `hub up` turns "which archetype" into a ready config.
/// INVARIANT: every `public-*` archetype uses token auth + the production profile
/// + a domain, so a non-expert can't stand up an open, no-auth public hub.
struct Archetype {
    id: &'static str,
    profile: Option<&'static str>, // HUB_PROFILE (production for public)
    operator_auth: &'static str,   // HUB_OPERATOR_AUTH: loopback | token
    bind: &'static str,            // serve --bind
    needs_domain: bool,
    tunnel: bool,
    blurb: &'static str,
}

const ARCHETYPES: &[Archetype] = &[
    Archetype { id: "dev",             profile: None,               operator_auth: "loopback", bind: "127.0.0.1", needs_domain: false, tunnel: false, blurb: "local dev — localhost only, no TLS" },
    Archetype { id: "private-vpn",     profile: None,               operator_auth: "loopback", bind: "0.0.0.0",   needs_domain: false, tunnel: false, blurb: "trusted team over a VPN/tailnet; admin via SSH" },
    Archetype { id: "public-managed",  profile: Some("production"), operator_auth: "token",    bind: "0.0.0.0",   needs_domain: true,  tunnel: false, blurb: "public managed host (e.g. Fly.io) — platform does TLS" },
    Archetype { id: "public-selfhost", profile: Some("production"), operator_auth: "token",    bind: "0.0.0.0",   needs_domain: true,  tunnel: false, blurb: "public self-hosted, fixed IP + Caddy/Let's Encrypt" },
    Archetype { id: "public-tunnel",   profile: Some("production"), operator_auth: "token",    bind: "127.0.0.1", needs_domain: true,  tunnel: true,  blurb: "self-hosted behind NAT via a reverse tunnel — no port-forward" },
];

fn find_archetype(id: &str) -> Option<&'static Archetype> {
    ARCHETYPES.iter().find(|a| a.id == id)
}

fn archetype_ids() -> String {
    ARCHETYPES.iter().map(|a| a.id).collect::<Vec<_>>().join(" | ")
}

async fn run_up(
    hub_dir: PathBuf,
    profile: Option<String>,
    domain: Option<String>,
    yes: bool,
) -> Result<()> {
    use std::io::Write as _;

    // 1. Resolve the archetype (flag or one interactive question).
    let arch: &Archetype = match profile {
        Some(p) => find_archetype(&p)
            .ok_or_else(|| anyhow::anyhow!("unknown --profile '{p}'. One of: {}", archetype_ids()))?,
        None if yes => anyhow::bail!("--profile is required with --yes. One of: {}", archetype_ids()),
        None => {
            println!("How will people reach this hub?");
            for (i, a) in ARCHETYPES.iter().enumerate() {
                println!("  {}. {:<16} {}", i + 1, a.id, a.blurb);
            }
            print!("Choose 1-{}: ", ARCHETYPES.len());
            std::io::stdout().flush().ok();
            let mut line = String::new();
            std::io::stdin().read_line(&mut line)?;
            let idx: usize = line
                .trim()
                .parse()
                .ok()
                .filter(|n| (1..=ARCHETYPES.len()).contains(n))
                .ok_or_else(|| anyhow::anyhow!("not a valid choice"))?;
            &ARCHETYPES[idx - 1]
        }
    };

    // 2. Domain for the public archetypes.
    let domain: Option<String> = if arch.needs_domain {
        Some(match domain {
            Some(d) if !d.trim().is_empty() => d.trim().to_string(),
            _ if yes => anyhow::bail!("archetype '{}' needs --domain (e.g. hub.4-gov.org)", arch.id),
            _ => {
                print!("Public hostname (e.g. hub.4-gov.org): ");
                std::io::stdout().flush().ok();
                let mut d = String::new();
                std::io::stdin().read_line(&mut d)?;
                let d = d.trim().to_string();
                if d.is_empty() {
                    anyhow::bail!("a hostname is required for '{}'", arch.id);
                }
                d
            }
        })
    } else {
        None
    };

    // 3. hub_dir + a fail-closed starter law (write only if absent).
    std::fs::create_dir_all(&hub_dir).with_context(|| format!("creating {}", hub_dir.display()))?;
    let law_path = hub_dir.join("hub-law.yaml");
    if !law_path.exists() {
        hub_lib::law::Law::parse_and_validate(STARTER_LAW_YAML)
            .context("embedded starter-law failed to validate (binary bug)")?;
        hub_lib::atomic_file::write_atomic(&law_path, STARTER_LAW_YAML)
            .with_context(|| format!("writing {}", law_path.display()))?;
    }

    // 4. Operator token for token archetypes (0600; reuse an existing one).
    // Minted via OperatorAuth::generate_and_write — the ONE code path that
    // also records `operator.token.created_at`, so a hub provisioned here can
    // later enable HUB_OPERATOR_TOKEN_TTL_SECONDS without being locked out
    // (the TTL check fail-closes on a missing creation timestamp).
    let token: Option<String> = if arch.operator_auth == "token" {
        let tpath = hub_dir.join("operator.token");
        if tpath.exists() {
            Some(std::fs::read_to_string(&tpath)?.trim().to_string())
        } else {
            Some(crate::rest::OperatorAuth::generate_and_write(&tpath)?)
        }
    } else {
        None
    };

    // 5. Write the env profile (reusable as a systemd EnvironmentFile).
    let base_url = domain.as_ref().map(|d| format!("https://{d}"));
    let env_path = hub_dir.join("hub-up.env");
    let mut env = format!("# hub up — {} profile\nHUB_BIND={}\n", arch.id, arch.bind);
    if let Some(p) = arch.profile {
        env.push_str(&format!("HUB_PROFILE={p}\n"));
    }
    env.push_str(&format!("HUB_OPERATOR_AUTH={}\n", arch.operator_auth));
    if let Some(u) = &base_url {
        env.push_str(&format!("HUB_PUBLIC_BASE_URL={u}\n"));
    }
    hub_lib::atomic_file::write_atomic(&env_path, &env)
        .with_context(|| format!("writing {}", env_path.display()))?;

    // 6. Print the tailored go-live runbook.
    println!();
    println!("✔ hub up — '{}' profile ready in {}", arch.id, hub_dir.display());
    println!("  {}", arch.blurb);
    println!();
    println!("Wrote:");
    println!("  {}  — env profile (HUB_PROFILE/OPERATOR_AUTH/PUBLIC_BASE_URL/BIND)", env_path.display());
    println!("  {}  — fail-closed starter law", law_path.display());
    if token.is_some() {
        println!("  {}  — operator token (0600)", hub_dir.join("operator.token").display());
    }
    println!();
    println!("Go live:");
    // A copy-pasteable hub name: the hub_dir's last component ("./hub" → "hub").
    let hub_name = hub_dir
        .file_name()
        .and_then(|s| s.to_str())
        .filter(|s| !s.is_empty() && *s != ".")
        .unwrap_or("hub");
    let mut n = 1;
    println!("  {n}. hub gen-lct sovereign.json           # your sovereign identity (prompts for a passphrase — keep both safe)");
    n += 1;
    println!("  {n}. hub init \"{hub_name}\" --sovereign-lct sovereign.json --hub-dir {}", hub_dir.display());
    n += 1;
    println!("  {n}. hub set-law {} {}   # ratify the law", hub_dir.display(), law_path.display());
    n += 1;
    if arch.tunnel {
        println!("  {n}. cloudflared tunnel run …            # map {} → http://127.0.0.1:8770 (no port-forward)", domain.as_deref().unwrap_or("<domain>"));
        n += 1;
    } else if base_url.is_some() {
        println!("  {n}. point DNS + TLS at this host       # {} → here (Caddy+LE, or the platform)", domain.as_deref().unwrap_or("<domain>"));
        n += 1;
    }
    println!("  {n}. set -a; . {}; set +a          # load the profile", env_path.display());
    n += 1;
    println!("     hub serve {} --bind \"$HUB_BIND\"", hub_dir.display());
    println!("  {n}. hub unlock                          # ignite the vault (passphrase — never stored)", );
    println!();
    if let Some(t) = &token {
        println!(
            "Operator token: {} (send as the X-Operator-Token header for admin/API)",
            crate::rest::OperatorAuth::fingerprint(t)
        );
        println!("  Full token is in {} — treat it as a secret.", hub_dir.join("operator.token").display());
        println!();
    }
    match &base_url {
        Some(u) => println!("You'll be live at: {u}"),
        // 0.0.0.0 is a bind address, not a dialable URL.
        None if arch.bind == "0.0.0.0" =>
            println!("You'll be live at: this host's LAN/VPN address, port 8770"),
        None => println!("You'll be live at: http://{}:8770", arch.bind),
    }
    println!();
    println!("Fail-closed by default: a public profile refuses to serve without a law and (production)");
    println!("without an https base URL + operator token — a novice can't accidentally stand up an");
    println!("open, unauthenticated, no-law public hub.");
    Ok(())
}

async fn run_declare_skill(hub_dir: PathBuf, member_lct_id: Uuid, skill: String) -> Result<()> {
    let mut session = HubSession::open(&hub_dir).await?;
    let entry = session.declare_skill(member_lct_id, skill.clone()).await?;
    println!("Skill declared.");
    println!("  Member LCT:   {}", member_lct_id);
    println!("  Skill:        {}", skill);
    println!("  Entry index:  {}", entry.index);
    println!("  Entry hash:   {}", entry.entry_hash);
    Ok(())
}

async fn run_set_profile(hub_dir: PathBuf, member_lct_id: Uuid, fields: Vec<String>) -> Result<()> {
    use std::collections::BTreeMap;
    use std::str::FromStr;

    let mut values = BTreeMap::new();
    let mut visibilities = BTreeMap::new();
    for pair in &fields {
        let (lhs, v) = pair.split_once('=').ok_or_else(|| {
            anyhow::anyhow!("field {:?} must be key=value or key@visibility=value", pair)
        })?;
        let (k, visibility) = if let Some((k, tier)) = lhs.split_once('@') {
            let tier = hub_lib::events::ProfileVisibility::from_str(tier.trim())
                .with_context(|| format!("parsing visibility for field {:?}", lhs))?;
            (k.trim().to_string(), Some(tier))
        } else {
            (lhs.trim().to_string(), None)
        };
        values.insert(k.clone(), v.to_string());
        if let Some(tier) = visibility {
            visibilities.insert(k, tier);
        }
    }
    let keys: Vec<String> = values.keys().cloned().collect();
    let mut session = HubSession::open(&hub_dir).await?;
    let entry = session.update_profile(member_lct_id, values, visibilities).await?;
    println!("Profile updated.");
    println!("  Member LCT:   {}", member_lct_id);
    println!("  Fields:       {}", keys.join(", "));
    println!("  Entry index:  {}", entry.index);
    println!("  Entry hash:   {}", entry.entry_hash);
    Ok(())
}

async fn run_query(sub: QueryCommand) -> Result<()> {
    match sub {
        QueryCommand::Members { hub_dir } => {
            let session = HubSession::open(&hub_dir).await?;
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
            let session = HubSession::open(&hub_dir).await?;
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
            let session = HubSession::open(&hub_dir).await?;
            let society = session.society().await?;
            let state = session.state();
            let unfilled = session.unfilled_base_roles().await?;
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
                println!("    (assign via `hub assign-role <chapter-dir> <role> <member-lct-id>` per hub law)");
            }
            Ok(())
        }
    }
}

/// P1 (residual review): production-profile preflight — pure + testable. Returns
/// `Err(reason)` when a required hardening isn't satisfied and isn't explicitly
/// overridden. Enforced only under `HUB_PROFILE=production` (opt-in; this fleet
/// binds 0.0.0.0 for a tailnet, which isn't "public", so it can't be auto-derived).
fn production_preflight(
    law_present: bool,
    public_base_url: &str,
    allow_no_law: bool,
    allow_insecure_origin: bool,
    operator_token_auth: bool,
    allow_loopback_operator: bool,
) -> std::result::Result<(), &'static str> {
    if !law_present && !allow_no_law {
        return Err("refusing to serve with NO hub law (acts/admissions ungated). \
                    Serve a signed law (hub set-law), or set HUB_ALLOW_NO_LAW=1");
    }
    let origin_ok = public_base_url.starts_with("https://")
        || (public_base_url.starts_with("http://") && allow_insecure_origin);
    if !origin_ok {
        return Err("HUB_PUBLIC_BASE_URL must be an https:// origin (issuer/audience URLs must \
                    not derive from the Host header). Set it, or HUB_ALLOW_INSECURE_ORIGIN=1 for http dev");
    }
    // HUB-002: the operator plane carries Sovereign-signing authority, and
    // loopback reachability alone is not authentication (X-001). Production
    // must present a real factor unless the deployment explicitly claims
    // host-level access control (SSH-gated box) as its second factor.
    if !operator_token_auth && !allow_loopback_operator {
        return Err("HUB_OPERATOR_AUTH=token is required in production (loopback alone is not \
                    authentication for the Sovereign-signing operator plane). Set it, or set \
                    HUB_ALLOW_LOOPBACK_OPERATOR=1 if host access (SSH) is the second factor");
    }
    Ok(())
}

/// The **public plane's** route set — the network-reachable surface, assembled
/// exactly as `run_serve` serves it (rate-limit and lock-gate layers are applied
/// by the caller and do not add or remove routes).
///
/// Extracted from `run_serve` so the plane split is testable. That split — which
/// router a route is declared in — is the hub's primary network boundary, and
/// until now it was enforced only by reading the assembly by eye: `/admin/ledger`
/// and `/admin/pairs` sat on the public plane until the 2026-07-23 review moved
/// them, and `require_loopback` (the only automated guard on the write tools) is
/// documented in `mcp.rs` as defeated behind a same-host reverse proxy. A route
/// that reaches this router is anonymously reachable from the internet on a
/// `--bind 0.0.0.0` hub; see `the_public_plane_serves_only_its_allowlist`.
fn public_plane_router(mcp_state: McpState, rest_state: RestState, admin_state: RestState) -> Router {
    mcp_read_router(mcp_state)
        .merge(rest_router(rest_state))
        .merge(admin::router(admin_state))
}

/// The **operator plane's** route set (127.0.0.1-only listener, never proxied).
/// Carries the member/skill read tools, the Sovereign-signing MCP write tools and
/// the `/admin/api/*` write API. `run_serve` layers operator auth and the lock
/// gate over this; neither changes the route set.
fn operator_plane_router(mcp_state: McpState, operator_state: RestState) -> Router {
    admin::router(operator_state.clone())
        .merge(admin::operator_router(operator_state.clone()))
        .merge(crate::rest::admin_api_router(operator_state))
        // Member/skill read tools live ONLY here (loopback-only, never
        // proxied) so anonymous internet clients cannot enumerate members.
        .merge(mcp_operator_read_router(mcp_state.clone()))
        // Sovereign-signing MCP write tools live ONLY here (loopback-only,
        // never proxied) — residual-review P0.
        .merge(mcp_write_router(mcp_state))
}

/// The two listen **addresses** `run_serve` binds, decided in one place so the
/// decision is testable. #609 pinned which router each route lands in; this pins
/// the address each router is served on. They are the same boundary from two
/// sides — a route correctly placed on `operator_plane_router` is still published
/// to the network if the operator listener follows `--bind`.
///
/// The public plane binds whatever `--bind` says (this hub binds `0.0.0.0` for
/// its tailnet; three of the four `hub up` archetypes bind it too). The operator
/// plane — the `/admin/api/*` admit/deny/remove/re-key API and the
/// Sovereign-signing MCP write tools — binds **127.0.0.1, always, whatever
/// `bind` is**. `bind` is taken here and deliberately unused for the operator
/// address, so making the operator listener follow it is a *failing test* rather
/// than a signature change the compiler would catch instead.
///
/// `admin_port == 0` disables the operator plane: `None`, not port 0, which the
/// OS would resolve to an arbitrary ephemeral port — a listener that is neither
/// off nor findable.
fn plane_addrs(bind: &str, port: u16, admin_port: u16) -> Result<(SocketAddr, Option<SocketAddr>)> {
    let public: SocketAddr = format!("{}:{}", bind, port).parse().map_err(|e| {
        anyhow::anyhow!(
            "--bind {bind} is not an IP address ({e}). Accepted: an IPv4 literal \
             (127.0.0.1, 0.0.0.0) or a BRACKETED IPv6 literal ([::1]). Host names \
             (`localhost`) and unbracketed IPv6 (`::1`) are not resolved here."
        )
    })?;
    let operator = (admin_port != 0).then(|| SocketAddr::from((Ipv4Addr::LOCALHOST, admin_port)));
    Ok((public, operator))
}

/// Whether the public listener is unreachable from the network — read from the
/// **parsed** address, not from the `--bind` spelling. This decides only whether
/// the "public bind without HUB_PROFILE=production" warning prints, so the
/// failure that matters is a network-reachable bind classified as loopback.
/// The string match it replaced tested four literals, two of which (`localhost`,
/// `::1`) `plane_addrs` rejects two lines earlier — dead arms advertising support
/// that does not exist. Reading the parsed IP also gets `127.0.0.2` right.
fn public_bind_is_loopback(addr: &SocketAddr) -> bool {
    addr.ip().is_loopback()
}

/// `run_serve`'s operator-plane layer stack, in the order it applies them. Axum
/// runs the **last** `.layer()` first, so operator auth is outermost and an
/// unauthorized caller is refused before the lock gate and before any handler.
/// Both gates run under either order — what the order decides is which one
/// answers first, and with the lock gate outermost a locked hub tells an
/// unauthenticated stranger `503 locked`, disclosing its lock state to someone
/// with no standing to ask. Takes the router already rate-limited (that layer is
/// conditional on the limiter's presence and neither adds routes nor rejects).
fn operator_plane_app(
    rate_limited: Router,
    gate_state: RestState,
    op_auth: crate::rest::OperatorAuth,
) -> Router {
    rate_limited
        .layer(axum::middleware::from_fn_with_state(gate_state, crate::rest::lock_gate))
        .layer(axum::middleware::from_fn_with_state(op_auth, crate::rest::operator_auth_gate))
}

async fn run_serve(hub_dir: PathBuf, port_override: Option<u16>, bind: String, admin_port: u16) -> Result<()> {
    let config = HubConfig::load(hub_lib::hub::HubPaths::new(&hub_dir).config())?;
    let port = port_override.unwrap_or(config.daemon.mcp_port);
    let (addr, operator_addr) = plane_addrs(&bind, port, admin_port)?;

    // Total enclosure, unlock-first: try to open the encrypted state store with whatever
    // key is available. If it opens (plaintext / NULL-keyed / fresh hub), boot normally.
    // If it fails closed (encrypted, no key), boot a LOCKED SHELL that serves only the
    // unlock path; `hub unlock` ignites it at runtime.
    //
    // "Whatever key is available" INCLUDES `HUB_PASSPHRASE`: this is the env'd entry point
    // (`open_hub_store_async` -> `store::store_key` -> `identity::env_passphrase`). A hub
    // whose daemon environment carries the passphrase therefore boots UNLOCKED and never
    // reaches the locked shell. That is a deployment property, not a code guarantee — what
    // makes a hub boot locked is that nothing put a passphrase in the unit environment.
    //
    // The de-env'ing is partial and deliberate, not finished:
    //   - runtime store re-opens ARE de-env'd — `RestState::open_store` passes the key held
    //     in memory since ignition, and never re-reads the environment;
    //   - construction is still env-fed — see the `store_key` / `protected` fields in
    //     `RestState::open_with_law_and_ledger` (rest.rs), which say "env-fed at
    //     construction for now ... increment 6".
    // Until that increment lands, an operator CAN get an unattended-igniting hub by putting
    // HUB_PASSPHRASE in the unit environment — at the cost of parking the passphrase at rest
    // beside the ciphertext it protects, which is the whole reason increment 6 exists.
    let store_opens = hub_lib::store::open_hub_store_async(&hub_dir).await.is_ok();

    let (rest_state, mcp_state) = if store_opens {
        // ── normal boot (store readable without a held key) ──
        let initial_law = {
            let store = hub_lib::store::open_hub_store_async(&hub_dir).await?;
            match store.read_law().await? {
                Some(yaml) => Some(hub_lib::law::Law::parse_and_validate(&yaml)?),
                None => None,
            }
        };
        let shared_law = std::sync::Arc::new(tokio::sync::RwLock::new(initial_law));
        let shared_ledger = {
            let store = hub_lib::store::open_hub_store_async(&hub_dir).await?;
            std::sync::Arc::new(tokio::sync::Mutex::new(
                hub_lib::ledger::HubLedger::open(store).await?,
            ))
        };
        let rest = RestState::open_with_law_and_ledger(
            hub_dir.clone(),
            shared_law.clone(),
            shared_ledger.clone(),
        )
        .await?;
        let mcp = McpState::open_with_law_and_ledger(
            hub_dir.clone(),
            shared_law,
            shared_ledger,
            rest.signer.clone(),
            rest.sovereign_lct_id,
            rest.store_key.clone(),
            rest.hub_id,
            rest.hub_name.clone(),
        )
        .await?;
        (rest, mcp)
    } else {
        // ── LOCKED SHELL (encrypted store, no key) ──
        tracing::warn!(
            "hub state is encrypted and no key is available — starting in a LOCKED shell \
             (only the unlock path is served). Run `hub unlock` to ignite."
        );
        let shared_law = std::sync::Arc::new(tokio::sync::RwLock::new(None));
        // Empty placeholder ledger on a throwaway temp dir (never the real hub dir, never
        // written) — replaced in memory at ignition.
        let placeholder_dir = std::env::temp_dir().join(format!("web4-hub-locked-{}", std::process::id()));
        std::fs::create_dir_all(&placeholder_dir)?;
        let placeholder_store = hub_lib::store::open_hub_store_with_key(&placeholder_dir, None)?;
        let shared_ledger = std::sync::Arc::new(tokio::sync::Mutex::new(
            hub_lib::ledger::HubLedger::open(placeholder_store).await?,
        ));
        let rest = RestState::open_locked_shell(hub_dir.clone(), shared_law.clone(), shared_ledger.clone()).await?;
        let mcp = McpState::open_with_law_and_ledger(
            hub_dir.clone(),
            shared_law,
            shared_ledger,
            rest.signer.clone(),
            rest.sovereign_lct_id,
            rest.store_key.clone(),
            rest.hub_id,
            rest.hub_name.clone(),
        )
        .await?;
        (rest, mcp)
    };
    // On a normal (unlocked) boot the signer is live, so hydrate any law-driven
    // code defaults into the law now (idempotent; witnessed only if it fills a
    // gap). On a locked boot this runs post-ignition in the unlock handler.
    if store_opens {
        match crate::rest::hydrate_law_defaults(&rest_state).await {
            Ok(true) => tracing::info!("law defaults hydrated at boot"),
            Ok(false) => {}
            Err(e) => tracing::warn!("law-default hydration skipped: {e}"),
        }
        // Re-deliver hub→citizen notices persisted before the last shutdown.
        // (Locked boots hydrate post-ignition in the unlock handler instead.)
        rest_state.hydrate_mailbox().await;
    }
    // Admin UI reuses RestState (read-only; shares ledger + law snapshot).
    let admin_state = rest_state.clone();
    let gate_state = rest_state.clone();
    // Operator plane (separate 127.0.0.1-only listener) shares the same RestState.
    let mut operator_state = rest_state.clone();
    operator_state.operator_plane = true; // this clone serves the write pages → show their nav links
    let operator_gate = rest_state.clone();
    // P0 (public-release): per-IP rate limiting. In-memory; production public hubs
    // should still use an edge/reverse-proxy layer for global limits.
    let rate_limiter = crate::rate_limit::RateLimiter::from_env();
    // H-003: make the no-law posture loud at startup — a hub with no law gates
    // nothing (acts/admissions run permissive). Production must serve a signed law.
    if rest_state.law.read().await.is_none() {
        tracing::warn!(
            "no hub law loaded — PERMISSIVE no-law mode: acts and admissions are NOT gated by law; \
             serve a signed law before production (hub set-law)"
        );
        println!("  ⚠ NO-LAW MODE — acts/admissions ungated; serve a signed law for production");
    } else if rest_state.verify_law_integrity().await == "mismatch" {
        // H-009: served law diverged from the witnessed ledger head (only checkable
        // once the store is unlocked; a locked boot reports "unverifiable" → skipped).
        // HUB-001: governed writes now refuse while this holds (reads still serve);
        // re-witness via `hub set-law`, or HUB_ALLOW_LAW_MISMATCH=1 for warn-only.
        println!("  ⚠ LAW INTEGRITY MISMATCH — served law != last witnessed LawAmended (see log); \
                  governed writes REFUSED until re-witnessed (hub set-law)");
    }

    // P1 (residual review): production profile. Opt-in via HUB_PROFILE=production
    // (the `hub up` kit sets it for public archetypes). When on, REFUSE the unsafe
    // defaults GPT flagged unless explicitly overridden. Deliberately NOT auto-
    // derived from the bind address: this hub binds 0.0.0.0 for a *tailnet*, which
    // is not "public", so an off-by-default enforcement must be opt-in.
    let loopback_bind = public_bind_is_loopback(&addr);
    if std::env::var("HUB_PROFILE").as_deref() == Ok("production") {
        let law_present = rest_state.law.read().await.is_some();
        production_preflight(
            law_present,
            &std::env::var("HUB_PUBLIC_BASE_URL").unwrap_or_default(),
            std::env::var("HUB_ALLOW_NO_LAW").as_deref() == Ok("1"),
            std::env::var("HUB_ALLOW_INSECURE_ORIGIN").as_deref() == Ok("1"),
            std::env::var("HUB_OPERATOR_AUTH").as_deref() == Ok("token"),
            std::env::var("HUB_ALLOW_LOOPBACK_OPERATOR").as_deref() == Ok("1"),
        )
        .map_err(|e| anyhow::anyhow!("HUB_PROFILE=production: {e}"))?;
        println!("  production profile: law + https public base URL + operator token enforced");
    } else if !loopback_bind {
        println!(
            "  ⚠ public bind ({bind}) without HUB_PROFILE=production — hardening (require law + \
             https base URL) is NOT enforced; set HUB_PROFILE=production to enable it"
        );
    }

    // Public listener: read-only MCP tools + REST + read-only admin. The
    // Sovereign-signing MCP WRITE tools are NOT here — they're mounted on the
    // loopback operator plane below (residual-review P0: a same-host proxy makes
    // ConnectInfo read as loopback, so the public listener can't safely carry them).
    let mut app = public_plane_router(mcp_state.clone(), rest_state, admin_state);
    if let Some(limiter) = &rate_limiter {
        // State-based wiring (NOT an Extension): the original extension-based
        // stack layered the middleware outside the Extension layer, so the
        // lookup always missed and the limiter silently never ran (review
        // 2026-07-23). With state, the limiter's presence is structural.
        app = app.layer(axum::middleware::from_fn_with_state(
            limiter.clone(),
            crate::rate_limit::layer,
        ));
    }
    // Fail-closed lock-gate over the whole surface: while locked, only the
    // tier-0 allowlist (unlock / well-known / law / issuer metadata) is served.
    let app = app.layer(axum::middleware::from_fn_with_state(gate_state, crate::rest::lock_gate));

    tracing::info!(
        hub = %config.hub.name,
        hub_dir = %hub_dir.display(),
        bind = %addr,
        "HTTP server starting"
    );
    println!("hub serve — {} listening on http://{}", config.hub.name, addr);
    println!("  MCP tools:    http://{}/tools", addr);
    println!("  REST v1:      http://{}/v1/", addr);
    println!("  Admin UI:     http://{}/admin (read-only on this plane)", addr);
    println!("  Stop:         Ctrl-C");

    // Operator plane: a SECOND listener bound to 127.0.0.1 only — never exposed
    // to the network, never reverse-proxied. Carries the admit/deny/remove/re-key
    // admin API (and the write GUI). Local-presence + an ignited hub is the
    // authorization; actions sign as the Sovereign and fail closed while locked.
    if let Some(op_addr) = operator_addr {
        // H-004: pluggable operator-plane auth (loopback default / token). Built
        // from HUB_OPERATOR_AUTH; applied as the OUTERMOST layer so an
        // unauthorized caller is rejected before the lock gate and any handler
        // (see `operator_plane_app`).
        let op_auth = crate::rest::OperatorAuth::from_env(&hub_dir)?;
        let mut operator_app = operator_plane_router(mcp_state, operator_state);
        if let Some(limiter) = &rate_limiter {
            // Same state-based wiring as the public plane. Loopback callers
            // (which is all of this plane) get the loopback rate multiplier,
            // so operator automation is advantaged but still bounded.
            operator_app = operator_app.layer(axum::middleware::from_fn_with_state(
                limiter.clone(),
                crate::rate_limit::layer,
            ));
        }
        let operator_app = operator_plane_app(operator_app, operator_gate, op_auth);
        match tokio::net::TcpListener::bind(op_addr).await {
            Ok(op_listener) => {
                println!("  Operator:     http://{}/admin (LOCAL-ONLY: admit/deny/remove/re-key)", op_addr);
                tracing::info!(operator_bind = %op_addr, "operator plane (loopback-only) starting");
                tokio::spawn(async move {
                    if let Err(e) = axum::serve(
                        op_listener,
                        operator_app.into_make_service_with_connect_info::<std::net::SocketAddr>(),
                    )
                    .await
                    {
                        tracing::error!("operator plane terminated: {e}");
                    }
                });
            }
            Err(e) => {
                tracing::warn!("operator plane disabled — could not bind {op_addr}: {e}");
            }
        }
    }

    let listener = tokio::net::TcpListener::bind(addr).await?;
    // `into_make_service_with_connect_info` exposes the peer `SocketAddr` to
    // handlers (the unlock slot uses it to enforce loopback-only). Other
    // handlers are unaffected.
    axum::serve(
        listener,
        app.into_make_service_with_connect_info::<std::net::SocketAddr>(),
    )
    .with_graceful_shutdown(shutdown_signal())
    .await?;

    println!("hub serve — shut down cleanly");
    Ok(())
}

async fn shutdown_signal() {
    let _ = tokio::signal::ctrl_c().await;
    tracing::info!("ctrl-c received — shutting down");
}

async fn run_verify_ledger(hub_dir: PathBuf) -> Result<()> {
    let result = verify_hub(&hub_dir).await?;
    println!("Ledger verified.");
    println!("  Chapter dir:    {}", result.hub_dir.display());
    println!("  Chapter name:   {}", result.hub_name);
    println!("  Entries:        {}", result.entries);
    println!("  Head hash:      {}", result.head_hash);
    // "Ledger verified." reads as "nothing was removed", and that is one
    // tamper class wider than what the chain can show. A forward hash chain is
    // anchored at Genesis and open at the head, so a truncated tail re-verifies
    // (hub-lib: `a_truncated_tail_still_verifies_because_the_chain_only_proves_consistency`).
    // Say so here rather than in a doc comment the operator reading this output
    // is not reading.
    println!();
    println!("  Proven:   the {} entries above are linked, hashed and signed consistently.",
             result.entries);
    println!("  NOT proven: that they are ALL the entries. Removing entries from the tail");
    println!("              leaves a chain that verifies. Compare the head hash against an");
    println!("              independently-recorded value (query_hub publishes it) to detect it.");
    Ok(())
}

async fn run_migrate(hub_dir: PathBuf, to: String) -> Result<()> {
    use std::str::FromStr;
    let target = hub_lib::store::BackendKind::from_str(&to)
        .context("parsing --to")?;
    println!("Migrating {} → {}", hub_dir.display(), target.as_str());
    let result = hub_lib::store::migrate_hub(&hub_dir, target).await
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
    let verify = verify_hub(&hub_dir).await
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
    dynamodb_table: Option<String>,
    dynamodb_region: Option<String>,
    dynamodb_endpoint: Option<String>,
) -> Result<()> {
    use std::str::FromStr;
    let hub_dir = hub_dir.unwrap_or_else(|| PathBuf::from(slugify(&name)));
    let backend = hub_lib::store::BackendKind::from_str(&storage)
        .context("parsing --storage")?;

    let dynamodb = if backend == hub_lib::store::BackendKind::Dynamodb {
        Some(hub_lib::init::DynamoDbInitArgs {
            table: dynamodb_table.ok_or_else(|| anyhow::anyhow!(
                "--storage dynamodb requires --dynamodb-table"
            ))?,
            region: dynamodb_region,
            endpoint: dynamodb_endpoint,
        })
    } else {
        None
    };

    let result = match (sovereign_lct, sovereign_hestia) {
        (Some(path), None) => {
            // Local mode
            init_hub(InitArgs {
                hub_name: name,
                hub_dir,
                sovereign_lct_path: path,
                storage: Some(backend),
                dynamodb,
            }).await?
        }
        (None, Some(callback_url)) => {
            // Hestia mode — clap's `requires_all` guarantees lct_id + pubkey are present
            let lct_id = sovereign_lct_id.expect("clap requires_all");
            let pubkey_hex = sovereign_pubkey.expect("clap requires_all");
            println!("hub init: Hestia mode — Genesis will be signed by {}", callback_url);
            hub_lib::init::init_hub_hestia(hub_lib::init::HestiaInitArgs {
                hub_name: name,
                hub_dir,
                sovereign_lct_id: lct_id,
                sovereign_pubkey_hex: pubkey_hex,
                hestia_callback_url: callback_url,
                storage: Some(backend),
                dynamodb,
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
            println!("      For now, inspect the hub dir or run `hub init {} ...` again",
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

/// Resolve the hub vault passphrase, **fail-closed** — there is no
/// "use plaintext" outcome. Order: `HUB_PASSPHRASE` env (set, INCLUDING empty =
/// a deliberate NULL passphrase) → interactive TTY prompt (Enter = NULL) → else
/// error. The vault doctrine: a private key is never written in the clear, and
/// "no passphrase" must be an explicit choice, never a silent default that could
/// propagate and erode the trust foundation.
fn require_passphrase(purpose: &str) -> Result<String> {
    use std::io::IsTerminal;
    if let Some(p) = hub_lib::identity::env_passphrase() {
        return Ok(p); // set — possibly "" (a deliberate NULL choice)
    }
    if std::io::stdin().is_terminal() {
        let p = rpassword::prompt_password(format!(
            "Hub vault passphrase for {purpose} (press Enter for NO passphrase — \
             still encrypted, but openable by anyone): "
        ))
        .context("reading passphrase")?;
        return Ok(p);
    }
    anyhow::bail!(
        "HUB_PASSPHRASE is not set and there is no terminal to prompt — refusing to \
         write a plaintext private key (vault doctrine). Set HUB_PASSPHRASE; an empty \
         value is allowed but must be explicit (HUB_PASSPHRASE=)."
    )
}

async fn run_seal_identity(path: PathBuf) -> Result<()> {
    // load_auto reads plaintext (legacy) OR an already-encrypted vault.
    let identity = IdentityFile::load_auto(&path)
        .with_context(|| format!("loading identity from {}", path.display()))?;
    let pass = require_passphrase("this identity")?;
    identity.save_encrypted(&path, &pass)
        .with_context(|| format!("sealing identity into {}", path.display()))?;
    let raw = std::fs::read(&path)?;
    println!("Identity sealed in place: {}", path.display());
    println!("  LCT id:    {}", identity.lct.id);
    println!("  On disk:   {} (encrypted vault)", if raw.starts_with(b"W4VT") { "W4VT" } else { "??" });
    if pass.is_empty() {
        println!("  WARNING: empty (NULL) passphrase — encrypted but openable by anyone.");
    }
    println!("  The plaintext private key is no longer on disk. Keep the passphrase safe.");
    Ok(())
}

/// The stub-console unlock plugin: prompt for the passphrase (never store it)
/// and present it to a locked, running hub's local `/unlock` slot.
/// Rotate the vault passphrase to an operator-chosen one. Re-keys identity + state
/// store + protected tier. The hub does not dictate the secret — the admin picks it.
async fn run_rotate_passphrase(hub_dir: PathBuf) -> Result<()> {
    use hub_lib::hub::{HubConfig, HubPaths, SovereignMode};
    use std::io::IsTerminal;
    if !std::io::stdin().is_terminal() {
        anyhow::bail!("rotate-passphrase is interactive — run it at a console");
    }
    // Current passphrase (env or prompt) — must decrypt the existing vaults.
    let old = require_passphrase("the CURRENT vault (to re-key it)")?;
    // New passphrase — operator's choice, entered twice. Empty = explicit NULL (allowed).
    let new = rpassword::prompt_password("New passphrase (your choice; Enter twice for NONE): ")
        .context("reading new passphrase")?;
    let confirm = rpassword::prompt_password("Confirm new passphrase: ")
        .context("reading confirmation")?;
    if new != confirm {
        anyhow::bail!("the two new passphrases did not match — nothing changed");
    }
    if new == old {
        anyhow::bail!("the new passphrase is the same as the current one — nothing to do");
    }

    let config = HubConfig::load(HubPaths::new(&hub_dir).config())?;

    // 1. Re-key the Sovereign identity (W4VT): decrypt with old, re-seal with new.
    if let SovereignMode::Local { lct_path } = config.sovereign.mode()? {
        let id = IdentityFile::load_encrypted(&lct_path, &old)
            .context("current passphrase did not open the identity — aborting (nothing changed)")?;
        id.save_encrypted(&lct_path, &new)
            .with_context(|| format!("re-sealing identity at {}", lct_path.display()))?;
        println!("  ✓ Sovereign identity re-keyed");
    }

    // 2. Re-key the SQLCipher state store (same per-hub salt, new passphrase → new key).
    let old_key = hub_lib::store::derive_store_key(&hub_dir, &old)?;
    let new_key = hub_lib::store::derive_store_key(&hub_dir, &new)?;
    hub_lib::store::rekey_store(&hub_dir, old_key, new_key)
        .context("re-keying the state store")?;
    println!("  ✓ state store (hub.db) re-keyed");

    // 3. Protected tier: it's keyed straight from the passphrase. Drop it; it re-seeds
    //    under the new passphrase on next ignition (regenerable).
    let protected = hub_dir.join("protected.hvlt");
    if protected.exists() {
        std::fs::remove_file(&protected).ok();
        println!("  ✓ protected tier dropped (re-seeds under the new passphrase on ignition)");
    }

    if new.is_empty() {
        println!("  ⚠ new passphrase is EMPTY (NULL) — encrypted but openable by anyone. Your choice.");
    }
    println!("Passphrase rotated. The old one no longer opens this hub.");
    println!("  → restart the hub (it will boot locked) and ignite with `hub unlock` using the NEW phrase.");
    Ok(())
}

/// Rotate the operator-plane bearer token. Generates a new 256-bit token,
/// writes it to `operator.token`, and prints the fingerprint.
async fn run_rotate_operator_token(hub_dir: PathBuf) -> Result<()> {
    let path = crate::rest::OperatorAuth::token_path(&hub_dir);
    if !path.exists() {
        anyhow::bail!(
            "no operator token file found at {}. \
             This command only works when HUB_OPERATOR_AUTH=token (run `hub up` with a public archetype first).",
            path.display()
        );
    }
    let (new_token, fingerprint) = crate::rest::OperatorAuth::rotate(&hub_dir)?;
    println!("Operator token rotated.");
    println!("  File:        {}", path.display());
    println!("  Fingerprint: {fingerprint}");
    println!("  New token:   {new_token}");
    println!();
    println!(
        "A running `hub serve` picks the new token up on its next operator request \
         (the token file is canonical, cached by mtime) — the old token stops \
         working from that moment; no restart needed."
    );
    Ok(())
}

/// Seed the clear tier-0 `public-identity.json` from the encrypted store + identity.
/// For DynamoDB-backed hubs there is no on-disk encrypted store, so the public
/// identity is derived directly from config.toml (no passphrase required).
async fn run_export_public_identity(hub_dir: PathBuf) -> Result<()> {
    use hub_lib::hub::{HubConfig, HubPaths, SovereignMode};
    let config = HubConfig::load(HubPaths::new(&hub_dir).config())?;

    let (hub_id, hub_name, founding, pubkey_hex): (Uuid, String, Uuid, Option<String>) =
        if config.storage.as_ref().is_some_and(|s| s.is_dynamodb()) {
            let hub_id = config.hub.id.ok_or_else(|| anyhow::anyhow!(
                "dynamodb backend requires hub.id in config.toml"
            ))?;
            let (founding, pubkey_hex) = match config.sovereign.mode()? {
                SovereignMode::Local { lct_path } => {
                    let pass = require_passphrase("the Sovereign identity")?;
                    let id = IdentityFile::load_encrypted(&lct_path, &pass)
                        .context("opening the encrypted identity")?;
                    let pk = id.keypair()?.verifying_key().to_hex();
                    (id.lct.id, Some(pk))
                }
                SovereignMode::Hestia { lct_id, pubkey_hex, .. } => (lct_id, Some(pubkey_hex)),
            };
            (hub_id, config.hub.name.clone(), founding, pubkey_hex)
        } else {
            let pass = require_passphrase("the hub vault (to read its public identity)")?;
            let key = hub_lib::store::derive_store_key(&hub_dir, &pass)?;
            let store = hub_lib::store::open_hub_store_with_key(&hub_dir, Some(key))
                .context("opening the encrypted hub store")?;
            let society = store
                .read_society()
                .await?
                .ok_or_else(|| anyhow::anyhow!("no society in the hub store"))?;
            let (founding, pubkey_hex) = match config.sovereign.mode()? {
                SovereignMode::Local { lct_path } => {
                    let id = IdentityFile::load_encrypted(&lct_path, &pass)
                        .context("opening the encrypted identity")?;
                    let pk = id.keypair()?.verifying_key().to_hex();
                    (id.lct.id, Some(pk))
                }
                SovereignMode::Hestia { lct_id, pubkey_hex, .. } => (lct_id, Some(pubkey_hex)),
            };
            (society.lct_id, society.name.clone(), founding, pubkey_hex)
        };

    let pid = crate::rest::PublicIdentity {
        hub_id,
        hub_name: hub_name.clone(),
        founding_sovereign_lct_id: founding,
        sovereign_pubkey_hex: pubkey_hex,
    };
    pid.write(&hub_dir)?;
    println!("Wrote {}/public-identity.json", hub_dir.display());
    println!("  hub:       {} ({})", hub_name, hub_id);
    println!("  sovereign: {}", founding);
    println!("  → the hub can now boot as a locked shell and be ignited with `hub unlock`.");
    Ok(())
}

async fn run_unlock(port: u16) -> Result<()> {
    let base = format!("http://127.0.0.1:{port}");
    let client = reqwest::Client::new();

    // Resolve the hub's LCT id from tier-0 discovery (served while locked).
    let info: serde_json::Value = client
        .get(format!("{base}/.well-known/web4-hub.json"))
        .send()
        .await
        .with_context(|| format!("contacting hub at {base} — is `hub serve` running?"))?
        .error_for_status()
        .context("hub discovery endpoint returned an error")?
        .json()
        .await
        .context("parsing hub discovery JSON")?;
    let hub_id = info
        .get("hub_lct_id")
        .and_then(|v| v.as_str())
        .ok_or_else(|| anyhow::anyhow!("discovery JSON had no hub_lct_id"))?
        .to_string();

    // Prompt for the passphrase here, in OUR UI — use it once, never store it.
    // (HUB_PASSPHRASE is honored too, including an explicit empty value.)
    let passphrase = require_passphrase("the running hub")?;

    let resp = client
        .post(format!("{base}/v1/hubs/{hub_id}/unlock"))
        .json(&serde_json::json!({ "passphrase": passphrase }))
        .send()
        .await
        .context("submitting unlock to the hub")?;
    let status = resp.status();
    let body: serde_json::Value = resp.json().await.unwrap_or_else(|_| serde_json::json!({}));

    if status.is_success() {
        println!("Hub unlocked ✓  ({})", body.get("status").and_then(|v| v.as_str()).unwrap_or("unlocked"));
        if let Some(sov) = body.get("sovereign_lct_id").and_then(|v| v.as_str()) {
            println!("  Sovereign LCT: {sov}");
        }
        println!("  The hub is now serving citizen-tier+ requests. The passphrase was not stored.");
        Ok(())
    } else {
        let msg = body.get("error").and_then(|v| v.as_str())
            .or_else(|| body.get("message").and_then(|v| v.as_str()))
            .unwrap_or("unlock refused");
        anyhow::bail!("unlock failed ({status}): {msg}");
    }
}

async fn run_gen_lct(output: PathBuf, entity_type: EntityType) -> Result<()> {
    let identity = IdentityFile::generate(entity_type);
    // Always encrypted — production never writes a plaintext private key.
    let pass = require_passphrase("the new identity")?;
    identity.save_encrypted(&output, &pass)?;
    println!("Identity generated (encrypted vault).");
    println!("  File:          {}", output.display());
    println!("  LCT id:        {}", identity.lct.id);
    println!("  Entity type:   {:?}", identity.lct.entity_type);
    println!();
    if pass.is_empty() {
        println!("WARNING: empty (NULL) passphrase — the vault is encrypted but openable by");
        println!("         anyone. Re-key with a real HUB_PASSPHRASE when you can.");
    } else {
        println!("Encrypted with HUB_PASSPHRASE. Keep that passphrase safe — without it this");
        println!("identity is unrecoverable.");
    }
    Ok(())
}

async fn run_envelope_sign(identity_path: PathBuf, nonce: String, payload_json: String) -> Result<()> {
    use chrono::Utc;
    use hub_lib::envelope::{build_envelope, Challenge};

    let identity = IdentityFile::load_auto(&identity_path)
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

/// PAIRED-CHANNELS Sprint E/F: encrypt a pair-message body.
/// Without ephemeral flags → Sprint E (static-key ECDH only).
/// With BOTH ephemeral flags → Sprint F (FS-mixed derivation).
async fn run_pair_encrypt(
    identity_path: PathBuf,
    peer_pubkey_hex: String,
    pair_id: Uuid,
    plaintext: String,
    my_ephemeral_secret: Option<String>,
    peer_ephemeral_pub: Option<String>,
) -> Result<()> {
    use web4_core::crypto::PublicKey;
    use web4_core::pair_channel::{seal, seal_fs, EphemeralKeyPair, ephemeral_public_from_hex};

    let identity = IdentityFile::load_auto(&identity_path)
        .with_context(|| format!("loading identity from {}", identity_path.display()))?;
    let kp = identity.keypair().context("reconstructing keypair")?;

    let peer_bytes = hex::decode(&peer_pubkey_hex)
        .context("decoding --peer-pubkey as hex")?;
    let peer_arr: [u8; 32] = peer_bytes.as_slice().try_into()
        .map_err(|_| anyhow::anyhow!("--peer-pubkey must be 32 bytes (got {})", peer_bytes.len()))?;
    let peer_pub = PublicKey::from_bytes(&peer_arr)
        .context("parsing peer pubkey")?;

    let sealed = match (my_ephemeral_secret, peer_ephemeral_pub) {
        (Some(my_eph_sec), Some(peer_eph_pub_hex)) => {
            // FS path
            let my_eph = EphemeralKeyPair::from_secret_hex(&my_eph_sec)
                .context("parsing --my-ephemeral-secret")?;
            let peer_eph_pub = ephemeral_public_from_hex(&peer_eph_pub_hex)
                .context("parsing --peer-ephemeral-pub")?;
            seal_fs(&kp, &my_eph, &peer_pub, &peer_eph_pub, pair_id, plaintext.as_bytes())
                .context("seal_fs failed")?
        }
        (None, None) => {
            // Sprint E static-only fallback
            seal(&kp, &peer_pub, pair_id, plaintext.as_bytes())
                .context("seal failed")?
        }
        _ => anyhow::bail!(
            "forward-secrecy requires BOTH --my-ephemeral-secret AND --peer-ephemeral-pub \
             (or neither, for the Sprint E static-key fallback)"
        ),
    };
    println!("{}", sealed.to_base64());
    Ok(())
}

/// PAIRED-CHANNELS Sprint E/F: symmetric inverse of pair-encrypt.
async fn run_pair_decrypt(
    identity_path: PathBuf,
    peer_pubkey_hex: String,
    pair_id: Uuid,
    ciphertext_b64: String,
    my_ephemeral_secret: Option<String>,
    peer_ephemeral_pub: Option<String>,
) -> Result<()> {
    use web4_core::crypto::PublicKey;
    use web4_core::pair_channel::{open, open_fs, Sealed, EphemeralKeyPair, ephemeral_public_from_hex};

    let identity = IdentityFile::load_auto(&identity_path)
        .with_context(|| format!("loading identity from {}", identity_path.display()))?;
    let kp = identity.keypair().context("reconstructing keypair")?;

    let peer_bytes = hex::decode(&peer_pubkey_hex)
        .context("decoding --peer-pubkey as hex")?;
    let peer_arr: [u8; 32] = peer_bytes.as_slice().try_into()
        .map_err(|_| anyhow::anyhow!("--peer-pubkey must be 32 bytes (got {})", peer_bytes.len()))?;
    let peer_pub = PublicKey::from_bytes(&peer_arr)
        .context("parsing peer pubkey")?;

    let sealed = Sealed::from_base64(&ciphertext_b64)
        .context("parsing --ciphertext-b64")?;

    let plaintext = match (my_ephemeral_secret, peer_ephemeral_pub) {
        (Some(my_eph_sec), Some(peer_eph_pub_hex)) => {
            let my_eph = EphemeralKeyPair::from_secret_hex(&my_eph_sec)
                .context("parsing --my-ephemeral-secret")?;
            let peer_eph_pub = ephemeral_public_from_hex(&peer_eph_pub_hex)
                .context("parsing --peer-ephemeral-pub")?;
            open_fs(&kp, &my_eph, &peer_pub, &peer_eph_pub, pair_id, &sealed)
                .context("open_fs failed")?
        }
        (None, None) => {
            open(&kp, &peer_pub, pair_id, &sealed)
                .context("open failed (wrong key, wrong pair_id, or tampered ciphertext)")?
        }
        _ => anyhow::bail!(
            "forward-secrecy requires BOTH --my-ephemeral-secret AND --peer-ephemeral-pub \
             (or neither, for the Sprint E static-key fallback)"
        ),
    };
    print!("{}", String::from_utf8_lossy(&plaintext));
    Ok(())
}

/// PAIRED-CHANNELS Sprint F: generate a fresh ephemeral X25519
/// keypair. Output JSON: {public_hex, secret_hex}. Caller persists
/// the secret locally (wipe when pair ends to honor FS) and
/// publishes the public in pair_request / pair_confirm.
async fn run_pair_generate_ephemeral() -> Result<()> {
    use web4_core::pair_channel::EphemeralKeyPair;
    let eph = EphemeralKeyPair::generate();
    let out = serde_json::json!({
        "public_hex": eph.public_hex(),
        "secret_hex": eph.secret_hex(),
    });
    println!("{}", serde_json::to_string_pretty(&out)?);
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
    fn starter_law_folds_rwoa_gradient() {
        use hub_lib::law::{Decision, Law, R6Request};
        let law: Law = Law::parse_and_validate(STARTER_LAW_YAML).expect("embedded starter law validates");
        let req = |action: &str| R6Request {
            role: "citizen".into(),
            action: action.into(),
            payload: Default::default(),
            resource: Default::default(),
        };
        // The gate evaluates `action` = HubEvent::kind() (member_added,
        // role_assigned, ...). Named norms cover the highest-stakes kinds:
        assert_eq!(law.evaluate(&req("role_assigned")), Decision::Escalate);
        assert_eq!(law.evaluate(&req("charter_amended")), Decision::Escalate);
        assert_eq!(law.evaluate(&req("law_amended")), Decision::Escalate);
        // S conservative default catches the other consequential governance kinds:
        assert_eq!(law.evaluate(&req("member_added")), Decision::Escalate);
        assert_eq!(law.evaluate(&req("council_threshold_changed")), Decision::Escalate);
        assert_eq!(law.evaluate(&req("pairing_revoked")), Decision::Escalate);
        // Low-stakes / reversible / informational kinds ride the permissive base:
        assert_eq!(law.evaluate(&req("member_join_requested")), Decision::Allow);
        assert_eq!(law.evaluate(&req("event_recorded")), Decision::Allow);
        assert_eq!(law.evaluate(&req("reputation_recorded")), Decision::Allow);
    }

    #[test]
    fn hub_up_public_archetypes_are_fail_closed() {
        assert!(find_archetype("nope").is_none());
        assert_eq!(find_archetype("dev").unwrap().operator_auth, "loopback");
        assert!(find_archetype("public-tunnel").unwrap().tunnel);
        for a in ARCHETYPES {
            if a.id.starts_with("public-") {
                assert_eq!(a.operator_auth, "token", "public must use token auth: {}", a.id);
                assert_eq!(a.profile, Some("production"), "public must set production: {}", a.id);
                assert!(a.needs_domain, "public needs a domain: {}", a.id);
            } else {
                assert_eq!(a.operator_auth, "loopback", "non-public uses loopback: {}", a.id);
            }
        }
    }

    #[test]
    fn production_preflight_requires_law_and_https_origin() {
        // Happy path: law present + https origin + operator token auth.
        assert!(production_preflight(true, "https://hub.4-gov.org", false, false, true, false).is_ok());
        // No law → refused, unless HUB_ALLOW_NO_LAW.
        assert!(production_preflight(false, "https://x", false, false, true, false).is_err());
        assert!(production_preflight(false, "https://x", true, false, true, false).is_ok());
        // Missing / http origin → refused, unless HUB_ALLOW_INSECURE_ORIGIN.
        assert!(production_preflight(true, "", false, false, true, false).is_err());
        assert!(production_preflight(true, "http://x", false, false, true, false).is_err());
        assert!(production_preflight(true, "http://x", false, true, true, false).is_ok());
    }

    #[test]
    fn production_preflight_requires_operator_token() {
        // HUB-002: loopback-only operator auth → refused in production...
        assert!(production_preflight(true, "https://x", false, false, false, false).is_err());
        // ...unless the deployment explicitly claims host access as the factor.
        assert!(production_preflight(true, "https://x", false, false, false, true).is_ok());
        // Token mode satisfies it outright.
        assert!(production_preflight(true, "https://x", false, false, true, false).is_ok());
    }

    #[test]
    fn slugify_handles_common_cases() {
        assert_eq!(slugify("Lisbon Chapter"), "lisbon-chapter");
        assert_eq!(slugify("NYC Chapter #1"), "nyc-chapter-1");
        // Unicode letters survive via char::is_alphanumeric — fine for hub dirs.
        assert_eq!(slugify("São Paulo"), "são-paulo");
        assert_eq!(slugify("東京"), "東京");
        assert_eq!(slugify("   spaces   "), "spaces");
        assert_eq!(slugify(""), "");
    }

    /// The public/operator **plane split** — which router a route is declared in
    /// — is the hub's primary network boundary, and nothing tested it. Until the
    /// 2026-07-23 review, `/admin/ledger` and `/admin/pairs` were on the public
    /// plane; the only automated guard on the Sovereign-signing write tools is
    /// `mcp::require_loopback`, which `mcp.rs` itself documents as defeated by a
    /// same-host reverse proxy — the public-deploy topology. A route that lands
    /// in `public_plane_router` is anonymously reachable from the internet on a
    /// `--bind 0.0.0.0` hub (this one).
    ///
    /// These drive the **assembled routers**, not a list of route strings, so
    /// moving a route between `admin::router` / `admin::operator_router` /
    /// `mcp::{read,operator_read,write}_router` is what the assertions see.
    /// The layers `run_serve` puts over each plane (rate limit, lock gate,
    /// operator auth) add and remove no routes, so omitting them here does not
    /// weaken the guard — it isolates it to the split.
    mod plane_split {
        use super::*;
        use crate::rest::channel_e2e_tests::fresh_rest_state;
        use axum::body::Body;
        use axum::http::{Request, StatusCode};
        use tower::ServiceExt;

        /// A real chapter, and the same `(rest, mcp)` state pair `run_serve`
        /// builds (McpState sharing RestState's signer / ledger / law / key).
        async fn planes() -> (tempfile::TempDir, Router, Router) {
            let (tmp, rest) = fresh_rest_state(None).await;
            let mcp = McpState::open_with_law_and_ledger(
                rest.paths.root.clone(),
                rest.law.clone(),
                rest.ledger.clone(),
                rest.signer.clone(),
                rest.sovereign_lct_id,
                rest.store_key.clone(),
                rest.hub_id,
                rest.hub_name.clone(),
            )
            .await
            .unwrap();
            let mut operator = rest.clone();
            operator.operator_plane = true;
            let public = public_plane_router(mcp.clone(), rest.clone(), rest.clone());
            let op = operator_plane_router(mcp, operator);
            (tmp, public, op)
        }

        async fn status(app: &Router, method: &str, path: &str) -> StatusCode {
            let req = Request::builder()
                .method(method)
                .uri(path)
                .body(Body::empty())
                .unwrap();
            app.clone().oneshot(req).await.unwrap().status()
        }

        /// Everything the operator plane carries and the public plane must not.
        /// 404 is the exact assertion: a route that exists but rejects the caller
        /// answers 405/500/403 — only an unrouted path answers 404, so this
        /// cannot be satisfied by a handler-level check that a proxy defeats.
        const OPERATOR_ONLY: &[(&str, &str)] = &[
            // Rosters, skills, relationship data, act payloads.
            ("GET", "/admin"),
            ("GET", "/admin/members"),
            ("GET", "/admin/joins"),
            ("GET", "/admin/manage"),
            ("GET", "/admin/ledger"),
            // Index 0 (genesis) EXISTS on a fresh chapter — `ledger_detail`
            // answers its own 404 for a missing index, so a nonexistent one
            // would make both directions of this table unfalsifiable.
            ("GET", "/admin/ledger/0"),
            ("GET", "/admin/pairs"),
            // MCP member/skill enumeration (public-release P0).
            ("GET", "/tools/list_members"),
            ("GET", "/tools/find_skill?q=rust"),
            // MCP write tools — these sign as the Sovereign.
            ("POST", "/tools/add_member"),
            ("POST", "/tools/assign_role"),
            ("POST", "/tools/record_event"),
            ("POST", "/tools/declare_skill"),
            // The admin write API — admit/deny/remove/re-key/limits.
            ("POST", "/admin/api/members/add"),
            ("POST", "/admin/api/members/00000000-0000-0000-0000-000000000000/key"),
            ("POST", "/admin/api/members/00000000-0000-0000-0000-000000000000/remove"),
            ("POST", "/admin/api/members/00000000-0000-0000-0000-000000000000/admission-reset"),
            ("POST", "/admin/api/admission-limits"),
            ("POST", "/admin/api/joins/00000000-0000-0000-0000-000000000000/admit"),
            ("POST", "/admin/api/joins/00000000-0000-0000-0000-000000000000/deny"),
            ("POST", "/admin/api/reviews/00000000-0000-0000-0000-000000000000/grant"),
            ("POST", "/admin/api/reviews/00000000-0000-0000-0000-000000000000/refuse"),
            ("GET", "/admin/api/ledger"),
            ("GET", "/admin/api/joins"),
            ("GET", "/admin/api/reviews"),
        ];

        #[tokio::test]
        async fn the_public_plane_serves_only_its_allowlist() {
            let (_tmp, public, _op) = planes().await;
            for (method, path) in OPERATOR_ONLY {
                assert_eq!(
                    status(&public, method, path).await,
                    StatusCode::NOT_FOUND,
                    "{method} {path} is REACHABLE on the public (network-facing) plane — \
                     it belongs on the operator listener"
                );
            }
        }

        /// The other half: moving a route off the public plane must not be how
        /// the guard above passes. Public transparency is law + roles + council
        /// + the hub's own identity, and it has to keep working.
        #[tokio::test]
        async fn the_public_plane_still_serves_the_transparency_surface() {
            let (_tmp, public, _op) = planes().await;
            for path in ["/", "/admin/roles", "/admin/law", "/admin/council", "/tools", "/tools/query_hub"] {
                assert_eq!(
                    status(&public, "GET", path).await,
                    StatusCode::OK,
                    "{path} must stay served on the public plane"
                );
            }
        }

        /// And the operator plane must actually carry every route the first test
        /// banished, or "not on the public plane" would be satisfiable by the
        /// route existing nowhere at all. Not-404 rather than 200: these handlers
        /// want `ConnectInfo`/bodies a bare `oneshot` doesn't supply, and *routed*
        /// is the property under test.
        #[tokio::test]
        async fn the_operator_plane_carries_what_the_public_plane_refuses() {
            let (_tmp, _public, op) = planes().await;
            for (method, path) in OPERATOR_ONLY {
                assert_ne!(
                    status(&op, method, path).await,
                    StatusCode::NOT_FOUND,
                    "{method} {path} is on NEITHER plane — the operator lost it"
                );
            }
        }
    }

    /// The residual #614 left open: "the three redaction sites are now correct;
    /// nothing structurally prevents a fourth."
    ///
    /// #614 fixed three `internal(..)` constructors and its tests name each one.
    /// That shape cannot see a *fourth* leak site: a handler added tomorrow with
    /// its own error type and its own `From<anyhow::Error>` reintroduces the
    /// leak and no existing test notices, because every existing test names a
    /// constructor. `redact_internal` is a convention, and a convention is not a
    /// constraint.
    ///
    /// #614 proposed closing this as a property over the **router** — drive
    /// every public route to a 500 and assert on the bodies — and recorded the
    /// blocker as "needs a way to force an arbitrary handler to fail, which does
    /// not exist today." The forcing mechanism did exist: #614 built it for
    /// `read_state` and used it once (**the storage goes away under a running,
    /// unlocked hub** — the signer stays live, so `lock_gate` passes and the
    /// handler runs).
    ///
    /// **That route-level property was built here and it does not work.**
    /// Measured, by mutating `redact_internal` to pass its detail through and
    /// re-running: every public-plane 500 the fixture can produce carries the
    /// same detail-free sentence, `no society found in hub store` — no path, no
    /// filename, no OS or sqlite reason. The leaking mutant survives the whole
    /// 41-pair sweep. It also survives #614's own end-to-end test — then named
    /// `the_public_state_route_does_not_name_the_store_it_failed_to_open`,
    /// **renamed under #617** to
    /// `the_public_state_route_answers_500_with_a_correlation_reference_when_its_store_is_gone`
    /// once this finding was applied at its own site — which asserts
    /// `!body.contains(root_path)` against that same sentence, so that test is
    /// vacuous with respect to the disclosure the old name claimed, and was
    /// vacuous when it was written. Corrupting the db instead does not help
    /// (`society()` still returns `Ok` — the store handle is already open), and
    /// an encrypted-store fixture is refused upstream by `lock_gate` for
    /// everything outside tier-0.
    ///
    /// So the residual is closed **at the type level** instead, by
    /// [`no_error_type_renders_a_response_without_a_redaction_test`]: the set of
    /// types that can render a response is asserted closed, so a fourth one
    /// fails the build until someone adds its redaction case. That guard was
    /// mutation-checked — a fourth error type with a leaking
    /// `From<anyhow::Error>` added to `mcp.rs` fails it.
    ///
    /// The route sweep is kept because it is a real net for a *different* leak —
    /// a handler that formats a path into any response, at any status, rather
    /// than through the `internal(..)` constructors — and because its route list
    /// is parsed from the routers' own source, so a route added tomorrow is
    /// covered without anyone remembering this module exists. It is **not** a
    /// guard on `redact_internal`; nothing here is, and the sentence above says
    /// why.
    mod public_plane_redaction {
        use super::*;
        use crate::rest::channel_e2e_tests::fresh_rest_state;
        use axum::body::Body;
        use axum::extract::ConnectInfo;
        use axum::http::{Request, StatusCode};
        use std::net::SocketAddr;
        use tower::ServiceExt;

        /// A request the way the real listener presents it. `run_serve` serves
        /// these routers through `into_make_service_with_connect_info`, so the
        /// peer address is always present in production; a bare `oneshot`
        /// without it is rejected by the `ConnectInfo` extractor *before the
        /// handler runs*, which would silently exempt every peer-aware route
        /// (`/unlock`, `/channel`, the join path) from this sweep — exactly the
        /// routes with the most to leak.
        fn request(method: &str, path: &str) -> Request<Body> {
            let mut req = Request::builder()
                .method(method)
                .uri(path)
                .header("content-type", "application/json")
                .body(Body::from("{}"))
                .unwrap();
            req.extensions_mut().insert(ConnectInfo(
                "203.0.113.7:54321".parse::<SocketAddr>().unwrap(),
            ));
            req
        }

        /// The route literals declared inside one router function, read from
        /// that function's own source at compile time.
        ///
        /// Parsing the source instead of maintaining a list is the point: the
        /// guard has to cover routes nobody thought about when writing it. The
        /// parse is deliberately brittle in the safe direction — a signature it
        /// cannot find, or a body with no routes in it, fails the test loudly
        /// rather than silently covering nothing.
        fn declared_routes(src: &str, marker: &str) -> Vec<String> {
            let start = src.find(marker).unwrap_or_else(|| {
                panic!(
                    "router signature {marker:?} not found — this parser has drifted from \
                     the source it guards; fix the marker, do not delete the test"
                )
            });
            // Router fns are top-level, so the first column-0 `}` closes it.
            let body = &src[start..];
            let end = body
                .find("\n}\n")
                .unwrap_or_else(|| panic!("unterminated router fn at {marker:?}"));
            let body = &body[..end];

            let mut out = Vec::new();
            let mut rest = body;
            while let Some(i) = rest.find(".route(\"") {
                rest = &rest[i + r#".route(""#.len()..];
                let j = rest
                    .find('"')
                    .unwrap_or_else(|| panic!("unterminated route literal in {marker:?}"));
                out.push(rest[..j].to_string());
                rest = &rest[j..];
            }
            assert!(
                !out.is_empty(),
                "parsed zero routes out of {marker:?} — the parse broke and this test \
                 would pass by covering nothing"
            );
            out
        }

        /// Every route on the public plane, from the three routers
        /// `public_plane_router` merges. Kept in lockstep with that function by
        /// `the_route_sources_match_the_assembled_public_plane` below.
        fn public_plane_routes() -> Vec<String> {
            let mut v = declared_routes(
                include_str!("mcp.rs"),
                "pub fn read_router(state: McpState) -> Router {",
            );
            v.extend(declared_routes(
                include_str!("rest.rs"),
                "pub fn router(state: RestState) -> Router {",
            ));
            v.extend(declared_routes(
                include_str!("admin.rs"),
                "pub fn router(state: RestState) -> Router {",
            ));
            v
        }

        /// `:param` → something a handler will accept far enough to reach the
        /// store. `:hub_id` must be the real one or `lock_gate`/the hub-id check
        /// short-circuits before the handler runs.
        fn concrete(path: &str, hub_id: Uuid) -> String {
            path.split('/')
                .map(|seg| match seg.strip_prefix(':') {
                    Some("hub_id") => hub_id.to_string(),
                    Some(_) => Uuid::nil().to_string(),
                    None => seg.to_string(),
                })
                .collect::<Vec<_>>()
                .join("/")
        }

        /// What an internal failure must never tell an anonymous caller. These
        /// are the substrings a real store failure carries on this hub, not
        /// invented ones: the absolute society path, the db filename, the
        /// passphrase sentence, and the raw OS/sqlite reason.
        fn leak_needles(root: &str) -> Vec<String> {
            vec![
                root.to_string(),
                "hub.db".into(),
                "HUB_PASSPHRASE".into(),
                "No such file".into(),
                "os error".into(),
                "SqliteFailure".into(),
            ]
        }

        /// A status axum's own body extractor produces *before* the handler
        /// runs. The sweep sends `{}` to every route, which is a valid body for
        /// almost none of them, so these say "this route was checked as far as
        /// its extractor and no further".
        fn body_extractor_rejected(status: StatusCode) -> bool {
            matches!(
                status,
                StatusCode::BAD_REQUEST
                    | StatusCode::UNSUPPORTED_MEDIA_TYPE
                    | StatusCode::UNPROCESSABLE_ENTITY
            )
        }

        /// The declared limit of this sweep. A generic driver cannot construct
        /// a valid body for a route it knows nothing about — a signed envelope,
        /// a sealed channel request, an unlock attestation — so these routes
        /// are exercised only up to their `Json<T>` extractor. They are listed,
        /// not hidden, because a guard that quietly covers half its surface
        /// reads as covering all of it.
        const BODY_EXEMPT: &[&str] = &[
            "/v1/auth/challenge",
            "/v1/hubs/:hub_id/channel",
            "/v1/hubs/:hub_id/constellation/enroll",
            "/v1/hubs/:hub_id/constellation/revoke",
            "/v1/hubs/:hub_id/council/propose",
            "/v1/hubs/:hub_id/council/sign",
            "/v1/hubs/:hub_id/credential",
            "/v1/hubs/:hub_id/events",
            "/v1/hubs/:hub_id/lcts/publish",
            "/v1/hubs/:hub_id/members/join",
            "/v1/hubs/:hub_id/pairs/:pair_id/confirm",
            "/v1/hubs/:hub_id/pairs/:pair_id/messages",
            "/v1/hubs/:hub_id/pairs/:pair_id/revoke",
            "/v1/hubs/:hub_id/pairs/request",
            "/v1/hubs/:hub_id/unlock",
            "/v1/hubs/:hub_id/unlock/attest",
            // NOT `/unlock/challenge`: it refuses (403) ahead of its body, so
            // the sweep does reach its handler.
            "/v1/hubs/:hub_id/vp/request",
            "/v1/hubs/:hub_id/vp/response",
        ];

        /// Drives the whole declared public surface with the store removed and
        /// asserts that no response, at any status, names the store.
        ///
        /// Scope, stated because it is narrower than the name suggests: this
        /// catches a handler that puts a path or an OS reason into a response
        /// body directly. It does **not** catch a regression in
        /// `redact_internal` — see the module comment; the failure this fixture
        /// induces carries no detail to leak, which was measured by mutation and
        /// not assumed.
        #[tokio::test]
        async fn no_public_plane_route_names_the_store_when_it_fails() {
            let (_tmp, rest) = fresh_rest_state(None).await;
            let mcp = McpState::open_with_law_and_ledger(
                rest.paths.root.clone(),
                rest.law.clone(),
                rest.ledger.clone(),
                rest.signer.clone(),
                rest.sovereign_lct_id,
                rest.store_key.clone(),
                rest.hub_id,
                rest.hub_name.clone(),
            )
            .await
            .unwrap();
            let public = public_plane_router(mcp, rest.clone(), rest.clone());

            let root = rest.paths.root.clone();
            let root_s = root.display().to_string();
            let needles = leak_needles(&root_s);

            // The storage goes away under a running, unlocked hub.
            std::fs::remove_dir_all(&root).unwrap();
            assert!(
                rest.society().await.is_err(),
                "the fixture never reached the failure state — every route below would \
                 answer from cache and this test would pass for the wrong reason"
            );

            let routes = public_plane_routes();
            let mut server_errors = 0usize;
            let mut reached = 0usize;
            let mut exempt: std::collections::BTreeSet<String> = Default::default();

            for route in &routes {
                let path = concrete(route, rest.hub_id);
                for method in ["GET", "POST"] {
                    let resp = public.clone().oneshot(request(method, &path)).await.unwrap();
                    let status = resp.status();
                    // 405 = this route exists under the other method; not a case.
                    if status == StatusCode::METHOD_NOT_ALLOWED {
                        continue;
                    }
                    if body_extractor_rejected(status) {
                        exempt.insert(route.clone());
                    } else {
                        reached += 1;
                        if status.is_server_error() {
                            server_errors += 1;
                        }
                    }
                    // Asserted on every response, not only the 5xx: a 200 that
                    // names the store is the same disclosure, and a rejection
                    // body is written by the same code path.
                    let bytes = axum::body::to_bytes(resp.into_body(), usize::MAX)
                        .await
                        .unwrap();
                    let body = String::from_utf8_lossy(&bytes);
                    for needle in &needles {
                        assert!(
                            !body.contains(needle.as_str()),
                            "{method} {path} answered {status} and published {needle:?} to an \
                             anonymous caller on the network-facing plane:\n{body}"
                        );
                    }
                }
            }

            // The coverage cap, declared rather than silent. Everything in
            // BODY_EXEMPT is checked only as far as its body extractor; the
            // handler behind it is NOT driven by this sweep. Exact equality
            // both ways: a new POST route lands here and its author has to
            // notice, and a route that stops being exempt has to be removed so
            // the list never over-states the gap.
            let exempt: Vec<&str> = exempt.iter().map(String::as_str).collect();
            assert_eq!(
                exempt, BODY_EXEMPT,
                "the set of routes this sweep cannot drive past their body extractor has \
                 changed. If you added a route, it is NOT covered end-to-end here — add it \
                 to BODY_EXEMPT (and prefer a route-specific test that supplies a valid \
                 body). If a route left the list, delete it from BODY_EXEMPT."
            );

            // Vacuity guards. Without these the test passes if the parse yields
            // a short list, or if nothing actually failed.
            assert!(
                routes.len() >= 36,
                "only {} public routes parsed — the source parse is under-reading",
                routes.len()
            );
            assert!(
                reached >= 20,
                "only {reached} route/method pairs reached a handler"
            );
            assert!(
                server_errors >= 4,
                "removing the store drove only {server_errors} routes into 5xx — the fixture \
                 is no longer inducing the failure this test is about, so a leak would not \
                 be seen"
            );
        }

        /// A 500 that says nothing and gives no way to find what happened is a
        /// deletion, not a redaction. Asserted only on 500 — `locked_error`'s
        /// curated 503 is the fleet's ignition instruction and must stay
        /// un-redacted (see `a_curated_5xx_keeps_the_sentence_the_caller_must_act_on`).
        #[tokio::test]
        async fn every_internal_error_on_the_public_plane_is_traceable_to_the_log() {
            let (_tmp, rest) = fresh_rest_state(None).await;
            let mcp = McpState::open_with_law_and_ledger(
                rest.paths.root.clone(),
                rest.law.clone(),
                rest.ledger.clone(),
                rest.signer.clone(),
                rest.sovereign_lct_id,
                rest.store_key.clone(),
                rest.hub_id,
                rest.hub_name.clone(),
            )
            .await
            .unwrap();
            let public = public_plane_router(mcp, rest.clone(), rest.clone());
            std::fs::remove_dir_all(&rest.paths.root).unwrap();

            let mut checked = 0usize;
            for route in &public_plane_routes() {
                let path = concrete(route, rest.hub_id);
                for method in ["GET", "POST"] {
                    let resp = public.clone().oneshot(request(method, &path)).await.unwrap();
                    if resp.status() != StatusCode::INTERNAL_SERVER_ERROR {
                        continue;
                    }
                    let bytes = axum::body::to_bytes(resp.into_body(), usize::MAX)
                        .await
                        .unwrap();
                    let body = String::from_utf8_lossy(&bytes);
                    assert!(
                        body.contains("reference"),
                        "{method} {path} answered 500 with no correlation reference — the \
                         detail was deleted rather than moved to the hub log:\n{body}"
                    );
                    checked += 1;
                }
            }
            assert!(
                checked >= 4,
                "only {checked} 500s seen — the store-removal fixture is no longer driving \
                 the public plane into internal failure, so this asserts nothing"
            );
        }

        /// The residual stated at the type level, which is where it actually
        /// bites.
        ///
        /// #614's redaction tests each name a constructor, so they are blind to
        /// a **new error type**: add one with its own `From<anyhow::Error>`, use
        /// `?` in a public handler, and the anyhow chain renders to an anonymous
        /// caller with no test failing. `redact_internal` is a convention and a
        /// convention cannot see a type that does not use it.
        ///
        /// This does not try to prove a new type redacts — a source grep cannot
        /// follow `AdminError::internal` to the `redact_internal` inside it. It
        /// asserts the weaker thing that is actually checkable and actually
        /// sufficient: the set of types that can render a response is closed.
        /// A fourth one fails here, and the author has to come to
        /// `internal_error_redaction_tests` and add its case before this test
        /// goes green again.
        #[test]
        fn no_error_type_renders_a_response_without_a_redaction_test() {
            /// Every type with a redaction case in
            /// `rest::internal_error_redaction_tests`.
            const COVERED: &[&str] = &[
                "admin.rs::AdminError",
                "mcp.rs::ApiError",
                "rest.rs::ApiError",
            ];

            let mut found: Vec<String> = Vec::new();
            for (file, src) in [
                ("mcp.rs", include_str!("mcp.rs")),
                ("admin.rs", include_str!("admin.rs")),
                ("rest.rs", include_str!("rest.rs")),
                ("main.rs", include_str!("main.rs")),
                ("rate_limit.rs", include_str!("rate_limit.rs")),
            ] {
                for line in src.lines() {
                    // Only real declarations: `impl IntoResponse for X {` at
                    // column 0. Doc comments and prose mentioning the trait are
                    // indented or lack the `impl` prefix.
                    let Some(rest_of) = line.strip_prefix("impl IntoResponse for ") else {
                        continue;
                    };
                    let ty = rest_of.trim_end_matches(" {").trim();
                    found.push(format!("{file}::{ty}"));
                }
            }
            found.sort();

            assert_eq!(
                found, COVERED,
                "the set of error types that can render a response on the hub's planes has \
                 changed. A type not listed here has no redaction test, and its \
                 `From<anyhow::Error>` (if any) will publish the anyhow chain — the store's \
                 absolute path, sqlite's reason, the passphrase sentence — to an anonymous \
                 caller on a `--bind 0.0.0.0` hub. Add a case to \
                 `rest::internal_error_redaction_tests` and then update COVERED."
            );
        }

        /// The parse covers what `public_plane_router` actually merges. If a
        /// fourth router joins that function, this fails and the two tests above
        /// stop being a claim about "the public plane" they cannot back.
        #[test]
        fn the_route_sources_match_the_assembled_public_plane() {
            let src = include_str!("main.rs");
            let start = src
                .find("fn public_plane_router(")
                .expect("public_plane_router not found");
            let body = &src[start..];
            let body = &body[..body.find("\n}\n").expect("unterminated fn")];
            // One base router plus N `.merge(` calls. `public_plane_routes()`
            // parses exactly these three sources; a fourth would be invisible
            // to it, and the two sweeps above would still claim to cover "the
            // public plane".
            let merged = body.matches(".merge(").count();
            assert_eq!(
                merged, 2,
                "public_plane_router composes {} routers now, not 3; \
                 public_plane_routes() must be updated to parse them all:\n{body}",
                merged + 1
            );
            for source in ["mcp_read_router(", "rest_router(", "admin::router("] {
                assert!(
                    body.contains(source),
                    "public_plane_router no longer merges {source} — the source that \
                     public_plane_routes() parses is not the one being served:\n{body}"
                );
            }
        }
    }

    /// The other half of the plane boundary. `plane_split` pins **which router**
    /// a route is declared in; these pin **where each router is served** and
    /// **in what order its gates run**. Both are decided in `run_serve` and
    /// neither was tested: a route can sit correctly in `operator_plane_router`
    /// and still be published to the internet if the operator listener follows
    /// `--bind`, which on this hub is `0.0.0.0`.
    mod listener_construction {
        use super::*;
        use std::net::SocketAddr;

        /// Every bind this hub or the `hub up` archetype table can produce.
        const BINDS: &[&str] = &[
            "127.0.0.1",      // dev / public-tunnel archetypes
            "0.0.0.0",        // this hub (tailnet) + private-vpn + both public archetypes
            "100.65.206.122", // a concrete public/tailnet interface
            "[::1]",          // IPv6 loopback, bracketed
        ];

        /// The one that matters. The operator plane carries the Sovereign-signing
        /// write tools and the admit/deny/remove/re-key API; it must be on
        /// loopback no matter what the public listener binds.
        #[test]
        fn the_operator_plane_stays_on_loopback_under_every_public_bind() {
            for bind in BINDS {
                let (_public, operator) = plane_addrs(bind, 8770, 8772).unwrap();
                let op = operator.expect("operator plane must exist at admin_port 8772");
                assert_eq!(
                    op,
                    "127.0.0.1:8772".parse::<SocketAddr>().unwrap(),
                    "--bind {bind} moved the Sovereign-signing operator plane off loopback"
                );
                assert!(op.ip().is_loopback(), "--bind {bind} published the operator plane");
            }
        }

        /// `admin_port 0` means *no operator plane*, not "port 0" — which the OS
        /// resolves to an arbitrary ephemeral port, giving a Sovereign-signing
        /// listener that is neither disabled nor findable.
        #[test]
        fn admin_port_zero_disables_the_operator_plane_rather_than_binding_an_ephemeral_port() {
            let (_public, operator) = plane_addrs("0.0.0.0", 8770, 0).unwrap();
            assert!(operator.is_none(), "admin_port 0 must disable the plane, got {operator:?}");
        }

        /// And the public listener must still bind exactly what it was told —
        /// pinning the operator plane to loopback must not be achieved by
        /// pinning both.
        #[test]
        fn the_public_plane_binds_exactly_what_it_was_told() {
            for bind in BINDS {
                let (public, _operator) = plane_addrs(bind, 8770, 8772).unwrap();
                assert_eq!(public, format!("{bind}:8770").parse::<SocketAddr>().unwrap());
            }
        }

        /// `--bind localhost` and `--bind ::1` do not work and never did: the
        /// `SocketAddr` parse rejects both before anything else runs. That was
        /// previously a bare `AddrParseError` with no hint, while the loopback
        /// classifier a hundred lines down listed both as supported spellings.
        /// The refusal is pinned here *and* made to name what it accepts.
        #[test]
        fn a_hostname_bind_is_refused_and_the_error_names_what_is_accepted() {
            for bind in ["localhost", "::1"] {
                let err = plane_addrs(bind, 8770, 8772).unwrap_err().to_string();
                assert!(err.contains(bind), "error must name the rejected bind: {err}");
                assert!(err.contains("[::1]"), "error must show the bracketed form: {err}");
            }
        }

        /// The production-hardening warning fires on `!loopback`, so the failure
        /// that matters is a network-reachable bind classified as loopback —
        /// that silently drops the "hardening is NOT enforced" notice on a public
        /// hub. Both directions are asserted; the unspecified addresses
        /// (`0.0.0.0`, `[::]`) are the ones a `is_unspecified`-shaped mistake
        /// would still get right, so the concrete interface IP carries the test.
        #[test]
        fn a_network_reachable_bind_is_never_classified_as_loopback() {
            for bind in ["0.0.0.0", "[::]", "100.65.206.122", "192.168.1.10"] {
                let (public, _) = plane_addrs(bind, 8770, 8772).unwrap();
                assert!(
                    !public_bind_is_loopback(&public),
                    "--bind {bind} is network-reachable but was classified loopback — \
                     the public-bind hardening warning would be suppressed"
                );
            }
            // 127.0.0.2 is loopback too; the string match this replaced warned on it.
            for bind in ["127.0.0.1", "127.0.0.2", "[::1]"] {
                let (public, _) = plane_addrs(bind, 8770, 8772).unwrap();
                assert!(public_bind_is_loopback(&public), "--bind {bind} is loopback");
            }
        }
    }

    /// Layer **order** on the operator plane. Both gates run under either order,
    /// so this is not about whether the plane is guarded — it is about which gate
    /// answers a caller who has no standing to ask anything at all.
    mod operator_layer_order {
        use super::*;
        use crate::rest::channel_e2e_tests::fresh_rest_state;
        use axum::body::Body;
        use axum::extract::ConnectInfo;
        use axum::http::{Request, StatusCode};
        use std::net::SocketAddr;
        use tower::ServiceExt;

        /// A **locked** hub, which is the only state where the two gates disagree:
        /// an unlocked hub's lock gate passes everything, making the order
        /// unobservable. Built the way `run_serve` builds a locked boot — a clear
        /// `public-identity.json` plus `open_locked_shell` (a locked-boot RestState
        /// installs a `LockedSigner`, which is what `is_locked()` reads).
        async fn locked_operator_app() -> (tempfile::TempDir, Router) {
            let (tmp, rest) = fresh_rest_state(None).await;
            crate::rest::PublicIdentity {
                hub_id: rest.hub_id,
                hub_name: rest.hub_name.clone(),
                founding_sovereign_lct_id: rest.sovereign_lct_id,
                sovereign_pubkey_hex: None,
            }
            .write(&rest.paths.root)
            .unwrap();
            let locked = crate::rest::RestState::open_locked_shell(
                rest.paths.root.clone(),
                rest.law.clone(),
                rest.ledger.clone(),
            )
            .await
            .unwrap();
            assert!(locked.is_locked(), "fixture must be locked or the order is unobservable");
            let mcp = McpState::open_with_law_and_ledger(
                locked.paths.root.clone(),
                locked.law.clone(),
                locked.ledger.clone(),
                locked.signer.clone(),
                locked.sovereign_lct_id,
                locked.store_key.clone(),
                locked.hub_id,
                locked.hub_name.clone(),
            )
            .await
            .unwrap();
            let mut operator = locked.clone();
            operator.operator_plane = true;
            // Default (no HUB_OPERATOR_AUTH) = loopback mode, so a non-loopback
            // peer is the unauthorized caller — no env mutation, no token file.
            let op_auth = crate::rest::OperatorAuth::from_env(&locked.paths.root).unwrap();
            let app = operator_plane_app(
                operator_plane_router(mcp, operator),
                locked.clone(),
                op_auth,
            );
            (tmp, app)
        }

        /// A stranger off the network, hitting a locked hub, on a path the lock
        /// gate does not allowlist. Auth outermost → `403 operator plane is
        /// local-only`. Lock gate outermost → `503 locked`, which hands the hub's
        /// lock state to a caller the very next layer was about to refuse.
        #[tokio::test]
        async fn an_unauthorized_operator_caller_is_refused_before_the_lock_gate() {
            let (_tmp, app) = locked_operator_app().await;
            let mut req = Request::builder()
                .method("GET")
                .uri("/admin/members")
                .body(Body::empty())
                .unwrap();
            req.extensions_mut()
                .insert(ConnectInfo("203.0.113.7:44444".parse::<SocketAddr>().unwrap()));
            let status = app.oneshot(req).await.unwrap().status();
            assert_eq!(
                status,
                StatusCode::FORBIDDEN,
                "expected the operator-auth gate to answer first; 503 means the lock gate is \
                 outermost and discloses lock state to an unauthorized caller"
            );
        }

        /// The other direction: an authorized (loopback) caller on a locked hub
        /// must still be stopped by the lock gate. Without this, putting auth
        /// outermost would be satisfiable by dropping the lock gate entirely.
        #[tokio::test]
        async fn an_authorized_caller_is_still_stopped_by_the_lock_gate() {
            let (_tmp, app) = locked_operator_app().await;
            let mut req = Request::builder()
                .method("GET")
                .uri("/admin/members")
                .body(Body::empty())
                .unwrap();
            req.extensions_mut()
                .insert(ConnectInfo("127.0.0.1:44444".parse::<SocketAddr>().unwrap()));
            let status = app.oneshot(req).await.unwrap().status();
            assert_ne!(
                status,
                StatusCode::OK,
                "a locked hub served an operator write page — the lock gate is not applied"
            );
        }
    }

    /// What a **locked** hub actually answers on its network-facing plane,
    /// driven end-to-end through the assembled public router with the real
    /// `lock_gate` layered over it. `rest::lock_gate_tests` pins the allowlist
    /// predicate; this pins that the predicate is the thing a caller meets, and
    /// that the handlers behind it are never reached.
    ///
    /// This state is not hypothetical for this hub: `web4-fleet/config.toml`
    /// carries no `[storage]` section and its `hub.db` is SQLCipher-encrypted,
    /// so disk auto-detection resolves sqlite, `open_hub_store_async` fails
    /// closed, and `run_serve` boots the locked shell on every restart until an
    /// operator ignites it.
    mod locked_tier0_surface {
        use super::*;
        use axum::body::Body;
        use axum::http::{Request, StatusCode};
        use tower::ServiceExt;

        async fn locked_public_app() -> (tempfile::TempDir, Router, uuid::Uuid) {
            let tmp = tempfile::tempdir().unwrap();
            let sov = tmp.path().join("sovereign.json");
            hub_lib::identity::IdentityFile::generate(web4_core::lct::EntityType::Human)
                .save(&sov)
                .unwrap();
            let hub_dir = tmp.path().join("chapter");
            hub_lib::init::init_hub(hub_lib::init::InitArgs {
                hub_name: "E2E Test Hub".into(),
                hub_dir: hub_dir.clone(),
                sovereign_lct_path: sov,
                storage: Some(hub_lib::store::BackendKind::Sqlite),
                dynamodb: None,
            })
            .await
            .unwrap();
            let law = std::sync::Arc::new(tokio::sync::RwLock::new(None));
            let store = hub_lib::store::open_hub_store(&hub_dir).unwrap();
            let ledger = std::sync::Arc::new(tokio::sync::Mutex::new(
                hub_lib::ledger::HubLedger::open(store).await.unwrap(),
            ));
            let rest = crate::rest::RestState::open_with_law_and_ledger(
                hub_dir.clone(),
                law.clone(),
                ledger.clone(),
            )
            .await
            .unwrap();
            crate::rest::PublicIdentity {
                hub_id: rest.hub_id,
                hub_name: rest.hub_name.clone(),
                founding_sovereign_lct_id: rest.sovereign_lct_id,
                sovereign_pubkey_hex: None,
            }
            .write(&rest.paths.root)
            .unwrap();
            // Encrypt the state store in place, then hold no key — which is the
            // ONLY way a locked shell is reached in `run_serve` (it boots the
            // shell precisely because `open_hub_store_async` failed).
            hub_lib::store::open_hub_store_with_key(&rest.paths.root, Some([7u8; 32])).unwrap();
            assert!(
                hub_lib::store::open_hub_store_async(&rest.paths.root).await.is_err(),
                "fixture must have a store that fails to open, or the locked shell is unreachable"
            );
            let locked = crate::rest::RestState::open_locked_shell(
                rest.paths.root.clone(),
                rest.law.clone(),
                rest.ledger.clone(),
            )
            .await
            .unwrap();
            assert!(locked.is_locked());
            let mcp = McpState::open_with_law_and_ledger(
                locked.paths.root.clone(),
                locked.law.clone(),
                locked.ledger.clone(),
                locked.signer.clone(),
                locked.sovereign_lct_id,
                locked.store_key.clone(),
                locked.hub_id,
                locked.hub_name.clone(),
            )
            .await
            .unwrap();
            let id = locked.hub_id;
            let app = public_plane_router(mcp, locked.clone(), locked.clone()).layer(
                axum::middleware::from_fn_with_state(locked.clone(), crate::rest::lock_gate),
            );
            (tmp, app, id)
        }

        async fn status(app: &Router, path: &str) -> StatusCode {
            app.clone()
                .oneshot(Request::builder().method("GET").uri(path).body(Body::empty()).unwrap())
                .await
                .unwrap()
                .status()
        }

        /// The defect. `/admin/law` is on the public plane, so this is an
        /// anonymous caller off the network hitting a locked hub. It answered
        /// `500` with `format!("{:#}", e)` from the store layer — which names
        /// the absolute path of `hub.db` — because the `ends_with("/law")`
        /// allowlist admitted it and its handler then called `open_store()` on
        /// a store that cannot open. The gate exists so that no handler runs
        /// against unpopulated state in a locked shell.
        #[tokio::test]
        async fn the_operator_law_page_is_refused_by_the_lock_gate_not_by_its_handler() {
            let (_tmp, app, _id) = locked_public_app().await;
            assert_eq!(
                status(&app, "/admin/law").await,
                StatusCode::SERVICE_UNAVAILABLE,
                "a locked hub let /admin/law reach its handler; a 500 here is the store \
                 error text (including hub.db's on-disk path) disclosed to an \
                 unauthenticated network caller"
            );
        }

        /// The sibling pages this one should always have matched. They were
        /// already correct — carried so that "law is refused" cannot be
        /// satisfied by a gate that has stopped running at all.
        #[tokio::test]
        async fn the_other_operator_pages_stay_refused_while_locked() {
            let (_tmp, app, _id) = locked_public_app().await;
            for p in ["/admin/roles", "/admin/council", "/tools", "/tools/query_hub"] {
                assert_eq!(
                    status(&app, p).await,
                    StatusCode::SERVICE_UNAVAILABLE,
                    "{p} must be refused while locked"
                );
            }
        }

        /// And the tier-0 surface must keep working, or the fix is just a hub
        /// that refuses everything — including the discovery doc an operator
        /// reads to find the hub id that ignition needs.
        #[tokio::test]
        async fn the_tier0_surface_is_still_served_while_locked() {
            let (_tmp, app, id) = locked_public_app().await;
            for p in [
                "/".to_string(),
                "/.well-known/web4-hub.json".to_string(),
                format!("/v1/hubs/{id}/law"),
            ] {
                assert_eq!(status(&app, &p).await, StatusCode::OK, "{p} is tier-0");
            }
            // `unlock` is POST-only: 405 proves the gate passed it through to
            // the router (a refusal would be 503), without needing a body.
            assert_eq!(
                status(&app, &format!("/v1/hubs/{id}/unlock")).await,
                StatusCode::METHOD_NOT_ALLOWED,
                "the unlock path must reach the router while locked, or the hub \
                 cannot be ignited"
            );
        }
    }
}
