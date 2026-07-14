#!/usr/bin/env bash
set -euo pipefail

build_protgraph() {
    docker build --no-cache \
        -f bin/Docker/protgraph_output_reader.Dockerfile \
        -t bpcsr_to_fasta:latest \
        bin/Docker
}

build_merger() {
    docker build --no-cache \
        -f bin/Docker/vcf_uniprot_merger.Dockerfile \
        -t vcf_uniprot_merger:latest \
        bin/Docker
}

case "${1:-all}" in
    protgraph) build_protgraph ;;
    merger)    build_merger ;;
    all)       build_protgraph && build_merger ;;
    *)         echo "Usage: $0 [protgraph|merger|all]" && exit 1 ;;
esac