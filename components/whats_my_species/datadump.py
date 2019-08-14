import pkg_resources
import datetime
import os
import re
import sys
import traceback
from bifrostlib import datahandling

config = datahandling.load_config()


def extract_bracken_txt(file_path, key, db):
    buffer = datahandling.read_buffer(file_path)
    buffer = buffer.split("\n")
    if len(buffer) > 1:
        for i in range(1, len(buffer) - 1 ):  # skip first line as it's header
            db["results"][key]["species_" + str(i) + "_name"] = buffer[i].split("\t")[0]
            db["results"][key]["species_" + str(i) + "_kraken_assigned_reads"] = buffer[i].split("\t")[3]
            db["results"][key]["species_" + str(i) + "_added_reads"] = buffer[i].split("\t")[4]
            db["results"][key]["species_" + str(i) + "_count"] = int(buffer[i].split("\t")[5].strip())
    return db


def extract_kraken_report_bracken_txt(file_path, key, db):
    buffer = datahandling.read_buffer(file_path)
    buffer = buffer.split("\n")
    if len(buffer) > 2:
        db["results"][key]["unclassified_count"] = int(buffer[0].split("\t")[1])
        db["results"][key]["root"] = int(buffer[1].split("\t")[1])
    return db


def extract_kraken_report_txt(file_path, key, db):
    buffer = datahandling.read_buffer(file_path)
    buffer = buffer.split("\n")
    db["results"][key]["kraken_output"] = []
    for item in buffer:
        db["results"][key]["kraken_output"].append([value.strip() for value in item.split("\t")])
    return db


def species_math(file_path, key, db):
    if "status" not in db["results"]["kraken_report_bracken_txt"] and "status" not in db["results"]["bracken_txt"] and "species_1_count" in db["results"]["bracken_txt"] and "species_2_count" in db["results"]["bracken_txt"]:
        db["summary"]["percent_unclassified"] = db["results"]["kraken_report_bracken_txt"]["unclassified_count"] / (db["results"]["kraken_report_bracken_txt"]["unclassified_count"] + db["results"]["kraken_report_bracken_txt"]["root"])
        db["summary"]["percent_classified_species_1"] = db["results"]["bracken_txt"]["species_1_count"] / (db["results"]["kraken_report_bracken_txt"]["unclassified_count"] + db["results"]["kraken_report_bracken_txt"]["root"])
        db["summary"]["name_classified_species_1"] = db["results"]["bracken_txt"]["species_1_name"]
        db["summary"]["percent_classified_species_2"] = db["results"]["bracken_txt"]["species_2_count"] / (db["results"]["kraken_report_bracken_txt"]["unclassified_count"] + db["results"]["kraken_report_bracken_txt"]["root"])
        db["summary"]["name_classified_species_2"] = db["results"]["bracken_txt"]["species_2_name"]
    return db


def set_sample_species(file_path, key, db):
    if db["properties"]["provided_species"] is not None:
        db["properties"]["species"] = db["properties"]["provided_species"]
    else:
        db["properties"]["species"] = db["properties"]["detected_species"]
    return db


def script__datadump(output, folder, sample_file, component_file, sample_component_file, log):
    try:
        output = str(output)
        log_out = str(log.out_file)
        log_err = str(log.err_file)
        db_sample = datahandling.load_sample(sample_file)
        db_component = datahandling.load_component(component_file)
        db_sample_component = datahandling.load_sample_component(sample_component_file)
        this_function_name = sys._getframe().f_code.co_name

        datahandling.log(log_out, "Started {}\n".format(this_function_name))

        # Save files to DB
        # datahandling.save_files_to_db(["cge_resfinder/results.txt", "cge_resfinder/results_tab.txt"], sample_component_id=db_sample_component["_id"])

        # Initialization of values, summary and reporter are also saved into the sample
        db_sample_component["summary"] = {"component": {"_id": db_component["_id"], "_date": datetime.datetime.utcnow()}}
        db_sample_component["results"] = {}
        db_sample_component["reporter"] = {}  # Currently unused, set to dict of component config path when used

        # Data extractions
        db_sample_component = datahandling.datadump_template(db_sample_component, folder, "bracken.txt", extract_bracken_txt)
        db_sample_component = datahandling.datadump_template(db_sample_component, folder, "kraken_report_bracken.txt", extract_kraken_report_bracken_txt)
        db_sample_component = datahandling.datadump_template(db_sample_component, folder, "kraken_report.txt", extract_kraken_report_txt)
        db_sample_component = datahandling.datadump_template(db_sample_component, folder, "", species_math)

        # Save to sample component
        datahandling.save_sample_component(db_sample_component, sample_component_file)
        # Save summary and reporter results into sample
        db_sample["properties"]["species_detection"] = db_sample_component["summary"]
        db_sample["properties"]["detected_species"] = db_sample_component["summary"]["name_classified_species_1"]
        db_sample = datahandling.datadump_template(db_sample, folder, "", set_sample_species)
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
    snakemake.params.folder,
    snakemake.params.sample_file,
    snakemake.params.component_file,
    snakemake.params.sample_component_file,
    snakemake.log)
