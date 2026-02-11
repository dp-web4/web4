"""CLI entry point for Security Reality Check v1."""

from .runner import run_scenarios
from .scenarios import SCENARIOS

if __name__ == "__main__":
    run_scenarios(SCENARIOS)
