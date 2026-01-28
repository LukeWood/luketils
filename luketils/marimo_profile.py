import cProfile
import pstats
import os
from contextlib import contextmanager
from typing import Any
from dataclasses import dataclass
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


@dataclass
class StatsResult:
    """Result from getting profiling statistics."""

    stats_data: list[StatsData]
    total_time: float


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
        while not thread.should_exit:
            self._display_stats(final=False)
            # Sleep in small increments to check should_exit more frequently
            for _ in range(int(self.refresh_interval * 10)):
                if thread.should_exit:
                    break
                time.sleep(0.1)

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

    def _find_git_root(self, path: str) -> str | None:
        """Find the git root directory by walking up from the given path."""
        current = os.path.abspath(path)
        while True:
            if os.path.exists(os.path.join(current, ".git")):
                return current
            parent = os.path.dirname(current)
            if parent == current:
                return None
            current = parent

    def _format_path(self, filename: str) -> str:
        """Format a file path by removing git root if possible."""
        if not filename or filename in ("<built-in>", "~"):
            return filename

        # Try to strip git root
        abs_path = os.path.abspath(filename)
        git_root = self._find_git_root(abs_path)
        if git_root:
            # Return path relative to git root
            return os.path.relpath(abs_path, git_root)
        return abs_path

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

            total_time = sum(item[3] for item in stats.stats.values())
            if total_time == 0:
                total_time = 1.0

            # Get all functions and calculate percentages
            for func, (cc, nc, tt, ct, callers) in stats.stats.items():
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

                # Filter out the profiler's own methods
                if self._should_filter_function(filename):
                    continue

                # Handle empty or special function names
                if not func_name or func_name.strip() == "":
                    func_name = "<unknown>"
                elif func_name == "~":
                    func_name = "<built-in>"
                elif func_name == "<module>":
                    func_name = "<module-level>"

                # Clean up filename for built-ins
                if not filename or filename.strip() == "" or filename == "~":
                    filename = "<built-in>"
                else:
                    # Format the path (remove git root)
                    filename = self._format_path(filename)

                # Ensure line is an integer
                if line is None:
                    line = 0

                # Use the cleaned function name directly
                display_name = func_name

                stats_data.append(
                    StatsData(
                        function=display_name,
                        file=filename,
                        line=line,
                        ncalls=nc,
                        tottime=tt,
                        cumtime=ct,
                        percall_tot=tt / nc if nc > 0 else 0,
                        percall_cum=ct / nc if nc > 0 else 0,
                        percent=(ct / total_time * 100) if total_time > 0 else 0,
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
