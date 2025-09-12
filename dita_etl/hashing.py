
import hashlib, pathlib

def file_sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def text_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def normalize_path(p: str) -> str:
    return str(pathlib.Path(p).as_posix())
