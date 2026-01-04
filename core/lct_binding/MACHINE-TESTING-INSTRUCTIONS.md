# LCT Hardware Binding - Machine-Specific Testing Instructions

**Priority: HIGH** - This is foundational for system-wide trust building.

**Status**: Draft implementations created on CBP (WSL2). Each machine needs to test and verify its hardware provider.

---

## Overview

The `lct_binding` module provides hardware-bound identity for LCTs:

| Machine | Platform | Hardware | Provider | Level | Trust Ceiling |
|---------|----------|----------|----------|-------|---------------|
| CBP | WSL2 | None | SoftwareProvider | 4 | 0.85 |
| Legion | Native Linux | TPM 2.0 | TPM2Provider | 5 | 1.0 |
| Thor | ARM64 Linux | TrustZone | TrustZoneProvider | 5 | 1.0 |
| Sprout | ARM64 Linux | TrustZone | TrustZoneProvider | 5 | 1.0 |

---

## LEGION: TPM2 Provider Testing

**Prerequisites**:
```bash
# Check TPM availability
ls -la /dev/tpm*
dmesg | grep -i tpm

# Install tpm2-tools if needed
sudo apt install tpm2-tools

# Verify tpm2-tools work
tpm2_getcap properties-fixed

# Add user to tss group for TPM access
sudo usermod -aG tss $USER
# Then logout/login
```

**Test Commands**:
```bash
cd /home/dp/ai-workspace/web4

# Run platform detection
python3 -c "
import sys
sys.path.insert(0, 'core')
from lct_binding import detect_platform

platform = detect_platform()
print(f'Platform: {platform.name}')
print(f'Has TPM2: {platform.has_tpm2}')
print(f'Max Level: {platform.max_level}')
"

# Test TPM2 provider
python3 -c "
import sys
sys.path.insert(0, 'core')
from lct_binding import TPM2Provider
from lct_capability_levels import EntityType

provider = TPM2Provider()
print(f'TPM Tools Available: {provider._tpm_available}')
print(f'Trust Ceiling: {provider.trust_ceiling}')

if provider._tpm_available:
    # Create a test LCT
    lct = provider.create_lct(EntityType.AI, 'legion-test')
    print(f'LCT ID: {lct.lct_id}')
    print(f'Level: {lct.capability_level.name}')
    print(f'Hardware Anchor: {lct.binding.hardware_anchor}')
    print(f'Trust Ceiling: {lct.t3_tensor.trust_ceiling}')

    # Test signing
    key_id = lct.lct_id.split(':')[-1]
    sig = provider.sign_data(key_id, b'test data')
    print(f'Signature OK: {sig.success}')

    # Test attestation
    att = provider.get_attestation(key_id)
    print(f'Attestation OK: {att.success}')
    if att.pcr_values:
        print(f'PCR[0]: {att.pcr_values.get(0)}')
"
```

**Expected Outcomes**:
1. `has_tpm2: True`
2. `max_level: 5`
3. LCT created with `hardware_anchor` pointing to TPM handle (0x8101xxxx)
4. `trust_ceiling: 1.0`
5. Successful signature with ECDSA-P256-SHA256
6. Attestation with PCR values

**If Issues**:
- TPM permission denied: Add user to `tss` group
- tpm2_createprimary fails: Check TPM state, may need `tpm2_clear`
- Algorithm not supported: Some TPMs don't support all algorithms

**Report Results**:
After testing, update `HARDWARE-BINDING-IMPLEMENTATION-PLAN.md` with:
- Actual test results
- Any fixes needed to `tpm2_provider.py`
- TPM-specific quirks discovered

---

## THOR: TrustZone Provider Testing

**Prerequisites**:
```bash
# Check TEE availability
ls -la /dev/tee*

# Check if OP-TEE is running
ps aux | grep tee-supplicant

# Verify OP-TEE test tools (optional)
which xtest
```

