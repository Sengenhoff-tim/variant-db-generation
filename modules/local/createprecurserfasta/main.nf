// TODO nf-core: If in doubt look at other nf-core/modules to see how we are doing things! :)
//               https://github.com/nf-core/modules/tree/master/modules/nf-core/
//               You can also ask for help via your pull request or on the #modules channel on the nf-core Slack workspace:
//               https://nf-co.re/join
// TODO nf-core: A module file SHOULD only define input and output files as command-line parameters.
//               All other parameters MUST be provided using the "task.ext" directive, see here:
//               https://www.nextflow.io/docs/latest/process.html#ext
//               where "task.ext" is a string.
//               Any parameters that need to be evaluated in the context of a particular sample
//               e.g. single-end/paired-end data MUST also be defined and evaluated appropriately.
// TODO nf-core: Software that can be piped together SHOULD be added to separate module files
//               unless there is a run-time, storage advantage in implementing in this way
//               e.g. it's ok to have a single module for bwa to output BAM instead of SAM:
//                 bwa mem | samtools view -B -T ref.fasta
// TODO nf-core: Optional inputs are not currently supported by Nextflow. However, using an empty
//               list (`[]`) instead of a file can be used to work around this issue.

process CREATEPRECURSERFASTA {
    tag "$meta.id"
    label 'process_high'

    //TODO add singularity/conda
    container 'bpcsr_to_fasta:latest'

    input:
    tuple val(meta), path(input)
    path(queries_csv)
    tuple (
        val(max_variants),
        val(min_da), 
        val(max_da), 
        val(zip_output), 
        val(bpcsr_reader_hash_bits), 
        val(bpcsr_reader_bin_size),
        val(bpcsr_reader_job_splits),
        val(bpcsr_reader_job_depth),
        val(bpcsr_reader_ch_processing_in_size),
        val(bpcsr_reader_ch_processing_out_size),
        val(bpcsr_reader_ch_dedup_in_size),
        val(bpcsr_reader_ch_dedup_out_size)
    )
    output:
    tuple val(meta), path("output_*", type: 'dir'), emit: output

    //TODO fix version
    tuple val("${task.process}"), val('bpcsr_to_fasta'), val("dev"), topic: versions, emit: versions_bpcsr_to_fasta

    when:
    task.ext.when == null || task.ext.when

    script:
    def args = task.ext.args ?: ''
    def prefix = task.ext.prefix ?: "${meta.id}"
    def zip = ""
    def ch_processing_in_size  = bpcsr_reader_ch_processing_in_size  != null ? "--ch_proc_in_size ${bpcsr_reader_ch_processing_in_size}" : ''
    def ch_processing_out_size = bpcsr_reader_ch_processing_out_size != null ? "--ch_proc_out_size ${bpcsr_reader_ch_processing_out_size}" : ''
    def ch_dedup_in_size       = bpcsr_reader_ch_dedup_in_size       != null ? "--ch_dedup_in_size ${bpcsr_reader_ch_dedup_in_size}" : ''
    def ch_dedup_out_size      = bpcsr_reader_ch_dedup_out_size      != null ? "--ch_dedup_out_size ${bpcsr_reader_ch_dedup_out_size}" : ''
    if(zip_output) {
        zip = "--zip"
    }
    """
    bpcsr_to_fasta \\
        --graphs ${input} \\
        --queries ${queries_csv} \\
        --outdir output_${prefix} \\
        ${zip} \\
        --max_vars ${max_variants} \\
        --lower_bound ${min_da} \\
        --upper_bound ${max_da} \\
        --avail_processors ${task.cpus} \\
        --avail_memory ${task.memory.toGiga()} \\
        --interval_bin_length ${bpcsr_reader_bin_size} \\
        --hash_bits ${bpcsr_reader_hash_bits} \\
        --job_splits ${bpcsr_reader_job_splits} \\
        --split_depth ${bpcsr_reader_job_depth} \\
        ${ch_processing_in_size} \\
        ${ch_processing_out_size} \\
        ${ch_dedup_in_size} \\
        ${ch_dedup_out_size} \\
        ${args}
    """

    stub:
    def args = task.ext.args ?: ''
    def prefix = task.ext.prefix ?: "${meta.id}"
    """
    echo $args
    
    touch ${prefix}.fasta
    """
}
