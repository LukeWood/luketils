#!/usr/bin/env -S uv run python

from luketils.remote.ssh_function import ssh_function


@ssh_function(host="condor1")
def remote_hello_world() -> str:
    return "Hello from condor1!"


@ssh_function(host="condor1")
def remote_compute_sum(a: int, b: int) -> int:
    return a + b


if __name__ == "__main__":
    result = remote_hello_world()
    print(result)

    sum_result = remote_compute_sum(5, 3)
    print(f"Sum computed remotely: {sum_result}")