**Test Commands**:
```bash
cd ~/ai-workspace/web4

# Run platform detection
python3 -c "
import sys
sys.path.insert(0, 'core')
from lct_binding import detect_platform

platform = detect_platform()
print(f'Platform: {platform.name}')
print(f'Architecture: {platform.arch}')
print(f'Has TrustZone: {platform.has_trustzone}')
print(f'Max Level: {platform.max_level}')
"

# Test TrustZone provider
python3 -c "
import sys
sys.path.insert(0, 'core')
from lct_binding import TrustZoneProvider
from lct_capability_levels import EntityType

provider = TrustZoneProvider()
print(f'TEE Available: {provider._tee_available}')
print(f'Trust Ceiling: {provider.trust_ceiling}')

# Create test LCT (may use simulation if no TA installed)
lct = provider.create_lct(EntityType.AI, 'thor-test')
print(f'LCT ID: {lct.lct_id}')
print(f'Level: {lct.capability_level.name}')
print(f'Hardware Type: {lct.binding.hardware_type}')
print(f'Trust Ceiling: {lct.t3_tensor.trust_ceiling}')
print(f'Ceiling Reason: {lct.t3_tensor.trust_ceiling_reason}')
"
```

**Expected Outcomes**:
1. `arch: aarch64`
2. `has_trustzone: True` (if /dev/tee* exists)
3. LCT created with TrustZone binding
4. If real TEE: `trust_ceiling: 1.0`, `hardware_type: trustzone`
5. If simulated: `trust_ceiling: 0.85`, `hardware_type: trustzone_simulated`

**For Full Hardware Binding (Future)**:
The current implementation falls back to simulation because a Web4 Trusted Application (TA) needs to be developed and deployed to OP-TEE. This requires:
1. Writing the TA in C for TEE execution
2. Deploying to /lib/optee_armtz/
3. Creating tee-supplicant helper for TA invocation

This is Phase 3 work - for now, verify that:
- Platform detection correctly identifies TrustZone capability
- Simulation mode works correctly
- Trust ceiling is appropriately reduced for simulation

**Report Results**:
After testing, update `HARDWARE-BINDING-IMPLEMENTATION-PLAN.md` with Thor-specific findings.

---

## SPROUT: TrustZone Provider Testing

Same as Thor - both are ARM64 with TrustZone/OP-TEE.

```bash
cd ~/ai-workspace/web4

python3 -c "
import sys
sys.path.insert(0, 'core')
from lct_binding import detect_platform, TrustZoneProvider
from lct_capability_levels import EntityType

platform = detect_platform()
print(f'Platform: {platform.name}')
print(f'Has TrustZone: {platform.has_trustzone}')

provider = TrustZoneProvider()
lct = provider.create_lct(EntityType.AI, 'sprout-test')
print(f'Created: {lct.lct_id}')
print(f'Trust Ceiling: {lct.t3_tensor.trust_ceiling}')
"
```

---

## Cross-Machine Verification

After each machine tests its provider:

1. **Compare trust ceilings**:
   - CBP (software): 0.85
   - Legion (TPM): 1.0
   - Thor/Sprout (TrustZone or simulated): 1.0 or 0.85

2. **Verify signature interoperability**:
   - Create LCT on one machine
   - Export public key
   - Verify signature on different machine

3. **Document any fixes**:
   - If provider code needed changes, commit with clear message
   - Update this file with actual vs expected results

---

## Commit After Testing

Each machine should:
```bash
git add -A
git commit -m "Verified lct_binding on [MACHINE]: [RESULTS]

- Platform: [detected info]
- Hardware: [TPM2/TrustZone/None]
- Trust ceiling: [value]
- Issues found: [any]
- Fixes applied: [any]

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"

git push
```

---

## Priority

**HIGH** - This is key infrastructure for trust-building across the system. Hardware binding enables:
- Unforgeable identity for AI agents
- Cross-machine trust verification
- Attestation of runtime environment
- Foundation for secure multi-agent coordination

Complete testing on all machines before proceeding with HRM integration.
