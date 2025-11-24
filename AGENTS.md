# Macro goals

the goal of luketils is to be a suite of utility functions in python that I can continue using for years.
Every project we implement should reflect these goals.
If you can, split the functions into many sub-functions, each of which is really useful.
Focus on modularity, reusability, and functional programming.

# Python style guide

- do not write try/except, ever.  LET IT CRASH
- only create empty __init__.py files,
- use modern type hints, `dict` not `Dict`, `x|None` not optional[x]
- only use frozen dataclasses, unless mutability is needed to achieve good performance.  When absolutely needed you may use mutable dataclsses as implementation details, not API surfaces.
- type annotations
- everything should be functional

