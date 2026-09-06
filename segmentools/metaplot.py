def plot_compare_metrics(self, directory, metrics):
    """
    Plot result for all metrics for one damaging method

    :param directory: directory for writing the pdf, filename is
        generated automatically
    """
    pyplot.axis([0, 100, 0, 1.05])
    pyplot.grid(which='major', color='0.75', linestyle='-')
    pyplot.xlabel('n (%)')
    pyplot.ylabel('score')
    for metric in self.metrics:
        pairs = util.series2tuples(self.list_results_metric(metric))
        x = [i[0] for i in pairs]
        y = [i[1] for i in pairs]
        pyplot.plot(x, y, label=metric)
    pyplot.legend(loc=8, ncol=2, fontsize=9)
    pyplot.savefig(os.path.join(directory, self.name + '.pdf'))
    pyplot.cla()
