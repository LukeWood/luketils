from luketils.artifacts.base import get_base


def path(path):
    base = get_base()
    if base is None:
        return None

    path = f"{base}/{path}"
    add_artifact(path)
    return path
