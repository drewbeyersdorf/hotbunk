import tempfile
import time
from pathlib import Path
from hotbunk.db import HotBunkDB

def test_record_and_list_jobs():
    with tempfile.TemporaryDirectory() as d:
        db = HotBunkDB(Path(d) / "test.db")
        job_id = db.record_job("militia", "echo hello", "work")
        jobs = db.list_jobs(status="running")
        assert len(jobs) == 1
        assert jobs[0]["job_type"] == "militia"
        assert jobs[0]["account"] == "work"

def test_complete_job():
    with tempfile.TemporaryDirectory() as d:
        db = HotBunkDB(Path(d) / "test.db")
        job_id = db.record_job("ci", "run tests", "personal")
        db.complete_job(job_id, exit_code=0)
        jobs = db.list_jobs(status="completed")
        assert len(jobs) == 1
        assert jobs[0]["exit_code"] == 0

def test_record_and_list_events():
    with tempfile.TemporaryDirectory() as d:
        db = HotBunkDB(Path(d) / "test.db")
        db.record_event("throttle", "work", "Rate limit hit")
        db.record_event("switch", "personal", "Switched to personal")
        events = db.list_events(limit=10)
        assert len(events) == 2
        assert events[0]["event_type"] == "switch"  # most recent first

def test_record_throttle():
    with tempfile.TemporaryDirectory() as d:
        db = HotBunkDB(Path(d) / "test.db")
        db.record_throttle("work")
        assert db.is_throttled("work") is True
        assert db.is_throttled("personal") is False

def test_throttle_expires():
    with tempfile.TemporaryDirectory() as d:
        db = HotBunkDB(Path(d) / "test.db")
        db.record_throttle("work", timestamp=time.time() - 3700)  # > 1 hour ago
        assert db.is_throttled("work") is False
