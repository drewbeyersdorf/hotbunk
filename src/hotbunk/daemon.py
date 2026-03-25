"""HotBunk daemon -- the always-on submarine.

Maintains a job queue, dispatches to the best available account via
PoolManager, monitors for rate limits, and auto-retries throttled jobs
on a fresh account. Designed to run in tmux or systemd on an always-on
machine.
"""

import json
import logging
import signal
import time
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from .accounts import AccountManager, HOTBUNK_DIR
from .db import HotBunkDB, DEFAULT_DB_PATH
from .detector import SessionDetector
from .pool import PoolManager
from .runner import JobRunner, JobResult

logger = logging.getLogger("hotbunk.daemon")


@dataclass
class DaemonConfig:
    """Configuration for the daemon."""
    db_path: Path = field(default_factory=lambda: DEFAULT_DB_PATH)
    poll_interval: int = 10          # seconds between pool checks
    max_concurrent_jobs: int = 2     # max jobs running at once
    retry_on_throttle: bool = True   # retry throttled jobs on another account
    max_retries: int = 3             # max retries per job


@dataclass
class PendingJob:
    """A job waiting to be dispatched."""
    job_type: str
    command: str
    retries: int = 0


class Daemon:
    """The always-on process that manages the account pool.

    The daemon:
    1. Maintains a job queue (deque of PendingJob)
    2. Ingests jobs from a JSONL queue file
    3. Dispatches jobs to the best available account
    4. Monitors for rate limits via the runner
    5. Auto-retries throttled jobs on another account
    6. Logs everything to SQLite
    """

    def __init__(
        self,
        config: Optional[DaemonConfig] = None,
        queue_path: Optional[Path] = None,
    ):
        self.config = config or DaemonConfig()
        self.db = HotBunkDB(self.config.db_path)
        self.accounts = AccountManager()
        self.detector = SessionDetector()
        self.pool = PoolManager(self.accounts, self.detector)
        self.runner = JobRunner(self.db)
        self.pending_jobs: deque[PendingJob] = deque()
        self.running_count = 0
        self._running = False
        self.queue_path = queue_path or (HOTBUNK_DIR / "queue.jsonl")

    def enqueue(self, job_type: str, command: str):
        """Add a job to the pending queue."""
        self.pending_jobs.append(PendingJob(job_type=job_type, command=command))
        logger.info(f"Enqueued {job_type} job: {command[:60]}")

    def dequeue(self) -> Optional[dict]:
        """Remove and return the next pending job, or None."""
        if not self.pending_jobs:
            return None
        job = self.pending_jobs.popleft()
        return {"job_type": job.job_type, "command": job.command, "retries": job.retries}

    def ingest_queue(self):
        """Read and clear the JSONL queue file, adding jobs to pending.

        The CLI writes jobs here via `hotbunk queue add`. The daemon picks
        them up on each tick, then truncates the file so jobs are not
        re-processed.
        """
        if not self.queue_path.exists():
            return
        try:
            text = self.queue_path.read_text().strip()
            self.queue_path.write_text("")  # clear after reading
            if not text:
                return
            for line in text.split("\n"):
                if not line.strip():
                    continue
                data = json.loads(line)
                self.enqueue(data["job_type"], data["command"])
        except (json.JSONDecodeError, KeyError, OSError) as e:
            logger.error(f"Error reading queue file: {e}")

    def run_forever(self):
        """Main daemon loop. Runs until SIGINT or SIGTERM."""
        self._running = True
        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)

        logger.info("Daemon started. Polling every %ds.", self.config.poll_interval)
        self.db.record_event("daemon_start", "", "Daemon started")

        while self._running:
            try:
                self._tick()
            except Exception as e:
                logger.error(f"Daemon tick error: {e}", exc_info=True)
                self.db.record_event("error", "", str(e))
            time.sleep(self.config.poll_interval)

        self.db.record_event("daemon_stop", "", "Daemon stopped")
        logger.info("Daemon stopped.")

    def _tick(self):
        """One iteration of the daemon loop."""
        # Ingest any new jobs from the queue file
        self.ingest_queue()

        # Sync throttle state from DB into pool manager
        for account in self.accounts.list_accounts():
            if self.db.is_throttled(account.name):
                self.pool.record_throttle(account.name)

        # Try to dispatch pending jobs
        while (
            self.pending_jobs
            and self.running_count < self.config.max_concurrent_jobs
        ):
            job_data = self.dequeue()
            if not job_data:
                break

            account_name = self.pool.pick_account(job_data["job_type"])
            if not account_name:
                # No account available -- put job back at the front
                self.pending_jobs.appendleft(
                    PendingJob(
                        job_type=job_data["job_type"],
                        command=job_data["command"],
                        retries=job_data["retries"],
                    )
                )
                logger.debug("No account available, job re-queued")
                break

            self._dispatch(job_data, account_name)

    def _dispatch(self, job_data: dict, account_name: str):
        """Run a job on the given account."""
        creds_dir = self.accounts.get_credentials_dir(account_name)
        logger.info(
            f"Dispatching {job_data['job_type']} to {account_name}: "
            f"{job_data['command'][:60]}"
        )
        self.db.record_event(
            "dispatch", account_name,
            f"{job_data['job_type']}: {job_data['command'][:80]}"
        )

        self.running_count += 1
        self.pool.record_job_start(account_name)

        try:
            result = self.runner.run_job(
                command=job_data["command"],
                account=account_name,
                job_type=job_data["job_type"],
                creds_dir=creds_dir,
            )
            self._handle_result(result, job_data)
        finally:
            self.running_count -= 1
            self.pool.record_job_end(account_name)

    def _handle_result(self, result: JobResult, job_data: dict):
        """Handle a completed job, retrying on throttle if configured."""
        if result.throttled and self.config.retry_on_throttle:
            retries = job_data.get("retries", 0)
            if retries < self.config.max_retries:
                logger.warning(
                    f"Job throttled on {result.account}, re-queuing "
                    f"(retry {retries + 1}/{self.config.max_retries})"
                )
                self.pending_jobs.append(
                    PendingJob(
                        job_type=job_data["job_type"],
                        command=job_data["command"],
                        retries=retries + 1,
                    )
                )
                self.db.record_event(
                    "retry", result.account,
                    f"Job {result.job_id} re-queued after throttle"
                )
                return

        if result.exit_code != 0 and not result.throttled:
            logger.error(f"Job {result.job_id} failed with exit code {result.exit_code}")
        else:
            logger.info(f"Job {result.job_id} completed on {result.account}")

    def _handle_signal(self, signum, frame):
        """Graceful shutdown on SIGINT/SIGTERM."""
        logger.info(f"Received signal {signum}, shutting down...")
        self._running = False
