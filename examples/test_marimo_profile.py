import marimo

__generated_with = "0.19.6"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    return


@app.cell
def _():
    import time
    import math
    from luketils import marimo_profile
    return (marimo_profile,)


@app.cell
def _(marimo_profile):
    def matrix_multiply(size):
        matrix_a = [[i * j for j in range(size)] for i in range(size)]
        matrix_b = [[i + j for j in range(size)] for i in range(size)]
        result = [[0 for _ in range(size)] for _ in range(size)]
        for i in range(size):
            for j in range(size):
                for k in range(size):
                    result[i][j] += matrix_a[i][k] * matrix_b[k][j]
        return result

    def nested_computation():
        """Run multiple matrix operations."""
        results = []
        for size in [100, 150, 200, 150, 100, 5000]:
            results.append(matrix_multiply(size))
        return results

    with marimo_profile(top_n=10):
        matrix_results = nested_computation()
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
