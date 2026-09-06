import os
import re
from collections import defaultdict
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt


class Plotter(object):
    """
    data format: list of pandas.DataFrame
    data[run]{method:DataFrame}
        columns: metrics
        rows: n
    """

    def __init__(self, root_dir=None):
        """
        root_dir: path to read CSVs from
        """
        self.root_dir = root_dir
        self.METHOD2COLOR = {'insert': '#00AA50',
                             'remove': '#AA5000',
                             'shift1': '#860052',
                             'shift2': '#901564',
                             'shift3': '#A4458D',
                             'shift4': '#BB79BE',
                             'shift5': '#C695D7',
                             'shift6': '#dab6e8',
                             'shift7': '#F0C6F8'}

    def __iter__(self):
        return iter(self.data)

    def __getitem__(self, index):
        return self.data[index]

    def __len__(self):
        return len(self.data)

    @property
    def root_dir(self):
        return self._root_dir

    @root_dir.setter
    def root_dir(self, path):
        if path:
            if not os.path.isdir(path):
                raise OSError(path)
            self._root_dir = path
            self.read_experiment()



    def plot_compare_methods(self, metric, write_dir=None):
        """
        metric: string {f_unit, ...}

        input format:
        dict
          keys: method
          values: DataFrame
            Columns: run1, run2, ..., std
            Rows: n
        """
        data = self.group_by_method(metric)
        fig = plt.figure()
        ax = fig.add_subplot(1,1,1)
        ax.set_xlim([0, 65])
        ax.set_ylim([0, 1.05])
        ax.set_xlabel('n')
        ax.set_ylabel(metric.replace('_',' ').capitalize())
        ax.grid(which='major', color='0.75', linestyle='-')
        for method in data:
            color = self.METHOD2COLOR[method]
            runs = [x for x im data[method]
                    if re.match('run\d+', column_name)]
            for column_name in runs:
                line = data[method][column_name]
                lines.append(line)
                
                    
                    ax.plot(val,
                            label=method+column_name,
                            linewidth=2,
#                            color=color,
                            alpha=0.2)
            substd = data[method]['substd']
            addstd = data[method]['addstd']
            poly_higher_xy = zip(addstd.index, addstd.tolist())
            substd.sort_index(ascending=False, inplace=True)
            poly_lower_xy = zip(substd.index, substd.tolist())
            poly_xy = poly_higher_xy + poly_lower_xy
            std_polygon = plt.Polygon(poly_xy,
                                      color='#d6e30c',
                                      closed=True)
            ax.add_patch(std_polygon)
        plt.legend(loc=8, ncol=2, fontsize=9)
        filename = 'compare_methods_{}.pdf'.format(metric)
        if write_dir:
            plt.savefig(os.path.join(write_dir, filename))


    def plot_compare_metrics_std(self, method, path):
        """
        input format:
        dict
          keys: metric
          values: DataFrame
            Columns: run1, run2, ..., std
            Rows: n
        """

        pass

    def group_by_method(self, metric):
        methods = self.data[0].keys()
        res = {}
        values = []
        for run in self.data:
            for method in methods:
                df_in = run[method]
            values.append(df_in[metric])
        for method in methods:
            method_data = {}
            for run_n, run_val in enumerate(values):
                method_data['run'+str(run_n)] = run_val
            std = np.std(values, axis=0)
            mean = np.mean(values, axis=0)
            method_data['substd'] = mean - std
            method_data['addstd'] = mean + std
            df_method = pd.DataFrame(method_data)
            res[method] = df_method
        return res


    def read_experiment(self):
        data = []
        for fname in os.listdir(self.root_dir):
            subpath = os.path.join(self.root_dir, fname)
            if os.path.isdir(subpath):
                if re.search(r'\w+\d+$', subpath):
                    data.append(self.read_subdir(subpath))
        self.data = data

    def read_subdir(self, subdir):
        data = {}
        a = None
        for fname in os.listdir(subdir):
            if fname.endswith('.csv'):
                if fname.lower().startswith('insert'):
                    method = 'insert'
                elif fname.lower().startswith('remove'):
                    method = 'remove'
                elif fname.lower().startswith('shift'):
                    m = re.match('SHIFTA(\d+)', fname)
                    a = m.groups()[0]
                    method = 'shift'+a
                path = os.path.join(subdir, fname)
                data[method] = pd.read_csv(path, index_col=0)
        return data
