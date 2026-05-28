FROM rust:latest AS builder

WORKDIR /app

RUN git clone https://github.com/Sengenhoff-tim/vcf_uniprot_merger .

RUN cargo build --release

FROM debian:bookworm-slim

WORKDIR /work

RUN apt-get update && apt-get install -y ca-certificates procps && rm -rf /var/lib/apt/lists/*

COPY --from=builder /app/target/release/vcf_uniprot_merger /usr/local/bin/vcf_uniprot_merger