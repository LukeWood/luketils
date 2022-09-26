import keras_cv
from luketils import utils
from luketils import drawing
from luketils.visualization.plot_gallery import plot_gallery
import functools


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
        thickness: (Optional) thickness for the box and text labels.  Defaults to 2.
        text_thickness: (Optional) the thickness for the text, defaults to `1.0`.
        font_scale: (Optional) font size to draw bounding boxes in.
        kwargs: keyword arguments to propagate to
            `keras_cv.visualization.gallery_show()`.
    """
    images = utils.to_numpy(images)
    y_true = utils.to_numpy(y_true)
    y_pred = utils.to_numpy(y_pred)

    plotted_images = images

    draw_fn = functools.partial(
        drawing.draw_bounding_boxes,
        bounding_box_format=bounding_box_format,
        class_mapping=class_mapping,
        thickness=thickness,
        text_thickness=text_thickness,
        font_scale=font_scale,
    )

    if y_true is not None:
        plotted_images = draw_fn(
            plotted_images,
            y_true,
            true_color,
        )

    if y_pred is not None:
        plotted_images = draw_fn(
            plotted_images,
            y_pred,
            pred_color,
        )

    plot_gallery(plotted_images, value_range, **kwargs)
