"""Pool manager -- routes jobs to the best available account."""

import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from .accounts import AccountManager, AccountInfo, AccountPolicy
from .detector import SessionDetector


class AccountState(Enum):
    INTERACTIVE = "interactive"  # owner is active
    IDLE = "idle"                # no session, available for automation
    SLEEPING = "sleeping"        # in sleep window, full automation access
    THROTTLED = "throttled"      # rate limited
    COOLDOWN = "cooldown"        # recently throttled, deprioritized


@dataclass
class AccountStatus:
    """Current runtime status of an account."""

    account: AccountInfo
    state: AccountState
    active_sessions: int = 0
    automated_jobs: int = 0
    last_throttled: Optional[float] = None
    headroom_estimate: float = 1.0  # 0.0 = fully consumed, 1.0 = fresh


@dataclass
class Job:
    """An automated job submitted to the pool."""

    id: str
    job_type: str  # militia, training, ci
    command: str
    submitted_at: float = field(default_factory=time.time)
    assigned_to: Optional[str] = None  # account name
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    status: str = "queued"  # queued, running, completed, failed


class PoolManager:
    """Decides which account should handle the next job."""

    def __init__(self, account_manager: AccountManager, detector: SessionDetector):
        self.accounts = account_manager
        self.detector = detector
        self._throttle_history: dict[str, float] = {}  # account_name -> last_throttle_time
        self._active_automated: dict[str, int] = {}  # account_name -> count of running automated jobs

    def get_pool_status(self) -> list[AccountStatus]:
        """Get current status of all accounts in the pool."""
        accounts = self.accounts.list_accounts()
        sessions = self.detector.get_active_sessions()
        statuses = []

        for account in accounts:
            state = self._determine_state(account, sessions)
            status = AccountStatus(
                account=account,
                state=state,
                active_sessions=self._count_sessions(account.name, sessions),
                automated_jobs=self._active_automated.get(account.name, 0),
                last_throttled=self._throttle_history.get(account.name),
                headroom_estimate=self._estimate_headroom(account.name, state),
            )
            statuses.append(status)

        return statuses

    def pick_account(self, job_type: str) -> Optional[str]:
        """Pick the best account for a new automated job.

        Returns account name or None if no account is available.
        """
        statuses = self.get_pool_status()
        candidates = []

        for status in statuses:
            # Skip accounts that can't take this job
            if not self._can_accept_job(status, job_type):
                continue
            candidates.append(status)

        if not candidates:
            return None

        # Sort by preference: sleeping > idle > cooldown
        # Within same state, prefer most headroom
        def sort_key(s: AccountStatus) -> tuple:
            state_priority = {
                AccountState.SLEEPING: 0,
                AccountState.IDLE: 1,
                AccountState.COOLDOWN: 2,
            }
            return (
                state_priority.get(s.state, 99),
                -s.headroom_estimate,  # higher headroom = better
                s.automated_jobs,       # fewer running jobs = better
            )

        candidates.sort(key=sort_key)
        return candidates[0].account.name

    def record_throttle(self, account_name: str):
        """Record that an account hit a rate limit."""
        self._throttle_history[account_name] = time.time()

    def record_job_start(self, account_name: str):
        """Record that an automated job started on an account."""
        self._active_automated[account_name] = (
            self._active_automated.get(account_name, 0) + 1
        )

    def record_job_end(self, account_name: str):
        """Record that an automated job ended on an account."""
        count = self._active_automated.get(account_name, 0)
        self._active_automated[account_name] = max(0, count - 1)

    def _determine_state(self, account: AccountInfo, sessions: list) -> AccountState:
        """Determine the current state of an account."""
        name = account.name

        # Check if throttled recently (within last 30 minutes)
        last_throttle = self._throttle_history.get(name)
        if last_throttle and (time.time() - last_throttle) < 1800:
            return AccountState.THROTTLED
        if last_throttle and (time.time() - last_throttle) < 3600:
            return AccountState.COOLDOWN

        # Check if in sleep window
        if account.policy and self._in_sleep_window(account.policy):
            return AccountState.SLEEPING

        # Check for active interactive sessions
        for session in sessions:
            if session.account == name:
                return AccountState.INTERACTIVE

        return AccountState.IDLE

    def _in_sleep_window(self, policy: AccountPolicy) -> bool:
        """Check if the current time is within the policy's sleep window."""
        if not policy.sleep_window:
            return False

        try:
            start_str, end_str = policy.sleep_window.split("-")
            now = datetime.now()
            start_h, start_m = map(int, start_str.strip().split(":"))
            end_h, end_m = map(int, end_str.strip().split(":"))

            start_minutes = start_h * 60 + start_m
            end_minutes = end_h * 60 + end_m
            now_minutes = now.hour * 60 + now.minute

            # Handle overnight windows (e.g., 22:00-06:00)
            if start_minutes > end_minutes:
                return now_minutes >= start_minutes or now_minutes < end_minutes
            else:
                return start_minutes <= now_minutes < end_minutes
        except (ValueError, AttributeError):
            return False

    def _can_accept_job(self, status: AccountStatus, job_type: str) -> bool:
        """Check if an account can accept a new automated job."""
        # Never assign to interactive accounts
        if status.state == AccountState.INTERACTIVE:
            return False
        # Never assign to throttled accounts
        if status.state == AccountState.THROTTLED:
            return False

        policy = status.account.policy
        if not policy:
            return False
        # Must allow automated use
        if not policy.allow_automated:
            return False
        # Must allow this job type
        if job_type not in policy.automated_types:
            return False
        # Must not exceed concurrent limit
        if status.automated_jobs >= policy.max_automated_concurrent:
            return False

        return True

    def _count_sessions(self, account_name: str, sessions: list) -> int:
        """Count sessions belonging to an account."""
        return sum(1 for s in sessions if s.account == account_name)

    def _estimate_headroom(self, account_name: str, state: AccountState) -> float:
        """Estimate remaining rate limit headroom (0.0-1.0).

        This is a rough estimate based on state and recent history.
        Future versions will poll the actual rate limit API.
        """
        if state == AccountState.THROTTLED:
            return 0.0
        if state == AccountState.COOLDOWN:
            return 0.3
        if state == AccountState.SLEEPING:
            # Sleeping accounts likely have full headroom
            return 1.0

        # Reduce estimate based on active automated jobs
        jobs = self._active_automated.get(account_name, 0)
        return max(0.1, 1.0 - (jobs * 0.3))
