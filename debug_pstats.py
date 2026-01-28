"""Debug script to see raw pstats function names."""

import cProfile
import pstats
import time

# Profile something simple
profiler = cProfile.Profile()
profiler.enable()

def test_func():
    time.sleep(0.01)

test_func()
profiler.disable()

# Check raw stats
stats = pstats.Stats(profiler)
print("Raw function names from pstats:")
for func, data in list(stats.stats.items())[:10]:
    filename, line, func_name = func
    print(f"  Function name: {func_name!r}")
    print(f"  Full: ({filename!r}, {line}, {func_name!r})")
    print()
