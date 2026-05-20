import crcmod

from datetime import datetime
from Bio.SeqUtils.ProtParam import ProteinAnalysis

#TODO validate which Uniprot fields are truly nessesary. mono weight and crc64 appear to change the order of the output. Further validation is required

TODAY = datetime.now().strftime("%d-%b-%Y").upper()
VALID = set("ACDEFGHIKLMNPQRSTVWY")
POLY = 0x1000000000000001B

get_crc64 = crcmod.mkCrcFun(POLY, initCrc=0, rev=False, xorOut=0)

DUMMY_ENTRY = (
     'ID   {dummy_ident}              Unreviewed;         {aa_count_head} AA.\n'
     'AC   {dummy_accession};\n'
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
     '{variants}'
     'SQ   SEQUENCE {aa_count_seq} AA; {mono_weight} MW; {crc64} CRC64;\n'
     '{aa_seq}\n'
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

def build_dummy_entry(str_seq_id: str, aa_count: int, str_variant: str, str_sequence: str) -> str:
    if not set(str_sequence).issubset(VALID):
        raise ValueError("Invalid amino acids in sequence")
    return DUMMY_ENTRY.format(
        dummy_ident = str_seq_id,
        aa_count_head = aa_count, 
        dummy_accession = str_seq_id, 
        variants = str_variant, 
        aa_count_seq = aa_count, 
        mono_weight = int(ProteinAnalysis(str_sequence).molecular_weight()),
        #mono_weight = 10000,
        crc64 = f"{get_crc64(str_sequence.encode()):016X}",
        #crc64 = 1000000000000000,
        aa_seq = format_sequence(str_sequence)
        )