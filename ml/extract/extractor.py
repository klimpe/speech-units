import logging
#import re
#import numpy as np
from annotationdata.label.label import Label
from annotationdata.ptime.interval import TimeInterval
from annotationdata.annotation import Annotation
#from annotationdata.tier import Tier
import data_access as da


class Extractor(object):
    '''
    Generic class for extractors
    '''
    def __init__(self):
        self._log = logging.getLogger(__name__)
        self._data = None
        self.data = None # Implemented with setter in children
        self.extracted = None   # Extracted features as 2d dictionnary
        self.labels = None # Labels, generated upon extraction
        self.speaker = None # Speaker (or part) label
        self._subset_order = None  # Available feature subsets in order
        self._subset_len = None  # Lengths of feature subsets, dict
        self.pause_labels = ('#', '+')  # TODO :use regex r'#|\+'
        self.pause_threshold = 0.2   # Separates short vs. long pauses
                                     # short pauses < THRESHOLD <= long pauses

    def _create_labels(self, subset=None):
        '''
        In: subset (list of strings)
        Out: list
        '''
        subset = self._prep_subset(subset)
        labels = []
        for item in self._subset_order:
            if item in subset:
                if item in ('AP', 'IP', 'DU', 'TIME', 'SPEAKER'):
                    labels.append(item.lower())
                else:
                    for num in range(1,self._subset_len[item]+1):
                        labels.append(item.lower() + str(num))
        self.labels = labels


    def _prep_subset(self, subset=None):
        '''
        List elements -> upcase.
        Raise error if list contains non-available feature subsets names.
        In: subset (list)
        Out: (list)
        '''

        if subset is None:
            subset = self._subset_order
        else:
            subset = [x.upper() for x in subset]
            if not set(subset).issubset(self._subset_order):
                allowed = ' '.join(self._subset_order)
                raise ValueError('Unknown subset. Allowed: {}'.format(allowed))
        # remove AP, IP, DU if not loaded
        tocheck = {'ip', 'ap', 'du'}
        missing = [x.upper()
                   for x in tocheck
                   if not self.data.dict.has_key(x)]
        res = []
        for label in self._subset_order:
            if label in subset:
                if label not in missing:
                    res.append(label)
        return res


    def __str__(self):
        return str(self.__class__) + '\n' + str(self._data)


    def _log_progress(self, i, total):
        '''Log percentage every 200 items'''
        if i % 200 == 0:
            percentage = round(i/float(total)*100,1)
            self._log.debug('{} items  {}%'.format(i, percentage))

    # =====================[ Data pre-processing ]=====================

    def _merge_pauses(self, which):
        '''
        Preprocess a tier by merging sequences of pauses
        In:
          which (str) - name of the tier to process
        '''
        pauses = {'','#','+'}# NB here, empty string is also included
        merged_count = 0
        index = 0
        while index < len(self.data.dict[which])-1:
            labels = [x.TextValue for x in self.data.reference[index:index+2]]
            if set(labels).issubset(pauses):
            #if self._count_pauses([index, index+1]) == 2:
                left = self.data.dict[which][index]
                right = self.data.dict[which][index+1]
                merged=Annotation(TimeInterval(left.Begin,right.End),
                                  Label('#'))
                self.data.dict[which].Remove(left.Begin, right.End)
                self.data.dict[which].Add(merged)
                merged_count += 1
                index -= 3 # [th]
            index += 1
        if merged_count:
            msg = 'Merged {} pauses in {}.'.format(merged_count, which)
            self._log.info(msg)

    # =====================[ Pause-related ]=====================

    def _count_pauses(self, indices, mindur=0, maxdur=0):
        '''
        How many of given indices of the syllable tier correspond
        to pauses.

        In:
          indices (list) - indices of syllable tier
          mindur (float) Minimal pause duration. 0 turns this off
          maxdur (float) Maximal pause duration. 0 turns this off
        Out: (int)
        '''
        n = [self._is_pause(i, mindur, maxdur) for i in indices]
        n = len([x for x in n if x])
        return n


    def _is_pause(self, index, mindur=0, maxdur=0):
        '''
        Check whether an annotation is a pause in reference tier.
        In:
          index (int) index of the annotation in reference tier
          mindur (float) Minimal pause duration.
          maxdur (float) Maximal pause duration. 0 = infinite
        Out: (bool)
        '''
        unit = self.data.reference[index]
        if unit.TextValue.strip() not in self.pause_labels:
            return False
        # Check duration
        mindur_res = True
        maxdur_res = True
        if mindur:
            mindur_res = unit.Time.Duration() >= mindur
        if maxdur:
            maxdur_res = unit.Time.Duration() <= maxdur
        return mindur_res and maxdur_res


    def _calc_average_pause_duration(self):
        '''
        Out: (float) Average pause duration in reference tier.
        '''
        durations = []
        i = 0
        while i < len(self.data.reference):
            if self._is_pause(i, mindur=0, maxdur=1):
                durations.append(self.data.reference[i].Time.Duration())
            i += 1
        return sum(durations)/len(durations)

    # =====================[ Extraction ]======================

    def extract(self, subset=None):
        '''
        Extract all and put it to Extractor.extracted

        === In ===
        subset (list)
            list of feature subset codes
            'None' means use all features

        === Out ===
        None
        '''
        subset = self._prep_subset(subset)
        self._create_labels(subset)
        msg = 'Extracting features. Subset:{}'
        self._log.info(msg.format(subset))
