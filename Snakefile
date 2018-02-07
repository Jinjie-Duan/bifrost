#!/usr/bin/env python3
import re
import pandas
import sys
import os
import lib.serum as serum  # all serum lib functions also have access to the config file to prevent reduce excess parameter passing
import pkg_resources

# config_file = pkg_resources.resource_filename(workflow.snakefile "/config/config.yaml")
configfile: os.path.join(os.path.dirname(workflow.snakefile), "config.yaml")
# from pytools.persistent_dict import PersistentDict
# storage = PersistentDict("qcquickie_storage")
# snakemake -s ~/code/serumqc/snakefiles/serumqc.snake --config R1_reads={read_location} R2_reads={read_location} Sample=Test
# snakemake -s ~/code/serumqc/snakefiles/serumqc.snake --config R1_reads=~/test/data/nextseq/FHA3_S64_L555_R1_001.fastq.gz R2_reads=~/test/data/nextseq/FHA3_S64_L555_R2_001.fastq.gz Sample=Test
# requires --config R1_reads={read_location},R2_reads={read_location}
# snakemake -s ~/git.repositories/SerumQC-private/batch_run.snake --config run_folder=../../data/tiny/ sample_sheet=/srv/data/BIG/NGS_facility/assembly/2018/180117_NS500304_0140_N_WGS_91_AHWHHFAFXX/sample_sheet.xlsx

run_folder = str(config["run_folder"])
sample_sheet = str(config["sample_sheet"])

# my understanding is all helps specify final output
onsuccess:
    print("Workflow complete")
    output = ["status.txt"]
    with open(output[0], "w") as status:
        status.write("Success")
onerror:
    print("Workflow error")
    output = ["status.txt"]
    with open(output[0], "w") as status:
        status.write("Failure")

rule all:
    input:
        "init_complete"

rule set_up_run:
    input:
        run_folder = run_folder
    output:
        samplesheet = "sample_sheet.xlsx",
        run_info_yaml = "init_complete"
    params:
        samplesheet = sample_sheet
    run:
        serum.check__robot_sample_sheet(params.samplesheet, output.samplesheet)
        serum.check__run_folder(input.run_folder)
        serum.check__combine_sample_sheet_with_run_info(output.samplesheet)
        serum.initialize__run_from_run_info()
        serum.start_initialized_samples()
        serum.initialize_complete()
        # post steps

rule qcquickie_samples:
    input:
        run_config = "run.yaml",
        cmd_qcquickie = expand({sample}/cmd_qcquickie.sh, sample=config["samples"])