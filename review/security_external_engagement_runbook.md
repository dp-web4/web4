# External Red-Team Engagement Runbook (Draft)

## 1) Pre-Engagement Checklist
- [ ] Rules of engagement approved.
- [ ] In-scope components and environments frozen.
- [ ] Logging/telemetry enabled with retention policy.
- [ ] Incident response contacts and escalation paths validated.
- [ ] Safe-stop criteria agreed.

## 2) Severity Model (Recommended)
- **Critical**: Cross-component compromise or invariant breach with high systemic impact.
- **High**: Privilege escalation, trust/economic manipulation with significant operational effect.
- **Medium**: Exploitable weakness with constrained blast radius.
- **Low**: Hardening/documentation issue with limited direct exploitability.

## 3) Evidence Requirements per Finding
- Attack preconditions.
- Step-by-step reproduction procedure.
- Observed vs expected behavior.
- Impact analysis (technical + governance/economic).
- Mitigation recommendations with implementation notes.

## 4) Purple-Team Validation Loop
1. Red team demonstrates exploit.
2. Blue team instruments/updates detection.
3. Red team reruns exploit variation.
4. Joint review of MTTD/MTTR and residual risk.

## 5) Reporting Cadence
- Daily short ops summary (open attacks, blockers, incidents).
- Weekly risk review (new high/critical findings).
- End-of-phase checkpoint sign-off.

## 6) Exit Criteria
- All Critical findings addressed or accepted with explicit risk sign-off.
- High findings either remediated or scheduled with owner and deadline.
- Retest completed for fixed items.
- Residual-risk report delivered.

