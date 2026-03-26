import gzip
import io
import sys
import re
from typing import Dict
from pathlib import Path


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

def open_buffered(path: str, buffer_size: int = io.DEFAULT_BUFFER_SIZE, encoding: str='utf-8') -> io.BufferedReader:
    if path == '-':
        return sys.stdin.buffer
    p = Path(path)
    if p.suffix == '.gz':
        raw = gzip.open(p, mode='rb')
    else:
        raw = open(p, 'rb')
    return io.TextIOWrapper(io.BufferedReader(raw, buffer_size=buffer_size), encoding)

def read_id_map(id_mapping_file: str, buffer_size: int, encoding: str) -> Dict[str, str]:
    reader = open_buffered(id_mapping_file, buffer_size, encoding)
    id_map: Dict[str, str] = {}
    for line in reader:
        fields = line.split()
        id_map[fields[0]] = fields[1]
    return id_map

def map_aas(aa_file: Path, id_map: Dict[str, str], buffer_size: int, encoding: str) -> Dict[str, str]:
    reader = open_buffered(aa_file, buffer_size, encoding)
    data: Dict[str, str] = {}
    start_char_id = '>'
    start_char_aa_change = 'amino_acid_change:'
    lines_processed = 0
    
    for line in reader:
        
        lines_processed += 1

        if lines_processed % 6 == 1:
            if line.startswith(start_char_id):
                key = line[1:].strip()
                entry_id = id_map.get(key)
                if entry_id is None:
                    raise KeyError(f"{id_map}:{lines_processed}: unknown id '{key}'")
            else:
                raise ValueError(f"{id_map}:{lines_processed}: expected '{start_char_id}'")
        elif lines_processed % 6 == 4:
            if line.startswith(start_char_aa_change):
                parts = line.split(':', 1)
                if not parts[1].strip():
                    raise ValueError(f"{id_map}:{lines_processed}: malformed '{start_char_aa_change}'")
                amino_acid_change = parts[1].strip()
                data[entry_id] = process_amino_acid_change(amino_acid_change)
            else:
                raise ValueError(f"{id_map}:{lines_processed}: expected '{start_char_aa_change}'")
    return data

def process_amino_acid_change(aa_change: str) -> str:
    changes = aa_change.split('; ')
    aa_formatted = []
    for change in changes:
        change = change.strip()
        if not change.startswith("no amino acid change"):
            match = re.match(r'^(\d+)([A-Z])>(\d*)([A-Z])$', change)
            if match:
                pos1, aa1, pos2, aa2 = match.groups()
                line1 = f"FT   VARIANT         {pos1}\n"
                line2 = f'FT                   /note="{aa1} -> {aa2} INSERTED"\n'
                line3 = 'FT                   /evidence="INSERTED"\n'
                aa_formatted.extend([line1, line2, line3])
            else:
                raise ValueError(f"Unexpected amino-acid-change format: {change!r} in {aa_change!r}")
    return "".join(aa_formatted)

def file_reader(aa_file: Path, id_mapping_file: str) -> Dict[str, str]:
    ensure_file(id_mapping_file)
    id_map = read_id_map(id_mapping_file, buffer_size=io.DEFAULT_BUFFER_SIZE, encoding='utf-8')
    aa_dict = map_aas(aa_file, id_map, buffer_size=io.DEFAULT_BUFFER_SIZE, encoding='utf-8')
    return aa_dict