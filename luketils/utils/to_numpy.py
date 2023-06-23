import numpy as np
try:
    import tensorflow as tf
except:
    tf = None


def to_numpy(x):
    if x is None:
        return None

    if tf is not None:
        if isinstance(x, tf.RaggedTensor):
            x = x.to_tensor(-1)
        if isinstance(x, tf.Tensor):
            x = x.numpy()

    if not isinstance(x, (np.ndarray, np.generic)):
        x = np.array(x)

    return np.ascontiguousarray(x)
