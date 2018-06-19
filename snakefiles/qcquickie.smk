import re
import pandas
from ruamel.yaml import YAML
import sys


configfile: os.path.join(os.path.dirname(workflow.snakefile), "../config.yaml")

sample = config["Sample"]  # expected input

global_threads = config["threads"]
global_memory_in_GB = config["memory"]

yaml = YAML(typ='safe')
yaml.default_flow_style = False

with open(sample, "r") as sample_yaml:
    config_sample = yaml.load(sample_yaml)

R1 = config_sample["sample"]["R1"]  # expected in sample config
R2 = config_sample["sample"]["R2"]  # expected in sample config

onsuccess:
    print("Workflow complete")
    config_sample["sample"]["components"]["success"].append("qcquickie")
    print("end", config_sample)
    with open(sample, "w") as output_file:
        yaml.dump(config_sample, output_file)
    # shell("rm qcquickie/*.fastq")
    # shell("rm qcquickie/contigs.sam")
    # shell("rm qcquickie/contigs.cov")
    # shell("rm qcquickie/contigs.vcf")
    # shell("rm qcquickie/raw_contigs.fasta")

onerror:
    print("Workflow error")
    config_sample["sample"]["components"]["failure"].append("qcquickie")
    with open(sample, "w") as output_file:
        yaml.dump(config_sample, output_file)


rule all:
    input:
        "qcquickie",
        "qcquickie/fastqc_data.txt",
        "qcquickie/contigs.bin.cov",
        "species.txt",
        "qcquickie/contigs.vcf",
        "qcquickie/contaminantion_check.txt",
        "qcquickie/contigs.variants",
        "qcquickie/quast",
        "qcquickie/contigs.sketch",


rule setup:
    output:
        dir = "qcquickie"
    shell:
        "mkdir {output}"


rule fastqc_on_reads:
    message:
        "Running step: {rule}"
    input:
        dir = "qcquickie",
        reads = (R1, R2)
    output:
        fastqc_summary = "qcquickie/fastqc_data.txt"
    threads:
        global_threads
    resources:
        memory_in_GB = global_memory_in_GB
    conda:
        "../envs/fastqc.yaml"
    log:
        "qcquickie/log/fastqc_on_reads.log"
    benchmark:
        "qcquickie/benchmarks/fastqc_on_reads.benchmark"
    shell:
        """
        mkdir qcquickie/fastqc
        fastqc --extract -o qcquickie/fastqc -t {threads} {input.reads[0]} {input.reads[1]} &> {log}
        cat qcquickie/fastqc/*/fastqc_data.txt > {output.fastqc_summary}
        """

rule setup__filter_reads_with_bbduk:
    message:
        "Running step: {rule}"
    input:
        dir = "qcquickie",
        reads = (R1, R2)
    output:
        filtered_reads = temp("qcquickie/filtered.fastq")
    params:
        adapters = os.path.join(os.path.dirname(workflow.snakefile), "../resources/adapters.fasta")
    threads:
        global_threads
    resources:
        memory_in_GB = global_memory_in_GB
    conda:
        "../envs/bbmap.yaml"
    log:
        "qcquickie/log/setup__filter_reads_with_bbduk.log"
    benchmark:
        "qcquickie/benchmarks/setup__filter_reads_with_bbduk.benchmark"
    shell:
        "bbduk.sh threads={threads} -Xmx{resources.memory_in_GB}G in={input.reads[0]} in2={input.reads[1]} out={output.filtered_reads} ref={params.adapters} ktrim=r k=23 mink=11 hdist=1 tbo minbasequality=14 &> {log}"


