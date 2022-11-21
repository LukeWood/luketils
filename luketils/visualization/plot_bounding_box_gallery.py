import functools

import keras_cv
import numpy as np
import tensorflow as tf
from matplotlib import patches

from luketils import drawing
from luketils import utils
from luketils.visualization.plot_gallery import plot_gallery


def plot_bounding_box_gallery(
    images,
    value_range,
    bounding_box_format,
    pred_color=(255, 128, 0),
    true_color=(0, 255, 255),
    y_true=None,
    y_pred=None,
    thickness=2,
    font_scale=1.0,
    text_thickness=None,
    class_mapping=None,
    ground_truth_mapping=None,
    prediction_mapping=None,
    legend=False,
    legend_handles=None,
    rows=3,
    cols=3,
    **kwargs
):
    """plots a gallery of images with corresponding bounding box annotations

    !Example bounding box gallery](https://i.imgur.com/Fy7kMnP.png)

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
        class_mapping: (Optional) class mapping from class IDs to strings
        ground_truth_mapping:  (Optional) class mapping from class IDs to strings,
            defaults to `class_mapping`
        prediction_mapping:  (Optional) class mapping from class IDs to strings,
            defaults to `class_mapping`
        thickness: (Optional) thickness for the box and text labels.  Defaults to 2.
        text_thickness: (Optional) the thickness for the text, defaults to `1.0`.
        font_scale: (Optional) font size to draw bounding boxes in.
        legend: Whether or not to create a legend with the specified colors for `y_true`
            and `y_pred`.  Defaults to False.
        kwargs: keyword arguments to propagate to
            `keras_cv.visualization.gallery_show()`.
    """
    prediction_mapping = prediction_mapping or class_mapping
    ground_truth_mapping = ground_truth_mapping or class_mapping

    if isinstance(images, tf.data.Dataset):
        if y_true is not None or y_pred is not None:
            raise ValueError(
                "When passing a ` tf.data.Dataset` to "
                "`plot_bounding_box_gallery()`, please do not provide `y_true` or "
                "`y_pred`. The values for `bounding_boxes` will be interpreted as "
                "`y_true` when inputs are a dictionary, or the second item of the "
                "input tuple."
            )

        images, boxes = [], []
        ds_iter = iter(images)
        total = 0
        while total < rows * cols:
            inputs = next(ds_iter)
            if isinstance(inputs, dict):
                x, y = inputs["images"], inputs["bounding_boxes"]
            else:
                x, y = inputs[0], inputs[1]
            total += x.shape[0]
            images.append(x)
            boxes.append(y)
        images = tf.concatenate(images, axis=0)
        y_true = tf.concatenate(boxes, axis=0)

    images = utils.to_numpy(images)
    y_true = utils.to_numpy(y_true)
    y_pred = utils.to_numpy(y_pred)

    plotted_images = images

    draw_fn = functools.partial(
        drawing.draw_bounding_boxes,
        bounding_box_format=bounding_box_format,
        thickness=thickness,
        text_thickness=text_thickness,
        font_scale=font_scale,
    )

    if y_true is not None:
        plotted_images = draw_fn(
            plotted_images, y_true, true_color, class_mapping=ground_truth_mapping
        )

    if y_pred is not None:
        plotted_images = draw_fn(
            plotted_images, y_pred, pred_color, class_mapping=prediction_mapping
        )

    if legend:
        if legend_handles:
            raise ValueError(
                "Only pass `legend` OR `legend_handles` to "
                "`luketils.visualization.plot_bounding_box_gallery()`."
            )
        legend_handles = [
            patches.Patch(color=np.array(true_color) / 255.0, label="Ground Truth"),
            patches.Patch(color=np.array(pred_color) / 255.0, label="Prediction"),
        ]

    plot_gallery(
        plotted_images,
        value_range,
        legend_handles=legend_handles,
        rows=rows,
        cols=cols,
        **kwargs
    )
