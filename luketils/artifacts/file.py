import contextlib
from luketils.artifacts.base import get_base

@contextlib.contextmanager
def file(path):
    with open(path, "w") as f:
        yield f
