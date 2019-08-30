#---- Templated section: start ---------------------------------------------------------------------
import pkg_resources
import datetime
import os
import re
import sys
import traceback
from bifrostlib import datahandling
#---- Templated section: end -----------------------------------------------------------------------
#**** Dynamic section: start ***********************************************************************
def extract_values_from_output(db, file_path, key, temp_data):
    buffer = datahandling.load_yaml(file_path)
    db["results"][key] = buffer
    return db


def convert_summary_for_reporter(db, file_path, key, temp_data):
    # Function is dependent on structure of report in config file, should only be working with summary
    return db
#**** Dynamic section: end *************************************************************************
#---- Templated section: start ---------------------------------------------------------------------
def script__datadump(output, sample_file, component_file, sample_component_file, log):
    try:
        output = str(output)
        log_out = str(log.out_file)
        log_err = str(log.err_file)
        sample_db = datahandling.load_sample(sample_file)
        component_db = datahandling.load_component(component_file)
        db_sample_component = datahandling.load_sample_component(sample_component_file)
        this_function_name = sys._getframe().f_code.co_name
        global GLOBAL_component_name
        GLOBAL_component_name = component_db["name"]
        global GLOBAL_category_name
        GLOBAL_category_name = component_db["category"]

        datahandling.write_log(log_out, "Started {}\n".format(this_function_name))

        # Save files to DB
        datahandling.save_files_to_db(component_db["db_values_changes"]["files"], sample_component_id=db_sample_component["_id"])

        # Initialization of values, summary and report are also saved into the sample
        db_sample_component["summary"] = {"component": {"_id": component_db["_id"], "_date": datetime.datetime.utcnow()}}
        db_sample_component["results"] = {}
        db_sample_component["report"] = component_db["db_values_changes"]["sample"]["report"][GLOBAL_category_name]
#---- Templated section: end -----------------------------------------------------------------------
#**** Dynamic section: start************************************************************************
        # Data extractions
        db_sample_component = datahandling.datadump_template(extract_values_from_output, db_sample_component, file_path=os.path.join(GLOBAL_component_name, "data.yaml"))
        db_sample_component = datahandling.datadump_template(convert_summary_for_reporter, db_sample_component)
#**** Dynamic section: end *************************************************************************
#---- Templated section: start ---------------------------------------------------------------------
        # Save to sample component
        datahandling.save_sample_component_to_file(db_sample_component, sample_component_file)
        # Save summary and report results into sample
        sample_db["properties"][GLOBAL_category_name] = db_sample_component["summary"]
        sample_db["report"][GLOBAL_category_name] = db_sample_component["report"]
        datahandling.save_sample_to_file(sample_db, sample_file)
        open(output, 'w+').close()  # touch file

    except Exception:
        datahandling.write_log(log_out, "Exception in {}\n".format(this_function_name))
        datahandling.write_log(log_err, str(traceback.format_exc()))
        raise Exception
        return 1

    finally:
        datahandling.write_log(log_out, "Done {}\n".format(this_function_name))
        return 0


script__datadump(
    snakemake.output.complete,
    snakemake.params.sample_file,
    snakemake.params.component_file,
    snakemake.params.sample_component_file,
    snakemake.log)
#---- Templated section: end -----------------------------------------------------------------------