rule contaminant_check__classify_reads_kraken_minikraken_db:
    message:
        "Running step: {rule}"
    input:
        filtered_reads = "qcquickie/filtered.fastq",
    output:
        kraken_report = "qcquickie/kraken_report.txt"
    params:
        db = config["kraken"]["database"]
    threads:
        global_threads
    resources:
        memory_in_GB = global_memory_in_GB
    conda:
        "../envs/kraken.yaml"
    log:
        "qcquickie/log/contaminant_check__classify_reads_kraken_minikraken_db.log"
    benchmark:
        "qcquickie/benchmarks/contaminant_check__classify_reads_kraken_minikraken_db.benchmark"
    shell:
        "kraken --threads {threads} -db {params.db} --fastq-input {input.filtered_reads} 2> {log} | kraken-report -db {params.db} 1> {output.kraken_report}"


rule contaminant_check__determine_species_bracken_on_minikraken_results:
    message:
        "Running step: {rule}"
    input:
        kraken_report = "qcquickie/kraken_report.txt"
    output:
        bracken = "qcquickie/bracken.txt"
    params:
        kmer_dist = config["kraken"]["kmer_dist"]
    threads:
        global_threads
    resources:
        memory_in_GB = global_memory_in_GB
    conda:
        "../envs/bracken.yaml"
    log:
        "qcquickie/log/contaminant_check__determine_species_bracken_on_minikraken_results.log"
    benchmark:
        "qcquickie/benchmarks/contaminant_check__determine_species_bracken_on_minikraken_results.benchmark"
    shell:
        """
        est_abundance.py -i {input.kraken_report} -k {params.kmer_dist} -o {output.bracken} &> {log}
        sort -r -t$'\t' -k7 {output.bracken} -o {output.bracken}
        """

rule assembly_check__combine_reads_with_bbmerge:
    message:
        "Running step: {rule}"
    input:
        filtered_reads = "qcquickie/filtered.fastq"
    output:
        merged_reads = temp("qcquickie/merged.fastq"),
        unmerged_reads = temp("qcquickie/unmerged.fastq")
    threads:
        global_threads
    resources:
        memory_in_GB = global_memory_in_GB
    conda:
        "../envs/bbmap.yaml"
    log:
        "qcquickie/log/assembly_check__combine_reads_with_bbmerge.log"
    benchmark:
        "qcquickie/benchmarks/assembly_check__combine_reads_with_bbmerge.benchmark"
    shell:
        "bbmerge.sh threads={threads} -Xmx{resources.memory_in_GB}G in={input.filtered_reads} out={output.merged_reads} outu={output.unmerged_reads} &> {log}"


rule assembly_check__quick_assembly_with_tadpole:
    message:
        "Running step: {rule}"
    input:
        merged_reads = "qcquickie/merged.fastq",
        unmerged_reads = "qcquickie/unmerged.fastq"
    output:
        contigs = temp("qcquickie/raw_contigs.fasta")
    threads:
        global_threads
    resources:
        memory_in_GB = global_memory_in_GB
    conda:
        "../envs/bbmap.yaml"
    log:
        "qcquickie/log/assembly_check__quick_assembly_with_tadpole.log"
    benchmark:
        "qcquickie/benchmarks/assembly_check__quick_assembly_with_tadpole.benchmark"
    shell:
        "tadpole.sh threads={threads} -Xmx{resources.memory_in_GB}G in={input.merged_reads},{input.unmerged_reads} out={output.contigs} &> {log}"


rule assembly_check__rename_contigs:
    message:
        "Running step: {rule}"
    input:
        contigs = "qcquickie/raw_contigs.fasta",
    output:
        contigs = "qcquickie/contigs.fasta"
    threads:
        global_threads
    resources:
        memory_in_GB = global_memory_in_GB
    conda:
        "../envs/python_packages.yaml"
    log:
        "qcquickie/log/assembly_check__rename_contigs.log"
    benchmark:
        "qcquickie/benchmarks/assembly_check__rename_contigs.benchmark"
    script:
        os.path.join(os.path.dirname(workflow.snakefile), "../scripts/rename_tadpole_contigs.py")


