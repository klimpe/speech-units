'''
Some random functions for plotting
TODO: make usable
'''

def plot_damaged_method():
    """
    plot damaged segmentations to compare multiple metrics'
    behaviour for one damaging method
    """
    pass


def plot_damaged_metric():
    """
    Plot to compare how one metric behaves across
    different damaging methods
    """
    pass


# ============= look into:
def plot_durations_of_categories(data):
    labels, counts, durations = data
    plot_durations(data, labels)


def plot_durations(tier, normed=False, bins=40, xmax=5, ymax=100):
    """
    Plot durations on the same layer. ??

    In:
      data (list): tuple of three lists of the same length:
          Label, Count, Durations
    """
    data = stats_label_distrib(tier)

    labels, counts, durations = data
    n_layers = len(labels)
    color = [0, 0, 0]
    color_step = 2.7 / n_layers
    i = 0
    plt.axis([0, xmax, 0, ymax])
    while i < n_layers:
        plt.xlabel('time (seconds)')
        plt.ylabel('count')
        plt.hist(durations[i], label=labels[i],
                 histtype='bar', color=tuple(color), alpha=0.4,
                 normed=normed, bins=bins, range=(0, xmax))
        plt.legend()
        color = change_color(color, color_step)
        print color
        i += 1
    plt.show()


def change_color(color, step):
    if color[0] == color[1] == color[2]:
        color[0] += step
    elif color[0] > color[1] == color[2]:
        color[1] += step
    else:
        color[2] += step
    return color
