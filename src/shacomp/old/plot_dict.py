import matplotlib.pyplot as plt
from src import shacomp as hlp
from shacomp.old import plot


def dict_stats(d, do_plot=False):
    # copies_hist - how many files (value) have (key) copies
    copies_per_hash, copies_hist, ext_hist = hlp.sum_default_dict(d)
    total = sum(copies_per_hash.values())
    print("dict stats: unique entries:{}/{}".format(len(d), total))

    if do_plot:
        print("plotting histograms")
        # plt.subplot(211)
        # plt.ylabel('copies per hash')
        # shacomp_plot.my_plot(copies_per_hash)

        plt.subplot(211)
        plt.ylabel("copies hist")
        plot.my_plot(copies_hist)

        plt.subplot(212)
        plt.ylabel("ext hist")
        plot.my_plot(ext_hist)

        plt.show()
