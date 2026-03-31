#!/usr/bin/env python3
import argparse
import sys
from typing import Dict
from aa_dict_builder import build_aa_dict
from utilities import die, ensure_file

ENSEMBL_ID = 'DR   Ensembl;'
SQ_LINE_PREFIX = 'SQ'

def build_file(insert_map: Dict[str, str]) -> None:
    insert = None
    out = sys.stdout
    for line in sys.stdin:
        if insert is None:
            out.write(line)
            if line.startswith(ENSEMBL_ID):
                parts = line.split()
                if len(parts) >= 2:
                    key = parts[1].rstrip(';')
                    insert = insert_map.get(key)
        else:
            if line.startswith(SQ_LINE_PREFIX):
                if insert is not None:
                    out.write(insert)
                out.write(line)
                insert = None
            else:
                out.write(line)

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--aa_changes_file', '-i', default='', help='path to aa changes file (vcf)')
    args = parser.parse_args()

    aa_filename = args.aa_changes_file
    try:
        ensure_file(aa_filename)
    except Exception as e:
        die(str(e))

    try:
        insert_map = build_aa_dict(aa_filename)
    except Exception as e:
        die(str(e))
    try:
        build_file(insert_map)
    except Exception as e:
        die(f"Runtime error while building file: {e}")

if __name__ == "__main__":
    main()
