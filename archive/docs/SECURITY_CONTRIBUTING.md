# Security Contributing Guide

**Want to help make Web4 LCT identity production-ready?**

We're explicitly inviting security researchers and developers to attack our system and help fix vulnerabilities.

---

## Quick Start

### 1. Read the Security Audit
**File**: `private-context/outreach/LCT_SECURITY_AUDIT.md` (also on GitHub)

This documents all known vulnerabilities with:
- Attack scenarios
- Proposed fixes
- Severity ratings

### 2. Pick a Vulnerability to Fix

**Critical (Help Needed Most)**:
1. **ATP Budget Tracking** - Budget limits not enforced ([roadmap](../private-context/outreach/LCT_SECURITY_FIX_ROADMAP.md#day-1-2-atp-budget-tracking-and-enforcement))
2. **Revocation Registry** - No way to revoke compromised keys ([roadmap](../private-context/outreach/LCT_SECURITY_FIX_ROADMAP.md#day-3-4-revocation-registry))
3. **Replay Attack Prevention** - Signatures can be reused ([roadmap](../private-context/outreach/LCT_SECURITY_FIX_ROADMAP.md#day-5-6-replay-attack-prevention))
4. **Timestamp Validation** - No temporal bounds checking
5. **Key Rotation** - No way to update keys without losing identity
6. **Witness Enforcement** - Witness requirements ignored
7. **Resource Constraints** - Delegation scope too broad

### 3. Implementation Guide

**We've provided working code for most fixes!**

See `private-context/outreach/LCT_SECURITY_FIX_ROADMAP.md` for:
- Complete implementation examples
- Integration code
- Test cases
- Timeline estimates

**You can literally copy-paste the code and adapt it.**

### 4. Development Setup

```bash
# Clone repos
git clone https://github.com/dp-web4/web4.git
git clone https://github.com/dp-web4/private-context.git

# Install dependencies
cd web4
pip install -r requirements.txt

# Run existing tests
python -m pytest implementation/reference/tests/

# Run LCT example
python implementation/reference/lct_identity.py
```

### 5. Make Your Changes

```bash
# Create branch
git checkout -b fix-atp-tracking

# Implement fix (use roadmap code as starting point)
# Add tests
# Document changes

# Run tests
python -m pytest

# Commit
git commit -m "Implement ATP budget tracking and enforcement

Fixes critical vulnerability: ATP limits defined but not enforced.

Implementation:
- Added ATPTracker class for budget management
- Integrated with verify_authorized_action()
- Added daily recharge mechanism
- Tests: 100% coverage

See: private-context/outreach/LCT_SECURITY_AUDIT.md#atp-budget-tracking
"
```

### 6. Submit Pull Request

```bash
git push origin fix-atp-tracking

# Open PR on GitHub with:
# - Title: "Fix: ATP budget tracking and enforcement"
# - Description: Link to security audit issue
# - Tests: Show test results
# - Reference: Mention vulnerability number
```

---

## What We're Looking For

### Security Fixes (Priority)
- Implement fixes from roadmap
- Add comprehensive tests
- Ensure no performance regression
- Document security considerations

### Attack Vectors (Always Welcome)
- Find vulnerabilities we missed
- Document attack scenarios
- Provide proof-of-concept exploits
- Suggest mitigations

### Code Review (Helpful)
- Review proposed fixes
- Identify edge cases
- Suggest improvements
- Validate cryptography usage

### Testing (Critical)
- Write attack-based tests
- Fuzzing and edge cases
- Load testing
- Security scanning

---

## Contribution Types

### 🔴 Critical: Security Fixes
Implement fixes for the 7 critical vulnerabilities. Complete working code is in the roadmap - adapt and integrate.

**Time**: 2-5 days per vulnerability
**Impact**: Production-readiness
**Credit**: Co-author on security documentation

### 🟡 High Value: Attack Discovery
Find new vulnerabilities, document attack scenarios, report via GitHub issues.

**Time**: Variable
**Impact**: System hardening
**Credit**: Researcher credit in documentation

### 🟢 Good: Testing & Review
Write tests, review code, validate fixes, provide feedback.

**Time**: Hours to days
**Impact**: Quality assurance
**Credit**: Contributor credit

---

## Communication

### GitHub Issues
- **Security vulnerabilities**: Label `security`
- **Bug reports**: Label `bug`
- **Questions**: Label `question`
- **Help wanted**: Label `help-wanted`

### Discord (Coming Soon)
We'll set up a Discord for real-time collaboration.

### Email
For sensitive security issues: dp@metalinxx.io

---

## Recognition

We don't have formal bug bounties yet, but contributors get:

1. **Credit** - Listed in security documentation
2. **Co-authorship** - Significant contributions earn co-author status
3. **Reputation** - T3/V3 scores in Web4 system (once operational)
4. **Visibility** - Showcased in project updates and papers

---

## Code Standards

### Security
- **No shortcuts** - Security > convenience
- **Test attack scenarios** - Every fix must test the attack it prevents
- **Document assumptions** - Make security assumptions explicit
- **Fail secure** - Default to denying access

### Code Quality
- **Type hints** - All function signatures
- **Docstrings** - All public functions
- **Tests** - Minimum 90% coverage for security code
- **Error handling** - Explicit, logged, informative

### Commit Messages
```
[Type]: Brief description (50 chars)

Detailed explanation of what and why (not how).

Implementation notes:
- Key decision 1
- Key decision 2

Fixes: #issue-number
See: path/to/documentation.md
```

**Types**: `Fix`, `Security`, `Test`, `Docs`, `Refactor`

---

## Timeline

**Target**: Production-ready by **December 1, 2025**

**Week 1** (Nov 11-17): Critical fixes (ATP, revocation, replay)
**Week 2** (Nov 18-24): Validation (timestamps, logging, constraints)
**Week 3** (Nov 25-Dec 1): Advanced (key rotation, witnesses)
**Dec 1**: LCT transition - first production deployment

**Your contributions directly impact this timeline!**

---

## Philosophy

> "We WANT adversarial interactions. That helps us strengthen the core.
> Challenges are invited and faced, not shunned. We are building an immune system."
> - Dennis Palatov

We're being radically transparent about vulnerabilities because:
- **Trust through honesty** - Not hiding weaknesses
- **Immune system building** - Expose to challenges early
- **Community collaboration** - Many eyes make security bugs shallow
- **Real-world readiness** - Better to find issues now than in production

**This is not a "look how secure we are" project. This is "help us make it secure."**

---

## Quick Links

- **Security Audit**: `private-context/outreach/LCT_SECURITY_AUDIT.md`
- **Fix Roadmap**: `private-context/outreach/LCT_SECURITY_FIX_ROADMAP.md`
- **LCT Implementation**: `implementation/reference/lct_identity.py`
- **Authorization Engine**: `implementation/reference/authorization_engine.py`
- **GitHub Issues**: https://github.com/dp-web4/web4/issues

---

## Example: Fixing ATP Budget Tracking

Here's a complete workflow example:

```bash
# 1. Read vulnerability description
cat private-context/outreach/LCT_SECURITY_AUDIT.md | grep -A 50 "ATP Budget"

# 2. Read proposed fix
cat private-context/outreach/LCT_SECURITY_FIX_ROADMAP.md | grep -A 200 "ATP Budget"

# 3. Create branch
git checkout -b fix-atp-tracking

# 4. Create new file with tracker implementation
cat > implementation/reference/atp_tracker.py <<'EOF'
# (Copy code from roadmap)
EOF

# 5. Integrate with lct_identity.py
# Edit verify_authorized_action() to call ATP tracker

# 6. Write tests
cat > implementation/reference/tests/test_atp_tracker.py <<'EOF'
def test_atp_tracking():
    tracker = ATPTracker()
    tracker.create_account("test-entity", daily_limit=1000, per_action_limit=100)

    # First deduction should succeed
    success, msg = tracker.check_and_deduct("test-entity", 50)
    assert success
    assert tracker.get_balance("test-entity") == 950

    # Exhaust budget
    for i in range(19):
        tracker.check_and_deduct("test-entity", 50)

    # Should fail - budget exhausted
    success, msg = tracker.check_and_deduct("test-entity", 50)
    assert not success
    assert "limit exceeded" in msg.lower()
EOF

# 7. Run tests
python -m pytest implementation/reference/tests/test_atp_tracker.py -v

# 8. Commit and push
git add .
git commit -m "Fix: Implement ATP budget tracking and enforcement"
git push origin fix-atp-tracking

# 9. Open PR on GitHub
```

**That's it! You've fixed a critical security vulnerability.**

---

## Questions?

- Open a GitHub issue with `question` label
- Email dp@metalinxx.io
- Comment on the security issue

**We're here to help you contribute!**

---

**Let's build the most secure AI coordination infrastructure possible - together.** 🚀
