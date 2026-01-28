"""HTML rendering for marimo profiler.

This module contains pure rendering functions for the LiveProfiler.
"""

from dataclasses import dataclass


@dataclass
class StatsData:
    """Data for a single function's profiling statistics."""

    function: str
    file: str
    line: int
    ncalls: int
    tottime: float
    cumtime: float
    percall_tot: float
    percall_cum: float
    percent: float


@dataclass
class RenderInput:
    """Input data for rendering profiling results."""

    stats_data: list[StatsData]
    total_time: float
    final: bool
    top_n: int


def render_initial_html() -> str:
    """Format initial loading message."""
    return """
    <div style="border: 2px solid #3b82f6; border-radius: 12px; padding: 20px; background: linear-gradient(135deg, #1e1e1e 0%, #2d2d2d 100%); margin: 10px 0; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);">
        <div style="display: flex; align-items: center;">
            <span style="font-size: 22px; font-weight: bold; color: #3b82f6; text-shadow: 0 2px 4px rgba(0,0,0,0.3);">⏱️  Starting profiler...</span>
        </div>
    </div>
    """


def render_no_data_html() -> str:
    """Format HTML for when no profiling data was collected."""
    return """
    <div style="border: 2px solid #10b981; border-radius: 12px; padding: 20px; background: linear-gradient(135deg, #1e1e1e 0%, #2d2d2d 100%); margin: 10px 0; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);">
        <div style="display: flex; align-items: center;">
            <span style="font-size: 22px; font-weight: bold; color: #10b981; text-shadow: 0 2px 4px rgba(0,0,0,0.3);">✓ Profiling Complete</span>
            <span style="margin-left: 16px; color: #9ca3af;">No profiling data collected</span>
        </div>
    </div>
    """


def _render_stat_row(stat: StatsData, index: int) -> str:
    """Render a single stats row as HTML.

    Args:
        stat: The stats data for a single function
        index: The row index for alternating colors

    Returns:
        HTML string for the row
    """
    # Alternate row colors
    bg_color = "#1a1f2e" if index % 2 == 0 else "#151923"

    # Color code percentage
    pct = stat.percent
    if pct > 50:
        pct_color = "#ef4444"  # Red for hot paths
    elif pct > 20:
        pct_color = "#f59e0b"  # Orange
    elif pct > 5:
        pct_color = "#10b981"  # Green
    else:
        pct_color = "#6b7280"  # Gray

    # Create percentage bar
    bar_width = min(pct, 100)
    pct_bar = f'<div style="background: {pct_color}; width: {bar_width}%; height: 100%; border-radius: 2px; opacity: 0.3;"></div>'

    # Style function name differently for special cases
    func_color = "#60a5fa"  # Default blue
    if stat.function.startswith("<"):
        func_color = "#a78bfa"  # Purple for special functions like <lambda>, <built-in>

    # Handle line number display
    line_display = stat.line if stat.line else "?"
    location = f"{stat.file}:{line_display}"

    return f"""
    <tr style="background: {bg_color};">
        <td style="padding: 8px 12px; color: {func_color}; font-weight: 500; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 250px;" title="{stat.function}">{stat.function}</td>
        <td style="padding: 8px 12px; color: #9ca3af; font-family: 'Monaco', 'Menlo', monospace; font-size: 11px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 200px;" title="{location}">{location}</td>
        <td style="padding: 8px 12px; text-align: right; color: #e5e7eb; font-family: 'Monaco', 'Menlo', monospace;">{stat.ncalls}</td>
        <td style="padding: 8px 12px; text-align: right; color: #e5e7eb; font-family: 'Monaco', 'Menlo', monospace;">{stat.tottime:.4f}</td>
        <td style="padding: 8px 12px; text-align: right; color: #e5e7eb; font-family: 'Monaco', 'Menlo', monospace;">{stat.percall_tot:.6f}</td>
        <td style="padding: 8px 12px; text-align: right; color: #fbbf24; font-family: 'Monaco', 'Menlo', monospace; font-weight: 600;">{stat.cumtime:.4f}</td>
        <td style="padding: 8px 12px; text-align: right; color: #e5e7eb; font-family: 'Monaco', 'Menlo', monospace;">{stat.percall_cum:.6f}</td>
        <td style="padding: 8px 12px; text-align: right; position: relative;">
            <div style="position: absolute; top: 0; left: 0; right: 0; bottom: 0; z-index: 0;">{pct_bar}</div>
            <span style="position: relative; z-index: 1; color: {pct_color}; font-family: 'Monaco', 'Menlo', monospace; font-weight: 700;">{pct:.1f}%</span>
        </td>
    </tr>
    """


