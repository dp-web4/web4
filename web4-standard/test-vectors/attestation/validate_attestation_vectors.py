#!/usr/bin/env python3
"""
Cross-language test vector validator for AttestationEnvelope.

Loads attestation-vectors.json and validates each vector against the
Python implementation. Other language implementations should produce
identical results for the same inputs.

Usage:
    python validate_attestation_vectors.py
"""

import json
import sys
import time
from pathlib import Path
from hashlib import sha256

# Add web4-core to path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'web4-core' / 'python'))

from web4.trust.attestation.envelope import (
    AttestationEnvelope, AnchorInfo, Proof, PlatformState,
    VerificationResult, TRUST_CEILINGS, FRESHNESS_MAX_AGE,
)
from web4.trust.attestation.verify import verify_envelope
from web4.trust.attestation.anchors.software import verify_software
from web4.trust.attestation.anchors.tpm2 import verify_tpm2
from web4.trust.attestation.anchors.fido2 import verify_fido2
from web4.trust.attestation.anchors.secure_enclave import verify_secure_enclave


def load_vectors():
    vectors_path = Path(__file__).parent / 'attestation-vectors.json'
    with open(vectors_path) as f:
        return json.load(f)


def build_envelope(data: dict) -> AttestationEnvelope:
    """Build an AttestationEnvelope from vector input dict."""
    kwargs = {}
    for key in ['entity_id', 'public_key', 'public_key_fingerprint',
                'timestamp', 'purpose', 'issuer', 'envelope_version',
                'challenge_ttl', 'trust_ceiling']:
        if key in data:
            kwargs[key] = data[key]

    if 'anchor' in data:
        a = data['anchor']
        kwargs['anchor'] = AnchorInfo(
            type=a.get('type', 'software'),
            manufacturer=a.get('manufacturer'),
            model=a.get('model'),
            firmware_version=a.get('firmware_version'),
        )

    if 'proof' in data:
        p = data['proof']
        kwargs['proof'] = Proof(
            format=p.get('format', 'ecdsa_software'),
            signature=p.get('signature', ''),
            challenge=p.get('challenge', ''),
            attestation_object=p.get('attestation_object'),
            pcr_digest=p.get('pcr_digest'),
            pcr_selection=p.get('pcr_selection'),
            authenticator_data=p.get('authenticator_data'),
            client_data_hash=p.get('client_data_hash'),
        )

    if 'platform_state' in data:
        ps = data['platform_state']
        pcr_vals = ps.get('pcr_values')
        if pcr_vals:
            pcr_vals = {int(k): v for k, v in pcr_vals.items()}
        kwargs['platform_state'] = PlatformState(
            available=ps.get('available', False),
            boot_verified=ps.get('boot_verified'),
            pcr_values=pcr_vals,
            os_version=ps.get('os_version'),
            kernel_version=ps.get('kernel_version'),
        )

    return AttestationEnvelope(**kwargs)


def validate_construction(vector: dict) -> list:
    """Validate envelope construction vectors."""
    failures = []
    env = build_envelope(vector['input'])
    expected = vector['expected']

    if 'trust_ceiling' in expected:
        if abs(env.trust_ceiling - expected['trust_ceiling']) > 1e-9:
            failures.append(
                f"trust_ceiling: got {env.trust_ceiling}, expected {expected['trust_ceiling']}")

    if 'anchor_type' in expected:
        if env.anchor.type != expected['anchor_type']:
            failures.append(
                f"anchor.type: got {env.anchor.type}, expected {expected['anchor_type']}")

    if 'public_key_fingerprint_length' in expected:
        if len(env.public_key_fingerprint) != expected['public_key_fingerprint_length']:
            failures.append(
                f"fingerprint length: got {len(env.public_key_fingerprint)}, "
                f"expected {expected['public_key_fingerprint_length']}")

    if 'public_key_fingerprint_not_empty' in expected:
        if expected['public_key_fingerprint_not_empty'] and not env.public_key_fingerprint:
            failures.append("fingerprint should not be empty")

    if 'public_key_fingerprint' in expected:
        if env.public_key_fingerprint != expected['public_key_fingerprint']:
            failures.append(
                f"fingerprint: got {env.public_key_fingerprint}, "
                f"expected {expected['public_key_fingerprint']}")

    if 'envelope_version' in expected:
        if env.envelope_version != expected['envelope_version']:
            failures.append(
                f"envelope_version: got {env.envelope_version}, "
                f"expected {expected['envelope_version']}")

    if 'challenge_ttl' in expected:
        if abs(env.challenge_ttl - expected['challenge_ttl']) > 1e-9:
            failures.append(
                f"challenge_ttl: got {env.challenge_ttl}, expected {expected['challenge_ttl']}")

    if 'fingerprint_length' in expected:
        if len(env.public_key_fingerprint) != expected['fingerprint_length']:
            failures.append(
                f"fingerprint length: got {len(env.public_key_fingerprint)}, "
                f"expected {expected['fingerprint_length']}")

    if 'fingerprint_is_hex' in expected and expected['fingerprint_is_hex']:
        try:
            int(env.public_key_fingerprint, 16)
        except ValueError:
            failures.append(f"fingerprint is not hex: {env.public_key_fingerprint}")

    return failures


