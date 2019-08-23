import pkg_resources
import datetime
import os
import re
import sys
import traceback
from bifrostlib import datahandling

config = datahandling.load_config()


def extract_cge_mlst_data(db, file_path, key, temp_data):
    buffer = datahandling.load_yaml(file_path)
    db["results"][key] = buffer
    return db


def convert_summary_for_reporter(db, file_path, key, temp_data):
    for mlst_db in db["results"][GLOBAL_component_name + "/resistance/report_tsv"]:
        strain_db = db["results"][GLOBAL_component_name + "/resistance/report_tsv"][mlst_db]
        strain = strain_db["mlst"]["results"]["sequence_type"]
        alleles = ", ".join([strain_db["mlst"]["results"]["allele_profile"][i]["allele_name"] for i in strain_db["mlst"]["results"]["allele_profile"]])
        db["reporter"]["content"].append([mlst_db, strain, alleles])
    return db


def script__datadump(output, sample_file, component_file, sample_component_file, log):
    try:
        output = str(output)
        log_out = str(log.out_file)
        log_err = str(log.err_file)
        db_sample = datahandling.load_sample(sample_file)
        db_component = datahandling.load_component(component_file)
        db_sample_component = datahandling.load_sample_component(sample_component_file)
        this_function_name = sys._getframe().f_code.co_name
        global GLOBAL_component_name
        GLOBAL_component_name = db_component["name"]

        datahandling.log(log_out, "Started {}\n".format(this_function_name))

        # Save files to DB
        datahandling.save_files_to_db(db_component["db_values_changes"]["files"], sample_component_id=db_sample_component["_id"])

        # Initialization of values, summary and reporter are also saved into the sample
        db_sample_component["summary"] = {"component": {"_id": db_component["_id"], "_date": datetime.datetime.utcnow()}}
        db_sample_component["results"] = {}
        db_sample_component["reporter"] = db_component["db_values_changes"]["sample"]["reporter"]["mlst"]

        # Data extractions
        db_sample_component = datahandling.datadump_template(extract_cge_mlst_data, db_sample_component, file_path=os.path.join(GLOBAL_component_name, "resistance/data.yaml"))
        db_sample_component = datahandling.datadump_template(convert_summary_for_reporter, db_sample_component)

        # Save to sample component
        datahandling.save_sample_component(db_sample_component, sample_component_file)
        # Save summary and reporter results into sample
        db_sample["properties"]["mlst"] = db_sample_component["summary"]
        db_sample["reporter"]["mlst"] = db_sample_component["reporter"]
        datahandling.save_sample(db_sample, sample_file)

        open(output, 'w+').close()  # touch file

    except Exception:
        datahandling.log(log_out, "Exception in {}\n".format(this_function_name))
        datahandling.log(log_err, str(traceback.format_exc()))
        raise Exception
        return 1

    finally:
        datahandling.log(log_out, "Done {}\n".format(this_function_name))
        return 0


script__datadump(
    snakemake.output.complete,
    snakemake.params.sample_file,
    snakemake.params.component_file,
    snakemake.params.sample_component_file,
    snakemake.log)