#        res = np.zeros((len(self.data.reference), len(self.labels)))
        res = []
        index = 0
        # Iterate through reference units skipping pauses.
        while index < len(self.data.reference):
            if not self._is_pause(index):
                item = self.extract_one(index, subset=subset)
                res.append(item)
            self._log_progress(index, len(self.data.reference))
            index += 1
        msg = 'Extracted {} items. Skipped pauses: {}'
        msg = msg.format(len(res), index-len(res))
        self._log.info(msg)
        self.extracted = res


    def extract_one(self, index, subset=None):
        '''
        Calculate feature vector for given syllable.
        Order: [endtime] [speaker] <subsets>

        === In ===
        index (int)
            index of the syllble
        subset (list)
            list of subset codes
            'None' means use all features

        === Out ===
        (list)
           One training example
        '''
        subset = self._prep_subset(subset)
        item = [] # one training example
        for sub in subset:
            funname = 'calc_' + sub
            calc_subset = getattr(self, funname)
            item += calc_subset(index)
        return item

    # ==================[ Common Features ]====================

    def calc_TIME(self, index):
        '''
        Returns endtime of a reference unit
        '''
        return [self.data.reference[index].EndValue]


    def calc_SPEAKER(self, index):
        '''
        Returns speaker's number
        '''
        return [da.SPEAKERS.index(self.speaker)]


    # --------------------- Annotations -----------------------
    def calc_DU(self, index):
        return [self._feat_du(index)]


    def calc_AP(self, index):
        return [self._feat_pu(index, 'ap')]


    def calc_IP(self, index):
        return [self._feat_pu(index, 'ip')]


    def _feat_pu_bin(self, index, which, delta=None):
        '''
        Presence of an annotated PU boundary
        after the unit

        In: (int)
        Out: 1 or 0
        '''
        if which not in ('ip', 'ap'):
            raise ValueError('accepted values: "ap", "ip"')        
        if delta is not None:
            self.data.dict['ip'].SetRadius(delta)
        # Syllable's right boundary
        boundary = self.data.reference[index].EndValue
        if self.data.dict['ip'].Rindex(boundary) != -1:
            return 1
        return 0

        
    def _feat_pu(self, index, which, delta=None):
        '''
        'Certainty' of the subsequent IP boundary,
        calculated from the number of annotators who agree on it.
        Expert and naive annotators are given different weights:
        1 and 0.25 respectively.

        === In ===
        index : int
        which : {'ip', 'ap'}
        delta : float
        === Out ===
        float
        '''
        if which not in ('ip', 'ap'):
            raise ValueError('accepted values: "ap", "ip"')
        naive_coeff = 0.25
        if delta is not None:
            self.data.dict[which].SetRadius(delta)
        # Syllable's right boundary
        boundary = self.data.reference[index].EndValue
        index = self.data.dict[which].Rindex(boundary)
        if index != -1:
            label = self.data.dict[which][index].TextValue
            if label:
                expert = int(label[-2])
                naive = int(label[-1])
                certainty = expert + naive * naive_coeff
                return certainty        
        return 0


    def _feat_du(self, index):
        '''
        'Certainty' of the subsequent DU boundary,
        calculated from the number of annotators who agree on it.
        Expert and naive annotators are given different weights:
        1 and 0.25 respectively.        

        In: (int)
        Out: 1 or 0
        '''
        naive_coeff = 0.25
        
        boundary = self.data.reference[index].EndValue
        du_tier = self.data.get_tier('du')
        index = du_tier.Rindex(boundary)
        if index != -1:
            label = du_tier[index].TextValue
            if label:
                label = label.split()[1]
                expert = int(label[0])
                naive = int(label[1])
                certainty = expert + naive * naive_coeff
                return certainty        
        return 0



    # ==================[ IO ]====================
    def write_csv(self, path, header=False):
        '''
        Write result to a simple comma-separated file.
        '''
        if self.extracted is None:
            raise Exception('First run extraction with "extract()"')
        data = []
        if header and self.labels:
            data = [self.labels] + data
        for row in self.extracted:
            row = ['?'
                   if x is None
                   else x
                   for x in row]
            data.append(row)
        da.write_csv(data, path)


    # def arff_header():
    #     self._create_labels()
    #     binary = re.compile('pd7|pp[7-8]|ps1|sb1|sc[1-8]|sd[1-4]|lm[1-5]')
    #     string = re.compile('lt[1-4]')

    #     header_lines = ['@relation\n']
    #     for label in self.labels:
    #         if re.match(binary, label):