def validate_trust_ceiling(vector: dict) -> list:
    """Validate trust ceiling vectors."""
    failures = []
    expected = vector['expected']

    if 'ceilings' in expected:
        for anchor_type, ceiling in expected['ceilings'].items():
            actual = TRUST_CEILINGS.get(anchor_type)
            if actual is None:
                failures.append(f"TRUST_CEILINGS missing key: {anchor_type}")
            elif abs(actual - ceiling) > 1e-9:
                failures.append(
                    f"TRUST_CEILINGS[{anchor_type}]: got {actual}, expected {ceiling}")

    if 'trust_ceiling' in expected and 'input' in vector:
        env = build_envelope(vector['input'])
        if abs(env.trust_ceiling - expected['trust_ceiling']) > 1e-9:
            failures.append(
                f"trust_ceiling: got {env.trust_ceiling}, expected {expected['trust_ceiling']}")

    # Validate the complete table
    if vector['id'] == 'ae-trust-ceiling-table':
        for key, val in expected.items():
            actual = TRUST_CEILINGS.get(key)
            if actual is None:
                failures.append(f"TRUST_CEILINGS missing: {key}")
            elif abs(actual - val) > 1e-9:
                failures.append(f"TRUST_CEILINGS[{key}]: got {actual}, expected {val}")

    return failures


def validate_freshness(vector: dict) -> list:
    """Validate freshness model vectors."""
    failures = []

    # Validate max age table
    if vector['id'] == 'ae-freshness-max-age-table':
        for purpose, expected_max_age in vector['expected'].items():
            actual = FRESHNESS_MAX_AGE.get(purpose)
            if expected_max_age is None:
                if actual is not None:
                    failures.append(f"FRESHNESS_MAX_AGE[{purpose}]: got {actual}, expected None")
            elif actual is None:
                failures.append(f"FRESHNESS_MAX_AGE[{purpose}]: got None, expected {expected_max_age}")
            elif abs(actual - expected_max_age) > 1e-9:
                failures.append(
                    f"FRESHNESS_MAX_AGE[{purpose}]: got {actual}, expected {expected_max_age}")
        return failures

    # Validate effective_trust computation
    if vector['id'] == 'ae-effective-trust':
        for case in vector['cases']:
            ceiling = case['trust_ceiling']
            factor = case['freshness_factor']
            expected = case['expected_effective_trust']
            actual = ceiling * factor
            if abs(actual - expected) > 1e-9:
                failures.append(
                    f"effective_trust({ceiling} * {factor}): got {actual}, expected {expected}")
        return failures

    # Validate freshness cases with time manipulation
    if 'cases' not in vector:
        return failures

    purpose = vector.get('input', {}).get('purpose')
    for case in vector['cases']:
        age = case['age_seconds']
        # Create envelope with fixed timestamp in the past
        now = time.time()
        env = AttestationEnvelope(
            entity_id='lct://test:freshness',
            public_key='testkey',
            purpose=purpose,
            timestamp=now - age,
        )

        if 'expected_fresh' in case:
            if env.is_fresh != case['expected_fresh']:
                failures.append(
                    f"purpose={purpose}, age={age}s: is_fresh got {env.is_fresh}, "
                    f"expected {case['expected_fresh']}")

        if 'expected_freshness_factor' in case:
            expected_factor = case['expected_freshness_factor']
            actual_factor = env.freshness_factor
            if abs(actual_factor - expected_factor) > 0.01:  # Small tolerance for timing
                failures.append(
                    f"purpose={purpose}, age={age}s: freshness_factor got {actual_factor:.4f}, "
                    f"expected {expected_factor}")

    return failures


def validate_serialization(vector: dict) -> list:
    """Validate serialization round-trip vectors."""
    failures = []
    env = build_envelope(vector['input'])

    # Dict round-trip
    d = env.to_dict()
    restored = AttestationEnvelope.from_dict(d)

    for field_path in vector['expected'].get('round_trip_preserves', []):
        parts = field_path.split('.')
        orig_val = env
        rest_val = restored
        for part in parts:
            if hasattr(orig_val, part):
                orig_val = getattr(orig_val, part)
                rest_val = getattr(rest_val, part)
            else:
                failures.append(f"Field not found: {field_path}")
                orig_val = rest_val = None
                break
        if orig_val != rest_val:
            failures.append(
                f"Round-trip mismatch for {field_path}: {orig_val} != {rest_val}")

    # JSON round-trip
    if vector['expected'].get('json_is_valid'):
        json_str = env.to_json()
        try:
            json.loads(json_str)
        except json.JSONDecodeError:
            failures.append("to_json() produced invalid JSON")

    if vector['expected'].get('from_json_matches_original'):
        json_str = env.to_json()
        json_restored = AttestationEnvelope.from_json(json_str)
        if json_restored.entity_id != env.entity_id:
            failures.append("JSON round-trip: entity_id mismatch")
        if abs(json_restored.trust_ceiling - env.trust_ceiling) > 1e-9:
            failures.append("JSON round-trip: trust_ceiling mismatch")

    return failures


