
from __future__ import annotations
import subprocess
from typing import List

class SubprocessError(RuntimeError):
    pass

class SubprocessRunner:
    def run(self, args: List[str], cwd: str | None = None) -> str:
        try:
            res = subprocess.run(args, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=True, text=True)
            return res.stdout
        except subprocess.CalledProcessError as e:
            raise SubprocessError(e.stdout) from e
