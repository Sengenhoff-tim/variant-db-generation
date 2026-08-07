    #!/usr/bin/env python3
    """
    Extract MS2 precursor neutral masses from an mzML file and write a CSV
    with a ppm-based [lower, upper] mass window for each one.
    Usage:
        extract_masses.py [-i INPUT] [-o OUTPUT] [-p PPM]
    By default reads mzML from stdin and writes CSV to stdout, so it can be
    used in a pipeline, e.g.:
        cat spectra.mzML | extract_masses.py -p 10 > masses.csv
        extract_masses.py -i spectra.mzML -o masses.csv -p 10
    Output is appended to OUTPUT if it already exists.
    """
    import argparse
    import csv
    import io
    import os
    import sys
    from pathlib import Path
    from pyteomics import mzml as pmzml

    PROTON_MASS = 1.007276466621


    def mz_to_da(mz, charge):
        return mz * charge - PROTON_MASS * charge


    def ppm_window(value, ppm):
        delta = value * ppm * 1e-6
        return value - delta, value + delta


    def parse_args():
        parser = argparse.ArgumentParser(
            description="Extract MS2 precursor neutral masses (as ppm windows) from an mzML file."
        )
        parser.add_argument(
            "-i", "--input",
            type=str,
            default="-",
            help="Input mzML file path. Defaults to stdin ('-').",
        )
        parser.add_argument(
            "-o", "--output",
            type=str,
            default="-",
            help="Output CSV file path. Appended to if it exists. Defaults to stdout ('-').",
        )
        parser.add_argument(
            "-p", "--ppm",
            type=float,
            required=True,
            help="Mass tolerance window in parts-per-million (ppm). Must be positive.",
        )
        args = parser.parse_args()
        if args.ppm <= 0:
            parser.error(f"--ppm must be a positive number, got {args.ppm}")
        return args


    def main():
        args = parse_args()

        if args.input == "-":
            in_handle = io.BytesIO(sys.stdin.buffer.read())
        else:
            in_path = Path(args.input)
            if not in_path.exists():
                sys.exit(f"Error: input file not found: {in_path}")
            in_handle = str(in_path)

        if args.output == "-":
            out_handle = sys.stdout
            write_header = True
        else:
            write_header = not (os.path.exists(args.output) and os.path.getsize(args.output) > 0)
            out_handle = open(args.output, "a", newline="")

        n_written = 0
        try:
            writer = csv.writer(out_handle)
            if write_header:
                writer.writerow(["lower", "upper"])
            with pmzml.read(in_handle) as reader:
                for spectrum in reader:
                    if spectrum.get("ms level") != 2:
                        continue
                    for precursor in spectrum.get("precursorList", {}).get("precursor", []):
                        for ion in precursor.get("selectedIonList", {}).get("selectedIon", []):
                            mz = ion.get("selected ion m/z")
                            charge = ion.get("charge state")
                            if mz is None or charge is None:
                                continue
                            da = mz_to_da(mz, charge)
                            lower, upper = ppm_window(da, args.ppm)
                            writer.writerow([lower, upper])
                            n_written += 1
        finally:
            if out_handle is not sys.stdout:
                out_handle.close()

        print(f"Wrote {n_written} rows to {args.output}", file=sys.stderr)


    if __name__ == "__main__":
        main()