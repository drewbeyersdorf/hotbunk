"""Integration test: daemon ingests a job from queue file and processes it."""

import json
import tempfile
from pathlib import Path
from hotbunk.daemon import Daemon, DaemonConfig


def test_daemon_ingests_and_dispatches():
    """Full cycle: write job to queue file, daemon ingests it, job enters pending."""
    with tempfile.TemporaryDirectory() as d:
        db_path = Path(d) / "test.db"
        queue_path = Path(d) / "queue.jsonl"

        # Write two jobs to the queue
        with open(queue_path, "w") as f:
            f.write(json.dumps({"job_type": "militia", "command": "echo submarine"}) + "\n")
            f.write(json.dumps({"job_type": "ci", "command": "echo periscope"}) + "\n")

        cfg = DaemonConfig(db_path=db_path, poll_interval=1, max_concurrent_jobs=2)
        daemon = Daemon(cfg, queue_path=queue_path)

        # Ingest from queue file
        daemon.ingest_queue()

        # Both jobs should be pending
        assert len(daemon.pending_jobs) == 2

        # Queue file should be cleared
        assert queue_path.read_text().strip() == ""

        # Dequeue should return them in order
        job1 = daemon.dequeue()
        assert job1["job_type"] == "militia"
        assert job1["command"] == "echo submarine"

        job2 = daemon.dequeue()
        assert job2["job_type"] == "ci"
        assert job2["command"] == "echo periscope"

        assert daemon.dequeue() is None


def test_daemon_tick_with_no_accounts():
    """Tick should not crash when no accounts are registered."""
    with tempfile.TemporaryDirectory() as d:
        db_path = Path(d) / "test.db"
        queue_path = Path(d) / "queue.jsonl"

        with open(queue_path, "w") as f:
            f.write(json.dumps({"job_type": "general", "command": "echo hello"}) + "\n")

        cfg = DaemonConfig(db_path=db_path, poll_interval=1)
        daemon = Daemon(cfg, queue_path=queue_path)

        # Should not raise even with no accounts
        daemon._tick()

        # Job should be re-queued (no account available)
        assert len(daemon.pending_jobs) == 1
