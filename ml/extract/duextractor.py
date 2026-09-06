from __future__ import division
# import csv
# import os
# import annotationdata.io as adio
import copy as cp
import re
import groupsegm as gs
from annotationdata.ptime.interval import TimeInterval
from annotationdata.label.label import Label
from annotationdata.annotation import Annotation
from annotationdata.tier import Tier
import data_access as da
import puextractor
import dm_list2 as dm_list
from extractor import Extractor


class DUExtractor(Extractor):
    '''
    Class for extracting features to detect discourse units.

    Iterates through tokens (excluding pauses),
    i.e. one token = one training example.

    Data locations are defined in data_access.py

    3.1 added m3 (weak initial DM)
        added z1 (combined )
    '''

    def __init__(self, speaker=None, data=None, copy=False):
        '''
        In:
          speaker (str) Used as prefix to name intermediate files.
          data (list)  If a piece of data is missing, use None.
            Expected contents
              0 tokens (Tier)
              1 syllables (Tier)
              2 ip: intermediate prosodic units (Tier)
              3 ap: intermediate prosodic units (Tier)
              4 du: discourse units (Tier)
              5 raw pitch (PitchTier)
              6 stylized pitch (PitchTier)
              7 nuclei
              8 chunks - POS tags
              9 chunks - disfluency categories
             10 chunks - disfluency boolean
        '''
        # Initialize parent
        super(DUExtractor, self).__init__()

        self._syll_indices = None
        self._pu_extractor = None

        # Available feature subsets in order
        self._subset_order = ['TIME', 'SPEAKER',
                              'PD', 'PP', 'PS',
                              'SB', 'SC', 'SD',
                              'LM', 'LT', 'DF',
                              'AP', 'IP', 'DU']
        # Lengths of feature subsets
        self._subset_len = {'PD':8, 'PP':10, 'PS':3,
                            'SB':1, 'SC':8, 'SD':4, 
                            'LM':5, 'LT':4,
                            'DU':1, 'IP':1, 'AP':1}
        self.speaker = speaker
        if copy:
            self.data = cp.copy(data)
        else:
            self.data = data  # tokens tier will be modified (merge pauses)

    @property
    def data(self):
        '''Access tiers grouped in GroupSegm object'''
        return self._data

        
    @data.setter
    def data(self, indata):
        '''
        In:
          indata (GroupSegm or other sequence of Tiers)
        '''
        if indata is None:
            return
        if isinstance(indata, gs.GroupSegm):
            self._data = indata
        else:
            self._data = gs.GroupSegm(indata)
        # One training example corresponds to one token
        self._data.reference_name = 'token'
        # [Calculations]
        # Preprocess reference (tokens)
        self._preprocess_tokens()

        # Instantiate client class PUExtractor
        #   to calculate D, P, S and C features.
        # (!) syllable tier will be modified (merge pauses) by the next line
        pudata = cp.copy(indata)
        self._pu_extractor = puextractor.PUExtractor(self.speaker, pudata)
        self._pu_extractor.pause_labels = self.pause_labels

        # Calculate indices of tokens in terms of syllables
        self._syll_indices = self._prep_syll_indices()


    def _prep_syll_indices(self):
        res = []
        for t in self.data.dict['token']:
            syll_index = self.data.dict['syllable'].Rindex(t.End)
            if syll_index == -1:
                syll_index = self.data.dict['syllable'].Near(t.End, 0)
                if syll_index == -1:
                    print '-1', t
            res.append(syll_index)
        res1 = [x for x in res if x != -1]
        unaligned = len(res)-len(res1)
        if unaligned:
            self._log.warning(str(unaligned)
                              + 'unaligned token-syll boundaries.')
        return res1


    # ============= Feature subset calculation =============

    def calc_PD(self, index):
        sindex = self._syll_indices[index]
        features =  self._pu_extractor.calc_PD(sindex)
        return features

    def calc_PP(self, index):
        sindex = self._syll_indices[index]
        features =  self._pu_extractor.calc_PP(sindex)
        return features

    def calc_PS(self, index):
        sindex = self._syll_indices[index]
        features =  self._pu_extractor.calc_PS(sindex)
        return features

    def calc_SB(self, index):
        sindex = self._syll_indices[index]
        features =  self._pu_extractor.calc_SB(sindex)
        return features

    def calc_SC(self, index):
        sindex = self._syll_indices[index]
        features =  self._pu_extractor.calc_SC(sindex)
        return features

    def calc_SD(self, index):
        sindex = self._syll_indices[index]
        features =  self._pu_extractor.calc_SD(sindex)
        return features

    def calc_LM(self, index):
        features = []
        features.append(self._feat_m1(index))
        features.append(self._feat_m2(index))
        features.append(self._feat_m3(index))
        features.append(self._feat_m4(index))
        features.append(self._feat_m5(index))
        return features

    def calc_LT(self, index):
        features = []
        features.append(self._feat_t1(index))
        features.append(self._feat_t2(index))
        features.append(self._feat_t3(index))
        features.append(self._feat_t4(index))
        return features              


    # ===============[ Features LM: Discourse Markers ]============= #

    def _feat_m1(self, index):
        '''
        Next token is initial strong discourse marker
        Out: 0 or 1, None if calculation is impossible.
        '''
        if index+1 >= len(self.data.dict['token']):
            return None
        # jump over pause
        if self._is_pause(index+1):
            index = index+1
        return int(self.data.dict['token'][index+1].TextValue
                   in dm_list.initials['strong'])


    def _feat_m2(self, index):
        '''
        Current token is final discourse marker
        Out: 0 or 1
        '''
        return int(self.data.dict['token'][index].TextValue in dm_list.finals)


    def _feat_m3(self, index):
        '''
        Next token is initial weak DM
        Out: 0 or 1, None if calculation is impossible.
        '''
        if index+1 >= len(self.data.dict['token']):
            return None
        # jump over pause
        if self._is_pause(index+1):
            index = index+1
        return int(self.data.dict['token'][index+1].TextValue in dm_list.initials['weak'])


    def _feat_m4(self, index):
        '''
        Next token is initial DM 'ah'
        Out: 0 or 1, None if calculation is impossible.
        '''
        if index+1 >= len(self.data.dict['token']):
            return None
        # jump over pause
        if self._is_pause(index+1):
            index = index+1
        return int(self.data.dict['token'][index+1].TextValue == 'ah')


    def _feat_m5(self, index):
        '''
        Next initial DM 'mais'
        Out: 0 or 1, None if calculation is impossible.
        '''
        if index + 1 >= len(self.data.dict['token']):
            return None
        # jump over pause
        if self._is_pause(index+1):
            index = index+1
        return int(self.data.dict['token'][index+1].TextValue == 'mais')

        
    # ===========[ Lexical features. Token uni/bi-grams ]=========

    def _feat_t1(self, index):
        '''
        Current token
        Out: string
        '''
        return self.data.dict['token'][index].TextValue


    def _feat_t2(self, index):
        '''
        Next token. Jump over pauses (output cant be '#').
        Out: string, None if calculation is impossible.
        '''
        nxt_index = index + 1
        if nxt_index >= len(self.data.dict['token']):
            return None
        if self._is_pause(nxt_index):
            nxt_index += 1
        if nxt_index >= len(self.data.dict['token']):
            return None
        return self.data.dict['token'][nxt_index].TextValue


    def _feat_t3(self, index):
        '''
        Bigram of previous + current token. Jump over pauses.
        Out: string, None if calculation is impossible.
        '''
        prv_index = index - 1
        if prv_index < 0:
            return None
        if self._is_pause(prv_index):
            prv_index -= 1
        if prv_index < 0:
            return None

        cur = self.data.dict['token'][index].TextValue
        prv = self.data.dict['token'][prv_index].TextValue
        res = prv + ' ' + cur
        return res


    def _feat_t4(self, index):
        '''
        Bigram of current + next token. Jump over pauses.
        Out: string, None if calculation is impossible.
        '''
        nxt_index = index + 1
        if nxt_index >= len(self.data.dict['token']):
            return None
        if self._is_pause(nxt_index):
            nxt_index += 1
        if nxt_index >= len(self.data.dict['token']):
            return None

        cur = self.data.dict['token'][index].TextValue
        nxt = self.data.dict['token'][nxt_index].TextValue
        res = cur + ' ' + nxt
        return res



    # # ===============[ Features U: dU related ]============= #
    # def _feat_u1(self, index):
    #     '''
    #     Distance to the last DU boundary - time or units or both?
    #     '''
    #     token = self.data.dict['token'][index]
    #     if
    #     du_bnd = self.du_tier.Near(token.BeginValue, -1)


    # # ===============[ Features Z: Combined features ]============= #

    # def calc_features_Z(self, index, D, M):
    #     features = []
    #     z1 = self._feat_z1(index, D, M)
    #     features.append(z1)
    #     return features

    # def _feat_z1(self, index, D, M):
    #     '''
    #     Followed by pause or is DM initial: (d1 or m1)
    #     Out: 0 or 1
    #     '''
    #     if 1 in (D[0], M[0]):
    #         return 1
    #     else:
    #         return 0

    def _preprocess_tokens(self):
        self._merge_pauses(self.data.reference.Name)
        self._remove_toe()
        

    def _remove_toe(self):
        '''
        Tokens preprocessing: remove 
        =x= --> merge with the interval on the left
        '''
        count = 0
        tier = self.data.dict['token']
        regex = re.compile(r'=[\w]=')
        for index, interval in enumerate(tier):
            if re.match(regex, interval.TextValue):
                removed = tier.Pop(index)
                prev = tier[index-1]
                prev.EndValue = removed.EndValue
                count += 1
        self._log.info('Removed {} liasons.'.format(count))
        return tier
                

    # ========================[ I/O ]============================= #

    def load_data(self, *args, **kwargs):
        '''
        Relies on paths defined in data_access module

        Args:
          speaker - cf. SPEAKERS
        Kwargs:
          du_strat - 'A', 'B', 'C' or None
          pu_strat - 'A', 'B', 'C', 'D' or None
          phonsegm - 'phonsyll', '', ...  If False, nuclei are not loaded.
          nuclei (bool) - load nuclei tier        
        '''
        group = da.load_extractor_group(*args, **kwargs)
        self.data = group



