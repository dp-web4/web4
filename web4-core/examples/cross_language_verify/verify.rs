//! Cross-language interop demo, Rust side.
//!
//! Reads a `LocalLedger` written by the Python script `mint.py` (see the
//! `cross_language_verify/` README) and verifies:
//!
//! 1. The hash chain is intact end-to-end (`LocalLedger::open` replays and
//!    verifies the chain on load — any tamper aborts).
//! 2. The LCT minted from Python is present in the ledger.
//! 3. An anchor proof for that LCT verifies under the Rust implementation.
//!
//! The point of the demo is not the LCT itself — it's that the on-disk
//! format is the contract. Any language with a Web4 spec implementation
//! can verify what any other language minted, with no shared runtime.
//!
//! Run from the `web4-core/` directory:
//!
//! ```sh
//! cargo run --example cross_language_verify -- \
//!     --ledger ./shared_ledger.jsonl \
//!     --lct-sidecar ./shared_lct.json
//! ```

use std::env;
use std::fs;
use std::path::PathBuf;
use std::process::ExitCode;

use serde::Deserialize;
use web4_core::{Ledger, LocalLedger};

#[derive(Deserialize)]
struct LctSidecar {
    lct_id: String,
    fingerprint: String,
}

fn parse_args() -> (PathBuf, PathBuf) {
    let mut ledger = PathBuf::from("./shared_ledger.jsonl");
    let mut sidecar = PathBuf::from("./shared_lct.json");
    let mut args = env::args().skip(1);
    while let Some(arg) = args.next() {
        match arg.as_str() {
            "--ledger" => {
                ledger = args
                    .next()
                    .expect("--ledger requires a path argument")
                    .into();
            }
            "--lct-sidecar" => {
                sidecar = args
                    .next()
                    .expect("--lct-sidecar requires a path argument")
                    .into();
            }
            "-h" | "--help" => {
                eprintln!(
                    "usage: cargo run --example cross_language_verify -- \
                     [--ledger PATH] [--lct-sidecar PATH]"
                );
                std::process::exit(0);
            }
            other => {
                eprintln!("unknown argument: {}", other);
                std::process::exit(2);
            }
        }
    }
    (ledger, sidecar)
}

fn main() -> ExitCode {
    let (ledger_path, sidecar_path) = parse_args();

    println!("[rust] Reading sidecar at {}", sidecar_path.display());
    let sidecar_text = match fs::read_to_string(&sidecar_path) {
        Ok(s) => s,
        Err(e) => {
            eprintln!("[rust] Could not read sidecar {}: {}", sidecar_path.display(), e);
            eprintln!("[rust] Did you run `python mint.py` first?");
            return ExitCode::from(2);
        }
    };
    let sidecar: LctSidecar = match serde_json::from_str(&sidecar_text) {
        Ok(s) => s,
        Err(e) => {
            eprintln!("[rust] Sidecar parse error: {}", e);
            return ExitCode::from(2);
        }
    };
    println!("[rust]   lct_id      = {}", sidecar.lct_id);
    println!("[rust]   fingerprint = {}", sidecar.fingerprint);

    println!(
        "[rust] Opening LocalLedger at {} (this replays + verifies the chain)",
        ledger_path.display()
    );
    let ledger = match LocalLedger::open(&ledger_path) {
        Ok(l) => l,
        Err(e) => {
            eprintln!("[rust] Ledger open failed: {}", e);
            eprintln!("[rust] If this is a chain-integrity failure, the ledger was tampered.");
            return ExitCode::from(3);
        }
    };
    println!("[rust] Chain intact. {} entries replayed.", ledger.len());

    let lct_uuid = match uuid::Uuid::parse_str(&sidecar.lct_id) {
        Ok(u) => u,
        Err(e) => {
            eprintln!("[rust] Sidecar lct_id is not a UUID: {}", e);
            return ExitCode::from(2);
        }
    };

    let lookup = match ledger.lookup(lct_uuid) {
        Ok(l) => l,
        Err(e) => {
            eprintln!("[rust] Ledger lookup failed: {}", e);
            return ExitCode::from(3);
        }
    };
    let lct = match lookup {
        Some(lct) => lct,
        None => {
            eprintln!("[rust] LCT {} not present in ledger.", sidecar.lct_id);
            return ExitCode::from(3);
        }
    };
    println!("[rust] LCT present in ledger.");

    if lct.fingerprint() != sidecar.fingerprint {
        eprintln!(
            "[rust] FINGERPRINT MISMATCH:\n  sidecar:  {}\n  on-chain: {}",
            sidecar.fingerprint,
            lct.fingerprint()
        );
        return ExitCode::from(3);
    }
    println!("[rust] Fingerprint matches sidecar.");

    let proof = match ledger.anchor(lct.id) {
        Ok(p) => p,
        Err(e) => {
            eprintln!("[rust] anchor() failed: {}", e);
            return ExitCode::from(3);
        }
    };
    let verified = match ledger.verify_proof(&proof) {
        Ok(v) => v,
        Err(e) => {
            eprintln!("[rust] verify_proof error: {}", e);
            return ExitCode::from(3);
        }
    };
    if !verified {
        eprintln!("[rust] Anchor proof DID NOT verify under the Rust implementation.");
        return ExitCode::from(3);
    }
    println!("[rust] Anchor proof verifies under the Rust implementation. ✓");
    println!();
    println!("[rust] Cross-language verification succeeded.");
    println!(
        "[rust] Python wrote a hash-chained ledger; Rust read the same file, replayed the chain, \
         looked up the LCT by id, matched its fingerprint, and verified the inclusion proof — \
         with zero shared runtime. The on-disk format is the contract."
    );
    ExitCode::SUCCESS
}
