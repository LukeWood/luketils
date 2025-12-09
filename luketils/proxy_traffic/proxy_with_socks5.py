import os
import socket
import subprocess
import time
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Generator


_PROXY_ENV_KEYS = ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY")


def _wait_for_port(port: int, timeout: float) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with socket.create_connection(("localhost", port), timeout=0.5):
                return
        except (ConnectionRefusedError, TimeoutError, OSError):
            time.sleep(0.05) 
    raise RuntimeError(
        f"SSH SOCKS tunnel did not become ready on port {port} within {timeout}s. "
        "Check that the SSH host is reachable and accepts connections."
    )


def _check_process_alive(proc: subprocess.Popen) -> None:
    """Check if SSH process is still running, raise with stderr if not."""
    exit_code = proc.poll()
    if exit_code is not None:
        stderr_output = proc.stderr.read().decode() if proc.stderr else ""
        raise RuntimeError(
            f"SSH process exited unexpectedly with code {exit_code}. "
            f"stderr: {stderr_output}"
        )


@dataclass(frozen=True)
class SavedEnv:
    values: dict[str, str | None]

    def restore(self) -> None:
        for key, value in self.values.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def _save_proxy_env() -> SavedEnv:
    return SavedEnv(values={k: os.environ.get(k) for k in _PROXY_ENV_KEYS})


def _set_proxy_env(proxy_url: str) -> None:
    for key in _PROXY_ENV_KEYS:
        os.environ[key] = proxy_url


def _cleanup_proc(proc: subprocess.Popen) -> None:
    if proc.poll() is None:
        proc.terminate()
        try:
            proc.wait(timeout=5.0)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()


@contextmanager
def proxy_via_ssh(
    hostname: str,
    local_port: int = 1080,
    connect_timeout: float = 10.0,
) -> Generator[subprocess.Popen, None, None]:
    """Proxies all traffice through an SSH SOCKS5 tunnel.

    usage example:
    ```
        with proxy_via_ssh("myserver"):
            response = requests.get("https://ifconfig.me")
            print(response.text)
    ```
    """
    saved_env = _save_proxy_env()

    proc = subprocess.Popen(
        ["ssh", "-N", "-D", str(local_port), hostname],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    try:
        _wait_for_port(local_port, connect_timeout)
        _check_process_alive(proc)

        protocol = "socks5h"
        proxy_url = f"{protocol}://localhost:{local_port}"
        _set_proxy_env(proxy_url)

        yield
    finally:
        saved_env.restore()
        _cleanup_proc(proc)
