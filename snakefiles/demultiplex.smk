import re
import pandas
from ruamel.yaml import YAML
import sys

# should scan samples.yaml and determine what I can report on

configfile: os.path.join(os.path.dirname(workflow.snakefile), "../config.yaml")
# requires --config R1_reads={read_location},R2_reads={read_location}
sample = config["Sample"]
global_threads = config["threads"]
global_memory_in_GB = config["memory"]

yaml = YAML(typ='safe')
yaml.default_flow_style = False

with open(sample, "r") as sample_yaml:
    config_sample = yaml.load(sample_yaml)


#!/bin/sh
#SBATCH --mem=12G --time=00-02:00 -p qc -c 10 -J 'NGS_demultiplexing'
samplesheet=$1 #assume in pwd
workdir=$(pwd) # was `pwd`
outpath='/srv/data/SeqData/2018/' #assume /srv/data/SeqData
run_name=`echo $samplesheet | cut -d '.' -f 1`
outdir=${outpath}`echo $(basename $workdir) | cut -d '_' -f1,2,3`_${run_name}_`echo $(basename $workdir) | rev | cut -d '_' -f -1 | rev`
if [ -e $outdir ]; then
	echo "Dir exists"
	exit 1
fi
srun bcl2fastq --no-lane-splitting -r 10 -p 10 -w 10 -R $workdir -o $outdir --sample-sheet $samplesheet
srun rename -v 's/((?<!L555))_R([12])_/_L555_R$2_/' $outdir/*gz
cp -r $workdir/InterOp  $outdir/
cp $workdir/RunInfo.xml $outdir/
cp $workdir/RunParameters.xml $outdir/
cp $samplesheet $outdir/