rule assembly_check__quast_on_contigs:
    message:
        "Running step: {rule}"
    input:
        contigs = "qcquickie/contigs.fasta"
    output:
        quast = "qcquickie/quast"
    threads:
        global_threads
    resources:
        memory_in_GB = global_memory_in_GB
    conda:
        "../envs/quast.yaml"
    log:
        "qcquickie/log/assembly_check__quast_on_tadpole_contigs.log"
    benchmark:
        "qcquickie/benchmarks/assembly_check__quast_on_tadpole_contigs.benchmark"
    shell:
        "quast.py --threads {threads} {input.contigs} -o {output.quast} &> {log}"


rule assembly_check__sketch_on_contigs:
    message:
        "Running step: {rule}"
    input:
        contigs = "qcquickie/contigs.fasta"
    output:
        sketch = "qcquickie/contigs.sketch"
    threads:
        global_threads
    resources:
        memory_in_GB = global_memory_in_GB
    conda:
        "../envs/bbmap.yaml"
    log:
        "qcquickie/log/assembly_check__sketch_on_contigs.log"
    benchmark:
        "qcquickie/benchmarks/assembly_check__sketch_on_contigs.benchmark"
    shell:
        "sketch.sh threads={threads} -Xmx{resources.memory_in_GB}G in={input.contigs} out={output.sketch} &> {log}"


rule assembly_check__map_reads_to_assembly_with_bbmap:
    message:
        "Running step: {rule}"
    input:
        contigs = "qcquickie/contigs.fasta",
        filtered = "qcquickie/filtered.fastq"
    output:
        mapped = temp("qcquickie/contigs.sam")
    threads:
        global_threads
    resources:
        memory_in_GB = global_memory_in_GB
    conda:
        "../envs/bbmap.yaml"
    log:
        "qcquickie/log/assembly_check__map_reads_to_assembly_with_bbmap.log"
    benchmark:
        "qcquickie/benchmarks/assembly_check__map_reads_to_assembly_with_bbmap.benchmark"
    shell:
        "bbmap.sh threads={threads} -Xmx{resources.memory_in_GB}G ref={input.contigs} in={input.filtered} out={output.mapped} ambig=random &> {log}"


rule assembly_check__pileup_on_mapped_reads:
    message:
        "Running step: {rule}"
    input:
        mapped = "qcquickie/contigs.sam"
    output:
        coverage = temp("qcquickie/contigs.cov"),
        pileup = "qcquickie/contigs.pileup"
    threads:
        global_threads
    resources:
        memory_in_GB = global_memory_in_GB
    conda:
        "../envs/bbmap.yaml"
    log:
        "qcquickie/log/assembly_check__pileup_on_mapped_reads.log"
    benchmark:
        "qcquickie/benchmarks/assembly_check__pileup_on_mapped_reads.benchmark"
    shell:
        "pileup.sh threads={threads} -Xmx{resources.memory_in_GB}G in={input.mapped} basecov={output.coverage} out={output.pileup} &> {log}"


rule summarize__depth:
    message:
        "Running step: {rule}"
    input:
        coverage = "qcquickie/contigs.cov"
    output:
        contig_depth_yaml = "qcquickie/contigs.sum.cov",
        binned_depth_yaml = "qcquickie/contigs.bin.cov"
    threads:
        global_threads
    resources:
        memory_in_GB = global_memory_in_GB
    conda:
        "../envs/python_packages.yaml"
    log:
        "qcquickie/log/summarize__bin_coverage.log"
    benchmark:
        "qcquickie/benchmarks/summarize__bin_coverage.benchmark"
    script:
        os.path.join(os.path.dirname(workflow.snakefile), "../scripts/summarize_depth.py")


rule assembly_check__call_variants:
    message:
        "Running step: {rule}"
    input:
        contigs = "qcquickie/contigs.fasta",
        mapped = "qcquickie/contigs.sam",
    output:
        variants = temp("qcquickie/contigs.vcf")
    threads:
        global_threads
    resources:
        memory_in_GB = global_memory_in_GB
    conda:
        "../envs/bbmap.yaml"
    log:
        "qcquickie/log/post_assembly__call_variants.log"
    benchmark:
        "qcquickie/benchmarks/post_assembly__call_variants.benchmark"
    shell:
        "callvariants.sh in={input.mapped} vcf={output.variants} ref={input.contigs} ploidy=1 clearfilters &> {log}"


