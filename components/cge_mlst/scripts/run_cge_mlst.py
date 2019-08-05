import subprocess
import traceback
from bifrostlib import datahandling


def script__run_cge_mlst(reads, folder, sample_file, component_file, log):
    try:
        db_sample = datahandling.load_sample(sample_file)
        db_component = datahandling.load_component(component_file)

        log_out = str(log.out_file)
        log_err = str(log.err_file)

        datahandling.log(log_out, "Started {}\n".format("script__run_cge_mlst"))
        species = db_sample["properties"]["species"]

        mlst_species = []
        if species not in db_component["mlst_species_mapping"]:
            datahandling.log(log_out, "cge mlst species: {}\n".format(species))
            subprocess.Popen("touch " + folder + "/no_mlst_species_DB").communicate()
        else:
            mlst_database_path = db_component["mlst_database_path"]
            mlst_species = db_component["mlst_species_mapping"][species]
            for mlst_entry in mlst_species:
                mlst_entry_path = folder + "/" + mlst_entry
                datahandling.log(log_out, "mlst {} on species: {}\n".format(mlst_entry, species))
                subprocess.Popen("if [ -d \"{}\" ]; then rm -r {}; fi".format(mlst_entry_path, mlst_entry_path), shell=True).communicate()
                subprocess.Popen("mkdir {}; mlst.py -x -matrix -s {} -p {} -mp kma -i {} {} -o {} 1> {} 2> {}".format(mlst_entry_path, mlst_entry, mlst_database_path, reads[0], reads[1], mlst_entry_path, log_out, log_err), shell=True).communicate()
            subprocess.Popen("touch {}".format(folder + "/mlst_complete"), shell=True).communicate()
        datahandling.log(log_out, "Done {}\n".format("script__run_cge_mlst"))
    except Exception as e:
        datahandling.log(log_err, str(traceback.format_exc()))
    return 0


script__run_cge_mlst(snakemake.input.reads, snakemake.params.folder, snakemake.params.sample_file, snakemake.params.component_file, snakemake.log)
