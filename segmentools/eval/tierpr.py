#-*- coding : utf-8 -*-
'''
Standard scores Precision, Recall and F-measure applied to segmentations.
Includes separate measures for
  - starts of units,
  - ends of units,
  - both boundaries.
'''
from __future__ import division
from segmentools.annotationdata import Tier


class PrecisionRecall:
    def __init__(self, data, pause_labels=('#', ''), delta=0):
        '''
        In:
          data : sequence
              Tiers to evaluate.
              The first one is considered as 'gold standard',
              all the other tiers are evaluated against it.
          pause_label : str
              regular expression defining labels which mark pauses
          delta : float
              How long a distance is still considered a match (in seconds).
              Allows to measure imperfectly aligned segmentations.

        Errors:
          ValueError
          TypeError
        '''
        # check input
        if not isinstance(data, list):
            raise TypeError('Expecting a list')
        for tier in data:
            if not isinstance(tier, Tier):
                raise TypeError('Every list item must be an '
                                'Tier object')
            if len(tier) < 2:
                raise ValueError('Tier {} is too short'.format(tier.Name))
        self.PAUSE_LABELS = pause_labels               
        try:
            self.delta = float(delta)
        except:
            raise ValueError('delta must be a number')
        self.data = data
        self._starts = None
        self._ends = None
        self._units = None


    def precision(self, side):
        '''
        In:
          side - str one of 'start', 'end', 'unit'
        '''
        # find necessary boundaries, if needed
        precision = []
        if side == 'start':
            self._find_starts()
            gold_bounds = self._starts[0]
            for test_bounds in self._starts[1:]:
                tp = self._count_true_positives_boundary(gold_bounds,
                                                         test_bounds)
                precision.append(tp / len(test_bounds))
        elif side == 'end':
            self._find_ends()
            gold_bounds = self._ends[0]
            for test_bounds in self._ends[1:]:
                tp = self._count_true_positives_boundary(gold_bounds,
                                                         test_bounds)
                precision.append(tp / len(test_bounds))
        elif side == 'unit':
            self._find_units()
            gold_bounds = self._units[0]
            for test_bounds in self._units[1:]:
                tp = self._count_true_positives_unit(gold_bounds, test_bounds)
                precision.append(tp / len(test_bounds))
        if len(precision) == 1:
            return precision[0]
        else:
            return precision


    def recall(self, side):
        '''
        In:
        side - str one of 'start', 'end', 'unit'
        '''
        recall = []
        if side == 'start':
            self._find_starts()
            gold_bounds = self._starts[0]
            for test_bounds in self._starts[1:]:
                tp = self._count_true_positives_boundary(gold_bounds,
                                                         test_bounds)
                recall.append(tp / len(gold_bounds))
        elif side == 'end':
            self._find_ends()
            gold_bounds = self._ends[0]
            for test_bounds in self._ends[1:]:
                tp = self._count_true_positives_boundary(gold_bounds,
                                                         test_bounds)
                recall.append(tp / len(gold_bounds))
        elif side == 'unit':
            self._find_units()
            gold_bounds = self._units[0]
            for test_bounds in self._units[1:]:
                tp = self._count_true_positives_unit(gold_bounds,
                                                     test_bounds)
                recall.append(tp / len(gold_bounds))
        if len(recall) == 1:
            return recall[0]
        else:
            return recall


    def f1(self, side):
        '''
        In:
          side - str one of 'start', 'end', 'unit'
        '''
        # find necessary boundaries, if needed
        f1 = []
        if side == 'start':
            self._find_starts()
            gold_bounds = self._starts[0]
            for test_bounds in self._starts[1:]:
                tp = self._count_true_positives_boundary(gold_bounds,
                                                         test_bounds)
                f1.append(2*((tp/len(test_bounds)*(tp/len(gold_bounds)))
                                      / (tp/len(test_bounds)+(tp/len(gold_bounds)))))
        elif side == 'end':
            self._find_ends()
            gold_bounds = self._ends[0]
            for test_bounds in self._ends[1:]:
                tp = self._count_true_positives_boundary(gold_bounds, test_bounds)
                f1.append(2 * ((tp/len(test_bounds)*(tp/len(gold_bounds)))
                                      / (tp/len(test_bounds)+(tp/len(gold_bounds)))))
        elif side == 'unit':
            self._find_units()
            gold_bounds = self._units[0]
            for test_bounds in self._units[1:]:
                tp = self._count_true_positives_unit(gold_bounds, test_bounds)
                try:
                    f1.append(2 * ((tp/len(test_bounds)*(tp/len(gold_bounds))) /
                                   (tp/len(test_bounds)+(tp/len(gold_bounds)))))
                except ZeroDivisionError:
                    print 'f1: Zero division'
                    print 'len(test_bounds)', len(test_bounds)
                    print 'len(gold_bounds)', len(gold_bounds)
                    print 'tp/len(test_bounds)+(tp/len(gold_bounds))', tp/len(test_bounds)+(tp/len(gold_bounds))
                    f1.append(0)
        if len(f1) == 1:
            return f1[0]
        else:
            return f1


    def _find_starts(self):
        '''
        Create self.starts, a list, which contains
        lists with time values for all tiers
        '''
        if self._starts:
            return None
        starts = []
        for tier in self.data:
            if not self.PAUSE_LABELS:
                tier_starts = [x.GetLocation().GetBeginMidpoint()
                               for x in tier]
            else:
                tier_starts = [x.GetLocation().GetBeginMidpoint()
                               for x in tier
                               if x.GetLabel().GetValue()
                               not in self.PAUSE_LABELS]
            starts.append(tier_starts)
        self._starts = starts


    def _find_ends(self):
        if self._ends:
            return None
        ends = []
        for tier in self.data:
            if not self.PAUSE_LABELS:
                tier_ends = [x.GetLocation().GetEndMidpoint() for x in tier]
            else:
                tier_ends = [x.GetLocation().GetEndMidpoint()
                             for x in tier
                             if x.GetLabel().GetValue()
                             not in self.PAUSE_LABELS]
            ends.append(tier_ends)
        self._ends = ends


    def _find_units(self):
        if self._units:
            return None
        units = []
        for tier in self.data:
            if self.PAUSE_LABELS is None:
                tier_units = [(x.GetLocation().GetBeginMidpoint(),
                               x.GetLocation.GetEndMidpoint)
                              for x in tier]
            else:
                tier_units = [(x.GetLocation().GetBeginMidpoint(),
                               x.GetLocation().GetEndMidpoint())
                              for x in tier
                              if x.GetLabel().GetValue()
                              not in self.PAUSE_LABELS]
            units.append(tier_units)
        self._units = units


    def _count_true_positives_boundary(self, gold, test):
        '''
        In:
          gold and test - lists of boundaries
        '''
        tp = 0
        for t in test:
            closer_g = gold[min(range(len(gold)),
                                key=lambda i: abs(gold[i]-t))]
            if abs(t - closer_g) <= self.delta:
                tp += 1
        return tp


    def _count_true_positives_unit(self, gold, test):
        tp = len([(g_start,g_end)
                  for (g_start,g_end) in gold
                  for (t_start,t_end) in test
                  if abs(t_start-g_start) <= self.delta
                  and abs(t_end-g_end) <= self.delta])
        return tp

