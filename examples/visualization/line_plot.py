"""
Title: Concisely create a line plot
Author: [lukewood](https://lukewood.xyz)
Date created: 2022/10/16
Last modified: 2022/10/16
Description: Concisely create a line plot with `luketils.visualization.line_plot()`.
"""
import numpy as np
from luketils import visualization

"""
`luketils.visualization.line_plot` is primarily a convenience wrapped around
`matplotlib`.  It allows you to more concisely specify metric names and plot multiple
lines to the same plot:
"""

metrics_to_plot = {
    "Train Box Loss": np.array(range(30)),
    "Validation Box Loss": np.array(range(30)) * 2,
    "Train Classification Loss": np.array(range(30)) * 1.5,
    "Validation Classification Loss": np.array(range(30)) * 0.3,
}

visualization.line_plot(
    data=metrics_to_plot,
    title="All Losses",
    xlabel="Epochs",
    ylabel="Box Loss",
    legend=True,
    show=True,
)
