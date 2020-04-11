import matplotlib
import matplotlib.pyplot as plt
import numpy as np

matplotlib.use("Qt5Agg")


def my_plot(c):
    # labels, values = zip(*collections.Counter(['A','B','A','C','A','A']).items())
    # labels, values = zip(*c.items())

    # dictionary items to list of tuples, sorted by key
    items = [a for a in c.items()]
    items.sort()
    labels, values = zip(*items)

    indexes = np.arange(len(labels))
    width = 1

    plt.bar(indexes, values, width)
    plt.xticks(indexes + width * 0.5, labels)
