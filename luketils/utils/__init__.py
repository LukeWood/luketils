import os
from datetime import datetime

def ensure_exists(path):
    """ensure a nested directory exists."""
     os.makedirs(path, exist_ok=True)

def experiment_name(base):
    now = datetime.now()
    return f"{base}-{now.strftime('%m/%d/%y-%H:%M%S')}"
