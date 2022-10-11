def tf_cap_memory(error_on_fail=False):
    """prevents TensorFlow's default behavior of pre-allocating all GPU memory.

    This is useful when working in large compute clusters, shared machines, or even
    just when trying to run concurrent local jobs.
    """
    gpus = tf.config.experimental.list_physical_devices("GPU")

    if gpus:
        for gpu in gpus:
            try:
                tf.config.experimental.set_memory_growth(gpu, True)
            except RuntimeError as e:
                if error_on_fail:
                    raise e
                else:
                    # Memory growth must be set before GPUs have been initialized
                    print(e)
