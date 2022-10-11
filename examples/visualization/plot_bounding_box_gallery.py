import keras_cv

import luketils

train_ds, ds_info = keras_cv.datasets.pascal_voc.load(
    split="train", bounding_box_format="xywh", batch_size=9
)
train_ds = train_ds.map(lambda sample: (sample["images"], sample["bounding_boxes"]))
images, boxes = next(iter(train_ds.take(1)))

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

luketils.visualization.plot_bounding_box_gallery(
    images,
    value_range=(0, 255),
    bounding_box_format="xywh",
    y_true=boxes,
    scale=4,
    rows=2,
    cols=2,
    true_color=(128, 128, 255),
    thickness=4,
    font_scale=1,
    class_mapping=class_mapping,
)

# same works for y_pred
luketils.visualization.plot_bounding_box_gallery(
    images,
    value_range=(0, 255),
    bounding_box_format="xywh",
    y_pred=boxes,
    scale=4,
    rows=2,
    cols=2,
    thickness=4,
    font_scale=1,
    class_mapping=class_mapping,
)
