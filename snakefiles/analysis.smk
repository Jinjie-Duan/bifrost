import re
import pandas
from ruamel.yaml import YAML
import sys
import gzip
import io

configfile: os.path.join(os.path.dirname(workflow.snakefile), "../config.yaml")
# requires --config R1_reads={read_location},R2_reads={read_location}
sample = config["Sample"]
global_threads = config["threads"]
global_memory_in_GB = config["memory"]


yaml = YAML(typ='safe')
yaml.default_flow_style = False
with open(sample, "r") as yaml_stream:
    config_sample = yaml.load(yaml_stream)

R1 = config_sample["sample"]["R1"]
R2 = config_sample["sample"]["R2"]

species = ""
if "species" in config_sample["sample"]:
    species = config_sample["sample"]["species"]
# my understanding is all helps specify final output
component = "analysis"

onsuccess:
    print("Workflow complete")
    with open(sample, "r") as sample_yaml:
        config_sample = yaml.load(sample_yaml)
    while component in config_sample["sample"]["components"]["failure"]:
        config_sample["sample"]["components"]["failure"].remove(component)
    if component not in config_sample["sample"]["components"]["success"]:
        config_sample["sample"]["components"]["success"].append(component)
    with open(sample, "w") as output_file:
        yaml.dump(config_sample, output_file)

onerror:
    print("Workflow error")
    with open(sample, "r") as sample_yaml:
        config_sample = yaml.load(sample_yaml)
    while component in config_sample["sample"]["components"]["success"]:
        config_sample["sample"]["components"]["failure"].remove(component)
    if component not in config_sample["sample"]["components"]["failure"]:
        config_sample["sample"]["components"]["success"].append(component)
    with open(sample, "w") as output_file:
        yaml.dump(config_sample, output_file)


rule all:
    input:
        "analysis/analysis_complete"


rule setup:
    output:
        folder = "analysis"
    shell:
        "mkdir {output}"


rule ariba__resfinder:
    message:
        "Running step: {rule}"
    input:
        folder = "analysis",
        reads = (R1, R2)
    output:
        folder = "analysis/ariba_resfinder",
    params:
        database = config["ariba"]["resfinder"]["database"]
    threads:
        global_threads
    resources:
        memory_in_GB = global_memory_in_GB
    conda:
        "../envs/ariba.yaml"
    log:
        out_file = "analysis/log/ariba__resfinder.out.log",
        err_file = "analysis/log/ariba__resfinder.err.log",
    benchmark:
        "analysis/benchmarks/ariba__resfinder.benchmark"
    shell:
        "ariba run {params.database} {input.reads[0]} {input.reads[1]} {output.folder} --tmp_dir /scratch > {log.out_file} 2> {log.err_file}"


rule abricate_on_ariba_resfinder:
    message:
        "Running step: {rule}"
    input:
        contigs = "analysis/ariba_resfinder",
    output:
        report = "analysis/abricate_on_resfinder_from_ariba.tsv",
    params:
        database = config["abricate"]["resfinder"]["database"],
        db_name = config["abricate"]["resfinder"]["name"],
    threads:
        global_threads
    resources:
        memory_in_GB = global_memory_in_GB
    conda:
        "../envs/abricate.yaml"
    log:
        err_file = "analysis/log/abricate_on_ariba_plasmidfinder.err.log",
    benchmark:
        "analysis/benchmarks/abricate_on_ariba_resfinder.benchmark"
    shell:
        """
        if [[ -e {input.contigs}/assemblies.fa.gz ]] && [[ -n $(gzip -cd {input.contigs}/assemblies.fa.gz | head -c1) ]];
        then abricate --datadir {params.database} --db {params.db_name} {input.contigs}/assemblies.fa.gz > {output.report} 2> {log.err_file};
        else touch {output.report};
        fi;
        """


rule ariba__plasmidfinder:
    message:
        "Running step: {rule}"
    input:
        folder = "analysis",
        reads = (R1, R2)
    output:
        folder = "analysis/ariba_plasmidfinder",
    params:
        database = config["ariba"]["plasmidfinder"]["database"]
    threads:
        global_threads
    resources:
        memory_in_GB = global_memory_in_GB
    conda:
        "../envs/ariba.yaml"
    log:
        out_file = "analysis/log/ariba__plasmidfinder.out.log",
        err_file = "analysis/log/ariba__plasmidfinder.err.log",
    benchmark:
        "analysis/benchmarks/ariba__plasmidfinder.benchmark"
    shell:
        "ariba run {params.database} {input.reads[0]} {input.reads[1]} {output.folder} --tmp_dir /scratch > {log.out_file} 2> {log.err_file}"


rule abricate_on_ariba_plasmidfinder:
    message:
        "Running step: {rule}"
    input:
        contigs = "analysis/ariba_plasmidfinder",
    output:
        report = "analysis/abricate_on_plasmidfinder_from_ariba.tsv",
    params:
        database = config["abricate"]["plasmidfinder"]["database"],
        db_name = config["abricate"]["plasmidfinder"]["name"],
    threads:
        global_threads
    resources:
        memory_in_GB = global_memory_in_GB
    conda:
        "../envs/abricate.yaml"
    log:
        err_file = "analysis/log/abricate_on_ariba_plasmidfinder.err.log",
    benchmark:
        "analysis/benchmarks/abricate_on_ariba_plasmidfinder.benchmark"
    shell:
        """
        if [[ -e {input.contigs}/assemblies.fa.gz ]] && [[ -n $(gzip -cd {input.contigs}/assemblies.fa.gz | head -c1) ]];
        then abricate --datadir {params.database} --db {params.db_name} {input.contigs}/assemblies.fa.gz > {output.report} 2> {log.err_file};
        else touch {output.report};
        fi;
        """


rule ariba__mlst:
    message:
        "Running step: {rule}"
    input:
        folder = "analysis",
        reads = (R1, R2)
    output:
        folder = "analysis/ariba_mlst",
    params:
        species = species,
    threads:
        global_threads
    resources:
        memory_in_GB = global_memory_in_GB
    conda:
        "../envs/ariba.yaml"
    log:
        out_file = "analysis/log/ariba__mlst.out.log",
        err_file = "analysis/log/ariba__mlst.err.log",
    benchmark:
        "analysis/benchmarks/ariba__mlst.benchmark"
    script:
        os.path.join(os.path.dirname(workflow.snakefile), "../scripts/ariba_mlst.py")


rule datadump_analysis:
    message:
        "Running step: {rule}"
    input:
        "analysis/ariba_mlst",
        "analysis/abricate_on_resfinder_from_ariba.tsv",
        "analysis/abricate_on_plasmidfinder_from_ariba.tsv"
    output:
        summary = touch("analysis/analysis_complete")
    params:
        sample = sample,
        folder = "analysis",
    threads:
        global_threads
    resources:
        memory_in_GB = global_memory_in_GB
    log:
        "analysis/log/datadump_analysis.log"
    benchmark:
        "analysis/benchmarks/datadump_analysis.benchmark"
    script:
        os.path.join(os.path.dirname(workflow.snakefile), "../scripts/datadump_analysis.py")
