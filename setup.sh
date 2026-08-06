#!/usr/bin/env bash
set -euo pipefail

build_reader() {
    docker build --no-cache \
        -f bin/Docker/protgraph_output_reader.Dockerfile \
        -t bpcsr_to_fasta:latest \
        bin/Docker
}

build_merger() {
    docker build --no-cache \
        -f bin/Docker/sp_embl_builder.Dockerfile \
        -t sp_embl_builder:latest \
        bin/Docker
}

case "${1:-all}" in
    reader)    build_reader ;;
    merger)    build_merger ;;
    all)       build_reader && build_merger ;;
    *)         echo "Usage: $0 [reader|merger|all]" && exit 1 ;;
esac