rule summarize__variants:
    message:
        "Running step: {rule}"
    input:
        variants = "qcquickie/contigs.vcf",
    output:
        variants_yaml = "qcquickie/contigs.variants",
    threads:
        global_threads
    resources:
        memory_in_GB = global_memory_in_GB
    conda:
        "../envs/python_packages.yaml"
    log:
        "qcquickie/log/summarize__variants.log"
    benchmark:
        "qcquickie/benchmarks/summarize__variants.benchmark"
    script:
        os.path.join(os.path.dirname(workflow.snakefile), "../scripts/summarize_variants.py")


rule contaminant_check__declare_contamination:
    message:
        "Running step: {rule}"
    input:
        bracken = "qcquickie/bracken.txt"
    output:
        contaminantion_check = "qcquickie/contaminantion_check.txt"
    threads:
        global_threads
    resources:
        memory_in_GB = global_memory_in_GB
    log:
        "qcquickie/log/contaminant_check__declare_contamination.log"
    benchmark:
        "qcquickie/benchmarks/contaminant_check__declare_contamination.benchmark"
    run:
        with open(output.contaminantion_check, "w") as contaminantion_check:
            df = pandas.read_table(input.bracken)
            if df[df["fraction_total_reads"] > 0.05].shape[0] == 1:
                contaminantion_check.write("No contaminant detected\n")
            else:
                contaminantion_check.write("Contaminant found or Error")


rule species_check__set_species:
    message:
        "Running step: {rule}"
    input:
        bracken = "qcquickie/bracken.txt",
    output:
        species = "species.txt",
    threads:
        global_threads
    resources:
        memory_in_GB = global_memory_in_GB
    log:
        "qcquickie/log/contaminant_check__declare_contamination.log"
    benchmark:
        "qcquickie/benchmarks/contaminant_check__declare_contamination.benchmark"
    run:
        with open(output.species, "w") as species_file:
            if "provided_species" in config_sample["sample"]:
                species_file.write(config_sample["sample"]["provided_species"] + "\n")
                config_sample["sample"]["species"] = config_sample["sample"]["provided_species"]
                with open(sample, "w") as output_file:
                    yaml.dump(config_sample, output_file)
            else:
                df = pandas.read_table(input.bracken)
                species_file.write(df["name"].iloc[0] + "\n")
                config_sample["sample"]["species"] = df["name"].iloc[0]
                with open(sample, "w") as output_file:
                    yaml.dump(config_sample, output_file)
        print(config_sample)

rule species_check__check_sizes:
    message:
        "Running step: {rule}"
    input:
        contig_depth_yaml = "qcquickie/contigs.sum.cov",
        species = "qcquickie/species.txt"
    output:
        size_check = "qcquickie/size_check.txt"
    params:
        species_db = os.path.join(os.path.dirname(workflow.snakefile), "../resources/species_qc_values.tsv")
    threads:
        global_threads
    resources:
        memory_in_GB = global_memory_in_GB
    log:
        "qcquickie/log/contaminant_check__declare_contamination.log"
    benchmark:
        "qcquickie/benchmarks/contaminant_check__declare_contamination.benchmark"
    run:
        with open(input.species, "r") as species_file:
            species = species_file.readlines().strip()
            df = pandas.read_table(params.species_db)
            if not df[df["ncbi_species"] == species].empty:
                with open(output.size_check, "w") as size_check:
                    size_check.write("{}\n".format(df[df["ncbi_species"] == species]["min_length"]))
                    size_check.write("{}\n".format(df[df["ncbi_species"] == species]["max_length"]))
            pass
