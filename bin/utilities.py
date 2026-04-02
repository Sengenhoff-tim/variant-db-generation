import gzip
from pathlib import Path
import io
import sys

def get_path(path_str: str) -> Path:
    try:
        p = Path(path_str).expanduser().resolve()
    except Exception as e:
        raise ValueError(f"invalid path {path_str!r}: {e}") from e
    if not p.exists():
        raise FileNotFoundError(f"input file not found: {p}")
    if not p.is_file():
        raise IsADirectoryError(f"not a file: {p}")
    return p

def open_buffered(path: str, encoding: str = 'utf-8') -> io.TextIOBase:
    p = Path(path)
    if p.suffix == '.gz':
        return gzip.open(p, mode='rt', encoding=encoding)
    else:
        return open(p, mode='rt', encoding=encoding)

def die(message: str) -> None:
    sys.stderr.write(message.rstrip() + "\n")
    sys.stderr.flush()
    sys.exit(1)