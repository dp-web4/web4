# Research Sessions

This directory contains research session scripts and outputs from Web4 development.

## Structure

```
sessions/
├── active/      # Current/recent session scripts (session_*.py)
├── archive/     # Completed research phases (to be organized)
├── outputs/     # Session results (.json, .log, .txt)
└── prototypes/  # Working prototypes (prototype_*.py)
```

## Session Numbering

Sessions are numbered sequentially and tracked in `/SESSION_MAP.md` at root.

- Sessions 1-100: Early exploration
- Sessions 101-150: Core concepts development
- Sessions 151-200: Integration and validation
- Sessions 200+: Current work

## Running Sessions

Most session scripts are standalone Python files:

```bash
cd sessions/active
python session_200_*.py
```

Check individual session headers for dependencies and context.
