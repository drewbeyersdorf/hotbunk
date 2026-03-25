"""Detect rate limit signals from Claude Code process output."""

import re
from dataclasses import dataclass
from typing import Optional

_THROTTLE_PATTERNS = [
    re.compile(r"rate.?limit", re.IGNORECASE),
    re.compile(r"usage.?limit", re.IGNORECASE),
    re.compile(r"too many requests", re.IGNORECASE),
    re.compile(r"please wait", re.IGNORECASE),
    re.compile(r"429", re.IGNORECASE),
]

_WAIT_PATTERN = re.compile(r"(\d+)\s*(minute|min|second|sec|hour|hr)", re.IGNORECASE)


@dataclass
class ThrottleMessage:
    raw: str
    wait_seconds: int = 300


def is_throttle_signal(line: str) -> bool:
    if not line or not line.strip():
        return False
    return any(p.search(line) for p in _THROTTLE_PATTERNS)


def parse_throttle_message(line: str) -> ThrottleMessage:
    match = _WAIT_PATTERN.search(line)
    if not match:
        return ThrottleMessage(raw=line, wait_seconds=300)

    amount = int(match.group(1))
    unit = match.group(2).lower()

    if unit.startswith("hour") or unit.startswith("hr"):
        seconds = amount * 3600
    elif unit.startswith("min"):
        seconds = amount * 60
    else:
        seconds = amount

    return ThrottleMessage(raw=line, wait_seconds=seconds)
