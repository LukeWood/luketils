import os


def ensure_exists(path):
    """ensure a nested directory exists."""
    if not os.path.exists(path):
        os.makedirs(path)
