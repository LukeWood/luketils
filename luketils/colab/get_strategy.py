import tensorflow as tf
import os

def get_strategy(
        require_tpu=False,
        require_gpu=False,
        try_tpu=True,
        verbose=1
    ):
    """`colab.get_strategy()` returns a `tf.distribute.Strategy` strategy for a Colab.

    The strategy is selected based on the following rules:
    - if a TPU is available, return a `tf.distribute.TPUStrategy`.
    - if a GPU is available, return a `tf.distribute.SingleDeviceStrategy`.
    - else, return the default strategy
    """
    if try_tpu:
        try:
            resolver = tf.distribute.cluster_resolver.TPUClusterResolver()
            tf.config.experimental_connect_to_cluster(resolver)
            tf.tpu.experimental.initialize_tpu_system(resolver)
            if verbose >= 1:
                print("All TPU devices: ", tf.config.list_logical_devices('TPU'))
            return tf.distribute.TPUStrategy(resolver)
        except ValueError:
            if verbose >= 2:
                print("TPU device not found.")
            if require_tpu:
                raise RuntimeError(
                    "No TPU device found, but `require_tpu=True`. "
                    "Please enable TPU in your Colab runtime."
                )

    if len(tf.config.list_physical_devices('GPU')) > 0:
        return tf.distribute.SingleDeviceStrategy(device='/gpu:0')

    if require_gpu:
        raise RuntimeError(
            "No GPU device found, but `require_gpu=True`. "
            "Please enable GPU in your Colab runtime."
        )
    return tf.distribute.get_strategy()
