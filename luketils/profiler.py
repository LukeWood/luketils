from __future__ import annotations

from functools import wraps
from time import perf_counter
from typing import Callable, ParamSpec, Protocol, TypeVar, cast

import polars as pl
import plotly.express as px

P = ParamSpec("P")
R = TypeVar("R")


class ProfiledCallable(Protocol[P, R]):
    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R: ...

    def times(self) -> pl.DataFrame: ...

    def plot_execution_times(self) -> px.Figure: ...

    def histogram(self) -> px.Figure: ...


def _times_df(runtimes: list[float]) -> pl.DataFrame:
    return pl.DataFrame(
        {
            "count": list(range(1, len(runtimes) + 1)),
            "runtime": runtimes,
        }
    )


def _plot_execution_times(df: pl.DataFrame) -> px.Figure:
    return px.scatter(
        df.to_pandas(),
        x="count",
        y="runtime",
        title="Execution Times",
        labels={"count": "Count", "runtime": "Runtime (s)"},
    )


def _histogram(df: pl.DataFrame) -> px.Figure:
    return px.histogram(
        df.to_pandas(),
        x="runtime",
        title="Runtime Histogram",
        labels={"runtime": "Runtime (s)"},
    )


def _rebuild_profiled(func: Callable[P, R]) -> ProfiledCallable[P, R]:
    return profile()(func)


def profile() -> Callable[[Callable[P, R]], ProfiledCallable[P, R]]:
    def decorator(func: Callable[P, R]) -> ProfiledCallable[P, R]:
        runtimes: list[float] = []

        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            start = perf_counter()
            try:
                return func(*args, **kwargs)
            finally:
                end = perf_counter()
                runtimes.append(end - start)

        def times() -> pl.DataFrame:
            return _times_df(runtimes)

        def plot_execution_times() -> px.Figure:
            return _plot_execution_times(times())

        def histogram() -> px.Figure:
            return _histogram(times())

        def __reduce__() -> tuple[
            Callable[[Callable[P, R]], Callable[P, R]], tuple[Callable[P, R]]
        ]:
            return (_rebuild_profiled, (func,))

        wrapper.times = times  # type: ignore[attr-defined]
        wrapper.plot_execution_times = plot_execution_times  # type: ignore[attr-defined]
        wrapper.histogram = histogram  # type: ignore[attr-defined]
        wrapper.__reduce__ = __reduce__  # type: ignore[attr-defined]

        return cast(ProfiledCallable[P, R], wrapper)

    return decorator
