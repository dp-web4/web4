"""P0 scenario stubs for Security Reality Check v1."""

from .rt01_witness_cartel import run as run_rt01
from .rt02_roi_sybil import run as run_rt02
from .rt04_trust_admin_pivot import run as run_rt04
from .rt05_replay_ordering_drift import run as run_rt05

SCENARIOS = {
    "RT-01": run_rt01,
    "RT-02": run_rt02,
    "RT-04": run_rt04,
    "RT-05": run_rt05,
}
