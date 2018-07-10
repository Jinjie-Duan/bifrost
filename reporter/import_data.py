import pandas as pd
import datetime
import components.mongo_interface as mongo_interface

def extract_data(sample_db):
    sample = {}
    sample['_id'] = str(sample_db['_id'])
    sample["input_read_status"] = sample_db["sample"]["input_read_status"]
    sample['name'] = sample_db['sample'].get('name')
    sample['user'] = sample_db['sample'].get('user')
    sample['R1_location'] = sample_db['sample'].get('R1')
    sample['R2_location'] = sample_db['sample'].get('R2')
    sample["run_name"] = sample_db["sample"]["run_folder"].split("/")[-1]
    if "setup_time" in sample_db["sample"]:
        sample["setup_time"] = datetime.datetime.strptime(
            sample_db["sample"]["setup_time"], "%Y-%m-%d %H:%M:%S.%f")
    else:
        sample["setup_time"] = None

    # Not nice, but we have many different combinations
    if "sample_sheet" in sample_db["sample"]:
        sample['supplied_name'] = sample_db['sample']["sample_sheet"]["sample_name"]
        if sample['name'] == None:
            sample['name'] = sample["supplied_name"]
        sample["provided_species"] = sample_db['sample']["sample_sheet"].get(
            "provided_species", "")
        sample['supplying_lab'] = sample_db['sample']["sample_sheet"]['group']
        sample['comments'] = sample_db["sample"]["sample_sheet"]["Comments"]
        sample["emails"] = sample_db["sample"]["sample_sheet"]["emails"]

    if "qcquickie" in sample_db:
        for key, value in sample_db['qcquickie']['summary'].items():
            sample["qcquickie_" + key] = value
        sample["qcquickie_N50"] = sample_db["qcquickie"]["quast/report_tsv"]["N50"]
        sample["qcquickie_N75"] = sample_db["qcquickie"]["quast/report_tsv"]["N75"]
        sample["qcquickie_bin_length_1x_25x_diff"] = sample["qcquickie_bin_length_at_1x"] - \
            sample["qcquickie_bin_length_at_25x"]

    if "assembly" in sample_db:
        for key, value in sample_db['assembly']['summary'].items():
            sample["assembly_" + key] = value
        if "bin_length_at_25x" not in sample_db["assembly"]["summary"]:
            print(sample["name"])
            print(sample_db['assembly']['summary'])
    
        sample["assembly_N50"] = sample_db["assembly"]["quast/report_tsv"]["N50"]
        sample["assembly_N75"] = sample_db["assembly"]["quast/report_tsv"]["N75"]
        sample["assembly_bin_length_1x_25x_diff"] = sample["assembly_bin_length_at_1x"] - \
            sample["assembly_bin_length_at_25x"]

    if not "run_name" in sample:
        sys.stderr.write("Sample {} has no run name.\n".format(sample["name"]))
        sample["run_name"] = ""

    if "qcquickie_name_classified_species_1" in sample:
        species_words = sample["qcquickie_name_classified_species_1"].split(
        )
        sample["short_class_species_1"] = '{}. {}'.format(
            species_words[0][0], ' '.join(species_words[1:]))
    else:
        sample["qcquickie_name_classified_species_1"] = "Not classified"
        sample["short_class_species_1"] = "Not classified"

    if not "supplying_lab" in sample:
        sample["supplying_lab"] = "Not specified"

    return sample

def import_data():
    return pd.DataFrame(list(map(extract_data, mongo_interface.test_get_all_samples())))