def render_stats_html(render_input: RenderInput) -> str:
    """Format stats as HTML table for display.

    This is a pure function that takes all necessary inputs and returns HTML.

    Args:
        render_input: All data needed for rendering

    Returns:
        Complete HTML string for the stats display
    """
    status = "✓ Profiling Complete" if render_input.final else "⏱️  Profiling..."
    color = "#10b981" if render_input.final else "#3b82f6"

    # Build table rows
    rows_html = "".join(
        _render_stat_row(stat, i) for i, stat in enumerate(render_input.stats_data)
    )

    html = f"""
    <div style="border: 2px solid {color}; border-radius: 12px; padding: 20px; background: linear-gradient(135deg, #1e1e1e 0%, #2d2d2d 100%); margin: 10px 0; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);">
        <div style="display: flex; align-items: center; margin-bottom: 16px;">
            <span style="font-size: 22px; font-weight: bold; color: {color}; text-shadow: 0 2px 4px rgba(0,0,0,0.3);">{status}</span>
            <span style="margin-left: auto; color: #9ca3af; font-size: 14px;">
                Top {render_input.top_n} functions by cumulative time · Total: {render_input.total_time:.4f}s
            </span>
        </div>
        <div style="overflow-x: auto;">
            <table style="width: 100%; border-collapse: collapse; font-size: 13px;">
                <thead>
                    <tr style="background: linear-gradient(180deg, #374151 0%, #1f2937 100%); border-bottom: 2px solid {color};">
                        <th style="padding: 12px; text-align: left; color: #f3f4f6; font-weight: 600; text-transform: uppercase; font-size: 11px; letter-spacing: 0.5px;">Function</th>
                        <th style="padding: 12px; text-align: left; color: #f3f4f6; font-weight: 600; text-transform: uppercase; font-size: 11px; letter-spacing: 0.5px;">Location</th>
                        <th style="padding: 12px; text-align: right; color: #f3f4f6; font-weight: 600; text-transform: uppercase; font-size: 11px; letter-spacing: 0.5px;">Calls</th>
                        <th style="padding: 12px; text-align: right; color: #f3f4f6; font-weight: 600; text-transform: uppercase; font-size: 11px; letter-spacing: 0.5px;">TotTime</th>
                        <th style="padding: 12px; text-align: right; color: #f3f4f6; font-weight: 600; text-transform: uppercase; font-size: 11px; letter-spacing: 0.5px;">Per Call</th>
                        <th style="padding: 12px; text-align: right; color: #f3f4f6; font-weight: 600; text-transform: uppercase; font-size: 11px; letter-spacing: 0.5px;">CumTime</th>
                        <th style="padding: 12px; text-align: right; color: #f3f4f6; font-weight: 600; text-transform: uppercase; font-size: 11px; letter-spacing: 0.5px;">Per Call</th>
                        <th style="padding: 12px; text-align: right; color: #f3f4f6; font-weight: 600; text-transform: uppercase; font-size: 11px; letter-spacing: 0.5px;">% Total</th>
                    </tr>
                </thead>
                <tbody>
                    {rows_html}
                </tbody>
            </table>
        </div>
    </div>
    """
    return html
