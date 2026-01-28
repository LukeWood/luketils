"""Quick test of marimo_profile"""

import marimo

__generated_with = "0.9.0"
app = marimo.App(width="medium")


@app.cell
def __():
    import marimo as mo
    import time
    return mo, time


@app.cell
def __(mo):
    mo.md("# Testing marimo_profile!")
    return


@app.cell
def __(mo, time):
    from luketils import marimo_profile

    def slow_function():
        """A slow function to profile."""
        total = 0
        for i in range(500000):
            total += i ** 2
        return total

    def another_slow_function():
        """Another slow function."""
        result = 1
        for i in range(1, 100000):
            result = (result * i) % 1000000
        return result

    def fast_function():
        """A fast function."""
        return sum(range(100))

    mo.md("## Running profiler...")

    # Profile the code!
    with marimo_profile(refresh_interval=0.3, top_n=10):
        for i in range(20):
            slow_function()
            another_slow_function()
            fast_function()
            time.sleep(0.1)

    mo.md("✅ **Done!**")
    return (
        marimo_profile,
        slow_function,
        another_slow_function,
        fast_function,
    )


if __name__ == "__main__":
    app.run()
