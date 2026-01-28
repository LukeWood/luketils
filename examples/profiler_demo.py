"""
Interactive demo of the marimo_profile context manager.

This notebook demonstrates live profiling with various computational scenarios.

To run this demo:
    marimo edit examples/profiler_demo.py
"""

import marimo

__generated_with = "0.19.6"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import time
    import numpy as np
    from luketils import marimo_profile
    return marimo_profile, np, time


@app.cell
def _(np, time):
    def cpu_intensive():
        total = 0
        for i in range(1000000):
            total += i * i
        return total

    def memory_allocation():
        arrays = []
        for _ in range(50):
            arrays.append(np.random.rand(1000, 1000))
        return sum(arr.sum() for arr in arrays)

    def io_simulation():
        time.sleep(0.1)
        return "done"
    return cpu_intensive, io_simulation, memory_allocation


@app.cell
def _(cpu_intensive, io_simulation, memory_allocation, time):

    def mixed_workload():
        for i in range(10):
            if i % 3 == 0:
                cpu_intensive()
            elif i % 3 == 1:
                memory_allocation()
            else:
                io_simulation()
            time.sleep(0.05)
    return (mixed_workload,)


@app.cell
def _(marimo_profile, mixed_workload):
    with marimo_profile(refresh_interval=0.001, top_n=15):
        mixed_workload()
    return


if __name__ == "__main__":
    app.run()
