"""
`luketils.visualization.plot_latents()` is probably my favorite visualization technique
in all of `luketils`.  `plot_latents()` allows you to visualize high dimensional spaces
in only a few lines of code!

This can provide unique insights into your model's internal structure:
"""

import numpy as np
from tensorflow import keras
from tensorflow.keras import layers
import luketils

"""
First, we create a `keras.Sequential` to transform our inputs to a low dimensional
latent space:
"""

encoder = keras.Sequential(
    [
        layers.Conv2D(64, kernel_size=(3, 3), activation="relu"),
        layers.MaxPooling2D(pool_size=(2, 2)),
        layers.Conv2D(32, kernel_size=(3, 3), activation="relu"),
        layers.MaxPooling2D(pool_size=(2, 2)),
        layers.Conv2D(32, kernel_size=(3, 3), activation="relu"),
        layers.MaxPooling2D(pool_size=(2, 2)),
        layers.Flatten(),
    ],
)

"""
Then we construct the actual model we will use to perform training:
"""

model = keras.Sequential([encoder, layers.Dense(10)])
model.compile(loss="sparse_categorical_crossentropy", optimizer="adam")

"""
and finally run `model.fit()`:
"""
(x_train, y_train), (x_test, y_test) = keras.datasets.fashion_mnist.load_data()
x_train, x_test = np.expand_dims(x_train, axis=-1), np.expand_dims(x_test, axis=-1)
x_train, x_test = x_train.astype(float)/255.0, x_test.astype(float)/255.0
model.fit(x_train, y_train, batch_size=64, epochs=1)

"""
Lets see how the latent space is organized!
"""

# Transform to latent space
latents = encoder.predict(x_test)

labels = {x: x for x in range(10)}  # TODO(lukewood): replace with real labels
luketils.visualization.plot_latents(latents, y_test, labels=labels, show=True)

"""
`plot_latents()` also supports 2D PCA for the weak hearted:
"""
luketils.visualization.plot_latents(
    latents, y_test, labels=labels, dimensions=2, show=True
)

"""
For better results, run for more epochs.
"""
