import os
import numpy as np
from .get_file import get_file
from .load_image import load_img

def get_image(filename):
    with RemoteImage(filename) as i:
        image = i
    return image

class RemoteImage:
    def __init__(self, filename):
        self.filename = filename
        self.downloaded_path = None

    def image(self):
        if self.downloaded_path is None:
            raise ValueError(
                "Only use `image()` within a "
                "`with RemoteImageManager() as im:` scope."
            )
        image = load_img(self.downloaded_path)
        image = np.array(image)
        return image

    def __enter__(self):
        self.downloaded_path = get_file(origin=self.filename)
        return self.image()

    def __exit__(self, exc_type, exc_value, exc_traceback):
        os.remove(self.downloaded_path)
        self.downloaded_path = None
