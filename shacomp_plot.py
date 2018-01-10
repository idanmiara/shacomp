import numpy as np

import matplotlib
matplotlib.use('Qt5Agg')
import matplotlib.pyplot as plt


def plot(c):
    # labels, values = zip(*Counter(['A','B','A','C','A','A']).items())
    labels, values = zip(*c.items())

    indexes = np.arange(len(labels))
    width = 1

    plt.bar(indexes, values, width)
    plt.xticks(indexes + width * 0.5, labels)
    plt.show()

