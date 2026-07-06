//! Self-service hub join client — submits a `member_join_request` to
//! `POST /v1/hubs/{id}/members/join`, reusing the codebase's exact envelope
//! signing (hub_lib::envelope::build_envelope) so canonical bytes match the
//! server's verify path. No hand-rolled crypto.
//!
//!   ./target/release/examples/join_client <BASE_URL> <MY_LCT> <KEYPAIR_FILE> <PUBKEY_HEX> <NAME> [MESSAGE]
//!
//! KEYPAIR_FILE = the 32-byte Ed25519 seed whose public half is PUBKEY_HEX.
//! The hub pins PUBKEY_HEX for MY_LCT on admission (Allow) or queues it (Escalate).

use uuid::Uuid;
use web4_core::crypto::KeyPair;
use hub_lib::envelope::{build_envelope, Challenge};

fn main() -> anyhow::Result<()> {
    let args: Vec<String> = std::env::args().collect();
    if args.len() < 6 {
        eprintln!("usage: join_client <BASE_URL> <MY_LCT> <KEYPAIR_FILE> <PUBKEY_HEX> <NAME> [MESSAGE]");
        std::process::exit(2);
    }
    let base = args[1].trim_end_matches('/');
    let my_lct: Uuid = args[2].parse()?;
    let seed_raw = std::fs::read(&args[3])?;
    let seed: [u8; 32] = seed_raw.as_slice().try_into()
        .map_err(|_| anyhow::anyhow!("keypair file must be 32 bytes (got {})", seed_raw.len()))?;
    let me = KeyPair::from_secret_bytes(&seed);
    let pubkey_hex = &args[4];
    let name = &args[5];
    let message = args.get(6).cloned().unwrap_or_else(|| "nomad joining the hub-mesh".into());

    // 1. Discover the hub id.
    let well_known = http(&format!("{base}/.well-known/web4-hub.json"), None)?;
    let hub_id: Uuid = well_known["hub_lct_id"].as_str()
        .ok_or_else(|| anyhow::anyhow!("discovery missing hub_lct_id"))?.parse()?;
    eprintln!("hub {hub_id} @ {base}");

    // 2. Get a challenge nonce for MY_LCT.
    let ch_body = serde_json::json!({ "for_lct_id": my_lct });
    let challenge: Challenge = serde_json::from_value(
        http(&format!("{base}/v1/auth/challenge"), Some(serde_json::to_vec(&ch_body)?))?
    )?;
    eprintln!("challenge issued (expires {})", challenge.expires_at);

    // 3. Build + sign the join payload.
    let payload = serde_json::json!({
        "action": "member_join_request",
        "member_lct_id": my_lct,
        "member_pubkey_hex": pubkey_hex,
        "name": name,
        "message": message,
    });
    let envelope = build_envelope(my_lct, &me, &challenge, payload)?;

    // 4. Submit the join request.
    let resp = http(
        &format!("{base}/v1/hubs/{hub_id}/members/join"),
        Some(serde_json::to_vec(&envelope)?),
    )?;
    println!("{}", serde_json::to_string_pretty(&resp)?);
    Ok(())
}

/// Minimal HTTP/1.1 over TcpStream (plain http on the trusted tailnet).
fn http(url: &str, post_body: Option<Vec<u8>>) -> anyhow::Result<serde_json::Value> {
    use std::io::{Read, Write};
    let rest = url.strip_prefix("http://")
        .ok_or_else(|| anyhow::anyhow!("only http:// supported; got {url}"))?;
    let (host, path) = rest.split_once('/').map(|(h, p)| (h, format!("/{p}"))).unwrap_or((rest, "/".into()));
    let addr = if host.contains(':') { host.to_string() } else { format!("{host}:80") };
    let mut stream = std::net::TcpStream::connect(&addr)?;
    let (method, body) = match &post_body {
        Some(b) => ("POST", b.as_slice()),
        None => ("GET", &[][..]),
    };
    write!(stream,
        "{method} {path} HTTP/1.1\r\nHost: {host}\r\nContent-Type: application/json\r\nContent-Length: {}\r\nConnection: close\r\n\r\n",
        body.len())?;
    stream.write_all(body)?;
    let mut buf = Vec::new();
    stream.read_to_end(&mut buf)?;
    let text = String::from_utf8_lossy(&buf);
    let (head, body) = text.split_once("\r\n\r\n").ok_or_else(|| anyhow::anyhow!("malformed HTTP response"))?;
    let status = head.lines().next().unwrap_or_default();
    if !(status.contains("200") || status.contains("202")) {
        anyhow::bail!("{status}: {body}");
    }
    let json_body = if head.to_lowercase().contains("transfer-encoding: chunked") {
        body.lines().filter(|l| !l.chars().all(|c| c.is_ascii_hexdigit()) || l.contains('{') || l.contains('}')).collect::<String>()
    } else { body.to_string() };
    Ok(serde_json::from_str(json_body.trim())?)
}
