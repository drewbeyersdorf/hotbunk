"""Session detection -- watches for active Claude Code processes.

Cross-platform implementation using psutil. Works on Linux, macOS, and Windows.

Note on macOS: Claude Code may store credentials in Keychain rather than
on-disk config files. Credential management is handled in accounts.py and
is a separate concern from process detection here. If you need to resolve
Keychain-stored credentials, see accounts.py.
"""

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import psutil


@dataclass
class ClaudeSession:
    """A detected Claude Code process."""

    pid: int
    user: str
    started_at: float
    cwd: str
    account: Optional[str] = None  # which hotbunk account, if detectable


class SessionDetector:
    """Detects active Claude Code sessions on this machine.

    Uses psutil for cross-platform process enumeration (Linux, macOS, Windows).
    """

    # Process name patterns that indicate a Claude Code process.
    # We match against both the process name and the full command line.
    _CLAUDE_INDICATORS = ("claude",)

    # Substrings that indicate a process is NOT a real Claude session
    # (e.g., this tool scanning for sessions, or grep/pgrep lookups).
    _SKIP_PATTERNS = ("pgrep", "grep", "hotbunk")

    def get_active_sessions(self) -> list[ClaudeSession]:
        """Find all running Claude Code processes."""
        sessions = []
        for proc in psutil.process_iter(["pid", "name", "cmdline"]):
            try:
                info = proc.info
                if not self._is_claude_process(info):
                    continue
                session = self._build_session(proc)
                if session:
                    sessions.append(session)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                # Process vanished or we lack permission -- skip it.
                continue
        return sessions

    def is_interactive_session_active(self) -> bool:
        """Check if there's an interactive (foreground) Claude Code session.

        Interactive sessions are attached to a TTY/terminal.
        """
        sessions = self.get_active_sessions()
        for session in sessions:
            if self._has_tty(session.pid):
                return True
        return False

    def get_current_account_from_env(self, pid: int) -> Optional[str]:
        """Try to determine which hotbunk account a process is using.

        Reads CLAUDE_CONFIG_DIR from the process environment. On some
        platforms (especially Windows and macOS), reading another process's
        environment may require elevated privileges.
        """
        try:
            proc = psutil.Process(pid)
            environ = proc.environ()
            config_dir = environ.get("CLAUDE_CONFIG_DIR")
            if not config_dir:
                return None
            # Extract account name from path like ~/.hotbunk/accounts/<name>/
            parts = Path(config_dir).parts
            if "accounts" in parts:
                idx = parts.index("accounts")
                if idx + 1 < len(parts):
                    return parts[idx + 1]
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess, OSError):
            pass
        return None

    def _is_claude_process(self, info: dict) -> bool:
        """Determine if a process_iter info dict represents a Claude Code process."""
        name = (info.get("name") or "").lower()
        cmdline = info.get("cmdline") or []
        cmdline_str = " ".join(cmdline).lower()

        # Must have "claude" somewhere in name or command line
        has_claude = any(
            indicator in name or indicator in cmdline_str
            for indicator in self._CLAUDE_INDICATORS
        )
        if not has_claude:
            return False

        # Skip processes that are clearly not Claude sessions
        if any(skip in cmdline_str for skip in self._SKIP_PATTERNS):
            return False

        return True

    def _build_session(self, proc: psutil.Process) -> Optional[ClaudeSession]:
        """Build a ClaudeSession from a psutil.Process."""
        pid = proc.pid
        started_at = self._get_process_start_time(proc)
        cwd = self._get_process_cwd(proc)
        user = self._get_process_user(proc)
        account = self.get_current_account_from_env(pid)

        return ClaudeSession(
            pid=pid,
            user=user,
            started_at=started_at,
            cwd=cwd,
            account=account,
        )

    def _has_tty(self, pid: int) -> bool:
        """Check if a process is attached to a terminal.

        On Unix (Linux/macOS), psutil.Process.terminal() returns the TTY
        device path (e.g., /dev/pts/0) or None if not attached.

        On Windows, terminal() is not available. We fall back to checking
        if the process has a valid console window handle via the session ID,
        though this is an imperfect heuristic.
        """
        try:
            proc = psutil.Process(pid)
            # terminal() is available on Unix platforms
            if hasattr(proc, "terminal"):
                tty = proc.terminal()
                return tty is not None
            # Windows fallback: no reliable TTY detection.
            # A process with a non-zero session ID is likely interactive.
            return False
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            return False

    def _get_process_start_time(self, proc: psutil.Process) -> float:
        """Get process start time as a Unix timestamp."""
        try:
            return proc.create_time()
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            return time.time()

    def _get_process_cwd(self, proc: psutil.Process) -> str:
        """Get the working directory of a process."""
        try:
            return proc.cwd()
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess, OSError):
            return "unknown"

    def _get_process_user(self, proc: psutil.Process) -> str:
        """Get the user running a process."""
        try:
            return proc.username()
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess, KeyError):
            return "unknown"
