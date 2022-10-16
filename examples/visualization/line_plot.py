from luketils import visualization
import numpy as np

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
