#!/usr/bin/env nextflow
/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    nf-core-like/variant-db-generation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    Github : https://github.com/nf-core-like/variant-db-generation
----------------------------------------------------------------------------------------
*/

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    IMPORT FUNCTIONS / MODULES / SUBWORKFLOWS / WORKFLOWS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

include { VARIANT_DB_GENERATION  } from './workflows/variant-db-generation'
include { PIPELINE_INITIALISATION } from './subworkflows/local/utils_nfcore_variant-db-generation_pipeline'
include { PIPELINE_COMPLETION     } from './subworkflows/local/utils_nfcore_variant-db-generation_pipeline'
/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    NAMED WORKFLOWS FOR PIPELINE
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

//
// WORKFLOW: Run main analysis pipeline depending on type of input
//
workflow NFCORELIKE_VARIANT_DB_GENERATION {

    take:
    aa_changes // channel: samplesheet read in from --input
    mzml
    params_database
    params_merger_fetch
    params_protgraph
    params_bpcsr_reader

    main:

    //
    // WORKFLOW: Run pipeline
    //
    VARIANT_DB_GENERATION (
        aa_changes,
        mzml,
        params_database,
        params_merger_fetch,
        params_protgraph,
        params_bpcsr_reader,
    )
}
/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    RUN MAIN WORKFLOW
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

workflow {

    main:
    //
    // SUBWORKFLOW: Run initialisation tasks
    //
    PIPELINE_INITIALISATION (
        
        // main i/o params
        params.input,
        params.outdir,
        params.zip_output,

        // functional params
            
        // ProtGraph
        params.features,
        params.digestion,
        params.protgraph_mass_annotation,
        params.protgraph_fixed_mod,
        params.protgraph_var_mod, 
        //params.max_misscleavages,

        // bpcsr reader
        params.max_variants,
        params.max_misscleavages,
        params.min_da,
        params.max_da,

        // general params
        params.version,
        params.validate_params,
        params.monochrome_logs,
        args,
        params.help,
        params.help_full,
        params.show_hidden,
        
        // Source database params

        // merger source database params
        params.uniprot_accessions,
        params.ebi_variants,
        params.ebi_source_type,
        params.uniprot_variants,
        params.ensembl_fallback,

        // merger fetch params
        params.merger_timeout_secs,
        params.merger_fetch_retries,
        params.merger_retry_backoff_ms,

        // ProtGraph options
        params.protgraph_elbpcsr_pdb, 
        params.protgraph_additional_params,

        // query builder
        params.query_builder_ppm,

        // ProtGraph bpcsr reader options
        params.bpcsr_reader_hash_bits,
        params.bpcsr_reader_bin_size, 
        params.bpcsr_reader_job_splits,
        params.bpcsr_reader_job_depth,
        params.bpcsr_reader_ch_processing_in_size,
        params.bpcsr_reader_ch_processing_out_size,
        params.bpcsr_reader_ch_dedup_in_size,
        params.bpcsr_reader_ch_dedup_out_size,
    )

    //
    // WORKFLOW: Run main workflow
    //
    NFCORELIKE_VARIANT_DB_GENERATION (
        PIPELINE_INITIALISATION.out.aa_changes,
        PIPELINE_INITIALISATION.out.mzml,
        PIPELINE_INITIALISATION.out.params_database,
        PIPELINE_INITIALISATION.out.params_merger_fetch,
        PIPELINE_INITIALISATION.out.params_protgraph,
        PIPELINE_INITIALISATION.out.params_bpcsr_reader,
    )
    //
    // SUBWORKFLOW: Run completion tasks
    //
    PIPELINE_COMPLETION (
        params.outdir,
        params.monochrome_logs,
    )
}

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    THE END
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/
