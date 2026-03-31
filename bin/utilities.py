import gzip
from pathlib import Path
import io
import sys

def ensure_file(path_str: str) -> Path:
    try:
        p = Path(path_str).expanduser().resolve()
    except Exception as e:
        raise ValueError(f"invalid path {path_str!r}: {e}") from e
    if not p.exists():
        raise FileNotFoundError(f"input file not found: {p}")
    if not p.is_file():
        raise IsADirectoryError(f"not a file: {p}")
    return p

def open_buffered(path: str, buffer_size: int = io.DEFAULT_BUFFER_SIZE, encoding: str='utf-8') -> io.TextIOWrapper:
    p = Path(path)
    if p.suffix == '.gz':
        raw = gzip.open(p, mode='rb')
    else:
        raw = open(p, 'rb')
    return io.TextIOWrapper(io.BufferedReader(raw, buffer_size=buffer_size), encoding)

def die(message: str) -> None:
    sys.stderr.write(message.rstrip() + "\n")
    sys.stderr.flush()
    sys.exit(1)