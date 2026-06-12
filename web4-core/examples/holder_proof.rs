// Throwaway helper: mint an OID4VCI holder key-possession proof JWT.
// Usage: holder_proof <issuer_aud> <c_nonce> <unix_now>
use web4_core::crypto::KeyPair;
use web4_core::oid4vc::build_holder_proof;

fn main() {
    let a: Vec<String> = std::env::args().collect();
    let issuer = &a[1];
    let nonce = &a[2];
    let now: i64 = a[3].parse().unwrap();
    let holder = KeyPair::generate();
    println!("{}", build_holder_proof(&holder, issuer, nonce, now));
}
