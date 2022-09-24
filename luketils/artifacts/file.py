import contextlib
from luketils.artifacts.base import get_base
from luketils.artifacts.collection import add_artifact


@contextlib.contextmanager
def file(path):
    with open(path, "w") as f:
        add_artifact(f)
        yield f
