import cProfile
import pstats
import os
from contextlib import contextmanager
from typing import Any
from dataclasses import dataclass
from pathlib import Path
from functools import lru_cache
import threading
import time
import marimo as mo
import anywidget
import traitlets

from luketils.marimo_profile_renderer import (
    StatsData,
    RenderInput,
    render_initial_html,
    render_no_data_html,
    render_stats_html,
)


@lru_cache(maxsize=128)
def _find_git_root_for_path(path: str) -> Path | None:
    """Find the git root directory for a given path.

    Args:
        path: File or directory path (must be str for caching)

    Returns:
        Git root directory as Path, or None if not in a git repo
    """
    current = Path(path).resolve()
    if current.is_file():
        current = current.parent

    while current != current.parent:
        if (current / ".git").exists():
            return current
        current = current.parent

    return None


@dataclass
class FunctionKey:
    """Represents a function identifier from pstats."""

    filename: str
    line: int | None
    function_name: str


@dataclass
class RawFunctionStats:
    """Raw statistics for a function from pstats.

    Fields from pstats.Stats.stats dictionary values:
    - primitive_call_count: Number of primitive (non-recursive) calls
    - call_count: Total number of calls
    - total_time: Total time spent in this function (excluding subcalls)
    - cumulative_time: Cumulative time spent in this function (including subcalls)
    - callers: Dictionary of callers
    """

    primitive_call_count: int
    call_count: int
    total_time: float
    cumulative_time: float
    callers: dict


@dataclass
class RawStatsEntry:
    """A single entry from pstats.Stats.stats."""

    function_key: FunctionKey
    stats: RawFunctionStats


@dataclass
class FormattedFunctionInfo:
    """Formatted function display information."""

    display_name: str
    file_path: str
    line_number: int


@dataclass
class StatsResult:
    """Result from getting profiling statistics."""

    stats_data: list[StatsData]
    total_time: float


@lru_cache(maxsize=256)
def _find_class_context(
    filename: str, line_number: int, function_name: str
) -> str | None:
    """Find the class name for a method using inspect.

    Args:
        filename: Path to the source file
        line_number: Line number where the function is defined
        function_name: Name of the function

    Returns:
        Class name if the function is a method, None otherwise
    """
    import inspect
    import sys

    try:
        # Try to load the module from the filename
        abs_filename = os.path.abspath(filename)

        # Check if module is already loaded
        for module_name, module in sys.modules.items():
            if module is None:
                continue
            try:
                module_file = inspect.getfile(module)
                if os.path.abspath(module_file) == abs_filename:
                    # Found the module, search for the function
                    for name, obj in inspect.getmembers(module):
                        # Only check actual classes defined in this module
                        if not inspect.isclass(obj):
                            continue

                        # Skip imported classes (not defined in this file)
                        try:
                            class_file = inspect.getfile(obj)
                            if os.path.abspath(class_file) != abs_filename:
                                continue
                        except (TypeError, AttributeError):
                            continue

                        # Check methods in this class
                        for method_name, method in inspect.getmembers(obj):
                            if method_name == function_name and (
                                inspect.ismethod(method) or inspect.isfunction(method)
                            ):
                                return name
                    break
            except (TypeError, AttributeError):
                continue

    except Exception:
        # If inspect fails, fall back to None
        pass

    return None


def _format_function_name(function_name: str, class_name: str | None) -> str:
    """Format a function name, optionally with class context.

    Args:
        function_name: The raw function name from profiling
        class_name: Optional class name if this is a method

    Returns:
        Formatted display name with parentheses (e.g., "MyClass:method()")
    """
    # Handle special/built-in function names
    if not function_name or function_name.strip() == "":
        return "<unknown>"
    elif function_name == "~":
        return "<built-in>"
    elif function_name == "<module>":
        return "<module-level>"

    # Add parentheses to indicate it's callable
    display_name = f"{function_name}()"

    # Format as class method if we have a class context
    if class_name:
        return f"{class_name}:{display_name}"

    return display_name


@lru_cache(maxsize=256)
def _format_file_path(filename: str) -> str:
    """Format a file path by removing git root if possible.

    Args:
        filename: Raw filename from profiling

    Returns:
        Formatted file path
    """
    if not filename or filename in ("<built-in>", "~") or filename.strip() == "":
        return "<built-in>"

    # Try to strip git root (pass as string for caching)
    abs_path = Path(filename).resolve()
    git_root = _find_git_root_for_path(str(abs_path))
    if git_root:
        return str(abs_path.relative_to(git_root))
    return str(abs_path)


