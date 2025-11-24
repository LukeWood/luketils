#!/usr/bin/env -S uv run python

import argparse
import subprocess
import sys

import argcomplete

from luketils.remote.ssh_function import ssh_function


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Execute a command remotely via SSH using the ssh_function decorator"
    )
    parser.add_argument(
        "-H",
        "--host",
        required=True,
        dest="host",
        help="Remote hostname to execute command on",
    )
    parser.add_argument(
        "command",
        nargs=argparse.REMAINDER,
        help="Command to execute remotely (all remaining arguments)",
    )

    argcomplete.autocomplete(parser)

    args = parser.parse_args()

    if not args.command:
        parser.error("Command is required")

    command_str = " ".join(args.command)

    @ssh_function(host=args.host)
    def execute_command() -> tuple[int, str, str]:
        """Execute the command via subprocess and return exit code, stdout, stderr."""
        result = subprocess.run(
            command_str,
            shell=True,
            capture_output=True,
            text=True,
        )
        return result.returncode, result.stdout, result.stderr

    exit_code, stdout, stderr = execute_command()

    sys.stdout.write(stdout)
    sys.stderr.write(stderr)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()

