# Governance integration helpers
PY?=python3

gov-check:
	$(PY) integrations/integrate_governance.py --config integrations/governance_map.yaml --repo-root .
gov-apply:
	$(PY) integrations/integrate_governance.py --config integrations/governance_map.yaml --repo-root . --apply
gov-tables:
	$(PY) integrations/govsim.py integrations/governance_map.yaml docs/collab/governance_controls.csv docs/collab/governance_controls.md
