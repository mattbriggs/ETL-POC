
from __future__ import annotations
import os, shutil
from typing import Tuple

def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)

def write_text(path: str, content: str) -> None:
    ensure_dir(os.path.dirname(path))
    with open(path, "w") as f:
        f.write(content)

def read_text(path: str) -> str:
    with open(path, "r") as f:
        return f.read()

def quarantine(src_path: str, quarantine_dir: str) -> str:
    ensure_dir(quarantine_dir)
    base = os.path.basename(src_path)
    dst = os.path.join(quarantine_dir, base)
    shutil.copy2(src_path, dst)
    return dst

def copy_into(src_path: str, dst_dir: str) -> str:
    ensure_dir(dst_dir)
    dst = os.path.join(dst_dir, os.path.basename(src_path))
    shutil.copy2(src_path, dst)
    return dst
