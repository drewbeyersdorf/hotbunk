import json
import tempfile
from pathlib import Path
from hotbunk.daemon import DaemonConfig, Daemon

def test_daemon_config_defaults():
    cfg = DaemonConfig()
    assert cfg.poll_interval == 10
    assert cfg.max_concurrent_jobs == 2
    assert cfg.retry_on_throttle is True

def test_daemon_creates_db():
    with tempfile.TemporaryDirectory() as d:
        db_path = Path(d) / "test.db"
        cfg = DaemonConfig(db_path=db_path)
        daemon = Daemon(cfg)
        assert db_path.exists()

def test_daemon_queue_and_dequeue():
    with tempfile.TemporaryDirectory() as d:
        db_path = Path(d) / "test.db"
        cfg = DaemonConfig(db_path=db_path)
        daemon = Daemon(cfg)
        daemon.enqueue("militia", "echo test")
        assert len(daemon.pending_jobs) == 1
        job = daemon.dequeue()
        assert job is not None
        assert job["command"] == "echo test"
        assert len(daemon.pending_jobs) == 0

def test_daemon_reads_queue_file():
    with tempfile.TemporaryDirectory() as d:
        db_path = Path(d) / "test.db"
        queue_path = Path(d) / "queue.jsonl"
        with open(queue_path, "w") as f:
            f.write(json.dumps({"job_type": "militia", "command": "echo hello"}) + "\n")
        cfg = DaemonConfig(db_path=db_path)
        daemon = Daemon(cfg, queue_path=queue_path)
        daemon.ingest_queue()
        assert len(daemon.pending_jobs) == 1
        assert queue_path.read_text().strip() == ""
