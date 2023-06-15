import luketils
import pytest
import numpy as np
import os


class TestRemoteImage:
    def test_remote_file_manager(self):
        image = luketils.data.get_image("https://i.imgur.com/gCNcJJI.jpg")
        assert isinstance(image, np.ndarray)

    def test_removes_files(self):
        image = luketils.data.RemoteImage("https://i.imgur.com/gCNcJJI.jpg")
        with image as f:
            downloaded_path = image.downloaded_path
            assert isinstance(f, np.ndarray)
        assert not os.path.exists(downloaded_path)
