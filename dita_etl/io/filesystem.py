"""Filesystem utilities for the pipeline's imperative shell.

All functions in this module perform actual I/O. They are called only from
stage ``run()`` methods and the pipeline orchestrator — never from pure
transform functions.
"""

from __future__ import annotations

import glob
import hashlib
import os
import pathlib
import shutil


# ---------------------------------------------------------------------------
# Directory helpers
# ---------------------------------------------------------------------------


def ensure_dir(path: str) -> None:
    """Create *path* and all missing parents. No-op if it already exists.

    :param path: Directory path to create.
    """
    os.makedirs(path, exist_ok=True)


# ---------------------------------------------------------------------------
# File read / write
# ---------------------------------------------------------------------------


def read_text(path: str) -> str:
    """Read a text file, falling back to ``latin-1`` if it is not UTF-8.

    :param path: Path to the file.
    :returns: File contents as a string.
    :raises FileNotFoundError: If *path* does not exist.
    """
    try:
        with open(path, encoding="utf-8") as fh:
            return fh.read()
    except UnicodeDecodeError:
        with open(path, encoding="latin-1") as fh:
            return fh.read()


def write_text(path: str, content: str) -> None:
    """Write *content* to *path*, creating parent directories as needed.

    :param path: Destination file path.
    :param content: Text to write.
    """
    ensure_dir(os.path.dirname(path))
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(content)


# ---------------------------------------------------------------------------
# Hashing
# ---------------------------------------------------------------------------


def file_sha256(path: str) -> str:
    """Compute the SHA-256 digest of a file without loading it fully into memory.

    :param path: Path to the file.
    :returns: Hex-encoded SHA-256 digest string.
    """
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(8192), b""):
            digest.update(chunk)
    return digest.hexdigest()


def text_sha256(text: str) -> str:
    """Compute the SHA-256 digest of a UTF-8 string.

    :param text: Input string.
    :returns: Hex-encoded SHA-256 digest string.
    """
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def normalize_path(p: str) -> str:
    """Return the POSIX-style normalised absolute path for *p*.

    :param p: Any path string.
    :returns: Normalised POSIX path string.
    """
    return str(pathlib.Path(p).as_posix())


# ---------------------------------------------------------------------------
# Discovery
# ---------------------------------------------------------------------------


def discover_files(root: str, extensions: list[str]) -> list[str]:
    """Recursively discover files matching any of *extensions* under *root*.

    :param root: Directory to search.
    :param extensions: File extensions to match, each starting with a dot
        (e.g. ``[".md", ".html"]``).
    :returns: Sorted list of matching file paths.
    """
    found: list[str] = []
    for ext in extensions:
        pattern = os.path.join(root, f"**/*{ext}")
        found.extend(glob.glob(pattern, recursive=True))
    return sorted(p for p in found if os.path.isfile(p))


# ---------------------------------------------------------------------------
# Asset copying
# ---------------------------------------------------------------------------


def copy_assets(
    src_root: str,
    dst_root: str,
    asset_folders: tuple[str, ...] = ("styles", "images", "imagers"),
) -> None:
    """Copy asset directories from *src_root* into *dst_root*.

    Each folder in *asset_folders* is copied recursively. Missing source
    folders are silently skipped. Errors on individual items are logged to
    stderr rather than raised, to avoid aborting the pipeline over
    non-critical assets.

    :param src_root: Source directory that may contain asset sub-folders.
    :param dst_root: Destination directory to copy assets into.
    :param asset_folders: Names of sub-folders to look for and copy.
    """
    for folder in asset_folders:
        src_path = os.path.join(src_root, folder)
        dst_path = os.path.join(dst_root, folder)
        if not os.path.exists(src_path):
            continue
        ensure_dir(dst_path)
        for item in os.listdir(src_path):
            src_item = os.path.join(src_path, item)
            dst_item = os.path.join(dst_path, item)
            try:
                if os.path.isfile(src_item):
                    shutil.copy2(src_item, dst_item)
                elif os.path.isdir(src_item):
                    shutil.copytree(src_item, dst_item, dirs_exist_ok=True)
            except Exception as exc:  # noqa: BLE001
                import sys
                print(f"Warning: skipped asset {src_item}: {exc}", file=sys.stderr)
