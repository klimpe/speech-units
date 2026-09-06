from __future__ import division

import random
import os
import sys
import copy
import numpy
import eval
import csv
import time
import pandas as pd
from matplotlib import pyplot

from .annotationdata import Annotation, Tier, TimeInterval, TimePoint, Label, Transcription, aio
import tierutil
import damcopy
import util


class DamBatchNotEmpty(Exception):
    pass



class DamBatch(object):
    """
    A collection of damaged segmentations, produced from the
    same original segmentation using the same method,
    but with different values of damaging magnitude (n).
    """
    def __init__(self, reference, original, n_range):
        """
        == IN ==
        reference : Tier
        original : Tier
        """
        self.method = None
        self.reference = reference
        self.original = original
        self._metrics = set()  # evaluations that have been run
        self.data = []  # sequence of damaged tiers with rising 'n'

        self.N = numpy.arange(*n_range)
        self.n_step = self.N[1] - self.N[0]
        self.max_damages = len(self.original)
        self.target_one_step = (self.n_step / 100.) * self.max_damages


    def __iter__(self):
        return iter(self.data)

    def __getitem__(self, index):
        return self.data[index]

    def __len__(self):
        return len(self.data)

    def __str__(self):
        s = ''
        for item in self.data:
            s += str(item)+'\n'
        return s

    @property
    def metrics(self):
        return sorted(list(self._metrics))

    #
    # @property
    # def n_range(self):
    #     if not self.data:
    #         return None
    #     step = self.data[1].n - self.data[0].n
    #     return self.data[0].n, self.data[-1].n, step

    @property
    def n_list(self):
        if not self.data:
            return None
        return [x.n for x in self.data]

    @property
    def name(self):
        date_time = util.datetime_short()
        return '{}_{}to{}step{}_{}'.format(self.method.upper(),
                                           self.N[0], self.N[-1],
                                           self.N[0]-self.N[1],
                                           date_time)

    def _previous(self):
        """
        :return: damcopy.DamCopy
            first original from previous step
        """
        if len(self.data) == 0:
            return damcopy.DamCopy(self.original, self.method, 0)
        return self.data[-1]

    def _relative_target(self, n):
        absolute_target = int(round(n / 100. * self.max_damages))
        prev_dc = self._previous()
        if self.method == 'insert':
            return absolute_target - prev_dc.boundaries_inserted
        elif self.method == 'remove':
            return absolute_target - prev_dc.boundaries_removed
        elif self.method.startswith('shift'):
            return absolute_target - prev_dc.boundaries_shifted
        elif self.method == 'mixed':
            return absolute_target - (prev_dc.boundaries_inserted +
                                      prev_dc.boundaries_removed +
                                      prev_dc.boundaries_shifted)
        else:
            raise ValueError(self.method)

    def generate_by_inserting(self, verbose=False):
        """
        Populate the batch with damaged copies
        by randomly inserting boundaries.
        """
        if self.data:
            raise DamBatchNotEmpty()
        self.method = 'insert'

        for n in self.N:
            if verbose:
                print 'n=', n
            dc = self.gen_dc_insert(n)
            if dc:
                self.data.append(dc)

    def generate_by_removing(self, verbose=False):
        """
        Populate the batch with damaged copies
        by removing random boundaries.
        """
        if self.data:
            raise DamBatchNotEmpty(self.data)
        self.method = 'remove'
        for n in self.N:
            if verbose:
                print 'n=', n
            dc = self.gen_dc_remove(n)
            if dc:
                self.data.append(dc)

    def generate_by_shifting(self, a, skip='', multi_a=True, verbose=False):
        """
        Populate the batch with damaged copies
        by shifting boundaries

        :param a: int
          Amplitude of the shift.
          How many units away from the original boundary.
        :return: None
        """
        if self.data:
            raise DamBatchNotEmpty()
        self.method = 'shiftA' + str(a)
        for n in self.N:
            if verbose:
                print 'n={}'.format(n)
            dc = self.gen_dc_shift(n, a, skip=skip, multi_a=multi_a)
            if dc:
                self.data.append(dc)

    def gen_dc_insert(self, n):
        """
        Damage one segmentation by adding boundaries at random locations.
        Possible locations are limited by by self.reference
        :paramn: int
            Magnitude. Percentage of boundaries to delete.
            Range: max (0, 100)
        :return: damcopy.DamCopy
        """
        dc = copy.deepcopy(self._previous())
        target = self._relative_target(n)

        # Prepare time values where a boundary can be inserted
        original_bounds = set([x.GetLocation().GetBeginMidpoint()
                               for x in dc.segmentation])
        reference_bounds = set([x.GetLocation().GetBeginMidpoint()
                                for x in self.reference])
        potential_bounds = list(reference_bounds - original_bounds)
        random.shuffle(potential_bounds)

        i = 0
        count = 0
        while count < target and i < len(potential_bounds):
            t = potential_bounds[i]
            if tierutil.boundary_insert(dc.segmentation, t):
                count += 1
            i += 1
        true_n = (dc.boundaries_inserted + count) / self.max_damages
        if count < target:
            print ('Stop damaging: No more available locations. '
                   'Inserted {} boundaries instead of {} n={}').format(
                        count, target, true_n)
            return False
        dc.boundaries_inserted += count
        dc.n = n
        dc.true_n = true_n
        return dc

    def gen_dc_remove(self, n):
        """
        Damage segmentation by deleting boundaries in random order.

        :param n: int
            Magnitude. Percentage of boundaries to delete.
            Range: (0, 100)
        :return: damcopy.DamCopy
        """
        dc = copy.deepcopy(self._previous())
        target = self._relative_target(n)
        boundary_locs = [x.GetLocation().GetEndMidpoint()
                         for x in dc.segmentation]
        random.shuffle(boundary_locs)
        # order = range(len(self.original) - 2)  # why 2?
        count = 0
        while count < target and count < len(boundary_locs):
            tierutil.boundary_remove(dc.segmentation, boundary_locs[count])
            count += 1
        if count < target:
            print ('Stop damaging: No more boundaries to remove.'
                   'Removed {} instead of {}'.format(count, target))
            return False
        dc.boundaries_removed += count
        dc.n = n
        return dc

    def gen_dc_shift(self, n, a, skip='', multi_a=False):
        """
        Move the boundary 'a' reference units in random direction,
        but not beyond other boundaries.

        Randomly picks an interval to modify.
        Number of modification attempts is limited to
        2 times the number of intervals in the original segmentation.
        Same interval may be picked more than once.

        :param n: tuple
            Range of n values (n_min, n_max[, n_step])
        :param a: int
            Amplitude of the shift
        :param skip: str
            don't affect units marked with this string
        :param multi_a: bool
            if True, the amplitude for each shift is randomly chosen
            between 1 and 'a'
        == OUT ==
        DamCopy
        """
        dc = copy.deepcopy(self._previous())
        target = self._relative_target(n)
        max_tries = len(dc.segmentation) * 2
        count = 0
        i = 0
        print 'max_tries=', max_tries, 'target=', target
        while count < target and i < max_tries:
            index = random.randint(0, len(dc.segmentation)-2)
            if i % 100 == 0:
                print 'i={} count={} index={}'.format(i, count, index)
            if tierutil.boundary_shift(
                    dc.segmentation, self.reference, index, a, skip=skip):
                count += 1
            i += 1
        true_n = round(float(count) / n * 100, 2)
        if count < target:
            print 'Stop damaging: Moved {} instead of {}, n={}'.format(
                count, target, true_n)
            return False
        dc.boundaries_shifted += count
        dc.n = n
        dc.true_n = true_n
        return dc

    def gen_dc_mixed(self, n, a_max):
        """
        Generate a damaged segmentation using
        randomly chosen method.
        :param a_max: int Maximum shifting amplitude
        :return: damcopy.DamCopy
        """

        target = self._relative_target(n)
        count = 0
        i = 0
        while count < target:
            index = random.randint(0, len(self.original)-2)
            method = random.choice(['insert', 'remove', 'shift'])
            if method == 'insert':
                pass
            elif method == 'remove':
                pass
            elif method == 'shift':
                pass
        return


    def estimate_shift_max_amplitude(self):
        """
        Return maximum amplitude for boundary shift in reference units, int.

        It is calculated as rounded average number of reference units
        in segmentations unit.
        """
        # a/2 ?
        a = (len(self.reference) / float(len(self.data))) / 2
        return int(round(a))

    def eval_kappa(self, original_items):
        for dcopy in self:
            if dcopy.items is None:
                dcopy.gen_items(self.reference, 1)
            data = dcopy.items + original_items
            dcopy.eval_result['kappa'] = eval.eval_kappa(data)
        self._metrics.add('kappa')

    def eval_boundary_similarity_time(self, step=0.01):
        self._metrics.add('boundary_similarity_time')
        for dcopy in self:
            dcopy.eval_result['boundary_similarity_time'] = eval.eval_boundary_similarity_time(
                self.original, dcopy.segmentation, step)
        self._metrics.add('boundary_similarity_time')

    def eval_boundary_similarity_unit(self):
        self._metrics.add('boundary_similarity_unit')
        for dcopy in self:
            dcopy.eval_result['boundary_similarity_unit'] = eval.eval_boundary_similarity_unit(
           dsadfdpipppdsaddds     self.reference, self.original, dcopy.segmentation)
        self._metrics.add('boundary_similarity_unit')

    def eval_windowdiff_time(self, step=0.01):
        for dcopy in self:
            dcopy.eval_result['windowdiff_time'] = 1 - eval.eval_windowdiff_time(
                self.original,
                dcopy.segmentation,
                step=step,
                verbose=True)
        self._metrics.add('windowdiff_time')

    def eval_windowdiff_unit(self):
        for dcopy in self:
            dcopy.eval_result['windowdiff_unit'] = 1 - eval.eval_windowdiff_unit(
                self.original,
                dcopy.segmentation,
                self.reference,
                verbose=True)
        self._metrics.add('windowdiff_unit')

    def eval_precision_recall_f1(self, pause_labels=('#', ''), delta=0):
        for dcopy in self:
            prf = eval.eval_precision_recall_f1(
                [self.original, dcopy.segmentation],
                pause_labels=pause_labels,
                delta=delta)
            dcopy.eval_result['precision_start'] = prf['start'][0]
            dcopy.eval_result['precision_end'] = prf['end'][0]
            dcopy.eval_result['precision_unit'] = prf['unit'][0]
            dcopy.eval_result['recall_start'] = prf['start'][1]
            dcopy.eval_result['recall_end'] = prf['end'][1]
            dcopy.eval_result['recall_unit'] = prf['unit'][1]
            dcopy.eval_result['f1_start'] = prf['start'][2]
            dcopy.eval_result['f1_end'] = prf['end'][2]
            dcopy.eval_result['f1_unit'] = prf['unit'][2]
        mm = ['precision_start', 'precision_end', 'precision_unit',
              'recall_start', 'recall_end', 'recall_unit',
              'f1_start', 'f1_end', 'f1_unit']
        for m in mm:
            self._metrics.add(m)

    def list_results(self):
        """
        :return: pandas.DataFrame, where row indices correspond to 'n'
                and columns correspond to metrics
        """
        data = {}
        for m in self.metrics:
            rows = []
            index = []
            for dc in self:
                index.append(dc.n)
                rows.append(dc.eval_result[m])
            series = pd.Series(rows, index=index)
            data[m] = series
        return pd.DataFrame(data, columns=self.metrics)

    def list_results_metric(self, metric):
        """
        Returns calculated metric values for each damaged copy

        :param metric: str, name of the metric
        :return: pandas.Series, where row indices correspond to 'n'
        :exception ValueError: Wrong metric name or this metric
            hasn't been calculated yet
        """
        data = [x.eval_result[metric] for x in self]
        if set(data) is None:
            raise ValueError("No results for:" + metric)
        return pd.Series(data, index=self.N)

    def plot_compare_metrics(self, directory):
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

    # ============ I/O ========

    def write_textgrid(self, directory):
        path = os.path.join(directory, self.name + '.textgrid')
        tg = Transcription()
        tg.Add(self.reference)
        tg.Add(self.original)
        if self.data:
            for dc in self.data:
                tg.Add(dc.segmentation)
        aio.write(path, tg)

    def write_csv(self, directory):
        path = os.path.join(directory, self.name + '.csv')
        res = self.list_results()
        res.to_csv(path, header=True, index_label='n')


            # def add(self, ds):
    #     if ds.method != self.method:
    #         raise ValueError('All segmentations must have the same '
    #                          'value of "method" property')
    #     if ds.n in self.N:
    #         raise ValueError('There is already a segmentation '
    #                          'with this value of n')
    #     self._data.append(ds)
    #     self.N.append(ds.n)
    #     self._sort_by_n()

    # def add_multiple(self, ds_list):
    #     if len(set([x.method for x in ds_list])) == 1:
    #         if self.method is None:
    #             self.method = ds_list[0].method
    #         else:
    #             if ds_list[0].method == self.method:
    #                 self._data.apppend(ds_list)
    #             else:
    #                 raise ValueError('This batch was set to accept'
    #                                  'segmentation damaged with method '
    #                                  + self.method)
    #     else:
    #         raise ValueError('All segmentations must have the same '
    #                          'value of "method" property')
    #     self._sort_by_n()


    # def _sort_by_n(self):
    #     """
    #     Sorts tiers in ._data based on .N values
    #     """
    #     zlist = zip(self.N, self._data)
    #     zlist.sort(key=lambda x:x[0])
    #     self.N = [x for x, y in zlist]
    #     self._data = [y for x, y in e]
