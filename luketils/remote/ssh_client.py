from pathlib import Path

import paramiko


def _load_ssh_config(hostname: str) -> dict:
    ssh_config_path = Path.home() / ".ssh" / "config"
    ssh_config = paramiko.SSHConfig()
    if ssh_config_path.exists():
        with open(ssh_config_path) as f:
            ssh_config.parse(f)
    return ssh_config.lookup(hostname)


def _resolve_hostname(config: dict, hostname: str) -> str:
    return config.get("hostname", hostname)


def _resolve_port(config: dict, port: int) -> int:
    return int(config.get("port", port))


def _resolve_username(config: dict, username: str | None) -> str | None:
    return username or config.get("user")


def _resolve_key_filenames(config: dict) -> list[str] | None:
    if "identityfile" not in config:
        return None
    key_filename = config["identityfile"]
    if isinstance(key_filename, list):
        return [str(Path(k).expanduser()) for k in key_filename]
    return [str(Path(key_filename).expanduser())]


def _build_connect_kwargs(
    hostname: str, port: int, username: str | None, key_filenames: list[str] | None
) -> dict:
    kwargs = {"hostname": hostname, "port": port}
    if username:
        kwargs["username"] = username
    if key_filenames:
        kwargs["key_filename"] = key_filenames
    return kwargs


def create_ssh_client(
    hostname: str, port: int, username: str | None
) -> paramiko.SSHClient:
    config = _load_ssh_config(hostname)
    actual_hostname = _resolve_hostname(config, hostname)
    actual_port = _resolve_port(config, port)
    actual_username = _resolve_username(config, username)
    key_filenames = _resolve_key_filenames(config)
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.load_system_host_keys()
    connect_kwargs = _build_connect_kwargs(
        actual_hostname, actual_port, actual_username, key_filenames
    )
    client.connect(**connect_kwargs)
    return client

