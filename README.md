# nf-core-like/variant-db-generation

[![GitHub Actions CI Status](https://github.com/nf-core-like/variant-db-generation/actions/workflows/nf-test.yml/badge.svg)](https://github.com/nf-core-like/variant-db-generation/actions/workflows/nf-test.yml)
[![GitHub Actions Linting Status](https://github.com/nf-core-like/variant-db-generation/actions/workflows/linting.yml/badge.svg)](https://github.com/nf-core-like/variant-db-generation/actions/workflows/linting.yml)[![Cite with Zenodo](http://img.shields.io/badge/DOI-10.5281/zenodo.XXXXXXX-1073c8?labelColor=000000)](https://doi.org/10.5281/zenodo.XXXXXXX)
[![nf-test](https://img.shields.io/badge/unit_tests-nf--test-337ab7.svg)](https://www.nf-test.com)

[![Nextflow](https://img.shields.io/badge/version-%E2%89%A525.04.0-green?style=flat&logo=nextflow&logoColor=white&color=%230DC09D&link=https%3A%2F%2Fnextflow.io)](https://www.nextflow.io/)
[![nf-core template version](https://img.shields.io/badge/nf--core_template-3.5.2-green?style=flat&logo=nfcore&logoColor=white&color=%2324B064&link=https%3A%2F%2Fnf-co.re)](https://github.com/nf-core/tools/releases/tag/3.5.2)
[![run with conda](http://img.shields.io/badge/run%20with-conda-3EB049?labelColor=000000&logo=anaconda)](https://docs.conda.io/en/latest/)
[![run with docker](https://img.shields.io/badge/run%20with-docker-0db7ed?labelColor=000000&logo=docker)](https://www.docker.com/)
[![run with singularity](https://img.shields.io/badge/run%20with-singularity-1d355c.svg?labelColor=000000)](https://sylabs.io/docs/)
[![Launch on Seqera Platform](https://img.shields.io/badge/Launch%20%F0%9F%9A%80-Seqera%20Platform-%234256e7)](https://cloud.seqera.io/launch?pipeline=https://github.com/nf-core-like/variant-db-generation)

## Introduction

**nf-core-like/variant-db-generation** is a bioinformatics pipeline that generates sample-specific protein sequence databases. For each sample, it combines a UniProt reference with sample-specific amino-acid-affecting variants (from VCF) using [ProtGraph](https://github.com/mpc-bioinformatics/ProtGraph) to build a variant-aware protein graph, digests it in silico (e.g. tryptic or Glu-C digestion), and filters the resulting peptides by mass and number of variants/missed cleavages. The output is a FASTA-formatted peptide database tailored to each sample's genomic variants and corresponding mzML file, suitable for downstream peptide/spectrum matching.

<!-- TODO nf-core:
   Complete this sentence with a 2-3 sentence summary of what types of data the pipeline ingests, a brief overview of the
   major pipeline sections and the types of output it produces. You're giving an overview to someone new
   to nf-core here, in 15-20 seconds. For an example, see https://github.com/nf-core/rnaseq/blob/master/README.md#introduction
-->

<!-- TODO nf-core: Include a figure that guides the user through the major workflow steps. Many nf-core
     workflows use the "tube map" design for that. See https://nf-co.re/docs/guidelines/graphic_design/workflow_diagrams#examples for examples.   -->
<!-- TODO nf-core: Fill in short bullet-pointed list of the default steps in the pipeline -->

## Usage

## Requirements

- [Nextflow](https://www.nextflow.io/) (`>=25.04.0`)
- [Docker](https://www.docker.com/)
- Two custom Docker images, built locally via the provided build script:
  - `bpcsr_to_fasta:latest` — reads ProtGraph binary output and converts it to FASTA
  - `vcf_uniprot_merger:latest` — merges VCF-derived amino acid changes with UniProt entries
- A UniProt `.txt` or `.txt.gz` source file (see [`--uniprot_source_file`](#usage))

## Installation

1. Install Nextflow (see the [official installation guide](https://nf-co.re/docs/usage/installation)).

2. Install Docker, Singularity, or Conda.

3. Clone this repository:

```bash
   git clone https://github.com/nf-core-like/variant-db-generation.git
   cd variant-db-generation
```

4. Build the required custom Docker images using the provided script:

```bash
   bash setup.sh all
```

   You can also  build them directly with `docker build`:

```bash
   docker build --no-cache \
     -f bin/Docker/protgraph_output_reader.Dockerfile \
     -t bpcsr_to_fasta:latest \
     bin/Docker

   docker build --no-cache \
     -f bin/Docker/sp_embl_builder.Dockerfile \
     -t sp_embl_builder:latest \
     bin/Docker
```

5. TODO Test your setup with the test profile before running on real data:

```bash
   nextflow run nf-core-like/variant-db-generation -profile test,docker --outdir <OUTDIR>
```

## Usage

### Samplesheet

First, prepare a samplesheet with your input data. It must be a comma-separated file with a header row and the following four columns. At least one of "ranges" and "mzml" must be set:

`samplesheet.csv`:

```csv
sample,aa_changes,ranges,mzml
SAMPLE,/path/to/aa/change/file.vcf.gz,/path/to/range/file.csv,/path/to/mzml/file.mzml
```

| Column       | Description                                                                 |
| ------------ | ---------------------------------------------------------------------------- |
| `sample`     | A unique sample identifier without spaces.                                   |
| `aa_changes` | Path to a `.vcf` or `.vcf.gz` file describing amino-acid-affecting variants. TODO ADD DESCRIPTION  |
| `ranges`     | Path to a `.csv` file describing the ranges to consider.                 |
| `mzml`       | Path to a corresponding `.mzml` file.                           |

### Running the pipeline

```bash
nextflow run nf-core-like/variant-db-generation \
   -profile docker \
   --input samplesheet.csv \
   --outdir <OUTDIR> \
   --uniprot_source_file </path/to/uniprot.txt.gz>
```

### Key parameters

A full parameter reference is available via `--help_full`, or by inspecting [`nextflow_schema.json`](nextflow_schema.json). Commonly used parameters include:

- `--uniprot_source_file` — path to the UniProt `.txt`/`.txt.gz` source file (required).
- `--digestion` — digestion method: `gluc`, `trypsin`, `skip`, or `full` (default: `trypsin`).
- `--max_variants` — maximum variants per peptide (default: `3`); increasing this significantly raises compute cost.
- `--max_misscleavages` — maximum missed cleavages per peptide (default: `3`).
- `--min_da` / `--max_da` — minimum/maximum peptide mass in Da (defaults: `10` / `10000`).
- `--confirmed_only` — only include variants present in the input VCF.

Performance-tuning parameters for the bpcsr reader (e.g. `--bpcsr_reader_hash_bits`, `--bpcsr_reader_bin_size`, `--bpcsr_reader_job_splits`) have no effect on results and only need adjustment for large-scale or memory-constrained runs — see the schema descriptions for guidance.

> [!WARNING]
> Please provide pipeline parameters via the CLI or a Nextflow `-params-file`, not via custom config files.

> [!NOTE]
> If you are new to Nextflow and nf-core, please refer to [this page](https://nf-co.re/docs/usage/installation) on how to set-up Nextflow. Make sure to [test your setup](https://nf-co.re/docs/usage/introduction#how-to-run-a-pipeline) with `-profile test` before running the workflow on actual data.

<!-- TODO nf-core: Describe the minimum required steps to execute the pipeline, e.g. how to prepare samplesheets.
     Explain what rows and columns represent. For instance (please edit as appropriate):

First, prepare a samplesheet with your input data that looks as follows:

`samplesheet.csv`:

```csv
sample,fastq_1,fastq_2
CONTROL_REP1,AEG588A1_S1_L002_R1_001.fastq.gz,AEG588A1_S1_L002_R2_001.fastq.gz
```

Each row represents a fastq file (single-end) or a pair of fastq files (paired end).

-->

Now, you can run the pipeline using:


> [!WARNING]
> Please provide pipeline parameters via the CLI or Nextflow `-params-file` option. Custom config files including those provided by the `-c` Nextflow option can be used to provide any configuration _**except for parameters**_; see [docs](https://nf-co.re/docs/usage/getting_started/configuration#custom-configuration-files).

## Credits

nf-core-like/variant-db-generation was originally written by Tim Sengenhoff.

We thank the following people for their extensive assistance in the development of this pipeline:

<!-- TODO nf-core: If applicable, make list of people who have also contributed -->

## Contributions and Support

If you would like to contribute to this pipeline, please see the [contributing guidelines](.github/CONTRIBUTING.md).

## Citations

<!-- TODO nf-core: Add citation for pipeline after first release. Uncomment lines below and update Zenodo doi and badge at the top of this file. -->
<!-- If you use nf-core-like/variant-db-generation for your analysis, please cite it using the following doi: [10.5281/zenodo.XXXXXX](https://doi.org/10.5281/zenodo.XXXXXX) -->

<!-- TODO nf-core: Add bibliography of tools and data used in your pipeline -->

An extensive list of references for the tools used by the pipeline can be found in the [`CITATIONS.md`](CITATIONS.md) file.

This pipeline uses code and infrastructure developed and maintained by the [nf-core](https://nf-co.re) community, reused here under the [MIT license](https://github.com/nf-core/tools/blob/main/LICENSE).

> **The nf-core framework for community-curated bioinformatics pipelines.**
>
> Philip Ewels, Alexander Peltzer, Sven Fillinger, Harshil Patel, Johannes Alneberg, Andreas Wilm, Maxime Ulysse Garcia, Paolo Di Tommaso & Sven Nahnsen.
>
> _Nat Biotechnol._ 2020 Feb 13. doi: [10.1038/s41587-020-0439-x](https://dx.doi.org/10.1038/s41587-020-0439-x).
