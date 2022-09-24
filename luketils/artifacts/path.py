from luketils.artifacts.base import get_base


def path(path):
    path = f"{get_base()}/{path}"
    add_artifact(path)
    return path
