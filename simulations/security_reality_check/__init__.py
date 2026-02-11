"""Security Reality Check v1 scaffolding.

This package provides:
- invariant loading,
- deterministic scenario replay hooks,
- scorecard reporting.
"""

from .runner import run_scenarios

__all__ = ["run_scenarios"]
