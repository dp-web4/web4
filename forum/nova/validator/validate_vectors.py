#!/usr/bin/env python3
"""
validate_vectors.py
Validator for Web4 interop vectors (JOSE/JSON and COSE/CBOR).

What it checks:
- JOSE: recomputes JCS-canonical protected header & payload, rebuilds signing_input,
        and compares SHA-256 to the vector's reference.
- COSE: recomputes Sig_structure bytes from protected bstr + payload CBOR and
        compares SHA-256 to the vector's reference.

Signature verification is optional and not implemented here (use your crypto stack).
This script focuses on canonicalization & byte-for-byte encoding equivalence.

Usage examples:
  # Validate all supplied vectors in a directory (our unsigned vectors)
  python validate_vectors.py --vectors-dir ./test-vectors

  # Check a JOSE compact token's canonicalization against a vector
  python validate_vectors.py --check-jose-token eyJhbGciOiJ... --against test-vectors/handshakeauth_jose.json

  # Check a COSE Sign1's protected b64 and payload CBOR hex against a vector
  python validate_vectors.py --check-cose --protected-b64 <b64> --payload-hex <hex> --against test-vectors/handshakeauth_cose.json
"""
import json, base64, hashlib, sys, os, binascii

def b64url(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode()

def b64url_decode(s: str) -> bytes:
    pad = '=' * ((4 - len(s) % 4) % 4)
    return base64.urlsafe_b64decode(s + pad)

def jcs(obj: dict) -> bytes:
    return json.dumps(obj, separators=(",", ":"), sort_keys=True).encode()

def sha256_hex(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def is_jose_vector(path: str) -> bool:
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return "signing_input" in data and "protected_header" in data and "payload" in data
    except Exception:
        return False

def is_cose_vector(path: str) -> bool:
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return "Sig_structure_hex" in data and "protected_bstr_b64" in data and "payload_cbor_hex" in data
    except Exception:
        return False

def validate_jose_vector(path: str) -> bool:
    with open(path, "r", encoding="utf-8") as f:
        v = json.load(f)
    hdr = v["protected_header"]
    pl = v["payload"]
    recomposed = b64url(jcs(hdr)) + "." + b64url(jcs(pl))
    ok = (recomposed == v["signing_input"])
    ok_hash = (sha256_hex(recomposed.encode()) == v["signing_input_sha256"])
    print(f"[JOSE] {path}: signing_input match={ok}, sha256 match={ok_hash}")
    return ok and ok_hash

def validate_cose_vector(path: str) -> bool:
    with open(path, "r", encoding="utf-8") as f:
        v = json.load(f)
    protected = b64url_decode(v["protected_bstr_b64"])
    payload = binascii.unhexlify(v["payload_cbor_hex"])
    # Sig_structure = ["Signature1", protected, external_aad="", payload]
    def cbor_mt_ai(mt, ai): return (mt<<5)|ai
    def hdr_len(mt, l):
        if l < 24: return bytes([cbor_mt_ai(mt, l)])
        elif l < 256: return bytes([cbor_mt_ai(mt,24), l])
        elif l < 65536: return bytes([cbor_mt_ai(mt,25)]) + l.to_bytes(2,'big')
        elif l < 4294967296: return bytes([cbor_mt_ai(mt,26)]) + l.to_bytes(4,'big')
        else: return bytes([cbor_mt_ai(mt,27)]) + l.to_bytes(8,'big')
    def enc_text(s): b=s.encode(); return hdr_len(3,len(b))+b
    def enc_bytes(b): return hdr_len(2,len(b))+b
    def enc_array(items):
        out = b"".join(items)
        return hdr_len(4, len(items)) + out
    sig_structure = enc_array([enc_text("Signature1"), enc_bytes(protected), enc_bytes(b""), enc_bytes(payload)])
    recomputed_hex = binascii.hexlify(sig_structure).decode()
    ok = (recomputed_hex == v["Sig_structure_hex"])
    ok_hash = (sha256_hex(sig_structure) == v["Sig_structure_sha256"])
    print(f"[COSE] {path}: Sig_structure match={ok}, sha256 match={ok_hash}")
    return ok and ok_hash

def check_jose_token(token: str, vector_path: str) -> bool:
    parts = token.split(".")
    if len(parts) != 3:
        print("Token must have 3 parts (header.payload.signature)")
        return False
    header_b64, payload_b64, sig_b64 = parts
    with open(vector_path, "r", encoding="utf-8") as f:
        v = json.load(f)
    expected = v["signing_input"]
    signing_input = header_b64 + "." + payload_b64
    ok = (signing_input == expected)
    print(f"[JOSE check] signing_input match={ok}")
    if not ok:
        # Decode and show diffs
        try:
            hdr = json.loads(b64url_decode(header_b64))
            pl = json.loads(b64url_decode(payload_b64))
            print("Decoded header:", hdr)
            print("Decoded payload:", pl)
        except Exception as e:
            print("Decoding error:", e)
    return ok

def check_cose_parts(protected_b64: str, payload_hex: str, vector_path: str) -> bool:
    with open(vector_path, "r", encoding="utf-8") as f:
        v = json.load(f)
    protected = b64url_decode(protected_b64)
    payload = binascii.unhexlify(payload_hex)
    # Build Sig_structure
    def cbor_mt_ai(mt, ai): return (mt<<5)|ai
    def hdr_len(mt, l):
        if l < 24: return bytes([cbor_mt_ai(mt, l)])
        elif l < 256: return bytes([cbor_mt_ai(mt,24), l])
        elif l < 65536: return bytes([cbor_mt_ai(mt,25)]) + l.to_bytes(2,'big')
        elif l < 4294967296: return bytes([cbor_mt_ai(mt,26)]) + l.to_bytes(4,'big')
        else: return bytes([cbor_mt_ai(mt,27)]) + l.to_bytes(8,'big')
    def enc_text(s): b=s.encode(); return hdr_len(3,len(b))+b
    def enc_bytes(b): return hdr_len(2,len(b))+b
    def enc_array(items):
        out = b"".join(items)
        return hdr_len(4, len(items)) + out
    sig_structure = enc_array([enc_text("Signature1"), enc_bytes(protected), enc_bytes(b""), enc_bytes(payload)])
    ok = (binascii.hexlify(sig_structure).decode() == v["Sig_structure_hex"])
    print(f"[COSE check] Sig_structure match={ok}")
    return ok

def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--vectors-dir", help="Directory containing JSON vectors (will scan recursively)")
    ap.add_argument("--check-jose-token", help="JOSE compact token (header.payload.signature) to check")
    ap.add_argument("--check-cose", action="store_true", help="Check COSE parts against a vector")
    ap.add_argument("--protected-b64", help="COSE protected header b64 (from your Sign1)")
    ap.add_argument("--payload-hex", help="COSE payload CBOR hex (from your Sign1)")
    ap.add_argument("--against", help="Vector JSON path to compare against")
    args = ap.parse_args()

    overall_ok = True

    if args.vectors_dir:
        for root, _, files in os.walk(args.vectors_dir):
            for name in files:
                if not name.endswith(".json"):
                    continue
                p = os.path.join(root, name)
                try:
                    if is_jose_vector(p):
                        ok = validate_jose_vector(p)
                    elif is_cose_vector(p):
                        ok = validate_cose_vector(p)
                    else:
                        continue
                    overall_ok = overall_ok and ok
                except Exception as e:
                    print(f"Error validating {p}: {e}")
                    overall_ok = False

    if args.check_jose_token and args.against:
        ok = check_jose_token(args.check_jose_token, args.against)
        overall_ok = overall_ok and ok

    if args.check_cose and args.protected_b64 and args.payload_hex and args.against:
        ok = check_cose_parts(args.protected_b64, args.payload_hex, args.against)
        overall_ok = overall_ok and ok

    sys.exit(0 if overall_ok else 1)

if __name__ == "__main__":
    main()
