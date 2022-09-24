# Copyright 2022 The KerasCV Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import keras_cv
import tensorflow as tf
import cv2
from luketils import utils
import numpy as np


def draw_bounding_boxes(
    images,
    bounding_boxes,
    color,
    bounding_box_format,
    thickness=2,
    text_thickness=1,
    font_scale=1.0,
    class_mapping=None,
):
    """draws bounding boxes on the target image.

    Args:
        images: a batch Tensor of images to plot bounding boxes onto.
        bounding_boxes: a Tensor of batched bounding boxes to plot onto the provided
            images
        color: the color in which to plot the bounding boxes
        bounding_box_format: The format of bounding boxes to plot onto the images. Refer
          [to the keras.io docs](https://keras.io/api/keras_cv/bounding_box/formats/)
          for more details on supported bounding box formats.
        thickness: (Optional) thickness for the box and text labels.  Defaults to 2.
        text_thickness: (Optional) the thickness for the text, defaults to `1.0`.
        font_scale: (Optional) scale of font to draw in.  Defaults to `1.0`.
        class_mapping: (Optional) dictionary from class ID to class label.
    Returns:
        images with bounding boxes plotted on top of them
    """
    bounding_boxes = keras_cv.bounding_box.convert_format(
        bounding_boxes, source=bounding_box_format, target="xyxy", images=images
    )
    text_thickness = text_thickness or thickness

    bounding_boxes = utils.to_numpy(bounding_boxes)
    images = utils.to_numpy(images)

    class_mapping = class_mapping or {}
    result = []

    if len(images.shape) != 4:
        raise ValueError(
            "Images must be a batched np-like with elements of shape "
            "(height, width, 3)"
        )

    for i in range(images.shape[0]):
        bounding_box_batch = bounding_boxes[i]
        image = utils.to_numpy(images[i]).astype('uint8')
        for b_id in range(bounding_box_batch.shape[0]):
            x, y, x2, y2, class_id = bounding_box_batch[b_id][:5].astype(int)

            if class_id == -1:
                continue
            # force conversion back to contigous array
            x, y, x2, y2 = int(x), int(y), int(x2), int(y2)
            cv2.rectangle(image, (x, y), (x2, y2), color, thickness)
            class_id = int(class_id)
            if class_id in class_mapping:
                label = class_mapping[class_id]
                cv2.putText(
                    image,
                    label,
                    (x, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    font_scale,
                    color,
                    text_thickness,
                )
        result.append(image)
    return np.array(result).astype(int)
