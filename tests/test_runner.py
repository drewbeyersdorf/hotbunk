import tempfile
from pathlib import Path
from hotbunk.runner import JobRunner
from hotbunk.db import HotBunkDB

def test_run_simple_job():
    with tempfile.TemporaryDirectory() as d:
        db = HotBunkDB(Path(d) / "test.db")
        runner = JobRunner(db)
        result = runner.run_job(
            command="echo hello",
            account="work",
            job_type="general",
            creds_dir=None,
        )
        assert result.exit_code == 0
        assert result.throttled is False

def test_run_failing_job():
    with tempfile.TemporaryDirectory() as d:
        db = HotBunkDB(Path(d) / "test.db")
        runner = JobRunner(db)
        result = runner.run_job(
            command="exit 1",
            account="work",
            job_type="general",
            creds_dir=None,
        )
        assert result.exit_code == 1
        assert result.throttled is False

def test_detects_throttle_in_output():
    with tempfile.TemporaryDirectory() as d:
        db = HotBunkDB(Path(d) / "test.db")
        runner = JobRunner(db)
        result = runner.run_job(
            command='echo "Rate limit exceeded" >&2; exit 1',
            account="work",
            job_type="militia",
            creds_dir=None,
        )
        assert result.throttled is True
        assert db.is_throttled("work") is True

def test_job_recorded_in_db():
    with tempfile.TemporaryDirectory() as d:
        db = HotBunkDB(Path(d) / "test.db")
        runner = JobRunner(db)
        runner.run_job(
            command="echo done",
            account="personal",
            job_type="ci",
            creds_dir=None,
        )
        jobs = db.list_jobs()
        assert len(jobs) == 1
        assert jobs[0]["account"] == "personal"
        assert jobs[0]["status"] == "completed"
