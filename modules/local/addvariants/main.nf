process ADDVARIANTS {
    tag "$meta.id"
    label 'process_single'

    //conda "${moduleDir}/environment.yml"

    //TODO add singluarity/conda
    container "vcf_uniprot_merger:latest"

    input:
    tuple val(meta), path(input)
    tuple path(uniprot_entries), val(confirmed_only), val(use_ensembl_fallback)
    

    output:
    tuple val(meta), path("*_merged.txt.gz"), emit: gz // TODO .txt or .gz: unclear
    //TODO fix version
    tuple val("${task.process}"), val('vcf_uniprot_merger'), val("dev"), topic: versions, emit: vcf_uniprot_merger
    
    when:
    task.ext.when == null || task.ext.when

    script:
    // def args = task.ext.args ?: ''
    def prefix = task.ext.prefix ?: "${meta.id}"
    // TODO nf-core: It MUST be possible to pass additional parameters to the tool as a command-line string via the "task.ext.args" directive
    // TODO nf-core: If the tool supports multi-threading then you MUST provide the appropriate parameter
    //               using the Nextflow "task" variable e.g. "--threads $task.cpus"
    def confirmed = ""
    if(confirmed_only) {
        confirmed = "--confirmed_only"
    }
    
    def fallback = ""
    if(use_ensembl_fallback) {
        fallback = "--ensembl_fallback"
    }

    """
    vcf_uniprot_merger \\
        --bcftools_input_path ${input} \\
        --uniprot_input_path ${uniprot_entries} \\
        --output_path ${prefix}_merged.txt.gz \\
        ${confirmed} \\
        ${fallback} \\
        --zip
    """

    stub:
    // def args = task.ext.args ?: ''
    def prefix = task.ext.prefix ?: "${meta.id}"
    """
    gzip -c /dev/null > "${prefix}_database.txt.gz"
    """
}
