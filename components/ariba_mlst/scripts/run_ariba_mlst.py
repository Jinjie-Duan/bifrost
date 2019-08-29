
#---- Templated section: start ---------------------------------------------------------------------
import sys
import subprocess
import traceback
import os
from bifrostlib import datahandling
#---- Templated section: end -----------------------------------------------------------------------
#**** Dynamic section: start ***********************************************************************
def script__run_ariba_mlst(input, output, sample_file, component_file, folder, log):
    import pandas
#**** Dynamic section: end *************************************************************************
#---- Templated section: start ---------------------------------------------------------------------
    try:
        log_out = str(log.out_file)
        log_err = str(log.err_file)
        db_sample = datahandling.load_sample(sample_file)
        db_component = datahandling.load_component(component_file)
        this_function_name = sys._getframe().f_code.co_name

        datahandling.write_log(log_out, "Started {}\n".format(this_function_name))
#---- Templated section: end -----------------------------------------------------------------------
#**** Dynamic section: start ***********************************************************************
        # Variables being used
        database_path = db_component["database_path"]
        reads = input.reads  # expected a tuple of read locations
        output_file = output.complete  # a file to mark success for snakemake
        species = db_sample["properties"]["species"]

        # Code to run
        if species not in db_component["options"]["mlst_species_mapping"]:
            datahandling.write_log(log_out, "cge mlst species: {}\n".format(species))
            subprocess.Popen("touch " + folder + "/no_mlst_species_DB").communicate()
        else:
            mlst_species = db_component["options"]["mlst_species_mapping"][species]
            data_dict = {}
            for mlst_entry in mlst_species:
                data_dict[mlst_entry] = {}
                mlst_entry_path = folder + "/" + mlst_entry
                mlst_database_path = os.path.join(database_path, mlst_entry, "ref_db")
                datahandling.write_log(log_out, "mlst {} on species: {}\n".format(mlst_entry, species))
                command = "if [ -d \"{}\" ]; then rm -r {}; fi".format(mlst_entry_path, mlst_entry_path)
                datahandling.write_log(log_out, "Running:{}".format(command))
                subprocess.Popen(command, shell=True).communicate()
                command = "ariba run --force {} {} {} {} 1> {} 2> {}".format(mlst_database_path, reads[0], reads[1], mlst_entry_path, log_out, log_err)
                datahandling.write_log(log_out, "Running:{}".format(command))
                subprocess.Popen(command, shell=True).communicate()
                data_dict[mlst_entry]["report"] = pandas.read_csv(os.path.join(mlst_entry_path, "mlst_report.tsv"), sep="\t").to_dict(orient="records")[0]
                data_dict[mlst_entry]["report_details"] = pandas.read_csv(os.path.join(mlst_entry_path, "mlst_report.details.tsv"), sep="\t", index_col="gene").to_dict(orient="index")
            datahandling.save_yaml(data_dict, output_file)
#**** Dynamic section: end *************************************************************************
#---- Templated section: start ---------------------------------------------------------------------
    except Exception:
        datahandling.write_log(log_out, "Exception in {}\n".format(this_function_name))
        datahandling.write_log(log_err, str(traceback.format_exc()))

    finally:
        datahandling.write_log(log_out, "Done {}\n".format(this_function_name))
        return 0

#**** Dynamic section: start ***********************************************************************
script__run_ariba_mlst(\
#**** Dynamic section: end *************************************************************************
    snakemake.input,
    snakemake.output,
    snakemake.params.sample_file,
    snakemake.params.component_file,
    snakemake.params.folder,
    snakemake.log)
#---- Templated section: end -----------------------------------------------------------------------
