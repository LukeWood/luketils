import matplotlib.pyplot as plt


def line_plot(
    data,
    title=None,
    legend=None,
    xlabel=None,
    ylabel=None,
    show=None,
    path=None,
    palette="mako_r",
):
    """Produces a line plot based on a dictionary of metrics and labels."""
    import seaborn as sns

    if show and path is not None:
        raise ValueError("Expected either `show` or `path` to be set, but not both.")
    if path is None and show is None:
        show = True
    palette = sns.color_palette("mako_r", len(data.keys()))

    sns.lineplot(data=data, palette=palette)
    plt.legend(list(data.keys()))

    if xlabel:
        plt.xlabel(xlabel)
    if ylabel:
        plt.ylabel(ylabel)

    plt.suptitle(title)

    if path is None and not show:
        return
    if path is not None:
        plt.savefig(
            fname=path,
            pad_inches=0,
            bbox_inches="tight",
            transparent=transparent,
            dpi=dpi,
        )
        plt.close()
    elif show:
        plt.show()
        plt.close()
