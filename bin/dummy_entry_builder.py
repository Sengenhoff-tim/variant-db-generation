from datetime import datetime
import random

TODAY = datetime.now().strftime("%d-%b-%Y").upper()

DUMMY_ENTRY = (
     'ID   {}              Unreviewed;         {} AA.\n'
     'AC   {};\n'
    f'DT   {TODAY}, integrated into DUMMY.\n'
    f'DT   {TODAY}, sequence version 1.\n'
    f'DT   {TODAY}, entry version 1.\n'
     'DE   dummy protein (DUMMY).\n'
     'OS   dummy organism (DUMMY).\n'
     'OC   Unclassified; dummy (DUMMY).\n'
     'OX   NCBI_TaxID=0; dummy (DUMMY).\n'
     'RN   [1]\n'
     'RP   SEQUENCE (DUMMY).\n'
     'RG   dummy group (DUMMY);\n'
     'RA   dummy authors (DUMMY);\n'
     'RL   Unpublished (DUMMY).\n'
     'PE   4: Predicted;\n'
     '{}'
     'SQ   SEQUENCE {} AA; 10000 MW; 1000000000000000 CRC64;\n'
     '{}\n'
     '//\n'
)

def format_sequence(seq: str) -> str:
    """
    Format sequence so each output line has 60 amino acids,
    grouped into 6 groups of 10 separated by a single space,
    and the sequence on each line begins at column 6 (i.e., there
    are 5 leading characters before the first residue).
    """
    seq = seq.replace('\n', '').replace(' ', '')
    lines = []
    i = 0
    leading = ' ' * 5
    while i < len(seq):
        chunk = seq[i:i+60]  # up to 60 aa per output line
        groups = [chunk[j:j+10] for j in range(0, len(chunk), 10)]
        line = leading + ' '.join(groups)
        lines.append(line)
        i += 60
    return '\n'.join(lines)


def build_dummy_entry(str_seq_id, aa_count, str_variant, str_sequence) -> str:
    return DUMMY_ENTRY.format(str_seq_id, aa_count, str_seq_id, str_variant, aa_count, format_sequence(str_sequence))