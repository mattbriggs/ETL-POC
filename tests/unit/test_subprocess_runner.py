"""Unit tests for dita_etl.io.subprocess_runner."""

import subprocess
from unittest.mock import MagicMock

import pytest

from dita_etl.io.subprocess_runner import RunnerError, SubprocessRunner


class TestSubprocessRunner:
    def test_successful_run_returns_stdout(self, monkeypatch):
        mock_result = MagicMock()
        mock_result.stdout = "pandoc 3.1\n"
        monkeypatch.setattr(subprocess, "run", lambda *a, **kw: mock_result)
        runner = SubprocessRunner()
        assert runner.run(["pandoc", "--version"]) == "pandoc 3.1\n"

    def test_failure_raises_runner_error(self, monkeypatch):
        exc = subprocess.CalledProcessError(1, ["false"], output="error text")
        monkeypatch.setattr(subprocess, "run", MagicMock(side_effect=exc))
        runner = SubprocessRunner()
        with pytest.raises(RunnerError):
            runner.run(["false"])

    def test_runner_error_contains_output(self, monkeypatch):
        exc = subprocess.CalledProcessError(1, ["cmd"], output="something went wrong")
        monkeypatch.setattr(subprocess, "run", MagicMock(side_effect=exc))
        runner = SubprocessRunner()
        with pytest.raises(RunnerError, match="something went wrong"):
            runner.run(["cmd"])

    def test_subprocess_error_alias(self):
        from dita_etl.io.subprocess_runner import SubprocessError
        assert SubprocessError is RunnerError
