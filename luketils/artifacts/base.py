import os

base = os.getenv("ARTIFACTS", "artifacts")


def set_base(path):
    global base
    base = path


def get_base():
    return base
