"""Unit tests for dita_etl.io.filesystem."""

from pathlib import Path

import pytest

from dita_etl.io.filesystem import (
    copy_assets,
    discover_files,
    ensure_dir,
    file_sha256,
    normalize_path,
    read_text,
    text_sha256,
    write_text,
)


class TestEnsureDir:
    def test_creates_directory(self, tmp_path):
        d = str(tmp_path / "new" / "nested")
        ensure_dir(d)
        assert Path(d).is_dir()

    def test_noop_if_exists(self, tmp_path):
        ensure_dir(str(tmp_path))  # already exists — should not raise


class TestReadText:
    def test_reads_utf8(self, tmp_path):
        f = tmp_path / "utf8.txt"
        f.write_text("café", encoding="utf-8")
        assert read_text(str(f)) == "café"

    def test_latin1_fallback(self, tmp_path):
        f = tmp_path / "latin1.txt"
        f.write_bytes("café".encode("latin-1"))
        result = read_text(str(f))
        assert "caf" in result  # content is present (encoding may differ)

    def test_missing_file_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            read_text(str(tmp_path / "missing.txt"))


class TestWriteText:
    def test_creates_file(self, tmp_path):
        p = str(tmp_path / "sub" / "out.txt")
        write_text(p, "hello")
        assert Path(p).read_text(encoding="utf-8") == "hello"

    def test_creates_parent_dirs(self, tmp_path):
        p = str(tmp_path / "a" / "b" / "c.txt")
        write_text(p, "content")
        assert Path(p).exists()


class TestHashing:
    def test_file_sha256_consistent(self, tmp_path):
        f = tmp_path / "hash.txt"
        f.write_text("hello", encoding="utf-8")
        h1 = file_sha256(str(f))
        h2 = file_sha256(str(f))
        assert h1 == h2
        assert len(h1) == 64

    def test_text_sha256_consistent(self):
        h = text_sha256("hello world")
        assert h == text_sha256("hello world")
        assert len(h) == 64

    def test_text_sha256_different_inputs(self):
        assert text_sha256("a") != text_sha256("b")


class TestNormalizePath:
    def test_returns_posix_string(self):
        result = normalize_path("/a/b/c.txt")
        assert "/" in result

    def test_returns_string_type(self):
        # normalize_path converts to POSIX notation; it does not resolve symlinks
        result = normalize_path("/a/b/c.txt")
        assert isinstance(result, str)


class TestDiscoverFiles:
    def test_finds_matching_extensions(self, tmp_path):
        (tmp_path / "a.md").write_text("# A")
        (tmp_path / "b.html").write_text("<h1>B</h1>")
        (tmp_path / "c.txt").write_text("skip")
        found = discover_files(str(tmp_path), [".md", ".html"])
        assert len(found) == 2
        assert all(f.endswith((".md", ".html")) for f in found)

    def test_recurses_into_subdirectories(self, tmp_path):
        sub = tmp_path / "sub"
        sub.mkdir()
        (sub / "doc.md").write_text("# Doc")
        found = discover_files(str(tmp_path), [".md"])
        assert len(found) == 1

    def test_returns_sorted_list(self, tmp_path):
        (tmp_path / "b.md").write_text("b")
        (tmp_path / "a.md").write_text("a")
        found = discover_files(str(tmp_path), [".md"])
        assert found == sorted(found)

    def test_empty_root_returns_empty(self, tmp_path):
        assert discover_files(str(tmp_path), [".md"]) == []


class TestCopyAssets:
    def test_copies_images_folder(self, tmp_path):
        src = tmp_path / "src"
        images = src / "images"
        images.mkdir(parents=True)
        (images / "logo.png").write_bytes(b"PNG")
        dst = str(tmp_path / "dst")
        copy_assets(str(src), dst, asset_folders=("images",))
        assert (Path(dst) / "images" / "logo.png").exists()

    def test_missing_folder_silently_skipped(self, tmp_path):
        src = tmp_path / "src"
        src.mkdir()
        dst = str(tmp_path / "dst")
        copy_assets(str(src), dst, asset_folders=("images",))
        # No error and dst/images not created
        assert not (Path(dst) / "images").exists()

    def test_copies_subdirectory(self, tmp_path):
        src = tmp_path / "src"
        styles = src / "styles" / "sub"
        styles.mkdir(parents=True)
        (styles / "main.css").write_text("body {}")
        dst = str(tmp_path / "dst")
        copy_assets(str(src), dst, asset_folders=("styles",))
        assert (Path(dst) / "styles" / "sub" / "main.css").exists()
