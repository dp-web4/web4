//! Reference sealed-channel client — the member side of `/v1/hubs/{id}/channel`.
//!
//! The minimal client every fleet machine can run once its channel key is
//! pinned (`hub set-member-key`). Seals `{tool, args}` to the hub's LCT pubkey,
//! POSTs, opens the sealed response. Nothing in the clear.
//!
//! Output discipline (so it's script-parseable): the sealed-response JSON is the
//! ONLY thing on **stdout**; all diagnostics go to **stderr**. So `... | jq` just
//! works — but only if cargo's build chatter stays off stdout. Use `-q` (or run
//! the prebuilt binary), e.g.:
//!
//!   cargo run -q --release --example channel_client -- \
//!     <BASE_URL> <MY_LCT> <KEYPAIR_FILE> <TOOL> [ARGS_JSON]   | jq
//!
//!   # or, no cargo noise at all:
//!   ./target/release/examples/channel_client <BASE_URL> <MY_LCT> <KEY> <TOOL> [ARGS]
//!
//! e.g.
//!   cargo run -q --release --example channel_client -- \
//!     http://100.65.206.122:8770 83810b44-…-ae5114f747cf ~/.web4/cbp/keypair.bin \
//!     find_members '{"query":"who knows about evals?","top_k":5}'
//!
//! KEYPAIR_FILE = the 32-byte Ed25519 secret seed (e.g. ~/.web4/<name>/keypair.bin
//! from the fleet-identity tooling). The hub must have the matching public half
//! pinned to MY_LCT.

use uuid::Uuid;
use web4_core::crypto::{KeyPair, PublicKey};
use web4_core::pair_channel::{self, Sealed};

fn main() -> anyhow::Result<()> {
    let args: Vec<String> = std::env::args().collect();
    if args.len() < 5 {
        eprintln!("usage: channel_client <BASE_URL> <MY_LCT> <KEYPAIR_FILE> <TOOL> [ARGS_JSON]");
        std::process::exit(2);
    }
    let base = args[1].trim_end_matches('/');
    let my_lct: Uuid = args[2].parse()?;
    let key_raw = std::fs::read(&args[3])?;
    let seed: [u8; 32] = key_raw
        .as_slice()
        .try_into()
        .map_err(|_| anyhow::anyhow!("keypair file must be exactly 32 bytes (got {})", key_raw.len()))?;
    let me = KeyPair::from_secret_bytes(&seed);
    let tool = &args[4];
    let tool_args: serde_json::Value = match args.get(5) {
        Some(s) => serde_json::from_str(s)?,
        None => serde_json::json!({}),
    };

    // 1. Discover the hub: LCT id + channel pubkey.
    let well_known: serde_json::Value =
        ureq_get(&format!("{base}/.well-known/web4-hub.json"))?;
    let hub_id: Uuid = well_known["hub_lct_id"]
        .as_str()
        .ok_or_else(|| anyhow::anyhow!("discovery missing hub_lct_id"))?
        .parse()?;
    let hub_pub_hex = well_known["hub_pubkey_hex"]
        .as_str()
        .ok_or_else(|| anyhow::anyhow!("hub exposes no channel pubkey"))?;
    let pk_raw = hex::decode(hub_pub_hex)?;
    let pk_arr: [u8; 32] = pk_raw.as_slice().try_into().map_err(|_| anyhow::anyhow!("bad hub pubkey"))?;
    let hub_pub = PublicKey::from_bytes(&pk_arr)?;
    eprintln!("hub {hub_id} @ {base} (pubkey {}…)", &hub_pub_hex[..16]);

    // 2. Seal {tool, args} with a fresh pair_id.
    let pair_id = Uuid::new_v4();
    let inner = serde_json::json!({ "tool": tool, "args": tool_args });
    let sealed = pair_channel::seal(&me, &hub_pub, pair_id, &serde_json::to_vec(&inner)?)?;

    // 3. POST the channel request.
    let body = serde_json::json!({
        "caller_lct_id": my_lct,
        "pair_id": pair_id,
        "sealed": sealed.to_base64(),
    });
    let resp: serde_json::Value = ureq_post(&format!("{base}/v1/hubs/{hub_id}/channel"), &body)?;

    // 4. Open the sealed response (AEAD failure here = tampered or wrong key).
    let sealed_resp = Sealed::from_base64(
        resp["sealed"].as_str().ok_or_else(|| anyhow::anyhow!("response missing 'sealed'"))?,
    )?;
    let plain = pair_channel::open(&me, &hub_pub, pair_id, &sealed_resp)?;
    let out: serde_json::Value = serde_json::from_slice(&plain)?;
    println!("{}", serde_json::to_string_pretty(&out)?);
    Ok(())
}

// -- tiny std-only HTTP (no extra deps): blocking reqwest is overkill here --
fn ureq_get(url: &str) -> anyhow::Result<serde_json::Value> {
    http(url, None)
}
fn ureq_post(url: &str, body: &serde_json::Value) -> anyhow::Result<serde_json::Value> {
    http(url, Some(serde_json::to_vec(body)?))
}
/// Minimal HTTP/1.1 over TcpStream — enough for plain-http tailnet use.
fn http(url: &str, post_body: Option<Vec<u8>>) -> anyhow::Result<serde_json::Value> {
    use std::io::{Read, Write};
    let rest = url
        .strip_prefix("http://")
        .ok_or_else(|| anyhow::anyhow!("only http:// supported (tailnet); got {url}"))?;
    let (host, path) = rest.split_once('/').map(|(h, p)| (h, format!("/{p}"))).unwrap_or((rest, "/".into()));
    let addr = if host.contains(':') { host.to_string() } else { format!("{host}:80") };
    let mut stream = std::net::TcpStream::connect(&addr)?;
    let (method, body) = match &post_body {
        Some(b) => ("POST", b.as_slice()),
        None => ("GET", &[][..]),
    };
    write!(
        stream,
        "{method} {path} HTTP/1.1\r\nHost: {host}\r\nContent-Type: application/json\r\nContent-Length: {}\r\nConnection: close\r\n\r\n",
        body.len()
    )?;
    stream.write_all(body)?;
    let mut buf = Vec::new();
    stream.read_to_end(&mut buf)?;
    let text = String::from_utf8_lossy(&buf);
    let (head, body) = text
        .split_once("\r\n\r\n")
        .ok_or_else(|| anyhow::anyhow!("malformed HTTP response"))?;
    let status = head.lines().next().unwrap_or_default();
    if !status.contains("200") {
        anyhow::bail!("{status}: {body}");
    }
    // Handle chunked transfer-encoding crudely: strip chunk-size lines.
    let json_body = if head.to_lowercase().contains("transfer-encoding: chunked") {
        body.lines().filter(|l| !l.chars().all(|c| c.is_ascii_hexdigit()) || l.contains('{') || l.contains('}')).collect::<String>()
    } else {
        body.to_string()
    };
    Ok(serde_json::from_str(json_body.trim())?)
}
