import matplotlib.pyplot as plt
from sklearn.decomposition import PCA

from luketils.utils.to_numpy import to_numpy


# TODO(lukewood): support TSNE.
def plot_latents(
    x,
    y,
    labels,
    dimensions=3,
    title=None,
    legend=True,
    legend_location="auto",
    figure_size=(6, 6),
    transparent=True,
    dpi=60,
    path=None,
    show=None,
):
    """plot_latents() plots the latent representation of `x`.

    These plots are useful for visualizing high dimensional spaces.

    Usage:
    ```python
    encoder = keras.Sequential(
        [
            keras.Input(shape=input_shape),
            layers.Conv2D(64, kernel_size=(3, 3), activation="relu"),
            layers.MaxPooling2D(pool_size=(2, 2)),
            layers.Conv2D(32, kernel_size=(3, 3), activation="relu"),
            layers.MaxPooling2D(pool_size=(2, 2)),
            layers.Conv2D(32, kernel_size=(3, 3), activation="relu"),
            layers.MaxPooling2D(pool_size=(2, 2)),
            layers.Flatten(),
        ],
    )
    model = keras.Sequential([encoder, layers.Dense(10)])
    model.compile(loss='categorical_crossentropy', optimizer='adam')
    (x_train, y_train), (x_test, y_test) = keras.datasets.fashion_mnist.load_data()
    y_test = y_test.astype("int32")

    model.fit(x_train, y_train, epochs=10)

    # Transform to latent space
    latents = encoder.predict(x_test)

    labels = {x: x for x in range(10)} # TODO(lukewood): replace with real labels
    luketils.visualization.plot_latents(latents, y_test, labels=labels, show=True)
    ```

    Args:
        x: array-like representing the latent representation of some data.
        y: array-like representing the true labels of the samples in `x`.
        labels: dictionary from indices to label names for the classes present in `y`.
        dimensions: the number of dimensions to include in the dimensionality reduction
            technique and plot used for visualization.  Can be `2` or `3`.
        title: the title to use for the plot.
        legend: whether or not to include a legend, defaults to True.
        legend_location: location for the legend, defaults to 'auto' which is 'upper right'
            for dimensions=2 and 'lower right' for dimensions=3.
        figure_size: figure size, defaults to `(6, 6)`.
        transparent: (Optional) whether or not to give the image a transparent
            background.  Defaults to True.
        dpi: (Optional) the dpi to pass to matplotlib.savefig().  Defaults to `60`.
        path: (Optional) path to save the resulting gallery to.
        show: (Optional) whether or not to show the gallery of images.
    """
    if path is None and show is None:
        # Default to showing the image
        show = True
    if path is not None and show:
        raise ValueError(
            "plot_latents() expects either `path` to be set, or `show` " "to be true. "
        )

    x = to_numpy(x)
    x = x.reshape((x.shape[0], -1))
    y = to_numpy(y)

    if len(y.shape) > 1:
        raise ValueError(
            "Expected `y` to be a 1D vector of class labels. "
            f"Got `y.shape={y.shape}`.  If your labels are on hot encoded, "
            "try passing `y=y.argmax(axis=1)`, if your labels have a dummy "
            "dimension for Keras compatibility, pass `y=y.squeeze()`"
        )

    if x.shape[0] != y.shape[0]:
        raise ValueError(
            "Expected `x.shape[0]==y.shape[0]`, "
            f"but got `x.shape[0]={x.shape[0]}` and "
            f"`y.shape[0]={labels.shape[0]}`."
        )

    if not isinstance(labels, dict):
        raise ValueError(
            "Expected `labels` to be a dictionary, but got " f"`labels={labels}`."
        )
    if not all(isinstance(x, int) for x in labels.keys()):
        raise ValueError(
            "Expected `labels` to be a dictionary with integer keys "
            f"corresponding to class ids, but got `labels.keys()={labels.keys()}`"
        )

    if legend_location == "auto":
        legend_location = {2: "upper right", 3: "lower right"}[dimensions]

    pca = PCA(n_components=dimensions)
    pca.fit(x)
    x = pca.transform(x)

    fig = plt.figure(figsize=figure_size)

    if dimensions == 2:
        ax = plt
    else:
        try:
            from mpl_toolkits.mplot3d import Axes3D
        except ImportError:
            raise ImportError(
                "`plot_latents(dimensions=3)` requires the `mpl_toolkits` "
                "package to be installed."
            )
        ax = Axes3D(fig)

    for i in labels.keys():
        indices = y == i
        if dimensions == 2:
            ax.scatter(x[indices, 0], x[indices, 1], label=str(labels[i]))
        if dimensions == 3:
            ax.scatter(
                x[indices, 0], x[indices, 1], x[indices, 2], label=str(labels[i])
            )
    plt.legend(loc=legend_location)

    if title is not None:
        plt.title(title)

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
