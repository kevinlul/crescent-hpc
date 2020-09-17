import sys

from scinet import *

if len(sys.argv) < 3:
    print("Usage: seurat-example.py <SSH username> <SSH password>")

credentials = SciNetCredentials(SciNetCluster.Niagara, sys.argv[1], sys.argv[2])
workflow = SciNetWorkflow()
workflow.template_cwl = 'seurat-singularity-example.cwl'
workflow.docker_image = 'crescentdev/crescent-seurat-droplet-gsva:latest'
workflow.script_file = 'Runs_Seurat_v3.R'
input_files = ['barcodes.tsv.gz', 'features.tsv.gz', 'matrix.mtx.gz']
run = {
    "sc_input_type": "MTX",
    "resolution": 1,
    "project_id": "frontend_example_mac_10x_cwl",
    "summary_plots": "n",
    "pca_dimensions": 10,
    "percent_mito": "0,0.2",
    "number_genes": "50,8000"
}

stdout, stderr = execute_hpc_cwl(credentials, workflow, run, input_files)
print(stdout)
print(stderr, file=sys.stderr)