def _format_function_key(function_key: FunctionKey) -> FormattedFunctionInfo:
    """Format a function key into display-friendly information.

    Args:
        function_key: The raw function key from pstats

    Returns:
        Formatted function information
    """
    # Detect class context if this is a real source file
    class_name = None
    if (
        function_key.filename
        and function_key.filename not in ("<built-in>", "~", "")
        and function_key.line is not None
    ):
        class_name = _find_class_context(
            filename=function_key.filename,
            line_number=function_key.line,
            function_name=function_key.function_name,
        )

    # Format the function name
    display_name = _format_function_name(
        function_name=function_key.function_name, class_name=class_name
    )

    # Format the file path
    file_path = _format_file_path(filename=function_key.filename)

    # Get line number
    line_number = function_key.line if function_key.line is not None else 0

    return FormattedFunctionInfo(
        display_name=display_name, file_path=file_path, line_number=line_number
    )


def _parse_pstats(stats_dict: dict) -> list[RawStatsEntry]:
    """Parse pstats.Stats.stats dictionary into structured dataclasses.

    Args:
        stats_dict: The stats.stats dictionary from pstats.Stats

    Returns:
        List of RawStatsEntry objects with parsed structure
    """
    entries = []
    for func, (cc, nc, tt, ct, callers) in stats_dict.items():
        # func is (filename, line, function_name)
        if not isinstance(func, tuple) or len(func) != 3:
            raise ValueError(
                f"Expected 3-tuple for func, got: {func!r} (type: {type(func)})"
            )

        filename, line, func_name = func

        # Validate types
        if not isinstance(filename, str):
            raise TypeError(
                f"Expected filename to be str, got {type(filename)}: {filename!r}"
            )
        if not isinstance(line, (int, type(None))):
            raise TypeError(
                f"Expected line to be int or None, got {type(line)}: {line!r}"
            )
        if not isinstance(func_name, str):
            raise TypeError(
                f"Expected func_name to be str, got {type(func_name)}: {func_name!r}"
            )

        entries.append(
            RawStatsEntry(
                function_key=FunctionKey(
                    filename=filename,
                    line=line,
                    function_name=func_name,
                ),
                stats=RawFunctionStats(
                    primitive_call_count=cc,
                    call_count=nc,
                    total_time=tt,
                    cumulative_time=ct,
                    callers=callers,
                ),
            )
        )

    return entries


