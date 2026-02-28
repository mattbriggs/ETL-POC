"""Subprocess execution boundary.

:class:`SubprocessRunner` is the only place in the pipeline where
``subprocess`` is called. Injecting it into extractors makes them trivially
testable without spawning real processes.
"""

from __future__ import annotations

import subprocess
from typing import Protocol


class RunnerError(RuntimeError):
    """Raised when a subprocess exits with a non-zero return code.

    :param message: Combined stdout/stderr from the failed process.
    """


class Runner(Protocol):
    """Protocol for objects that can execute shell commands.

    Implementations must be stateless and thread-safe so they can be shared
    across a :class:`~concurrent.futures.ThreadPoolExecutor`.
    """

    def run(self, args: list[str], cwd: str | None = None) -> str:
        """Execute *args* and return combined output.

        :param args: Command and its arguments as a list of strings.
        :param cwd: Optional working directory.
        :returns: Combined stdout text.
        :raises RunnerError: If the process exits with a non-zero code.
        """
        ...


class SubprocessRunner:
    """Real subprocess runner that delegates to the operating system.

    :Example:

    .. code-block:: python

        runner = SubprocessRunner()
        output = runner.run(["pandoc", "--version"])
    """

    def run(self, args: list[str], cwd: str | None = None) -> str:
        """Execute *args* as a subprocess and return stdout.

        :param args: Command and arguments.
        :param cwd: Optional working directory for the child process.
        :returns: Captured stdout text.
        :raises RunnerError: If the process exits with a non-zero code.
        """
        try:
            result = subprocess.run(
                args,
                cwd=cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                check=True,
                text=True,
            )
            return result.stdout
        except subprocess.CalledProcessError as exc:
            raise RunnerError(exc.stdout or str(exc)) from exc


# Keep the old name as an alias so existing tests continue to work.
SubprocessError = RunnerError
