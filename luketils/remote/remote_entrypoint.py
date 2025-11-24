#!/usr/bin/env python3

import sys

import cloudpickle

from luketils.remote.function_wrapper import execute_bytes_as_cloudpickle_wrapper

# Steal stdout buffer to avoid printing to the console, which we
# use to serialize the pickled result back to the caller.
stdout_buffer = sys.stdout.buffer
sys.stdout = sys.stderr

pickled_wrapper = sys.stdin.buffer.read()
result = execute_bytes_as_cloudpickle_wrapper(pickled_wrapper)

pickled_result = cloudpickle.dumps(result)
stdout_buffer.write(pickled_result)
stdout_buffer.flush()

