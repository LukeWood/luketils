"""
Example demonstrating the marimo_profile context manager.

To run this example:
1. Install marimo: pip install marimo
2. Run: marimo edit examples/marimo_profile_example.py
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
def _(marimo_profile, np, time):
    def expensive_computation():
        result = 0
        for i in range(100000):
            result += i ** 2
        return result

    def matrix_operations():
        a = np.random.rand(100, 100)
        b = np.random.rand(100, 100)
        return np.dot(a, b)

    def nested_function():
        expensive_computation()
        matrix_operations()

    # Profile the code - the profiler automatically displays updates!
    with marimo_profile(refresh_interval=0.5, top_n=100):
        # Run some expensive operations
        for i in range(50):
            nested_function()
            time.sleep(0.005)
    return


if __name__ == "__main__":
    app.run()
