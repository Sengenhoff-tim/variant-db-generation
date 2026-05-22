process ADDVARIANTS {
    tag "$meta.id"
    label 'process_single'

    conda "${moduleDir}/environment.yml"
    container "${ workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container ?
        'TODO':
        'community.wave.seqera.io/library/biopython_crcmod_python_requests:6bec89e659c2d117' }"

    input:
    path(uniprot_entries)
    tuple val(meta), path(input)
    tuple val(use_fallback)
    

    output:
    tuple val(meta), path("*_database.txt.gz"), emit: gz // TODO .txt or .gz: unclear
    tuple val("${task.process}"), val('python'), eval("python --version | sed 's/Python //g'"), topic: versions, emit: versions_python
    
    when:
    task.ext.when == null || task.ext.when

    script:
    // def args = task.ext.args ?: ''
    def prefix = task.ext.prefix ?: "${meta.id}"
    // TODO nf-core: It MUST be possible to pass additional parameters to the tool as a command-line string via the "task.ext.args" directive
    // TODO nf-core: If the tool supports multi-threading then you MUST provide the appropriate parameter
    //               using the Nextflow "task" variable e.g. "--threads $task.cpus"
    
    """
    gzip -cdf ${uniprot_entries} | entry_builder.py -i ${input} | gzip "${prefix}_database.txt.gz"
    """

    //gzip -cdf ${uniprot_entries} | \
    //entry_builder.py \
    //    --aa_changes_file ${input} | \
    //gzip > ${prefix}_wvariants.txt.gz
    stub:
    // def args = task.ext.args ?: ''
    def prefix = task.ext.prefix ?: "${meta.id}"
    """
    gzip -c /dev/null > "${prefix}_database.txt.gz"
    """
}
