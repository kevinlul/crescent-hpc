# [CReSCENT](https://github.com/pughlab/crescent-frontend)-HPC

Python 3.6+ module to execute some Common Workflow Language pipelines on high-performance clusters.
Currently supports SciNet Niagara, Graham, Cedar, and Béluga.

The reusable module of code here is `scinet.py` and its `execute_hpc_cwl` function.

## Testing an example
This will run a Seurat pipeline on SciNet Niagara. To change the target cluster, edit `seurat-example.py`.
1. Copy `Runs_Seurat_v3.R`, `barcodes.tsv.gz`, `features.tsv.gz`, and `matrix.mtx.gz` to the working directory.
1. Activate the virtualenv for Python 3.6+ and install dependencies:
`virtualenv venv && . venv/bin/activate && pip install -r requirements.txt`
1. Run `python seurat-example.py USERNAME PASSWORD`.
This will take some time, and even longer for the first run to pull the image and convert to Singularity.
1. Find the workflow outputs in `SEURAT` in the working directory and some remote logs in the console.

## Development
Security concerns about the plaintext password, authenticating instead with RSA keys,
and verifying the identity of the server have not been addressed here.

Originally written as a specific script in `seurat-hardcoded.py` and then somewhat genericized,
though many CReSCENT-Seurat-isms remain.

## Assumptions about the pipeline
- CWL 1.0
- Runs on a single Docker image using a single workflow file
  - See `seurat-singularity-example.cwl` for how to specify the image
- All inputs are located in the same directory, default `input`
- There is only one output directory, default `SEURAT`
- The main script is located in a volume in the image, default `pipeline`
  - This is a holdover from CReSCENT and should instead be baked into the image

## Assumptions about SciNet
- Accessible via port 22 SSH
- Login nodes have internet access
- `$SCRATCH` exists and is writable even on batch compute nodes
- Module `python/3.6` is available and contains `virtualenv` and `pip`
- Module `singularity/3` is available and usable on batch compute nodes
- The execution engine is `slurm`
