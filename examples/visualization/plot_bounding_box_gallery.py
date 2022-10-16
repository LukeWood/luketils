"""
Title: Plot a bounding box gallery
Author: [lukewood](https://lukewood.xyz)
Date created: 2022/10/16
Last modified: 2022/10/16
Description: Visualize ground truth and predicted bounding boxes for a given dataset.
"""

"""
`luketils.visualization.plot_bounding_box_gallery()` is a function dedicated to the
visualization for bounding boxes predicted by a `TensorFlow` object detection model.
The API is based on the `KerasCV` object detection API.
"""

import keras_cv
import luketils

"""
First, we load a dataset:
"""

train_ds, ds_info = keras_cv.datasets.pascal_voc.load(
    split="train", bounding_box_format="xywh", batch_size=9
)
train_ds = train_ds.map(lambda sample: (sample["images"], sample["bounding_boxes"]))
images, boxes = next(iter(train_ds.take(1)))

"""
You can give the utility class IDs to annotate the drawn bounding boxes:
"""

class_ids = [
    "Aeroplane",
    "Bicycle",
    "Bird",
    "Boat",
    "Bottle",
    "Bus",
    "Car",
    "Cat",
    "Chair",
    "Cow",
    "Dining Table",
    "Dog",
    "Horse",
    "Motorbike",
    "Person",
    "Potted Plant",
    "Sheep",
    "Sofa",
    "Train",
    "Tvmonitor",
    "Total",
]
class_mapping = dict(zip(range(len(class_ids)), class_ids))

"""
The function accepts `y_true`, `y_pred`, or both to visualize boxes:
"""
luketils.visualization.plot_bounding_box_gallery(
    images,
    value_range=(0, 255),
    bounding_box_format="xywh",
    y_true=boxes,
    scale=3,
    rows=2,
    cols=2,
    thickness=4,
    font_scale=1,
    legend=True,
    class_mapping=class_mapping,
)

"""
Same but with `y_pred`:
"""

luketils.visualization.plot_bounding_box_gallery(
    images,
    value_range=(0, 255),
    bounding_box_format="xywh",
    y_pred=boxes,
    scale=3,
    rows=2,
    cols=2,
    thickness=4,
    font_scale=1,
    legend=True,
    class_mapping=class_mapping,
)
