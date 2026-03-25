"""Session detection -- watches for active Claude Code processes."""

import os
import re
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class ClaudeSession:
    """A detected Claude Code process."""

    pid: int
    user: str
    started_at: float
    cwd: str
    account: Optional[str] = None  # which hotbunk account, if detectable


class SessionDetector:
    """Detects active Claude Code sessions on this machine."""

    def get_active_sessions(self) -> list[ClaudeSession]:
        """Find all running Claude Code processes."""
        sessions = []
        try:
            # Find claude processes (the Node.js CLI)
            result = subprocess.run(
                ["pgrep", "-af", "claude"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            for line in result.stdout.strip().split("\n"):
                if not line:
                    continue
                session = self._parse_process_line(line)
                if session:
                    sessions.append(session)
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        return sessions

    def is_interactive_session_active(self) -> bool:
        """Check if there's an interactive (foreground) Claude Code session."""
        sessions = self.get_active_sessions()
        # Filter out background/automated sessions
        # Interactive sessions are attached to a TTY
        for session in sessions:
            if self._has_tty(session.pid):
                return True
        return False

    def get_current_account_from_env(self, pid: int) -> Optional[str]:
        """Try to determine which account a process is using via CLAUDE_CONFIG_DIR."""
        try:
            environ_path = Path(f"/proc/{pid}/environ")
            if not environ_path.exists():
                return None
            env_data = environ_path.read_bytes().decode("utf-8", errors="replace")
            for entry in env_data.split("\0"):
                if entry.startswith("CLAUDE_CONFIG_DIR="):
                    config_dir = entry.split("=", 1)[1]
                    # Extract account name from path like ~/.hotbunk/accounts/<name>/
                    parts = Path(config_dir).parts
                    if "accounts" in parts:
                        idx = parts.index("accounts")
                        if idx + 1 < len(parts):
                            return parts[idx + 1]
        except (PermissionError, OSError):
            pass
        return None

    def _parse_process_line(self, line: str) -> Optional[ClaudeSession]:
        """Parse a pgrep output line into a ClaudeSession."""
        parts = line.split(None, 1)
        if len(parts) < 2:
            return None
        try:
            pid = int(parts[0])
        except ValueError:
            return None

        cmd = parts[1]
        # Only match actual Claude Code processes, not grep or this script
        if "claude" not in cmd.lower():
            return None
        # Skip pgrep/grep/hotbunk processes
        if any(skip in cmd for skip in ["pgrep", "grep", "hotbunk"]):
            return None

        # Get process start time
        started_at = self._get_process_start_time(pid)
        cwd = self._get_process_cwd(pid)
        user = self._get_process_user(pid)

        return ClaudeSession(
            pid=pid,
            user=user,
            started_at=started_at,
            cwd=cwd,
            account=self.get_current_account_from_env(pid),
        )

    def _has_tty(self, pid: int) -> bool:
        """Check if a process is attached to a terminal."""
        try:
            stat_path = Path(f"/proc/{pid}/stat")
            if not stat_path.exists():
                return False
            stat = stat_path.read_text()
            # Field 7 in /proc/pid/stat is tty_nr (0 means no TTY)
            fields = stat.split()
            if len(fields) > 6:
                return int(fields[6]) != 0
        except (PermissionError, OSError, ValueError):
            pass
        return False

    def _get_process_start_time(self, pid: int) -> float:
        """Get process start time as Unix timestamp."""
        try:
            stat_path = Path(f"/proc/{pid}/stat")
            return stat_path.stat().st_mtime
        except OSError:
            return time.time()

    def _get_process_cwd(self, pid: int) -> str:
        """Get the working directory of a process."""
        try:
            return str(Path(f"/proc/{pid}/cwd").resolve())
        except (PermissionError, OSError):
            return "unknown"

    def _get_process_user(self, pid: int) -> str:
        """Get the user running a process."""
        try:
            stat = Path(f"/proc/{pid}").stat()
            import pwd
            return pwd.getpwuid(stat.st_uid).pw_name
        except (PermissionError, OSError, KeyError):
            return "unknown"
