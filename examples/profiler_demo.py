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
    return marimo_profile, mo, np, time


@app.cell
def _(mo):
    mo.md("""
    # 🔍 Live Profiler Demo

    This demo showcases `marimo_profile()` - a context manager that provides
    **live profiling visualization** for your Python code!

    Watch as the profiler updates in real-time, showing you exactly which
    functions are consuming the most CPU time.
    """)
    return


@app.cell
def _(mo):
    mo.md("""
    ## 🎯 Demo 1: Recursive Fibonacci
    """)
    return


@app.cell
def _(marimo_profile, mo):
    """Profile a recursive fibonacci implementation."""

    def fibonacci_recursive(n):
        """Inefficient recursive fibonacci."""
        if n <= 1:
            return n
        return fibonacci_recursive(n - 1) + fibonacci_recursive(n - 2)

    def run_fibonacci():
        """Run multiple fibonacci calculations."""
        results = []
        for i in range(25, 32):
            results.append(fibonacci_recursive(i))
        return results

    mo.md("**Running recursive Fibonacci calculations...**")

    # Profile the fibonacci code
    with marimo_profile(top_n=10):
        results = run_fibonacci()
    return


@app.cell
def _(mo):
    mo.md("""
    ## 🧮 Demo 2: Matrix Operations
    """)
    return


@app.cell
def _(marimo_profile, np, time):
    """Profile various matrix operations."""

    def matrix_multiply(size=200):
        """Large matrix multiplication."""
        a = np.random.rand(size, size)
        b = np.random.rand(size, size)
        return np.dot(a, b)

    def matrix_eigenvalues(size=300):
        """Compute eigenvalues of a matrix."""
        a = np.random.rand(size, size)
        return np.linalg.eigvals(a)

    def matrix_svd(size=200):
        """Singular value decomposition."""
        a = np.random.rand(size, size)
        return np.linalg.svd(a)

    def run_matrix_ops():
        """Run a mix of matrix operations."""
        for _ in range(3):
            matrix_multiply(200)
            time.sleep(0.2)
        for _ in range(2):
            matrix_eigenvalues(200)
            time.sleep(0.2)
        for _ in range(2):
            matrix_svd(150)
            time.sleep(0.2)

    with marimo_profile(refresh_interval=0.4, top_n=12):
        run_matrix_ops()

    return


@app.cell
def _(mo):
    mo.md("""
    ## 🔄 Demo 3: Mixed Workload
    """)
    return


@app.cell
def _(marimo_profile, mo, np, time):
    """Profile a mixed workload with different operations."""

    def cpu_intensive():
        """CPU-bound computation."""
        total = 0
        for i in range(1000000):
            total += i * i
        return total

    def memory_allocation():
        """Memory-intensive operation."""
        arrays = []
        for _ in range(50):
            arrays.append(np.random.rand(1000, 1000))
        return sum(arr.sum() for arr in arrays)

    def io_simulation():
        """Simulate I/O wait."""
        time.sleep(0.1)
        return "done"

    def mixed_workload():
        """Run a mixed workload."""
        for i in range(10):
            if i % 3 == 0:
                cpu_intensive()
            elif i % 3 == 1:
                memory_allocation()
            else:
                io_simulation()
            time.sleep(0.05)

    mo.md("**Running mixed workload...**")

    with marimo_profile(refresh_interval=0.5, top_n=15):
        mixed_workload()

    mo.md("**Mixed workload complete!**")
    return


@app.cell
def _(mo):
    mo.md("""
    ## 📚 Key Features

    - **Live Updates**: Watch profiling stats update in real-time
    - **Automatic Display**: No need to manually show widgets
    - **Cumulative Stats**: Shows total time spent in each function
    - **Top-N Display**: Configurable number of top functions to show
    - **Clean Formatting**: Beautiful HTML output with color coding

    ## 🛠️ Usage

    ```python
    from luketils import marimo_profile

    with marimo_profile(refresh_interval=0.5, top_n=15):
        # Your code here
        my_expensive_function()
    ```

    **Parameters:**
    - `refresh_interval`: Update frequency in seconds (default: 0.5)
    - `top_n`: Number of top functions to display (default: 15)

    ## 💡 Use Cases

    Perfect for:
    - Identifying performance bottlenecks
    - Understanding where time is spent in your code
    - Optimizing machine learning pipelines
    - Debugging slow operations
    - Real-time performance monitoring

    Try modifying the code above to profile your own functions!
    """)
    return


if __name__ == "__main__":
    app.run()
