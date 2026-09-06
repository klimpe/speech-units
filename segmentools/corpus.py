"""
Name: corpus
Python: 2.7
Author: Klim Peshkov
"""

from __future__ import division
import os
import math
import re
import logging
import csv
import datetime
import codecs
from tabulate import tabulate

import numpy as np
import scipy

import groupsegm
import chunker_fr as chunker
# import chunker_tw as chunker
import tierutil


class Corpus(object):
    """
    Represents a collection of groupsegm.GroupSegm objects
    === In ===
    path : str or list
        path to a TextGrid or list of paths
    reference : int
        index of the reference tier, 0-based
    subset : int
        list of 0-based indices of the segmentation tiers
    """
    def __init__(self, path=None, subset=None, reference=None,
                 equalize=False, log_path='.'):
        self.data = []
        self.pathlist = []
        self._log_init(log_path)
        if path is not None:
            self.load(path, subset=subset, reference=reference,
                      equalize=equalize)

    def __iter__(self):
        return iter(self.data)

    def __getitem__(self, index):
        return self.data[index]

    def __len__(self):
        return len(self.data)

    def _log_init(self, log_path):
        now = datetime.datetime.now()
        now = datetime.datetime.strftime(now, '%Y-%m-%d_%H.%M.%S')
        self._now = now
        log_fname = os.path.join(log_path,'corpus_{}.log'.format(now))
        logging.basicConfig(filename=log_fname,
                            level=logging.INFO,
                            format='%(levelname)s:%(message)s')

    def __str__(self):
        if self.data:
            rows = [['index', 'name', 'n tiers']]
            if self.pathlist:
                rows = [['index', 'name', 'n tiers', 'path']]
            for index, group in enumerate(self.data):
                row = [index, group.name, len(group)]
                if self.pathlist:
                    row.append(self.pathlist[index])
                rows.append(row)
            return tabulate(rows, headers='firstrow',
                            tablefmt='simple')
        else:
            return 'empty Corpus'

    @property
    def names(self):
        """List of GroupSegm names"""
        if self.data:
            return [x.name for x in self.data]
        return []

    def replace_pattern(self, index, pattern, replacement, regex=False):
        """
        Replace matching interval labels in one tier of all groups.

        === In ===
        index : int
            index of the tier in each group
        pattern : str
            string to replace or regex pattern
        replacement : str
        regex : bool
            turn regex on/off
        """
        count = 0
        for group in self:
            for annot in group[index]:
                if regex:
                    annot.TextValue = re.sub(
                        pattern, replacement, annot.TextValue)
                else:
                    annot.TextValue = annot.TextValue.replace(
                        pattern, replacement)

    def chunk(self, pos_tier_index, stats_dir):
        """
        Generate chunk tiers for each GroupSegm.
        This requires POS-tagging in GRACE
        format to be present in each GroupSegm.

        == In ==
        pos_segm_index : int
          index of the tier with pos tags in every GroupSegm
        stats_dir : str
          directory for saving statistics
        """
        stats_fname_chunk = os.path.join(
            stats_dir, 'stats_chunking_{}.csv'.format(self._now))
        stats_fname_categ = os.path.join(
            stats_dir, 'stats_category_{}.csv'.format(self._now))
        stats_file_chunk = codecs.open(stats_fname_chunk, 'w',
                                       encoding='utf-8')
        stats_file_categ = codecs.open(stats_fname_categ, 'w',
                                       encoding='utf-8')
        i = 0
        for i, group in enumerate(self.data):
            logging.info('Chunking: ' + self.pathlist[i])
            print group.data[pos_tier_index][-1]
            ch = chunker.Chunker(group.reference,
                                 group.data[pos_tier_index])
            ch.launch_chunking()
            group.add(ch.synt_tier)
            group.add(ch.simple_synt_tier)
            group.add(ch.chunk_tier)
            group.add(ch.synt_cat_tier)
            group.add(ch.disf_cat_tier)
            group.add(ch.disf_bool_tier)
            # for tier in group.data:
            #     print tier.GetName()

            # Write chunk statistics:
            # (1) rules that have been applied
            line_chunk = ','.join([self.pathlist[i]] +
                                  [str(ch.stats[key])
                                   for key in ch.skeys])
            # (2) distribution of morphosyntactic categories of chunks
            # (ex. Nominal Chunk - NC , Verbal Chunk - VC)
            line_categ = ','.join([self.pathlist[i]] +
                                  [str(ch.stats_category[key])
                                   for key in ch.skeys_category])
            stats_file_chunk.write(line_chunk+'\n')
            stats_file_categ.write(line_categ+'\n')
        stats_file_chunk.write(','.join([' ']+[key for key in ch.skeys]))
        stats_file_categ.write(','.join([' ']
                                        + [key for key in ch.skeys_category]))

    def _write_chunking_stats(self, chkr, directory):
        """
        [TODO: (simplify .chunk() method by putting stats-related code here)]

        Write chunking-related statistics
        chkr : chunker.Chunker instance
        """
        pass

    def write_stats(self, index, path):
        """
        Write statistics as csv file

        index (int) - index of the tier in each group to use
        path (str) - full path with filename for saving csv file
        """

        rows, total_count, total_dur = self.calc_stats(index)
        tier_names = list(set([x.data[index].GetName() for x in self.data]))
        outfile = codecs.open(path, mode='wb', encoding='utf8')
        outcsv = csv.writer(outfile, delimiter=',')
        outcsv.writerow(['Groups:', len(self.data)])
        outcsv.writerow(['Tier index:', index])
        outcsv.writerow(['Tier names:', ' '.join(tier_names)])
        outcsv.writerow(['Total items:', total_count])
        outcsv.writerow(['Total duration (s):', total_dur])
        for row in rows:
            outcsv.writerow(row)
        outfile.close()

    def calc_stats(self, index):
        stats_all = []
        whole_dur_all = [] # Durations of tiers
        for group in self.data:
            labels_gr,counts_gr,durs_gr = tierutil.stats_label_distrib(
                group.data[index])

            # Convert to dict {label:(count, durs)}
            stats_group = {}
            i = 0
            while i < len(labels_gr):
                stats_group[labels_gr[i]] = [counts_gr[i], durs_gr[i]]
                i += 1
            stats_all.append(stats_group)

            # Get tier durations
            whole_dur = (group.data[index].GetEndValue()
                         - group.data[index].GetBeginValue())
            whole_dur_all.append(whole_dur)

        # Get list of unique lables
        all_labels = []
        for stats_group in stats_all:
            all_labels.extend(stats_group.keys())
        all_labels = list(set(all_labels))

        # Sum up through groups
        summed_stats = {}
        for label in all_labels:
            for stats_group in stats_all:
                if label in stats_group.keys():
                    if label not in summed_stats.keys():
                        summed_stats[label] = stats_group[label]
                    else:
                        summed_stats[label][0] += stats_group[label][0]
                        summed_stats[label][1] += stats_group[label][1]

        # Calculate more stats and convert to rows
        table = [] # Table for the result
        header_row = ['Label', 'Count', 'Freq (%)',
                      'Dur:summed', 'Dur:normed(%)', 'Dur:mean',
                      'Dur:median', 'Dur:min', 'Dur:max', 'Dur:skew']
        table.append(header_row)
        total_duration = sum(whole_dur_all)
        total_count = sum([summed_stats[key][0] for key in summed_stats])
        for label in (sorted(summed_stats.keys())):
            count = summed_stats[label][0]
            dur = summed_stats[label][1]
            frequency = count/total_count*100
            dur_summed = sum(dur)
            dur_normed = sum(dur)/total_duration*100
            dur_mean = sum(dur)/count
            dur_median = np.percentile(dur, 50)
            dur_min = min(dur)
            dur_max = max(dur)
            dur_skew = scipy.stats.skew(dur, axis=0, bias=True)
            row = [label, count, frequency, dur_summed, dur_normed,
                   dur_mean, dur_median, dur_min, dur_max, dur_skew]
            table.append(row)
        return table, total_count, total_duration

    def search_by_label(self, index, patterns, verbose=0):
        """
        Regular expression search in labels
        === In ===
        index : int
            Index of the tier in each group
        patterns : list
            List of regular expressions
        verbose : int {0,1,2} default 0
            Level of verbosity
        showunique : int
            Maximum number of unique text values that can be printed
        === Out ===
        list
           List of tuples (group_index, annotation)
        """
        if isinstance(patterns, str):
            patterns = [patterns]
        res = []
        for group_index, group in enumerate(self.data):
            if verbose==2:
                print 'Group:', group_index, group.name
            gr_res = group.search_regex(index, patterns, verbose=(verbose==2))
            if gr_res:
                gr_res = [(group_index, x) for x in gr_res]
                res.extend(gr_res)
        if verbose:
            if len(res) != 0:
                print 30*'-'+'\nTotal of {} matches'.format(len(res))
                # Count unique labels
                unique = {}
                for label in [annot.TextValue for group,annot in res]:
                    unique[label] = unique.get(label, 0) + 1
                print 'Unique:', len(unique)
                # Sort uniques
                unique = list(unique.iteritems())
                unique.sort(key=lambda t: t[1], reverse=True)
                print tabulate(unique)
            else:
                print 30*'-'+'\nNo matches in the corpus'
        return res

    def describe(self, index=None, latex=False):
        if index is None and self.data:
            for index in range(len(self.data[0])):
                self.describe(index=index, latex=latex)
            return
        table, total_count, total_dur = self.calc_stats(index)
        if latex:
            fmt = 'latex'
        else:
            fmt = 'simple'
        tier_names = list(set([x.data[index].GetName() for x in self.data]))
        print 'Groups:', len(self.data)
        print 'Tier index:', index
        print 'Tier names:', ' '.join(tier_names)
        print 'Total items:', total_count
        print 'Total duration (s):', total_dur
        print tabulate(table, headers='firstrow', tablefmt=fmt)
        print '\n'

    def remove(self, index):
        self.data = self.data[:index]+self.data[index+1:]

    def load(self, path, subset=None, reference=None, equalize=False):
        """
        Read a signle textgrid or a list of textgrids from disk
        and append them to .data
        === In ===
        path : str or list
            path to a TextGrid or list of paths
        reference (int)
            index of the reference tier, 0-based
            (ex. it may be tokens tier for discourse units)
        subset (int) - list of 0-based indices
            of the segmentation tiers
        """
        # a list is given
        if hasattr(path, '__iter__'):
            pathlist = [x for x in path if x.lower().endswith('.textgrid')]
            if not pathlist:
                raise IOError('No textgrids')
            for p in pathlist:
                self.load(p, subset=subset, reference=reference,
                          equalize=equalize)
            return

        # # one directory is given
        # if not os.path.isdir(path):
        #     raise IOError('No such directory: ' + path)
        # path_list = glob(os.path.join(path,'*.[Tt]ext[Gg]rid'))
        # path_list = [x for x in os.listdir(path)
        #              if x.lower().endswith('.textgrid')]
        fname = os.path.split(path)[1]
        print 'Loading', path, '...'
        # logging.info('Loading '+path)
        gs = groupsegm.GroupSegm(name=fname)
        gs.load_textgrid(path, subset=subset, reference=reference,
                         equalize=equalize)
        self.pathlist.append(os.path.abspath(path))
        self.data.append(gs)


    def write(self, path, fname_prefix=None):
        """
        Write corpus to a directory.
        If the corpus was read from a directory and 'fname_prefix' is
        not set, original file names are used. Otherwise file names are
        numbers from 0 with an optional prefix.

        path (str) - path for writing, created if non existant
        fname_prefix (str) - setting prefix forces numbering instad of using
                             original filenames, even if they do exist
        """
        if not os.path.isdir(path):
            if not os.path.exists(path):
                os.mkdir(path)
            else:
                raise IOError('Cannot create directory. File with such '
                              'name already exists.')
        # 1. eventually create filenames
        if fname_prefix:
            fill = self._calc_fill(len(self.data))
            fname_matrix = fname_prefix + '{:0' + fill + '}.TextGrid'
            fnames = [fname_matrix.format(x) for x in range(len(self.data))]
        elif self.pathlist:
            fnames = [os.path.split(x)[1] for x in self.pathlist]
        else:
            fill = self._calc_fill(len(self.data))
            fname_matrix = '{:0' + fill + '}.TextGrid'
            fnames = [fname_matrix.format(x) for x in range(len(self.data))]
        # 2. write
        i = 0
        while i < len(self.data):
            self.data[i].write(os.path.join(path, fnames[i]))
            i += 1

    def _calc_fill(self, x):
        fill = math.log10(x)
        if fill.is_integer():
            return str(int(fill))
        else:
            return str(int(fill) + 1)

    def trim_right(self, t):
        for segm in self.data:
            segm.trim_right(t)

    def trim_left(self, t):
        for segm in self.data:
            segm.trim_left(t)

    def eval(self, metric, subset):
        res = []
        for group in self.data:
            res.append(group.eval(metric, subset))
        return sum(res) / len(res)

    def getbyname(self, patt):
        """
        Returns first tier which file name matches regular expression
        === In ===
        patt : str
            python regular expression
        === Out ===
        groupsegm.GroupSegm
        """
        res = []
        for i, path in enumerate(self.pathlist):
            fname = os.path.split(path)[1]
            if re.search(patt, fname):
                res.append(self.data[i])
        if res:
            return res
        return None
