def experiment_name(base):
    now = datetime.now()
    return f"{base}-{now.strftime('%m/%d/%y-%H:%M%S')}"
