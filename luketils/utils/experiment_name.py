def experiment_name(base):
    """creates an experiment name based on the current timestamp and a base string.

    Args:
        base: the base string to interpolate in to the experimet name.
    """
    now = datetime.now()
    return f"{base}-{now.strftime('%m/%d/%y-%H:%M%S')}"
