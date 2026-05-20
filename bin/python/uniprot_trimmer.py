#!/usr/bin/env python3
import sys

KEEP = {'ID', 'AC', 'FT', 'SQ', '  ', 'DT', 'PE'}
KEEP_DR = 'DR   Ensembl'
ENTRY_END = '//'

TRUNC = {
    'DE': '   Truncated protein (TRUNC).\n',
    'OS': '   Truncated organism (TRUNC).\n',
    'OC': '   Unclassified; truncated (TRUNC).\n',
    'OX': '   NCBI_TaxID=0; truncated (TRUNC).\n',
    'RN': '   [1]\n',
    'RP': '   SEQUENCE (TRUNC).\n',
    'RG': '   Truncated group (TRUNC);\n',
    'RA': '   Truncated authors (TRUNC);\n',
    'RL': '   Unpublished (TRUNC).\n',
}

def trim() -> None:
    out = sys.stdout.write
    trunc_seen = set()

    for line in sys.stdin:
        if line.startswith(KEEP_DR):
            out(line)
            continue

        code = line[:2]

        if code == ENTRY_END:
            trunc_seen.clear()
            out(line)
            continue

        if code in KEEP:
            out(line)
            continue

        if code in TRUNC and code not in trunc_seen:
            out(code + TRUNC[code])
            trunc_seen.add(code)

def main() -> None:
    try:
        trim()
    except Exception as e:
        sys.stderr.write(f"Error: {e}\n")
        sys.exit(1)

if __name__ == "__main__":
    main()