from bifrostlib import datahandling


def extract_cge_resfinder_data(sampleComponentObj):
    summary, results, file_path, key = sampleComponentObj.start_data_extraction("data_resfinder.json")
    results[key] = datahandling.load_yaml(file_path)
    return (summary, results)


def convert_summary_for_reporter(sampleComponentObj):
    summary, results, file_path, key = sampleComponentObj.start_data_extraction()
    key = sampleComponentObj.get_file_location_key("data_resfinder.json")
    data = []
    resfinder_dict = results[key]["resfinder"]["results"]
    for anti_biotic_class in resfinder_dict:
        for subclass in resfinder_dict[anti_biotic_class]:
            if resfinder_dict[anti_biotic_class][subclass] != "No hit found":
                gene_dict = resfinder_dict[anti_biotic_class][subclass]
                for gene in gene_dict:
                    data.append([gene_dict[gene]["resistance_gene"], gene_dict[gene]["coverage"], gene_dict[gene]["identity"], anti_biotic_class, gene_dict[gene]["predicted_phenotype"]])  # table rows
    return data


def datadump(sampleComponentObj, log):
    sampleComponentObj.start_data_dump(log=log)
    sampleComponentObj.run_data_dump_on_function(extract_cge_resfinder_data, log=log)
    sampleComponentObj.end_data_dump(generate_report, log=log)

datadump(
    snakemake.params.sampleComponentObj,
    snakemake.log)
