# Marimo Profiler Design Considerations

## Current Implementation

The current `marimo_profile` uses:
- **anywidget** for a single, live-updating widget
- **mo.Thread** for background updates from Python
- **traitlets** for Python ↔ JavaScript synchronization
- Periodic polling (refresh_interval) to update stats

### Pros
✓ Single widget that updates in-place
✓ Works with marimo's reactive model
✓ Clean separation of concerns

### Cons
✗ Requires anywidget dependency
✗ Thread management complexity
✗ Potential race conditions (fixed with `_is_complete` flag)
✗ Polling overhead

---

## Alternative Approaches

### 1. **Simple Append-Only (Current Fallback)**

```python
def _display_stats(self, final: bool = False):
    html = self._format_stats_html(stats_str, final=final)
    self._mo.output.append(self._mo.Html(html))
```

**Pros:**
- No anywidget dependency
- No widget state management
- Simple and reliable

**Cons:**
- Creates multiple widgets (visual clutter)
- Shows progression but not "live update"

**Best for:** Quick debugging, simple cases

---

### 2. **mo.status.spinner() Approach**

```python
with mo.status.spinner(title="Profiling") as spinner:
    while not done:
        stats = get_current_stats()
        spinner.update(subtitle=format_top_function(stats))
        time.sleep(refresh_interval)
```

**Pros:**
- Built-in marimo API
- No external dependencies
- Designed for live status updates

**Cons:**
- Limited to text/subtitle updates
- Can't show full profiling table
- Less visual customization

**Best for:** Simple progress indicators

---

### 3. **Reactive State with mo.state()**

```python
# In cell 1: Create reactive state
profiler_state = mo.state({"html": "Starting..."})

# In cell 2: Display widget that reacts to state
profiler_state.value["html"]  # Auto-updates when state changes

# In cell 3: Background thread updates state
def update_loop():
    while running:
        profiler_state.set({"html": get_profiling_html()})
```

**Pros:**
- Uses marimo's reactive paradigm
- Automatic UI updates
- No anywidget needed

**Cons:**
- Requires multi-cell setup (not context manager friendly)
- State management across cells
- Thread safety concerns

**Best for:** Interactive notebooks with manual control

---

### 4. **Event-Driven with mo.ui.refresh()**

```python
refresh_button = mo.ui.refresh(options=[0.5, 1, 2])

@refresh_button
def show_profiler_stats():
    return mo.Html(get_current_profiling_stats())
```

**Pros:**
- User-controlled updates
- No threading needed
- Simple and explicit

**Cons:**
- Manual refresh required
- Not "live" updates
- Requires user interaction

**Best for:** Manual/interactive profiling

---

### 5. **Post-Processing Only (Simplest)**

```python
with marimo_profile() as profiler:
    # Run code
    expensive_operation()

# Only show results at the end
profiler.display()
```

**Pros:**
- No threading complexity
- No live updates needed
- Minimal dependencies

**Cons:**
- No live feedback during execution
- Can't see progress

**Best for:** Short operations, final analysis only

---

## Recommended Hybrid Approach

Offer **multiple modes** via a parameter:

```python
@contextmanager
def marimo_profile(
    refresh_interval: float = 0.5,
    top_n: int = 15,
    mode: str = "live"  # "live", "append", "final_only"
):
    """
    Args:
        mode:
            - "live": Single widget with live updates (requires anywidget)
            - "append": Append snapshots over time (no deps)
            - "final_only": Show results only at end (simplest)
    """
    if mode == "live":
        return LiveProfiler(...)
    elif mode == "append":
        return AppendProfiler(...)
    else:
        return FinalOnlyProfiler(...)
```

### Benefits:
- Users can choose complexity vs features
- Graceful degradation (fallback if anywidget not available)
- Different use cases supported

---

## Implementation Improvements

### Current Issues & Fixes

#### 1. **Race Condition (FIXED)**
- **Issue:** Thread continues updating after `__exit__`
- **Fix:** Added `_is_complete` flag
  ```python
  if self._is_complete and not final:
      return  # Don't update if already complete
  ```

#### 2. **Thread Cleanup**
- Consider using `threading.Event` instead of checking `thread.should_exit` in loop
  ```python
  self._stop_event = threading.Event()

  def _update_loop(self):
      while not self._stop_event.is_set():
          self._display_stats(final=False)
          self._stop_event.wait(timeout=self.refresh_interval)
  ```

#### 3. **Error Handling**
- Add logging instead of silent failures
  ```python
  except Exception as e:
      import sys
      print(f"Profiler error: {e}", file=sys.stderr)
  ```

#### 4. **Resource Cleanup**
- Ensure profiler is disabled even if exception occurs
  ```python
  try:
      self.profiler.enable()
      # ... setup widget, thread ...
  except:
      self.profiler.disable()  # Cleanup on setup failure
      raise
  ```

---

## Performance Considerations

### Current Overhead
- Background thread wakes up every 0.1s to check `should_exit`
- Stats computation on every update (can be expensive)
- HTML string generation and widget update

### Optimizations

1. **Lazy Stats Collection**
   ```python
   # Only compute stats if widget is visible
   if not widget_visible:
       return
   ```

2. **Delta Updates**
   ```python
   # Only update if stats changed significantly
   if not stats_changed_significantly(old_stats, new_stats):
       return
   ```

3. **Async Updates**
   ```python
   # Use asyncio instead of threading
   async def _update_loop(self):
       while not self._stop_event.is_set():
           await asyncio.sleep(self.refresh_interval)
           await self._display_stats_async()
   ```

4. **Sampling Instead of Full Profiling**
   ```python
   # Use sampling profiler for less overhead
   import yappi  # or py-spy
   ```

---

## Testing Strategy

### Unit Tests
```python
def test_profiler_completes_without_flicker():
    with marimo_profile(refresh_interval=0.1) as p:
        time.sleep(0.5)
    # Widget should show "Complete" and not flicker back to "Profiling"
    assert p._widget_instance.html_content.contains("Complete")
```

### Integration Tests
```python
def test_expensive_computation():
    with marimo_profile():
        result = matrix_multiply(1000)
    # Should show multiple updates during execution
```

---

## Future Enhancements

1. **Flame Graph View**
   - Interactive flame graph in widget
   - Click to zoom into functions

2. **Memory Profiling**
   - Track memory usage alongside CPU time
   - Show memory allocations

3. **Comparison Mode**
   - Profile multiple runs
   - Show diffs between runs

4. **Export Options**
   - Save profile data to file
   - Export as Chrome trace format
   - Generate static HTML report

5. **Smart Refresh**
   - Faster updates when things are changing
   - Slower updates when stable
   - Adaptive refresh interval

---

## Conclusion

The current implementation with anywidget + mo.Thread is solid for **live updates** with **good UX**. The `_is_complete` flag fix resolves the flickering issue.

For maximum flexibility, consider implementing **multiple modes** (live/append/final) so users can choose based on their needs and available dependencies.
