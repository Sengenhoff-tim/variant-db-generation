#!/usr/bin/env python3
import argparse
import sys
import re
from typing import Dict
from aa_dict_builder import build_aa_dict
from utilities import die, get_path

ENSEMBL_ID_LINE_PREFIX = 'DR   Ensembl;'
SQ_LINE_PREFIX = 'SQ'

REGEX_ENST = re.compile(r'^ENST\d{11}(?:\.\d+)?$')

def add_variants(insert_map: Dict[str, str]) -> None:
    insert = None
    out = sys.stdout
    for line in sys.stdin:
        if line.startswith(ENSEMBL_ID_LINE_PREFIX):
            tokens = line.split()
            parts_to_append = []
            for token in tokens:
                t = token.rstrip(';')
                if REGEX_ENST.match(t):
                    key = t.split('.', 1)[0]
                    val = insert_map.pop(key, None)
                    if val is not None:
                        parts_to_append.append(val)
            if parts_to_append:
                insert = (insert or "") + "".join(parts_to_append)
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