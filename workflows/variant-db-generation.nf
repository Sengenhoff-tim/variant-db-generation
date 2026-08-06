/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    IMPORT MODULES / SUBWORKFLOWS / FUNCTIONS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/
include { paramsSummaryMap       } from 'plugin/nf-schema'
include { softwareVersionsToYAML } from '../subworkflows/nf-core/utils_nfcore_pipeline'
include { methodsDescriptionText } from '../subworkflows/local/utils_nfcore_variant-db-generation_pipeline'
include { ADDVARIANTS } from '../modules/local/addvariants/main.nf'
include { PROTGRAPH } from '../modules/local/protgraph/main.nf'
include { CREATEPRECURSERFASTA } from '../modules/local/createprecurserfasta'
include { BCFTOOLSPLUGINSPLITVEP } from '../modules/local/bcftoolspluginsplitvep'
include { QUERYBUILDER } from '../modules/local/querybuilder/main.nf'

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    RUN MAIN WORKFLOW
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

workflow VARIANT_DB_GENERATION {

    take:
    ch_aa_changes // channel: samplesheet read in from --input
    ch_ranges_mzml
    database_params
    merger_fetch_params
    querybuilder_params
    protgraph_params
    bpcsr_reader_params
    main:

    ch_versions = channel.empty()

    BCFTOOLSPLUGINSPLITVEP(ch_aa_changes)

    ADDVARIANTS(BCFTOOLSPLUGINSPLITVEP.out.gz, database_params, merger_fetch_params)
    
    PROTGRAPH(ADDVARIANTS.out.gz, protgraph_params)

    ch_ranges_mzml
        .branch { _meta, ranges, mzml ->
            mzml_only  : mzml && !ranges
            both       : mzml && ranges
            ranges_only: !mzml && ranges
        }
        .set { ch_branched }

    ch_to_extract = ch_branched.both.mix(ch_branched.mzml_only)
        .map { meta, ranges, mzml ->
            def out_name = ranges ? file(ranges).name : "${meta.id}_mzml_ranges.csv"
            def existing = ranges ? file(ranges) : file('NO_FILE')
            tuple(meta, mzml, existing, out_name)
        }

    ch_ranges_passthrough = ch_branched.ranges_only
        .map { meta, ranges, _mzml -> tuple(meta, ranges) }

    QUERYBUILDER(ch_to_extract, querybuilder_params)

    ch_final_ranges = QUERYBUILDER.out.csv.mix(ch_ranges_passthrough)

    CREATEPRECURSERFASTA(PROTGRAPH.out.bpcsr, ch_final_ranges, bpcsr_reader_params)

    
    //
    // Collate and save software versions
    //
    def topic_versions = channel.topic("versions")
        .distinct()
        .branch { entry ->
            versions_file: entry instanceof Path
            versions_tuple: true
        }

    def topic_versions_string = topic_versions.versions_tuple
        .map { process, tool, version ->
            [ process[process.lastIndexOf(':')+1..-1], "  ${tool}: ${version}" ]
        }
        .groupTuple(by:0)
        .map { process, tool_versions ->
            tool_versions.unique().sort()
            "${process}:\n${tool_versions.join('\n')}"
        }

    softwareVersionsToYAML(ch_versions.mix(topic_versions.versions_file))
        .mix(topic_versions_string)
        .collectFile(
            storeDir: "${params.outdir}/pipeline_info",
            name:  'variant-db-generation_software_'  + 'versions.yml',
            sort: true,
            newLine: true
        ).set { ch_collated_versions }


    emit:
    versions       = ch_versions                 // channel: [ path(versions.yml) ]

}

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    THE END
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/
