#!/usr/bin/env python3
import argparse
import sys
import importlib
import os
import json
from typing import Callable, Dict, Any
from pathlib import Path

def build_file(insert_map: Dict[str, str]) -> None:
    insert = None
    out = sys.stdout
    for line in sys.stdin:
        if insert is None:
            out.write(line)
            if line.startswith('AC'):
                parts = line.split()
                if len(parts) >= 2:
                    key = parts[1].rstrip(';')
                    insert = insert_map.get(key)
        else:
            if line.startswith('SQ'):
                if insert is not None:
                    out.write(insert)
                out.write(line)
                insert = None
            else:
                out.write(line)
    
def parse_input_file(input_filename: str, input_reader_function: Callable[..., Dict[str, str]], *args: Any) -> Dict[str, str]:
    insert_mapping = input_reader_function(input_filename, *args)
    if not isinstance(insert_mapping, dict):
        raise Exception(f"{input_reader_function} must return a dict")
    return insert_mapping

def resolve_callable(func_spec: str) -> Callable[..., Any]:
    if not func_spec:
        raise Exception("empty function spec")

    if ':' in func_spec:
        path, fn_name = func_spec.rsplit(':', 1)
    else:
        path, fn_name = func_spec.rsplit('.', 1)

    path = os.path.abspath(path)
    if not os.path.isfile(path):
        raise Exception(f"file not found: {path!r}")

    module_name = f"_dynamic_module_{abs(hash(path))}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise Exception(f"could not load spec for {path!r}")

    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception as e:
        raise Exception(f"failed to execute module {path!r}: {e}") from e

    try:
        return getattr(module, fn_name)
    except AttributeError:
        raise Exception(f"module loaded from {path!r} has no attribute {fn_name!r}")

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

def die(message: str) -> None:
    sys.stderr.write(message.rstrip() + "\n")
    sys.stderr.flush()
    sys.exit(1)

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--aa_changes_file', '-i', default='', help='path to aa changes file')
    parser.add_argument(
        '--aa_change_func', '-f',
        required=True,
        metavar='FILE:FUNC',
        help='function to call, e.g. /full/path/to/test.py:tesstfunc (or dir/subdir/test.py.tesstfunc)'
        )

    parser.add_argument('--aa_change_fargs', '-a', default='[]', help='JSON list of positional arguments')
    args = parser.parse_args()

    try:
        fn = resolve_callable(args.aa_change_func)
    except Exception as e:
        die(f"failed to resolve function: {e}")

    try:
        pos_args = json.loads(args.aa_change_fargs)
    except json.JSONDecodeError as e:
        die(f"failed to parse --aa_change_fargs as JSON: {e}")

    aa_filename = args.aa_changes_file
    try:
        ensure_file(aa_filename)
    except Exception as e:
        die(str(e))

    try:
        insert_map = parse_input_file(aa_filename, fn, *pos_args)
    except Exception as e:
        die(str(e))
    try:
        build_file(insert_map)
    except Exception as e:
        die(f"Runtime error while building file: {e}")

if __name__ == "__main__":
    main()
