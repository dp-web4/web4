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
use hub_lib::init::{init_hub, verify_hub, InitArgs, InitResult};
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
    /// more `key=value` pairs, e.g. `skills="..." interests="..."`. An empty
    /// value clears that field.
    SetProfile {
        hub_dir: PathBuf,
        member_lct_id: Uuid,
        /// `key=value` pairs (repeatable).
        #[arg(value_name = "KEY=VALUE", required = true)]
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
            hub_dir, storage,
        }) => {
            run_init(name, sovereign_lct, sovereign_hestia, sovereign_lct_id,
                     sovereign_pubkey, hub_dir, storage).await
        }
        Some(Command::GenLct { output, entity_type }) => {
            run_gen_lct(output, entity_type.into()).await
        }
        Some(Command::SealIdentity { path }) => run_seal_identity(path).await,
        Some(Command::Unlock { port }) => run_unlock(port).await,
        Some(Command::ExportPublicIdentity { hub_dir }) => run_export_public_identity(hub_dir).await,
        Some(Command::RotatePassphrase { hub_dir }) => run_rotate_passphrase(hub_dir).await,
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
    std::fs::write(&output, STARTER_LAW_YAML)
        .with_context(|| format!("writing starter law to {}", output.display()))?;

    println!("Starter hub-law written to {}.", output.display());
    println!();
    println!("Next steps:");
    println!("  1. Edit {} — adjust norms, admission, atp_issuance, etc.", output.display());
    println!("  2. Apply to a chapter:  hub set-law <chapter-dir> {}", output.display());
    println!("  3. If serve is running: curl -X POST http://<host>/v1/admin/reload-law");
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
    let mut map = std::collections::BTreeMap::new();
    for pair in &fields {
        let (k, v) = pair.split_once('=').ok_or_else(|| {
            anyhow::anyhow!("field {:?} must be key=value", pair)
        })?;
        map.insert(k.trim().to_string(), v.to_string());
    }
    let keys: Vec<String> = map.keys().cloned().collect();
    let mut session = HubSession::open(&hub_dir).await?;
    let entry = session.update_profile(member_lct_id, map).await?;
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

async fn run_serve(hub_dir: PathBuf, port_override: Option<u16>, bind: String, admin_port: u16) -> Result<()> {
    let config = HubConfig::load(hub_lib::hub::HubPaths::new(&hub_dir).config())?;
    let port = port_override.unwrap_or(config.daemon.mcp_port);
    let addr: SocketAddr = format!("{}:{}", bind, port).parse()?;

    // Total enclosure, unlock-first: try to open the encrypted state store with whatever
    // key is available (none — we keep no passphrase on disk or in env). If it opens
    // (plaintext / NULL-keyed / fresh hub), boot normally. If it fails closed (encrypted,
    // no key), boot a LOCKED SHELL that serves only the unlock path; `hub unlock` ignites it
    // at runtime. The passphrase is never read from the environment.
    let store_opens = hub_lib::store::open_hub_store(&hub_dir).is_ok();

    let (rest_state, mcp_state) = if store_opens {
        // ── normal boot (store readable without a held key) ──
        let initial_law = {
            let store = hub_lib::store::open_hub_store(&hub_dir)?;
            match store.read_law().await? {
                Some(yaml) => Some(hub_lib::law::Law::parse_and_validate(&yaml)?),
                None => None,
            }
        };
        let shared_law = std::sync::Arc::new(tokio::sync::RwLock::new(initial_law));
        let shared_ledger = {
            let store = hub_lib::store::open_hub_store(&hub_dir)?;
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
    }
    // Admin UI reuses RestState (read-only; shares ledger + law snapshot).
    let admin_state = rest_state.clone();
    let gate_state = rest_state.clone();
    // Operator plane (separate 127.0.0.1-only listener) shares the same RestState.
    let mut operator_state = rest_state.clone();
    operator_state.operator_plane = true; // this clone serves the write pages → show their nav links
    let operator_gate = rest_state.clone();
    let app = mcp_router(mcp_state)
        .merge(rest_router(rest_state))
        .merge(admin::router(admin_state))
        // Fail-closed lock-gate over the whole surface: while locked, only the
        // tier-0 allowlist (unlock / well-known / law / issuer metadata) is served.
        .layer(axum::middleware::from_fn_with_state(gate_state, crate::rest::lock_gate));

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
    if admin_port != 0 {
        let op_addr: SocketAddr = format!("127.0.0.1:{}", admin_port).parse()?;
        let operator_app = admin::router(operator_state.clone())
            .merge(admin::operator_router(operator_state.clone()))
            .merge(crate::rest::admin_api_router(operator_state))
            .layer(axum::middleware::from_fn_with_state(operator_gate, crate::rest::lock_gate));
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
) -> Result<()> {
    use std::str::FromStr;
    let hub_dir = hub_dir.unwrap_or_else(|| PathBuf::from(slugify(&name)));
    let backend = hub_lib::store::BackendKind::from_str(&storage)
        .context("parsing --storage")?;

    let result = match (sovereign_lct, sovereign_hestia) {
        (Some(path), None) => {
            // Local mode
            init_hub(InitArgs {
                hub_name: name,
                hub_dir,
                sovereign_lct_path: path,
                storage: Some(backend),
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

/// Seed the clear tier-0 `public-identity.json` from the encrypted store + identity.
async fn run_export_public_identity(hub_dir: PathBuf) -> Result<()> {
    use hub_lib::hub::{HubConfig, HubPaths, SovereignMode};
    let pass = require_passphrase("the hub vault (to read its public identity)")?;
    let key = hub_lib::store::derive_store_key(&hub_dir, &pass)?;
    let store = hub_lib::store::open_hub_store_with_key(&hub_dir, Some(key))
        .context("opening the encrypted hub store")?;
    let society = store
        .read_society()
        .await?
        .ok_or_else(|| anyhow::anyhow!("no society in the hub store"))?;
    let config = HubConfig::load(HubPaths::new(&hub_dir).config())?;
    let (founding, pubkey_hex) = match config.sovereign.mode()? {
        SovereignMode::Local { lct_path } => {
            let id = IdentityFile::load_encrypted(&lct_path, &pass)
                .context("opening the encrypted identity")?;
            let pk = id.keypair()?.verifying_key().to_hex();
            (id.lct.id, Some(pk))
        }
        SovereignMode::Hestia { lct_id, pubkey_hex, .. } => (lct_id, Some(pubkey_hex)),
    };
    let pid = crate::rest::PublicIdentity {
        hub_id: society.lct_id,
        hub_name: society.name.clone(),
        founding_sovereign_lct_id: founding,
        sovereign_pubkey_hex: pubkey_hex,
    };
    pid.write(&hub_dir)?;
    println!("Wrote {}/public-identity.json", hub_dir.display());
    println!("  hub:       {} ({})", society.name, society.lct_id);
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
    fn slugify_handles_common_cases() {
        assert_eq!(slugify("Lisbon Chapter"), "lisbon-chapter");
        assert_eq!(slugify("NYC Chapter #1"), "nyc-chapter-1");
        // Unicode letters survive via char::is_alphanumeric — fine for hub dirs.
        assert_eq!(slugify("São Paulo"), "são-paulo");
        assert_eq!(slugify("東京"), "東京");
        assert_eq!(slugify("   spaces   "), "spaces");
        assert_eq!(slugify(""), "");
    }
}
