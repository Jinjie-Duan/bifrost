# script for use with snakemake
import sys
import subprocess
import traceback
from bifrostlib import datahandling


def script__run_cge_resfinder(input, output, sample_file, component_file, folder, log):
    try:
        log_out = str(log.out_file)
        log_err = str(log.err_file)
        sample_db = datahandling.load_sample(sample_file)
        component_db = datahandling.load_component(component_file)
        this_function_name = sys._getframe().f_code.co_name

        datahandling.write_log(log_out, "Started {}\n".format(this_function_name))

        # Variables being used
        database_path = component_db["database_path"]
        reads = input.reads  # expected a tuple of read locations

        # Code to run
        subprocess.Popen("resfinder.py -x -matrix -p {} -mp kma -i {} {} -o {} 1> {} 2> {}".format(database_path, reads[0], reads[1], folder, log_out, log_err), shell=True).communicate()

    except Exception:
        datahandling.write_log(log_out, "Exception in {}\n".format(this_function_name))
        datahandling.write_log(log_err, str(traceback.format_exc()))

    finally:
        datahandling.write_log(log_out, "Done {}\n".format(this_function_name))
        return 0


script__run_cge_resfinder(
    snakemake.input,
    snakemake.output,
    snakemake.params.sample_file,
    snakemake.params.component_file,
    snakemake.params.folder,
    snakemake.log)
