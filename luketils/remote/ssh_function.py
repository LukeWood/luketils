import functools
import sys
from pathlib import Path
from typing import Callable, TypeVar

import paramiko

from luketils.git_utils.repo import (
    find_git_root,
    get_current_branch,
    get_gitignore_patterns,
    get_repo_name,
)
from luketils.remote.execution import RemoteHostConfig
from luketils.remote.function_wrapper import serialize_function_for_execution
from luketils.remote.ssh_client import create_ssh_client
from luketils.remote.sync import SyncConfig, sync_code
import cloudpickle

T = TypeVar("T")


class RemoteExecutionError(RuntimeError):
    def __init__(self, exit_code: int, stderr: str, hostname: str):
        self.exit_code = exit_code
        self.stderr = stderr
        self.hostname = hostname
        super().__init__(
            f"Remote execution failed on {hostname} (exit {exit_code}):\n{stderr}"
        )


def ssh_function(host: str, port: int = 22, username: str | None = None):
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            git_root = find_git_root()
            repo_name = get_repo_name()
            branch_name = get_current_branch()
            gitignore_patterns = get_gitignore_patterns()

            remote_path_template = f"~/.remote-repos/{repo_name}/{branch_name}"

            host_config = RemoteHostConfig(
                hostname=host,
                port=port,
                username=username,
            )

            home_dir = host_config.get_home()
            remote_path = remote_path_template.replace("~", home_dir)

            sync_config = SyncConfig(
                local_root=git_root,
                remote_path=remote_path,
                ignore_patterns=gitignore_patterns,
            )

            sync_code(host_config=host_config, sync_config=sync_config)

            entrypoint_path = Path(__file__).parent / "remote_entrypoint.py"
            assert entrypoint_path.exists(), f"Expected remote_entrypoint.py to exist at {entrypoint_path}"

            remote_entrypoint_path = f"{remote_path}/.remote_entrypoint.py"
            python_version = f"{sys.version_info.major}.{sys.version_info.minor}"

            ssh_client = create_ssh_client(
                hostname=host_config.hostname,
                port=host_config.port,
                username=host_config.username,
            )

            sftp = ssh_client.open_sftp()
            sftp.put(str(entrypoint_path), remote_entrypoint_path)
            sftp.close()

            pickled_data = serialize_function_for_execution(func, *args, **kwargs)

            remote_cmd = f"cd {remote_path} && uv run --python {python_version} python {remote_entrypoint_path}"
            stdin, stdout, stderr = ssh_client.exec_command(remote_cmd)
            stdin.write(pickled_data)
            stdin.channel.shutdown_write()
            exit_code = stdout.channel.recv_exit_status()
            stdout_bytes = stdout.read()
            stderr_bytes = stderr.read()
            ssh_client.close()

            if exit_code != 0:
                stderr_text = stderr_bytes.decode()
                raise RemoteExecutionError(
                    exit_code=exit_code,
                    stderr=stderr_text,
                    hostname=host_config.hostname,
                )

            result = cloudpickle.loads(stdout_bytes)
            return result

        return wrapper

    return decorator

