import tensorflow as tf
import numpy as np


def to_numpy(x):
    if x is None:
        return None

    if isinstance(x, tf.RaggedTensor):
        x = x.to_tensor(-1)

    if isinstance(x, tf.Tensor):
        return x.numpy()
    if isinstance(x, (np.ndarray, np.generic)):
        return x
    return np.array(x)
