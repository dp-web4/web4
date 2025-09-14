# Hello-Web4 (5-minute demo)

## What this shows

Two toy nodes (Alice/Bob) perform:
1. **Pairing** (exchange W4IDs)  
2. **Birth Certificate** (automatic citizen role assignment)
3. **LCT** issuance (Alice → Bob, signed context unit)  
4. **Verification** (Bob verifies Alice's signature, checks MRH horizon)  
5. **MRH update** (Bob records the witnessed context)

## Prerequisites

```bash
pip install pynacl
```

## Run

```bash
python3 hello_web4.py
```

## You should see

```
[INIT] Creating entities with birth certificates...
[BIRTH] Alice citizen role established    ✅
[BIRTH] Bob citizen role established      ✅
[PAIR] Alice↔Bob W4IDs exchanged         ✅
[SIGN] Alice issued LCT                  ✅
[VERIFY] Bob verified LCT sig            ✅
[MRH] Bob updated relationship            ✅
[TRUST] Role-contextual trust verified   ✅
```

## Output Files

- `sample_w4id_alice.json` - Alice's W4ID document
- `sample_w4id_bob.json` - Bob's W4ID document  
- `sample_lct.json` - The signed LCT from Alice to Bob
- `sample_birth_cert_alice.json` - Alice's birth certificate
- `sample_birth_cert_bob.json` - Bob's birth certificate

## Notes

- Crypto: Ed25519 for identity signatures (using PyNaCl)
- Transport/HPKE are stubbed (local exchange) to keep demo simple
- Demonstrates citizen role as birth certificate concept
- Shows role-contextual trust (no global scores)
- See `schemas/` in repo for formal definitions