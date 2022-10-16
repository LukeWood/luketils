import luketils
import numpy as np

n = 1000
y = np.random.choice([0, 1, 2, 3, 4, 5], size=(n,))
labels = {l: l for l in range(6)}

x = np.random.uniform(size=(n, 100))

for label in labels.keys():
    x = np.where(np.expand_dims(y == label, axis=1), x * (label + 1), x)

luketils.visualization.plot_latents(x, y, labels=labels)
luketils.visualization.plot_latents(x, y, labels=labels, dimensions=2)
