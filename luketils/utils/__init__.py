import os


def ensure_exists(path):
    """ensure a nested directory exists."""
     os.makedirs(path, exist_ok=True)