def validate_verification(vector: dict) -> list:
    """Validate verification dispatch vectors."""
    failures = []

    # Wrong anchor type cases
    if 'cases' in vector:
        verifier_map = {
            'software': verify_software,
            'tpm2': verify_tpm2,
            'fido2': verify_fido2,
            'secure_enclave': verify_secure_enclave,
        }
        for case in vector['cases']:
            verifier_fn = verifier_map.get(case['verifier'])
            if not verifier_fn:
                failures.append(f"Unknown verifier: {case['verifier']}")
                continue
            env = AttestationEnvelope(
                entity_id='lct://test:wrong-type',
                public_key='testkey',
                anchor=AnchorInfo(type=case['anchor_type']),
                proof=Proof(format='test', signature='sig', challenge='ch'),
            )
            if case['verifier'] == 'tpm2':
                result = verifier_fn(env, expected_pcrs=None)
            else:
                result = verifier_fn(env)
            if result.valid != case['expected_valid']:
                failures.append(
                    f"verifier={case['verifier']}, anchor={case['anchor_type']}: "
                    f"valid got {result.valid}, expected {case['expected_valid']}")
        return failures

    # Standard verification vectors
    if 'input' not in vector:
        return failures

    inp = vector['input']
    env_data = inp.get('envelope', inp)
    env = build_envelope(env_data)

    expected_challenge = inp.get('expected_challenge', '')
    kwargs = {}
    if 'expected_pcrs' in inp:
        pcrs = {int(k): v for k, v in inp['expected_pcrs'].items()}
        kwargs['expected_pcrs'] = pcrs

    result = verify_envelope(env, expected_challenge=expected_challenge, **kwargs)
    expected = vector['expected']

    if 'valid' in expected:
        if result.valid != expected['valid']:
            failures.append(f"valid: got {result.valid}, expected {expected['valid']}")

    if 'effective_trust' in expected:
        if abs(result.effective_trust - expected['effective_trust']) > 1e-9:
            failures.append(
                f"effective_trust: got {result.effective_trust}, "
                f"expected {expected['effective_trust']}")

    if 'trust_ceiling' in expected:
        if abs(result.trust_ceiling - expected['trust_ceiling']) > 1e-9:
            failures.append(
                f"trust_ceiling: got {result.trust_ceiling}, "
                f"expected {expected['trust_ceiling']}")

    if 'fresh' in expected:
        if result.fresh != expected['fresh']:
            failures.append(f"fresh: got {result.fresh}, expected {expected['fresh']}")

    if 'anchor_verified' in expected:
        if result.anchor_verified != expected['anchor_verified']:
            failures.append(
                f"anchor_verified: got {result.anchor_verified}, "
                f"expected {expected['anchor_verified']}")

    if 'platform_state_ok' in expected:
        if result.platform_state_ok != expected['platform_state_ok']:
            failures.append(
                f"platform_state_ok: got {result.platform_state_ok}, "
                f"expected {expected['platform_state_ok']}")

    if 'reason_contains' in expected:
        if expected['reason_contains'] not in result.reason:
            failures.append(
                f"reason should contain '{expected['reason_contains']}', "
                f"got '{result.reason}'")

    return failures


CATEGORY_VALIDATORS = {
    'construction': validate_construction,
    'trust_ceiling': validate_trust_ceiling,
    'freshness': validate_freshness,
    'serialization': validate_serialization,
    'verification': validate_verification,
}


def main():
    data = load_vectors()
    vectors = data['vectors']

    passed = 0
    failed = 0
    errors = []

    for v in vectors:
        vid = v['id']
        category = v.get('category', 'unknown')
        validator = CATEGORY_VALIDATORS.get(category)

        if not validator:
            print(f"  SKIP {vid} (unknown category: {category})")
            continue

        try:
            failures = validator(v)
        except Exception as e:
            failures = [f"Exception: {e}"]

        if failures:
            failed += 1
            for f in failures:
                errors.append(f"{vid}: {f}")
            print(f"  FAIL {vid}")
            for f in failures:
                print(f"       {f}")
        else:
            passed += 1
            print(f"  OK   {vid}")

    print(f"\n{'=' * 60}")
    print(f"Attestation vectors: {passed} passed, {failed} failed, {passed + failed} total")

    if errors:
        print(f"\nFailures:")
        for e in errors:
            print(f"  - {e}")
        return 1

    print("\nAll vectors validated successfully.")
    return 0


if __name__ == '__main__':
    sys.exit(main())
