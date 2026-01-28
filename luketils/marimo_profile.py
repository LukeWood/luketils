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


def _normalize_function_name(raw_name: str) -> str:
    """Normalize function name to be readable, replacing non-printable characters.

    Args:
        raw_name: The raw function name from pstats

    Returns:
        Normalized function name with non-printable chars replaced
    """
    if not raw_name:
        return "<empty>"

    # Check if name has non-printable characters
    has_non_printable = any(not c.isprintable() for c in raw_name)

    if has_non_printable:
        # Replace non-printable with hex representation
        normalized = ""
        for c in raw_name:
            if c.isprintable():
                normalized += c
            else:
                normalized += f"\\x{ord(c):02x}"
        return f"<{normalized}>"

    return raw_name


def _format_function_name(function_name: str, class_name: str | None) -> str:
    """Format a function name, optionally with class context.

    Args:
        function_name: The raw function name from profiling
        class_name: Optional class name if this is a method

    Returns:
        Formatted display name with parentheses (e.g., "MyClass:method()")

    Raises:
        ValueError: If function_name is invalid or would produce empty output
    """
    # Validate input
    if not isinstance(function_name, str):
        raise TypeError(
            f"function_name must be str, got {type(function_name)}: {function_name!r}"
        )

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
        result = f"{class_name}:{display_name}"
    else:
        result = display_name

    # Validate output - should never be just "()"
    if result == "()":
        raise ValueError(
            f"Invalid formatted name '()' produced from function_name={function_name!r}, "
            f"class_name={class_name!r}"
        )

    return result


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

    Raises:
        ValueError: If formatting produces invalid output
    """
    # Validate input
    if not isinstance(function_key, FunctionKey):
        raise TypeError(f"Expected FunctionKey, got {type(function_key)}")

    # Normalize the function name first (handles non-printable characters)
    normalized_name = _normalize_function_name(function_key.function_name)

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

    # Format the function name (this will raise if it produces "()")
    display_name = _format_function_name(
        function_name=normalized_name, class_name=class_name
    )

    # Format the file path
    file_path = _format_file_path(filename=function_key.filename)

    # Get line number
    line_number = function_key.line if function_key.line is not None else 0

    # Final validation
    if not display_name or display_name.strip() == "":
        raise ValueError(f"Empty display_name produced from {function_key!r}")

    return FormattedFunctionInfo(
        display_name=display_name, file_path=file_path, line_number=line_number
    )


def _parse_pstats(stats_dict: dict) -> list[RawStatsEntry]:
    """Parse pstats.Stats.stats dictionary into structured dataclasses.

    Args:
        stats_dict: The stats.stats dictionary from pstats.Stats

    Returns:
        List of RawStatsEntry objects with parsed structure

    Raises:
        ValueError: If the stats data structure is invalid
        TypeError: If data types are incorrect
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

        # Additional validation - catch suspicious function names
        if func_name.strip() == "" and filename not in ("<built-in>", "~", ""):
            raise ValueError(
                f"Empty function name for non-builtin file: {filename!r} line {line}"
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
        import traceback

        assert self._mo
        thread = self._mo.current_thread()
        # Check exit every 10ms for responsiveness
        check_interval = 0.01

        try:
            while not thread.should_exit:
                try:
                    self._display_stats(final=False)
                except Exception as e:
                    # Log the error and display it to the user
                    error_msg = f"Error updating profiler stats: {e}"
                    print(f"\n{'=' * 60}")
                    print(f"PROFILER ERROR:")
                    print(error_msg)
                    print(f"{'=' * 60}")
                    traceback.print_exc()
                    print(f"{'=' * 60}\n")

                    # Try to display error in widget
                    if self._widget_instance:
                        error_html = f"""
                        <div style="border: 2px solid #ef4444; border-radius: 12px; padding: 20px; background: linear-gradient(135deg, #1e1e1e 0%, #2d2d2d 100%); margin: 10px 0;">
                            <div style="color: #ef4444; font-weight: bold; font-size: 18px; margin-bottom: 10px;">⚠️ Profiler Error</div>
                            <div style="color: #fca5a5; font-family: monospace; font-size: 12px; white-space: pre-wrap;">{error_msg}</div>
                            <div style="color: #9ca3af; font-size: 11px; margin-top: 10px;">Check console for full traceback</div>
                        </div>
                        """
                        self._widget_instance.html_content = error_html

                    # Re-raise to crash properly
                    raise

                # Sleep in small increments to check should_exit frequently
                elapsed = 0.0
                while elapsed < self.refresh_interval and not thread.should_exit:
                    sleep_time = min(check_interval, self.refresh_interval - elapsed)
                    time.sleep(sleep_time)
                    elapsed += sleep_time

        except Exception as e:
            # Catch any unexpected errors in the loop itself
            print(f"\n{'=' * 60}")
            print(f"FATAL PROFILER ERROR:")
            print(f"{e}")
            print(f"{'=' * 60}")
            traceback.print_exc()
            print(f"{'=' * 60}\n")

    def _should_filter_function(self, filename: str, function_name: str) -> bool:
        """
        Check if a function should be filtered out from profiling results.

        Args:
            filename: The filename where the function is defined
            function_name: The name of the function

        Returns:
            True if the function should be filtered out, False otherwise
        """
        # Debug: Log if we see empty function name
        if function_name == "":
            print(f"DEBUG FILTER: Empty function name! filename={filename!r}")
            return True

        # Filter out the profiler's own file
        if os.path.abspath(filename) == self._profiler_file:
            return True

        # Filter out marimo framework internals
        marimo_internal_paths = [
            "marimo/_output/",
            "marimo/_runtime/",
            "marimo/_plugins/",
            "marimo/_server/",
        ]
        for internal_path in marimo_internal_paths:
            if internal_path in filename.replace("\\", "/"):
                return True

        # Filter out empty or whitespace-only function names
        if not function_name or not function_name.strip():
            print(f"DEBUG FILTER: Whitespace-only function name! {function_name!r} filename={filename!r}")
            return True

        # Filter out function names with only non-printable/weird characters
        printable_chars = [c for c in function_name if c.isprintable() and c.strip()]
        if len(printable_chars) == 0:
            print(f"DEBUG FILTER: Non-printable function name! {function_name!r} bytes={function_name.encode('utf-8')!r}")
            return True

        # Filter out marimo cell functions (they show up as __ or variations)
        if function_name.strip() == "__":
            return True

        # Also filter if function name is just underscores (up to 4)
        stripped = function_name.strip()
        if stripped and all(c == "_" for c in stripped) and len(stripped) <= 4:
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
            if not hasattr(stats, "stats"):
                return StatsResult(stats_data=[], total_time=0.0)

            # Parse raw pstats into structured dataclasses
            raw_entries = _parse_pstats(stats.stats)  # type: ignore

            # Filter entries first, before calculating totals
            filtered_entries = []
            for entry in raw_entries:
                func_name = entry.function_key.function_name
                filename = entry.function_key.filename

                # Debug: Log only truly problematic entries (empty or non-printable)
                has_non_printable = any(not c.isprintable() for c in func_name) if func_name else False
                if func_name == "" or not func_name.strip() or has_non_printable:
                    print(f"DEBUG PRE-FILTER: Found problematic entry!")
                    print(f"  func_name repr: {func_name!r}")
                    print(f"  func_name bytes: {func_name.encode('utf-8')!r}")
                    print(f"  func_name len: {len(func_name)}")
                    print(f"  Has non-printable: {has_non_printable}")
                    print(f"  filename={filename!r}")
                    print(f"  Calling filter...")

                should_filter = self._should_filter_function(
                    filename=filename,
                    function_name=func_name,
                )

                if func_name == "" or not func_name.strip() or has_non_printable:
                    print(f"  Filter returned: {should_filter}")

                if not should_filter:
                    filtered_entries.append(entry)

            # Calculate total time from filtered entries only
            total_time = sum(entry.stats.cumulative_time for entry in filtered_entries)
            if total_time == 0:
                total_time = 1.0

            # Process each filtered entry
            for entry in filtered_entries:
                func_key = entry.function_key
                func_stats = entry.stats

                # Debug: Log only truly empty/problematic function names
                stripped = func_key.function_name.strip()
                if not stripped or stripped in ("__", "()", "~") or (all(c == "_" for c in stripped)):
                    print(f"DEBUG: Processing empty/problematic function: {func_key.function_name!r} in {func_key.filename}")

                # Format the function key into display-friendly info
                formatted = _format_function_key(function_key=func_key)

                # Debug: Log if we get "()" after formatting
                if formatted.display_name == "()":
                    print(f"DEBUG: Got '()' display_name from:")
                    print(f"  Raw function_name: {func_key.function_name!r}")
                    print(f"  Filename: {func_key.filename}")
                    print(f"  Line: {func_key.line}")
                    continue

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
                        debug_raw_name=func_key.function_name,  # Debug: show raw name
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
        """Display the current profiling stats.

        Raises any exceptions to be caught by the calling thread's error handler.
        """
        if self._widget_instance is None:
            return

        # Don't update if profiling is complete (unless this IS the final update)
        if self._is_complete and not final:
            return

        # Get stats - let exceptions propagate to thread error handler
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
