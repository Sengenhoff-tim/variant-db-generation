process PROTGRAPH {
    tag "$meta.id"
    label 'process_high'

    conda "${moduleDir}/environment.yml"
    container "${ workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container ?
        'https://depot.galaxyproject.org/singularity/protgraph:0.3.11--pyhdfd78af_0':
        'quay.io/biocontainers/protgraph:0.3.12--pyhdfd78af_0' }"

    input:
    tuple val(meta), path(input)
    tuple val(features), val(digestion), val(max_misscleavages), val(protgraph_additional_params)

    output:
    tuple val(meta), path("${prefix}/database.bpcsr"), emit: bpcsr
    tuple val("${task.process}"), val('protgraph'), val("0.3.12"), topic: versions, emit: versions_protgraph

    when:
    task.ext.when == null || task.ext.when

    script:
    def args = task.ext.args ?: ''
    def feats = "${features}".replace(",", " -ft ")
    def addititonal_params = protgraph_additional_params ?: ''
    prefix = task.ext.prefix ?: "${meta.id}"
    // TODO nf-core: It MUST be possible to pass additional parameters to the tool as a command-line string via the "task.ext.args" directive
    // TODO nf-core: If the tool supports multi-threading then you MUST provide the appropriate parameter
    //               using the Nextflow "task" variable e.g. "--threads $task.cpus"

    """ 
        gzip -cdf ${input} > ${prefix}.txt

        protgraph \\
            -eo ${prefix} \\
            -ft ${feats} \\
            --digestion ${digestion} \\
            ${addititonal_params} \\
            ${args} \\
            ${prefix}.txt
    """

    stub:
    def args = task.ext.args ?: ''
    prefix = task.ext.prefix ?: "${meta.id}"
    // TODO nf-core: A stub section should mimic the execution of the original module as best as possible
    //               Have a look at the following examples:
    //               Simple example: https://github.com/nf-core/modules/blob/818474a292b4860ae8ff88e149fbcda68814114d/modules/nf-core/bcftools/annotate/main.nf#L47-L63
    //               Complex example: https://github.com/nf-core/modules/blob/818474a292b4860ae8ff88e149fbcda68814114d/modules/nf-core/bedtools/split/main.nf#L38-L54
    // TODO nf-core: If the module doesn't use arguments ($args), you SHOULD remove:
    //               - The definition of args `def args = task.ext.args ?: ''` above.
    //               - The use of the variable in the script `echo $args ` below.
    """
    echo $args
    
    touch ${prefix}.csv | gzip
    """
}
