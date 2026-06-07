// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Metalinxx Inc.

//! AIC Hub daemon — single-binary entrypoint.
//!
//! Sprint 1 surface: `hub init` + `hub gen-lct` (chapter bootstrap + Sovereign
//! LCT generation). Subsequent sprints add: `hub serve` (sprint 3, MCP server),
//! `hub status / add-member / assign-role / record-event / query` (sprint 4),
//! Docker entrypoint (sprint 5), error-message + docs polish (sprint 6).

use anyhow::Result;
use clap::{Parser, Subcommand};
use std::path::PathBuf;

use hub_lib::identity::IdentityFile;
use hub_lib::init::{init_chapter, verify_chapter, InitArgs, InitResult};
use web4_core::lct::EntityType;

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

fn main() -> Result<()> {
    let filter = tracing_subscriber::EnvFilter::try_from_default_env()
        .unwrap_or_else(|_| tracing_subscriber::EnvFilter::new("info"));
    tracing_subscriber::fmt().with_env_filter(filter).init();

    let cli = Cli::parse();

    match cli.command {
        None => {
            // No subcommand — print short usage hint and exit 0.
            println!("hub {} — AIC Hub (Sprint 1)", hub_lib::VERSION);
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
    }
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
