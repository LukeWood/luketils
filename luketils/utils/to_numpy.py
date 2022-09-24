import tensorflow as tf
import numpy as np


def to_numpy(x):
    if x is None:
        return None
    if isinstance(x, tf.RaggedTensor):
        x = x.to_tensor(-1)
    if isinstance(x, tf.Tensor):
        x = x.numpy()
    if not isinstance(x, (np.ndarray, np.generic)):
        x = np.array(x)
    return np.ascontiguousarray(x)
