import keras_cv
import matplotlib.pyplot as plt
import tensorflow as tf


def plot_gallery(
    images,
    value_range,
    rows=3,
    columns=3,
    scale=2,
    path=None,
    show=None,
    cols=None,
    transparent=True,
    dpi=60,
):
    """gallery_show shows a gallery of images.

    Args:
        images: a Tensor or NumPy array containing images to show in the gallery.
        value_range: value range of the images.
        rows: number of rows in the gallery to show.
        columns: number of columns in the gallery to show.
        scale: how large to scale the images in the gallery
        path: (Optional) path to save the resulting gallery to.
        show: (Optional) whether or not to show the gallery of images.
        cols: (Optional) alias for columns.
        transparent: (Optional) whether or not to give the image a transparent
            background.  Defaults to True.
        dpi: (Optional) the dpi to pass to matplotlib.savefig().  Defaults to `60`.
    """
    columns = cols if cols is not None else columns
    if path is None and show is None:
        # Default to showing the image
        show = True
    if path is not None and show:
        raise ValueError(
            "plot_gallery() expects either `path` to be set, or `show` " "to be true."
        )

    # 3fig, axes = plt.subplots(nrows=rows, ncols=columns, figsize=(8, 8))
    # fig.tight_layout() # Or equivalently,  "plt.tight_layout()"
    fig = plt.figure(figsize=(columns * scale, rows * scale))
    fig.tight_layout()  # Or equivalently,  "plt.tight_layout()"
    plt.subplots_adjust(wspace=0, hspace=0)
    plt.margins(x=0, y=0)
    plt.axis("off")

    images = keras_cv.utils.transform_value_range(
        images, original_range=value_range, target_range=(0, 255)
    )
    if isinstance(images, tf.Tensor):
        images = images.numpy()

    images = images.astype(int)
    for row in range(rows):
        for col in range(columns):
            index = row * columns + col
            plt.subplot(rows, columns, index + 1)
            plt.imshow(images[index].astype("uint8"))
            plt.axis("off")
            plt.margins(x=0, y=0)

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
