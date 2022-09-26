import subprocess


def install_keras_cv_cuda():
    """Update the CUDA kernel in your Colab environment to support running KerasCV."""
    subprocess.run(
        [
            "apt",
            "install",
            "--allow-change-held-packages",
            "libcudnn8=8.1.0.77-1+cuda11.2",
        ]
    )
