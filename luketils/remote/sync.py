import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

from luketils.remote.execution import RemoteHostConfig


@dataclass(frozen=True)
class SyncConfig:
    local_root: Path
    remote_path: str
    ignore_patterns: list[str]


def sync_code(
    *,
    host_config: RemoteHostConfig,
    sync_config: SyncConfig,
) -> None:
    ssh_cmd = f"ssh -p {host_config.port}"
    mkdir_cmd = [
        "ssh",
        "-p",
        str(host_config.port),
        host_config.ssh_command_hostname(),
        f"mkdir -p {sync_config.remote_path}",
    ]
    mkdir_result = subprocess.run(mkdir_cmd, capture_output=True, text=True)
    assert mkdir_result.returncode == 0, f"Failed to create remote directory: {mkdir_result.stderr}"

    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write(".git/\n")
        f.write(".venv/\n")
        f.write("__pycache__/\n")
        f.write("*.pyc\n")
        for pattern in sync_config.ignore_patterns:
            f.write(f"{pattern}\n")
        exclude_file = f.name

    cmd = [
        "rsync",
        "-avz",
        "--delete",
        "--include=**/cache/",
        f"--exclude-from={exclude_file}",
        "-e",
        ssh_cmd,
        f"{sync_config.local_root}/",
        f"{host_config.ssh_command_hostname()}:{sync_config.remote_path}/",
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    Path(exclude_file).unlink()
    assert result.returncode == 0, f"Rsync failed: {result.stderr}"

