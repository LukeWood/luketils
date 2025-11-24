import contextlib
import sys
from dataclasses import dataclass

import paramiko

from luketils.remote.executor import CommandExecutor
from luketils.remote.paramiko_executor import ParamikoCommandExecutor
from luketils.remote.ssh_client import create_ssh_client


@dataclass(frozen=True)
class RemoteHostConfig:
    hostname: str
    port: int = 22
    username: str | None = None

    def ssh_command_hostname(self) -> str:
        if self.username:
            return f"{self.username}@{self.hostname}"
        return self.hostname

    def create_executor(self) -> CommandExecutor:
        ssh_client = create_ssh_client(
            hostname=self.hostname,
            port=self.port,
            username=self.username,
        )
        return ParamikoCommandExecutor(ssh_client)

    @contextlib.contextmanager
    def executor(self):
        ssh_client = create_ssh_client(
            hostname=self.hostname,
            port=self.port,
            username=self.username,
        )
        try:
            yield ParamikoCommandExecutor(ssh_client)
        finally:
            ssh_client.close()

    def get_home(self) -> str:
        with self.executor() as e:
            home_result = e.run_command("echo $HOME")
        return home_result.stdout.strip()
