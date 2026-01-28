"""
Example demonstrating the marimo_profile context manager.

To run this example:
1. Install marimo: pip install marimo
2. Run: marimo edit examples/marimo_profile_example.py
"""

import marimo

__generated_with = "0.9.0"
app = marimo.App(width="medium")


@app.cell
def __():
    import marimo as mo
    import time
    import numpy as np
    from luketils import marimo_profile
    return mo, time, np, marimo_profile


@app.cell
def __(mo):
    mo.md(
        """
        # Live Profiling Example

        This example demonstrates the `marimo_profile()` context manager,
        which provides live profiling visualization for your code.
        """
    )
    return


@app.cell
def __(mo, time, np, marimo_profile):
    """Example with some compute-intensive functions."""

    def expensive_computation():
        """Simulate an expensive computation."""
        result = 0
        for i in range(100000):
            result += i ** 2
        return result

    def matrix_operations():
        """Perform some matrix operations."""
        a = np.random.rand(100, 100)
        b = np.random.rand(100, 100)
        return np.dot(a, b)

    def nested_function():
        """Call other functions."""
        expensive_computation()
        matrix_operations()

    # Profile the code - the profiler automatically displays updates!
    with marimo_profile(refresh_interval=0.5, top_n=15):
        # Run some expensive operations
        for i in range(50):
            nested_function()
            time.sleep(0.05)  # Small delay to see live updates

    mo.md("**Profiling complete!** Check the widget above for final results.")
    return expensive_computation, matrix_operations, nested_function


@app.cell
def __(mo):
    mo.md(
        """
        ## How to Use

        ```python
        from luketils import marimo_profile

        # Simply wrap your code in the context manager
        with marimo_profile(refresh_interval=0.5, top_n=15):
            # Your code to profile goes here
            for i in range(1000):
                expensive_function()
        ```

        **Parameters:**
        - `refresh_interval`: How often to update the display (in seconds, default: 0.5)
        - `top_n`: Number of top functions to show (default: 15)

        The profiler automatically displays live updates and shows the final
        results when your code completes!
        """
    )
    return


if __name__ == "__main__":
    app.run()
