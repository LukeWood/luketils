import os

import tensorflow as tf


def get_strategy(require_tpu=False, require_gpu=False, try_tpu=True, verbose=1):
    """`colab.get_strategy()` returns a `tf.distribute.Strategy` strategy for a Colab.

    The strategy is selected based on the following rules:
    - if a TPU is available, return a `tf.distribute.TPUStrategy`.
    - if a GPU is available, return a `tf.distribute.SingleDeviceStrategy`.
    - else, return the default strategy

    Args:
        require_tpu: If True, raise when no TPU available.
        require_gpu: If True, raise when no GPU available.
        try_tpu: if True, try to connect to TPU.
        verbose: 0, 1, or 2.  Determines how many logs are printed.  Defaults to 1.
    """
    if try_tpu:
        try:
            resolver = tf.distribute.cluster_resolver.TPUClusterResolver()
            tf.config.experimental_connect_to_cluster(resolver)
            tf.tpu.experimental.initialize_tpu_system(resolver)
            if verbose >= 1:
                print(
                    "Using TPU strategy with device: ",
                    tf.config.list_logical_devices("TPU"),
                )
            return tf.distribute.TPUStrategy(resolver)
        except ValueError:
            if verbose >= 2:
                print("TPU device not found.")
            if require_tpu:
                raise RuntimeError(
                    "No TPU device found, but `require_tpu=True`. "
                    "Please enable TPU in your Colab runtime."
                )

    if len(tf.config.list_physical_devices("GPU")) > 0:
        if verbose >= 1:
            print("Using SingleDeviceStrategy with one GPU.")
        return tf.distribute.SingleDeviceStrategy(device="/gpu:0")

    if require_gpu:
        raise RuntimeError(
            "No GPU device found, but `require_gpu=True`. "
            "Please enable GPU in your Colab runtime."
        )
    print("No hardware accelerators found, running with the default strategy.")
    return tf.distribute.get_strategy()
