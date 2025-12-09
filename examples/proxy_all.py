#!/usr/bin/env -S uv run python

import click
import requests

from luketils.proxy_traffic import proxy_via_ssh


@click.command()
@click.argument("hostname")
def main(hostname: str):
    print("Local IP:", requests.get("https://ifconfig.me").text)

    with proxy_via_ssh(hostname):
        print("Proxy IP:", requests.get("https://ifconfig.me").text)


if __name__ == "__main__":
    main()
