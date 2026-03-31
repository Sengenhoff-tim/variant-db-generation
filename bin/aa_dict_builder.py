import gzip
import io
import re
from typing import Dict, List
from pathlib import Path

STR_INFO = '##INFO='
STR_INFO_CSQ = 'ID=CSQ'
STR_FORMAT = 'Description='
STR_BODY_HEADER = '#CHROM'
STR_CSQ = 'CSQ='

STR_FEAT_TYPE_VALUE = 'Transcript'

STR_FEAT_TYPE = 'Feature_type'
STR_FEAT_NAME = 'Feature'
STR_PROTEIN_POSITION = 'Protein_position'
STR_AA_CHANGE_SINGLE = 'Amino_acids'
STR_AA_CHANGE_FRAMESHIFT = 'DownstreamProtein'

LIST_RELEVANT_FIELDS = [STR_FEAT_TYPE, STR_FEAT_NAME, STR_PROTEIN_POSITION, STR_AA_CHANGE_SINGLE, STR_AA_CHANGE_FRAMESHIFT]

STR_FT_VARIANT_LINE = 'FT   VARIANT         {}\n'
STR_FT_AA_CHANGE_LINE = 'FT                   /note="{} -> {}"\n'
STR_FT_EVIDENCE_LINE = 'FT                   /evidence="%"\n'

REGEX_HEADER_FORMAT = re.compile(r'Description="[^"]*?Format:\s*([^"]*?)"', re.IGNORECASE)
REGEX_AA_CHANGE = re.compile(r'([A-Z])/([A-Z]+)')


def ensure_file(path_str: str) -> Path:
    try:
        p = Path(path_str).expanduser().resolve()
    except Exception as e:
        raise ValueError(f'invalid path {path_str!r}: {e}') from e
    if not p.exists():
        raise FileNotFoundError(f'input file not found: {p}')
    if not p.is_file():
        raise IsADirectoryError(f'not a file: {p}')
    return p

def open_buffered(path: str, buffer_size: int = io.DEFAULT_BUFFER_SIZE, encoding: str='utf-8') -> io.TextIOWrapper:
    p = Path(path)
    if p.suffix == '.gz':
        raw = gzip.open(p, mode='rb')
    else:
        raw = open(p, 'rb')
    return io.TextIOWrapper(io.BufferedReader(raw, buffer_size=buffer_size), encoding)

def read_header(reader: io.TextIOWrapper) -> Dict[str, int]:
    field_map: List[str] = []
    info_found = False

    for line in reader:
        if line.startswith(STR_INFO):
            if STR_INFO_CSQ not in line:
                continue
            if info_found:
                raise ValueError('Malformed input file: Duplicate CSQ INFO header')

            m = REGEX_HEADER_FORMAT.search(line)
            if not m:
                raise ValueError('Malformed CSQ header: missing Format in Description')
            raw = m.group(1)
            field_map = [f.strip().strip('"') for f in raw.split('|')]
            info_found = True

        if line.startswith(STR_BODY_HEADER):
            break

    if not info_found:
        raise ValueError('Missing CSQ INFO header with Format specification')

    index_map: Dict[str, int] = {}
    for idx, field in enumerate(field_map):
        if field in LIST_RELEVANT_FIELDS:
            index_map[field] = idx

    missing = [f for f in LIST_RELEVANT_FIELDS if f not in index_map]
    if missing:
        raise ValueError(f"Missing field(s) in CSQ Format: {', '.join(missing)}")

    return index_map

def read_body(reader: io.TextIOWrapper, indexes: Dict[str, int]) -> Dict[str, List[str]]:
    aa_changes: Dict[str, List[str]] = {}
    for line in reader:
        line = line.rstrip('\n')
        if not line or line.startswith('#'):
            continue

        cols = line.split('\t')
        if len(cols) <= 7:
            continue

        info_field = cols[7]
        csq_pos = info_field.find(STR_CSQ)
        if csq_pos == -1:
            continue
        csq_index = csq_pos + len(STR_CSQ)
        csq_value = info_field[csq_index:]
        if not csq_value:
            continue

        line_variants = csq_value.split(',')
        for variant in line_variants:
            variant_fields = variant.split('|')
            add_variant_entry(aa_changes, variant_fields, indexes)
    return aa_changes


def add_variant_entry(aa_dict: Dict[str, List[str]], variant_fields: List[str], field_indexes: Dict[str, int]) -> None:
    feat_type_idx = field_indexes.get(STR_FEAT_TYPE)
    if feat_type_idx is None:
        return

    if variant_fields[feat_type_idx] != STR_FEAT_TYPE_VALUE:
        return

    aa_change_idx = field_indexes.get(STR_AA_CHANGE_SINGLE)
    frameshift_idx = field_indexes.get(STR_AA_CHANGE_FRAMESHIFT)
    pos_idx = field_indexes.get(STR_PROTEIN_POSITION)
    name_idx = field_indexes.get(STR_FEAT_NAME)
        

    try:
        aa_change = re.match(REGEX_AA_CHANGE, variant_fields[aa_change_idx])
        if aa_change:
            aa_old = aa_change.group(1)
            aa_new = variant_fields[frameshift_idx] if variant_fields[frameshift_idx] != '' else aa_change.group(2)
            position = variant_fields[pos_idx]
            feat_name = variant_fields[name_idx]
    

            line1 = STR_FT_VARIANT_LINE.format(position)
            line2 = STR_FT_AA_CHANGE_LINE.format(aa_old, aa_new)
            line3 = STR_FT_EVIDENCE_LINE

            if feat_name not in aa_dict:
                aa_dict[feat_name] = []

            aa_dict[feat_name].append(line1 + line2 + line3)
    except (TypeError, IndexError):
        return

def build_aa_dict(vcf_file) -> Dict[str, List[str]]:
    ensure_file(vcf_file)
    with open_buffered(vcf_file) as vcf_reader:
        field_indexes = read_header(vcf_reader)
        aa_mapping = read_body(vcf_reader, field_indexes)
    return aa_mapping