process COMPACTFASTA {
    tag "$meta.id"
    label 'process_single'

    conda "${moduleDir}/environment.yml"
    container "${ workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container ?
        'https://depot.galaxyproject.org/singularity/protgraph:0.3.11--pyhdfd78af_0':
        'quay.io/biocontainers/protgraph:0.3.12--pyhdfd78af_0' }"

    input:
    tuple val(meta), path(input)

    output:
    tuple val(meta), path("*.fasta"), emit: fasta
    tuple val("${task.process}"), val('compactfasta'), val("dev"), topic: versions, emit: versions_compactfasta

    when:
    task.ext.when == null || task.ext.when

    script:
    def prefix = task.ext.prefix ?: "${meta.id}"
    """
    protgraph_compact_fasta ${input} -o ${prefix}_final.fasta
    """

    stub:       
    def prefix = task.ext.prefix ?: "${meta.id}"
    """
    touch ${prefix}.bam
    """
}
