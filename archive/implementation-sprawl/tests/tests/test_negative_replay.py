"""
test_negative_replay.py
Illustrative replay-window test (logic only).
"""
from datetime import datetime, timedelta
import pytest

def accepts(ts, now, skew_s=300):
    delta = abs((ts - now).total_seconds())
    return delta <= skew_s

def test_replay_window_rejects_old_nonce():
    now = datetime(2025,9,11,15,0,0)
    stale = datetime(2025,9,11,14,40,0)
    assert not accepts(stale, now, skew_s=300)  # 20 min old -> reject

def test_timestamp_within_skew_is_ok():
    now = datetime(2025,9,11,15,0,0)
    near = datetime(2025,9,11,14,56,0)
    assert accepts(near, now, skew_s=300)  # 4 min diff -> ok
