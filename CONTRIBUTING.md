# Contributing to Web4

Web4 is research into trust-native distributed intelligence. Contributions welcome.

## Quick Start

```bash
# Clone the repo
git clone https://github.com/dp-web4/web4.git
cd web4

# Explore the structure
ls docs/           # Documentation by purpose
ls sessions/       # Research session scripts
ls archive/        # Historical prototypes
```

## How to Contribute

### Documentation
- Fix broken links, typos, outdated info
- Improve navigation and onboarding
- Add examples and clarifications

### Research
- Extend existing research sessions
- Propose new experiments
- Challenge assumptions

### Implementation
- Reference implementations in `web4-standard/implementation/`
- Integration patterns in `docs/how/`
- Test coverage improvements

## Terminology Protection

Web4 has established terminology. Please don't redefine these terms:

| Term | Meaning | Spec Location |
|------|---------|---------------|
| **LCT** | Linked Context Token | `web4-standard/core-spec/LCT-linked-context-token.md` |
| **MRH** | Markov Relevancy Horizon | `web4-standard/core-spec/mrh-tensors.md` |
| **T3** | Trust Tensor (6 dimensions) | `web4-standard/core-spec/t3-v3-tensors.md` |
| **V3** | Value Tensor (6 dimensions) | `web4-standard/core-spec/t3-v3-tensors.md` |
| **ATP/ADP** | Allocation Transfer/Discharge Packet | `web4-standard/core-spec/atp-adp-cycle.md` |
| **R6** | Rules/Role/Request/Reference/Resource/Result | `web4-standard/core-spec/r6-framework.md` |

Before creating new identity/trust systems:
1. Check [docs/reference/GLOSSARY.md](docs/reference/GLOSSARY.md)
2. Check if existing infrastructure can be extended
3. Never create new meanings for established acronyms

## Development Philosophy

This is a research environment:
- Failures teach more than successes
- Pragmatic over performative
- Document lessons, not just successes
- Uncertainty is the medium, not the problem

## PR Workflow

1. Fork the repository
2. Create a descriptive branch (`feature/lct-witness-optimization`)
3. Make changes with clear commit messages
4. Submit PR with:
   - What changed
   - Why it matters
   - Any new terminology or concepts introduced
   - Test results if applicable

## Questions?

- Open an issue for discussions
- See [docs/START_HERE.md](docs/START_HERE.md) for navigation
- Read [STATUS.md](STATUS.md) for current project state

---

*Contributions should advance the research mission: building infrastructure where trust emerges from behavior.*
