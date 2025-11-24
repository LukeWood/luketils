import paramiko

from luketils.remote.executor import CommandExecutor, CommandResult


class ParamikoCommandExecutor(CommandExecutor):
    def __init__(self, ssh_client: paramiko.SSHClient):
        self._ssh_client = ssh_client

    def run_command(self, command: str) -> CommandResult:
        shell_command = f"bash -l -c '{command}'"
        stdin, stdout, stderr = self._ssh_client.exec_command(shell_command)
        exit_code = stdout.channel.recv_exit_status()
        stdout_text = stdout.read().decode()
        stderr_text = stderr.read().decode()
        return CommandResult(
            exit_code=exit_code,
            stdout=stdout_text,
            stderr=stderr_text,
        )