class LiveProfiler:
    def __init__(self, refresh_interval: float, top_n: int):
        self.refresh_interval = refresh_interval
        self.top_n = top_n
        self.profiler = cProfile.Profile()
        self._mo = None
        self._update_thread: Any | None = None
        self._lock = None
        self._widget_instance = None
        self._is_complete = False
        self._profiler_file = os.path.abspath(__file__)

    def __enter__(self):
        """Start profiling and the live update loop."""
        self.profiler.enable()

        self._mo = mo
        self._lock = threading.Lock()

        class LiveProfilerWidget(anywidget.AnyWidget):
            _esm = """
            function render({ model, el }) {
                let container = document.createElement("div");
                el.appendChild(container);

                function updateDisplay() {
                    const html = model.get("html_content");
                    container.innerHTML = html;
                }

                // Initial render
                updateDisplay();

                // Update when html_content changes
                model.on("change:html_content", () => {
                    updateDisplay();
                });
            }
            export default { render };
            """

            html_content = traitlets.Unicode("").tag(sync=True)

        # Create and display the widget
        self._widget_instance = LiveProfilerWidget()
        initial_html = self._format_initial_html()
        self._widget_instance.html_content = initial_html

        # Display the widget
        widget_display = self._mo.ui.anywidget(self._widget_instance)
        self._mo.output.append(widget_display)

        # Start the update thread using mo.Thread for marimo compatibility
        self._update_thread = self._mo.Thread(target=self._update_loop)
        self._update_thread.start()

        # Return self so the caller can access methods if needed
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop profiling and the live update loop."""
        self.profiler.disable()

        # Signal that profiling is complete
        self._is_complete = True

        # Wait for the thread to finish
        if self._update_thread:
            self._update_thread.join(timeout=2.0)

        # Display final stats (thread should have stopped by now)
        self._display_stats(final=True)

        return False

    def _update_loop(self):
        """Background thread that updates stats periodically."""
        assert self._mo
        thread = self._mo.current_thread()
        # Check exit every 10ms for responsiveness
        check_interval = 0.01

        while not thread.should_exit:
            self._display_stats(final=False)

            # Sleep in small increments to check should_exit frequently
            elapsed = 0.0
            while elapsed < self.refresh_interval and not thread.should_exit:
                sleep_time = min(check_interval, self.refresh_interval - elapsed)
                time.sleep(sleep_time)
                elapsed += sleep_time

    def _should_filter_function(self, filename: str) -> bool:
        """
        Check if a function should be filtered out from profiling results.

        Args:
            filename: The filename where the function is defined

        Returns:
            True if the function should be filtered out, False otherwise
        """
        # Filter out the profiler's own file
        if os.path.abspath(filename) == self._profiler_file:
            return True
        return False

    def _format_initial_html(self) -> str:
        """Format initial loading message."""
        return render_initial_html()

    def _get_stats_data(self) -> StatsResult:
        """Get the current profiling stats as structured data."""
        with self._lock:
            # Get stats sorted by cumulative time (don't strip dirs)
            stats = pstats.Stats(self.profiler)
            stats.sort_stats("cumulative")

            # Extract structured data
            stats_data: list[StatsData] = []

            # Calculate total time from all function cumulative times
            if not hasattr(stats, "stats") or not stats.stats:
                return StatsResult(stats_data=[], total_time=0.0)

            # Parse raw pstats into structured dataclasses
            raw_entries = _parse_pstats(stats.stats)

            # Calculate total time
            total_time = sum(entry.stats.cumulative_time for entry in raw_entries)
            if total_time == 0:
                total_time = 1.0

            # Process each entry
            for entry in raw_entries:
                func_key = entry.function_key
                func_stats = entry.stats

                # Filter out the profiler's own methods
                if self._should_filter_function(func_key.filename):
                    continue

                # Format the function key into display-friendly info
                formatted = _format_function_key(function_key=func_key)

                # Calculate percentages and per-call metrics
                ncalls = func_stats.call_count
                tottime = func_stats.total_time
                cumtime = func_stats.cumulative_time

                stats_data.append(
                    StatsData(
                        function=formatted.display_name,
                        file=formatted.file_path,
                        line=formatted.line_number,
                        ncalls=ncalls,
                        tottime=tottime,
                        cumtime=cumtime,
                        percall_tot=tottime / ncalls if ncalls > 0 else 0,
                        percall_cum=cumtime / ncalls if ncalls > 0 else 0,
                        percent=(cumtime / total_time * 100) if total_time > 0 else 0,
                    )
                )

            # Sort by percentage descending and take top N
            stats_data.sort(key=lambda x: x.percent, reverse=True)
            stats_data = stats_data[: self.top_n]

            return StatsResult(stats_data=stats_data, total_time=total_time)

    def _render_html(self, stats_result: StatsResult, final: bool) -> str | None:
        """Render HTML for the given stats result.

        Args:
            stats_result: The profiling statistics to render
            final: Whether this is the final render

        Returns:
            HTML string to display, or None to keep the current display
        """
        if not stats_result.stats_data:
            if not final:
                return None  # Keep showing "Starting profiler..."
            else:
                return render_no_data_html()

        render_input = RenderInput(
            stats_data=stats_result.stats_data,
            total_time=stats_result.total_time,
            final=final,
            top_n=self.top_n,
        )
        return render_stats_html(render_input=render_input)

    def _display_stats(self, final: bool):
        """Display the current profiling stats."""
        if self._widget_instance is None:
            return

        # Don't update if profiling is complete (unless this IS the final update)
        if self._is_complete and not final:
            return

        stats_result = self._get_stats_data()
        html = self._render_html(stats_result=stats_result, final=final)

        if html is not None:
            # Update the widget's html_content trait
            # This will trigger the JavaScript model.on("change:html_content") handler
            self._widget_instance.html_content = html


@contextmanager
def marimo_profile(refresh_interval: float = 0.05, top_n: int = 15):
    profiler = LiveProfiler(refresh_interval=refresh_interval, top_n=top_n)
    with profiler:
        yield profiler
