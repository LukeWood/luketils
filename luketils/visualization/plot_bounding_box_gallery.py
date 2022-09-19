import keras_cv


def plot_bounding_box_gallery(
    images,
    value_range,
    bounding_box_format,
    pred_color=(255.0, 0, 0),
    true_color=(0, 255.0, 255.0),
    y_true=None,
    y_pred=None,
    **kwargs
):
    """plots a gallery of images with corresponding bounding box annotations

    Args:
        images: a Tensor or NumPy array containing images to show in the gallery.
        value_range: value range of the images.
        bounding_box_format: the bounding_box_format  the provided bounding boxes are
            in.
        y_true: a Tensor or RaggedTensor representing the ground truth bounding boxes.
        y_pred: a Tensor or RaggedTensor representing the predicted truth bounding
            boxes.
        pred_color: three element tuple representing the color to use for plotting
            predicted bounding boxes.
        true_color: three element tuple representing the color to use for plotting
            true bounding boxes.
        kwargs: keyword arguments to propagate to
            `keras_cv.visualization.gallery_show()`.
    """

    plotted_images = images

    if y_pred is not None:
        plotted_images = keras_cv.visualization.draw_bounding_boxes(
            plotted_images,
            y_pred[..., :4],
            pred_color,
            bounding_box_format=bounding_box_format,
        )

    if y_true is not None:
        plotted_images = keras_cv.visualization.draw_bounding_boxes(
            plotted_images,
            y_true[..., :4],
            true_color,
            bounding_box_format=bounding_box_format,
        )

    keras_cv.visualization.plot_gallery(plotted_images, value_range, **kwargs)
