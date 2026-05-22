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
    samplesheet // channel: samplesheet read in from --input
    params_database
    params_merge
    params_protgraph
    params_bpcsr_reader
    main:

    //
    // WORKFLOW: Run pipeline
    //
    VARIANT_DB_GENERATION (
        samplesheet,
        params_database,
        params_merge,
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
        params.max_misscleavages,

        // bpcsr reader
        params.max_variants,
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
        params.use_ensembl_fallback,
        params.merge_uniprot_database,
        params.uniprot_source_file,
        params.uniprot_source_accession_list,

        // ProtGraph options
        params.protgraph_additional_params,

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
        PIPELINE_INITIALISATION.out.samplesheet,
        PIPELINE_INITIALISATION.out.ch_database_params,
        PIPELINE_INITIALISATION.out.ch_merge_params,
        PIPELINE_INITIALISATION.out.ch_protgraph_params,
        PIPELINE_INITIALISATION.out.ch_bpcsr_reader_params,
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
