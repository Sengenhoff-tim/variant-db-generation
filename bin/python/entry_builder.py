#!/usr/bin/env python3
import argparse
import sys
import re
from typing import Dict, List

from aa_dict_builder import build_aa_dict
from utilities import die, get_path
from dummy_entry_builder import build_dummy_entry
from ensembl_sequence_getter import get_sequences_by_batch

ENSEMBL_ID_LINE_PREFIX = 'DR   Ensembl;'
SQ_LINE_PREFIX = 'SQ'
FT_LINE_PREFIX = 'FT'
FT_VARIANT_LINE_PREFIX = 'FT   VARIANT         '

REGEX_ENSP = re.compile(r'^ENSP\d{11}(?:\.\d+)?$')
REGEX_AA_CHANGE = re.compile(r'\b[A-Z]+ -> [A-Z]+\b')

STR_VARIANT_ENTRY = (
    'FT   VARIANT         {variant_pos_str}\n'
    'FT                   /note="{variant_aa_change}"\n'
    'FT                   /evidence="INSERTED"\n'
)

def _normalize_seq_key(t: str) -> str:
    # remove version suffix from Ensembl transcript ID (ENSTxxxxx.##)
    return t.split('.', 1)[0]

def add_variants(insert_map: Dict[str, Dict[str, List[str]]]) -> None:
    """
    Read lines from sys.stdin and write modified lines to sys.stdout,
    inserting or adjusting variant entries based on insert_map.

    insert_map keys should be transcript IDs without the version suffix (e.g., 'ENST00000'),
    values are dicts mapping variant position (as string) -> list of variant change strings (e.g., ['A->T', 'AAA->TTT']).
    """
    out = sys.stdout
    insert = None
    variant_pos = None

    for line in sys.stdin:

        # ENSEMBL ID line: find transcript key, set insert for this record
        if line.startswith(ENSEMBL_ID_LINE_PREFIX):
            tokens = line.split()
            for token in tokens:
                t = token.rstrip(';')
                if REGEX_ENSP.match(t):
                    ensembl_key = _normalize_seq_key(t)
                    entry = insert_map.get(ensembl_key)
                    if entry:
                        # merge lists for matching positions
                        insert = {}
                        for pos, changes in entry.items():
                            if pos in insert:
                                insert[pos].extend(changes)
                            else:
                                insert[pos] = changes
            out.write(line)
            continue

        # FT variant header line: parse variant position
        if insert is not None and line.startswith(FT_VARIANT_LINE_PREFIX):
            sub = line[len(FT_VARIANT_LINE_PREFIX):].lstrip()
            m = re.match(r"(\d+)", sub)
            if not m:
                raise ValueError(f"Malformed variant entry: {line.rstrip()}")
            variant_pos = m.group(1) 
            out.write(line)
            continue

        # Feature lines that may contain AA-change annotations (process only when we flagged a position)
        if variant_pos is not None and line.startswith(FT_LINE_PREFIX):
            aa_changes = re.findall(REGEX_AA_CHANGE, line)
            if aa_changes:
                lst = insert.get(variant_pos, [])
                for aa in aa_changes:
                    if aa in lst:
                        lst.remove(aa)
                if not lst and variant_pos in insert:
                    del insert[variant_pos]
                else:
                    insert[variant_pos] = lst
            variant_pos = None
            out.write(line)
            continue

        # Sequence (SQ) line: before writing it, if we have pending insert entries for this record, output them
        if insert is not None and line.startswith(SQ_LINE_PREFIX):
            for var_pos in insert.keys():
                changes = insert.get(var_pos, [])
                for aa_change in changes:
                    out.write(STR_VARIANT_ENTRY.format(variant_pos_str=var_pos, variant_aa_change=aa_change))
            out.write(line)
            # reset record-specific state
            insert = None
            continue

        # Default: write unchanged
        out.write(line)

    # After stdin exhausted: for any remaining sequences in insert_map that weren't found in input,
    # fetch sequences by batch and write dummy entries.
    remaining_keys = list(insert_map.keys())
    if remaining_keys:
        
        for batch_results in get_sequences_by_batch(remaining_keys):
            
            for seq_id, seq in batch_results.items():
                if seq is None:
                    continue
                #TODO handle missing seq?
                variant_insert = ""
                for var_pos, change_list in insert_map.get(seq_id, {}).items():
                    for aa_change in change_list:
                        variant_insert += STR_VARIANT_ENTRY.format(variant_pos_str = var_pos, variant_aa_change=aa_change)
                
                out.write(build_dummy_entry(seq_id, len(seq), variant_insert, seq))

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--aa_changes_file', '-i', default='', help='path to aa changes file (vcf)')
    args = parser.parse_args()

    aa_filename = args.aa_changes_file
    try:
        get_path(aa_filename)
    except Exception as e:
        die(str(e))

    try:
        insert_map = build_aa_dict(aa_filename)

    except Exception as e:
        die(str(e))
    try:
        add_variants(insert_map)
    except Exception as e:
        die(f"Runtime error while building file: {e}")

if __name__ == "__main__":
    main()