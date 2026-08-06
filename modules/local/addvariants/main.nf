process ADDVARIANTS {
    tag "$meta.id"
    label 'process_single'

    //conda "${moduleDir}/environment.yml"

    //TODO add singluarity/conda
    container "vcf_uniprot_merger:latest"

    input:
    tuple val(meta), path(input)
    tuple path(uniprot_accessions), val(ebi_variants), val(ebi_source_type), val(uniprot_variants), val(ensembl_fallback)
    tuple val(merger_timeout_secs), val(merger_fetch_retries), val(merger_retry_backoff_ms)    

    output:
    tuple val(meta), path("*_merged.txt"), emit: txt // TODO .txt or .gz: unclear
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

    """
    vcf_uniprot_merger \\
        --variants ${input} \\
        --accessions ${uniprot_accessions} \\
        --output ${prefix}_merged.txt \\
        --ebi_varaints ${ebi_variants} \\
        --source_type ${ebi_source_type} \\
        --uniprot_variants ${uniprot_variants} \\
        --ensembl_fallback ${ensembl_fallback} \\
        --exceptions ${prefix}_exceptions.log \\
        --timeout_secs ${merger_timeout_secs} \\
        --max_attempts ${merger_fetch_retries} \\
        --retry_backoff_ms ${merger_retry_backoff_ms}
    """
    /*
    stub:
    // def args = task.ext.args ?: ''
    def prefix = task.ext.prefix ?: "${meta.id}"
    """
    gzip -c /dev/null > "${prefix}_database.txt.gz"
    """
    */
}
