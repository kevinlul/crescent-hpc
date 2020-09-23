from datetime import datetime
from enum import Enum
from io import StringIO
import json
from typing import List, Tuple

from paramiko import SSHClient, AutoAddPolicy, RSAKey
from scp import SCPClient


class SciNetCluster(Enum):
    Beluga = 'beluga.computecanada.ca'
    Cedar = 'cedar.computecanada.ca'
    Graham = 'graham.computecanada.ca'
    Niagara = 'niagara.computecanada.ca'


# TODO: add RSA key support
class SciNetCredentials:
    def __init__(self, cluster: SciNetCluster, username: str, RSApath: str):
        self.cluster = cluster
        self.username = username
        self.key = RSAKey.from_private_key_file(RSApath)


class SciNetCommonConfig:
    version: str = '20200617'  # used to disambiguate virtualenvs
    subdirectory: str = 'crescent-hpc'  # all files will be written here in scratch space
    slurm_args: str = '-t 01:00:00'  # min 00:15:00


class SciNetWorkflow:
    template_cwl: str
    docker_image: str
    script_file: str  # to be removed by embedding the script in the image
    script_subdirectory: str = 'pipeline'  # bind mount, to be removed as above
    input_subdirectory: str = 'input'  # bind mount
    output_subdirectory: str = 'SEURAT'  # CWL output


def ssh_exec_or_raise(client: SSHClient, command: str) -> Tuple[str, str]:
    """
    Implementation helper.
    Returns stdout and stderr as a tuple, converted from file-like to str.
    Raises RuntimeError on non-zero exit code.
    """
    stdin, stdout, stderr = client.exec_command(command)
    exit_code = stdout.channel.recv_exit_status()
    stdout = ''.join(stdout.readlines())
    stderr = ''.join(stderr.readlines())
    if exit_code:
        raise RuntimeError({
            "exit_code": exit_code,
            "stdout": stdout,
            "stderr": stderr
        })
    return stdout, stderr


def execute_hpc_cwl(credentials: SciNetCredentials,
                    workflow: SciNetWorkflow,
                    params: dict,
                    input_files: List[str],
                    local_output_path: str = '',
                    config: SciNetCommonConfig = SciNetCommonConfig()) -> Tuple[str, str]:
    """
    Public interface. Blocks until the workflow is complete.
    Returns stdout and stderr in string form as a tuple.

    Assumes SciNet specifics:
    - $SCRATCH
    - python/3.6 available, including virtualenv and pip
    - singularity/3 available
    - execution engine: slurm
    """
    run_uuid = 'run-' + datetime.now().isoformat().replace(':', '_')

    with SSHClient() as ssh:
        # Compares server's key to known SciNet cluster keys from file
        ssh.load_host_keys('./scinet_hosts')
        
        ssh.connect(
            credentials.cluster.value,
            username=credentials.username,
            pkey=credentials.key
        )

        stdout, stderr = ssh_exec_or_raise(ssh, 'echo $SCRATCH')
        scratch = stdout.strip()

        ssh_exec_or_raise(ssh, f"""
            mkdir -p \
            $SCRATCH/{config.subdirectory}/{run_uuid}/{workflow.input_subdirectory} \
            $SCRATCH/{config.subdirectory}/{run_uuid}/{workflow.script_subdirectory}
        """)

        run_directory = f"{scratch}/{config.subdirectory}/{run_uuid}"
        # Replace the templated field `dockerImageId` with the absolute host path
        # for the undocumented cwltool implementation that runs Docker containers
        # via singularity instead. The `dockerPull` field is still required.
        with open(workflow.template_cwl) as cwl_in:
            cwl_out = cwl_in.read().format(host_directory=run_directory)

        with SCPClient(ssh.get_transport()) as scp:
            # These support callbacks to display upload progress
            scp.putfo(StringIO(cwl_out), f"{run_directory}/workflow.cwl")
            scp.putfo(StringIO(json.dumps(params)), f"{run_directory}/run.cwl")
            scp.put(workflow.script_file, f"{run_directory}/{workflow.script_subdirectory}")
            for file in input_files:
                scp.put(file, f"{run_directory}/{workflow.input_subdirectory}")

        stdout, stderr = ssh_exec_or_raise(ssh, f"""
            cd $SCRATCH/{config.subdirectory}
            module load python/3.6 singularity/3
            virtualenv venv-{config.version}
            . venv-{config.version}/bin/activate
            pip install toil[cwl]==4.0
            cd {run_uuid}
            singularity pull docker://{workflow.docker_image}
            TOIL_SLURM_ARGS="{config.slurm_args}" toil-cwl-runner \
                --batchSystem slurm --singularity --retryCount 0 \
                --workDir . --jobStore toil_job_store \
                workflow.cwl run.cwl
        """)

        with SCPClient(ssh.get_transport()) as scp:
            scp.get(f"{run_directory}/{workflow.output_subdirectory}",
                recursive=True,
                local_path=local_output_path)

        return stdout, stderr
