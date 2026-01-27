import pytest
from n8n_factory.verify.runner import VerificationRunner

def test_runner_success():
    runner = VerificationRunner({})
    # Use 'dir' on windows, 'ls' on linux/mac. Assuming windows environment from context.
    # Actually python print is safer cross-platform test command
    res = runner.run_shell("python -c \"print('hello')\"")
    assert res["success"] is True
    assert "hello" in res["stdout"]

def test_runner_fail():
    runner = VerificationRunner({})
    res = runner.run_shell("python -c \"import sys; sys.exit(1)\"")
    assert res["success"] is False
    assert res["exit_code"] == 1

def test_runner_timeout():
    runner = VerificationRunner({}, timeout=1)
    # Sleep for 2 seconds
    res = runner.run_shell("python -c \"import time; time.sleep(2)\"")
    assert res["success"] is False
    assert "timed out" in res["stderr"]
