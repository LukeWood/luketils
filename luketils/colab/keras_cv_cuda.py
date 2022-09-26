import subprocess


def keras_cv_cuda():
    subprocess.run(
        [
            "apt",
            "install",
            "--allow-change-held-packages",
            "libcudnn8=8.1.0.77-1+cuda11.2",
        ]
    )
