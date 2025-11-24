from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class CommandResult:
    exit_code: int
    stdout: str
    stderr: str


class CommandExecutor(Protocol):
    def run_command(self, command: str) -> CommandResult:
        ...

