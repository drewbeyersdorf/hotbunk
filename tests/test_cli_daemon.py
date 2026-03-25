from click.testing import CliRunner
from hotbunk.cli import main

def test_daemon_help():
    runner = CliRunner()
    result = runner.invoke(main, ["daemon", "--help"])
    assert result.exit_code == 0
    assert "daemon" in result.output.lower()

def test_queue_help():
    runner = CliRunner()
    result = runner.invoke(main, ["queue", "--help"])
    assert result.exit_code == 0

def test_queue_add_help():
    runner = CliRunner()
    result = runner.invoke(main, ["queue", "add", "--help"])
    assert result.exit_code == 0
