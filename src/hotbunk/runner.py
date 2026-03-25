"""Job runner with throttle-aware subprocess management."""

import os
import subprocess
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .db import HotBunkDB
from .throttle_detector import is_throttle_signal, parse_throttle_message


@dataclass
class JobResult:
    """Result of a completed job."""
    job_id: str
    exit_code: int
    throttled: bool = False
    throttle_wait: int = 0
    account: str = ""


class JobRunner:
    """Runs jobs as subprocesses, monitoring for throttle signals."""

    def __init__(self, db: HotBunkDB):
        self.db = db

    def run_job(
        self,
        command: str,
        account: str,
        job_type: str,
        creds_dir: Optional[Path] = None,
    ) -> JobResult:
        """Run a command and monitor for rate limit signals.

        Returns a JobResult with throttled=True if a rate limit was detected.
        """
        env = os.environ.copy()
        if creds_dir:
            env["CLAUDE_CONFIG_DIR"] = str(creds_dir)
        env["HOTBUNK_ACCOUNT"] = account
        env["HOTBUNK_JOB_TYPE"] = job_type

        proc = subprocess.Popen(
            command,
            shell=True,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        job_id = self.db.record_job(job_type, command, account, pid=proc.pid)
        throttled = False
        throttle_wait = 0

        # Read stderr in a thread to detect throttle signals
        stderr_lines: list[str] = []

        def read_stderr():
            nonlocal throttled, throttle_wait
            for line_bytes in proc.stderr:
                line = line_bytes.decode("utf-8", errors="replace").strip()
                stderr_lines.append(line)
                if is_throttle_signal(line):
                    throttled = True
                    msg = parse_throttle_message(line)
                    throttle_wait = msg.wait_seconds
                    self.db.record_throttle(account)
                    self.db.record_event(
                        "throttle", account,
                        f"Rate limit detected: {line[:100]}"
                    )

        stderr_thread = threading.Thread(target=read_stderr, daemon=True)
        stderr_thread.start()

        # Drain stdout in the main thread -- stderr is handled by the thread
        if proc.stdout:
            proc.stdout.read()
        proc.wait()
        stderr_thread.join(timeout=5)

        exit_code = proc.returncode
        error = "\n".join(stderr_lines[-5:]) if stderr_lines else ""

        self.db.complete_job(job_id, exit_code=exit_code, error=error)

        if throttled:
            self.db.record_event(
                "throttle_exit", account,
                f"Job {job_id} exited due to throttle (code {exit_code})"
            )

        return JobResult(
            job_id=job_id,
            exit_code=exit_code,
            throttled=throttled,
            throttle_wait=throttle_wait,
            account=account,
        )
