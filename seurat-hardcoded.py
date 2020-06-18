from datetime import datetime
from io import StringIO
import sys
from paramiko import SSHClient, AutoAddPolicy
from scp import SCPClient

if len(sys.argv) < 3:
    print("Usage: seurat-hardcoded.py <SSH username> <SSH password>")

VERSION = 20200617
run_uuid = datetime.now().isoformat().replace(':', '_')

## Connect via SSH
ssh = SSHClient()
ssh.set_missing_host_key_policy(AutoAddPolicy)
# alternate: ssh.load_system_host_keys()
# should probably only permit known host keys
ssh.connect('graham.computecanada.ca', username=sys.argv[1], password=sys.argv[2])
# niagara.scinet.utoronto.ca
# graham.computecanada.ca
# cedar.computecanada.ca
# beluga.computecanada.ca

## Copy files for current workflow, setting the absolute image path correctly
stdin, stdout, stderr = ssh.exec_command('echo $SCRATCH')
exit_code = stdout.channel.recv_exit_status()
scratch = stdout.readlines()[0].strip()

stdin, stdout, stderr = ssh.exec_command(f"""
    mkdir -p $SCRATCH/crescent-hpc/run-{run_uuid}/input \
        $SCRATCH/crescent-hpc/run-{run_uuid}/pipeline
""")
exit_code = stdout.channel.recv_exit_status()

with open('seurat-singularity-example.cwl') as cwl_in:
    cwl_out = cwl_in.read().format(host_directory=f"{scratch}/crescent-hpc/run-{run_uuid}")

with SCPClient(ssh.get_transport()) as scp:
    scp.putfo(StringIO(cwl_out), f"{scratch}/crescent-hpc/run-{run_uuid}/seurat-singularity.cwl")
    scp.put('run.cwl', f"{scratch}/crescent-hpc/run-{run_uuid}/")
    scp.put('Runs_Seurat_v3.R', f"{scratch}/crescent-hpc/run-{run_uuid}/pipeline")
    scp.put('barcodes.tsv.gz', f"{scratch}/crescent-hpc/run-{run_uuid}/input")
    scp.put('features.tsv.gz', f"{scratch}/crescent-hpc/run-{run_uuid}/input")
    scp.put('matrix.mtx.gz', f"{scratch}/crescent-hpc/run-{run_uuid}/input")


## Setup runtime environment, then call toil-cwl-runner
stdin, stdout, stderr = ssh.exec_command(f"""
    cd $SCRATCH/crescent-hpc
    module load python/3.6 singularity
    virtualenv venv-{VERSION}
    . venv-{VERSION}/bin/activate
    pip install toil[cwl]==4.0
    cd run-{run_uuid}
    singularity pull docker://crescentdev/crescent-seurat:3.1.4-3.6.3-3.10
    TOIL_SLURM_ARGS="-t 00:15:00" toil-cwl-runner \
        --batchSystem slurm --singularity --retryCount 0 \
        --workDir . --jobStore toil_job_store \
        seurat-singularity.cwl run.cwl
""")
exit_code = stdout.channel.recv_exit_status()
print(exit_code)
print(''.join(stdout.readlines()))
print("===")
print(''.join(stderr.readlines()))

with SCPClient(ssh.get_transport()) as scp:
    scp.get(f"{scratch}/crescent-hpc/run-{run_uuid}/SEURAT", recursive=True)

# alternatively, use a with statement
del stdin  # Suppress paramiko/paramiko#1078
ssh.close()
